# Equivalence And Invalid Context Matrix

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

```json
{
  "artifact_family": "EQUIVALENCE_AND_INVALID_CONTEXT_MATRIX",
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "equivalence_row_count": 7,
  "equivalence_rows": [
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "EURUSD",
      "canonical_economic_group": "EURUSD_FUTURES_6E_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "6EM26-CME",
        "EURUSD"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "GBPUSD_6B",
      "canonical_economic_group": "GBPUSD_FUTURES_6B_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "6BM26-CME"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "NAS100_NQ",
      "canonical_economic_group": "NAS100_NQ_FUTURES_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "NQM26-CME",
        "MNQM26-CME"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "US30_YM",
      "canonical_economic_group": "US30_DOW_FUTURES_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "YMM26-CBOT",
        "MYMM26-CBOT"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "USDJPY_6J",
      "canonical_economic_group": "USDJPY_FUTURES_6J_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "6JM26-CME"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY_INVERSE_FX_CONTRACT",
      "special_mapping_requirement": "Inverse FX futures convention must be explicit before any context join."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "XAGUSD_SI",
      "canonical_economic_group": "XAGUSD_SILVER_FUTURES_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "SIM26-COMEX",
        "SILM26-COMEX"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_TRANSFER_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    },
    {
      "allowed_contexts": [
        "source availability and source-status control",
        "orderflow/depth context packet construction",
        "future parser fixture selection",
        "failure-anatomy hypothesis input after separate result lane opens",
        "proxy-transfer audit input after separate G12/G0 gate"
      ],
      "asof_roll_session_requirement": "Future packet must bind source family, exact contract/root, roll rule, session calendar, timezone policy, source hash/deferral, and non-equivalence label.",
      "broker_cfd_truth_allowed": false,
      "broker_native_cfd_truth_claim_allowed": false,
      "candidate_symbol": "XAUUSD_GC",
      "canonical_economic_group": "XAUUSD_GOLD_FUTURES_PROXY",
      "contract_attachment_status": "NON_EQUIVALENCE_CONTRACT_ATTACHED_CONTEXT_ONLY",
      "contracts_or_roots": [
        "GCM26-COMEX",
        "MGCM26-COMEX",
        "XAUUSD"
      ],
      "equivalence_status": "NON_EQUIVALENT_CONTEXT_OR_CONTROL_ONLY",
      "future_acceptance_gate": "Separate proxy-transfer validation or same-market source contract required before any result interpretation; this route emits no validation.",
      "invalid_context_rules": [
        {
          "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
          "invalid_context": "broker_native_cfd_truth"
        },
        {
          "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
          "invalid_context": "result_or_performance_claim"
        },
        {
          "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
          "invalid_context": "roll_or_session_ambiguous"
        },
        {
          "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
          "invalid_context": "stale_or_closed_market_depth"
        },
        {
          "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
          "invalid_context": "inverse_or_basis_missing"
        },
        {
          "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
          "invalid_context": "hash_or_pointer_missing"
        }
      ],
      "material_non_equivalence_factors": [
        "contract basis and roll calendar",
        "exchange session/calendar differences",
        "CFD broker spread/quote construction absent",
        "futures queue/depth not broker fill queue",
        "no account/order/deal/position evidence allowed"
      ],
      "may_score_results_now": false,
      "proxy_class": "FUTURES_PROXY_AND_SAME_MARKET_CONTEXT_ONLY",
      "special_mapping_requirement": "No symbol-specific override beyond contract/root, roll, session, and non-equivalence controls."
    }
  ],
  "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
  "generated_at_utc": "2026-05-13T02:48:20Z",
  "invalid_context_rules": [
    {
      "fail_closed_rule": "Reject any interpretation that futures/Sierra/Databento proxy data proves MT5 broker CFD quote, spread, queue, fill, order, deal, account, or position truth.",
      "invalid_context": "broker_native_cfd_truth"
    },
    {
      "fail_closed_rule": "Reject any use for validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion in this lane.",
      "invalid_context": "result_or_performance_claim"
    },
    {
      "fail_closed_rule": "Reject any proxy row without contract month, roll rule, exchange session calendar, timezone policy, and as-of timestamp.",
      "invalid_context": "roll_or_session_ambiguous"
    },
    {
      "fail_closed_rule": "Reject or flag clear-book-only, Sunday/holiday, sparse, or stale depth windows before any future context use.",
      "invalid_context": "stale_or_closed_market_depth"
    },
    {
      "fail_closed_rule": "Reject proxy rows such as USDJPY/6J unless inverse-price convention and basis caveat are explicit.",
      "invalid_context": "inverse_or_basis_missing"
    },
    {
      "fail_closed_rule": "Reject source rows without source pointer and sha256 or G12-accepted hash deferral id.",
      "invalid_context": "hash_or_pointer_missing"
    }
  ],
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
  "proxy_rows_context_only": 7,
  "route_id": "SCID_ORDERFLOW_PROXY_VALIDITY_CONTRACT_AND_CONTEXT_PACKET_ROUTE",
  "schema_version": "scid_blocked17_orderflow_proxy_contract_v1",
  "valid_contexts": [
    "source availability and source-status control",
    "orderflow/depth context packet construction",
    "future parser fixture selection",
    "failure-anatomy hypothesis input after separate result lane opens",
    "proxy-transfer audit input after separate G12/G0 gate"
  ],
  "validation_safe": false
}
```
