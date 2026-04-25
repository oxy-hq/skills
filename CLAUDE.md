# Claude Code Development Guide for Oxy Skills Plugin

This guide helps you work on the Oxy Skills plugin using Claude Code. It covers plugin architecture, development workflows, and best practices for using Claude's plugin-dev skills.

## Quick Start

When working on this plugin with Claude Code, you can use these specialized skills:

- `/plugin-dev:plugin-structure` - Understand plugin architecture and file organization
- `/plugin-dev:skill-development` - Create or modify skills
- `/plugin-dev:command-development` - Create or modify slash commands
- `/plugin-dev:agent-development` - Create or modify autonomous agents
- `/plugin-dev:hook-development` - Create event-driven hooks
- `/plugin-dev:plugin-settings` - Configure plugin settings

## Repository Structure

```text
oxy-template/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest and metadata
│   └── marketplace.json     # Marketplace publishing config
├── skills/                  # Auto-activating skills
│   ├── oxy-semantic-layer/
│   │   ├── SKILL.md         # Main skill instructions for Claude
│   │   ├── README.md        # User documentation
│   │   ├── QUICK-REFERENCE.md
│   │   └── *.yml            # Templates and examples
│   ├── oxy-workflow-builder/
│   │   └── ...
│   ├── oxy-etl-builder/
│   │   ├── SKILL.md         # ETL skill instructions
│   │   ├── README.md        # User documentation
│   │   ├── playbook-*.md    # Source-specific guides
│   │   └── templates/       # Code templates
│   ├── oxy-app-builder/
│   │   ├── SKILL.md         # App builder skill instructions
│   │   ├── README.md        # User documentation
│   │   ├── QUICK-REFERENCE.md
│   │   ├── templates/       # App templates
│   │   └── examples/        # Example prompts
│   └── oxy-test-drafter/
│       ├── SKILL.md         # Test drafter skill instructions
│       └── README.md        # User documentation
├── commands/                # Slash commands
│   ├── validate.md
│   ├── build.md
│   ├── sync.md
│   └── test.md
├── agents/                  # Autonomous agents
│   └── config-validator.md
└── examples/                # Demo projects and examples
    └── demo-project/
```

## Development Workflows

### Creating a New Skill

Use the skill-development skill to create new auto-activating skills:

```text
"Create a new skill for Oxy data modeling that helps users create
data models from existing views"
```

The skill-development skill will:

1. Guide you through the skill structure
2. Help write clear activation descriptions
3. Create the SKILL.md with proper frontmatter
4. Generate user-facing README.md
5. Add example templates

**Key Guidelines:**

- **SKILL.md**: Contains instructions for Claude on how to execute the skill
- **README.md**: User-facing documentation explaining what the skill does
- **Description**: Must clearly explain when the skill auto-activates
- Use progressive disclosure - start simple, add detail as needed
- Include concrete examples and templates

### Creating a New Command

Use the command-development skill to create slash commands:

```text
"Create a /oxy:deploy command that deploys the semantic layer
to production"
```

The command-development skill will:

1. Create the command file with YAML frontmatter
2. Generate bash implementation
3. Add argument parsing if needed
4. Include error handling

**Command Template:**

```markdown
---
name: oxy:command-name
description: Brief description of what this command does
---

#!/bin/bash

# Command implementation
oxy some-cli-command "$@"
```

### Creating a New Agent

Use the agent-development skill to create autonomous agents:

```text
"Create an agent that automatically suggests semantic layer improvements
when users create view files"
```

The agent-development skill will:

1. Design the agent's triggering conditions
2. Write system prompt and instructions
3. Configure available tools
4. Set activation timing (proactive vs on-demand)

**Agent Template:**

```markdown
---
name: agent-name
description: When this agent should activate and what it does
tools: [Read, Grep, Bash, Edit]
---

# Agent Title

You are an expert at [domain]. Your role is to [purpose].

## When to Activate

[Specific conditions when this agent should run]

## Core Tasks

[What the agent should do]

## Available Tools

[How to use each tool]
```

### Modifying Plugin Metadata

Edit [.claude-plugin/plugin.json](.claude-plugin/plugin.json) to update:

- Plugin name, version, and description
- Author information
- Keywords for discoverability
- Repository and homepage URLs

Use semantic versioning:

- **MAJOR**: Breaking changes to plugin API
- **MINOR**: New features (skills, commands, agents)
- **PATCH**: Bug fixes and documentation

### Testing Changes

When you make changes to skills, commands, or agents:

1. **Test locally** using the plugin directory:

   ```bash
   claude --plugin-dir /Users/luong/oxy-hq/oxy-template
   ```

2. **Verify skill activation**:

   ```text
   "Create a semantic layer view for my database"
   # Should activate oxy-semantic-layer skill
   ```

