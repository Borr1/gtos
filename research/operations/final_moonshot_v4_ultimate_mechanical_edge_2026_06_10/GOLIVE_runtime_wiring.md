# GOLIVE — Runtime wiring (DEFAULT-OFF) + staged config patch

Track: **Runtime wiring (default-off) + staged config patch**. Status: **staged / prepare-don't-flip**.
Nothing here places a live order or connects to a broker. The system stays hard-halted; halt files
remain the physical control. New behaviour ships behind the repo triple-gate, defaulting OFF.

This document is the wiring map + apply instructions for the human owner. It covers (1) what is WIRED
default-off and tested now, and (2) the STAGED config patch awaiting owner apply.

---

## 1. What is WIRED now (default-off, tested, no broker)

### 1.1 The runtime bridge — `ultimate_book_runtime_bridge.py` (NEW, route-dir, default-off)
The bridge from the deploy book to execution, mirroring the established repo pattern
`src/components/gtos_vnext_runtime.evaluate_vnext_selector_v4_admission` (line 15187). It is a pure
decision module: NO network, NO MT5, NO broker, NO order placement.

Entry point: `evaluate_vnext_ultimate_book_admission(config, intents, governor_state, account, limits)`
returning an `UltimateBookAdmissionDecision` (JSON-serializable; no broker/order fields).

