---
name: oxygen:test
description: Run evaluation tests on agent or workflow files
activeForm: Testing Oxygen agents/workflows
argument-hint: "[file-path]"
allowed-tools:
  - Bash
  - Read
  - Glob
  - AskUserQuestion
  - Write
---

# Test Oxygen Agents and Workflows

Run evaluation tests defined in agent or workflow configuration files to validate reliability and output quality.

## Pre-Test Steps

1. **Check for Oxygen installation**
   - Run `oxygen --version` to verify Oxygen CLI is installed
   - If not found, inform the user they need to install Oxygen first

2. **Determine test file**
   - If command invoked with argument (file path), use that file
   - If no argument:
     - Check if there's a currently open file in the editor
     - If it's a `.agent.yml` or `.workflow.yml` file, use it
     - Otherwise, ask user to specify which file to test using AskUserQuestion

## File Selection (if needed)

If no file specified:
1. Search for test files using Glob: `**/*.agent.yml` and `**/*.workflow.yml`
2. Use AskUserQuestion to let user select which file to test
3. Options should show clear file paths

## Test Execution

1. **Run tests**
   - Execute `oxygen test <file-path>` with default options
   - Use pretty format for readable output
   - Show test progress to user

2. **Monitor test execution**
   - Display each test case as it runs
   - Show which assertions pass/fail

## Results Summary

After tests complete, provide a clear summary:

### If all tests pass:
```
✅ All tests passed!

File: <file-path>
Test cases: X passed, 0 failed
Accuracy: 100%

Your agent/workflow is ready to use.
```

### If tests fail:
```
⚠️  Some tests failed

File: <file-path>
Test cases: X passed, Y failed
Accuracy: Z%

Failed tests:
1. [Test name]: [Reason for failure]
2. [Test name]: [Reason for failure]

Review the test configuration and agent/workflow logic.
```

## Error Handling

Common issues:
- **No tests defined**: File has no `tests:` section - inform user they need to add tests
- **File not found**: Verify the file path is correct
- **Invalid test format**: Check test configuration syntax in the YAML file
- **Execution error**: Show the error and suggest checking agent/workflow configuration

## Test Options

The command uses these defaults (recommended for most cases):
- Format: Pretty (human-readable)
- Threshold mode: Average (overall accuracy)
- Min accuracy: Not enforced (show results regardless)

For advanced testing options, users can run `oxygen test` directly in terminal.

## Notes

- Tests validate that agents/workflows produce expected outputs
- Test cases are defined in the `tests:` section of `.agent.yml` or `.workflow.yml` files
- Tests help ensure reliability before deploying to production
- Re-run tests after modifying agent/workflow logic
