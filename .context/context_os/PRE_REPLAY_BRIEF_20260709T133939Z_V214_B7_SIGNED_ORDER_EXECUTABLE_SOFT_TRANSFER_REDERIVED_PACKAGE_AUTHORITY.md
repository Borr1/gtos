# Pre-Replay Brief - V214 B7 Signed Order-Executable Soft-Transfer Re-derived Package Authority

Generated UTC: 2026-07-09T13:39:39Z.

## Control Surface

- Fable batch: B7 full proof ladder, transfer/composition repair after V211/V212/V213.
- Broker/live/final boundary: broker mutation disabled, live broker authority false, final selection false.
- Replay authority: local replay/package authority full.
- Scope: targeted proof slice only, not a full-reservoir transfer claim.
- Dependency order: B0/B1/B4/B6 remain done or conditional-done; B2/B3/B7 remain active; B8 remains open.

## Latest Completed Replay

Latest completed targeted proof:
`BROAD_LIVE_AS_IF_REPLAY_V213_B7_SIGNED_SOFT_TRANSFER_FINALIZER_CONSUMER_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

- Scope: 2026-05-13..2026-05-14, XAUUSD/USDCAD/USDJPY, repaired profile only.
- Candidate/decision/scorecard/order/trade/missed/bucket rows: 1651 / 4608 / 192 / 8 / 3 / 1647 / 92.
- W/L/F: 3 / 0 / 0.
- Net/gross/final R: +1.10761535 / +1.35101129 / +1.35101129.
- Cash PnL: +277.0648589.
- Risk cash / risk pct sum: 750.86709783 / 0.75.
- Expected cost R: 0.24339594.
- Executed REFUSED/source-gap rows: 0 / 0.
- Target exact transfer: 2/3 candidate, 2/3 scorecard, 2/3 missed, 0/3 order/trade.
- V213 interpretation: behavior-identical to V212; signed proof reached scorecard/missed, but target order/trade transfer did not improve.

## V213 Root Evidence

Target-row scan:

- Candidate target rows XAUUSD and USDCAD had valid signed authority, order-executable authority, broker-calibrated cost, and source-complete package surface.
- Missed target rows still showed `risk_finalizer_signed_soft_transfer_displacement_allowed=false`.
- XAUUSD target failures: `not_reallocation_candidate`, `soft_transfer_reason_missing`; risk decision reject with `stop_hazard_materialization_requires_reallocation_dominance`.
- USDCAD target failures: `not_reallocation_candidate`, `soft_transfer_reason_missing`, `fill_probability`; risk decision open-reduced-risk.

Subagent dispositions:

- Einstein: incorporated. V213 supersedes stale V208/V209 acceptance text; B2/B3/B7 remain active and no broad replay should run before focused repair proof.
- Schrodinger: incorporated. V213 vs V212 counters are behavior-identical; 45 scorecard executable-probe rows remain final-blocked, 27 missed rows are already `package_candidate_and_signed_new_entry_authority_executable`, and only 4 risk-admitted orders materialized.
- Franklin: incorporated. `origin_preserved_after_scheduler_risk_cap` must not be promoted into router-refusal authority. The valid authority surface for this repair is explicit package-executable replay materialization plus the signed order-executable contract.

## Current Patch Batch

Batch:
`V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY`.

Root issue:

- The signed soft-transfer finalizer required broad `package_replay_executable_candidate_use_allowed=True`.
- V213 target missed rows can carry stale broad package-executable false while the narrower signed order-executable authority remains valid, broker-cost-passed, source-complete, and non-outcome.
- That caused valid signed order-executable rows to fail as non-reallocation candidates instead of being judged by the causal soft-transfer quality/cost/fill/source checks.

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T133939Z_V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY.md`

Patch types:

- Correctness repair: signed order-executable authority can rederive the stale broad package-executable alias only inside the finalizer's causal signed soft-transfer path.
- Performance repair: enables selected-composition/reallocation transfer for valid signed, cost-passed, source-complete, order-executable reduced-risk rows that were previously final-blocked by stale broad alias truth.
- Diagnostic/ledger repair: added trace fields for signed-order route candidacy and rederived package-executable authority.

Focused proof already run:

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`
- `pytest -q tests/test_v4_timewarp_simulated_live_research_loop.py -k 'signed_soft_transfer or signed_order_executable_soft_transfer' --tb=short`: 4 passed.
- Focused finalizer pytest set: 5 passed.

## Expected V214 Effects

- Candidate -> scorecard transfer: should stay near V213; this patch should not suppress candidates.
- Scorecard -> order transfer: valid signed order-executable rows with stale broad package-executable false should advance or expose the next exact downstream blocker.
- Order -> fill transfer: must preserve ordered-tick/fillability realism; no REFUSED/source-gap execution.
- Missed positive/negative R: executable signed rows still missed must carry exact next blocker, not generic stale package-executable alias failure.
- Trade count/net R: may increase if XAU/USDCAD target rows advance; positivity is not required for this targeted proof.
- Full/reduced risk: risk provenance must remain visible and separated.
- Cost/source execution: executed REFUSED/source-gap rows must remain 0/0.

## V214 Replay Command

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
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V214_B7_SIGNED_ORDER_EXECUTABLE_SOFT_TRANSFER_REDERIVED_PACKAGE_AUTHORITY_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY
```

## Success / Failure Criteria

Success:

- No broker/live/final authority opens.
- No executed REFUSED/source-gap rows.
- V213 target rows improve from 0/3 order/trade or expose a more precise downstream blocker.
- `risk_finalizer_signed_soft_transfer_displacement_signed_order_executable_route_candidate` appears on proof rows where the route is valid.
- `risk_finalizer_signed_soft_transfer_displacement_package_executable_rederived_from_signed_order_authority` appears only when broad package-executable was stale false but signed order-executable authority was valid.
- Improvement is not positive-by-suppression; candidate/scorecard/missed opportunity surfaces remain comparable to V213.

Failure:

- Target rows remain final-blocked with only `not_reallocation_candidate` / stale broad executable alias causes.
- Re-derived authority appears on broker-cost REFUSED/source-gap/unfillable rows.
- Signed authority fields disappear from scorecard/order/trade/missed surfaces.
- Trade count rises by admitting invalid authority instead of valid causal predecision authority.

Next deeper flaw if V214 passes locally:

- Parse V214 target rows and all 27 `package_candidate_and_signed_new_entry_authority_executable` missed rows.
- If target rows advance but behavior remains weak, rank the next B7 transfer leak from order/fill/lifecycle/exit evidence before any broad replay.
- Route builder/verifier and artifact audits run after V214 artifacts exist.

Broker/live/final remain closed regardless of V214 result.
