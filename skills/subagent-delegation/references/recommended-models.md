# Recommended model tiers

| Runtime | Apprentice | Technician | Engineer | Architect |
| --- | --- | --- | --- | --- |
| Claude Code | `haiku@high` | `sonnet@medium` | `opus@medium` | `opus@high` |
| Codex | `latest Sol@low` | `latest Sol@medium` | `latest Sol@xhigh` | `latest Astra@xhigh` |

The table is the source of recommendations for Setup and Forge. Configure any model and effort the active runtime offers. In Claude Code, save an Agent-tool alias (`sonnet`, `opus`, `haiku`, or `fable`) or `inherit`. Also offer `haiku@xhigh` when the live model list shows support. In Codex, resolve a `latest` recommendation to the newest plain release of its model family in the live model list. Skip variants such as `-mini` and save the exact model ID.

## Record what the user reviewed

Use a `Reviewed model recommendations` row in the Forge settings table at the chosen scope. For the active runtime's cell, copy the four published values from the table above, in order, as comma-separated plain text. Copy `latest` family labels verbatim. Record the recommendations even when the user keeps or chooses other models. This row is only for comparison against later editions of the installed table.

## Check in Forge

Use the installed table above and the same baseline settings sources used for tier resolution. Before applying run overrides, find the highest-priority saved value for each built-in tier for the active runtime. Compare only at scopes supplying at least one of those values. Use each scope's own `Reviewed model recommendations` cell and compare the entries for the tiers it supplies, ignoring Markdown code formatting and surrounding whitespace.

When a recommendation differs from the corresponding reviewed entry, show the affected tier, scope, and previous and current recommendations. For older settings with no complete reviewed cell, report verifiable differences in the saved model or explicit effort. Compare fixed aliases and known model families directly. Compare exact IDs for `latest` recommendations only when the live model list is available. Skip `inherit` values and the Haiku alternative offered above. Describe legacy values as differing from the current recommendations. A saved value alone provides no history of recommendations.

Combine differences into one user-facing notice before agents start. If Setup is installed, invite the user to review model recommendations at the affected scope using its registered command, including any plugin prefix. Continue the current run using its resolved settings. Check once per Forge invocation when the installed reference is available. Keep the check read-only.
