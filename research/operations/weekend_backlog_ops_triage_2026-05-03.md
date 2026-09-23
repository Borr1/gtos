# Weekend Backlog Ops Triage

Date: 2026-05-03
Scope: operations documentation only
Promotion verdict: `NO_PROMOTION_VERDICT`
Status: `FILED_NO_LIVE_CODE_CHANGE`

## Purpose

P2-J asked for small backlog operations docs. This note covers three low-risk items without changing live code:

1. D-6 / O-2 style alias documentation for `NAS100` vs broker-side `NDX100`.
2. O-1 `_trade_index.json` frozen/stale triage refresh.
3. O-8 `live_evaluations` plus `trade_records` enrichment gap audit.

## Evidence Commands

Local read-only counts were taken from:

- `knowledge_base/index/_trade_index.json`
- `knowledge_base/trade_records/**/*.json`
- `knowledge_base/live_evaluations/**/*.jsonl`
- `config/profiles/redacted_account.yaml`
- `scripts/watchdog.ps1`
- `scripts/research/extract_ohlcv_2022_2023.py`
- `scripts/research/extract_ohlcv_history.py`
- `scripts/export_mt5_research_ohlcv.py`
- `research/operations/trade_index_frozen_bug_2026-04-28.md`

No source code, config, risk, prompt, or execution behavior was modified.

## 1. NAS100 / NDX100 Alias Boundary

Current canonical policy:

- GTOS canonical symbol stays `NAS100`.
- redacted_account MT5 broker symbol is `NDX100`.
- Some older FTMO/demo research extraction paths used `US100.cash`; those are broker-context-specific historical aliases, not a global replacement target.

Current evidence:

| File | Current mapping / note |
|---|---|
| `config/profiles/redacted_account.yaml` | `NAS100.market.mt5_symbol: "NDX100"` with comments saying FN uses `NDX100`. |
| `scripts/watchdog.ps1` | maps `"NAS100" = "NDX100"` for FN watchdog checks. |
| `scripts/research/extract_ohlcv_2022_2023.py` | maps `"NAS100": "NDX100"` for the 2022-2023 FN backfill. |
| `scripts/export_mt5_research_ohlcv.py` | default export mapping includes `NAS100:NDX100`. |
| `scripts/research/extract_ohlcv_history.py` | maps `"NAS100": "US100.cash"` and states it was verified against FTMO demo on 2026-04-26. |
| `research/ml_program/audit/data_backfill_2022_2023.md` | explicitly records FN broker symbol `NDX100` and saves data as canonical `NAS100_{TF}.csv`. |

Triage verdict:

- `NAS100` should remain the canonical internal symbol.
- `NDX100` should remain a redacted_account broker-profile alias.
- `US100.cash` should remain historical/demo extraction context unless a current broker profile explicitly uses it.
- Do not bulk rename `NAS100` to `NDX100`, and do not bulk replace `US100.cash`; centralize aliases only through broker/profile mapping.

Recommended next doc/code hygiene:

- Add a small broker-symbol alias table to the next data-extraction README or operations runbook.
- If a future code change is approved, centralize broker alias resolution for extraction scripts so `redacted_account.yaml` and one-shot research extractors cannot drift.

## 2. O-1 `_trade_index.json` Staleness Refresh

Existing ticket:

- `research/operations/trade_index_frozen_bug_2026-04-28.md`

Current read-only counts:

| Source | Count | Latest / status |
|---|---:|---|
| `knowledge_base/index/_trade_index.json` | 129 trades | latest trade date `2026-03-13`; source count `batch_session=129`. |
| `knowledge_base/trade_records/**/*.json` | 263 records | latest records extend to `2026-05-01` across active symbols. |
| `knowledge_base/live_evaluations/**/*.jsonl` | 89 files / 1647 rows | latest rows extend to `2026-05-01`. |

Trade-record counts by symbol:

