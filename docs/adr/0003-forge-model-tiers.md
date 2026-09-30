---
status: accepted
---

# Model tiers in The Forge, configured by settings

The Forge previously left model choice to the runtime, apart from asking for the highest-capability reviewer at `build`. On 2026-09-29 the maintainer asked for bounded work to go to mid-tier models such as Sonnet or Sol, for the proposed top tier to be Opus or Astra, while leaving any offered model available to users who choose it, and for The Forge to use the session model when nothing is configured.

Later that day (#9), Artificial Analysis benchmarks showed effort level matters as much as model choice: Opus 5.5 at medium effort beats Sonnet 5.5 at high, and GPT-6.1 Sol at xhigh matches GPT-6 Astra at high for about a quarter of the cost, and comes close at medium. Setup also configured every runtime from whichever one ran it, guessing other runtimes' ids, and pinned versioned ids that go stale.

## Settled design

- The Forge assigns roles to tiers but names no models, keeping the portability rule in `AGENTS.md`. Mid takes bounded, well-specified assignments: workers, accepted fixes, researchers, validation runs, and the complexity reviewer. Top takes ambiguous, architectural, or cross-cutting work, any issue that survives two mid-tier fixes, and the adversarial reviewer at `build` or on targets meeting those conditions.
- Settings map tiers to a model and an optional effort level, written `model@effort`. Only a known effort name after the last `@` is effort, so Vertex-style ids that contain `@` still work; a colon never separates them. `setup-rmkr-skills` writes them to `docs/agents/forge.md` for a repository or a `### The Forge` block in global instructions.
- Neither Claude Code nor Codex documents setting effort when an agent starts, so setup generates one effort agent per level the settings use, in the user's agent folder. Each sets effort only; The Forge starts the matching one and passes the model per spawn, and reports effort it cannot apply. The strict reviewer keeps the session effort, so setup never edits its definition.
- Each runtime runs its own setup, writing only its own global block and its own column in repository settings. The template suggests families, Opus at medium and high for Claude Code and the latest Sol at medium and xhigh for Codex; setup resolves a family to the newest id in the runtime's live model list and writes that exact id, keeping Claude Code aliases. Any offered model stays selectable.
- A tier set to `inherit` follows the session model. `mid=`, `top=`, and `reviewer=`, with or without a review level, or plain words directing The Forge's agents, override settings for one run.
- The top tier is the ceiling for models only; effort resolves per tier. A mid tier resolving above it drops to the top model unless the user set mid for the run, including to `inherit`.
- Without settings, every agent inherits the session model and the report suggests setup, so an unconfigured run never stops to ask.
- The reviewer setting defaults to `capped`: the session model capped at the top tier for routine review. The top tier's effort replaces the earlier fixed high-reasoning rule. `top` and `inherit` apply to every review.
- Each setting resolves per runtime: the user's request, repository settings, global settings, then caller preferences, then the session model and effort. Saved settings are user choices, so they outrank a calling workflow, and a caller cannot go above the top tier. A target that changes the settings is reviewed under the baseline settings.
