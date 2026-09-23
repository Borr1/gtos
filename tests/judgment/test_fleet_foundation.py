"""Feedback Fleet P0 — schema lock, normalize, relay offset, LABEL-only promote."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from judgment.fleet.common import (
    QUARANTINE_LOGINS,
    SOURCE_LOGIN,
    close_loop_miss_type,
    load_schema,
    miss_type_for_timing,
    normalize_book_row,
    validate_fleet_event,
    validate_fleet_feedback,
)
from judgment.fleet.feedback_ingest import build_row
from judgment.fleet.fleet_relay import relay_once
from judgment.fleet.mirror_adapter import DemoMirrorAdapter
from judgment.fleet.promote_feedback_to_close_loop import label_row, promote_once

FIXTURE = REPO / "judgment" / "fleet" / "fixtures" / "sample_book_event_ledger.jsonl"


def _load_fixture_rows() -> list[dict]:
    rows = []
    for line in FIXTURE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_source_and_quarantine_locks():
    lock = load_schema("schema_locks_v1.json")
    event = load_schema("fleet_event.v0.json")
    registry = load_schema("observers.v0.json")
    assert lock["login_only"] == SOURCE_LOGIN == 0
    assert lock["quarantine_logins"] == [0]
    assert event["source_login"] == SOURCE_LOGIN
    assert 0 in QUARANTINE_LOGINS
    assert registry["observers"] == []
    assert registry["ftmo_challenge_default"] == "VETO"
    assert lock["verbs"]["LABEL"] is True
    assert lock["verbs"]["place"] is False


def test_timing_map_matches_schema():
    spec = load_schema("fleet_feedback.v0.json")
    for timing, mapped in spec["maps_to_close_loop_miss_type"].items():
        assert miss_type_for_timing(timing) == mapped
    assert miss_type_for_timing("too_early") == "bad_timing"
    assert miss_type_for_timing("unclear") == "unknown"
    assert close_loop_miss_type("bad_timing") == "bad_timing"
    assert close_loop_miss_type("unknown") == "unlabeled"


def test_normalize_sample_ledger_lines():
    rows = _load_fixture_rows()
    events = [normalize_book_row(row) for row in rows]
    kept = [event for event in events if event is not None]
    tickets = [event["ticket"] for event in kept]
    kinds = [event["kind"] for event in kept]

    assert 293611741 in tickets
    assert 291072108 in tickets
    assert kinds.count("fill") == 1
    assert kinds.count("close") == 2
    assert kinds.count("mfe") == 1
    assert kinds.count("high") == 1
    assert 999 not in tickets
    assert 111 not in tickets

    first = kept[0]
    assert first["schema"] == "gtos.fleet_event.v0"
    assert first["source_login"] == SOURCE_LOGIN
    assert first["symbol"] == "XAUUSD"
    assert first["side"] == "sell"
    assert not validate_fleet_event(first)

    replay = next(event for event in kept if event["ticket"] == 291072108)
    assert replay["kind"] == "close"
    assert replay["exit_class"] == "orig_stop"
    assert replay["r_orig"] == pytest.approx(-0.9662)

    spoken = next(event for event in kept if event["ticket"] == 293540988 and event["kind"] == "mfe")
    assert spoken["symbol"] == "GBPJPY"
    assert spoken["side"] == "buy"
    assert spoken["sleeve"] == "xa_huge_20_ex"


def test_normalize_drops_quarantine_and_missing_ticket():
    assert (
        normalize_book_row(
            {"kind": "close", "ticket": 1, "symbol": "XAUUSD", "login": 0}
        )
        is None
    )
    assert normalize_book_row({"kind": "fill", "symbol": "XAUUSD", "login": SOURCE_LOGIN}) is None
    assert (
        normalize_book_row(
            {"event": "news_t15_pending_cancel", "symbol": "XAUUSD", "login": SOURCE_LOGIN}
        )
        is None
    )


def test_relay_once_offset_is_durable(tmp_path: Path):
    ledger = tmp_path / "book_event_ledger.jsonl"
    ledger.write_bytes(FIXTURE.read_bytes())
    outbox = tmp_path / "outbox.jsonl"
    state = tmp_path / "state.json"

    first = relay_once(ledger=ledger, outbox=outbox, state_path=state)
    assert first["ok"] is True
    assert first["place"] is False
    assert first["emitted"] == 5
    assert first["quarantined"] == 1
    assert first["foreign"] == 1
    assert state.is_file()
    offset = json.loads(state.read_text())["offset_bytes"]
    assert offset == ledger.stat().st_size

    second = relay_once(ledger=ledger, outbox=outbox, state_path=state)
    assert second["emitted"] == 0
    assert json.loads(state.read_text())["offset_bytes"] == offset

    extra = {
        "kind": "fill",
        "ticket": 777,
        "symbol": "ETHUSD",
        "side": "buy",
        "login": SOURCE_LOGIN,
        "ts_utc": "2026-09-18T12:00:00Z",
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(extra) + "\n")
    third = relay_once(ledger=ledger, outbox=outbox, state_path=state)
    assert third["emitted"] == 1
    lines = outbox.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 6
    assert json.loads(lines[-1])["ticket"] == 777


def test_relay_cli_once(tmp_path: Path):
    ledger = tmp_path / "book_event_ledger.jsonl"
    ledger.write_bytes(FIXTURE.read_bytes())
    outbox = tmp_path / "out.jsonl"
    state = tmp_path / "st.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "judgment/fleet/fleet_relay.py"),
            "--once",
            "--ledger",
            str(ledger),
            "--outbox",
            str(outbox),
            "--state",
            str(state),
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["emitted"] == 5
    assert payload["place"] is False


def test_feedback_and_promote_are_label_only(tmp_path: Path):
    feedback = build_row(
        observer_id="friend_alex",
        ticket="293611741",
        timing="too_early",
        symbol="XAUUSD",
        note="spike",
    )
    assert not validate_fleet_feedback(feedback)
    assert feedback["verb"] == "LABEL"
    assert feedback["place"] is False
    assert feedback["miss_type"] == "bad_timing"
    assert feedback["source_login"] == SOURCE_LOGIN

    label = label_row(feedback)
    assert label["schema"] == "gtos.close_loop.v1"
    assert label["verb"] == "LABEL"
    assert label["never_place"] is True
    assert label["place"] is False
    assert label["remint"] is False
    assert label["human_timing_vote"] == "too_early"
    assert label["miss_type"] == "bad_timing"
    assert label["close_loop_miss_type"] == "bad_timing"
    assert label["observer_ids"] == ["friend_alex"]

    unclear = label_row(build_row(observer_id="friend_alex", ticket="1", timing="unclear"))
    assert unclear["miss_type"] == "unknown"
    assert unclear["close_loop_miss_type"] == "unlabeled"

    inbox = tmp_path / "inbox.jsonl"
    labels = tmp_path / "labels.jsonl"
    state = tmp_path / "promote.json"
    inbox.write_text(json.dumps(feedback) + "\n", encoding="utf-8")
    result = promote_once(inbox=inbox, labels=labels, state_path=state)
    assert result["promoted"] == 1
    assert result["place"] is False
    again = promote_once(inbox=inbox, labels=labels, state_path=state)
    assert again["promoted"] == 0
    written = json.loads(labels.read_text(encoding="utf-8").splitlines()[0])
    assert written["verb"] == "LABEL"
    assert "place_on_observer" not in written


def test_ingest_cli(tmp_path: Path):
    inbox = tmp_path / "inbox.jsonl"
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "judgment/fleet/feedback_ingest.py"),
            "--observer-id",
            "friend_alex",
            "--ticket",
            "293540988",
            "--timing",
            "wrong_session",
            "--inbox",
            str(inbox),
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["row"]["miss_type"] == "bad_timing"
    assert payload["place"] is False


def test_mirror_adapter_refuses_challenge_and_quarantine():
    adapter = DemoMirrorAdapter(demo_login=SOURCE_LOGIN)
    assert adapter.allowed_target(SOURCE_LOGIN) is False
    assert adapter.allowed_target(0) is False
    assert adapter.allowed_target(999001) is True
    result = adapter.sync_fill(
        {"kind": "fill", "ticket": 1, "symbol": "XAUUSD", "side": "buy", "source_login": SOURCE_LOGIN}
    )
    assert result["ok"] is False
    assert result["reason"] in {"veto_challenge_copy", "forbidden_challenge_login"}
    assert result["place_on_challenge"] is False
    assert result.get("order_send") is False
