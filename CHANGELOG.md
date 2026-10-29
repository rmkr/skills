# Changelog

This log starts at version 0.3.0. Earlier changes are in the Git history.

## 0.3.3 (unreleased)

### Changed

- Rename The Forge to `forge` in skill titles, Codex display metadata, current documentation, and validation. Keep `$forge` and `/forge` as the commands.

## 0.3.2 (unreleased)

### Changed

- Let Setup rmkr skills save The Forge's round limit globally or per repository; resolve explicit run choices before saved preferences.
- Limit The Forge's review loops to a shared round budget, with incomplete work reported at the limit.
- Focus later reviews on fixes and affected behavior, group repeated findings, and keep optional suggestions from extending the loop.
- Load applicable baseline `REVIEW.md` rules explicitly and preserve the agreed review scope.

### Added

- Reusable review-loop replay cases and a grading guide for native agent behavior trials.

## 0.3.1 (unreleased)

### Changed

- Suggest the latest Terra at high effort for Codex's Apprentice tier, followed by the latest Sol at medium, high, and xhigh effort for Technician, Engineer, and Architect, based on Artificial Analysis results.
- Use the skills CLI directly for installation and removal.
- Use matching quick-install tables in the README and installation guide, with `npx` and `bunx` commands, interactive skill and agent selection, and Symlink as the default installation choice.
- Keep the installation guide focused on this collection's setup and link to the skills CLI documentation for other commands.

### Removed

- The Python install picker, its `preferred-skills.json` settings file, and its tests.
- The legacy Python uninstall helper, its unused support code, and its tests.
- The `questionary` package and its unused dependencies.

## 0.3.0 (2026-10-26, untagged)

### Added

- Shared test cases and a fresh-session guide for checking review findings.

### Changed

- Group review findings by model tier and shared source context for verification.
- Move delegation's tier override rules and worker worktree steps into separate reference files.

### Removed

- The Forge's Claude Code `workflow` option, its script, reference, and tests. Use `/forge review`, `/forge fix`, or `/forge build` directly.
