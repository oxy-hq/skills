"""
Spreadsheet Template Template
=============================

Template for building spreadsheet parsers with:
- Auto-detection of file format
- Entity mapping for multi-sheet files
- Column extraction with flexible patterns
- Period/date parsing

Replace <TemplateName> with your actual template name.
"""

import re
from abc import ABC, abstractmethod
from typing import Iterator

import pendulum
from openpyxl.workbook import Workbook

# Import core utilities (adjust path)
# from ..core import (
#     sheet_to_grid,
#     find_header_row,
#     build_column_map,
#     extract_month_columns,
#     parse_period_to_date,
#     safe_float,
#     safe_string,
# )


# =============================================================================
# Placeholder utilities - replace with imports from core.py
# =============================================================================

def sheet_to_grid(sheet) -> list[list]:
    """Convert worksheet to 2D list."""
    return [[cell for cell in row] for row in sheet.iter_rows(values_only=True)]


def find_header_row(grid, required_keywords, max_rows=20) -> int | None:
    """Find row containing header keywords."""
    required_lower = [k.lower() for k in required_keywords]
    for i, row in enumerate(grid[:max_rows]):
        row_text = " ".join(str(cell).lower() for cell in row if cell)
        if all(kw in row_text for kw in required_lower):
            return i
    return None


def build_column_map(header_row, patterns) -> dict[str, int]:
    """Map logical names to column indices."""
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


def extract_month_columns(header_row, start_col=0) -> list[tuple[int, str]]:
    """Extract period columns from header row."""
    patterns = [
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{2,4}",
        r"FY\d{4}-\d{2}",
        r"\d{4}-\d{2}",
    ]
    combined = "|".join(f"({p})" for p in patterns)
    periods = []
    for col_idx, header in enumerate(header_row[start_col:], start=start_col):
        if header and re.search(combined, str(header), re.IGNORECASE):
            periods.append((col_idx, str(header).strip()))
    return periods


def parse_period_to_date(period_str):
    """Parse period string to datetime."""
    try:
        return pendulum.parse(period_str, strict=False)
    except:
        return None


def safe_float(value, default=0.0) -> float:
    """Safely convert to float."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = re.sub(r"[,$()]", "", str(value))
        return float(cleaned) if cleaned.strip() not in ("", "-") else default
    except:
        return default


def safe_string(value, default="") -> str:
    """Safely convert to string."""
    return str(value).strip() if value else default


# =============================================================================
# Base Template
# =============================================================================

class BaseTemplate(ABC):
    """
    Abstract base class for spreadsheet templates.

    Subclass this and implement the abstract methods for each
    spreadsheet format you need to parse.
    """

    @classmethod
    @abstractmethod
    def detect(cls, workbook: Workbook) -> float:
        """
        Detect if this template matches the workbook.

        Args:
            workbook: openpyxl Workbook object

        Returns:
            Confidence score 0.0 to 1.0
            - 0.0: Definitely not this template
            - 0.5: Uncertain
            - 1.0: Definitely this template
        """
        pass

    @classmethod
    @abstractmethod
    def get_entity_mapping(cls, workbook: Workbook) -> dict[str, str]:
        """
        Map sheet names to entity identifiers.

        For multi-entity files (e.g., one sheet per restaurant),
        return a mapping of sheet names to entity IDs.

        Args:
            workbook: openpyxl Workbook object

        Returns:
            Dict of {sheet_name: entity_id}
        """
        pass

    @classmethod
    @abstractmethod
    def extract(
        cls,
        workbook: Workbook,
        entity_mapping: dict[str, str],
    ) -> Iterator[dict]:
        """
        Extract fact records from workbook.

        Args:
            workbook: openpyxl Workbook object
            entity_mapping: Result from get_entity_mapping()

        Yields:
            Normalized fact records as dicts
        """
        pass


# =============================================================================
# Example Template Implementation
# =============================================================================

class IncomeStatementTemplate(BaseTemplate):
    """
    Template for income statement spreadsheets.

    Expected format:
    - Multiple sheets (one per entity/location)
    - Pivot-style layout: categories in rows, periods in columns
    - Headers contain "Category" and period columns (e.g., "Jan 2024")
    """

    # Keywords for detection
    DETECTION_KEYWORDS = ["revenue", "expense", "income", "profit"]

    # Column patterns for mapping
    COLUMN_PATTERNS = {
        "category": r"(category|account|description|item)",
        "subcategory": r"(sub.?category|detail|line.?item)",
    }

    # Sheets to skip (summary/total sheets)
    SKIP_SHEETS = {"summary", "total", "consolidated", "template", "instructions"}

    @classmethod
    def detect(cls, workbook: Workbook) -> float:
        """Detect income statement format."""
        score = 0.0

        for sheet in workbook.worksheets:
            grid = sheet_to_grid(sheet)

            # Get text from first 30 rows for keyword matching
            text = " ".join(
                str(cell).lower()
                for row in grid[:30]
                for cell in row
                if cell
            )

            # Check for detection keywords
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
        """Map sheet names to entity IDs."""
        mapping = {}

        for sheet in workbook.worksheets:
            name = sheet.title.strip()
            name_lower = name.lower()

            # Skip non-entity sheets
            if any(skip in name_lower for skip in cls.SKIP_SHEETS):
                continue

            # Normalize name to entity ID
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

                # Skip empty rows
                if not any(row):
                    continue

                # Get category
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


# =============================================================================
# Template Registry
# =============================================================================

ALL_TEMPLATES: list[type[BaseTemplate]] = [
    IncomeStatementTemplate,
    # Add more templates here as you create them
]


def detect_template(workbook: Workbook) -> tuple[type[BaseTemplate] | None, float]:
    """
    Auto-detect the best matching template for a workbook.

    Args:
        workbook: openpyxl Workbook object

    Returns:
        Tuple of (template_class, confidence_score)
        Returns (None, 0.0) if no template matches with confidence > 0.5
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
