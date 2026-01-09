# Playbook: Spreadsheet Ingestion

This playbook guides you through building ETL pipelines for spreadsheets and semi-structured files (XLSX, CSV, etc.).

## Overview

Spreadsheet pipelines use a template-based approach:

```
etl/sources/spreadsheets/
├── __init__.py
├── core.py              # Shared utilities
└── templates/
    ├── __init__.py
    ├── base.py          # BaseTemplate ABC
    └── <name>.py        # Concrete implementations
```

## Step 1: Understand the Spreadsheet

Before coding, analyze the file structure:

### Sheet Organization
- Single sheet or multiple sheets?
- One entity per sheet or mixed data?
- Header location (row 1 or elsewhere)?

### Data Layout
- Standard tabular (headers in row 1)?
- Pivot-style (periods as columns)?
- Hierarchical (categories with subcategories)?

### Identification
- How to detect this template vs others?
- Unique headers or patterns?
- Version indicators?

### Entity Mapping
- For multi-location files: how to identify each entity?
- Sheet name = entity name?
- Entity ID in specific cell?

## Step 2: Build Core Utilities (If Not Exists)

```python
# etl/sources/spreadsheets/core.py
import re
from pathlib import Path
from typing import Iterator
from datetime import datetime

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


def load_workbook(file_path: str | Path) -> Workbook:
    """Load Excel workbook with data values (not formulas)."""
    return openpyxl.load_workbook(
        file_path,
        data_only=True,  # Get calculated values, not formulas
        read_only=True,  # Memory efficient for large files
    )


def sheet_to_grid(sheet: Worksheet) -> list[list]:
    """Convert worksheet to 2D list of values."""
    return [[cell for cell in row] for row in sheet.iter_rows(values_only=True)]


def find_header_row(
    grid: list[list],
    required_keywords: list[str],
    max_rows: int = 20,
) -> int | None:
    """Find the row index containing header keywords."""
    required_lower = [k.lower() for k in required_keywords]

    for i, row in enumerate(grid[:max_rows]):
        row_text = " ".join(str(cell).lower() for cell in row if cell)
        if all(kw in row_text for kw in required_lower):
            return i

    return None


def build_column_map(
    header_row: list,
    patterns: dict[str, str],
) -> dict[str, int]:
    """Map logical names to column indices using regex patterns.

    Args:
        header_row: List of header cell values
        patterns: Dict of {logical_name: regex_pattern}

    Returns:
        Dict of {logical_name: column_index}
    """
    column_map = {}

    for col_idx, header in enumerate(header_row):
        if header is None:
            continue
        header_str = str(header).strip()

        for name, pattern in patterns.items():
            if re.search(pattern, header_str, re.IGNORECASE):
                column_map[name] = col_idx
                break

    return column_map


def extract_month_columns(
    header_row: list,
    start_col: int = 0,
) -> list[tuple[int, str]]:
    """Extract columns that represent time periods (e.g., 'Jan 2024', 'FY2024-01').

    Returns list of (column_index, period_string) tuples.
    """
    month_patterns = [
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{2,4}",
        r"FY\d{4}-\d{2}",
        r"\d{4}-\d{2}",
        r"Q[1-4]\s*\d{4}",
    ]
    combined_pattern = "|".join(f"({p})" for p in month_patterns)

    periods = []
    for col_idx, header in enumerate(header_row[start_col:], start=start_col):
        if header and re.search(combined_pattern, str(header), re.IGNORECASE):
            periods.append((col_idx, str(header).strip()))

    return periods


def parse_period_to_date(period_str: str) -> datetime | None:
    """Parse period string to datetime.

    Handles: 'Jan 2024', 'FY2024-01', '2024-01', 'Q1 2024'
    """
    import pendulum

    period_str = period_str.strip()

    # FY2024-01 format
    if match := re.match(r"FY(\d{4})-(\d{2})", period_str):
        return pendulum.datetime(int(match.group(1)), int(match.group(2)), 1)

    # 2024-01 format
    if match := re.match(r"(\d{4})-(\d{2})", period_str):
        return pendulum.datetime(int(match.group(1)), int(match.group(2)), 1)

    # Jan 2024 format
    try:
        return pendulum.parse(period_str, strict=False)
    except:
        pass

    # Q1 2024 format
    if match := re.match(r"Q([1-4])\s*(\d{4})", period_str, re.IGNORECASE):
        quarter = int(match.group(1))
        year = int(match.group(2))
        month = (quarter - 1) * 3 + 1
        return pendulum.datetime(year, month, 1)

    return None


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Handle strings with currency symbols, commas
        cleaned = re.sub(r"[,$()]", "", str(value))
        if cleaned.strip() in ("", "-", "—"):
            return default
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def safe_string(value, default: str = "") -> str:
    """Safely convert value to string."""
    if value is None:
        return default
    return str(value).strip()
```

