# Session CF — the broker rename event: repair + watchdog (wave 15, B2350–B2399)

Findings first. Nothing here touched the VPS, ran a broker-capable script, or edited
`config/agent_config.yaml`, `config/profiles/redacted_account.yaml`, or any R2-bound path. The R2 drift
count was **1 before and 1 after**, and it is the documented B905 standing hazard
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`), read after
`git lfs checkout` per the H1 LFS caveat. Nothing was armed, disarmed, resized or restarted.

---

## 0. The findings, in the order they matter

**F-CF-1 — There was no rename. FTMO has served `.cash` index names for as long as the estate has
any evidence, the four "muted" members were never mute, and the armed book was never degraded.**
[MEASURED]

The 2026-07-31 probe asked both terminals for `SPX500`, `UK100`, `GER40`, `JP225`, `NAS100`, got
`symbol_info = None` from FTMO, and read that as an overnight rename. Those five are GTOS
**canonical** names — the broker-agnostic registry vocabulary (`sleeves/registry.py` →
`spec.on_surface`). They have never been FTMO broker names. Three independent places in this
repository, all written well before today, say so and agree exactly:

| where | what it says |
|---|---|
| `config/profiles/operator_profile.yaml` (the live profile) | `SPX500→US500.cash`, `UK100→UK100.cash`, `GER40→GER40.cash`, `JP225→JP225.cash`, `NAS100→US100.cash` |
| `src/components/ultimate_book/symbol_map.py:8` (the resolver's own docstring) | `FTMO : SPX500 -> US500.cash, US30_cash -> US30.cash, …` |
| `v4_timewarp_simulated_live_research_loop.py` → `FTMO_SYMBOL_MAP` (the research layer) | the same five mappings, verbatim |

And the broker's own answer settles it. In the read-only **2026-07-25** export
(`09_mt5_api/ftmo_symbols_get.jsonl`, 167 symbols, pulled `2026-07-25T23:28:21Z` from login
531325516 on FTMO-Server3, `connected: true`) — **six days BEFORE the alleged rename** — every bare
name was already absent and every `.cash` target already present:

| canonical | bare in tree 2026-07-25 | resolves to | resolved name in tree 2026-07-25 |
|---|---|---|---|
| `SPX500` | **no** | `US500.cash` | **yes** |
| `UK100` | **no** | `UK100.cash` | **yes** |
| `GER40` | **no** | `GER40.cash` | **yes** |
| `JP225` | **no** | `JP225.cash` | **yes** |
| `NAS100` | **no** | `US100.cash` | **yes** |

**The same export is its own control.** redacted_account, probed at the same instant by the same code,
*does* carry bare `SPX500/UK100/JP225` and carries **no `.cash` symbol at all** — which is exactly
what the two profiles encode (`redacted_account.yaml`: `SPX500→SPX500`, `GER40→GER30`). One export, one
moment, two brokers, opposite answers, both matching their own profile. A probe artifact cannot
produce that; a genuine naming difference between the two brokers does.

Swept across the **full declared registry** — 34 sleeves (`BUILT` 11 + `CANDIDATE_BUILT` 9 +
`MARKET_EXPANSION_BUILT` 14), 137 generation slots, 48 distinct canonical symbols — resolved
through each account's real profile against each broker's real tree:

| account | slots | resolved OK | **resolved-but-absent** | profile-unsupported |
|---|---:|---:|---:|---:|
| FTMO | 137 | 135 | **0** | 2 |
| redacted_account | 137 | 104 | **0** | 33 |

**Zero unresolvable on either account.** Not one member of any sleeve — armed or not — asks for a
symbol its broker does not serve. Receipt: `phase15/receipts/CF_SYMBOL_RESOLUTION_V1.json`.

**F-CF-2 — The defect the event was reaching for is real, and it is the SILENCE, not the names.**
[MEASURED, by direct read]

Had a rename actually happened, nothing would have said so. The generation path swallows it whole:

- `bar_provider.py:120-125` — `get_closed_bars` wraps the fetch in a bare
  `except Exception: return [], []`;
- `book_engine.py:563` — `if not bars or not enough(bars, spec.cluster): continue`.

No log line. No counter. No skip record. A member whose broker symbol vanishes generates nothing
**forever**, while the supervisor heartbeat, the launcher cycle records, the equity read and every
panel of the command center stay green. The exact log line the commission asked me to quote **does
not exist** — that absence is the watchdog's justification, and it is the strongest form the
justification could take.

The neighbouring condition *is* reported, which is what made the gap easy to miss:
`book_engine.py:526-541` counts a canonical name with no instrument config as
`broker_unsupported_symbol_slot_count` and appends a `profile_missing_instrument_config` skip.
**Profile-missing is instrumented; broker-missing is not.** The watchdog keeps the two apart —
folding them together would have redacted_account raising a broker emergency every cycle for its 33
standing profile gaps.

**F-CF-3 — The repair the commission scoped would have been a no-op, and building it would have
cost an unnecessary token re-mint on two armed, funded accounts.** [MEASURED]

CF-2 asked for an account-scoped alias map covering the four renames, and said that if its honest
home was a token-bound profile yaml, to build the edit and ride the re-mint ceremony due before
2026-08-05. That map is `SPX500→US500.cash`, `UK100→UK100.cash`, `GER40→GER40.cash`,
`JP225→JP225.cash` — **which is byte-for-byte what `config/profiles/operator_profile.yaml`
already contains.** Applying it would at best change nothing and at worst double-map. And the
profile is one of R2's 43 bound paths *and* is bound by the activation token, so shipping it would
have required a config edit + token re-mint + worker restart against a live book carrying open
authority — a real operational risk taken for a change with no effect.

**The deliverable here is the ceremony that does NOT happen.** `phase15/CF_SYMBOL_WATCHDOG_CEREMONY.md`
transfers code and tests only: no config byte moves, no profile byte moves, the token digest is
unchanged, and no book needs restarting for the watchdog to be useful.

**F-CF-4 — The adoption gap is real, but the premise about it is backwards: the path with the
worse consequence already had the better detection.** [MEASURED, behaviourally pinned]

The commission flagged mid-hold rename — "that gap is worse than the generation gap and today it is
untested" — as the thing to consider. Measured:

- **The gap is real.** `_open_book_positions_by_canonical` (`book_owner.py:3063-3071`) builds its
  broker→canonical map from the **current** profile, so a position still carrying the old broker
  name matches no canonical symbol. It reaches neither the per-pair comment route nor the leftover
  safety net at `:2290`, so it is not adopted and not exit-managed.
- **But it is not silent.** `_alert_out_of_universe` (`:2353-2385`) exists for exactly this shape —
  a W7-magic position whose broker symbol is outside the currently-resolved manageable set — and it
  raises a log warning, an operator card **and** a `summary["out_of_universe"]` row, once per
  ticket. Its own docstring names the consequence: such a position *"would silently ride the broker
  SL/TP only."*

So the asymmetry runs the other way: **generation had the quieter failure and no alarm; adoption
has the worse failure and a working alarm.** Pinned behaviourally in
`tests/ultimate_book/test_symbol_rename_adoption_gap.py` (3 tests, through `manage_open_positions`,
with the current-name control).

**And the answer to "should the alias also cover adoption" is NO, on the evidence.** Making an old
broker name resolve again would have the book *manage* a position on a symbol the terminal no
longer serves: every `get_tick(old_name)` fails, so the time stop, trail/BE moves, scale-outs and
TP edits would run against absent prices — worse than not managing it. Per H8 the broker-side SL/TP
set at entry (`execution.py:3488`) survives regardless, so the position rides its hard stop rather
than being naked. The correct response is the operator ceremony the alert already exists to
trigger: close it, or re-adopt it deliberately under the new name.

**F-CF-5 — No research artifact needs a rename or an alias note.** [MEASURED, by direct read]

| artifact | keys on | verdict |
|---|---|---|
| `GTOS_24_SYMBOL_SURFACE` (`v4_timewarp…:251-278`) | **canonical** (`GER40`, `SPX500`, `NAS100`, `UK100`, `JP225`) | correct as-is; `FTMO_SYMBOL_MAP` sits beside it and does the crossing |
| bar archive `data/`, `data/historical_2026/` | **canonical** (`NAS100_H4.csv`, `GER40_H4.csv`) | correct as-is |
| tick archive `vps-ticks-20260726/ftmo/` | **broker, underscore form** (`FTMO_AUS200_cash_ticks_*`) | already bridged — `spread_model.py:328-333` tries `.cash`↔`_cash`↔bare |
| sealed replay exports | their own sealed names | **must not be renamed** (H1/H4) |

Replay reads its own sealed exports and carries its own FTMO map; renaming anything there would
break seals for no gain.

---

## 1. Delivered

| artifact | what it is |
|---|---|
| `src/components/ultimate_book/symbol_resolution_watch.py` | the watchdog core — pure, no MT5 import, no I/O; `build_slots` + `watch` + `rename_candidates` |
| `scripts/gtos_command_center.py` → **panel 6** | wired into the operator page; reads each profile **from the export** (host truth) and each tree from the broker's own `symbols_get()` |
| `tests/ultimate_book/test_symbol_resolution_watch.py` | 17 tests — synthetic rename, severity split, fail-closed, and the false-alarm regression pinned on live profiles |
| `tests/ultimate_book/test_symbol_rename_adoption_gap.py` | 3 tests — the mid-hold gap and its existing alarm, through `manage_open_positions` |
| `phase15/receipts/CF_SYMBOL_RESOLUTION_V1.json` | the full sweep + the verdict on the event |
| `phase15/receipts/BROKER_SYMBOL_TREE_20260725.json` | vendored name surface, both accounts — the test fixture and the refreshed broker-truth baseline |
| `phase15/receipts/cf_resolution_probe.py` | regenerates both of the above from the export |
| `phase15/receipts/cf_revendor_symbol_tree_probe.py` | **CF-4's re-vendor probe, for the orchestrator** — three read-only MT5 calls, every mutating name asserted absent at run time; CF wrote it and did not run it |
| `phase15/CF_SYMBOL_WATCHDOG_CEREMONY.md` | the transfer page — code + tests only, no config byte, no token re-mint |
| `phase15/receipts/SESSION_CF_AB_RECEIPT.md` | the scoped A/B, tool-emitted |

### How the watchdog behaves

Per cycle, per account: resolve every declared sleeve's `on_surface` through
`symbol_map.build_broker_symbol_resolver` — **the same crossing `book_engine.py:543` fetches bars
with** — and diff the resolved names against the broker's own `symbols_get()` tree.

- an armed member unresolvable → **STOP**, naming sleeve, canonical, resolved name, and (via
  `rename_candidates`) what the broker offers instead;
- an unarmed member unresolvable → **ALERT**;
- **tree unreadable or empty → UNCHECKED, never CLEAN.** A terminal that answers `symbols_get()`
  with nothing is evidence the read failed, not evidence every symbol vanished;
- unknown armed set → every sleeve treated as armed, so it can only over-report;
- profile-unsupported reported **separately**, never as a rename.

It proposes names; it never rewrites a profile. A real rename repair is a token-bound profile edit
and therefore an owner ceremony.

---

## 2. What I got wrong

**I built the module with a hole in exactly the property it exists to guarantee, and my own
hostile-case test caught it.** In the first version, a resolver that *raised* set
`profile_supported=False`, which `watch()` skips — so a slot whose broker name could not be
determined was dropped from the diff instead of alarmed. A watchdog that goes quiet when
resolution breaks is the failure it was written to end.
`test_a_resolver_that_raises_cannot_mute_the_watch` failed on the first run; the fix keeps such a
slot in the diff with `broker: None`, which can never be in a tree, so it reports unresolvable.
Worth stating plainly: the fail-closed principle was in the docstring before it was in the code.

**I over-read `rg -rn` output early on** and briefly took every `build_broker_symbol_resolver` call
site to be a function named `n` — `-r` consumed the `n` as a replacement string. It changed no
conclusion (I read the file directly), but it is why the first call-site list looked wrong.

**On the commission itself:** I could not deliver CF-2 as scoped, because the thing it asked me to
build already exists in the file it would have been added to. I have said so with the measurement
rather than building a redundant map, and CF-1, CF-3, CF-4 and CF-5 are delivered in full.

---

## 3. What this leaves open

1. **`[UNVERIFIED]` for today's host.** Every broker fact here is the 2026-07-25 export plus the
   event receipt's own 2026-07-31 statement of what FTMO serves now. CF does not touch the VPS.
   The re-vendor probe closes this the next time the orchestrator runs an export — and the
   watchdog then reads the fresh tree with no code change.
2. **The generation-path silence is detected, not fixed.** Panel 6 catches a rename from *outside*
   the book. Making `book_engine.py:563` itself distinguish "no bars because the symbol is gone"
   from "no bars because it is a holiday" is a change to an armed hot path and is filed, not taken.
3. **The mid-hold adoption gap stays open by design** (F-CF-4). It is alarmed, not repaired, and
   the repair is an operator decision per position.
4. **`BROKER_SYMBOL_SPEC_COMPARISON.json` is absent from this tree**, not merely stale — the
   2026-07-26 path in CLAUDE.md §4 (`research/operations/vps_broker_truth_2026_07_26/`) does not
   exist at HEAD; the file lives in git history at `1b52e4b6b` and its data survives in the export.
   `BROKER_SYMBOL_TREE_20260725.json` is the name-surface replacement; the re-vendor probe produces
   the full spec successor.

---

## 4. Handoff

**`phase15/CF_SYMBOL_WATCHDOG_CEREMONY.md`** — and its first line is that there is no ceremony to
perform on the books. The transfer is code and tests; no config byte, no profile byte, no token
re-mint, no restart required. The one thing the orchestrator is asked to run is the read-only
re-vendor probe, at its convenience, on the next export.

**redacted_account statement:** unaffected today and structurally unaffected by this class of event —
its profile maps the same canonical names to its own bare names, and its tree carries them. The
watchdog covers it from day one on the same terms as FTMO, and its 33 profile-unsupported slots are
reported as the standing configuration fact they are, never as a broker alarm.
