import pytest
from django.urls import reverse


@pytest.mark.parametrize("model", ["task", "tasklist"])
def test_admin_search_does_not_crash(admin_client, model):
    response = admin_client.get(reverse(f"admin:tasks_{model}_changelist"), {"q": "example"})
    assert response.status_code == 200
