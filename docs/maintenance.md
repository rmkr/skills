# Releases and maintenance

Austin ([@rmkr](https://github.com/rmkr)) owns scope, merge decisions, and releases. Maintenance is best effort. Contributors follow the [contribution guide](../CONTRIBUTING.md).

## Releases

Release the collection together under one version tag. Tagged releases are the stable installation source; `main` is development. Do not move an existing release tag to new content. Skills with companion requirements must ship compatible versions together.

Before tagging a release:

1. Run the repository validator and full tooling suite, and resolve independent-review findings. For changed instructions, retain representative fresh-session evidence and describe unverified runtime behavior.
2. Exercise the [installation instructions](installation.md) in a disposable project for a standalone skill and the integrated workflow set. Check required agent configuration against the same release. Preserve live installations and customizations.
3. Write release notes covering behavior changes, dependency changes, renames, removals, and migration or manual setup steps. State what was tested and any support limitations.
4. Publish only the reviewed commit when release publication is authorized. After tagging, verify installation from the actual published tag before presenting it as stable.

There is no fixed release schedule. Until the first tagged release exists, users can explicitly choose the development installation route.

## Merge enforcement

Require maintainer approval for contributed pull requests, and require the `validate` status check on `main` with an up-to-date branch whenever the `Validate` workflow is enabled. The repository's code owner is `@rmkr`. Protect against force pushes and branch deletion. Keep existing protections when adjusting settings.

GitHub code-owner review requires the ownership file on the target branch. Repository administrators can bypass classic branch protection unless administrator enforcement is enabled. A sole maintainer cannot approve their own pull request: for maintainer-authored work, use the independent-review process and passing local checks before merging, and record both in the pull request. Do not claim this human decision is mechanically enforced by a self-approval rule.

On 2026-09-16, the private repository's `main` protection was configured with the required `validate` check, up-to-date branches, one approving code-owner review, stale-review dismissal, and force-push/deletion protection. Administrator bypass remains enabled for maintainer-owned work as described above.

Since 2026-09-09, GitHub has not started `Validate` jobs for this private repository: the account's Actions billing blocks them. (The last runs on 2026-09-08 failed on a missing tooling dependency, which the workflow now installs.) On 2026-09-27 the workflow was disabled, and the required `validate` check and its up-to-date-branch requirement were removed, so pull requests no longer wait on CI; the review, force-push, and deletion protections are unchanged. Until CI is restored, validation and tooling tests run locally. To restore CI, resolve the Actions billing block (or point `runs-on` in `.github/workflows/validate.yml` at another runner provider), re-enable the workflow, confirm a pull-request run of `validate` passes, then require the `validate` check with up-to-date branches again and verify it with `gh api repos/rmkr/skills/branches/main/protection`.

CI configuration and ownership declarations take effect on GitHub after they are pushed. Restore and verify CI before opening the repository to outside contributions; local validation cannot establish that GitHub ran a workflow.

## Public-readiness review

Keep the landing documentation focused on maintained skills. Historical research, plans, and the incomplete inspector evaluation are preserved in [the archive](archive/) with historical-state notices; they do not grant current task authority or establish current runtime support. New scratch work is ignored by default.

Before changing visibility, review the intended public tree and reachable history for credentials, personal information, and third-party attribution. Removing a file from the current tree does not remove it from history. Resolve concrete findings without discarding unrelated work or rewriting history without authorization.

The project uses the [MIT license](../LICENSE). Unslop retains its [original MIT notice](../skills/unslop/LICENSE), including Lauren Tan's attribution. Keep imported notices with their material.

Making the repository public, publishing a release, and pushing local commits are separate actions from preparing and committing these changes.
