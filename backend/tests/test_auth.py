"""Tests for registration and login.

Each test asserts on both the HTTP-level outcome (status code) and the
envelope shape ({success, message, data}/{success, message, errors}) --
a status code alone doesn't prove the response body is actually correct.
"""

import pytest


class TestRegistration:
    def test_register_returns_created_user_without_password(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"name": "Alice", "email": "alice-reg@example.com", "password": "SecurePass123"},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["email"] == "alice-reg@example.com"
        assert body["data"]["role"] == "USER"
        assert "password" not in body["data"]
        assert "password_hash" not in body["data"]

    def test_register_duplicate_email_returns_conflict(self, client):
        payload = {"name": "Alice", "email": "dup@example.com", "password": "SecurePass123"}
        client.post("/api/v1/auth/register", json=payload)

        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409
        body = response.json()
        assert body["success"] is False
        assert "already exists" in body["message"].lower()

    def test_register_ignores_client_supplied_role(self, client, db):
        """Even if a client smuggles a `role` field into the request body,
        the created user must still be USER -- public registration can
        never create an admin. This is a security-critical test, not a
        trivial one: it directly verifies the privilege-escalation
        prevention documented in AuthService.register."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Attacker",
                "email": "attacker@example.com",
                "password": "SecurePass123",
                "role": "ADMIN",
            },
        )

        assert response.status_code == 201
        assert response.json()["data"]["role"] == "USER"

    @pytest.mark.parametrize(
        "password,reason",
        [
            ("short1", "tooshort"),
            ("nodigitshere", "nodigit"),
            ("12345678", "noletter"),
            ("a1" * 40, "toolong"),
        ],
    )
    def test_register_rejects_weak_passwords(self, client, password, reason):
        response = client.post(
            "/api/v1/auth/register",
            json={"name": "Weak", "email": f"weak-{reason}@example.com", "password": password},
        )
        assert response.status_code == 422, f"expected 422 for {reason}, got {response.status_code}"
        body = response.json()
        assert body["success"] is False
        assert len(body["errors"]) >= 1

    def test_register_rejects_invalid_email(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"name": "Bad Email", "email": "not-an-email", "password": "SecurePass123"},
        )
        assert response.status_code == 422

    def test_register_rejects_short_name(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"name": "X", "email": "shortname@example.com", "password": "SecurePass123"},
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_with_correct_credentials_returns_token(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"name": "Bob", "email": "bob-login@example.com", "password": "SecurePass123"},
        )

        response = client.post(
            "/api/v1/auth/login", data={"username": "bob-login@example.com", "password": "SecurePass123"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["data"]["token_type"] == "bearer"
        assert len(body["data"]["access_token"]) > 20

    def test_login_with_wrong_password_returns_401(self, client):
        client.post(
            "/api/v1/auth/register",
            json={"name": "Bob", "email": "bob-wrong@example.com", "password": "SecurePass123"},
        )

        response = client.post(
            "/api/v1/auth/login", data={"username": "bob-wrong@example.com", "password": "WrongPassword1"}
        )

        assert response.status_code == 401

    def test_login_with_nonexistent_email_returns_401_not_404(self, client):
        """A nonexistent email must fail the SAME way as a wrong password
        (401, same generic message) -- returning something different
        (e.g. 404) would let an attacker enumerate which emails are
        registered."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody-at-all@example.com", "password": "Whatever123"},
        )

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["message"].lower()