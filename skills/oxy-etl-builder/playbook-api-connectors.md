# Playbook: API Connectors

This playbook guides you through building ETL pipelines for third-party APIs (Toast, Square, Stripe, etc.).

## Overview

API connector pipelines follow this structure:

```
etl/sources/<provider>/
├── __init__.py
├── auth.py              # Optional: OAuth, token refresh
├── client.py            # API client with rate limiting
├── rate_limiter.py      # Optional: advanced rate limiting
├── mock_client.py       # Optional: for testing
├── <entity>_source.py   # DLT source definition
└── fixtures/            # Optional: test data
    └── <entity>.json
```

## Step 1: Understand the API

Before coding, gather this information:

### Authentication
- **API Key**: Simple header or query param
- **OAuth2**: Client credentials flow, token refresh
- **Custom**: Signatures, multi-step auth

### Rate Limits
- Requests per second/minute
- Different limits per endpoint
- Backoff requirements

### Data Model
- Available endpoints
- Response structure
- Pagination method (offset, cursor, page)
- Date filtering capabilities

### Incremental Strategy
- `modified_date` / `updated_at` field available?
- `business_date` for day-based data?
- Append-only with `created_at`?

## Step 2: Build the Client

### Basic Client Structure

```python
# etl/sources/<provider>/client.py
import os
import time
import requests
from typing import Iterator
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class ProviderClient:
    """Client for Provider API with rate limiting and error handling."""

    BASE_URL = "https://api.provider.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        backfill_mode: bool = False,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("PROVIDER_API_KEY")
        self.backfill_mode = backfill_mode
        self.max_retries = max_retries
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self):
        """Configure session with auth headers."""
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> requests.Response:
        """Make HTTP request with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    timeout=30,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = self._get_retry_after(response)
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    def _get_retry_after(self, response: requests.Response) -> int:
        """Extract retry-after from response headers."""
        return int(response.headers.get("Retry-After", 60))

    def close(self):
        """Close the session."""
        self.session.close()

    # --- Data Fetching Methods ---

    def get_orders(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict]:
        """Fetch orders for a date range."""
        try:
            response = self._make_request(
                "GET",
                "/orders",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                }
            )
            return response.json().get("orders", [])
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            return []  # Graceful degradation

    def get_orders_paginated(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Iterator[dict]:
        """Fetch orders with pagination (streaming)."""
        cursor = None

        while True:
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "limit": 100,
            }
            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", "/orders", params=params)
            data = response.json()

            for order in data.get("orders", []):
                yield order

            cursor = data.get("next_cursor")
            if not cursor:
                break

            # Rate limit delay in backfill mode
            if self.backfill_mode:
                time.sleep(0.5)
```

### OAuth2 Authentication

```python
# etl/sources/<provider>/auth.py
import os
import time
import requests
from dataclasses import dataclass

@dataclass
class TokenInfo:
    access_token: str
    expires_at: float

class ProviderAuthenticator:
    """OAuth2 client credentials authenticator."""

    TOKEN_URL = "https://api.provider.com/oauth/token"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.client_id = client_id or os.getenv("PROVIDER_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("PROVIDER_CLIENT_SECRET")
        self._token_info: TokenInfo | None = None

    def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed."""
        if self._token_info and time.time() < self._token_info.expires_at - 60:
            return self._token_info.access_token

        return self._refresh_token()

    def _refresh_token(self) -> str:
        """Request new access token."""
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()

        data = response.json()
        self._token_info = TokenInfo(
            access_token=data["access_token"],
            expires_at=time.time() + data["expires_in"],
        )
        return self._token_info.access_token
```

### Rate Limiter

