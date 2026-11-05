# Releases and maintenance

Austin ([@rmkr](https://github.com/rmkr)) owns scope, merge decisions, and releases. Maintenance is best effort. Contributors follow the [contribution guide](../CONTRIBUTING.md).

## Releases

Release the collection together under one version tag. Tagged releases are the stable installation source. Merging a new collection version to `main` authorizes publication after its checks pass. Do not move an existing release tag to new content. Skills with companion requirements must ship compatible versions together.

Keep the root `plugin.json` version equal to the collection version in `pyproject.toml`. The Codex marketplace points at the repository root, so the plugin uses the same skills as individual installations. The development plugin tracks `main`; its scheduled updates take effect after reviewed changes reach that branch.

Before merging a release:

1. Run the repository validator and full tooling suite, and resolve independent-review findings. For changed instructions, retain representative fresh-session evidence and describe unverified runtime behavior.
2. Exercise the [installation instructions](installation.md) in a disposable project for a standalone skill and the integrated workflow set. Check required agent configuration against the same release. Preserve live installations and customizations.
3. Update [CHANGELOG.md](../CHANGELOG.md) under the selected version. Cover behavior changes, dependency changes, renames, removals, and migration or manual setup steps. Use a version heading without an `unreleased` label for new entries; GitHub Releases records publication status and date. Older unreleased entries are historical changelog groups, not separate published releases.
4. Write the PR title and description for release readers. GitHub generates the release notes from merged PRs and contributors. State checks and remaining limitations in the PR.

The `Validate` workflow runs the validator and tooling tests first. Its release job then reads `pyproject.toml` and publishes `v<version>` from that validated `main` commit. Only this job gets `contents: write`; pull requests run checks without publishing. A manual workflow run on `main` also validates before attempting publication.

The job generates notes through GitHub, creates the tag and release, or publishes an existing draft with fresh notes and the validated target. It skips published versions and stale runs when `main` has advanced. An existing tag must resolve to the validated commit; a mismatch stops the job without moving the tag. Release jobs run one at a time.

No package build or custom release asset is needed for this Git-based plugin. GitHub supplies [source archives](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases). After publication, verify installation from the actual tag in a disposable Codex profile before presenting that route as verified:

```bash
trial_profile="$(mktemp -d)"
CODEX_HOME="$trial_profile" codex plugin marketplace add rmkr/skills --ref v0.3.4
CODEX_HOME="$trial_profile" codex plugin add rmkr@rmkr-skills --json
```

Replace `v0.3.4` with the published version being checked. Fixed tags stay pinned; the daily development updater continues to follow `main`.

If publication fails, inspect the failed job and rerun the `Validate` workflow on `main`. A rerun cannot replace a published version or move its tag. Fix a version or tag mismatch through a reviewed change. No personal access token or separate release secret is required; the job uses GitHub's built-in token.

The [skill evaluation guide](skill-evaluation.md) describes reusable verifier cases and fresh-context comparisons. Keep raw trial artifacts outside the tracked tree.

## Merge enforcement

Require maintainer approval for contributed pull requests, and require the `validate` status check on `main` with an up-to-date branch whenever the `Validate` workflow is enabled. The repository's code owner is `@rmkr`. Protect against force pushes and branch deletion. Keep existing protections when adjusting settings.

GitHub code-owner review requires the ownership file on the target branch. Repository administrators can bypass classic branch protection unless administrator enforcement is enabled. A sole maintainer cannot approve their own pull request: for maintainer-authored work, use the independent-review process and passing local checks before merging, and record both in the pull request. Do not claim this human decision is mechanically enforced by a self-approval rule.

On 2026-11-05, the public repository's `Validate` workflow was active, and the plugin PR and its merge to `main` passed `validate`. Branch protection required that check and one approving code-owner review, with stale-review dismissal. The check did not require an up-to-date branch. Administrator bypass remained enabled. Recheck live enforcement with `gh api repos/rmkr/skills/branches/main/protection` when changing it.

CI configuration and ownership declarations take effect on GitHub after they are pushed. Local tests do not prove a live release job or publication from the final tag.

## Public-readiness review

Keep the landing documentation focused on maintained skills. Historical research, plans, and the incomplete inspector evaluation are preserved in [the archive](archive/) with historical-state notices; they do not grant current task authority or establish current runtime support. New scratch work is ignored by default.

Before changing visibility, review the intended public tree and reachable history for credentials, personal information, and third-party attribution. Removing a file from the current tree does not remove it from history. Resolve concrete findings without discarding unrelated work or rewriting history without authorization.

The project uses the [MIT license](../LICENSE). Unslop retains its [original MIT notice](../skills/unslop/LICENSE), including Lauren Tan's attribution. Keep imported notices with their material.

Unslop is adapted from [cursor/plugins pstack](https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md) at `bc697d0`. Its rules are rewritten and renumbered for this repository, so port upstream changes by hand.

Making the repository public, publishing a release, and pushing local commits are separate actions from preparing and committing these changes.
