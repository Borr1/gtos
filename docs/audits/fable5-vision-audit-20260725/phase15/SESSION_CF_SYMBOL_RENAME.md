# Session CF — the broker rename event: repair + watchdog (wave 15, B2350–B2399)

Read first: `phase15/receipts/FTMO_SYMBOL_RENAME_EVENT_20260731.md` (the event — measured on
the live tree this morning; your charter), `phase15/OD_HISTORICAL_FIRST_SCALING.md`,
`phase13/SESSION_BB_SLEEVE_SUPPLY_RESULT.md` (the quiet-book alarm this event slips past),
`phase13/SESSION_BC_COMMAND_CENTER_RESULT.md` (the watchdog's home — it reads truth from
process/broker, never from what was typed), CLAUDE.md §3–§4 (H1 before every `src/` edit;
the token binds `config/agent_config.yaml` AND both live profiles' bytes). Owner authority:
OD-HISTORICAL-FIRST and the standing directives.

**The objective in one sentence:** the four muted FTMO index members
(`SPX500→US500.cash`, `UK100→UK100.cash`, `GER40→GER40.cash`, `JP225→JP225.cash`) resolve
again through a minimal, account-scoped mapping, and the estate gains a watchdog so the next
broker rename ALARMS within one monitor cycle instead of muting members silently.

## Work orders

**CF-1 — Find the resolution layer and prove the failure shape.** Trace exactly where a
spec's `on_surface` name becomes a broker symbol for live generation (`bar_provider.py`,
`bridge.py`, `launcher.py` — the `USOIL_cash → USOIL.cash` conversion proves a mapping
exists; find it). Then prove what a mute member looks like TODAY on mainline: is the bar
fetch failure logged loudly, once, or not at all? Quote the exact log line (or its absence)
— that is the watchdog's justification. Do NOT touch the VPS; the host lineage's copy of the
layer is readable from the read-only export and `CARRIED_STATE.json` history.

**CF-2 — The minimal repair, at the right layer.** An account-scoped symbol alias map
(canonical → broker) covering the four renames, default-off or config-byte-free if the layer
allows (the `--tags`-argument pattern); if the honest home is a token-bound profile yaml,
BUILD the edit + the re-mint plan instead of avoiding it — the token re-mint is already due
before 2026-08-05, and the repair rides that ceremony. Identity proof: with the map empty,
behaviour is byte-identical to today; with the map on, ONLY the four names change
resolution. H1/R2 membership check on every file; AR's `DEFAULT_CONFIG`/AST hardening on any
new key. Consider and state (don't just implement): should the alias also apply to
position ADOPTION and exit management paths (`book_owner`'s `_manageable_pairs`), so a
position opened under an old name is still managed after a rename mid-hold? That gap is
worse than the generation gap and today it is untested.

**CF-3 — The rename watchdog.** A command-center/monitor check that, every cycle, diffs the
terminal's symbol tree (`symbols_get`) against the ARMED surfaces' resolved broker names per
account, and raises a named alarm listing exactly which members went unresolvable. It must
be read-only, cheap, and fire within one cycle of a rename. Wire it into the monitor page
the way BC's checks are wired (truth from the broker, never from what was typed). Test with
a synthetic tree diff.

**CF-4 — Refresh the vendored broker truth.** Re-vendor the symbol-spec comparison from the
live trees (the orchestrator can pull a fresh export if you write the exact read-only probe
— hand it over rather than touching the VPS yourself), stamp the rename event's date, and
mark the 2026-07-26 artifact superseded. Also state which RESEARCH artifacts key on the
bare names (the 24-symbol surface constant, caches, exports) and whether any needs a
same-name alias note — replay reads its own sealed exports and must NOT be renamed.

**CF-5 — The ceremony page.** One page for the orchestrator: the exact transfer set, the
re-mint sequence it rides (flatten-check → flags held → edit → re-mint token binding the new
digest → restart → PROVING log lines — the four members generating or at least resolving —
→ release), rollback, and the FN statement (unaffected today; the watchdog covers it from
day one anyway).

## Done means

Result doc findings-first + receipts under `phase15/receipts/`, blocks B2350–B2399, scoped
A/B green vs the ZERO baseline (12,403) with the tool-emitted `gtos-ab-receipt-v1` fence,
honest "what I got wrong", handoff = the ceremony page. Never touch the VPS; never run
broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or any R2-bound path (build profile edits as PAYLOADS
for the orchestrator's ceremony, never apply them). Sessions CD and CE run in parallel —
keep compute light.
