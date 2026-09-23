# Raw-OHLC Path Scaling V2 Final Disposition

**Created:** 2026-05-02
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Disposition:** `STRUCTURAL_SIGNAL_PRESENT__NOT_PROMOTION_READY`
**Completion:** `V2_CLOSED_NO_BLOCKING_AMBIGUITY`

## Artifacts

| artifact | path | sha256 |
| --- | --- | --- |
| V2 protocol | `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_PROTOCOL_2026-05-02.md` | `C3A8B31B713DF4ECAB1B91068C0514E7C938CAA77DD5AC288BB218ADAA08995F` |
| V2 spec | `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_SPEC_V1.json` | `5D31926145C27CB20FF579E8418A9631AAC0BECE1FF664BECA722A7ADBF11D52` |
| V2 replay report | `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURAL_LEVEL_SELECTOR_REPORT_2026-05-02.md` | `1D52424A070259F8335A6FAE16B1AF50107BFFEAB7333080C46D082863D22010` |
| V2 summary JSON | `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_20260501T223136Z.json` | `D9CD082C25747C1841A15D9FD2231712C69321F75C67B5F2699F7B84E20B59B7` |
| V2 event log | `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl` | `7EF19C3C5D4666A807E1BE81214CA06DA3FC05FB3945FEC179FD715302B34CF9` |

## Boundary

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No reentry tested.
- Full available corpus used for the final result.

## Direct Answers

| question | answer |
| --- | --- |
| Did V2 beat V1/J46 globally? | Yes on the registered headline metric. `STRUCT_SWING_PROTECTED_V2` net_mean_r_cost_0.05=`0.188405` versus J46 `0.163894`, delta=`+0.024511`. |
| Did it survive pessimistic same-bar stress? | Yes. All-enabled pessimistic best-structural-minus-J46=`+0.058720`. |
| Does that promote live logic? | No. This remains same-dataset historical research and must keep `NO_PROMOTION_VERDICT`. |
| Is the whole structural idea dead? | No. V2 found a structural signal. The failure is not "structure does not matter"; the limitation is that the headline winner is concentrated and not yet a general policy. |
| Which structural family looked most like a real next hypothesis? | The OB-boundary selector is the cleanest next candidate because it is positive across target, primary, cleared, negative-control, and dominance groups, and has much lower truncation than swing/FVG. |
| Which V2 idea failed most clearly? | The composite selector failed. It fired too often, over-tightened exits, and recreated the V1 truncation problem. |
| Is this market, logic, or execution? | It is logic interacting with market structure. Execution was not tested. Market path does offer exploitable structure, but generic "best floor from everything" logic over-locks, and the swing winner is regime/cohort concentrated. |

## Headline Result

| variant | family | resolved_n | gross_mean_r | net_mean_r_cost_0.05 | gross_win_rate | lock_trigger_rate | lock_then_stop_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| J46_J49_ONLY | j46_j49 | 4477 | 0.213894 | 0.163894 | 0.466384 | 0.098507 | 0.006240 |
| PATH_LOCK_HALF_GAIN_V0 | path_lock_only | 3884 | 0.191565 | 0.141565 | 0.531926 | 0.318941 | 0.177846 |
| STRUCT_SWING_PROTECTED_V2 | swing_structure | 4530 | 0.238405 | 0.188405 | 0.604194 | 0.493069 | 0.395380 |
| STRUCT_FVG_MID_EDGE_V2 | poi_boundary | 4530 | 0.236154 | 0.186154 | 0.587417 | 0.535534 | 0.454345 |
| STRUCT_OB_BOUNDARY_V2 | poi_boundary | 4530 | 0.227765 | 0.177765 | 0.507064 | 0.283608 | 0.171617 |
| STRUCT_COMPOSITE_ANY_V2 | composite | 4530 | 0.171828 | 0.121828 | 0.659823 | 0.653245 | 0.630583 |

## Same-Bar Stress

| treatment | all-enabled best structural | best_structural_minus_J46 | best_structural_minus_best_fixed_R |
| --- | --- | ---: | ---: |
| exclude_unresolved | STRUCT_SWING_PROTECTED_V2 | 0.024511 | 0.046840 |
| samebar_breakeven | STRUCT_SWING_PROTECTED_V2 | 0.028378 | 0.069610 |
| samebar_pessimistic | STRUCT_SWING_PROTECTED_V2 | 0.058720 | 0.214642 |

Same-bar ambiguity is not the reason V2 is blocked. The pessimistic stress improves the structural-relative result because structural policies reduce same-bar exposure versus fixed-R lock ladders.

## Pairwise Forensics Versus J46

