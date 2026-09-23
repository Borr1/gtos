# Evidence-Chain Graph

- **selected_next_lane_class:** `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`

```json
{
  "artifact_family": "evidence_chain_graph_selected_downstream_route",
  "graph": [
    {
      "evidence_class": "SOURCE_UNIVERSE_CONTROL",
      "node": "source_universe",
      "status": "accepted_predecessor"
    },
    {
      "evidence_class": "NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY",
      "node": "no_api_mechanical_replay_substrate",
      "status": "accepted_by_g12"
    },
    {
      "evidence_class": "G0_SYNTHESIS_CONTROL_ONLY",
      "node": "g0_route_selection",
      "status": "this_route"
    },
    {
      "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
      "node": "family_path_behavior_discovery_result_screen",
      "status": "rank_1_next_route"
    },
    {
      "evidence_class": "G12_DISCOVERY_RESULT_AUDIT_ONLY",
      "node": "g12_post_discovery_result_audit",
      "status": "mandatory_after_rank_1"
    },
    {
      "evidence_class": "G0_SYNTHESIS_OR_VALIDATION_PREP_ONLY",
      "node": "future_g0_result_synthesis_or_validation_prep",
      "status": "blocked_until_post_result_g12_acceptance"
    }
  ],
  "mandatory_follow_on_audit": "G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT",
  "selected_next_lane_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "validation_gate": "No validation-prep or promotion lane may consume discovery results until the mandatory G12 audit accepts them."
}
```
