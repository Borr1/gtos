from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage04_mixed_resolution_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage04", MODULE_PATH)
stage04 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage04)


def _rows() -> list[dict]:
    path = stage04.REPO_ROOT / stage04.MIXED_RESOLUTION_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _summary() -> dict:
    return json.loads(
        (stage04.REPO_ROOT / stage04.STAGE04_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def test_stage04_mixed_resolution_ledger_covers_all_replay_mixed_rows():
    rows = _rows()
    summary = _summary()

    assert summary["mixed_resolution_runtime_row_instances"] == 1018
    assert summary["unique_mixed_resolution_row_ids"] == 1018
    assert summary["mixed_resolution_class_counts"] == {
        "ambiguous_but_replay_measured": 374,
        "harmful_overblock_context": 32,
        "replay_resolvable_into_avoid_candidate": 74,
        "replay_resolvable_into_follow_candidate": 86,
        "useful_avoid_context": 452,
    }
    assert summary["computed_decision_counts"] == {
        "AVOID": 526,
        "FOLLOW": 86,
        "MIXED": 406,
    }
    assert not stage04.verify_rows(rows, summary)


def test_stage04_harmful_overblock_rows_are_non_override_mixed_guards():
    rows = _rows()
    harmful = [row for row in rows if row["mixed_resolution_class"] == "harmful_overblock_context"]

    assert len(harmful) == 32
    for row in harmful:
        assert row["computed_decision"] == "MIXED"
        assert row["runtime_candidate_use_permitted"] is False
        assert row["mixed_resolution_non_override_guard"] is True
        assert row["harmful_overblock_killed_or_redesigned"] is True
        assert row["production_activation_gate"] == "gtos_vnext_runtime.apply_to_execution"
        assert row["live_effect"] is False
        assert row["broker_operation"] is False
        assert row["paid_api_or_vendor_call"] is False


def test_stage04_actionable_rows_keep_required_runtime_anchors():
    rows = _rows()
    actionable = [row for row in rows if row["runtime_candidate_use_permitted"]]

    assert len(actionable) == 612
    for row in actionable:
        scope = row["event_scope"]
        assert any(scope.get(field) for field in ("symbol", "source_symbol", "symbol_family", "market"))
        assert scope.get("route_session")
        assert scope.get("side")
        assert row["computed_decision"] in {"FOLLOW", "AVOID"}
        assert row["source_component"] == scope["source_component"]