| candidate | paired_n | mean_delta | candidate_better_n | J46_better_n | truncation_lost_R | rescued_J46_nonpositive_n | rescued_to_positive_n | positive_to_nonpositive_n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| STRUCT_FVG_MID_EDGE_V2 | 4394 | 0.033292 | 1073 | 1054 | 793.079710 | 574 | 573 | 7 |
| STRUCT_SWING_PROTECTED_V2 | 4394 | 0.024514 | 1046 | 807 | 768.847276 | 632 | 631 | 2 |
| STRUCT_OB_BOUNDARY_V2 | 4394 | 0.024061 | 418 | 466 | 257.611975 | 212 | 211 | 9 |
| STRUCT_BOS_LEVEL_V2 | 4394 | 0.022727 | 777 | 776 | 532.688734 | 296 | 295 | 9 |
| STRUCT_LIQUIDITY_RUN_V2 | 4394 | 0.010034 | 781 | 712 | 587.180533 | 316 | 315 | 9 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | 4394 | -0.038580 | 1153 | 1134 | 1151.977482 | 631 | 630 | 7 |
| STRUCT_COMPOSITE_ANY_V2 | 4394 | -0.042453 | 1477 | 1380 | 1471.473712 | 881 | 880 | 0 |

Interpretation:

- FVG and swing generated the largest pairwise gains, but both still paid substantial truncation.
- OB boundary generated a similar positive mean delta with far lower truncation. It did not win the headline net table because it fires less often, but it is structurally cleaner.
- Composite failed because "all structural floors" is not automatically smarter. It over-locks and cuts winners.

## Concentration Audit

The headline winner `STRUCT_SWING_PROTECTED_V2` is not broad enough to promote or accept as a general policy.

| dimension | positive evidence | negative evidence | interpretation |
| --- | --- | --- | --- |
| symbol | NAS100 `+118.162180`, GBPJPY `+63.985417`, US30_cash `+51.982632` | USDJPY `-114.195992`, GBPUSD `-15.153686`, XAUUSD `-1.460202` | Lift is not symbol-uniform. |
| session | NY `+168.684610`, Tokyo `+18.051471` | London `-79.021795` | NY dominance carries the winner. |
| selected timeframe | M1 `+98.893754`, M5 `+96.406067` | M15 `-87.585535` | Lower-timeframe structure is the edge; M15 fallback is adverse. |
| side | LONG `+244.112315` | SHORT `-136.398029` | Strong side asymmetry. |
| role/group | dominance_watchlist `+168.684610` | target_cohorts `-52.864989`, primary_controlled_family `-39.773892`, cleared_non_primary_targets `-13.091097` | Headline winner is not strongest where the original target thesis wanted it. |

Top positive cohorts for `STRUCT_SWING_PROTECTED_V2`:

| cohort | n | sum_delta_vs_J46 | mean_delta | share_of_positive_lift |
| --- | ---: | ---: | ---: | ---: |
| NAS100\|ny\|bullish\|D1 | 732 | 118.162180 | 0.161424 | 0.3910 |
| GBPJPY\|tokyo\|bullish\|D1 | 455 | 63.985417 | 0.140627 | 0.2117 |
| USDJPY\|tokyo\|bearish\|H4+H1_consensus | 257 | 56.623685 | 0.220326 | 0.1874 |
| US30_cash\|ny\|bullish\|H4+H1_consensus | 278 | 51.982632 | 0.186988 | 0.1720 |

Top four positive cohorts explain roughly 96% of the positive lift before offsetting losses. This is not a broad policy.

Top negative cohorts:

| cohort | n | sum_delta_vs_J46 | mean_delta |
| --- | ---: | ---: | ---: |
| USDJPY\|tokyo\|bearish\|D1 | 219 | -103.759309 | -0.473787 |
| USDJPY\|london\|bearish\|D1 | 149 | -74.108719 | -0.497374 |
| GBPUSD\|london\|bearish\|H4+H1_consensus | 715 | -15.153686 | -0.021194 |
| XAUUSD\|ny\|bullish\|D1 | 467 | -1.460202 | -0.003127 |

## What Worked

| item | evidence | why it worked |
| --- | --- | --- |
| Structural floors beat fixed-R globally | Best structural-minus-J46=`+0.024511`; best fixed-R-minus-J46=`-0.022329`. | Structure adapts to actual pullback/support behavior instead of imposing a fixed R ladder. |
| MTF path resolution remained useful | selected timeframes: M1=774, M5=4738, M15=7319; lower-TF start violations=0. | The measurement layer resolves enough path order to make structural candidates testable without leakage. |
| Protected swing floors improved headline net | `STRUCT_SWING_PROTECTED_V2` net_mean_r_cost_0.05=`0.188405`; pairwise delta=`+0.024514`. | Confirmed pullback swings often lock profit after a real structural reaction, not at arbitrary R. |
| OB boundary showed coherent structural behavior | Pairwise delta=`+0.024061`; truncation_lost_R=`257.611975`, far below swing/FVG/composite. | OB boundary fires less often and closer to actual defended structure, so it truncates fewer winners. |

## What Failed

