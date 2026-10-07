---
status: accepted
---

# The orchestrator makes worker worktrees

Delegated writers shared one checkout and were told to preserve each other's edits. That is an instruction, not isolation: parallel writers on The Forge's `build` level could still overwrite each other or the user's uncommitted work. Each writer in a Git repository now gets its own worker worktree, branched from the staging branch and merged back into it.

The runtimes' own isolation features were rejected because none of them branches from a staging branch the orchestrator picks:

- Claude Code's `isolation: "worktree"` branches from `origin/HEAD` by default. `worktree.baseRef: "head"` uses the current HEAD instead, but that is a user setting the skill cannot rely on, and it never accepts a branch name.
- Codex has no per-subagent worktree; its worktrees are per session.
- OhMyPi's `isolated: true` clones the parent's checkout, uncommitted changes included, and lands work by patch or cherry-pick onto the parent's HEAD.

One rule that the orchestrator runs with plain `git worktree add` behaves the same in every runtime, keeps the user's uncommitted changes out of the workers' view, and keeps merging under the orchestrator's control.

## Settled design

- `subagent-delegation` owns the rule; The Forge uses it like the other delegation rules.
- The staging branch is the task branch, such as `feature/37-recipes`. There is no separate integration branch.
- Every writer in a Git repository gets a worker worktree, including a sole writer. Researchers and reviewers do not. Work outside Git keeps the shared-workspace rule.
- So delegated edits in a Git repository always arrive as commits on the staging branch, outside The Forge too. Limiting worktrees to parallel writers, so a sole writer left an uncommitted diff, was rejected to keep one rule.
- Worker branches are `<staging>--<worker>`, because Git cannot create `feature/37-recipes/api` while `feature/37-recipes` exists. Worktree folders are siblings of the repository, `../<repo>--<worker>`.
- Worktrees start from a commit, so the orchestrator commits its own prerequisite work on staging first. It never commits the user's uncommitted changes to make them visible; it asks.
- Workers run the project's setup command in their worktree, commit their own work, and hand back the branch and commit.
- The orchestrator squash-merges each accepted branch into staging, naming the worker branch and its tip commit in the message. It resolves small conflicts; for a larger one the owning worker updates its branch from staging and retries.
- Squash merges are not seen as merged by `git branch -d`, so the orchestrator deletes a worker branch and worktree right after its squash only when the branch still points at the recorded tip. Anything else is kept and reported. Later fixes, such as accepted Forge findings, go to the same agent in a new worktree from the current staging branch.
