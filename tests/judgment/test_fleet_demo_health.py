"""Demo-observer health, redacted_account targets, and Challenge event emit. No broker mutate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import importlib.util

from judgment.fleet.allowlist import FORBIDDEN_LOGINS, PlaceVeto
from judgment.fleet.book_event_emit import emit_close, emit_place
from judgment.fleet.common import DEFAULT_OUTBOX, SOURCE_LOGIN, resolve_outbox
from judgment.fleet.observer_config import fanout_targets, targeted_observers
from judgment.fleet.worker_plan import build_plan

def _load_health():
    path = REPO / "scripts" / "f5_desk" / "fleet_demo_health.py"
    spec = importlib.util.spec_from_file_location("fleet_demo_health", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


health = _load_health()
collect_health = health.collect_health
health_main = health.main

LIVE_REGISTRY = REPO / "judgment" / "fleet" / "mirror" / "registry" / "observers.v0.json"
HEALTH_SCRIPT = REPO / "scripts" / "f5_desk" / "fleet_demo_health.py"
START_PS1 = REPO / "scripts" / "f5_desk" / "vps_start_workers.ps1"
MIRROR_PS1 = REPO / "judgment" / "fleet" / "mirror" / "vps_start_workers.ps1"


def test_live_registry_includes_redacted_account_in_targets():
    payload = json.loads(LIVE_REGISTRY.read_text(encoding="utf-8"))
    targets = payload["mirror_fanout"]["targets"]
    assert targets == ["observer_sh", "observer_redacted_account", "observer_redacted_account"]
    by_id = {row["id"]: row for row in payload["observers"]}
    assert by_id["observer_redacted_account"]["demo_login"] == 1514684855
    assert "FTMO_redacted_account" in by_id["observer_redacted_account"]["terminal_dir"]
    assert by_id["observer_sh"]["demo_login"] == 0
    assert by_id["observer_redacted_account"]["demo_login"] == 0
    for row in payload["observers"]:
        assert row["demo_login"] not in FORBIDDEN_LOGINS
    assert fanout_targets(LIVE_REGISTRY) == targets
    ids = [item.id for item in targeted_observers(LIVE_REGISTRY)]
    assert ids == targets


def test_default_outbox_is_judgment_live():
    assert resolve_outbox() == DEFAULT_OUTBOX
    assert DEFAULT_OUTBOX == REPO / "judgment" / "live" / "fleet_events.jsonl"


def test_emit_place_and_close_write_outbox(tmp_path):
    outbox = tmp_path / "fleet_events.jsonl"
    placed = emit_place(ticket=293611741, symbol="XAUUSD", side="sell", sleeve="dsp", outbox=outbox)
    closed = emit_close(
        ticket=293611741,
        symbol="XAUUSD",
        side="sell",
        exit_class="orig_stop",
        outbox=outbox,
    )
    assert placed["ok"] is True
    assert closed["ok"] is True
    assert placed["place_on_challenge"] is False
    assert placed["broker_mutate"] is False
    lines = [json.loads(line) for line in outbox.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["kind"] for row in lines] == ["fill", "close"]
    assert all(row["source_login"] == SOURCE_LOGIN for row in lines)
    assert all(row["ticket"] == 293611741 for row in lines)


def test_emit_refuses_quarantine_login(tmp_path):
    with pytest.raises(PlaceVeto):
        emit_place(
            ticket=1,
            symbol="XAUUSD",
            extra={"source_login": 0, "login": 0},
            outbox=tmp_path / "x.jsonl",
        )


def test_worker_plan_starts_relay_and_three_observers():
    plan = build_plan(registry=LIVE_REGISTRY)
    assert plan["place_on_challenge"] is False
    assert plan["targets"] == ["observer_sh", "observer_redacted_account", "observer_redacted_account"]
    assert plan["relay"]["id"] == "fleet_relay"
    assert "--follow" in plan["relay"]["argv"]
    ids = [row["id"] for row in plan["workers"]]
    assert ids == ["observer_sh", "observer_redacted_account", "observer_redacted_account"]
    for row in plan["workers"]:
        assert row["demo_login"] not in FORBIDDEN_LOGINS
        assert "FTMO\\" + "terminal" not in row["terminal_path"].replace("/", "\\")
        assert "--follow" in row["argv"]
        joined = " ".join(str(part) for part in row["argv"])
        assert "0" not in joined
        assert "0" not in joined


def test_health_offline_reports_three_observers_and_redacted_account(tmp_path, monkeypatch):
    outbox = tmp_path / "fleet_events.jsonl"
    outbox.write_text(
        json.dumps(
            {
                "schema": "gtos.fleet_event.v0",
                "kind": "fill",
                "ticket": 1,
                "symbol": "XAUUSD",
                "source_login": SOURCE_LOGIN,
                "ts_utc": "2026-09-21T00:00:00Z",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(REPO)
    report = collect_health(registry=LIVE_REGISTRY, outbox=outbox, offline=True)
    assert report["place_on_challenge"] is False
    assert report["broker_mutate"] is False
    assert report["challenge_login_touched"] is False
    assert report["checklist"]["redacted_account_in_targets"] is True
    assert report["checklist"]["targets_cover_three"] is True
    assert report["checklist"]["no_challenge_login_in_observers"] is True
    ids = [row["id"] for row in report["observers"]]
    assert ids == ["observer_sh", "observer_redacted_account", "observer_redacted_account"]
    redacted_account = next(row for row in report["observers"] if row["id"] == "observer_redacted_account")
    assert redacted_account["login"] == 1514684855
    assert redacted_account["in_targets"] is True
    assert redacted_account["balance"] is None  # offline
    assert report["ok"] is True


def test_health_cli_offline_exit_zero():
    proc = subprocess.run(
        [sys.executable, str(HEALTH_SCRIPT), "--offline", "--json"],
        cwd=REPO,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO)},
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["checklist"]["redacted_account_in_targets"] is True
    assert payload["place_on_challenge"] is False


def test_health_main_refuses_challenge_observer(tmp_path):
    registry = tmp_path / "observers.json"
    registry.write_text(
        json.dumps(
            {
                "mirror_fanout": {"targets": ["bad"]},
                "observers": [
                    {
                        "id": "bad",
                        "channel": "mt5_demo",
                        "account_kind": "demo",
                        "demo_login": SOURCE_LOGIN,
                        "terminal_path": r"C:\MT5\FTMO_Trial\terminal64.exe",
                        "status": "active",
                        "place_enabled": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    code = health_main(["--offline", "--json", "--registry", str(registry)])
    assert code == 2


def test_vps_start_workers_ps1_is_supervisor_safe():
    text = START_PS1.read_text(encoding="utf-8")
    assert "Start-Process" in text
    assert "WindowStyle Hidden" in text
    assert "worker_plan.py" in text
    assert "place_on_challenge" in text
    assert "0" in text
    assert r"\MT5\FTMO\terminal" in text.replace("\\\\", "\\")
    assert MIRROR_PS1.is_file()
    assert "vps_start_workers.ps1" in MIRROR_PS1.read_text(encoding="utf-8")
