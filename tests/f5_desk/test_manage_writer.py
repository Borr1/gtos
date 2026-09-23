"""The manage writer respects gtos.judgment.manage.v1 exactly."""
from __future__ import annotations

import json
from datetime import timedelta

from scripts.f5_desk import common, shim

from .conftest import MIDDAY_NOW

SLATE = {
    "schema": "gtos.judgment.slate.v2",
    "namespace": "operator",
    "slate_id": "feed0123deadbeef",
    "candidates": [],
    "open_positions": [
        {"ticket": 111, "symbol": "EURUSD", "direction": "LONG",
         "entry_price": 1.2000, "stop_now": 1.1950},
        {"ticket": 222, "symbol": "XAUUSD", "direction": "SHORT",
         "entry_price": 2400.0, "stop_now": 2412.0},
    ],
}


def _clean(manage_rows):
    raw = {"schema": shim.VERDICT_SCHEMA, "slate_id": SLATE["slate_id"],
           "verdicts": [], "manage": manage_rows, "notes": ""}
    clean, reject, drops = shim.validate_verdict(raw, SLATE)
    assert clean is not None, reject
    return clean, drops


def test_contract_shape_exact(tmp_path):
    clean, _ = _clean([
        {"ticket": 111, "action": "tighten_stop", "new_stop": 1.1980,
         "mechanism": "microstructure", "why_code": "spread_blowout"},
        {"ticket": 222, "action": "close", "mechanism": "weekend_carry",
         "why_code": "friday_close"},
    ])
    out = shim.write_manage(clean, SLATE, tmp_path, now=MIDDAY_NOW)
    path = shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat())
    assert out["path"] == str(path)
    doc = json.loads(path.read_text())
    assert set(doc) == {"schema", "rows"}
    assert doc["schema"] == "gtos.judgment.manage.v1"
    by_key = {(r["ticket"], r["action"]): r for r in doc["rows"]}
    tighten = by_key[(111, "tighten_stop")]
    assert tighten["new_stop"] == 1.1980
    assert isinstance(tighten["ticket"], int)
    assert tighten["why_code"] == "spread_blowout"
    assert common.parse_utc(tighten["written_at_utc"]) is not None
    assert 60 <= tighten["ttl_s"] <= 14400
    close = by_key[(222, "close")]
    assert "new_stop" not in close
    assert close["mechanism"] == "weekend_carry"


def test_short_direction_tighten_semantics(tmp_path):
    # SHORT: risk-reducing stop moves DOWN
    clean, drops = _clean([
        {"ticket": 222, "action": "tighten_stop", "new_stop": 2408.0,
         "mechanism": "microstructure", "why_code": "ok_down"},
    ])
    assert len(clean["manage"]) == 1
    # and a widen (up) is dropped
    _, drops = _clean([
        {"ticket": 222, "action": "tighten_stop", "new_stop": 2415.0,
         "mechanism": "microstructure", "why_code": "widen"},
    ])
    assert drops.get("manage_tighten_not_risk_reducing") == 1


def test_tighten_without_new_stop_dropped(tmp_path):
    _, drops = _clean([
        {"ticket": 111, "action": "tighten_stop",
         "mechanism": "microstructure", "why_code": "no_stop"},
    ])
    assert drops.get("manage_tighten_missing_new_stop") == 1


def test_merge_replaces_same_ticket_action(tmp_path):
    clean1, _ = _clean([{"ticket": 111, "action": "tighten_stop", "new_stop": 1.1960,
                         "mechanism": "microstructure", "why_code": "first"}])
    shim.write_manage(clean1, SLATE, tmp_path, now=MIDDAY_NOW)
    clean2, _ = _clean([{"ticket": 111, "action": "tighten_stop", "new_stop": 1.1985,
                         "mechanism": "microstructure", "why_code": "second"}])
    shim.write_manage(clean2, SLATE, tmp_path, now=MIDDAY_NOW + timedelta(minutes=5))
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    rows = [r for r in doc["rows"] if r["ticket"] == 111]
    assert len(rows) == 1
    assert rows[0]["new_stop"] == 1.1985
    assert rows[0]["why_code"] == "second"


def test_expired_rows_pruned_on_rewrite(tmp_path):
    clean1, _ = _clean([{"ticket": 111, "action": "close",
                         "mechanism": "event_proximity", "why_code": "old"}])
    shim.write_manage(clean1, SLATE, tmp_path, now=MIDDAY_NOW, ttl_s=60)
    clean2, _ = _clean([{"ticket": 222, "action": "close",
                         "mechanism": "weekend_carry", "why_code": "new"}])
    shim.write_manage(clean2, SLATE, tmp_path, now=MIDDAY_NOW + timedelta(hours=2))
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    tickets = {r["ticket"] for r in doc["rows"]}
    assert tickets == {222}, "the 60s-ttl row written 2h ago must be gone"


