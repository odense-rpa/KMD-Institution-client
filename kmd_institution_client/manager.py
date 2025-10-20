from .client import KMDInstitutionClient
from .functionality.bruger import BrugerClient
from .functionality.institutioner_og_grupper import InstitutionerOgGrupperClient
from .functionality.indmeldelser import IndmeldelserClient

class KMDInstitutionClientManager:

    def __init__(self, idp: str, username: str, password: str) -> None:
        self._client = KMDInstitutionClient(idp, username, password)
        self._bruger = BrugerClient(self._client)
        
        # Brugerid skal til tider bruges i stringen til api kald, derfor skal brugerclient instantieres efter login for at sikre vi har id'et
        self._brugerid = self._bruger.brugerid
        self._institutioner_og_grupper = InstitutionerOgGrupperClient(self._client, self._brugerid)
        self._indmeldelser = IndmeldelserClient(self._client, self._brugerid)

    @property
    def client(self) -> KMDInstitutionClient:
        """Get the base KMD Institution client."""
        return self._client
    
    @property
    def bruger(self) -> BrugerClient:
        """Get the Bruger client for user-related operations."""
        return self._bruger
    
    @property
    def institutioner_og_grupper(self) -> InstitutionerOgGrupperClient:
        """Get the Institutioner og Grupper client."""
        return self._institutioner_og_grupper

    @property
    def indmeldelser(self) -> IndmeldelserClient:
        """Get the Indmeldelser client."""
        return self._indmeldelser

