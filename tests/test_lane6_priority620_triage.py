from __future__ import annotations

import json

from scripts import analyze_lane6_priority620_triage as mod


def test_latest_file_uses_mtime(tmp_path):
    root = tmp_path / "x"
    root.mkdir()
    old = root / "a_1.jsonl"
    new = root / "a_2.jsonl"
    old.write_text("", encoding="utf-8")
    new.write_text("", encoding="utf-8")

    assert mod.latest_file(root, "a_*.jsonl") == new


def test_inventory_counts_jsonl_symbols(tmp_path):
    root = tmp_path / "data" / "external" / "normalized" / "cftc_cot"
    root.mkdir(parents=True)
    path = root / "disagg_combined_20260501T000000Z.jsonl"
    path.write_text(
        json.dumps({"gtos_symbol": "XAUUSD"}) + "\n" + json.dumps({"gtos_symbol": "XAUUSD"}) + "\n",
        encoding="utf-8",
    )

    inv = mod.cftc_inventory(tmp_path)

    assert inv["rows"] == 2
    assert inv["symbols"] == {"XAUUSD": 2}


def test_build_payload_preserves_no_promotion_and_expected_statuses(tmp_path):
    payload = mod.build_payload(tmp_path)
    by_id = {item["id"]: item for item in payload["classifications"]}

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["A-4"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["C-4"]["status"] == "DONE"
    assert by_id["R-7"]["status"] == "REJECTED_FAILED"
    assert by_id["A-16"]["status"] == "FILED_FOR_APPROVAL"


def test_hpm_inventory_reads_current_dsr_schema(tmp_path):
    root = tmp_path / "research" / "ml_program" / "phase_2" / "position_mgmt"
    root.mkdir(parents=True)
    (root / "h_pm01_per_cohort_results.json").write_text(
        json.dumps(
            {
                "primary_full_cohort": {
                    "backtest": {"delta": {"mean_r": -0.0049}},
                    "dsr_paired_delta": {"dsr_p": 0.9999},
                },
                "per_cohort": {
                    "per_instrument": {
                        "NAS100": {
                            "backtest": {"delta": {"mean_r": 0.0906}},
                            "dsr_paired": {"dsr_p": 0.0152},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    inv = mod.hpm_inventory(tmp_path)

    assert inv["hpm01_delta_mean_r"] == -0.0049
    assert inv["hpm01_dsr_p"] == 0.9999
    assert inv["hpm01_nas100_delta_r"] == 0.0906
    assert inv["hpm01_nas100_dsr_p"] == 0.0152


def test_render_markdown_contains_classification_matrix(tmp_path):
    payload = mod.build_payload(tmp_path)
    md = mod.render_markdown(payload)

    assert "## Classification Matrix" in md
    assert "NO_PROMOTION_VERDICT" in md
    assert "| A-1 |" in md
