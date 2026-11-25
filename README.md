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
from kmd_institution_client import KMDInstitutionClientManager

with KMDInstitutionClientManager("odense", "...", "...") as kmd:
    institution = kmd.institutioner_og_grupper.hent_institution("Skolen på Søndersø")
    resultater = kmd.indmeldelser.find_indmeldelser(
        institution, udmeldelsesdato_fra="01-01-2025"
    )
```

Browseren kører headless som standard. Brug `headless=False` til fejlsøgning.
Manageren kan også oprettes fra miljøvariabler med `KMDInstitutionClientManager.fra_env()`
(`KMD_IDP`, `KMD_USERNAME`, `KMD_PASSWORD`, `KMD_HEADLESS`, se `env.example`).

## Licens

MIT
