# Phase 3 Valid Base Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Boundary

This audit validates the current Phase 3 path-scaling and orderflow research base before any further expansion. It does not validate historical project-wide alpha claims outside the current Phase 3/orderflow research map, and it does not change live trading logic, prompts, risk settings, or promotion status.

## Validation Commands Rerun

| Area | Command | Result |
|---|---|---|
| Preflight state | `python scripts/generate_live_state.py` | regenerated `.context/LIVE_STATE.md` successfully |
| V0 raw-OHLC replay | `python scripts\run_raw_ohlc_path_ablation_v0.py --include-blocked-controls --quiet` | completed full available corpus: `take_rows_seen=23483`, best `J46_J49_ONLY`, `best_net_mean_r_cost_0.05=0.190128`, `NO_PROMOTION_VERDICT` |
| V1 disposition | `python scripts\analyze_raw_ohlc_path_ablation_v1_disposition.py --write --quiet` | wrote a fresh disposition JSON; V1 remains `REJECTED_FOR_EXIT_POLICY_PROMOTION` |
| V2 concentration | `python scripts\audit_raw_ohlc_path_scaling_v2_concentration.py --compute-hash` | `verification=PASS`; event-log SHA256 recomputed as `7ef19c3c5d4666a807e1be81214ca06da3fc05fb3945fec179fd715302b34cf9` |
| V2b prospective | `python scripts\evaluate_raw_ohlc_path_scaling_v2b_prospective.py` | `BLOCKED_NO_PROSPECTIVE_ROWS`; post-cutoff resolved pairs `0` |
| Proxy map priority | `python scripts\audit_orderflow_proxy_mapping_priorities.py` | remaining unsupported candidates `57`: `GBPJPY=23`, `USDJPY=34` |
| NAS100 readiness | `python scripts\audit_orderflow_nas100_hypothesis_readiness.py` | `DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET`; failed gates: actual-R minimum, winner minimum, MBP10 candidate minimum |
| Limit intent reconciliation | `python scripts\audit_orderflow_limit_intent_reconciliation.py` | one XAUUSD LIMIT_PLACED row remains an internal intent/counterfactual anomaly, not broker-realized R |
| Forward collection plan | `python scripts\build_orderflow_forward_collection_plan.py` | rebuilt on proxy-expanded defaults; unsupported candidates now `57`, not stale `92` |

## Validated Findings

| Finding | Status | Evidence | Current conclusion |
|---|---|---|---|
| V0 fixed-R path scaling | VERIFIED | full corpus `205197` rows replayed in existing report; rerun output confirmed `23483` TAKE rows and J46 best at `0.190128R` net mean at `0.05R` cost | V0 does not promote an exit policy; it only justified lower-timeframe path refinement |
| V1 MTF path resolution | VERIFIED_REJECTED_FOR_PROMOTION | latest disposition reports J46 `0.163894R` net mean, best lock-only minus J46 `-0.022329R`, samebar-pessimistic target-family delta `-0.077802R` | V1 is diagnostic infrastructure, not an exit-policy candidate |
| V2 structural selector | VERIFIED_DISCOVERY_ONLY | concentration audit recomputed pairwise deltas; `STRUCT_SWING_PROTECTED_V2` mean delta `+0.024514R`; top-four positive cohort share `0.962136` | structural signal exists, but headline winner is concentration-blocked |
| V2 OB-boundary candidate | VERIFIED_DISCOVERY_ONLY | OB-boundary pairwise mean delta `+0.024061R`, sum delta `+105.724281R`, positive in all listed major groups | cleanest V2b candidate, still same-event-log evidence only |
| V2b prospective validation | VERIFIED_BLOCKED | total rows seen `281796`; rows after cutoff `0`; wanted resolved rows after cutoff `0` | V2b is not failed; it is unevaluable until post-cutoff rows exist |
| USDJPY/6J transfer | VERIFIED_REVIEW_OPEN | 9 windows tested; 8/9 strict corr pass; weak window corr `0.825301`; min directional agreement `0.928977`; all best lags zero | no proxy activation yet |
| Proxy-expanded orderflow coverage | VERIFIED_DIAGNOSTIC_ONLY | supported current candidates `58`; manifest-capped supported events `54`; unsupported candidates `57` | GBPUSD/6B and XAGUSD/SI are research-supported; GBPJPY and USDJPY remain blocked/review-open |
| NAS100 orderflow hypothesis | VERIFIED_NOT_READY | orderflow rows `12`; synthetic labels `11`; actual-R labels `1`; synthetic winners/losers `1 / 10`; MBP10 candidate rows `11` | forward collect only; do not register replay |
| XAUUSD limit-intent anomaly | VERIFIED_TELEMETRY_GAP | limit rows audited `1`; broker actual-R rows `0`; pending-discard rows `1`; counterfactual M1 TP rows `1` | execution telemetry gap, not an orderflow alpha datapoint |
| Broad orderflow rule | NOT_VALIDATED | actual broker-R coverage is `1 / 54` candidate feature rows in expanded coverage | no broad orderflow rule or expectancy claim is valid |

## Corrections Made During This Audit

| Issue | Before | After | Files |
|---|---|---|---|
| Forward-plan input staleness | default plan inputs used pre-proxy-expansion artifacts and reported `92` unsupported candidates | defaults now use proxy-expanded manifest/fetch/diagnostic/coverage artifacts and report `57` unsupported candidates | `scripts/build_orderflow_forward_collection_plan.py`, `tests/test_orderflow_forward_collection_plan.py`, `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_13_2026-05-02.*` |
| Current-vs-manifest candidate ambiguity | forward plan showed only manifest-supported events, hiding current source supported count | report now separates current supported candidates `58` from manifest-supported events inside available data cap `54` | same as above |
| Limit-intent count bug | forward-plan JSON action evidence read missing `counts` and showed `limit_rows_audited=0` | action evidence reads reconciliation `synthesis` and now shows `limit_rows_audited=1`, `counterfactual_m1_tp_rows=1` | same as above |
| Current-state stale unsupported list | research state still grouped GBPUSD/XAGUSD with unsupported symbols | updated state distinguishes supported research proxies from unresolved GBPJPY/USDJPY | `.context/00_core/research_current_state.md` |

## Remaining Blockers

| Area | Blocker |
|---|---|
| Path scaling | V2/V2b promotion remains blocked by same-dataset evidence and zero post-cutoff V2b rows |
| Path scaling | V2 swing headline remains concentration-blocked and cannot be generalized |
| Orderflow | Actual broker-R labels are too sparse for expectancy claims |
| Orderflow | NAS100 lacks winner-side sample and MBP10 candidate sample |
| Orderflow | USDJPY/6J remains review-open; GBPJPY needs a separately registered two-book synthetic-cross method |
| Execution labels | LIMIT_PLACED intent cannot be converted into actual R without broker/deal evidence or forward pending-intent telemetry |
| Market data | MBP10 snapshots do not prove order identity, queue position, or iceberg/refresh behavior; MBO remains deferred |

## Valid Base Verdict

The current base is valid for continued research and forward collection, not for promotion. The findings that survive this audit are artifact-backed, recomputed where practical, and explicitly label-separated. The invalid or stale parts found during the audit were tooling/reporting issues, not alpha confirmations: the forward plan was using stale defaults, and its limit-intent evidence field was reading the wrong JSON location.

Next work should continue from this corrected base: collect post-cutoff V2b rows, keep V2/V2b forensics discovery-only, follow the NAS100-first orderflow forward collection plan, and keep every output under `NO_PROMOTION_VERDICT` until a separate promotion dossier exists.
