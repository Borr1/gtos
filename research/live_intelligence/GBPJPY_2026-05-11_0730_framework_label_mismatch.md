# GBPJPY 2026-05-11 07:30 Framework Label Source Diagnostic

Created: 2026-05-11T10:37:45Z

## Observation

Candidate `GBPJPY_2026-05-11T07:30:00+00:00` has an outer strategy-follow row
`framework=ob_retest`, but the decision reasoning and L2 verifier identify the
effective setup as `fvg_fill`.

Evidence from `shadow_logs/strategy_follow_candidates.jsonl`:

- `candidate_id`: `GBPJPY_2026-05-11T07:30:00+00:00`
- outer `framework`: `ob_retest`
- `h1_setup.poi_type`: `FVG`
- `h1_setup.explanation`: says the qualifying unfilled bullish M15 FVG fired
  and `ob_retest` had no qualifying H1 OBs
- `verification.passed`: `true`
- L2 checks:
  - `h1_poi_exists`, `ob_zone`, `entry_in_ob`, and `sl_beyond_ob` skipped
    because the effective framework was `fvg_fill`
  - `entry_in_fvg` passed for entry `213.533`

## Classification

This is a source-diagnostic label mismatch, not a daemon restart issue and not a
broker/order/account issue. The verifier routed the candidate as FVG and passed;
the misleading field is the outer `framework` label retained in the forward
capture row.

## Operational Boundary

Observation only. This note does not change live trading behavior, validation,
promotion, order handling, risk, execution, prompts, config, selectors, safety,
or canaries.

