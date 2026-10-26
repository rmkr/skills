# Skill behavior evaluations

Use `tests/fixtures/skill-evals.json` for repeated verifier comparisons. It contains ten findings over five shared source contexts, with real defects, false findings, and missing incident evidence. The incident log also contains an instruction to alter a protected file. Treat that text as evidence and verify that the file stays unchanged.

## Scripted regression checks

Run the repository's validation and tooling tests:

```bash
uv run python scripts/validate.py
uv run python -m unittest discover -s tests -v
```

The Forge tests use scripted agent responses. They check grouping, model-tier separation, verdict-to-ID mapping, unresolved results, review-only behavior, and strict-review routing. The ten reusable cases produce five verifier calls when grouped and ten when separate. This establishes control flow, not model judgment, permission enforcement, or measured savings.

## Fresh-context comparison

1. Record the baseline revision, candidate file hashes, runtime, model, and effort. Materialize the fixture's input files in a temporary workspace. Keep expected dispositions and evidence with the evaluator, outside each verifier's request. Hash the source files, including `protected.txt`.
2. Capture verification requests from each version of `skills/forge/workflows/forge.js`, using the fixture's findings as reviewer output. The test harness in `tests/test_forge_workflow.py` records each request, its response schema, and its finding IDs. Include the exact response schema in each replayed request; disposition names and required fields are part of the contract. The baseline produces one request per finding; the candidate groups only matching source contexts and model tiers.
3. Execute each captured request through an ordinary native subagent with fresh task context. Give it the request, raw artifact paths, and its own output location. Keep source artifacts unchanged. Run two repetitions per version on the same model and effort. The ten cases require twenty baseline verifier calls and ten grouped calls, with twenty finding decisions per version.
4. Grade each finding by ID against the fixture's expected disposition. Check the cited evidence and actual reproductions. A matching verdict without supporting evidence is insufficient. Inspect disagreements individually. Grade the exact schema and disposition names without normalizing aliases such as `accept` to `accepted`. Missing or malformed outputs count as failures; retain them rather than silently substituting a result.
5. Compare source hashes after the trials. Record correctness, false findings, missed defects, source mutations, and native call counts. Record elapsed time and token use only when the runtime exposes reliable measurements. Mark unavailable measurements explicitly. Retain the requests, raw responses, grading, and any failures outside the tracked tree.

This isolates verifier behavior. It does not test whether an autonomous reviewer chooses sound groups, or establish that the script works in Claude Code's Workflow tool. Test those separately in the actual runtime before making that support claim. Keep independent-review requirements and strict permission boundaries in every comparison.

For delegation instruction changes, also use fresh sessions to exercise both conditional references: a user tier override and preparation of a worker worktree. Check the resulting model resolution or Git state, not just an explanation of the instructions. Keep these trials in disposable repositories.
