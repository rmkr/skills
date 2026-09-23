---
status: accepted
---

# Extend adversarial review beyond software

The previous review workflow excluded non-engineering work. The design interview on 2026-09-14 settled a broader subject scope, including plans and research, and review of both underlying goals and assumptions and fulfillment of the agreed brief. Retain the improvement loop: the independent reviewer inspects, and the main agent verifies findings and owns authorized corrections before re-review.

Subject-specific workflows alone do not provide the requested shared adversarial improvement loop. Broader coverage requires a way to judge each task against appropriate evidence and criteria; software checks cannot establish the quality of every work product.

## Settled design

- Extend the existing adversarial-review-loop skill, retaining automatic selection for substantial review or improvement tasks across subjects. Small edits receive proportionate handling. The Forge retains its separate engineering scope.
- Ground findings in the brief, evidence, constraints, or concrete audience needs. Unsupported taste preferences are optional and do not block completion.
- The main agent derives and states review criteria and assumptions from the task and available domain skills. Ask when a missing decision would materially change the result. The reviewer may challenge the criteria with evidence.
- Finish when accepted fixes are verified and no material finding remains unresolved. Diagnose repeated findings or stalled rounds, and return decisions to the user when progress requires them. Honor user budgets without imposing an arbitrary round limit.
- Review accessible evidence and identify coverage gaps. Leave material checks unresolved when the required evidence or tools are unavailable; request access or an export only when needed to proceed.
- Correct factual errors within the agreed task. Bring proposed changes to the user's goal or intended position back to the user with evidence.
- Use existing domain skills and task requirements for validation: source verification for research, recalculation for spreadsheets, and rendered inspection for documents or slides. Add specialist reviewers when distinct expertise is needed.

## Workflow

Establish the target, brief, criteria, assumptions, and available evidence. Have an independent reviewer assess a stable state for premise and delivery findings. The main agent verifies and dispositions findings, makes authorized corrections, and performs artifact-appropriate checks. Re-review the combined result until the stopping conditions above are met, or report the unresolved decision or coverage gap.

Retain the existing native-subagent coordination contract, inspection-only reviewer assignment, stable snapshot checks, and review-only behavior. A request solely for review ends with verified findings; improvement requests include corrections and re-review.

## Implementation boundary

The change belongs in the existing review skill, its invocation metadata, and README routing. The shared delegation contract already supports non-software work. Keep domain procedures in the relevant existing skills.

The user confirmed the combined design by requesting implementation on 2026-09-14. Implementation should include fresh-context trials of research, planning, and rendered or calculated artifacts, plus an engineering regression case. Include an unavailable-evidence case and a preference-only suggestion to check the agreed boundaries.
