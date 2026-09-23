# vNext Production Change Stage06 LTF Entry And No-Fill Dossier

Created: 2026-05-25T08:43:58.557944Z

## Runtime Change

- Added `evaluate_vnext_ltf_path_execution` as a replay-backed Stage06 decision surface.
- Added orchestrator post-L2/pre-prop-selector handling for LTF skip, monitor, market entry, and adjusted limit entry.
- Added an activation-gated LTF pending monitor that can check M1/M5 candles during monitored sleep and outside-KZ pending checks.
- Current config keeps `ltf_path_execution_apply_to_execution=false`, so no broker-facing activation occurs by default.

## Replay Evidence Consumed

- M15-vs-LTF disagreement rows: 405729.
- Would change execution/decision: {"False": 1732, "True": 403997}.
- LTF modes: {"m1_path_aware": 211410, "m5_path_aware": 148893, "tick_or_sierra_path_aware": 45426}.
- Change flags: {"entry_timing_changed": 393221, "simulated_r_changed": 131795, "terminal_outcome_changed": 128918}.
- LTF minus M15 simulated R mean: -0.284700.
- No-fill/pending lifecycle rows: 253234.
- Pending lifecycle states: {"cancelled_target_reached_without_fill_or_same_bar_entry_ambiguity": 23965, "cancelled_wrong_side_or_stop_blowthrough_before_fill": 12498, "filled_then_ambiguous_stop_target_order": 5236, "filled_then_pending_trade_timeout_mark_to_market": 5275, "filled_then_stop_first": 116981, "filled_then_target_first": 88719, "pending_expired_no_fill_48h": 560}.
- Missed-winner/avoided-loser rows: 253234.
- Classification counts: {"accepted_loser": 100166, "avoided_loser": 16815, "captured_winner": 75646, "missed_winner": 13073, "no_fill_pending": 37023, "same_bar_ambiguous": 5236, "timeout_mark_to_market": 5275}.
- Path outcome/R rows: 1978947.
- Simulated R count/sum/mean: 903180 / 223996.487069 / 0.248009.

## Runtime Surface Coverage

- Production-change LTF surface rows consumed: 1064.
- Rows by prior stage: {"STAGE_02_PROMOTION_IMPLEMENTATION": 520, "STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION": 544}.
- Source components: {"nofill_far_miss_avoid": 544, "nofill_near_miss_market_entry": 15, "nofill_pending_lifecycle": 45, "static_limit_adaptive_entry_challenger": 460}.
- Computed decisions: {"AVOID": 509, "FOLLOW": 475, "MIXED": 80}.

## Scenario Coverage

- Runtime scenario rows: 7.
- Action counts: {"ADJUST_LIMIT_ENTRY": 1, "MARKET_ENTRY_NOW": 1, "MONITOR_LTF_PATH": 2, "PLACE_LIMIT": 1, "SKIP_LTF_NOFILL_AVOID": 2}.
- Would-action counts: {"ADJUST_LIMIT_ENTRY": 1, "MARKET_ENTRY_NOW": 2, "MONITOR_LTF_PATH": 2, "SKIP_LTF_NOFILL_AVOID": 2}.
- Scenarios cover shadow would-action, active market entry on touch, active monitor, adjusted limit entry, no-fill skip, target-without-entry skip, and source-gap monitoring.

## Activation Boundary

- The engine is activation-gated by global `gtos_vnext_runtime.apply_to_execution` and `ltf_path_execution_apply_to_execution`.
- The pending monitor uses read-only candle/tick state and only calls the existing execution path when a configured active pending intent touches the entry.
- No live trading, broker mutation, paid API, source deletion, remote push, or activation flip is performed by this stage.
