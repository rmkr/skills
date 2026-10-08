---
status: accepted
---

# Apprentice, added tiers, and tiers by complexity

On 2026-10-07 Anthropic released Claude Haiku 5.5, a fast small model built for subagent work at $0.10 per million input tokens. OpenAI's GPT-6 Luna, released 2026-09-22, sits at the same price below Sol. ADR 0004's three tiers had no place for a model this cheap, and the maintainer wanted to add further tiers without a code change. On 2026-10-08 the maintainer also asked for setup to ask its questions the way `setup-matt-pocock-skills` does.

## Settled design

- A fourth built-in tier, apprentice, sits below technician for quick attempts and narrow work. Its working results are kept, not thrown away; review catches its mistakes. A separate unranked "try things" kind was rejected in favour of a ranked tier, so the caps and escalation chain cover it. The trade name keeps ADR 0004's naming.
- Users can add tiers in setup with a name, a place in the order, a one-line description of the work, and a model. An added tier may sit above architect, and then the top tier, not architect, is the model ceiling.
- Tiers are chosen by how complex an assignment is, the lowest tier that can do it well, rather than by a fixed list of work kinds; the lists become typical work. When a planning or research agent makes the plan, its plan sets each assignment's tier. The orchestrator may raise a tier it judges too low and reports the raise, but never lowers one.
- Escalation moves failed work up one tier after one failure from every tier except engineer, which keeps two. Shared exploration runs on apprentice or technician by its breadth. These supersede ADR 0004's escalation rule, its assignment by work kind, and its exploration on technician.
- An added tier's place and work come from the narrowest settings scope that lists it. Its name is one lowercase word that clashes with no tier, effort, informal tier name, `reviewer`, `inherit`, or `capped`, so `<name>=` overrides stay unambiguous.
- Informal names keep their ADR 0004 mapping, so "low" still means technician; apprentice has none. The Forge's reviewer policy still names architect, even when an added tier sits above it.
- Suggested apprentice settings: Claude Code `haiku@high`, offering `xhigh` only when the live model list shows Haiku supports it; Codex the latest Luna at `high`.
- Setup asks through the runtime's multiple-choice question tool when it has one, `AskUserQuestion` in Claude Code or `request_user_input` in Codex. Otherwise it follows the Matt Pocock pattern: lead with the recommended answer, explain only real branches, and skip questions exploration settled.
- Existing settings without an apprentice row still work: an unmapped apprentice uses technician's model and effort until setup is rerun, so it never costs more than technician.
