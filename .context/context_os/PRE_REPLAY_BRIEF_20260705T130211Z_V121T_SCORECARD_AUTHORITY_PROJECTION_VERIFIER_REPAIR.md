# V121T Pre-Replay Brief

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121S_SIGNED_AUTHORITY_MISSED_SEMANTIC_CROSS_ASSET_ATR_REPAIR_20260514`
- Window: `2026-05-14..2026-05-14`
- Trades: `24`
- Net/gross/final R: `+0.29253564 / +2.11053495 / +2.11053495`
- Cash PnL / risk cash / risk pct: `+24.60851082 / 2406.04506533 / 2.4`
- W/L/F: `9 / 15 / 0`
- Candidate/scorecard/order/trade/missed rows: `7968 / 96 / 51 / 24 / 7942`
- Interpretation: bounded one-day hostile repair proof only; not total reservoir conversion proof.

## Active Process State

No broad replay, verifier, analyzer, pytest, or Python repair process is active before the V121T rerun.

## Baseline Comparison

- V121S behavior matches V121R on this one-day window: 24 trades, `+0.29253564R`, W/L/F `9/15/0`.
- V121R vs V121Q one-day same-window remained `+2.02477337R` net delta with unchanged trade count.
- V89D/V90/V92 remain historical broad comparators; this smoke is not a global reservoir-transfer denominator.

## Current Patch Batch

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  - Scorecard no-final-selection backfill now reports signed package authority candidate id, decision time, canonical/source-bound instance keys, identity status, authority field/family/source boundary, and selector action/reason.
  - Adds `scorecard_reported_package_new_entry_authority_identity_status` and listed identity fields when signed authority identity is reported.
- `verify_denominator_to_deployment_execution.py`
  - Signed package authority identity now compares against the full legitimate current/scheduler identity set.
  - Final-blocked scorecard-window signed probe identity is accepted as projected proof only when no real selected/order/trade identity exists.
  - Valid signed `ultimate_candidate_package_open_reduced_risk_authority` satisfies open-reduced authority even if legacy compatibility flags are absent.
  - Non-order-executable missed dynamic fill-floor bypass rows are diagnostic counts, not executable leaks.
- Tests updated in `tests/test_v4_timewarp_simulated_live_research_loop.py` and `tests/test_denominator_to_deployment_verifier.py`.

## Subagent Findings Incorporated

- Schrodinger: verifier precision around terminal blockers and missed materialization; incorporated in V121S/V121T verifier scans.
- Erdos: missed rows are not fills and cross-asset ATR source projection was real; incorporated in V121S.
- James: scorecard selected-scheduler/signed authority projection mismatch; incorporated in V121T.
- Goodall/Nash/Meitner: stop-hazard cap, transfer ranking, and verifier fatal coverage remain incorporated from V121R.

## Known Mismatch Classes

- Source-bound -> candidate: cross-asset ATR projection fixed in V121S; candidate quality scan is now clean on V121S.
- Candidate -> selector -> scheduler: signed authority alias normalization fixed; remaining V121T work is scorecard-window signed probe projection, not selection behavior.
- Scheduler -> risk -> order: order-executable transfer scan is clean on V121S; cost-refused/source-gap execution remains zero.
- Order -> lifecycle -> fill -> missed: missed counterfactual fill is no longer real fill status; dynamic fill-floor bypass on non-order-executable missed rows is diagnostic.
- Ledger/verifier: scorecard rows are scheduler windows, not always single-candidate rows; V121T preserves that distinction.

## Success Criteria

- Fresh V121T scorecard rows include `scorecard_reported_package_new_entry_authority_*` identity fields for no-final-selection signed package probes.
- `scan_broad_emitted_scheduler_status_authority` bad_counts is `{}`; diagnostic counts preserve the 14 missed dynamic bypass rows.
- `scan_broad_order_executable_transfer_contract` bad_counts is `{}`.
- `scan_broad_candidate_quality_parity` candidate bad counts are `{}`.
- Trade count/R is expected to remain behavior-neutral because this batch is proof/ledger precision. Any behavior delta must be reported but not treated as optimization.

This smoke proves or disproves the local scorecard authority projection repair; it does not prove total reservoir conversion.