3. **Test commands**:

   ```text
   /oxy:validate
   /oxy:build
   ```

4. **Validate agent triggers**:
   Create or modify files that should trigger autonomous agents

## Plugin Architecture Patterns

### Skills vs Commands vs Agents

**Use Skills when:**

- User requests involve multi-step guided workflows
- Claude needs to make decisions based on context
- The task requires reading files, analyzing code, or generating content
- Example: "Build a semantic layer" - requires analyzing schemas, creating files, validating

**Use Commands when:**

- The task is a single, straightforward operation
- You're wrapping an existing CLI tool
- No decision-making is needed
- Example: `/oxy:build` - just runs `oxy build`

**Use Agents when:**

- The task should happen proactively/autonomously
- You want to validate or analyze code after certain events
- The agent can run without explicit user requests
- Example: config-validator runs automatically when YAML files are created

### File Organization

**Skills:**

- Each skill gets its own subdirectory under `skills/`
- SKILL.md is required and contains Claude instructions
- README.md provides user documentation
- QUICK-REFERENCE.md has syntax/API references
- Templates (*.yml, *.sql) provide scaffolding

**Commands:**

- Single markdown file per command
- YAML frontmatter for metadata
- Bash script in content
- Keep commands simple - complex logic belongs in skills

**Agents:**

- Single markdown file per agent
- YAML frontmatter with tools array
- Detailed instructions for autonomous operation
- Clear activation conditions

### Progressive Disclosure in Skills

Skills should reveal information progressively:

1. **Overview** - What the skill does (2-3 sentences)
2. **Core Workflow** - High-level steps
3. **Essential Commands** - Key CLI commands
4. **Detailed Patterns** - Specific examples and templates
5. **Advanced Usage** - Edge cases and optimizations
6. **Troubleshooting** - Common issues

**Example structure:**

```markdown
---
name: skill-name
description: Brief user-facing trigger description
---

# Skill Title

[2-3 sentence overview]

## Core Workflow

[High-level steps]

## Essential Commands

[Key commands]

## [Main Concept] Structure

[Detailed patterns with examples]

## Quality Guidelines

[Best practices]

## Common Issues

[Troubleshooting]
```

## Working with Oxy-Specific Content

### Understanding Oxy Concepts

When modifying skills or documentation, understand these Oxy concepts:

- **Semantic Layer**: Views and topics that map databases to natural language
- **Views**: Define entities, dimensions, and measures from database tables
- **Topics**: Organize views by business domain
- **Workflows**: Multi-step ETL/analysis pipelines
- **Agents**: AI-powered analysis using LLMs
- **ETL Pipelines**: Data extraction using DLT (data-load-tools) for loading into warehouses
- **Apps**: Interactive dashboards combining tasks (SQL, workflows, agents) with displays (tables, charts, markdown)

### Oxy CLI Integration

Commands should wrap Oxy CLI operations:

```bash
oxy sync          # Extract database schemas
oxy build         # Compile semantic layer
oxy validate      # Check configuration
oxy run           # Execute workflows
```

### File Conventions

Oxy projects use these file patterns:

- `*.view.yml` - Semantic layer views
- `*.topic.yml` - Topic definitions
- `*.workflow.yml` / `*.procedure.yml` - Workflow / procedure definitions
- `*.agent.yml` - Classic single-call AI agent configurations
- `*.agentic.yml` - Multi-step FSM analytics / app-builder agents
- `*.app.yml` - Data app definitions (dashboards)
- `*.test.yml` / `*.aw.test.yml` - Test suites for classic / agentic agents
- `config.yml` - Project configuration
- `semantics.yml` - Semantic layer entry point
- `etl/` - ETL pipeline directory (sources, runners, transforms)

## Best Practices

### Writing Skill Instructions

1. **Be specific about activation**: "Use when user asks to X, Y, or Z"
2. **Provide complete examples**: Include full YAML structures, not snippets
3. **Explain the why**: Document business logic, not just syntax
4. **Include error cases**: Common mistakes and how to fix them
5. **Reference external docs**: Link to official Oxy documentation

### Writing Commands

1. **Keep them simple**: Single responsibility per command
2. **Add error handling**: Check for required tools and files
3. **Support arguments**: Use `$@` to pass through args
4. **Provide feedback**: Echo what the command is doing
5. **Exit cleanly**: Use proper exit codes

### Writing Agents

1. **Clear triggers**: Explicitly state when the agent activates
2. **Scoped responsibilities**: Each agent should have one job
3. **Tool selection**: Only request tools the agent needs
4. **Proactive guidance**: Suggest fixes, don't just identify problems
5. **Non-intrusive**: Don't overwhelm users with constant validation

### Documentation

