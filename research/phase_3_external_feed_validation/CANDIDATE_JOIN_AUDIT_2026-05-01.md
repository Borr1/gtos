# Phase 3 Candidate Join Audit

**Date:** 2026-05-01
**Status:** candidate/opportunity join built; validation substrate improved; no alpha claim
**Scope:** `calendar_macro_bundle_v1`, shadow-only. No live trading logic, prompt, orchestrator, or production config change.

## What Changed

Implemented `scripts/build_external_feed_candidate_dataset.py`, which joins GTOS CANDIDATE rows to no-lookahead external-feed validation snapshots by exact symbol plus M15 candle close.

Scope note: this artifact uses the then-current live/shadow candidate log. It is not a 2022-2026 historical AI-candidate replay. The 72 CANDIDATE rows below are recent live/shadow coverage only.

Implemented `scripts/export_mt5_research_ohlcv.py`, a read-only, versioned MT5 exporter for research data. It writes under ignored `data/mt5_research_exports/` and does not place, modify, or cancel orders.

The candidate join also supports a trade-specific synthetic opportunity label using the existing `src.research_infra.dumb_baseline.resolve_mechanical_outcome` resolver. This is a candidate-R proxy, not live execution P&L.

## Commands Run

```powershell
python -m pytest tests/test_external_feeds.py -q -p no:cacheprovider
python scripts/export_mt5_research_ohlcv.py --start 2026-04-25T00:00:00Z --end 2026-05-02T00:00:00Z --label phase3_candidate_gap_20260501 --timeframes M15 --yes-live-readonly
python scripts/build_external_feed_snapshots_historical.py --data-dir data/mt5_research_exports/phase3_candidate_gap_20260501 --start 2026-04-27T00:00:00Z --end 2026-05-01T04:00:00Z --write --label phase3_m15_candidate_gap_external_v1
python scripts/build_external_feed_validation_dataset.py --data-dir data/mt5_research_exports/phase3_candidate_gap_20260501 --snapshot-label-contains phase3_m15_candidate_gap_external_v1 --label phase3_m15_candidate_gap_validation_v1 --bundle-id calendar_macro_bundle_v1 --write
python scripts/build_external_feed_candidate_dataset.py --validation-label-contains phase3_m15_calendar_macro_validation_v3 --validation-label-contains phase3_m15_candidate_gap_validation_v1 --label phase3_candidate_calendar_macro_join_union_v2 --simulate-opportunity --ohlcv-dir data/mt5_research_exports/phase3_candidate_gap_20260501 --ohlcv-dir data/historical_2026 --write
```

Test result: `36 passed`.

## Generated Artifacts

Ignored research data:

```text
data/mt5_research_exports/phase3_candidate_gap_20260501/manifest.json
data/external/features/{SYMBOL}/phase3_m15_candidate_gap_external_v1_20260501T005921Z.jsonl
data/external/validation/calendar_macro_bundle_v1/phase3_m15_candidate_gap_validation_v1_summary_20260501T005926Z.json
data/external/validation/calendar_macro_bundle_v1/candidate_join/phase3_candidate_calendar_macro_join_union_v2_summary_20260501T010216Z.json
data/external/validation/calendar_macro_bundle_v1/candidate_join/phase3_candidate_calendar_macro_join_union_v2_20260501T010216Z.jsonl
```

The committed artifacts are this report plus the code/tests that regenerate them.

## MT5 Export Result

Read-only export from redacted_account live account `0` succeeded. No orders were sent.

