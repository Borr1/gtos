import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/classify_b4_source_realism_blockers.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("classify_b4_source_realism_blockers", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def stage(summary: dict, key: str) -> dict:
    return next(row for row in summary["stage_buckets"] if row["key"] == key)


def test_b4_source_realism_classifier_separates_cost_source_and_geometry(tmp_path):
    module = load_module()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_TEST"
    write_jsonl(
        tmp_path / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        [
            {
                "symbol": "GER40",
                "session": "london",
                "fill_realism_class": "ordered_tick_entry_touch",
                "missed_cost_disposition": "scoreable_missed_cost_refused_non_executable_diagnostic",
                "broker_pretrade_cost_executable": False,
                "miss_reason": "scheduler_materialization_skipped_selector_not_risk_bearing_cost_failed",
                "opportunity_net_proxy_r": 1.25,
                "expected_net_r": 2.0,
                "risk_expression_ladder": {"ladder_tier": "diagnostic", "risk_decision_reason": "cost_failed"},
            },
            {
                "symbol": "AUDUSD",
                "session": "tokyo",
                "fill_realism_class": "m15_proxy",
                "missed_cost_disposition": "cost_authority_not_primary_miss_reason",
                "broker_pretrade_cost_executable": True,
                "fill_realism_reason": "postdecision_m15_proxy_diagnostic_path_not_executable",
                "expected_net_r": 0.8,
                "expected_cost_r": 0.1,
                "counterfactual_order_close_mark_r": 0.6,
                "risk_expression_ladder": {"ladder_tier": "diagnostic", "risk_decision_reason": "source_proxy"},
            },
            {
                "symbol": "XAUUSD",
                "session": "ny",
                "fill_realism_class": "source_safe_immediate_marketable",
                "missed_cost_disposition": "cost_authority_not_primary_miss_reason",
                "broker_pretrade_cost_executable": True,
                "missed_non_executable_diagnostic_reason": "package_marketable_limit_entry_guard_blocked",
                "opportunity_net_proxy_r": -0.5,
                "expected_net_r": 1.1,
                "risk_expression_ladder": {"ladder_tier": "reduced", "risk_decision_reason": "marketable_guard"},
            },
        ],
    )

    summary, bucket_rows = module.classify_missed_ledger(prefix, route=tmp_path, generated_at="2026-07-06T00:00:00Z")

    assert summary["rows"] == 3
    cost_stage = stage(summary, "B6_cost_refusal_or_cost_authority")
    assert cost_stage["rows"] == 1
    assert cost_stage["scoreable_rows"] == 1
    assert cost_stage["opportunity_net_r_sum"] == 1.25
    assert cost_stage["expected_net_r_sum_diagnostic_only"] == 2.0
    source_stage = stage(summary, "B4_source_realism_or_missing_ordered_source")
    assert source_stage["unscoreable_rows"] == 1
    assert source_stage["diagnostic_proxy_mark_rows"] == 1
    assert source_stage["diagnostic_proxy_mark_net_r_sum"] == 0.5
    assert stage(summary, "B4_order_geometry_guard")["negative_r_sum"] == -0.5
    assert summary["missed_cost_disposition_counts"] == {
        "cost_authority_not_primary_miss_reason": 2,
        "scoreable_missed_cost_refused_non_executable_diagnostic": 1,
    }
    assert any(
        row["bucket_type"] == "stage_fill"
        and row["key"] == "B4_source_realism_or_missing_ordered_source|m15_proxy"
        and row["rows"] == 1
        for row in bucket_rows
    )
