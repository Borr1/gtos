from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
DRIVER = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/ch_declare.py"
)
RECEIPT = DRIVER.with_name("CH_MEASUREMENT_PROTOCOL_V1.json")


def _module():
    spec = importlib.util.spec_from_file_location("ch_declare", DRIVER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _digest(doc: dict) -> str:
    body = {k: v for k, v in doc.items() if k != "self_sha256"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_protocol_receipt_reproduces_from_outcome_blind_declaration_driver():
    mod = _module()
    on_disk = json.loads(RECEIPT.read_text())
    assert on_disk == json.loads(json.dumps(mod.protocol()))
    assert on_disk["self_sha256"] == _digest(on_disk)


def test_ce_four_looks_remain_exactly_four_and_strict_m2_never_falls_back():
    doc = json.loads(RECEIPT.read_text())
    assert doc["multiplicity"]["p1_hist"] == 4
    assert len(doc["p1_hist"]["looks"]) == 4
    assert "does not fall back" in doc["p1_hist"]["strict_m2_rule"]


def test_entry_hour_controls_are_billed_as_looks_before_gating():
    doc = json.loads(RECEIPT.read_text())
    arms = doc["entry_hour"]["looks"]
    assert arms[:3] == [
        "h00_control",
        "h01_ratified",
        "inverse_cheapest_shift_matched",
    ]
    assert arms[3:] == [f"random_shift_matched_s{i}" for i in range(5)]
    assert doc["multiplicity"]["entry_hour"] == len(arms) == 8
    assert doc["multiplicity"]["total_new_looks"] == 12


def test_control_population_is_count_matched_and_decision_rule_is_fixed():
    doc = json.loads(RECEIPT.read_text())["entry_hour"]
    assert "same number of rows" in doc["inverse_cheapest_shift_matched"]
    assert "same number of rows" in doc["random_shift_matched"]
    assert "at least 4 of 5" in doc["arm_rule"]
    assert "none <= -0.10" in doc["arm_rule"]


def test_march_is_blackout_plus_pre_replay_horizon_guard():
    doc = json.loads(RECEIPT.read_text())["march_2026"]
    assert doc["status"] == "OUTCOME_UNREAD"
    assert doc["engine_blackout"] == [["2026-03-01", "2026-03-31"]]
    assert "before any OHLC path" in doc["stronger_driver_guard"]
