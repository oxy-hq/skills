---
name: oxy:build-instance
description: Build a complete Oxy analytics instance from scratch — semantic layer, workflows + agents, optional ETL pipeline, and executive dashboard app. Runs all 4 core skills in sequence. Use in a fresh oxy project directory.
activeForm: Building oxy instance
argument-hint: "[--no-etl]  (optional: skip ETL pipeline step)"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Build Oxy Instance

Build a complete Oxy analytics instance by running the 4 core skills in sequence:
semantic layer → workflows & agents → ETL pipeline (optional) → dashboard app.

Parse the argument: if `--no-etl` was passed, skip Step 4 (ETL).

---

## Step 1: Environment Setup

Before building anything, verify the project is properly configured. If anything is
missing, pause and help the user set it up before continuing.

### 1a. Check for config.yml

Run: `ls config.yml 2>/dev/null && echo "EXISTS" || echo "MISSING"`

If **MISSING**, create it now. Ask the user which database type they are using, then
generate a `config.yml` using the appropriate template below:

**ClickHouse (e.g. restaurant analytics):**
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/config.json
defaults:
  database: clickhouse

models:
  - vendor: openai
    name: openai-4.1
    model_ref: gpt-4.1
    key_var: OPENAI_API_KEY
    api_url: https://api.openai.com/v1

  - vendor: anthropic
    name: claude-sonnet-4-6
    model_ref: claude-sonnet-4-6
    key_var: ANTHROPIC_API_KEY

databases:
  - name: clickhouse
    type: clickhouse
    host_var: CLICKHOUSE_HOST
    user_var: CLICKHOUSE_USERNAME
    password_var: CLICKHOUSE_PASSWORD
    database_var: CLICKHOUSE_DATABASE
    schemas:
      your_schema_name:
        - "your_schema_name___*"   # adjust to match your table prefix pattern
```

**Snowflake (e.g. HubSpot / enterprise):**
```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/oxy-hq/oxy/refs/heads/main/json-schemas/config.json
databases:
  - name: snowflake
    type: snowflake
    account: YOUR_ACCOUNT_IDENTIFIER   # e.g. SW55517-HUBSPOT
    username: your@email.com
    warehouse: YOUR_WAREHOUSE
    database: YOUR_DATABASE
    role: YOUR_ROLE

models:
  - name: openai
    vendor: openai
    model_ref: gpt-4.1
    key_var: OPENAI_API_KEY
```

### 1b. Check for .env

Run: `ls .env 2>/dev/null && echo "EXISTS" || echo "MISSING"`

If **MISSING**, create a `.env` file using the appropriate template:

**ClickHouse:**
```bash
# ClickHouse connection
CLICKHOUSE_HOST=https://your-host.clickhouse.cloud:8123   # include https:// and port
CLICKHOUSE_USERNAME=your_username
CLICKHOUSE_PASSWORD=your_password
CLICKHOUSE_DATABASE=your_database

# AI model keys — at least one required
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...   # optional, for Claude models

# ETL sources (add as needed)
# TOAST_CLIENT_ID=...
# TOAST_CLIENT_SECRET=...
# TOAST_BASE_URL=https://ws-api.toasttab.com
```

**Snowflake:**
```bash
# Snowflake authentication
SNOWFLAKE_PASSWORD=your_password   # or use private key auth (see config.yml)

