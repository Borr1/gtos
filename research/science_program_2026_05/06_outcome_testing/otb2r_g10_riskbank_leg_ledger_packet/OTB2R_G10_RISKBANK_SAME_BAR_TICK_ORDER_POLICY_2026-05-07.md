# Same-Bar Tick-Order Policy - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_type": "same_bar_tick_order_policy",
  "m1_path_order_packet_rows": 86,
  "outcome_review_opened": false,
  "policy": "Same-minute terminal order is never guessed. M1 path-order evidence can flag same-minute ambiguity, but this packet does not resolve terminal order or populate outcome labels. Supporting candidate_path_contract rows currently say NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY for the latest accepted setup rows, so tick/terminal order must remain a future source requirement.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "same_bar_state_counts": {
    "not_flagged_or_not_applicable": 52,
    "same_m1_ambiguity_flagged": 34
  },
  "source_evidence": [
    {
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json",
      "sha256": "6ab93ef336c76a48d6d8c8ad96afbf5929261b6e60a6c00cd6fec5e40ac84766"
    },
    {
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl",
      "sha256": "afd1959582a0ee9326666466672cb2cdd9a39572e3df56421f85bfed3f019286"
    },
    {
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl",
      "sha256": "22a2960830823651b39833333f711e47936496568e4a7dace8b63ce4ac0d4d35"
    }
  ],
  "supporting_contract_tick_order_claim_counts": {
    "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY": 86
  },
  "terminal_order_claim_allowed": false,
  "terminal_order_evidence_counts": {
    "NO_TERMINAL_ORDER_CLAIM_PACKET_FLAGS_ONLY": 52,
    "SAME_M1_TERMINAL_AMBIGUITY_FLAGGED_NOT_RESOLVED": 34
  },
  "validation_safe": false
}

```