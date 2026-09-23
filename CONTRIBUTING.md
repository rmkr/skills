# Contributing

This collection helps agents plan, execute, review, and communicate across subjects. Contributions can include new skills. Austin ([@rmkr](https://github.com/rmkr)) decides scope, merges, and releases. Maintenance is best effort, without promised response times or a release schedule.

## Propose a change

Send small fixes directly as pull requests. For a new skill or a major behavior change, [open an issue](https://github.com/rmkr/skills/issues) first with the problem, intended user, and a concrete example. Wait for agreement on scope before implementing it.

A new skill needs a distinct purpose, evidence from a fresh session, and a contributor willing to address review feedback. Improve an existing skill when the use case and outcome overlap. Skills outside the collection's scope can be suggested for the [recommendations page](docs/recommendations.md); expanding the collection's scope is a separate maintainer decision.

## Develop and validate

Keep skills in `skills/`, required runtime adapters in `agents/`, and tooling in `scripts/` and `tests/`. Follow [AGENTS.md](AGENTS.md) for authoring, portability, and safety rules, [CONTEXT.md](CONTEXT.md) for shared terminology, and applicable [architecture decisions](docs/adr/). Codex is the primary runtime; see [compatibility](docs/compatibility.md) before claiming support elsewhere.

From the checkout, use [uv](https://docs.astral.sh/uv/) to run:

```bash
uv run python scripts/validate.py
uv run python -m unittest discover -s tests -v
```

Test observable behavior at existing interfaces. Add a regression test when tooling behavior changes; avoid tests coupled to exact prose or headings. For substantial instruction changes, include representative fresh-session trials, raw evidence, the runtime used, and any unverified behavior. Configuration validation alone does not prove runtime behavior or permission enforcement.

For installation changes, use a disposable project and the [documented installation route](docs/installation.md). Check a standalone skill and the integrated workflow set, preserving user-owned configuration. Documentation changes need a reader walkthrough and link checks; they do not need a new behavioral test suite.

## Review and merge

Explain the problem, resulting behavior, checks performed, and remaining limitations in the pull request. Include dependency, invocation, installation, or migration implications when relevant. Preserve existing license notices and attribution; contributions must be material you are entitled to contribute under the project's [MIT license](LICENSE).

Merges require passing validation and tooling tests plus maintainer approval. Substantial instruction changes also require independent behavioral review. Review findings need evidence; the author addresses accepted findings and reviewers check the resulting combined state. See [AGENTS.md](AGENTS.md) for the repository's independent-review requirement.

The `Validate` workflow runs on pull requests, pushes to `main`, and manual dispatch. Repository-host protection settings are separate from this file; see [release and maintenance guidance](docs/maintenance.md) for enforcement and publication checks.
