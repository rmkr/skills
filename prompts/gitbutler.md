<!-- gitbutler-agent-setup:start -->
## Version control

### Task isolation and starting point

- Use GitButler (`but`) for supported version-control operations. This policy takes precedence over shared-workspace examples and automatic-update recipes in the installed GitButler skill; use that skill and command help for current syntax.
- Give each concurrent task its own worktree and branch. Use the user's specified starting branch or commit; otherwise capture the branch and commit checked out in the user's source checkout when the task starts. Do not assume `main`, `master`, the remote target, or a different task's branch. Resolve an ambiguous source before creating the worktree.
- Resume existing work in its existing task worktree. Reuse a worktree already provided by the coding tool; do not create a nested one. A captured commit or explicitly selected detached HEAD is a valid starting point. Create a task branch before committing.
- Leave the user's source checkout and other tasks' branches untouched. Starting from a feature branch includes its existing commits; later changes on that branch are not incorporated automatically.
- Before repository edits, verify the task directory, branch or detached HEAD, and captured base. Prefer Worktrunk (`wt`) for worktree creation when installed. Pass the selected base explicitly: `wt switch --create <task-branch> --base <selected-base> --no-cd --format json`; never rely on its default branch. Read the returned worktree path, use that directory for subsequent commands, and verify its starting commit matches the captured base. Inspect configured hooks before running them; handle hook effects under the task's existing authorization rather than blindly approving them. If `wt` is unavailable, use native worktree creation, then a scoped `git worktree add` with the captured commit as a fallback. Do not run `but setup` in a linked worktree or combine in-progress branches in the task checkout.
- If the source has uncommitted changes needed by the task, preserve them and use a supported handoff or explicit selection; do not silently omit them or copy unrelated changes. A request to commit existing dirty changes may be handled in their existing checkout without moving them. Do not switch a shared checkout without the user's authorization.

### Commands and commits

- Inspect changes with `but diff`. Use `but status` for branch context and `but status -fv` when file or hunk identifiers are needed. Read-only Git inspection is permitted when GitButler does not expose the needed fact.
- For linked worktrees, prefer GitButler's supported controlling-checkout operations, using worktree-scoped change IDs and this task's branch as the target. Never mix changes from different checkouts. If the installed version rejects worktree-local commits and offers no supported scoped route, use Git to commit only this task's selected changes in its own worktree. For other unsupported mutations, report the limitation instead of changing shared state or enabling bypass modes.
- Keep the selected-change fast path only where the installed version and checkout mode support it safely: `but diff`, then `but commit -b <task-branch> -m "type(scope): summary" <id> <id>`. In single-branch mode, creating a branch may switch the checkout; do this only in the task's own worktree or with user authorization. Reuse the existing task branch rather than creating another branch for every commit.
- Commit only this task's files or hunks. Preserve unrelated changes, including other changes in the same file. Keep tests with the behavior they verify; split unrelated work into coherent commits.
- Make a local checkpoint after completing a requested change and running relevant checks, or reporting unmet checks. Read-only work and personal configuration outside a repository need no repository commit. Checkpoints do not authorize pushing or publication.
- Use `type(scope): summary` commit messages. Keep messages and PR descriptions concise and explain the change and its reason. Do not push, create PRs, or land changes onto a base branch unless the user asks.
- Trust successful mutation output. Request `--status-after` only when the next step needs resulting IDs or state; inspect again when output is ambiguous. A commit-only request ends after the requested commit succeeds; a larger task continues until its remaining requirements are met.

### Updates and history

- Keep the task's captured or explicitly selected base separate from GitButler's remote target. Do not start new work with an automatic pull or replace the selected base because another checkout moved.
- Before an update or history operation, check its target and affected branches. Use GitButler only when it can restrict the operation to authorized work. Do not rebase, move, unapply, amend, discard, or otherwise change another task's work without user authorization.
- Amend a small follow-up into its matching unpublished task commit when ownership and intent are clear. Ask before rewriting pushed, shared, reviewed, or ambiguous history. Tidy unpublished checkpoints only when requested.
- If an update reports conflicts, stop and report them unless resolution was authorized. Ask before resolving semantic conflicts, dependency updates, generated files, or conflicts involving another person's work. Never discard unrelated work to make an operation succeed.
<!-- gitbutler-agent-setup:end -->
