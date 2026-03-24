---
name: oxy:build
description: Build Oxy semantic layer and vector embeddings
activeForm: Building Oxy semantic layer
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
---

# Build Oxy Semantic Layer

Compile the semantic layer definitions into Cube.js schema and build vector embeddings for semantic search.

## Pre-Build Steps

1. **Check for Oxy installation**
   - Run `oxy --version` to verify Oxy CLI is installed
   - If not found, inform the user they need to install Oxy first

2. **Check for semantic layer files**
   - Verify that `semantics/views/` and `semantics/topics/` directories exist and have files
   - If missing, inform the user they need to create view and topic files first
   - Note: `oxy validate` does NOT validate semantic layer files — `oxy build` is the
     correct command for this

## Build Process

1. **Execute build command**
   - Run `oxy build`
   - This compiles semantic layer definitions to Cube.js schema
   - Builds vector embeddings for semantic search

2. **Monitor output**
   - Show build progress to the user
   - Report any errors or warnings that occur during build

## Success Actions

When build completes successfully:

1. **Report success** with summary:
   ```
   ✅ Oxy build completed successfully!

   - Semantic layer compiled to Cube.js schema
   - Vector embeddings created

   Next steps:
   - Run `oxy semantic-engine --dev-mode` to test queries
   - Or use the semantic layer in your agents/workflows
   ```

2. **Offer next step**
   - Ask user if they want to start the semantic engine for testing
   - If yes, inform them to run `oxy semantic-engine --dev-mode` in their terminal

## Error Handling

If build fails:
- Show the full error message
- Identify which semantic layer file caused the error (if applicable)
- Suggest common fixes:
  - Check entity key references match dimension names
  - Verify all view names referenced in topics exist
  - Ensure SQL expressions in dimensions/measures are valid
  - Run `oxy sync` if database schema has changed

## Notes

- Build should be run after defining or modifying semantic layer files
- Requires a `semantics/` directory with view and topic files
- Database connections must be configured in config.yml
- Run `oxy sync` first if working with database schemas
