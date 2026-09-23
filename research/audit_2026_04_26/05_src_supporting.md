# AUDIT 05: SRC-SUPPORTING (shadow loggers, gates, classifiers, trackers)

~5,200 LOC across 18+ shadow loggers + gates + classifiers.

## Pattern consistency: 89% (16/18 follow ADR-005)

## Severity
- 4 HIGH (all exception handling at WARNING level — CONFIRMED CORRECT, not anti-pattern as initially feared)
- 3 REFACTOR candidates (defensive getattr duplication across 5 modules, JSONL append duplication 18 loggers, state persistence across 2 loggers)

## NAMING inconsistency
- 3 modules omit `_shadow_` prefix (direction_emission, candidate_features, d1_bias_lag) — LOW severity

## Notes
- `evaluation_logger` has no dedicated unit test
- Tick capture daemon code-complete but never started
- ALL 18 loggers wired into orchestrator/permissions/verification
