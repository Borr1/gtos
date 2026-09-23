from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage05_avoid_pre_ai_repair_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_candidate_repair_stage05", MODULE_PATH)
stage05 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage05
spec.loader.exec_module(stage05)


def _row(r: float | None, **overrides):
    row = {
        "symbol": "XAUUSD",
        "session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "month": "2026-01",
        "source_mode": "OHLC_M1_CSV",
        "new_route_decision": "AVOID",
        "pre_ai_action": "SKIP_AI_AVOID_ONLY",
        "avoid_evidence_family": "fixture_family",
        "avoid_source_component": "fixture_component",
        "simulated_r": r,
    }
    row.update(overrides)
    return row


def test_group_decision_preserves_only_net_useful_avoid_filters():
    group = stage05.GroupStats("family", "component")
    for _ in range(30):
        group.add(_row(-1.0))
    for _ in range(10):
        group.add(_row(1.5))

    decision = group.decision()

    assert decision["implementation_decision"] == "PRESERVE_BOUNDED_AVOID_FILTER"
    assert decision["r_sum_if_taken"] < 0
    assert decision["losers_avoided"] > decision["winners_blocked"]


def test_group_decision_demotes_net_harmful_and_null_attribution_blocks():
    harmful = stage05.GroupStats("family", "component")
    null_attr = stage05.GroupStats("family", "__NULL__")
    for _ in range(25):
        harmful.add(_row(1.5))
        null_attr.add(_row(-1.0))

    assert harmful.decision()["implementation_decision"] == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
    assert null_attr.decision()["implementation_decision"] == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK"
    assert "missing_source_component" in null_attr.decision()["decision_reason"]


def test_avoid_group_key_separates_pre_ai_without_route_join():
    key = stage05.avoid_group_key(
        _row(
            -1.0,
            new_route_decision="FOLLOW",
            avoid_evidence_family=None,
            avoid_source_component=None,
        )
    )

    assert key == ("pre_ai_skip_avoid_only", "pre_ai_skip_avoid_only_no_route_avoid_join")
