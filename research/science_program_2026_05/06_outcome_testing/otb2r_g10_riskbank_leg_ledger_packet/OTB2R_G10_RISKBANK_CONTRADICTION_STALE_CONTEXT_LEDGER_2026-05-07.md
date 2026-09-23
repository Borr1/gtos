# Contradiction Stale-Context Ledger - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`

```json

[
  {
    "evidence": [
      "research/science_program_2026_05/06_outcome_testing/otl2_synthetic_replay_packet_audit/OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json"
    ],
    "item": "OTL2 blocked all synthetic packets, but OTI2 later ran OTG0-PKT-013.",
    "resolution": "OTL2 was the initial audit. OTB2R later rebuilt a sanitized G10 packet, and G12 OTB rebuild reaudit accepted only OTG0-PKT-013 for future outcome-test packet audit."
  },
  {
    "evidence": [
      "research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json"
    ],
    "item": "OTB0/G12 blocker-clearing baseline listed OTG0-PKT-013 as blocked/rejected.",
    "resolution": "OTB0 and first G12 audit remain valid historical baselines; OTB2R rebuilt sanitized source hashes and coverage later, clearing those blockers for this packet only."
  },
  {
    "evidence": [
      "research/science_program_2026_05/06_outcome_testing/g12_oti_post_test_audit/G12_OTI_POST_TEST_ACCEPTED_REJECTED_BLOCKED_SUMMARY_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json"
    ],
    "item": "G12 accepted OTI2 as quarantined evidence, but risk-bank primary metric is not computable.",
    "resolution": "Acceptance is lane-level quarantined discovery only. G12 explicitly retains a residual question requiring leg-level risk-bank fields before any risk-bank score."
  },
  {
    "evidence": [
      "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json",
      "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl"
    ],
    "item": "Packet coverage says M1 path recovered, while supporting path-contract rows say no tick-order claim.",
    "resolution": "These are different evidence roles. OTB2R packet hashes bind to sanitized candidate_ltf_path_order M1 coverage and same-M1 ambiguity flags; candidate_path_contract latest rows are supporting negative evidence that terminal/tick order should not be claimed."
  }
]

```