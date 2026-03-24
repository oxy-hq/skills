---
name: oxy:validate
description: Validate all Oxy configuration files (config.yml, agents, workflows, semantic layer)
activeForm: Validating Oxy configuration
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
---

# Validate Oxy Configuration

Validate all Oxy configuration files in the current project to catch errors before running workflows or agents.

## What to Validate

`oxy validate` checks these file types:
1. **Agent files** - All `.agent.yml` files
2. **Workflow files** - All `.workflow.yml` and `.procedure.yml` files
3. **App files** - All `.app.yml` files

**Note:** `oxy validate` does NOT process semantic layer files (`.view.yml`, `.topic.yml`).
Use `oxy build` to validate and compile the semantic layer.

**Note:** `config.yml` is validated automatically when any oxy command loads the
configuration — you do not need to run a separate validate step for it.

## Steps

1. **Check for Oxy installation**
   - Run `oxy --version` to verify Oxy CLI is installed
   - If not found, inform the user they need to install Oxy first

2. **Run validation**
   - Execute `oxy validate` command
   - This validates config.yml, all agent files, and all workflow files

3. **Report results**
   - If validation passes: Report success with summary
   - If validation fails:
     - Show all errors with file paths and line numbers
     - Explain what each error means in clear terms
     - Suggest fixes where possible

## Error Handling

Common validation errors and how to help:

- **YAML syntax errors**: Show the line with the error and suggest the fix
- **Missing required fields**: List which fields are missing and what values they should have
- **Invalid references**: Explain which referenced entity/view/dimension doesn't exist
- **Type mismatches**: Show expected vs actual types

## Success Message

When validation passes, show a clear success message like:

```
✅ Oxy validation passed!

Validated:
- X agent files
- Y workflow files
- Z app files

Your Oxy project is ready to run.
Note: To validate the semantic layer, run `oxy build`.
```

## Notes

- Always run from the project root directory (where config.yml is located)
- This command doesn't modify any files, it only checks them
- Run this before `/oxy:test` to catch workflow/agent/app errors early
- For semantic layer errors, use `/oxy:build` instead
