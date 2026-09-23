# G12 NOFILL Forward Source Capture Text-Gate Adversarial Hash Policy Proof 2026-05-10

Route: `G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Status: `PASS`.

| Case | Target Verifier Decision | Text Gate | Synthetic LF Match | Conclusion |
|---|---|---|---|---|
| `STRICT_TEXT_EOL_PORTABILITY_ACCEPTED_ONLY_BY_TEXT_FALLBACK` | `ACCEPT_TEXT_LF_NORMALIZED_FALLBACK_WARNING` | `True` | `True` | `accepted=True` |
| `STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED` | `REJECT_HASH_RECOMPUTE_FAILURE` | `True` | `False` | `accepted=False` |
| `STRICT_BINARY_NON_TEXT_RAW_SHA_DRIFT_REJECTED_EVEN_WITH_SYNTHETIC_LF_MATCH` | `REJECT_HASH_RECOMPUTE_FAILURE` | `False` | `True` | `accepted=False` |
| `MUTABLE_CONTEXT_NON_STRICT_DRIFT_WARNING_ONLY` | `ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING` | `True` | `False` | `accepted=True` |

Cleanup verified: `True`.

The text gate closes the narrowed blocker: strict text EOL portability still passes only through bounded LF-normalized text fallback; true text mutation fails; strict .bin/non-text raw SHA drift fails even when the synthetic LF-normalized digest matches; mutable-context drift remains warning-only and does not mask strict-source failure.
