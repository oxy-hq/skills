# Customer Operations Skill

## Quick Start

To use this skill, invoke it in your Claude Code conversation:

```
Use the customer-ops skill to create a new customer
```

## Common Commands

```
# Create a customer
Create customer "Jane Smith" at "Tech Corp" with email jane@techcorp.com

# Log an interaction
Log a call with customer jane-smith: discussed pricing, 20 minutes, outcome resolved

# Search customers
Show all active customers with tag "enterprise"

# Get customer details
Get customer jane-smith with interaction history

# Generate report
Create a summary report for customer jane-smith from last quarter
```

## Data Location

All customer data is stored in:
- Customers: `.claude/skills/customer-ops/data/customers/`
- Interactions: `.claude/skills/customer-ops/data/interactions/`

## File Structure

```
customer-ops/
├── SKILL.md              # Main skill documentation
├── README.md             # This file
├── templates/            # JSON templates
│   ├── customer-template.json
│   └── interaction-template.json
└── data/
    ├── customers/        # Customer profiles (one file per customer)
    └── interactions/     # Interaction logs (organized by customer)
```

## Interaction Types

- `call` - Phone or video calls
- `email` - Email correspondence
- `meeting` - In-person or virtual meetings
- `support_ticket` - Support or help desk tickets
- `note` - General notes or observations

## Customer Statuses

- `prospect` - Potential customer
- `active` - Active paying customer
- `inactive` - Former customer or dormant account

## Interaction Outcomes

- `resolved` - Issue or discussion completed
- `pending` - Awaiting response or action
- `follow_up_needed` - Requires additional follow-up

## Best Practices

1. Use consistent customer IDs (lowercase, hyphenated slugs)
2. Tag customers and interactions for easy filtering
3. Log interactions promptly while details are fresh
4. Include outcome and next steps in interaction summaries
5. Use metadata for custom fields specific to your business