## Step 3: Create Base Template

```python
# etl/sources/spreadsheets/templates/base.py
from abc import ABC, abstractmethod
from typing import Iterator
from openpyxl.workbook import Workbook


class BaseTemplate(ABC):
    """Abstract base class for spreadsheet templates."""

    @classmethod
    @abstractmethod
    def detect(cls, workbook: Workbook) -> float:
        """Detect if this template matches the workbook.

        Returns:
            Confidence score 0.0 to 1.0 (0 = no match, 1 = certain match)
        """
        pass

    @classmethod
    @abstractmethod
    def get_entity_mapping(cls, workbook: Workbook) -> dict[str, str]:
        """Map sheet names to entity identifiers.

        Returns:
            Dict of {sheet_name: entity_id}
        """
        pass

    @classmethod
    @abstractmethod
    def extract(cls, workbook: Workbook, entity_mapping: dict[str, str]) -> Iterator[dict]:
        """Extract fact records from workbook.

        Yields:
            Normalized fact records
        """
        pass
```

## Step 4: Implement Concrete Template

### Example: Income Statement Template

```python
# etl/sources/spreadsheets/templates/income_statement.py
import re
import pendulum
from typing import Iterator
from openpyxl.workbook import Workbook

from .base import BaseTemplate
from ..core import (
    sheet_to_grid,
    find_header_row,
    build_column_map,
    extract_month_columns,
    parse_period_to_date,
    safe_float,
    safe_string,
)


class IncomeStatementTemplate(BaseTemplate):
    """Template for standard income statement spreadsheets."""

    # Detection keywords
    DETECTION_KEYWORDS = ["revenue", "expense", "income", "profit"]

    # Column patterns for mapping
    COLUMN_PATTERNS = {
        "category": r"(category|account|description|item)",
        "subcategory": r"(sub.?category|detail|line.?item)",
    }

    @classmethod
    def detect(cls, workbook: Workbook) -> float:
        """Detect income statement format."""
        score = 0.0

        for sheet in workbook.worksheets:
            grid = sheet_to_grid(sheet)
            text = " ".join(
                str(cell).lower()
                for row in grid[:30]
                for cell in row
                if cell
            )

            # Check for keywords
            matches = sum(1 for kw in cls.DETECTION_KEYWORDS if kw in text)
            if matches >= 2:
                score = max(score, 0.5 + (matches * 0.1))

            # Check for period columns
            header_row_idx = find_header_row(grid, ["category"])
            if header_row_idx is not None:
                periods = extract_month_columns(grid[header_row_idx])
                if len(periods) >= 3:
                    score = max(score, 0.8)

        return min(score, 1.0)

    @classmethod
    def get_entity_mapping(cls, workbook: Workbook) -> dict[str, str]:
        """Map sheet names to entity IDs.

        Assumes sheet names are entity/location names.
        """
        mapping = {}
        skip_sheets = {"summary", "total", "consolidated", "template"}

        for sheet in workbook.worksheets:
            name = sheet.title.strip()
            name_lower = name.lower()

            # Skip non-entity sheets
            if any(skip in name_lower for skip in skip_sheets):
                continue

            # Use sheet name as entity ID (normalized)
            entity_id = re.sub(r"[^a-z0-9]+", "_", name_lower).strip("_")
            mapping[name] = entity_id

        return mapping

    @classmethod
    def extract(
        cls,
        workbook: Workbook,
        entity_mapping: dict[str, str],
    ) -> Iterator[dict]:
        """Extract income statement line items."""

        for sheet_name, entity_id in entity_mapping.items():
            sheet = workbook[sheet_name]
            grid = sheet_to_grid(sheet)

            # Find header row
            header_row_idx = find_header_row(
                grid,
                required_keywords=["category"],
                max_rows=20,
            )
            if header_row_idx is None:
                continue

            header_row = grid[header_row_idx]

            # Build column map
            column_map = build_column_map(header_row, cls.COLUMN_PATTERNS)
            if "category" not in column_map:
                continue

            # Find period columns
            periods = extract_month_columns(header_row)
            if not periods:
                continue

            # Extract data rows
            current_category = None

            for row_idx in range(header_row_idx + 1, len(grid)):
                row = grid[row_idx]
                if not any(row):  # Skip empty rows
                    continue

                # Get category (may be hierarchical)
                category_val = safe_string(row[column_map["category"]])
                if category_val:
                    current_category = category_val

                # Get subcategory if available
                subcategory = None
                if "subcategory" in column_map:
                    subcategory = safe_string(row[column_map["subcategory"]])

                # Skip if no category context
                if not current_category:
                    continue

                # Extract values for each period
                for col_idx, period_str in periods:
                    amount = safe_float(row[col_idx])

                    # Skip zero/empty values
                    if amount == 0.0:
                        continue

                    period_date = parse_period_to_date(period_str)

                    yield {
                        "entity_id": entity_id,
                        "entity_name": sheet_name,
                        "period": period_str,
                        "period_date": period_date.isoformat() if period_date else None,
                        "category": current_category,
                        "subcategory": subcategory,
                        "amount": amount,
                        "_etl_source": "income_statement_template",
                        "_etl_extracted_at": pendulum.now().isoformat(),
                    }
```

