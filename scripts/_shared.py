from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallationTarget:
    name: str
    skills_path: Path
    agents_path: Path
    agent_sources: Path
    agent_suffix: str


INSTALLATION_TARGETS = {
    "codex": InstallationTarget(
        name="codex",
        skills_path=Path(".agents/skills"),
        agents_path=Path(".codex/agents"),
        agent_sources=Path("agents"),
        agent_suffix=".toml",
    ),
    "claude": InstallationTarget(
        name="claude",
        skills_path=Path(".claude/skills"),
        agents_path=Path(".claude/agents"),
        agent_sources=Path("agents/claude"),
        agent_suffix=".md",
    ),
    "omp": InstallationTarget(
        name="omp",
        skills_path=Path(".omp/agent/skills"),
        agents_path=Path(".omp/agent/agents"),
        agent_sources=Path("agents/omp"),
        agent_suffix=".md",
    ),
}
TARGET_ALIASES = {"ohmypi": "omp"}
SKILL_AGENT_DEPENDENCIES = {
    "diff-skeptic": {
        "codex": ("diff_skeptic_reviewer",),
        "claude": ("diff-skeptic-reviewer",),
        "omp": ("diff-skeptic-reviewer",),
    },
}


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def installation_target(name: str) -> InstallationTarget:
    canonical_name = TARGET_ALIASES.get(name, name)
    try:
        return INSTALLATION_TARGETS[canonical_name]
    except KeyError as error:
        choices = ", ".join((*INSTALLATION_TARGETS, *TARGET_ALIASES))
        raise ValueError(f"unknown target {name!r}; available: {choices}, all") from error


def resolve_targets(requested: list[str] | None) -> tuple[str, ...]:
    if not requested:
        return ("codex",)
    if "all" in requested:
        if len(requested) != 1:
            raise ValueError("target 'all' cannot be combined with another target")
        return tuple(INSTALLATION_TARGETS)

    resolved = [TARGET_ALIASES.get(name, name) for name in requested]
    for name in resolved:
        installation_target(name)
    return tuple(dict.fromkeys(resolved))


def default_skills_dir(target: str = "codex") -> Path:
    return Path.home() / installation_target(target).skills_path


def default_agents_dir(target: str = "codex") -> Path:
    return Path.home() / installation_target(target).agents_path


def discover_skills(repo_root: Path, *, allow_empty: bool = False) -> dict[str, Path]:
    skills_root = repo_root.resolve() / "skills"
    if not skills_root.exists():
        if allow_empty:
            return {}
        raise ValueError(f"skills directory does not exist: {skills_root}")
    if not skills_root.is_dir():
        raise ValueError(f"skills path is not a directory: {skills_root}")

    hidden_skills = sorted(
        entry
        for entry in skills_root.iterdir()
        if entry.name.startswith(".")
        and entry.is_dir()
        and (entry / "SKILL.md").is_file()
    )
    if hidden_skills:
        names = ", ".join(entry.name for entry in hidden_skills)
        raise ValueError(f"hidden skill directories are not allowed: {names}")

    skills = {
        entry.name: entry.resolve()
        for entry in skills_root.iterdir()
        if not entry.name.startswith(".")
        and entry.is_dir()
        and (entry / "SKILL.md").is_file()
    }
    if not skills and not allow_empty:
        raise ValueError(f"no skills found under: {skills_root}")
    return dict(sorted(skills.items()))


def select_skills(
    available: dict[str, Path], requested: list[str] | None
) -> dict[str, Path]:
    if not requested:
        return available

    unknown = sorted(set(requested) - available.keys())
    if unknown:
        choices = ", ".join(available)
        missing = ", ".join(unknown)
        raise ValueError(f"unknown skill(s): {missing}; available: {choices}")

    return {name: available[name] for name in dict.fromkeys(requested)}


