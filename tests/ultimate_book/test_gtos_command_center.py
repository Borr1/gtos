"""Behavioural tests for `scripts/gtos_command_center.py`.

Every test here pins a BEHAVIOUR against synthetic inputs, not a source substring — a grep test
passes against a wrong implementation, and the two defects these tests exist for were both
implementations that looked right.

The two that matter most, and why:

* `test_union_not_last_record_*` — a cycle record's `tags` is the tags whose TIMEFRAME ADVANCED that
  tick (`launcher.py:328`), not the armed set. On the 2026-07-25 export the last record said 22
  (FTMO) and 10 (redacted_account) where the union said 32 for both. Under-reporting the armed set is the
  FAIL-OPEN direction wearing a clean read's clothes, so it gets a dedicated regression test.
* `test_trading_days_*` — a first cut counted trading days with `str(deal["time"])[:10]` on a field
  that is an epoch INTEGER, and reported 240 trading days over a 33-day history. The number was
  wrong by 12x and looked entirely plausible on the page.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
# NOTE: `scripts/` is never added to sys.path — see the long note in gtos_command_center.py.
# The module under test is loaded by FILE PATH for exactly that reason.
_SPEC = importlib.util.spec_from_file_location(
    "gtos_command_center", REPO / "scripts" / "gtos_command_center.py")
cc = importlib.util.module_from_spec(_SPEC)
sys.modules["gtos_command_center"] = cc
_SPEC.loader.exec_module(cc)

NOW = dt.datetime(2026, 7, 26, 6, 0, tzinfo=dt.timezone.utc)


# ---------------------------------------------------------------------------
# --tags off a running command line: the check the older pages had to ask for
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cmdline,expected_tags,expected_state", [
    ("python.exe run_book.py --namespace ftmo --poll-seconds 60", None, "absent"),
    ('python.exe run_book.py --tags "" --namespace ftmo', [], "empty"),
    ("python.exe run_book.py --tags '' --namespace ftmo", [], "empty"),
    ("python.exe run_book.py --tags crypto,energy_agri", ["crypto", "energy_agri"], "present"),
    ('python.exe run_book.py --tags "crypto,energy_agri"', ["crypto", "energy_agri"], "present"),
    ("python.exe run_book.py --tags=crypto,energy_agri", ["crypto", "energy_agri"], "present"),
    ("python.exe run_book.py --tags  crypto, energy_agri ", ["crypto"], "present"),
])
def test_tags_from_cmdline(cmdline, expected_tags, expected_state):
    tags, state = cc._tags_from_cmdline(cmdline)
    assert state == expected_state
    assert tags == expected_tags


def test_absent_and_empty_tags_are_both_fail_open_and_both_stop():
    """`--tags ""` is falsy at run_book.py:340 and silently means ALL BUILT sleeves.

    It must not read as a deliberate restriction just because the flag is present.
    """
    export = cc.Export(None)
    for cl in ("python.exe run_book.py --namespace operator_profile",
               'python.exe run_book.py --namespace operator_profile --tags ""'):
        workers = {"operator_profile": {
            "tags": cc._tags_from_cmdline(cl)[0], "tags_state": cc._tags_from_cmdline(cl)[1],
            "pids": [1], "n_processes": 1, "uptime_hours": 1.0, "started_utc": None,
            "cmdlines": [cl], "max_working_set_bytes": 0}}
        _, findings = cc.armed_panel(export, [], workers, {}, None, ["crypto"], 168.0, NOW)
        stops = [f for f in findings if f.level == cc.STOP and f.scope == "FTMO"]
        assert stops, f"an ineffective --tags must be a STOP, got nothing for {cl!r}"
        assert "whole registry" in stops[0].text


# ---------------------------------------------------------------------------
# THE headline: union over a window, never a single record
# ---------------------------------------------------------------------------
def _cycle(ts, ns, tags, tfs):
    return {"action": "cycle", "namespace": ns, "ts": ts, "tags": list(tags), "advanced_tf": tfs}


def _synthetic_log(ns="operator_profile"):
    """Two timeframes; the LAST record advances only H4 and so carries only the H4 sleeves."""
    return [
        _cycle("2026-07-25T00:00:00+00:00", ns, ["a_h4", "b_h4", "c_d1", "d_d1"], [16388, 16408]),
        _cycle("2026-07-25T04:00:00+00:00", ns, ["c_d1", "d_d1"], [16408]),
        _cycle("2026-07-25T08:00:00+00:00", ns, ["a_h4", "b_h4"], [16388]),
    ]


def test_union_not_last_record_recovers_the_full_set():
    got = cc._armed_set_from_launcher(_synthetic_log(), 168.0, NOW)["operator_profile"]
    assert got["n_union_window"] == 4
    assert got["union_window"] == ["a_h4", "b_h4", "c_d1", "d_d1"]
    # the trap, made explicit: the last record alone would have said 2
    assert got["last_record_tag_count"] == 2
    assert got["union_is_complete"] is True


def test_union_publishes_the_single_record_disagreement():
    """When per-record counts vary the page must SAY what a single-record read would have claimed."""
    export = cc.Export(None)
    panel, _ = cc.armed_panel(export, _synthetic_log(), {}, {}, None, None, 168.0, NOW)
    lu = panel["per_account"]["FTMO"]["reads"]["launcher_union"]
    assert "single_record_would_have_said" in lu
    assert "between 2 and 4" in lu["single_record_would_have_said"]


def test_union_is_a_lower_bound_when_a_timeframe_never_advanced_in_the_window():
    """The completeness condition is CHECKED, not assumed.

    A window that never saw D1 advance cannot contain the D1 sleeves, so the union is a lower bound
    and must be reported UNCHECKED rather than CLEAN.
    """
    rows = _synthetic_log()
    # window of 3 h ending at NOW sees no record at all; use a 24 h window with the D1 tick outside
    rows = [_cycle("2026-07-20T00:00:00+00:00", "operator_profile", ["c_d1"], [16408]),
            _cycle("2026-07-26T04:00:00+00:00", "operator_profile", ["a_h4"], [16388])]
    got = cc._armed_set_from_launcher(rows, 24.0, NOW)["operator_profile"]
    assert got["union_is_complete"] is False
    assert got["timeframes_missing_from_window"] == [16408]
    assert got["n_union_window"] == 1

    export = cc.Export(None)
    panel, findings = cc.armed_panel(export, rows, {}, {}, None, None, 24.0, NOW)
    lu = panel["per_account"]["FTMO"]["reads"]["launcher_union"]
    assert lu["state"] == cc.UNCHECKED
    assert lu["is_lower_bound"] is True
    assert any("LOWER BOUND" in f.text for f in findings)


def test_worker_tags_not_seen_generating_is_an_alert():
    """A tag the engine never resolved is dropped silently — registry.py:144 has no error path."""
    export = cc.Export(None)
    workers = {"operator_profile": {
        "tags": ["a_h4", "sub_xvol_pullback"], "tags_state": "present", "pids": [1],
        "n_processes": 1, "uptime_hours": 1.0, "started_utc": None, "cmdlines": [],
        "max_working_set_bytes": 0}}
    _, findings = cc.armed_panel(export, _synthetic_log(), workers, {}, None, None, 168.0, NOW)
    alerts = [f for f in findings if f.level == cc.ALERT]
    assert any("never appeared in a launcher cycle" in f.text for f in alerts)


def test_worker_tags_disagreeing_with_expected_is_a_stop():
    export = cc.Export(None)
    workers = {"operator_profile": {
        "tags": ["crypto"], "tags_state": "present", "pids": [1], "n_processes": 1,
        "uptime_hours": 1.0, "started_utc": None, "cmdlines": [], "max_working_set_bytes": 0}}
    _, findings = cc.armed_panel(export, [], workers, {}, None, ["crypto", "energy_agri"],
                                 168.0, NOW)
    assert any(f.level == cc.STOP and "not the expected armed set" in f.text for f in findings)


# ---------------------------------------------------------------------------
# trading days — the epoch-string regression
# ---------------------------------------------------------------------------
class _FakeExport:
    def __init__(self, deals):
        self._deals = deals

    def deals(self, _account):
        return self._deals


def _deal(epoch, symbol="XAUUSD", dtype=0):
    return {"time": epoch, "type": dtype, "symbol": symbol, "profit": 1.0}


def test_trading_days_counts_days_not_distinct_seconds():
    """The regression: `str(epoch)[:10]` made every distinct second a distinct 'day'.

    Six deals across two calendar days must count 2, never 6.
    """
    base = int(dt.datetime(2026, 6, 2, 12, 0, tzinfo=dt.timezone.utc).timestamp())
    deals = [_deal(base + i) for i in range(3)] + [_deal(base + 86400 + i) for i in range(3)]
    out = cc._trading_days(_FakeExport(deals), "FTMO", "FTMO-Server3", None, [])
    assert out["trading_days_state"] == cc.CLEAN
    assert out["distinct_trading_days_in_export"] == 2, \
        "six deals over two days must be two trading days"


def test_trading_days_excludes_balance_operations():
    """`type: 2` with an empty symbol is the 'Initial account balance' row, not a trading day."""
    base = int(dt.datetime(2026, 6, 2, 12, 0, tzinfo=dt.timezone.utc).timestamp())
    deals = [{"time": base, "type": 2, "symbol": "", "profit": 100000.0},
             _deal(base + 86400)]
    out = cc._trading_days(_FakeExport(deals), "FTMO", "FTMO-Server3", None, [])
    assert out["distinct_trading_days_in_export"] == 1


def test_trading_days_fails_closed_on_an_unknown_server():
    """broker_clock fails closed rather than guessing; the page must report UNCHECKED, not zero."""
    findings = []
    out = cc._trading_days(_FakeExport([_deal(1780320211)]), "FTMO", "Nope-Server-9", None, findings)
    assert out["trading_days_state"] == cc.UNCHECKED
    assert any(f.level == cc.UNCHECKED for f in findings)
    assert "distinct_trading_days_in_export" not in out


def _broker_epoch(instant_utc, server="FTMO-Server3"):
    """The epoch value MT5 stores for a deal that HAPPENED at `instant_utc`.

    A deal's `time` is a BROKER-CLOCK epoch, not a UTC one — the trap CLAUDE.md warns about
    ("never trust a `_utc` field name"), and the reason the estate routes every deal time through
    `broker_epoch_to_utc` (`w7_live_forensics.py:266`). Building the fixture the naive way — from a
    UTC timestamp — silently shifts it by the broker offset, which is how the first cut of this
    very test convinced itself the CODE was wrong.
    """
    from src.utils.broker_clock import offset_seconds_at_utc, resolve_rule
    rule = resolve_rule(server)
    return int(instant_utc.timestamp()) + offset_seconds_at_utc(instant_utc, rule)


def test_trading_days_uses_the_firms_own_reset_calendar():
    """A deal at 22:30 UTC is 00:30 CEST the NEXT day, so it is a separate FTMO trading day."""
    late_utc = dt.datetime(2026, 6, 2, 22, 30, tzinfo=dt.timezone.utc)
    early_utc = dt.datetime(2026, 6, 2, 10, 0, tzinfo=dt.timezone.utc)
    out = cc._trading_days(
        _FakeExport([_deal(_broker_epoch(early_utc)), _deal(_broker_epoch(late_utc))]),
        "FTMO", "FTMO-Server3", None, [])
    assert out["trading_day_calendar"] == "CE(S)T"
    assert out["distinct_trading_days_utc"] == 1, "both deals are 2026-06-02 in UTC"
    assert out["distinct_trading_days_in_export"] == 2, \
        "22:30 UTC is 00:30 CEST on 06-03 and is a separate FTMO trading day"


def test_deal_time_is_read_as_a_broker_epoch_not_a_utc_one():
    """Pin the convention itself: the same integer means different instants under the two readings.

    If someone ever "simplifies" `_trading_days` to `datetime.utcfromtimestamp(deal["time"])`, the
    day keys shift by the broker offset and this test fails rather than the page quietly reporting
    a different number.
    """
    instant = dt.datetime(2026, 6, 2, 23, 30, tzinfo=dt.timezone.utc)
    epoch = _broker_epoch(instant)
    naive_utc_reading = dt.datetime.fromtimestamp(epoch, dt.timezone.utc)
    assert naive_utc_reading.date().isoformat() == "2026-06-03", "the naive reading lands a day out"
    out = cc._trading_days(_FakeExport([_deal(epoch)]), "FTMO", "FTMO-Server3", None, [])
    assert out["deal_history_span_utc"][0].startswith("2026-06-02T23:30")


# ---------------------------------------------------------------------------
# phase detection — a wrong phase moves distance-to-target by thousands
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("product,phase", [
    ("redacted_account-STLR 2-Step P1- Borhen Benltaief", 1),
    ("redacted_account-STLR 2-Step P2- Borhen Benltaief", 2),
    ("$100k FTMO Challenge 2-Step", 1),
    ("Some Phase 2 Account", 2),
    (None, None),
])
def test_detect_phase(product, phase):
    got, why = cc._detect_phase(product)
    assert got == phase
    assert why


def test_ftmo_product_without_a_phase_says_it_is_assuming():
    _, why = cc._detect_phase("$100k FTMO Challenge 2-Step")
    assert "assuming phase 1" in why, "a silent phase guess is the error this string prevents"


# ---------------------------------------------------------------------------
# UNCHECKED must never collapse into CLEAN
# ---------------------------------------------------------------------------
def _args(**kw):
    base = dict(export_root=None, fills=None, conditions=str(cc.DEFAULT_CONDITIONS),
                basis=str(cc.DEFAULT_BASIS), armed_utc=None, expect_tags=None, quiet_basis=None,
                token_dir=None, phase=None, day_start_equity={}, window_hours=168.0,
                heartbeat_alert_hours=1.0, export_stale_hours=24.0,
                token_expiry_alert_hours=72.0, now_utc="2026-07-26T06:00:00Z")
    base.update(kw)
    import argparse
    return argparse.Namespace(**base)


def test_no_export_exits_3_not_0():
    """'Nothing is wrong' and 'nothing was checked' are different states."""
    page = cc.build_page(_args())
    assert page["exit_code"] == 3
    assert page["verdict"] == cc.UNCHECKED
    assert any(f["panel"] == "EXPORT" for f in page["findings"])


def test_missing_fills_makes_the_sleeve_panel_unchecked_not_clean():
    panel, findings = cc._sleeve_panel(_args())
    assert panel["state"] == cc.UNCHECKED
    assert findings and findings[0].level == cc.UNCHECKED


# ---------------------------------------------------------------------------
# the quiet alarm: a threshold without a false-alarm rate is refused
# ---------------------------------------------------------------------------
def test_quiet_threshold_without_a_false_trip_probability_is_refused():
    """FIVE_SLEEVE_OPERATOR_PAGE §S1: a floor firing 74 % of the time on a healthy sleeve is a
    coin flip wearing a threshold's clothes. An uncalibrated alarm is refused, not adopted."""
    basis = {"book_level": {"FTMO": {"warn_after_silent_weekday_sessions": 5,
                                      "alert_after_silent_weekday_sessions": 8}}}
    findings = []
    out = cc._quiet_verdict(basis, "FTMO", {"last_placed_utc": "2026-07-01T00:00:00+00:00"},
                            findings, now=dt.datetime(2026, 7, 20, tzinfo=dt.timezone.utc))
    assert out["state"] == cc.UNCHECKED
    assert "false-trip" in out["reason"]
    assert not findings, "a refused threshold must not also raise an alarm"


