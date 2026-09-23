# AUDIT 10: SCRIPTS (scripts/ directory)

90 scripts examined.

## ACTIVE production
- 7 monitors: displacement_logger, api_refusal, ob_continuation, cusum, no_data_alert, correlation_shock, monthly_decay (DISABLED)
- TOOL: canary_test.py, mt5_preflight.py, fn_smoke_trade.py, watchdog_e2e_verify.py, generate_live_state.py

## STALE
- watchdog.bat (5 lines, superseded by .ps1)

## ARCHIVE candidates 40+
- session*_*.py
- smc_a*.py, smc_phase_b.py
- edge_discovery_*.py
- test_opus_*, test_sonnet_*
- (research artifacts no production imports)

## Canary fixtures
- 78 on disk, 75 in manifest, 3 extra orphans (verify), all manifest entries valid
- Last canary 2026-04-26 01:47 PASS 75/75

## Cross-platform
Windows-only ps1+bat appropriate.
