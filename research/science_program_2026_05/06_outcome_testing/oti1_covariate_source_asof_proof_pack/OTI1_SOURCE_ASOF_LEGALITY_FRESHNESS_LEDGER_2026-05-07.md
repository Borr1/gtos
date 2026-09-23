# OTI1 Source/As-Of Legality And Freshness Ledger

- promotion_verdict: NO_PROMOTION_VERDICT
| Source/context | Classification | Packets | Blocker or role |
|---|---|---|---|
| OTB1R-SANITIZED-LIFECYCLE-SOURCE-PROJECTIONS | CLEARED_FOR_LIFECYCLE_SOURCE_FRESHNESS_CONTEXT_ONLY | OTG0-PKT-011, OTG0-PKT-016, OTG0-PKT-025, OTG0-PKT-029, OTG0-PKT-045, OTG0-PKT-055, OTG0-PKT-059, OTG0-PKT-071, OTG0-PKT-079 | Lifecycle source provenance only: decision_asof_utc/source_capture_utc/source_hash for existing lifecycle/no-fill rows. |
| SRC-G5-NEWS-CALENDAR-LOCAL-001 | CLEARED_FOR_PACKET_BUILDING_CONTEXT_ONLY | OTG0-PKT-055, OTG0-PKT-059 | Schedule and stale-calendar context only; no release result, surprise, sentiment, or live-filter change. |
| SRC-G7-FED-FOMC-001 | BLOCKED_WITH_NEXT_EXACT_EVIDENCE | OTG0-PKT-071 | Source-hashed event-window parser output with event_time_utc, source/cache time, raw official cache hash, parser/version, stale-source handling, decision_asof_utc, and no-lookahead fixture. |
| SRC-G8-CBOE-VOL-CSV-001 | BLOCKED_WITH_NEXT_EXACT_EVIDENCE | OTG0-PKT-079 | Legal/license allowance, official publication_asof_utc or conservative next-day rule, raw CSV cache path/hash, parser/version, feature_asof_utc, date alignment rule, and no-lookahead fixture. |
| SRC-G8-CBOE-METHODOLOGY-002 | CONTEXT_ONLY_NOT_TIME_SERIES_DECISION_ROWS | OTG0-PKT-079 | Methodology/spec references cannot supply per-decision short-vol values; CSV/legal/publication/parser proof is still required. |
| G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE | BLOCKED_FOR_DECISION_TIME_FRICTION_COVARIATE | OTG0-PKT-016, OTG0-PKT-079 | Packet-bound spread_at_decision, spread_atr_ratio_at_decision, tick_value_asof, contract_spec_version_asof, commission_schedule_asof, min_stop_distance_asof, source hash, parser/version, and feature_asof_utc <= decision_asof_utc. |
| G2-REALIZED-VOL-VOL-OF-VOL-SIDECAR | SOURCE_NOT_PACKET_BOUND | OTG0-PKT-025 | Frozen realized-vol formula/window, raw OHLC/tick input file path and sha256, parser/version, feature_window_end_utc <= decision_asof_utc, feature_asof_utc, per-row source_hash, and no-lookahead fixture. |
| G4-ORDERFLOW-ABSORPTION-SIDECAR | SOURCE_NOT_PACKET_BOUND | OTG0-PKT-045 | Packet-bound orderflow source id, license/access state, raw cache path/hash, source symbol/proxy map, parser/version, feature window start/end <= decision_asof_utc, absorption classifier version, and no-lookahead fixture. |
| G7-G5-MACRO-ATTENTION-SIDECAR | SOURCE_NOT_PACKET_BOUND | OTG0-PKT-059 | Official/raw source cache paths and hashes, exact series/table ids, publication/vintage/as-of rules, parser versions, event/source freshness state, feature_asof_utc <= decision_asof_utc, and no-lookahead fixtures. |
