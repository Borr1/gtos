from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_candidate_repair_stage03_executable_stream_semantics_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_candidate_repair_stage03", MODULE_PATH)
stage03 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stage03
spec.loader.exec_module(stage03)


def test_classify_repaired_semantics_keeps_legacy_mixed_and_off_kz_out_of_prop_budget():
    base = {
        "session": "london",
        "pre_ai_action": "ALLOW_AI",
        "ltf_action": "PLACE_LIMIT",
        "pending_action": "PLACE_LIMIT",
    }

    legacy = stage03.classify_repaired_semantics({**base, "new_route_decision": "LEGACY"})
    mixed = stage03.classify_repaired_semantics({**base, "new_route_decision": "MIXED"})
    off_kz = stage03.classify_repaired_semantics(
        {**base, "session": "off_kz", "new_route_decision": "FOLLOW"}
    )
    follow = stage03.classify_repaired_semantics({**base, "new_route_decision": "FOLLOW"})

    assert legacy["prop_governance_eligible_after_stage03"] is False
    assert legacy["preserve_current_system_behavior"] is True
    assert mixed["prop_governance_eligible_after_stage03"] is False
    assert mixed["preserve_current_system_behavior"] is True
    assert off_kz["prop_governance_eligible_after_stage03"] is False
    assert off_kz["reason"] == "off_kz_diagnostic_non_executable"
    assert follow["prop_governance_eligible_after_stage03"] is True


def test_classify_repaired_semantics_excludes_pre_ai_and_ltf_blocks_before_prop_budget():
    base = {
        "session": "london",
        "new_route_decision": "FOLLOW",
        "pending_action": "PLACE_LIMIT",
    }

    pre_ai_avoid = stage03.classify_repaired_semantics(
        {**base, "pre_ai_action": "SKIP_AI_AVOID_ONLY", "ltf_action": "PLACE_LIMIT"}
    )
    ltf_avoid = stage03.classify_repaired_semantics(
        {
            **base,
            "pre_ai_action": "ALLOW_AI",
            "ltf_action": "SKIP_LTF_NOFILL_AVOID",
            "ltf_reason": "fixture_ltf_block",
        }
    )

    assert pre_ai_avoid["prop_governance_eligible_after_stage03"] is False
    assert pre_ai_avoid["reason"] == "pre_ai_skip_avoid_only"
    assert ltf_avoid["prop_governance_eligible_after_stage03"] is False
    assert ltf_avoid["reason"] == "fixture_ltf_block"


def test_scenario_accumulator_reports_selected_only_coverage_separate_from_candidate_count():
    acc = stage03.ScenarioAccumulator("fixture")
    acc.add(
        {
            "symbol": "XAUUSD",
            "session": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "source_mode": "OHLC_M1_CSV",
            "month": "2026-01",
            "simulated_r": 1.5,
        },
        selected=True,
        reason="selected",
    )
    acc.add(
        {
            "symbol": "GBPJPY",
            "session": "tokyo",
            "side": "SHORT",
            "framework": "fvg_fill",
            "source_mode": "OHLC_M1_CSV",
            "month": "2026-01",
            "simulated_r": -1.0,
        },
        selected=False,
        reason="not_selected",
    )

    record = acc.to_record()

    assert record["candidate_count"] == 2
    assert record["selected_count"] == 1
    assert record["performance_count"] == 1
    assert record["selected_only_coverage"]["symbols"] == {"XAUUSD": 1}
    assert record["skip_reasons"] == {"not_selected": 1}


def test_stage03_no_paid_mechanical_follow_actions_cover_current_and_legacy_labels():
    assert "MECHANICAL_FOLLOW_NO_AI" in stage03.NO_PAID_MECHANICAL_FOLLOW_ACTIONS
    assert "FOLLOW_WITHOUT_AI" in stage03.NO_PAID_MECHANICAL_FOLLOW_ACTIONS
