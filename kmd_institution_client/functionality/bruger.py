from kmd_institution_client.client import KMDInstitutionClient

class BrugerClient:
    def __init__(self, kmd_institution_client: KMDInstitutionClient) -> None:
        self.client = kmd_institution_client
        # Fetch user info during initialization
        self._bruger_data = self.hent_egen_bruger()
        
    @property
    def brugerid(self) -> str | None:
        """Get the current user's ID."""
        if self._bruger_data:
            # Try common ID field names
            return (self._bruger_data["id"])
        return None
    
    
    def hent_egen_bruger(self):
        endpoint = "/api/municipalities/461"
        response = self.client.get(endpoint)

        return response.json()