# Codex inspector installation and test results

> Historical record. Runtime observations, installation state, and task authorization below describe the original work only. For current support and setup, see [compatibility](../compatibility.md) and [installation](../installation.md).

Date: 2026-09-14

## Installed candidate

The repository's Codex inspector definition is linked from the personal Codex agent directory. Installation preflight checked for an unmanaged destination; none existed. The installed link target was verified. The candidate requests a read-only filesystem, no approval escalation, disabled child delegation, and disabled apps by default. Workflow routing remains unchanged until effective restrictions are verified.

## Configuration checks

Repository validation passed for six skills and four native agent definitions. All 40 unit tests passed, including a regression check that the validator rejects writable or delegation-enabled inspector settings. These checks do not establish live runtime enforcement.

## Runtime results

The native delegation call with `agent_type: inspector` returned `unknown agent_type 'inspector'` in the current session after installation. No child started.

| Check | Result |
| --- | --- |
| Installed definition and target link | Passed |
| Read assigned disposable artifact | Blocked: role unavailable |
| Filesystem write denial | Blocked: role unavailable |
| Further delegation unavailable | Blocked: role unavailable |
| External mutation tools unavailable or denied | Unverified |
| Parent full-access override behavior | Unverified |

The current parent session has full filesystem access. Configured read-only defaults must not be treated as proof that its children have a restricted filesystem. Disabling apps by default also does not prove that inherited per-app overrides, MCP servers, or browser tools are restricted.

## Resume

After the native runtime loads the new role, spawn `inspector` with fresh context. Read a disposable input file, inspect effective permissions and tool availability, and test only disposable filesystem writes if the controlling instructions permit them. Count a voluntary instruction refusal as inconclusive, not a runtime denial. Inspect external tool availability without mutating any real service. Never substitute an ordinary subagent and report it as an inspector test.

This is a Codex candidate installation, not completion of the cross-runtime spec. Claude Code and OhMyPi adapters, distribution integration, external-tool enforcement, and workflow routing remain pending.
