from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage03_kill_redesign_guards_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage03", MODULE_PATH)
stage03 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage03)


def _rows() -> list[dict]:
    path = stage03.REPO_ROOT / stage03.KILL_REDESIGN_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _summary() -> dict:
    return json.loads(
        (stage03.REPO_ROOT / stage03.STAGE03_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def test_stage03_kill_redesign_ledger_covers_all_kill_and_guard_only_ids():
    rows = _rows()
    summary = _summary()

    assert summary["unique_stage03_decision_map_row_ids"] == 1130
    assert summary["stage03_runtime_row_instances"] == 1130
    assert summary["source_final_decision_counts"] == {
        "KEEP_SHADOW_OR_GUARD_ONLY": 272,
        "KILL_OR_REDESIGN_BEFORE_USE": 858,
    }
    assert not stage03.verify_rows(rows, summary)
    assert summary["system_surface_counts"]["ltf_path_nofill_pending_lifecycle_engine"] == 544
    assert summary["computed_decision_counts"].get("FOLLOW", 0) == 0


def test_stage03_rows_are_activation_gated_and_guard_only_rows_are_mixed():
    rows = _rows()
    assert rows

    for row in rows:
        assert row["activation_gated"] is True
        assert row["production_activation_gate"] == "gtos_vnext_runtime.apply_to_execution"
        assert row["live_effect"] is False
        assert row["broker_operation"] is False
        assert row["paid_api_or_vendor_call"] is False
        assert row["runtime_trading_or_live_broker_effect"] is False
        assert row["requires_owner_review_before_runtime_effect"] is True
        assert row["computed_decision"] != "FOLLOW"
        if row["source_final_decision"] == "KEEP_SHADOW_OR_GUARD_ONLY":
            assert row["computed_decision"] == "MIXED"
        if row["runtime_candidate_use_permitted"]:
            scope = row["event_scope"]
            assert any(scope.get(field) for field in ("symbol", "source_symbol", "symbol_family", "market"))
            assert scope.get("route_session")
            assert scope.get("side")
            assert row["computed_decision"] == "AVOID"
