import os

import pytest
from dotenv import load_dotenv

from kmd_institution_client import KMDInstitutionClientManager

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session")
def kmd_institution_manager():
    """Én indlogget manager for hele testkørslen // One login per test run."""
    manglende = [
        navn for navn in ("KMD_IDP", "KMD_USERNAME", "KMD_PASSWORD") if not os.getenv(navn)
    ]
    if manglende:
        pytest.skip(f"Mangler i .env: {', '.join(manglende)}")

    # Headless styres af KMD_HEADLESS (standard true); sæt KMD_HEADLESS=false for at se browseren
    manager = KMDInstitutionClientManager.fra_env()
    assert manager.client.cookies, "Ingen session-cookies efter login"
    yield manager
    manager.close()
