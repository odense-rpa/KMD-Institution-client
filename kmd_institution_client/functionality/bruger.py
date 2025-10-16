from kmd_institution_client.client import KMDInstitutionClient

class BrugerClient:
    def __init__(self, kmd_institution_client: KMDInstitutionClient) -> None:
        self.client = kmd_institution_client
    
    def hent_egen_bruger(self):
        endpoint = "/api/municipalities/461"
        respone = self.client.get(endpoint)

        if respone.status_code != 200:
            raise ValueError(f"Kunne ikke hente egen bruger fejl {respone.status_code}")

        return respone.json()