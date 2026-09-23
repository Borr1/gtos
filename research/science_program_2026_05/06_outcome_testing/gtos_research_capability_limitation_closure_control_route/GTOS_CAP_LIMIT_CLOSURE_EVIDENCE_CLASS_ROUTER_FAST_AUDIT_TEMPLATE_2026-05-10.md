# GTOS Evidence-Class Router And Fast-Audit Template

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "anti_lazy_blocker_rule": "A same-evidence-class blocker is not complete until searched, cleared, proven non-generatable, or reduced to an exact owner/access/source/capture requirement.",
  "artifact_family": "evidence_class_router_and_fast_audit_template",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_classes": [
    {
      "class": "source_control",
      "continue_inside_same_goal_when": [
        "missing source root can still be searched",
        "source hash can be recomputed",
        "contamination or embargo can be audited",
        "parser hash drift can be repaired without changing rows"
      ],
      "split_required_when": [
        "accepted packet would open result scoring",
        "G12 acceptance is required for a self-built packet",
        "live behavior, paid source, registry edit, or broker account/order evidence is needed"
      ]
    },
    {
      "class": "result_scoring",
      "continue_inside_same_goal_when": [
        "lane explicitly authorizes quarantined outcomes and labels are frozen"
      ],
      "split_required_when": [
        "source proof is incomplete or promotion wording would be introduced"
      ]
    },
    {
      "class": "promotion_or_live_behavior",
      "continue_inside_same_goal_when": [],
      "split_required_when": [
        "always requires separate owner-approved dossier and live-surface review"
      ]
    }
  ],
  "fast_narrow_audit_template": {
    "inputs": [
      "source packet manifest",
      "source hash manifest",
      "parser hash manifest",
      "purge/embargo ledger",
      "duplicate denominator ledger"
    ],
    "outputs": [
      "decision ledger",
      "repair/source requirement ledger",
      "future route eligibility ledger",
      "completion audit"
    ],
    "required_checks": [
      "parse artifacts",
      "recompute hashes",
      "confirm row counts",
      "confirm safe flags",
      "confirm forbidden fields absent or redacted",
      "confirm denominator exclusions",
      "write exact blocker ledger"
    ],
    "template_id": "FAST_G12_SOURCE_CONTROL_AUDIT"
  },
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "handoff_artifact_requirements": [
    "context anchor with HEAD and prompt path",
    "machine-readable output manifest",
    "source hash manifest",
    "decision ledger",
    "exact blocker or repair ledger",
    "safe flag ledger",
    "verifier result",
    "focused test result command transcript or pytest output path"
  ],
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "speed_without_label_collapse_rule": "Use narrow audits for source facts, but split before labels, result scoring, validation, promotion, or live behavior.",
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
