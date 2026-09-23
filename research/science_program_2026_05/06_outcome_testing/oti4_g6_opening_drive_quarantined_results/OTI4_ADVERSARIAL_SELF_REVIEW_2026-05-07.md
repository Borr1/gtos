# OTI4 G6 Opening-Drive Adversarial Self-Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

```json
{
  "artifact_family": "OTI4_G6_OPENING_DRIVE_ADVERSARIAL_SELF_REVIEW",
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "residual_unresolved_risk": "If the owner approves a separate OTI4b method freeze that treats path-order labels as the outcome source, it must rebuild source hashes, same-bar policy, and no-leak constraints explicitly before scoring.",
  "resolution": "Do not do that in OTI4. The prereg requires source-complete session/opening-range breakout fields and the objective forbids hidden path labels. All accepted rows are NO_BREAKOUT_ASOF with stale OHLC coverage, so a path-label-only result would answer a different, leaky question.",
  "strongest_reason_result_could_be_wrong": "G12 accepted OTG0-PKT-062 for future quarantined outcome audit, so a less strict auditor might read the referenced candidate_ltf_path_order source and produce path labels despite missing opening-drive range fields.",
  "validation_safe": false
}
```
