---
status: accepted
---

# Model tiers in The Forge, configured by settings

The Forge previously left model choice to the runtime, apart from asking for the highest-capability reviewer at `build`. On 2026-09-29 the maintainer asked for bounded work to go to mid-tier models such as Sonnet or Sol, for the proposed top tier to be Opus or Astra rather than a higher model such as Fable, while leaving any offered model, Fable included, available to users who choose it, and for The Forge to use the session model when nothing is configured.

## Settled design

- The Forge assigns roles to tiers but names no models, keeping the portability rule in `AGENTS.md`. Mid takes bounded, well-specified assignments: workers, accepted fixes, researchers, validation runs, and the complexity reviewer. Top takes ambiguous, architectural, or cross-cutting work, any issue that survives two mid-tier fixes, and the adversarial reviewer at `build` or on targets meeting those conditions.
- Settings map tiers to model ids. `setup-rmkr-skills` writes them to `docs/agents/forge.md` for a repository or a `### The Forge` block in global instructions. Its template proposes Sonnet/Sol and Opus/Astra, and the user confirms the ids.
- A tier set to `inherit` follows the session model. `mid=`, `top=`, and `reviewer=`, with or without a level, or plain words directing The Forge's agents, override settings for one run.
- The top tier is the ceiling: a mid tier resolving above it drops to the top model unless the user set mid for the run, including to `inherit`.
- Without settings, every agent inherits the session model and the report suggests setup, so an unconfigured run never stops to ask.
- The reviewer setting defaults to `capped`: the session model capped at the top tier for routine review. `top` and `inherit` apply to every review.
- Each setting resolves per runtime: the user's request, repository settings, global settings, then caller preferences. Saved settings are user choices, so they outrank a calling workflow, and a caller cannot go above the top tier. A target that changes the settings is reviewed under the baseline settings.
