---
status: accepted
---

# Merge the review skills into The Forge, with levels

Three skills covered overlapping review work: Adversarial Review Loop, The Forge, and Diff Skeptic. The Forge was mostly a pointer to the loop and to Subagent Delegation, with three rules of its own. Diff Skeptic was a single strict review of a Git diff. Nothing selected Diff Skeptic automatically, so The Forge never used its enforced reviewer. On 2026-09-27 the maintainer chose one skill named The Forge, with levels. No release had been published, so the rename breaks no stable installation.

## Settled design

- One skill, `forge`, with three levels: `review` (verified findings only), `fix` (the former loop and the default for review-and-improve requests), and `build` (the former Forge: workers implement, then `fix` runs).
- `strict` is an option on any level with a Git target, not a fourth level. It carries Diff Skeptic's enforced read-only reviewer and immutable, fingerprinted bundle. The reviewer definitions become `forge-strict-reviewer`.
- `build` keeps the former Forge's engineering scope; ADR 0001's "The Forge retains its separate engineering scope" now applies to that level. A `build` request on another subject is implemented through Subagent Delegation, then runs `fix`, instead of being declined.
- The skill keeps automatic selection. `build` and `strict` run only on user request. Only the instructions enforce this; the explicit-invocation policy that previously protected The Forge and Diff Skeptic no longer applies to them.
- The strict reviewer keeps the premise challenge. Strict rounds skip only the complexity review, because the enforced reviewer cannot load skills.
- When the target changes during a strict review, the Forge reviews a fresh bundle before claiming the current state reviewed. It drops Diff Skeptic's single-review stop.
- `build` and `strict` rules live in `references/` so runs that do not need them do not load them.
