# G12 R11 Downstream Fork: Executable Geometry Capture Implementation

Route ID: G12_R11_EXECUTABLE_GEOMETRY_CAPTURE_IMPLEMENTATION_ROUTE
Date: 2026-05-16
Evidence class: G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_ONLY

## Objective

Implement a no-promotion, research-only geometry capture route that can convert the
5,502 R11 row-level capture requirements into replayable trade geometry rows for a
future sealed retest. This route must not edit live trading, prompts, config, risk,
safety, execution, canary, selector, broker, order, history, deal, or position
surfaces.

## Mandatory Context And Posture

Before any work, regenerate/read `.context/LIVE_STATE.md`, then read AGENTS.md,
CLAUDE.md, `.context/00_core/research_operating_doctrine.md`, and
`.context/00_core/goal_session_research_discipline.md` from disk. Do not rely on chat memory.
Treat those files and this prompt as active instructions, not
background; operationalize them in an instruction-coverage ledger.

Use active creativity and curiosity with no conservative brake. Pursue every
same-evidence-class repair opportunity first. If a row cannot be repaired, emit
proof-or-impossibility with the exact missing field, source, join key, and lawful
next route.

Safe flags are evidence labels only and must remain closed:

- NO_PROMOTION_VERDICT
- validation_safe=false
- outcome_review_opened=false
- live_effect=false

Forbidden surfaces remain closed: promotion/live-effect behavior, paid/API/vendor
access, broker/account/order/history/deal/position evidence, prompt/config/risk/
safety/execution/canary/selector edits, remote push, and raw market-data blob
commits.

## Required Inputs

- `R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_2026-05-16.jsonl`
- `R11_CAPTURE_SCHEMA_CONTRACT_2026-05-16.json`
- `G12_R11_CAPTURE_REQUIREMENT_AUDIT_LEDGER_2026-05-16.jsonl`
- `G12_R11_WEAK_OVERLAP_AUDIT_LEDGER_2026-05-16.jsonl`
- `G12_R11_SOURCE_ROOT_AUDIT_LEDGER_2026-05-16.jsonl`

## Implementation Scope

Create route-local or `src/research_infra/` research-only code that:

1. Defines a strict `ready8_trade_geometry_capture_contract_v1` schema matching
   the R11 contract fields.
2. Accepts one capture row per R11 row key and validates:
   `candidate_input_row_id`, `source_trade_intent_id`, `canonical_symbol`,
   `proxy_source_symbol`, `decision_time_utc`, `trade_side_long_short`,
   `entry_reference_price`, `entry_reference_time_utc`,
   `entry_order_type_or_fill_model`, `stop_loss_or_invalidation_price`,
   `target_price_or_r_multiple`, `risk_reward_ratio`, `horizon_m15_bars`,
   `path_source_timeframe`, `entry_first_touch_utc`, `target_first_touch_utc`,
   `stop_first_touch_utc`, `same_bar_target_stop_order_policy`,
   `spread_or_cost_model`, `slippage_model_or_observed_shadow_field`,
   `source_file_path`, `source_sha256`, `asof_cutoff_utc`, and
   `no_leak_status`.
3. Emits a row-level rejection ledger for any row that cannot be captured, with
   the exact missing field, source owner, source path, and lawful next route.
4. Produces a sealed forward retest execution packet only after every accepted
   row passes source hash, no-leak, identity, and path-order validation.

## Acceptance Criteria

- 5,502 R11 row keys are present exactly once in accepted capture rows or
  rejection rows.
- No arbitrary top-N, top 3/5/10, number-limited cutoff, or representative-only
  scope is allowed. Preserve all material rows in the full ledger.
- Accepted rows must bind to `candidate_input_row_id`; symbol-time-only rows are
  proxy evidence and cannot be marked exact.
- Same-bar target/stop order is rejected unless M1/tick path ordering or an
  explicit policy is present.
- Cost/spread/slippage is source-bound or policy-bound; broker/account/order/
  history/deal/position evidence remains closed.
- The route emits decision, recomputation, row-level capture, rejection,
  verifier, focused tests, artifact audit, manifest artifacts, and a completion
  audit.
- Emit a completion audit.

## Prohibited Reroutes

Do not emit a new G0, summary-only, blocker-only, ambiguity-only, or capture
requirement-only packet. The deliverable is executable code plus row-level
validation artifacts.
