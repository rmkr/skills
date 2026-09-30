# Build level

Run `build` for software engineering or software architecture, including engineering documents and agent skills that serve that work. Determine scope from the subject, not the app or file format. For other subjects, implement through `subagent-delegation`, then run `fix`.

## Prepare

Establish the requested outcomes, checkable acceptance criteria, write authority, and artifact baseline, including protected user changes. Use authority already present in the conversation. Keep one set of task records and review findings across all phases.

Check implementation delegation alongside the reviewer preflight. If a required capability is unavailable, disclose the unmet workflow requirement; useful local work does not fulfill required delegation or independent review. Honor an explicit instruction to wait for that capability.

## Implement

Workers normally perform their own task-specific research. Use a researcher only when shared unknowns, consequential choices, or task boundaries justify it under the delegation contract.

When existing work needs an initial assessment, run one `review` round first and return its verified findings to implementation in the same records.

Assign one worker for a cohesive implementation, including a small task that explicitly invokes The Forge. Use multiple workers for independent slices. The ordinary-delegation shortcut for local work cannot skip this level's implementation worker. Apply the shared ownership and scheduling rules; validate prerequisites before dependent work starts. The orchestrator may investigate, integrate, validate, and make cohesive integration fixes within existing authority.

## Integrate and review

Collect worker results, audit actual changes against ownership and the protected baseline, integrate the combined result, and run acceptance checks. A worker's completion message is evidence for verification, not acceptance by itself.

Run the `fix` loop against the complete integrated snapshot with the original requirements and raw validation evidence. Route accepted corrections to the existing implementation owner unless ownership has been explicitly reassigned under the delegation contract.

## Finish

Finish when the `fix` loop finishes and all assigned agents have finished or are confirmed stopped. Report the implemented outcomes alongside the loop's report, including any reviewer capability or model-selection limitation.
