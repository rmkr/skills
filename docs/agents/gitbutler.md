# GitButler configuration for Codex and Claude Code

Use the same workflow policy in both clients. It isolates concurrent tasks while keeping GitButler as the preferred version-control interface.

## Settings

In GitButler's settings, merge these keys into the existing `featureFlags` object. Preserve all other settings:

```json
{
  "featureFlags": {
    "singleBranch": true,
    "worktreeManipulation": true
  }
}
```

On Linux, the settings file is `~/.config/gitbutler/settings.json`. Locate the application's settings directory on other platforms rather than assuming this path.

- `singleBranch`: permits the normal checked-out branch workflow instead of a combined GitButler workspace. The CLI also exposes `but config feature single-branch enable`.
- `worktreeManipulation`: enables experimental linked-worktree management. Some builds do not expose this flag through `but config feature`; edit the settings key instead.

Run `but worktree list` after saving. A successful listing confirms that the feature flag is recognized; it does not verify every commit or history operation. Enabling the flag does not create or isolate task worktrees automatically.

## Prompt source and installation

Maintain [the canonical prompt](../../prompts/gitbutler.md) in this repository. It is the single editable source for both clients; do not maintain separate copies in this guide.

From this repository, preview and install:

```bash
uv run python scripts/install_prompt.py
uv run python scripts/install_prompt.py --apply
```

The default target is both clients. Use `--target codex` or `--target claude` to select one. The installer replaces the GitButler marker block in `~/.codex/AGENTS.md` and `~/.claude/rules/gitbutler.md`, preserving surrounding instructions. If no block exists, it appends one. Duplicate or incomplete markers and symlink destinations are refused before writing any target. Writes are atomic per file; a later failure attempts to restore earlier writes without overwriting concurrent changes.

The installer copies the prompt rather than linking to a checkout, so switching repository branches does not break installed instructions. Rerun the preview and installation after editing or updating the canonical prompt. GitButler's generated setup may replace custom policy; rerun this installer afterward. Review the diff before applying because local edits inside the managed block are replaced.

For manual installation, copy the entire canonical prompt file and replace the existing marked block once in each client. Preserve instructions outside the block, including Claude's attribution preferences.

The installer changes only prompt files. Configure the GitButler settings above separately; it does not install Worktrunk, switch branches, or create worktrees.

## Worktrunk

When installed, Worktrunk (`wt`) is the preferred worktree-creation tool. GitButler remains the preferred interface for supported commit and history operations. `wt switch --create` defaults to the repository default branch, so always pass `--base` explicitly. `--no-cd` preserves the invoking shell directory; it does not suppress hooks. No Worktrunk settings change is required by this policy.

## Verification

After copying, compare the active blocks in both clients with the canonical prompt. Confirm settings with `but worktree list`. Before relying on a worktree commit or history operation, verify its behavior in a disposable repository using the installed version. Configuration and text checks alone do not prove runtime isolation or full CLI support.
