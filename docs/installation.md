# Installation

Use the shared [skills CLI](https://github.com/vercel-labs/skills) with [Bun](https://bun.sh). Replace `bunx` with `npx` if you prefer npm. Commands below target Codex globally; use the CLI's interactive prompts to choose another supported client or installation scope.

## Choose a source

Tagged collection releases are the stable channel. Choose a published tag from [releases](https://github.com/rmkr/skills/releases), read its notes, then enter its exact name:

```bash
read -r release
bunx skills@latest add "https://github.com/rmkr/skills/tree/$release" --global --agent codex --skill unslop
```

The first command waits for you to type the selected tag and press Enter. There are no published release tags yet; this command becomes usable when one exists. Do not treat an invented tag as a stable release. The GitHub tree URL selects the ref; `skills@latest` selects the installer version, not the collection release. This ref syntax was checked against skills CLI 1.5.26.

Until a release exists, or to try development changes, opt into the default branch:

```bash
bunx skills@latest add rmkr/skills --global --agent codex --skill unslop
```

To try unpublished edits, run this from the repository checkout:

```bash
bunx skills@latest add ./skills --global --agent codex --skill unslop
```

## Select skills and companions

`unslop` in the examples is a standalone skill. Replace it with the skill names you need, using the [README chooser](../README.md). Omit `--skill` to choose interactively.

The Forge needs Subagent Delegation; Setup rmkr skills is optional and configures delegation's model tiers and The Forge's reviewer policy. Install them from the same chosen release:

```bash
bunx skills@latest add "https://github.com/rmkr/skills/tree/$release" --global --agent codex --skill subagent-delegation forge setup-rmkr-skills
```

For development, substitute `rmkr/skills` for the release URL. Subagent Delegation and The Forge require matching orchestration contract version `1`; their presence in the runtime's skill catalog matters as well as their presence on disk.

Start a fresh session and confirm that the installed skills are available. In Codex, invoke `$unslop` or another `$skill-name`. Concise Write-up and Setup rmkr skills require explicit invocation. See [compatibility](compatibility.md) for other runtimes and enforcement limitations.

## Configure the strict reviewer

Installing The Forge does not install the custom reviewer its `strict` mode requires. Copy the matching reviewer from a checkout of the same collection release or development revision. Compare existing configuration before replacing it, preserve local customizations, and use the configured directory if your runtime data has been relocated.

| Runtime | Source in checkout | Default destination |
| --- | --- | --- |
| Codex | [Reviewer](../agents/forge_strict_reviewer.toml) | `~/.codex/agents/forge_strict_reviewer.toml` |
| Claude Code | [Reviewer](../agents/claude/forge-strict-reviewer.md) | `~/.claude/agents/forge-strict-reviewer.md` |
| OhMyPi | [Reviewer](../agents/omp/forge-strict-reviewer.md) | `~/.omp/agent/agents/forge-strict-reviewer.md` |

Open a fresh runtime session after configuration. Strict mode must confirm that effective controls prevent filesystem and external mutations and disable every delegation route. Copying the profile alone does not establish those controls. If the boundary cannot be verified, the strict review remains incomplete. Levels without `strict` do not require this custom agent.

## Update and remove

Finish active workflow runs and preserve local customizations before updating. Read the selected release's notes for behavior changes, dependencies, renames, removals, and migration steps. For stable installations, select the next published tag and rerun the explicit tagged `add` command with the same skill set. Update the matching strict reviewer from that tag too. Do not use an unqualified update command as the stable upgrade path: it does not explicitly select your reviewed release.

For installations that intentionally track development or other upstream sources, the CLI provides:

```bash
bunx skills@latest update --global
```

That command can update other installed skills too. It does not remove skills merged into The Forge: remove `adversarial-review-loop`, `forge-review-loop`, and `diff-skeptic`, and the `diff_skeptic_reviewer.toml` or `diff-skeptic-reviewer.md` reviewer copy, then install `forge` and its strict reviewer. To remove a skill from all CLI-managed agents:

```bash
bunx skills@latest remove --global --skill unslop
```

Add `--agent codex` to request removal for Codex only. Shared skill directories can remain when other detected agents use them; check the installed files and `bunx skills@latest list --global` rather than relying only on the removal message.

Do not remove a companion while keeping a workflow that requires it. Custom reviewer copies are separate from skill removal; remove one manually only after confirming it is the copy you installed and no remaining workflow needs it.

Older installations may still symlink into this repository. From the checkout, preview cleanup:

```bash
uv run python scripts/uninstall.py --target all --dry-run
```

The helper removes only repository-managed links. Inspect the preview before rerunning without `--dry-run`; preserve unmanaged files. From another checkout, pass `--repo-root` pointing to the repository that owns those links.

## Optional setup

The [recommendations page](recommendations.md) includes the optional collection picker and third-party setup links. It is not required to install an individual skill. For worktree-isolation instructions, see [GitButler configuration](agents/gitbutler.md).
