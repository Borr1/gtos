# Adversarial Baseline Placebo Matrix

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "adversarial_baseline_placebo_matrix",
  "baseline_card_count": 5,
  "baseline_card_ids": [
    "ADV-001",
    "ADV-002",
    "ADV-003",
    "ADV-004",
    "ADV-005"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-12T05:31:11Z",
  "live_effect": false,
  "matrix_row_count": 40,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_placebo_families_present": [
    "session_only",
    "volatility_only",
    "duplicate_key_random_proxy",
    "side_flip_after_capture",
    "translated_poi_after_capture"
  ],
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "rows": [
    {
      "baseline_family": "session_only",
      "card_id": "GEO-001",
      "hidden_beta_or_artifact_it_can_detect": "POI bounds are unavailable or collapse into session-only buckets.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "same symbol/session/time bucket with shuffled POI-width bins",
      "requires_future_result_lane": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "baseline_family": "volatility_only",
      "card_id": "GEO-002",
      "hidden_beta_or_artifact_it_can_detect": "LTF availability is sparse or compression is only volatility state.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "volatility-only matched compression placebo",
      "requires_future_result_lane": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "baseline_family": "session_only",
      "card_id": "GEO-003",
      "hidden_beta_or_artifact_it_can_detect": "Void descriptor is not stable under duplicate-key grouping.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "random route-window permutation within same session",
      "requires_future_result_lane": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "GEO-004",
      "hidden_beta_or_artifact_it_can_detect": "Angle derives from post-decision bars unless source windows are frozen.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "entry-time matched straight-line placebo",
      "requires_future_result_lane": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "baseline_family": "session_only",
      "card_id": "GEO-005",
      "hidden_beta_or_artifact_it_can_detect": "Framework flags are not emitted as source truth.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "framework-label shuffle within source_symbol_session_partition",
      "requires_future_result_lane": true,
      "science_domain": "geometry_topology_path_shape"
    },
    {
      "baseline_family": "session_only",
      "card_id": "HAZ-001",
      "hidden_beta_or_artifact_it_can_detect": "Candidate IDs are too sparse by partition or dominated by one session clock.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "Poisson-like random spacing matched by symbol/session",
      "requires_future_result_lane": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "HAZ-002",
      "hidden_beta_or_artifact_it_can_detect": "Lifecycle source truth remains non-generatable historically.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "lifecycle time randomized within same candidate day",
      "requires_future_result_lane": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "HAZ-003",
      "hidden_beta_or_artifact_it_can_detect": "Ambiguity cannot be known without post-decision path unless route freezes only predecision availability.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "same timeframe availability placebo",
      "requires_future_result_lane": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "baseline_family": "volatility_only",
      "card_id": "HAZ-004",
      "hidden_beta_or_artifact_it_can_detect": "Tail measure becomes a renamed volatility bucket.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "volatility-only placebo with identical range bucket",
      "requires_future_result_lane": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "HAZ-005",
      "hidden_beta_or_artifact_it_can_detect": "Transition clock is indistinguishable from session-only frequency.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "day-of-week and hour-only placebo",
      "requires_future_result_lane": true,
      "science_domain": "stochastic_tail_hazard_first_passage"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "MIC-001",
      "hidden_beta_or_artifact_it_can_detect": "Proxy mapping is unavailable or not source-hash stable.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "proxy-instrument random date alignment placebo",
      "requires_future_result_lane": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "MIC-002",
      "hidden_beta_or_artifact_it_can_detect": "Feature requires post-event depth or raw blob not committed.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "volume-only placebo",
      "requires_future_result_lane": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "MIC-003",
      "hidden_beta_or_artifact_it_can_detect": "POI and proxy timestamps fail as-of alignment.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "same POI with shuffled proxy timestamp",
      "requires_future_result_lane": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "MIC-004",
      "hidden_beta_or_artifact_it_can_detect": "Proxy basis is not stable enough to be source-control eligible.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "symbol-only proxy placebo",
      "requires_future_result_lane": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "baseline_family": "session_only",
      "card_id": "MIC-005",
      "hidden_beta_or_artifact_it_can_detect": "Liquidity vacuum is just session clock or missing-data pattern.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "session liquidity placebo",
      "requires_future_result_lane": true,
      "science_domain": "microstructure_orderflow_liquidity_trapped_flow"
    },
    {
      "baseline_family": "session_only",
      "card_id": "BEH-001",
      "hidden_beta_or_artifact_it_can_detect": "Question never escapes session-only frequency.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "session-only null is the primary hypothesis competitor",
      "requires_future_result_lane": true,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "baseline_family": "session_only",
      "card_id": "BEH-002",
      "hidden_beta_or_artifact_it_can_detect": "Lifecycle gap prevents determining whether the level remained actionable.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "same symbol with random session handoff flag",
      "requires_future_result_lane": true,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "BEH-003",
      "hidden_beta_or_artifact_it_can_detect": "Price reference is unavailable or overfits instrument tick scale.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "random offset placebo around same price scale",
      "requires_future_result_lane": true,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "BEH-004",
      "hidden_beta_or_artifact_it_can_detect": "Calendar source as-of convention is missing.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "calendar-window placebo shifted by one non-event day",
      "requires_future_result_lane": true,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "baseline_family": "session_only",
      "card_id": "BEH-005",
      "hidden_beta_or_artifact_it_can_detect": "Repeated-level identity cannot be reconstructed without POI source hashes.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "duplicate-key shuffle preserving symbol/session",
      "requires_future_result_lane": true,
      "science_domain": "behavioral_game_theory_session_participant_constraints"
    },
    {
      "baseline_family": "session_only",
      "card_id": "MAC-001",
      "hidden_beta_or_artifact_it_can_detect": "Calendar bucket is too coarse or sample concentration is high.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "same symbol/session random calendar reassignment",
      "requires_future_result_lane": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "MAC-002",
      "hidden_beta_or_artifact_it_can_detect": "Publication-time convention is not source-hash proven.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "macro timestamp placebo shifted outside publication as-of",
      "requires_future_result_lane": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "MAC-003",
      "hidden_beta_or_artifact_it_can_detect": "Cross-asset source timestamps are not aligned as-of.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "single-asset trend placebo",
      "requires_future_result_lane": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "MAC-004",
      "hidden_beta_or_artifact_it_can_detect": "Fix proximity is indistinguishable from session clock.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "time-of-day-only placebo excluding fix labels",
      "requires_future_result_lane": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "baseline_family": "volatility_only",
      "card_id": "MAC-005",
      "hidden_beta_or_artifact_it_can_detect": "Event source contract is absent or future-revised.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "volatility-only placebo without event label",
      "requires_future_result_lane": true,
      "science_domain": "macro_session_calendar_cross_asset_context"
    },
    {
      "baseline_family": "session_only",
      "card_id": "EXE-001",
      "hidden_beta_or_artifact_it_can_detect": "Spread data is unavailable or broker-specific forbidden evidence is required.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "session-liquidity placebo",
      "requires_future_result_lane": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "baseline_family": "session_only",
      "card_id": "EXE-002",
      "hidden_beta_or_artifact_it_can_detect": "Lifecycle logger lacks nonbroker fill/cancel/expiry source events.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "candidate timestamp shuffled within same session",
      "requires_future_result_lane": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "EXE-003",
      "hidden_beta_or_artifact_it_can_detect": "Quote gaps require raw market blobs not admitted by this route.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "range-only placebo",
      "requires_future_result_lane": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "baseline_family": "session_only",
      "card_id": "EXE-004",
      "hidden_beta_or_artifact_it_can_detect": "Orderability is accidentally inferred from broker outcome.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "session-only orderability placebo",
      "requires_future_result_lane": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "EXE-005",
      "hidden_beta_or_artifact_it_can_detect": "Proxy validity cannot be separated from missingness.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "random eligible-candidate placebo with same source coverage",
      "requires_future_result_lane": true,
      "science_domain": "execution_science_spread_slippage_fillability"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "UNC-001",
      "hidden_beta_or_artifact_it_can_detect": "Availability itself is a hidden session/source proxy.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "missingness-only placebo",
      "requires_future_result_lane": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "UNC-002",
      "hidden_beta_or_artifact_it_can_detect": "Framework flags are not captured as source truth.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "framework flag permutation placebo",
      "requires_future_result_lane": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "UNC-003",
      "hidden_beta_or_artifact_it_can_detect": "Future lane mixes lifecycle labels with result labels.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "label-family swap placebo in audit only",
      "requires_future_result_lane": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "UNC-004",
      "hidden_beta_or_artifact_it_can_detect": "Completeness is constant across all rows or merely route-level.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "random source-completeness placebo",
      "requires_future_result_lane": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "UNC-005",
      "hidden_beta_or_artifact_it_can_detect": "Representation list becomes too broad to audit or leaks post-decision fields.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "representation-name shuffle placebo",
      "requires_future_result_lane": true,
      "science_domain": "ml_meta_labeling_model_disagreement_uncertainty_controls"
    },
    {
      "baseline_family": "session_only",
      "card_id": "ADV-001",
      "hidden_beta_or_artifact_it_can_detect": "Placebo absorbs the entire question, proving mechanism under-specified.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "session-only is the placebo itself",
      "requires_future_result_lane": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "baseline_family": "volatility_only",
      "card_id": "ADV-002",
      "hidden_beta_or_artifact_it_can_detect": "Volatility source cannot be attached as-of or dominates every mechanism.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "volatility-only null",
      "requires_future_result_lane": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "baseline_family": "random_or_shuffle",
      "card_id": "ADV-003",
      "hidden_beta_or_artifact_it_can_detect": "Duplicate policy is later changed or row-level counts leak into denominators.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "duplicate-key random proxy assignment",
      "requires_future_result_lane": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "ADV-004",
      "hidden_beta_or_artifact_it_can_detect": "Side source remains unavailable or flip violates instrument convention.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "side-flip placebo",
      "requires_future_result_lane": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    },
    {
      "baseline_family": "mechanism_specific_placebo",
      "card_id": "ADV-005",
      "hidden_beta_or_artifact_it_can_detect": "Translated POI is invalid for tick/scale or uses future path.",
      "no_current_scoring": true,
      "primary_adversarial_baseline_or_placebo": "translated-POI placebo",
      "requires_future_result_lane": true,
      "science_domain": "adversarial_baselines_placebo_explanations"
    }
  ],
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "validation_safe": false
}
```
