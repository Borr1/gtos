# G7 Context Ledger

Generated: 2026-05-06T08:30:00Z
Lane: G7
Promotion verdict: NO_PROMOTION_VERDICT

## Mandatory Preflight

| Step | Evidence |
| --- | --- |
| Regenerated live state | `python scripts/generate_live_state.py` wrote `.context/LIVE_STATE.md`; HEAD reported as `42bf621c research: merge g0 wave 1 reconciliation`. |
| Latest handoff read | `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`. |
| Quick reference read | `.context/00_core/quick_reference_card.md`. |
| Research doctrine read | `.context/00_core/research_operating_doctrine.md`. |
| Research current state read | `.context/00_core/research_current_state.md`; it marks G7 as `READY_TO_LAUNCH_NOT_RUN` before this pass. |
| Reading order read | `.context/00_READING_ORDER.md`. |
| Controlling prompt read | `research/science_program_2026_05/04_goal_prompts/G7_G7_MACRO_CROSS_ASSET_GOAL_PROMPT_2026-05-06.md`. |
| G0 governor read | `G0_WAVE1_RECONCILIATION_2026-05-06.md`, master registry, source registry, schema contracts, governor, completion audit, and goal status registry. |

## G0 Constraints Imported

- G0 wave 1 reconciled G1-G6 only; G7 was not run at HEAD `42bf621c`.
- All wave-1 rows remain `NO_PROMOTION_VERDICT`; no survivor backlog exists.
- All source contracts reviewed by G0 were `validation_safe=false`.
- Master registries are G0-owned and should not be modified by G7.
- G7 must write lane-owned artifacts only.

## Local Context Reads

| Source | G7-relevant finding |
| --- | --- |
| `.context/01_knowledge_base/edge_mechanism.md` | GTOS edge is OB-zone precision and stop-cascade mean reversion, not macro prediction; macro rows must explain context/decay rather than replace the edge. |
| `.context/01_knowledge_base/kb_gold_market_deep_knowledge.md` | COT direct gold predictiveness is killed; DXY is soft context only; LBMA/COMEX/CFD layers and fix times matter as market-structure context. |
| `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md` | DSR/PBO, label separation, and no-promotion discipline are mandatory. |
| `.context/03_analysis/research_execution_plan_113q.md` | Older G7-adjacent questions exist for DXY, rates, macro news, safe haven, and cross-currency signals. |
| `research/program_control/LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md` | FX COT mapping, KMW FX fix, H-K-M/intermediary capital, BIS, and Fed research feeds remain blocked or source-incomplete. |
| `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md` | `$0` budget, free/public/existing sources only, and no live decision use. |
| `research/program_control/EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.md` | Source-transfer evidence is not validation; feed lineage and timestamp rules are required. |
| `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md` | CFTC XAUUSD rows and LBMA rows exist locally in prior audit notes; FX COT mapping and KMW fix remain blocked. |
| `research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md` | FRED, FlashAlpha GEX, CFTC, and LBMA routes were triaged; many macro source routes remain blockers. |
| `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md` | Real-rate proxies exist in design/audit notes but CPI/PCE/deflator and validation-safe source handling remain incomplete. |
| `research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md` | WGC, tick inventory, tail correlation, and vol-scaling routes are source/validation constrained. |
| `research/program_control/CL_ZN_VIX_CONTEXT_CONTROL_READINESS_2026-05-04.md` | CL/ZN/VIX context controls are readiness-only and wait for forward rows; no promotion. |
| `.context/00_core/master_roadmap.md` | Older DXY/US10Y/SPX prompt-context ideas are stale and not permission to touch prompts. |

## Search Plan And Source Cache

The pass prioritized official/public sources before vendor or paid feeds. Raw source evidence was cached under:

`research/science_program_2026_05/01_domain_syntheses/raw/G7_macro_cross_asset_sources_2026-05-06/`

| Source family | Status | Use in lane |
| --- | --- | --- |
| CFTC COT | Official pages fetched and cached. | Slow positioning source contract; direct gold predictor killed; FX mapping blocked. |
| BIS statistics | Official index fetched and cached. | Source discovery for global liquidity, FX, banking, and derivatives; no exact table selected. |
| Federal Reserve FOMC calendars | Official page fetched and cached. | Scheduled event/attention labels only. |
| Federal Reserve economic research | Official page fetched and cached. | Research feed discovery only; no extractor. |
| FRED rates/broad dollar | Fetch attempts failed/reset; no raw FRED cache created. | Source blocker; local code/docs mention series but validation cache absent. |
| LBMA Gold Price / daily auction | Official pages fetched and cached. | Benchmark timing context; no auction imbalance. |
| World Gold Council Goldhub data | Public page fetched and cached. | Gold flow/data discovery; no validation-safe series selected. |
| ICE U.S. Dollar Index futures | Public page fetched and cached. | Official DXY-adjacent source candidate; no parser/cache. |

## Evolving Questions

1. Can dollar/real-rate states explain XAU/XAG path differences after respecting daily-source close times and local DXY counter-evidence?
2. Do FOMC and high-impact event windows change GTOS lifecycle/no-fill/path instability, or are they already covered by existing live calendar behavior?
3. Are LBMA fix-window cohorts mechanically different for XAUUSD/XAGUSD, or merely time-of-day/session effects?
4. Can COT remain useful as a slow crowding descriptor after direct gold predictiveness is killed?
5. What exact BIS tables and release rules would make global liquidity/carry context decision-time safe?
6. Can cross-asset stress be measured without duplicating or weakening existing correlation/risk gates?
7. Which G8 vol-source rows and G11 source-governance rows should G7 depend on after those lanes run?

## Stale Refresh Rules

- COT: use CFTC publication timestamp, not Tuesday report date alone; stale if no cache confirmation after release.
- FOMC: use Fed calendar publication/page timestamp and event time; stale if event is missing or modified after decision without as-of record.
- FRED/rates: daily close values become usable only after their source publication/close timestamp and cache hash are known.
- LBMA fix: benchmark timestamp labels are valid only as timestamp context; auction imbalance requires a separate contract.
- BIS/WGC: slow-series rows require release calendar, vintage/as-of metadata, and stable cache before outcome review.
- ICE/DXY: source values require official/authorized data path, timestamp, and parser; local stale CSV cannot validate.

## Neighbor Pass

G5 committed artifacts were read after first synthesis. G8 and G11 had prompts only at this HEAD, so their cross-domain rows are dependency placeholders.

| Neighbor | Status | G7 action |
| --- | --- | --- |
| G5 behavioral/game | Committed lane artifacts exist. | Added `HYP-G7-XG5-MACRO-ATTN-010` to link macro event labels with attention/herding labels. |
| G8 options/vol | No committed lane outputs at HEAD. | Added blocked `HYP-G7-XG8-VOL-MACRO-011` only. |
| G11 source expansion | No committed lane outputs at HEAD. | Added blocked `HYP-G7-XG11-SOURCE-FRESH-012` only. |

## Killed Routes And Non-Actions

- No direct COT-to-gold alpha route was reopened.
- No DXY, US10Y, real-yield, or SPX hard prompt context was added.
- No live news-filter, risk, correlation, selector, or permission logic changed.
- No paid source was fetched or recommended.
- No outcome review was opened.
- No source was marked validation-safe.

Promotion verdict: NO_PROMOTION_VERDICT