# AI model keys
OPENAI_API_KEY=sk-...
```

### 1c. Verify OpenAI key is accessible

The retrieval tool used by agents requires an OpenAI API key for embeddings.

Check: `grep -r "OPENAI_API_KEY" .env 2>/dev/null | head -1`

If not found in `.env`, check the shell environment: `echo ${OPENAI_API_KEY:0:7}`

If neither has it, ask the user to add it. They can add it to `.env`:
```
OPENAI_API_KEY=sk-...
```
Or permanently to their shell:
```bash
echo 'export OPENAI_API_KEY=sk-...' >> ~/.zshrc && source ~/.zshrc
```

Do not proceed until an OpenAI key is confirmed present.

### 1d. Schema discovery (conditional — oxy sync)

First, check whether view files already exist:
```bash
find semantics/views -name "*.view.yml" 2>/dev/null | wc -l
```

**If view files exist (count > 0):** Skip sync entirely. The semantic layer skill will
read the existing views directly. Proceed to Step 1e.

**If no view files exist (from-scratch build):** Run `oxy sync` to discover the schema —
but only after verifying the database has schema config in `config.yml`.

Check config.yml for a `schemas` (ClickHouse) or `datasets` (Snowflake) key under the
database entry. If missing, sync will connect but return 0 dimensions.

- **ClickHouse** needs `schemas` with table prefix patterns, e.g.:
  ```yaml
  schemas:
    your_schema_name:
      - "your_schema_name___*"
  ```
- **Snowflake** needs `datasets` with schema names, e.g.:
  ```yaml
  datasets:
    YOUR_SCHEMA_NAME:
      - "*"
  ```

If the schema config is present, run sync:
```bash
oxy sync
```

Verify `semantics.yml` is non-empty:
```bash
wc -l semantics.yml
```

If `semantics.yml` is empty (0 dimensions) after sync, stop and help the user fix
the connection or schema config before continuing. If sync cannot be resolved,
discover the schema manually: run `SHOW SCHEMAS IN DATABASE <db>;` (Snowflake) or
`SHOW TABLES FROM <schema>;` (ClickHouse) via a direct DB connection, then use that
output to inform the semantic layer build in Step 2.

### 1e. Start PostgreSQL for oxy build

**Pause here and ask the user to run the following in a separate terminal:**

```
oxy start --enterprise
```

Wait for the user to confirm it is running before proceeding. This is required for
`oxy build` in Step 2. Once confirmed, set the database URL for use in this session:

```bash
export OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy
```

Note: env vars don't persist between shell invocations in Claude Code, so prefix
`OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy` on any
`oxy build` or `oxy run` command that requires it.

---

## Step 2: Semantic Layer

Build the semantic layer for this project. Create one view file and one topic file per
table. The skill will read `semantics.yml` if it was produced by sync, or fall back to
reading existing view files or using schema information gathered in Step 1d.

_(The oxy-semantic-layer skill will activate and guide this step.)_

Wait until `oxy build` completes successfully before proceeding.

---

## Step 3: Workflows & Agents

Build operational workflows and a data analyst agent for this project. Use the semantic
layer we just built wherever possible — check existing views and topics before writing
raw SQL.

_(The oxy-workflow-builder skill will activate and guide this step.)_

Wait until all workflow and agent files are created and validated before proceeding.

---

## Step 4: ETL Pipeline

> **Skip this step if `--no-etl` was passed.**

Build an ETL pipeline for this project using DLT. Identify the relevant data sources
(APIs, spreadsheets, or files) from the project context and implement extraction into
the data warehouse.

_(The oxy-etl-builder skill will activate and guide this step.)_

Wait until runner files are created and `uv run python -m etl.runners.<runner> test`
passes before proceeding.

---

## Step 5: Dashboard App

Build an executive dashboard app that uses the workflows and agent we just created.
Reference workflow task outputs with dot notation (`workflow_name.task_name`). Include
a mix of KPI tables, trend charts, and AI-generated insights from the agent.

Before writing the app YAML, run the workflow and agent to confirm they execute cleanly:
```bash
OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy oxy run workflows/<workflow>.workflow.yml
OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy oxy run <agent>.agent.yml "summarize performance last week"
```

Fix any SQL errors before writing the app.

_(The oxy-app-builder skill will activate and guide this step.)_

---

## Step 6: Final Validation

Run a full validation pass across all generated files:

```bash
oxy validate
OXY_DATABASE_URL=postgresql://postgres:postgres@localhost:15432/oxy oxy build
```

If both pass, the instance is ready. Navigate to `http://localhost:3000` and open
the app (the `oxy start --enterprise` server from Step 1e should still be running).

Summarize what was built:
- Number of semantic layer views and topics created
- Workflow and agent files created
- ETL pipeline (if built): sources and runners
- App file and display count
