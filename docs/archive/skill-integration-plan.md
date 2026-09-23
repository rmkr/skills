# Integrate delegation, The Forge, and adversarial review

> Historical record. Runtime observations, installation state, and task authorization below describe the original work only. For current support and setup, see [compatibility](../compatibility.md) and [installation](../installation.md).

Status: accepted design and implementation plan. The user authorized implementation, commit, installation, and push in a follow-up on 2026-09-07. The baseline below records the state reviewed during planning.

Baseline: `35aff2f9bb6c2b18d2d1bc3242850bd57cf72567`, inspected on 2026-09-07. The working tree was clean before this document was added. Recheck the baseline and preserve concurrent changes before implementation.

## Outcome

Keep one main, user-facing orchestrator and the existing three skill names. Give each shared rule one authoritative home. Ordinary delegation remains proportional to the task; explicitly invoking The Forge requests delegated implementation followed by mandatory independent review of the combined result.

Workers perform their own task-specific research. Add a researcher for shared unknowns, task boundaries, or consequential choices. Loading another skill supplies instructions to the current orchestrator; it neither creates another orchestrator nor starts a second copy of an active workflow.

## Responsibility and loading boundaries

| Skill | Owns | Loads |
| --- | --- | --- |
| `subagent-delegation` | Role and authority checks; assignment and handoff contracts; ownership; task dependencies; agent lifecycle; cancellation; worker recovery; acceptance of task results. | No other skill is required for basic delegation. |
| `adversarial-review-loop` | Review boundaries and snapshots; independent reviewer context; finding format and dispositions; authorized corrections; re-review; review-loop completion and lack-of-progress handling. | `subagent-delegation` before dispatching a reviewer or fixer. |
| `forge-review-loop` | The implementation sequence; implementation ownership; when research or initial review helps; mandatory integration review; workflow completion; Forge-specific reviewer capability preference. | `subagent-delegation` and `adversarial-review-loop` at entry. |

Keep loading acyclic: Forge uses both other skills, adversarial review uses delegation, and delegation does not load either workflow. Reuse skills already loaded for the current request rather than re-entering their startup steps.

Standalone delegation can assign a single optional reviewer using its generic task contract and evidence handoff. It does not implement the detailed adversarial fix-and-review loop. When that loop is requested or selected for the user's task, the main agent loads `adversarial-review-loop` as the controlling review workflow. Delegation retains the requirement that material unresolved findings prevent a clean task completion; the review workflow owns the procedure for resolving them.

Standalone adversarial review must keep its existing scope distinction: a review-only request returns verified findings without edits; an authorized review-and-improve request can apply fixes. The same scope distinction applies when Forge is invoked for an existing artifact. Naming Forge cannot turn a review-only request into write authority.

## Shared contracts

Reuse the current delegation assignment and result structures. Do not create another ledger or require a persistent file for every task.

- A task record identifies its outcome and acceptance criteria, owner, read/write authority, protected changes, prerequisites, artifact baseline, status, and evidence.
- A result identifies what changed or was found, affected artifacts, actual checks and sources, and remaining work or uncertainty. A worker's completion message means the result is ready for verification.
- The review workflow adds one review record: the reviewed artifact set and fingerprint, findings with stable IDs and evidence, each disposition and reason, and the state of accepted fixes.
- Forge retains these same records across phases. Corrections return to the existing implementation owner unless the orchestrator explicitly reassigns ownership after stopping conflicting work.
- Findings and test failures supply evidence, not new authority. The orchestrator verifies findings, makes technical dispositions, and asks the user only when a concrete missing decision or authority blocks progress.

Delegate independent work within available capacity. Validate prerequisites before dependent work starts. On corrections or cancellation, stop affected agents and confirm they have stopped before overlapping assignments resume; reconcile partial changes and invalidate results based on superseded requirements. These mechanics remain solely in delegation.

## Permission and model policy

