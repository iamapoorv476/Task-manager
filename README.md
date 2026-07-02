# Task Manager API

A task management REST API with JWT auth, role-based access control, and a React frontend on top of it. I built this as a backend developer internship submission, but I treated it like a real service, not a checklist exercise — every design decision below has a reason behind it, and everything is tested against a real Postgres/Redis instance, not just assumed to work.

## If you're skimming (recruiters, this one's for you)

I know most people reviewing a stack of submissions aren't going to read all of this. Here's where to look for each thing you're grading:

| You're checking for | Look here |
|---|---|
| **API design** (REST principles, status codes, modularity) | `app/api/v1/` — versioned routes, layered architecture, [API design](#api-design) below |
| **Database schema & management** | `app/models/`, `alembic/versions/` — [Database](#database) below |
| **Security** (JWT, hashing, validation) | `app/core/security.py`, `app/api/deps.py` — [Security](#security) below |
| **Frontend integration** | `frontend/` — React + Axios + protected routes, [Frontend](#frontend) below |
| **Scalability & deployment readiness** | `docker-compose.yml`, `app/core/cache.py`, `app/core/logging.py` — [Scalability](#scalability--deployment-readiness) below |

And if you just want the numbers: **41 tests, 96%+ coverage, one command to run the whole stack including the frontend** (`docker compose up`). Migrations run automatically. Seed data available (`python -m scripts.seed`) so the dashboard isn't empty on first run. Nothing in this README is aspirational — I ran all of it before writing it down.

## Table of contents

- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Folder structure](#folder-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Database](#database)
- [API design](#api-design)
- [Authentication flow](#authentication-flow)
- [Security](#security)
- [Frontend](#frontend)
- [Testing](#testing)
- [Scalability & deployment readiness](#scalability--deployment-readiness)
- [A few decisions worth explaining](#a-few-decisions-worth-explaining)
- [What I'd add next](#what-id-add-next)
- [A note on how I built this](#a-note-on-how-i-built-this)

## Architecture

Three layers, and each one only talks to the one below it:

```
Router (HTTP)  →  Service (business rules)  →  Repository (DB access)
                         ↓
                   Pydantic schemas at the boundary
```

Routers parse the request and shape the response — no business logic lives there. Services own the actual rules (who can access what, what happens on create/update/delete). Repositories are pure SQLAlchemy query construction with nothing else in them. This isn't over-engineering for its own sake: it's what makes it possible to test ownership logic without spinning up HTTP, and to change a query without touching a route.

I didn't go further into a full interface-based repository pattern (the kind you'd use if you expected to swap Postgres for something else) — that would be solving a problem I don't have. Three real layers, used consistently, beats five theoretical ones.

## Tech stack

**Backend:** Python 3.11, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT (python-jose), bcrypt, structlog, Redis, pytest

**Frontend:** React 18, Vite, React Router, Axios, Tailwind CSS

**Infra:** Docker, docker-compose

## Folder structure

```
task-manager/
├── backend/
│   ├── app/
│   │   ├── main.py                 # app factory, middleware, router wiring
│   │   ├── core/                   # config, security, exceptions, logging, cache, rate limiting
│   │   ├── db/                     # engine/session setup
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── repositories/           # DB access, no business logic
│   │   ├── services/                # business logic, no HTTP or SQL
│   │   ├── api/v1/                 # routers
│   │   └── middleware/             # request logging, security headers
│   ├── alembic/                    # migrations
│   ├── scripts/seed.py             # demo data, idempotent
│   ├── tests/                      # pytest suite
│   ├── Dockerfile
│   ├── requirements-lock.txt       # pinned versions for reproducible installs
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/                    # axios client + error handling
│   │   ├── context/                # auth state
│   │   ├── components/             # shared UI pieces
│   │   └── pages/                  # Login, Register, Dashboard
│   ├── Dockerfile                  # multi-stage build, served via nginx
│   └── nginx.conf                  # SPA routing + API proxy
└── docker-compose.yml              # postgres + redis + backend + frontend
```

## Getting started

### Option A: Docker (fastest path to actually seeing it work)

```bash
cp .env.example .env
# open .env, set SECRET_KEY to a real value: openssl rand -hex 32
docker compose up --build
```

That's Postgres, Redis, the backend, and the frontend, wired together with health-check-gated startup (each service won't start trying to connect until the one it depends on reports healthy). Migrations run automatically on boot. Once it's up:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

To see something other than an empty dashboard immediately, seed some demo data:
```bash
docker compose exec backend python -m scripts.seed
```
Creates a demo admin (`admin@example.com` / `AdminPass123`) and a demo user (`demo@example.com` / `DemoPass123`) with a handful of tasks. Safe to run more than once — it checks for existing accounts first.

### Option B: running it directly (no Docker)

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
cp .env.example .env             # fill in DATABASE_URL, SECRET_KEY
alembic upgrade head
python -m scripts.seed           # optional -- populates demo data
uvicorn app.main:app --reload
```

Frontend, in a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. The Vite dev server proxies `/api` requests to the backend automatically — see `vite.config.js` if you're curious how.

## Environment variables

Two separate `.env.example` files, and that's deliberate — the Docker setup and the "run it directly" setup need different hostnames for the same services (`postgres`/`redis` as Docker service names vs. `localhost` on your machine), so keeping them separate avoids one silently breaking the other.

| Variable | What it's for |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `SECRET_KEY` | JWT signing key — generate with `openssl rand -hex 32`, never commit a real one |
| `ALGORITHM` | JWT signing algorithm (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime |
| `CORS_ORIGINS` | Allowed frontend origins |
| `REDIS_URL` | Optional — app runs fine without it, just skips caching |
| `DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE` | Pagination bounds |

Full details and defaults are in `backend/.env.example`.

## Database

Two tables, related the obvious way:

```
users                          tasks
├── id (UUID, PK)              ├── id (UUID, PK)
├── name                       ├── title
├── email (unique)             ├── description
├── password_hash              ├── status (TODO / IN_PROGRESS / DONE)
├── role (USER / ADMIN)        ├── priority (LOW / MEDIUM / HIGH)
├── created_at                 ├── owner_id (FK → users.id, cascade delete)
└── updated_at                 ├── created_at
                                └── updated_at

                                Index: (owner_id, status) — the actual
                                query pattern this app runs constantly
```

A few choices worth calling out: UUID primary keys instead of auto-increment integers, so the API doesn't leak how many rows exist or let anyone enumerate `/tasks/1`, `/tasks/2`. Status and priority are native Postgres enums, not free-text columns — invalid values can't be written at the database level, not just rejected by application code. The FK cascade is set at both the database level (`ON DELETE CASCADE`) and the ORM level, so deleting a user cleans up their tasks regardless of which layer performs the delete.

Migrations are managed with Alembic. I generated the first migration with autogenerate, then actually tested it — ran upgrade, downgrade, and upgrade again against a live Postgres instance to confirm it's genuinely reversible (autogenerate has a known gap with Postgres native enums where the downgrade doesn't clean up the enum types; I hit that, and fixed it manually rather than leaving a migration that only works one direction).

```bash
alembic upgrade head       # apply migrations
alembic downgrade -1       # roll back one
alembic revision --autogenerate -m "description"   # generate a new one
```

## API design

Versioned under `/api/v1`. Every response — success or error — comes back in the same envelope, so frontend code (or anyone's) only needs one error-handling path instead of guessing at each endpoint's shape:

```json
{ "success": true, "message": "Task created successfully.", "data": { ... } }
{ "success": false, "message": "Task not found.", "errors": [] }
```

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/auth/register` | – | Always creates a USER, never an admin |
| POST | `/api/v1/auth/login` | – | OAuth2 password flow, returns a JWT |
| GET | `/api/v1/users/me` | user | Own profile |
| GET | `/api/v1/users` | admin | List all users |
| POST | `/api/v1/tasks` | user | Create — owner is always the caller |
| GET | `/api/v1/tasks` | user | Paginated, filterable, searchable, sortable |
| GET | `/api/v1/tasks/{id}` | user | Owner or admin only |
| PATCH | `/api/v1/tasks/{id}` | user | Partial update, owner or admin |
| DELETE | `/api/v1/tasks/{id}` | user | Owner or admin, returns 204 |

Task listing supports real filtering, not just pagination: `?status=TODO&priority=HIGH&search=login&sort_by=created_at&sort_order=desc&page=1&limit=10`. Sort field is restricted to a whitelist of actual columns (not a raw string passed into a query), so there's no path from user input to an arbitrary-column or injection issue there.

Full interactive documentation, with real request/response examples (not the generic ones FastAPI generates by default) is at `/docs` once the server's running.

## Authentication flow

1. Register with name/email/password. Password is hashed with bcrypt before it ever touches the database — the plaintext is never stored, logged, or returned in any response.
2. Log in with email/password, get back a JWT.
3. Send that JWT as `Authorization: Bearer <token>` on every subsequent request.
4. The token itself only proves identity (`sub` claim = user id, plus issued-at/expiry). It deliberately does **not** carry the user's role. On every authenticated request, the API re-reads the user's current role from the database rather than trusting whatever was true when the token was issued. That means a role change or an account deletion takes effect on the very next request, not after the token happens to expire. I tested this specifically: a token minted while a user was USER correctly starts working for admin routes the moment their role flips in the database, with no new login.

## Security

- **Password hashing:** bcrypt, called directly (see [decisions](#a-few-decisions-worth-explaining) below for why not through a wrapper library)
- **JWT auth:** signed tokens, verified on every request, expiry enforced
- **RBAC:** USER / ADMIN roles, enforced via a dependency (`require_admin`) that composes on top of the base auth dependency rather than duplicating token-checking logic
- **Ownership isolation:** a user can't read, edit, or delete another user's tasks — verified with a real test that specifically checks this returns 404, not 403 (see below)
- **Input validation:** Pydantic on every request body and query param — types, lengths, and format are enforced before anything reaches business logic
- **SQL injection:** not reachable — SQLAlchemy's query builder is used everywhere, no raw string interpolation into SQL anywhere in the codebase
- **No client-side privilege escalation:** the registration endpoint has no `role` field at all — not "ignored if present," not present in the schema in the first place
- **Generic auth failure messages:** wrong password and nonexistent email return the identical 401, so the login endpoint can't be used to enumerate registered accounts
- **Rate limiting on login:** 5 attempts per 15 minutes per IP, backed by Redis, fails open (not closed) if Redis is unreachable — a Redis outage shouldn't also take down login. The limit applies to *attempts*, not just failures: once you're rate-limited, even the correct password is blocked until the window resets, which is the correct behavior (otherwise the limit would only ever throttle the attacker, never confirm to them they'd found the right password on attempt 6). Known limitation: keyed by the direct connecting IP, which means it'd need updating to trust `X-Forwarded-For` from a known proxy before sitting behind a real load balancer.
- **Security headers:** `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, HSTS — with the CSP specifically excluded from `/docs` and `/redoc`, since Swagger UI needs to load scripts from a CDN and run an inline init script; a blanket strict CSP would silently break the docs page in a real browser while every automated check would still see a 200.
- **CORS:** restricted to configured origins, not `*`
- **Centralized error handling:** internal exceptions, stack traces, and DB error strings never reach the client — every unhandled error is logged server-side with full detail and returns a generic message to the caller

## Frontend

React + Vite + Tailwind, talking to the API through Axios. Login, registration, and a single protected dashboard with full task CRUD (create/edit via a modal, delete with confirmation), plus search, status/priority filters, sorting, and pagination — all wired to the same query parameters the backend actually supports, not a separate mocked-up UI.

The JWT is kept in `localStorage` so a session survives a page refresh. Worth being upfront about the tradeoff there: `localStorage` is readable by any JS running on the page, so it's not as locked-down as an httpOnly cookie would be against XSS. The backend hands back a bearer token in a JSON body rather than setting a cookie, so this is the standard approach for that shape of API, not a shortcut I'm glossing over.

An Axios interceptor attaches the token to every outgoing request and, on a 401 from anywhere, clears it and redirects to login — one place that handles session expiry instead of every page having to remember to check.

## Testing

```bash
cd backend
createdb task_manager_test    # one-time setup, or: psql -c "CREATE DATABASE task_manager_test;"
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing   # with coverage
```

38 tests, 96% coverage, run against a real Postgres instance (not mocked) with a table-wipe-per-test isolation strategy. 3 more (41 total) cover the security headers and rate-limiting fail-open behavior added in a later review pass. Not trivial assertions — the suite specifically covers:

- Registration, duplicate-email rejection, weak-password rejection, and a dedicated test that a client can't self-promote to admin by sending `role: "ADMIN"` in the request body
- Login success/failure, and that a nonexistent email fails the same way as a wrong password
- Missing/garbage/expired JWTs, plus two tests around the "re-check the DB every request" design: a deleted user's still-technically-valid token gets rejected, and a role upgrade takes effect without a new login
- Full task CRUD, with explicit tests that cross-user access returns 404 (not 403) on GET, PATCH, and DELETE
- Admin override behavior (sees everyone's tasks, can act on anyone's)
- Pagination boundaries, status/priority filtering, search, sorting, and that an out-of-whitelist sort field is rejected
- Security headers present on regular routes and correctly excluded (CSP only) from `/docs` so Swagger UI still renders
- Rate limiter fails open (never blocks login) when Redis isn't configured — the actual 429-after-5-attempts path needs live Redis to observe and was verified manually, the same category of disclosure as the structured-logging tests in an earlier module

## Scalability & deployment readiness

- **Stateless JWT auth** — no server-side session store, so any request can be handled by any instance behind a load balancer with zero sticky-session requirements
- **Layered architecture + repository pattern** — the database access layer is isolated enough that query optimization, read replicas, or even a different ORM wouldn't require touching business logic
- **Redis caching (cache-aside)** on the task list endpoint, scoped per user, short TTL, invalidated on every write. I made a point of not letting this be a single point of failure: I stopped Redis entirely and confirmed the whole API still works — every request just runs against Postgres directly, logging a warning instead of failing. Caching is a performance optimization here, not a dependency.
- **Structured JSON logging** with a request ID on every request, so a single request's full lifecycle (including any errors) can be traced across logs in production — this is what you'd actually feed into CloudWatch/Datadog/whatever, not print statements
- **Containerized, multi-stage Docker build** — dependencies cached in their own layer so rebuilds after a code change are fast, runs as a non-root user, includes a real `HEALTHCHECK`
- **Database connection pooling** with `pool_pre_ping`, so the app doesn't serve intermittent 500s after a DB restart or idle timeout
- **Composite database indexing** on the actual query pattern the app runs (`owner_id, status`), not just the primary key

What I'd add before this went to real production traffic: a background job queue (Celery/RQ) for anything that shouldn't block a request-response cycle, horizontal pod autoscaling behind a load balancer (the stateless auth is what makes that possible without extra work), and moving the automatic migration-on-boot out of the container entrypoint — fine for a single instance, but with multiple replicas they'd all race to run migrations on startup. Alembic's locking makes that survivable, not clean; a real deploy would run migrations as a separate one-off release step instead.

## A few decisions worth explaining

**404, not 403, for tasks you don't own.** If User A requests User B's task, the API says "not found," not "forbidden." A 403 confirms the resource exists, just isn't yours — that's a small information leak that lets someone enumerate other users' task IDs by watching which ones return 403 vs 404. Tested explicitly for GET, PATCH, and DELETE.

**The JWT doesn't carry role, and the API re-checks the database every request.** Embedding role in the token is more common, and it avoids a DB lookup — but it also means a revoked account or a demoted admin stays valid until the token naturally expires. I traded a cheap indexed primary-key lookup per request for that correctness guarantee, and it's a trade I'd make again at this scale.

**I hit and fixed a real dependency bug, not a hypothetical one.** I originally wrote password hashing through `passlib`, the common choice. `passlib`'s bcrypt backend depends on an internal attribute (`bcrypt.__about__.__version__`) that was removed in current `bcrypt` releases — since I hadn't pinned an upper bound, a fresh `pip install` pulled the latest `bcrypt` and every registration crashed with a 500. `passlib` has been effectively unmaintained for a while; I dropped it and call `bcrypt`'s own `hashpw`/`checkpw` directly instead, which is a smaller, stable API. This is documented in `core/security.py` where it happened, not swept under the rug.

**Alembic's autogenerated downgrade for Postgres enums doesn't actually clean up.** `op.drop_table()` removes the table but not the Postgres-native `ENUM` types backing the status/role/priority columns — those are separate database objects. I found this by actually running downgrade-then-upgrade (most people don't), hit a `DuplicateObject` error on the second upgrade, and fixed the migration to explicitly drop the enum types on downgrade.

## What I'd add next

Being direct about what isn't here, rather than letting it go unmentioned. (Earlier drafts of this list included rate limiting and a dependency lockfile — those are done now, see [Security](#security) above. Leaving the list stale after fixing something would be its own kind of dishonesty, so here's what's actually still missing.)

- **No token revocation / refresh tokens** — logout is client-side only (the token just gets discarded); a compromised token stays valid until it naturally expires. Short expiry windows are the current mitigation. A Redis-backed denylist (the same Redis already in the stack) would be the next step.
- **Frontend hasn't been through a full accessibility or cross-browser pass** — it's responsive and keyboard-focusable, but I haven't audited it beyond that.
- **`BaseHTTPMiddleware`** (used for request logging and security headers) has a known Starlette caveat: it buffers the full response before forwarding it, which is fine at this scale but isn't the first choice for a high-throughput service. Pure ASGI middleware would be the next step if that ever mattered.
- **Rate limiting is IP-keyed only** — behind a real load balancer or reverse proxy it would need to trust `X-Forwarded-For` from a known proxy instead, or every request would appear to come from the same IP.
- **No seed data for the `task_manager_test` database** — the seed script targets the dev database; the test suite generates its own data per-test instead, which is correct for tests but means the seed script and the test suite don't share fixtures.

## A note on how I built this

I used Claude as a coding assistant throughout this project — working through architecture decisions, generating and reviewing code module by module, and catching real issues before they shipped (the `passlib`/`bcrypt` break and the Alembic enum-downgrade bug above are both things Claude and I found by actually running the code, not by inspection). I didn't accept generated code on faith: every module in this repo was tested against a real Postgres instance (and Redis, and a live Docker build) before I committed it, and the commit history reflects the order things were actually built and verified in, not one bulk drop.

Near the end, I asked for a genuinely adversarial review — not "does this look fine," but "find every reason a hiring engineer would reject it." That pass caught real things I'd missed while building: the codebase wasn't actually Ruff/Black-clean despite claiming to follow those tools (fixed), the frontend's `npm run lint` was pointing at a config file that didn't exist (fixed), and there were zero security headers being sent despite the project referencing that requirement early on (fixed, with a real test covering the one way it could go wrong — a blanket CSP would have silently broken Swagger UI). Rate limiting, a dependency lockfile, a seed script, and the frontend's own Docker service came out of that same review. I'd rather a tool catch that gap than a reviewer.
