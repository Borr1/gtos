# Lane 5 Data Source Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify Lane 5 D-1/D-4/D-5/D-12 against local data-source evidence.

## Local Inventory

- Tick capture symbols with parquet files: `7/7`; max days for any symbol: `5`.
- Tick helper files: capture daemon `True`, feature helper `True`.
- CFTC normalized rows: `410` across GTOS symbols `XAUUSD`.
- LBMA normalized rows: `2037` for metals `gold, silver` and symbols `XAGUSD, XAUUSD`.
- 2021 M15 probe symbols with any rows: `XAGUSD`.

## Task Classifications

| id | status | blocker / trigger | candidate strength |
| --- | --- | --- | --- |
| D-1 | DEFERRED_WITH_TRIGGER | Tick capture exists but local history is only 5 days at best; MT5 retail volume/last fields are not a real volume/dollar substrate. | not_applicable_data_substrate |
| D-4 | BLOCKED_WITH_REASON | CFTC fetcher and gold XAUUSD cache exist, but no local FX COT contract mappings/rows are present. | not_applicable_data_source |
| D-5 | BLOCKED_WITH_REASON | LBMA gold/silver fix calendar exists, but no local Krohn-Mueller-Whelan FX-fix source/cache is present. | not_applicable_data_source |
| D-12 | BLOCKED_WITH_REASON | Current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice. | not_applicable_data_availability |

## Interpretation

- `D-1` is deferred, not done: tick capture exists, but volume/dollar/imbalance bars are still blocked by MT5 retail substrate limits and short local tick history.
- `D-4` is blocked as a full backlog item: the CFTC COT fetcher and XAUUSD gold cache exist, but the requested FX positioning side is not locally mapped/cached.
- `D-5` is blocked as a full backlog item: LBMA gold/silver fix calendar exists, but the KMW FX-fix source is absent locally.
- `D-12` is blocked by broker history availability: current 2021 probe does not provide full all-symbol pre-2022 M15 coverage.

## Source Files

- `research/ml_program/MASTER_BACKLOG.md`
- `data/ticks/`
- `data/mt5_research_exports/history_availability/`
- `data/mt5_research_exports/tick_availability/`
- `data/external/status/`
- `data/external/normalized/`
- `src/components/external_feeds.py`
- `scripts/fetch_external_feeds.py`

## NO_PROMOTION_VERDICT

This artifact classifies data-source readiness only. It does not validate, promote, or modify live trading behavior.
