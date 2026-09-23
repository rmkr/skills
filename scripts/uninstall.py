#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _shared import (
    SKILL_AGENT_DEPENDENCIES,
    default_agents_dir,
    default_repo_root,
    default_skills_dir,
    discover_custom_agents,
    discover_skills,
    managed_custom_agent_links,
    managed_skill_links,
    points_to,
    resolve_targets,
)


def remove_links_atomically(
    planned: list[Path],
) -> tuple[OSError | None, list[str]]:
    removed: list[tuple[Path, str]] = []
    try:
        for destination in planned:
            target = os.readlink(destination)
            destination.unlink()
            removed.append((destination, target))
    except OSError as error:
        rollback_errors: list[str] = []
        for destination, target in reversed(removed):
            try:
                if destination.exists() or destination.is_symlink():
                    rollback_errors.append(
                        f"{destination} changed before rollback and was preserved"
                    )
                else:
                    destination.symlink_to(
                        target,
                        target_is_directory=not destination.suffix,
                    )
            except OSError as rollback_error:
                rollback_errors.append(f"{destination}: {rollback_error}")
        return error, rollback_errors
    return None, []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Remove only user-level skill and custom-agent symlinks managed by "
            "this repository."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--target",
        action="append",
        dest="targets",
        choices=("codex", "claude", "omp", "ohmypi", "all"),
        help=(
            "Installation target; repeat for multiple targets or use 'all' "
            "(default: codex). 'ohmypi' is an alias for 'omp'."
        ),
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="Override the user skills directory for a single target.",
    )
    parser.add_argument(
        "--agents-dir",
        type=Path,
        help="Override the user custom-agent directory for a single target.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        dest="skills",
        help="Uninstall only this skill; repeat to select more than one.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without writing them.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        targets = resolve_targets(args.targets)
        if len(targets) > 1 and (args.skills_dir or args.agents_dir):
            raise ValueError(
                "--skills-dir and --agents-dir can be used only with one target"
            )
        available_skills = discover_skills(args.repo_root, allow_empty=True)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    target_state: dict[
        str, tuple[Path, Path, dict[str, Path], dict[str, Path], dict[str, Path]]
    ] = {}
    managed_skill_names = set(available_skills)
    try:
        for target in targets:
            skills_dir = (
                args.skills_dir
                if args.skills_dir is not None
                else default_skills_dir(target)
            ).expanduser().resolve()
            agents_dir = (
                args.agents_dir
                if args.agents_dir is not None
                else default_agents_dir(target)
            ).expanduser().resolve()
            available_agents = discover_custom_agents(
                args.repo_root, target=target, allow_empty=True
            )
            managed_skills = managed_skill_links(args.repo_root, skills_dir)
            managed_agents = managed_custom_agent_links(
                args.repo_root, agents_dir, target=target
            )
            managed_skill_names.update(managed_skills)
            target_state[target] = (
                skills_dir,
                agents_dir,
                available_agents,
                managed_skills,
                managed_agents,
            )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.skills:
        unknown = sorted(set(args.skills) - managed_skill_names)
        if unknown:
            print(
                f"error: unknown skill(s): {', '.join(unknown)}; available: "
                f"{', '.join(sorted(managed_skill_names))}",
                file=sys.stderr,
            )
            return 2
        selected_skill_names = list(dict.fromkeys(args.skills))
    else:
        selected_skill_names = sorted(managed_skill_names)

    planned: list[Path] = []
    conflicts: list[str] = []

    def preflight(
        name: str,
        destination: Path,
        source: Path | None,
        managed_links: dict[str, Path],
    ) -> None:
        if not destination.exists() and not destination.is_symlink():
            print(f"not installed: {destination}")
        elif name in managed_links or (
            source is not None and points_to(destination, source)
        ):
            planned.append(destination)
        elif destination.is_symlink():
            conflicts.append(
                f"{destination} is a symlink to {destination.resolve(strict=False)}, "
                f"not {source}"
            )
        else:
            conflicts.append(
                f"{destination} exists but is not managed by this repository"
            )

    for target, state in target_state.items():
        skills_dir, agents_dir, available_agents, managed_skills, managed_agents = state
        if args.skills:
            selected_agent_names = sorted(
                {
                    agent_name
                    for skill_name in selected_skill_names
                    for agent_name in SKILL_AGENT_DEPENDENCIES.get(skill_name, {}).get(
                        target, ()
                    )
                }
            )
        else:
            selected_agent_names = sorted(set(available_agents) | set(managed_agents))

        for name in selected_skill_names:
            preflight(
                name,
                skills_dir / name,
                available_skills.get(name),
                managed_skills,
            )
        for name in selected_agent_names:
            source = available_agents.get(name)
            destination_name = source.name if source is not None else (
                managed_agents[name].name
            )
            preflight(
                name,
                agents_dir / destination_name,
                source,
                managed_agents,
            )

    if conflicts:
        for conflict in conflicts:
            print(f"error: {conflict}", file=sys.stderr)
        print("no changes made", file=sys.stderr)
        return 1

    if args.dry_run:
        for destination in planned:
            print(f"would uninstall: {destination}")
        return 0

    error, rollback_errors = remove_links_atomically(planned)
    if error is not None:
        print(f"error: uninstallation failed: {error}", file=sys.stderr)
        for rollback_error in rollback_errors:
            print(f"error: rollback incomplete: {rollback_error}", file=sys.stderr)
        if not rollback_errors:
            print("uninstallation rolled back; all links restored", file=sys.stderr)
        return 1

    for destination in planned:
        print(f"uninstalled: {destination}")

    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
