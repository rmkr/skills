# Workflow option

`workflow` hands the review, verification, and fix rounds to [the workflow script](../workflows/forge.js), so the loop's control flow runs deterministically. The rest of The Forge still applies, and the main agent stays orchestrator around the run.

## Check the runtime

Run the script through the Workflow tool, available in Claude Code, with `scriptPath` set to the script's absolute path. Attaching `workflow` to The Forge is the user's opt-in to run it. When the runtime has no Workflow tool or refuses the script, report that `workflow` is unavailable here and run the same level without it.

## Prepare the run

Complete The Forge's steps through "Set the boundary" first: the coordination contract, tiers and reviewer, the boundary, and the reviewer preflight. At `build`, implement and integrate through [build](build.md), then run the script at `fix` on the integrated snapshot.

Pass `args` as a JSON object:

- `level`: `review` or `fix`.
- `brief`: the original request, governing requirements, acceptance criteria, and the review criteria and assumptions you derived. Keep proposed fixes, suspected bugs, and earlier conclusions out.
- `target`: what to review, where it lives, and how to read it. For a Git target, compare the base with the working tree, so uncommitted fixes stay in view. At `strict`, name the bundle and base tree from [strict](strict.md).
- `snapshot`: a shell command, run from the target checkout, that captures the target and prints its fingerprint. The same content must print the same output. At `strict`, it rebuilds the bundle and prints its digest.
- `checks`: the required validation commands.
- `strict`: true at `strict`.
- `complexity`: true when The Forge's complexity reviewer condition holds.
- `models`: per role, `{model, effort}` with the Agent-tool model alias. Set `reviewer` from "Match models to roles", `complexity` to engineer, and `verifier`, `fixer`, and `snapshot` from delegation's tier for that work. Omit a field to inherit the session's.
- `dynamic` and `tiers`: at `dynamic`, set `dynamic` to true and list `tiers` lowest first as `{name, work, model, effort}`, added tiers included. Only `reviewer` and `complexity` are then read from `models`.
- `max_rounds`: only from a user budget.

## Act on the result

The run returns `status`, `rounds`, the final `fingerprint`, a `ledger` of every finding with its disposition, `open_questions`, `coverage_gaps`, `escalations`, and `last_checks`. Audit the ledger: re-verify any rejected or unresolved disposition whose reason looks weak, then act on `status`:

- `clean`: run the required checks and acceptance criteria on the final state, confirm its fingerprint, and finish. A failure becomes a finding for another run.
- `findings`: the `review` result; report the dispositions.
- `unresolved`: bring those findings to the user with their evidence.
- `stalled`: diagnose the repeating issue before another run.
- `changed`: the target changed under review. Reconcile, then run again.
- `checks-failed`, `budget`, or a `-failed` status: report it and the remaining findings. The loop is incomplete.

Resume an interrupted run with `resumeFromRunId` rather than restarting it. Report the run ID with The Forge's report.
