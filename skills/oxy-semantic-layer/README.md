# Oxy Semantic Layer Skill

A Claude Agent Skill for building and maintaining Oxy semantic layer files (views and topics) for analytics.

## What is this?

This skill provides Claude with specialized knowledge for creating Oxy semantic layers, including:

- Understanding database schemas
- Creating view files with entities, dimensions, and measures
- Creating topic files to organize views
- Validating and testing semantic layers
- Best practices and common patterns

## Skill Structure

This skill follows the [Claude Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) architecture:

```
oxy-semantic-layer/
├── SKILL.md                  # Main skill instructions (Level 2: loaded when triggered)
├── view-template.yml         # Template for creating view files (Level 3: loaded as needed)
├── topic-template.yml        # Template for creating topic files (Level 3: loaded as needed)
├── QUICK-REFERENCE.md        # Quick reference guide (Level 3: loaded as needed)
└── README.md                 # This file (documentation)
```

### Progressive Loading

The skill uses progressive disclosure to minimize context usage:

1. **Level 1 (Metadata)**: Claude knows this skill exists and when to use it (~100 tokens)
2. **Level 2 (Instructions)**: When triggered, Claude reads `SKILL.md` for detailed guidance (~4k tokens)
3. **Level 3+ (Resources)**: Claude accesses templates and references only when needed (on-demand)

## When Claude Uses This Skill

Claude automatically activates this skill when you:

- Ask to create or update Oxy semantic layers
- Need help with view or topic files
- Want to understand database schemas for semantic layer creation
- Ask about entities, dimensions, measures, or topics

## Key Capabilities

### View Files

- Define data models with entities (primary and foreign)
- Create dimensions (filterable/groupable attributes)
- Create measures (aggregatable metrics)
- Support for filtered measures and custom calculations

### Topic Files

- Organize views by business domain
- Apply default filters (with correct `filter_type` syntax)
- Configure base views

### Validation

- Correct syntax for measure filters (`expr` property)
- Proper entity key references (dimension names, not columns)
- Topic default_filters structure

## Usage Examples

Ask Claude:

- "Create an Oxy semantic layer for my sales data"
- "Help me build view files from these database schemas"
- "What's the correct syntax for filtered measures in Oxy?"
- "Create a topic file for my orders view"

## Key Syntax

### Measure Filters (in view files)

```yaml
filters:
  - expr: "{{dimension_name}} operator value"
```

### Topic Default Filters (in topic files)

```yaml
default_filters:
  - field: table.column
    filter_type:
      operator:
        value: "value"
```

## Documentation

For more details on Oxy semantic layers, see:

- [Oxy Semantic Layer Docs](https://docs.oxy.tech/learn-about-oxy/semantic-layer)
- [Views](https://docs.oxy.tech/learn-about-oxy/semantic-layer/views)
- [Topics](https://docs.oxy.tech/learn-about-oxy/semantic-layer/topics)
- [Entities](https://docs.oxy.tech/learn-about-oxy/semantic-layer/entities)
- [Dimensions](https://docs.oxy.tech/learn-about-oxy/semantic-layer/dimensions)
- [Measures](https://docs.oxy.tech/learn-about-oxy/semantic-layer/measures)

## Version

Created: 2025-12-18
Compatible with: Oxy semantic layer (Cube.js-based)
