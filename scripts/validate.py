#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml
from _shared import (
    INSTALLATION_TARGETS,
    agents_for_skills,
    default_repo_root,
    discover_custom_agents,
    discover_skills,
)

SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
AGENT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_SKILL_FIELDS = {"name", "description"}
SUPPORTED_SKILL_FIELDS = REQUIRED_SKILL_FIELDS | {
    "allowed-tools",
    "argument-hint",
    "compatibility",
    "disable-model-invocation",
    "license",
    "metadata",
}
REQUIRED_INTERFACE_FIELDS = {
    "display_name",
    "short_description",
    "default_prompt",
}
REQUIRED_AGENT_FIELDS = {"name", "description", "developer_instructions"}
SKILL_CONTRACTS = {
    "subagent-delegation": {
        "allow_implicit_invocation": True,
        "disable_model_invocation": False,
        "skill_dependencies": (),
        "orchestration_contract": "1",
    },
    "forge": {
        "display_name": "The Forge",
        "allow_implicit_invocation": True,
        "disable_model_invocation": False,
        "skill_dependencies": ("subagent-delegation",),
        "orchestration_contract": "1",
    },
    "unslop": {
        "display_name": "Unslop",
        "allow_implicit_invocation": True,
        "disable_model_invocation": False,
    },
}
CUSTOM_AGENT_CONTRACTS = {
    "inspector": {
        "sandbox_mode": "read-only",
        "portable_model": True,
        "agents_enabled": False,
    },
    "forge_strict_reviewer": {
        "sandbox_mode": "read-only",
        "portable_model": True,
        "agents_enabled": False,
    },
}
MARKDOWN_AGENT_CONTRACTS = {
    "claude": {
        "forge-strict-reviewer": {
            "tools": {"Read", "Grep", "Glob"},
            "disallowed_tools": {"Agent"},
            "permission_mode": "plan",
        },
    },
    "omp": {
        "forge-strict-reviewer": {
            "tools": {"read", "grep", "glob"},
        },
    },
}
NON_FILE_URI = re.compile(
    r"\b(?!file:)(?![A-Za-z]:\\)(?![A-Za-z]:/(?!/))[A-Za-z][A-Za-z0-9+.-]*:[^\s'\"<>]*",
    re.IGNORECASE,
)
FILE_URL_LOCAL_PATH = re.compile(
    r"file:(?://(?:localhost)?/|/)[^\s'\"<>]+", re.IGNORECASE
)
SCAFFOLD_PLACEHOLDER = re.compile(r"\[TODO:\s*[^\]]+\]", re.IGNORECASE)


def contains_scaffold_placeholder(value: str) -> bool:
    """Find standalone scaffold directives, leaving Markdown examples alone."""
    fence_character = ""
    fence_length = 0
    for line in value.splitlines():
        # Blockquotes and indented code are examples, not unfinished instructions.
        if line.startswith(("    ", "\t")) or line.lstrip().startswith(">"):
            continue
        stripped = line.strip()
        if not fence_character:
            stripped = re.sub(r"^(?:[-+*]|\d+[.)])\s+", "", stripped)
        fence = re.match(r"(`{3,}|~{3,})(.*)$", stripped)
        if fence_character:
            if (
                fence
                and fence[1][0] == fence_character
                and len(fence[1]) >= fence_length
                and not fence[2].strip()
            ):
                fence_character = ""
            continue
        if fence:
            fence_character = fence[1][0]
            fence_length = len(fence[1])
            continue
        if SCAFFOLD_PLACEHOLDER.fullmatch(stripped):
            return True
    return False


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_frontmatter_document(
    path: Path, document_name: str
) -> tuple[dict[str, Any] | None, str, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0] != "---":
        return None, "", [f"{path}: {document_name} must start with YAML frontmatter"]

    try:
        closing = lines.index("---", 1)
    except ValueError:
        return None, "", [f"{path}: YAML frontmatter is not closed"]

    raw_frontmatter = "\n".join(lines[1:closing])
    body = "\n".join(lines[closing + 1 :]).strip()
    try:
        frontmatter = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as error:
        return None, body, [f"{path}: invalid YAML frontmatter: {error}"]

    if not isinstance(frontmatter, dict):
        errors.append(f"{path}: YAML frontmatter must be a mapping")
        return None, body, errors

    return frontmatter, body, errors