### Handling Different Layouts

#### Pivot-Style (Periods as Columns)

```python
# Periods are column headers
# Row 1: | Category | Jan 2024 | Feb 2024 | Mar 2024 |
# Row 2: | Revenue  | 10000    | 12000    | 11000    |

def extract_pivot(cls, workbook, entity_mapping):
    for sheet_name, entity_id in entity_mapping.items():
        grid = sheet_to_grid(workbook[sheet_name])
        header_row = grid[0]

        periods = extract_month_columns(header_row, start_col=1)

        for row in grid[1:]:
            category = safe_string(row[0])
            if not category:
                continue

            for col_idx, period_str in periods:
                yield {
                    "entity_id": entity_id,
                    "category": category,
                    "period": period_str,
                    "amount": safe_float(row[col_idx]),
                }
```

#### Transactional (Standard Table)

```python
# Standard tabular format
# | Date       | Category | Amount | Description |
# | 2024-01-15 | Revenue  | 500    | Sale #123   |

def extract_transactional(cls, workbook, entity_mapping):
    for sheet_name, entity_id in entity_mapping.items():
        grid = sheet_to_grid(workbook[sheet_name])
        header_row = grid[0]

        column_map = build_column_map(header_row, {
            "date": r"date",
            "category": r"category|type",
            "amount": r"amount|value",
            "description": r"description|memo|notes",
        })

        for row in grid[1:]:
            yield {
                "entity_id": entity_id,
                "date": row[column_map["date"]],
                "category": safe_string(row[column_map["category"]]),
                "amount": safe_float(row[column_map["amount"]]),
                "description": safe_string(row[column_map.get("description", -1)]),
            }
```

## Step 5: Build the DLT Source

```python
# etl/sources/spreadsheets/income_statement_source.py
import dlt
import pendulum
from pathlib import Path
from typing import Iterator

from .core import load_workbook
from .templates.income_statement import IncomeStatementTemplate


@dlt.source(name="income_statement")
def income_statement_source(
    file_path: str,
    entity_mapping: dict[str, str] | None = None,
):
    """DLT source for income statement spreadsheets."""

    workbook = load_workbook(file_path)

    # Auto-detect entity mapping if not provided
    if entity_mapping is None:
        entity_mapping = IncomeStatementTemplate.get_entity_mapping(workbook)

    return [
        income_statement_facts(workbook, entity_mapping),
    ]


@dlt.resource(
    name="income_statement_facts",
    write_disposition="merge",
    primary_key=["entity_id", "period", "category", "subcategory"],
)
def income_statement_facts(
    workbook,
    entity_mapping: dict[str, str],
) -> Iterator[dict]:
    """Extract income statement facts."""
    yield from IncomeStatementTemplate.extract(workbook, entity_mapping)
```

## Step 6: Build the Runner