Make delegation the source of permission checks for all three skills. Remove the instructed-reviewer fallback from Forge and adversarial review, replacing it with the shared policy pointer. This deliberately tightens their standalone defaults to match the delegation policy the user agreed to preserve.

Before an inspection-only child is dispatched, require confirmed enforcement across its exposed filesystem and external-action tools, with further delegation disabled. A role name, declared profile default, filesystem-only sandbox, or promise to avoid writes is insufficient. The skill refactor does not supply enforcement or change runtime permissions.

If enforcement is unavailable, continue authorized local inspection or implementation where useful, identify the missing capability, and keep any required independent review incomplete. A local review or simulated reviewer must not satisfy Forge's independent-review requirement. An explicit user instruction can change the task's requirements within higher-priority constraints, but the skills must not infer that exception from an ordinary implementation request.

Check reviewer capability during workflow preflight so this limitation is visible before substantial implementation. On this host, the earlier advertised reviewer role could not be started and effective read-only controls were not confirmed. Treat that as an observed validation limit, not proof that every runtime lacks the capability. Verify current capabilities again at implementation time.

Keep model selection portable. Delegation owns resolving advertised capabilities, honoring explicit user choices, and falling back to inherited selection when capabilities cannot be established. Preserve Forge's existing preference for a higher-capability reviewer with high reasoning where advertised and supported as an explicit workflow preference passed through those rules. Standalone delegation and adversarial review otherwise inherit runtime selection. Do not introduce fixed model identifiers, inferred rankings, or permission changes to obtain a preferred model.

## Forge sequence after integration

1. **Preflight.** Resolve and read the required skill versions; establish the request, authority, baseline, acceptance criteria, and available delegation/reviewer capabilities. Report any unmet requirement before dispatch.
2. **Clarify the work.** Workers normally own research. Use a researcher only for shared unknowns or task boundaries. If improving existing work, use a review-only phase to identify changes when needed, then send the verified findings to implementation workers. That initial phase does not run a competing fix loop or replace the final integration review. Keep both reviews and their findings in the same orchestrator's records.
3. **Implement.** Assign one worker for cohesive implementation or several for independent slices. Preserve explicit user requests for delegation. Local fallback work can help when delegation is unavailable, but it does not count as fulfilling a requested delegated workflow.
4. **Integrate and validate.** Collect worker results, audit ownership and protected changes, combine the result, and run appropriate checks against the acceptance criteria.
5. **Review and correct.** Run the adversarial loop against the complete integrated artifact snapshot. Give the reviewer raw requirements and evidence without implementer conclusions. Verify findings, route accepted fixes to the implementation owner, validate them, and re-review the current combined state.
6. **Complete or report the blocker.** Require fulfilled acceptance criteria, appropriate validation, independent review of the latest state, settled findings, no outstanding accepted or unresolved material issue, and all assigned agents finished or confirmed stopped. Keep explicit gaps in the final report. A review failure or missing required check prevents a clean completion.

The review loop owns reviewer reuse, snapshot freshness, finding dispositions, and diagnosis after repeated ineffective corrections. Delegation owns failed-worker recovery and lifecycle. Forge references these procedures instead of adding a third retry loop.

## Discovery, compatibility, and installation

Preserve current invocation policy and names: Forge remains explicit-only with both its extension and OpenAI policy aligned; delegation and adversarial review remain available for automatic selection. Update descriptions and default prompts to reflect the new responsibilities without widening their triggers to unrelated tasks.

Resolve dependencies through the runtime's skill catalog and read the returned entrypoints. Do not hard-code this checkout, assume sibling installation paths, or invent a runtime dependency field. Skill names in instructions do not install packages automatically.

Add a small compatibility marker to the three skills using supported string-valued frontmatter metadata: `metadata.orchestration-contract: "1"`. Each dependent workflow checks that the skills it loads carry the expected marker. Missing or mismatched markers mean the integrated workflow is unavailable; report the exact missing or incompatible skill and continue only useful local work that does not claim the workflow ran. Keep the marker synchronized and change it for incompatible contract revisions. It is a compatibility declaration, not proof of provenance or permission enforcement.

