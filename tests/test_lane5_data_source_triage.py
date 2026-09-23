from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane5_data_source_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _seed_minimal_root(root: Path) -> None:
    for symbol in mod.GTOS_SYMBOLS:
        symbol_dir = root / "data" / "ticks" / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        (symbol_dir / ".state.json").write_text("{}", encoding="utf-8")
        (symbol_dir / "2026-05-01.parquet").write_bytes(b"fake")

    _write_json(
        root / "data" / "external" / "status" / "cftc_cot__disagg_combined_088691_XAUUSD.json",
        {
            "source": "cftc_cot",
            "status": "fresh",
            "status_key": "disagg_combined_088691_XAUUSD",
            "row_count": 1,
            "latest_observation_utc": "2026-04-21T00:00:00+00:00",
            "extra": {"cftc_contract_market_code": "088691", "gtos_symbol": "XAUUSD"},
        },
    )
    _write_jsonl(
        root / "data" / "external" / "normalized" / "cftc_cot" / "disagg_combined_20260501T000000Z.jsonl",
        [{"source": "cftc_cot", "report_type": "disagg_combined", "gtos_symbol": "XAUUSD"}],
    )

    _write_json(
        root / "data" / "external" / "status" / "lbma_calendar__fix_calendar.json",
        {
            "source": "lbma_calendar",
            "status": "fresh",
            "status_key": "fix_calendar",
            "row_count": 2,
            "latest_observation_utc": "2026-04-24T00:00:00+00:00",
        },
    )
    _write_jsonl(
        root / "data" / "external" / "normalized" / "lbma_calendar" / "fix_calendar_20260501T000000Z.jsonl",
        [
            {"source": "lbma_calendar", "metal": "gold", "gtos_symbol": "XAUUSD"},
            {"source": "lbma_calendar", "metal": "silver", "gtos_symbol": "XAGUSD"},
        ],
    )

    _write_json(
        root
        / "data"
        / "mt5_research_exports"
        / "history_availability"
        / "phase3_m15_probe_2021_calendar_year_v2_20260501_20260501T012140Z.json",
        {
            "files": {
                "XAGUSD_M15": {
                    "file_symbol": "XAGUSD",
                    "rows": 817,
                    "first": "2021-12-17T16:15:00+00:00",
                    "last": "2021-12-31T22:30:00+00:00",
                    "has_rows_in_requested_range": True,
                    "covers_requested_start": False,
                    "reaches_requested_end": False,
                },
                "XAUUSD_M15": {
                    "file_symbol": "XAUUSD",
                    "rows": 1,
                    "has_rows_in_requested_range": False,
                    "covers_requested_start": False,
                    "reaches_requested_end": False,
                },
            }
        },
    )

    (root / "src" / "components").mkdir(parents=True, exist_ok=True)
    (root / "src" / "components" / "tick_capture.py").write_text("", encoding="utf-8")
    (root / "src" / "components" / "tick_features.py").write_text("", encoding="utf-8")
    (root / "research" / "ml_program").mkdir(parents=True, exist_ok=True)
    (root / "research" / "ml_program" / "MASTER_BACKLOG.md").write_text(
        "K-1 tick-count-time bars", encoding="utf-8"
    )


def test_lane5_triage_classifies_partial_sources_and_blockers(tmp_path):
    _seed_minimal_root(tmp_path)

    payload = mod.build_payload(tmp_path)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["task_classifications"]["D-1"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert payload["task_classifications"]["D-4"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["task_classifications"]["D-5"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["task_classifications"]["D-12"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["inventories"]["cftc"]["gtos_symbols"] == ["XAUUSD"]
    assert payload["inventories"]["lbma"]["gtos_symbols"] == ["XAGUSD", "XAUUSD"]
    assert payload["inventories"]["history_availability"]["symbols_with_2021_rows"] == ["XAGUSD"]


def test_tick_inventory_counts_symbol_days(tmp_path):
    _seed_minimal_root(tmp_path)
    (tmp_path / "data" / "ticks" / "XAUUSD" / "2026-05-02.parquet").write_bytes(b"fake")

    inventory = mod.tick_inventory(tmp_path)

    assert inventory["symbols_with_ticks"] == 7
    assert inventory["max_symbol_days"] == 2
    assert inventory["tick_features_helper_exists"] is True
