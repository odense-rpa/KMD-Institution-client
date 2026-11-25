"""Offline-tests af klientens HTTP-lag - kræver ikke login eller netværk."""

import logging

import httpx
import pytest

from kmd_institution_client import KMDInstitutionClient
from kmd_institution_client.hooks import mask_url


def _klient(handler) -> KMDInstitutionClient:
    return KMDInstitutionClient(
        "idp", "bruger", "kodeord",
        auto_login=False,
        transport=httpx.MockTransport(handler),
    )


def test_mask_url_fjerner_query_og_id():
    url = httpx.URL("https://institution.kmd.dk/api/municipalities/461/children/8888888?cpr=9999999999")
    assert mask_url(url) == "https://institution.kmd.dk/api/municipalities/461/children/***"


def test_get_genforsoeger_gateway_fejl(monkeypatch):
    monkeypatch.setattr("kmd_institution_client.client.time.sleep", lambda _: None)
    svar = iter([503, 502, 200])
    kald = []

    def handler(request: httpx.Request) -> httpx.Response:
        kald.append(request)
        return httpx.Response(next(svar), json={"ok": True})

    with _klient(handler) as klient:
        assert klient.get("api/test").status_code == 200
    assert len(kald) == 3


def test_post_genforsoeges_aldrig(monkeypatch):
    monkeypatch.setattr("kmd_institution_client.client.time.sleep", lambda _: None)
    kald = []

    def handler(request: httpx.Request) -> httpx.Response:
        kald.append(request)
        return httpx.Response(503)

    with _klient(handler) as klient, pytest.raises(httpx.HTTPStatusError):
        klient.post("api/test", json={"a": 1})
    assert len(kald) == 1


def test_fejlbesked_indeholder_ikke_id_eller_query():
    with _klient(lambda r: httpx.Response(404)) as klient, pytest.raises(httpx.HTTPStatusError) as e:
        klient.get("api/children/8888888?cpr=9999999999")
    assert "8888888" not in str(e.value)
    assert "9999999999" not in str(e.value)
    assert "HTTP 404: GET" in str(e.value)


def test_log_indeholder_ikke_bodies(caplog):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"navn": "Hemmeligt Barn"})

    with caplog.at_level(logging.INFO), _klient(handler) as klient:
        klient.post("api/test", json={"cpr": "9999999999"})

    tekst = " ".join(f"{r.getMessage()} {r.__dict__}" for r in caplog.records)
    assert "Hemmeligt Barn" not in tekst
    assert "9999999999" not in tekst
    assert any(r.__dict__.get("http_status") == 200 for r in caplog.records)
