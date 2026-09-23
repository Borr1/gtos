# GTOS Primitive-Science Goal Program - 2026-05-06

**Status:** `SCIENCE_GOAL_PROGRAM_READY_RESEARCH_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Schema:** `science_goal_program_control_v1`
**Generated:** `2026-05-06T00:00:00+00:00`

## Purpose

Turn primitive sciences into GTOS mechanisms, preregistered hypotheses, shadow-only evidence lanes, and later promotion dossiers only if evidence survives.

This is a research-control scaffold. It does not launch trades, change prompts, alter risk, modify execution, call canaries, call MT5, fetch paid data, or produce a promotion verdict.

## Launch Order

- `coordinator_first`: G0
- `parallel_wave_1_max_6`: G1, G2, G3, G4, G5, G6
- `parallel_wave_2_max_5`: G7, G8, G9, G10, G11
- `cross_domain_second_pass`: G1, G2, G3, G4, G5, G6, G7, G8, G9, G10, G11
- `red_team_after_first_synthesis`: G12

Maximum parallel science lanes: `8`

## Lanes

| Lane | Role | Domain | Worktree | Neighbors |
| --- | --- | --- | --- | --- |
| G0 | coordinator | research governance | C:\tmp\gtosg\G0 | G1, G4, G9 |
| G1 | science_lane | validation, probability, statistics, causality | C:\tmp\gtosg\G1 | G2, G9, G10 |
| G2 | science_lane | stochastic processes, time series, tails | C:\tmp\gtosg\G2 | G1, G3, G10 |
| G3 | science_lane | geometry, fractals, signal processing | C:\tmp\gtosg\G3 | G2, G4, G6 |
| G4 | science_lane | market microstructure, order book, auction | C:\tmp\gtosg\G4 | G3, G6, G11 |
| G5 | science_lane | behavioral finance, psychology, game theory | C:\tmp\gtosg\G5 | G4, G6, G7 |
| G6 | science_lane | momentum, continuation, breakout, mean reversion | C:\tmp\gtosg\G6 | G3, G5, G10 |
| G7 | science_lane | macro, cross-asset, rates, FX, gold | C:\tmp\gtosg\G7 | G5, G8, G11 |
| G8 | science_lane | options, gamma, volatility risk premium | C:\tmp\gtosg\G8 | G2, G7, G10 |
| G9 | science_lane | AI, ML, RL, LLM trading systems | C:\tmp\gtosg\G9 | G1, G4, G10 |
| G10 | science_lane | execution, entries, exits, risk, portfolio | C:\tmp\gtosg\G10 | G1, G6, G9 |
| G11 | science_lane | data sources and market expansion | C:\tmp\gtosg\G11 | G4, G7, G8 |
| G12 | red_team | methodology red team | C:\tmp\gtosg\G12 | G1, G9, G11 |

## Required Acceptance Tests

- registry schema tests for mechanism, hypothesis, source, and prereg rows
- no-leak tests proving post-outcome fields are excluded from decision-time features
- duplicate active setup tests so repeated rows do not inflate opportunity counts
- label separation tests for broker actual-R, synthetic path-R, lifecycle/no-fill, and observation-only labels
- source contract tests blocking forward-context or paid/incomplete sources from validation_safe
- reproducibility tests for frozen cohort plus prereg spec regeneration
- methodology report with DSR/PBO/effective-N or explicit not_computable reason

## Safety Counters

- AI calls: `0`
- Canary calls: `0`
- MT5 calls: `0`
- Order calls: `0`
- Paid data calls: `0`
- Live behavior changed: `False`

## NO_PROMOTION_VERDICT

All outputs from this program remain research/shadow-only until a separate owner-approved promotion dossier exists.
