"""Daemon behavior: skip-when-unchanged, the 40-call cap, breach on garbage,
single-instance lock — over the real composer state on the real fixtures."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import timedelta

import pytest

from scripts.f5_desk import common, composer, judge_daemon, shim
from src.components.ultimate_book.judgment_layer import judgment_flow

from .conftest import FIXED_NOW, FIXTURES, build_desk_repo

posix_only = pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX fake providers")

XAU_ID = "LAUNCHER::XAUUSD::dsp_walked_high_accepted_through::2026-08-24"


def make_daemon(tmp_path, providers=None, **kw):
    root = build_desk_repo(tmp_path)
    cfg = composer.ComposerConfig(repo_root=root)
    return judge_daemon.JudgeDaemon(cfg, providers=providers, **kw)


def stub_call_fn(counter: dict, verdicts_for=XAU_ID):
    """A call_fn that answers like a well-behaved judge, counting invocations."""

    def fn(prompt, **_kw):
        counter["calls"] = counter.get("calls", 0) + 1
        match = re.search(r'"slate_id": "([0-9a-f]{16})"', prompt)
        slate_id = match.group(1) if match else "unknown"
        verdict = {
            "schema": "gtos.f5.judge.verdict.v1",
            "slate_id": slate_id,
            "verdicts": [
                {"candidate_id": verdicts_for, "verdict": "hold",
                 "mechanism": "event_proximity", "why_code": "fomc_within_ttl",
                 "confidence": 0.7},
            ] if verdicts_for else [],
            "manage": [],
            "notes": "stub",
        }
        meta = {"attempts": [{"name": "stub", "ok": True, "latency_ms": 5.0,
                              "stdout_bytes": 100, "fail_reason": None}],
                "provider": "stub"}
        return verdict, meta

    return fn


def test_skip_when_unchanged_calls_model_once(tmp_path):
    daemon = make_daemon(tmp_path)
    counter: dict = {}
    fn = stub_call_fn(counter)

    s1 = daemon.run_cycle(now=FIXED_NOW, call_fn=fn)
    assert s1["outcome"] == "judged", s1
    assert counter["calls"] == 1

    s2 = daemon.run_cycle(now=FIXED_NOW + timedelta(minutes=2), call_fn=fn)
    assert s2["outcome"] == "skipped_unchanged"
    assert counter["calls"] == 1, "unchanged candidate/open sets must not re-call the model"

    # a new fill in the stream changes the open set -> judged again
    fill = {"event": "f5_fill", "schema": "gtos.f5.minimal_size_event.v1",
            "namespace": "operator", "ticket": 424242, "symbol": "XAUUSD",
            "sleeve": "dsp_walked_high_accepted_through",
            "candidate_id": "W7_BOOK::dsp_c_walk::XAUUSD::2026-08-24::LONG::dsp_walked_high_accepted_through",
            "decision_day": "2026-08-24", "ts_utc": "2026-08-24T23:50:00+00:00"}
    with open(daemon.cfg.events_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(fill) + "\n")
    s3 = daemon.run_cycle(now=FIXED_NOW + timedelta(minutes=6), call_fn=fn)
    assert s3["outcome"] == "judged"
    assert counter["calls"] == 2


def test_judged_hold_reaches_the_real_consumer(tmp_path):
    daemon = make_daemon(tmp_path)
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn({}))
    assert s["outcome"] == "judged"
    decision = judgment_flow(XAU_ID, FIXED_NOW + timedelta(seconds=90),
                             verdict_dir=daemon.flow_dir,
                             namespace="operator", extra_row_dirs=[])
    assert decision["action"] == "HOLD"
    assert decision["why_code"] == "fomc_within_ttl"


def test_call_cap_blocks_at_40(tmp_path):
    daemon = make_daemon(tmp_path)
    common.write_json_atomic(daemon.call_counter_path,
                             {"day": common.utc_day(FIXED_NOW), "count": 40})
    counter: dict = {}
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn(counter))
    assert s["outcome"] == "skipped_call_cap"
    assert counter.get("calls") is None, "the cap must stop the call before it happens"


def test_call_cap_rolls_over_at_utc_midnight(tmp_path):
    daemon = make_daemon(tmp_path)
    common.write_json_atomic(daemon.call_counter_path, {"day": "2026-08-23", "count": 40})
    counter: dict = {}
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn(counter))
    assert s["outcome"] == "judged"
    assert counter["calls"] == 1
    cap = json.loads(daemon.call_counter_path.read_text())
    assert cap["day"] == "2026-08-24" and cap["count"] == 1


@posix_only
def test_malformed_provider_breach_and_nothing_written(tmp_path):
    daemon = make_daemon(
        tmp_path,
        providers=[{"name": "bad", "argv": ["/bin/bash", str(FIXTURES / "fake_provider_malformed.sh")]}],
    )
    s = daemon.run_cycle(now=FIXED_NOW)
    assert s["outcome"] == "verdict_unparseable"
    breach = json.loads(shim.breach_counter_path(daemon.state_dir).read_text())
    assert breach["count"] == 1 and breach["last_reason"] == "verdict_unparseable"
    assert not any(daemon.flow_dir.glob("*.json")), "no sidecar may exist after a breach"
    journal = (daemon.state_dir / f"judge_{common.utc_day(FIXED_NOW)}.jsonl").read_text()
    assert "cycle_no_verdict" in journal


@posix_only
def test_end_to_end_with_fake_cli_provider(tmp_path):
    daemon = make_daemon(
        tmp_path,
        providers=[{"name": "ok", "argv": ["/bin/bash", str(FIXTURES / "fake_provider_ok.sh")]}],
    )
    s = daemon.run_cycle(now=FIXED_NOW)
    assert s["outcome"] == "judged", s
    last = json.loads(daemon.last_judged_path.read_text())
    assert last["slate_id"] == s["slate_id"]
    # empty verdicts -> applied, nothing to write into flow, journal records it
    s2 = daemon.run_cycle(now=FIXED_NOW + timedelta(minutes=2))
    assert s2["outcome"] == "skipped_unchanged"


def test_no_material_skips_without_calling(tmp_path):
    cfg = composer.ComposerConfig(repo_root=tmp_path / "empty_repo")
    daemon = judge_daemon.JudgeDaemon(cfg)
    counter: dict = {}
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn(counter))
    assert s["outcome"] == "skipped_no_material"
    assert counter.get("calls") is None


def test_all_dark_is_counted_not_fatal(tmp_path):
    daemon = make_daemon(tmp_path)

    def dark(prompt, **_kw):
        return None, {"attempts": [{"name": "claude", "ok": False, "latency_ms": None,
                                    "stdout_bytes": 0, "fail_reason": "executable_not_found"}],
                      "provider": None}

    s = daemon.run_cycle(now=FIXED_NOW, call_fn=dark)
    assert s["outcome"] == "all_providers_dark"
    breach = json.loads(shim.breach_counter_path(daemon.state_dir).read_text())
    assert breach["count"] == 1


def test_single_instance_lock(tmp_path):
    daemon = make_daemon(tmp_path)
    assert daemon.acquire_lock() is True
    other = judge_daemon.JudgeDaemon(daemon.cfg)
    assert other.acquire_lock() is False, "a fresh lock belongs to a live instance"
    # stale lock (crashed daemon) is stolen
    old = time.time() - judge_daemon.LOCK_STALE_S - 60
    os.utime(daemon.lock_path, (old, old))
    assert other.acquire_lock() is True
    daemon.release_lock()


def test_cycle_never_raises(tmp_path, monkeypatch):
    daemon = make_daemon(tmp_path)

    def boom(*a, **kw):
        raise RuntimeError("composer exploded")

    monkeypatch.setattr(composer, "build_slate", boom)
    s = daemon.run_cycle(now=FIXED_NOW)
    assert s["outcome"].startswith("cycle_error_")


def _write_inbox(daemon, slate, now, verdict="abstain", why="no_current_named_context_mechanism"):
    inbox_dir = daemon.state_dir / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    raw = {
        "schema": "gtos.f5.judge.verdict.v1",
        "slate_id": slate["slate_id"],
        "fingerprint": slate.get("fingerprint"),
        "written_at_utc": common.iso_utc(now),
        "verdicts": [{
            "candidate_id": XAU_ID,
            "verdict": verdict,
            "mechanism": "",
            "why_code": why,
            "confidence": 0.4,
        }],
        "manage": [],
        "notes": "inbox-smoke",
    }
    (inbox_dir / "verdict.json").write_text(
        json.dumps(raw), encoding="utf-8",
    )
    return raw


def test_inbox_abstain_consumed_without_provider_call(tmp_path):
    daemon = make_daemon(tmp_path)
    slate, _ = composer.build_slate(daemon.cfg, now_utc=FIXED_NOW)
    _write_inbox(daemon, slate, FIXED_NOW)
    counter: dict = {}
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn(counter))
    assert s["outcome"] == "judged", s
    assert s["provider"] == "grok-inbox"
    assert s["inbox"] == "slate_id"
    assert counter.get("calls") is None
    decision = judgment_flow(
        XAU_ID, FIXED_NOW + timedelta(seconds=90),
        verdict_dir=daemon.flow_dir, namespace="operator", extra_row_dirs=[],
    )
    assert decision["action"] == "PASS"
    assert decision["verdict"] == "abstain"
    assert not (daemon.state_dir / "inbox" / "verdict.json").exists()
    applied = list((daemon.state_dir / "inbox" / "applied").glob("*.json"))
    assert applied, "consumed inbox must land in inbox/applied/"


def test_inbox_binds_on_fingerprint_when_clock_moves(tmp_path):
    daemon = make_daemon(tmp_path)
    slate, _ = composer.build_slate(daemon.cfg, now_utc=FIXED_NOW)
    later = FIXED_NOW + timedelta(minutes=2)
    _write_inbox(daemon, slate, later)
    s = daemon.run_cycle(now=later, call_fn=stub_call_fn({}))
    assert s["outcome"] == "judged", s
    assert s["provider"] == "grok-inbox"
    assert s["inbox"] == "fingerprint"


def test_inbox_stale_fail_open(tmp_path):
    daemon = make_daemon(tmp_path)
    slate, _ = composer.build_slate(daemon.cfg, now_utc=FIXED_NOW)
    _write_inbox(daemon, slate, FIXED_NOW - timedelta(minutes=20))
    counter: dict = {}
    s = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn(counter))
    assert s["inbox"] == "stale"
    assert counter.get("calls") == 1
    assert s["outcome"] == "judged"


def test_inbox_overrides_skip_unchanged(tmp_path):
    daemon = make_daemon(tmp_path)
    s1 = daemon.run_cycle(now=FIXED_NOW, call_fn=stub_call_fn({}))
    assert s1["outcome"] == "judged"
    later = FIXED_NOW + timedelta(minutes=2)
    slate2, _ = composer.build_slate(daemon.cfg, now_utc=later)
    last = common.read_json(daemon.last_judged_path)
    assert slate2["fingerprint"] == last["fingerprint"]
    _write_inbox(daemon, slate2, later, why="spread_normalized")
    counter: dict = {}
    s2 = daemon.run_cycle(now=later, call_fn=stub_call_fn(counter))
    assert s2["outcome"] == "judged", s2
    assert s2["provider"] == "grok-inbox"
    assert counter.get("calls") is None
