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

Check all of these file types:
1. **config.yml** - Project configuration
2. **Agent files** - All `.agent.yml` files
3. **Workflow files** - All `.workflow.yml` files
4. **Semantic layer** - All `.view.yml` and `.topic.yml` files

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
- config.yml
- X agent files
- Y workflow files
- Z semantic layer files (if applicable)

Your Oxy project is ready to run.
```

## Notes

- Always run from the project root directory (where config.yml is located)
- This command doesn't modify any files, it only checks them
- Run this before `/oxy:build` or `/oxy:test` to catch errors early
