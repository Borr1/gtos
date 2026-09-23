from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane4_options_proxy_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _seed_flashalpha(root: Path) -> None:
    mappings = {
        "QQQ": "NAS100",
        "DIA": "US30",
        "SPY": "US30",
        "GLD": "XAUUSD",
        "SLV": "XAGUSD",
    }
    for idx, (proxy, symbol) in enumerate(mappings.items()):
        _write_json(
            root / "data" / "external" / "status" / f"flashalpha_gex__{proxy}_{symbol}_2026-05-15.json",
            {
                "source": "flashalpha_gex",
                "status": "fresh",
                "status_key": f"{proxy}_{symbol}_2026-05-15",
                "row_count": 1,
                "latest_publication_utc": f"2026-05-01T00:1{idx}:00+00:00",
                "extra": {
                    "proxy_symbol": proxy,
                    "gtos_symbol": symbol,
                    "expiration": "2026-05-15",
                },
            },
        )
        _write_jsonl(
            root / "data" / "external" / "normalized" / "flashalpha_gex" / f"{proxy}_gex_20260501T001{idx}00Z.jsonl",
            [
                {
                    "source": "flashalpha_gex",
                    "proxy_symbol": proxy,
                    "gtos_symbol": symbol,
                    "expiration": "2026-05-15",
                    "as_of_utc": f"2026-05-01T00:1{idx}:00+00:00",
                    "net_gex": 100.0 + idx,
                    "net_gex_label": "positive",
                    "gamma_flip": 450.0 + idx,
                    "underlying_price": 451.0 + idx,
                }
            ],
        )


def test_build_payload_blocks_missing_vix_terms_and_marks_flashalpha_proxy_done(tmp_path):
    _write_json(
        tmp_path / "data" / "external" / "status" / "fred__VIXCLS.json",
        {
            "source": "fred",
            "status": "fresh",
            "status_key": "VIXCLS",
            "row_count": 1128,
            "latest_observation_utc": "2026-04-29T00:00:00+00:00",
            "extra": {"series_id": "VIXCLS"},
        },
    )
    _write_jsonl(
        tmp_path / "data" / "external" / "normalized" / "fred" / "VIXCLS_observations_20260501T000732Z.jsonl",
        [{"source": "fred", "series_id": "VIXCLS", "observation_date": "2026-04-29", "value": 24.1}],
    )
    _seed_flashalpha(tmp_path)

    payload = mod.build_payload(tmp_path)

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["task_classifications"]["A-2"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["task_classifications"]["A-3"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["task_classifications"]["D-3"]["status"] == "DONE"
    assert payload["feed_inventory"]["flashalpha_gex"]["normalized_row_count"] == 5
    assert payload["feed_inventory"]["fred"]["available_vol_terms"]["VIXCLS"] is True
    assert payload["feed_inventory"]["fred"]["available_vol_terms"]["VIX1D"] is False
    assert payload["feed_inventory"]["fred"]["available_vol_terms"]["VIX9D"] is False


def test_detect_external_data_terms_reads_status_metadata(tmp_path):
    _write_json(
        tmp_path / "data" / "external" / "status" / "fred__VIX9D.json",
        {"source": "fred", "status_key": "VIX9D", "extra": {"series_id": "VIX9D"}},
    )

    found = mod.detect_external_data_terms(tmp_path, ("VIX9D", "VIX1D"))

    assert found == {"VIX9D": True, "VIX1D": False}
