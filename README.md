# KMD Institution Client

Python-klient til KMD Institution (`institution.kmd.dk`). Bruger Playwright til browser-baseret login og httpx til efterfølgende API-kald.

> Denne klient er ikke officielt støttet eller godkendt af KMD. Brug på eget ansvar.

## Nuværende funktionalitet

- Login via kommunens IdP
- Hent og søg institutioner
- Søg indmeldelser pr. institution og dato

## Installation

```bash
uv add git+https://github.com/odense-rpa/KMD-Institution-client
playwright install chromium
```

## Forudsætninger

- Python ≥ 3.13
- Adgang til KMD Institution via kommunens IdP

## Brug

```python
from kmd_institution_client import KMDInstitutionClient
from kmd_institution_client.functionality.institutioner_og_grupper import InstitutionerOgGrupperClient
from kmd_institution_client.functionality.indmeldelser import IndmeldelserClient

client = KMDInstitutionClient(idp="odense", username="...", password="...")
inst_client = InstitutionerOgGrupperClient(client, brugerid="...")

institution = inst_client.hent_institution("Skolen på Søndersø")

indmeldelser = IndmeldelserClient(client, brugerid="...")
resultater = indmeldelser.find_indmeldelser(institution, udmeldelsesdato_fra="01-01-2025")
```

## Licens

MIT
