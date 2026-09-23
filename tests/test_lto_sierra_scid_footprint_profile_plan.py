from __future__ import annotations

from pathlib import Path

from scripts import build_lto031_lto032_sierra_scid_footprint_profile_plan as script
from src.research_infra import lto_sierra_scid_footprint_profile_plan as mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_sierra(root: Path) -> None:
    _write(root / "NQM26-CME" / "manifest.json", '{"symbol":"NQM26-CME"}\n')
    _write(
        root / "NQM26-CME" / "NQM26_M15.csv",
        "\n".join(
            [
                "timestamp,open,high,low,close,volume,num_trades,bid_volume,ask_volume",
                "2026-05-05T13:00:00Z,100,101,99,100.5,1000,100,450,550",
                "2026-05-05T13:15:00Z,100.5,102,100,101,1200,110,500,700",
            ]
        )
        + "\n",
    )
    _write(
        root / "NQM26-CME" / "NQM26_H1.csv",
        "\n".join(
            [
                "timestamp,open,high,low,close,volume,num_trades",
                "2026-05-05T13:00:00Z,100,102,99,101,2200,210",
            ]
        )
        + "\n",
    )


def test_sierra_inventory_counts_manifests_csv_rows_and_bid_ask_capability(tmp_path: Path):
    sierra_root = tmp_path / "data/sierra_ohlcv_roots"
    _seed_sierra(sierra_root)

    inventory = mod.inventory_sierra_ohlcv_roots(sierra_root, repo_root=tmp_path)

    assert inventory["manifest_count"] == 1
    assert inventory["csv_file_count"] == 2
    assert inventory["csv_total_rows"] == 3
    assert inventory["bid_ask_capable_csv_count"] == 1
    assert inventory["files_by_timeframe"] == {"H1": 1, "M15": 1}
    assert inventory["files_by_root"] == {"NQM26-CME": 2}


def test_sierra_payload_feature_statuses_and_symbol_blockers(tmp_path: Path):
    sierra_root = tmp_path / "data/sierra_ohlcv_roots"
    _seed_sierra(sierra_root)

    payload = mod.build_payload(
        repo_root=tmp_path,
        sierra_root=sierra_root,
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )
    features = {row["feature_family"]: row for row in payload["feature_contracts"]}
    symbols = {row["gtos_symbol"]: row for row in payload["source_symbol_status"]}

    assert payload["status"] == mod.STATUS_READY
    assert payload["promotion_verdict"] == mod.PROMOTION_VERDICT
    assert payload["validation_issues"] == []
    assert features["scid_bid_ask_volume_v1"]["status"] == "READY_FROM_CONVERTED_SCID_OHLCV"
    assert features["scid_delta_v1"]["status"] == "READY_FROM_CONVERTED_SCID_OHLCV"
    assert features["scid_profile_poc_hvn_lvn_v1"]["status"] == "CONTRACT_READY_BIN_RULE_REQUIRED"
    assert features["scid_stacked_imbalance_v1"]["status"] == "BLOCKED_PRICE_LEVEL_BID_ASK_VOLUME_REQUIRED"
    assert features["scid_vah_val_v1"]["status"] == "BLOCKED_VALUE_AREA_DEFINITION_NOT_FROZEN"
    assert all(row["validation_safe"] is False for row in payload["feature_contracts"])
    assert symbols["XAGUSD"]["blocked"] is True
    assert symbols["USDJPY"]["blocked"] is True
    assert symbols["GBPUSD"]["blocked"] is True


def test_sierra_payload_has_no_action_counters(tmp_path: Path):
    payload = mod.build_payload(
        repo_root=tmp_path,
        sierra_root=tmp_path / "missing",
        generated_at_utc="2026-05-06T00:00:00+00:00",
    )

    assert payload["ai_calls"] == 0
    assert payload["order_calls"] == 0
    assert payload["paid_data_calls"] == 0
    assert payload["sierra_inventory"]["csv_file_count"] == 0


def test_validation_flags_unblocked_vah_val_and_unblocked_xagusd():
    payload = {
        "feature_contracts": mod.feature_contracts(),
        "source_symbol_status": mod.source_symbol_status_rows(),
    }
    for row in payload["feature_contracts"]:
        if row["feature_family"] == "scid_vah_val_v1":
            row["status"] = "READY"
    for row in payload["source_symbol_status"]:
        if row["gtos_symbol"] == "XAGUSD":
            row["blocked"] = False

    issues = mod.validate_payload(payload)

    assert "scid_vah_val_v1:VAH_VAL_NOT_BLOCKED" in issues
    assert "XAGUSD:SI_SOURCE_NOT_BLOCKED" in issues


def test_script_writes_sierra_plan_artifacts(tmp_path: Path):
    sierra_root = tmp_path / "data/sierra_ohlcv_roots"
    _seed_sierra(sierra_root)
    out_json = tmp_path / "sierra.json"
    out_md = tmp_path / "sierra.md"
    ops_md = tmp_path / "ops.md"

    assert script.main(
        [
            "--repo-root",
            str(tmp_path),
            "--sierra-root",
            str(sierra_root),
            "--output-json",
            str(out_json),
            "--output-md",
            str(out_md),
            "--operations-md",
            str(ops_md),
            "--generated-at-utc",
            "2026-05-06T00:00:00+00:00",
        ]
    ) == 0

    assert out_json.exists()
    assert out_md.exists()
    assert ops_md.exists()
    assert "NO_PROMOTION_VERDICT" in out_md.read_text(encoding="utf-8")
    assert "VAH/VAL is deferred" in ops_md.read_text(encoding="utf-8")