def test_quiet_threshold_with_a_false_trip_probability_is_adopted():
    basis = {"book_level": {"FTMO": {"warn_after_silent_weekday_sessions": 5,
                                     "alert_after_silent_weekday_sessions": 8,
                                     "alarm_false_trip_probability": {"warn": 0.05,
                                                                       "alert": 0.01},
                                     "expected_fills_per_week": 1.4}}}
    findings = []
    out = cc._quiet_verdict(basis, "FTMO",
                            {"last_placed_utc": "2026-07-01T00:00:00+00:00"}, findings,
                            now=dt.datetime(2026, 7, 13, tzinfo=dt.timezone.utc))
    assert out["state"] == cc.ALERT
    assert out["silent_weekday_sessions"] == 8
    assert findings and "1%" in findings[0].why


def test_quiet_warns_at_p95_before_the_p99_alert():
    basis = {"book_level": {"FTMO": {"warn_after_silent_weekday_sessions": 5,
                                       "alert_after_silent_weekday_sessions": 8,
                                       "alarm_false_trip_probability": {"warn": 0.05,
                                                                         "alert": 0.01}}}}
    findings = []
    out = cc._quiet_verdict(basis, "FTMO",
                            {"last_placed_utc": "2026-07-03T00:00:00+00:00"}, findings,
                            now=dt.datetime(2026, 7, 10, tzinfo=dt.timezone.utc))
    assert out["silent_weekday_sessions"] == 5
    assert out["state"] == cc.WARN
    assert findings and findings[0].level == cc.WARN