| File symbol | MT5 symbol | M15 rows | First bar UTC | Last bar UTC |
|---|---|---:|---|---|
| GBPJPY | GBPJPY | 398 | 2026-04-27 00:15 | 2026-05-01 03:45 |
| GBPUSD | GBPUSD | 400 | 2026-04-27 00:00 | 2026-05-01 03:45 |
| NAS100 | NDX100 | 380 | 2026-04-27 01:00 | 2026-05-01 03:45 |
| US30_cash | US30 | 380 | 2026-04-27 01:00 | 2026-05-01 03:45 |
| USDJPY | USDJPY | 400 | 2026-04-27 00:00 | 2026-05-01 03:45 |
| XAGUSD | XAGUSD | 380 | 2026-04-27 01:00 | 2026-05-01 03:45 |
| XAUUSD | XAUUSD | 380 | 2026-04-27 01:00 | 2026-05-01 03:45 |

## Candidate Join Coverage

Input shadow log: `shadow_logs/candidate_features_log.jsonl`.

| Metric | Count |
|---|---:|
| Shadow rows read | 418 |
| CANDIDATE rows kept | 72 |
| External snapshots matched | 66 |
| External snapshots missing | 6 |
| Trade records matched | 66 |
| Actual realized-R in trade records | 0 |
| Synthetic opportunity R available | 29 |

The six unmatched rows are all off-boundary candidate timestamps such as `00:16`, `01:31`, `00:20`, and `00:25`. The join intentionally does not force these onto a nearby M15 candle.

## Synthetic Opportunity Labels

Outcome resolver semantics:

- Pending-limit fill required.
- Same-bar fill plus TP/SL is `SAME_BAR` with no R label.
- SL-first rule applies after fill.
- Maximum hold is 96 M15 bars.
- OHLCV roots require a near future bar; the join rejects multi-day gap bridges before falling back to another root.

Synthetic outcomes:

| Outcome | Count |
|---|---:|
| TP | 14 |
| SL | 13 |
| TIMEOUT | 2 |
| NO_ENTRY | 27 |
| SAME_BAR | 10 |
| INVALID | 6 |

Resolved synthetic R only: `n=29`, sum `+9.3602R`, mean `+0.3228R`, wins `16`, losses `13`.

By symbol:

| Symbol | Resolved n | Sum R | Mean R |
|---|---:|---:|---:|
| GBPUSD | 9 | +13.5031 | +1.5003 |
| GBPJPY | 4 | +4.3571 | +1.0893 |
| XAUUSD | 2 | +3.0000 | +1.5000 |
| USDJPY | 3 | -3.0000 | -1.0000 |
| NAS100 | 11 | -8.5000 | -0.7727 |

This is not statistically actionable. It is a substrate artifact that proves the join/label path works.

## External-Feature Availability On Matched Candidates

Among the 66 matched candidate rows:

| Source family | Candidate rows available | Interpretation |
|---|---:|---|
| FRED macro | 66 | Usable immediately for candidate-level diagnostics. |
| LBMA calendar | 2 | Only XAU/XAG candidates get metal-fix context. |
| CFTC COT | 2 | Current mapping only gives gold context on XAUUSD. |
| WGC | 0 | Correct PIT behavior; imported workbooks are not historical candidate context except after import. |
| FlashAlpha GEX | 0 | Correct PIT behavior; no NAS100/US30/XAU/XAG candidates after the May 1 GEX fetch yet. |

## Current Verdict

We are no longer blocked at ingestion. We now have a candidate-level, no-lookahead validation substrate with a first trade-specific label path.

We are still blocked from a real DSR/PBO alpha verdict by effective N. The resolved synthetic candidate-R set is only 29 rows, and actual realized-R is absent from trade records. Any feature claim here would violate the project methodology.

## Next Actions

1. Keep daily read-only MT5 M15 export plus external-feed snapshot generation running so the candidate join grows without manual recovery.
2. Add a first diagnostic evaluator that reports baseline-vs-bundle lift but suppresses verdicts until effective N and PBO/DSR gates are met.
3. Add clean CFTC mappings for additional instruments only where the futures contract proxy is defensible.
4. Keep FlashAlpha forward collection active; it becomes testable only after post-fetch NAS100/US30/XAU/XAG candidates accumulate.
5. Investigate why six candidate rows have off-boundary timestamps and keep them quarantined until the candle-close source is unambiguous.
