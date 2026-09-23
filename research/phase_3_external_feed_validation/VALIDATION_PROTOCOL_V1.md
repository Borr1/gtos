# Phase 3 External Feed Validation Protocol V1

**Status:** frozen before outcome evaluation
**Scope:** shadow-only external feeds; no live trading logic, prompt, orchestrator, or config change.

## Registered Bundles

Two bundles are registered in `frozen_feature_bundles_v1.json`:

1. `calendar_macro_bundle_v1`
   LBMA fix calendar, FRED real-yield/USD/vol series, CFTC positioning, and WGC ETF/GDT gold-flow context.

2. `nas_us30_gamma_regime_v1`
   FlashAlpha single-expiry GEX proxies for QQQ/DIA/SPY, FRED volatility proxy, and option-expiry/calendar controls.

Each bundle consumes one Phase 3 validation trial. Individual feature thresholds inside a bundle are not separate promotion claims.

## Target And Outcome

Primary target: `candidate_realized_r` for GTOS candidate/opportunity rows, joined to external-feed snapshots as-of the candle close.

Secondary targets:

- `candidate_win_loss`
- `candidate_no_trade_quality`
- `candidate_directional_decay`

Secondary targets may explain failure modes but cannot promote a source if the primary target fails.

## Baseline

Baseline comparison is the canonical GTOS internal feature set without external feeds, using the same candidate population, labels, splits, and model family.

No result is valid if the external-feed path changes candidate generation, order routing, prompt content, or production config.

## As-Of Rule

Feature snapshots must join on publication/as-of timestamps, not observation dates:

```text
feature.published_at_utc <= candle_close_utc
```

For sources without an authoritative release timestamp in the file, use the fetch/import timestamp and mark the source lag explicitly. Rows that would only be known after the candle close must be unavailable in that snapshot.

## Effective N

Effective N is not raw candle count. It is the number of independent validation paths after CPCV/path grouping and any ONC-style dependence adjustment used by the project methodology.

Promotion requires:

- `effective_N >= 3`
- no single date range, symbol, expiry, or source dominates the effect
- fold-level results reported, not just pooled headline results

## Methodology Gates

Use the project-wide methodology gate from the DSR audit:

- DSR-corrected `p < 0.01`
- PBO `< 0.4`
- cumulative trial budget `N = 200`
- Sharpe noise ceiling `3.078`

Report raw p-values only as diagnostics. The claim lives or dies on DSR/PBO.

## Trial Budget Protection

Allowed:

- one evaluation of `calendar_macro_bundle_v1`
- one evaluation of `nas_us30_gamma_regime_v1`
- pre-declared ablations after the bundle verdict, labeled exploratory

Not allowed:

- choosing individual FRED/WGC/CFTC/GEX thresholds after seeing outcomes
- swapping proxy symbols after fold results are known
- using observation dates as availability dates
- re-running in-sample data to validate a fix

## Invalidation Rules

A source or bundle is invalidated for Phase 3 promotion if any of these occur:

- no DSR-safe lift at bundle level
- PBO fails
- effective N remains below 3
- lift is driven by one symbol, month, expiry, or stale-source artifact
- no-lookahead tests fail
- source terms, quota, or format fragility make the data unreliable for repeatable shadow collection

Invalidation does not require deleting ingestion code. It means the source remains archival/context-only until a new pre-registered hypothesis is approved.

## Operational Commands

Manual/scheduled daily refresh:

```powershell
python scripts/fetch_external_feeds.py daily --expiration 2026-05-15
```

Dataset-level status:

```powershell
python scripts/external_feed_status.py
python scripts/external_feed_status.py --source wgc
python scripts/external_feed_status.py --json
```

WGC remains operator-triggered from downloaded files:

```powershell
python scripts/fetch_external_feeds.py wgc-import --file ETF_Flows_March_2026.xlsx --dataset gold_etf_flows
python scripts/fetch_external_feeds.py wgc-import --file GDT_Tables_Q126_EN.xlsx --dataset gold_demand_trends
```
