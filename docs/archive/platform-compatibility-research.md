# Platform compatibility research

> Historical record. Runtime observations, installation state, and task authorization below describe the original work only. For current support and setup, see [compatibility](../compatibility.md) and [installation](../installation.md).

Current as of 2026-08-17. This note uses only first-party product documentation, official repositories, and the Agent Skills specification. OhMyPi (`omp`) and upstream Pi are separate products; both are covered where that distinction affects installation.

## Conclusion

Use the [Agent Skills specification](https://agentskills.io/specification) as the canonical skill format, then add platform-specific installation and custom-agent adapters.

The repository's current `skills/<name>/SKILL.md` files satisfy the portable core's naming and description constraints: the directory and frontmatter `name` match, both names are lowercase kebab-case, and each file has a specific `description`. Their Markdown bodies are mostly runtime-neutral. They now also carry `disable-model-invocation: true` to express a manual-only intent. That field is recognized by the targeted local Claude/OMP/Pi clients but is not one of the six standard fields, and its enforcement differs: Claude blocks model invocation, while OMP/Pi use hidden-from-catalog behavior rather than the same hard block; OMP still permits direct `skill://` access. These files are therefore not strictly portable to spec validators, claude.ai upload, or the Skills API. The standard has no equivalent manual-only field: an export must reject that unsupported requirement or strip it only when automatic/model activation is an accepted behavior change. The remaining nonportable pieces are orchestration bindings:

- `skills/*/agents/openai.yaml` is Codex presentation/invocation metadata, not shared Agent Skills metadata.
- `agents/diff_skeptic_reviewer.toml` is a Codex custom-agent definition. Claude Code and OMP use different Markdown agent schemas and do not load that TOML.
- The Codex profile remains named `diff_skeptic_reviewer`; Claude custom-agent names allow lowercase letters and hyphens, so the adapter needs a hyphenated name. The shared skill should continue resolving the role semantically rather than naming either identifier.
- Tool names, subagent dispatch calls, model selectors, and read-only enforcement are client capabilities, not part of Agent Skills.

## Portable Agent Skills baseline

A portable skill is a directory containing exact-uppercase `SKILL.md`. The file is YAML frontmatter followed by unrestricted Markdown. Standard frontmatter is:

| Field | Status | Portable constraint |
| --- | --- | --- |
| `name` | Required | 1-64 ASCII lowercase letters, digits, and hyphens; no leading/trailing hyphen or `--`; equals the parent directory |
| `description` | Required | 1-1024 non-empty characters; says both what the skill does and when to use it |
| `license` | Optional | License name or bundled-file reference |
| `compatibility` | Optional | 1-500 characters describing real environment requirements |
| `metadata` | Optional | String-to-string extension map |
| `allowed-tools` | Optional, experimental | Space-separated pre-approved tools; semantics vary by client |

The standard recommends `scripts/`, `references/`, and `assets/`, skill-root-relative references, a `SKILL.md` under 500 lines, and progressive disclosure: clients catalog `name` and `description`, load the full instructions on activation, then load resources only as needed. [Specification and progressive-disclosure rules](https://agentskills.io/specification)

The specification deliberately does **not** define installation paths, explicit invocation syntax, custom subagents, tool identifiers, or symlink behavior. Its implementor guide recommends scanning both client-native roots and the interoperable `.agents/skills/` convention, but calls that convention non-normative. It also leaves `/skill-name` versus `$skill-name` to the client. [Official client implementation guide](https://agentskills.io/client-implementation/adding-skills-support)

Portability rules for this repository:

- Prefer the six standard top-level fields. If manual-only invocation is a cross-runtime product requirement, treat shared `disable-model-invocation: true` as an intentional local-client extension and document both the strict-spec/upload limitation and OMP's weaker hidden-from-catalog semantics. Strip it only when automatic/model activation is explicitly acceptable; otherwise reject that export.
- Use ordinary relative resource paths. Do not put Claude substitutions, Claude shell injection, OMP `skill://` URLs, Codex-only tool names, or a platform-specific subagent call in the shared body.
- Treat `allowed-tools` as advisory portability metadata, not a cross-client sandbox.
- Validate the canonical source's standard fields strictly. For a strict-spec distribution, render out the documented client extension and validate that exported artifact end to end.

## Skill discovery and invocation

### Claude Code

Claude Code's documented skill locations include:

- personal: `~/.claude/skills/<skill-name>/SKILL.md`
- project: `.claude/skills/<skill-name>/SKILL.md`
- plugin: `<plugin>/skills/<skill-name>/SKILL.md` or a plugin-root `SKILL.md`

Enterprise-managed skills are an additional organization-wide scope. Project skills are found from the starting directory and its ancestors to the repository root. Nested project `.claude/skills/` directories below the start directory appear on demand when Claude works in that subtree. Skills in `--add-dir` directories are also loaded. Personal/project skills invoke as `/directory-name [arguments]` or activate automatically from `description`; a plugin skill's guaranteed form is `/plugin-name:skill-name`, with a bare `/skill-name` alias when no other command owns that name. The frontmatter `name` is only a display label for personal/project skills, so keeping directory and frontmatter names identical is important. [Claude Code skills documentation](https://code.claude.com/docs/en/slash-commands)

Claude Code explicitly follows a symlink used as an individual `<skill-name>` entry and deduplicates multiple paths to the same target. This supports:

```text
~/.claude/skills/diff-skeptic -> <checkout>/skills/diff-skeptic
```

The documentation does not guarantee that replacing the entire `~/.claude/skills` directory with one symlink behaves the same way. It also does not document `~/.agents/skills` as a Claude Code discovery root, so a neutral-root-only installation is not a documented or supported Claude Code strategy. [Claude symlink and location rules](https://code.claude.com/docs/en/slash-commands#where-skills-live)

Claude Code accepts every standard field. Its CLI also implements nonportable fields including `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, and `shell`. It also implements `$ARGUMENTS`, positional/named substitutions, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, pre-execution shell injection, and `context: fork`. Claude's own docs warn that only the six standard fields are accepted by claude.ai uploads and the Skills API. Apart from the repository's documented manual-only `disable-model-invocation` exception for local clients, keep those CLI features out of canonical cross-client skills. [Claude frontmatter and cross-product rules](https://code.claude.com/docs/en/slash-commands#frontmatter-reference)

Claude has no dedicated standalone-skill installer requirement: copying or linking the folder into a discovery root is sufficient. For packaged distribution, a Claude plugin can bundle `skills/` and `agents/` and be installed from a marketplace, but plugin skills acquire a namespace and plugin agent security fields are restricted. [Claude plugin model](https://code.claude.com/docs/en/plugins)

### OhMyPi (`omp`)

OMP's native roots are:

- personal: `~/.omp/agent/skills/<skill-name>/SKILL.md`
- project: `<ancestor>/.omp/skills/<skill-name>/SKILL.md`, walking from the working directory toward the repository/home boundary

The personal path is the default-profile spelling. Named profiles use `~/.omp/profiles/<name>/agent/skills`; `PI_CODING_AGENT_DIR` and existing OMP XDG roots can also relocate native user data. [OMP config roots and profiles](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md#L237-L268)

OMP also scans `~/.agent/skills`, `~/.agents/skills`, and ancestor project `.agent/skills` / `.agents/skills`. It imports Claude, Codex, OpenCode, GitHub, Claude-plugin, and OMP-plugin skill roots too. Native OMP has highest precedence; skills are deduplicated by name, generally first source wins, while configured custom directories override default-provider copies. [OMP native discovery](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md#6-native-omp-provider-behavior-packagescoding-agentsrcdiscoverybuiltints), [shared `.agent` / `.agents` provider source](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/discovery/agents.ts#L127-L181), and [provider precedence](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md#built-in-skill-providers-and-precedence)

Provider scans are one level deep: `<skills-root>/<name>/SKILL.md`. OMP accepts top-level symlinked skill directories, reads `SKILL.md` through the link, and uses `realpath` to deduplicate the same physical skill exposed from multiple roots. [OMP scanner source](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/discovery/helpers.ts#L325-L410) and [runtime deduplication](https://github.com/can1357/oh-my-pi/blob/main/packages/coding-agent/src/extensibility/skills.ts#L199-L235)

Manual invocation is `/skill:<name> [arguments]` when `skills.enableSkillCommands` is enabled. When the read tool is available, automatic activation exposes `name` and `description` for non-hidden skills to the model, which loads the body through that tool. `skill://<name>` and resource URLs below it are OMP conveniences, not portable skill syntax. [OMP skill runtime](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md#system-prompt-exposure)

OMP is best described as a tolerant Agent-Skills-compatible consumer, not a strict validator. It recognizes `name`, `description`, `globs`, `alwaysApply`, `hide`, and normalized `disable-model-invocation`, preserves unknown metadata, and defaults a missing name to the directory. A description is required for OMP-native, OMP-plugin, GitHub, and custom-directory scans, while some foreign providers are looser. The docs do not assign OMP permission behavior to the standard `allowed-tools` field, nor clear activation semantics to `globs` / `alwaysApply`; do not depend on those fields in shared behavior. [OMP frontmatter behavior](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md#skillmd-frontmatter)

No first-party standalone `omp skill install` command was found. Copying/linking into a discovery root is the direct installation convention; packaged skills can instead arrive through OMP plugins/extensions. The lowest-duplication shared installation is an individual repository-managed link under `~/.agents/skills/<name>`, which OMP natively scans. [OMP plugin installer plumbing](https://github.com/can1357/oh-my-pi/blob/main/docs/plugin-manager-installer-plumbing.md)

### Upstream Pi clarification

Upstream Pi is not OMP. Its native roots are `~/.pi/agent/skills/` and trusted-project `.pi/skills/`, and it also scans user/project `.agents/skills/`. It recursively discovers directories containing `SKILL.md`, manually invokes them as `/skill:<name>`, and explicitly says it implements Agent Skills leniently. OMP does not load `.pi/skills` as its native provider; legacy OMP setting names containing `Pi` gate `.omp` discovery. [Upstream Pi skills documentation](https://pi.dev/docs/latest/skills) and [OMP compatibility note](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md#skills-subsystem)

No first-party core custom-subagent file format was found for upstream Pi. Its official SDK and extension surface lets packages build tools that spawn agents, so any Markdown agent schema comes from the chosen extension and is not a Pi-wide portability target. [Pi extensions](https://pi.dev/docs/latest/extensions) and [Pi SDK](https://pi.dev/docs/latest/sdk)

## Custom subagents are platform adapters

Agent Skills standardizes reusable instructions, not custom-agent definitions. Preserve one conceptual role contract, but render a separate file for each runtime.

### Claude Code custom agents

- Paths: project `.claude/agents/**/*.md`, personal `~/.claude/agents/**/*.md`, or plugin `agents/**/*.md`. Project and personal directories are recursive.
- Format: YAML frontmatter plus Markdown system prompt. `name` and `description` are required.
- Capability fields include `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`, and `initialPrompt`.
- Invocation can be automatic from `description`, requested in natural language, guaranteed for one task with `@agent-<name>`, or used for the whole session with `claude --agent <name>`.
- Subagents normally start with fresh context. They may spawn nested subagents (current default depth: three) unless `Agent` is omitted/denied. Full skill content can be preloaded with `skills`.

[Claude custom-subagent reference](https://code.claude.com/docs/en/sub-agents)

Claude has no Codex-style per-agent `sandbox_mode`. A read-only reviewer adapter should allow only the required read/search tools, omit `Write`, `Edit`, shell tools, and `Agent`, and use `permissionMode: plan` as defense in depth. The allowlist remains essential because parent `acceptEdits` / `bypassPermissions` modes take precedence and parent auto mode ignores an agent's `permissionMode`. `isolation: worktree` isolates a writable checkout but is not a read-only policy. Agent-file symlink behavior is not documented, so generated/copied files or a plugin are safer than relying on links.

### OMP custom agents

- Paths: project `.omp/agents/*.md` and personal `~/.omp/agent/agents/*.md` for the default profile. Named profiles and the same supported environment/XDG relocation mechanisms move the personal agent root. OMP deliberately does not import ordinary `.claude/agents`, `.codex/agents`, or `.gemini/agents` because their schemas differ. Extension/plugin roots may provide OMP-compatible definitions. [OMP agent discovery](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md#filesystem-and-plugin-discovery)
- Format: YAML frontmatter plus Markdown system prompt. `name`, `description`, and a non-empty body are required.
- Capability fields include `tools`, `spawns`, prioritized `model`, `thinking` / `thinking-level`, `output`, `blocking`, `autoloadSkills`, `read-summarize`, `prewalk`, and `advisor`.
- Dispatch occurs through OMP's `task` tool, whose default batch shape supplies shared `context` plus per-agent `tasks`. Nested delegation is controlled by `spawns` and runtime depth policy.

[OMP agent discovery and schema](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md) and [OMP task tool](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)

OMP also has no documented equivalent of Codex's `sandbox_mode = "read-only"`. A skeptic adapter should use the smallest read-only tool allowlist, omit `task`, and avoid a non-empty `spawns` policy. A local OMP 17.2.9 discovery smoke loaded the symlinked adapter with only `read`, `grep`, `glob`, and the runtime-added read-only `yield` tool, with no `task` or effective `spawns` policy. That establishes discovery and the no-delegation tool surface, but an attempted-write rejection remains a separate forward test. An empty `spawns: []` currently normalizes to an absent policy rather than an explicit deny, so omission is clearer and the tool allowlist remains the actual no-delegation control.

## Recommended repository design

1. Keep `skills/<name>/SKILL.md` as the single source and validate its standard fields against Agent Skills. Produce a strictly validated spec-only export only when losing manual-only activation is acceptable; otherwise report that target as unsupported.
2. Install individual skill-directory links, not duplicated copies:
   - Claude Code: `~/.claude/skills/<name> -> <checkout>/skills/<name>`
   - OMP: use `~/.omp/agent/skills/<name>` when installing the complete OMP adapter, including its matching custom agent; `~/.agents/skills/<name>` remains a viable shared skill-only root
   - upstream Pi shared root: `~/.agents/skills/<name> -> <checkout>/skills/<name>`
   - Codex: retain the existing repository-managed Codex installation path.
3. Keep separate custom-agent adapters:
   - Codex TOML with enforceable read-only sandbox
   - Claude Markdown with a strict read/search tool allowlist and no `Agent`
   - OMP Markdown with a strict read-only tool allowlist, no `task`, and no non-empty `spawns` policy
4. Keep the shared `diff-skeptic` prose's semantic reviewer-role lookup instead of hard-coding a platform identifier. `diff-skeptic-reviewer` satisfies Claude/OMP naming needs; the Codex adapter can retain `diff_skeptic_reviewer` until that installed identity is migrated safely.
5. Keep explicit user invocation documentation per runtime: Codex `$skill-name`, Claude `/skill-name`, OMP/Pi `/skill:skill-name`.
6. Forward-test each release with a fresh session: discovery, explicit activation, each client's model-invocation policy (including OMP's catalog hiding and direct-path behavior), relative resources, subagent dispatch, no-delegation enforcement, and attempted-write rejection for the skeptic. Symlinked discovery should be tested even where documented because all three clients evolve quickly.

## Uncertainties and limits

- The Agent Skills standard has no normative symlink contract. Claude and OMP document or expose their own behavior; upstream Pi symlink semantics were not established here.
- Claude documents per-skill entry symlinks, not a symlink replacing the whole skills root, and does not document agent-definition symlinks.
- OMP skill-directory symlinks are source-supported. The local OMP 17.2.9 discovery smoke also established an individual custom-agent file symlink for that release, but this remains runtime evidence rather than a documented cross-version contract.
- OMP preserves standard optional fields it does not understand, but preservation does not imply runtime enforcement.
- OMP's documented `globs` and `alwaysApply` fields lack clear current skill-activation semantics.
- Neither Claude nor OMP exposes the same immutable read-only custom-agent sandbox contract as the existing Codex TOML. Tool allowlists are the available adapter mechanism and require adversarial verification.
- First-party docs and `main` source are fast-moving. Pin minimum tested versions when the port is implemented and rerun the discovery/security fixture against release binaries.
