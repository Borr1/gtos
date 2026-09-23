# Phase 3 Raw-OHLC Prequential Replay Protocol

**Created:** 2026-05-01
**Status:** research/tooling protocol
**Scope:** raw historical candle replay for Phase 3 cohort diagnostics
**Promotion allowed:** no

## Boundary

This protocol extends the truth-layer replay lab downward to raw OHLC candles.
The truth-layer replay already proved that prebuilt opportunity rows can be
evaluated through an observation/scorer boundary. The raw-OHLC adapter adds a
stricter layer: it walks historical M15 candles forward, reconstructs as-of
Component 2 and deterministic pre-AI state from candle windows, locks a cohort
decision, and only then attaches mechanical outcomes.

This is research/tooling only. It does not authorize live trading changes,
prompt edits, risk-policy changes, execution changes, parameter optimization,
or paid AI/API calls.

## Canonical Candle Schema

Raw candle files are MT5 CSV exports with these required columns:

| column | policy |
|---|---|
| `time` | UTC bar-open timestamp from MT5 export |
| `open` | float |
| `high` | float |
| `low` | float |
| `close` | float |
| `volume` | optional numeric field; missing/bad values become 0 for aggregation |

The replay clock is the M15 candle close:

`candle_close_utc = time + 15 minutes`

The adapter sorts all selected symbols by `candle_close_utc`, then `symbol`,
then `session`. File order is never evidence.

## Available Raw OHLC Coverage

Default raw roots:

- `data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1`
- `data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1`

First-version active symbols are derived from the five approved targets plus
negative controls: `GBPJPY`, `GBPUSD`, `USDJPY`, `XAGUSD`.

| symbol | timeframe | status | first | last | rows | note |
|---|---|---|---|---|---:|---|
| GBPJPY | M15 | available | 2022-04-14 11:15:00 | 2026-04-30 23:45:00 | 100012 | primary target |
| GBPJPY | H1 | available | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 26764 | HTF source |
| GBPJPY | H4 | derived | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | n/a | derived from H1 when needed |
| GBPJPY | D1 | available | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 1124 | HTF source |
| GBPJPY | M5 | available | 2024-12-26 11:25:00 | 2026-04-30 23:55:00 | 99941 | inventory only in v1 |
| GBPJPY | M1 | available | 2026-01-23 08:54:00 | 2026-04-30 23:59:00 | 99711 | inventory only in v1 |
| GBPUSD | M15 | available | 2022-04-14 19:00:00 | 2026-04-30 23:45:00 | 100012 | negative control |
| GBPUSD | H1 | available | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 26766 | HTF source |
| GBPUSD | H4 | derived | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | n/a | derived from H1 when needed |
| GBPUSD | D1 | available | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 1124 | HTF source |
| GBPUSD | M5 | available | 2024-12-26 16:50:00 | 2026-04-30 23:55:00 | 99941 | inventory only in v1 |
| GBPUSD | M1 | available | 2026-01-23 09:15:00 | 2026-04-30 23:59:00 | 99722 | inventory only in v1 |
| USDJPY | M15 | available | 2022-04-14 19:00:00 | 2026-04-30 23:45:00 | 100012 | primary and cleared target |
| USDJPY | H1 | available | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | 26768 | HTF source |
| USDJPY | H4 | derived | 2022-01-03 00:00:00 | 2026-04-30 23:00:00 | n/a | derived from H1 when needed |
| USDJPY | D1 | available | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 1124 | HTF source |
| USDJPY | M5 | available | 2024-12-26 17:30:00 | 2026-04-30 23:55:00 | 99941 | inventory only in v1 |
| USDJPY | M1 | available | 2026-01-23 08:58:00 | 2026-04-30 23:59:00 | 99718 | inventory only in v1 |
| XAGUSD | M15 | available | 2022-01-03 01:00:00 | 2026-04-30 23:45:00 | 99195 | cleared target |
| XAGUSD | H1 | available | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | 24847 | HTF source |
| XAGUSD | H4 | derived | 2022-01-03 01:00:00 | 2026-04-30 23:00:00 | n/a | derived from H1 when needed |
| XAGUSD | D1 | available | 2022-01-03 00:00:00 | 2026-04-30 00:00:00 | 1113 | HTF source |
| XAGUSD | M5 | available | 2024-11-29 03:20:00 | 2026-04-30 23:55:00 | 99953 | inventory only in v1 |
| XAGUSD | M1 | available | 2026-01-19 11:39:00 | 2026-04-30 23:59:00 | 99768 | inventory only in v1 |

