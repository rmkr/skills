from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import install as installer


class SkillsInstallerTests(unittest.TestCase):
    def test_picker_selections_and_cancel(self):
        entries = installer.read_manifest(installer.MANIFEST)
        self.assertEqual([e['id'] for e in entries], ['rmkr-workflows', 'matt-pocock', 'archify'])
        with mock.patch.object(installer, 'multiselect', return_value=['archify']):
            self.assertEqual(installer.choose(entries, None), [entries[-1]])
        with mock.patch.object(installer, 'multiselect', return_value=[]), mock.patch.object(installer.subprocess, 'run') as run:
            self.assertEqual(installer.main([]), 0)
            self.assertEqual(installer.main(['--item', 'archify']), 0)
            run.assert_not_called()
        self.assertEqual(installer.choose(entries, ['all']), entries)
        with mock.patch.object(installer, 'installed_targets', return_value=['codex']):
            self.assertEqual(installer.choose_targets(['all']), ['codex'])
        self.assertEqual(installer.choose_targets(['claude', 'claude-code', 'cursor']), ['claude-code', 'cursor'])
        for target in ['--help', 'agent;command']:
            with self.assertRaises(ValueError):
                installer.choose_targets([target])

    def test_target_menu_and_all_use_only_detected_agents(self):
        with mock.patch.object(installer, 'installed_targets', return_value=['codex', 'cursor']), \
                mock.patch.object(installer, 'multiselect', return_value=['cursor']) as select:
            self.assertEqual(installer.choose_targets(None), ['cursor'])
            self.assertEqual([choice.value for choice in select.call_args.args[1]], ['codex', 'cursor'])
            self.assertEqual(installer.choose_targets(['all']), ['codex', 'cursor'])
            self.assertEqual(installer.choose_targets(['all', 'cursor', 'claude']), ['codex', 'cursor', 'claude-code'])
        with mock.patch.object(installer, 'installed_targets', return_value=[]), \
                mock.patch.object(installer, 'multiselect') as select, \
                mock.patch.object(installer.subprocess, 'run') as run:
            self.assertEqual(installer.choose_targets(None), [])
            self.assertEqual(installer.main(['--item', 'all', '--target', 'all']), 0)
            select.assert_not_called()
            run.assert_not_called()
            self.assertEqual(installer.choose_targets(['claude', 'openclaw']), ['claude-code', 'openclaw'])

    def test_detection_uses_executables_apps_and_extensions_not_config(self):
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(installer.Path, 'home', return_value=Path(temp)), \
                mock.patch.object(installer.shutil, 'which', return_value=None) as which, \
                mock.patch.object(installer.sys, 'platform', 'linux'):
            home = Path(temp)
            for config in ('.claude', '.codex', '.cursor', '.continue'):
                (home / config).mkdir()
            self.assertEqual(installer.installed_targets(), [])
            which.side_effect = lambda command: '/bin/claude' if command == 'claude' else None
            self.assertEqual(installer.installed_targets(), ['claude-code'])
            which.side_effect = None
            for target, extension in installer.EXTENSIONS.items():
                package = home / '.vscode/extensions' / f'{extension}-1.0.0/package.json'
                package.parent.mkdir(parents=True)
                self.assertNotIn(target, installer.installed_targets())
                package.write_text('{}')
                self.assertIn(target, installer.installed_targets())
            app = home / 'Applications/Cursor.app/Contents/MacOS'
            app.mkdir(parents=True)
            self.assertNotIn('cursor', installer.installed_targets())
            with mock.patch.object(installer.sys, 'platform', 'darwin'), \
                    mock.patch.object(installer.Path, 'is_dir', autospec=True,
                                      side_effect=lambda path: path == app):
                self.assertIn('cursor', installer.installed_targets())
                self.assertNotIn('claude-code', installer.installed_targets())

    @mock.patch.object(installer.shutil, 'which', return_value='/bin/bunx')
    @mock.patch.object(installer.subprocess, 'run')
    def test_install_leaves_all_repository_skills_available_in_picker(self, run, which):
        self.assertEqual(installer.main(['--item', 'all', '--target', 'codex', '--target', 'claude']), 0)
        self.assertEqual(run.call_args_list, [
            mock.call(['bunx', 'skills', 'add', 'rmkr/skills', '--global', '--agent', 'codex', 'claude-code'], check=True),
            mock.call(['bunx', 'skills', 'add', 'mattpocock/skills', '--global', '--agent', 'codex', 'claude-code'], check=True),
            mock.call(['bunx', 'skills', 'add', 'tt-a1i/archify', '--global', '--agent', 'codex', 'claude-code'], check=True),
        ])
        run.reset_mock()
        run.side_effect = installer.subprocess.CalledProcessError(1, ['bunx'])
        self.assertEqual(installer.main(['--item', 'all', '--target', 'codex']), 1)
        self.assertEqual(run.call_count, 1)

    @mock.patch.object(installer.shutil, 'which', return_value=None)
    @mock.patch.object(installer.subprocess, 'run')
    def test_dry_run_needs_no_bun_and_never_installs(self, run, which):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(installer.main(['--item', 'all', '--target', 'codex', '--dry-run']), 0)
        self.assertEqual(len(output.getvalue().splitlines()), 3)
        self.assertTrue(all(line.startswith('bunx skills add ') for line in output.getvalue().splitlines()))
        self.assertEqual(installer.main(['--item', 'all', '--target', 'codex']), 1)
        for item in ['ponytail-plugin', 'plannotator', 'codebase-memory-mcp']:
            self.assertEqual(installer.main(['--item', item, '--target', 'codex']), 1)
        run.assert_not_called()

    def test_manifest_rejects_non_skills_and_invalid_sources(self):
        entry = {'id': 'example', 'repository': 'owner/repo'}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'preferences.json'
            invalid = [[], {}, [None], [entry, entry]] + [[{**entry, **change}] for change in (
                {'kind': 'plugin'}, {'kind': 'mcp'}, {'targets': ['*']}, {'manual': {}},
                {'repository': '--help'}, {'id': 'bad id'}, {'skills': []}, {'skills': ['--all']},
            )]
            for value in invalid:
                with self.subTest(value=value):
                    path.write_text(json.dumps(value))
                    with self.assertRaises(ValueError):
                        installer.read_manifest(path)


if __name__ == '__main__':
    unittest.main()
