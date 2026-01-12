"""
DLT Source Template (API)
=========================

Template for building DLT sources that extract data from APIs.
Includes patterns for:
- Incremental loading with cursor tracking
- Backfill mode with cursor reset
- Parallel execution across entities
- ETL metadata fields

Replace <Provider> and <Entity> with your actual names.
"""

import os
from typing import Iterator, Any

import dlt
import pendulum

# Import your client (adjust path)
# from .client import ProviderClient, MockProviderClient


# =============================================================================
# Configuration
# =============================================================================

# Entity IDs from environment (comma-separated)
ENTITY_IDS = [
    id.strip()
    for id in os.getenv("PROVIDER_ENTITY_IDS", "").split(",")
    if id.strip()
]

# Default lookback days
DEFAULT_DAYS = int(os.getenv("PROVIDER_DAYS", "7"))


# =============================================================================
# Helper Functions
# =============================================================================

def _add_etl_metadata(record: dict, source_name: str = "provider_api") -> dict:
    """Add ETL provenance fields to a record."""
    return {
        **record,
        "_etl_source": source_name,
        "_etl_extracted_at": pendulum.now().isoformat(),
    }


def _get_client(use_mock: bool, backfill_mode: bool):
    """Get appropriate client based on configuration."""
    # Uncomment when you have the client module
    # if use_mock:
    #     from .client import MockProviderClient
    #     return MockProviderClient()
    # else:
    #     from .client import ProviderClient
    #     return ProviderClient(backfill_mode=backfill_mode)
    raise NotImplementedError("Import your client classes")


# =============================================================================
# DLT Source
# =============================================================================

@dlt.source(name="provider_orders")
def provider_orders_source(
    use_mock: bool = False,
    backfill_mode: bool = False,
    days_back: int = DEFAULT_DAYS,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list:
    """
    DLT source for Provider orders data.

    Args:
        use_mock: Use mock client for testing
        backfill_mode: Enable backfill mode (resets cursors)
        days_back: Days of data to fetch (default mode)
        start_date: Explicit start date (ISO format)
        end_date: Explicit end date (ISO format)

    Returns:
        List of DLT resources
    """
    # Initialize client
    client = _get_client(use_mock, backfill_mode)

    # Return resources
    return [
        entities_resource(client),
        orders_resource(
            client=client,
            entity_ids=ENTITY_IDS,
            backfill_mode=backfill_mode,
            days_back=days_back,
            start_date=start_date,
            end_date=end_date,
        ),
        order_items_resource(
            client=client,
            entity_ids=ENTITY_IDS,
            backfill_mode=backfill_mode,
            days_back=days_back,
            start_date=start_date,
            end_date=end_date,
        ),
    ]


# =============================================================================
# Static Resources (No Date Filtering)
# =============================================================================

@dlt.resource(
    name="entities",
    write_disposition="merge",
    primary_key="id",
)
def entities_resource(client: Any) -> Iterator[dict]:
    """
    Fetch entity (location/store) metadata.

    This is static data that doesn't change often.
    Load once, not in date chunks.
    """
    for entity_id in ENTITY_IDS:
        entity = client.get_entity(entity_id)
        if entity:
            yield _add_etl_metadata(entity)


# =============================================================================
# Time-Series Resources (With Incremental Loading)
# =============================================================================

@dlt.resource(
    name="orders",
    write_disposition="merge",
    primary_key="id",
    parallelized=True,  # Enable parallel processing across entities
)
def orders_resource(
    client: Any,
    entity_ids: list[str],
    backfill_mode: bool,
    days_back: int,
    start_date: str | None,
    end_date: str | None,
    # Incremental cursor - DLT tracks this automatically
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",  # Field name in the data
        initial_value=pendulum.now().subtract(days=7).isoformat(),
    ),
) -> Iterator:
    """
    Fetch orders with incremental loading.

    Uses DLT's incremental loading to only fetch records modified
    since the last run. In backfill mode, resets the cursor to
    fetch all historical data.
    """
    # CRITICAL: Reset cursor for backfill mode
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    # Determine date range
    if start_date and end_date:
        s_date = pendulum.parse(start_date)
        e_date = pendulum.parse(end_date)
    else:
        e_date = pendulum.now()
        s_date = e_date.subtract(days=days_back)

    # Yield lambdas for parallel execution across entities
    # DLT will execute these in parallel
    for entity_id in entity_ids:
        yield lambda eid=entity_id: list(
            _fetch_orders_for_entity(client, eid, s_date, e_date)
        )


def _fetch_orders_for_entity(
    client: Any,
    entity_id: str,
    start_date,
    end_date,
) -> Iterator[dict]:
    """Fetch and transform orders for a single entity."""
    for order in client.get_orders_paginated(
        start_date=start_date,
        end_date=end_date,
        entity_id=entity_id,
    ):
        yield _add_etl_metadata(order)


# =============================================================================
# Nested Data Resources (Flatten Parent-Child)
# =============================================================================

@dlt.resource(
    name="order_items",
    write_disposition="merge",
    primary_key=["order_id", "item_id"],  # Composite key
    parallelized=True,
)
def order_items_resource(
    client: Any,
    entity_ids: list[str],
    backfill_mode: bool,
    days_back: int,
    start_date: str | None,
    end_date: str | None,
    modified_date: dlt.sources.incremental[str] = dlt.sources.incremental(
        "modified_date",
        initial_value=pendulum.now().subtract(days=7).isoformat(),
    ),
) -> Iterator:
    """
    Flatten nested items from orders.

    Many APIs return nested data (e.g., order with line items).
    This resource flattens that into a separate table for easier analysis.
    """
    if backfill_mode:
        modified_date.start_value = "2015-01-01T00:00:00Z"

    if start_date and end_date:
        s_date = pendulum.parse(start_date)
        e_date = pendulum.parse(end_date)
    else:
        e_date = pendulum.now()
        s_date = e_date.subtract(days=days_back)

    for entity_id in entity_ids:
        yield lambda eid=entity_id: list(
            _fetch_order_items_for_entity(client, eid, s_date, e_date)
        )


def _fetch_order_items_for_entity(
    client: Any,
    entity_id: str,
    start_date,
    end_date,
) -> Iterator[dict]:
    """Flatten order items from orders."""
    for order in client.get_orders_paginated(
        start_date=start_date,
        end_date=end_date,
        entity_id=entity_id,
    ):
        order_id = order.get("id")
        order_date = order.get("created_at") or order.get("modified_date")

        for item in order.get("items", []):
            yield _add_etl_metadata({
                "order_id": order_id,
                "item_id": item.get("id"),
                "order_date": order_date,
                "entity_id": entity_id,
                **{k: v for k, v in item.items() if k != "id"},
            })


# =============================================================================
# Resource Selection Helper
# =============================================================================

def get_source_with_resources(
    resource_name: str | None = None,
    **kwargs,
):
    """
    Get source with optional resource filtering.

    Useful in runners for loading specific resources.
    """
    source = provider_orders_source(**kwargs)

    if resource_name:
        return source.with_resources(resource_name)

    return source
