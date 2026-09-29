---
name: setup-rmkr-skills
description: Configure the rmkr skills globally or for this repository, starting with The Forge's model tiers and reviewer policy. Run once before relying on them, or again to change the settings.
disable-model-invocation: true
compatibility: Explicit-only invocation requires a client that honors disable-model-invocation or the OpenAI allow_implicit_invocation policy.
---

# Setup rmkr skills

Write the settings the rmkr skills read from instruction files. Explore, present what you found, confirm with the user, then write.

## 1. Explore

Read what exists instead of assuming:

- Global instruction files for the runtimes the user has: `~/.claude/CLAUDE.md` for Claude Code, `~/.codex/AGENTS.md` for Codex, and the equivalent file for any other runtime. Use the configured directory when one is relocated, such as by `CLAUDE_CONFIG_DIR` or `CODEX_HOME`.
- In a repository: root `CLAUDE.md` and `AGENTS.md`, and `docs/agents/forge.md`.
- Existing `## Agent skills` blocks and `### The Forge` sub-blocks in all of these.
- Which rmkr skills are installed. Configure only installed skills; today only The Forge has settings.
- The model ids each runtime offers, from its model picker or catalog.

## 2. Ask

Summarise what exists and what is missing. Ask one question at a time and lead with the recommended answer.

1. **Scope:** global, recommended when no global settings exist, or this repository. Repository settings override global ones, so use them for exceptions.
2. **Tiers:** propose the table in [forge.md](forge.md) with ids confirmed from exploration, or `inherit` for every tier to follow the session model. The user may choose any model the runtime offers, including one above the proposal, such as Fable. At global scope, ask only about runtimes the user uses.
3. **Reviewer:** `capped` (recommended): the top tier at `build` and when the target is ambiguous, architectural, or cross-cutting, or an issue survives two mid-tier fixes; otherwise the session model capped at the top tier. `top` always uses the top tier, and `inherit` always uses the session model.

At repository scope, record complete settings for Claude Code and Codex, since teammates do not share the user's global files and may use either runtime. Confirm ids for a runtime the user does not use against its catalog or official documentation.

## 3. Confirm and write

Show the draft and let the user edit it. Then write:

- **Global:** add or update a `### The Forge` sub-block under `## Agent skills` in each chosen global file, confirming the path with the user before creating a missing file, and hold the settings inline.
- **Repository:** write `docs/agents/forge.md` from [forge.md](forge.md). In the root instruction file, add or update this sub-block under `## Agent skills`:

  ```markdown
  ### The Forge

  Model tiers and reviewer policy: see `docs/agents/forge.md`.
  ```

  Edit `CLAUDE.md` if it exists, else `AGENTS.md`. If neither exists, ask which to create.

Update existing blocks in place. Preserve surrounding content, including sub-blocks other setup skills wrote under `## Agent skills`.

## 4. Done

Report the files written and the settings in effect. Repository settings govern Forge runs once they are in the baseline of the reviewed change, for example committed to the base branch; global settings apply in new sessions. Mention that `mid=`, `top=`, and `reviewer=` on a Forge run override them for that run. Edit settings directly in `docs/agents/forge.md` or the global block later; rerun this skill to add a scope or a newly installed skill.
