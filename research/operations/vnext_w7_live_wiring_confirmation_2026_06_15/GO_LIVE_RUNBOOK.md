# GO-LIVE Runbook — W7 ultimate_book (FTMO primary, 1.25% half-Kelly)

Owner GO given 2026-06-15 03:29 UTC (build all 11 + go active in live; gated only on Claude's
correctness verification). This is the exact, auditable flip procedure. DO NOT execute any step until
the PRE-FLIGHT below is fully green.

## PRE-FLIGHT (every item must be GREEN before the flip)

1. **All 11 sleeves registered + contract-clean.** registry.BUILT has 11 entries; `pytest tests/
   ultimate_book` green incl. test_generator_contract (every generator accepts the engine call) and
   every per-sleeve real-oracle parity test.
2. **Full book live-wiring** (read-only, gates off): `run_book.py --once` on FTMO → all decision TFs
   advance, every sleeve runs on live bars, place=False (halt present), 0 orders. M1 vp aux fetch OK.
3. **Order path proven** [RAN]: the router trade_params clears all 3 fail-closed gates
   (test_order_route) AND the live admission sizes a realized unit with risk_pct_override <= the cell
   risk (<= 1.25% nominal half-Kelly). Verify on a live shadow unit that would_unit risk_pct <= 0.0125.
4. **Sizing/governor** confirmed: profile=clean3_w7_measured_nom1p25, kelly_conservative=true (half),
   soft_daily_stop 3%, gross_open_risk_cap 4%, derisk_start 7%. Contract sizes per broker verified
   (no 10x hazard on FTMO).
5. **Kill-switch + halt** behavior tested: ULTIMATE_BOOK_KILL.flag and any halt flag force
   run_cycle(place=False) (launcher) AND open_trade raises RuntimeHaltError (runtime_control.enabled=
   true). Idempotency: each (sleeve,symbol,decision_bar) places once.
6. **Replacement invariant**: selector_v4_apply_to_execution=false (agent_config 745) so the bridge
   does not fail-closed; ultimate_book_disable_broad_selector defaults true.

## THE FLIP (in order)

### Step 1 — enable the triple-gate (config)
In `config/agent_config.yaml` under `gtos_vnext_runtime:` (lines 1118-1120):
```
ultimate_book_enabled: true                 # was false
ultimate_book_apply_to_execution: true      # was false
ultimate_book_live_activation_allowed: true # was false
```
Leave everything else as-is: profile clean3_w7_measured_nom1p25, include_clean3 true (11 sleeves),
kelly_lite true, kelly_conservative true (half-Kelly), drop_w7_symbols true, governor caps as set.

### Step 2 — remove the 3 runtime-halt flags (open_trade enforces these; runtime_control.enabled=true)
```
rm pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag
rm pipeline_state/RESEARCH_RUNTIME_HALT.flag
rm knowledge_base/meta/AUTOSTART_DISABLED.flag
```
(Re-creating ANY of these is the instant hard-stop — see Rollback.)

### Step 3 — arm the kill-switch (ensure absent so the book may place; operator drops it to brake)
```
rm -f pipeline_state/ULTIMATE_BOOK_KILL.flag   # absent = armed/live; present = observe-only
```

### Step 4 — launch FTMO primary ONLY (continuous)
```
cd C:/Users/MSI/Documents/ai-trading-agent
export PYTHONPATH="$(pwd)"
.venv-gtos/Scripts/python.exe run_book.py \
    --profile operator_profile \
    --terminal-path "C:\MT5\FTMO\terminal64.exe" \
    --namespace operator_profile \
    --poll-seconds 60
```
redacted_account follower stays DOWN until both parities are clean (separate launch, redacted_account namespace).

### Step 5 — confirm live
- launcher log line: triple_gate_ON=True halted=False killed=False.
- shadow_logs/ultimate_book_launcher.jsonl: place=True on the next decision-bar advance.
- On the first realized placement: a real FTMO ticket; record first fill + first session.

## SAFETY CONTROLS (live)

- **Instant brake (operator):** `touch pipeline_state/ULTIMATE_BOOK_KILL.flag` → next tick observe-only.
- **Hard stop:** `touch pipeline_state/RESEARCH_RUNTIME_HALT.flag` → open_trade raises, launcher place=False.
- **Governor (automatic):** new entries blocked at -3% intraday; gross open-risk capped 4%; size shrinks
  from -7% toward the -10% wall. Prop rules: 5% daily / 10% max DD.
- **Sizing dial:** 1.25% half-Kelly ONLY. 1.50%/2.00% steps require a fresh owner sign-off — never auto.

## ROLLBACK (instant, no code change)
`touch pipeline_state/RESEARCH_RUNTIME_HALT.flag` (and ULTIMATE_BOOK_KILL.flag) → all sends stop
immediately (open_trade RuntimeHaltError + launcher observe-only). Then set the 3 gate flags back to
false to fully disarm. Open positions are unaffected by the halt (halt blocks NEW sends, not management
— manage/flatten via the terminal or the execution engine if needed).
