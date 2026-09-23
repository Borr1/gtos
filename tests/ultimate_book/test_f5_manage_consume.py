"""THE MANAGE CONSUME SEAM (schema gtos.judgment.manage.v1), F5 only.

Contract under test (the shared interface with the judgment side):
file pipeline_state/ultimate_book/<ns>/judgment/manage_<YYYY-MM-DD>.json; a row is
ACTIONABLE iff written_at_utc parses AND age < ttl_s AND ttl_s in [60,14400] AND the
ticket is an open position of this book AND (tighten_stop) new_stop is STRICTLY
risk-reducing for the direction and not beyond current price. Malformed / expired /
unknown rows are logged+counted, never acted on, never fatal. Tighten-only is MANDATORY:
any widen rejects with reason ``widen_refused``.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book.book_owner import UltimateBookOwner
from src.components.ultimate_book.minimal_size import MinimalSizeConfig

F5_NS = "operator"
NOW = datetime(2026, 8, 25, 0, 5, 0, tzinfo=timezone.utc)


class _MT5:
    def __init__(self, bid=100.0, ask=100.02):
        self.bid, self.ask = bid, ask

    def get_tick(self, _symbol):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=datetime.now(timezone.utc))

    def get_account_balance(self):
        return 100_000.0

    def get_account_equity(self):
        return 100_000.0


class _ManageEE:
    """Execution-engine double: one open position + recording close/modify paths."""

    def __init__(self, ticket=42, direction="LONG", stop_loss=99.0,
                 close_ok=True, modify_ok=True):
        self.active_trade = SimpleNamespace(
            ticket=ticket, direction=direction, stop_loss=stop_loss,
            entry_price=100.0, current_volume=1.0,
        )
        self.closes = []
        self.modifies = []
        self._close_ok = close_ok
        self._modify_ok = modify_ok

    def close_position(self, reason):
        self.closes.append(reason)
        if self._close_ok:
            self.active_trade = None
        return self._close_ok

    def _modify_sl(self, ticket, new_sl, *, trade=None, modify_reason=""):
        self.modifies.append((ticket, new_sl, modify_reason))
        return self._modify_ok


def _config(authority=True):
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": True,
            "ultimate_book_live_broker_authority": authority,
            "ultimate_book_disable_broad_selector": True,
            "ultimate_book_profile": "clean3_w7_measured_nom1p25",
            "ultimate_book_include_clean3": True,
            "ultimate_book_derisk_mode": "band",
            "ultimate_book_include_candidate_book": False,
            "ultimate_book_include_market_expansion_book": False,
            "ultimate_book_stress_derisk": False,
            "ultimate_book_kelly_lite": True,
            "ultimate_book_kelly_conservative": True,
            "ultimate_book_drop_w7_symbols": True,
            "selector_v4_enabled": True,
            "selector_v4_apply_to_execution": False,
        },
    }


def _owner(tmp_path, namespace=F5_NS, authority=True, mt5=None):
    return UltimateBookOwner(
        _config(authority=authority),
        mt5 or _MT5(),
        str(tmp_path),
        namespace=namespace,
        engine_factory=lambda _symbol: _ManageEE(),
        minimal_size=MinimalSizeConfig(
            enabled=True, target_risk_usd=75.0, notional_initial_usd=100_000.0,
        ),
    )


def _write_manage(tmp_path, rows, *, day=None, namespace=F5_NS,
                  schema="gtos.judgment.manage.v1", raw=None):
    d = Path(tmp_path) / "pipeline_state" / "ultimate_book" / namespace / "judgment"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"manage_{day or NOW.date().isoformat()}.json"
    if raw is not None:
        p.write_text(raw, encoding="utf-8")
    else:
        p.write_text(json.dumps({"schema": schema, "rows": rows}), encoding="utf-8")
    return p


def _row(ticket=42, action="close", new_stop=None, written=None, ttl_s=600, **over):
    row = {
        "ticket": ticket, "action": action,
        "mechanism": "unit_test", "why_code": "test_case",
        "written_at_utc": written or (NOW - timedelta(seconds=30)).isoformat(),
        "ttl_s": ttl_s,
    }
    if new_stop is not None:
        row["new_stop"] = new_stop
    row.update(over)
    return row


def _events(tmp_path, event=None, namespace=F5_NS):
    p = Path(tmp_path) / "shadow_logs" / "f5_minimal" / namespace / "events.jsonl"
    if not p.is_file():
        return []
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if event is None or r["event"] == event]


def _consume(owner, ee, tmp_path, now=NOW, sym="LTCUSD", sleeve="asia_pdl_fade"):
    owner._exec_engines[(sym, sleeve)] = ee
    summary = {"managed": [], "adopted": [], "closed": [], "errors": []}
    owner._f5_consume_manage_rows(summary, now)
    return summary


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def test_close_row_applies_through_the_engine_close_path(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")])
    summary = _consume(owner, ee, tmp_path)
    assert ee.closes == ["f5_manage"]
    assert ee.active_trade is None
    applied = _events(tmp_path, "f5_manage_applied")
    assert len(applied) == 1
    assert applied[0]["ticket"] == 42
    assert applied[0]["action"] == "close"
    assert applied[0]["why_code"] == "test_case"
    assert applied[0]["broker_mutation"] is True
    assert summary["f5_manage"]["applied"] == 1
    assert summary["f5_manage"]["rejected"] == 0


def test_tighten_row_applies_through_modify_sl(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)   # price 100.0/100.02
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=99.5)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == [(42, 99.5, "f5_manage_tighten")]
    assert ee.active_trade.stop_loss == 99.5                       # engine view synced
    applied = _events(tmp_path, "f5_manage_applied")
    assert len(applied) == 1
    assert applied[0]["new_stop"] == 99.5
    assert applied[0]["previous_stop"] == 99.0


def test_short_tighten_direction_semantics(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=100.0, ask=100.02))
    ee = _ManageEE(ticket=7, direction="SHORT", stop_loss=101.0)
    _write_manage(tmp_path, [_row(ticket=7, action="tighten_stop", new_stop=100.5)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == [(7, 100.5, "f5_manage_tighten")]        # 100.5 < 101 == tighter
    assert len(_events(tmp_path, "f5_manage_applied")) == 1


# ---------------------------------------------------------------------------
# reject: widen (MANDATORY tighten-only)
# ---------------------------------------------------------------------------
def test_widen_is_refused_long(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=98.0)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == []
    rejected = _events(tmp_path, "f5_manage_rejected")
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "widen_refused"
    assert rejected[0]["broker_mutation"] is False


def test_widen_is_refused_short(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="SHORT", stop_loss=101.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=102.0)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "widen_refused"


def test_equal_stop_is_a_widen_strictly(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=99.0)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "widen_refused"


def test_tighten_beyond_current_price_is_refused(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=100.0, ask=100.02))
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=100.01)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "beyond_current_price"


# ---------------------------------------------------------------------------
# reject: expired / ttl bounds
# ---------------------------------------------------------------------------
def test_expired_row_is_rejected(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close",
                                  written=(NOW - timedelta(seconds=700)).isoformat(),
                                  ttl_s=600)])
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "expired"


@pytest.mark.parametrize("ttl", [0, 59, 14401, -5])
def test_ttl_out_of_bounds_is_rejected(tmp_path, ttl):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close", ttl_s=ttl)])
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "ttl_out_of_bounds"


# ---------------------------------------------------------------------------
# reject: malformed
# ---------------------------------------------------------------------------
def test_malformed_rows_are_rejected_not_fatal(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [
        _row(ticket="not-a-ticket", action="close"),
        _row(ticket=42, action="hedge_reverse"),                     # unknown action
        _row(ticket=42, action="close", written="2026-99-99T99:99"),
        _row(ticket=42, action="tighten_stop"),                      # new_stop missing
        "not even a dict",
    ])
    _consume(owner, ee, tmp_path)
    assert ee.closes == [] and ee.modifies == []
    reasons = sorted(e["reason"] for e in _events(tmp_path, "f5_manage_rejected"))
    assert reasons == ["invalid_action", "malformed_row", "new_stop_invalid",
                       "written_at_unparseable"]


def test_corrupt_json_file_never_raises(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, None, raw="{{{ not json \x00")
    summary = _consume(owner, ee, tmp_path)                          # must not raise
    assert ee.closes == [] and ee.modifies == []
    assert summary["f5_manage"]["malformed_rows"] == 1


def test_wrong_schema_file_is_ignored(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")], schema="gtos.other.v9")
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert _events(tmp_path, "f5_manage_applied") == []


# ---------------------------------------------------------------------------
# reject: unknown ticket
# ---------------------------------------------------------------------------
def test_unknown_ticket_is_rejected_once_but_reevaluated(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=777, action="close")])
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    rejected = _events(tmp_path, "f5_manage_rejected")
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "unknown_ticket"
    # Second tick: no duplicate event spam...
    _consume(owner, ee, tmp_path)
    assert len(_events(tmp_path, "f5_manage_rejected")) == 1
    # ...but the row is still live: when the ticket appears (late adoption), it applies.
    late = _ManageEE(ticket=777)
    _consume(owner, late, tmp_path, sym="GBPJPY", sleeve="fx_jpy")
    assert late.closes == ["f5_manage"]
    assert len(_events(tmp_path, "f5_manage_applied")) == 1


# ---------------------------------------------------------------------------
# midnight boundary
# ---------------------------------------------------------------------------
def test_yesterdays_file_is_consumed_across_midnight(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    # Written 23:58 with a 10-minute TTL, consumed 00:05: actionable, from yesterday's file.
    _write_manage(tmp_path, [_row(ticket=42, action="close",
                                  written=(NOW - timedelta(minutes=7)).isoformat())],
                  day=yesterday)
    _consume(owner, ee, tmp_path)
    assert ee.closes == ["f5_manage"]
    assert len(_events(tmp_path, "f5_manage_applied")) == 1


def test_yesterdays_expired_rows_stay_expired(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    _write_manage(tmp_path, [_row(ticket=42, action="close",
                                  written=(NOW - timedelta(hours=20)).isoformat())],
                  day=yesterday)
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "expired"


# ---------------------------------------------------------------------------
# idempotence, gating, degraded paths
# ---------------------------------------------------------------------------
def test_applied_row_is_not_reapplied_next_tick(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=99.5)])
    _consume(owner, ee, tmp_path)
    _consume(owner, ee, tmp_path)
    assert ee.modifies == [(42, 99.5, "f5_manage_tighten")]        # exactly once
    assert len(_events(tmp_path, "f5_manage_applied")) == 1


def test_namespace_gated_off_for_production(tmp_path):
    owner = _owner(tmp_path, namespace="operator_profile")
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")],
                  namespace="operator_profile")
    _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert _events(tmp_path, namespace="operator_profile") == []


def test_authority_false_suppresses_and_keeps_rows_pending(tmp_path):
    owner = _owner(tmp_path, authority=False)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close")])
    summary = _consume(owner, ee, tmp_path)
    assert ee.closes == []
    assert summary["f5_manage"]["suppressed"] == "live_broker_authority_false"
    assert _events(tmp_path, "f5_manage_applied") == []
    assert _events(tmp_path, "f5_manage_rejected") == []


def test_price_unavailable_refuses_tighten(tmp_path):
    class _DarkMT5(_MT5):
        def get_tick(self, _symbol):
            return None

    owner = _owner(tmp_path, mt5=_DarkMT5())
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=99.5)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == []
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "price_unavailable"


def test_no_manage_file_is_a_silent_no_op(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    summary = _consume(owner, ee, tmp_path)
    assert "f5_manage" not in summary
    assert _events(tmp_path) == []


def test_setting_a_first_stop_on_a_stopless_position_is_a_tighten(tmp_path):
    owner = _owner(tmp_path, mt5=_MT5(bid=100.0, ask=100.02))
    ee = _ManageEE(ticket=42, direction="SHORT", stop_loss=0.0)    # no stop at all
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=101.0)])
    _consume(owner, ee, tmp_path)
    assert ee.modifies == [(42, 101.0, "f5_manage_tighten")]       # first stop != widen

# ---------------------------------------------------------------------------
# TTL default 1800 + persist cursor (2026-08-30 bind)
# ---------------------------------------------------------------------------
def test_missing_ttl_defaults_to_1800_and_applies(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    row = _row(ticket=42, action="close")
    row.pop("ttl_s")
    _write_manage(tmp_path, [row])
    _consume(owner, ee, tmp_path)
    assert ee.closes == ["f5_manage"]
    assert len(_events(tmp_path, "f5_manage_applied")) == 1


def test_unparseable_ttl_defaults_to_1800_and_applies(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close", ttl_s="soon")])
    _consume(owner, ee, tmp_path)
    assert ee.closes == ["f5_manage"]


def test_persist_cursor_survives_new_owner_no_reemit_expired(tmp_path):
    """178427810 class: expired leftover in the day file must not re-fire after restart."""
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42)
    _write_manage(tmp_path, [_row(ticket=42, action="close",
                                  written=(NOW - timedelta(seconds=700)).isoformat(),
                                  ttl_s=600)])
    _consume(owner, ee, tmp_path)
    assert _events(tmp_path, "f5_manage_rejected")[0]["reason"] == "expired"
    cursor = (Path(tmp_path) / "pipeline_state" / "ultimate_book" / F5_NS
              / "judgment" / "state" / "manage_consume_cursor.json")
    assert cursor.is_file()
    doc = json.loads(cursor.read_text(encoding="utf-8"))
    assert doc["schema"] == "gtos.judgment.manage_consume_cursor.v1"
    assert "42" in doc["tickets"]
    assert doc["tickets"]["42"]["action"] == "close"
    assert isinstance(doc.get("terminal_keys"), list) and doc["terminal_keys"]

    restarted = _owner(tmp_path)
    late = _ManageEE(ticket=42)
    _consume(restarted, late, tmp_path)
    assert late.closes == []
    rejected = _events(tmp_path, "f5_manage_rejected")
    assert len(rejected) == 1  # no second expired emit


def test_persist_cursor_survives_new_owner_no_reapply(tmp_path):
    owner = _owner(tmp_path)
    ee = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _write_manage(tmp_path, [_row(ticket=42, action="tighten_stop", new_stop=99.5)])
    _consume(owner, ee, tmp_path)
    assert len(ee.modifies) == 1
    restarted = _owner(tmp_path)
    late = _ManageEE(ticket=42, direction="LONG", stop_loss=99.0)
    _consume(restarted, late, tmp_path)
    assert late.modifies == []
    assert len(_events(tmp_path, "f5_manage_applied")) == 1