def test_quiet_is_unchecked_without_a_basis_never_clean():
    out = cc._quiet_verdict(None, "FTMO", {"last_placed_utc": "2025-01-01T00:00:00+00:00"}, [])
    assert out["state"] == cc.UNCHECKED


# ---------------------------------------------------------------------------
# readers
# ---------------------------------------------------------------------------
def test_read_json_tolerates_the_powershell_bom(tmp_path):
    """Every PowerShell-produced file in the VPS export carries a UTF-8 BOM.

    A reader that dies on it reports the whole runtime snapshot as absent, which reads as
    'nothing to see' rather than 'I could not look'.
    """
    p = tmp_path / "x.json"
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps({"a": 1}).encode())
    assert cc.read_json(p) == {"a": 1}
    assert cc.read_json(tmp_path / "missing.json") is None


def test_parse_dotnet_date():
    got = cc.parse_dotnet_date("/Date(1783151881890)/")
    assert got == dt.datetime.fromtimestamp(1783151881.890, dt.timezone.utc)
    assert cc.parse_dotnet_date(None) is None


def test_export_accepts_either_the_extracted_dir_or_its_parent(tmp_path):
    (tmp_path / "extracted" / "09_mt5_api").mkdir(parents=True)
    assert cc.Export(tmp_path).root == tmp_path / "extracted"
    assert cc.Export(tmp_path / "extracted").root == tmp_path / "extracted"
    assert cc.Export(tmp_path / "nope").root is None