def load_skill(path: Path) -> tuple[dict[str, Any] | None, str, list[str]]:
    return load_frontmatter_document(path, "SKILL.md")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    frontmatter, body, load_errors = load_skill(skill_file)
    errors.extend(load_errors)
    if frontmatter is None:
        return errors

    fields = set(frontmatter)
    missing = REQUIRED_SKILL_FIELDS - fields
    extra = fields - SUPPORTED_SKILL_FIELDS
    if missing:
        errors.append(
            f"{skill_file}: missing frontmatter field(s): {', '.join(sorted(missing))}"
        )
    if extra:
        errors.append(
            f"{skill_file}: unsupported frontmatter field(s): {', '.join(sorted(extra))}"
        )

    name = frontmatter.get("name")
    if not nonempty_string(name):
        errors.append(f"{skill_file}: name must be a non-empty string")
    else:
        if len(name) > 64 or not SKILL_NAME.fullmatch(name):
            errors.append(
                f"{skill_file}: name must be at most 64 lowercase letters, digits, "
                "or hyphen-separated segments"
            )
        if skill_dir.name != name:
            errors.append(
                f"{skill_file}: folder name {skill_dir.name!r} must match skill name {name!r}"
            )

    if not nonempty_string(frontmatter.get("description")):
        errors.append(f"{skill_file}: description must be a non-empty string")
    elif len(frontmatter["description"]) > 1024:
        errors.append(f"{skill_file}: description must be at most 1024 characters")
    if nonempty_string(frontmatter.get("description")) and contains_scaffold_placeholder(
        frontmatter["description"]
    ):
        errors.append(
            f"{skill_file}: description contains an unfinished scaffold placeholder"
        )

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None and (
        not nonempty_string(compatibility) or len(compatibility) > 500
    ):
        errors.append(
            f"{skill_file}: compatibility must be a non-empty string of at most 500 characters"
        )

    license_value = frontmatter.get("license")
    if license_value is not None and not nonempty_string(license_value):
        errors.append(f"{skill_file}: license must be a non-empty string")

    metadata = frontmatter.get("metadata")
    if metadata is not None and (
        not isinstance(metadata, dict)
        or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in metadata.items()
        )
    ):
        errors.append(f"{skill_file}: metadata must map strings to strings")

    contract = SKILL_CONTRACTS.get(str(name))
    if contract is not None and "orchestration_contract" in contract:
        expected_marker = contract["orchestration_contract"]
        if (
            not isinstance(metadata, dict)
            or metadata.get("orchestration-contract") != expected_marker
        ):
            errors.append(
                f"{skill_file}: metadata.orchestration-contract must be "
                f"the string {expected_marker!r}"
            )

    allowed_tools = frontmatter.get("allowed-tools")
    if allowed_tools is not None and not nonempty_string(allowed_tools):
        errors.append(f"{skill_file}: allowed-tools must be a non-empty string")

    argument_hint = frontmatter.get("argument-hint")
    if argument_hint is not None and not nonempty_string(argument_hint):
        errors.append(f"{skill_file}: argument-hint must be a non-empty string")

    disable_model_invocation = frontmatter.get("disable-model-invocation", False)
    if not isinstance(disable_model_invocation, bool):
        errors.append(
            f"{skill_file}: disable-model-invocation must be a boolean"
        )

    if contract is not None and (
        disable_model_invocation is not contract["disable_model_invocation"]
    ):
        errors.append(
            f"{skill_file}: {name} disable-model-invocation must be "
            f"{str(contract['disable_model_invocation']).lower()}"
        )

    if not body:
        errors.append(f"{skill_file}: instruction body must not be empty")
    elif len(body.splitlines()) > 500:
        errors.append(f"{skill_file}: instruction body exceeds 500 lines")
    if contains_scaffold_placeholder(body):
        errors.append(
            f"{skill_file}: instruction body contains an unfinished scaffold placeholder"
        )

    metadata_file = skill_dir / "agents" / "openai.yaml"
    if not metadata_file.is_file():
        errors.append(f"{metadata_file}: metadata file is required")
    else:
        errors.extend(
            validate_openai_metadata(
                metadata_file,
                str(name or ""),
                disable_model_invocation=(
                    disable_model_invocation
                    if isinstance(disable_model_invocation, bool)
                    else None
                ),
            )
        )

    return errors


