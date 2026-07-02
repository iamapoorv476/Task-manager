"""Tests for task CRUD, ownership enforcement, and list features
(pagination, filtering, search, sorting).
"""


class TestTaskCreation:
    def test_create_task_requires_authentication(self, client):
        response = client.post("/api/v1/tasks", json={"title": "Unauthenticated task"})
        assert response.status_code == 401

    def test_create_task_success(self, client, regular_user):
        _, headers = regular_user

        response = client.post(
            "/api/v1/tasks",
            json={"title": "Write project docs", "description": "Cover setup and deploy", "priority": "HIGH"},
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"] == "TODO"  # every new task starts as TODO
        assert data["priority"] == "HIGH"

    def test_create_task_assigns_current_user_as_owner(self, client, regular_user):
        user, headers = regular_user

        response = client.post("/api/v1/tasks", json={"title": "Ownership check task"}, headers=headers)

        assert response.json()["data"]["owner_id"] == str(user.id)

    def test_create_task_rejects_short_title(self, client, regular_user):
        _, headers = regular_user
        response = client.post("/api/v1/tasks", json={"title": "ab"}, headers=headers)
        assert response.status_code == 422


class TestTaskOwnership:
    """The security-critical suite: users must never be able to read,
    modify, or delete tasks belonging to another user."""

    def test_user_cannot_get_another_users_task(self, client, regular_user, make_user):
        _, owner_headers = regular_user
        _, other_headers = make_user()

        created = client.post("/api/v1/tasks", json={"title": "Owner's private task"}, headers=owner_headers)
        task_id = created.json()["data"]["id"]

        response = client.get(f"/api/v1/tasks/{task_id}", headers=other_headers)

        # 404, not 403 -- must not confirm the task's existence to a
        # non-owner (see TaskService._ensure_access docstring).
        assert response.status_code == 404

    def test_user_cannot_update_another_users_task(self, client, regular_user, make_user):
        _, owner_headers = regular_user
        _, other_headers = make_user()

        created = client.post("/api/v1/tasks", json={"title": "Owner's task"}, headers=owner_headers)
        task_id = created.json()["data"]["id"]

        response = client.patch(
            f"/api/v1/tasks/{task_id}", json={"status": "DONE"}, headers=other_headers
        )

        assert response.status_code == 404

    def test_user_cannot_delete_another_users_task(self, client, regular_user, make_user):
        _, owner_headers = regular_user
        _, other_headers = make_user()

        created = client.post("/api/v1/tasks", json={"title": "Owner's task"}, headers=owner_headers)
        task_id = created.json()["data"]["id"]

        response = client.delete(f"/api/v1/tasks/{task_id}", headers=other_headers)

        assert response.status_code == 404
        # confirm it's genuinely NOT deleted, not just blocked
        still_there = client.get(f"/api/v1/tasks/{task_id}", headers=owner_headers)
        assert still_there.status_code == 200

    def test_list_tasks_is_scoped_to_owner(self, client, regular_user, make_user):
        _, alice_headers = regular_user
        _, bob_headers = make_user()

        client.post("/api/v1/tasks", json={"title": "Alice task 1"}, headers=alice_headers)
        client.post("/api/v1/tasks", json={"title": "Alice task 2"}, headers=alice_headers)
        client.post("/api/v1/tasks", json={"title": "Bob task 1"}, headers=bob_headers)

        alice_list = client.get("/api/v1/tasks", headers=alice_headers)
        bob_list = client.get("/api/v1/tasks", headers=bob_headers)

        assert alice_list.json()["meta"]["total_items"] == 2
        assert bob_list.json()["meta"]["total_items"] == 1

    def test_admin_can_access_any_users_task(self, client, admin_user, make_user):
        _, admin_headers = admin_user
        _, user_headers = make_user()

        created = client.post("/api/v1/tasks", json={"title": "Regular user's task"}, headers=user_headers)
        task_id = created.json()["data"]["id"]

        response = client.get(f"/api/v1/tasks/{task_id}", headers=admin_headers)
        assert response.status_code == 200

    def test_admin_can_delete_any_users_task(self, client, admin_user, make_user):
        _, admin_headers = admin_user
        _, user_headers = make_user()

        created = client.post("/api/v1/tasks", json={"title": "To be deleted by admin"}, headers=user_headers)
        task_id = created.json()["data"]["id"]

        response = client.delete(f"/api/v1/tasks/{task_id}", headers=admin_headers)
        assert response.status_code == 204

        confirm = client.get(f"/api/v1/tasks/{task_id}", headers=user_headers)
        assert confirm.status_code == 404

    def test_admin_list_includes_all_users_tasks(self, client, admin_user, make_user):
        _, admin_headers = admin_user
        _, alice_headers = make_user()
        _, bob_headers = make_user()

        client.post("/api/v1/tasks", json={"title": "Alice's"}, headers=alice_headers)
        client.post("/api/v1/tasks", json={"title": "Bob's"}, headers=bob_headers)

        response = client.get("/api/v1/tasks", headers=admin_headers)
        assert response.json()["meta"]["total_items"] == 2


class TestTaskUpdate:
    def test_partial_update_only_changes_specified_fields(self, client, regular_user):
        _, headers = regular_user
        created = client.post(
            "/api/v1/tasks",
            json={"title": "Original title", "description": "Original description", "priority": "LOW"},
            headers=headers,
        )
        task_id = created.json()["data"]["id"]

        response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "IN_PROGRESS"}, headers=headers)

        data = response.json()["data"]
        assert data["status"] == "IN_PROGRESS"
        assert data["title"] == "Original title"
        assert data["description"] == "Original description"
        assert data["priority"] == "LOW"

    def test_update_nonexistent_task_returns_404(self, client, regular_user):
        _, headers = regular_user
        response = client.patch(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            json={"status": "DONE"},
            headers=headers,
        )
        assert response.status_code == 404


