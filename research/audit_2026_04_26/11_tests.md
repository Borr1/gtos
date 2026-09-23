# AUDIT 11: TESTS

2652 tests (2645 ✓ / 6 skip / 1 xfail). 99 test files.

## Skips/xfails
- ALL 6 skips VALID (data-availability guards)
- 1 xfail GENUINE BUG: `identify_structure()` recency weighting (ADR-004 priority HIGH)

## Conftest
5 autouse fixtures (production-path-guard, deployment-phase-shim, isolation for touch_count/direction_emission/sl_beyond_ob loggers).

## Patterns
- NO brittle patterns (no clock dependencies, no network without mock, no hardcoded SHAs)

## Recent additions verified
- 257 tests across 9 files for ADR-006/A.1/A.2/E.2/heartbeat/B.1/C.3 — all properly isolated

## Coverage gaps
- 11 components covered via parent/integration tests (acceptable)
- evaluation_logger no dedicated unit test (verify WF-1 path coverage)

## Status
PRODUCTION-READY.
