# G4 Context And Ambiguity Ledger - 2026-05-06

**Lane:** `G4`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Mandatory Preflight Ledger

| Step | Evidence | Changed claim or next question |
| --- | --- | --- |
| Run `python scripts/generate_live_state.py` | Command returned `Wrote .context\LIVE_STATE.md`. | Live state refreshed before relying on repo state. |
| Read `.context/LIVE_STATE.md` | Generated 2026-05-06 06:45:12 UTC; clean tree; latest handoff `SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`. | Worktree is fresh enough for G4. |
| Read latest numbered handoff | `SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`. | Treat as historical; current live state and G0 artifacts supersede stale rows. |
| Read quick reference | `.context/00_core/quick_reference_card.md`. | Preserve live safety boundaries and `NO_PROMOTION_VERDICT`. |
| Read doctrine | `.context/00_core/research_operating_doctrine.md`. | Orderflow is serious but diagnostic-only while actual-R labels are sparse. |
| Read current state | `.context/00_core/research_current_state.md`. | G4 must respect LTO/orderflow blockers, V2b blockers, source/budget posture, and K55 label separation. |
| Read reading order and Tier 2-4 artifacts | `.context/00_READING_ORDER.md`, `CLAUDE.md`, knowledge-base validation/edge/gold docs, orderflow and Sierra program-control artifacts. | G4 must cross-check against killed routes and current research map. |

## Search Plan

1. Start with local GTOS artifacts because they contain direct project state, source/cost blockers, and label constraints.
2. Search public primary papers for OFI, queue imbalance, LOB queueing, and stop cascades.
3. Search official exchange/vendor docs for schema/auction capabilities: Databento, CME, Nasdaq, ICE/LBMA.
4. Compare every mechanism to local killed routes: broad orderflow rule, influencer footprint claims, MT5 tick-volume misuse, MBP-1 heatmap overclaim, unsupported futures proxies.
5. Translate only survivable mechanisms into schema rows with no-leak fields, sample floors, source contracts, and explicit blockers.
6. After first synthesis, inspect neighboring G3/G6/G11 worktrees and add no cross-lane rows unless their lane evidence exists.

## Source-Read Ledger

| Artifact/source | Claim changed | Next question or action |
| --- | --- | --- |
| G0 governor, schema, budget, synthesis | Science lanes write lane-owned rows; no source validation-safe while budget/source blockers remain. | Keep G4 rows separate from master registries for G0 merge. |
| `ORDERFLOW_RESEARCH_CLOSURE_SYNTHESIS_2026-05-02.md` | Orderflow survives as symbol-specific research, not broad rule. | Register NAS100 and fill-quality hypotheses only as blocked/shadow rows. |
| `ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md` | MBO deepens the same NAS100 thin-depth clue but remains label-limited. | Do not make an MBO-only hypothesis until MBP/depth ambiguity requires order identity. |
| `ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md` | Leave-one-date instability is a core decay/overfit risk. | Require leave-one-date/session/effective-N in prereg specs. |
| `LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md` | NAS100 floors are explicit: 20 broker actual-R, 30 MBP10 candidate rows. | Carry the floors into G4 hypotheses. |
| `LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md` | GTOS already has primitive families and role boundaries. | G4 should map mechanisms to these rather than inventing generic feature names. |
| `LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.md` | Sierra delta is ready from converted SCID, but stacked imbalance and VAH/VAL are blocked. | Profile/footprint hypotheses must name blocked fields and source definitions. |
| `LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md` | NQ/YM depth context can be shadow usable; several symbols are blocked/no-proxy. | Source contracts must be symbol-specific. |
| `LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md` | GBPJPY cannot infer direct confluence from 6B/6J. | Keep GBPJPY proxy transfer hypothesis context-only and pre-outcome. |
| `kb_edge_mechanisms_and_risks.md` | Stop-cascade framing is compatible with evidence, but dumb momentum is unresolved. | Stop-cascade hypothesis must compare against generic pullback/momentum. |
| `kb_gold_market_deep_knowledge.md` | Gold institutional intent stories are unsafe; COT is killed as direct gold signal. | Keep auction/source hypotheses separate from macro positioning filters. |
| Cont/Kukanov/Stoikov OFI evidence | OFI/depth is a credible primitive mechanism. | Test as short-window as-of feature, not raw trade-volume folklore. |
| Cont/de Larrard LOB queueing evidence | Queue-state can affect price-change probabilities. | Use queue/depth fields only where source gives enough depth/order-state granularity. |
| Cartea/Donnelly/Jaimungal LOB signal evidence | Volume imbalance can predict market-order sign and adverse selection in equities. | Treat as prior; require per-symbol transfer and no CFD overgeneralization. |
| Osler/New York Fed stop cascade evidence | Stop-loss clusters can create self-reinforcing price moves. | Test cascade/retest signatures against dumb momentum and trap decay. |
| Databento docs | MBO/MBP/trades schemas differ materially. | Keep trades-only, MBP-10, and MBO claims separated. |
| Nasdaq Trader cross docs | NOII and opening/closing crosses are measurable auction data. | Source contract required before Nasdaq/NQ cross-market auction feature use. |
| ICE/LBMA docs | LBMA Gold Price is an auction with 30-second rounds, imbalance threshold, and Round Zero. | Use as auction-window prior only; licensing and data feed blockers remain. |
| `C:\tmp\gtosg\G3\research\science_program_2026_05\01_domain_syntheses\G3_GEOMETRY_SIGNAL_DOMAIN_SYNTHESIS_2026-05-06.md` | G3 registered directional-change, wavelet/HAR, coherence, Hurst/DFA, MFDFA, TDA, and path-signature rows with killed-route checks. | Add only cross-domain G4/G3 hypotheses that preserve no-leak feature windows, source status, and dimensionality controls. |
| `C:\tmp\gtosg\G3\research\science_program_2026_05\02_hypothesis_registry\G3_GEOMETRY_SIGNAL_HYPOTHESIS_ROWS_2026-05-06.json` | G3 directional-change overshoot and TDA/path rows provide neighbor-owned anchors for G4 microstructure/path hypotheses. | Tie G4/G3 rows to G3 concepts without treating G3 methodology rows as GTOS validation. |
| `C:\tmp\gtosg\G6\research\science_program_2026_05\01_domain_syntheses\G6_MOMENTUM_REVERSION_DOMAIN_SYNTHESIS_2026-05-06.md` | G6 registered continuation, no-retrace, opening-drive, exhaustion, regime, residual-reversion, and gold round-number hypotheses with explicit generic-baseline blockers. | Add only cross-domain G4/G6 hypotheses that preserve source status, label separation, and no-promotion blockers. |
| `C:\tmp\gtosg\G6\research\science_program_2026_05\02_hypothesis_registry\G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json` | G6 row IDs and label policies provide neighbor-owned anchors for cross-domain G4/G6 preregs. | Tie G4/G6 rows to G6 concepts without claiming G6 validation. |

