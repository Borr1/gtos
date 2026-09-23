# Proxy Validity Non Equivalence Ledger

- **route_id:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "all_proxy_rows_context_only": true,
  "artifact_family": "PROXY_VALIDITY_NON_EQUIVALENCE_LEDGER",
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:37:18Z",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "proxy_rows": [
    {
      "candidate_symbol": "EURUSD",
      "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
      "cfd_symbol": "EURUSD",
      "contracts_or_roots": [
        "6EM26-CME",
        "EURUSD"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "GBPUSD_6B",
      "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY",
      "cfd_symbol": "GBPUSD",
      "contracts_or_roots": [
        "6BM26-CME"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "NAS100_NQ",
      "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY",
      "cfd_symbol": "NAS100",
      "contracts_or_roots": [
        "NQM26-CME",
        "MNQM26-CME"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "US30_YM",
      "canonical_economic_group": "US30_DOW_FUTURES_PROXY",
      "cfd_symbol": "US30_cash",
      "contracts_or_roots": [
        "YMM26-CBOT",
        "MYMM26-CBOT"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "USDJPY_6J",
      "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY",
      "cfd_symbol": "USDJPY",
      "contracts_or_roots": [
        "6JM26-CME"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY_INVERSE_FX_CONTRACT",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "XAGUSD_SI",
      "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY",
      "cfd_symbol": "XAGUSD",
      "contracts_or_roots": [
        "SIM26-COMEX",
        "SILM26-COMEX"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    },
    {
      "candidate_symbol": "XAUUSD_GC",
      "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
      "cfd_symbol": "XAUUSD",
      "contracts_or_roots": [
        "GCM26-COMEX",
        "MGCM26-COMEX",
        "XAUUSD"
      ],
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "validity_status": "CONTEXT_ONLY_NOT_BROKER_NATIVE_CFD_TRUTH"
    }
  ],
  "route_id": "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_ltf_orderflow_proxy_source_expansion_v1",
  "validation_safe": false
}
```
