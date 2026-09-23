# G12 NOFILL Forward Source Capture Adversarial Hash Policy Proof 2026-05-09

Route: `G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Status: `FAIL_BINARY_NON_TEXT_FALLBACK_WEAKENING`.

| Case | Target Verifier Decision | Safe Policy Decision | Conclusion |
|---|---|---|---|
| `STRICT_TEXT_EOL_PORTABILITY_ACCEPTED` | `ACCEPT_LF_NORMALIZED_FALLBACK_WARNING` | `ACCEPT_TEXT_LF_NORMALIZED_FALLBACK_WARNING` | matches safe policy |
| `STRICT_TEXT_TRUE_CONTENT_MUTATION_REJECTED` | `REJECT_HASH_RECOMPUTE_FAILURE` | `REJECT_HASH_RECOMPUTE_FAILURE` | matches safe policy |
| `STRICT_BINARY_NON_TEXT_RAW_SHA_REQUIRED` | `ACCEPT_LF_NORMALIZED_FALLBACK_WARNING` | `REJECT_HASH_RECOMPUTE_FAILURE` | diverges from safe policy |
| `MUTABLE_CONTEXT_NON_STRICT_DRIFT_ALLOWED` | `ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING` | `ACCEPT_MUTABLE_CONTEXT_RAW_DRIFT_WARNING` | matches safe policy |

Cleanup verified: `True`.

The repaired verifier passes the intended text portability and true-mutation cases, but the same LF-normalized branch also accepts a .bin strict artifact whose raw SHA changed. That is a remaining source-integrity repair blocker because LF fallback is not text-gated.
