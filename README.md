# rmkr-skills

My agent skills for planning, execution, review, and communication across subjects. Built for experienced agent users, with Codex as the primary runtime and best-effort support elsewhere.

## Choose a skill

| Skill | Use it when | Required companions | Invocation |
| --- | --- | --- | --- |
| [Subagent Delegation](skills/subagent-delegation/SKILL.md) | Parts of a task benefit from separate agents, with one main agent coordinating the results. No formal plan or implementation worker is required. | None | Automatic or explicit |
| [Adversarial Review Loop](skills/adversarial-review-loop/SKILL.md) | Existing work needs independent scrutiny of its assumptions and delivery, across software, research, plans, documents, and other subjects. Authorized improvements include fixes and re-review. | Subagent Delegation | Automatic or explicit |
| [The Forge](skills/forge-review-loop/SKILL.md) | Software engineering or architecture work needs delegated implementation and mandatory independent review. | Subagent Delegation and Adversarial Review Loop | Explicit only |
| [Diff Skeptic](skills/diff-skeptic/SKILL.md) | A fixed Git diff needs one isolated adversarial review with verified findings. | Matching runtime reviewer configuration | Explicit only |
| [Unslop](skills/unslop/SKILL.md) | Prose needs formulaic phrasing removed while preserving meaning and evidence. | None | Automatic or explicit |
| [Triage Investigate](skills/triage-investigate/SKILL.md) | A reported bug needs investigation using logs and source, with an evidence-backed HTML report and Markdown handoff. | uv and Python 3.11+ for rendering | Automatic or explicit |
| [Concise Write-up](skills/concise-writeup/SKILL.md) | Existing findings need a concise summary with evidence and known next steps. | None | Explicit only |

A review request does not authorize edits. Reviewers inspect; the main agent verifies findings and owns any separately authorized corrections. Diff Skeptic requires runtime-enforced read-only and no-delegation controls. Routine independent review uses ordinary native subagents with inspection-only assignments.

## Install

Use [Bun](https://bun.sh) and the [skills CLI](https://github.com/vercel-labs/skills). This installs one standalone skill from the development branch:

```bash
bunx skills@latest add rmkr/skills --global --agent codex --skill unslop
```

Tagged collection releases are the stable channel; the default branch is development. No release tag is published yet. See [installation](docs/installation.md) for selecting a release, installing companion skills, configuring Diff Skeptic, updates, and removal. Use `npx` instead of `bunx` if you prefer npm.

In Codex, invoke a skill with `$skill-name`, for example `$unslop`. See [compatibility](docs/compatibility.md) for other runtimes, invocation policies, and verification limits.

## Contribute and maintain

Contributions are welcome, including new skills within the collection's scope. Small fixes can go straight to a pull request; discuss new skills and major behavior changes in an issue first. The [contribution guide](CONTRIBUTING.md) explains acceptance criteria, checks, review, and collection-wide releases. The maintainer retains scope, merge, and release decisions. Maintenance is best effort, without promised response times or a release schedule.

## Recommendations and license

[Personal recommendations](docs/recommendations.md) cover third-party skills, plugins, MCPs, and the optional installation picker. Those projects retain their own maintainers and support channels.

Project-authored material is available under the [MIT license](LICENSE). Existing third-party license notices and attribution remain applicable to their material.
