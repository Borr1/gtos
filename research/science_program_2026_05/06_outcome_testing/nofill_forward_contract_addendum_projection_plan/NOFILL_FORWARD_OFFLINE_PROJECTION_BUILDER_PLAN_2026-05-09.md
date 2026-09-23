# NOFILL Forward Offline Projection Builder Plan 2026-05-09

- route_id: `NOFILL_FORWARD_CONTRACT_ADDENDUM_PROJECTION_PLAN`
- promotion_verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Purpose

Build an offline, read-only projection builder that consumes existing source/log artifacts only through an allowlist and emits source/control rows matching `NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json`.

## Inputs

- `shadow_logs/strategy_follow_candidates.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/candidate_ltf_path_order.jsonl`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl`
- `shadow_logs/prefill_delivery_path.jsonl`
- `shadow_logs/v2b_forward_pairs.jsonl`
- `shadow_logs/fvg_ob_confluence.jsonl`
- read-only tick/lower-timeframe manifests only when source-hashed
- parser/build/source-contract artifacts listed in the context anchor

## Projection Stages

1. Read raw rows as source inventory and compute source SHA256, parser SHA256, controlling git head, source line number, and source route.
2. Apply a strict allowlist for identity, decision/as-of, source coverage, event-order, and the addendum fields.
3. Redact ticket, order-send, fill, account/order-history, slippage, execution-quality, actual-R, synthetic-R, win-rate, expectancy, DSR, and PBO fields.
4. Emit explicit missing statuses for capture latency/write/skew, native pending-order observability, and entry-touch spread when source fields are absent.
5. Attach duplicate/denominator controls and assert `NO_CHANGE` to the frozen 225/182/139 denominators.
6. Run verifier before any row is treated as contract-complete.

## Forbidden Routes

No MT5 live call, order/account/history/deal/position export, paid/API/Databento call, live logger wiring, prompt/risk/execution/permissions/safety/selector/canary change, result scoring, validation, promotion, or registry edit is opened by this plan.

## Future Owner/Access Requirements

- Direct live capture latency/write/skew population requires a separate owner-approved live-wiring lane.
- Native broker pending-order observability beyond redacted status requires a separate source contract proving no ticket/order-history/fill leakage.
- Cost/slippage/execution-quality or survival-adjusted expectancy testing requires a separate result/cost lane after source fields are captured and accepted.
