import pytest
from kmd_institution_client import KMDInstitutionClientManager


def test_cookies_login(kmd_institution_manager: KMDInstitutionClientManager):
    """Test that login works and cookies are set."""
    client = kmd_institution_manager.client
    assert client.cookies is not None
    assert isinstance(client.cookies, dict)
    assert len(client.cookies) > 0

def test_hent_brugerid_ved_login(kmd_institution_manager: KMDInstitutionClientManager):
    brugerid = kmd_institution_manager.user_id

    assert brugerid is not None