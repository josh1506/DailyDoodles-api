"""Regression + abuse-protection tests for the SPA auth endpoints (UPG-001 S3/S4)."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import AccessToken

pytestmark = pytest.mark.django_db
User = get_user_model()
PASSWORD = "c0rrect-Horse-battery"


@pytest.fixture
def account():
    return User.objects.create_user(email="owner@example.com", password=PASSWORD)


@pytest.fixture
def low_auth_rate(monkeypatch):
    # DRF binds THROTTLE_RATES at import time, so patch the class attribute.
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"auth": "3/minute"})


def login(client, password=PASSWORD):
    return client.post("/api/token", {"email": "owner@example.com", "password": password}, format="json")


def test_register_creates_hashed_user():
    response = APIClient().post(
        "/api/register", {"email": "new@example.com", "password": PASSWORD, "password2": PASSWORD}, format="json"
    )

    assert response.status_code == 201
    assert response.json() == {"email": "new@example.com"}
    user = User.objects.get(email="new@example.com")
    assert user.check_password(PASSWORD) and user.password != PASSWORD


def test_register_rejects_mismatch_and_weak_passwords():
    client = APIClient()
    mismatch = client.post(
        "/api/register", {"email": "a@example.com", "password": PASSWORD, "password2": "x" + PASSWORD}, format="json"
    )
    weak_payload = {"email": "b@example.com", "password": "123", "password2": "123"}
    weak = client.post("/api/register", weak_payload, format="json")

    assert mismatch.status_code == 400 and "password" in mismatch.json()
    assert weak.status_code == 400 and "password" in weak.json()


def test_login_returns_tokens_with_email_claim(account):
    response = login(APIClient())

    assert response.status_code == 200
    assert AccessToken(response.json()["access"])["email"] == account.email


def test_wrong_password_rejected(account):
    assert login(APIClient(), "wrong").status_code == 401


def test_login_is_throttled(account, low_auth_rate):
    client = APIClient()
    codes = [login(client, "wrong").status_code for _ in range(4)]

    assert codes == [401, 401, 401, 429]
    assert login(client).status_code == 429  # even the right password waits out the window


def test_register_is_throttled(low_auth_rate):
    client = APIClient()
    codes = [client.post("/api/register", {}, format="json").status_code for _ in range(4)]

    assert codes[-1] == 429


def test_legacy_auth_token_endpoint_is_throttled(account, low_auth_rate):
    client = APIClient()
    codes = [
        client.post("/auth-token/", {"username": account.email, "password": "wrong"}).status_code for _ in range(4)
    ]

    assert codes[-1] == 429


def test_refresh_is_not_limited_by_auth_scope(account, low_auth_rate):
    client = APIClient()
    refresh = login(client).json()["refresh"]
    for _ in range(4):
        response = client.post("/api/token/refresh", {"refresh": refresh}, format="json")
        assert response.status_code == 200
        refresh = response.json()["refresh"]  # ROTATE_REFRESH_TOKENS


def test_blacklisted_refresh_token_cannot_be_reused(account):
    client = APIClient()
    refresh = login(client).json()["refresh"]

    assert client.post("/api/token/blacklist", {"refresh": refresh}, format="json").status_code == 200
    assert client.post("/api/token/refresh", {"refresh": refresh}, format="json").status_code == 401
