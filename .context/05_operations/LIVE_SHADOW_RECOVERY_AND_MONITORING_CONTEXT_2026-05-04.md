# Live Shadow Recovery And Monitoring Context - 2026-05-04

Status: active context
Promotion posture: `NO_PROMOTION_VERDICT`
Related commit: `404beb1 feat: add live mechanical shadow recovery`

This context records the live-shadow recovery fix and the first monitoring pass after it. Future sessions should read this together with `.context/00_core/research_current_state.md`, `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`, and `.context/LIVE_STATE.md`.

## Recovery Fix

- Forward JSONL append helpers now lock, flush, and `fsync` writes. If a Windows lock remains busy after retry, the row is preserved under a pending-append sidecar instead of silently dropped.
- `shadow_logs/d1_bias_lag.jsonl` was repaired without fabricating replacement rows: 333 valid rows retained and 3 corrupt fragments quarantined in `shadow_logs/d1_bias_lag_recovery.jsonl`, with raw backup under `research/program_control/raw_shadow_log_quarantine/`.
- `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl` now receives one append-only row per candidate, strategy, and as-of candle from `scripts/follow_live_candidate_paths.py`.
- `shadow_logs/shadow_observer_tick_enrichment.jsonl` adds MT5 recent-tick summaries for observer windows without AI, canary, Databento, or order calls.
- Verification after the fix: focused pytest `19 passed`; shadow integrity `OK_WITH_DOCUMENTED_WAITING_LANES`; forward readiness `OK=12`, `WAITING=1`; live monitor `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.

## Live Monitoring Pass - 2026-05-04 08:15 UTC As-Of

After running `python scripts/follow_live_candidate_paths.py`, the tracked live-shadow rows were:

- `shadow_logs/strategy_follow_candidates.jsonl`: 7 candidates.
- `shadow_logs/candidate_path_follow.jsonl`: 25 path-follow rows.
- `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl`: 400 mechanical shadow rows.
- `shadow_logs/strategy_follow_evaluations.jsonl`: 49 pre-AI/status rows.
- `shadow_logs/v2b_forward_pairs.jsonl`, `prefill_delivery_path.jsonl`, `fvg_ob_confluence.jsonl`, and `context_control_ledger.jsonl`: 7 rows each.
- `shadow_logs/pending_limit_lifecycle.jsonl`: 15 rows.
- `shadow_logs/shadow_observer_tick_enrichment.jsonl`: 6 rows.

Candidate interpretation as of the 08:15 UTC M15 close:

- `XAUUSD_2026-05-04T07:15:00+00:00` was `LIMIT_PLACED`, short, entry `4668.45`, TP1 `4650.73`, SL `4680.26`. The limit did not fill, but price continued to the TP area. This is a missed move for market-style/proximity-style entry logic, not a filled GTOS result.
- `NAS100_2026-05-04T07:15:00+00:00` was `LIMIT_PLACED`, long, entry `27736.8`, TP1 `27831.7`, SL `27673.5`. The limit did not fill, but price continued to the TP area. This is also a missed move for market-style/proximity-style entry logic, not a filled GTOS result.
- XAGUSD produced five repeated short candidates at `07:15`, `07:30`, `07:45`, `08:00`, and `08:15` UTC. All were `REJECTED_L2` on `m15_choch_exists`. Their shared limit entry `75.471` was touched and no SL/TP1 was hit by 08:15 UTC; latest computed max favorable excursion was about `0.70R`, so these are open unresolved counterfactuals, not confirmed missed winners.

Mechanical shadow interpretation:

- Computed from candidate path for every latest candidate: `LIVE_AI_J46_J49_BASELINE_COMPARATOR`, `V2B_OB_BOUNDARY_PROSPECTIVE`, `V2_STRUCT_OB_BOUNDARY`, and `PENDING_LIMIT_LIFECYCLE`.
- Not entry strategies by design: `J46_J49_PORTFOLIO_POLICY`, `S79_UNIFORM_FN_RISK_POLICY`.
- NAS100-only context was attached for the NAS100 row and marked not applicable elsewhere.
- Exact V2/V3 variants that require structural-lock/reentry metadata are explicitly marked `MISSING_REQUIRED_LIVE_METADATA`; this is a live-data capture gap to close going forward, not a computed outcome.
- `PREFILL_DELIVERY_REVERSAL_PATH` remains `NOT_COMPUTABLE` from current candidate-path rows alone because it needs the richer pre-fill delivery path fields.

## Operating Notes

- No manual canary call was made.
- No manual AI/API test call was made.
- No paid Databento fetch was made.
- No order or live decision behavior was changed.
- The active goal tool reported `status=paused`; immediate monitoring can still be done in-session, but unattended looping requires the owner to send `/goal resume`.
