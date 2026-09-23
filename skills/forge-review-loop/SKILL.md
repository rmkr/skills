---
name: forge-review-loop
description: Delegate authorized software engineering or software architecture work, independently review the combined result, and repeat fixes and verification until the acceptance criteria are met. Excludes general Work tasks such as document, presentation, spreadsheet, or business-content review.
disable-model-invocation: true
metadata:
  orchestration-contract: "1"
---

# The Forge

Check that the task concerns software engineering or software architecture before loading dependencies. Include engineering documents and agent skills when they serve that work. For non-engineering tasks, use the task's own workflow without starting The Forge or loading its dependencies. Determine scope from the subject, not the app or file format.

Use this workflow when explicitly invoked for delegated implementation and mandatory independent review. Keep the main agent as the user-facing orchestrator throughout. Loading the supporting skills supplies instructions to that orchestrator; it does not create another coordinator or start another copy of an active loop. A review-only request remains review-only even when it names The Forge.

## Preflight the workflow

Resolve `subagent-delegation` and `adversarial-review-loop` through the active runtime's skill catalog and read their returned entrypoints. Require this skill and both dependencies to declare `metadata.orchestration-contract: "1"`. Reuse dependencies already loaded and checked for the current request. Do not assume sibling paths or install missing skills automatically. If a required skill cannot be found or read, or its marker is missing or incompatible, identify that skill and report the integrated workflow unavailable. Continue useful authorized local work without claiming The Forge ran.

Establish the requested outcomes, checkable acceptance criteria, write authority, and artifact baseline, including protected user changes. Use authority already present in the conversation. Ask only when a concrete missing decision or additional authority blocks progress. Keep one set of task records and review findings across all phases.

Use `subagent-delegation` for role resolution, assignments, permissions, ownership, scheduling, handoffs, worker recovery, and cancellation. Use `adversarial-review-loop` for independent review and its correction procedure. Check native review delegation before substantial work, and implementation delegation only when implementation is requested. An ordinary reviewer with an inspection-only assignment is sufficient unless the user explicitly requires stronger isolation. If a required capability is unavailable, disclose the unmet workflow requirement; useful local work does not fulfill required delegation or independent review. Honor an explicit instruction to wait for that capability.

Pass these workflow preferences through delegation's model-selection rules: an appropriate execution-capable worker, and the highest-capability advertised reviewer with high reasoning when supported. Explicit user choices take precedence. If capability ranking or selection is unavailable, inherit runtime selection and disclose the limitation. These preferences do not change permissions or justify invented model rankings.

## Clarify and implement

Workers normally perform their own task-specific research. Use a researcher only when shared unknowns, consequential choices, or task boundaries justify it under the delegation contract.

When existing work needs an initial assessment, run an adversarial review-only phase and return its verified findings to implementation. Keep its findings in the same records; this phase does not run a competing fix loop or replace the final combined review. If the user's entire request is review-only, return verified findings without assigning implementers or applying fixes.

Assign one worker for a cohesive implementation, including a small task that explicitly invokes The Forge. Use multiple workers for independent slices. The ordinary-delegation shortcut for local work cannot skip this workflow's implementation worker. Apply the shared ownership and scheduling rules; validate prerequisites before dependent work starts. The orchestrator may investigate, integrate, validate, and make cohesive integration fixes within existing authority.

## Integrate, review, and correct

Collect worker results, audit actual changes against ownership and the protected baseline, integrate the combined result, and run appropriate acceptance checks. A worker's completion message is evidence for verification, not acceptance by itself.

Run `adversarial-review-loop` against the complete integrated artifact snapshot with the original requirements and raw validation evidence. That workflow owns reviewer context, snapshot freshness, finding dispositions, correction checks, reviewer reuse, and diagnosis after ineffective fixes. Do not add another review loop or call back into The Forge from a dependency.

Route accepted corrections to the existing implementation owner unless ownership has been explicitly reassigned under the delegation contract. Collect and validate corrections before re-reviewing the current combined state. Retain the same acceptance criteria and finding IDs throughout.

## Complete or report the blocker

For implementation, finish when acceptance criteria and required checks pass, the latest combined state has independent review, every finding has a disposition, no accepted issue or unresolved material finding remains, and all assigned agents have finished or are confirmed stopped. A review-only request finishes through the review workflow's reporting criteria; it does not enter implementation or require fixing reported defects.

A missing reviewer capability, failed required check, outstanding material question, or stale review leaves the workflow incomplete. A user-accepted gap stays explicit and does not become a passing review. Report the implemented outcomes, validation, review rounds and dispositions, reviewer capability or model-selection limitation, and any unmet requirements.
