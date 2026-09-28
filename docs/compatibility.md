# Compatibility

Codex is the primary runtime. Keep the shared skill instructions portable where practical; Claude Code and OhMyPi support is best effort. A supplied adapter or passing repository check does not establish that a workflow works in every client version.

## Runtime expectations

| Runtime | Invocation | Support and evidence |
| --- | --- | --- |
| Codex | `$skill-name` | Primary target. The repository includes OpenAI invocation metadata and a strict reviewer definition for The Forge. Runtime discovery, delegation, and effective permissions still need verification in the installed client. |
| Claude Code | `/skill-name` | Best effort. A separate strict reviewer adapter is included; repository validation checks its configuration. No current release-wide live-runtime qualification is claimed. |
| OhMyPi | `/skill:skill-name` | Best effort; skill commands must be enabled. Historical OMP 17.2.9 checks covered reviewer discovery and its tool surface, not attempted-write rejection or the current collection's full behavior. |

The [installation guide](installation.md) lists the matching reviewer files and default destinations. Relocated runtime profiles may use different directories.

## Invocation and dependencies

Concise Write-up requires explicit invocation. Its entrypoint declares `disable-model-invocation: true`; OpenAI metadata also declares `allow_implicit_invocation: false`. These are client-specific policies, not universal Agent Skills guarantees. Other skills permit automatic selection when relevant.

Clients that do not enforce an explicit-invocation policy cannot satisfy that requirement merely by loading the Markdown. Historical OhMyPi behavior hides explicit-only skills from the model's catalog but still permits direct skill-path access; do not treat that as the same hard restriction. Strict Agent Skills consumers may reject the extension. Removing it changes behavior and is not a supported workaround for preserving explicit-only use.

The Forge requires Subagent Delegation. Both declare orchestration contract version `1`; install compatible copies together and make them discoverable through the runtime's skill catalog. Missing or incompatible dependencies leave the integrated workflow unavailable.

## Reviewer boundaries

Subagent Delegation and The Forge use the active runtime's native subagent facility. Ordinary review needs an inspection-only assignment; stronger isolation applies when the task requires it. A missing native reviewer must be reported, not replaced with a claim that local inspection was independent review.

The Forge's `strict` mode additionally requires its matching custom reviewer and verified runtime enforcement against filesystem writes, external mutations, and further delegation. A read-only filesystem alone does not constrain connected services. Profile declarations, tool allowlists, and copied configuration are inputs to that verification, not proof of the effective boundary. If enforcement cannot be confirmed, the strict review remains incomplete.

## What checks establish

Repository validation and tooling tests check file structure, invocation metadata, dependency contracts, reviewer configuration, and maintenance-tool behavior. They do not prove discovery, activation, model behavior, or permission enforcement in a live runtime.

Compatibility claims for a release should name the client version, collection revision, environment, and exercised behavior: skill discovery and invocation, companion resolution, native delegation, and reviewer controls where relevant. Record missing coverage explicitly. Substantial instruction changes also require representative fresh-session trials and independent behavioral review, as described in [contributing](../CONTRIBUTING.md).

The [platform research note](archive/platform-compatibility-research.md) records investigation from August 2026. It is historical evidence, not a current support matrix; its inventory and installation recommendations may predate the present collection. For optional worktree setup, see [GitButler configuration](agents/gitbutler.md).

## Installation check, 2026-09-16

On macOS, skills CLI 1.5.26 installed Unslop, the three-skill integrated workflow set, and Diff Skeptic into a disposable project. A local Git fixture exercised the documented GitHub tree/tag URL while its default branch deliberately contained different content. Installed skill files matched the tagged source, the project lock recorded the tag, and the copied Codex reviewer matched its source. Removing Unslop across managed agents preserved the other skills and reviewer.

This checked project-scope installation and removal, not global installation or live runtime enforcement. No public collection release exists yet; installation from an actual published release tag remains a release-time check. Codex-only removal retained the shared skill directory when another detected agent could use it, as noted in the installation guide.
