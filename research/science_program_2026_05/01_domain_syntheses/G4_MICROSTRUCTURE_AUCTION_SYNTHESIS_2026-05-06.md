# G4 Market Microstructure, Order Book, Auction Synthesis - 2026-05-06

**Lane:** `G4`
**Role:** `science_lane`
**Domain:** `market microstructure, order book, auction`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Status:** `G4_SYNTHESIS_COMPLETE_SHADOW_ONLY`

## Objective

Extract primitive mechanisms from OFI, queueing, liquidity, footprint, volume profile, VWAP, opening/closing auctions, stop cascades, and futures-proxy transfer, then translate useful mechanisms into measurable, preregistered, source-aware, label-safe GTOS research rows.

This synthesis is research-only. It changes no live trading prompt, risk, execution, permissions, safety gate, selector, MT5, canary, paid-data path, or order behavior.

## Mechanisms Worth Finding Before Search

The useful G4 mechanisms should not be public strategy recipes. They should be primitive market behaviors that GTOS can observe before an outcome:

1. **OFI/depth impact:** short-horizon price change should be better explained by best-level order-flow imbalance scaled by available depth than by raw traded volume alone.
2. **Queue/adverse selection:** a setup that asks GTOS to rest or wait in a thin or pulled book should have worse fill quality and worse immediate path than a structurally similar setup in a resilient book.
3. **Footprint absorption/exhaustion:** aggressive flow into an OB/FVG/structural level should matter differently when price fails to progress versus when it sweeps through available liquidity.
4. **Volume profile/VWAP anchoring:** low-volume pockets, POC/HVN/LVN, and VWAP displacement should identify whether the intended POI is a fair-value revisit, a liquidity vacuum, or a bad price.
5. **Auction imbalance spillover:** opening/closing/fix auctions should alter the distribution of early-session imbalance, displacement, and reversal risk.
6. **Stop cascade propagation:** stop clusters can create self-reinforcing bursts, but the GTOS edge must distinguish usable cascade-and-retest behavior from generic momentum or trap artifacts.
7. **Futures-proxy transfer:** CME/CBOT/COMEX futures can improve CFD market awareness only when timestamp, contract, basis, spread, and source-proxy transfer checks pass.
8. **Execution-state awareness:** orderflow may be more useful for whether to arm, fill, abort, or monitor a pending intent than for overriding the structural CANDIDATE decision.

The strongest evidence is likely to live in local Databento/Sierra artifacts, the G0 source/budget ledger, primary microstructure papers, official exchange/vendor schema docs, and existing GTOS killed-route audits.

## First-Pass Synthesis

G4 should keep orderflow as a serious research lane, but only as source-aware shadow evidence. The local state already rejects the broad version: `ORDERFLOW_RESEARCH_CLOSURE_SYNTHESIS_2026-05-02.md:10` says the broad footprint/heatmap/orderflow-inversion idea became testable constraints and symbol-specific hypotheses, not a promoted rule; lines 18-20 say MBP-10 is more relevant than MBP-1, NAS100 has a loser-heavy clue, and NAS100 is still not ready for replay registration.

The best current live-adjacent mechanism is **NAS100/NQ depth-adverse-selection**. Cached MBO and MBP-10 both point to lower depth in NAS100 candidate windows, but the same evidence blocks promotion. `ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md:10-12` records the thin-depth clue, label limitation, and leave-one-date instability. `LTO011_NAS100_ORDERFLOW_ADVERSE_SELECTION_READINESS_2026-05-05.md:24-27` records only `1` NAS100 broker actual-R row, `12` cached MBP10 candidate rows, and `12` cached MBO candidate rows against floors of `20` actual-R and `30` MBP10 candidate rows.

The best source architecture is not "one feed solves everything." Databento is strongest for targeted historical/programmatic CME `GLBX.MDP3` trades/MBP/MBO. Sierra is strongest for local forward/recent depth, footprint/profile, and visual replay once parser/parity is proven. `SIERRACHART_AND_PRIMITIVE_DATA_SOURCE_SYNTHESIS_2026-05-02.md` says Sierra is useful for forward and recent depth-level capture, but not a long-horizon historical MBO replacement; `PRIMITIVE_ORDERFLOW_SOURCE_SYNTHESIS_2026-05-02.md` ranks direct CME as conceptually pure but high-friction, Databento as the current programmatic route, and Sierra as the current visual/forward route.

The highest-value new G4 contribution is to organize the mechanism stack into lane rows rather than add another ad hoc orderflow report:

- OFI/depth price impact maps to GTOS pre60/event15 features and should remain symbol/session-specific.
- Queue/depth depletion maps to NAS100 adverse selection and pending-limit fill quality.
- Footprint/profile maps to Sierra `.scid` bid/ask volume, delta, POC/HVN/LVN, with stacked imbalance and VAH/VAL blocked until source definitions are frozen.
- Auction imbalance maps to LBMA Gold Price AM/PM and Nasdaq open/close imbalance data, but those data sources have licensing/subscription blockers and cannot be treated as validation-safe.
- Stop cascade maps to the current OB-retreat explanation, but the killed-route check must always include the unresolved dumb-momentum baseline and prompt-narrative risk.
- Futures-proxy transfer maps to NQ/YM/GC/SI/6B/6J with symbol-specific blockers, especially USDJPY/6J and GBPJPY two-book semantics.

## External Evidence Incorporated

Primary papers and official docs support the mechanism priors, not GTOS validation:

- Cont, Kukanov, and Stoikov report that short-interval price changes are mainly driven by order-flow imbalance and that the OFI slope is inversely related to market depth. The direct Oxford/SSRN raw fetches returned 403, so G4 records the blocked raw responses and uses the source-indexed RePEc/open evidence as a mechanism prior only.
- Cont and de Larrard model LOB dynamics as market-order, limit-order, and cancellation arrivals in a Markovian queueing system, with price moves conditional on book state. This supports queue-state hypotheses, not promotion.
- Cartea, Donnelly, and Jaimungal use Nasdaq high-frequency data to show LOB volume imbalance predicts market-order sign and immediate price changes, with out-of-sample testing in their own equity setting. This supports adverse-selection hypotheses, not CFD/futures transfer.
- Osler's New York Fed staff report gives empirical support that clustered stop-loss orders can create self-reinforcing price cascades in FX. This supports cascade mechanisms, while GTOS still must test whether its observed OB behavior is more than generic momentum.
- Databento official docs classify MBO as L3/order-id data and MBP-10 as L2/top-ten market depth. This separates trades-only, MBP, and MBO claims.
- CME's public MBO page was curl-blocked, but source-indexed evidence says MBO exposes queue position/full depth while MBP aggregates by price. This supports the source-boundary distinction already present in GTOS artifacts.
- Nasdaq Trader documents opening/closing cross timing and NOII dissemination. This is source capability evidence for future auction hypotheses, not current NQ futures evidence.
- ICE documents the LBMA Gold/Silver auction rounds, imbalance thresholds, AM/PM timing, and Round Zero order queuing. This supports gold auction-window hypotheses, with licensing blockers.

## Counter-Evidence And Decay-Mode Review

| Risk | Current evidence | G4 rule |
| --- | --- | --- |
| Broad orderflow rule overreach | `ORDERFLOW_RESEARCH_CLOSURE_SYNTHESIS_2026-05-02.md:10` rejects a promoted broad rule; lines 108-110 close current NAS100 registration, broad MBO, and unsupported-symbol orderflow routes. | No universal orderflow filter or veto. |
| Label leakage | `ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md:11` says outcome contrast is synthetic-label dominated with one winner and one actual-R row. | Broker actual-R, synthetic path-R, lifecycle/no-fill, observation-only, and context-only labels stay separate. |
| Date concentration | `ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md:12` says the headline depth delta flips when 2026-04-28 is removed. | Require leave-one-date/session and effective-N before claims. |
| Queue overfit | `ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md:126` says MBO did not show strong queue-flow separation beyond depth. | Treat MBO queue fields as secondary until depth-only explanations fail. |
| Source proxy false confidence | `LTO013_SIERRA_SOURCE_PARITY_REGISTRY_2026-05-05.md:39-45` separates validated, same-market, blocked, and no-proxy symbols. | Every hypothesis names proxy status and source-transfer blockers. |
| GBPJPY two-book semantics | `LTO014_GBPJPY_ORDERFLOW_PROXY_GAP_2026-05-05.md:75` forbids treating two-book context as broker outcome validation. | GBPJPY orderflow stays blocked until 6B/6J transfer and synthetic-cross protocol pass. |
| XAGUSD/SI depth definition | `LTO030_6B_SI_DEPTH_POLICY_2026-05-05.md` keeps SI blocked after common-second masking failed to remove material depth deltas. | XAGUSD/SI depth remains source-status only. |
| Sierra footprint/profile incompleteness | `LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.md:25-28` says delta is ready but stacked imbalance, VAH, and VAL are blocked. | No stacked imbalance or value-area claim until source definitions are frozen. |
| Momentum duplicate route | `kb_edge_mechanisms_and_risks.md:73` says the dumb momentum baseline remains untested. | Stop-cascade hypotheses must compare against generic pullback/momentum baselines. |
| Narrative trap | `kb_edge_mechanisms_and_risks.md:51` says GTOS should not be described as reading institutional footprints. | Use observable flow/depth signatures, not intent language. |

## Killed-Route Notes

