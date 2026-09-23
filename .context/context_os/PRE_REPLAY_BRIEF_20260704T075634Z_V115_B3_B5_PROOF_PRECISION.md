# Pre-Replay Brief: V115 B3/B5 Proof Precision

Generated: 2026-07-04T07:56:34Z

## Current Replay State

Latest completed replay:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V114C_RISK_EXPRESSION_AUTHORITY_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: 2026-06-03..2026-06-03
- Status: `broad_live_as_if_replay_materialized_broker_live_closed`
- Candidate rows: 6,603
- Scorecard rows: 96
- Orders: 28
- Trades: 12
- Net R: -2.30082618
- Gross R / final R: -1.15118996 / -1.15118996
- Cash PnL: -230.28228129
- W/L/F: 3/9/0
- Orders: 12 filled, 16 expired_unfilled
- Risk decisions: 28 open-reduced-risk

This is a one-day repair proof slice. It does not prove total reservoir conversion.

## Process State

No broad replay, pytest, git helper, or `generate_live_state.py` process is running. A fresh `generate_live_state.py` attempt was interrupted after it sat at zero CPU inside source grep over `execution_packets.py`; the last disk `LIVE_STATE.md` remains the current anchor until that hygiene issue is patched.

## Baseline Comparison Context

- B0 audit exists in `AUDIT_PROVENANCE_AND_FLAGS_V114.json`.
- V110B audit: 75,562 aggregate rows, 12,525 selector origin/effective mismatches, 0 mismatches without materialized flag, 0 R-accounting drift, 0 raw-failure poisoning.
- V111 audit: 76,102 aggregate rows, 12,705 selector origin/effective mismatches, 0 mismatches without materialized flag, 0 R-accounting drift, 0 raw-failure poisoning.
- V110B broad 19d memory: 95 trades and +22.80442652R; verify exact artifact before quoting further.
- V111 broad 19d memory: about 45 trades and -4.19R; verify exact artifact before quoting further.

## Dirty Files In This Checkpoint

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/compare_broad_live_as_if_replay_runs.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `tests/test_build_source_bound_execution_parity.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

## Subagent Findings

- Socrates: B4 fill realism remains open. Passive limit first-touch optimism, `fill_realism_class`, M15 proxy split, and same-bar conservative close still need implementation.
- Feynman: B5 verifier/comparison precision gaps are incorporated in this patch.
- Lorentz: B0/B1 are complete on current proof surface; B2 is partial; B3 had code but no replay proof and no verifier fatal. This patch adds the B5 fatal checks.

## Mismatch Classes

- Source-bound -> candidate: partially fixed. Profile preservation now uses row/summary profile or `unknown_profile`; no repaired-profile stamping.
- Candidate -> selector: partially fixed. Effective selector action is now required in compact proof rows; selector policy tuning is not changed in this checkpoint.
- Selector -> scheduler: partially fixed. B2 reallocation/fill-floor path remains open.
- Scheduler -> risk: partially fixed. Structured risk ladder exists in code/tests and verifier now fails false full-risk claims.
- Risk -> order/cost: partially fixed. Broker-cost authority scan is executable-scoped; diagnostics remain scoreable.
- Order -> lifecycle/fill -> exit: open. B4 fill realism is the next implementation batch after V115 proof.
- Ledger/verifier/comparison: patched. Off-configured fallback predicate, raw/effective promotion leak, full-risk ladder fatal, window-filtered comparator, risk/fill-realism splits, parity profile preservation, full-package symbol scope, and bounded-smoke tags are implemented.

## Patch Batch

Highest-leverage same-root batch: B3 proof hooks plus B5 verifier/comparator/parity/bridge precision.

Patch type:

- Correctness: raw/effective signed-materialization fatal, full-risk ladder signing fatal, profile preservation, explicit full-package bridge scope.
- Diagnostic/ledger: executable-scoped cost scan, comparator same-window filtering, risk/fill-realism splits, executable-vs-diagnostic reservoir delta.
- Performance: no direct performance tuning in this batch.

## Expected Before Replay

- Candidate -> scorecard: no intentional increase.
- Scorecard -> order: no intentional increase.
- Order -> fill: no intentional increase.
- Missed positive/negative R: unchanged by B5; B4 should later reclassify optimistic fills.
- Trade count and R: unchanged unless artifact rebuild exposes previous proof omissions.
- Cost-refused/source-gap execution: must remain 0.
- Risk distribution: next replay must show structured ladder tier counts; all-open-reduced remains an open system issue if it persists.

## V115 Proof Criteria

Helpful result:

- Structured `risk_expression_ladder*` appears in scorecard/order/trade/missed rows.
- No executable REFUSED/source-gap rows.
- No unsigned raw reject/source-required promotion to executable trade/open-reduced.
- Full-risk rows, if any, satisfy signed authority, broker-cost, source-completeness, fill-floor, full-risk-allowed, and full-risk-applied conditions.
- B5 verifier scans pass.

Failure:

- Missing `effective_selector_action` in compact executable rows.
- Diagnostic/counterfactual cost rows treated as executable proof.
- Off-configured fallback allowed=true still false-fails.
- Full-risk ladder tier appears without signing conditions.

Next deeper flaw if proof passes but behavior stays weak:

- Do not narrow selector buckets. Patch B4 fill-simulation realism and revisit B2 reallocation/fill-floor transfer, then replay targeted before broader regimes.

## Verification So Far

- `python3 -m py_compile` passed for verifier, comparator, parity builder, selected bridge, and focused tests.
- Focused pytest: 9 passed, 1 warning.
- `git diff --check` passed for touched files.