| item | evidence | why it failed |
| --- | --- | --- |
| General promotion of `STRUCT_SWING_PROTECTED_V2` | target_cohorts pairwise sum_delta=`-52.864989`; M15 sum_delta=`-87.585535`; SHORT sum_delta=`-136.398029`. | The headline lift is concentrated in lower-TF, LONG, NY/dominance pockets. |
| Composite "use every structural floor" | pairwise mean_delta=`-0.042453`; truncation_lost_R=`1471.473712`; lock_then_stop_rate=`0.630583`. | Too many floors means over-locking. It protects losers but destroys too much right-tail payoff. |
| Displacement halfback as a standalone exit | net_mean_r_cost_0.05=`0.118598`; pairwise mean_delta=`-0.038580`. | Halfback is too close and too frequent, behaving like an aggressive early lock. |
| Fixed-R lock-only thesis | best fixed-R net_mean_r_cost_0.05=`0.141565`, below J46 `0.163894` and below best structural `0.188405`. | V1 root cause stands: fixed R is too blunt. |

## Structural Event Catalog Closure

| family | V2 answer |
| --- | --- |
| confirmed swing/protected swing | Works as a headline signal, but concentration blocks general-policy acceptance. |
| BOS broken level | Positive versus J46 but weaker than swing/FVG/OB. |
| FVG midpoint/protective edge | Strong pairwise gain, but target/cleared groups are negative and truncation remains high. |
| OB protective boundary | Best structural next-hypothesis candidate due lower truncation and broader group positivity. |
| liquidity run/equal level | Mildly positive versus J46, not enough to lead. |
| displacement halfback | Rejected as standalone. |
| composite any-structure | Rejected. |
| breaker, round number, reentry, higher-timeframe composite | Not answered by V2; these require fresh registration because they add state reconstruction or risk accounting. |

## Ambiguity Ledger

| ambiguity | status | resolution |
| --- | --- | --- |
| Same-bar ordering | ANSWERED_NOT_BLOCKING | Pessimistic same-bar treatment still gives best structural-minus-J46=`+0.058720`. |
| Lower-timeframe leakage | CLEARED | M1/M5 rows start strictly after the setup candle close; lower-TF start violations=`0`. |
| Future swing confirmation leakage | CLEARED | Confirmed swing candidates require two later selected-timeframe bars; tests cover the lag. |
| Cost model | QUANTIFIED_NOT_MEASURED | Report uses 0/0.02/0.05/0.1R round-turn sensitivity. Historical OHLC has no reliable spread/slippage. |
| Concentration | ANSWERED_BLOCKS_GENERAL_POLICY | Headline winner is concentrated in lower-TF LONG/dominance pockets and is negative in target cohorts. |
| Structural event completeness | ANSWERED_FOR_V2_SCOPE | Broad catalog registered. Breaker, round-number, HTF composite, and reentry require separate hypotheses. |
| Live promotion | BLOCKED_BY_DESIGN | Same-dataset historical replay cannot promote live trading logic. |

## Opened Questions

| question | status | answer |
| --- | --- | --- |
| Is structural path scaling worth continuing after V2? | ANSWERED_YES | V2 produced positive structural signals that beat J46 and fixed-R on full corpus. |
| Is the headline winner promotable as-is? | ANSWERED_NO | `STRUCT_SWING_PROTECTED_V2` is concentration-blocked. |
| Which family should be the next registered hypothesis? | ANSWERED | OB boundary is the cleanest next candidate; swing protected can be retained as a comparison arm, not the headline hypothesis. |
| Did V2 prove reentry is needed? | ANSWERED_NO | V2 did not test reentry. The next step should validate structural level quality before adding risk-budgeted reentry complexity. |
| Did the market fail the idea? | ANSWERED_NO | Market paths contain structural information; the failure mode is policy selection and concentration, not absence of favorable structure. |
| Did execution fail the idea? | ANSWERED_NO | No live execution was tested. Execution remains outside V2. |

## Next Steps

| rank | next_step | reason |
| ---: | --- | --- |
| 1 | Register a V2b structural-family validation hypothesis centered on OB-boundary floors, with swing-protected and FVG as comparison arms. | OB boundary has lower truncation and broader group positivity than the headline swing winner. |
| 2 | Add explicit concentration gates before any next replay is treated as research-accepted. | V2 headline passed global metrics but failed broadness. |
| 3 | Keep reentry/V3 blocked until structural level selection is validated. | Reentry would add risk accounting and a second fill; V2 has not earned that complexity yet. |
| 4 | Preserve `NO_PROMOTION_VERDICT` on all V2/V2b artifacts. | Same-dataset historical research cannot promote live logic. |

## Synthesis

V2 did not fail the way V1 failed. V1 showed fixed-R locks were too blunt. V2 showed that structural floors are materially better than fixed-R floors and can beat J46 on the full available corpus. The truth is narrower than the headline: the best net policy, protected swing, is a lower-timeframe LONG/dominance-pocket signal and is not broad enough to promote or accept as a general rule.

The useful discovery is that structural level selection matters, and the cleanest next structural hypothesis is not "use every structure" or "trail every swing." It is a more selective POI-boundary hypothesis, especially OB-boundary floors, because that family produced positive pairwise performance with materially less winner truncation. V2 is therefore closed with no blocking ambiguity: structural path scaling remains alive, but only as a fresh validation hypothesis, not as a promoted policy.
