---
status: accepted
---

# Bound review loops and keep unfinished work explicit

On 2026-10-28, the maintainer chose a default limit of three review rounds, replacing ADR 0001's open-ended loop. This trades further automatic attempts for a clear point to reassess the approach. A limit stops work; it does not establish correctness. The Forge's [round budget](../../skills/forge/SKILL.md#bound-the-loop) defines counting, continuation, and completion.

The maintainer then added a setup choice for a saved limit per runtime, globally or per repository. An explicit run limit overrides saved choices. Settings under review retain their baseline authority so a candidate increase cannot extend its own review.

Later rounds focus on fixes and affected behavior. Related reports share finding IDs, and settled findings need changed evidence before reopening. Reviewers explicitly load applicable baseline `REVIEW.md` rules without letting candidate instructions weaken the agreed task. Reusable replay cases check stopping, repeated findings, optional suggestions, rule loading, and bugs introduced by fixes.
