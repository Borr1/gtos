"""A no-path initialize switches terminals. connect() must not do that.

The fake's initialize() with no path moves the login, the way a host process
did. connect() refuses that call. A reconnect that comes back on another login
is shut down, and reads and sends stay refused until a later connect proves
the launched login.
"""

import inspect
import logging
import sys
from types import SimpleNamespace

from src.mt5.mt5_real import RealMT5
from src.safety.activation_token import config_digest_for
from src.utils.broker_profile import sha256_text

RIGHT = 0
FOREIGN = 0
TERMINAL = r"C:\MT5\FTMO"
DATA = r"C:\MT5\FTMO"
EXE = r"C:\MT5\FTMO\terminal64.exe"


def _contract() -> dict:
    return {
        "broker_profile": {
            "expected_account": {
                "server": "FTMO-Server",
                "company": "FTMO Global Markets Ltd",
                "currency": "USD",
                "login_sha256": sha256_text(RIGHT),
                "terminal_path": TERMINAL,
                "terminal_data_path": DATA,
            }
        }
    }


class SwitchingMT5:
    """No-path initialize attaches the other login. A flagged initialize does too."""

    def __init__(self) -> None:
        self.login = RIGHT
        self.calls: list[dict] = []
        self.account_reads = 0
        self.sends = 0
        self.shutdowns = 0
        self.switch_next = False
        self.link_up = True

    def initialize(self, **kwargs):
        self.calls.append(dict(kwargs))
        if "path" not in kwargs or self.switch_next:
            self.login = FOREIGN
            self.switch_next = False
        else:
            self.login = RIGHT
        return True

    def account_info(self):
        self.account_reads += 1
        foreign = self.login == FOREIGN
        return SimpleNamespace(
            login=self.login,
            server="redacted_account-Server 2" if foreign else "FTMO-Server",
            company="redacted_account Ltd" if foreign else "FTMO Global Markets Ltd",
            currency="USD",
            equity=96520.44 if foreign else 93522.57,
            balance=96520.44 if foreign else 93522.57,
            margin_mode=2,
        )

    def terminal_info(self):
        return SimpleNamespace(path=TERMINAL, data_path=DATA, connected=self.link_up)

    def shutdown(self) -> None:
        self.shutdowns += 1

    def order_send(self, request):
        self.sends += 1
        return SimpleNamespace(
            retcode=10009, order=1, volume=0.01, price=1.0, comment="ok",
        )


def _adapter(monkeypatch, fake: SwitchingMT5) -> RealMT5:
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    monkeypatch.setattr(
        "src.mt5.mt5_real.enforce_broker_mutation_authorized",
        lambda *args, **kwargs: None,
    )
    real = RealMT5(terminal_path=EXE, portable=True)
    real.bind_launched_account(_contract())
    return real


def test_config_digest_does_not_hash_mt5_real_or_launcher():
    src = inspect.getsource(config_digest_for)
    assert "config_path" in src
    assert "profile_path_for" in src
    assert "mt5_real" not in src
    assert "launcher.py" not in src


def test_empty_path_is_refused_and_no_path_initialize_would_switch(monkeypatch, caplog):
    fake = SwitchingMT5()
    monkeypatch.setitem(sys.modules, "MetaTrader5", fake)
    real = RealMT5(terminal_path="  ", portable=True)
    real.bind_launched_account(_contract())
    with caplog.at_level(logging.ERROR):
        assert real.connect() is False
    assert fake.calls == []
    assert real.is_connected() is False
    assert real.identity_refused() is False
    assert "terminal path is empty" in caplog.text
    fake.initialize()
    assert fake.calls == [{}]
    assert fake.login == FOREIGN


