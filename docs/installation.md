# Installation

Choose one command to install this collection globally from the development branch:

| Tool | Command |
| --- | --- |
| npm | `npx skills@latest add rmkr/skills --global` |
| Bun | `bunx skills@latest add rmkr/skills --global` |

Choose the skills and agents when prompted. Keep **Symlink** selected if asked for an installation method. This lets agents share one installed copy of each skill.

Install `subagent-delegation` with `forge`. Start a fresh agent session after installation.

See [skills CLI documentation](https://github.com/vercel-labs/skills) for other commands.

## Strict reviewer setup

The Forge's optional `strict` mode requires a separate reviewer. Copy the matching file from the same collection revision to your runtime's agent directory. Preserve existing custom settings. Use your configured directory if it differs from the default below.

| Runtime | Source in checkout | Default destination |
| --- | --- | --- |
| Codex | [Reviewer](../agents/forge_strict_reviewer.toml) | `~/.codex/agents/forge_strict_reviewer.toml` |
| Claude Code | [Reviewer](../agents/claude/forge-strict-reviewer.md) | `~/.claude/agents/forge-strict-reviewer.md` |
| OhMyPi | [Reviewer](../agents/omp/forge-strict-reviewer.md) | `~/.omp/agent/agents/forge-strict-reviewer.md` |

Start a fresh agent session after adding the reviewer. Strict mode must verify that its controls prevent writes and further delegation before it runs. See [reviewer boundaries](compatibility.md#reviewer-boundaries) for details.
