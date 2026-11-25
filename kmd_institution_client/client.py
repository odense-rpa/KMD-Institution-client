import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from types import TracebackType
from typing import Any, Self
from urllib.parse import urljoin

import httpx
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .hooks import create_response_logging_hook, mask_url
from .selectors import KMDSelectors

# Navnet på de session-cookies KMD Institution sætter efter login
SESSION_COOKIE_PREFIX = ".AspNetCore.saml2Cookie"

# Hvor længe de valgfrie login-trin (fx IdP-valg, brugernavn) afventes, før de springes over
VALGFRIT_TRIN_TIMEOUT_MS = 5000

# Sider hvor login ender
DASHBOARD_PATH = "/Caseworker#/dashboard"


class KMDInstitutionClient:
    """Core client: logger ind med Playwright og udfører API-kald med httpx."""

    # Midlertidige gateway-fejl genforsøges. Kun idempotente metoder,
    # så fx en POST aldrig sendes to gange.
    RETRY_STATUSES = frozenset({502, 503, 504})
    RETRY_METHODS = frozenset({"GET"})
    RETRY_DELAYS = (1.0, 2.0, 4.0)

    @property
    def cookies(self) -> dict[str, str]:
        """Get the current active cookies."""
        return self._cookies

    @cookies.setter
    def cookies(self, value: dict[str, str]) -> None:
        """Set the current active cookies."""
        self._cookies = value
        # Clear existing cookies and set new ones in bulk
        self._client.cookies.clear()
        self._client.cookies.update(value)

    def __init__(
        self,
        idp: str,
        username: str,
        password: str,
        *,
        headless: bool = True,
        login_timeout: float = 60.0,
        trin_timeout: float = 30.0,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        auto_login: bool = True,
    ) -> None:
        """
        :param idp: Navnet på kommunens IdP i dropdown'en (fx "odense")
        :param username: Brugernavn
        :param password: Password
        :param headless: Kør browseren uden vindue (standard). Brug False til fejlsøgning.
        :param login_timeout: Max sekunder for at nå dashboardet efter brugernavn/password er indtastet
        :param trin_timeout: Max sekunder for hvert øvrigt login-trin før TimeoutError
        :param timeout: HTTP-timeout i sekunder
        :param transport: Valgfri httpx-transport (bruges til offline-tests)
        :param auto_login: Log ind med det samme (blokerer til login er færdigt)
        """
        self.logger = logging.getLogger(__name__)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        self._base_url = "https://institution.kmd.dk/"
        self._idp = idp
        self._username = username
        self._password = password
        self._headless = headless
        self._login_timeout = login_timeout
        self._trin_timeout = trin_timeout
        self._cookies: dict[str, str] = {}
        self._client = httpx.Client(
            timeout=timeout,
            transport=transport,
            event_hooks={"response": [create_response_logging_hook(self.logger)]},
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
            },
        )

        if auto_login:
            self.login()

    @property
    def headless(self) -> bool:
        return self._headless

    def login(self) -> None:
        """
        Log ind på KMD Institution:

        1. Klik videre på Fælleskommunal-siden (springes over hvis den ikke vises).
        2. Vælg kommunens IdP og tryk OK (springes over hvis man allerede er videresendt).
        3. Indtast brugernavn og password (springes over hvis IdP'en allerede har en session).
        4. Vent på dashboardet og kopiér SAML2-session-cookies til httpx-klienten.
        """
        sel = KMDSelectors.Login

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self._headless)
            try:
                context = browser.new_context(
                    storage_state=None,  # No stored state (similar to incognito)
                    accept_downloads=False,
                    ignore_https_errors=True,
                )
                # Alle handlinger og navigationer er begrænset af trin_timeout.
                context.set_default_timeout(self._trin_timeout * 1000)
                context.set_default_navigation_timeout(self._trin_timeout * 1000)
                page = context.new_page()

                with self._trin("åbn login-side"):
                    page.goto(self._base_url)

                # Fælleskommunal login-side
                try:
                    page.locator(sel.FAELLESKOMMUNAL_KNAP).click(timeout=3000)
                except PlaywrightTimeoutError:
                    self.logger.debug("Registrerede ikke Fælleskommunal side, skipper videre")

                # Vælg IDP og klik OK
                try:
                    page.select_option(
                        sel.IDP_SELECT, label=self._idp, timeout=VALGFRIT_TRIN_TIMEOUT_MS
                    )
                    page.click(sel.IDP_OK_BUTTON, timeout=VALGFRIT_TRIN_TIMEOUT_MS)
                except PlaywrightTimeoutError:
                    self.logger.debug(
                        "Kunne ikke vælge IDP og/eller klikke OK, skipper videre, muligvis allerede logget ind"
                    )

                # Indtast bruger
                try:
                    page.wait_for_selector(sel.USERNAME_INPUT, timeout=VALGFRIT_TRIN_TIMEOUT_MS)
                    page.fill(sel.USERNAME_INPUT, self._username)
                    page.click(sel.SUBMIT_BUTTON)
                except PlaywrightTimeoutError:
                    self.logger.debug("Kunne ikke indtaste bruger, skipper videre")

                # Indtast password
                try:
                    page.wait_for_selector(sel.PASSWORD_INPUT, timeout=VALGFRIT_TRIN_TIMEOUT_MS)
                    page.fill(sel.PASSWORD_INPUT, self._password)
                    page.click(sel.SUBMIT_BUTTON)
                except PlaywrightTimeoutError:
                    self.logger.debug("Kunne ikke indtaste password, skipper videre")

                with self._trin("vent på dashboard", timeout=self._login_timeout):
                    page.wait_for_url(
                        urljoin(self._base_url, DASHBOARD_PATH),
                        timeout=self._login_timeout * 1000,
                    )
                self.logger.info("Successfully reached dashboard")

                # Hent cookies før konteksten lukkes
                cookies = context.cookies()
                saml2_cookies = {
                    c["name"]: c["value"]
                    for c in cookies
                    if SESSION_COOKIE_PREFIX in c["name"]
                }

                if not saml2_cookies:
                    error_msg = (
                        f"No SAML2 cookies found after authentication. "
                        f"Current URL: {page.url}. Found {len(cookies)} total cookies."
                    )
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)

                self.logger.info(
                    "Successfully authenticated and found %d SAML2 cookies", len(saml2_cookies)
                )
                self.cookies = saml2_cookies
            finally:
                browser.close()

    @contextmanager
    def _trin(self, navn: str, timeout: float | None = None) -> Generator[None]:
        """Gør en Playwright-timeout i et login-trin til en TimeoutError der nævner trinnet."""
        try:
            yield
        except PlaywrightTimeoutError as e:
            sek = int(timeout if timeout is not None else self._trin_timeout)
            raise TimeoutError(f"Login hang ved trin '{navn}' i mere end {sek} sekunder") from e

    def _normalize_url(self, endpoint: str) -> str:
        """Ensure the URL is absolute, handling relative URLs."""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        # For relative URLs, just join with base URL (caller should include /odata/ or /api/ as needed)
        return urljoin(self._base_url, endpoint)

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> httpx.Response:
        url = self._normalize_url(endpoint)
        response = self._send(method, url, **kwargs)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Re-raise uden den fulde URL: den kan indeholde id'er og datoer.
            raise httpx.HTTPStatusError(
                f"HTTP {e.response.status_code}: {method} {mask_url(e.request.url)}",
                request=e.request,
                response=e.response,
            ) from None
        return response

    def _send(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send en request og genforsøg midlertidige gateway-fejl for idempotente metoder."""
        forsoeg_i_alt = len(self.RETRY_DELAYS) + 1
        for forsoeg, ventetid in enumerate((*self.RETRY_DELAYS, None), start=1):
            response = self._client.request(method, url, **kwargs)
            kan_proeve_igen = (
                ventetid is not None
                and method.upper() in self.RETRY_METHODS
                and response.status_code in self.RETRY_STATUSES
            )
            if not kan_proeve_igen:
                break
            self.logger.warning(
                "HTTP %s: %s %s - prøver igen om %s sek (forsøg %d/%d)",
                response.status_code, method, mask_url(response.request.url),
                ventetid, forsoeg, forsoeg_i_alt,
            )
            response.close()
            time.sleep(ventetid)
        return response

    def get(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """
        Perform GET request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, json: Any = None, **kwargs: Any) -> httpx.Response:
        """
        Perform POST request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        return self._request("POST", endpoint, json=json, **kwargs)

    def put(self, endpoint: str, json: Any = None, **kwargs: Any) -> httpx.Response:
        """
        Perform PUT request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        return self._request("PUT", endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> httpx.Response:
        """
        Perform DELETE request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        return self._request("DELETE", endpoint, **kwargs)

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