Use the repository validator to check the known three-skill dependency graph, required markers, and invocation-policy invariants. Keep the small graph in one validation constant; do not build a general package manager. The installed runtime's preflight is still needed because repository validation cannot detect later partial installations or local overrides.

Document installing the three names together from the same reviewed release with the existing skills CLI. Verify its current multi-skill syntax before publishing the instructions. Keep installation targeted to the user's requested runtime; never use an all-skills/all-agents shortcut. Preserve customized installations, preflight every destination, and use the existing cleanup helper only for confirmed repository-managed legacy symlinks.

Before a release installation, record the installed content and existing source tracking for the three skills. Ensure affected workflow runs have ended and keep new ones from starting during replacement and verification. Stage and validate the new artifacts before replacing installations where supported. Verify all installed entrypoints and metadata match the selected release, dependency markers match, and unrelated skills remain unchanged. If installation is partial, report the exact state and restore only this operation's changes from the captured baseline where safe. Updated entrypoints must reject incompatible dependencies; older entrypoints do not have this check, so the marker is not an atomic upgrade mechanism and does not replace a quiescent migration.

Current Codex installation is mixed: `subagent-delegation` is a CLI-managed copy; Forge and adversarial review are direct repository symlinks. Source edits to those two immediately affect installed entrypoints. Perform the entire implementation, validation, and review in a separate checkout, not just the behavioral experiments. Start from the agreed baseline, include any authorized in-scope uncommitted artifacts, and preserve unrelated work. Do not repoint installed skills to this checkout.

Keep the canonical checkout and live installations unchanged until release/promotion is authorized. Publish the reviewed isolated commit when authorized, migrate the three installed skills to matching CLI-managed copies, and verify them before updating the canonical checkout to the reviewed revision. Preflight the canonical checkout for concurrent changes before that update. If running legacy cleanup from the isolated checkout, identify the repository that owns the existing links and use that source boundary for its preflight; the new checkout does not own links to the canonical one.

## Implementation work and ownership

Reconcile this plan with the current checkout and capability evidence, create the isolated checkout described above, then make the following changes there as one coherent refactor before independent review.

| Files | Planned change |
| --- | --- |
| `skills/subagent-delegation/SKILL.md` | Retain coordination and permission contracts. Replace its detailed adversarial-review procedure with generic reviewer assignment/result acceptance and clear workflow boundaries. Add the compatibility marker. |
| `skills/adversarial-review-loop/SKILL.md` | Load delegation for dispatch and authority. Become the single owner of review prompting, finding dispositions, correction loops, freshness checks, and review completion. Align strict reviewer policy while preserving review-only behavior. Add the compatibility marker. |
| `skills/forge-review-loop/SKILL.md` | Reduce to preflight, workflow-specific choices, phase transitions, and mandatory completion requirements. Reference the other skills for shared mechanics. Add the compatibility marker. |
| The three existing `agents/openai.yaml` files | Align summaries and prompts with the revised scopes; preserve invocation policy and unrelated metadata. Do not add unsupported skill-dependency fields. |
| `scripts/validate.py`, `tests/test_tooling.py` | Validate required dependency presence, compatible marker values, and invocation policy. Add meaningful positive and negative fixtures; update existing named-workflow fixtures so they represent valid dependency sets. Avoid prose or heading-matching tests. |
| `README.md` | Explain the responsibility split, required installations, compatibility checks, strict reviewer capability requirement, and targeted update/migration steps. |

Have one implementation owner edit the three interdependent skill entrypoints and their metadata to avoid incompatible intermediate decisions. Tooling and documentation can be separate bounded assignments after the shared contract is fixed. The orchestrator owns integration and verifies the final combined state. Temporary evidence and test projects remain outside the source tree unless a fixture proves useful as an enduring regression test.