Native H4 files are absent in the default Phase 3 export. H4 is derived from
H1 for completed historical H4 bars. The current in-progress H4 bar is rebuilt
from already-closed M15 bars under the policy below.

## No-Leak HTF Policy

First-version policy: `partial_from_m15_no_leak`.

At each M15 close:

1. M15 history exposes only bars with `M15.close_time <= replay_clock`.
2. Completed H1/H4/D1 history exposes only native or derived bars whose close
   is no later than the replay clock.
3. The current in-progress H1/H4/D1 bar is reconstructed from M15 rows with
   `period_start <= M15.open_time` and `M15.close_time <= replay_clock`.
4. The final high, low, close, or volume of a still-open H1/H4/D1 bar is never
   read from native HTF CSV.
5. Event logs stamp lookback counts, as-of last closes, and whether a partial
   HTF bar was included.

This is more conservative than the earlier truth-layer builder's
`partial_htf` approximation, because native historical HTF CSVs contain final
bar OHLC that would leak within an unfinished HTF bar.

## Cohort Filter Policy

Target cohort filters are computed from as-of deterministic fields only:

`raw_cohort_key = symbol|session|deterministic_bias|deterministic_bias_source`

The adapter does not read or join `truth_*` fields. The five first-version
diagnostic targets are:

- `USDJPY|tokyo|bearish|D1`
- `GBPJPY|tokyo|bullish|D1`
- `USDJPY|london|bearish|D1`
- `USDJPY|tokyo|bearish|H4+H1_consensus`
- `XAGUSD|london|bullish|D1`

Negative controls:

- `USDJPY|tokyo|bullish|D1`
- `USDJPY|london|bullish|D1`
- `GBPUSD|london|bearish|H4+H1_consensus`

Blocked dominance-watchlist names are excluded by default:

- `NAS100|ny|bullish|D1`
- `US30_cash|ny|bullish|H4+H1_consensus`
- `XAUUSD|ny|bullish|D1`

They can only run if explicitly enabled as blocked controls.

## Decision And Scoring Order

For every replay event:

1. Load rolling M15/H1/H4/D1 windows as of the M15 close.
2. Build Component 2 market state and deterministic pre-AI gate fields.
3. Project an allowlisted observation.
4. Decide `TAKE` or `SKIP` by raw cohort key.
5. After the decision is locked, attach mechanical OB-retest setup/outcome.
6. Record an event log row with the decision, alignment diagnostics, and
   scorer-only outcome.

Mechanical scoring is diagnostic only. Default outcome timeframe is M15 with a
96-bar maximum hold. M1/M5 coverage is inventoried but not used for v1 scoring
because the historical lower-timeframe coverage starts much later than the M15
population.

## Event Log Requirements

Each event log row must include:

- replay index and event key
- candle close, symbol, session, raw cohort key
- pre-AI gate status and `would_send_ai`
- mechanical setup status
- action and decision reason
- `decision_locked_before_outcome=true`
- mechanical outcome and R, if scored
- HTF/M15 as-of alignment diagnostics

The event log must not expose `truth_*` fields or mechanical outcome fields in
the observation projection.

## Guardrails

A clean run requires:

- 0 duplicate event keys
- 0 invalid replay clocks
- 0 future candle exposure violations
- 0 HTF as-of violations
- 0 forbidden observation-field exposure violations
- 0 AI-attempted rows and 0 AI calls

Reports must retain `NO_PROMOTION_VERDICT`. Same-dataset historical replay can
rank, kill, and debug hypotheses; it cannot promote alpha without a separate
prospective or untouched promotion dossier that computes DSR, PBO, effective_N,
and trial-budget accounting.

## Minimum Correct V1

V1 is correct if it:

- reads canonical raw OHLC CSVs,
- walks M15 replay clocks chronologically across symbols,
- exposes rolling windows without future candles,
- aligns H1/H4/D1 with the `partial_from_m15_no_leak` policy,
- filters cohorts without `truth_*` fields,
- writes reproducibility metadata, guardrails, and event logs,
- includes negative controls,
- emits only `NO_PROMOTION_VERDICT`.
