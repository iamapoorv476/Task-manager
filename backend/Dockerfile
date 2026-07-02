# syntax=docker/dockerfile:1

# ---- Builder stage ----
# Installs dependencies into a venv, kept separate from the final image
# so build-time state (pip cache, any compiler artifacts) never ends up
# in what actually ships.
FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Dependencies are installed from just pyproject.toml plus an empty
# package stub, BEFORE the real source is copied in. This layer only
# gets invalidated (re-downloading every dependency) when pyproject.toml
# itself changes -- not on every source code edit -- which is most of
# the point of splitting the build into stages like this.
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# Now bring in the real source and reinstall just our own package.
# --no-deps because every dependency is already satisfied by the layer
# above; this second install is just registering the real `app` code,
# which is fast since there's no dependency resolution to redo.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir --no-deps .

# ---- Final stage ----
FROM python:3.11-slim

# Runs as a non-root user -- if the app is ever compromised through a
# code-level vulnerability, that shouldn't also hand an attacker root
# inside the container.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini entrypoint.sh ./

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Invoked via `sh` explicitly rather than relying on the file's execute
# bit -- that bit doesn't reliably survive a Windows git checkout, and
# this way it doesn't matter whether it did.
ENTRYPOINT ["sh", "./entrypoint.sh"]