# D-11 Missing Old Labels Regeneration

Generated: 2026-05-03T00:41:09.250617+00:00
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question Registered Before Output

GBPJPY and US30_cash old mechanical labels can be regenerated from local data/historical OHLCV with the same F11-style BOS/OB-retest resolver, but must remain a versioned supplement with explicit source flags.

## Headline

- Verdict: `DONE_SUPPLEMENT_GENERATED`.
- GBPJPY and US30_cash labels were generated as a versioned supplement, not merged into the canonical five-symbol cohort.
- Supplemental CSV: `data/historical_2022_2023/trade_cohort_missing_symbols_2026-05-03.csv`.
- Supplemental JSONL: `data/historical_2022_2023/trade_cohort_missing_symbols_2026-05-03.jsonl`.

## Source Flags

| Field | Value |
| --- | --- |
| source_period | old_backfill_builder_window_2022-01-01_to_2024-02-20 |
| mechanical_vs_live_like | mechanical_f11_ob_retest_filled_only |
| label_type | synthetic_mechanical_r |
| as_of_policy | local_static_ohlcv_no_external_fetch |
| merge_policy | supplement_do_not_overwrite_canonical_trade_cohort |

## Symbol Summary

| Symbol | Status | BOS | Filled | NO_ENTRY | Skipped | H1 Source | M15 Source |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| GBPJPY | OK | 330 | 238 | 65 | 27 | data/historical/GBPJPY_H1.csv | data/historical/GBPJPY_M15.csv |
| US30_cash | OK | 354 | 227 | 64 | 63 | data/historical/US30_cash_H1.csv | data/historical/US30_cash_M15.csv |

## Totals

- BOS rows: `684`.
- Supplemental JSONL rows: `684`.
- Supplemental filled CSV rows: `465`.

## Use Constraints

- These rows are synthetic mechanical labels, not broker-realized R and not live-equivalent AI outcomes.
- Any future all-symbol training merge must carry `source_period` and `mechanical_vs_live_like` explicitly.
- This report does not validate a trading rule, model, risk setting, prompt, or live filter.