```python
# etl/sources/<provider>/rate_limiter.py
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Sliding window rate limiter."""

    def __init__(
        self,
        requests_per_second: int = 10,
        requests_per_minute: int = 100,
    ):
        self.per_second = requests_per_second
        self.per_minute = requests_per_minute
        self.second_window: deque = deque()
        self.minute_window: deque = deque()
        self.lock = Lock()

    def acquire(self):
        """Wait until a request slot is available."""
        with self.lock:
            now = time.time()

            # Clean old entries
            while self.second_window and self.second_window[0] < now - 1:
                self.second_window.popleft()
            while self.minute_window and self.minute_window[0] < now - 60:
                self.minute_window.popleft()

            # Wait if at limit
            if len(self.second_window) >= self.per_second:
                sleep_time = 1 - (now - self.second_window[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            if len(self.minute_window) >= self.per_minute:
                sleep_time = 60 - (now - self.minute_window[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # Record request
            now = time.time()
            self.second_window.append(now)
            self.minute_window.append(now)
```

## Step 3: Build the DLT Source

### Source Structure

```python
# etl/sources/<provider>/<entity>_source.py
import os
import dlt
import pendulum
from typing import Iterator

from .client import ProviderClient

# Configuration
ENTITY_IDS = os.getenv("PROVIDER_ENTITY_IDS", "").split(",")


@dlt.source(name="provider_orders")
def provider_orders_source(
    use_mock: bool = False,
    backfill_mode: bool = False,
    days_back: int = 7,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """DLT source for Provider orders data."""

    # Initialize client
    if use_mock:
        from .mock_client import MockProviderClient
        client = MockProviderClient()
    else:
        client = ProviderClient(backfill_mode=backfill_mode)

    # Return resources
    return [
        entities_resource(client, ENTITY_IDS),
        orders_resource(client, ENTITY_IDS, backfill_mode, days_back, start_date, end_date),
        order_items_resource(client, ENTITY_IDS, backfill_mode, days_back, start_date, end_date),
    ]


# --- Static Resources (no date filtering) ---

@dlt.resource(name="entities", write_disposition="merge", primary_key="id")
def entities_resource(client: ProviderClient, entity_ids: list[str]) -> Iterator[dict]:
    """Fetch entity (location/store) metadata."""
    for entity_id in entity_ids:
        yield client.get_entity(entity_id)


# --- Time-Series Resources (with incremental loading) ---

@dlt.resource(name="orders", write_disposition="merge", primary_key="id", parallelized=True)
def orders_resource(
    client: ProviderClient,
    entity_ids: list[str],
    backfill_mode: bool,
    days_back: int,
    start_date: str | None,
    end_date: str | None,
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",
        initial_value=pendulum.now().subtract(days=7).isoformat(),
    ),
) -> Iterator[dict]:
    """Fetch orders with incremental loading."""

    # Reset cursor for backfill
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    # Determine date range
    if start_date and end_date:
        s_date = pendulum.parse(start_date)
        e_date = pendulum.parse(end_date)
    else:
        e_date = pendulum.now()
        s_date = pendulum.parse(modified_date.start_value)

    # Yield lambdas for parallel execution
    for entity_id in entity_ids:
        yield lambda eid=entity_id: list(
            _fetch_orders_for_entity(client, eid, s_date, e_date)
        )


def _fetch_orders_for_entity(
    client: ProviderClient,
    entity_id: str,
    start_date,
    end_date,
) -> Iterator[dict]:
    """Fetch orders for a single entity."""
    for order in client.get_orders_paginated(start_date, end_date):
        if order.get("entity_id") == entity_id:
            yield _add_etl_metadata(order)


def _add_etl_metadata(record: dict) -> dict:
    """Add ETL provenance fields."""
    return {
        **record,
        "_etl_source": "provider_api",
        "_etl_extracted_at": pendulum.now().isoformat(),
    }
```

### Key DLT Patterns

#### Incremental Loading with Cursor Reset

