# Repository instructions

## Source of truth

Treat this repository as the canonical editable source for Austin's custom Agent Skills across Codex, Claude Code, and OhMyPi. Personal installations are derived from it; make lasting changes here rather than editing an installed symlink target from another location.

## Skill changes

1. Use the available `skill-creator` and `writing-for-agents` skills when creating or materially changing agent-facing instructions.
2. Keep each skill in `skills/<name>/`, with the folder and frontmatter `name` identical.
3. Keep `SKILL.md` concise, imperative, and limited to behavior that changes how the agent works. Put only essential scripts, references, and assets inside a skill; do not add per-skill READMEs or process notes.
4. Keep the portable `SKILL.md` core aligned with the Agent Skills specification. Document any client extension required for behavior, such as `disable-model-invocation`. Maintain `agents/openai.yaml` whenever the skill name, purpose, or invocation policy changes; its default prompt must mention the skill as `$<name>`. Keep explicit-only behavior aligned across the extension and the OpenAI policy.
5. Preserve model portability. Resolve role capabilities against the active runtime and omit fixed model identifiers unless the user explicitly requires one or the workflow depends on a documented model-specific capability.
6. Forward-test complex workflows with fresh task context and raw artifacts. Keep evaluation fixtures out of the final repository unless they provide lasting regression value.

## Custom agents

Add a reusable custom agent only when a stable role needs fixed instructions, tools, or sandbox behavior that a skill cannot express cleanly. Keep Codex definitions at `agents/<name>.toml`, Claude Code definitions at `agents/claude/<name>.md`, and OhMyPi definitions at `agents/omp/<name>.md`. Keep names aligned with each runtime's identifier rules and prefer runtime-selected models.

Routine independent audits and The Forge use ordinary native subagents with explicit inspection-only reviewer assignments. Describe routine work as inspecting or reviewing; explain permission limits when asked or when they block a requirement. They do not require custom agent definitions. Diff Skeptic requires the platform's bundled reviewer definition because its read-only and no-delegation role cannot be enforced reliably by the skill prompt alone.

## Safety and verification

- Preserve pre-existing user changes and keep writes within the requested scope.
- Installation tooling must preflight all targets and refuse unmanaged conflicts.
- Uninstallation tooling may remove only repository-managed links or files.
- Reject absolute user-specific paths from portable agent definitions.
- Run `uv run python scripts/validate.py` and `uv run python -m unittest discover -s tests -v` after repository changes.
- Review the final combined state with an independent subagent created through the active coding tool's native subagent facility, and apply accepted findings before declaring completion. Keep the review in that tool; do not launch another coding agent CLI or external review service. If a suitable native reviewer is unavailable, report the unmet review requirement and continue authorized local checks.