def validate_openai_metadata(
    path: Path,
    skill_name: str,
    *,
    disable_model_invocation: bool | None,
) -> list[str]:
    errors: list[str] = []
    try:
        metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(metadata, dict):
        return [f"{path}: metadata must be a mapping"]

    interface = metadata.get("interface")
    if not isinstance(interface, dict):
        return [f"{path}: interface must be a mapping"]

    missing = REQUIRED_INTERFACE_FIELDS - set(interface)
    if missing:
        errors.append(
            f"{path}: missing interface field(s): {', '.join(sorted(missing))}"
        )

    for field in REQUIRED_INTERFACE_FIELDS:
        if field in interface and not nonempty_string(interface[field]):
            errors.append(f"{path}: interface.{field} must be a non-empty string")

    short_description = interface.get("short_description")
    if nonempty_string(short_description) and not 25 <= len(short_description) <= 64:
        errors.append(
            f"{path}: interface.short_description must be 25 to 64 characters"
        )

    default_prompt = interface.get("default_prompt")
    if nonempty_string(default_prompt) and ("$" + skill_name) not in default_prompt:
        errors.append(f"{path}: interface.default_prompt must mention $" + skill_name)

    policy = metadata.get("policy")
    if not isinstance(policy, dict):
        errors.append(f"{path}: policy must be a mapping")
    elif "allow_implicit_invocation" not in policy:
        errors.append(f"{path}: policy.allow_implicit_invocation is required")
    elif not isinstance(policy["allow_implicit_invocation"], bool):
        errors.append(f"{path}: policy.allow_implicit_invocation must be a boolean")
    elif disable_model_invocation is not None and (
        policy["allow_implicit_invocation"] is disable_model_invocation
    ):
        expected = str(not disable_model_invocation).lower()
        errors.append(
            f"{path}: policy.allow_implicit_invocation must be {expected} to match "
            "SKILL.md disable-model-invocation"
        )

    contract = SKILL_CONTRACTS.get(skill_name)
    if contract is not None:
        expected_display_name = contract.get("display_name")
        if (
            expected_display_name is not None
            and interface.get("display_name") != expected_display_name
        ):
            errors.append(
                f"{path}: {skill_name} interface.display_name must be "
                f"{expected_display_name!r}"
            )
        implicit_invocation = (
            policy.get("allow_implicit_invocation")
            if isinstance(policy, dict)
            else None
        )
        expected_implicit_invocation = contract["allow_implicit_invocation"]
        if implicit_invocation is not expected_implicit_invocation:
            errors.append(
                f"{path}: {skill_name} policy.allow_implicit_invocation must be "
                f"{str(expected_implicit_invocation).lower()}"
            )

    return errors


def contains_absolute_local_path(value: str) -> bool:
    """Detect filesystem paths in free-form text without mistaking URLs for paths."""
    if FILE_URL_LOCAL_PATH.search(value):
        return True

    without_uris = NON_FILE_URI.sub(lambda match: " " * len(match.group()), value)
    return bool(
        re.search(r"(?<![A-Za-z0-9_.:/-])/(?:[^\s'\"]*)", without_uris)
        or re.search(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]", without_uris)
        or re.search(r"(?<![A-Za-z0-9])\\\\[^\\/\s]+[\\/][^\s]+", without_uris)
    )


