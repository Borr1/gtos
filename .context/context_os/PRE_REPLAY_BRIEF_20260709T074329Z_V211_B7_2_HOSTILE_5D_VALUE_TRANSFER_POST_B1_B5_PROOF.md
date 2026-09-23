# V211 B7.2 Pre-Replay Brief

Generated: `2026-07-09T07:43:29Z`

This brief selects the next Fable dependency action from current disk evidence.
It is not a new paperwork branch and it is not a live/final claim.

## 1. Latest Completed Replay

Latest accepted completed replay:
`BROAD_LIVE_AS_IF_REPLAY_V210_B1_B5_POST_PATCH_MISSED_CONFIDENCE_SOURCE_PROOF_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

V210 is a bounded one-day B1/B5 truth proof:

- window: `2026-05-13`;
- source / candidate / decision / scorecard / order-event / trade / missed /
  bucket rows: `180 / 8864 / 2304 / 96 / 9 / 2 / 8858 / 412`;
- W/L/F: `2 / 0 / 0`;
- net/gross/final R: `+0.52110312 / +0.65111456 / +0.65111456`;
- cash PnL: `+130.31196876`;
- risk cash / risk pct: `500.10039132 / 0.5`;
- cost R: `0.13001144`;
- same-window source-bound R: `149486.17602471R`;
- package axes / candidate-generated axes / scorecard-or-order axes /
  filled axes: `1101 / 853 / 4 / 2`.

V210 proof results:

- missed confidence-source omissions: `0 / 8858`;
- flow analyzer succeeded: `601` flow bucket rows;
- source-bound parity succeeded: `8130` parity rows and `1101` leakage bucket
  rows;
- route builder succeeded and wrote V210 under `broad_quality_parity_prefix`
  and `broad_holdout_gate_prefix`;
- route verifier succeeded: `ok=true`, `issue_count=0`,
  `verified_utc=2026-07-09T07:38:32Z`;
- broker/live/final remain false.

V210 proves the local B1/B5 repair. It does not prove total reservoir
conversion.

## 2. Active Process State

The latest process scan found no active broad replay, route builder, route
verifier, flow analyzer, or source-bound parity process. A transient `pgrep`
match had exited before `ps` inspection.

Therefore V211 may be launched after this brief is saved.

## 3. Baseline Comparison

Same-window hostile five-day comparators (`2026-05-13..2026-05-17`):

| Run | Trades | Net R | Gross R | Final R | Cash PnL | W/L/F | Orders | Missed |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| V89D | 56 | +34.84520454 | +39.93441037 | +39.93441037 | +8178.90660707 | 41/15/0 | 243 | 24885 |
| V90 | 51 | +28.84201157 | +33.36349114 | +33.36349114 | +6371.80465431 | 37/14/0 | 233 | 24890 |
| V92 | 51 | +29.35570236 | +33.93212860 | +33.93212860 | +6228.63096022 | 37/14/0 | 239 | 24887 |
| V97 | 47 | +13.89627731 | +18.23890670 | +18.23890670 | +4461.09800786 | 23/24/0 | 196 | 24908 |
| V198 | 75 | -3.84033809 | +1.79005938 | +1.79005938 | -3530.29276461 | 43/31/0 | 178 | 24908 |
| V205 | 73 | -5.20239659 | +0.16828289 | +0.16828289 | -3907.50669036 | 41/31/0 | 172 | 24914 |
| V209 | 18 | -3.47466796 | -1.91290882 | -1.91290882 | -868.32556257 | 11/7/0 | 50 | 24979 |

Bounded one-day proof comparator:

| Run | Window | Trades | Net R | Gross R | Final R | Cash PnL | W/L/F | Orders | Missed |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| V210 | 2026-05-13 | 2 | +0.52110312 | +0.65111456 | +0.65111456 | +130.31196876 | 2/0/0 | 9 | 8858 |

V211 must be judged against the five-day hostile baselines, not against the
global million-R reservoir and not against the one-day V210 proof as a full
behavioral truth.

## 4. Dirty Files And Active Changes

Route-owned active changes:

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260709T074329Z_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T074329Z_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF.md`
- `.context/context_os/CONTINUATION_CURSOR.json` after cursor update.

Generated route summaries/manifests from the V210 builder/verifier are also
dirty and route-owned:

- `DENOMINATOR_TO_DEPLOYMENT_EXECUTION_SUMMARY.json`
- `OUTPUT_MANIFEST.json`
- `VERIFICATION_RESULT.json`

Unrelated dirty files exist in `.context/00_core`, `src/gtos_context_os`,
`scripts/generate_live_state.py`, broader-origin generator code, several tests,
and deleted old science-program JSONL files. They are not part of this V211
checkpoint unless a later batch explicitly selects them.

## 5. Subagent Findings

- Fable plan/audit: incorporated as the controlling B0-B8 ladder.
- Hegel B1/B5 default-confidence finding: incorporated. The harness now
  preserves compact missed confidence-source/default-warning provenance; the
  verifier now fails hidden default confidence and confidence-without-source
  rows; V210 proved the repair.
- Fable/B5 artifact-locality finding: incorporated. Large dataless APFS route
  artifacts now fail fast, while small readable compressed files are allowed.
