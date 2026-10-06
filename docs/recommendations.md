# Tools I recommend

These are personal recommendations alongside [my maintained skills](../README.md). Suggestions are welcome through an issue, but inclusion follows my own evaluation. The linked projects own their installation instructions and support.

| Project | Why I use it |
| --- | --- |
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | Planning, implementation, testing, and review. |
| [Archify](https://github.com/tt-a1i/archify) | Interactive architecture and workflow diagrams. |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | Keeping coding agents focused on simple solutions. |
| [Plannotator](https://plannotator.ai) | Visual review of plans, documents, and code changes. |
| [Codebase Memory MCP](https://github.com/DeusData/codebase-memory-mcp) | Structural code search, call tracing, and architecture queries. |

Follow each project's upstream instructions for installation and updates. Recommended third-party collections are linked here, not copied into this repository.

## Optional skills picker

For a checkbox picker covering the recommended skill collections and this repository, run from a checkout:

```bash
uv run install.py
uv run install.py --item all --target codex --dry-run
```

Requires [uv](https://docs.astral.sh/uv/) and [Bun](https://bun.sh). Space toggles selections; Enter continues. The picker reads [preferred-skills.json](../preferred-skills.json) and delegates to the skills CLI, which still prompts for individual skills and confirmation. It installs skills only; plugins and MCPs use their upstream setup.

The agent menu and `--target all` include detected installations: commands on `PATH`, supported macOS app bundles, or extension packages in standard VS Code, VS Code Insiders, Cursor, and Windsurf directories. Configuration directories alone do not count. If none are detected, the picker exits without installing.

Repeat `--item` and `--target` to bypass the menus. Explicit agent IDs bypass detection for custom installations; `claude` aliases `claude-code`. Remove `--dry-run` to install. Commands run sequentially; if one fails, earlier installs may have completed.

The picker uses the sources in its manifest, including this collection's default branch. For a stable tagged version of this collection, use the [release installation instructions](installation.md) instead.