def test_ttl_clamped_into_contract_bounds(tmp_path):
    clean, _ = _clean([{"ticket": 111, "action": "close",
                        "mechanism": "microstructure", "why_code": "x"}])
    # Function-level ttl_s is the fallback when the row has no ttl_s.
    # Per-row default 1800 (validate_verdict) is the Monday chair bind.
    for row in clean["manage"]:
        row.pop("ttl_s", None)
    shim.write_manage(clean, SLATE, tmp_path, now=MIDDAY_NOW, ttl_s=10 ** 9)
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    assert doc["rows"][0]["ttl_s"] == 14400
    shim.write_manage(clean, SLATE, tmp_path, now=MIDDAY_NOW + timedelta(minutes=1), ttl_s=1)
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    assert doc["rows"][0]["ttl_s"] == 60


def test_direction_unknown_tighten_dropped(tmp_path):
    slate = {
        "schema": "gtos.judgment.slate.v2", "namespace": "operator",
        "slate_id": "feed0123deadbeef", "candidates": [],
        "open_positions": [{"ticket": 333, "symbol": "US30", "stop_now": 44000.0}],
    }
    raw = {"schema": shim.VERDICT_SCHEMA, "slate_id": slate["slate_id"], "verdicts": [],
           "manage": [{"ticket": 333, "action": "tighten_stop", "new_stop": 44100.0,
                       "mechanism": "microstructure", "why_code": "x"}]}
    clean, _, drops = shim.validate_verdict(raw, slate)
    assert clean is not None
    assert clean["manage"] == []
    assert drops.get("manage_direction_unknown") == 1
    # close needs no direction — still allowed
    raw["manage"] = [{"ticket": 333, "action": "close", "mechanism": "microstructure",
                      "why_code": "x"}]
    clean, _, drops = shim.validate_verdict(raw, slate)
    assert len(clean["manage"]) == 1


def test_expired_rows_are_pruned_even_when_no_new_manage_rows_arrive(tmp_path):
    """Ticket 178427810 class (2026-08-25): an expired row lingering in the day file
    re-emits one 'expired' consumer rejection per book restart, because the consumer's
    terminal memo is process-scoped. Any verdict application — even manage-empty —
    must sweep expired rows out of the file."""
    from datetime import datetime, timedelta, timezone
    from scripts.f5_desk import common, shim

    now = datetime(2026, 8, 25, 7, 0, tzinfo=timezone.utc)
    state = tmp_path / "state"
    state.mkdir()
    path = shim.manage_path(state, common.utc_day(now))
    stale = {"ticket": 178427810, "action": "close", "mechanism": "correlation",
             "why_code": "same_symbol_same_geometry_double_stack_dedup",
             "written_at_utc": (now - timedelta(hours=3)).isoformat(), "ttl_s": 1800}
    live = {"ticket": 42, "action": "close", "mechanism": "m", "why_code": "w",
            "written_at_utc": (now - timedelta(seconds=60)).isoformat(), "ttl_s": 1800}
    common.write_json_atomic(path, {"schema": shim.MANAGE_SCHEMA, "rows": [stale, live]})

    out = shim.write_manage({"manage": []}, {}, state, now=now)
    assert out == {"rows": 0, "path": None}
    doc = common.read_json(path)
    tickets = [r["ticket"] for r in doc["rows"]]
    assert tickets == [42], "expired row must be swept; live row must survive"


def test_ticket_not_on_slate_is_dropped():
    raw = {"schema": shim.VERDICT_SCHEMA, "slate_id": SLATE["slate_id"],
           "verdicts": [], "manage": [
               {"ticket": 999999, "action": "close",
                "mechanism": "microstructure", "why_code": "ghost"},
           ], "notes": ""}
    clean, reject, drops = shim.validate_verdict(raw, SLATE)
    assert clean is not None, reject
    assert clean["manage"] == []
    assert drops.get("manage_unknown_ticket") == 1


def test_per_row_ttl_defaults_1800(tmp_path):
    clean, _ = _clean([{"ticket": 111, "action": "close",
                        "mechanism": "microstructure", "why_code": "x"}])
    assert clean["manage"][0]["ttl_s"] == 1800
    out = shim.write_manage(clean, SLATE, tmp_path, now=MIDDAY_NOW)
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    assert doc["rows"][0]["ttl_s"] == 1800
    assert out["rows"] == 1


def test_per_row_ttl_clamped_and_honored(tmp_path):
    clean, _ = _clean([{"ticket": 111, "action": "close",
                        "mechanism": "microstructure", "why_code": "x",
                        "ttl_s": 10 ** 9}])
    assert clean["manage"][0]["ttl_s"] == 14400
    clean2, _ = _clean([{"ticket": 111, "action": "close",
                         "mechanism": "microstructure", "why_code": "y",
                         "ttl_s": 7}])
    assert clean2["manage"][0]["ttl_s"] == 60
    shim.write_manage(clean2, SLATE, tmp_path, now=MIDDAY_NOW)
    doc = json.loads(shim.manage_path(tmp_path, MIDDAY_NOW.date().isoformat()).read_text())
    assert doc["rows"][0]["ttl_s"] == 60
