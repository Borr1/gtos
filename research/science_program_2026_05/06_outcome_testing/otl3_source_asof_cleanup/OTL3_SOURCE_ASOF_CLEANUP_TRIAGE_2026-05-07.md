# OTL3 Source/As-Of Cleanup Triage - 2026-05-07

## Controls

- Generated at UTC: `2026-05-06T18:05:29+00:00`
- Git branch/head at generation: `otl3-source-asof` / `7e60bfa3`
- Scope: research-only source/as-of cleanup. No outcomes were opened.
- `validation_safe=false` for every packet and source.
- `outcome_review_opened=false` for every packet.
- `promotion_verdict=NO_PROMOTION_VERDICT` remains unchanged.
- No live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remotes, or order behavior are touched.

## Summary

- SOURCE_ASOF packets triaged: `21`
- Unique registered source IDs classified: `19`
- Source classes: `{'BLOCKED_WITH_NEXT_EXACT_QUESTION': 12, 'CLEAR_FOR_RESEARCH_PACKET_USE': 2, 'CONTEXT_ONLY': 5}`
- Packet classes: `{'BLOCKED_WITH_NEXT_EXACT_QUESTION': 21}`
- Limited clear sources: SRC-G5-NEWS-CALENDAR-LOCAL-001, SRC-G7-LBMA-FIX-001
- Context-only sources: G10-SRC-NEIGHBOR-G1-G6-G9, G10-SRC-PHASE3-PATH-REPLAY, SRC-G7-LOCAL-GTOS-MACRO-001, SRC-G8-CBOE-METHODOLOGY-002, SRC-G8-GAMMA-VRP-LITERATURE-007
- Blocked sources: G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE, SRC-G5-AI-SHADOW-LOCAL-001, SRC-G5-PROMPT-NEUTRAL-001, SRC-G7-BIS-STATS-001, SRC-G7-FED-FOMC-001, SRC-G7-FRED-RATES-001, SRC-G7-ICE-DXY-001, SRC-G7-WGC-GOLDHUB-001, SRC-G8-CBOE-VOL-CSV-001, SRC-G8-FLASHALPHA-GEX-PROXY-003, SRC-G8-OFFICIAL-HISTORICAL-GEX-004, SRC-G8-VRP-FORMULA-005

The two limited-clear sources are not validation-safe promotions. They are restricted to research packet context: local news-calendar schedule/stale-calendar context, and deterministic LBMA fix schedule/window context. Every packet remains closed to outcome review.

## Universal As-Of Rule

feature_asof_utc = max(source_publication_timestamp_utc, source_cache_time_utc, source_bar_or_observation_close_time_utc when applicable); require feature_asof_utc <= candidate_decision_timestamp_utc; unknown/date-only/revised/no hash remains blocked.

## Source Classifications