def discover_custom_agents(
    repo_root: Path, *, target: str = "codex", allow_empty: bool = False
) -> dict[str, Path]:
    target_config = installation_target(target)
    agents_root = repo_root.resolve() / target_config.agent_sources
    if not agents_root.exists():
        if allow_empty:
            return {}
        raise ValueError(f"agents directory does not exist: {agents_root}")
    if not agents_root.is_dir():
        raise ValueError(f"agents path is not a directory: {agents_root}")

    entries = sorted(agents_root.iterdir())
    if target_config.name == "codex":
        platform_directories = {
            config.agent_sources.name
            for config in INSTALLATION_TARGETS.values()
            if config.agent_sources.parent == Path("agents")
        }
        entries = [
            entry
            for entry in entries
            if not (entry.is_dir() and entry.name in platform_directories)
        ]
    hidden_agents = [entry for entry in entries if entry.name.startswith(".")]
    if hidden_agents:
        names = ", ".join(entry.name for entry in hidden_agents)
        raise ValueError(f"hidden custom agent definitions are not allowed: {names}")

    invalid_agents = [
        entry
        for entry in entries
        if not entry.is_file() or entry.suffix != target_config.agent_suffix
    ]
    if invalid_agents:
        names = ", ".join(entry.name for entry in invalid_agents)
        raise ValueError(
            f"{target_config.name} custom agents must be standalone "
            f"{target_config.agent_suffix} files: {names}"
        )

    agents = {entry.stem: entry.resolve() for entry in entries}
    if not agents and not allow_empty:
        raise ValueError(f"no custom agents found under: {agents_root}")
    return agents


def agents_for_skills(
    selected_skills: dict[str, Path],
    available_agents: dict[str, Path],
    *,
    target: str = "codex",
) -> dict[str, Path]:
    canonical_target = installation_target(target).name
    required = {
        agent_name
        for skill_name in selected_skills
        for agent_name in SKILL_AGENT_DEPENDENCIES.get(skill_name, {}).get(
            canonical_target, ()
        )
    }
    missing = sorted(required - available_agents.keys())
    if missing:
        raise ValueError(
            "missing custom agent dependency or dependencies: " + ", ".join(missing)
        )
    return {name: available_agents[name] for name in sorted(required)}


def points_to(destination: Path, source: Path) -> bool:
    return (
        destination.is_symlink()
        and destination.resolve(strict=False) == source.resolve()
    )


def managed_skill_links(repo_root: Path, skills_dir: Path) -> dict[str, Path]:
    """Return immediate user-skill links with targets directly under repo skills."""
    if not skills_dir.is_dir():
        return {}

    skills_root = (repo_root.resolve() / "skills").resolve()
    managed: dict[str, Path] = {}
    for destination in skills_dir.iterdir():
        if not destination.is_symlink():
            continue
        try:
            target = Path(os.readlink(destination))
            if target.name == "..":
                continue
            if not target.is_absolute():
                target = destination.parent / target
            # Resolve aliases and '..' together, retaining a possibly missing leaf.
            target_parent = target.parent.resolve()
        except (OSError, RuntimeError):
            # Ownership is unproven if the target cannot be resolved.
            continue
        if target_parent == skills_root:
            managed[destination.name] = destination
    return dict(sorted(managed.items()))


def managed_custom_agent_links(
    repo_root: Path, agents_dir: Path, *, target: str = "codex"
) -> dict[str, Path]:
    """Return immediate user-agent links whose targets are repo agent definitions."""
    if not agents_dir.is_dir():
        return {}

    target_config = installation_target(target)
    agents_root = (repo_root.resolve() / target_config.agent_sources).resolve()
    managed: dict[str, Path] = {}
    for destination in agents_dir.iterdir():
        if (
            not destination.is_symlink()
            or destination.suffix != target_config.agent_suffix
        ):
            continue
        try:
            target = Path(os.readlink(destination))
            if target.name == "..":
                continue
            if not target.is_absolute():
                target = destination.parent / target
            target_parent = target.parent.resolve()
        except (OSError, RuntimeError):
            continue
        if target_parent == agents_root:
            managed[destination.stem] = destination
    return dict(sorted(managed.items()))
