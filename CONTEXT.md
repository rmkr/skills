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
One of three ordered capability levels that subagent delegation assigns to every delegated agent by its role: technician, engineer, or architect. Each level is capped by the one above it.
_Avoid_: Model class, model level

**Technician**:
The lowest model tier, for mechanical work: searching and exploring, running validation, and changes already fully specified. Informally the basic, low, or light tier.

**Engineer**:
The middle model tier, for bounded, well-specified work that needs judgement, such as implementation and research. Informally the intermediate, middle, or mid tier.

**Architect**:
The highest model tier, for ambiguous, architectural, or cross-cutting work and for work that has failed at the engineer tier. Informally the advanced, high, or top tier.

**Staging branch**:
The task branch that delegated changes integrate into. Each worker worktree branches from it and merges back into it.
_Avoid_: Integration branch, base branch

**Worker worktree**:
A disposable Git worktree and branch that the orchestrator creates from the staging branch for one writer. It holds only that writer's changes and is removed after they merge, unless it has moved on since.

**Effort level**:
The reasoning depth a model applies, set per model tier and distinct from the model. Delegation settings write a tier as `model@effort`.
_Avoid_: Reasoning level, thinking budget

**Runtime**:
The coding agent that runs skills and starts subagents, such as Claude Code, Codex, or OhMyPi. Delegation settings map each model tier to a model and optional effort per runtime.
_Avoid_: Client, harness, platform

**Provider**:
The service a runtime gets models from, such as Anthropic, OpenAI, or OpenRouter. A provider is part of a model id, not a separate setting.
_Avoid_: Vendor, backend
