/*
oxy:
  description: "Brief description of what this query does and its purpose"
  variables:
    start_date:
      type: string
      description: "Start date for the date range filter (YYYY-MM-DD)"
      # Optional: Add enum for predefined values
      # enum:
      #   - "2024-01-01"
      #   - "2024-06-01"

    end_date:
      type: string
      description: "End date for the date range filter (YYYY-MM-DD)"

    # Example: Number variable
    # limit:
    #   type: number
    #   description: "Maximum number of results to return"
    #   default: 100

    # Example: Boolean variable
    # include_cancelled:
    #   type: boolean
    #   description: "Whether to include cancelled orders"
    #   default: false

    # Example: Enum variable
    # status:
    #   type: string
    #   description: "Order status to filter by"
    #   enum:
    #     - "pending"
    #     - "completed"
    #     - "cancelled"
*/

-- Main query
SELECT
    column1,
    column2,
    SUM(metric_column) as total_metric,
    COUNT(*) as record_count
FROM {{ databases.database_name.schema_name }}.table_name
WHERE
    date_column >= '{{ start_date }}'
    AND date_column <= '{{ end_date }}'
    {% if include_cancelled %}
    -- Include all statuses
    {% else %}
    AND status != 'cancelled'
    {% endif %}
GROUP BY
    column1,
    column2
ORDER BY
    total_metric DESC
LIMIT {{ limit | default(100) }};

/*
Usage:
  oxygen run query_name.sql -v start_date=2024-01-01 -v end_date=2024-12-31

Best Practices:
  - Define all variables in the oxy front matter with types and descriptions
  - Use {{ databases.db_name.schema }}.table for table references
  - Use {{ variable_name }} for Jinja2 variable substitution
  - Test with --dry-run before executing: oxygen run query_name.sql --dry-run
  - Keep queries focused on a single purpose
  - Add enums for variables with predefined valid values
  - Set sensible defaults where appropriate
*/
