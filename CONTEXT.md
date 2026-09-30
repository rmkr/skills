# Skill collection

Shared language for the writing and review capabilities in this collection.

## Language

**Concise write-up**:
A brief, evidence-supported summary of existing findings for a mixed technical audience. For an issue, it explains the problem, impact, known or suspected causes, and any available next steps with their actual status.

**Adversarial review**:
An independent assessment that challenges both a work product's underlying goal and assumptions and its fulfillment of the agreed brief.

**Review finding**:
An evidence-supported issue identified by a review. A premise finding challenges the goal or assumptions; a delivery finding identifies a failure to meet the agreed brief.

**Review improvement loop**:
A cycle of independent review, main-agent verification of findings, authorized corrections, and independent re-review. The reviewer inspects; the main agent owns corrections.

**Review level**:
How far The Forge carries a review improvement loop: `review` stops at verified findings, `fix` corrects and re-reviews until clean, and `build` has workers implement before `fix` runs.

**Strict review**:
A review on a Git target by a runtime-enforced read-only reviewer against an immutable, fingerprinted bundle. It is an option on any review level.

**Model tier**:
A capability level The Forge assigns to an agent by its role: mid for bounded, well-specified work, top for ambiguous, architectural, or cross-cutting work.
_Avoid_: Model class, model level

**Runtime**:
The coding agent that runs skills and starts subagents, such as Claude Code, Codex, or OhMyPi. Forge settings map each model tier to a model id per runtime.
_Avoid_: Client, harness, platform

**Provider**:
The service a runtime gets models from, such as Anthropic, OpenAI, or OpenRouter. A provider is part of a model id, not a separate setting.
_Avoid_: Vendor, backend
