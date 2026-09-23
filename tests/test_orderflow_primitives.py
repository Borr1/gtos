from __future__ import annotations

import json

from scripts import audit_orderflow_primitives as script
from src.research_infra import orderflow_primitives as mod


def _feature_payload(fields: dict) -> dict:
    return {
        "schema_version": "fixture_features_v1",
        "feature_rows": [
            {
                "data_status": "ok",
                "event_class": "candidate",
                "event_id": "evt1",
                **fields,
            }
        ],
        "synthesis": {"data_status_counts": {"ok": 1}},
    }


def _forensics_payload() -> dict:
    return {
        "feeds": {
            "MBP10_TOP10": {
                "coverage": {"candidate_rows": 12, "context_rows": 61},
                "label_coverage": {"actual_r_n": 1, "synthetic_label_n": 11},
                "concentration": {"candidate_by_date": {"top_share": 0.75}},
                "stability": {
                    "event15_total_depth": {"leave_one_date": {"sign_flip_count": 1}},
                    "event15_thin_rate": {"leave_one_date": {"sign_flip_count": 2}},
                    "event15_imbalance": {"leave_one_date": {"sign_flip_count": 1}},
                },
            }
        }
    }


def test_registry_contains_required_orderflow_families_and_separate_roles():
    registry = mod.primitive_registry()
    families = mod.required_families_present(registry)
    matrix = mod.role_matrix(registry)

    assert all(families.values())
    assert "X1_FOOTPRINT_DELTA_ABSORPTION_V1" in matrix["entry_timing"]
    assert "X2_DEPTH_THINNESS_WALL_CONCENTRATION_V1" in matrix["bad_condition_veto"]
    assert "VP_VOLUME_PROFILE_CONTEXT_V1" in matrix["target_rr_expansion"]
    assert all(matrix.values())


def test_no_lookahead_rejects_post_event_decision_fields():
    registry = mod.primitive_registry()
    clean = mod.no_lookahead_check(registry)
    bad_registry = [dict(registry[0], decision_feature_fields=["post15_signed_volume"])]
    bad = mod.no_lookahead_check(bad_registry)

    assert clean["status"] == "PASS"
    assert bad["status"] == "FAIL"
    assert bad["bad_fields"]["X1_FOOTPRINT_DELTA_ABSORPTION_V1"] == ["post15_signed_volume"]


def test_build_report_payload_preserves_no_promotion_and_uses_cached_fields(tmp_path):
    trades = _feature_payload(
        {
            "pre60_signed_volume": 1.0,
            "pre60_buy_fraction": 0.5,
            "pre60_absorption_volume_per_tick": 10.0,
            "pre60_delta_price_divergence": False,
            "event15_signed_volume": 2.0,
            "event15_buy_fraction": 0.6,
            "event15_absorption_volume_per_tick": 20.0,
            "event15_delta_price_divergence": True,
            "profile_poc_price": 100.0,
            "profile_event_price_volume_percentile": 0.7,
            "profile_nearest_hvn_distance_ticks": 1.0,
            "profile_nearest_lvn_distance_ticks": 2.0,
            "profile_levels": 20,
        }
    )
    mbp10 = _feature_payload(
        {
            "pre60_median_total_depth10": 100,
            "pre60_median_depth10_imbalance": 0.1,
            "event15_median_total_depth10": 90,
            "event15_thin_depth10_rate": 0.2,
            "event15_median_depth10_imbalance": 0.0,
            "event15_median_near_far_ratio": 0.3,
            "event15_median_max_bid_wall": 5,
            "event15_median_max_ask_wall": 6,
        }
    )
    mbo = _feature_payload(
        {
            "pre60_near10_pull_pressure": 0.51,
            "pre60_near10_net_liquidity": -10,
            "pre60_action_count": 1000,
            "event15_action_count": 200,
            "mbo_book_clear_count": 1,
            "event15_near10_add_size": 30,
            "event15_near10_remove_size": 40,
            "event15_near10_pull_pressure": 0.52,
            "event15_near10_net_liquidity": -20,
            "event15_near10_add_bid_size": 10,
            "event15_near10_add_ask_size": 20,
            "event15_near10_remove_bid_size": 11,
            "event15_near10_remove_ask_size": 21,
        }
    )
    lto011 = {"status": "WAITING_FOR_DATABENTO_LIVE_LICENSE", "status_row": {"databento_live_status": {"license_blocker": True}}}
    lto012 = {"status": "OK_WITH_GUARDED_DEPTH_QUEUE", "status_row": {"current_counts": {"latest_candidate_rows": 1}}}
    lto030 = {
        "status": "OK_WITH_6B_POLICY_AND_SI_BLOCKER",
        "completion_evidence": {
            "common_second_alignment_policy_registered_for_6b": True,
            "si_depth_definition_remains_blocked": True,
        },
    }
    paths = {}
    for name, payload in {
        "trades": trades,
        "mbp10": mbp10,
        "mbo": mbo,
        "forensics": _forensics_payload(),
        "lto010": {"status": "OK"},
        "lto011": lto011,
        "lto012": lto012,
        "lto030": lto030,
    }.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = path

    payload = mod.build_report_payload(
        root=tmp_path,
        generated_at_utc="2026-05-05T00:00:00+00:00",
        cached_trades_path=paths["trades"].relative_to(tmp_path),
        cached_mbp10_path=paths["mbp10"].relative_to(tmp_path),
        cached_mbo_path=paths["mbo"].relative_to(tmp_path),
        nas100_forensics_path=paths["forensics"].relative_to(tmp_path),
        lto010_path=paths["lto010"].relative_to(tmp_path),
        lto011_path=paths["lto011"].relative_to(tmp_path),
        lto012_path=paths["lto012"].relative_to(tmp_path),
        lto030_path=paths["lto030"].relative_to(tmp_path),
    )

    assert payload["status"] == "OK_PRIMITIVES_REGISTERED_WITH_SOURCE_BLOCKERS"
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["completion_evidence"]["new_paid_data_calls"] == 0
    assert payload["completion_evidence"]["no_lookahead_pass"] is True
    assert payload["completion_evidence"]["roles_are_separate"] is True
    assert payload["status_row"]["source_readiness"]["databento_live"]["license_blocker"] is True
    vp = payload["status_row"]["field_coverage"]["VP_VOLUME_PROFILE_CONTEXT_V1"]
    assert "profile_vah_price" in vp["missing_decision_fields"]
    assert payload["status_row"]["cached_feature_stability"]["feeds"]["MBP10_TOP10"]["actual_r_rows"] == 1


def test_append_status_row_is_idempotent(tmp_path):
    row = {"row_key": "same", "schema_version": "orderflow_primitives_status_v1"}
    path = tmp_path / "status.jsonl"

    assert script.append_status_row_if_missing(row, path) == 1
    assert script.append_status_row_if_missing(row, path) == 0
    assert path.read_text(encoding="utf-8").count("\n") == 1
