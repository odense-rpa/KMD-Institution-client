from .client import KMDInstitutionClient

class KMDInstitutionClientManager:

    def __init__(
            self, 
            idp: str
    ) -> None:                
        # Initialize client - this will block until login completes (10-35 seconds)
        self._client = KMDInstitutionClient(idp=idp)

    @property
    def client(self) -> KMDInstitutionClient:
        """Get the base KMD Institution client."""
        return self._client

