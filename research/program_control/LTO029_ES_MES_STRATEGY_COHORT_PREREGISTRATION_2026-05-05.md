# LTO029 ES/MES Strategy-Cohort Preregistration - 2026-05-05

**Schema:** `lto029_es_mes_strategy_cohort_preregistration_v1`
**Status:** `ES_MES_STRATEGY_COHORT_PREREGISTERED_SOURCE_STATUS_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

ES/MES is now preregistered as context/control and future separate-cohort source status only. Outcome files remain unopened, and every future ES/MES row must be point-in-time/as-of.

## Registration

- Registered question: `Can ES/MES provide preregistered equity-index context/control evidence, and later a separate strategy cohort if event ids and scoring rules are frozen before outcomes?`
- Strategy family: `ES_MES_EQUITY_INDEX_CONTEXT_CONTROL`
- Evidence classes: `['FUTURES_PROXY_TRANSFER', 'CROSS_INSTRUMENT_CONTEXT']`
- Opened outcome slices at registration: `0`
- Opened outcome artifacts: `[]`
- Outcome opening status: `OUTCOMES_CLOSED`

## Source Status

| Source | Status | SCID files | Depth files |
|---|---|---:|---:|
| `ES` | `READY_SCID_AND_DEPTH_PRESENT` | 1 | 2 |
| `MES` | `READY_SCID_AND_DEPTH_PRESENT` | 2 | 2 |

## Gates

| Gate | Passed | Observed | Blocker |
|---|---:|---|---|
| `G0_NO_LIVE_BEHAVIOR_OR_PAID_CALLS` | `True` | `{"ai_calls": 0, "behavior_unchanged": true, "canary_calls": 0, "no_ai_calls": true, "no_canary_required": true, "no_execution": true, "order_calls": 0, "paid_data_calls": 0, "paid_fetch_attempted": false}` | `-` |
| `G1_REGISTRY_FIELDS_FROZEN` | `True` | `{"evidence_complete": true, "no_lookahead_complete": true, "registry_present": true, "session_windows_complete": true, "source_mapping_complete": true, "strategy_family": "ES_MES_EQUITY_INDEX_CONTEXT_CONTROL"}` | `-` |
| `G2_OUTCOMES_CLOSED_AT_REGISTRATION` | `True` | `{"label_status": "LABEL_STATUS_ONLY_NO_REGISTERED_FROZEN_COHORT", "opened_outcome_artifacts": [], "opened_outcome_slices_at_registration": 0}` | `-` |
| `G3_SOURCE_FILES_READY_FOR_FUTURE_ASOF_ROWS` | `True` | `{"conversion_rows": [{"evidence_class": "FUTURES_PROXY_TRANSFER", "file_symbol": "SPX_ES", "first": "2026-04-15 00:00:00", "gap_count": 2, "invalid_records_skipped": 0, "last": "2026-04-17 20:45:00", "price_transform": "identity", "rows": 268, "source_symbol": "ESM26-CME"}, {"evidence_class": "FUTURES_PROXY_TRANSFER", "file_symbol": "SPX_MES", "first": "2026-04-15 00:00:00", "gap_count": 2, "invalid_records_skipped": 0, "last": "2026-04-17 20:45:00", "price_transform": "identity", "rows": 268, "source_symbol": "MESM26-CME"}], "sierra_source_status": {"ES": {"depth_file_count": 2, "evidence_class": "FUTURES_PROXY_TRANSFER", "latest_depth_utc": "2026-05-04T19:06:29.424031+00:00", "latest_scid_utc": "2026-05-04T19:06:28.012791+00:00", "scid_file_count": 1, "status": "READY_SCID_AND_DEPTH_PRESENT"}, "MES": {"depth_file_count": 2, "evidence_class": "FUTURES_PROXY_TRANSFER", "latest_depth_utc": "2026-05-04T19:06:29.424031+00:00", "latest_scid_utc": "2026-05-04T19:06:28.012791+00:00", "scid_file_count": 2, "status": "READY_SCID_AND_DEPTH_PRESENT"}}}` | `-` |
| `G4_NO_LOOKAHEAD_RULES_EXPLICIT` | `True` | `{"no_lookahead_rules": ["Any future feature row must use source events with timestamp <= decision_time_utc/asof_cutoff_utc.", "Registry/status rows must not contain TP/SL hits, realized R, synthetic path labels, or replay lift.", "Outcome files stay closed until event ids, source files, hashes, session windows, and scoring spec are frozen.", "ES/MES evidence must remain labeled as transfer/context evidence, not broker actual-R."]}` | `-` |
| `G5_NO_PROMOTION_OR_DIRECT_BROKER_TRUTH_CLAIM` | `True` | `{"allowed_use": ["equity-index context/control around NAS100 and US30 diagnostics", "future standalone ES/MES strategy cohort only after a separate frozen event registry exists"], "disallowed_use": ["direct broker-truth validation for NAS100 or US30", "promotion dossier input before broker/source/cost/lifecycle floors are met", "outcome mining from existing converted ES/MES rows"], "promotion_verdict": "NO_PROMOTION_VERDICT"}` | `-` |

## Boundary

LTO-029 preregisters ES/MES context/control and future separate-cohort rules only. It opens no outcomes and cannot validate or promote a strategy.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