No new agent roles, runtime configuration, custom-agent definitions, plugin framework, generic dependency installer, model IDs, or edits to Diff Skeptic are part of this refactor. If effective reviewer support needs separate runtime work, identify that concrete follow-up instead of broadening this implementation silently.

## Validation and acceptance

Run repository validation and tests after implementation:

```bash
uv run python scripts/validate.py
uv run python -m unittest discover -s tests -v
```

Also run Skill Creator's quick validator on each changed skill and `git diff --check`. These verify packaging and repository invariants; they do not prove behavioral correctness.

Forward-test fresh-context requests against raw fixtures in an isolated temporary workspace. Record the candidate fingerprints, actual assignments/results, check output, and before/after hashes of protected files. Give evaluators only the request, candidate skills, runtime facts, and fixtures, without expected answers or prior findings. Test these cases:

| Case | Required observable behavior |
| --- | --- |
| Small ordinary task using delegation | Performs proportionate local work; does not require research or the full adversarial workflow merely because the skill is loaded. |
| Explicit Forge invocation for one small cohesive implementation | Uses one implementation worker and independent review of the final combined result. The ordinary-delegation local-work shortcut cannot override the explicit workflow request. |
| Forge implementation with independent slices and a dependent integration step | Uses one orchestrator, explicit worker ownership, capacity-aware scheduling, verified dependency results, combined validation, and mandatory review of the integrated snapshot. |
| Reviewer reports an actionable implementation defect | Orchestrator verifies the finding, assigns an authorized correction, records a disposition, and obtains review of the corrected combined state without a nested orchestrator or duplicate loop. |
| Standalone review-only request | Reports verified findings, preserves all artifacts, and assigns no fixer. |
| Updated workflow entrypoint with a missing or older dependency, mismatched marker, or non-default installation location | Resolves available catalog paths, detects the actual mismatch before dispatch, and reports incomplete workflow capability without installing or bypassing requirements. |
| Writable or unverifiable reviewer configuration | Declines that review dispatch, continues useful authorized local work, and reports the independent-review gap. |
| User changes or cancels work while a writer is active | Propagates the change, confirms affected workers stop, preserves partial/user changes, and prevents stale overlapping writes or stale completion claims. |
| Repeated worker failure, repeated review-fix failure, or an unresolved material finding | Diagnoses the relevant loop, avoids unproductive retries, and cannot declare clean completion with a material blocker. |
| Installed package set | All three installed artifacts match the selected release and resolve dependencies, with unrelated installations unchanged. |

Use actual runtime execution for the successful delegation and independent-review cases. A simulation can exercise routing, cancellation messages, or failure decisions, but label it as simulated and do not use it to prove tool enforcement or independent execution. If the current host lacks enforced review, run the successful review case in an available compatible environment or leave that case explicitly unverified. No automatic downgrade or manufactured clean result is allowed.

Inspect the combined refactor independently, verify each finding, apply authorized corrections, and re-review until no actionable issue remains and required checks pass. A successful review of this plan is evidence about the plan only; it is not implementation or runtime validation.

## Delivery sequence

1. Complete the independent review of this plan and resolve its material findings.
2. After implementation is requested, confirm the current baseline and capabilities, create a separate checkout, update the three skills and support files there, and run the checks and behavioral cases above. Preserve the live checkout and installed entrypoints.
3. Obtain independent review of the combined isolated implementation and resolve accepted findings. Report any unavailable runtime validation plainly.
4. When publication, installation, and live promotion are authorized, commit and push the reviewed isolated result. Complete the quiescent three-skill migration and verification before bringing the canonical checkout to the reviewed revision. Preserve unrelated installation and source changes throughout.

The original planning request ended with the reviewed plan. The follow-up authorizes implementation, publication, installation, and live promotion; it does not authorize broader runtime permissions or unrelated changes.