def test_workers_from_processes_reads_namespace_uptime_and_tags(tmp_path):
    (tmp_path / "27_runtime_snapshot").mkdir(parents=True)
    (tmp_path / "09_mt5_api").mkdir(parents=True)
    procs = [{"Name": "python.exe", "ProcessId": 7, "CreationDate": "/Date(1783151881890)/",
              "WorkingSetSize": 10, "CommandLine":
                  "python.exe run_book.py --namespace operator_profile --tags crypto"},
             {"Name": "powershell.exe", "ProcessId": 8, "CommandLine": "run_book.py --tags nope"}]
    (tmp_path / "27_runtime_snapshot" / "processes_full.json").write_text(json.dumps(procs))
    got = cc.workers_from_processes(cc.Export(tmp_path), NOW)
    assert set(got) == {"operator_profile"}, "only the python worker is a book worker"
    row = got["operator_profile"]
    assert row["tags"] == ["crypto"] and row["uptime_hours"] > 0


# ---------------------------------------------------------------------------
# the read-only guarantee, asserted structurally
# ---------------------------------------------------------------------------
def test_the_module_imports_no_broker_module():
    """The page must be incapable of touching a broker, not merely disinclined to."""
    assert "MetaTrader5" not in sys.modules or "MetaTrader5" not in dir(cc)
    src = (REPO / "scripts" / "gtos_command_center.py").read_text()
    for forbidden in ("import MetaTrader5", "order_send", "mt5.order", "positions_get()"):
        assert forbidden not in src, f"{forbidden!r} must never appear in a read-only page"


