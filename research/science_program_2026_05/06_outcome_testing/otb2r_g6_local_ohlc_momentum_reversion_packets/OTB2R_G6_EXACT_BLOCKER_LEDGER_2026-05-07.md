# OTB2R G6 Exact Blocker Ledger - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "artifact_family": "OTB2R_G6_EXACT_BLOCKER_LEDGER",
  "blocker_count": 4,
  "blockers": [
    {
      "blocker_id": "G6-BLK-060-OB-BOUNDS-PARTIAL",
      "blocking_fact": "Some OB bounds are parsed from decision-time verifier text rather than a structured OB bounds source.",
      "exact_missing_field_or_source": "Structured mechanical OB low/high, OB creation event, and touch sequence captured as decision-time fields for every row.",
      "next_action": "Add source-specific structured OB bounds capture before any OB-vs-generic outcome test.",
      "packet_id": "OTG0-PKT-060"
    },
    {
      "blocker_id": "G6-BLK-061-CNR-ORDERED-PATH",
      "blocking_fact": "Continuation/no-retrace candidate rows exist but exact executable decision price and ordered post-decision path are incomplete.",
      "exact_missing_field_or_source": "Exact decision executable price plus ordered M1/tick path source included in input packet, not resolution labels.",
      "next_action": "Capture exact price and ordered path prospectively; keep resolution logs closed until packet freeze.",
      "packet_id": "OTG0-PKT-061"
    },
    {
      "blocker_id": "G6-BLK-063-TRUE-CHANGEPOINT",
      "blocking_fact": "Current packet supplies fixed OHLC proxy exhaustion fields, not a registered statistical changepoint model.",
      "exact_missing_field_or_source": "Preregistered changepoint parser/model output with feature_asof_utc <= decision_asof_utc.",
      "next_action": "Treat current exhaustion packet as input-feature scaffold; register a true changepoint source before scoring.",
      "packet_id": "OTG0-PKT-063"
    },
    {
      "blocker_id": "G6-BLK-066-LIQUIDITY-SWEEP-STRUCTURE",
      "blocking_fact": "Round-number fields are local and source-safe, but liquidity sweep fields are not structured for every row in this packet.",
      "exact_missing_field_or_source": "Decision-time liquidity sweep type, sweep level, and source hash joined to the XAU OB zone.",
      "next_action": "Add a structured liquidity-sweep as-of projection before testing round-number/OB confluence outcomes.",
      "packet_id": "OTG0-PKT-066"
    }
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}

```
