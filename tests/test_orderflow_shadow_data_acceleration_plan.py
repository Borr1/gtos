from __future__ import annotations

import json
from pathlib import Path

from scripts import build_orderflow_shadow_data_acceleration_plan as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_plan_uses_lto_reports_and_preserves_license_boundary(tmp_path):
    _write_json(
        tmp_path / mod.DEFAULT_LTO011,
        {
            "status": "WAITING_FOR_DATABENTO_LIVE_LICENSE",
            "status_row": {
                "databento_live_status": {"license_blocker": True},
                "current_counts": {
                    "broker_actual_r_rows_nas100_unique": 1,
                    "cached_mbp10_candidate_rows": 12,
                    "live_mbp10_candidate_rows": 0,
                    "declared_nas100_nq_requests": 5,
                },
            },
        },
    )
    _write_json(
        tmp_path / mod.DEFAULT_LTO012,
        {
            "status": "OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE",
            "status_row": {
                "current_counts": {
                    "latest_candidate_rows": 48,
                    "features_extracted": 23,
                    "background_queue_candidates": 22,
                }
            },
        },
    )
    _write_json(
        tmp_path / mod.DEFAULT_LTO013,
        {
            "status": "OK_WITH_BLOCKED_PROXY_ROWS",
            "current_counts": {"usable_depth_context_rows": 14, "blocked_or_no_proxy_rows": 33},
        },
    )

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert payload["status"] == "SIERRA_ACTIVE_DATABENTO_HISTORICAL_REPLAY_DATABENTO_LIVE_LICENSE_BLOCKED"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["current_state"]["sierra"]["candidate_rows"] == 48
    assert payload["current_state"]["databento"]["live_license_blocker"] is True
    assert payload["paid_data_calls"] == 0
    assert any(row["lane_id"] == "DATABENTO_HISTORICAL_COUNTERFACTUAL_REPLAY" for row in payload["execution_lanes"])


def test_plan_encodes_footprint_and_volume_profile_as_shadow_feature_families(tmp_path):
    _write_json(tmp_path / mod.DEFAULT_LTO011, {"status": "WAITING_FOR_DATABENTO_LIVE_LICENSE"})
    _write_json(tmp_path / mod.DEFAULT_LTO012, {"status": "OK_FEATURES_OR_BLOCKERS_COMPLETE"})
    _write_json(tmp_path / mod.DEFAULT_LTO013, {"status": "OK_REGISTRY_BACKFILLED"})

    payload = mod.build_payload(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")
    families = {row["family"]: row for row in payload["ict_to_orderflow_translation"]["feature_families"]}

    assert "footprint_delta_absorption" in families
    assert "volume_profile_context" in families
    assert families["footprint_delta_absorption"]["decision_role_to_test"] == "entry_timing_or_veto_shadow_only"
    assert families["volume_profile_context"]["decision_role_to_test"] == "target_selection_and_rr_expansion_shadow_only"
    rendered = mod.render_markdown(payload)
    assert "SIERRA_FOOTPRINT_AND_VOLUME_PROFILE_DESIGN" in rendered
    assert "POC proximity" in json.dumps(payload)
