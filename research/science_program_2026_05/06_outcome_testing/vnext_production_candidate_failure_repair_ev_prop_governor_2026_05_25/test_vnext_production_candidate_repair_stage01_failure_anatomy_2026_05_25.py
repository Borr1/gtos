from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE01_FAILURE_ANATOMY_SUMMARY_2026-05-25.json"
ACCEPTANCE_PATH = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_ACCEPTANCE_GATE_FAILURE_LEDGER_2026-05-25.jsonl"


def load_summary() -> dict:
    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_stage01_preserves_full_failed_replay_counts() -> None:
    summary = load_summary()
    counts = summary["row_counts"]

    assert counts["failure_anatomy_rows"] == 253234
    assert counts["selected_rows"] == 10
    assert counts["dropped_baseline_rows"] == 35977
    assert counts["avoid_ev_rows"] == 37047
    assert counts["route_semantics_legacy_mixed_rows"] == 174413
    assert counts["avoid_dominance_missing_rows"] == 0
    assert summary["transition_matrix"] == {
        "baseline_false__new_false": 217247,
        "baseline_false__new_true": 4,
        "baseline_true__new_false": 35977,
        "baseline_true__new_true": 6,
    }


def test_stage01_acceptance_gate_ledger_names_repair_families() -> None:
    with ACCEPTANCE_PATH.open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    families = {record["failure_family"] for record in records}

    assert "stage09_viability_gate_absent" in families
    assert "stage10_artifact_existence_completion" in families
    assert "stage10_allows_stage10_in_progress" in families
    assert "new_mechanical_does_not_require_follow" in families
    assert "continuous_account_path" in families