def test_rendering_a_page_writes_nothing_by_itself(tmp_path):
    page = cc.build_page(_args())
    before = sorted(p.name for p in tmp_path.iterdir())
    cc.render_markdown(page)
    cc.render_html(page)
    assert sorted(p.name for p in tmp_path.iterdir()) == before


def test_html_is_self_contained_and_escapes_content():
    page = cc.build_page(_args())
    html = cc.render_html(page)
    assert "<style>" in html and "http://" not in html and "https://" not in html
    assert "<script" not in html.lower()


def test_importing_this_module_does_not_shadow_the_top_level_research_package():
    """Regression: putting `scripts/` on sys.path breaks `research.operations` process-wide.

    A first cut of `gtos_command_center` INSERTED `scripts/` at position 0, which made
    `research.operations...` unresolvable for every test that ran afterwards in the same process and
    silently turned two passing tests in `test_defect_register_repairs.py` into skips (they use
    `pytest.importorskip`). Appending instead did not fix it either — see below.

    The failure was invisible to this file's own tests — 61/61 green either way — and only the
    directory-wide A/B showed it, as +59 passed / +2 skipped where +61 passed was expected. That is
    the whole argument for capturing a real failure set on both sides rather than a scoped one.

    In a CLEAN SUBPROCESS on purpose. The in-process check a first cut used was over-strict and
    failed whenever another test file legitimately put `scripts/` on the path — `test_mc_firm_rules`
    and friends do, and they are entitled to, because they pre-warm `sys.modules` with the correct
    `research` package first. The invariant this module owns is not "scripts/ is never on sys.path
    in this process"; it is "importing THIS module does not put it there, and does not break
    `research.operations`". A subprocess is the only way to assert that without depending on
    collection order.
    """
    import subprocess
    import textwrap
    probe = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(REPO)!r})
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gtos_command_center", {str(REPO / "scripts" / "gtos_command_center.py")!r})
        mod = importlib.util.module_from_spec(spec)
        sys.modules["gtos_command_center"] = mod
        spec.loader.exec_module(mod)
        assert {str(REPO / "scripts")!r} not in sys.path, "importing it put scripts/ on sys.path"
        mod._load_sibling("book_sleeve_telemetry")
        assert {str(REPO / "scripts")!r} not in sys.path, "_load_sibling put scripts/ on sys.path"
        import importlib
        r = importlib.import_module(
            "research.operations.final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
            ".ultimate_book_live_package")
        assert r.__file__.startswith({str(REPO / "research")!r}), r.__file__
        print("OK")
    """)
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                         cwd=str(REPO))
    assert out.returncode == 0 and "OK" in out.stdout, (
        "importing gtos_command_center broke research.operations.\n"
        "scripts/research/ is a REGULAR package (it has __init__.py) and the repo root's research/ "
        "is a NAMESPACE package (it does not), so it wins regardless of sys.path position — "
        "appending instead of inserting is NOT a fix. Load siblings by file path.\n"
        f"stdout: {out.stdout}\nstderr: {out.stderr}")


def test_sibling_modules_load_without_touching_sys_path():
    """`_load_sibling` is the mechanism that keeps the invariant above true."""
    before = list(sys.path)
    mod = cc._load_sibling("book_sleeve_telemetry")
    assert sys.path == before, "loading a sibling must have no global side effect"
    assert hasattr(mod, "build_page")


def test_markdown_and_html_carry_the_same_words():
    """One renderer of record. Two would drift, and the estate has paid for that before."""
    page = cc.build_page(_args())
    md = cc.render_markdown(page)
    html = cc.render_html(page)
    for probe in ("GTOS command center", "The armed set", "Alive, and quiet"):
        assert probe in md and probe in html
