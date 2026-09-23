# NOFILL Forward Source Inventory And Search Ledger 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Route Decision

The builder consumes the current worktree allowlisted logs, the frozen CAT V3 count packet, the accepted addendum schema, and source-hashed local tick parquet for spread fields only. Absolute main shadow logs have matching hashes for the approved current logs. Prior worktrees under `C:/tmp/gtos_otb` were searched and added `0` needed candidate IDs beyond the current allowlisted logs.

Rows without approved-log matches are retained as source/control projection rows with explicit missing statuses. They are not scored and do not change the denominator.

## Approved Logs

| Log | Exists | Lines | Candidate IDs | Forbidden Raw Key Hits |
|---|---:|---:|---:|---|
| `shadow_logs/strategy_follow_candidates.jsonl` | `True` | `190` | `190` | `mt5_order_ticket` |
| `shadow_logs/candidate_path_follow.jsonl` | `True` | `4088` | `190` | `none` |
| `shadow_logs/candidate_ltf_path_order.jsonl` | `True` | `6914` | `190` | `none` |
| `shadow_logs/pending_limit_lifecycle.jsonl` | `True` | `237` | `7` | `actual_r, broker_fill_state, fill_time_utc, mt5_order_ticket, order_send_attempted, order_send_success, pending_ticket, slippage_price, synthetic_path_r, trade_state_ticket` |
| `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl` | `True` | `285` | `11` | `none` |
| `shadow_logs/prefill_delivery_path.jsonl` | `True` | `190` | `190` | `none` |
| `shadow_logs/v2b_forward_pairs.jsonl` | `True` | `190` | `190` | `none` |
| `shadow_logs/fvg_ob_confluence.jsonl` | `True` | `190` | `190` | `none` |

## Negative Evidence

- Prior worktree log union did not add missing universe candidate IDs.
- Absolute main shadow logs match the current hashes for approved logs.
- Tick parquet supports spread source-control fields only; it does not supply order, fill, account, deal, position, R, win-rate, expectancy, DSR, or PBO evidence.
