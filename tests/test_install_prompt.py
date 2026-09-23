from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_prompt


class PromptInstallationTests(unittest.TestCase):
    def run_installer(self, home, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/install_prompt.py"), "--home", str(home), *args],
            capture_output=True, text=True,
        )

    def test_preview_install_update_and_idempotence(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            codex = home / install_prompt.TARGETS["codex"]
            claude = home / install_prompt.TARGETS["claude"]
            codex.parent.mkdir(parents=True)
            codex.write_text("Before\n" + install_prompt.START + "\nOld policy\n" + install_prompt.END + "\nAfter\n")
            original = codex.read_bytes()
            self.assertEqual(self.run_installer(home).returncode, 0)
            self.assertEqual(codex.read_bytes(), original)
            self.assertFalse(claude.exists())
            result = self.run_installer(home, "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
            prompt = install_prompt.SOURCE.read_text()
            self.assertEqual(codex.read_text(), "Before\n" + prompt.rstrip("\n") + "\nAfter\n")
            self.assertEqual(claude.read_text(), prompt)
            self.assertIn("0 file(s) changed", self.run_installer(home, "--apply").stdout)

    def test_conflicting_second_target_prevents_all_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            codex = home / install_prompt.TARGETS["codex"]
            claude = home / install_prompt.TARGETS["claude"]
            claude.parent.mkdir(parents=True)
            for invalid in (install_prompt.START, install_prompt.END + install_prompt.START,
                            install_prompt.START * 2 + install_prompt.END):
                claude.write_text(invalid)
                self.assertNotEqual(self.run_installer(home, "--apply").returncode, 0)
                self.assertFalse(codex.exists())
                self.assertEqual(claude.read_text(), invalid)
            claude.unlink()
            protected = home / "protected.md"
            protected.write_text("Keep me")
            claude.symlink_to(protected)
            self.assertNotEqual(self.run_installer(home, "--apply").returncode, 0)
            self.assertEqual(protected.read_text(), "Keep me")
            self.assertFalse(codex.exists())

    def test_later_write_failure_restores_earlier_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            codex = home / install_prompt.TARGETS["codex"]
            codex.parent.mkdir(parents=True)
            codex.write_text("Personal instructions\n")
            original = install_prompt.replace_file
            calls = 0

            def fail_second(path, content, mode):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated second-target failure")
                original(path, content, mode)

            with mock.patch.object(sys, "argv", ["install_prompt.py", "--home", str(home), "--apply"]), \
                 mock.patch.object(install_prompt, "replace_file", side_effect=fail_second):
                self.assertEqual(install_prompt.main(), 1)
            self.assertEqual(codex.read_text(), "Personal instructions\n")
            self.assertFalse((home / install_prompt.TARGETS["claude"]).exists())

    def test_concurrent_second_target_edit_is_preserved_and_first_rolled_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            codex = home / install_prompt.TARGETS["codex"]
            claude = home / install_prompt.TARGETS["claude"]
            codex.parent.mkdir(parents=True)
            claude.parent.mkdir(parents=True)
            codex.write_text("Original Codex\n")
            claude.write_text("Original Claude\n")
            original = install_prompt.replace_file

            def edit_second_after_first(path, content, mode):
                original(path, content, mode)
                if path == codex:
                    claude.write_text("Concurrent Claude edit\n")

            with mock.patch.object(sys, "argv", ["install_prompt.py", "--home", str(home), "--apply"]), \
                 mock.patch.object(install_prompt, "replace_file", side_effect=edit_second_after_first):
                self.assertEqual(install_prompt.main(), 1)
            self.assertEqual(codex.read_text(), "Original Codex\n")
            self.assertEqual(claude.read_text(), "Concurrent Claude edit\n")
