# Installation

## Codex plugin

Use Codex CLI `0.166.0` or a compatible newer version. The plugin packages all six skills together, including Forge and Subagent Delegation. It uses this repository's `skills/` files directly, with no second copy to maintain.

After the plugin files reach `main`, install from the development branch:

```bash
codex plugin marketplace add rmkr/skills --ref main
codex plugin add rmkr-skills@rmkr-skills
codex plugin list --marketplace rmkr-skills --json
```

Start a fresh session after installation or an update. Codex gives plugin skills a prefix, such as `$rmkr-skills:forge` and `$rmkr-skills:unslop`. The two explicit-only skills retain their invocation policy. Forge's strict reviewer still needs the [separate setup below](#strict-reviewer-setup).

### Existing installations

Choose one installation route per skill in Codex. Before using the plugin, disable the old copies in Codex's skill settings. Preserve shared files used by Claude Code or OhMyPi. Update saved prompts or global instructions to use the plugin's prefixed skill names where needed.

### Updates

Fetch the latest `main` revision and refresh the installed plugin:

```bash
codex plugin marketplace upgrade rmkr-skills --json
codex plugin list --marketplace rmkr-skills --json
```

The upgrade command refreshes both the Git marketplace and its installed plugin cache. Tracking `main` accepts later development changes. A fixed tag or commit stays pinned until you change the source ref. This route does not update separate skill installations or manually copied reviewers.

Codex CLI does not document a personal marketplace refresh interval. Use the optional task below for a set schedule. Workspace admins can instead use [GitHub marketplace sync](https://learn.chatgpt.com/docs/enterprise/plugin-management), which checks daily. See [OpenAI's plugin guide](https://developers.openai.com/plugins/build/plugins) for the package format and marketplace commands.

### Daily updates on macOS

Run the upgrade command above successfully first. Private repositories need saved Git access that works without a prompt. This task uses `launchd`, the macOS service that runs scheduled commands. It runs at login and every 24 hours while you are logged in. It updates this marketplace only.

Run this once in the shell where `codex` works. It records your current Codex executable, profile, and `PATH`. It preserves any existing task file with the same name.

```bash
python3 - <<'PY'
import os
import plistlib
import shutil
from pathlib import Path

codex = shutil.which("codex")
if codex is None:
    raise SystemExit("codex must be on PATH")
profile = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
agent = Path.home() / "Library/LaunchAgents/io.rmkr.skills-update.plist"
logs = Path.home() / "Library/Logs/rmkr-skills"
agent.parent.mkdir(parents=True, exist_ok=True)
logs.mkdir(parents=True, exist_ok=True)
with agent.open("xb") as stream:
    plistlib.dump({
        "Label": "io.rmkr.skills-update",
        "ProgramArguments": [codex, "plugin", "marketplace", "upgrade", "rmkr-skills", "--json"],
        "EnvironmentVariables": {"CODEX_HOME": str(profile), "PATH": os.environ["PATH"]},
        "WorkingDirectory": str(Path.home()),
        "RunAtLoad": True,
        "StartInterval": 86400,
        "StandardOutPath": str(logs / "update.log"),
        "StandardErrorPath": str(logs / "error.log"),
    }, stream)
PY
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/io.rmkr.skills-update.plist"
```

Check `~/Library/Logs/rmkr-skills/update.log` for an empty `errors` array after a run. Check `error.log` if the command failed. A failed network fetch needs a later retry; run the upgrade command to retry now. Start a fresh Codex session after a successful update. Recreate the task if you move Codex or change profiles.

To stop daily updates and remove this task:

```bash
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/io.rmkr.skills-update.plist"
rm "$HOME/Library/LaunchAgents/io.rmkr.skills-update.plist"
```

### Local test before merging

Keep tests outside your real Codex profile. From the checkout:

```bash
trial_profile="$(mktemp -d)"
CODEX_HOME="$trial_profile" codex plugin marketplace add "$PWD"
CODEX_HOME="$trial_profile" codex plugin add rmkr-skills@rmkr-skills --json
CODEX_HOME="$trial_profile" codex plugin list --marketplace rmkr-skills --json
```

This checks a local source. It does not exercise Git fetching or daily updates. `CODEX_HOME` separates plugin configuration and caches, but Codex can still discover shared skills from `~/.agents/skills`. Keep the trial profile until you finish inspecting it. Repository checks and an offline Git trial do not prove access to the published repository or behavior in the desktop app.

## Skills CLI

Choose one command to install individual skills from the development branch:

| Tool | Command |
| --- | --- |
| npm | `npx skills@latest add rmkr/skills --global` |
| Bun | `bunx skills@latest add rmkr/skills --global` |

Choose the skills and agents when prompted. Keep **Symlink** selected if asked for an installation method. This lets agents share one installed copy of each skill.

Install `subagent-delegation` with `forge`. Start a fresh agent session after installation.

See [skills CLI documentation](https://github.com/vercel-labs/skills) for other commands.

## Strict reviewer setup

forge's optional `strict` mode requires a separate reviewer. Copy the matching file from the same collection revision to your runtime's agent directory. Preserve existing custom settings. Use your configured directory if it differs from the default below.

| Runtime | Source in checkout | Default destination |
| --- | --- | --- |
| Codex | [Reviewer](../agents/forge_strict_reviewer.toml) | `~/.codex/agents/forge_strict_reviewer.toml` |
| Claude Code | [Reviewer](../agents/claude/forge-strict-reviewer.md) | `~/.claude/agents/forge-strict-reviewer.md` |
| OhMyPi | [Reviewer](../agents/omp/forge-strict-reviewer.md) | `~/.omp/agent/agents/forge-strict-reviewer.md` |

Start a fresh agent session after adding the reviewer. Strict mode must verify that its controls prevent writes and further delegation before it runs. See [reviewer boundaries](compatibility.md#reviewer-boundaries) for details.
