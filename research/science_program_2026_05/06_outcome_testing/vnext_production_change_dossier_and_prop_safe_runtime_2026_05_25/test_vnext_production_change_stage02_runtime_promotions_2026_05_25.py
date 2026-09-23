from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name(
    "build_vnext_production_change_stage02_runtime_promotions_2026_05_25.py"
)
spec = importlib.util.spec_from_file_location("vnext_prod_stage02", MODULE_PATH)
stage02 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stage02)


def _rows() -> list[dict]:
    path = stage02.REPO_ROOT / stage02.RUNTIME_CHANGE_LEDGER_PATH
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _summary() -> dict:
    return json.loads(
        (stage02.REPO_ROOT / stage02.STAGE02_SUMMARY_PATH).read_text(encoding="utf-8")
    )


def test_stage02_runtime_change_ledger_covers_every_promoted_decision_map_id():
    rows = _rows()
    summary = _summary()

    assert summary["unique_promoted_decision_map_row_ids"] == 982
    assert summary["promoted_runtime_row_instances"] >= 982
    assert len(rows) == summary["promoted_runtime_row_instances"]
    assert not stage02.verify_rows(rows, summary)
    assert summary["system_surface_counts"]["ltf_path_nofill_pending_lifecycle_engine"] > 0
    assert summary["system_surface_counts"]["route_decision_scorer_filter_router"] > 0
    assert summary["system_surface_counts"]["pending_policy_nofill_limit_market_selector"] > 0
    assert summary["system_surface_counts"]["pre_ai_route_selector_and_ai_narrowing"] > 0
    assert summary["system_surface_counts"]["risk_adjustment_and_prop_safe_selector"] > 0


def test_stage02_runtime_rows_are_owner_activation_gated_and_broker_safe():
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
        if row["runtime_candidate_use_permitted"]:
            scope = row["event_scope"]
            assert any(scope.get(field) for field in ("symbol", "source_symbol", "symbol_family", "market"))
            assert scope.get("route_session")
            assert scope.get("side")
            assert row["computed_decision"] in {"FOLLOW", "AVOID"}
        else:
            assert row["computed_decision"] == "MIXED"
