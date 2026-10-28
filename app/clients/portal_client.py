from __future__ import annotations

from urllib.parse import quote
import httpx

from app.config import (
    PORTAL_BASE_URL,
    PORTAL_EMAIL,
    PORTAL_PASSWORD,
    REQUEST_TIMEOUT_SECONDS,
)


class PortalClientError(Exception):
    """Base exception for portal communication errors."""


class PortalAuthenticationError(PortalClientError):
    """Raised when portal login fails."""


class PortalClient:
    """HTTP client for read-only access to the Urja Meter Ops portal."""

    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=PORTAL_BASE_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"Accept": "application/json"},
        )
        self._authenticated = False

    def login(self) -> None:
        """Log in and retain the session cookie in the HTTP client."""
        if not PORTAL_EMAIL or not PORTAL_PASSWORD:
            raise PortalAuthenticationError(
                "Configure PORTAL_EMAIL and PORTAL_PASSWORD in .env."
            )

        try:
            response = self._client.post(
                "/login",
                data={
                    "email": PORTAL_EMAIL,
                    "password": PORTAL_PASSWORD,
                },
                headers={
                    "X-Sveltekit-Action": "true",
                    "Referer": f"{PORTAL_BASE_URL}/login",
                    "Origin": PORTAL_BASE_URL,
                },
            )
            response.raise_for_status()
            result = response.json()

        except httpx.HTTPError as exc:
            raise PortalAuthenticationError(
                "Portal login request failed."
            ) from exc
        except ValueError as exc:
            raise PortalAuthenticationError(
                "Portal login returned an unexpected response."
            ) from exc

        # The observed portal responds with redirect metadata in JSON.
        if (
            not isinstance(result, dict)
            or result.get("type") != "redirect"
            or result.get("location") != "/meters"
        ):
            raise PortalAuthenticationError(
                "Portal did not return the expected login response."
            )

        # Keep cookies inside this client; never print or expose them.
        if len(self._client.cookies) == 0:
            raise PortalAuthenticationError(
                "Login response did not establish a session cookie."
            )

        self._authenticated = True

    def search_meters(
        self, query: str = "", page: int = 1
    ) -> dict:
        """Search meters using the observed portal endpoint."""
        if not self._authenticated:
            raise PortalAuthenticationError(
                "Call login() before requesting meter data."
            )

        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        try:
            response = self._client.get(
                "/portal/meters/search",
                params={"q": query, "page": page},
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as exc:
            raise PortalClientError(
                "Meter search request failed."
            ) from exc
        except ValueError as exc:
            raise PortalClientError(
                "Meter search returned invalid JSON."
            ) from exc

        if not isinstance(result, dict) or not isinstance(
            result.get("data"), list
        ):
            raise PortalClientError(
                "Meter search response has an unexpected structure."
            )

        return result
    
    def _request_json(self, path: str, params: dict | None = None) -> dict:
        """Send an authenticated GET request and parse its JSON response."""
        if not self._authenticated:
            raise PortalAuthenticationError(
                "Call login() before requesting portal data."
            )

        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
            result = response.json()
        except httpx.TimeoutException as exc:
            raise PortalClientError("Portal request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise PortalClientError(
                f"Portal returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise PortalClientError("Portal request failed.") from exc
        except ValueError as exc:
            raise PortalClientError(
                "Portal returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise PortalClientError(
                "Portal returned an unexpected JSON structure."
            )

        return result

    def get_meter_geo(self, meter_id: str) -> dict:
        """Retrieve geographic coordinates for one meter."""
        if not meter_id.strip():
            raise ValueError("meter_id cannot be empty")

        safe_id = quote(meter_id.strip(), safe="")
        result = self._request_json(
            f"/portal/meters/{safe_id}/geo"
        )

        if not isinstance(result.get("data"), dict):
            raise PortalClientError(
                "Unexpected geographic response structure."
            )

        return result

    def get_meter_energy(self, meter_id: str) -> dict:
        """Retrieve consumption history for one meter."""
        if not meter_id.strip():
            raise ValueError("meter_id cannot be empty")

        safe_id = quote(meter_id.strip(), safe="")
        result = self._request_json(
            f"/portal/meters/{safe_id}/energy"
        )

        if not isinstance(result.get("data"), list):
            raise PortalClientError(
                "Unexpected energy response structure."
            )

        return result

    def list_transformers(self, page: int = 1) -> dict:
        """Retrieve a page of distribution transformer records."""
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        result = self._request_json(
            "/portal/dts",
            params={"page": page},
        )

        if not isinstance(result.get("data"), list):
            raise PortalClientError(
                "Unexpected transformer response structure."
            )

        return result


    def close(self) -> None:
        """Close the HTTP client and its session."""
        self._client.close()
        self._authenticated = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