| Source ID | Classification | Packets | Allowed role | Next exact question |
| --- | --- | --- | --- | --- |
| G10-SRC-NEIGHBOR-G1-G6-G9 | CONTEXT_ONLY | OTG0-PKT-014 | Local neighbor synthesis and control context only. | If G10 needs neighbor conditioning beyond context, which registered G9/G6 point-in-time packet supplies source_hash, source_capture_utc, parser_version, and no-lookahead fixtures? |
| G10-SRC-PHASE3-PATH-REPLAY | CONTEXT_ONLY | OTG0-PKT-014 | Synthetic path-R discovery context and prereg design only. | Which prospective path-replay packet freezes source_capture_utc, source_hash, parser_version, lifecycle labels, and setup geometry before outcome review? |
| G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-014 | Candidate execution lifecycle context after source/as-of proof only. | Which packet stores decision_asof/source_capture timestamps, close-side cost rows, broker actual-R join evidence, and separated lifecycle labels without opening outcomes? |
| SRC-G5-AI-SHADOW-LOCAL-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-051 | Local AI-shadow context only until paired-run protocol and label separation are proven. | Which frozen paired-prompt/AI-shadow packet contains setup_id, decision_time_utc, prompt/model version, comparator decision, and separated lifecycle/synthetic/broker labels? |
| SRC-G5-NEWS-CALENDAR-LOCAL-001 | CLEAR_FOR_RESEARCH_PACKET_USE | OTG0-PKT-077 | Schedule and stale-calendar context only; not surprise, sentiment, macro release impact, or outcome label. | If G5/G7 needs more than schedule context, which official calendar/release source supplies release result, vintage, source_hash, and feature_asof_utc <= decision_time_utc fixtures? |
| SRC-G5-PROMPT-NEUTRAL-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-051 | Prompt-neutral rerun design only until budget, protocol, and cache are approved. | Will the owner approve a bounded prompt-neutral rerun budget/cache protocol, or should this remain blocked and context-only? |
| SRC-G7-BIS-STATS-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-067 | Official BIS context only until exact table/dataflow and release vintage are frozen. | Which exact BIS table/dataflow, release/vintage field, raw hash, parser version, and no-lookahead fixture supplies the packet feature? |
| SRC-G7-FED-FOMC-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-077 | Official FOMC schedule/event context only after event-window parser and stale-source fixture are frozen. | Which FOMC calendar parser/cache hash/stale-source fixture creates event_time_utc and predeclared event-window rows? |
| SRC-G7-FRED-RATES-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-067, OTG0-PKT-070, OTG0-PKT-078 | Daily rates/macro context only after series, cache, vintage/release rule, and no-lookahead test are packet-bound. | Which FRED series cache with vintage/release metadata, raw hash, and parser hash proves feature_asof_utc <= decision_time_utc? |
| SRC-G7-ICE-DXY-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-070, OTG0-PKT-078 | Dollar-index context only after authorized bar source, close-time rule, and parser fixtures are frozen. | Which authorized DXY or broad-dollar source supplies bar close/publication time, retrieval hash, parser version, and no-lookahead fixture? |
| SRC-G7-LBMA-FIX-001 | CLEAR_FOR_RESEARCH_PACKET_USE | OTG0-PKT-073 | Deterministic LBMA fix schedule/window context only; no auction imbalance, auction flow, or benchmark price feature. | If the packet needs LBMA auction imbalance or benchmark price history, which licensed source grants access, raw hash, parser version, publication timestamp, and no-lookahead fixture? |
| SRC-G7-LOCAL-GTOS-MACRO-001 | CONTEXT_ONLY | OTG0-PKT-067, OTG0-PKT-070, OTG0-PKT-073, OTG0-PKT-077, OTG0-PKT-078 | Local GTOS macro-source inventory and blocked-route context only. | Which underlying official/vendor source row supplies the actual macro feature with source_hash and feature_asof_utc? |
| SRC-G7-WGC-GOLDHUB-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-073 | WGC/Goldhub context only until exact series/download and revision policy are frozen. | Which WGC series/workbook/export, publication date, revision policy, raw hash, and parser test supplies this feature? |
| SRC-G8-CBOE-METHODOLOGY-002 | CONTEXT_ONLY | OTG0-PKT-081, OTG0-PKT-084, OTG0-PKT-086 | Cboe methodology/specification context only. | Which Cboe row-level data source and parser supplies the timestamped feature rows used by the packet? |
| SRC-G8-CBOE-VOL-CSV-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-081, OTG0-PKT-083, OTG0-PKT-084, OTG0-PKT-085, OTG0-PKT-086 | Public Cboe volatility CSV context only until publication timing, license, parser, and no-lookahead fixtures are frozen. | What official Cboe publication/as-of timestamp and license rule permits same-day or next-day CSV use, and where is the parser/no-lookahead fixture? |
| SRC-G8-FLASHALPHA-GEX-PROXY-003 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-080, OTG0-PKT-083 | Vendor GEX proxy context only until forward snapshot cache and legal state are packet-bound. | Which forward snapshot cache with as_of_utc, vendor plan/legal state, proxy mapping, raw hash, and parser version clears context-only packet use? |
| SRC-G8-GAMMA-VRP-LITERATURE-007 | CONTEXT_ONLY | OTG0-PKT-080, OTG0-PKT-085 | Literature mechanism prior only. | If used beyond prior/context, which registered market data source supplies the actual gamma/VRP feature rows? |
| SRC-G8-OFFICIAL-HISTORICAL-GEX-004 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-080 | Potential official/vendor GEX source route only. | Which legal exchange/vendor aggregate GEX source, cost, point-in-time rows, raw hash, and parser fixture can be used? |
| SRC-G8-VRP-FORMULA-005 | BLOCKED_WITH_NEXT_EXACT_QUESTION | OTG0-PKT-081, OTG0-PKT-085 | Derived VRP formula route only after formula, tenor, realized window, implied source, and as-of rule are frozen. | Which frozen VRP formula, tenor, annualization, implied as-of rule, realized-window no-lookahead proof, and derived cache clears this source? |

## Packet Triage

