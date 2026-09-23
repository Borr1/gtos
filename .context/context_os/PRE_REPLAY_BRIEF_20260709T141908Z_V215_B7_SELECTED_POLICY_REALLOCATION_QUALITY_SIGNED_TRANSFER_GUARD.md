# Pre-Replay Brief - V215 B7 Selected-Policy Reallocation Quality Signed-Transfer Guard

Generated UTC: 2026-07-09T14:19:08Z.

## Control Surface

- Fable batch: B7 full proof ladder, targeted transfer-composition repair.
- Broker/live/final boundary: broker mutation disabled, live broker authority false, final selection false.
- Replay authority: local replay/package authority full.
- Scope: bounded two-day proof slice only, not a full-reservoir transfer claim.
- Current process state before replay: no broad replay, route builder, verifier, or pytest process is running; active Python processes are Context OS MCP stdio servers only.

## Latest Completed Replay

Latest completed targeted proof:
`BROAD_LIVE_AS_IF_REPLAY_V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

- Scope: 2026-05-13..2026-05-14, XAUUSD/USDCAD/USDJPY, repaired profile only.
- Candidate/scorecard/order/trade/missed/bucket rows: 1651 / 192 / 28 / 13 / 1637 / 95.
- W/L/F: 8 / 5 / 0.
- Net/gross/final R: -1.76172422 / -0.52207133 / -0.52207133.
- Cash PnL: -128.7023959.
- Risk cash / reduced-risk order decisions: 1598.50574717 / 14.
- Expected cost R: 1.23965289.
- Executed REFUSED/source-gap rows: 0 / 0.
- V214 versus V213 delta: trade count +10, net R -2.86933957, gross/final R -1.87308262, cash PnL -405.7672548.
- Added V214 trades: 11 trades, -2.08087572R.
- Removed V213 trades: 1 trade, +0.78846385R.
- Target transfer: XAUUSD target advanced to order/trade and +0.02R; USDCAD target remained candidate/missed only.
- Stress/MC: 200-iteration MC total net R -1.76172422, median max drawdown -3.12611916R, worst max drawdown -4.72898588R.

Interpretation: V214 proved the stale broad package-executable alias was a real transfer blocker, but the repair was too permissive. It admitted signed-transfer rows whose finite selected-policy reallocation quality scores were below the predecision floor. The added cohort was net negative; this is not acceptable as value transfer.

## Subagent Finding Disposition

- Singer: INCORPORATED. V214 deterioration is selection/admission, not exit/profit-harvest. Added losers had tiny MFE, and the common leak is signed soft transfer overriding finite negative `selected_policy_executable_quality_reallocation_score` / `risk_admitted_scheduler_reallocation_score` that V213 blocked with `stop_hazard_materialization_requires_reallocation_dominance`.
- Helmholtz: INCORPORATED. `signed_order_executable_route_candidate=true` is necessary but not sufficient. Original scheduler passthrough rows must not be blocked just because signed soft-transfer displacement failed, but non-original signed package micro-rescue must require signed displacement allowance or a separate explicit package-reallocation contract.
- Anscombe: INCORPORATED/DEFERRED. Existing focused tests cover most signed soft-transfer paths and V214 preserves live/final closure and cost-source safety. Latest-route verifier binding remains deferred until V215 artifacts exist, because current `VERIFICATION_RESULT.json` is still bound to an older broad-quality prefix.

## Current Patch Batch

Batch:
`V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD`.

Root issue:

- V214 allowed signed soft-transfer authority to remove the `selected_policy_reallocation_quality_score` gate failure unconditionally.
- That allowed finite negative selected-policy/reallocation-quality rows below floor to become executable trades.
- The same issue also affected signed package micro-rescue authority: non-original rows could use structural package/order authority without proving signed soft-transfer displacement was allowed.

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T141908Z_V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD.md`

Patch types:

- Correctness repair: selected-policy quality gate reads scheduler stop-hazard aliases and finite reallocation-quality scores from the executable policy surface.
- Correctness/performance repair: signed soft-transfer displacement may override stale/missing reallocation-quality fields, but may not override a finite score below the configured floor.
- Correctness repair: non-original signed package micro-rescue requires `risk_finalizer_signed_soft_transfer_displacement_allowed=True`; original scheduler passthrough remains separately valid.
- Diagnostic/proof repair: signed displacement trace fields and micro-rescue block reasons propagate into probe, order, trade, and missed surfaces.

Focused proof already run:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py` passed.
- Focused signed/selected-policy pytest cluster passed: 7 passed, 606 deselected, 1 warning.

## Expected V215 Effects

- Candidate -> scorecard transfer: expected near V214; this batch should not suppress candidate generation.
- Scorecard -> order transfer: rows whose only support is signed-transfer override with finite negative selected-policy reallocation quality should move from order/trade to missed/diagnostic with explicit gate failure.
- Order -> fill transfer: expected lower than V214 if the negative cohort is correctly blocked; original scheduler passthrough rows with independent authority should remain executable.
- Missed positive/negative R: missed rows must carry `selected_policy_reallocation_quality_score` or micro-rescue block reasons where applicable.
- Trade count/net R: likely moves back toward V213; success is not positivity by suppression, it is causal predecision quality blocking plus preserved valid transfer.
- Full/reduced risk: distribution must remain visible; V214 all filled trades were reduced-risk, so V215 must report whether any full-risk transfer appears or whether B3 remains open.
- Cost/source execution: executed REFUSED/source-gap rows must remain 0 / 0.

## V215 Replay Command

Run only the targeted proof slice:

```bash
PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 \
  --end 2026-05-14 \
  --chunk-size 1 \
  --profiles repaired_package_conversion_v3 \
  --symbols XAUUSD USDCAD USDJPY \
  --compact-missed-ledger \
  --gc-between-chunks \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V215_B7_SELECTED_POLICY_REALLOCATION_QUALITY_SIGNED_TRANSFER_GUARD_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY
```

## Success / Failure Criteria

Success:

- No broker/live/final authority opens.
- No executed REFUSED/source-gap rows.
- V214 rows with finite negative selected-policy reallocation quality no longer execute solely due signed-transfer override.
- Original scheduler passthrough rows with independent authority still execute when they pass broker cost, source completeness, fillability, and policy gates.
- Non-original micro-rescue rows without signed displacement allowance are blocked and traced.
- Improvement is not accepted if it comes only from suppressing all opportunity; candidate, scorecard, missed, and target-transfer surfaces must remain explainable.

Failure:

- Finite negative selected-policy reallocation-quality rows still execute through signed soft-transfer.
- Original scheduler passthrough is wrongly blocked by signed displacement failure.
- Signed micro-rescue can still execute without signed displacement allowance or original-scheduler status.
- Cost-refused/source-gap rows execute.
- Trade count collapses without explicit missed-opportunity and gate attribution.

Next step if V215 passes:

- Parse V215 against V214 and V213 with the same local denominator.
- Bind latest accepted behavior artifacts into the route builder/verifier, or patch the verifier if it cannot recompute the latest behavior report.
- Only then broaden to the next Fable B7 proof slice; do not jump straight to broad replay if V215 exposes another targeted truth leak.

Broker/live/final remain closed regardless of V215 result.