def absolute_path_fields(value: Any, location: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else str(key)
            errors.extend(absolute_path_fields(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(absolute_path_fields(child, f"{location}[{index}]"))
    elif isinstance(value, str) and contains_absolute_local_path(value):
        errors.append(location)
    return errors


def validate_custom_agent(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return [f"{path}: invalid TOML: {error}"]

    missing = REQUIRED_AGENT_FIELDS - set(config)
    if missing:
        errors.append(f"{path}: missing field(s): {', '.join(sorted(missing))}")

    for field in REQUIRED_AGENT_FIELDS:
        if field in config and not nonempty_string(config[field]):
            errors.append(f"{path}: {field} must be a non-empty string")

    name = config.get("name")
    if nonempty_string(name):
        if not AGENT_NAME.fullmatch(name):
            errors.append(
                f"{path}: agent name must use lowercase letters, digits, and underscores"
            )
        if path.stem != name:
            errors.append(
                f"{path}: filename stem {path.stem!r} must match agent name {name!r}"
            )

    for field in absolute_path_fields(config):
        errors.append(f"{path}: {field} must not contain an absolute local path")

    if name == "inspector":
        if config.get("approval_policy") != "never":
            errors.append(f"{path}: inspector approval_policy must be never")
        apps = config.get("apps", {})
        defaults = apps.get("_default", {}) if isinstance(apps, dict) else {}
        if not isinstance(defaults, dict) or defaults.get("enabled") is not False:
            errors.append(f"{path}: inspector apps._default.enabled must be false")

    contract = CUSTOM_AGENT_CONTRACTS.get(str(name))
    if contract is not None:
        expected_sandbox = contract["sandbox_mode"]
        if config.get("sandbox_mode") != expected_sandbox:
            errors.append(f"{path}: sandbox_mode must be {expected_sandbox!r}")
        if contract["portable_model"]:
            for field in ("model", "model_reasoning_effort"):
                if field in config:
                    errors.append(
                        f"{path}: {field} must be omitted for runtime model selection"
                    )
        agents_config = config.get("agents")
        actual_agents_enabled = (
            agents_config.get("enabled") if isinstance(agents_config, dict) else None
        )
        if actual_agents_enabled is not contract["agents_enabled"]:
            errors.append(f"{path}: agents.enabled must be false")

    return errors


def normalize_string_list(value: Any) -> list[str] | None:
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list) and all(nonempty_string(item) for item in value):
        return value
    return None


def validate_markdown_agent(path: Path, target: str) -> list[str]:
    errors: list[str] = []
    frontmatter, body, load_errors = load_frontmatter_document(
        path, f"{target} agent definition"
    )
    errors.extend(load_errors)
    if frontmatter is None:
        return errors

    required_fields = {"name", "description", "tools"}
    supported_fields = required_fields | {"model"}
    if target == "claude":
        required_fields |= {"disallowedTools", "permissionMode"}
        supported_fields |= {
            "disallowedTools",
            "permissionMode",
        }
    elif target == "omp":
        supported_fields |= {
            "advisor",
            "autoloadSkills",
            "blocking",
            "output",
            "prewalk",
            "read-summarize",
            "spawns",
            "thinking-level",
        }

    missing = required_fields - set(frontmatter)
    extra = set(frontmatter) - supported_fields
    if missing:
        errors.append(f"{path}: missing field(s): {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{path}: unsupported field(s): {', '.join(sorted(extra))}")

    name = frontmatter.get("name")
    if not nonempty_string(name):
        errors.append(f"{path}: name must be a non-empty string")
    else:
        if len(name) > 64 or not SKILL_NAME.fullmatch(name):
            errors.append(
                f"{path}: name must be at most 64 lowercase letters, digits, "
                "or hyphen-separated segments"
            )
        if path.stem != name:
            errors.append(
                f"{path}: filename stem {path.stem!r} must match agent name {name!r}"
            )

    if not nonempty_string(frontmatter.get("description")):
        errors.append(f"{path}: description must be a non-empty string")
    if not body:
        errors.append(f"{path}: instruction body must not be empty")

    tools = normalize_string_list(frontmatter.get("tools"))
    if not tools:
        errors.append(f"{path}: tools must be a non-empty string or string list")

    if "model" in frontmatter:
        errors.append(f"{path}: model must be omitted for runtime model selection")

    for field in absolute_path_fields(frontmatter):
        errors.append(f"{path}: {field} must not contain an absolute local path")
    if contains_absolute_local_path(body):
        errors.append(f"{path}: instruction body must not contain an absolute local path")

    contract = MARKDOWN_AGENT_CONTRACTS.get(target, {}).get(str(name))
    if contract is None:
        return errors

    if tools is not None and set(tools) != contract["tools"]:
        errors.append(
            f"{path}: tools must be exactly {', '.join(sorted(contract['tools']))}"
        )

    if target == "claude":
        disallowed_tools = normalize_string_list(frontmatter.get("disallowedTools"))
        if disallowed_tools is None or set(disallowed_tools) != contract[
            "disallowed_tools"
        ]:
            errors.append(f"{path}: disallowedTools must contain only Agent")
        if frontmatter.get("permissionMode") != contract["permission_mode"]:
            errors.append(f"{path}: permissionMode must be 'plan'")
    elif target == "omp" and "spawns" in frontmatter:
        errors.append(
            f"{path}: spawns must be omitted; no-delegation comes from omitting the task tool"
        )

    return errors


def validate_repository(repo_root: Path) -> tuple[list[str], int, int]:
    errors: list[str] = []
    skills_root = repo_root / "skills"
    skill_count = 0
    agent_count = 0
    discovered_skills: dict[str, Path] = {}
    reviewer_instructions: dict[str, str] = {}

    if not skills_root.is_dir():
        errors.append(f"{skills_root}: directory is required")
    else:
        try:
            discovered_skills = discover_skills(repo_root)
        except ValueError as error:
            errors.append(str(error))
        entries = sorted(
            entry for entry in skills_root.iterdir() if not entry.name.startswith(".")
        )
        for entry in entries:
            if not entry.is_dir():
                errors.append(f"{entry}: only skill directories are allowed here")
            elif not (entry / "SKILL.md").is_file():
                errors.append(f"{entry}: missing SKILL.md")
            else:
                skill_count += 1
                errors.extend(validate_skill(entry))
        if skill_count == 0:
            errors.append(f"{skills_root}: at least one skill is required")

    for name, skill_dir in discovered_skills.items():
        for dependency in SKILL_CONTRACTS.get(name, {}).get("skill_dependencies", ()):
            if dependency not in discovered_skills:
                errors.append(
                    f"{skill_dir / 'SKILL.md'}: {name} requires skill dependency {dependency}"
                )

    for target in INSTALLATION_TARGETS:
        try:
            custom_agents = discover_custom_agents(
                repo_root, target=target, allow_empty=True
            )
        except ValueError as error:
            errors.append(str(error))
            continue

        for entry in custom_agents.values():
            agent_count += 1
            if target == "codex":
                errors.extend(validate_custom_agent(entry))
                if entry.stem == "forge_strict_reviewer":
                    try:
                        config = tomllib.loads(entry.read_text(encoding="utf-8"))
                    except tomllib.TOMLDecodeError:
                        pass
                    else:
                        instructions = config.get("developer_instructions")
                        if nonempty_string(instructions):
                            reviewer_instructions[target] = instructions.strip()
            else:
                errors.extend(validate_markdown_agent(entry, target))
                if entry.stem == "forge-strict-reviewer":
                    _, body, _ = load_frontmatter_document(
                        entry, f"{target} agent definition"
                    )
                    if body:
                        reviewer_instructions[target] = body
        try:
            agents_for_skills(discovered_skills, custom_agents, target=target)
        except ValueError as error:
            errors.append(f"{target}: {error}")

    if len(reviewer_instructions) == len(INSTALLATION_TARGETS) and len(
        set(reviewer_instructions.values())
    ) != 1:
        errors.append(
            "Forge strict reviewer instructions must match across codex, claude, and omp"
        )

    return errors, skill_count, agent_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate all skills and optional custom agents in this repository."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=default_repo_root(),
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    errors, skill_count, agent_count = validate_repository(repo_root)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(
        f"validated {skill_count} skill(s) and {agent_count} custom agent definition(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
