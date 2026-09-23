# V121U Stop-Hazard Public Risk Surface Repair

Current latest completed replay is `BROAD_LIVE_AS_IF_REPLAY_V121T_SCORECARD_AUTHORITY_PROJECTION_VERIFIER_REPAIR_20260514`, covering `2026-05-14..2026-05-14` only. It is a bounded hostile one-day repair proof, not a global million-R reservoir transfer proof.

V121T numbers: 7,968 candidate rows, 96 scorecard rows, 51 order rows, 24 trade rows, 7,942 missed rows. Headline eligible trades: 24, net R `+0.29253564`, gross/final R `+2.11053495`, cash PnL `+24.60851082`, risk cash `2406.04506533`, W/L/F `9/15/0`. Full route verifier selected V121T and passed with zero issues at `2026-07-05T13:37:28Z`.

No broad replay or verifier was running before this patch. One stale long-running `git add` helper was terminated before route work continued.

Subagent findings already incorporated: scorecard signed authority projection, missed counterfactual fill semantics, and cross-asset ATR projection. Active finding in this batch: stop-hazard cap escape through public risk surfaces. Deferred next after this proof: scheduler/reallocation ranking where authority is treated as value instead of eligibility.

Known mismatch chain: source-bound parity is materialized for the V121T bounded window; scorecard authority projection is verifier-clean; risk-to-order still had two V121T diagnostic order rows with `final_approved_risk_pct` / `scheduler_approved_risk_pct` / `selected_cell_risk_pct` above a `0.10` stop-hazard cap even though executable `risk_pct` was zero or capped. That pollutes sizing and downstream allocation truth.

Patch batch: clamp stop-hazard-capped public risk surfaces in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`; extend stop-hazard tests in `tests/test_v4_timewarp_simulated_live_research_loop.py`.

Expected effect before replay: candidate -> scorecard, scorecard -> order, and order -> fill transfer should be neutral. Trade count and net R should be neutral or show only sizing/ledger-side effects. Cost-refused/source-gap execution must remain zero. Capped rows must expose scheduler, selected-cell, runtime, final, and nested risk-expression fields at or below the cap while preserving pre-cap reduction basis.

Proof criteria: focused tests pass; fresh V121U one-day replay has zero cap-applied order/trade rows with any public risk field above cap; route verifier remains green after V121U parity/flow artifacts are selected. This replay proves local truth repair only.
