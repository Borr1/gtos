# AUDIT 17: CROSS-DEPS (naming, imports, duplicates, dependencies)

## Code Quality Score: 72/100

## God module
- 1 god module (orchestrator.py 27 dependents — refactor candidate)

## Duplicate code
~710 lines duplicate code:
- JSONL append 9 implementations
- file locking 4
- time-handling 5+
- config loading 3

## Naming inconsistencies: 8
- touch_count_gate_logger hybrid
- pre_ai_gates plural
- 3 loggers no `_shadow_` prefix
- 1 observer-vs-logger

## Type hints
- modern files 95%+
- legacy 10-20%
- overall 60-70%

## Findings
- NO circular imports
- NO stale module references

## Constants vs config
- 3 hardcoded shadow_logs paths
- DEFAULT_LOOKBACK_H4
- dumb_baseline_timeout
- (should move to config)

## Other
- 11 print() calls should be logging

## TOP refactors
- Extract jsonl_utils (2h, 315 lines)
- file_lock (1h, 200 lines)
- Split orchestrator (4-6h)

## Total
18-20h savings 835 lines.

## Strengths
- 89% naming consistency on shadow loggers
- 0 circular imports
