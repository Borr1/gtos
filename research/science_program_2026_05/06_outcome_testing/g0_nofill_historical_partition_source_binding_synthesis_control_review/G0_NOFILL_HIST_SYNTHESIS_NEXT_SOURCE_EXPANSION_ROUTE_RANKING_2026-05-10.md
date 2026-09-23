# Next Source Expansion Route Ranking

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "next_source_expansion_route_ranking",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T04:31:04Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recommended_next_route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
  "recommended_next_route_terminal_boundary": "Build a source-hashed candidate packet and exact blocker ledger only; route to G12 source/control audit next. Do not execute validation or score outcomes.",
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "routes": [
    {
      "candidate_universe_seed": {
        "date_rule": "Future builder must recompute from contaminated row ledger by symbol/source-lane and exclude source-date plus one-day embargo overlaps before row admission.",
        "embargo_clear_tick_dates_by_symbol": {
          "GBPJPY": [
            "2026-04-28",
            "2026-05-08"
          ],
          "GBPUSD": [
            "2026-04-28",
            "2026-05-08"
          ],
          "NAS100": [
            "2026-04-27",
            "2026-04-28",
            "2026-05-08"
          ],
          "US30_cash": [
            "2026-04-27",
            "2026-04-28",
            "2026-05-08"
          ],
          "USDJPY": [
            "2026-04-28",
            "2026-05-08"
          ],
          "XAGUSD": [
            "2026-04-28",
            "2026-05-08"
          ],
          "XAUUSD": [
            "2026-04-28",
            "2026-05-08"
          ]
        }
      },
      "must_not_do": [
        "score outcomes",
        "read broker actual-R/account history",
        "promote",
        "edit registry",
        "change live behavior"
      ],
      "rank": 1,
      "required_outputs": [
        "source hash manifest for every consumed tick/shadow/source file",
        "frozen source-bound NOFILL candidate packet",
        "55-field binding checklist per row",
        "duplicate key and duplicate group ledgers",
        "forbidden field scan",
        "G12 audit prompt pack"
      ],
      "route_class": "source_expansion_builder",
      "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
      "source_roots": [
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
        "current worktree committed source-control artifacts"
      ],
      "status": "BEST_NEXT_G0_SOURCE_CONTROL_ROUTE",
      "why": "Uses already-local MT5 tick parquet plus candidate/pending shadow logs; no paid/API route is needed."
    },
    {
      "must_not_do": [
        "treat futures proxy context as direct CFD/broker validation",
        "score NOFILL outcomes in this route"
      ],
      "rank": 2,
      "required_outputs": [
        "Sierra parser/source hash manifest",
        "proxy transfer contract by symbol",
        "as-of timestamp convention",
        "separation from GTOS broker NOFILL labels"
      ],
      "route_class": "source_contract_and_context_packet",
      "route_id": "NOFILL_SIERRA_FUTURES_PROXY_CONTEXT_SOURCE_EXPANSION",
      "source_roots": [
        "C:\\SierraChart\\Data",
        "C:\\SierraChart\\Data\\MarketDepthData"
      ],
      "status": "PROMISING_CONTEXT_ROUTE_NOT_DIRECT_VALIDATION",
      "why": "Sierra SCID/depth files exist for GC/SI/NQ/YM/6J/6B proxy families and can improve source/context design."
    },
    {
      "must_not_do": [
        "restart live processes in this lane",
        "treat forward capture realism as historical sealed validation"
      ],
      "rank": 3,
      "required_outputs": [
        "owner/current-process state check",
        "first-row schema verification",
        "forward pool separation from historical sealed validation"
      ],
      "route_class": "forward_shadow_source_capture",
      "route_id": "NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_CANDIDATE_PACKET",
      "source_roots": [
        "shadow_logs\\nofill_forward_source_capture.jsonl"
      ],
      "status": "USEFUL_BUT_NOT_HISTORICAL_SEALED_VALIDATION",
      "why": "The additive 55-field logger is source/control accepted, but no forward capture row exists yet."
    },
    {
      "must_not_do": [
        "use stale artifacts as sealed validation rows"
      ],
      "rank": 4,
      "required_outputs": [
        "prior artifact hash ledger",
        "contradiction ledger",
        "proof that no row is admitted solely from stale worktree output"
      ],
      "route_class": "source_control_reconciliation",
      "route_id": "NOFILL_PRIOR_WORKTREE_ARTIFACT_RECONCILIATION_CONTROL_ROUTE",
      "source_roots": [
        "C:\\tmp\\gtos_otb"
      ],
      "status": "CONTROL_ONLY_NOT_ROW_EXPANSION",
      "why": "Prior worktrees can catch contradictions but are likely contaminated by prompt/audit exposure."
    },
    {
      "must_not_do": [
        "open inside this G0 synthesis or next source expansion builder"
      ],
      "rank": 5,
      "required_outputs": [
        "separate owner-approved evidence-class prompt if ever needed"
      ],
      "route_class": "forbidden_here",
      "route_id": "BROKER_ACCOUNT_HISTORY_OR_RESULT_LABEL_ROUTE",
      "source_roots": [],
      "status": "CLOSED_IN_THIS_G0_SOURCE_CONTROL_ROUTE",
      "why": "The controlling prompt forbids broker actual-R, account/order/deal/position behavior, result/cost labels, and validation execution."
    }
  ],
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "validation_safe": false
}
```
