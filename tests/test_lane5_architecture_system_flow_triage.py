from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane5_architecture_system_flow_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _seed_artifacts(root: Path) -> None:
    _write_json(
        root
        / "research"
        / "ml_program"
        / "phase_2"
        / "position_mgmt"
        / "h_pm01_per_cohort_results.json",
        {
            "metadata": {"cohort_size": 2338},
            "primary_full_cohort": {
                "backtest": {
                    "delta": {
                        "mean_r": -0.004960547358764833,
                        "sharpe_pct": -2.5761764707408985,
                    }
                },
                "dsr_paired_delta": {"dsr_p": 0.9999646857030353},
                "gate": {"overall_pass": False},
            },
            "per_cohort": {
                "per_instrument": {
                    "NAS100": {
                        "backtest": {
                            "n_trades": 252,
                            "delta": {
                                "mean_r": 0.09066365782920549,
                                "sharpe_pct": 9.65503862508914,
                            },
                        },
                        "dsr_paired": {"dsr_p": 0.015223281554341606},
                    }
                }
            },
        },
    )
    v3 = root / "research" / "ml_program" / "models" / "k54_v3"
    v3.mkdir(parents=True, exist_ok=True)
    (v3 / "k54_v3_meta_label.lgb").write_bytes(b"fake")
    _write_json(
        v3 / "conformal_calibration.json",
        {
            "coverage_observed": 0.8810606060606061,
            "target_coverage": 0.9,
            "christoffersen_p": 0.0015804301852155866,
            "gate_g_status": "DEFERRED",
        },
    )
    v4 = root / "research" / "ml_program" / "models" / "k54_v4"
    _write_json(
        v4 / "component_ablation.json",
        {
            "gate_h_pass": False,
            "t7_nas_routing_add_over_master_nas_fallthrough": {
                "per_path_mean": -0.0052050670338545674,
                "boot_p_one_sided": 0.5874,
            },
        },
    )
    _write_json(
        v4 / "final_verdicts.json",
        {
            "verdicts": {
                "PRIMARY_Hybrid_5": {"verdict": "FAIL"},
                "FALLBACK_1_Master": {"verdict": "FAIL"},
            },
            "ship_arch": None,
        },
    )


def test_architecture_system_flow_triage_classifies_p_items(tmp_path):
    _seed_artifacts(tmp_path)

    payload = mod.build_payload(tmp_path)
    by_id = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["P-1"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["P-2"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["P-3"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["P-5"]["status"] == "REJECTED_FAILED"
    assert by_id["P-6"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert "NAS100-only subcandidate" in by_id["P-1"]["candidate_strength_vs_j46_j49"]


def test_evidence_extracts_vol_and_routing_numbers(tmp_path):
    _seed_artifacts(tmp_path)

    evidence = mod.load_evidence(tmp_path)

    assert evidence["vol_conditioning"]["full_cohort_gate_pass"] is False
    assert evidence["vol_conditioning"]["nas100_delta_mean_r"] == 0.09066365782920549
    assert evidence["meta_labeling"]["component_ran"] is True
    assert evidence["routing"]["all_v4_architectures_failed"] is True
    assert evidence["routing"]["t7_nas_routing_delta"] == -0.0052050670338545674
