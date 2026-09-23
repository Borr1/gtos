# V211 Pre-Final Subagent Findings

Generated: `2026-07-09T08:23:35Z`

Scope: read-only sidecar audits while
`BROAD_LIVE_AS_IF_REPLAY_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
was still running. These findings guide the next repair only after V211
terminal artifacts exist.

Broker/live/final remain false.

## Incorporated Sidecars

- Gauss: comparator/value-transfer audit.
- Ptolemy: risk-expression ladder audit.
- Plato: scheduler/order/fillability transfer audit.
- Galileo: lifecycle/exit/stop-geometry audit.

All four sidecars were read-only. No sidecar ran a broad replay or changed code.

## Shared Root Diagnosis

The completed negative behavior through V209 is not source/candidate shortage:
five-day candidate and scorecard counts stay essentially fixed around
`25006` candidates and `288` scorecards. The failure is B7 value transfer after
generation:

- V92: `25006` candidates, `288` scorecards, `239` order events, `51` trades,
  net `+29.35570236R`.
- V97: `25006` candidates, `288` scorecards, `196` order events, `47` trades,
  net `+13.89627731R`.
- V198: `25006` candidates, `288` scorecards, `178` order events, `75` trades,
  net `-3.84033809R`.
- V205: `25006` candidates, `288` scorecards, `172` order events, `73` trades,
  net `-5.20239659R`.
- V209: `25006` candidates, `288` scorecards, `50` order events, `18` trades,
  net `-3.47466796R`.
- V210: one-day proof only, `8864` candidates, `96` scorecards, `9` order
  events, `2` trades, net `+0.52110312R`, verifier `ok=true`.

The later B7 path removed the old positive winner cohorts and admitted a
smaller set of weak selected-policy/open-reduced replacements.

## Comparator Finding

V209 versus positive baselines:

- vs V89D: removed `55` trades with `+34.14936711R`, added `17` trades with
  `-4.26313181R`.
- vs V90: removed `49` trades with `+29.18019940R`, added `16` trades with
  `-3.17850255R`.
- vs V92: removed `49` trades with `+29.69389019R`, added `16` trades with
  `-3.17850255R`.
- vs V97: removed `46` trades with `+13.74825578R`, added `17` trades with
  `-3.49466796R`.

Removed positive cohorts concentrate in `XAUUSD`, `USDJPY`, `XAGUSD`, and
`USDCAD`, mostly `target_reached_before_stop` plus profitable giveback/
protective-stop winners.

Added negative cohorts concentrate in `GER40`, `NAS100`, `SPX500`, `UK100`,
and one `XAUUSD` loser, mostly selected-policy stop-loss rows.

## Risk-Expression Finding

Reduced-risk dominance is real, not just reporting:

- V209 order rows: `50/50` effective `open-reduced-risk`.
- V210 order rows: `9/9` effective `open-reduced-risk`.
- Direct order-ledger read found V209 raw actions `24` open-reduced and `26`
  reject, all effective open-reduced; V210 raw actions `7` open-reduced and
  `2` reject, all effective open-reduced.
- All checked order rows had `full_risk_allowed=false`,
  `full_risk_applied=false`, and missing `risk_pct_basis`.

Risk finalizer is active but selects no reallocations:

- V210: `36` reallocation candidates, `4` admitted, `2` quality-blocked,
  `0` selected.
- V209: `240` reallocation candidates, `36` admitted, `0` selected.

Gap to patch after V211 if confirmed:

- preserve explicit `risk_pct_basis` / `risk_pct_basis_source` for positive-risk
  order/trade/scorecard/missed rows;
- make route verifier fatal when positive-risk rows lack risk basis;
- expose finalizer admitted-candidate rank/transfer-dominance/headroom and exact
  selected/not-selected reason.

## Scheduler / Order / Fillability Finding

V210 one-day transfer collapse:

- package axes: `1101`;
- candidate-generated axes: `853`;
- scorecard/order axes: `4`;
- filled axes: `2`.

V210 leakage labels:

- `candidate_generated_broker_cost_refused_not_executable`: `201` source axes,
  blocked `2462`, blocked net `-731.91964536R`;
- `candidate_generated_not_scheduler_selected`: `137` source axes, missed
  `1230`, missed net `-119.29120177R`;
- `candidate_generated_selector_reduce_risk_not_scheduler_selected`: `30`
  source axes, missed `2165`, missed net `-279.47926184R`;
- `scheduler_selected_no_trade`: `2` source axes, missed `195`, missed net
  `+9.05994266R`.

Primary correctness target if V211 confirms this shape:

- patch risk-finalizer transfer so admitted same-window executable
  replacements are not dropped into `zero_trade_no_risk_admitted_candidate` or
  `no_risk_admitted_candidate` when the selected candidate is rejected;
- patch selector-to-scheduler authority mapping where open-reduced/reduce-risk/
  source-required candidates are demoted to non-risk-bearing despite executable
  package authority;
- patch order contract materialization where an available passive-limit/immediate
  route still becomes `effective_order_type=none`.

## Lifecycle / Exit Finding

V209 is not mainly an exit-threshold tuning failure. It is a transfer/
composition failure.

V209 losing close-reason bucket:

- `selected_policy_replay:stop_loss`: `7` trades, `-7.67990484R`.
- `profit_harvest_mfe_capture_v4_replay_giveback_close`: `6` trades,
  `+1.55140362R`.
- `selected_policy_replay:giveback_close`: `2` trades, `+1.38359509R`.
- `profit_harvest_mfe_capture_v4_replay_protective_stop`: `3` trades,
  `+1.27023817R`.

All seven V209 stop-loss losers were open-reduced, `0.25%`, ordered-path
fills, no target touch, stop touch present. Most were off-session index trades.

Highest-leverage repair if V211 remains negative:

- winner-preserving scorecard-to-order transfer, not a first-pass
  profit-harvest tweak;
- compare any new open-reduced/off-session index candidate against the
  displaced same-window V89D/V90/V92/V97 cohort before it consumes order/trade
  headroom;
- make selected-policy executable-quality, stop-hazard reallocation,
  passive-limit/fill-floor, and off-session marketability gates cohort-
  preserving rather than letting weak GER40/NAS100/SPX500/UK100 stop-loss
  replacements displace positive XAUUSD/USDJPY/XAGUSD/USDCAD winners.

## Current Rule

Do not patch from these findings alone while V211 is in flight. First parse
V211 summary/trade/order/missed/bucket/flow/parity artifacts. If V211 confirms
the same transfer/composition failure, patch the same-root chain:

`selector/admission -> scheduler ranking/reallocation -> risk finalizer -> order/fillability -> selected-policy quality`.

Do not reopen cost-only tuning as the primary batch unless V211 evidence
contradicts these findings.
