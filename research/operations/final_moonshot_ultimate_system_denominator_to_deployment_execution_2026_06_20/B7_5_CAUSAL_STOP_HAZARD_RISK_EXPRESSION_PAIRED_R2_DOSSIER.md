# B7.5 Causal Stop-Hazard Risk-Expression Paired Comparison

Decision: `DEEPER_AUTHORITY_GAP_EXPOSED`
Evidence: `ACCEPT`
Structure: `ACCEPT`
Economics: `MIXED_UNRESOLVED`
Downstream authority: `DEEPER_AUTHORITY_GAP_EXPOSED`

Decision reasons:

- `non_hostile_physical_net_r_down_cash_up:net_r=-1.96378776:cash=+1612.01421486`
- `pressure_cohort_outcome_unresolved:broadorigin_730290b8b2d3fc07f83c9320@@2026-06-04T07:45:00+00:00:unresolved_positive_diagnostic_displacement`
- `unscoreable_replacement_trades_require_terminal_outcomes:hostile:count=1`
- `unscoreable_replacement_trades_require_terminal_outcomes:non_hostile:count=2`

## Hostile

- Day: `2026-05-15`
- Candidate identity status: `unavailable_trade_identity_only`
- Physical net-R delta: `+2.15939803R`
- Cash-PnL delta: `+1849.74556362`
- Candidate added/removed/shared: `0/0/0`
- Pressure cohort dispositions: `{"filled_cap_cleared": 3, "scorecard_preserved_scheduler_not_selected": 1}`
- Pressure cohort outcome assessments: `{"BENEFICIAL_NEGATIVE_DISPLACEMENT": 1, "RESOLVED_SCOREABLE_FILL": 3}`
- New unscoreable replacement fills: `1`

The candidate introduced 1 replacement fill(s) without scoreable terminal-R outcomes. Their economics remain unresolved; they are not automatically losses or proof of a flaw.

## Non Hostile

- Day: `2026-06-04`
- Candidate identity status: `exact`
- Physical net-R delta: `-1.96378776R`
- Cash-PnL delta: `+1612.01421486`
- Candidate added/removed/shared: `0/0/6981`
- Pressure cohort dispositions: `{"candidate_preserved_before_scorecard": 1, "filled_cap_cleared": 3}`
- Pressure cohort outcome assessments: `{"RESOLVED_SCOREABLE_FILL": 3, "UNRESOLVED_POSITIVE_DIAGNOSTIC_DISPLACEMENT": 1}`
- New unscoreable replacement fills: `2`

The non-hostile candidate's physical net-R fell while cash PnL rose. That sizing-versus-selection conflict is mixed evidence, not proof that either policy is economically superior.

The candidate introduced 2 replacement fill(s) without scoreable terminal-R outcomes. Their economics remain unresolved; they are not automatically losses or proof of a flaw.

Broker/live/final authority remains false. This artifact decides only the bounded
same-root hostile/non-hostile causal repair; it is not broad generalization or
broker-real economic proof.
