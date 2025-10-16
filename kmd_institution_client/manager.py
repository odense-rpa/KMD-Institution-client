from .client import KMDInstitutionClient
from .functionality.bruger import BrugerClient

class KMDInstitutionClientManager:

    def __init__(
            self, 
            idp: str,
            username: str,
            password: str
    ) -> None:                
        self._client = KMDInstitutionClient(idp=idp, username=username, password=password)
        self._bruger = BrugerClient(self._client)

    @property
    def client(self) -> KMDInstitutionClient:
        """Get the base KMD Institution client."""
        return self._client
    
    @property
    def bruger(self) -> BrugerClient:
        """Get the Bruger client for user-related operations."""
        return self._bruger
    
    @property
    def user_id(self) -> str | None:
        """Get the current user's ID."""
        return self._bruger.user_id

