import logging
from collections.abc import Callable

import httpx

# Path segments with 4+ digits are treated as identifiers (municipality IDs, CPR, institution IDs, ...)
_MIN_CIFRE = 4


def _mask_segment(segment: str) -> str:
    return "***" if sum(c.isdigit() for c in segment) >= _MIN_CIFRE else segment


def mask_url(url: httpx.URL) -> str:
    """Return the URL without query string, with identifier-like path segments masked."""
    path = "/".join(_mask_segment(s) for s in url.path.split("/"))
    return str(url.copy_with(query=None, path=path))


def create_response_logging_hook(logger: logging.Logger) -> Callable[[httpx.Response], None]:
    """
    Create an httpx response event hook that logs each HTTP transaction.

    Only method, masked URL and status are logged. Request/response bodies and
    query strings are left out, and numbers in the path are masked: they can
    contain CPR numbers and other personal data about children and guardians.

    Args:
        logger: Logger to write to.

    Returns:
        A callable usable in ``httpx.Client(event_hooks={"response": [...]})``.
    """

    def log_response(response: httpx.Response) -> None:
        request = response.request
        is_error = response.is_error
        url = mask_url(request.url)
        logger.log(
            logging.ERROR if is_error else logging.INFO,
            "HTTP %s: %s %s",
            response.status_code,
            request.method,
            url,
            extra={
                "event_type": "http_transaction",
                "http_method": request.method,
                "http_url": url,
                "http_status": response.status_code,
                "is_error": is_error,
            },
        )

    return log_response
