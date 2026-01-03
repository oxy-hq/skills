"""
API Client Template
===================

Template for building API clients with:
- OAuth2 or API key authentication
- Rate limiting with exponential backoff
- Pagination handling
- Streaming for large datasets
- Graceful error handling

Replace <Provider> with your actual provider name (e.g., Toast, Square, Stripe).
"""

import os
import time
import logging
from datetime import timedelta
from typing import Iterator

import requests

logger = logging.getLogger(__name__)


# =============================================================================
# Authentication
# =============================================================================

class ProviderAuthenticator:
    """
    OAuth2 client credentials authenticator.

    For API key auth, skip this class and use headers directly in the client.
    """

    TOKEN_URL = "https://api.provider.com/oauth/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.client_id = client_id or os.getenv("PROVIDER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PROVIDER_CLIENT_SECRET")
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        return self._refresh_token()

    def _refresh_token(self) -> str:
        """Request new access token from OAuth endpoint."""
        logger.debug("Refreshing OAuth token")

        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600)

        return self._access_token


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    Simple rate limiter with sliding window.

    For more complex rate limiting (multiple quotas, adaptive backoff),
    expand this class or use a library like ratelimit.
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        min_interval: float = 0.1,
    ):
        self.min_interval = max(1.0 / requests_per_second, min_interval)
        self.last_request_time: float = 0

    def wait(self) -> None:
        """Wait until the next request is allowed."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def handle_429(self, retry_after: int | None = None) -> float:
        """
        Handle rate limit (429) response.

        Returns the time waited.
        """
        wait_time = retry_after or 60
        logger.warning(f"Rate limited, waiting {wait_time}s")
        time.sleep(wait_time)
        return wait_time


# =============================================================================
# Main Client
# =============================================================================

class ProviderClient:
    """
    API client for Provider with authentication, rate limiting, and error handling.

    Usage:
        client = ProviderClient()
        orders = client.get_orders(start_date, end_date)

        # For backfill mode (slower, more polite)
        client = ProviderClient(backfill_mode=True)
    """

    BASE_URL = "https://api.provider.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        backfill_mode: bool = False,
        max_retries: int = 3,
    ):
        """
        Initialize the client.

        Args:
            api_key: API key (if using key-based auth)
            client_id: OAuth client ID (if using OAuth)
            client_secret: OAuth client secret (if using OAuth)
            backfill_mode: Enable slower, rate-limit-friendly mode
            max_retries: Maximum retry attempts for failed requests
        """
        self.api_key = api_key or os.getenv("PROVIDER_API_KEY")
        self.backfill_mode = backfill_mode
        self.max_retries = max_retries

        # Initialize authenticator (choose one)
        # Option 1: OAuth2
        # self.auth = ProviderAuthenticator(client_id, client_secret)
        # Option 2: API key (set self.auth = None)
        self.auth = None

        # Rate limiter (adjust based on API limits)
        requests_per_second = 2.0 if backfill_mode else 10.0
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)

        # HTTP session for connection pooling
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """Configure session with default headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add authentication header
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session.headers.update(headers)

    def _get_auth_header(self) -> dict[str, str]:
        """Get authentication header for request."""
        if self.auth:
            token = self.auth.get_access_token()
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
        timeout: int = 30,
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/orders")
            params: Query parameters
            json: JSON body
            timeout: Request timeout in seconds

        Returns:
            Response object

        Raises:
            requests.RequestException: If all retries fail
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self.rate_limiter.wait()

                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=self._get_auth_header(),
                    timeout=timeout,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.rate_limiter.handle_429(retry_after)
                    continue

                # Raise for other errors
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                time.sleep(2 ** attempt)

        raise requests.exceptions.RequestException(f"Max retries exceeded for {endpoint}")

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    # =========================================================================
    # Data Fetching Methods - Customize for your API
    # =========================================================================

    def get_entity(self, entity_id: str) -> dict:
        """
        Fetch a single entity (e.g., restaurant, store, location).

        Args:
            entity_id: Entity identifier

        Returns:
            Entity data dict, or empty dict on error
        """
        try:
            response = self._make_request("GET", f"/entities/{entity_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch entity {entity_id}: {e}")
            return {}

    def get_orders(
        self,
        start_date,
        end_date,
        entity_id: str | None = None,
    ) -> list[dict]:
        """
        Fetch orders for a date range.

        Args:
            start_date: Start date (datetime or string)
            end_date: End date (datetime or string)
            entity_id: Optional entity filter

        Returns:
            List of order dicts, or empty list on error
        """
        try:
            params = {
                "start_date": str(start_date),
                "end_date": str(end_date),
            }
            if entity_id:
                params["entity_id"] = entity_id

            response = self._make_request("GET", "/orders", params=params)
            return response.json().get("orders", [])

        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            return []  # Graceful degradation

    def get_orders_paginated(
        self,
        start_date,
        end_date,
        entity_id: str | None = None,
        page_size: int = 100,
    ) -> Iterator[dict]:
        """
        Fetch orders with pagination (streaming/generator).

        Use this for large date ranges or backfills.

        Args:
            start_date: Start date
            end_date: End date
            entity_id: Optional entity filter
            page_size: Number of records per page

        Yields:
            Individual order dicts
        """
        cursor = None

        while True:
            params = {
                "start_date": str(start_date),
                "end_date": str(end_date),
                "limit": page_size,
            }
            if entity_id:
                params["entity_id"] = entity_id
            if cursor:
                params["cursor"] = cursor

            try:
                response = self._make_request("GET", "/orders", params=params)
                data = response.json()

                for order in data.get("orders", []):
                    yield order

                # Check for next page
                cursor = data.get("next_cursor")
                if not cursor:
                    break

                # Extra delay in backfill mode
                if self.backfill_mode:
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed during pagination: {e}")
                break

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def health_check(self) -> bool:
        """
        Check if the API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            self._make_request("GET", "/health", timeout=5)
            return True
        except Exception:
            return False


# =============================================================================
# Mock Client for Testing
# =============================================================================

class MockProviderClient:
    """
    Mock client for testing without real API calls.

    Returns fixture data from JSON files.
    """

    def __init__(self, *args, **kwargs):
        """Accept any arguments to match real client signature."""
        import json
        from pathlib import Path

        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.calls: list[tuple] = []  # Track method calls for testing

    def _load_fixture(self, name: str) -> list | dict:
        """Load fixture data from JSON file."""
        import json

        path = self.fixtures_dir / name
        if path.exists():
            return json.loads(path.read_text())
        return []

    def get_entity(self, entity_id: str) -> dict:
        self.calls.append(("get_entity", entity_id))
        entities = self._load_fixture("entities.json")
        for entity in entities:
            if entity.get("id") == entity_id:
                return entity
        return {"id": entity_id, "name": f"Mock Entity {entity_id}"}

    def get_orders(self, start_date, end_date, entity_id=None) -> list[dict]:
        self.calls.append(("get_orders", start_date, end_date, entity_id))
        return self._load_fixture("orders.json")

    def get_orders_paginated(self, start_date, end_date, entity_id=None, page_size=100):
        self.calls.append(("get_orders_paginated", start_date, end_date, entity_id))
        yield from self._load_fixture("orders.json")

    def health_check(self) -> bool:
        return True

    def close(self) -> None:
        pass
