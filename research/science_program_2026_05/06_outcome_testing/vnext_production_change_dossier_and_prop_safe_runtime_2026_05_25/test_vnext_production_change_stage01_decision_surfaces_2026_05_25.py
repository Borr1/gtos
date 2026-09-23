from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage01_decision_surfaces_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage01", MODULE_PATH)
stage01 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage01)


def _groups():
    path = stage01.REPO_ROOT / stage01.DECISION_SURFACE_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_stage01_groups_all_decision_map_rows_and_preserves_decisions():
    groups = _groups()
    summary = stage01.summarize_groups(groups)

    assert stage01.verify(groups, summary) == []
    assert summary["decision_map_row_count"] == 7555
    assert (
        summary["unique_decision_map_row_ids"]
        + summary["duplicate_decision_map_row_id_extra_instances"]
    ) == 7555
    assert summary["implementation_decision_counts"] == stage01.EXPECTED_FINAL_DECISION_COUNTS


def test_stage01_routes_promotions_guards_ltf_ai_and_prop_surfaces():
    groups = _groups()
    required_stage_counts = stage01.summarize_groups(groups)["required_stage_row_counts"]
    runtime_surfaces = {
        group["group_key"]["runtime_surface"]
        for group in groups
    }

    assert required_stage_counts["STAGE_02_PROMOTION_IMPLEMENTATION"] > 0
    assert required_stage_counts["STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION"] > 0
    assert required_stage_counts["STAGE_04_MIXED_RESOLUTION"] > 0
    assert required_stage_counts["STAGE_05_PROP_SAFE_SELECTOR"] > 0
    assert required_stage_counts["STAGE_06_LTF_ENTRY_NOFILL_ENGINE"] > 0
    assert "pre_ai_route_selector_and_ai_narrowing" in runtime_surfaces
    assert "risk_adjustment_and_prop_safe_selector" in runtime_surfaces
    assert "ltf_path_nofill_pending_lifecycle_engine" in runtime_surfaces
