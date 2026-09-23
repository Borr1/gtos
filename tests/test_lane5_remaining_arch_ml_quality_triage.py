from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane5_remaining_arch_ml_quality_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _seed_root(root: Path) -> None:
    _write_json(
        root / "research" / "ml_program" / "models" / "k54_v3" / "dsr_per_gate.json",
        {
            "gate_b_primary_lift": {
                "lift_observed": 0.04835986000202819,
                "dsr_p": 0.32095808514499824,
                "pbo": 0.2,
                "verdict": "FAIL",
            }
        },
    )
    _write_json(
        root / "research" / "ml_program" / "models" / "k54_v3" / "specialist_results.json",
        {
            "n_nas_us30": 113,
            "specialist_auc": 0.6014106583072101,
            "delta": 0.10297805642633234,
            "gate_pass": True,
        },
    )
    _write_json(
        root / "research" / "ml_program" / "models" / "k54_v4" / "final_verdicts.json",
        {
            "verdicts": {
                "PRIMARY_Hybrid_5": {"verdict": "FAIL"},
                "FALLBACK_1_Master": {"verdict": "FAIL"},
            },
            "ship_arch": None,
        },
    )
    _write_json(
        root / "research" / "ml_program" / "models" / "k54_v4" / "component_ablation.json",
        {
            "t7_nas_routing_add_over_master_nas_fallthrough": {
                "per_path_mean": -0.0052050670338545674,
                "boot_p_one_sided": 0.5874,
            }
        },
    )
    _write_json(
        root / "research" / "ml_program" / "audit" / "LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json",
        {
            "inventories": {
                "ticks": {
                    "max_symbol_days": 5,
                    "symbols_with_ticks": 7,
                    "tick_capture_daemon_exists": True,
                    "tick_features_helper_exists": True,
                }
            }
        },
    )
    _write_json(
        root
        / "research"
        / "ml_program"
        / "audit"
        / "D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json",
        {"inventories": {"old_label_gaps": {"GBPJPY": "missing", "US30_cash": "missing"}}},
    )
    (root / "research" / "ml_program" / "literature" / "synthesis").mkdir(parents=True, exist_ok=True)
    (root / "research" / "ml_program" / "literature" / "synthesis" / "group_a_foundations.md").write_text(
        "\n".join(
            [
                "H-Sticky-HDP-HMM-Regime-Classifier Kirby null-test",
                "H-Trade-Count-Time-Triggers",
                "H-Signature-Feature-K54-v2",
                "H-Fractional-Differentiation-Features",
                "H-HAR-RV-Cascade-K54-Features",
                "H-Hawkes-Dynamic-Correlation-Threshold",
            ]
        ),
        encoding="utf-8",
    )
    (root / "research" / "ml_program" / "literature" / "synthesis" / "group_b_microstructure.md").write_text(
        "", encoding="utf-8"
    )
    ticket = root / "research" / "operations" / "k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md"
    ticket.parent.mkdir(parents=True, exist_ok=True)
    ticket.write_text("TARGET MODEL UPGRADE PENDING\norchestrator.py\nk55_shadow:\n", encoding="utf-8")


def test_remaining_arch_ml_quality_triage_classifies_open_cluster(tmp_path):
    _seed_root(tmp_path)

    payload = mod.build_payload(tmp_path)
    by_id = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    for item_id in ("K-16", "K-17", "P-7", "P-8", "P-9", "P-10", "S-2", "S-3", "S-4", "S-5"):
        assert by_id[item_id]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["S-1"]["status"] == "FILED_FOR_APPROVAL"
    assert payload["status_counts"] == {"DEFERRED_WITH_TRIGGER": 10, "FILED_FOR_APPROVAL": 1}


def test_remaining_arch_ml_quality_evidence_extracts_blockers(tmp_path):
    _seed_root(tmp_path)

    evidence = mod.build_evidence(tmp_path)

    assert evidence["k54"]["v4_all_architectures_failed"] is True
    assert evidence["k54"]["v4_t7_nas_routing_delta"] == -0.0052050670338545674
    assert evidence["data_source"]["tick_max_symbol_days"] == 5
    assert evidence["k55_ticket"]["ticket_exists"] is True
    assert evidence["k55_ticket"]["shadow_module_exists"] is False
    assert evidence["literature"]["signature_fracdiff_harrv_ranked"] is True