## Ambiguity Ledger

| Ambiguity | Pursued answer | Status | Next evidence needed |
| --- | --- | --- | --- |
| Is orderflow dead or useful? | Local closure says useful as source-aware NAS100/fill-quality research, not broad rule. | Answered. | Forward source rows and actual-R labels. |
| Is NAS100 thin depth stable? | Cached forensics says sign flips when 2026-04-28 is removed. | Sharper hypothesis. | New predeclared NAS100 candidate windows. |
| Does MBO add beyond MBP-10? | Current MBO deepens depth clue but not strong queue-flow separation. | Answered for current data. | MBO only when MBP/depth cannot answer a precise queue question. |
| Can trades data prove heatmap/resting liquidity? | No. Trades cannot observe resting book. | Answered. | MBP-10/MBO/Sierra depth for resting liquidity. |
| Can Sierra `.scid` provide footprint/profile? | Partial. Bid/ask volume and delta ready; stacked imbalance and VAH/VAL blocked. | Sharper hypothesis. | Candidate as-of join, bin/session/value-area definitions, source transfer caveats. |
| Can GBPJPY use 6B/6J orderflow directly? | No direct proxy; two-book design is pre-registered but inactive. | Answered. | Price transfer stability and leg-specific semantics. |
| Is XAGUSD/SI depth usable? | No; SI source-depth definition remains blocked. | Answered. | Registered SI depth semantics and retest. |
| Are auctions relevant to GTOS windows? | Yes as priors: LBMA AM/PM overlaps gold KZ boundaries, Nasdaq NOII exists. | Sharper hypothesis. | Licensed/cached imbalance data and as-of timestamp conventions. |
| Is stop-cascade enough as mechanism? | Not alone; dumb momentum baseline remains unresolved. | Explicit blocker. | Generic pullback/momentum comparator. |
| Does futures orderflow lead MT5 CFDs? | Not assumed; source-proxy transfer must be per symbol/session. | Explicit blocker. | Synchronized MT5 tick plus futures proxy lead/lag study. |
| Can G4 add neighbor-lane hypotheses now? | Yes for G3 and G6. Both produced lane-owned outputs during this work session; G11 remains scaffold-only. | Sharper hypothesis. | G11 outputs; G3/G6 experiment results remain future-only. |

## Owner Questions

No owner preference is required to complete G4 research artifacts. Future owner decisions are needed only for paid/license sources:

- Databento live GLBX.MDP3 license.
- Nasdaq NOII subscription or historical auction imbalance source.
- ICE/LBMA auction data licensing if raw order/imbalance history is needed.
- Any new Sierra/Denali, exchange, or vendor subscription beyond the current `$0` new-cash cap.

## Stale-Context Refreshes

- Live state was regenerated at session start.
- Neighbor-lane state was inspected after the first synthesis pass, then refreshed when G3 and G6 produced outputs during the same work session.
- No stale context required a second regeneration before artifact writing because no live/runtime claim was made after preflight.

## NO_PROMOTION_VERDICT

This ledger is context and ambiguity tracking only. It carries `NO_PROMOTION_VERDICT`.