| Packet | Lane | Experiment | Hypothesis | Classification | Registered sources | Unresolved refs | Next exact question |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OTG0-PKT-014 | G10 | G10-EXP-XDOMAIN-008 | G10-HYP-XDOMAIN-008 | BLOCKED_WITH_NEXT_EXACT_QUESTION | G10-SRC-NEIGHBOR-G1-G6-G9, G10-SRC-PHASE3-PATH-REPLAY, G10-SRC-SHADOW-LIFECYCLE-SLIPPAGE | NONE | Which prospective G10 lifecycle/slippage packet supplies source_capture_utc, source_hash, parser_version, close-side cost, and separated lifecycle/synthetic/broker labels? |
| OTG0-PKT-015 | G11 | EXP-G11-COVERAGE-GATE-002 | HYP-G11-COVERAGE-GATE-002 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Should HYP-G11-COVERAGE-GATE-002 adopt CD2-08 proposed source_ids/no_leak_fields, and where is the coverage manifest with as-of timestamps and hashes? |
| OTG0-PKT-018 | G11 | EXP-G11-OPTIONS-VOL-005 | HYP-G11-OPTIONS-VOL-005 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Should HYP-G11-OPTIONS-VOL-005 adopt SRC-G11-CBOE-OPTIONS-VOL plus concrete G8 source rows after Cboe/VRP parser rules are frozen? |
| OTG0-PKT-039 | G4 | EXP-G4-FILL-QUALITY-008 | HYP-G4-FILL-QUALITY-009 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Which G4/G10 packet stores pending-native fill/no-fill, spread/depth, source_hash, source_symbol, trade IDs, and separated broker/synthetic/lifecycle labels? |
| OTG0-PKT-041 | G4 | EXP-G4-OFI-DEPTH-001 | HYP-G4-OFI-DEPTH-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Which concrete G4 orderflow source contract and as-of depth/OFI cache supplies pre60/event15 fields without post-event windows? |
| OTG0-PKT-042 | G4 | EXP-G4-PROFILE-VWAP-004 | HYP-G4-PROFILE-VWAP-004 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Which Sierra/Databento profile/VWAP source contract freezes POC/HVN/LVN/VWAP definitions and source hashes? |
| OTG0-PKT-047 | G4 | EXP-G4G3-DC-DEPTH-012 | HYP-G4G3-DC-DEPTH-013 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Which joint G3/G4 packet proves directional-change and depth features are both as-of and source-hashed? |
| OTG0-PKT-050 | G4 | EXP-G4G6-DEPTH-CONTINUATION-009 | HYP-G4G6-DEPTH-CONTINUATION-010 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | NONE | Which NAS100/NQ depth-regime packet supplies source-safe depth status without date concentration or actual-R floor leakage? |
| OTG0-PKT-051 | G5 | EXP-G5-AINARR-006 | HYP-G5-AINARR-006 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G5-AI-SHADOW-LOCAL-001, SRC-G5-PROMPT-NEUTRAL-001 | LIT-G5-LLM-001 | Move LIT-G5-LLM-001 to evidence_refs or SRC-G5-ACADEMIC-LIT-001, then register/cache the prompt-neutral paired-run protocol. |
| OTG0-PKT-057 | G5 | EXP-G5-XG4-PRED-007 | HYP-G5-XG4-PRED-007 | BLOCKED_WITH_NEXT_EXACT_QUESTION | NONE | LIT-G5-PRED-001 | Move LIT-G5-PRED-001 to evidence_refs and add concrete G4 source contracts for the pre-outcome stress proxy. |
| OTG0-PKT-067 | G7 | EXP-G7-BIS-CARRY-007 | HYP-G7-BIS-CARRY-STRESS-007 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G7-BIS-STATS-001, SRC-G7-FRED-RATES-001, SRC-G7-LOCAL-GTOS-MACRO-001 | NONE | Which BIS carry-stress table/dataflow and vintage parser supplies the feature rows without date-only or revised-data leakage? |
| OTG0-PKT-070 | G7 | EXP-G7-DXY-SOFT-002 | HYP-G7-DXY-SOFT-CONTEXT-002 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G7-FRED-RATES-001, SRC-G7-ICE-DXY-001, SRC-G7-LOCAL-GTOS-MACRO-001 | NONE | Which authorized DXY or broad-dollar source supplies bar close/publication time and no-lookahead fixtures? |
| OTG0-PKT-073 | G7 | EXP-G7-GOLD-FLOW-009 | HYP-G7-GOLD-FLOW-009 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G7-LBMA-FIX-001, SRC-G7-LOCAL-GTOS-MACRO-001, SRC-G7-WGC-GOLDHUB-001 | NONE | Which WGC/LBMA source rows separate public schedule context from licensed auction/flow/price histories and freeze publication timestamps? |
| OTG0-PKT-077 | G7 | EXP-G7-XG5-MACRO-ATTN-010 | HYP-G7-XG5-MACRO-ATTN-010 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G5-NEWS-CALENDAR-LOCAL-001, SRC-G7-FED-FOMC-001, SRC-G7-LOCAL-GTOS-MACRO-001 | HYP-G5-XG7-MACRO-ATTN-009 | Move HYP-G5-XG7-MACRO-ATTN-009 to neighbor_lane_dependency, then keep only concrete G5/G7 source IDs with source hashes. |
| OTG0-PKT-078 | G7 | EXP-G7-XG8-VOL-MACRO-011 | HYP-G7-XG8-VOL-MACRO-011 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G7-FRED-RATES-001, SRC-G7-ICE-DXY-001, SRC-G7-LOCAL-GTOS-MACRO-001 | future_G8_options_vol_rows | Replace future_G8_options_vol_rows with concrete G8 source IDs only after Cboe/VRP source blockers clear. |
| OTG0-PKT-080 | G8 | EXP-G8-GEX-FEEDBACK-001 | HYP-G8-GEX-FEEDBACK-001 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-FLASHALPHA-GEX-PROXY-003, SRC-G8-GAMMA-VRP-LITERATURE-007, SRC-G8-OFFICIAL-HISTORICAL-GEX-004 | NONE | Which legal forward GEX source or proxy snapshot cache supplies as_of_utc, vendor/legal state, raw hash, and parser version? |
| OTG0-PKT-081 | G8 | EXP-G8-GVZ-METALS-003 | HYP-G8-GVZ-METALS-003 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-CBOE-METHODOLOGY-002, SRC-G8-CBOE-VOL-CSV-001, SRC-G8-VRP-FORMULA-005 | NONE | Which Cboe GVZ CSV publication/as-of and parser rule permits metals-vol use without same-day availability leakage? |
| OTG0-PKT-083 | G8 | EXP-G8-PROXYMAP-006 | HYP-G8-PROXYMAP-006 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-CBOE-VOL-CSV-001, SRC-G8-FLASHALPHA-GEX-PROXY-003 | NONE | Which proxy map is source-hashed and tested so option-vol proxy rows are not transferred post hoc? |
| OTG0-PKT-084 | G8 | EXP-G8-VIX1D9D-STRESS-002 | HYP-G8-VIX1D9D-STRESS-002 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-CBOE-METHODOLOGY-002, SRC-G8-CBOE-VOL-CSV-001 | NONE | Which Cboe VIX1D/VIX9D publication/as-of rule and parser fixture freezes short-vol stress rows before decision time? |
| OTG0-PKT-085 | G8 | EXP-G8-VRP-004 | HYP-G8-VRP-004 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-CBOE-VOL-CSV-001, SRC-G8-GAMMA-VRP-LITERATURE-007, SRC-G8-VRP-FORMULA-005 | NONE | Which frozen VRP formula, implied-vol source timing, and realized-window lag fixture avoids forward return leakage? |
| OTG0-PKT-086 | G8 | EXP-G8-VVIX-TAIL-007 | HYP-G8-VVIX-TAIL-007 | BLOCKED_WITH_NEXT_EXACT_QUESTION | SRC-G8-CBOE-METHODOLOGY-002, SRC-G8-CBOE-VOL-CSV-001 | NONE | Which Cboe VVIX publication/as-of and parser fixture freezes tail-vol rows before decision time? |

## Required Follow-Up Before Outcomes

- G11 packets need source_contract_v2 replacements and no-leak field rewrites from CD2-08/G12, not outcome review.
- G4 packets need concrete OFI/depth/profile/auction/fill source contracts and source-hashed as-of caches.
- G5 literature refs must move to evidence_refs or context-only source rows; prompt-neutral reruns need approved budget/cache protocol.
- G7 macro sources need exact series/table/source selection, release/vintage policy, raw hashes, parser versions, and no-lookahead fixtures.
- G8 vol/gamma sources need legal access state, publication/as-of timing, parser tests, proxy-map rules, and derived-feature no-lookahead fixtures.

## Verdict

NO_PROMOTION_VERDICT. OTL3 produced source/as-of triage only. `validation_safe=false` and `outcome_review_opened=false` remain the controlling state.
