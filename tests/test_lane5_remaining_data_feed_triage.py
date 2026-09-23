from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane5_remaining_data_feed_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _seed_feed_root(root: Path) -> None:
    _write_json(
        root / "data" / "mt5_research_exports" / "tick_availability" / "probe.json",
        {
            "files": {
                "XAUUSD_recent": {
                    "file_symbol": "XAUUSD",
                    "window": "recent",
                    "start": "2026-05-01T00:00:00+00:00",
                    "end": "2026-05-01T23:59:59+00:00",
                    "has_ticks": True,
                    "rows": 123,
                    "first_tick_utc": "2026-05-01T00:00:01+00:00",
                    "last_tick_utc": "2026-05-01T23:59:58+00:00",
                },
                "XAUUSD_pre_2024": {
                    "file_symbol": "XAUUSD",
                    "window": "pre_2024",
                    "start": "2023-12-01T00:00:00+00:00",
                    "end": "2023-12-01T23:59:59+00:00",
                    "has_ticks": False,
                    "rows": 0,
                },
            }
        },
    )
    for series_id in ("DGS10", "VIXCLS"):
        _write_json(
            root / "data" / "external" / "status" / f"fred__{series_id}.json",
            {
                "source": "fred",
                "status_key": series_id,
                "status": "fresh",
                "row_count": 2,
                "latest_observation_utc": "2026-05-01T00:00:00+00:00",
            },
        )
        _write_jsonl(
            root / "data" / "external" / "normalized" / "fred" / f"{series_id}.jsonl",
            [
                {
                    "source": "fred",
                    "series_id": series_id,
                    "observation_date": "2026-05-01",
                    "value": 1.0,
                    "published_at_utc": "2026-05-02T00:00:00+00:00",
                }
            ],
        )

    _write_json(
        root / "data" / "external" / "status" / "wgc__gold_demand_trends.json",
        {
            "source": "wgc",
            "status_key": "gold_demand_trends",
            "status": "fresh",
            "row_count": 2,
            "latest_observation_utc": "2026-03-31T00:00:00+00:00",
        },
    )
    _write_jsonl(
        root / "data" / "external" / "normalized" / "wgc" / "gold_demand_trends.jsonl",
        [
            {
                "source": "wgc",
                "dataset": "gold_demand_trends_gold_balance_central_bank_and_other_institutions_quarterly",
                "category": "Central Bank and Other Institutions",
                "observation_date": "2026-03-31",
                "value": 10.0,
            },
            {
                "source": "wgc",
                "dataset": "gold_etf_flows",
                "category": "Global ETF holdings",
                "observation_date": "2026-03-31",
                "value": 20.0,
            },
        ],
    )


def test_remaining_data_feed_triage_classifies_source_state(tmp_path):
    _seed_feed_root(tmp_path)

    payload = mod.build_payload(tmp_path)
    by_id = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["D-2"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["D-7"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["D-8"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["D-9"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["D-10"]["status"] == "DONE"
    assert payload["status_counts"] == {"BLOCKED_WITH_REASON": 4, "DONE": 1}


def test_remaining_data_feed_triage_extracts_feed_inventory(tmp_path):
    _seed_feed_root(tmp_path)

    payload = mod.build_payload(tmp_path)
    inventories = payload["inventories"]

    assert inventories["tick_probe"]["pre_2024_windows_with_ticks"] == 0
    assert inventories["tick_probe"]["windows_with_ticks"] == 1
    assert inventories["fred"]["series"] == ["DGS10", "VIXCLS"]
    assert inventories["fred"]["normalized_row_count"] == 2
    assert inventories["source_terms"]["bis"] is False
    assert inventories["wgc"]["central_bank_row_count"] == 1
    assert inventories["wgc"]["central_bank_datasets"] == [
        "gold_demand_trends_gold_balance_central_bank_and_other_institutions_quarterly"
    ]
