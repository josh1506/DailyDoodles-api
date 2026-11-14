import pytest

from dailydoodles_api.users.models import User
from dailydoodles_api.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache

    cache.clear()


@pytest.fixture
def user(db) -> User:
    return UserFactory()
