from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_gbpjpy_orderflow_proxy_gap as mod


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_csv(path: Path, rows: list[tuple[str, float, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["time,open,high,low,close,volume,num_trades"]
    for ts, close, volume in rows:
        lines.append(f"{ts},{close},{close},{close},{close},{volume},{volume}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _candidate(candidate_id: str, symbol: str = "GBPJPY") -> dict:
    return {
        "schema_version": "strategy_follow_candidate_v1",
        "row_key": f"candidate|{candidate_id}",
        "candidate_id": candidate_id,
        "symbol": symbol,
        "broker_symbol": symbol,
        "decision_time_utc": "2026-05-04T02:15:00+00:00",
        "created_at_utc": "2026-05-04T02:15:20+00:00",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _source_rows() -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]], list[tuple[str, float, float]]]:
    rows_6b: list[tuple[str, float, float]] = []
    rows_6j: list[tuple[str, float, float]] = []
    rows_gbpjpy: list[tuple[str, float, float]] = []
    for idx in range(16):
        hour = idx // 4
        minute = (idx % 4) * 15
        ts = f"2026-05-04 {hour:02d}:{minute:02d}:00"
        price_6b = 1.30 + idx * 0.001
        price_6j = 1.60 - idx * 0.0005
        price_gbpjpy = 180.0 + idx * 0.25
        rows_6b.append((ts, price_6b, 100 + idx))
        rows_6j.append((ts, price_6j, 200 + idx))
        rows_gbpjpy.append((ts, price_gbpjpy, 300 + idx))
    return rows_6b, rows_6j, rows_gbpjpy


def test_build_report_keeps_gbpjpy_confluence_blocked_and_registers_two_book_design(tmp_path):
    _write_jsonl(
        tmp_path / "shadow_logs/strategy_follow_candidates.jsonl",
        [_candidate("gbp-1"), _candidate("nas-1", "NAS100")],
    )
    rows_6b, rows_6j, rows_gbpjpy = _source_rows()
    _write_csv(tmp_path / "data/6b.csv", rows_6b)
    _write_csv(tmp_path / "data/6j.csv", rows_6j)
    _write_csv(tmp_path / "data/gbpjpy.csv", rows_gbpjpy)

    report = mod.build_report(
        root=tmp_path,
        generated_at_utc="2026-05-05T00:00:00+00:00",
        leg_6b_m15=Path("data/6b.csv"),
        leg_6j_m15=Path("data/6j.csv"),
        gbpjpy_m15=Path("data/gbpjpy.csv"),
    )
    row = report["candidate_status_rows"][0]

    assert report["status"] == "BLOCKED_WITH_PRE_REGISTERED_PROXY_DESIGN"
    assert report["completion_evidence"]["gbpjpy_candidates_seen"] == 1
    assert report["completion_evidence"]["existing_gbpjpy_confluence_inferred"] is False
    assert row["direct_confluence_allowed"] is False
    assert row["existing_confluence_inferred"] is False
    assert row["current_proxy_status"] == "NO_REGISTERED_DIRECT_PROXY"
    assert row["paid_data_calls"] == 0
    assert row["paid_fetch_attempted"] is False
    assert "TWO_BOOK_SYNTHETIC_6B_6J" in {design["design_id"] for design in report["proxy_designs"]}
    assert {
        "GBPJPY-PROXY-T1-CORRELATION-STABILITY",
        "GBPJPY-PROXY-T2-LEAD-LAG",
        "GBPJPY-PROXY-T3-SESSION-OVERLAP",
        "GBPJPY-PROXY-T4-CONTRACT-LIQUIDITY",
        "GBPJPY-PROXY-T5-OUTCOME-TRANSFER-CAVEAT",
    } == {test["test_id"] for test in report["pre_registered_tests"]}
    assert report["price_transfer_validation"]["no_outcomes_opened"] is True


def test_append_status_rows_is_idempotent(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate("gbp-1")])
    rows_6b, rows_6j, rows_gbpjpy = _source_rows()
    _write_csv(tmp_path / "data/6b.csv", rows_6b)
    _write_csv(tmp_path / "data/6j.csv", rows_6j)
    _write_csv(tmp_path / "data/gbpjpy.csv", rows_gbpjpy)
    report = mod.build_report(
        root=tmp_path,
        generated_at_utc="2026-05-05T00:00:00+00:00",
        leg_6b_m15=Path("data/6b.csv"),
        leg_6j_m15=Path("data/6j.csv"),
        gbpjpy_m15=Path("data/gbpjpy.csv"),
    )
    target = tmp_path / "shadow_logs/gbpjpy_proxy_gap_status.jsonl"

    assert mod.append_status_rows_if_missing(report["candidate_status_rows"], target) == 1
    assert mod.append_status_rows_if_missing(report["candidate_status_rows"], target) == 0
    assert len(target.read_text(encoding="utf-8").splitlines()) == 1

    _write_jsonl(
        tmp_path / "shadow_logs/strategy_follow_candidates.jsonl",
        [_candidate("gbp-1"), _candidate("nas-1", "NAS100")],
    )
    refreshed = mod.build_report(
        root=tmp_path,
        generated_at_utc="2026-05-05T00:05:00+00:00",
        leg_6b_m15=Path("data/6b.csv"),
        leg_6j_m15=Path("data/6j.csv"),
        gbpjpy_m15=Path("data/gbpjpy.csv"),
    )
    assert mod.append_status_rows_if_missing(refreshed["candidate_status_rows"], target) == 0
    assert len(target.read_text(encoding="utf-8").splitlines()) == 1


def test_no_gbpjpy_candidates_still_registers_design(tmp_path):
    _write_jsonl(tmp_path / "shadow_logs/strategy_follow_candidates.jsonl", [_candidate("nas-1", "NAS100")])

    report = mod.build_report(root=tmp_path, generated_at_utc="2026-05-05T00:00:00+00:00")

    assert report["status"] == "NO_GBPJPY_CANDIDATES_DESIGN_REGISTERED"
    assert report["candidate_status_rows"] == []
    assert report["completion_evidence"]["existing_gbpjpy_confluence_inferred"] is False
    assert any(design["design_id"] == "TWO_BOOK_SYNTHETIC_6B_6J" for design in report["proxy_designs"])
