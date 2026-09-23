# LTO031 / LTO032 Databento Credit Replay Manifests - 2026-05-06

**Schema:** `lto031_lto032_databento_credit_replay_manifests_v1`
**Generated:** `2026-05-06T00:26:49.167118+00:00`
**Status:** `DATABENTO_CREDIT_REPLAY_MANIFESTS_READY_ESTIMATE_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

P2 Databento historical-credit replay request contracts. Requests are predeclared and intentionally not fetch-ready until vendor cost estimates exist and caps pass.

No Databento API call, paid fetch, live collector, AI/canary call, or live trading behavior change occurred.

## Credit Policy

- Existing credits only: `True`
- New external cash: `False`
- Estimate before fetch: `True`
- Total cap: `$25.0`
- Daily cap: `$8.0`
- Per-request cap: `$1.0`

## Local Cache Inventory

- Raw files: `113`
- Metadata files: `113`
- Total size MB: `3590.279098`
- Files by schema: `{'mbo': 3, 'mbp-1': 4, 'mbp-10': 38, 'trades': 67}`

## Requests

| Request | Priority | GTOS | Raw symbols | Schema | Status | Fetch ready |
| --- | --- | --- | --- | --- | --- | --- |
| P2_NAS100_NQ_TRADES_DECISION_WINDOW_V1 | 1 | NAS100 | NQ.v.0 | trades | WAITING_FOR_COST_ESTIMATE | false |
| P2_NAS100_NQ_MBP10_DECISION_WINDOW_V1 | 2 | NAS100 | NQ.v.0 | mbp-10 | WAITING_FOR_COST_ESTIMATE | false |
| P2_US30_YM_ES_MBP10_DECISION_WINDOW_V1 | 3 | US30 | YM.v.0, ES.v.0 | mbp-10 | WAITING_FOR_COST_ESTIMATE | false |
| P2_XAUUSD_GC_MBP10_DECISION_WINDOW_V1 | 4 | XAUUSD | GC.v.0 | mbp-10 | WAITING_FOR_COST_ESTIMATE | false |
| P2_XAGUSD_SI_MBP10_DECISION_WINDOW_V1 | 5 | XAGUSD | SI.v.0 | mbp-10 | BLOCKED_SOURCE_DEFINITION_BEFORE_ESTIMATE | false |
| P2_USDJPY_6J_TRADES_DECISION_WINDOW_V1 | 6 | USDJPY | 6J.v.0 | trades | BLOCKED_PROXY_TRANSFER_REVIEW_BEFORE_ESTIMATE | false |
| P2_GBPUSD_6B_TRADES_DECISION_WINDOW_V1 | 7 | GBPUSD | 6B.v.0 | trades | BLOCKED_ALIGNMENT_POLICY_BEFORE_ESTIMATE | false |
| P2_NAS100_NQ_MBO_QUEUE_FOLLOWUP_V1 | 8 | NAS100 | NQ.v.0 | mbo | DEFERRED_UNTIL_MBP10_LEAVES_QUEUE_QUESTION | false |

## Source Separation

- decision_time_features: records with ts_event <= decision_cutoff_utc only
- post_event_labels: records after decision_cutoff_utc used only for labels/outcome diagnostics
- actual_r: broker actual-R remains separate from synthetic path-R
- historical_replay: evidence for live-subscription value, not live operational validation

## Validation

- Fetch-ready requests: `0`
- Validation issues: `[]`

## Safety Counters

- Paid data calls: `0`
- Paid fetch attempted: `False`
- AI calls: `0`
- Order calls: `0`

## NO_PROMOTION_VERDICT

Historical replay manifests are source planning only and do not promote Databento or any trading rule.
