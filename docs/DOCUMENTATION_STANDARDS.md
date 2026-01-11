# Documentation Standards

This document defines the structure, naming conventions, and templates for all markdown documentation in the Change-Driven Development project. All AI agents and contributors must follow these standards when creating or updating documentation.

## Directory Structure

```
/
├── README.md                    # Main project entry point
├── STATUS.md                    # Current implementation status
├── TODO.md                      # Simple task backlog
├── COPILOT_TASK.md              # Active task for Copilot
├── change-driven-dev_COPILOT_TASKS.md  # Comprehensive task backlog
├── LICENSE                      # Project license
├── docs/
│   ├── DOCUMENTATION_STANDARDS.md  # This file
│   ├── user/                    # End-user documentation
│   │   ├── README.md            # User docs index
│   │   ├── QUICKSTART.md        # 10-minute tutorial
│   │   └── BACKGROUND_PROCESSES.md  # Background process management
│   ├── dev/                     # Developer documentation
│   │   ├── README.md            # Developer docs index
│   │   ├── DEVELOPMENT.md       # Local development setup
│   │   ├── DEPLOYMENT.md        # Production deployment
│   │   ├── LOCAL_SETUP.md       # Local setup without Docker
│   │   ├── SERVICE_SETUP.md     # Systemd service configuration
│   │   └── TESTING.md           # Testing guide
│   └── reference/               # Reference documentation
│       ├── README.md            # Reference docs index
│       ├── DECISIONS.md         # Decision model
│       └── SECURITY.md          # Security model
├── reports/                     # Agent-generated session reports
│   ├── README.md                # Reports index
│   ├── YYYY-MM-DD_session_name.md
│   └── archive/                 # Old reports (>30 days)
└── PROMPTS/                     # AI agent instructions
    ├── planner.md               # Planner agent
    ├── architect.md             # Architect agent
    └── coder.md                 # Coder agent
```

## Document Categories

### 1. User Documentation (`docs/user/`)

**Purpose**: Help end users understand and use the system  
**Audience**: Non-technical users, product owners, stakeholders  
**Style**: Tutorial-based, step-by-step, comprehensive

**Requirements**:
- Clear prerequisites section
- Step-by-step instructions with examples
- Screenshots or diagrams where helpful
- Troubleshooting section
- Cross-references to related docs

**Naming**: `DESCRIPTIVE_NAME.md` (SCREAMING_SNAKE_CASE)

### 2. Developer Documentation (`docs/dev/`)

**Purpose**: Guide developers through setup, development, and deployment  
**Audience**: Software developers, DevOps engineers  
**Style**: Technical, command-focused, practical

**Requirements**:
- Prerequisites clearly stated
- Complete command examples (copy-pasteable)
- Environment setup instructions
- Architecture explanations where needed
- Links to code references

**Naming**: `DESCRIPTIVE_NAME.md` (SCREAMING_SNAKE_CASE)

### 3. Reference Documentation (`docs/reference/`)

**Purpose**: Define core concepts, models, and principles  
**Audience**: Developers, architects, AI agents  
**Style**: Concise, authoritative, principle-based

**Requirements**:
- Short and focused (10-50 lines)
- Clear definitions
- Minimal examples (only when essential)
- No tutorial content
- Authoritative tone

**Naming**: `CONCEPT_NAME.md` (SCREAMING_SNAKE_CASE)

### 4. Session Reports (`reports/`)

**Purpose**: Document work completed by AI agents in sessions  
**Audience**: Project maintainers, historical record  
**Style**: Technical log, structured, dated

**Requirements** (see template below):
- Date prefix in filename
- Required metadata section
- Categorized work sections
- File references with line numbers
- Statistics and metrics
- Next steps

**Naming**: `YYYY-MM-DD_descriptive_session_name.md`  
**Examples**:
- `2026-01-11_e2e_test_implementation.md`
- `2026-01-09_type_safety_fixes.md`
- `2026-01-15_security_sandbox_refactor.md`

### 5. Agent Instructions (`PROMPTS/`)

**Purpose**: Define roles and rules for AI agents  
**Audience**: AI agents (Planner, Architect, Coder)  
**Style**: Imperative, rule-based, concise

**Requirements**:
- Clear role definition
- Explicit rules and constraints
- Output format specifications
- Examples of expected behavior
- 10-30 lines (very focused)

**Naming**: `agent_name.md` (lowercase)

## Templates

### Session Report Template

