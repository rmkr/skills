from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate import contains_absolute_local_path, validate_custom_agent


def run_script(name: str, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *(str(arg) for arg in args)],
        check=False,
        capture_output=True,
        text=True,
    )


def write_minimal_skill(repo_root: Path, name: str = "test-skill") -> Path:
    skill_dir = repo_root / "skills" / name
    metadata_dir = skill_dir / "agents"
    metadata_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                "description: Exercise the repository validator on a temporary skill.",
                "disable-model-invocation: true",
                "---",
                "",
                "# Test skill",
                "",
                "Perform the requested test.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (metadata_dir / "openai.yaml").write_text(
        "\n".join(
            [
                "interface:",
                '  display_name: "Test Skill"',
                '  short_description: "Exercise repository validation"',
                '  default_prompt: "Use $' + name + ' to exercise validation."',
                "",
                "policy:",
                "  allow_implicit_invocation: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return skill_dir


def write_orchestration_skills(
    repo_root: Path,
    names: tuple[str, ...] = ("subagent-delegation", "forge"),
) -> dict[str, Path]:
    fixtures = {
        "subagent-delegation": "Subagent Delegation",
        "forge": "forge",
    }
    if "forge" in names:
        # forge requires its strict reviewer definitions.
        (repo_root / "agents").symlink_to(REPO_ROOT / "agents", target_is_directory=True)
    skills: dict[str, Path] = {}
    for name in names:
        display_name = fixtures[name]
        skill_dir = write_minimal_skill(repo_root, name)
        skill_file = skill_dir / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8").replace(
            f"name: {name}\n",
            f'name: {name}\nmetadata:\n  orchestration-contract: "1"\n',
        )
        text = text.replace("disable-model-invocation: true\n", "")
        skill_file.write_text(text, encoding="utf-8")
        metadata_file = skill_dir / "agents" / "openai.yaml"
        metadata_file.write_text(
            metadata_file.read_text(encoding="utf-8")
            .replace('display_name: "Test Skill"', f'display_name: "{display_name}"')
            .replace(
                "allow_implicit_invocation: false",
                "allow_implicit_invocation: true",
            ),
            encoding="utf-8",
        )
        skills[name] = skill_dir
    return skills


class ToolingTests(unittest.TestCase):
    def test_repository_validates(self) -> None:
        result = run_script("validate.py", "--repo-root", REPO_ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        skill_count = sum(
            1 for path in (REPO_ROOT / "skills").glob("*/SKILL.md") if path.is_file()
        )
        self.assertGreater(skill_count, 0)
        self.assertIn(f"validated {skill_count} skill(s)", result.stdout)
        self.assertIn("4 custom agent definition(s)", result.stdout)

    def test_inspector_rejects_weakened_role_configuration(self) -> None:
        source = (REPO_ROOT / "agents/inspector.toml").read_text()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "inspector.toml"
            path.write_text(source)
            self.assertEqual(validate_custom_agent(path), [])
            for before, after in (
                ('sandbox_mode = "read-only"', 'sandbox_mode = "workspace-write"'),
                ('[agents]\nenabled = false', '[agents]\nenabled = true'),
                ('approval_policy = "never"', 'approval_policy = "on-request"'),
                ('[apps._default]\nenabled = false', '[apps._default]\nenabled = true'),
            ):
                with self.subTest(setting=before):
                    path.write_text(source.replace(before, after))
                    self.assertTrue(validate_custom_agent(path))

    def test_validator_rejects_unfinished_skill_scaffolds(self) -> None:
        cases = (
            (
                "description",
                'description: "[TODO: Briefly describe what this skill does and when it applies.]"',
            ),
            (
                "instruction body",
                "[TODO: Add the task-specific guidance Codex needs. "
                "Reference supporting files only when they are relevant.]",
            ),
            ("instruction body", "- [TODO: Add the review steps.]"),
            ("instruction body", "1. [TODO: Define the stopping condition.]"),
            (
                "instruction body",
                "```markdown\nExample\n```\n\n[TODO: Add the review steps.]",
            ),
            (
                "instruction body",
                "~~~markdown\nExample\n~~~\n\n[TODO: Add the review steps.]",
            ),
            (
                "instruction body",
                "- ```markdown\n  [TODO: Example only.]\n  ```\n\n"
                "[TODO: Add the review steps.]",
            ),
        )
        for field, placeholder in cases:
            with self.subTest(field=field, placeholder=placeholder):
                with tempfile.TemporaryDirectory() as temporary:
                    repo_root = Path(temporary)
                    skill_file = write_minimal_skill(repo_root) / "SKILL.md"
                    original = (
                        "description: Exercise the repository validator on a temporary skill."
                        if field == "description"
                        else "Perform the requested test."
                    )
                    skill_file.write_text(
                        skill_file.read_text(encoding="utf-8").replace(
                            original, placeholder
                        ),
                        encoding="utf-8",
                    )
                    result = run_script("validate.py", "--repo-root", repo_root)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(
                        f"{field} contains an unfinished scaffold placeholder",
                        result.stderr,
                    )

    def test_validator_allows_todo_discussion_and_markdown_examples(self) -> None:
        examples = (
            "Review TODO comments and report unresolved work.",
            'Explain the marker "[TODO: Add the review steps.]" to the user.',
            "`[TODO: Add the review steps.]`",
            '"[TODO: Add the review steps.]"',
            "> [TODO: Add the review steps.]",
            "    [TODO: Add the review steps.]",
            "\t[TODO: Add the review steps.]",
            "```markdown\n[TODO: Add the review steps.]\n```",
            "~~~markdown\n[TODO: Add the review steps.]\n~~~",
            "- ```markdown\n  [TODO: Example only.]\n  ```",
            "```markdown\n- ```\n[TODO: Example only.]\n```",
            "````markdown\n```\n[TODO: Add the review steps.]\n```\n````",
        )
        for example in examples:
            with self.subTest(example=example):
                with tempfile.TemporaryDirectory() as temporary:
                    repo_root = Path(temporary)
                    skill_file = write_minimal_skill(repo_root) / "SKILL.md"
                    skill_file.write_text(
                        skill_file.read_text(encoding="utf-8")
                        .replace(
                            "description: Exercise the repository validator on a temporary skill.",
                            "description: 'Discuss TODO markers such as [TODO: Add guidance.].'",
                        )
                        .replace("Perform the requested test.", example),
                        encoding="utf-8",
                    )
                    result = run_script("validate.py", "--repo-root", repo_root)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_validator_rejects_stale_default_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_minimal_skill(repo_root)
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8").replace(
                    "$test-skill", "$old-name"
                ),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "interface.default_prompt must mention $test-skill", result.stderr
            )

    def test_validator_requires_skill_metadata_and_explicit_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_minimal_skill(repo_root)
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.unlink()

            missing_metadata = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(missing_metadata.returncode, 1)
            self.assertIn("metadata file is required", missing_metadata.stderr)

            metadata_file.write_text("interface: {}\npolicy: {}\n", encoding="utf-8")
            missing_policy = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(missing_policy.returncode, 1)
            self.assertIn(
                "policy.allow_implicit_invocation is required", missing_policy.stderr
            )

            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8").replace(
                    "policy: {}", "policy:\n  allow_implicit_invocation: true"
                ),
                encoding="utf-8",
            )
            true_policy = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(true_policy.returncode, 1)
            self.assertNotIn(
                "policy.allow_implicit_invocation must be a boolean", true_policy.stderr
            )

    def test_validator_rejects_empty_argument_hint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_file = write_minimal_skill(repo_root, "hinted") / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8").replace(
                    "name: hinted\n", 'name: hinted\nargument-hint: ""\n'
                ),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("argument-hint must be a non-empty string", result.stderr)

    def test_validator_aligns_cross_runtime_invocation_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_minimal_skill(repo_root)
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8").replace(
                    "allow_implicit_invocation: false",
                    "allow_implicit_invocation: true",
                ),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "must be false to match SKILL.md disable-model-invocation",
                result.stderr,
            )

    def test_validator_requires_orchestration_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_orchestration_skills(repo_root, ("forge",))

            result = run_script("validate.py", "--repo-root", repo_root)

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "forge requires skill dependency subagent-delegation", result.stderr
            )

    def test_validator_accepts_complete_orchestration_dependency_sets(self) -> None:
        cases = (
            ("subagent-delegation",),
            ("subagent-delegation", "forge"),
        )
        for names in cases:
            with self.subTest(names=names):
                with tempfile.TemporaryDirectory() as temporary:
                    repo_root = Path(temporary)
                    write_orchestration_skills(repo_root, names)

                    result = run_script("validate.py", "--repo-root", repo_root)

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"validated {len(names)} skill(s)", result.stdout)

    def test_validator_requires_orchestration_contract_markers(self) -> None:
        valid_metadata = 'metadata:\n  orchestration-contract: "1"\n'
        cases = (
            ("absent metadata", ""),
            ("absent marker", "metadata:\n  author: Example\n"),
            ("mismatched marker", 'metadata:\n  orchestration-contract: "2"\n'),
            ("numeric marker", "metadata:\n  orchestration-contract: 1\n"),
        )
        for name in ("subagent-delegation", "forge"):
            for label, replacement in cases:
                with self.subTest(name=name, marker=label):
                    with tempfile.TemporaryDirectory() as temporary:
                        repo_root = Path(temporary)
                        skills = write_orchestration_skills(repo_root)
                        skill_file = skills[name] / "SKILL.md"
                        skill_file.write_text(
                            skill_file.read_text(encoding="utf-8").replace(
                                valid_metadata, replacement
                            ),
                            encoding="utf-8",
                        )

                        result = run_script("validate.py", "--repo-root", repo_root)

                        self.assertEqual(result.returncode, 1)
                        self.assertIn(
                            f"{skill_file}: metadata.orchestration-contract "
                            "must be the string '1'",
                            result.stderr,
                        )

    def test_validator_rejects_unsupported_shared_orchestration_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            for skill_dir in write_orchestration_skills(repo_root).values():
                skill_file = skill_dir / "SKILL.md"
                skill_file.write_text(
                    skill_file.read_text(encoding="utf-8").replace(
                        'orchestration-contract: "1"', 'orchestration-contract: "2"'
                    ),
                    encoding="utf-8",
                )

            result = run_script("validate.py", "--repo-root", repo_root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stderr.count(
                    "metadata.orchestration-contract must be the string '1'"
                ),
                2,
            )

    def test_validator_preserves_orchestration_invocation_policy(self) -> None:
        for name in ("subagent-delegation", "forge"):
            for change_skill, change_policy in (
                (True, False),
                (False, True),
                (True, True),
            ):
                with self.subTest(name=name, skill=change_skill, policy=change_policy):
                    with tempfile.TemporaryDirectory() as temporary:
                        repo_root = Path(temporary)
                        skill_dir = write_orchestration_skills(repo_root)[name]
                        if change_skill:
                            skill_file = skill_dir / "SKILL.md"
                            skill_file.write_text(
                                skill_file.read_text(encoding="utf-8").replace(
                                    f"name: {name}\n",
                                    f"name: {name}\ndisable-model-invocation: true\n",
                                ),
                                encoding="utf-8",
                            )
                        if change_policy:
                            metadata_file = skill_dir / "agents" / "openai.yaml"
                            metadata_file.write_text(
                                metadata_file.read_text(encoding="utf-8").replace(
                                    "allow_implicit_invocation: true",
                                    "allow_implicit_invocation: false",
                                ),
                                encoding="utf-8",
                            )

                        result = run_script("validate.py", "--repo-root", repo_root)

                        self.assertEqual(result.returncode, 1)
                        if change_skill:
                            self.assertIn(
                                f"{name} disable-model-invocation must be false",
                                result.stderr,
                            )
                        if change_policy:
                            self.assertIn(
                                f"{name} policy.allow_implicit_invocation must be true",
                                result.stderr,
                            )

    def test_validator_enforces_forge_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_orchestration_skills(repo_root)["forge"]
            valid = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8")
                .replace('display_name: "forge"', 'display_name: "The Forge"'),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("interface.display_name must be 'forge'", result.stderr)

    def test_validator_requires_forge_strict_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root, "forge")

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing custom agent dependency", result.stderr)

    def test_validator_enforces_unslop_identity_and_implicit_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_minimal_skill(repo_root, "unslop")
            skill_file = skill_dir / "SKILL.md"
            valid_skill = skill_file.read_text(encoding="utf-8").replace(
                "disable-model-invocation: true\n", ""
            )
            skill_file.write_text(valid_skill, encoding="utf-8")
            metadata_file = skill_dir / "agents" / "openai.yaml"
            valid_metadata = (
                metadata_file.read_text(encoding="utf-8").replace(
                    'display_name: "Test Skill"', 'display_name: "Unslop"'
                ).replace(
                    "allow_implicit_invocation: false",
                    "allow_implicit_invocation: true",
                )
            )
            metadata_file.write_text(valid_metadata, encoding="utf-8")

            valid = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(valid.returncode, 0, valid.stderr)

            skill_file.write_text(
                valid_skill.replace(
                    "description: Exercise the repository validator on a temporary skill.\n",
                    "description: Exercise the repository validator on a temporary skill.\n"
                    "disable-model-invocation: true\n",
                ),
                encoding="utf-8",
            )
            disabled = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(disabled.returncode, 1)
            self.assertIn(
                "unslop disable-model-invocation must be false", disabled.stderr
            )

            skill_file.write_text(valid_skill, encoding="utf-8")
            metadata_file.write_text(
                valid_metadata.replace(
                    "allow_implicit_invocation: true",
                    "allow_implicit_invocation: false",
                ),
                encoding="utf-8",
            )
            explicit = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(explicit.returncode, 1)
            self.assertIn(
                "unslop policy.allow_implicit_invocation must be true",
                explicit.stderr,
            )

            metadata_file.write_text(
                valid_metadata.replace(
                    'display_name: "Unslop"', 'display_name: "Generic Rewrite"'
                ),
                encoding="utf-8",
            )
            renamed = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(renamed.returncode, 1)
            self.assertIn(
                "unslop interface.display_name must be 'Unslop'", renamed.stderr
            )

    def test_validator_enforces_forge_strict_reviewer_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            agents_dir = repo_root / "agents"
            agents_dir.mkdir()
            (agents_dir / "forge_strict_reviewer.toml").write_text(
                """name = "forge_strict_reviewer"
description = "Review immutable diff bundles."
developer_instructions = "Return actionable findings."
sandbox_mode = "workspace-write"
model = "fixed-model"
model_reasoning_effort = "high"
""",
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("sandbox_mode must be 'read-only'", result.stderr)
            self.assertIn("model must be omitted", result.stderr)
            self.assertIn("model_reasoning_effort must be omitted", result.stderr)
            self.assertIn("agents.enabled must be false", result.stderr)

    def test_validator_enforces_cross_runtime_reviewer_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            claude_agents = repo_root / "agents" / "claude"
            claude_agents.mkdir(parents=True)
            (claude_agents / "forge-strict-reviewer.md").write_text(
                """---
name: forge-strict-reviewer
description: Review immutable diff bundles.
tools: [Read, Grep, Glob, Agent]
disallowedTools: []
permissionMode: acceptEdits
model: fixed-model
---

Review the bundle.
""",
                encoding="utf-8",
            )
            omp_agents = repo_root / "agents" / "omp"
            omp_agents.mkdir(parents=True)
            (omp_agents / "forge-strict-reviewer.md").write_text(
                """---
name: forge-strict-reviewer
description: Review immutable diff bundles.
tools: [read, grep, task]
spawns: [task]
model: fixed-model
---

Review the bundle.
""",
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("permissionMode must be 'plan'", result.stderr)
            self.assertIn("disallowedTools must contain only Agent", result.stderr)
            self.assertIn("spawns must be omitted", result.stderr)
            self.assertGreaterEqual(
                result.stderr.count("model must be omitted for runtime model selection"),
                2,
            )

    def test_validator_rejects_cross_runtime_reviewer_instruction_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            for source in (
                REPO_ROOT / "skills",
                REPO_ROOT / "agents",
            ):
                destination = repo_root / source.name
                destination.symlink_to(source, target_is_directory=True)

            claude_agent = REPO_ROOT / "agents/claude/forge-strict-reviewer.md"
            copied_agents = repo_root / "copied-claude"
            copied_agents.mkdir()
            copied_agent = copied_agents / claude_agent.name
            copied_agent.write_text(
                claude_agent.read_text(encoding="utf-8").replace(
                    "Review exactly one immutable diff bundle",
                    "Review any available diff bundle",
                ),
                encoding="utf-8",
            )
            (repo_root / "agents").unlink()
            agents_root = repo_root / "agents"
            agents_root.mkdir()
            (agents_root / "forge_strict_reviewer.toml").symlink_to(
                REPO_ROOT / "agents/forge_strict_reviewer.toml"
            )
            (agents_root / "omp").symlink_to(
                REPO_ROOT / "agents/omp", target_is_directory=True
            )
            (agents_root / "claude").symlink_to(
                copied_agents, target_is_directory=True
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "reviewer instructions must match across codex, claude, and omp",
                result.stderr,
            )

    def test_hidden_skill_is_rejected_by_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root, ".hidden-skill")

            validation = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(validation.returncode, 1)
            self.assertIn("hidden skill directories are not allowed", validation.stderr)

    def test_validator_rejects_absolute_agent_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            agents_dir = repo_root / "agents"
            agents_dir.mkdir()
            (agents_dir / "reviewer.toml").write_text(
                """name = "reviewer"
description = "Review implementation output."
developer_instructions = "Report actionable findings."

[[skills.config]]
path = "/home/example/.agents/skills/review/SKILL.md"
""",
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("must not contain an absolute local path", result.stderr)

    def test_validator_rejects_posix_and_windows_paths_in_agent_text_fields(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            agents_dir = repo_root / "agents"
            agents_dir.mkdir()
            (agents_dir / "reviewer.toml").write_text(
                """name = "reviewer"
description = "Review implementation output."
developer_instructions = "Read C:\\\\Users\\\\example\\\\private.txt, but see https://example.com/docs."
command = "cat /home/example/private.txt"
args = ["--config", "C:\\\\Users\\\\example\\\\config.toml"]
""",
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("developer_instructions must not contain", result.stderr)
            self.assertIn("command must not contain", result.stderr)
            self.assertIn("args[1] must not contain", result.stderr)

    def test_absolute_path_detector_excludes_urls_and_relative_paths(self) -> None:
        self.assertTrue(contains_absolute_local_path("Read /home/example/private.txt"))
        self.assertTrue(
            contains_absolute_local_path(r"Read C:\Users\example\private.txt")
        )
        self.assertTrue(
            contains_absolute_local_path(r"Read \\server\share\private.txt")
        )
        self.assertFalse(contains_absolute_local_path("See https://example.com/docs"))
        self.assertFalse(
            contains_absolute_local_path("https://example.com/?next=/home/user")
        )
        self.assertFalse(
            contains_absolute_local_path("https://example.com/#/home/user")
        )
        self.assertFalse(
            contains_absolute_local_path("vscode://remote?path=/home/user")
        )
        self.assertFalse(
            contains_absolute_local_path("x://example.test/?next=/home/user")
        )
        self.assertFalse(contains_absolute_local_path("open docs/guide.md"))
        self.assertTrue(
            contains_absolute_local_path("Open file:///home/user/private.txt")
        )
        self.assertTrue(
            contains_absolute_local_path(
                "See https://example.com/?next=/remote/path then /home/user/private.txt"
            )
        )
        self.assertTrue(
            contains_absolute_local_path(
                "See x://example.test/?next=/remote/path then /home/user/private.txt"
            )
        )

    def test_validator_rejects_absolute_paths_in_evolving_agent_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            agents_dir = repo_root / "agents"
            agents_dir.mkdir()
            (agents_dir / "reviewer.toml").write_text(
                """name = "reviewer"
description = "Review implementation output."
developer_instructions = "Use vscode://remote?path=/home/not-local."
model_instructions_file = "/home/example/instructions.md"
model_catalog_json = "C:\\\\Users\\\\example\\\\catalog.json"
log_dir = "/var/log/reviewer"
sqlite_home = "/home/example/.sqlite"
notify = ["/usr/local/bin/notify"]

[sandbox_workspace_write]
writable_roots = ["/workspace/output"]
""",
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            for field in (
                "model_instructions_file",
                "model_catalog_json",
                "log_dir",
                "sqlite_home",
                "notify[0]",
                "sandbox_workspace_write.writable_roots[0]",
            ):
                self.assertIn(f"{field} must not contain", result.stderr)


if __name__ == "__main__":
    unittest.main()
