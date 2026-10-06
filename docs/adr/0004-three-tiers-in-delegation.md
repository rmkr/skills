---
status: accepted
---

# Three model tiers, owned by subagent delegation

On 2026-10-06 Claude Code's usage view showed subagents driving nearly all usage. Two days of subagent transcripts (29 agents) cost about $99 at API rates, all on Opus 5.5. Implementer workers started by `implement-spec` accounted for about 88% of it, at 80 to 245 turns each over a 100k to 150k token context. None ran through The Forge, so its tiers never applied: delegation inherited the session model for every agent.

Cache reads were 58% of that cost and cache writes 38%. Sonnet 5.5 and Opus 5.5 both bill cache reads at $0.20 per million tokens, so the same tokens on Sonnet would have cost about $79, a 21% saving at best. Turns times context size drives cost more than model choice does. Switching every agent to a cheaper model is not the fix this ADR records.

## Settled design

- `subagent-delegation` owns model tiers and assigns one to every delegated agent. The Forge takes tiers from it and keeps only its reviewer policy and level rules. This supersedes ADR 0003's placement of tiers in The Forge.
- Three ordered tiers replace mid and top: technician for mechanical work (search, exploration, validation runs, fully specified changes), engineer for bounded work that needs judgement (workers, research, the complexity reviewer), and architect for ambiguous, architectural, or cross-cutting work. Role names were rejected because they collide with delegation's roles; rank and size words were rejected by the maintainer. Informal names such as light, mid, and top are accepted. A bare `low` or `high` that names neither effort nor tier is asked about.
- Escalation runs technician to engineer after one failure, and engineer to architect after two. Each tier is capped by the one above it.
- Suggested settings: Claude Code `sonnet@medium`, `opus@medium`, `opus@high`; Codex the latest Sol at `low`, `medium`, `xhigh`. Engineer stays on Opus because Sonnet would save little on long workers.
- Settings move to `docs/agents/subagents.md` and a `### Subagent delegation` global block, and effort agents become `delegate-<effort>`. The repository is private, so existing installs are migrated by hand rather than by setup.
- Setup also sets Claude Code's `CLAUDE_CODE_SUBAGENT_MODEL` to the engineer model, so an agent started without the skill does not fall back to the session model. It never sets the `_FORCE` variant, which would override the tiers.
- Delegation keeps context small: assignments point to sources instead of pasting them, one worker takes a cohesive slice rather than one agent per small ticket, shared exploration runs once at technician and is saved as notes, finished agents are reused for follow-ups, and no fork starts from a parent context over about 100k tokens.
- The Forge's complexity reviewer runs once, after the first clean adversarial review, and again only when later fixes change the source substantially.
- `implement-spec` is not this repository's skill and is left unchanged; it is covered through delegation and the subagent model default.
