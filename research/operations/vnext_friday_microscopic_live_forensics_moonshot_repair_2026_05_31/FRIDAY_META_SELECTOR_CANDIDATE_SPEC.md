# Friday Meta-Selector Candidate Spec

Status: design input, not a new live execution gate.

The current London liquidity-sweep and displacement-continuation quality predicates remain unchanged, but their evidence anchor is repaired from weekend-only artifacts to clean Friday plus broad selected replay support.

## Candidate Inputs

- session and origin-family interaction
- selected-cell risk proof presence
- spread/R at candidate
- MFE/MAE path shape from Stage 05
- current selected policy and broker-ready denominator status
- broad selected historical family/session metrics

## Guardrails

- Do not add new execution-blocking predicates from Friday alone.
- Treat gross historical R as source-bound proxy where cost fields are missing.
- Preserve positive non-configured families as meta-selector features until cost/stress and split checks exist.

Current rule decision: `keep_execution_predicates_reanchor_evidence_metadata_no_rule_expansion`.
