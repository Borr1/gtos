# Raw-OHLC Path Scaling V1 MTF Ambiguity Review

**Date:** 2026-05-02
**Primary report:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_REPORT_2026-05-02.md`
**Event log:** `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_ablation_v1_mtf/raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl`
**Scope:** `FULL_AVAILABLE_CORPUS`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No V2/V3 work started.

## Direct Answers

| question | answer |
| --- | --- |
| Did V1 reduce V0 same-bar ambiguity? | Yes. V0 same-bar policy-event rows fell from 9104 to 6615; 2258 V0 same-bar rows resolved under M1/M5. |
| Did V1 clear all path-ordering ambiguity? | No. V1 still has 6615 same-bar policy-event rows, including 160 on M1, 1417 on M5, and 5038 on M15 fallback. |
| Is there a start-clock leak? | No. Lower-timeframe rows with close_time <= setup decision clock: 0. |
| Did MTF resolution change interpretation? | Yes. The main report flags 5 group/cohort best-variant or lock-vs-J46 sign changes. |
| Can V2 start immediately? | No. V1 has quantified blockers that need explicit acceptance or follow-up before structural level selection. |

## Same-Bar Breakdown

Policy-event rows:

| selected_timeframe | v1_same_bar_rows |
| --- | ---: |
| M1 | 160 |
| M5 | 1417 |
| M15 | 5038 |

Unique setup rows:

| selected_timeframe | unique_v1_same_bar_setups |
| --- | ---: |
| M1 | 64 |
| M5 | 496 |
| M15 | 1429 |

V0 same-bar rows resolved by MTF:

| selected_timeframe | policy_event_rows_resolved | unique_setup_rows_resolved |
| --- | ---: | ---: |
| M1 | 578 | 204 |
| M5 | 1680 | 601 |

Remaining V1 same-bars by variant and selected timeframe:

| variant_id | M1 | M5 | M15 |
| --- | ---: | ---: | ---: |
| BASE_RAW_FIXED_TP | 27 | 272 | 996 |
| J46_J49_ONLY | 15 | 85 | 613 |
| PATH_LOCK_CONSERVATIVE_V0 | 27 | 282 | 1000 |
| PATH_LOCK_HALF_GAIN_V0 | 27 | 282 | 1000 |
| PATH_LOCK_EARLY_BE_V0 | 64 | 496 | 1429 |

Top remaining V1 same-bar concentrations by cohort/timeframe:

| cohort_key | selected_timeframe | v1_same_bar_rows |
| --- | --- | ---: |
| NAS100\|ny\|bullish\|D1 | M15 | 1027 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | M15 | 999 |
| NAS100\|ny\|bullish\|D1 | M5 | 771 |
| USDJPY\|tokyo\|bullish\|D1 | M15 | 649 |
| USDJPY\|london\|bullish\|D1 | M15 | 496 |
| GBPUSD\|london\|bearish\|H4+H1_consensus | M15 | 389 |
| XAUUSD\|ny\|bullish\|D1 | M15 | 378 |
| GBPJPY\|tokyo\|bullish\|D1 | M15 | 259 |
| USDJPY\|tokyo\|bearish\|D1 | M15 | 250 |
| XAGUSD\|london\|bullish\|D1 | M15 | 238 |

## Conclusion Changes

| scope | v0_best_variant | v0_net_mean_r_cost_0.05 | v1_best_variant | v1_net_mean_r_cost_0.05 | interpretation |
| --- | --- | ---: | --- | ---: | --- |
| group: negative_controls | PATH_LOCK_CONSERVATIVE_V0 | -0.108947 | J46_J49_ONLY | -0.150354 | Best variant changed, but both remain negative. |
| group: primary_controlled_family | J46_J49_ONLY | 0.420624 | PATH_LOCK_CONSERVATIVE_V0 | 0.423483 | Lock-vs-J46 sign flips slightly positive under V1. |
| group: target_cohorts | PATH_LOCK_EARLY_BE_V0 | 0.487573 | PATH_LOCK_CONSERVATIVE_V0 | 0.472889 | Lock family still leads J46, but best lock ladder changes. |
| cohort: USDJPY\|london\|bullish\|D1 | BASE_RAW_FIXED_TP | -0.055699 | J46_J49_ONLY | -0.013785 | Negative-control interpretation remains weak/negative. |
| cohort: XAUUSD\|ny\|bullish\|D1 | BASE_RAW_FIXED_TP | 0.420817 | PATH_LOCK_EARLY_BE_V0 | 0.410777 | Dominance-watchlist best variant changes. |

## Methodology Diagnostics

| diagnostic | value | promotion_usable |
| --- | ---: | --- |
| exit_policy_pbo | 0.358974 | false |
| exit_policy_effective_N | 1.501323 | false |
| same_dataset_DSR_language | diagnostic only | false |

## Ambiguity Ledger

| item | status | detail |
| --- | --- | --- |
| M15 fallback same-bars | BLOCKING_OR_ACCEPTANCE_REQUIRED | 5038 policy-event rows remain because lower-timeframe coverage is unavailable for those windows. |
| M5 same-bars | BLOCKING_OR_ACCEPTANCE_REQUIRED | 1417 policy-event rows remain inside M5 bars where M1 was unavailable. |
| M1 same-bars | BLOCKING_OR_ACCEPTANCE_REQUIRED | 160 policy-event rows remain inside M1 bars and cannot be resolved with current OHLC granularity. |
| Start-clock discipline | CLEARED | Lower-timeframe start violations are 0. |
| Cost model | OPEN_LIMITATION | Costs remain sensitivity assumptions, not measured spread/commission/slippage. |
| Promotion | BLOCKED_BY_DESIGN | Same-dataset historical ablation cannot promote an exit policy. |

## Opened Questions

| question | status | detail |
| --- | --- | --- |
| Should V2 proceed with M15 fallback same-bars carried as explicit unresolved outcomes? | OPEN | This would preserve full-corpus scope but keep a known pre-2024/2026 coverage limitation. |
| Should M5 same-bars be accepted where M1 coverage is absent? | OPEN | This is a data-resolution limitation, not a code leak. It still affects variant conclusions. |
| Should M1 same-bars be dropped, pessimistically scored, or retained as unresolved? | OPEN | Current V1 retains them as unresolved to avoid fabricating order inside M1 OHLC. |
| Should V2 be limited to M1/M5-covered windows? | OPEN | That would improve ordering precision but would no longer be the full available corpus and would introduce period-selection risk. |

## Next Steps

| rank | next_step | reason |
| --- | --- | --- |
| 1 | Review same-bar event rows by cohort and variant. | The largest concentrations are in blocked/dominance and negative-control cohorts, but target/primary rows are also affected. |
| 2 | Decide a registered treatment for residual same-bars before V2. | Options are keep unresolved, pessimistic scoring, coverage-subset diagnostic, or data acquisition. |
| 3 | If a treatment is accepted, update the V2 protocol before implementation. | Structural level selection must inherit a fixed path-resolution policy. |
| 4 | Do not start V2 until the above is accepted. | V1 is implemented and replayed, but ambiguity is not cleared. |

## Synthesis

V1 is implemented and full-corpus replayed. It materially reduces M15 same-bar ambiguity and confirms there is no lower-timeframe start-clock leak.

The result does not clear V1 for V2. Remaining ambiguity is quantified and mostly caused by data coverage/fallback, with a smaller but real set of unresolved M1/M5 same-bars. V2 should not begin until the residual same-bar treatment is explicitly registered.
