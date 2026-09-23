# VPSOP — Full-context bootstrap for the VPS Claude (track findings)

Track: Full-context bootstrap for the resident VPS Claude operator.
Posture: PREPARE/OPERATE-DON'T-EXCEED. No production `src/` or `config/agent_config.yaml` live-behaviour
change. Deliverable is a doc only; nothing places an order or connects a broker.
Date: 2026-06-15. Dev surface: this Mac. Deliverable consumed on: the VPS.

## Deliverable

`CLAUDE_VPS_BOOTSTRAP.md` (route dir) — the read-first index + condensed-but-complete brief so a fresh
Claude session on the VPS operates with full continuity. It is self-sufficient: it folds in the
load-bearing content of every source so the VPS Claude is not blind even before opening the pointers.

## Bootstrap outline (13 sections)

0. **THE ONE GUARDRAIL** — PREPARE/OPERATE, never EXCEED; the 3 halt flags = physical control; the
   triple-gate (default-off); full authority for correctness/health/repair/learning BOUNDED by the
   risk dial (1.25→1.5%, ceiling 2.0%) + governor + halt files + FTMO rules.
1. **READ-FIRST INDEX** — 15-row ordered table (scorecard → dossier → W7 build → go-live package →
   sequence → runbook → dual-MT5 → charter → grand vision → VPS package → deploy module → bridge →
   persistent memory → repo doctrine → KB7 evidence).
2. **METHOD DOCTRINE** — no-averages / per-trade-intelligence / build-and-improve / forward-validate /
   leak-free / size-by-confidence / parity-ledger-is-truth / order-flow-not-required (verbatim, binding).
3. **PROGRAM ARC** — the pivot (small gold sleeve → 11-sleeve substrate book) + waves W0–W7 with the
   one-line decisive result of each; MATURE-research status.
4. **FINAL DEPLOY BOOK + SIZING DIAL** — clean_3 11 sleeves minus {HEATOIL,NATGAS}; per-symbol tick
   floors; the 3-stage dial table (1.25 / 1.50 / 2.00) with P(both) / DD-breach / daily-breach; the
   replacement invariant; the two entrypoints (`admit_and_size`, `evaluate_vnext_ultimate_book_admission`).
5. **DUAL-MT5 ARCHITECTURE** — FTMO PRIMARY / redacted_account FOLLOWER; two LOCAL terminals (bridge is
   dev-only); flow; the two parity ledgers; cross-broker hazards (symbol/spec, spread, timezone, margin).
6. **YOUR CHARTER** — authority + the one bound; continuous duties (monitor/repair/learn/verify); the
   repair watchlist (timezone/sequence/null/missing-param/LFS/spec); escalation; startup self-check.
7. **GO-LIVE FLIP SEQUENCE** — Steps 0–10 (DONE / OWNER-APPLIES / BLOCKED); the order-path control
   chain; kill-switch; safe resting state.
8. **FAILURE-MODE WATCHLIST + INCIDENT LADDER** — governor limits; SEV-1..4 table; the system-specific
   top hazards (chronological/timezone, null intel, LFS-missing, exit-honesty, correlated-unit collapse,
   dropped energy legs).
9. **SCORECARD AS LOOP CONTROLLER** — 6 dims; current grades D1–D5 green/A, D6=C (authority gate only);
   keep the compounding loop alive on live trades.
10. **CURRENT VERIFIED STATE** — 136 tests pass, parity_ok=True, pre-flight exit 0, 3 halt flags
    present, 0-diff production; plus the exact reproduce-on-VPS commands.
11. **MT5 CONTRACT** — the `MT5Interface` ABC method list to mirror (Step-7 promotion target).
12. **ORDERED POINTER LIST** — every key artifact grouped (authority/go-live/architecture/deploy
    code/locked MC/staged patches/KB7/persistent-memory/repo-doctrine).
13. **ONE-PARAGRAPH BOOT SUMMARY** — the whole system in one paragraph for a cold start.

## Verification (reproduced this session, none fabricated)

- Deploy test suite: **136 passed** via `/usr/bin/python3` pytest
  (`test_ultimate_book_live_package.py` + `test_ultimate_book_runtime_bridge.py` +
  `GOLIVE_vps_deploy/tests/test_golive_vps_package.py`).
- `GOLIVE_preflight_verify.py` → **exit 0** (PASS; broad-selector WARN advisory by design).
- All 3 halt flags present: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`,
  `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, `knowledge_base/meta/AUTOSTART_DISABLED.flag`.
- `MT5Interface` ABC contract confirmed in `src/mt5/mt5_interface.py` (connect/disconnect/is_connected/
  get_tick/get_candles[_range]/get_ticks_range/get_positions/get_account_balance/get_account_equity/
  get_margin_mode/order_send/get_history_deals).
- Sizing/parity numbers transcribed from `INTEG_W7_FINAL_RESULT.json` /
  `PORTFOLIO_BUILD_W7_FINAL.md` / `ALLOCATION_PROFILES` in `ultimate_book_live_package.py` (not
  re-simulated; the W7 integrator is the authority).
- Production untouched: `git diff src/` empty; `config/agent_config.yaml` change was pre-existing at
  session start (not from this track).

## Caveats

- The persistent-memory files live at the dev-Mac path
  `~/.claude/projects/-Users-borr-Documents-gtos-repo-ai-trading-agent/memory/`; their load-bearing
  content is folded into the bootstrap, but the owner should carry the four files to the VPS for the
  full record. (Bootstrap notes this explicitly.)
- `SiliconBridgeAdapter` is a reviewed seam, not a live-verified driver — the bootstrap repeats the
  charter requirement to reconcile method signatures against the installed bridge build before live use,
  and notes the VPS live path is the two LOCAL MT5 terminals, not the dev bridge.
- The sqrt-N pooling tail-improvement is documented as opt-in / not-yet-folded into the deployed MC.
- This track produced documentation only; the live gate remains the owner-domain broker/runtime
  AUTHORITY work (Step 9) + VPS+FTMO provisioning (Step 8) — not the edge.
