# Saturation Self-Red-Team Pass

- **saturation_decision:** `PASS_WITH_EXACT_NEXT_LANE_FOR_FULL_STREAM_DISCOVERY_AGGREGATION`

```json
{
  "artifact_family": "saturation_self_redteam_pass",
  "redteam_checks": [
    {
      "finding": "Path labels can look like trade results if wording is loose.",
      "repair_or_route": "Every G0 artifact and next prompt states labels are DISCOVERY_PATH_LABEL_ONLY and not wins/losses/R/PnL/expectancy.",
      "risk": "path-label overinterpretation",
      "status": "REPAIRED_IN_G0_AND_NEXT_PROMPT"
    },
    {
      "finding": "Only 120000 rows are materialized in each compact artifact, while over 12.7M rows are suppressed.",
      "repair_or_route": "Full aggregate counts drive denominator reasoning; compact crosstabs are labeled compact-sample-only; rank-1 prompt owns full-stream aggregation.",
      "risk": "compact-cap bias",
      "status": "ROUTED_WITH_EXACT_NEXT_LANE"
    },
    {
      "finding": "Family-level matrix ranks liquidity_stop_run_context highest, but choosing it alone would amplify selection bias.",
      "repair_or_route": "Rank-1 route is all-family and baseline-controlled.",
      "risk": "single-family cherry pick",
      "status": "REPAIRED_BY_ROUTE_SELECTION"
    },
    {
      "finding": "Simple baseline families can be ignored or mistaken for promotable strategies.",
      "repair_or_route": "Baseline role ledger freezes them as adversarial controls.",
      "risk": "baseline misuse",
      "status": "REPAIRED_IN_LEDGER"
    },
    {
      "finding": "Raw candidate attempts, duplicate keys, unique nonduplicate path denominator, compact written rows, and suppressed rows differ.",
      "repair_or_route": "Family coverage ledger and next prompt freeze all denominator names and policies.",
      "risk": "denominator confusion",
      "status": "REPAIRED_IN_LEDGER"
    },
    {
      "finding": "Current GTOS edge could hide orderflow/depth/tick/AI-intent routes.",
      "repair_or_route": "Science horizon check and excluded high-value family ledger route those families exactly.",
      "risk": "science horizon boxing",
      "status": "ROUTED_WITH_EXACT_NEXT_ROUTES"
    },
    {
      "finding": "Staying in source-control only would delay the accepted substrate's main purpose.",
      "repair_or_route": "Rank-1 opens quarantined no-API discovery-result screening while preserving G12 and G0 gates before validation.",
      "risk": "too conservative route selection",
      "status": "REPAIRED_BY_NEXT_EVIDENCE_CLASS"
    }
  ],
  "saturation_decision": "PASS_WITH_EXACT_NEXT_LANE_FOR_FULL_STREAM_DISCOVERY_AGGREGATION"
}
```
