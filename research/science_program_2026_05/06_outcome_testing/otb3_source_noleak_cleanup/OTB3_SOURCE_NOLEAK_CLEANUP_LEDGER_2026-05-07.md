# OTB3 Source/No-Leak Cleanup Ledger - 2026-05-07

**Generated at UTC:** `2026-05-06T19:04:05+00:00`
**Branch/head:** `otb3-source-noleak` / `5fbfd8a5`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`

## Summary

- Assignments processed: `8`
- G11 no-leak rewrites proposed: `8`
- Source statuses: `{'CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY': 7, 'STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION': 12}`
- Packet context statuses: `{'STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION': 21}`
- Proposed direct master-registry edits applied: `False`
- External fetches/API/paid calls: `0`

## Assignment Status

| Assignment | Scope | Status | Evidence |
| --- | --- | --- | --- |
| SA-001 | G5/G7 local calendar path cleanup | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | Configured local data/news_calendar.json exists, is hash-stamped, and can be used only for schedule/stale-calendar packet context. |
| SA-002 | FOMC event-window parser/cache | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Cached official Fed page is hash-stamped and date-parsed, but event_time_utc and stale-source/no-lookahead fixture are not packet-ready. |
| SA-003 | FRED/DXY/BIS macro as-of cleanup | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | FRED/BIS/DXY need exact series/table/source, vintage or close-time rule, raw cache, parser version, and no-lookahead fixture. |
| SA-004 | Cboe volatility CSV publication/legal/parser cleanup | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Cboe CSV caches are hash/header/date-range probed but publication_asof_utc and license rules remain unresolved. |
| SA-005 | LBMA fix schedule context | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | LbmaFixCalendar supports deterministic fix schedule/window context; auction/price/imbalance data remain forbidden. |
| SA-006 | G4 orderflow/depth/profile/fill source contracts | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | G4 orderflow/depth/profile/fill rows still require packet-bound source symbols, schemas, hashes, proxy maps, and feature windows ending before decision time. |
| SA-007 | G8 GEX/VRP derived-source cleanup | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | GEX/VRP rows still need legal source route, proxy-map version, formula/tenor/annualization, realized-window lag, raw hashes, and parser fixtures. |
| SA-008 | G5 literature and prompt-neutral source cleanup | OWNER_APPROVAL_REQUIRED | Literature/source-ref cleanup is proposed as context-only patchset; any prompt-neutral pilot remains owner/budget/cache gated. |

## Source Status

| Source | OTL3 class | OTB3 status | Next exact question |
| --- | --- | --- | --- |
| G10-SRC-NEIGHBOR-G1-G6-G9 | CONTEXT_ONLY | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | If G10 needs neighbor conditioning beyond context, which registered G9/G6 point-in-time packet supplies source_hash, source_capture_utc, parser_version, and no-lookahead fixtures? |
| G10-SRC-PHASE3-PATH-REPLAY | CONTEXT_ONLY | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | Which prospective path-replay packet freezes source_capture_utc, source_hash, parser_version, lifecycle labels, and setup geometry before outcome review? |
| G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which packet stores decision_asof/source_capture timestamps, close-side cost rows, broker actual-R join evidence, and separated lifecycle labels without opening outcomes? |
| SRC-G5-AI-SHADOW-LOCAL-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which frozen paired-prompt/AI-shadow packet contains setup_id, decision_time_utc, prompt/model version, comparator decision, and separated lifecycle/synthetic/broker labels? |
| SRC-G5-NEWS-CALENDAR-LOCAL-001 | CLEAR_FOR_RESEARCH_PACKET_USE | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | If G5/G7 needs more than schedule context, which official calendar/release source supplies release result, vintage, source_hash, and feature_asof_utc <= decision_time_utc fixtures? |
| SRC-G5-PROMPT-NEUTRAL-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Will the owner approve a bounded prompt-neutral rerun budget/cache protocol, or should this remain blocked and context-only? |
| SRC-G7-BIS-STATS-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which exact BIS table/dataflow, release/vintage field, raw hash, parser version, and no-lookahead fixture supplies the packet feature? |
| SRC-G7-FED-FOMC-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which FOMC calendar parser/cache hash/stale-source fixture creates event_time_utc and predeclared event-window rows? |
| SRC-G7-FRED-RATES-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which FRED series cache with vintage/release metadata, raw hash, and parser hash proves feature_asof_utc <= decision_time_utc? |
| SRC-G7-ICE-DXY-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which authorized DXY or broad-dollar source supplies bar close/publication time, retrieval hash, parser version, and no-lookahead fixture? |
| SRC-G7-LBMA-FIX-001 | CLEAR_FOR_RESEARCH_PACKET_USE | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | If the packet needs LBMA auction imbalance or benchmark price history, which licensed source grants access, raw hash, parser version, publication timestamp, and no-lookahead fixture? |
| SRC-G7-LOCAL-GTOS-MACRO-001 | CONTEXT_ONLY | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | Which underlying official/vendor source row supplies the actual macro feature with source_hash and feature_asof_utc? |
| SRC-G7-WGC-GOLDHUB-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which WGC series/workbook/export, publication date, revision policy, raw hash, and parser test supplies this feature? |
| SRC-G8-CBOE-METHODOLOGY-002 | CONTEXT_ONLY | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | Which Cboe row-level data source and parser supplies the timestamped feature rows used by the packet? |
| SRC-G8-CBOE-VOL-CSV-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | What official Cboe publication/as-of timestamp and license rule permits same-day or next-day CSV use, and where is the parser/no-lookahead fixture? |
| SRC-G8-FLASHALPHA-GEX-PROXY-003 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which forward snapshot cache with as_of_utc, vendor plan/legal state, proxy mapping, raw hash, and parser version clears context-only packet use? |
| SRC-G8-GAMMA-VRP-LITERATURE-007 | CONTEXT_ONLY | CLEAR_FOR_PACKET_BUILDING_CONTEXT_ONLY | If used beyond prior/context, which registered market data source supplies the actual gamma/VRP feature rows? |
| SRC-G8-OFFICIAL-HISTORICAL-GEX-004 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which legal exchange/vendor aggregate GEX source, cost, point-in-time rows, raw hash, and parser fixture can be used? |
| SRC-G8-VRP-FORMULA-005 | BLOCKED_WITH_NEXT_EXACT_QUESTION | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which frozen VRP formula, tenor, annualization, implied as-of rule, realized-window no-lookahead proof, and derived cache clears this source? |

## Packet Context Status

| Packet | Experiment | Status | Next exact question |
| --- | --- | --- | --- |
| OTG0-PKT-014 | G10-EXP-XDOMAIN-008 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which prospective G10 lifecycle/slippage packet supplies source_capture_utc, source_hash, parser_version, close-side cost, and separated lifecycle/synthetic/broker labels? |
| OTG0-PKT-015 | EXP-G11-COVERAGE-GATE-002 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Should HYP-G11-COVERAGE-GATE-002 adopt CD2-08 proposed source_ids/no_leak_fields, and where is the coverage manifest with as-of timestamps and hashes? |
| OTG0-PKT-018 | EXP-G11-OPTIONS-VOL-005 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Should HYP-G11-OPTIONS-VOL-005 adopt SRC-G11-CBOE-OPTIONS-VOL plus concrete G8 source rows after Cboe/VRP parser rules are frozen? |
| OTG0-PKT-039 | EXP-G4-FILL-QUALITY-008 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which G4/G10 packet stores pending-native fill/no-fill, spread/depth, source_hash, source_symbol, trade IDs, and separated broker/synthetic/lifecycle labels? |
| OTG0-PKT-041 | EXP-G4-OFI-DEPTH-001 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which concrete G4 orderflow source contract and as-of depth/OFI cache supplies pre60/event15 fields without post-event windows? |
| OTG0-PKT-042 | EXP-G4-PROFILE-VWAP-004 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which Sierra/Databento profile/VWAP source contract freezes POC/HVN/LVN/VWAP definitions and source hashes? |
| OTG0-PKT-047 | EXP-G4G3-DC-DEPTH-012 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which joint G3/G4 packet proves directional-change and depth features are both as-of and source-hashed? |
| OTG0-PKT-050 | EXP-G4G6-DEPTH-CONTINUATION-009 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which NAS100/NQ depth-regime packet supplies source-safe depth status without date concentration or actual-R floor leakage? |
| OTG0-PKT-051 | EXP-G5-AINARR-006 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Move LIT-G5-LLM-001 to evidence_refs or SRC-G5-ACADEMIC-LIT-001, then register/cache the prompt-neutral paired-run protocol. |
| OTG0-PKT-057 | EXP-G5-XG4-PRED-007 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Move LIT-G5-PRED-001 to evidence_refs and add concrete G4 source contracts for the pre-outcome stress proxy. |
| OTG0-PKT-067 | EXP-G7-BIS-CARRY-007 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which BIS carry-stress table/dataflow and vintage parser supplies the feature rows without date-only or revised-data leakage? |
| OTG0-PKT-070 | EXP-G7-DXY-SOFT-002 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which authorized DXY or broad-dollar source supplies bar close/publication time and no-lookahead fixtures? |
| OTG0-PKT-073 | EXP-G7-GOLD-FLOW-009 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which WGC/LBMA source rows separate public schedule context from licensed auction/flow/price histories and freeze publication timestamps? |
| OTG0-PKT-077 | EXP-G7-XG5-MACRO-ATTN-010 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Move HYP-G5-XG7-MACRO-ATTN-009 to neighbor_lane_dependency, then keep only concrete G5/G7 source IDs with source hashes. |
| OTG0-PKT-078 | EXP-G7-XG8-VOL-MACRO-011 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Replace future_G8_options_vol_rows with concrete G8 source IDs only after Cboe/VRP source blockers clear. |
| OTG0-PKT-080 | EXP-G8-GEX-FEEDBACK-001 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which legal forward GEX source or proxy snapshot cache supplies as_of_utc, vendor/legal state, raw hash, and parser version? |
| OTG0-PKT-081 | EXP-G8-GVZ-METALS-003 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which Cboe GVZ CSV publication/as-of and parser rule permits metals-vol use without same-day availability leakage? |
| OTG0-PKT-083 | EXP-G8-PROXYMAP-006 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which proxy map is source-hashed and tested so option-vol proxy rows are not transferred post hoc? |
| OTG0-PKT-084 | EXP-G8-VIX1D9D-STRESS-002 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which Cboe VIX1D/VIX9D publication/as-of rule and parser fixture freezes short-vol stress rows before decision time? |
| OTG0-PKT-085 | EXP-G8-VRP-004 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which frozen VRP formula, implied-vol source timing, and realized-window lag fixture avoids forward return leakage? |
| OTG0-PKT-086 | EXP-G8-VVIX-TAIL-007 | STILL_BLOCKED_WITH_NEXT_EXACT_QUESTION | Which Cboe VVIX publication/as-of and parser fixture freezes tail-vol rows before decision time? |

## Guardrails

- Master registries were not edited; patch operations are sidecar proposals for G12/G0 review.
- `data/news_calendar.json` was hash-stamped and used as existing local evidence only; no live news-filter behavior changed.
- No outcomes, R/result values, quarantine files, Databento pulls, AI/API calls, MT5, canaries, prompts, risk, execution, permissions, selectors, safety gates, credentials, remotes, or order behavior were touched.
