from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage06_ltf_entry_nofill_repair_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_candidate_repair_stage06", MODULE_PATH)
stage06 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage06
spec.loader.exec_module(stage06)


def _row(**overrides):
    row = {
        "terminal_outcome": "target_first",
        "simulated_r": 1.5,
        "ltf_action": "PLACE_LIMIT",
    }
    row.update(overrides)
    return row


def _path(**overrides):
    row = {
        "path_source_status": "SIMULATED_FROM_LOCAL_OHLC",
        "price_path_truth_status": "measured",
        "source_mode": "OHLC_M1_CSV",
        "source_window_complete": True,
        "same_bar_ambiguity": False,
        "pre_entry_tp_touch_utc": None,
        "pre_entry_sl_touch_utc": None,
    }
    row.update(overrides)
    return row


def test_stage06_policy_requires_source_when_path_row_missing_or_unmeasured():
    missing = stage06.classify_stage06_ltf_policy(_row(), None, None)
    unmeasured = stage06.classify_stage06_ltf_policy(
        _row(),
        _path(price_path_truth_status="not_claimed_runtime_reference_only"),
        None,
    )

    assert missing["stage06_ltf_action"] == "SOURCE_CAPTURE_REQUIRED"
    assert missing["selected_after_stage06_ltf"] is True
    assert unmeasured["stage06_ltf_action"] == "SOURCE_CAPTURE_REQUIRED"
    assert unmeasured["source_complete_for_ltf_decision"] is False


def test_stage06_policy_monitors_when_path_monitor_sees_pre_entry_touch():
    policy = stage06.classify_stage06_ltf_policy(
        _row(terminal_outcome="stop_first", simulated_r=-1.0),
        _path(pre_entry_tp_touch_utc="2025-01-01T10:01:00Z"),
        None,
    )

    assert policy["stage06_ltf_action"] == "MONITOR_LTF_PATH"
    assert policy["selected_after_stage06_ltf"] is True
    assert policy["decision_inputs_exclude_future_r"] is True


def test_stage06_policy_monitors_same_bar_nofill_and_m15_ltf_disagreement():
    same_bar = stage06.classify_stage06_ltf_policy(
        _row(),
        _path(same_bar_ambiguity=True),
        None,
    )
    no_fill = stage06.classify_stage06_ltf_policy(
        _row(terminal_outcome="no_fill", simulated_r=None),
        _path(),
        None,
    )
    disagreement = stage06.classify_stage06_ltf_policy(
        _row(),
        _path(),
        {"ltf_simulated_r": -1.0, "m15_simulated_r": 1.5},
    )

    assert same_bar["stage06_ltf_action"] == "MONITOR_LTF_PATH"
    assert no_fill["stage06_ltf_action"] == "MONITOR_LTF_PATH"
    assert disagreement["stage06_ltf_action"] == "MONITOR_LTF_PATH"


def test_stage06_policy_leaves_clean_measured_path_as_place_limit():
    policy = stage06.classify_stage06_ltf_policy(_row(), _path(), None)

    assert policy["stage06_ltf_action"] == "PLACE_LIMIT"
    assert policy["execution_behavior_changed"] is False
