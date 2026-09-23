from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import uninstall as uninstall_tool
from _shared import managed_custom_agent_links, managed_skill_links
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
    names: tuple[str, ...] = (
        "subagent-delegation",
        "adversarial-review-loop",
        "forge-review-loop",
    ),
) -> dict[str, Path]:
    fixtures = {
        "subagent-delegation": ("Subagent Delegation", False),
        "adversarial-review-loop": ("Adversarial Review Loop", False),
        "forge-review-loop": ("The Forge", True),
    }
    skills: dict[str, Path] = {}
    for name in names:
        display_name, explicit_only = fixtures[name]
        skill_dir = write_minimal_skill(repo_root, name)
        skill_file = skill_dir / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8").replace(
            f"name: {name}\n",
            f'name: {name}\nmetadata:\n  orchestration-contract: "1"\n',
        )
        if not explicit_only:
            text = text.replace("disable-model-invocation: true\n", "")
        skill_file.write_text(text, encoding="utf-8")
        metadata_file = skill_dir / "agents" / "openai.yaml"
        metadata_file.write_text(
            metadata_file.read_text(encoding="utf-8")
            .replace('display_name: "Test Skill"', f'display_name: "{display_name}"')
            .replace(
                "allow_implicit_invocation: false",
                f"allow_implicit_invocation: {str(not explicit_only).lower()}",
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

    def test_uninstall_removes_managed_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_dir = Path(temporary) / "skills"
            agents_dir = Path(temporary) / "agents"
            skills_dir.mkdir()
            agents_dir.mkdir()
            links = {
                skills_dir / "forge-review-loop": REPO_ROOT / "skills/forge-review-loop",
                skills_dir / "diff-skeptic": REPO_ROOT / "skills/diff-skeptic",
                agents_dir / "diff_skeptic_reviewer.toml": REPO_ROOT / "agents/diff_skeptic_reviewer.toml",
            }
            for destination, source in links.items():
                destination.symlink_to(source, target_is_directory=source.is_dir())
            result = run_script("uninstall.py", "--skills-dir", skills_dir, "--agents-dir", agents_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            for destination in links:
                self.assertFalse(destination.exists())
                self.assertFalse(destination.is_symlink())

    def test_named_diff_skeptic_uninstall_includes_reviewer_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_dir = Path(temporary) / "skills"
            agents_dir = Path(temporary) / "agents"
            skills_dir.mkdir()
            agents_dir.mkdir()
            for name in ("diff-skeptic", "forge-review-loop"):
                (skills_dir / name).symlink_to(REPO_ROOT / "skills" / name, target_is_directory=True)
            reviewer = agents_dir / "diff_skeptic_reviewer.toml"
            reviewer.symlink_to(REPO_ROOT / "agents/diff_skeptic_reviewer.toml")
            result = run_script("uninstall.py", "--skills-dir", skills_dir, "--agents-dir", agents_dir, "--skill", "diff-skeptic")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((skills_dir / "diff-skeptic").is_symlink())
            self.assertFalse(reviewer.is_symlink())
            self.assertTrue((skills_dir / "forge-review-loop").is_symlink())

    def test_all_targets_uninstall_matching_agent_definitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_home = Path(temporary)
            expected_links = {
                temporary_home / ".agents/skills/diff-skeptic": REPO_ROOT / "skills/diff-skeptic",
                temporary_home / ".claude/skills/diff-skeptic": REPO_ROOT / "skills/diff-skeptic",
                temporary_home / ".omp/agent/skills/diff-skeptic": REPO_ROOT / "skills/diff-skeptic",
                temporary_home / ".codex/agents/diff_skeptic_reviewer.toml": REPO_ROOT / "agents/diff_skeptic_reviewer.toml",
                temporary_home / ".claude/agents/diff-skeptic-reviewer.md": REPO_ROOT / "agents/claude/diff-skeptic-reviewer.md",
                temporary_home / ".omp/agent/agents/diff-skeptic-reviewer.md": REPO_ROOT / "agents/omp/diff-skeptic-reviewer.md",
            }
            for destination, source in expected_links.items():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.symlink_to(source, target_is_directory=source.is_dir())
            with mock.patch.dict(os.environ, {"HOME": str(temporary_home)}):
                result = run_script("uninstall.py", "--target", "all")
            self.assertEqual(result.returncode, 0, result.stderr)
            for destination in expected_links:
                self.assertFalse(destination.is_symlink(), destination)

    def test_ohmypi_alias_uninstalls_omp_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_dir = Path(temporary) / "skills"
            agents_dir = Path(temporary) / "agents"
            skills_dir.mkdir()
            agents_dir.mkdir()
            skill = skills_dir / "diff-skeptic"
            skill.symlink_to(REPO_ROOT / "skills/diff-skeptic", target_is_directory=True)
            reviewer = agents_dir / "diff-skeptic-reviewer.md"
            reviewer.symlink_to(REPO_ROOT / "agents/omp/diff-skeptic-reviewer.md")
            result = run_script("uninstall.py", "--target", "ohmypi", "--skills-dir", skills_dir, "--agents-dir", agents_dir, "--skill", "diff-skeptic")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(skill.is_symlink())
            self.assertFalse(reviewer.is_symlink())

    def test_uninstall_rolls_back_when_second_unlink_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            skill_destination = temporary_root / "diff-skeptic"
            reviewer_destination = temporary_root / "diff_skeptic_reviewer.toml"
            skill_source = REPO_ROOT / "skills" / "diff-skeptic"
            reviewer_source = REPO_ROOT / "agents" / "diff_skeptic_reviewer.toml"
            skill_destination.symlink_to(skill_source, target_is_directory=True)
            reviewer_destination.symlink_to(reviewer_source)

            real_unlink = Path.unlink

            def fail_on_reviewer(path: Path, *args: object, **kwargs: object) -> None:
                if path == reviewer_destination:
                    raise PermissionError("simulated unlink failure")
                real_unlink(path, *args, **kwargs)

            with mock.patch.object(Path, "unlink", fail_on_reviewer):
                error, rollback_errors = uninstall_tool.remove_links_atomically(
                    [skill_destination, reviewer_destination]
                )

            self.assertIsInstance(error, PermissionError)
            self.assertEqual(rollback_errors, [])
            self.assertTrue(skill_destination.is_symlink())
            self.assertEqual(skill_destination.resolve(), skill_source.resolve())
            self.assertTrue(reviewer_destination.is_symlink())
            self.assertEqual(reviewer_destination.resolve(), reviewer_source.resolve())

    def test_uninstall_refuses_unmanaged_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            skills_dir = Path(temporary) / "skills"
            agents_dir = Path(temporary) / "agents"
            destination = skills_dir / "forge-review-loop"
            skeptic_destination = skills_dir / "diff-skeptic"
            skeptic_source = REPO_ROOT / "skills" / "diff-skeptic"
            reviewer_destination = agents_dir / "diff_skeptic_reviewer.toml"
            reviewer_source = REPO_ROOT / "agents" / "diff_skeptic_reviewer.toml"
            destination.mkdir(parents=True)
            marker = destination / "owned-by-user"
            marker.write_text("preserve", encoding="utf-8")

            skeptic_destination.symlink_to(skeptic_source, target_is_directory=True)
            agents_dir.mkdir(parents=True)
            reviewer_destination.symlink_to(reviewer_source)
            uninstall = run_script(
                "uninstall.py",
                "--skills-dir",
                skills_dir,
                "--agents-dir",
                agents_dir,
            )
            self.assertEqual(uninstall.returncode, 1)
            self.assertTrue(marker.exists())
            self.assertTrue(skeptic_destination.is_symlink())
            self.assertEqual(skeptic_destination.resolve(), skeptic_source.resolve())
            self.assertTrue(reviewer_destination.is_symlink())
            self.assertEqual(reviewer_destination.resolve(), reviewer_source.resolve())
            self.assertIn("no changes made", uninstall.stderr)

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
        cases = (
            (
                ("adversarial-review-loop",),
                (("adversarial-review-loop", "subagent-delegation"),),
            ),
            (
                ("forge-review-loop",),
                (
                    ("forge-review-loop", "subagent-delegation"),
                    ("forge-review-loop", "adversarial-review-loop"),
                ),
            ),
            (
                ("subagent-delegation", "forge-review-loop"),
                (("forge-review-loop", "adversarial-review-loop"),),
            ),
            (
                ("adversarial-review-loop", "forge-review-loop"),
                (
                    ("adversarial-review-loop", "subagent-delegation"),
                    ("forge-review-loop", "subagent-delegation"),
                ),
            ),
        )
        for names, missing_dependencies in cases:
            with self.subTest(names=names):
                with tempfile.TemporaryDirectory() as temporary:
                    repo_root = Path(temporary)
                    write_orchestration_skills(repo_root, names)

                    result = run_script("validate.py", "--repo-root", repo_root)

                    self.assertEqual(result.returncode, 1)
                    for name, dependency in missing_dependencies:
                        self.assertIn(
                            f"{name} requires skill dependency {dependency}",
                            result.stderr,
                        )

    def test_validator_accepts_complete_orchestration_dependency_sets(self) -> None:
        cases = (
            ("subagent-delegation",),
            ("subagent-delegation", "adversarial-review-loop"),
            ("subagent-delegation", "adversarial-review-loop", "forge-review-loop"),
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
        for name in (
            "subagent-delegation",
            "adversarial-review-loop",
            "forge-review-loop",
        ):
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
                3,
            )

    def test_validator_preserves_orchestration_invocation_policy(self) -> None:
        cases = (
            ("subagent-delegation", "false", "true"),
            ("adversarial-review-loop", "false", "true"),
            ("forge-review-loop", "true", "false"),
        )
        for name, expected_disabled, expected_implicit in cases:
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
                            text = skill_file.read_text(encoding="utf-8")
                            if expected_disabled == "true":
                                text = text.replace(
                                    "disable-model-invocation: true\n", ""
                                )
                            else:
                                text = text.replace(
                                    f"name: {name}\n",
                                    f"name: {name}\ndisable-model-invocation: true\n",
                                )
                            skill_file.write_text(text, encoding="utf-8")
                        if change_policy:
                            metadata_file = skill_dir / "agents" / "openai.yaml"
                            metadata_file.write_text(
                                metadata_file.read_text(encoding="utf-8").replace(
                                    f"allow_implicit_invocation: {expected_implicit}",
                                    f"allow_implicit_invocation: {expected_disabled}",
                                ),
                                encoding="utf-8",
                            )

                        result = run_script("validate.py", "--repo-root", repo_root)

                        self.assertEqual(result.returncode, 1)
                        if change_skill:
                            self.assertIn(
                                f"{name} disable-model-invocation "
                                f"must be {expected_disabled}",
                                result.stderr,
                            )
                        if change_policy:
                            self.assertIn(
                                f"{name} policy.allow_implicit_invocation "
                                f"must be {expected_implicit}",
                                result.stderr,
                            )

    def test_validator_enforces_forge_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_orchestration_skills(repo_root)["forge-review-loop"]
            valid = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8")
                .replace('display_name: "The Forge"', 'display_name: "Old Forge"')
                .replace(
                    "allow_implicit_invocation: false",
                    "allow_implicit_invocation: true",
                ),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("interface.display_name must be 'The Forge'", result.stderr)
            self.assertIn(
                "policy.allow_implicit_invocation must be false", result.stderr
            )

    def test_validator_enforces_diff_skeptic_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            skill_dir = write_minimal_skill(repo_root, "diff-skeptic")
            metadata_file = skill_dir / "agents" / "openai.yaml"
            metadata_file.write_text(
                metadata_file.read_text(encoding="utf-8")
                .replace('display_name: "Test Skill"', 'display_name: "Passive Review"')
                .replace(
                    "allow_implicit_invocation: false",
                    "allow_implicit_invocation: true",
                ),
                encoding="utf-8",
            )

            result = run_script("validate.py", "--repo-root", repo_root)
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "interface.display_name must be 'Diff Skeptic'", result.stderr
            )
            self.assertIn(
                "policy.allow_implicit_invocation must be false", result.stderr
            )
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

    def test_validator_enforces_diff_skeptic_reviewer_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            write_minimal_skill(repo_root)
            agents_dir = repo_root / "agents"
            agents_dir.mkdir()
            (agents_dir / "diff_skeptic_reviewer.toml").write_text(
                """name = "diff_skeptic_reviewer"
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
            (claude_agents / "diff-skeptic-reviewer.md").write_text(
                """---
name: diff-skeptic-reviewer
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
            (omp_agents / "diff-skeptic-reviewer.md").write_text(
                """---
name: diff-skeptic-reviewer
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

            claude_agent = REPO_ROOT / "agents/claude/diff-skeptic-reviewer.md"
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
            (agents_root / "diff_skeptic_reviewer.toml").symlink_to(
                REPO_ROOT / "agents/diff_skeptic_reviewer.toml"
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

    def test_uninstall_removes_broken_orphan_managed_links_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            repo_root = temporary_root / "repo"
            skills_dir = temporary_root / "user-skills"
            agents_dir = temporary_root / "user-agents"
            skills_dir.mkdir()
            orphan = skills_dir / "renamed-skill"
            orphan.symlink_to(
                repo_root / "skills" / "removed-skill", target_is_directory=True
            )
            unrelated = skills_dir / "unrelated"
            unrelated.symlink_to(temporary_root / "elsewhere", target_is_directory=True)

            explicit = run_script(
                "uninstall.py",
                "--repo-root",
                repo_root,
                "--skills-dir",
                skills_dir,
                "--agents-dir",
                agents_dir,
                "--skill",
                "renamed-skill",
            )
            self.assertEqual(explicit.returncode, 0, explicit.stderr)
            self.assertFalse(orphan.is_symlink())
            self.assertTrue(unrelated.is_symlink())

            broken = skills_dir / "broken-skill"
            broken.symlink_to(
                repo_root / "skills" / "also-removed", target_is_directory=True
            )
            default = run_script(
                "uninstall.py",
                "--repo-root",
                repo_root,
                "--skills-dir",
                skills_dir,
                "--agents-dir",
                agents_dir,
            )
            self.assertEqual(default.returncode, 0, default.stderr)
            self.assertFalse(broken.is_symlink())
            self.assertTrue(unrelated.is_symlink())

    def test_uninstall_recognizes_orphan_targets_through_directory_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            canonical = temporary_root / "canonical"
            canonical.mkdir()
            alias = temporary_root / "alias"
            alias.symlink_to(canonical, target_is_directory=True)
            repo_root = canonical / "repo"
            skills_dir = temporary_root / "user-skills"
            agents_dir = temporary_root / "user-agents"
            skills_dir.mkdir()
            agents_dir.mkdir()

            managed_skill = skills_dir / "removed-skill"
            managed_skill.symlink_to(alias / "repo/skills/removed-skill")
            managed_agent = agents_dir / "removed_agent.toml"
            managed_agent.symlink_to(alias / "repo/agents/removed_agent.toml")
            unmanaged_skill = skills_dir / "unmanaged-skill"
            unmanaged_skill.symlink_to(alias / "other/skills/unmanaged-skill")
            unmanaged_agent = agents_dir / "unmanaged_agent.toml"
            unmanaged_agent.symlink_to(alias / "other/agents/unmanaged_agent.toml")
            unmanaged_directory = skills_dir / "local-skill"
            unmanaged_directory.mkdir()

            result = run_script(
                "uninstall.py",
                "--repo-root",
                repo_root,
                "--skills-dir",
                skills_dir,
                "--agents-dir",
                agents_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(managed_skill.is_symlink())
            self.assertFalse(managed_agent.is_symlink())
            self.assertTrue(unmanaged_skill.is_symlink())
            self.assertTrue(unmanaged_agent.is_symlink())
            self.assertTrue(unmanaged_directory.is_dir())

    def test_managed_links_preserve_symlink_sensitive_parent_traversal(self) -> None:
        for directory, filename, discover in (
            ("skills", "foreign", managed_skill_links),
            ("agents", "foreign.toml", managed_custom_agent_links),
        ):
            with self.subTest(directory=directory):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    repo_root = root / "repo"
                    source_root = repo_root / directory
                    source_root.mkdir(parents=True)
                    outside = root / "outside"
                    (outside / "nested").mkdir(parents=True)
                    (source_root / "nested").symlink_to(outside / "nested")
                    alias = root / "alias"
                    alias.symlink_to(source_root)
                    installed = root / "installed"
                    installed.mkdir()
                    foreign = installed / filename
                    foreign.symlink_to(alias / "nested" / ".." / filename)
                    self.assertEqual(foreign.resolve(), (outside / filename).resolve())
                    self.assertEqual(discover(repo_root, installed), {})
                    self.assertTrue(foreign.is_symlink())

    def test_managed_links_preserve_final_parent_traversal(self) -> None:
        for directory, filename, discover in (
            ("skills", "shortcut", managed_skill_links),
            ("agents", "shortcut.toml", managed_custom_agent_links),
        ):
            with self.subTest(directory=directory):
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    repo_root = root / "repo"
                    source_root = repo_root / directory
                    source_root.mkdir(parents=True)
                    installed = root / "installed"
                    installed.mkdir()
                    shortcut = installed / filename
                    shortcut.symlink_to(source_root / "..")
                    self.assertEqual(shortcut.resolve(), repo_root.resolve())
                    self.assertEqual(discover(repo_root, installed), {})
                    self.assertTrue(shortcut.is_symlink())

    def test_uninstall_preserves_looping_links_and_removes_managed_orphans(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo_root = root / "repo"
            skills_dir = root / "user-skills"
            agents_dir = root / "user-agents"
            loop = root / "loop"
            loop.symlink_to(loop)
            managed = []
            unrelated = []
            for installed, directory, filename in (
                (skills_dir, "skills", "removed"),
                (agents_dir, "agents", "removed.toml"),
            ):
                installed.mkdir()
                managed_link = installed / filename
                managed_link.symlink_to(repo_root / directory / filename)
                managed.append(managed_link)
                unrelated_link = installed / ("looping" + Path(filename).suffix)
                unrelated_link.symlink_to(loop / filename)
                unrelated.append(unrelated_link)
            result = run_script(
                "uninstall.py",
                "--repo-root",
                repo_root,
                "--skills-dir",
                skills_dir,
                "--agents-dir",
                agents_dir,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for link in managed:
                self.assertFalse(link.is_symlink())
            for link in unrelated:
                self.assertTrue(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
