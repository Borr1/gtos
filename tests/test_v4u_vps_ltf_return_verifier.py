from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.verify_v4u_vps_ltf_returns import main as verify_returns_main
from src.research_infra.v4u_vps_ltf_return_verifier import verify_ltf_returns


def test_verify_ltf_returns_catalogs_accepted_rejected_and_missing(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.jsonl"
    rows = [
        _requirement("v4u_ltf_reqaccepted", "NAS100"),
        _requirement("v4u_ltf_reqrejected", "XAUUSD"),
        _requirement("v4u_ltf_reqmissing", "GBPUSD"),
    ]
    _write_jsonl(requirements, rows)
    root = tmp_path / "data" / "mt5_research_exports"
    _write_valid_m1(root, rows[0])
    _write_valid_tick(root, rows[0])
    _write_invalid_m1(root, rows[1])

    report, result_rows = verify_ltf_returns(
        requirements_jsonl=requirements,
        source_roots=(root,),
        run_id="unit_test_returns",
    )

    by_id = {row["requirement_id"]: row for row in result_rows}
    assert report["requirements_total"] == 3
    assert report["requirements_with_accepted_source"] == 1
    assert report["return_status_counts"] == {
        "accepted_m1_and_tick": 1,
        "missing_returned_exports": 1,
        "rejected_returned_sources_only": 1,
    }
    accepted = by_id["v4u_ltf_reqaccepted"]
    assert accepted["return_status"] == "accepted_m1_and_tick"
    assert accepted["accepted_m1_source_count"] == 1
    assert accepted["accepted_tick_source_count"] == 1
    assert accepted["can_rerun_ordered_path_oracle_for_requirement"] is True
    assert all(
        source["request_window_status"] == "request_window_matches"
        for source in accepted["accepted_sources"]
    )
    rejected = by_id["v4u_ltf_reqrejected"]
    assert rejected["return_status"] == "rejected_returned_sources_only"
    assert "source_broker=FTMO" in rejected["rejected_sources"][0][
        "source_provenance_status"
    ]
    missing = by_id["v4u_ltf_reqmissing"]
    assert missing["return_status"] == "missing_returned_exports"
    assert missing["accepted_source_count"] == 0


def test_verify_ltf_returns_cli_writes_report_and_rows(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.jsonl"
    row = _requirement("v4u_ltf_reqaccepted", "NAS100")
    _write_jsonl(requirements, [row])
    root = tmp_path / "data" / "mt5_research_exports"
    _write_valid_m1(root, row)
    report = tmp_path / "report.json"
    output_rows = tmp_path / "rows.jsonl"

    assert (
        verify_returns_main(
            [
                "--requirements-jsonl",
                str(requirements),
                "--source-root",
                str(root),
                "--output-report-json",
                str(report),
                "--output-requirement-jsonl",
                str(output_rows),
                "--run-id",
                "unit_test_cli",
            ]
        )
        == 0
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in output_rows.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert payload["requirements_with_accepted_source"] == 1
    assert rows[0]["return_status"] == "accepted_m1_only"


def _requirement(requirement_id: str, symbol: str) -> dict:
    return {
        "schema_version": "v4u_vps_mt5_ltf_export_requirement_v1",
        "requirement_id": requirement_id,
        "symbol": symbol,
        "mt5_symbol": symbol,
        "date": "2026-06-02",
        "session": "NY_BROAD",
        "request_start_utc": "2026-06-02T13:00:00Z",
        "request_end_utc": "2026-06-02T13:02:00Z",
        "candidate_rows": 1,
    }


def _write_valid_m1(root: Path, requirement: dict) -> None:
    folder = root / f"v4u_ftmo_ltf_{requirement['requirement_id']}_m1"
    path = folder / f"{requirement['symbol']}_M1.csv"
    folder.mkdir(parents=True)
    path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-06-02T13:00:00+00:00,100,100,99.9,100,1",
                "2026-06-02T13:01:00+00:00,100,101,99.9,100.5,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_manifest(
        folder / "manifest.json",
        schema="mt5_research_ohlcv_export_v1",
        source_broker="FTMO",
        requirement=requirement,
        files={
            f"{requirement['symbol']}_M1": {
                "path": str(path),
                "file_symbol": requirement["symbol"],
                "mt5_symbol": requirement["mt5_symbol"],
                "timeframe": "M1",
                "rows": 2,
                "row_count": 2,
                "first": "2026-06-02T13:00:00+00:00",
                "last": "2026-06-02T13:01:00+00:00",
                "request_start_utc": requirement["request_start_utc"],
                "request_end_utc": requirement["request_end_utc"],
                "sha256": _sha256(path),
                "source_server": "FTMO-Demo",
                "source_account_login": 123456,
                "export_tool": "scripts/export_mt5_research_ohlcv.py",
            }
        },
    )


def _write_valid_tick(root: Path, requirement: dict) -> None:
    folder = root / f"v4u_ftmo_ltf_{requirement['requirement_id']}_tick"
    path = folder / "ticks" / requirement["symbol"] / "window_ticks.jsonl"
    path.parent.mkdir(parents=True)
    _write_jsonl(
        path,
        [
            {"ts_utc": "2026-06-02T13:00:01+00:00", "bid": 100.0, "ask": 100.1},
            {"ts_utc": "2026-06-02T13:00:02+00:00", "bid": 101.0, "ask": 101.1},
        ],
    )
    _write_manifest(
        folder / "manifest.json",
        schema="mt5_research_tick_export_v1",
        source_broker="FTMO",
        requirement=requirement,
        files={
            f"{requirement['symbol']}_window_TICK": {
                "path": str(path),
                "file_symbol": requirement["symbol"],
                "mt5_symbol": requirement["mt5_symbol"],
                "timeframe": "TICK",
                "rows": 2,
                "row_count": 2,
                "first": "2026-06-02T13:00:01+00:00",
                "last": "2026-06-02T13:00:02+00:00",
                "request_start_utc": requirement["request_start_utc"],
                "request_end_utc": requirement["request_end_utc"],
                "sha256": _sha256(path),
                "source_server": "FTMO-Demo",
                "source_account_login": 123456,
                "export_tool": "scripts/export_mt5_research_ticks.py",
            }
        },
    )


def _write_invalid_m1(root: Path, requirement: dict) -> None:
    folder = root / f"v4u_ftmo_ltf_{requirement['requirement_id']}_m1"
    path = folder / f"{requirement['symbol']}_M1.csv"
    folder.mkdir(parents=True)
    path.write_text(
        "time,open,high,low,close,volume\n2026-06-02T13:00:00+00:00,1,1,1,1,1\n",
        encoding="utf-8",
    )
    _write_manifest(
        folder / "manifest.json",
        schema="mt5_research_ohlcv_export_v1",
        source_broker="redacted_account",
        requirement=requirement,
        files={
            f"{requirement['symbol']}_M1": {
                "path": str(path),
                "file_symbol": requirement["symbol"],
                "mt5_symbol": requirement["mt5_symbol"],
                "timeframe": "M1",
                "rows": 1,
                "row_count": 1,
                "request_start_utc": requirement["request_start_utc"],
                "request_end_utc": requirement["request_end_utc"],
                "sha256": _sha256(path),
                "source_server": "redacted_account",
                "source_account_login": 123456,
                "export_tool": "scripts/export_mt5_research_ohlcv.py",
            }
        },
    )


def _write_manifest(
    path: Path,
    *,
    schema: str,
    source_broker: str,
    requirement: dict,
    files: dict,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": schema,
                "account": {"login": 123456, "server": "FTMO-Demo"},
                "source_provenance": {
                    "source_broker": source_broker,
                    "source_role": "owner_authorized_path_override",
                    "replaces_missing_frozen_path_source": True,
                    "not_redacted_account_native": True,
                    "source_truth_scope": "ordered_price_path_only_not_broker_order_lifecycle_truth",
                    "handoff_requirement_id": requirement["requirement_id"],
                    "broker_lifecycle_truth_satisfied": False,
                    "asof_decision_truth_satisfied": False,
                },
                "files": files,
            }
        ),
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
