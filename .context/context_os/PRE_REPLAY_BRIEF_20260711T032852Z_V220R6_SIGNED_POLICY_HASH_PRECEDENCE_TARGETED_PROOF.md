# V220R6 Signed Policy Hash Precedence Targeted Proof

Generated UTC: 2026-07-11T03:28:52Z.

## Snapshot

- Base commit: `cc4bf946a`; current B7.2 work remains a scoped dirty batch.
- No replay, test, builder, verifier, or subagent process is running.
- Latest completed targeted replay is V220R5. It certified under schema v2 and
  materialized every required artifact, but produced no terminal execution.
- Broker/live/final remain false. Local replay/package authority remains full.

This smoke tests the late selected-policy hash consumer only. It does not prove
five-day value, broad holdout performance, reservoir conversion, final
selection, or live readiness.

## Current Comparators

- V220R5 source/decision/candidate/scorecard/order/trade/missed:
  `29/4608/1651/192/0/0/1651`.
- V220R5 W/L/F, net/gross/final R, cash, risk cash/pct: all zero because no
  order or fill materialized.
- V220R5 diagnostic scoreable missed rows/R: `366/-118.10784844R`; executable
  scoreable missed rows/R: `0/0R` under the final authority labels.
- V220R5 stress/MC trade count: `0/0`; executed REFUSED/source-gap: `0/0`.
- V218 same bounded scope remains the behavioral comparator: 3 trades, W/L/F
  `3/0/0`, net/gross/final R
  `+1.10761535/+1.35101129/+1.35101129`, cash `+989.52983936`.
- V219 remains the newest broad five-day run: 23 trades, W/L/F `14/9/0`,
  net/gross/final R `-2.82440031/-0.79141028/-0.79141028`, cash
  `+204.17530212`.
- V89D/V90/V92 are five-day historical transfer comparators only; they are not
  denominator-equivalent to this two-day/three-symbol proof.

## V220R5 Exact Transfer Evidence

Twelve exact-instance signed candidates received a positive reduced-risk
allocation (`0.1%`) before finalization. They split into two causal groups:

1. Seven candidates passed broker cost, source completeness, selected-policy
   quality, signed order authority, immediate-marketable causal quality, and
   immediate-route authorization. Order preflight then re-ran the owner proxy
   selected-policy builder and generated a different calibration hash, causing
   `current_signed_authority_projection_mismatch:selected_policy_expected_net_calibration_hash`.
2. Five candidates were independently blocked by the marketable-entry guard.
   Their causal fill/entry-quality checks passed, but broker-calibrated
   `expected_cost_r` exceeded the configured package release ceiling. Those
   denials remain authoritative.

The seven hash-blocked candidates have expected net R `0.713177822` through
`1.214011947`, probability `0.732949303` through `0.913609109`, execution fill
probability `0.92`, source completeness `1.0`, cost status `PASSED`, and valid
signed order authority. Three also carry scheduler same-decision-cluster
competition and may expose that next after hash repair.

## Same-Root Repair

- Order preflight first resolves one valid exact-instance signed envelope.
- When that envelope contains selected-policy calibration, all seven policy
  atoms come from its immutable payload.
- The owner-approved reconstructed policy builder is not called again for a
  valid signed envelope.
- Unsigned rows still use the owner-approved reconstructed fallback.
- Current broker-cost, fill-floor, lifecycle, and order denials remain
  effective and are not replaced by admission-time signed allow.
- Existing verifier logic rejects any recurrence of mutable signed-policy
  projection drift.

Classification: correctness and executable-transfer repair. It adds no
suppression, cost bypass, outcome bucket, or live authority.

## Root-Cause Chain

| Stage | State after patch |
| --- | --- |
| source-bound -> candidate | Preserved: exact matched axes only. |
| candidate -> selector | Preserved: causal candidate-instance quality and fillability. |
| selector -> scheduler | Preserved: one finalized exact-instance signature. |
| scheduler -> risk | Repaired: signed selected-policy atoms reach all consumers. |
| risk -> order | Repaired/pending proof: no late owner hash re-derivation. |
| order -> lifecycle/fill | Open: current cost, marketable guard, cluster, lifecycle, expiry, and ticks remain authoritative. |
| fill -> exit | Deferred until fills exist. |
| ledger/verifier | V220R5 certification passed; projection-drift verifier remains active. |

## Files And Verification

Behavior code and consumers:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- selected-package bridge, source parity builder, route verifier, and their
  focused tests in the active route/test surface.

Verification:

- Python compile: passed.
- Direct signed-policy/current-denial tests: `9 passed`.
- Six-file scheduler/runtime/materialization/bridge/parity/verifier barrier:
  `1603 passed`.
- Scoped `git diff --check`: passed.
- No unreconciled subagent return remains.

## Acceptance

- Candidate/scorecard counts should remain near `1651/192`; opportunity
  suppression fails.
- The seven selected-policy hash mismatches must become zero.
- Those seven candidates must reach the next current risk/order/lifecycle stage,
  except where a separate exact blocker such as same-decision cluster applies.
- The five broker-cost-ceiling marketable denials remain blocked unless current
  broker-calibrated evidence itself changes.
- Executed REFUSED/source-gap rows remain `0/0`.
- Current denials must not be reopened by signed admission-time truth.
- Report orders, fills, trades, missed positive/negative R, W/L/F,
  net/gross/final R, cash, risk cash/pct, full/reduced risk, stress, MC, and the
  next exact blocker.
- Success: zero hash mismatch, no opportunity deletion, no cost/source bypass,
  and measurable transfer to a later stage.
- Failure: hash mismatch recurs, the run fails certification, current denials
  reopen, or the seven candidates disappear without exact attribution.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R6_SIGNED_POLICY_HASH_PRECEDENCE_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

The existing storage protection extends through V220R6. No cleanup is
authorized during this bounded run. A new bounded storage review is required
before any later broad replay.