```python
@dlt.resource(name="orders", write_disposition="merge", primary_key="id")
def orders_resource(
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",  # Field in data that tracks updates
        initial_value=pendulum.now().subtract(days=7).isoformat(),
    ),
):
    # CRITICAL: Reset for backfill to get all historical data
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    # Now modified_date.start_value has the correct starting point
```

#### Parallel Execution

```python
@dlt.resource(parallelized=True)
def orders_resource(entity_ids: list[str]):
    # Yield lambdas for parallel processing
    for entity_id in entity_ids:
        yield lambda eid=entity_id: _fetch_for_entity(eid)
```

#### Nested Data Flattening

```python
@dlt.resource(name="order_items", write_disposition="merge", primary_key=["order_id", "item_id"])
def order_items_resource(client, ...):
    """Flatten nested items from orders."""
    for order in client.get_orders_paginated(...):
        for item in order.get("items", []):
            yield {
                "order_id": order["id"],
                "item_id": item["id"],
                **item,
            }
```

## Step 4: Build the Runner

```python
# etl/runners/<provider>_<entity>.py
import typer
from datetime import datetime
from rich.console import Console

from etl.core.pipeline import BasePipelineRunner, PipelineConfig
from etl.core.cli import setup_logging, parse_date
from etl.sources.<provider>.<entity>_source import provider_orders_source

app = typer.Typer(help="Provider Orders ETL Pipeline")
console = Console()


class ProviderOrdersRunner(BasePipelineRunner):
    """Runner for Provider orders pipeline."""

    @property
    def pipeline_name(self) -> str:
        return "provider_orders_pipeline"

    @property
    def dataset_name(self) -> str:
        return "analytics"

    @property
    def pipeline_emoji(self) -> str:
        return "📦"

    @property
    def pipeline_description(self) -> str:
        return "Provider Orders"

    def get_source(
        self,
        config: PipelineConfig,
        resource_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        return provider_orders_source(
            use_mock=config.dry_run and not config.mock_api and not config.real_api,
            backfill_mode=config.backfill,
            days_back=config.days,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
        )

    def get_resources_config(self) -> dict[str, bool]:
        """Map resource names to whether they need date filtering."""
        return {
            "entities": False,      # Static, load once
            "orders": True,         # Time-series, date filtered
            "order_items": True,    # Time-series, date filtered
        }

    def compute_metrics(self) -> None:
        """Optional: compute derived metrics after load."""
        # from etl.transforms.compute_order_metrics import compute_order_metrics
        # compute_order_metrics()
        pass


# --- CLI Commands ---

@app.command()
def run(
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Use DuckDB instead of production"),
    mock_api: bool = typer.Option(False, "--mock-api", help="Use mock API responses"),
    real_api: bool = typer.Option(False, "--real-api", help="Use real API with dry-run destination"),
    days: int = typer.Option(7, "--days", help="Days of data to fetch"),
    backfill: bool = typer.Option(False, "--backfill", "-b", help="Enable backfill mode"),
    start_date: str = typer.Option(None, "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end-date", help="End date (YYYY-MM-DD)"),
    chunk_days: int = typer.Option(30, "--chunk-days", help="Days per chunk in backfill"),
    log_level: str = typer.Option("WARNING", "--log-level", "-l", help="Log level"),
):
    """Run the ETL pipeline."""
    setup_logging(log_level)

    config = PipelineConfig(
        dry_run=dry_run,
        mock_api=mock_api,
        real_api=real_api,
        days=days,
        backfill=backfill,
        start_date=parse_date(start_date) if start_date else None,
        end_date=parse_date(end_date) if end_date else None,
        chunk_days=chunk_days,
        log_level=log_level,
    )

    runner = ProviderOrdersRunner()
    runner.run(config)


@app.command()
def test():
    """Run with mock data for quick testing."""
    config = PipelineConfig(dry_run=True, mock_api=True, days=7)
    runner = ProviderOrdersRunner()
    runner.run(config)


@app.command()
def config():
    """Show current configuration."""
    from etl.sources.<provider>.<entity>_source import ENTITY_IDS
    console.print("[bold]Configuration[/bold]")
    console.print(f"  Entity IDs: {ENTITY_IDS}")


if __name__ == "__main__":
    app()
```

