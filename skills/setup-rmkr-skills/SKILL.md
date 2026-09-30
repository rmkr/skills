---
name: setup-rmkr-skills
description: Configure the rmkr skills globally or for this repository, starting with The Forge's model tiers and reviewer policy. Run once before relying on them, or again to change the settings.
disable-model-invocation: true
compatibility: Explicit-only invocation requires a client that honors disable-model-invocation or the OpenAI allow_implicit_invocation policy.
---

# Setup rmkr skills

Write the settings the rmkr skills read from instruction files. Configure only the active runtime; teammates on another runtime run this skill there. In a runtime other than Claude Code or Codex, write nothing and report that The Forge uses the session model and effort there. Explore, present what you found, confirm with the user, then write.

## 1. Explore

Read what exists instead of assuming:

- The active runtime's global instruction file and agent folder: `~/.claude/CLAUDE.md` and `~/.claude/agents/` for Claude Code, `~/.codex/AGENTS.md` and `~/.codex/agents/` for Codex. Use the configured directory when one is relocated, such as by `CLAUDE_CONFIG_DIR` or `CODEX_HOME`.
- In a repository: root `CLAUDE.md` and `AGENTS.md`, and `docs/agents/forge.md`.
- Existing `## Agent skills` blocks and `### The Forge` sub-blocks in all of these, and existing effort agents. Only a `forge-<effort>` or `forge_<effort>` name whose suffix is a known effort level, one The Forge accepts (`low`, `medium`, `high`, `xhigh`, `max`, or `ultra`), is an effort agent; never edit the strict reviewer.
- Which rmkr skills are installed. Configure only installed skills; today only The Forge has settings.
- The model ids and effort levels the active runtime offers, from its live model list rather than a local cache.

## 2. Ask

Summarise what exists and what is missing. Ask one question at a time and lead with the recommended answer.

1. **Scope:** global, recommended when no global settings exist, or this repository. Repository settings override global ones, so use them for exceptions.
2. **Tiers:** propose the active runtime's suggested tiers from [forge.md](forge.md), resolved against its live model list, or `inherit` for every tier to follow the session model. Present only the suggested values and that they are suggestions: the user may choose any model and effort the runtime offers, including a model above the proposal, such as Fable. In Claude Code, map a chosen full id to the alias that currently resolves to that exact id, or ask the user to pick an alias, before writing.
3. **Reviewer:** `capped` (recommended): the top tier at `build` and when the target is ambiguous, architectural, or cross-cutting, or an issue survives two mid-tier fixes; otherwise the session model capped at the top tier. `top` always uses the top tier, and `inherit` always uses the session model.

## 3. Confirm and write

Show the draft and let the user edit it. Then write:

- **Global:** add or update a `### The Forge` sub-block under `## Agent skills` in the active runtime's global file, confirming the path with the user before creating a missing file, and hold the settings inline in the format [forge.md](forge.md) gives.
- **Repository:** write the active runtime's column in `docs/agents/forge.md` from [forge.md](forge.md), keeping other runtimes' columns. In the root instruction file, add or update this sub-block under `## Agent skills`:

  ```markdown
  ### The Forge

  Model tiers and reviewer policy: see `docs/agents/forge.md`.
  ```

  Edit `CLAUDE.md` if it exists, else `AGENTS.md`. If neither exists, ask which to create.

- **Effort agents:** at either scope, write the [effort agents](forge.md#effort-agents) for each effort level these settings use, plus any level the user asks for unprompted, to the active runtime's agent folder, confirming the path before creating a missing folder. Generate only known effort levels the runtime offers for the chosen model, and report any others.

Update existing blocks and effort agents in place. Preserve surrounding content, including sub-blocks other setup skills wrote under `## Agent skills`.

## 4. Done

Report the files written and the settings in effect. Repository settings govern Forge runs once they are in the baseline of the reviewed change, for example committed to the base branch; global settings and effort agents apply in new sessions. Mention that `mid=`, `top=`, and `reviewer=` on a Forge run, such as `mid=opus@high`, override them for that run. Edit settings directly in `docs/agents/forge.md` or the global block later; rerun this skill to add a scope or a newly installed skill, or when a newer model ships.
