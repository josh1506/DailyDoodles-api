"""Security regression suite from the UPG-001 threat model (docs/upgrade-kit/reports/UPG-001/THREAT_MODEL.md).

* Plain tests guard controls that already hold.
* ``known_gap`` tests are strict xfails: each documents a confirmed weakness (finding ID in the reason).
  When the planned fix lands the test XPASSes, the suite fails, and the marker must be removed,
  so a fix can't merge without its regression test going green.
"""
import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from dailydoodles_api.tasks.models import Task

pytestmark = pytest.mark.django_db
User = get_user_model()
PW = "c0rrect-Horse-battery"
NEW_PW = "n3w-Horse-battery-staple"


def known_gap(finding):
    return pytest.mark.xfail(strict=True, reason=f"{finding}: confirmed gap, fix pending approval")


def make_user(email="victim@example.com", verified=False, **extra):
    user = User.objects.create_user(email=email, password=PW, **extra)
    if verified:
        EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    return user


def jwt_pair(email="victim@example.com", password=PW):
    response = APIClient().post("/api/token", {"email": email, "password": password}, format="json")
    assert response.status_code == 200, response.content
    return response.json()


def refresh(token):
    return APIClient().post("/api/token/refresh", {"refresh": token}, format="json")


def as_user(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


# --------------------------------------------------------------------------------------------
# Controls that hold today
# --------------------------------------------------------------------------------------------


def test_inactive_user_cannot_obtain_tokens():
    make_user(is_active=False)
    response = APIClient().post("/api/token", {"email": "victim@example.com", "password": PW}, format="json")
    assert response.status_code == 401


def test_tokens_of_deactivated_user_cannot_access_api():
    user = make_user()
    access = jwt_pair()["access"]
    user.is_active = False
    user.save()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert client.get("/api/tasks/").status_code in (401, 403)


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_task_owner_cannot_be_reassigned_via_payload(method):
    victim, attacker = make_user(), make_user("attacker@example.com")
    client = as_user(attacker)
    if method == "post":
        client.post("/api/tasks/", {"title": "t", "user": victim.pk}, format="json")
        task = Task.objects.get()
    else:
        task = Task.objects.create(user=attacker, title="t")
        getattr(client, method)(f"/api/tasks/{task.pk}", {"title": "t", "user": victim.pk}, format="json")
        task.refresh_from_db()
    assert task.user == attacker


def test_users_api_is_scoped_to_self():
    me, other = make_user(), make_user("other@example.com", name="Other")
    client = as_user(me)
    listing = client.get("/api/users/").json()
    assert [u["url"].rstrip("/").rsplit("/", 1)[-1] for u in listing] == [str(me.pk)]
    assert client.get(f"/api/users/{other.pk}/").status_code == 404
    assert client.patch(f"/api/users/{other.pk}/", {"name": "pwned"}, format="json").status_code == 404
    other.refresh_from_db()
    assert other.name == "Other"


@pytest.mark.parametrize("path", ["/api/schema/", "/api/docs/"])
def test_api_docs_require_admin(path):
    assert APIClient().get(path).status_code in (401, 403)
    assert as_user(make_user()).get(path).status_code == 403
    assert as_user(make_user("admin@example.com", is_staff=True)).get(path).status_code == 200


def test_django_admin_requires_staff(client):
    make_user(verified=True)
    client.login(email="victim@example.com", password=PW)
    response = client.get("/admin/tasks/task/")
    assert response.status_code == 302 and "/login/" in response["Location"]


def test_password_reset_does_not_reveal_registered_emails(client):
    make_user(verified=True)
    known = client.post("/accounts/password/reset/", {"email": "victim@example.com"})
    unknown = client.post("/accounts/password/reset/", {"email": "nobody@example.com"})
    assert (known.status_code, known.get("Location")) == (unknown.status_code, unknown.get("Location"))


def test_allauth_login_locks_out_after_repeated_failures(client):
    make_user(verified=True)
    for i in range(6):
        response = client.post("/accounts/login/", {"login": "victim@example.com", "password": f"wrong{i}"})
    assert b"Too many failed login attempts" in response.content
    still_locked = client.post("/accounts/login/", {"login": "victim@example.com", "password": PW})
    assert still_locked.status_code == 200  # form re-rendered, not logged in


# --------------------------------------------------------------------------------------------
# Confirmed gaps (strict xfail until the approved fix lands)
# --------------------------------------------------------------------------------------------


@known_gap("F1/H1")
def test_password_change_revokes_existing_refresh_tokens():
    user = make_user()
    stolen = jwt_pair()["refresh"]
    user.set_password(NEW_PW)
    user.save()
    assert refresh(stolen).status_code == 401
    assert jwt_pair(password=NEW_PW)["refresh"]  # fresh sign-in still works


@known_gap("F1/H2")
def test_deactivation_revokes_existing_refresh_tokens():
    user = make_user()
    stolen = jwt_pair()["refresh"]
    user.is_active = False
    user.save()
    assert refresh(stolen).status_code == 401


def test_password_change_does_not_revoke_other_users_tokens():
    # Guard for F1: revocation must be per user. Holds today (nothing is revoked) and must keep holding.
    victim, bystander = make_user(), make_user("bystander@example.com")
    bystander_refresh = jwt_pair("bystander@example.com")["refresh"]
    victim.set_password(NEW_PW)
    victim.save()
    assert refresh(bystander_refresh).status_code == 200


@known_gap("F2/H6")
def test_admin_login_is_rate_limited(client):
    make_user(verified=True, is_staff=True, is_superuser=True)
    for i in range(10):
        client.post("/admin/login/", {"username": "victim@example.com", "password": f"wrong{i}"})
    client.post("/admin/login/?next=/admin/", {"username": "victim@example.com", "password": PW})
    assert client.get("/admin/").status_code != 200


@known_gap("F3/H18")
def test_legacy_non_expiring_token_endpoint_removed():
    make_user()
    response = APIClient().post("/auth-token/", {"username": "victim@example.com", "password": PW})
    assert response.status_code == 404


@known_gap("F4a/H4")
def test_register_rejects_case_variant_of_existing_email():
    make_user()
    response = APIClient().post(
        "/api/register", {"email": "Victim@EXAMPLE.com", "password": PW, "password2": PW}, format="json"
    )
    assert response.status_code == 400
    assert User.objects.filter(email__iexact="victim@example.com").count() == 1


@known_gap("F4b/H3+S2")
def test_register_requires_email_verification_before_api_access():
    APIClient().post("/api/register", {"email": "new@example.com", "password": PW, "password2": PW}, format="json")
    response = APIClient().post("/api/token", {"email": "new@example.com", "password": PW}, format="json")
    assert response.status_code in (400, 401, 403)


@known_gap("F5/H5")
def test_user_detail_page_hidden_from_other_users(client):
    victim = make_user(name="Victim Name")
    make_user("attacker@example.com", verified=True)
    client.login(email="attacker@example.com", password=PW)
    assert client.get(f"/users/{victim.pk}/").status_code == 404


@known_gap("F6/H8")
def test_task_description_size_is_bounded():
    response = as_user(make_user()).post(
        "/api/tasks/", {"title": "t", "description": "x" * (1024 * 1024)}, format="json"
    )
    assert response.status_code == 400
