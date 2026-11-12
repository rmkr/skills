# Installation

## Codex plugin

Use Codex CLI `0.166.0` or a compatible newer version. The `rmkr` plugin packages all four skills together, including Forge and Subagent Delegation. It uses this repository's `skills/` files directly, with no second copy to maintain.

After the plugin files reach `main`, install from the development branch:

```bash
codex plugin marketplace add rmkr/skills --ref main
codex plugin add rmkr@rmkr-skills
codex plugin list --marketplace rmkr-skills --json
```

Start a fresh session after installation or an update. Codex gives plugin skills a prefix, such as `$rmkr:forge` and `$rmkr:unslop`. The two explicit-only skills retain their invocation policy. Forge's strict reviewer still needs the [separate setup below](#strict-reviewer-setup).

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
CODEX_HOME="$trial_profile" codex plugin add rmkr@rmkr-skills --json
CODEX_HOME="$trial_profile" codex plugin list --marketplace rmkr-skills --json
```

This checks a local source. It does not exercise Git fetching or daily updates. `CODEX_HOME` separates plugin configuration and caches, but Codex can still discover shared skills from `~/.agents/skills`. Keep the trial profile until you finish inspecting it. Repository checks and an offline Git trial do not prove access to the published repository or behavior in the desktop app.

## Claude Code plugin

The `rmkr` Claude Code plugin loads the same four skill folders as the Codex plugin. Custom agents remain a separate installation, so Claude does not scan the other runtimes' reviewer files.

After the Claude plugin files reach `main`, install from the development branch:

```bash
claude plugin marketplace add rmkr/skills#main
claude plugin install rmkr@rmkr-skills
claude plugin list --json
```

Start a fresh session. Plugin skills use commands such as `/rmkr:forge` and `/rmkr:unslop`. Setup rmkr skills keeps its explicit-only invocation policy. Forge's strict reviewer still needs the [separate setup below](#strict-reviewer-setup).

If you already use individual skills in Claude Code, choose one installation route per skill. Remove only the old Claude links after checking them. Preserve shared skill folders used by other agents and any custom reviewer settings. Update saved prompts to use the plugin's prefixed commands where needed.

### Updates

Refresh the marketplace and the installed plugin:

```bash
claude plugin marketplace update rmkr-skills
claude plugin update rmkr@rmkr-skills
```

Start a fresh session after an update. For automatic updates, run `/plugin` in Claude Code, open **Marketplaces**, select `rmkr-skills`, and select **Enable auto-update**. Third-party marketplaces have auto-update off by default. See [Claude Code's plugin guide](https://code.claude.com/docs/en/discover-plugins) for update behavior.

### Local test before merging

From the checkout, validate both files and install into a disposable Claude profile:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
trial_profile="$(mktemp -d)"
CLAUDE_CONFIG_DIR="$trial_profile" claude plugin marketplace add "$PWD"
CLAUDE_CONFIG_DIR="$trial_profile" claude plugin install rmkr@rmkr-skills
CLAUDE_CONFIG_DIR="$trial_profile" claude plugin list --json
CLAUDE_CONFIG_DIR="$trial_profile" claude plugin details rmkr@rmkr-skills
```

This checks local installation and the component list. It does not prove GitHub fetching, skill behavior, or strict-reviewer permission enforcement. See [Claude Code's manifest reference](https://code.claude.com/docs/en/plugins-reference) for the package format. Keep the trial profile until you finish inspecting it.

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

forge's optional `strict` mode requires a separate reviewer, including for plugin installations. Copy the matching file from the same collection revision to your runtime's agent directory. Preserve existing custom settings. Use your configured directory if it differs from the default below.

| Runtime | Source in checkout | Default destination |
| --- | --- | --- |
| Codex | [Reviewer](../agents/forge_strict_reviewer.toml) | `~/.codex/agents/forge_strict_reviewer.toml` |
| Claude Code | [Reviewer](../agents/claude/forge-strict-reviewer.md) | `~/.claude/agents/forge-strict-reviewer.md` |
| OhMyPi | [Reviewer](../agents/omp/forge-strict-reviewer.md) | `~/.omp/agent/agents/forge-strict-reviewer.md` |

Start a fresh agent session after adding the reviewer. Strict mode must verify that its controls prevent writes and further delegation before it runs. See [reviewer boundaries](compatibility.md#reviewer-boundaries) for details.