```markdown
# Session Report: [Descriptive Title]

## Metadata
- **Date**: YYYY-MM-DD
- **Agent**: [Agent name or "Human"]
- **Session ID**: [Optional unique identifier]
- **Related EPICs**: [EPIC-X, EPIC-Y] (if applicable)
- **Status**: [Completed | In Progress | Blocked]

## Summary

[2-3 sentence summary of what was accomplished or attempted]

## Work Completed

### ✅ Successfully Implemented
- [Task 1 with file reference: [file.py#L10-L20](path/to/file.py#L10-L20)]
- [Task 2]
- [Task 3]

### ⚠️ Partial / In Progress
- [Task description and current state]

### ❌ Failed / Blocked
- [Issue description]
- **Blocker**: [What's preventing completion]

## Files Modified

- [path/to/file1.py](path/to/file1.py) - [Brief description of changes]
- [path/to/file2.ts](path/to/file2.ts) - [Brief description of changes]

## Statistics

- Files modified: X
- Lines added: +XXX
- Lines removed: -XXX
- Tests added: X
- Tests passing: X/Y

## Technical Details

### [Component/Feature 1]
[Detailed technical explanation]

### [Component/Feature 2]
[Detailed technical explanation]

## Issues Encountered

1. **[Issue title]**: [Description and resolution/workaround]
2. **[Issue title]**: [Description and resolution/workaround]

## Next Steps

- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

## Related Documentation

- [Link to related docs]
- [Link to related PRs/issues]
```

### User Guide Template

```markdown
# [Feature/Topic Name]

[Brief description of what this guide covers - 1-2 sentences]

## Prerequisites

- Requirement 1
- Requirement 2
- [Link to setup guide if needed](docs/dev/DEVELOPMENT.md)

## Quick Start

[Fastest path to get started - 3-5 steps]

## Detailed Guide

### Step 1: [Action]

[Instructions]

\`\`\`bash
# Command example
command --with-flags
\`\`\`

### Step 2: [Action]

[Instructions]

## Common Tasks

### Task 1: [Task name]

[How to accomplish this task]

### Task 2: [Task name]

[How to accomplish this task]

## Troubleshooting

### Problem: [Issue description]

**Solution**: [How to fix]

### Problem: [Issue description]

**Solution**: [How to fix]

## Next Steps

- [Link to related guide]
- [Link to advanced topics]

## Related Documentation

- [Cross-reference 1]
- [Cross-reference 2]
```

### Developer Guide Template

```markdown
# [Topic/Feature] - Developer Guide

[Technical description - 1-2 sentences]

## Prerequisites

- Technical requirement 1
- Technical requirement 2
- Knowledge of [technology/concept]

## Architecture Overview

[Optional: Brief architecture description or ASCII diagram]

## Setup

\`\`\`bash
# Installation commands
npm install
task setup
\`\`\`

## Development Workflow

### 1. [Phase/Step]

\`\`\`bash
# Commands
\`\`\`

### 2. [Phase/Step]

\`\`\`bash
# Commands
\`\`\`

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| \`option1\` | \`value\` | Description |
| \`option2\` | \`value\` | Description |

## Testing

\`\`\`bash
# Run tests
task test
\`\`\`

## Deployment

[Deployment instructions or link to DEPLOYMENT.md]

## Troubleshooting

Common development issues and solutions.

## Reference

- [API documentation link]
- [External resources]
```

### Reference Document Template

```markdown
# [Concept Name]

[1-2 sentence definition of the concept]

## Core Principles

1. **Principle 1**: [Brief explanation]
2. **Principle 2**: [Brief explanation]
3. **Principle 3**: [Brief explanation]

## Key Points

- Point 1
- Point 2
- Point 3

## Rules

1. [Rule with clear constraint]
2. [Rule with clear constraint]

## Example

[Optional: Minimal example only if critical for understanding]

## See Also

- [Related concept]
- [Related documentation]
```

## Formatting Standards

### Headings

- Use ATX-style headings (`# H1`, `## H2`, etc.)
- One H1 (`#`) per document (the title)
- Don't skip heading levels
- Use sentence case for headings

### Code Blocks

- Always specify language for syntax highlighting
- Include comments in code examples
- Make examples copy-pasteable (use real paths, not placeholders unless necessary)

### Links

- Use relative paths for internal links: `[text](../dev/DEVELOPMENT.md)`
- Include line numbers for code references: `[handler.py#L42](backend/app/handler.py#L42)`
- Use descriptive link text (not "click here")

### Lists

- Use `-` for unordered lists
- Use `1.` for ordered lists (auto-numbering)
- Indent nested lists with 2 spaces

### Tables

- Use tables for structured data
- Include header row
- Align columns for readability in source

### Emojis

- **Session reports**: Use emojis for visual categorization (✅ ❌ ⚠️ 📝)
- **User/dev guides**: Minimal emoji use, only for callouts
- **Reference docs**: No emojis

### Callouts

Use blockquotes for important notes:

```markdown
> **Note**: Important information
> 
> **Warning**: Critical warning
> 
> **Tip**: Helpful suggestion
```

## File Naming Rules

### General Rules

1. **User/Dev/Reference**: `SCREAMING_SNAKE_CASE.md`
   - Examples: `QUICKSTART.md`, `SERVICE_SETUP.md`, `DECISIONS.md`

