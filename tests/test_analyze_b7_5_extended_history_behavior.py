import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/analyze_b7_5_extended_history_behavior.py"
)
VERIFIER_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py"
)
REAL_REPORT_PATH = MODULE_PATH.parent / "B7_5_EXTENDED_HISTORY_BEHAVIOR_SUMMARY.json"


def load_module():
    spec = importlib.util.spec_from_file_location("analyze_b7_5_history", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_b7_5_history", VERIFIER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def surface(net_r: float, trades: int = 1) -> dict:
    return {
        "trade_rows": trades,
        "wins": int(net_r > 0),
        "losses": int(net_r < 0),
        "flats": int(net_r == 0),
        "net_r": net_r,
        "gross_r": net_r,
        "final_r": net_r,
        "execution_cost_r": 0.0,
        "cash_pnl": net_r * 100.0,
        "risk_cash": 100.0,
        "risk_pct": 0.1,
        "breakdowns": {},
    }


def window(
    window_id: str,
    start: str,
    end: str,
    source_digest: str,
    net_r: float,
    *,
    execution_digest: str = "shared-contract",
) -> dict:
    return {
        "window_id": window_id,
        "role": "paired_extended_history",
        "prefix": window_id,
        "date_start": start,
        "date_end": end,
        "contract_binding": {
            "valid": True,
            "actual_shared_execution_contract_digest_sha256": execution_digest,
            "behavioral_execution_contract_digest_sha256": execution_digest,
            "execution_contract_authority_partition_valid": True,
            "expected_source_plan_digest_sha256": source_digest,
        },
        "truth_contract": {"pass": True},
        "transfer": {
            "package_axes": 1101,
            "candidate_generated_axes": 900,
            "scorecard_or_order_present_axes": 400,
            "order_present_axes": 20,
            "filled_trade_axes": 10,
            "non_additive_window_source_bound_signal_r": 1000.0,
            "actual_physical_executable_r": net_r,
            "actual_headline_executable_r": net_r,
        },
        "behavior": {
            "physical": surface(net_r),
            "headline": surface(net_r),
            "diagnostic_only": surface(0.0, trades=0),
        },
        "stress": {
            "guarded_stress_rows": [
                {"stress_id": "extra_cost", "net_r": max(net_r - 0.1, 0.1)}
            ]
        },
        "identity_comparison_disposition": (
            "cross_window_trade_identity_comparison_forbidden_disjoint_dates"
        ),
    }


def source_contract(reports: dict[str, dict]) -> dict:
    windows = [
        {
            "window_id": report["window_id"],
            "start_day": report["date_start"],
            "end_day": report["date_end"],
            "source_plan_digest_sha256": report["contract_binding"][
                "expected_source_plan_digest_sha256"
            ],
            "selector_disposition_digest_sha256": "d" * 64,
        }
        for report in reports.values()
    ]
    return {
        "artifact": {
            "path": "B7_5_EXTENDED_HISTORY_SOURCE_WINDOW_CONTRACT.json",
            "required": True,
            "present": True,
            "hash_bound": True,
            "sha256": "e" * 64,
        },
        "valid": True,
        "contract_digest_sha256": "f" * 64,
        "pair_binding_sha256": "a" * 64,
        "shared_execution_contract_digest_sha256": next(iter(reports.values()))[
            "contract_binding"
        ]["actual_shared_execution_contract_digest_sha256"],
        "behavioral_execution_contract_digest_sha256": next(
            iter(reports.values())
        )["contract_binding"]["behavioral_execution_contract_digest_sha256"],
        "postrun_proof_consumer_contract_digest_sha256": "b" * 64,
        "execution_contract_authority_partition_valid": True,
        "source_bound_signal_semantics": {
            "evidence_class": (
                "source_member_axis_overlap_not_additive_exact_execution_r"
            ),
            "additive_allowed": False,
            "executable_r_percentage_allowed": False,
        },
        "windows": windows,
    }


def test_aggregate_rows_keeps_terminal_unscoreable_trade_out_of_wlf_and_r() -> None:
    module = load_module()

    result = module.aggregate_rows(
        [
            {
                "net_proxy_r": 1.2,
                "gross_r": 1.3,
                "final_r": 1.3,
                "pnl_cash": 120.0,
                "risk_cash": 100.0,
                "risk_pct": 0.1,
            },
            {
                "net_proxy_r": -0.4,
                "gross_r": -0.3,
                "final_r": -0.3,
                "pnl_cash": -40.0,
                "risk_cash": 100.0,
                "risk_pct": 0.1,
            },
            {
                "entry_fill_executable": True,
                "terminal_r_scoreable": False,
                "net_proxy_r": None,
                "gross_r": None,
                "final_r": None,
                "pnl_cash": None,
                "risk_cash": 100.0,
                "risk_pct": 0.1,
            },
        ]
    )

    assert result["trade_rows"] == 3
    assert result["scoreable_trade_rows"] == 2
    assert result["unscoreable_trade_rows"] == 1
    assert result["terminal_r_unscoreable_trade_rows"] == 1
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["flats"] == 0
    assert result["net_r"] == 0.8
    assert result["gross_r"] == 1.0
    assert result["final_r"] == 1.0
    assert result["cash_pnl"] == 80.0
    assert result["risk_cash"] == 300.0
    assert result["risk_pct"] == 0.3


def test_cross_window_truth_can_pass_while_economic_generalization_fails(monkeypatch):
    module = load_module()
    reports = {
        "january": window(
            "january", "2026-01-01", "2026-01-31", "source-january", 1.0
        ),
        "april": window(
            "april", "2026-04-01", "2026-04-30", "source-april", -1.0
        ),
    }
    monkeypatch.setattr(
        module,
        "window_report",
        lambda spec, root=module.ROUTE: reports[spec.window_id],
    )

    report = module.build_report(
        [
            module.WindowSpec("january", "paired_extended_history", "january"),
            module.WindowSpec("april", "paired_extended_history", "april"),
        ],
        source_contract=source_contract(reports),
    )

    pair = report["paired_extended_history"]
    assert pair["truth_integrity_pass"] is True
    assert pair["paired_windows_disjoint"] is True
    assert pair["paired_windows_non_adjacent"] is True
    assert pair["economic_generalization_pass"] is False
    assert pair["b7_5_gate_pass"] is False
    assert report["status"] == "b7_5_truth_green_economic_generalization_failed"
    assert report["comparison_boundary"]["cross_window_trade_identity"].startswith(
        "not comparable"
    )


def test_cross_window_execution_digest_mismatch_fails_truth(monkeypatch):
    module = load_module()
    reports = {
        "january": window(
            "january",
            "2026-01-01",
            "2026-01-31",
            "source-january",
            1.0,
            execution_digest="contract-a",
        ),
        "april": window(
            "april",
            "2026-04-01",
            "2026-04-30",
            "source-april",
            1.0,
            execution_digest="contract-b",
        ),
    }
    monkeypatch.setattr(
        module,
        "window_report",
        lambda spec, root=module.ROUTE: reports[spec.window_id],
    )

    report = module.build_report(
        [
            module.WindowSpec("january", "paired_extended_history", "january"),
            module.WindowSpec("april", "paired_extended_history", "april"),
        ],
        source_contract=source_contract(reports),
    )

    assert report["paired_extended_history"]["same_execution_contract"] is False
    assert report["paired_extended_history"]["truth_integrity_pass"] is False
    assert report["status"] == "b7_5_truth_integrity_failed"


def test_window_report_rejects_loaded_trade_count_mismatch(tmp_path, monkeypatch):
    module = load_module()
    prefix = "BROAD_LIVE_AS_IF_REPLAY_SYNTHETIC"
    summary_path = module.replay_compare.summary_path(prefix, root=tmp_path)
    summary_path.write_text(
        json.dumps(
            {
                "status": "broad_live_as_if_replay_materialized_broker_live_closed",
                "date_start": "2026-01-01",
                "date_end": "2026-01-31",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module.replay_compare,
        "run_metrics",
        lambda *args, **kwargs: {"physical_trades": 2, "headline_trades": 1},
    )
    monkeypatch.setattr(module.replay_compare, "iter_jsonl", lambda path: iter([{}]))

    with pytest.raises(ValueError, match="trade ledger mismatch"):
        module.window_report(
            module.WindowSpec("synthetic", "paired_extended_history", prefix),
            root=tmp_path,
        )


def test_non_additive_signal_is_not_reported_as_executable_r_percentage():
    module = load_module()

    transfer = module.transfer_rates(
        {
            "package_axes_available_inside_replay_window": 1101,
            "candidate_generated_axes_inside_replay_window": 900,
            "non_additive_executable_gated_source_bound_signal_r_inside_replay_window": 1000.0,
            "source_bound_signal_evidence_class": (
                "source_member_axis_overlap_not_additive_exact_execution_r"
            ),
            "source_bound_r_additive_allowed": False,
            "executable_r_to_source_bound_r_percentage_allowed": False,
            "actual_executable_r_pct_of_window_source_bound_r": None,
            "actual_executable_r_pct_disposition": (
                "forbidden_non_additive_source_member_axis_overlap_signal"
            ),
        }
    )

    assert transfer["non_additive_window_source_bound_signal_available"] is True
    assert transfer["non_additive_window_source_bound_signal_r"] == 1000.0
    assert transfer["physical_r_pct_of_source_bound_signal"] is None


def test_canonical_verifier_accepts_current_cross_window_proof():
    verifier = load_verifier()
    report = json.loads(REAL_REPORT_PATH.read_text(encoding="utf-8"))

    assert verifier.b7_5_extended_history_behavior_issues(report) == []


def test_canonical_verifier_rejects_artifact_hash_drift():
    verifier = load_verifier()
    report = json.loads(REAL_REPORT_PATH.read_text(encoding="utf-8"))
    report["windows"][0]["artifacts"]["trade_ledger"]["sha256"] = "0" * 64

    issues = verifier.b7_5_extended_history_behavior_issues(report)

    assert any("artifact_binding_invalid" in issue for issue in issues)


def test_canonical_verifier_rejects_window_contract_drift():
    verifier = load_verifier()
    report = json.loads(REAL_REPORT_PATH.read_text(encoding="utf-8"))
    report["windows"][0]["contract_binding"][
        "actual_shared_execution_contract_digest_sha256"
    ] = "0" * 64

    issues = verifier.b7_5_extended_history_behavior_issues(report)

    assert "b7_5_paired_window_contract_binding_invalid" in issues