def test_reconnect_that_lands_on_another_login_is_refused(monkeypatch, caplog):
    fake = SwitchingMT5()
    real = _adapter(monkeypatch, fake)
    assert real.connect() is True
    assert real.get_account_equity() == 93522.57
    assert fake.login == RIGHT

    fake.switch_next = True
    caplog.clear()
    with caplog.at_level(logging.ERROR):
        assert real.connect() is False
    assert real.identity_refused() is True
    assert real.is_connected() is False
    assert fake.shutdowns == 1
    assert str(RIGHT) in caplog.text
    assert str(FOREIGN) in caplog.text

    reads = fake.account_reads
    assert real.get_account_equity() == 0.0
    assert real.get_account_login() is None
    sent = real.order_send({"action": 1, "symbol": "XAUUSD", "volume": 0.01})
    assert sent.comment == "MT5 account identity refused"
    assert fake.sends == 0
    assert fake.account_reads == reads

    assert real.connect() is True
    assert real.identity_refused() is False
    assert real.get_account_equity() == 93522.57
    assert fake.login == RIGHT
    proceeded = real.order_send({"action": 1, "symbol": "XAUUSD", "volume": 0.01})
    assert proceeded.retcode == 10009
    assert fake.sends == 1


def test_right_login_proceeds(monkeypatch):
    fake = SwitchingMT5()
    real = _adapter(monkeypatch, fake)
    assert real.connect() is True
    assert real.connect() is True
    assert [call.get("path") for call in fake.calls] == [EXE, EXE]
    assert all(call.get("portable") is True for call in fake.calls)
    assert real.get_account_equity() == 93522.57
    assert real.get_account_login() == RIGHT
    proceeded = real.order_send({"action": 1, "symbol": "XAUUSD", "volume": 0.01})
    assert proceeded.retcode == 10009
    assert fake.sends == 1
    assert fake.shutdowns == 0


def test_launcher_reconnect_calls_connect():
    from src.components.ultimate_book.launcher import BookLauncher

    tick = inspect.getsource(BookLauncher.tick)
    refused = tick.find("_identity_refused")
    wake = tick.find("_wake_clock")
    body = tick.find("_tick_body")
    assert 0 <= refused < wake < body
    assert "self._mt5.connect()" in inspect.getsource(BookLauncher._tick_body)


class _Book:
    """Records the work a tick must not do while the login is wrong."""

    def __init__(self) -> None:
        self.events: list[str] = []
        self._breach_block = False
        self._namespace = "operator"
        self.base_config: dict = {}

    def run_cycle(self, **kwargs):
        self.events.extend(("generation", "admission", "placement"))
        self._f5_real_account_breach_verdict(kwargs.get("now_utc"))
        return {"ok": True, "placed": [1], "shadow": 0, "n_intents": 1, "skipped": []}

    def manage_open_positions(self, **kwargs):
        self.events.append("management")
        self._f5_real_account_breach_verdict(kwargs.get("now_utc"))
        return {"closed": [], "adopted": [], "errors": []}

    def _f5_real_account_breach_verdict(self, now):
        self.events.append("breach_verdict")
        self._breach_block = True
        return {"flatten": True}


def test_blocked_tick_only_reconnects_and_a_clean_reconnect_leaves_no_breach(tmp_path, monkeypatch):
    from src.components.ultimate_book.launcher import BookLauncher

    fake = SwitchingMT5()
    real = _adapter(monkeypatch, fake)
    assert real.connect() is True
    book = _Book()
    launcher = BookLauncher(
        book, real, lambda symbol: symbol, repo_root=str(tmp_path), tags=("crypto",),
    )
    fake.link_up = False
    fake.switch_next = True

    blocked = launcher.tick()

    assert blocked["action"] == "identity_refused"
    assert blocked["cleared"] is False
    assert real.identity_refused() is True
    assert book.events == []
    assert book._breach_block is False
    assert fake.sends == 0
    assert fake.calls[-1].get("path") == EXE

    cleared = launcher.tick()

    assert cleared["action"] == "identity_reconnected"
    assert cleared["cleared"] is True
    assert real.identity_refused() is False
    assert real.get_account_login() == RIGHT
    assert book.events == []
    assert book._breach_block is False
    assert fake.sends == 0
    assert fake.login == RIGHT
