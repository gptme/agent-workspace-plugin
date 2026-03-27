# Agent Workspace Plugin

A Claude Code plugin that provides persistent workspace infrastructure for autonomous AI agents.

## What It Does

Sets up and manages a git-tracked "brain" for AI agents with:

- **Structured Tasks** — YAML frontmatter task files with state tracking, priorities, and dependencies
- **Append-Only Journal** — Daily session logs that never get modified, preserving full history
- **Behavioral Lessons** — Keyword-matched guidance that prevents known failure modes
- **Knowledge Base** — Long-term documentation organized by topic

## Why

Most AI agent sessions are ephemeral — everything is lost when the conversation ends. This plugin gives Claude Code the infrastructure to maintain persistent state across sessions, learn from mistakes, and build compound knowledge over time.

Based on the [gptme-agent-template](https://github.com/gptme/gptme-agent-template) — the same architecture powering [Bob](https://github.com/TimeToBuildBob), an autonomous AI agent with 3000+ completed sessions. Includes an autonomous-run skill that teaches Claude Code how to select work, execute, and journal — turning any project into a self-improving agent workspace.

## Installation

```bash
# Install from GitHub
/install https://github.com/gptme/agent-workspace-plugin
```

**Requires**: Python 3.10+ (for task validation hook)

## Commands

| Command | Description |
|---------|-------------|
| `/agent-workspace:workspace-init` | Initialize a new agent workspace with all directories |
| `/agent-workspace:workspace-status` | Show tasks, recent journal entries, lessons, git state |
| `/agent-workspace:journal [name]` | Create or append to today's journal entry |

## Skills

| Skill | Description |
|-------|-------------|
| `autonomous-run` | Execute a structured autonomous work session with cascade task selection |
| `task-management` | Create, update, and query structured task files |
| `lessons` | Create behavioral lessons that encode reusable patterns |

## Hooks

| Event | Trigger | Action |
|-------|---------|--------|
| PostToolUse | Write/Edit on `tasks/*.md` | Validates YAML frontmatter (state, created fields) |

## Workspace Structure

```txt
workspace/
├── tasks/          # Structured task files with YAML frontmatter
├── journal/        # Daily append-only session logs (YYYY-MM-DD/)
├── lessons/        # Behavioral guidance (keyword-matched)
│   ├── patterns/   # Cross-cutting patterns
│   ├── tools/      # Tool-specific lessons
│   └── workflow/   # Process lessons
├── knowledge/      # Long-term documentation
└── people/         # Collaborator profiles
```

## Quick Start

1. Install the plugin
2. Run `/agent-workspace:workspace-init` to create the workspace
3. Create your first task with the `task-management` skill
4. Start a journal with `/agent-workspace:journal getting-started`
5. When you learn something reusable, create a lesson with the `lessons` skill

## Task States

```txt
backlog -> todo -> active -> done
                     |
                  waiting -> active
                     |
                 cancelled
```

## Example Workflows

### Interactive
```
User: Let's start tracking our work on this project
Claude: /agent-workspace:workspace-init  →  Creates tasks/, journal/, lessons/, knowledge/

User: Create a task for adding user authentication
Claude: [Uses task-management skill → tasks/add-user-auth.md]

User: I learned that JWT tokens need rotation — save that
Claude: [Uses lessons skill → lessons/tools/jwt-token-rotation.md]
```

### Autonomous
```
Cron/Scheduled: "Run an autonomous work session"
Claude: [Uses autonomous-run skill]
  1. Checks git status, finds no loose ends
  2. CASCADE: finds tasks/add-user-auth.md in active state
  3. Implements auth, writes tests, commits
  4. Updates task state to done, writes journal entry
```

## Architecture

This plugin packages the core patterns from the [gptme-agent-template](https://github.com/gptme/gptme-agent-template):

- **Tasks** use the same YAML frontmatter schema as [gptme](https://gptme.org) agents
- **Journal** follows the append-only, subdirectory-per-day pattern
- **Lessons** use keyword matching for contextual activation
- **Everything is git-tracked** for persistence and auditability

## Learn More

- [gptme-agent-template](https://github.com/gptme/gptme-agent-template) — Full agent template with autonomous operation
- [gptme](https://gptme.org) — The AI assistant framework
- [Bob's blog](https://timetobuildbob.github.io) — Learnings from 1700+ autonomous sessions
- [Superuser Labs](https://superuserlabs.org) — The team behind gptme

## License

MIT
