# OTX G6 Blocker Impossibility Ledger

- Generated at UTC: `2026-05-07T07:50:26Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTX_G6_BLOCKER_IMPOSSIBILITY_LEDGER",
  "generated_at_utc": "2026-05-07T07:50:26Z",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rows": [
    {
      "evidence": "External ticks are quote/path evidence only; they do not encode GTOS selected OB identity or market-state source rows.",
      "internal_decision": "BLOCKED_WITH_EXACT_IMPOSSIBILITY_FROM_APPROVED_LOCAL_TICKS",
      "next_exact_unblocker": "Prospective mechanical_ob_bounds_asof_v1 capture with market_state source path/hash, row hash, H1 OB id, low/high/mid, OB creation UTC, impulse BOS UTC, mitigation state, and touch sequence.",
      "packet_id": "OTG0-PKT-060",
      "status": "BLOCKED"
    },
    {
      "evidence": "Decision quote and ordered tick-path hashes exist for most rows, but the coverage ledger identifies the missing row exactly.",
      "internal_decision": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE",
      "next_exact_unblocker": "Capture or recover XAUUSD 2026-05-06 07:15 UTC decision quote and ordered path ticks, then have G12 review the fixed-horizon proposal.",
      "packet_id": "OTG0-PKT-061",
      "status": "BLOCKED_WITH_EXACT_PARTIAL_TICK_COVERAGE_EVIDENCE"
    },
    {
      "evidence": "Tick-derived range/breakout/path fields and OTI4b quarantined result ledger emitted.",
      "internal_decision": "CLEARED_AND_QUARANTINED_TESTED_DISCOVERY_ONLY_WITH_ROW_EXCLUSIONS",
      "next_exact_unblocker": "Sample floor and external G12 result-lane audit before any validation claim.",
      "packet_id": "OTG0-PKT-062",
      "status": "CLEARED_AND_QUARANTINED_TESTED_WITH_ROW_EXCLUSIONS"
    },
    {
      "evidence": "Tick-derived changepoint feature packet emitted without outcome labels; coverage ledger identifies insufficient-window rows.",
      "internal_decision": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS",
      "next_exact_unblocker": "G12 must accept the OTX CUSUM parser and either exclude or recapture rows without sufficient predecision M1 bars before scoring.",
      "packet_id": "OTG0-PKT-063",
      "status": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS"
    },
    {
      "evidence": "Structured sweep status/type/level/source fields joined to XAU rows where predecision tick coverage exists; row gaps are explicit.",
      "internal_decision": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS",
      "next_exact_unblocker": "G12 must accept the sweep parser and either exclude or recapture XAU rows without predecision tick coverage; sample floor remains 150 XAU OB-retouch rows.",
      "packet_id": "OTG0-PKT-066",
      "status": "CLEARED_FOR_EXTERNAL_G12_REAUDIT_WITH_EXACT_ROW_BLOCKERS"
    }
  ],
  "validation_safe": false
}
```
