# V104 Passive Distance Hard Block Pre-Replay Brief

Generated: 2026-07-03T14:14:42Z

## Current Completed Evidence

- V102 hostile: 51 trades, +25.59750407 net R, +30.33465208 gross/final R, W/L/F 29/22/0, 11 expired.
- V103 hostile: 64 trades, +24.46549669 net R, +30.42580024 gross/final R, W/L/F 35/29/0, 26 expired.
- V103 vs V102: trades +13, net R -1.13200738. Added trades were net positive (+2.43961548R) but weaker than removed V102 trades (+3.57162286R).
- V103 vs V92: net R -4.89020567.
- V103 same-window transfer: 1101 package axes, 894 candidate axes, 37 scorecard/order axes, 30 filled axes, +23.95367081 executable R. This is a local hostile-bucket repair proof only, not full reservoir conversion.

## Finding From V103

Lowering the passive degraded transfer floor from 0.55 to 0.40 did not improve headline behavior. It converted more rows, but displaced stronger transfers. The filled degraded passive queue class in V103 was 23 trades, +2.23567392R, W/L 11/12, but all of those rows were released because `passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling` was treated as fallback-only.

Historical V102 degraded passive queue rows show the same root:
- V102 hostile: 2 degraded filled rows, -0.09684507R, both distance-breach releases.
- V102 non-May: 17 degraded filled rows, -3.57604010R, all distance-breach releases.

Kant and Kepler subagent findings are incorporated: do not broaden cost or scale-in blocks; harden the passive fallback envelope path where thesis-geometry distance breach is being downgraded into executable passive queue release.

## Patch Batch

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: removed `passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling` from `passive_limit_fallback_envelope_fallback_only_reasons`.
- `verify_denominator_to_deployment_execution.py`: degraded passive release validator no longer treats distance-breach as an allowed degraded reason.
- Tests updated:
  - high-fill fallback-only passive queue release remains valid;
  - low transfer score remains blocked;
  - broker-cost REFUSED still blocks;
  - distance-breach degraded passive queue release is hard-blocked;
  - verifier rejects distance-breach degraded release.

Focused verification passed: py_compile for touched modules and 9 focused pytest tests.

## Expected V104 Effect

- V104 should remove distance-breach degraded passive queue fills from V103.
- Candidate rows should remain around 25006 and scorecard rows around 288.
- Cost REFUSED/source-gap executed counts must remain zero.
- Success: V104 improves versus V103 and ideally restores or improves versus V102 by avoiding distance-breach passive queue displacement. If trade count falls, classify whether the change is correctness hardening rather than positive-by-suppression.
- Failure: if V104 worsens materially or verifier flags the new semantics, the next root cause is not passive distance release; move to finalizer selected-but-not-materialized reallocation/action-intent authority.

Broker/live/final remain false; local replay/package authority remains full.
