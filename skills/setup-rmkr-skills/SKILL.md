---
name: setup-rmkr-skills
description: Configure the rmkr skills globally or for this repository, starting with subagent delegation's model tiers and The Forge's reviewer policy. Run once before relying on them, or again to change the settings.
disable-model-invocation: true
compatibility: Explicit-only invocation requires a client that honors disable-model-invocation or the OpenAI allow_implicit_invocation policy.
---

# Setup rmkr skills

Write the settings the rmkr skills read from instruction files. Configure only the active runtime; teammates on another runtime run this skill there. In a runtime other than Claude Code or Codex, write nothing and report that delegated agents use the session model and effort there. Explore, present what you found, confirm with the user, then write.

## 1. Explore

Read what exists instead of assuming:

- The active runtime's global instruction file and agent folder: `~/.claude/CLAUDE.md` and `~/.claude/agents/` for Claude Code, `~/.codex/AGENTS.md` and `~/.codex/agents/` for Codex. Use the configured directory when one is relocated, such as by `CLAUDE_CONFIG_DIR` or `CODEX_HOME`.
- In Claude Code, the `env` block of the user settings file, `settings.json` in that same directory: the current `CLAUDE_CODE_SUBAGENT_MODEL`, and whether `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is set.
- In a repository: root `CLAUDE.md` and `AGENTS.md`, and `docs/agents/subagents.md`.
- Existing `## Agent skills` blocks and `### Subagent delegation` sub-blocks in all of these, and existing effort agents. Only a `delegate-<effort>` or `delegate_<effort>` name whose suffix is a known effort level, one delegation accepts (`low`, `medium`, `high`, `xhigh`, `max`, or `ultra`), is an effort agent.
- Which rmkr skills are installed. Configure only installed skills: subagent delegation has the tiers, and The Forge adds the reviewer policy.
- The model ids and effort levels the active runtime offers, from its live model list rather than a local cache.

## 2. Ask

Summarise what exists and what is missing. Ask one question at a time and lead with the recommended answer.

1. **Scope:** global, recommended when no global settings exist, or this repository. Repository settings override global ones, so use them for exceptions.
2. **Tiers:** propose the active runtime's suggested technician, engineer, and architect tiers from [subagents.md](subagents.md), resolved against its live model list, or `inherit` for every tier to follow the session model. Present only the suggested values and that they are suggestions: the user may choose any model and effort the runtime offers. In Claude Code, map a chosen full id to the alias that currently resolves to that exact id, or ask the user to pick an alias, before writing.
3. **Reviewer**, when The Forge is installed: `capped` (recommended): the architect tier at `build` and when the target is ambiguous, architectural, or cross-cutting, or an issue survives two engineer-tier fixes; otherwise the session model capped at the architect tier. `architect` always uses the architect tier, and `inherit` always uses the session model.

## 3. Confirm and write

Show the draft and let the user edit it. Then write:

- **Global:** add or update a `### Subagent delegation` sub-block under `## Agent skills` in the active runtime's global file, confirming the path with the user before creating a missing file, and hold the settings inline in the format [subagents.md](subagents.md) gives.
- **Repository:** write the active runtime's column in `docs/agents/subagents.md` from [subagents.md](subagents.md), keeping other runtimes' columns. In the root instruction file, add or update this sub-block under `## Agent skills`:

  ```markdown
  ### Subagent delegation

  Model tiers and The Forge's reviewer policy: see `docs/agents/subagents.md`.
  ```

  Edit `CLAUDE.md` if it exists, else `AGENTS.md`. If neither exists, ask which to create.

- **Effort agents:** at either scope, write the [effort agents](subagents.md#effort-agents) for each effort level these settings use, plus any level the user asks for unprompted, to the active runtime's agent folder, confirming the path before creating a missing folder. Generate only known effort levels the runtime offers for the chosen model, and report any others.
- **Subagent model default**, Claude Code only: set `env.CLAUDE_CODE_SUBAGENT_MODEL` in the user settings file to the engineer tier's model alias, the part before `@`, so an agent started without delegation's tiers gets the engineer model rather than the session model. Skip it when the engineer model is `inherit`. Leave `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` unset: it overrides every tier. Include the change in the draft, and edit the JSON in place, keeping every other key.

Update existing blocks and effort agents in place. Preserve surrounding content, including sub-blocks other setup skills wrote under `## Agent skills`.

## 4. Done

Report the files written, the settings in effect, and the `CLAUDE_CODE_SUBAGENT_MODEL` value set or skipped. If `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is already set, report that it overrides the tiers until the user removes it. Repository settings govern delegation once written, and Forge runs once they are in the baseline of the reviewed change, for example committed to the base branch; global settings, effort agents, and `CLAUDE_CODE_SUBAGENT_MODEL` apply in new sessions. Mention that `technician=`, `engineer=`, `architect=`, and The Forge's `reviewer=`, such as `engineer=opus@high`, override them for one run. Edit settings directly in `docs/agents/subagents.md` or the global block later; rerun this skill to add a scope or a newly installed skill, or when a newer model ships.