- `KILL-G4-001`: Do not promote a broad orderflow filter from current local evidence. Blocked by actual-R sparsity, date concentration, and local closure synthesis.
- `KILL-G4-002`: Do not infer heatmap/resting liquidity from trades-only or MT5 CFD tick volume. Trades can support aggressor flow, not resting book.
- `KILL-G4-003`: Do not use MBP-1 as full ladder evidence. MBP-10 or MBO/Sierra depth is needed for ladder-depth questions.
- `KILL-G4-004`: Do not activate NAS100 orderflow replay or live adverse-selection veto. The floors are not met.
- `KILL-G4-005`: Do not treat XAUUSD orderflow continuation as validated from current two-winner/no-loser contrast.
- `KILL-G4-006`: Do not activate USDJPY/6J or GBPJPY two-book orderflow proxies. USDJPY transfer is review-open; GBPJPY is blocked.
- `KILL-G4-007`: Do not claim "institutional footprint" intent. GTOS can observe flow/depth/auction effects, not private motives.
- `KILL-G4-008`: Do not mark any external source validation-safe while the G0 budget ledger has `$0` new cash cap and source contracts are incomplete.

## Source And Budget Blockers

- The program source ledger keeps current external cash spend cap at `$0`; no G4 source contract is validation-safe.
- Databento live remains blocked for NAS100/NQ by `LIVE_SESSION_FAILED_NO_LICENSE`.
- Databento historical credits can be used only under estimate-first, cost-capped manifests; this lane made no paid data calls.
- Sierra depth is shadow/source metadata only until parser/parity and symbol-specific source policies pass.
- Nasdaq NOII and LBMA/ICE auction data require licensing/subscription or explicit source contracts before feature use.
- Direct CME rulebook/docs fetches returned 403; no claim depends on those blocked raw files.

## Neighbor-Lane Pass

After first synthesis, G4 inspected neighboring lane worktrees `G3`, `G6`, and `G11`. `G11` still contains only the shared scaffold and G0 artifacts, with no domain synthesis, mechanism rows, hypothesis rows, prereg rows, or status rows from that lane.

`G3` produced geometry/fractal/signal rows after G4's first synthesis pass. G4 read the G3 synthesis, mechanism rows, hypothesis rows, preregs, and status summary, then added only two G4/G3 hypotheses that survive the source, leakage, and killed-route checks:

- `HYP-G4G3-DC-DEPTH-013`: tests whether directional-change overshoot/event-density state conditions OFI/depth depletion around structure breaks. It stays blocked by same-dataset discovery limits, source transfer, and the sweep-reversal trap risk named by G3.
- `HYP-G4G3-AUCTION-PATH-014`: tests whether auction/orderflow context plus G3 topology/path features separates choppy retests from directional displacements. It stays blocked by auction source contracts, TDA/path dimensionality risk, and context-only status.

`G6` produced a momentum/reversion synthesis, row registry, and completion audit after G4's first synthesis pass. G4 read those neighbor-owned outputs and added only G4/G6 cross-domain hypotheses that survive the source, leakage, and killed-route checks:

- `HYP-G4G6-DEPTH-CONTINUATION-010`: tests whether source-valid NAS100/NQ depth-adverse-selection state interacts with G6 opening-drive/continuation regimes. It stays blocked by NAS100 actual-R sparsity and date concentration.
- `HYP-G4G6-CASCADE-GENERIC-011`: tests whether stop-cascade/retest orderflow adds value over G6's required generic momentum/retrace baseline. It stays discovery-only until the dumb momentum comparator is frozen.
- `HYP-G4G6-AUCTION-EXHAUSTION-012`: tests whether auction/opening-drive context plus as-of depth/imbalance separates continuation from exhaustion. It stays observation/context-only until auction source contracts and source-safe imbalance feeds exist.

No G11 cross-domain rows were added. Adding rows without neighbor-owned evidence would violate source, leakage, and killed-route discipline. Candidate links to revisit after G11 produces outputs:

- G11 data-source expansion could join orderflow only through source-contract and proxy-transfer rows.

## Output Files

- `research/science_program_2026_05/00_control/G4_SOURCE_INDEX_2026-05-06.md`
- `research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_SOURCE_CONTRACTS_2026-05-06.json`
- `research/science_program_2026_05/01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_SYNTHESIS_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_CONTEXT_LEDGER_2026-05-06.md`
- `research/science_program_2026_05/02_hypothesis_registry/G4_MICROSTRUCTURE_AUCTION_MECHANISMS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G4_MICROSTRUCTURE_AUCTION_HYPOTHESES_2026-05-06.json`
- `research/science_program_2026_05/03_experiment_specs/G4_MICROSTRUCTURE_AUCTION_EXPERIMENT_PREREGS_2026-05-06.json`
- `research/science_program_2026_05/00_control/G4_MICROSTRUCTURE_AUCTION_GOAL_STATUS_2026-05-06.json`

## NO_PROMOTION_VERDICT

Every G4 mechanism, hypothesis, source contract, prereg, ledger, and synthesis row remains `NO_PROMOTION_VERDICT`. This lane produced research artifacts only.
