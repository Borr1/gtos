# G12 G3 G6 Blocked Rejected Question Ledger 2026-05-07 - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

```json
{
  "artifact_family": "G12_G3_G6_PACKET_BUILDER_AUDIT",
  "artifact_type": "blocked_rejected_question_ledger",
  "blocked_or_rejected_packets": [
    {
      "builder_exact_blockers": [
        {
          "blocker_id": "G6-BLK-060-OB-BOUNDS-PARTIAL",
          "blocking_fact": "Some OB bounds are parsed from decision-time verifier text rather than a structured OB bounds source.",
          "exact_missing_field_or_source": "Structured mechanical OB low/high, OB creation event, and touch sequence captured as decision-time fields for every row.",
          "next_action": "Add source-specific structured OB bounds capture before any OB-vs-generic outcome test.",
          "packet_id": "OTG0-PKT-060"
        }
      ],
      "decision": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
      "decision_reason": "Structured OB bounds are core to OB-vs-generic; verifier-text parsing is not strong enough for this packet to clear outcome-audit readiness.",
      "evidence": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "experiment_id": "G6-EXP-001-OB-VS-GENERIC-RETRACE",
      "next_exact_question": "Can every OB bound and generic retrace comparator be supplied from structured mechanical market-state/source rows with file/row hash, and can the matched-control denominator reach the preregistered floor without standalone generic rows?",
      "packet_id": "OTG0-PKT-060"
    },
    {
      "builder_exact_blockers": [
        {
          "blocker_id": "G6-BLK-061-CNR-ORDERED-PATH",
          "blocking_fact": "Continuation/no-retrace candidate rows exist but exact executable decision price and ordered post-decision path are incomplete.",
          "exact_missing_field_or_source": "Exact decision executable price plus ordered M1/tick path source included in input packet, not resolution labels.",
          "next_action": "Capture exact price and ordered path prospectively; keep resolution logs closed until packet freeze.",
          "packet_id": "OTG0-PKT-061"
        }
      ],
      "decision": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
      "decision_reason": "Exact executable decision price and ordered path are core to continuation/no-retrace lifecycle odds.",
      "evidence": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
      "next_exact_question": "Can a prospective packet supply exact executable decision price plus ordered M1/tick path source before any continuation/no-retrace resolution labels are opened?",
      "packet_id": "OTG0-PKT-061"
    },
    {
      "builder_exact_blockers": [
        {
          "blocker_id": "G6-BLK-063-TRUE-CHANGEPOINT",
          "blocking_fact": "Current packet supplies fixed OHLC proxy exhaustion fields, not a registered statistical changepoint model.",
          "exact_missing_field_or_source": "Preregistered changepoint parser/model output with feature_asof_utc <= decision_asof_utc.",
          "next_action": "Treat current exhaustion packet as input-feature scaffold; register a true changepoint source before scoring.",
          "packet_id": "OTG0-PKT-063"
        }
      ],
      "decision": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
      "decision_reason": "A true preregistered changepoint source is core to the exhaustion/changepoint hypothesis; current fields are only OHLC proxy scaffolding.",
      "evidence": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
      "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
      "next_exact_question": "Can a preregistered changepoint parser/model output be produced with feature_asof_utc <= decision_asof_utc and fixed thresholds before scoring?",
      "packet_id": "OTG0-PKT-063"
    },
    {
      "builder_exact_blockers": [
        {
          "blocker_id": "G6-BLK-066-LIQUIDITY-SWEEP-STRUCTURE",
          "blocking_fact": "Round-number fields are local and source-safe, but liquidity sweep fields are not structured for every row in this packet.",
          "exact_missing_field_or_source": "Decision-time liquidity sweep type, sweep level, and source hash joined to the XAU OB zone.",
          "next_action": "Add a structured liquidity-sweep as-of projection before testing round-number/OB confluence outcomes.",
          "packet_id": "OTG0-PKT-066"
        }
      ],
      "decision": "BLOCKED_WITH_NEXT_EXACT_QUESTION",
      "decision_reason": "Structured liquidity-sweep fields are core to the round-number/OB confluence hypothesis.",
      "evidence": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
      "experiment_id": "G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE",
      "next_exact_question": "Can decision-time liquidity sweep type, sweep level, and source hash be joined to every XAU OB-zone/round-number record before outcome opening?",
      "packet_id": "OTG0-PKT-066"
    }
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rejected_alternative_packetizations": [
    {
      "alternative": "Use only the 86 accepted OTB2R path rows from candidate_ltf_path_order projections",
      "decision": "REJECTED_AS_PRIMARY_G3_FEATURE_SOURCE",
      "reason": "Those rows answer path-order source existence, not DC/TDA pre-decision feature construction. Many decisions are 2026-05-03 to 2026-05-06 after local OHLC coverage and some LTF rows are SOURCE_BLOCKED."
    },
    {
      "alternative": "Open V2/V3 forward pair resolution or path-scaling replay ledgers",
      "decision": "REJECTED_FOR_POLICY",
      "reason": "Those files are result-bearing synthetic path/replay ledgers and may expose terminal order, hit TP/SL, or path-R values."
    },
    {
      "alternative": "Use broker account/trade record actual-R files to backfill labels or terminal order",
      "decision": "REJECTED_FOR_POLICY",
      "reason": "Broker actual-R is forbidden for this OTB2R input-only builder and remains absent from primary metric fields."
    },
    {
      "alternative": "Use prior blocked G3 packet records",
      "decision": "REJECTED_AS_DATA_SOURCE",
      "reason": "Prior OTB2R G3 packets contain zero rebuilt records; their file hashes are retained only as control evidence."
    },
    {
      "alternative": "Fetch public DC/TDA examples or market data from the network",
      "decision": "REJECTED_FOR_SCOPE",
      "reason": "G3 source contract allows methodology context only; this lane uses local market evidence and performs no network/API/data purchase."
    },
    {
      "alternative": "Use same-bar terminal path assumptions to fill unavailable synthetic replay fields",
      "decision": "REJECTED_FOR_NO_LEAK",
      "reason": "This builder computes only pre-decision geometry. Same-bar policy is recorded as input-only and never claims terminal order."
    },
    {
      "alternative": "shadow_logs/continuation_no_retrace_resolutions.jsonl",
      "decision": "REJECTED_AS_PACKET_INPUT_SOURCE",
      "reason": "Post-decision continuation resolution labels are not packet inputs."
    },
    {
      "alternative": "shadow_logs/m15_choch_diagnostic_audit.jsonl",
      "decision": "REJECTED_AS_PACKET_INPUT_SOURCE",
      "reason": "Contains post-decision path labels and touch/hit fields; used only as blocker context, not records."
    },
    {
      "alternative": "shadow_logs/broker_actual_r_audit.jsonl",
      "decision": "REJECTED_AS_PACKET_INPUT_SOURCE",
      "reason": "Broker actual-R is forbidden in this packet lane."
    },
    {
      "alternative": "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
      "decision": "REJECTED_AS_PACKET_INPUT_SOURCE",
      "reason": "Account-history realized-R/fill data is forbidden in this packet lane."
    },
    {
      "alternative": "Pool OB setup rows and generic retrace comparator rows as independent records",
      "decision": "REJECTED_DENOMINATOR_INFLATION",
      "reason": "OTG0-PKT-060 must use matched_control_group_id; OB and generic comparator fields share one setup denominator."
    },
    {
      "alternative": "Treat same-bar path windows as terminal-order evidence",
      "decision": "REJECTED_NO_LEAK_TIMING_POLICY",
      "reason": "Packets may define path_start/path_end only; terminal order remains unclaimed until a future outcome lane freezes tick/order policy."
    },
    {
      "alternative": "Open broker actual-R or OTI quarantined result folders to judge packet quality",
      "decision": "REJECTED_FOR_SCOPE_AND_LABEL_POLICY",
      "reason": "This audit is packet-readiness only and must not inspect broker actual-R, result values, or blocked outcomes."
    }
  ],
  "validation_safe": false
}
```