## Step 5: Handle Backfill

### Chunking Strategy

For large historical loads, chunk by date ranges:

```python
# In runner, override _run_backfill if needed
def _run_backfill(self, pipeline, config):
    from etl.core.chunking import generate_date_chunks

    chunks = generate_date_chunks(
        start_date=config.start_date,
        end_date=config.end_date or pendulum.now(),
        chunk_size_days=config.chunk_days,
    )

    # Load static resources once
    static_resources = [r for r, needs_date in self.get_resources_config().items() if not needs_date]
    if static_resources:
        source = self.get_source(config)
        pipeline.run(source.with_resources(*static_resources))

    # Load time-series resources in chunks
    time_resources = [r for r, needs_date in self.get_resources_config().items() if needs_date]
    for start, end in chunks:
        console.print(f"Processing chunk: {start} to {end}")
        source = self.get_source(config, start_date=start, end_date=end)
        pipeline.run(
            source.with_resources(*time_resources),
            write_disposition="merge",
        )
```

### API Chunking

Many APIs limit date ranges (e.g., max 30 days). Handle in client:

```python
def get_orders_chunked(self, start_date, end_date, chunk_days=30):
    """Fetch orders in chunks to respect API limits."""
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=chunk_days), end_date)
        yield from self.get_orders(current, chunk_end)
        current = chunk_end

        if self.backfill_mode:
            time.sleep(1)  # Be nice to the API
```

## Common API Patterns

### Pagination: Cursor-Based

```python
def get_items_paginated(self, **filters):
    cursor = None
    while True:
        params = {**filters, "limit": 100}
        if cursor:
            params["cursor"] = cursor

        data = self._make_request("GET", "/items", params=params).json()
        yield from data["items"]

        cursor = data.get("next_cursor")
        if not cursor:
            break
```

### Pagination: Offset-Based

```python
def get_items_paginated(self, **filters):
    offset = 0
    limit = 100
    while True:
        params = {**filters, "limit": limit, "offset": offset}
        data = self._make_request("GET", "/items", params=params).json()

        items = data["items"]
        yield from items

        if len(items) < limit:
            break
        offset += limit
```

### Webhook Data vs Polling

For APIs with webhooks, consider hybrid approach:
1. **Webhooks** for real-time updates → append to staging table
2. **Polling** for backfill and reconciliation → merge to main table

## Testing

### Mock Client

```python
# etl/sources/<provider>/mock_client.py
import json
from pathlib import Path

class MockProviderClient:
    """Mock client returning fixture data."""

    def __init__(self, *args, **kwargs):
        self.fixtures_dir = Path(__file__).parent / "fixtures"

    def get_orders(self, start_date, end_date):
        return self._load_fixture("orders.json")

    def get_orders_paginated(self, start_date, end_date):
        yield from self._load_fixture("orders.json")

    def _load_fixture(self, name):
        path = self.fixtures_dir / name
        if path.exists():
            return json.loads(path.read_text())
        return []

    def close(self):
        pass
```

### Fixtures

```json
// etl/sources/<provider>/fixtures/orders.json
[
  {
    "id": "order_001",
    "entity_id": "entity_001",
    "amount": 125.50,
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "modified_date": "2024-01-15T10:30:00Z"
  }
]
```

## Checklist

Before completing an API connector:

- [ ] Client handles authentication (API key or OAuth2)
- [ ] Client has rate limiting with backoff
- [ ] Client returns empty on errors (graceful degradation)
- [ ] DLT source has incremental loading configured
- [ ] Backfill mode resets cursor correctly
- [ ] Runner has all CLI commands (run, test, config)
- [ ] Mock client available for testing
- [ ] Fixtures have sample data
