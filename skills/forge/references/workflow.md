# Workflow option

`workflow` hands the review, verification, and fix rounds to [the workflow script](../workflows/forge.js), so the loop's control flow runs deterministically. The rest of The Forge still applies, and the main agent stays orchestrator around the run. The script's verifier subagents verify each finding, and the orchestrator audits their verdicts after the run.

## Check the runtime

Run the script through the Workflow tool, available in Claude Code, with `scriptPath` set to the script's absolute path. Attaching `workflow` to The Forge is the user's opt-in to run it. When the runtime has no Workflow tool or refuses the script, report that `workflow` is unavailable here and run the same level without it.

## Prepare the run

Complete The Forge's steps through "Set the boundary" first: the coordination contract, tiers and reviewer, the boundary, and the reviewer preflight. At `build`, implement and integrate through [build](build.md), then run the script at `fix` on the integrated snapshot; its fixer takes the place of the implementation owners for the loop.

At `fix` in a Git repository, the script's fixer is a writer. Give it a worker worktree under delegation's worktree steps, created from the staging branch, so protected user changes stay outside the target. Point `target`, `snapshot`, and `checks` at that worktree. Outside Git, the fixer edits the target in place and preserves others' edits.

Pass `args` as a JSON object:

- `level`: `review` or `fix`.
- `brief`: the original request, governing requirements, acceptance criteria, and the review criteria and assumptions you derived. Keep proposed fixes, suspected bugs, and earlier conclusions out.
- `target`: what to review, where it lives, and how to read it. At `fix` with a Git target, compare the recorded base with the worker worktree's working tree, so the fixes stay in view. At `strict`, name the bundle and base tree from [strict](strict.md).
- `snapshot`: a shell command, run from the target checkout, that captures the target and prints its fingerprint. The same content must print the same output. At `strict`, it rebuilds the bundle and prints its digest.
- `checks`: the required validation commands.
- `strict`: true at `strict`.
- `complexity`: true when The Forge's complexity reviewer condition holds.
- `reviewer`: `{model, effort}` from "Match models to roles", with the Agent-tool model alias. At `strict`, the script passes only the model, so the strict reviewer keeps the session effort.
- `tiers`: every resolved tier, lowest first, as `{name, work, model, effort}`, added tiers included. Omit a field to inherit the session's. The script runs snapshots on apprentice and verification, fixes, and the complexity pass on engineer.
- `dynamic`: true at `dynamic`. Verification and fixes then run at each finding's tier, and a failed fix escalates.
- `max_rounds`: only from a user budget.

The script starts a fresh reviewer each round and runs the complexity pass once, after the first round with no accepted findings. Run another complexity pass yourself when later fixes change the source substantially. Effort `ultra` runs as `max`, the highest the Workflow tool accepts; report it.

## Act on the result

The run returns `status`, `rounds`, the final `fingerprint`, a `ledger` of every finding with its disposition, `open_questions`, `coverage_gaps`, `escalations`, and `last_checks`. Audit the ledger: re-verify any disposition whose reason looks weak, then act on `status`:

- `clean`: run the required checks and acceptance criteria on the final state, confirm its fingerprint, commit the worker worktree, and integrate it under delegation's worktree steps. A failure becomes a finding for another run.
- `findings`: the `review` result; report the dispositions.
- `unresolved`: bring the unresolved findings to the user with their evidence.
- `stalled`: an issue survived two fixes. Diagnose it before another run.
- `changed`: the target changed under review. Reconcile, then run again.
- `checks-failed`, `budget`, or a `-failed` status: report it and the remaining findings. The loop is incomplete.

On any status but `clean`, keep the worker worktree and report its path. Run the next attempt against the same worktree, or integrate its accepted fixes under delegation's worktree steps.

To resume an interrupted run, first run `snapshot` and compare it with the last snapshot result in the run's `journal.jsonl`. Resume with `resumeFromRunId` only when they match; otherwise start a new run. Report the run ID with The Forge's report.
