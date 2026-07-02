"""Tests for authentication/authorization mechanics: JWT validation,
unauthorized access, and role-based access control.

These are deliberately more thorough than "does the happy path work" --
they probe the exact edge cases that a real security review would ask
about: what happens with no token, a garbage token, an expired token,
and a token for a user who no longer exists.
"""

from datetime import timedelta

from app.core.security import create_access_token
from app.models.user import UserRole


class TestUnauthorizedAccess:
    def test_protected_route_without_any_token_returns_401(self, client):
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        body = response.json()
        # This specifically exercises the Starlette HTTPException handler
        # path (OAuth2PasswordBearer raises before our code runs) -- must
        # still come back in our envelope, not FastAPI's default {detail}.
        assert body["success"] is False
        assert "success" in body and "message" in body

    def test_protected_route_with_garbage_token_returns_401(self, client):
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not.a.real.token"}
        )
        assert response.status_code == 401
        assert response.json()["success"] is False

    def test_protected_route_with_expired_token_returns_401(self, client, regular_user):
        user, _ = regular_user
        expired_token = create_access_token(subject=str(user.id), expires_delta=timedelta(seconds=-1))

        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_token_for_deleted_user_is_rejected(self, client, regular_user, db):
        """Proves the design decision in get_current_user: identity is
        re-verified against the DB on every request, not trusted from
        the token alone. A token that was valid at issue time must stop
        working the moment the underlying user is deleted -- it should
        NOT remain valid until natural expiry."""
        user, headers = regular_user

        # sanity check: token works before deletion
        pre_delete = client.get("/api/v1/users/me", headers=headers)
        assert pre_delete.status_code == 200

        db.delete(user)
        db.commit()

        post_delete = client.get("/api/v1/users/me", headers=headers)
        assert post_delete.status_code == 401


class TestRoleBasedAccessControl:
    def test_regular_user_cannot_list_all_users(self, client, regular_user):
        _, headers = regular_user

        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == 403
        body = response.json()
        assert body["success"] is False
        assert "administrator" in body["message"].lower()

    def test_admin_can_list_all_users(self, client, admin_user):
        _, headers = admin_user

        response = client.get("/api/v1/users", headers=headers)

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_role_change_takes_effect_without_new_login(self, client, regular_user, db):
        """The flip side of the deleted-user test: a role UPGRADE must
        also take effect immediately on the existing token, since
        get_current_user always re-reads the current role from the DB.
        """
        user, headers = regular_user

        blocked = client.get("/api/v1/users", headers=headers)
        assert blocked.status_code == 403

        user.role = UserRole.ADMIN
        db.commit()

        allowed = client.get("/api/v1/users", headers=headers)
        assert allowed.status_code == 200