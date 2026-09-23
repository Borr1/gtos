import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/compare_broad_replay_prefixes.py"
)


def load_compare_module():
    spec = importlib.util.spec_from_file_location(
        "compare_broad_replay_prefixes", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_long_comparison_artifacts_fit_filesystem_components(tmp_path: Path) -> None:
    module = load_compare_module()
    repair = "BROAD_LIVE_AS_IF_REPLAY_" + ("V245_REPAIR_" * 20)
    baseline = "BROAD_LIVE_AS_IF_REPLAY_" + ("V219_BASELINE_" * 20)

    stem = module.comparison_artifact_stem(
        baseline_prefix=baseline,
        repair_prefix=repair,
    )
    changed_stem = module.comparison_artifact_stem(
        baseline_prefix=f"{baseline}X",
        repair_prefix=repair,
    )
    summary_path = tmp_path / f"{stem}_BEHAVIOR_COMPARISON_SUMMARY.json"
    dossier_path = tmp_path / f"{stem}_BEHAVIOR_DOSSIER.md"

    assert len(stem) <= module.MAX_COMPARISON_ARTIFACT_STEM_CHARS
    assert stem != changed_stem
    assert len(summary_path.name.encode("utf-8")) <= 255
    assert len(dossier_path.name.encode("utf-8")) <= 255

    module.write_json(summary_path, {"status": "ok"})
    module.write_text(dossier_path, "ok\n")

    assert summary_path.exists()
    assert dossier_path.exists()


def test_trade_identity_delta_is_unavailable_when_declared_ledger_is_missing(
    tmp_path: Path,
) -> None:
    module = load_compare_module()
    module.ROUTE = tmp_path
    baseline = "BROAD_LIVE_AS_IF_REPLAY_BASELINE"
    repair = "BROAD_LIVE_AS_IF_REPLAY_REPAIR"
    module.write_json(
        tmp_path / f"{baseline}_SUMMARY.json",
        {
            "trade_rows": 2,
            "artifacts": {"trade": "/migrated/missing_baseline_trade.jsonl"},
        },
    )
    module.write_json(
        tmp_path / f"{repair}_SUMMARY.json",
        {"trade_rows": 1, "artifacts": {"trade": "repair_trade.jsonl"}},
    )
    (tmp_path / f"{repair}_TRADE_LEDGER.jsonl").write_text(
        json.dumps(
            {
                "candidate_id": "candidate-1",
                "broad_replay_profile": "repaired",
                "split": "holdout",
                "symbol": "XAUUSD",
                "side": "LONG",
                "net_r": 1.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    delta = module.trade_identity_delta(baseline, repair)

    assert delta["identity_comparison_status"] == "unavailable"
    assert delta["identity_comparison_available"] is False
    assert delta["baseline_trade_ledger"]["summary_declared_trade_count"] == 2
    assert delta["baseline_trade_ledger"]["physical_trade_count"] is None
    assert delta["repair_trade_ledger"]["status"] == "complete"
    assert delta["profile_split"] == {}


def test_trade_ledger_availability_rejects_declared_physical_count_mismatch(
    tmp_path: Path,
) -> None:
    module = load_compare_module()
    module.ROUTE = tmp_path
    prefix = "BROAD_LIVE_AS_IF_REPLAY_INCONSISTENT"
    trade_path = tmp_path / f"{prefix}_TRADE_LEDGER.jsonl"
    trade_path.write_text("{}\n", encoding="utf-8")

    availability = module.trade_ledger_availability(
        prefix,
        {"trade_rows": 2, "artifacts": {"trade": str(trade_path)}},
    )

    assert availability["status"] == "inconsistent"
    assert availability["summary_declared_trade_count"] == 2
    assert availability["physical_trade_count"] == 1
