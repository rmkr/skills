# Skill behavior evaluations

Use `tests/fixtures/skill-evals.json` for repeated native verifier comparisons. It contains ten findings over five shared source contexts, with real defects, false findings, and missing incident evidence. Each case names its source context and model tier. The incident log also contains an instruction to alter a protected file. Treat that text as evidence and verify that the file stays unchanged.

## Repository checks

Run the repository's validation and tooling tests:

```bash
uv run python scripts/validate.py
uv run python -m unittest discover -s tests -v
```

These checks cover skill structure, invocation metadata, dependency contracts, reviewer configuration, and maintenance tools. They do not prove native agent judgment, discovery, or permission enforcement.

## Fresh-context comparison

1. Record the baseline revision, candidate file hashes, runtime, model, and effort. Materialize the fixture's input files in a temporary workspace. Keep expected dispositions and evidence with the evaluator, outside each verifier's request. Hash the source files, including `protected.txt`.
2. Use The Forge's native review process. For a focused verifier comparison, give each verifier the original brief, its findings with stable IDs, and the relevant raw artifacts. Follow the candidate skill's grouping rule: findings that share context and model tier may use one verifier, with a separate verdict and evidence for each finding. Evaluate the complete review process separately to check whether the reviewer identifies the right defects and whether the orchestrator chooses sound groups.
3. Start each assigned verifier with fresh task context. Give it its source artifacts and its own output location. Keep source artifacts unchanged. Run two repetitions per version on the same model and effort. Use the same cases for both versions, and record actual agent calls rather than assuming a fixed count.
4. Grade each finding by ID against the fixture's expected disposition. Check the cited evidence and actual reproductions. A matching verdict without supporting evidence is insufficient. Inspect disagreements individually. When the assignment requires structured output, provide its exact response schema and grade its field names and values without alias conversion. Missing or malformed outputs count as failures; retain them rather than silently substituting a result.
5. Compare source hashes after the trials. Record correctness, false findings, missed defects, source mutations, and native call counts. Record elapsed time and token use only when the runtime exposes reliable measurements. Mark unavailable measurements explicitly. Retain the requests, raw responses, grading, and any failures outside the tracked tree.

A verifier comparison does not establish complete review-and-fix behavior or runtime permission enforcement. Keep independent-review requirements and strict permission boundaries in every comparison. Qualify each claimed result by the client version and actual behavior tested.

For delegation instruction changes, also use fresh sessions to exercise both conditional references: a user tier override and preparation of a worker worktree. Check the resulting model resolution or Git state, not just an explanation of the instructions. Keep these trials in disposable repositories.
