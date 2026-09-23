from __future__ import annotations

import json

from scripts import analyze_q13_cpcv_bias_variance as mod


def test_decompose_path_variance_classifies_variance_dominated():
    rows = [
        {"path": 0, "auc_diff": 0.10},
        {"path": 1, "auc_diff": -0.08},
        {"path": 2, "auc_diff": 0.06},
        {"path": 3, "auc_diff": -0.04},
    ]

    out = mod.decompose_path_variance(rows)

    assert out["classification"] == "VARIANCE_DOMINATED_NO_SIGNAL_CLAIM"
    assert out["path_variance_share_of_second_moment"] > out["signal_share_of_second_moment"]
    assert out["weighted_ci_crosses_zero"] is True


def test_build_payload_reads_fixed_hp_paths(tmp_path):
    cpcv = tmp_path / "cpcv.json"
    cpcv.write_text(
        json.dumps(
            {
                "summary_fixed_hp_recommended": {
                    "diff_mean": 0.01,
                    "diff_std": 0.02,
                    "diff_se": 0.01,
                    "delong_p_combined_stouffer": 0.2,
                    "gate_a_pass": False,
                },
                "paths_fixed_hp": [
                    {"path": 0, "auc_v2": 0.55, "auc_v1": 0.45, "auc_diff": 0.10, "delong_p": 0.1, "n_test": 10},
                    {"path": 1, "auc_v2": 0.45, "auc_v1": 0.53, "auc_diff": -0.08, "delong_p": 0.2, "n_test": 10},
                    {"path": 2, "auc_v2": 0.52, "auc_v1": 0.46, "auc_diff": 0.06, "delong_p": 0.3, "n_test": 10},
                    {"path": 3, "auc_v2": 0.47, "auc_v1": 0.51, "auc_diff": -0.04, "delong_p": 0.4, "n_test": 10},
                ],
            }
        ),
        encoding="utf-8",
    )
    stat = tmp_path / "stat.md"
    stat.write_text("prior", encoding="utf-8")

    payload = mod.build_payload(cpcv_json=cpcv, stat_reeval_md=stat)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["task_id"] == "M-16"
    assert payload["decomposition"]["n_paths"] == 4
    assert payload["answer"]["variance_vs_signal"] == "VARIANCE_DOMINATED_NO_SIGNAL_CLAIM"

