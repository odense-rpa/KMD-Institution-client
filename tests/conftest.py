import pytest
import os
from dotenv import load_dotenv
from kmd_institution_client import KMDInstitutionClientManager

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def kmd_institution_manager() -> KMDInstitutionClientManager:
    idp = os.getenv("IDP") or ""
    
    assert idp

    manager = KMDInstitutionClientManager(idp=idp)
    assert manager._client.cookies  # Check the actual cookies property
    return manager

