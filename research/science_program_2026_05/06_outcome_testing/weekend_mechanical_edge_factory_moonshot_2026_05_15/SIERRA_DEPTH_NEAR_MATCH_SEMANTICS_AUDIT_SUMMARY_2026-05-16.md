# Sierra Depth Near-Match Semantics Audit

Generated UTC: `2026-05-15T21:06:37Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: delayed/suffixed near-match source semantics only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `candidate_input_rows`: `3`
- `candidate_audit_rows`: `3`
- `unique_candidate_hashes`: `1`
- `parsed_candidate_rows`: `3`
- `near_requirement_rows`: `9`
- `requirement_impact_rows`: `27`
- `substitutable_impact_rows`: `0`
- `not_substitutable_impact_rows`: `27`
- `question_rows`: `3`

## Substitution Status

- `NOT_SUBSTITUTABLE`: `27`

## Coverage Status

- `CANDIDATE_RECORDS_START_AFTER_EVENT_WINDOW`: `27`

## Interpretation Boundary

- The delayed/suffixed NQ files are parser/source-semantics leads only.
- They do not repair the missing exact `NQM26-CME.2026-05-01.depth` source-date requirement.
- Exact source-date file acquisition or an approved equivalent source contract remains required.
