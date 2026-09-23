from __future__ import annotations

from scripts import fetch_databento_manifest as mod


def test_request_from_group_uses_manifest_symbols_and_window():
    request = mod.request_from_group(
        {
            "databento_symbols": ["YM.v.0", "ES.v.0"],
            "start_utc": "2026-04-17T12:45:00+00:00",
            "end_utc": "2026-04-17T17:00:00+00:00",
        },
        dataset="GLBX.MDP3",
        schema="trades",
        stype_in="continuous",
    )
    assert request.symbols == ("YM.v.0", "ES.v.0")
    assert request.start == "2026-04-17T12:45:00+00:00"
    assert request.end == "2026-04-17T17:00:00+00:00"


def test_select_groups_filters_requested_ids():
    manifest = {
        "fetch_groups": [
            {"group_id": "ofwin_0001"},
            {"group_id": "ofwin_0002"},
        ]
    }
    assert mod.select_groups(manifest, ["ofwin_0002"]) == [{"group_id": "ofwin_0002"}]


def test_parse_group_ids_accepts_repeatable_and_csv():
    assert mod.parse_group_ids(["ofwin_0001,ofwin_0002", "ofwin_0003"]) == [
        "ofwin_0001",
        "ofwin_0002",
        "ofwin_0003",
    ]
