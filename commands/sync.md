---
name: oxygen:sync
description: Sync database metadata and schemas from configured databases
activeForm: Syncing database metadata
argument-hint: "[database-name]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
  - Write
---

# Sync Database Metadata

Extract and synchronize metadata, schemas, and table structures from your configured databases.

## Pre-Sync Steps

1. **Check for Oxygen installation**
   - Run `oxygen --version` to verify Oxygen CLI is installed
   - If not found, inform the user they need to install Oxygen first

2. **Read configuration**
   - Read `config.yml` to find configured databases
   - Extract the list of database names under the `databases:` section
   - If no databases configured, inform user and stop

## Database Selection

1. **Interactive selection**
   - Use AskUserQuestion to ask which database(s) to sync
   - Options:
     - Each configured database as individual option
     - "All databases" option
   - Allow single selection (recommend one database at a time for clarity)

2. **Handle selection**
   - If user selects specific database: `oxygen sync <database-name>`
   - If user selects "All databases": `oxygen sync` (without database argument)

## Sync Process

1. **Execute sync command**
   - Run the appropriate `oxygen sync` command based on selection
   - Show progress output to user

2. **Monitor completion**
   - Wait for sync to complete
   - Capture any errors or warnings

## Success Actions

When sync completes successfully:

1. **Report results**
   ```
   ✅ Database sync completed!

   Synced: <database-name>
   Schema files saved to: .databases/<database-name>/

   Tables synchronized: X
   ```

2. **Show next steps**
   - Suggest: "Schema files are now available in .databases/ directory"
   - Suggest: "You can now create semantic layer views based on these schemas"
   - Suggest: "Run /oxygen:build to compile your semantic layer"

## Error Handling

If sync fails:
- Show the full error message
- Common issues and solutions:
  - **Connection failed**: Check database credentials in config.yml
  - **Database not found**: Verify database name in config.yml
  - **Authentication failed**: Check API keys or credentials in environment variables
  - **Network error**: Verify database host is accessible

## Notes

- Schema files are saved to `.databases/<database-name>/` directory
- These files are used when building semantic layer views
- Re-run sync after database schema changes (new tables, columns, etc.)
- Sync does not modify your database, only reads metadata
