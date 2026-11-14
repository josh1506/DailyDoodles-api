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
# Fixed gaps (F1, F2, F4a, F5, F6) and remaining ones (strict xfail until their fix is approved)
# --------------------------------------------------------------------------------------------


def test_password_change_revokes_existing_refresh_tokens():
    user = make_user()
    stolen = jwt_pair()["refresh"]
    user.set_password(NEW_PW)
    user.save()
    assert refresh(stolen).status_code == 401
    assert jwt_pair(password=NEW_PW)["refresh"]  # fresh sign-in still works


def test_deactivation_revokes_existing_refresh_tokens():
    user = make_user()
    stolen = jwt_pair()["refresh"]
    user.is_active = False
    user.save()
    assert refresh(stolen).status_code == 401


def test_password_change_revokes_existing_access_tokens():
    user = make_user()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {jwt_pair()['access']}")
    assert client.get("/api/tasks/").status_code == 200
    user.set_password(NEW_PW)
    user.save()
    response = client.get("/api/tasks/")
    assert response.status_code in (401, 403)
    assert response.json()["code"] == "token_not_valid"  # the SPA treats this as "refresh, else sign out"


def test_password_change_revokes_rotated_refresh_tokens():
    # simplejwt 5.3 doesn't track rotated refresh tokens as outstanding, so bulk blacklisting would miss them.
    user = make_user()
    rotated = refresh(jwt_pair()["refresh"]).json()["refresh"]
    user.set_password(NEW_PW)
    user.save()
    assert refresh(rotated).status_code == 401


def test_unchanged_account_keeps_working_through_rotation():
    make_user()
    token = jwt_pair()["refresh"]
    for _ in range(3):
        response = refresh(token)
        assert response.status_code == 200
        token = response.json()["refresh"]
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
    assert client.get("/api/tasks/").status_code == 200


def legacy_tokens(user):
    # Shape of tokens issued before session binding: no "sah" claim.
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user)
    token["email"] = user.email
    return token


def test_tokens_without_session_claim_rejected_by_default():
    token = legacy_tokens(make_user())
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    assert client.get("/api/tasks/").status_code in (401, 403)
    assert refresh(str(token)).status_code == 401


def test_transition_flag_accepts_tokens_without_session_claim(settings):
    settings.JWT_REQUIRE_SESSION_CLAIM = False
    token = legacy_tokens(make_user())
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    assert client.get("/api/tasks/").status_code == 200
    assert refresh(str(token)).status_code == 200


def test_password_change_does_not_revoke_other_users_tokens():
    # F1 revocation is per user.
    victim = make_user()
    make_user("bystander@example.com")
    bystander_refresh = jwt_pair("bystander@example.com")["refresh"]
    victim.set_password(NEW_PW)
    victim.save()
    assert refresh(bystander_refresh).status_code == 200


def test_production_routes_admin_login_through_allauth(monkeypatch):
    # F2 is a production default; import the production settings module in isolation to check it.
    import importlib
    import sys

    for key, value in {
        "DJANGO_SECRET_KEY": "test-only-not-a-secret",
        "DJANGO_ADMIN_URL": "admin/",
        "REDIS_URL": "redis://127.0.0.1:1/0",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("DJANGO_ADMIN_FORCE_ALLAUTH", raising=False)
    sys.modules.pop("config.settings.production", None)
    production = importlib.import_module("config.settings.production")
    sys.modules.pop("config.settings.production", None)
    assert production.DJANGO_ADMIN_FORCE_ALLAUTH is True


def test_forced_allauth_admin_login_redirects_to_allauth(rf):
    # The DJANGO_ADMIN_FORCE_ALLAUTH mechanism (users/admin.py) sends anonymous admin sign-in to
    # allauth's login, whose lockout is covered by test_allauth_login_locks_out_after_repeated_failures.
    # (Admin URLs are bound at import, so this checks the wrapped view directly.)
    from django.contrib import admin
    from django.contrib.auth.decorators import login_required
    from django.contrib.auth.models import AnonymousUser

    request = rf.get("/admin/login/")
    request.user = AnonymousUser()
    response = login_required(admin.site.login)(request)
    assert response.status_code == 302 and response["Location"].startswith("/accounts/login/")


@known_gap("F3/H18")
def test_legacy_non_expiring_token_endpoint_removed():
    make_user()
    response = APIClient().post("/auth-token/", {"username": "victim@example.com", "password": PW})
    assert response.status_code == 404


def test_register_rejects_case_variant_of_existing_email():
    make_user()
    response = APIClient().post(
        "/api/register", {"email": "Victim@EXAMPLE.com", "password": PW, "password2": PW}, format="json"
    )
    assert response.status_code == 400
    assert response.json() == {"email": ["user with this email address already exists."]}  # same shape as before
    assert User.objects.filter(email__iexact="victim@example.com").count() == 1


def test_register_normalises_email_domain():
    response = APIClient().post(
        "/api/register", {"email": "new@EXAMPLE.com", "password": PW, "password2": PW}, format="json"
    )
    assert response.status_code == 201
    assert User.objects.get().email == "new@example.com"


@known_gap("F4b/H3+S2")
def test_register_requires_email_verification_before_api_access():
    APIClient().post("/api/register", {"email": "new@example.com", "password": PW, "password2": PW}, format="json")
    response = APIClient().post("/api/token", {"email": "new@example.com", "password": PW}, format="json")
    assert response.status_code in (400, 401, 403)


def test_user_detail_page_hidden_from_other_users(client):
    victim = make_user(name="Victim Name")
    make_user("attacker@example.com", verified=True)
    client.login(email="attacker@example.com", password=PW)
    assert client.get(f"/users/{victim.pk}/").status_code == 404


def test_user_detail_page_still_shows_own_page(client):
    me = make_user("me@example.com", verified=True, name="Me")
    client.login(email="me@example.com", password=PW)
    response = client.get(f"/users/{me.pk}/")
    assert response.status_code == 200 and b"Me" in response.content


def test_task_description_size_is_bounded():
    response = as_user(make_user()).post(
        "/api/tasks/", {"title": "t", "description": "x" * (1024 * 1024)}, format="json"
    )
    assert response.status_code == 400
    assert "description" in response.json()


def test_task_description_at_limit_and_null_still_accepted():
    client = as_user(make_user())
    assert client.post("/api/tasks/", {"title": "t", "description": "x" * 10_000}, format="json").status_code == 201
    assert client.post("/api/tasks/", {"title": "t", "description": None}, format="json").status_code == 201
    assert client.post("/api/tasks/", {"title": "t"}, format="json").status_code == 201