```python
# etl/runners/income_statement.py
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from etl.core.pipeline import BasePipelineRunner, PipelineConfig
from etl.core.cli import setup_logging
from etl.sources.spreadsheets.core import load_workbook
from etl.sources.spreadsheets.income_statement_source import income_statement_source
from etl.sources.spreadsheets.templates.income_statement import IncomeStatementTemplate

app = typer.Typer(help="Income Statement ETL Pipeline")
console = Console()


class IncomeStatementRunner(BasePipelineRunner):
    """Runner for income statement pipeline."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    @property
    def pipeline_name(self) -> str:
        return "income_statement_pipeline"

    @property
    def dataset_name(self) -> str:
        return "financials"

    @property
    def pipeline_emoji(self) -> str:
        return "📊"

    @property
    def pipeline_description(self) -> str:
        return "Income Statement"

    def get_source(self, config, **kwargs):
        return income_statement_source(
            file_path=self.file_path,
            entity_mapping=kwargs.get("entity_mapping"),
        )

    def get_resources_config(self) -> dict[str, bool]:
        return {"income_statement_facts": False}


# --- CLI Commands ---

@app.command()
def run(
    file: Path = typer.Argument(..., help="Path to Excel file"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Use DuckDB"),
    log_level: str = typer.Option("WARNING", "--log-level", "-l"),
):
    """Load income statement from spreadsheet."""
    setup_logging(log_level)

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    config = PipelineConfig(dry_run=dry_run, log_level=log_level)
    runner = IncomeStatementRunner(str(file))
    runner.run(config)


@app.command()
def detect(
    file: Path = typer.Argument(..., help="Path to Excel file"),
):
    """Detect template and show entity mapping."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    workbook = load_workbook(file)

    # Detection
    confidence = IncomeStatementTemplate.detect(workbook)
    console.print(f"[bold]Template Detection[/bold]")
    console.print(f"  Income Statement: {confidence:.0%} confidence")

    if confidence < 0.5:
        console.print("[yellow]Warning: Low confidence match[/yellow]")

    # Entity mapping
    mapping = IncomeStatementTemplate.get_entity_mapping(workbook)

    table = Table(title="Entity Mapping")
    table.add_column("Sheet Name")
    table.add_column("Entity ID")

    for sheet, entity_id in mapping.items():
        table.add_row(sheet, entity_id)

    console.print(table)


@app.command()
def preview(
    file: Path = typer.Argument(..., help="Path to Excel file"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of records"),
):
    """Preview extracted data without loading."""
    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    workbook = load_workbook(file)
    mapping = IncomeStatementTemplate.get_entity_mapping(workbook)

    table = Table(title=f"Preview (first {limit} records)")
    table.add_column("Entity")
    table.add_column("Period")
    table.add_column("Category")
    table.add_column("Amount", justify="right")

    count = 0
    for record in IncomeStatementTemplate.extract(workbook, mapping):
        if count >= limit:
            break
        table.add_row(
            record["entity_id"],
            record["period"],
            record["category"],
            f"{record['amount']:,.2f}",
        )
        count += 1

    console.print(table)
    console.print(f"\n[dim]Showing {count} of extracted records[/dim]")


if __name__ == "__main__":
    app()
```

## Template Auto-Detection

For projects with multiple templates:

```python
# etl/sources/spreadsheets/templates/__init__.py
from .base import BaseTemplate
from .income_statement import IncomeStatementTemplate
# from .inventory import InventoryTemplate
# from .sales_report import SalesReportTemplate

ALL_TEMPLATES: list[type[BaseTemplate]] = [
    IncomeStatementTemplate,
    # InventoryTemplate,
    # SalesReportTemplate,
]


def detect_template(workbook) -> tuple[type[BaseTemplate] | None, float]:
    """Auto-detect the best matching template.

    Returns:
        Tuple of (template_class, confidence_score)
    """
    best_match = None
    best_score = 0.0

    for template_cls in ALL_TEMPLATES:
        score = template_cls.detect(workbook)
        if score > best_score:
            best_score = score
            best_match = template_cls

    if best_score < 0.5:
        return None, best_score

    return best_match, best_score
```

## Common Patterns

### Multi-Section Sheets

When a sheet has multiple sections:

```python
def extract(cls, workbook, entity_mapping):
    for sheet_name, entity_id in entity_mapping.items():
        grid = sheet_to_grid(workbook[sheet_name])

        # Find section headers
        sections = []
        for row_idx, row in enumerate(grid):
            first_cell = safe_string(row[0])
            if first_cell.upper() in ["REVENUE", "EXPENSES", "OTHER"]:
                sections.append((row_idx, first_cell))

        # Extract each section
        for i, (start_idx, section_name) in enumerate(sections):
            end_idx = sections[i + 1][0] if i + 1 < len(sections) else len(grid)

            for row_idx in range(start_idx + 1, end_idx):
                row = grid[row_idx]
                # ... extract with section context
```

### Merged Cells

Handle merged cells in headers:

```python
def get_unmerged_headers(sheet):
    """Get header row with merged cell values propagated."""
    headers = list(sheet.iter_rows(min_row=1, max_row=1, values_only=True))[0]

    # Fill merged cell gaps
    last_value = None
    result = []
    for val in headers:
        if val is not None:
            last_value = val
        result.append(last_value)

    return result
```

### Date Parsing Edge Cases

```python
def parse_flexible_date(value) -> datetime | None:
    """Parse dates in various formats."""
    if value is None:
        return None

    # Already a datetime
    if isinstance(value, datetime):
        return value

    # Excel serial date
    if isinstance(value, (int, float)) and 1 < value < 100000:
        from openpyxl.utils.datetime import from_excel
        return from_excel(value)

    # String parsing
    import pendulum
    try:
        return pendulum.parse(str(value), strict=False)
    except:
        return None
```

## Checklist

Before completing a spreadsheet pipeline:

- [ ] Template has `detect()` returning appropriate confidence
- [ ] Template handles missing/optional columns gracefully
- [ ] Entity mapping works for single and multi-sheet files
- [ ] Period parsing handles expected date formats
- [ ] Numeric parsing handles currency symbols, negatives, blanks
- [ ] DLT resource has appropriate primary key
- [ ] Runner has detect and preview commands for validation
- [ ] Empty rows/sections are skipped properly
- [ ] Makefile targets added for preview/test/run/schema commands