1. **Update README.md**: When adding features, update the main README
2. **Add examples**: Create demo files in `examples/demo-project/`
3. **Keep CLAUDE.md current**: Update this file when patterns change
4. **Use QUICK-REFERENCE.md**: For syntax and API references
5. **Link to official docs**: Don't duplicate, reference

## Common Development Tasks

### Adding a New Oxy Feature Skill

When Oxy adds a new feature (e.g., "data catalogs"), create a skill:

1. Use `/plugin-dev:skill-development` to scaffold
2. Read Oxy documentation to understand the feature
3. Create templates for file types the feature uses
4. Write examples in `examples/demo-project/`
5. Test with real Oxy projects

### Improving Existing Skills

When enhancing a skill:

1. Read the current SKILL.md to understand structure
2. Add new patterns or examples
3. Update QUICK-REFERENCE.md with new syntax
4. Test that existing functionality still works
5. Update version in plugin.json (MINOR bump)

### Fixing Bugs

When fixing issues:

1. Reproduce the bug in a test case
2. Identify the root cause (skill logic, command script, agent trigger)
3. Make minimal changes to fix
4. Test the fix with the reproduction case
5. Update version in plugin.json (PATCH bump)

### Adding Templates

When adding template files:

1. Create the template with example values
2. Add comments explaining each section
3. Reference the template in SKILL.md
4. Include in the skill's directory
5. Use clear, realistic example data

## Testing Checklist

Before committing changes:

- [ ] Plugin loads without errors: `claude --plugin-dir .`
- [ ] Skills activate with correct descriptions
- [ ] Commands execute successfully
- [ ] Agents trigger at the right time
- [ ] Examples in `examples/` run correctly
- [ ] Documentation is accurate and up-to-date
- [ ] Version number is updated in plugin.json
- [ ] No broken links in markdown files

## Plugin-Dev Skills Reference

Use these skills when working on this plugin:

| Skill                                  | Use Case                                      |
| -------------------------------------- | --------------------------------------------- |
| `/plugin-dev:plugin-structure`         | Understanding overall plugin architecture     |
| `/plugin-dev:skill-development`        | Creating or modifying skills                  |
| `/plugin-dev:command-development`      | Creating or modifying commands                |
| `/plugin-dev:agent-development`        | Creating or modifying agents                  |
| `/plugin-dev:hook-development`         | Adding event-driven hooks                     |
| `/plugin-dev:plugin-settings`          | Managing plugin configuration                 |
| `/plugin-dev:mcp-integration`          | Adding Model Context Protocol servers         |
| `/plugin-dev:create-plugin`            | Full guided plugin creation                   |

## Example Development Sessions

### Adding a New Skill

```text
You: "I want to add a skill for creating Oxy data models from existing views.
Use the plugin-dev skill to help me."

Claude: [Activates /plugin-dev:skill-development]
Let me help you create a new skill for Oxy data modeling...

[Guides through creating the skill with proper structure]
```

### Creating a Command

```text
You: "Create a /oxy:status command that shows the current semantic layer status.
Use plugin-dev."

Claude: [Activates /plugin-dev:command-development]
I'll create a new command that shows semantic layer status...

[Creates command file with proper frontmatter and implementation]
```

### Debugging a Skill

```text
You: "The oxy-semantic-layer skill isn't activating when I ask to create views.
Can you fix it?"

Claude: Let me read the skill file to understand the activation description...

[Reads SKILL.md, identifies issue with description, updates it]
```

## Resources

- [Claude Code Plugin Documentation](https://docs.anthropic.com/claude/docs/claude-code-plugins)
- [Oxy Documentation](https://docs.oxy.tech)
- [Oxy GitHub Repository](https://github.com/oxy-hq/oxy)
- [Plugin Development Best Practices](https://docs.anthropic.com/claude/docs/claude-code-plugin-best-practices)

## Getting Help

When working with Claude Code on this plugin:

1. Use `/plugin-dev:*` skills for plugin-specific tasks
2. Reference this CLAUDE.md for patterns and conventions
3. Check existing skills/commands/agents for examples
4. Review [examples/demo-project](examples/demo-project/) for usage patterns
5. Ask Claude to use the appropriate plugin-dev skill if unsure

## Contributing Guidelines

When contributing to this plugin:

1. **Follow existing patterns**: Match the style of current skills/commands/agents
2. **Use plugin-dev skills**: Leverage Claude's plugin development expertise
3. **Test thoroughly**: Verify changes work in real Oxy projects
4. **Document changes**: Update README.md and this CLAUDE.md
5. **Version appropriately**: Follow semantic versioning
6. **Provide examples**: Add to examples/demo-project/
7. **Keep it focused**: Each component should have one clear purpose

---

This plugin is designed to make Oxy development delightful with Claude Code. Use the plugin-dev skills to maintain consistency and quality across all plugin components.
