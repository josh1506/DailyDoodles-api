"""Object-level authorization and contract tests for the tasks API (UPG-001 S1/S5)."""
import pytest
from rest_framework.test import APIClient

from dailydoodles_api.tasks.models import Task, TaskList
from dailydoodles_api.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

TASKS = "/api/tasks/"
LISTS = "/api/tasks/lists"


@pytest.fixture
def alice():
    return UserFactory()


@pytest.fixture
def bob():
    return UserFactory()


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_anonymous_is_rejected():
    # Existing contract: SessionAuthentication is first in DEFAULT_AUTHENTICATION_CLASSES, so DRF answers 403.
    assert APIClient().get(TASKS).status_code == 403


def test_list_returns_only_own_tasks_in_creation_order(alice, bob):
    first = Task.objects.create(user=alice, title="first")
    second = Task.objects.create(user=alice, title="second")
    Task.objects.create(user=bob, title="bob's")
    # Touch the first row so Postgres may move it physically; order must stay stable.
    Task.objects.filter(pk=first.pk).update(is_completed=True)

    response = client_for(alice).get(TASKS)

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [first.pk, second.pk]


def test_create_keeps_existing_contract(alice):
    response = client_for(alice).post(TASKS, {"title": "new"}, format="json")

    assert response.status_code == 201
    assert set(response.json()) == {"id", "title", "description", "task_list", "is_completed", "due_date"}
    assert Task.objects.get(pk=response.json()["id"]).user == alice


def test_create_into_own_list_allowed(alice):
    own_list = TaskList.objects.create(user=alice, title="mine")

    response = client_for(alice).post(TASKS, {"title": "x", "task_list": own_list.pk}, format="json")

    assert response.status_code == 201


def test_cannot_create_task_in_another_users_list(alice, bob):
    bobs_list = TaskList.objects.create(user=bob, title="private")

    response = client_for(alice).post(TASKS, {"title": "injected", "task_list": bobs_list.pk}, format="json")

    assert response.status_code == 400
    assert not bobs_list.tasks.exists()


def test_foreign_list_error_is_indistinguishable_from_missing_list(alice, bob):
    bobs_list = TaskList.objects.create(user=bob, title="private")
    client = client_for(alice)

    foreign = client.post(TASKS, {"title": "x", "task_list": bobs_list.pk}, format="json")
    missing = client.post(TASKS, {"title": "x", "task_list": 999999}, format="json")

    assert foreign.status_code == missing.status_code == 400
    assert foreign.json()["task_list"] == [m.replace("999999", str(bobs_list.pk)) for m in missing.json()["task_list"]]


def test_cannot_move_own_task_into_another_users_list(alice, bob):
    task = Task.objects.create(user=alice, title="mine")
    bobs_list = TaskList.objects.create(user=bob, title="private")

    response = client_for(alice).put(
        f"{TASKS}{task.pk}", {"title": "mine", "task_list": bobs_list.pk}, format="json"
    )

    assert response.status_code == 400
    task.refresh_from_db()
    assert task.task_list is None


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_other_users_task_is_not_found(alice, bob, method):
    bobs_task = Task.objects.create(user=bob, title="secret")

    response = getattr(client_for(alice), method)(f"{TASKS}{bobs_task.pk}", {"title": "pwned"}, format="json")

    assert response.status_code == 404
    bobs_task.refresh_from_db()
    assert bobs_task.title == "secret"


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_other_users_tasklist_is_not_found(alice, bob, method):
    bobs_list = TaskList.objects.create(user=bob, title="secret")

    response = getattr(client_for(alice), method)(f"{LISTS}/{bobs_list.pk}", {"title": "pwned"}, format="json")

    assert response.status_code == 404
    assert TaskList.objects.filter(pk=bobs_list.pk, title="secret").exists()


def test_owner_update_toggle_and_delete(alice):
    task = Task.objects.create(user=alice, title="t")
    client = client_for(alice)

    updated = client.put(
        f"{TASKS}{task.pk}",
        {"id": task.pk, "title": "t2", "description": "d", "is_completed": True, "due_date": "2026-01-02"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["is_completed"] is True
    assert updated.json()["due_date"] == "2026-01-02"

    assert client.delete(f"{TASKS}{task.pk}").status_code == 204
    assert not Task.objects.filter(pk=task.pk).exists()


def test_preexisting_foreign_task_hidden_from_list_owner(alice, bob):
    # Simulates a row injected before the S1 fix: bob's task filed under alice's list.
    alices_list = TaskList.objects.create(user=alice, title="mine")
    Task.objects.create(user=alice, title="own", task_list=alices_list)
    Task.objects.create(user=bob, title="injected", task_list=alices_list)
    client = client_for(alice)

    detail = client.get(f"{LISTS}/{alices_list.pk}").json()
    listing = client.get(LISTS).json()

    assert [t["title"] for t in detail["tasks"]] == ["own"]
    assert [t["title"] for t in listing[0]["tasks"]] == ["own"]
