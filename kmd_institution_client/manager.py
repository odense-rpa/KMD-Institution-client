import os
from types import TracebackType
from typing import Any, Self

from .client import KMDInstitutionClient
from .functionality.bruger import BrugerClient
from .functionality.indmeldelser import IndmeldelserClient
from .functionality.institutioner_og_grupper import InstitutionerOgGrupperClient


class KMDInstitutionClientManager:
    bruger: BrugerClient
    institutioner_og_grupper: InstitutionerOgGrupperClient
    indmeldelser: IndmeldelserClient

    def __init__(self, idp: str, username: str, password: str, **client_kwargs: Any) -> None:
        # Initialize client - this blocks until login completes
        self._client = KMDInstitutionClient(idp, username, password, **client_kwargs)
        self.bruger = BrugerClient(self._client)

        # Brugerid skal til tider bruges i stringen til api kald, derfor skal brugerclient instantieres efter login for at sikre vi har id'et
        self._brugerid = self.bruger.brugerid
        self.institutioner_og_grupper = InstitutionerOgGrupperClient(self._client, self._brugerid)
        self.indmeldelser = IndmeldelserClient(self._client, self._brugerid)

    @classmethod
    def fra_env(cls, **client_kwargs: Any) -> Self:
        """
        Opret manager ud fra miljøvariabler: KMD_IDP, KMD_USERNAME, KMD_PASSWORD og KMD_HEADLESS.
        Headless er standard; KMD_HEADLESS=false giver synlig browser. Et eksplicit
        ``headless``-argument vinder over miljøvariablen.

        Indlæser ikke selv .env - brug fx python-dotenv's load_dotenv() først.
        """
        idp = os.getenv("KMD_IDP", "")
        username = os.getenv("KMD_USERNAME", "")
        password = os.getenv("KMD_PASSWORD", "")
        headless = os.getenv("KMD_HEADLESS", "true").strip().lower() not in ("0", "false", "no")
        client_kwargs.setdefault("headless", headless)
        return cls(idp, username, password, **client_kwargs)

    @property
    def client(self) -> KMDInstitutionClient:
        """Get the base KMD Institution client."""
        return self._client

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
