"""The funnel reader anchors on timestamps and stays read-only."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load():
    path = Path(__file__).resolve().parents[2] / "scripts" / "flow_trace.py"
    spec = importlib.util.spec_from_file_location("flow_trace", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["flow_trace"] = module
    spec.loader.exec_module(module)
    return module


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _tree(root: Path) -> Path:
    ns = "book_alpha"
    state = root / "pipeline_state" / "ultimate_book" / ns / "judgment"
    logs = root / "shadow_logs"
    state.mkdir(parents=True)
    logs.mkdir()
    early = "2026-09-23T03:45:00.100000+00:00"
    late = "2026-09-23T04:00:00.100000+00:00"
    # Completion order is not start order. The later cycle is written first.
    launcher = [
        {
            "ts": late,
            "action": "cycle",
            "namespace": ns,
            "n_intents": 1,
            "placed": [],
            "skipped": [
                {
                    "symbol": "EURUSD",
                    "sleeve": "sample_sleeve",
                    "decision_bar_iso": "2026-09-23T04:00:00+00:00",
                    "reason": "stale_late_entry_after_restart",
                },
                {
                    "symbol": "GBPUSD",
                    "sleeve": "sample_sleeve",
                    "decision_bar_iso": "2026-09-23T04:00:00+00:00",
                    "reason": "stale_late_entry_after_restart",
                },
            ],
            "reason": "admitted_book_authority+terminals:unit_unset=1,candidate_emitted=1",
            "bridge": {
                "decision_status": "admitted_book_authority",
                "reason": "ok",
                "would_new_entries_allowed": True,
                "would_total_risk_pct": 0.014,
                "would_units": [{
                    "sized": True,
                    "reason": "sized",
                    "risk_pct_per_trade": 0.014,
                }],
                "realized_units": [],
                "governor": {"allow": True, "reason": "ok"},
            },
        },
        {
            "ts": early,
            "action": "cycle",
            "namespace": ns,
            "n_intents": 0,
            "placed": [],
            "skipped": [],
            "reason": "no_candidates_this_bar",
            "bridge": {"decision_status": "blocked_by_governor", "reason": "KEEP"},
        },
    ]
    _write_jsonl(logs / "ultimate_book_launcher.jsonl", launcher)
    _write_jsonl(state / "pipeline_choices.jsonl", [
        {
            "logged_at_utc": "2026-09-23T03:45:10Z",
            "question": "last_bar",
            "choice": None,
            "error": "WriteError",
            "login": 100000001,
            "spot": "EURUSD|15",
        },
        {
            "logged_at_utc": "2026-09-23T04:00:10Z",
            "question": "closed_series",
            "choice": None,
            "error": "LocalProtocolError",
            "login": 100000001,
        },
        {
            "logged_at_utc": "2026-09-23T04:00:11Z",
            "question": "placement_brake",
            "choice": "brake_off",
            "error": "JSONDecodeError",
        },
    ])
    _write_jsonl(state / "book_engine_choices.jsonl", [
        {
            "logged_at_utc": "2026-09-23T04:00:12Z",
            "question": "include_clean3",
            "choice": "include",
            "error": None,
        },
        {
            "logged_at_utc": "2026-09-23T04:00:20Z",
            "question": "unit",
            "choice": None,
            "error": "ReadError",
            "spot": "EURUSD",
        },
        {
            "logged_at_utc": "2026-09-23T03:45:20Z",
            "question": "unit",
            "choice": "unit_long",
            "error": None,
        },
    ])
    _write_jsonl(state / "execution_choices.jsonl", [
        {
            "logged_at_utc": "2026-09-23T04:00:25Z",
            "question": "lot",
            "choice": "block",
            "error": "timeout",
            "symbol": "EURUSD",
            "reason": "empty_score",
        }
    ])
    _write_jsonl(state / "manage_choices.jsonl", [
        {
            "logged_at_utc": "2026-09-23T04:00:40Z",
            "act": "move_sl",
            "choice": "move_sl",
            "send": False,
            "symbol": "EURUSD",
            "error": None,
        },
        {
            "logged_at_utc": "2026-09-23T04:00:41Z",
            "act": "move_tp",
            "choice": "move_sl",
            "send": False,
            "symbol": "EURUSD",
            "error": None,
        }
    ])
    _write_jsonl(state / "place_path_choices.jsonl", [])
    _write_jsonl(logs / "f5_minimal" / ns / "events.jsonl", [
        {
            "ts_utc": "2026-09-23T04:00:15Z",
            "event": "f5_slate",
            "namespace": ns,
            "intents": [{
                "sleeve": "sample_sleeve",
                "symbol": "EURUSD",
                "direction": 1,
                "entry_price": "25608.09",
                "stop_dist": 0.01,
                "target_dist": None,
                "lot": None,
            }],
        },
        {
            "ts_utc": "2026-09-23T04:00:50Z",
            "event": "position_filled",
            "namespace": ns,
            "symbol": "EURUSD",
        },
    ])
    audit = root / "activation_audit.jsonl"
    _write_jsonl(audit, [
        {
            "decided_at_utc": "2026-09-23T04:00:32Z",
            "namespace": ns,
            "allowed": False,
            "reason": "exposure_increasing_new_deal",
            "risk_direction": "increasing",
            "classification": "exposure_increasing_new_deal",
            "account_login_sha256": "abc",
            "request_summary": {"symbol": "EURUSD", "volume": 0.1},
        },
        {
            "decided_at_utc": "2026-09-23T04:00:33Z",
            "namespace": ns,
            "allowed": True,
            "reason": "risk_reducing_position_close",
            "risk_direction": "reducing",
            "classification": "risk_reducing_position_close",
        },
    ])
    log = logs / "f5_verification.log"
    text = "\n".join([
        "2026-09-23 04:00:30,100 INFO order_check retcode=10013",
        "Traceback (most recent call last): order_check retcode=1",
        "not a timestamp order_send retcode=99999",
        "2026-09-23 04:00:31,100 INFO order_send retcode=10009",
        "2026-09-23 03:45:30,100 INFO order_check retcode=10018",
    ])
    log.write_bytes(text.encode("utf-16-le"))
    return audit


def test_latest_cycle_is_the_latest_start_not_the_last_line(tmp_path, capsys):
    audit = _tree(tmp_path)
    module = _load()
    code = module.main([
        "--repo", str(tmp_path),
        "--namespace", "book_alpha",
        "--activation-audit", str(audit),
        "--tail-bytes", "0",
    ])
    text = capsys.readouterr().out
    assert code == 0
    assert "cycle=2026-09-23T04:00:00.100000+00:00" in text
    assert "cycle=2026-09-23T03:45:00.100000+00:00" not in text
    assert "[pipeline closed_series]\ncount=1" in text
    assert "LocalProtocolError=1" in text
    assert "JSONDecodeError=1" in text
    assert "[pipeline last_bar]\ncount=0" in text
    assert "[book unit]\ncount=1" in text
    assert "ReadError=1" in text
    assert "fired=1" in text
    assert "not_fired=1" in text
    assert "side=present:1 unset:0" in text
    assert "lot=present:0 unset:1" in text
    assert "target=present:0 unset:1" in text
    assert "stale_late_entry_after_restart=2" in text
    assert "25608.09" in text
    assert "risk_pct_per_trade=0.014" in text
    assert "choice:block=1" in text
    assert "[order_check]\ncount=1" in text
    assert "retcodes=10013" in text
    assert "retcodes=10009" in text
    assert "audit_increasing=1" in text
    assert "[order_send]\ncount=2" in text
    assert "100000001" not in text
    assert "position_filled" in text
    assert "[management move_sl]\ncount=1" in text
    assert "[management move_tp]\ncount=1" in text
    assert "[management close]\ncount=0" in text
    assert "elapsed_s=" in text
    for name in ("WriteError", "LocalProtocolError", "ReadError", "JSONDecodeError", "timeout"):
        assert name in text


def test_since_keeps_each_cycle_in_its_own_window(tmp_path, capsys):
    audit = _tree(tmp_path)
    module = _load()
    code = module.main([
        "--repo", str(tmp_path),
        "--namespace", "book_alpha",
        "--activation-audit", str(audit),
        "--since", "2026-09-23T03:45:00Z",
        "--tail-bytes", "0",
    ])
    text = capsys.readouterr().out
    assert code == 0
    assert text.index("cycle=2026-09-23T03:45:00.100000+00:00") < text.index(
        "cycle=2026-09-23T04:00:00.100000+00:00"
    )
    early, late = text.split("cycle=2026-09-23T04:00:00.100000+00:00", 1)
    assert "[order_check]\ncount=1" in early
    assert "retcodes=10018" in early
    assert "retcodes=10013" not in early
    assert "[pipeline last_bar]\ncount=1" in early
    assert "held=1" in early
    assert "[order_check]\ncount=1" in late
    assert "retcodes=10013" in late


def test_missing_cycle_exits_2(tmp_path, capsys):
    audit = _tree(tmp_path)
    module = _load()
    code = module.main([
        "--repo", str(tmp_path),
        "--namespace", "book_alpha",
        "--activation-audit", str(audit),
        "--cycle-start", "2026-09-23T01:00:00Z",
        "--tail-bytes", "0",
    ])
    text = capsys.readouterr().out
    assert code == 2
    assert "no cycle" in text
