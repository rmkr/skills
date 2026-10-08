# Subagent delegation settings

## Suggested tiers

These are suggestions; the user may choose any model the runtime offers.

| Runtime | Apprentice | Technician | Engineer | Architect |
| --- | --- | --- | --- | --- |
| Claude Code | `haiku@high` | `sonnet@medium` | `opus@medium` | `opus@high` |
| Codex | latest Luna `@high` | latest Sol `@low` | latest Sol `@medium` | latest Sol `@xhigh` |

In Claude Code, write tier models only as the Agent tool's per-call aliases, `sonnet`, `opus`, `haiku`, or `fable`, or as `inherit`. Resolve "latest Sol" and "latest Luna" to the newest plain release of that family in Codex's live model list, such as `gpt-6.1-sol`, ignoring variants such as `-mini`, and write that exact id. Offer `haiku@xhigh` too when the live model list shows Haiku supports it.

## Repository settings

Write this as `docs/agents/subagents.md` with the active runtime's column only, and the Reviewer row only when The Forge is installed. List tiers lowest first, with each added tier's row in its chosen place, and include the added tiers list only when the user added a tier. In an existing file, add or update that column and keep the others. The global `### Subagent delegation` block uses the same format.

```markdown
# Subagent delegation settings

Model and effort for subagent delegation's model tiers and The Forge's reviewer, one column per runtime. Write each tier as `model@effort`, with effort optional, and the reviewer as `capped`, `architect`, `inherit`, or a model; `inherit` follows the session model and effort on each run, `inherit@<effort>` fixes only the effort, and a missing column or entry falls back to the next settings scope.

| Tier | <runtime> |
| --- | --- |
| Apprentice | <apprentice> |
| Technician | <technician> |
| Engineer | <engineer> |
| Architect | <architect> |
| Reviewer | <reviewer> |

Added tiers:

- **<name>**: <the work it takes>
```

## Effort agents

Replace `<effort>` with the level. Set effort only: no model, no tool limits.

Claude Code, `delegate-<effort>.md`:

```markdown
---
name: delegate-<effort>
description: Delegated agent at <effort> effort.
effort: <effort>
---

Serve as a delegated agent. Follow your assignment.
```

Codex, `delegate_<effort>.toml`:

```toml
name = "delegate_<effort>"
description = "Delegated agent at <effort> effort."
model_reasoning_effort = "<effort>"
developer_instructions = "Serve as a delegated agent. Follow your assignment."
```
