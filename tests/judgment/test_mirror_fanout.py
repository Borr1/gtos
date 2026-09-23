"""Challenge → demo fan-out PLACE. Mock MT5. Challenge login never placed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from judgment.fleet.allowlist import (
    FORBIDDEN_LOGINS,
    PlaceVeto,
    assert_demo_place_target,
    looks_like_challenge_path,
    place_veto_reason,
)
from judgment.fleet.common import SOURCE_LOGIN
from judgment.fleet.mirror_adapter import DemoMirrorAdapter, fleet_comment
from judgment.fleet.mirror_fanout import fanout_once, main as fanout_main, state_path_for
from judgment.fleet.mt5_demo import (
    ORDER_TYPE_BUY,
    ORDER_TYPE_SELL,
    TRADE_RETCODE_DONE,
    connect_demo_terminal,
)
from judgment.fleet.observer_config import Observer, parse_observer, placeable_observers

CHALLENGE_PATH = r"C:\MT5\FTMO\terminal64.exe"
TRIAL_PATH = r"C:\MT5\FTMO_Trial\terminal64.exe"
redacted_account_PATH = r"C:\MT5\FTMO_redacted_account\terminal64.exe"
redacted_account_PATH = r"C:\MT5\FTMO_redacted_account\terminal64.exe"
DEMO_NESTED_PATH = r"C:\MT5\FTMO\demo\terminal64.exe"
DEMO_LOGIN = 888001
PASSWORD_ENV = "GTOS_FLEET_DEMO_PASSWORD_FRIEND_ALEX"


class FakeMT5:
    def __init__(self, *, account_login: int = DEMO_LOGIN) -> None:
        self.account_login = account_login
        self.initialize_calls: list[dict] = []
        self.login_calls: list[int] = []
        self.order_sends: list[dict] = []
        self.shutdown_calls = 0
        self._next_ticket = 50001
        self.positions: dict[int, SimpleNamespace] = {}
        self.selected: list[str] = []

    def initialize(self, path=None, login=None, password=redacted server=None, portable=True):
        self.initialize_calls.append(
            {
                "path": path,
                "login": login,
                "password": password,
                "server": server,
                "portable": portable,
            }
        )
        return True

    def login(self, login, password=redacted server=None):
        self.login_calls.append(int(login))
        return True

    def order_send(self, request):
        payload = dict(request)
        self.order_sends.append(payload)
        ticket = self._next_ticket
        self._next_ticket += 1
        if payload.get("position"):
            self.positions.pop(int(payload["position"]), None)
            return SimpleNamespace(retcode=TRADE_RETCODE_DONE, order=ticket, deal=ticket)
        self.positions[ticket] = SimpleNamespace(
            ticket=ticket,
            symbol=payload.get("symbol"),
            type=payload.get("type"),
            volume=payload.get("volume"),
            comment=payload.get("comment"),
        )
        return SimpleNamespace(retcode=TRADE_RETCODE_DONE, order=ticket, deal=ticket)

    def positions_get(self, ticket=None, symbol=None):
        if ticket is None:
            return tuple(self.positions.values())
        pos = self.positions.get(int(ticket))
        return (pos,) if pos is not None else ()

    def symbol_select(self, symbol, enable=True):
        self.selected.append(symbol)
        return True

    def symbol_info_tick(self, symbol):
        return SimpleNamespace(ask=2650.20, bid=2650.00, symbol=symbol)

    def account_info(self):
        return SimpleNamespace(login=self.account_login)

    def shutdown(self):
        self.shutdown_calls += 1

    def last_error(self):
        return (1, "ok")


def _observer(**overrides) -> Observer:
    row = {
        "id": "friend_alex",
        "display_name": "Alex",
        "channel": "mt5_demo",
        "account_kind": "free_trial",
        "demo_login": DEMO_LOGIN,
        "server": "FTMO-Demo",
        "terminal_path": TRIAL_PATH,
        "password_env": PASSWORD_ENV,
        "status": "active",
        "place_enabled": True,
    }
    row.update(overrides)
    return parse_observer(row)


def _event(kind: str, ticket=293611741, symbol="XAUUSD", side="sell", **extra) -> dict:
    row = {
        "schema": "gtos.fleet_event.v0",
        "fleet_event_id": f"{kind}-{ticket}",
        "ts_utc": "2026-09-18T08:01:02Z",
        "kind": kind,
        "ticket": ticket,
        "symbol": symbol,
        "side": side,
        "source_login": SOURCE_LOGIN,
        "ns": "operator",
        "relay_ts_utc": "2026-09-18T08:01:03Z",
    }
    row.update(extra)
    return row


def _assert_no_challenge_place(fake: FakeMT5) -> None:
    for call in fake.initialize_calls:
        assert call["login"] not in FORBIDDEN_LOGINS
        path = str(call["path"] or "")
        assert r"\MT5\FTMO\terminal" not in path.replace("/", "\\")
    assert all(login not in FORBIDDEN_LOGINS for login in fake.login_calls)
    for request in fake.order_sends:
        assert request.get("login") not in FORBIDDEN_LOGINS
        assert request.get("comment", "").startswith("fleet:")


def test_allowlist_forbids_challenge_and_quarantine_logins():
    assert place_veto_reason(login=0, terminal_path=TRIAL_PATH, account_kind="demo") == (
        "forbidden_challenge_login"
    )
    assert place_veto_reason(login=0, terminal_path=TRIAL_PATH, account_kind="demo") == (
        "forbidden_quarantine_login"
    )
    with pytest.raises(PlaceVeto) as exc:
        assert_demo_place_target(login=SOURCE_LOGIN, terminal_path=TRIAL_PATH, account_kind="demo")
    assert exc.value.extra["place_on_challenge"] is False


def test_allowlist_challenge_path_without_markers():
    assert looks_like_challenge_path(CHALLENGE_PATH) is True
    assert looks_like_challenge_path(r"C:\MT5\FTMO") is True
    assert place_veto_reason(login=DEMO_LOGIN, terminal_path=CHALLENGE_PATH, account_kind="demo") == (
        "forbidden_challenge_path"
    )


def test_allowlist_trial_redacted_account_demo_markers():
    assert looks_like_challenge_path(TRIAL_PATH) is False
    assert looks_like_challenge_path(redacted_account_PATH) is False
    assert looks_like_challenge_path(redacted_account_PATH) is False
    assert looks_like_challenge_path(r"C:\MT5\FTMO_redacted_account") is False
    assert looks_like_challenge_path(DEMO_NESTED_PATH) is False
    assert place_veto_reason(login=DEMO_LOGIN, terminal_path=TRIAL_PATH, account_kind="free_trial") is None
    assert place_veto_reason(login=DEMO_LOGIN, terminal_path=redacted_account_PATH, account_kind="demo") is None
    assert place_veto_reason(login=DEMO_LOGIN, terminal_path=redacted_account_PATH, account_kind="free_trial") is None
    assert place_veto_reason(login=DEMO_LOGIN, terminal_path=DEMO_NESTED_PATH, account_kind="demo") is None


def test_allowlist_veto_challenge_account_kind():
    assert (
        place_veto_reason(login=DEMO_LOGIN, terminal_path=TRIAL_PATH, account_kind="ftmo_challenge")
        == "veto_challenge_copy"
    )


def test_fill_opens_mapped_micro_lot_and_comment(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, micro_lot=0.01, dry_run=False)
    adapter.connect()
    event = _event("fill", volume=2.5)
    result = adapter.sync_fill(event)
    assert result["ok"] is True
    assert result["reason"] == "opened"
    assert result["demo_ticket"] == 50001
    assert result["volume"] == 0.01
    assert result["comment"] == "fleet:293611741"
    assert result["place_on_challenge"] is False
    assert adapter.ticket_map["293611741"] == 50001
    assert len(fake.order_sends) == 1
    request = fake.order_sends[0]
    assert request["symbol"] == "XAUUSD"
    assert request["type"] == ORDER_TYPE_SELL
    assert request["volume"] == 0.01
    assert request["comment"] == fleet_comment(293611741)
    assert "position" not in request
    _assert_no_challenge_place(fake)


def test_close_closes_mapped_demo_ticket(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, dry_run=False)
    adapter.connect()
    opened = adapter.sync_fill(_event("fill"))
    closed = adapter.sync_close(_event("close"))
    assert opened["demo_ticket"] == 50001
    assert closed["ok"] is True
    assert closed["reason"] == "closed"
    assert closed["demo_ticket"] == 50001
    assert "293611741" not in adapter.ticket_map
    assert fake.order_sends[1]["position"] == 50001
    assert fake.order_sends[1]["comment"] == "fleet:293611741"
    _assert_no_challenge_place(fake)


def test_unmapped_close_skips_without_order_send():
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, dry_run=True)
    result = adapter.sync_close(_event("close", ticket=404))
    assert result["ok"] is True
    assert result["reason"] == "unmapped_close_skipped"
    assert fake.order_sends == []
    assert fake.initialize_calls == []


def test_challenge_login_never_called_for_place(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    challenge = _observer(demo_login=SOURCE_LOGIN, terminal_path=TRIAL_PATH)
    adapter = DemoMirrorAdapter(observer=challenge, mt5=fake, dry_run=False)
    result = adapter.sync_fill(_event("fill"))
    assert result["ok"] is False
    assert result["place_on_challenge"] is False
    assert result["reason"] in {"veto_challenge_copy", "forbidden_challenge_login"}
    assert fake.initialize_calls == []
    assert fake.login_calls == []
    assert fake.order_sends == []


def test_challenge_path_never_initialized(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(
        observer=_observer(terminal_path=CHALLENGE_PATH),
        mt5=fake,
        dry_run=False,
    )
    with pytest.raises(PlaceVeto) as exc:
        adapter.connect()
    assert exc.value.reason == "forbidden_challenge_path"
    assert fake.initialize_calls == []
    assert fake.order_sends == []
    fill = adapter.sync_fill(_event("fill"))
    assert fill["ok"] is False
    assert fill["reason"] == "forbidden_challenge_path"
    assert fake.order_sends == []


def test_connected_challenge_login_shuts_down(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5(account_login=SOURCE_LOGIN)
    with pytest.raises(PlaceVeto) as exc:
        connect_demo_terminal(_observer(), fake)
    assert exc.value.reason == "connected_login_forbidden"
    assert fake.shutdown_calls == 1
    assert fake.order_sends == []
    assert fake.initialize_calls[0]["login"] == DEMO_LOGIN


def test_dry_run_maps_without_order_send():
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, dry_run=True)
    opened = adapter.sync_fill(_event("fill"))
    closed = adapter.sync_close(_event("close"))
    assert opened["ok"] is True
    assert opened["demo_ticket"] == "dry:293611741"
    assert opened.get("order_send") is False
    assert closed["reason"] in {"dry_run", "closed_dry_map"}
    assert fake.order_sends == []
    assert fake.initialize_calls == []


def test_fanout_once_fill_then_close(tmp_path, monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    outbox = tmp_path / "fleet_events.jsonl"
    state = tmp_path / "mirror_state_friend_alex.json"
    with outbox.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(_event("fill")) + "\n")
        handle.write(json.dumps(_event("close")) + "\n")
        handle.write(json.dumps(_event("mfe", ticket=293540988, symbol="GBPJPY", side="buy")) + "\n")
    fake = FakeMT5()
    first = fanout_once(
        observer=_observer(),
        outbox=outbox,
        state_path=state,
        mt5=fake,
        micro_lot=0.01,
        dry_run=False,
    )
    assert first["opened"] == 1
    assert first["closed"] == 1
    assert first["place_on_challenge"] is False
    assert first["source_login"] == SOURCE_LOGIN
    assert json.loads(state.read_text())["ticket_map"] == {}
    assert [req["comment"] for req in fake.order_sends] == ["fleet:293611741", "fleet:293611741"]
    second = fanout_once(
        observer=_observer(),
        outbox=outbox,
        state_path=state,
        mt5=fake,
        dry_run=False,
    )
    assert second["handled"] == 0
    assert len(fake.order_sends) == 2
    _assert_no_challenge_place(fake)


def test_duplicate_fill_does_not_open_twice(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, dry_run=False)
    adapter.connect()
    first = adapter.sync_fill(_event("fill"))
    second = adapter.sync_fill(_event("fill"))
    assert first["reason"] == "opened"
    assert second["reason"] == "already_mapped"
    assert len(fake.order_sends) == 1


def test_buy_side_uses_buy_type(monkeypatch):
    monkeypatch.setenv(PASSWORD_ENV, "demo-secret")
    fake = FakeMT5()
    adapter = DemoMirrorAdapter(observer=_observer(), mt5=fake, dry_run=False)
    adapter.connect()
    adapter.sync_fill(_event("fill", side="buy"))
    assert fake.order_sends[0]["type"] == ORDER_TYPE_BUY


def test_placeable_observers_drop_challenge_rows(tmp_path):
    registry = {
        "observers": [
            {
                "id": "ok",
                "channel": "mt5_demo",
                "account_kind": "demo",
                "demo_login": DEMO_LOGIN,
                "terminal_path": TRIAL_PATH,
                "status": "active",
                "place_enabled": True,
            },
            {
                "id": "challenge",
                "channel": "mt5_demo",
                "account_kind": "challenge",
                "demo_login": SOURCE_LOGIN,
                "terminal_path": CHALLENGE_PATH,
                "status": "active",
                "place_enabled": True,
            },
            {
                "id": "telegram_only",
                "channel": "telegram",
                "demo_login": 777,
                "status": "active",
            },
        ]
    }
    path = tmp_path / "observers.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    rows = placeable_observers(path)
    assert [row.id for row in rows] == ["ok"]


def test_cli_dry_run_and_print_launchers(tmp_path, monkeypatch):
    monkeypatch.chdir(REPO)
    registry = tmp_path / "observers.json"
    outbox = tmp_path / "fleet_events.jsonl"
    state = tmp_path / "state.json"
    registry.write_text(
        json.dumps(
            {
                "observers": [
                    {
                        "id": "friend_alex",
                        "channel": "mt5_demo",
                        "account_kind": "free_trial",
                        "demo_login": DEMO_LOGIN,
                        "server": "FTMO-Demo",
                        "terminal_path": TRIAL_PATH,
                        "password_env": PASSWORD_ENV,
                        "status": "active",
                        "place_enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    outbox.write_text(json.dumps(_event("fill")) + "\n", encoding="utf-8")
    listed = subprocess.run(
        [
            sys.executable,
            str(REPO / "judgment/fleet/mirror_fanout.py"),
            "--print-launchers",
            "--registry",
            str(registry),
            "--dry-run",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(listed.stdout)
    assert payload["count"] == 1
    assert "--observer-id friend_alex" in payload["commands"][0]
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "judgment/fleet/mirror_fanout.py"),
            "--once",
            "--dry-run",
            "--observer-id",
            "friend_alex",
            "--registry",
            str(registry),
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
    result = json.loads(proc.stdout)
    assert result["opened"] == 1
    assert result["dry_run"] is True
    assert result["place_on_challenge"] is False
    assert json.loads(state.read_text())["ticket_map"]["293611741"] == "dry:293611741"


def test_cli_refuses_challenge_observer(tmp_path):
    registry = tmp_path / "observers.json"
    registry.write_text(
        json.dumps(
            {
                "observers": [
                    {
                        "id": "bad",
                        "channel": "mt5_demo",
                        "account_kind": "demo",
                        "demo_login": SOURCE_LOGIN,
                        "terminal_path": TRIAL_PATH,
                        "status": "active",
                        "place_enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    code = fanout_main(
        [
            "--once",
            "--dry-run",
            "--observer-id",
            "bad",
            "--registry",
            str(registry),
        ]
    )
    assert code == 2


def test_state_path_is_per_observer():
    assert state_path_for("friend_alex").name == "mirror_state_friend_alex.json"
