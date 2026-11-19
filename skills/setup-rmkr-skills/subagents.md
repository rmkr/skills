# Subagent delegation settings

## Repository settings

Write this as `docs/agents/subagents.md` with the active runtime's column only. Include the Reviewer row and separate Forge settings table only when forge is installed. List tiers lowest first, with each added tier's row in its chosen place, and include the added tiers list only when the user added a tier. In an existing file, add or update the active runtime's column in each table and keep the others. The global `### Subagent delegation` block uses the same format.

```markdown
# Subagent delegation settings

Model and effort for subagent delegation's model tiers and forge's reviewer, one column per runtime. Write each tier as `model@effort`, with effort optional, and the reviewer as `capped`, `architect`, `inherit`, or a model; `inherit` follows the session model and effort on each run, `inherit@<effort>` fixes only the effort, and a missing column or entry falls back to the next settings scope.

| Tier | <runtime> |
| --- | --- |
| Apprentice | <apprentice> |
| Technician | <technician> |
| Engineer | <engineer> |
| Architect | <architect> |
| Reviewer | <reviewer> |

Forge settings:

| Setting | <runtime> |
| --- | --- |
| Review rounds | <positive integer> |
| Reviewed model recommendations | <reviewed recommendations> |

Added tiers:

- **<name>**: <the work it takes>
```

`Review rounds` is a positive integer, not a model tier. Write the confirmed choice; recommend the existing valid value, or three when no choice exists. Preserve absent values for other runtimes so they can fall back to their global settings. Resolve forge through the runtime's skill catalog; its "Bound the loop" rules own resolution and validation.

Include `Reviewed model recommendations` after the user confirms a review of the recommendations. If the installed `subagent-delegation` skill lacks the recommendation reference, report that recommendations are unavailable and preserve any existing reviewed values.

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