2. **Session Reports**: `YYYY-MM-DD_descriptive_name.md`
   - Examples: `2026-01-11_session_summary.md`
   - Date format: ISO 8601 (YYYY-MM-DD)
   - Descriptive part: lowercase with underscores

3. **Agent Instructions**: `agent_name.md` (lowercase)
   - Examples: `planner.md`, `architect.md`, `coder.md`

4. **Index Files**: `README.md` in each directory

### Prohibited Patterns

- ❌ Spaces in filenames
- ❌ CamelCase for documentation
- ❌ Dates in middle of filename (use prefix)
- ❌ Version numbers in filenames (use git)
- ❌ Duplicate/redundant files

## Metadata Standards

### Session Reports (Required)

All session reports must include:

```markdown
## Metadata
- **Date**: YYYY-MM-DD
- **Agent**: [Planner | Architect | Coder | Human | AI Assistant]
- **Session ID**: [Optional identifier]
- **Related EPICs**: [EPIC numbers if applicable]
- **Status**: [Completed | In Progress | Blocked]
```

### Other Documents (Optional)

User and developer guides may include:

```markdown
---
last_updated: YYYY-MM-DD
version: X.Y.Z
status: [Draft | Active | Deprecated]
---
```

## Cross-Reference Guidelines

### Internal Links

- Use relative paths from document location
- Link to sections with anchors: `[section](#heading-name)`
- Update links when moving files

### Code References

- Include line numbers when referencing code: `[handler.py#L42-L58](backend/app/handler.py#L42-L58)`
- Link to current version, not specific commits
- Use workspace-relative paths

### External Links

- Use full URLs for external resources
- Include brief description: `[FastAPI docs](https://fastapi.tiangolo.com) - Web framework documentation`

## Maintenance

### Lifecycle Management

1. **Living Documents** (frequently updated):
   - `STATUS.md`, `TODO.md`, `COPILOT_TASK.md`
   - Update with each change
   - Keep concise and current

2. **Stable Documents** (rarely change):
   - User guides, developer guides
   - Review quarterly
   - Version with git tags

3. **Historical Documents** (point-in-time):
   - Session reports
   - Archive after 30 days to `reports/archive/`
   - Never delete (historical record)

### Archiving Session Reports

After 30 days:

```bash
mv reports/2026-01-11_*.md reports/archive/
```

Keep reports organized:
- Recent reports: `reports/`
- Old reports: `reports/archive/YYYY-MM/`

## Agent-Specific Rules

### For All AI Agents

When creating documentation:

1. ✅ **Do**:
   - Follow template for document type
   - Include all required metadata
   - Use proper file naming (date prefix for reports)
   - Create file references with line numbers
   - Update cross-references if moving files
   - Include statistics and metrics in reports
   - List next steps

2. ❌ **Don't**:
   - Create duplicate documentation
   - Use generic names like "report.md"
   - Skip metadata sections
   - Create files in wrong directories
   - Use vague descriptions
   - Include outdated information

### Planner Agent

When creating session reports:
- Must include EPIC references
- List all tasks created with IDs
- Include plan.json artifact reference
- Document task dependencies

### Architect Agent

When creating ADR (Architecture Decision Records):
- Use format: `reports/YYYY-MM-DD_adr_task_NNN_decision.md`
- Include decision context, options, and rationale
- Reference architecture artifacts

### Coder Agent

When creating implementation reports:
- Include test results
- Reference quality gate results
- Document git commits made
- List all file modifications

## Quality Checklist

Before committing documentation:

- [ ] File is in correct directory
- [ ] Filename follows naming convention
- [ ] Metadata section complete (for reports)
- [ ] Code blocks have language specified
- [ ] Links use relative paths
- [ ] Cross-references are valid
- [ ] Headings don't skip levels
- [ ] No spelling/grammar errors
- [ ] Template sections completed
- [ ] Index files updated if needed

## Examples

### Good Filename Examples

✅ `docs/user/QUICKSTART.md`  
✅ `reports/2026-01-11_e2e_test_implementation.md`  
✅ `docs/reference/SECURITY.md`  
✅ `PROMPTS/planner.md`

### Bad Filename Examples

❌ `my-report.md` (in root, no date)  
❌ `Session Report 2026.md` (spaces, wrong format)  
❌ `docs/UserGuide.md` (wrong case)  
❌ `PROMPTS/PLANNER.md` (wrong case)

### Good Session Report Example

See: [reports/2026-01-11_e2e_test_summary.md](../reports/2026-01-11_e2e_test_summary.md)

## Updates to This Document

This standard should be updated when:
- New document categories are needed
- Naming conventions change
- Template improvements are identified
- Agent requirements change

All updates require review and approval from project maintainer.

---

**Version**: 1.0  
**Last Updated**: 2026-01-11  
**Status**: Active
