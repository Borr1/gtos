from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage00_inventory_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage00", MODULE_PATH)
stage00 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage00)


def test_stage00_outputs_cover_terminal_replay_and_next_invariant():
    inventory = json.loads((stage00.REPO_ROOT / stage00.INVENTORY_PATH).read_text())
    state = json.loads((stage00.REPO_ROOT / stage00.STATE_PATH).read_text())

    failures = stage00.verify_outputs(inventory, state)
    assert failures == []
    assert inventory["stage00_checks"]["final_decision_map_logical_rows"] == 7555
    assert inventory["stage00_checks"]["prop_metric_rows"] == 24
    assert state["first_incomplete_invariant"] != "STAGE_00_INPUT_INVENTORY"
    assert state["stage_status_table"]["STAGE_00_INPUT_INVENTORY"] == "complete"


def test_stage00_inventory_records_runtime_config_and_replay_hashes():
    inventory = json.loads((stage00.REPO_ROOT / stage00.INVENTORY_PATH).read_text())
    state = json.loads((stage00.REPO_ROOT / stage00.STATE_PATH).read_text())

    assert inventory["prompt"]["sha256"] == state["prompt_hash"]
    assert inventory["starter"]["sha256"] == state["starter_hash"]
    assert inventory["config"]["gtos_vnext_runtime_selected"]["enabled"] is True
    assert inventory["config"]["gtos_vnext_runtime_selected"]["apply_to_execution"] is False
    assert inventory["config"]["gtos_vnext_runtime_artifact_path_count"] > 0
    assert "final_decision_map" in state["replay_artifact_hashes_used"]
