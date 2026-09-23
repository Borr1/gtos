"""Judgment-layer seam fixes (2026-08-25): fail-closed freshness, midnight survival,
date-bounded row scans, anchored default directory.

The one fail-closed path in the flow consume is the HOLD freshness law: a HOLD row that
cannot prove it is current must NOT bind. Before this fix a HOLD with a mangled
written_at_utc (or ttl_s <= 0) was treated as eternally fresh -- a bot bug became a
standing veto that killed every fire and no TTL could clear it.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.components.ultimate_book.judgment_layer import (
    VERDICT_ABSENT,
    VERDICT_RESCUE,
    _default_verdict_dir,
    _entry_fresh,
    judgment_flow,
    judgment_verdict,
    verdict_filename,
)

NOW = datetime(2026, 8, 25, 0, 3, 0, tzinfo=timezone.utc)
NS = "operator"
CID = "W7_BOOK::liquidity_sweep::LTCUSD::2026-08-24::LONG::asia_pdl_fade"


def _flow(tmp_path, now=NOW, cid=CID):
    return judgment_flow(cid, now, verdict_dir=tmp_path, namespace=NS, extra_row_dirs=[])


def _write_sidecar(tmp_path, day, entry, cid=CID):
    path = Path(tmp_path) / f"flow_{day}.json"
    path.write_text(json.dumps({cid: entry}), encoding="utf-8")
    return path


def _write_hedge_rows(tmp_path, rows, name="judgment_bot.jsonl"):
    d = Path(tmp_path) / "rows"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return p


def _hold_row(written_at, ttl_s=600, cid=CID):
    return {
        "schema_version": "gtos.debate.judgment.v1",
        "role": "JUDGMENT",
        "join_key": cid,
        "verdict": "veto",
        "why_code": "thin_hour",
        "written_at_utc": written_at,
        "ttl_s": ttl_s,
        "namespace": NS,
    }


# ---------------------------------------------------------------------------
# 1. _entry_fresh is fail-closed on a broken clock
# ---------------------------------------------------------------------------
def test_entry_fresh_unparseable_written_at_is_not_fresh():
    assert _entry_fresh({"written_at_utc": "not-a-time", "ttl_s": 600}, NOW, 600.0) is False


def test_entry_fresh_absent_written_at_is_not_fresh():
    assert _entry_fresh({"ttl_s": 600}, NOW, 600.0) is False


def test_entry_fresh_nonpositive_ttl_is_not_fresh():
    written = (NOW - timedelta(seconds=5)).isoformat()
    assert _entry_fresh({"written_at_utc": written, "ttl_s": 0}, NOW, 600.0) is False
    assert _entry_fresh({"written_at_utc": written, "ttl_s": -30}, NOW, 600.0) is False


def test_entry_fresh_true_inside_ttl():
    written = (NOW - timedelta(seconds=120)).isoformat()
    assert _entry_fresh({"written_at_utc": written, "ttl_s": 600}, NOW, 600.0) is True


# ---------------------------------------------------------------------------
# 2. THE IMPORTANT TEST: a HOLD row with a mangled timestamp consumes as PASS
# ---------------------------------------------------------------------------
def test_hold_row_with_mangled_timestamp_is_pass_not_a_forever_veto(tmp_path):
    _write_hedge_rows(tmp_path, [_hold_row("2026-13-45T99:99:99")])
    decision = _flow(tmp_path)
    assert decision["action"] == "PASS"
    assert decision["reason"] == "stale_hold_row"


def test_hold_row_with_no_timestamp_is_pass(tmp_path):
    row = _hold_row("x")
    del row["written_at_utc"]
    _write_hedge_rows(tmp_path, [row])
    assert _flow(tmp_path)["action"] == "PASS"


def test_hold_row_with_zero_ttl_is_pass(tmp_path):
    _write_hedge_rows(tmp_path, [_hold_row((NOW - timedelta(seconds=5)).isoformat(), ttl_s=0)])
    assert _flow(tmp_path)["action"] == "PASS"


def test_fresh_hold_row_still_holds(tmp_path):
    _write_hedge_rows(tmp_path, [_hold_row((NOW - timedelta(seconds=30)).isoformat())])
    decision = _flow(tmp_path)
    assert decision["action"] == "HOLD"
    assert decision["verdict"] == "veto"


def test_sidecar_hold_with_mangled_timestamp_is_skipped_to_pass(tmp_path):
    _write_sidecar(tmp_path, NOW.date().isoformat(), {
        "action": "HOLD", "verdict": "veto", "why_code": "x",
        "written_at_utc": "garbage", "ttl_s": 600, "namespace": NS,
    })
    assert _flow(tmp_path)["action"] == "PASS"


# ---------------------------------------------------------------------------
# 3. midnight: today AND yesterday are read, TTL still binding
# ---------------------------------------------------------------------------
def test_sidecar_written_before_midnight_survives_the_day_roll(tmp_path):
    yesterday = (NOW - timedelta(days=1)).date().isoformat()   # row day 2026-08-24
    written = (NOW - timedelta(minutes=4)).isoformat()          # 23:59 the previous day
    _write_sidecar(tmp_path, yesterday, {
        "action": "HOLD", "verdict": "veto", "why_code": "x",
        "written_at_utc": written, "ttl_s": 600, "namespace": NS,
    })
    decision = _flow(tmp_path)                                  # consumed at 00:03
    assert decision["action"] == "HOLD"


def test_yesterday_sidecar_past_ttl_is_still_stale(tmp_path):
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    written = (NOW - timedelta(hours=3)).isoformat()
    _write_sidecar(tmp_path, yesterday, {
        "action": "HOLD", "verdict": "veto", "why_code": "x",
        "written_at_utc": written, "ttl_s": 600, "namespace": NS,
    })
    assert _flow(tmp_path)["action"] == "PASS"


def test_todays_sidecar_wins_over_yesterdays(tmp_path):
    written = (NOW - timedelta(minutes=2)).isoformat()
    _write_sidecar(tmp_path, NOW.date().isoformat(), {
        "action": "APPROVE", "verdict": "approve", "why_code": "today",
        "written_at_utc": written, "ttl_s": 600, "namespace": NS,
    })
    _write_sidecar(tmp_path, (NOW - timedelta(days=1)).date().isoformat(), {
        "action": "HOLD", "verdict": "veto", "why_code": "yesterday",
        "written_at_utc": written, "ttl_s": 600, "namespace": NS,
    })
    decision = _flow(tmp_path)
    assert decision["action"] == "APPROVE"
    assert decision["why_code"] == "today"


def test_judgment_verdict_reads_yesterdays_file_ttl_binding(tmp_path):
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    fresh_written = (NOW - timedelta(minutes=4)).isoformat()
    (Path(tmp_path) / verdict_filename(yesterday)).write_text(json.dumps({
        CID: {"verdict": "RESCUE", "role": "COST", "why_code": "x",
              "written_at_utc": fresh_written, "ttl_s": 600, "namespace": NS},
    }), encoding="utf-8")
    assert judgment_verdict(CID, NOW, verdict_dir=tmp_path, namespace=NS) == VERDICT_RESCUE
    # …and the same entry past its TTL is ABSENT even though the file is found.
    stale_written = (NOW - timedelta(hours=2)).isoformat()
    (Path(tmp_path) / verdict_filename(yesterday)).write_text(json.dumps({
        CID: {"verdict": "RESCUE", "role": "COST", "why_code": "x",
              "written_at_utc": stale_written, "ttl_s": 600, "namespace": NS},
    }), encoding="utf-8")
    assert judgment_verdict(CID, NOW, verdict_dir=tmp_path, namespace=NS) == VERDICT_ABSENT


def test_judgment_verdict_corrupt_today_falls_through_to_yesterday(tmp_path):
    (Path(tmp_path) / verdict_filename(NOW.date().isoformat())).write_text(
        "{not json", encoding="utf-8")
    yesterday = (NOW - timedelta(days=1)).date().isoformat()
    (Path(tmp_path) / verdict_filename(yesterday)).write_text(json.dumps({
        CID: {"verdict": "RESCUE", "role": "COST", "why_code": "x",
              "written_at_utc": (NOW - timedelta(minutes=1)).isoformat(),
              "ttl_s": 600, "namespace": NS},
    }), encoding="utf-8")
    assert judgment_verdict(CID, NOW, verdict_dir=tmp_path, namespace=NS) == VERDICT_RESCUE


# ---------------------------------------------------------------------------
# 4. the row scan is bounded by date
# ---------------------------------------------------------------------------
def test_row_scan_skips_files_older_than_the_bound(tmp_path):
    p = _write_hedge_rows(tmp_path, [_hold_row((NOW - timedelta(seconds=30)).isoformat())])
    old = time.time() - 60 * 86400
    os.utime(p, (old, old))
    # The row inside is textually fresh, but a file untouched for 60 days cannot hold a
    # consumable row under the TTL law -- the scan must not even read it.
    assert _flow(tmp_path, now=datetime.now(timezone.utc))["action"] == "PASS"


def test_row_scan_reads_recent_files(tmp_path):
    now = datetime.now(timezone.utc)
    _write_hedge_rows(tmp_path, [_hold_row((now - timedelta(seconds=30)).isoformat())])
    assert _flow(tmp_path, now=now)["action"] == "HOLD"


# ---------------------------------------------------------------------------
# 5. no cwd-relative default directory
# ---------------------------------------------------------------------------
def test_default_verdict_dir_is_anchored_not_cwd_relative(tmp_path, monkeypatch):
    d = _default_verdict_dir()
    assert d.is_absolute()
    # Anchored on the repo root that owns this module, so a cwd change moves nothing.
    import src.components.ultimate_book.judgment_layer as jl
    assert d == Path(jl.__file__).resolve().parents[3] / "judgment"
    monkeypatch.chdir(tmp_path)
    assert _default_verdict_dir() == d


# ---------------------------------------------------------------------------
# 6. never raises
# ---------------------------------------------------------------------------
def test_flow_never_raises_on_corrupt_everything(tmp_path):
    (Path(tmp_path) / f"flow_{NOW.date().isoformat()}.json").write_text("{{{", encoding="utf-8")
    d = Path(tmp_path) / "rows"
    d.mkdir()
    (d / "judgment_bot.jsonl").write_text("not json at all\n\x00\x01", encoding="utf-8")
    decision = _flow(tmp_path)
    assert decision["action"] == "PASS"
