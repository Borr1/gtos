# LTO028 XAUUSD Same-Market Extension - 2026-05-05

**Schema:** `lto028_xauusd_same_market_extension_v1`
**Status:** `XAUUSD_SAME_MARKET_EXTENSION_PREREGISTERED_SOURCE_STATUS_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

XAUUSD same-market structural/path extension is preregistered as source-status only. Outcomes remain closed at registration, live rows remain forward snapshots, and XAUUSD/GC/MGC source statuses are documented before any replay evidence is opened.

## Registration

- Registered question: `Do pre-registered XAUUSD.scid/GC slices reproduce structural source-transfer diagnostics without same-slice tuning?`
- Families: `['XAUUSD.scid same-market', 'GC/MGC futures proxy']`
- Evidence classes: `['SAME_MARKET_SOURCE_TRANSFER', 'FUTURES_PROXY_TRANSFER']`
- Opened outcome slices at registration: `0`
- Outcome opening status: `OUTCOMES_CLOSED`
- Target resolved rows before validation discussion: `30`

## Forward Snapshot

- Candidate symbol counts: `{'XAGUSD': 60, 'XAUUSD': 30, 'NAS100': 76, 'GBPJPY': 50, 'USDJPY': 4, 'US30_cash': 40, 'GBPUSD': 57, 'JP225': 20, 'BTCUSD': 24, 'ETHUSD': 23, 'EURJPY': 19, 'AUDJPY': 8, 'CHFJPY': 21, 'UKOIL_cash': 26, 'USDCAD': 25, 'USOIL_cash': 24, 'EURGBP': 27, 'NZDUSD': 3, 'UK100': 1}`
- Evaluation symbol counts: `{'EURUSD': 210, 'GBPJPY': 475, 'XAGUSD': 405, 'USDJPY': 528, 'XAUUSD': 369, 'GBPUSD': 459, 'NAS100': 174, 'GER40': 226, 'UK100': 189, 'US30_cash': 254, 'BTCUSD': 98, 'UKOIL_cash': 96, 'USOIL_cash': 96, 'JP225': 98, 'AUDJPY': 112, 'NZDUSD': 111, 'USDCHF': 124, 'SPX500': 121, 'ETHUSD': 97, 'EURJPY': 98, 'EURGBP': 102, 'USDCAD': 96, 'AUDUSD': 115, 'CHFJPY': 98}`
- XAUUSD live candidate rows: `30`
- XAUUSD live evaluation rows: `369`
- Live rows are not replay outcomes: `True`

## Source Status

| Source | Status | SCID files | Depth files | Evidence class |
|---|---|---:|---:|---|
| `XAUUSD` | `CAUTION_SCID_PRESENT_DEPTH_MISSING` | 1 | 0 | `SAME_MARKET_SOURCE_TRANSFER` |
| `GC` | `READY_SCID_AND_DEPTH_PRESENT` | 1 | 2 | `FUTURES_PROXY_TRANSFER` |
| `MGC` | `READY_SCID_AND_DEPTH_PRESENT` | 1 | 2 | `FUTURES_PROXY_TRANSFER` |

## Gates

| Gate | Passed | Observed | Blocker |
|---|---:|---|---|
| `G0_NO_LIVE_BEHAVIOR_OR_PAID_CALLS` | `True` | `{"ai_calls": 0, "behavior_unchanged": true, "canary_calls": 0, "no_ai_calls": true, "no_canary_required": true, "no_execution": true, "order_calls": 0, "paid_data_calls": 0, "paid_fetch_attempted": false}` | `-` |
| `G1_SOURCE_TRANSFER_REGISTRY_PRESENT` | `True` | `{"registry_has_xau_family": true, "registry_no_promotion": true, "registry_present": true}` | `-` |
| `G2_OUTCOMES_CLOSED_AT_REGISTRATION` | `True` | `{"opened_outcome_slices_at_registration": 0}` | `-` |
| `G3_LIVE_ROWS_SEPARATE_FROM_REPLAY_EVIDENCE` | `True` | `{"live_replay_separated": true, "xauusd_live_candidate_rows": 30, "xauusd_live_evaluation_rows": 369}` | `-` |
| `G4_SOURCE_STATUS_DOCUMENTED` | `True` | `{"GC": {"depth_file_count": 2, "evidence_class": "FUTURES_PROXY_TRANSFER", "latest_depth_utc": "2026-05-04T19:06:29.424031+00:00", "latest_scid_utc": "2026-05-04T19:06:28.012791+00:00", "scid_file_count": 1, "status": "READY_SCID_AND_DEPTH_PRESENT"}, "MGC": {"depth_file_count": 2, "evidence_class": "FUTURES_PROXY_TRANSFER", "latest_depth_utc": "2026-05-04T19:06:29.424031+00:00", "latest_scid_utc": "2026-05-04T19:06:28.012791+00:00", "scid_file_count": 1, "status": "READY_SCID_AND_DEPTH_PRESENT"}, "XAUUSD": {"depth_file_count": 0, "evidence_class": "SAME_MARKET_SOURCE_TRANSFER", "latest_depth_utc": null, "latest_scid_utc": "2026-05-02T15:50:48.748170+00:00", "scid_file_count": 1, "status": "CAUTION_SCID_PRESENT_DEPTH_MISSING"}}` | `-` |
| `G5_NO_PROMOTION_OR_VALIDATION_CLAIM` | `True` | `{"registry_no_promotion": true, "source_map_no_promotion": true}` | `-` |

## Boundary

LTO-028 preregisters XAUUSD same-market/source-transfer evidence only. It opens no outcomes and cannot validate replay lift, promote a selector, or modify live behavior.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
