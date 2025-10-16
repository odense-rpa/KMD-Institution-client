from kmd_institution_client.client import KMDInstitutionClient
from typing import Optional

class InstitutionerOgGrupperClient:
    def __init__(self, kmd_client: KMDInstitutionClient, brugerid: str | None) -> None:
        self.client = kmd_client
        self.brugerid = brugerid
    
    def hent_institutioner(self) -> dict:
        if not self.brugerid:
            raise ValueError("User ID is required but not available")
            
        endpoint = f"api/municipalities/{self.brugerid}/institutions/search/simple?"
        response = self.client.get(endpoint)
        
        if response.status_code != 200:
            raise ValueError(f"Could not fetch institutions, status code: {response.status_code}")
            
        return response.json()
    
    def hent_institution(self, institutionsnavn: str) -> Optional[dict]:
        """
        Find a specific institution by name.
        
        :param institutionsnavn: The name of the institution to find
        :return: The institution dict if found, None otherwise
        """
        institutioner = self.hent_institutioner()
        return next((inst for inst in institutioner if inst["name"] == institutionsnavn), None)

        