| Symbol | Records | Earliest | Latest |
|---|---:|---|---|
| GBPJPY | 59 | 2026-04-13T07:15:56.261845+00:00 | 2026-05-01T09:30:05.012277+00:00 |
| GBPUSD | 45 | 2026-04-13T07:30:05.021164+00:00 | 2026-04-29T15:30:05.029101+00:00 |
| NAS100 | 13 | 2026-04-28T07:30:05.010189+00:00 | 2026-05-01T08:15:05.023431+00:00 |
| US30_cash | 36 | 2026-04-13T08:15:54.549732+00:00 | 2026-04-27T10:30:05.016670+00:00 |
| USDJPY | 75 | 2026-04-07T01:15:05.007351+00:00 | 2026-05-01T15:30:05.010989+00:00 |
| XAGUSD | 14 | 2026-05-01T08:15:05.025978+00:00 | 2026-05-01T17:00:05.007998+00:00 |
| XAUUSD | 21 | 2026-04-15T13:15:52.698253+00:00 | 2026-05-01T15:45:05.007519+00:00 |

O-1 triage verdict:

- The old ticket remains valid but its numbers are stale.
- `_trade_index.json` is not just frozen at 2026-04-04; current local evidence shows latest indexed trade date `2026-03-13` and no current `trade_records` ingestion.
- Do not use `_trade_index.json` for current live/OOS counts until a main-thread index rebuild or consumer migration is implemented.

Recommended fix remains:

- Repoint the index builder at `knowledge_base/trade_records/`, or replace consumers with direct `trade_records` aggregation.
- Add a verifier that fails if latest trade-record date is more recent than latest index date by more than one day.

## 3. O-8 `live_evaluations` / `trade_records` Enrichment Gap

Current trade-record field presence from 263 records:

| Field | Present rows |
|---|---:|
| `metadata` | 259 |
| `decision_pipeline` | 259 |
| `mso` | 259 |
| `shadow` | 258 |
| `execution` | 0 |
| `outcome` / `final_outcome` / `status` | 0 |

Decision-pipeline snapshot:

| Metric | Count |
|---|---:|
| AI decision `CANDIDATE` | 259 |
| AI decision missing | 4 |
| L2 passed | 78 |
| L2 failed | 181 |
| L2 missing | 4 |
| `execution is null` | 263 |

Live-evaluation snapshot:

| Metric | Count |
|---|---:|
| Files | 89 |
| Rows | 1647 |
| `decision` present | 1647 |
| `usage` present | 340 |

Live-evaluation CANDIDATE / NO_TRADE rows by symbol:

| Symbol | CANDIDATE | NO_TRADE |
|---|---:|---:|
| GBPJPY | 41 | 345 |
| GBPUSD | 46 | 143 |
| NAS100 | 12 | 75 |
| US30_cash | 36 | 283 |
| USDJPY | 70 | 335 |
| XAGUSD | 14 | 19 |
| XAUUSD | 20 | 208 |

O-8 triage verdict:

- `live_evaluations` is the broad evaluation stream.
- `trade_records` is currently rich for AI/MSO/L2/shadow context but poor for execution/outcome truth.
- `trade_records` cannot serve actual-R, fill/no-fill, slippage, or V3 lifecycle validation without enrichment.
- This directly supports P2-I pending-limit lifecycle telemetry and L-7 close-side slippage as the next observability layer.

Recommended next doc/code hygiene:

- Add an enrichment verifier with required fields by lifecycle state:
  - `REJECTED_L2`: needs AI/MSO/L2 reason, no execution expected.
  - `LIMIT_PLACED`: needs pending-intent lifecycle state after P2-I telemetry exists.
  - `FILLED`: needs MT5 ticket, entry fill, close fill, realized R, slippage, and close reason.
- Do not backfill missing actual-R from research OHLC path touches.
- Add a daily ops count comparing `live_evaluations`, `trade_records`, `_trade_index.json`, and shadow outcome logs.

## Open Follow-Ups

1. Main-thread O-1 fix: rebuild or replace `_trade_index.json` consumers.
2. Main-thread O-8 verifier: classify trade-record completeness by lifecycle state.
3. Alias hygiene: keep `NAS100` canonical and broker aliases profile-scoped.
4. P2-I approval gate: implement pending-limit lifecycle logger only when live-observability changes are approved.

## NO_PROMOTION_VERDICT

This triage does not change trading behavior and does not validate a strategy, symbol, data source, or promotion claim.