class TestTaskListFeatures:
    def _seed(self, client, headers):
        client.post(
            "/api/v1/tasks",
            json={"title": "Alpha task", "description": "first one", "priority": "LOW"},
            headers=headers,
        )
        client.post(
            "/api/v1/tasks",
            json={"title": "Beta task", "description": "contains keyword banana", "priority": "HIGH"},
            headers=headers,
        )
        client.post(
            "/api/v1/tasks",
            json={"title": "Gamma task", "description": "third", "priority": "MEDIUM"},
            headers=headers,
        )

    def test_filter_by_status(self, client, regular_user):
        _, headers = regular_user
        self._seed(client, headers)
        first = client.get("/api/v1/tasks", headers=headers).json()["data"][0]
        client.patch(f"/api/v1/tasks/{first['id']}", json={"status": "DONE"}, headers=headers)

        response = client.get("/api/v1/tasks?status=DONE", headers=headers)
        assert response.json()["meta"]["total_items"] == 1

    def test_filter_by_priority(self, client, regular_user):
        _, headers = regular_user
        self._seed(client, headers)

        response = client.get("/api/v1/tasks?priority=HIGH", headers=headers)
        body = response.json()
        assert body["meta"]["total_items"] == 1
        assert body["data"][0]["title"] == "Beta task"

    def test_search_matches_title_and_description(self, client, regular_user):
        _, headers = regular_user
        self._seed(client, headers)

        response = client.get("/api/v1/tasks?search=banana", headers=headers)
        body = response.json()
        assert body["meta"]["total_items"] == 1
        assert body["data"][0]["title"] == "Beta task"

    def test_sort_by_title_ascending(self, client, regular_user):
        _, headers = regular_user
        self._seed(client, headers)

        response = client.get("/api/v1/tasks?sort_by=title&sort_order=asc", headers=headers)
        titles = [t["title"] for t in response.json()["data"]]
        assert titles == ["Alpha task", "Beta task", "Gamma task"]

    def test_pagination_returns_correct_page_and_metadata(self, client, regular_user):
        _, headers = regular_user
        self._seed(client, headers)

        page1 = client.get("/api/v1/tasks?page=1&limit=2", headers=headers).json()
        page2 = client.get("/api/v1/tasks?page=2&limit=2", headers=headers).json()

        assert len(page1["data"]) == 2
        assert len(page2["data"]) == 1
        assert page1["meta"]["total_items"] == 3
        assert page1["meta"]["total_pages"] == 2

    def test_sort_by_field_not_in_whitelist_is_rejected(self, client, regular_user):
        """sort_by is a Literal type restricted to real, safe columns --
        an out-of-whitelist value must fail request validation (422),
        never reach query construction."""
        _, headers = regular_user
        response = client.get("/api/v1/tasks?sort_by=owner_id", headers=headers)
        assert response.status_code == 422