Flow (mirrors selector_v4's enabled/apply_to_execution/would_action semantics):
1. Read the `ultimate_book_*` block from `config["gtos_vnext_runtime"]` with FAIL-CLOSED defaults
   (a missing/partial config bears NO risk).
2. **W7 tick-true symbol drop** — `filter_w7_dropped_symbols` removes `HEATOIL_c` + `NATGAS_cash`
   intents (their modeled EV was a cost-map artifact; real spread swamps the stop). Default on.
3. **Shadow projection** — always computes what the book WOULD size (`would_units`,
   `would_total_risk_pct`) via `ultimate_book_live_package.admit_and_size`, so the owner can dry-run
   the book in live telemetry BEFORE any flip. Leak-free; no broker.
4. **Replacement-invariant guard** — if `ultimate_book_disable_broad_selector` is true (default) AND
   the broad V4 selector is still apply-to-execution (`selector_v4_enabled` AND
   `selector_v4_apply_to_execution`), the bridge FAILS CLOSED (`fail_closed_broad_selector_still_live`)
   and bears zero risk. Belt-and-braces so the two selectors can never both reach execution.
5. **Triple-gate** — realized risk (`runtime_effect_now=True`, `realized_units` populated) is emitted
   ONLY when `ultimate_book_enabled` AND `ultimate_book_apply_to_execution` AND
   `ultimate_book_live_activation_allowed` ALL true (and the broad selector is clear). Any gate off →
   shadow-only, zero realized risk.

The governor runs inside `admit_and_size`: soft -3% daily stop, max-DD de-risk band (shrink from -7%
into the -10% wall), 4% gross open-risk cap, outer operator circuit breaker, fail-closed on
NaN/invalid state. The bridge passes the live `GovernorState` straight through (no duplication).

### 1.2 Deploy-book module additions — `ultimate_book_live_package.py` (route-dir, edited)
Edited the route-dir deploy module only (permitted; not production src). Additions:
- **WAVE-7 NOMINAL dials** (owner-chosen sizing; clean_3 11-sleeve W7 final book):
  - `clean3_w7_measured_nom1p25` = 1.25% nominal (first cycle, half-Kelly) — **the default**.
  - `clean3_w7_growth_nom1p50` = 1.50% nominal (after first account clears; handset Kelly + stress_derisk).
  - `clean3_w7_ceiling_nom2p00` = 2.00% nominal (hard ceiling; not a default).
  Constants `CLEAN3_W7_FIRST_CYCLE_PROFILE / _GROWTH_PROFILE / _CEILING_PROFILE`. P(both) base/fwd/
  1.5x-stress stats are the LOCKED `INTEG_W7_FINAL_RESULT.json` `two_account_final` balanced pairs.
  These carry the **nominal** dial directly; the Kelly-lite reshape is applied as a runtime multiplier
  in `size_correlated_units` (deploy WITH `include_clean3=True` + `kelly_lite=True`).
- **`W7_DROPPED_SYMBOLS`** frozenset + **`filter_w7_dropped_symbols(...)`** helper (tick-true drop).
- `describe_book()["clean3"]["w7_final"]` self-description (dropped symbols, dials, kelly bins) for
  the go-live audit.
Sleeve registry is UNCHANGED (map-don't-kill: HEATOIL_c/NATGAS_cash stay in the documented universe;
the drop happens at candidate generation in the bridge).

### 1.3 Candidate generation → admit_and_size → execution risk%
The bridge consumes a `Sequence[TradeIntent]` (one sleeve firing on a decision-day for a symbol;
leak-free decision-bar facts only) and returns `SizedUnit` risk% per trade. In production, intents are
sourced from the locked sleeve rules (KB3_live_package.md §2.2 #3); the bridge does the admission +
governor + confidence/Kelly-lite sizing. Execution (`src/components/execution.py` /
`execution_manager_v4.py`) consumes `realized_units[*].risk_pct_per_trade` — its order path is
unchanged; only its admission/size INPUT now comes from the book module instead of the broad selector.
The module emits NO orders.

### 1.4 Tests — `test_ultimate_book_runtime_bridge.py` (NEW, 23 tests) + existing 78 = 101 pass
```
ROOT=/Users/borr/Documents/gtos/repo/ai-trading-agent
ROUTE=$ROOT/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10
PYTHONPATH=$ROOT:$ROUTE /usr/bin/python3 -m pytest \
  $ROUTE/test_ultimate_book_runtime_bridge.py $ROUTE/test_ultimate_book_live_package.py -q
# -> 101 passed
```
Bridge tests cover: default-off / empty-config fail-closed; the triple-gate (each single gate off →
no effect; all three → admit); the broad-selector replacement invariant (fail-closed when broad still
live; OK when broad enabled-but-not-apply; guard skipped when owner disables the requirement); W7
symbol drop (helper + bridge, toggle); governor pass-through (soft daily stop / circuit breaker / NaN
fail-closed all block while gated-on); unknown-profile fail-closed; W7 dial presence/monotonicity;
JSON-serializable no-broker-field decision; describe_bridge no-broker contract.

---

## 2. STAGED config patch — `STAGED_disable_broad_selector.patch` (NOT applied)

A reviewed, ready-to-apply patch to `config/agent_config.yaml`. **It is NOT applied.** The live config
still has the broad selector ON (`selector_v4_apply_to_execution: true`) and NO `ultimate_book_*` block.

The patch makes exactly two changes inside the existing `gtos_vnext_runtime:` block:
1. **Disable the broad losing selector**: `selector_v4_apply_to_execution: true → false` (the single
   most important pre-live change — the broad pool is -0.25R/fill native; go-live is a REPLACEMENT).
   `selector_v4_enabled` / `_live_activation_allowed` are left untouched (the broad selector can still
   run in shadow/telemetry; it just can't reach execution).
2. **Add the default-OFF `ultimate_book_*` block** (every gate false; profile = the W7 first-cycle
   1.25% nominal half-Kelly dial; `include_clean3: true`; `drop_w7_symbols: true`).

### Apply (owner, when authorized — Phase A of GO_LIVE_SEQUENCE.md)
```
cd /Users/borr/Documents/gtos/repo/ai-trading-agent
git apply --check research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/STAGED_disable_broad_selector.patch  # dry-run (verified clean)
git apply        research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/STAGED_disable_broad_selector.patch  # apply
```
Reverse (rollback): `git apply -R <patch>`. The patch was generated against the current HEAD config
and verified with `git apply --check` (applies cleanly, not applied).

> NOTE: applying the patch only DISABLES the loser and ADDS the default-off block. It does NOT enable
> the book (all three `ultimate_book_*` gates stay false). Enabling live order placement is a separate,
> deliberate owner action gated on broker/runtime authority (Phase C). Even after the patch, the
> bridge bears zero risk until the owner flips all three gates AND the halt files are cleared.

---

## 3. READY vs BLOCKED

READY (done, tested, in-our-control):
- Runtime bridge built default-off, triple-gated, broker-free; 23 unit tests (101 total) green.
- W7 final-book dials (1.25/1.50/2.00 nominal) + tick-true symbol drop wired into the deploy module.
- Staged config patch (disable broad selector + default-off block) generated, normalized, and
  `git apply --check`-verified; live config untouched.

BLOCKED (needs owner / broker / VPS — NOT in this track's scope):
- **Owner apply** of the staged patch (Phase A authorization).
- **Production-src integration** of the bridge call into `gtos_vnext_runtime` and the candidate
  generators → `execution.py`. Per guardrails this prep stages the bridge in the route dir; folding
  the call into production src is a reviewed follow-up the owner authorizes (it changes the live
  decision path). The bridge function signature and the config keys are final and stable.
- **Broker / runtime authority** (the REAL gate, per CLAUDE.md + ULTIMATE_GO_LIVE_DOSSIER.md):
  hard-halt row-level forensic join, V3-vs-live authority gap audit, dual-broker audit,
  production-return dossier sign-off. The system is hard-halted; this must be cleared, not bypassed.
- **VPS provisioning** + MT5↔FTMO connection (`siliconmetatrader5 @ localhost:8001`), live
  GovernorState feed, live-vs-replay parity monitoring (GO_LIVE_SEQUENCE.md Phase B/C).

---

## 4. Files (this track)
- `ultimate_book_runtime_bridge.py` — NEW default-off runtime bridge (no broker).
- `test_ultimate_book_runtime_bridge.py` — NEW, 23 tests.
- `ultimate_book_live_package.py` — EDITED: W7 nominal dials, `W7_DROPPED_SYMBOLS` +
  `filter_w7_dropped_symbols`, `describe_book` w7_final section. (78 existing tests still green.)
- `STAGED_disable_broad_selector.patch` — STAGED (not applied) config patch.
- `GOLIVE_runtime_wiring.md` — this document.
