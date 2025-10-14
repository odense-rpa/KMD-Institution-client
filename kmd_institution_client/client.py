import time
import httpx
import logging

from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect

from kmd_institution_client.hooks import create_response_logging_hook

class KMDInstitutionClient:
    @property
    def cookies(self) -> dict[str, str]:
        """Get the current active cookies."""
        return self._cookies
    
    @cookies.setter
    def cookies(self, value: dict[str, str]) -> None:
        """Set the current active cookies."""
        self._cookies = value

    def __init__(
            self, 
            idp: str
            ) -> None:

        self.logger = logging.getLogger(__name__)

        # Create response logging hook
        response_hook = create_response_logging_hook(logger=self.logger)
        hooks = {'response': [response_hook]}

        self._base_url = "https://institution.kmd.dk/"
        self._timeout = 30.0  # seconds
        self._idp = idp
        self._client = httpx.Client(
            timeout=self._timeout,
            event_hooks=hooks,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            },
        )
        self.login()

    def login(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                storage_state=None,  # No stored state (similar to incognito)
                accept_downloads=False,
                ignore_https_errors=True,
            )
            page = context.new_page()
            page.goto(self._base_url)
            

            # Håndter FællesKommunal login side
            try:
                page.locator("a.btn[role='button']").click(timeout=3000)
            except:
                self.logger.debug("Registerede ikke Fælleskommunal side, skipper videre")
                pass  # Forsæt hvis den af en eller anden grund ikke dukker op

            # Vælg IDP og klik OK
            try:
                page.select_option("select#SelectedAuthenticationUrl", label=f"{self._idp}")
                page.click("input[type='button'][value='OK']")
            except:
                self.logger.debug("Kunne ikke vælge IDP og/eller klikke OK, skipper videre, muligvis allerede logget ind")
                pass # Forsæt hvis IDP ikke dukker op (måske allerede logget ind)
            
            # Wait for the final dashboard URL or handle login flow
            try:
                dashboard_url = urljoin(self._base_url, "/Caseworker#/dashboard")
                page.wait_for_url(dashboard_url, timeout=60000)
                self.logger.info("Successfully reached dashboard")
            except Exception as e:
                if "login" in page.url.lower() or "auth" in page.url.lower():
                    self.logger.warning(f"Still in authentication flow at: {page.url}")
                else:
                    self.logger.info(f"Authentication may have completed, currently at: {page.url}")

            # Get cookies before closing the context
            cookies = context.cookies()
            saml2_cookies = {}

            # Look for all SAML2 related cookies
            for cookie in cookies:
                if '.AspNetCore.saml2Cookie' in cookie['name']:
                    saml2_cookies[cookie['name']] = cookie['value']
            
            if not saml2_cookies:
                error_msg = f"No SAML2 cookies found after authentication. Current URL: {page.url}. Found {len(cookies)} total cookies."
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            self.logger.info(f"Successfully authenticated and found {len(saml2_cookies)} SAML2 cookies")
            self.cookies = saml2_cookies

    def _normalize_url(self, endpoint: str) -> str:
        """Ensure the URL is absolute, handling relative URLs."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        # For relative URLs, just join with base URL (caller should include /odata/ or /api/ as needed)
        return urljoin(self._base_url, endpoint)

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """
        Perform GET request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self._client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(self, endpoint: str, json: dict | None = None, **kwargs) -> httpx.Response:
        """
        Perform POST request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self._client.post(url, json=json, **kwargs)
        response.raise_for_status()
        return response

    def put(self, endpoint: str, json: dict | None = None, **kwargs) -> httpx.Response:
        """
        Perform PUT request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param json: JSON data to send in request body
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self._client.put(url, json=json, **kwargs)
        response.raise_for_status()
        return response

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """
        Perform DELETE request to the specified endpoint.

        :param endpoint: API endpoint (relative or absolute URL)
        :param kwargs: Additional arguments passed to httpx
        :return: HTTP response
        """
        url = self._normalize_url(endpoint)
        response = self._client.delete(url, **kwargs)
        response.raise_for_status()
        return response