- Earlier Popper/James/Hilbert/Dirac/Dalton/Halley and prior B7 findings:
  carried forward only where current disk artifacts/tests already prove them.
  They are not re-opened as active work in this checkpoint without V211 evidence.

No current subagent finding is rejected. Deferred findings belong to the next
B7 repair selected from V211 leakage buckets.

## 6. Known Mismatch Classes

Source-bound -> candidate:
V210 generated `853/1101` package axes on the one-day window. Candidate
generation is materially present, but not enough for executable transfer.

Candidate -> selector:
Candidate quality parity is verifier-clean. The active concern is not missing
candidate fields; it is value transfer after generation.

Selector -> scheduler:
V210 transfer collapsed from `853` generated axes to `4` scorecard/order axes.
V211 must show whether the five-day collapse is scheduler ranking/reallocation,
selector admission, or truthful non-executability.

Scheduler -> risk:
V210 materialized order risk decisions were all `open-reduced-risk`, with no
selected reallocation probes. V211 must report full-risk versus reduced-risk
distribution and PnL.

Risk -> order:
Broker-cost REFUSED/source-gap rows remain non-executable. This must stay true
in V211 while still preserving scoreable missed opportunity.

Order -> lifecycle -> fill:
V210 had `9` order events, `6` flow order rows, and `2` filled trades. V211 must
separate filled, pending, expired, guarded-market-fallback-unmet, delayed,
cancel-replace, and lifecycle-terminal rows.

Fill -> exit:
V209 was still negative, so if V211 remains negative the next repair should be
selected from actual added/removed trade and exit/stop/fillability buckets, not
from broad one-day tuning.

Ledger/proof:
B1/B5 confidence-source truth is now green. Route verifier is the gate for V211.

## 7. Fixed, Partial, Open, Newly Exposed

Fixed:

- B1/B5 missed confidence-source provenance.
- B5 large dataless artifact fail-fast verifier behavior.
- B5 route verifier determinism for the V210 route proof.

Partial:

- B7 hostile value transfer. V209 is useful exposure only because it launched
  before the B1/B5 missed-row patch.
- Risk expression and scheduler/reallocation transfer remain suspected but need
  same-window V211 proof before the next patch.

Open:

- V211 hostile five-day value-transfer proof under patched harness.
- Same-window comparison versus V89D/V90/V92/V97/V198/V205/V209.
- Exact leakage ranking after V211: generated axes, scorecard/order axes,
  filled axes, missed positive/negative R, and added/removed trade value.

Newly exposed:

- V210 one-day proof is positive but has severe transfer compression. That is a
  local proof-slice signal, not a full system success.

## 8. Next Same-Root Batch

Next batch:
`V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF`.

Reason:
B1/B5 is now closed by V210. Dependency order requires B7.2 hostile five-day
value-transfer proof before more policy tuning. V209 cannot be accepted because
it was pre-patch.

## 9. Affected Components

Replay/proof components to exercise, not patch before V211:

- `run_broad_live_as_if_replay_harness.py`
- `analyze_broad_live_as_if_replay_flow.py`
- `build_source_bound_execution_parity.py`
- `build_denominator_to_deployment_execution.py`
- `verify_denominator_to_deployment_execution.py`

Policy components to inspect only after V211 evidence:

- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/components/broker_net_cost_engine.py`

## 10. Patch Type

No new behavior patch is selected before V211. V211 is a behavior/proof replay
under already-patched B1/B5 truth and B5 verifier infrastructure.

If V211 exposes a material leak, the next patch must be classified as
correctness, performance, or diagnostic/ledger repair before implementation.

## 11. Expected Measurable Effect

Expected if V211 is behavior-neutral relative to V209:

- candidate -> scorecard/order transfer: near `25006 -> 288` row class;
- order -> fill transfer: near V209 `50 -> 18` class, unless patched proof
  surfaces alter materialization;
- missed confidence-source omissions: `0`;
- cost-refused/source-gap executions: `0/0`;
- trade count/net/gross/final R/W/L/F: may stay near V209; if so, B7 remains
  open and the next repair must use V211 leakage buckets;
- full-risk/reduced-risk distribution: likely reduced-risk dominated and must
  be reported;
- missed positive and negative R: must be split by reason;
- added/removed trades versus V89D/V90/V92/V97/V198/V205/V209 must explain
  whether transfers are net-positive or net-negative.

## 12. Success / Failure Criteria

V211 helped if:

- route verifier passes with `ok=true`, `issue_count=0`;
- missed confidence-source omissions remain `0`;
- no broker-cost REFUSED/source-gap row executes as a trade;
- same-window transfer is improved or the next limiting B7 leak is exactly
  ranked with row counts and R;
- any positivity is not achieved only by suppressing opportunity.

V211 failed if:

- B1/B5 proof-surface issues reopen;
- V211 remains negative with unexplained removed winners;
- generated axes still collapse into scorecard/order without precise missed
  positive/negative attribution;
- full-risk/reduced-risk distribution remains collapsed and unexplainable;
- the result is positive only because trades or opportunities are suppressed.

Broker/live/final remain closed.
