from __future__ import annotations

import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"


def test_stage01_summary_and_state_are_semantic_not_wrapper_only() -> None:
    summary = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_SUMMARY_{DATE_ID}.json").read_text(
            encoding="utf-8"
        )
    )
    state = json.loads(
        (ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json").read_text(encoding="utf-8")
    )
    assert summary["no_arbitrary_top_n"] is True
    assert summary["lossy_sampling_used"] is False
    assert summary["first_incomplete_invariant_after_stage01"] == "STAGE_02_SOURCE_AND_PATH_CAPABILITY_INVENTORY"
    assert state["stage_status_table"]["STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT"] == "complete"
    assert state["first_incomplete_invariant"] != "STAGE_01_STATIC_PRIMITIVE_ASSUMPTION_AUDIT"
    assert state["static_proxy_assumption_ledger_path"].endswith(
        f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_LEDGER_{DATE_ID}.jsonl"
    )


def test_stage01_ledger_contains_required_action_families() -> None:
    ledger = ROUTE_DIR / f"VNEXT_MOONSHOT_STATIC_PRIMITIVE_ASSUMPTION_LEDGER_{DATE_ID}.jsonl"
    families = set()
    actions = set()
    source_kinds = set()
    with ledger.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            families.add(row["assumption_family"])
            actions.add(row["exact_action"])
            source_kinds.add(row["source_kind"])
    assert "fixed_bracket_or_proxy_r" in families
    assert "candidate_origin_boxing" in families
    assert "dynamic_execution_gap" in families
    assert "replay_under_dynamic_execution_policy" in actions
    assert "semantic_verifier_hardening" in actions
    assert "large_row_ledger_deferred" in source_kinds
