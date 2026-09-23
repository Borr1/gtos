from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane5_k54_architecture_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _seed_k54_artifacts(root: Path) -> None:
    v3 = root / "research" / "ml_program" / "models" / "k54_v3"
    v4 = root / "research" / "ml_program" / "models" / "k54_v4"
    _write_json(
        v3 / "dsr_per_gate.json",
        {
            "gate_b_primary_lift": {
                "lift_observed": 0.04835986000202819,
                "sr_paired": 1.2748258512453603,
                "dsr_p": 0.32095808514499824,
                "pbo": 0.2,
                "null_p_emp": 0.0,
                "verdict": "FAIL",
            }
        },
    )
    _write_json(
        v3 / "diagnostic_w_unit_ablation.json",
        {
            "variants": [
                {
                    "label": "K54 v3 features + W-unit ON (current spec)",
                    "best_hp_oos_mean_auc": 0.5099822065485595,
                },
                {
                    "label": "K54 v3 features + W-unit OFF",
                    "best_hp_oos_mean_auc": 0.5639553708274125,
                },
                {
                    "label": "Arch A reproduction (no kw__ + W-unit OFF)",
                    "best_hp_oos_mean_auc": 0.5604983423919125,
                },
            ],
            "feature_cols_count": {"v3": 1240, "arch_a": 1234},
        },
    )
    _write_json(
        v3 / "feature_stability.json",
        {
            "n_paths": 15,
            "mean_pairwise_jaccard_top50": 0.1685447455309013,
            "n_features_in_>=80%_paths": 2,
            "gate_threshold": "n_stable >= 30 AND mean_jaccard >= 0.6",
            "gate_pass": False,
        },
    )
    _write_json(
        v3 / "conformal_calibration.json",
        {
            "coverage_observed": 0.8810606060606061,
            "target_coverage": 0.9,
            "christoffersen_p": 0.0015804301852155866,
            "gate_g_status": "DEFERRED",
        },
    )
    _write_json(
        v3 / "specialist_results.json",
        {
            "n_nas_us30": 113,
            "specialist_auc": 0.6014106583072101,
            "global_v3_on_nas": 0.49843260188087773,
            "delta": 0.10297805642633234,
            "gate_pass": True,
        },
    )
    _write_json(
        v4 / "final_verdicts.json",
        {
            "verdicts": {
                "PRIMARY_Hybrid_5": {"n_passed": 3, "n_testable_gates": 7, "verdict": "FAIL"},
                "FALLBACK_1_Master": {"n_passed": 3, "n_testable_gates": 7, "verdict": "FAIL"},
                "FALLBACK_2_Hybrid_4": {"n_passed": 3, "n_testable_gates": 7, "verdict": "FAIL"},
            },
            "ship_arch": None,
            "closest_to_pass": {"arch": "PRIMARY_Hybrid_5", "n_passed": 3},
        },
    )
    _write_json(
        v4 / "component_ablation.json",
        {
            "master_bundle_add_over_arch_a": {
                "per_path_mean": 0.01644587748200793,
                "gate_h_a_pass": False,
            },
            "t7_nas_routing_add_over_master_nas_fallthrough": {
                "per_path_mean": -0.0052050670338545674,
                "gate_h_b_pass": False,
            },
            "gate_h_pass": False,
        },
    )
    _write_json(
        v4 / "feature_stability.json",
        {"master": {"mean_jaccard": 0.1648606871577491, "n_stable_features": 3, "gate_f_pass": False}},
    )


def test_k54_triage_classifies_architecture_items_from_artifacts(tmp_path):
    _seed_k54_artifacts(tmp_path)

    payload = mod.build_payload(tmp_path)
    by_id = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["K-5"]["status"] == "REJECTED_FAILED"
    assert by_id["K-6"]["status"] == "REJECTED_FAILED"
    assert by_id["K-7"]["status"] == "REJECTED_FAILED"
    assert by_id["K-10"]["status"] == "REJECTED_FAILED"
    assert by_id["K-11"]["status"] == "DONE"
    assert by_id["K-12"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["K-13"]["status"] == "DONE"
    assert by_id["K-14"]["status"] == "DONE"
    assert by_id["K-15"]["status"] == "DONE"
    assert by_id["K-18"]["status"] == "REJECTED_FAILED"
    assert by_id["K-18"]["candidate_strength_vs_j46_j49"].startswith("NAS_US30 specialist")


def test_w_unit_ablation_and_v4_verdict_summary_are_extracted(tmp_path):
    _seed_k54_artifacts(tmp_path)

    evidence = mod.load_evidence(tmp_path)

    assert evidence["k54_v3"]["w_unit_ablation"]["w_unit_on_auc"] == 0.5099822065485595
    assert evidence["k54_v3"]["w_unit_ablation"]["w_unit_off_auc"] == 0.5639553708274125
    assert evidence["k54_v3"]["w_unit_ablation"]["v3_features_minus_arch_a_auc"] > 0.003
    assert evidence["k54_v4"]["verdict_summary"]["all_architectures_failed"] is True
    assert evidence["k54_v4"]["verdict_summary"]["ship_arch"] is None
