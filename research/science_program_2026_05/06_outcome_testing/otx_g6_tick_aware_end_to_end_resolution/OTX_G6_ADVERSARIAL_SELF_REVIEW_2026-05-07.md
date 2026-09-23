# OTX G6 Adversarial Self Review

- Generated at UTC: `2026-05-07T07:50:26Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTX_G6_ADVERSARIAL_SELF_REVIEW",
  "findings": [
    {
      "finding": "A broad manual rg during exploration emitted post-decision resolution-log lines.",
      "mitigation": "The builder forbids those source fragments and uses only frozen packet/control artifacts plus external tick parquet. The emitted lines are not referenced in any source hash, proposal, audit, or result computation.",
      "severity": "HIGH"
    },
    {
      "finding": "OTG0-PKT-060 cannot be cleared from quote ticks alone.",
      "mitigation": "It remains blocked with an exact mechanical_ob_bounds_asof_v1 capture contract requirement.",
      "severity": "HIGH"
    },
    {
      "finding": "OTG0-PKT-061 ordered path proposal uses a fixed 4h horizon because the original packet lacked path_start/path_end.",
      "mitigation": "Marked external G12 reaudit only; no result lane opened.",
      "severity": "MEDIUM"
    },
    {
      "finding": "OTI4b results are same-dataset tick-derived discovery and below the preregistered sample floor.",
      "mitigation": "Report marks DSR/PBO/effective-N not computable and keeps validation_safe=false.",
      "severity": "MEDIUM"
    },
    {
      "finding": "Tick-derived M1 range and sweep parsers are deterministic but newly frozen in this OTX lane.",
      "mitigation": "Outputs are proposals or quarantined discovery only until external G12 review.",
      "severity": "LOW"
    }
  ],
  "generated_at_utc": "2026-05-07T07:50:26Z",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
