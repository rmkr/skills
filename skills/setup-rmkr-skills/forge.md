# The Forge settings

## Suggested tiers

These are suggestions; the user may choose any model the runtime offers.

| Runtime | Mid | Top |
| --- | --- | --- |
| Claude Code | `opus@medium` | `opus@high` |
| Codex | latest Sol `@medium` | latest Sol `@xhigh` |

In Claude Code, write tier models only as the Agent tool's per-call aliases, `sonnet`, `opus`, `haiku`, or `fable`, or as `inherit`. Resolve "latest Sol" to the newest plain Sol release in Codex's live model list, such as `gpt-6.1-sol`, ignoring variants such as `-mini`, and write that exact id.

## Repository settings

Write this as `docs/agents/forge.md` with the active runtime's column only. In an existing file, add or update that column and keep the others. The global `### The Forge` block uses the same table.

```markdown
# The Forge settings

Model and effort for The Forge's tiers, one column per runtime. Write each tier as `model@effort`, with effort optional, and the reviewer as `capped`, `top`, `inherit`, or a model; `inherit` follows the session model, and a missing column or entry falls back to the next settings scope.

| Tier | <runtime> |
| --- | --- |
| Mid | <mid> |
| Top | <top> |
| Reviewer | <reviewer> |
```

## Effort agents

Replace `<effort>` with the level. Set effort only: no model, no tool limits.

Claude Code, `forge-<effort>.md`:

```markdown
---
name: forge-<effort>
description: Forge agent at <effort> effort.
effort: <effort>
---

Serve as a Forge agent. Follow your assignment.
```

Codex, `forge_<effort>.toml`:

```toml
name = "forge_<effort>"
description = "Forge agent at <effort> effort."
model_reasoning_effort = "<effort>"
developer_instructions = "Serve as a Forge agent. Follow your assignment."
```
