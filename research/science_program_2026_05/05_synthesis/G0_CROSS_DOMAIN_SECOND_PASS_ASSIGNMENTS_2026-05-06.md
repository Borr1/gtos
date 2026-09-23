# G0 Cross-Domain Second-Pass Assignments - 2026-05-06

**Lane:** `G0`
**Status:** `CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_READY_FOR_LANE_HANDOFF`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Generated at UTC:** `2026-05-06T08:53:27Z`

These assignments are research handoffs only. They do not authorize source validation, live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid data, or order behavior changes.

## CD2-01 - Macro-vol-source freshness triad

- Lanes: `G7, G8, G11, G1`
- Seed rows: `HYP-G7-XG8-VOL-MACRO-011, HYP-G7-XG11-SOURCE-FRESH-012, HYP-G11-PUBLIC-LAG-004, HYP-G8-VRP-004`
- Objective: Freeze publication/as-of rules for macro, volatility-index, and source-freshness context before any outcome review.
- Stop output: source-freshness compatibility ledger plus prereg update proposal, not a validation result
- Required blocker checks:
  - FRED/BIS/COT/Cboe publication timestamps
  - no stale calendar or revised value leakage
  - source_contract_v2 rows remain validation_safe=false until parser/cache/no-lookahead tests pass
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-02 - Short-vol stress versus execution lifecycle

- Lanes: `G8, G10, G11`
- Seed rows: `HYP-G8-VIX1D9D-STRESS-002, G10-HYP-PENDING-001, G10-HYP-PREFILL-003, HYP-G11-FRICTION-GATE-007`
- Objective: Define whether short-tenor volatility context can be joined to pending-limit no-fill, spread, and close-side cost rows without label mixing.
- Stop output: lifecycle-only prereg and missing-source ledger
- Required blocker checks:
  - Cboe CSV same-day availability
  - pending lifecycle ordering
  - close-side slippage coverage
  - synthetic path-R, lifecycle, and broker actual-R separation
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-03 - Offline-RL reward and risk-bank boundary

- Lanes: `G9, G10, G1, G6`
- Seed rows: `HYP-G9-OFFLINE-RL-POLICY-009, G10-HYP-RISKBANK-005, G6-HYP-002`
- Objective: Translate offline policy comparison into a frozen reward definition that respects risk-bank invariants and never uses live exploration.
- Stop output: offline-only reward contract and red-teamable prereg; no policy promotion
- Required blocker checks:
  - no live sizing or execution change
  - risk-bank invariant
  - duplicate lifecycle controls
  - broker actual-R versus synthetic path-R separation
  - DSR/PBO/effective-N policy
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-04 - K55 source-provenance and orderflow feature gate

- Lanes: `G9, G4, G11, G1`
- Seed rows: `HYP-G9G4-K55-SOURCE-006, HYP-G9G4-TOOL-ORDERFLOW-005, HYP-G11G4-SOURCE-GATED-ORDERFLOW-008, HYP-G4-OFI-DEPTH-001`
- Objective: Convert orderflow/depth rows into K55 source-status and provenance flags only, not validation-safe predictive features.
- Stop output: feature-provenance contract and source-status join map
- Required blocker checks:
  - Databento/Sierra legality and timestamp provenance
  - feature bundle target-version match
  - no source marked validation_safe=true
  - tool-grounding remains approval/budget blocked
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-05 - Macro attention and behavioral attention interaction

- Lanes: `G7, G5, G1`
- Seed rows: `HYP-G7-XG5-MACRO-ATTN-010, HYP-G5-XG7-MACRO-ATTN-009, HYP-G7-FOMC-ATTN-003, HYP-G5-NEWS-005`
- Objective: Resolve duplicated macro/news attention rows into one lifecycle-only prereg with stale-calendar and event-publication gates.
- Stop output: deduped attention prereg proposal and blocker ledger
- Required blocker checks:
  - local calendar freshness
  - event source publication timestamp
  - no post-release surprise leakage
  - no live news-filter change
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-06 - Pre-fill delivery path and no-retrace opportunity map

- Lanes: `G10, G6, G4`
- Seed rows: `G10-HYP-PREFILL-003, G10-HYP-XDOMAIN-008, G6-HYP-002, HYP-G4-FILL-QUALITY-009`
- Objective: Make setup-decision-to-fill/cancel path capture precise enough to study no-retrace and adverse-fill mechanisms without scoring a live strategy.
- Stop output: prefill path capture spec and missing-field audit
- Required blocker checks:
  - exact decision entry price
  - ordered M1 or tick path
  - pending lifecycle state
  - same-bar ambiguity classification
  - fill/no-fill separated from R labels
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-07 - Prop-firm stress calendar and portfolio opportunity cost

- Lanes: `G10, G7, G8, G11`
- Seed rows: `G10-HYP-PROP-006, G10-HYP-PORTFOLIO-007, HYP-G7-CROSSASSET-STRESS-008, HYP-G8-VVIX-TAIL-007`
- Objective: Define observation-only portfolio/risk stress context that explains blocked opportunity cost without changing risk, correlation gates, or order behavior.
- Stop output: portfolio opportunity-cost source map and observation-only prereg
- Required blocker checks:
  - prop rule parser completeness
  - correlation/opportunity lifecycle labels
  - stress context as-of timestamps
  - no risk config edits
- Promotion verdict: `NO_PROMOTION_VERDICT`

## CD2-08 - Source/no-leak field cleanup pass

- Lanes: `G11, G7, G5, G0, G12`
- Seed rows: `all HYP-G11-* rows, HYP-G7-XG5-MACRO-ATTN-010, HYP-G7-XG8-VOL-MACRO-011, HYP-G7-XG11-SOURCE-FRESH-012`
- Objective: Separate actual source_contract_v2 references from literature references, future placeholders, and forbidden outcome-field lists.
- Stop output: row-cleanup proposal for G12 review; no row promotion
- Required blocker checks:
  - no_leak_fields must be as-of feature names, not forbidden fields
  - source_ids must resolve to source_contract_v2 or move to evidence_refs
  - all source contracts remain validation_safe=false unless explicit blocker-clearing notes exist
- Promotion verdict: `NO_PROMOTION_VERDICT`

