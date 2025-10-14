import pytest
from kmd_institution_client import KMDInstitutionClientManager


def test_login(kmd_institution_manager: KMDInstitutionClientManager):
    """Test that login works and cookies are set."""
    client = kmd_institution_manager.client
    assert client.cookies is not None
    assert isinstance(client.cookies, dict)
    assert len(client.cookies) > 0