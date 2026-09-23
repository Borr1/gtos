"""Today's day start is the account's reset, derived from the terminal."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import src.judgment.equity_frame as equity_frame
from src.judgment.apply_size import binding_room_usd, honor_f5_scaler_risk
from src.judgment.rung_choice import open_pair
from src.judgment.unique_loader import _open_broker_positions
from src.utils.broker_clock import daily_reset_instant_utc


NOW = datetime(2026, 9, 23, 6, 38, tzinfo=timezone.utc)
RESET = "2026-09-22T22:00:00Z"


def _paths(monkeypatch, tmp_path):
    baseline = tmp_path / "chair_day_baseline.json"
    equity = tmp_path / "chair_day_equity.json"
    monkeypatch.setattr(equity_frame, "_CHAIR_BASELINE", baseline)
    monkeypatch.setattr(equity_frame, "_CHAIR_EQUITY", equity)
    return baseline, equity


def _deal(when, profit=0.0, commission=0.0, swap=0.0, fee=0.0, entry=0, position_id=1):
    return SimpleNamespace(
        time=when,
        profit=profit,
        commission=commission,
        swap=swap,
        fee=fee,
        entry=entry,
        position_id=position_id,
    )


class _Book:
    def __init__(self, balance, deals, positions):
        self._balance = balance
        self._deals = deals
        self._mt5 = SimpleNamespace(positions_get=lambda: positions)
        self.calls = 0

    def get_account_balance(self):
        self.calls += 1
        return self._balance

    def get_account_history_deals(self, _start, _end):
        return list(self._deals)


def _room(day):
    return {
        "equity": 93522.57,
        "balance": 93522.57,
        "initial_balance": 100000.0,
        "overall_loss_pct": 10.0,
        "daily_percent_external": 5.0,
        "day_start_balance": day.get("day_start_balance"),
        "day_start_equity": day.get("day_start_equity"),
        "positions_total": 0,
        "open_risk_usd": 0.0,
    }


def test_prague_reset_is_summer_then_winter_after_the_clock_change():
    summer = daily_reset_instant_utc(NOW, "Europe/Prague")
    assert summer == datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    winter_now = datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc)
    winter = daily_reset_instant_utc(winter_now, "Europe/Prague")
    assert winter == datetime(2026, 10, 25, 23, 0, tzinfo=timezone.utc)
    seam = daily_reset_instant_utc(
        datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc),
        "Europe/Prague",
    )
    assert seam == datetime(2026, 10, 24, 22, 0, tzinfo=timezone.utc)


def test_unknown_reset_rule_is_unset():
    assert daily_reset_instant_utc(NOW, "not-a-calendar") is None


def test_stale_file_is_unset_and_sends_no_cash(tmp_path, monkeypatch):
    baseline, _equity = _paths(monkeypatch, tmp_path)
    baseline.write_text(
        json.dumps({"balance": 93670.92, "reset_utc": "2026-09-21T22:00:00Z"}),
        encoding="utf-8",
    )
    day = equity_frame.read_chair_day_start(
        now=NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert day["day_start_reset_utc"] == RESET
    assert day["day_start_balance"] is None
    assert day["day_start_equity"] is None
    assert binding_room_usd(_room(day)) == (None, "unset")
    cash, _row = honor_f5_scaler_risk(
        10.0,
        trade_params=_room(day),
        login=0,
        ns="operator",
    )
    assert cash is None
    assert json.loads(baseline.read_text(encoding="utf-8"))["balance"] == 93670.92


def test_balance_operation_is_in_the_day_start_and_a_flat_book_sets_equity(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    book = _Book(
        93722.57,
        [
            _deal(reset - timedelta(hours=1), profit=999.0, position_id=0),
            _deal(reset + timedelta(hours=1), profit=200.0, position_id=0),
        ],
        [],
    )
    day = equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        login=0,
        record=True,
    )
    assert abs(day["day_start_balance"] - 93522.57) < 1e-6
    assert abs(day["day_start_equity"] - 93522.57) < 1e-6
    assert day["day_start_source"] == "derived"
    assert day["day_start_equity_source"] == "flat_across_reset"
    stored = equity_frame.read_chair_day_start(
        SimpleNamespace(get_account_balance=lambda: (_ for _ in ()).throw(AssertionError("again"))),
        NOW,
        rule_name="Europe/Prague",
        login=0,
        record=False,
    )
    assert stored["day_start_source"] == "recorded"
    assert abs(stored["day_start_balance"] - 93522.57) < 1e-6
    assert abs(stored["day_start_equity"] - 93522.57) < 1e-6


def test_a_position_open_across_the_reset_leaves_equity_unset(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    book = _Book(
        93522.57,
        [],
        [SimpleNamespace(time=reset - timedelta(minutes=5), ticket=1, symbol="EURUSD")],
    )
    day = equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert day["day_start_balance"] == 93522.57
    assert day["day_start_equity"] is None
    assert day["day_start_equity_source"] == "unset"
    assert binding_room_usd(_room(day)) == (None, "unset")
    cash, _row = honor_f5_scaler_risk(
        10.0,
        trade_params=_room(day),
        login=0,
        ns="operator",
    )
    assert cash is None


def test_unreadable_positions_leave_equity_unset(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    book = _Book(93522.57, [], None)
    day = equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert day["day_start_balance"] == 93522.57
    assert day["day_start_equity"] is None


def test_live_positions_none_is_unread_and_empty_is_flat():
    unread, ok = equity_frame.read_live_positions(SimpleNamespace(positions_get=lambda: None))
    assert unread is None and ok is False
    flat, read = equity_frame.read_live_positions(SimpleNamespace(positions_get=lambda: ()))
    assert flat == [] and read is True


def test_a_failed_positions_read_does_not_return_a_chair_ticket(tmp_path, monkeypatch):
    wake = tmp_path / "chair_wake.json"
    wake.write_text(
        json.dumps({"book": {"positions": [{"ticket": 294356559, "symbol": "GBPUSD"}]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        equity_frame,
        "read_live_positions",
        lambda raw=None: (None, False),
    )
    assert _open_broker_positions() is None
    pair = open_pair(tmp_path)
    assert pair["pair_present"] is None
    assert pair.get("ticket") is None


def test_a_live_position_wins_over_a_stale_open_record(tmp_path, monkeypatch):
    records = tmp_path / "trade_records"
    records.mkdir()
    (records / "294356559.json").write_text(
        json.dumps({"ticket": 294356559, "symbol": "GBPUSD", "status": "open"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        equity_frame,
        "read_live_positions",
        lambda raw=None: (
            [{"ticket": 1, "symbol": "EURUSD", "sleeve": "sleeve", "comment": "sleeve"}],
            True,
        ),
    )
    pair = open_pair(tmp_path)
    assert pair["pair_present"] is True
    assert pair["ticket"] == 1
    assert pair["symbol"] == "EURUSD"


def test_chair_baseline_roll_does_not_write(tmp_path):
    from scripts.f5_desk import chair_ledger

    path = tmp_path / "chair_day_baseline.json"
    assert chair_ledger.maybe_roll_baseline(path, 93522.57, NOW) is None
    assert not path.exists()
    path.write_text(
        json.dumps({"balance": 93670.92, "reset_utc": "2026-09-21T22:00:00Z"}),
        encoding="utf-8",
    )
    before = path.read_text(encoding="utf-8")
    assert chair_ledger.maybe_roll_baseline(path, 93522.57, NOW) is None
    assert path.read_text(encoding="utf-8") == before
    path.write_text(
        json.dumps({"balance": 93522.57, "reset_utc": RESET}),
        encoding="utf-8",
    )
    assert chair_ledger.maybe_roll_baseline(path, 1.0, NOW) == 93522.57
    assert chair_ledger.ftmo_reset_utc(NOW) == datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)


def test_a_missing_rule_stays_unset(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    book = _Book(93522.57, [], [])
    day = equity_frame.read_chair_day_start(book, NOW, record=False)
    assert day["day_start_reset_utc"] is None
    assert day["day_start_balance"] is None
    assert day["day_start_equity"] is None
    assert book.calls == 0


def test_broker_epoch_uses_the_server_offset(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    offset = 10800
    before = int((reset - timedelta(hours=1)).timestamp()) + offset
    after = int((reset + timedelta(hours=1)).timestamp()) + offset
    book = _Book(
        93722.57,
        [
            _deal(before, profit=999.0, position_id=0),
            _deal(after, profit=200.0, position_id=0),
        ],
        [],
    )
    book.get_broker_offset_seconds = lambda: offset
    day = equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert abs(day["day_start_balance"] - 93522.57) < 1e-6
    bare = _Book(93722.57, [_deal(after, profit=200.0, position_id=0)], [])
    missing = equity_frame.read_chair_day_start(
        bare,
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert missing["day_start_balance"] is None


def test_the_running_book_records_and_another_login_does_not(tmp_path, monkeypatch):
    state = tmp_path / "ultimate_book" / "operator" / "judgment" / "state"
    state.mkdir(parents=True)
    baseline = state / "chair_day_baseline.json"
    equity = state / "chair_day_equity.json"
    monkeypatch.setattr(equity_frame, "_CHAIR_BASELINE", baseline)
    monkeypatch.setattr(equity_frame, "_CHAIR_EQUITY", equity)
    monkeypatch.setattr(sys, "argv", ["run_book.py", "operator"])
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    book = _Book(93522.57, [], [])
    book.get_account_login = lambda: 0
    equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        login=0,
    )
    assert not baseline.exists()
    equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        login=0,
        namespace="friend_book",
    )
    assert not baseline.exists()
    equity_frame.read_chair_day_start(
        book,
        NOW,
        rule_name="Europe/Prague",
        login=0,
        namespace="operator",
    )
    stored = json.loads(baseline.read_text(encoding="utf-8"))
    assert stored["login"] == 0
    assert stored["reset_utc"] == RESET
    side = json.loads(equity.read_text(encoding="utf-8"))
    assert side["login"] == 0
    other = _Book(1.0, [], [])
    other.get_account_login = lambda: 0
    friend = equity_frame.read_chair_day_start(
        other,
        NOW,
        rule_name="Europe/Prague",
        login=0,
        namespace="operator",
    )
    assert friend["day_start_balance"] == 1.0
    assert friend["day_start_source"] == "derived"
    assert json.loads(baseline.read_text(encoding="utf-8"))["login"] == 0
    assert json.loads(baseline.read_text(encoding="utf-8"))["balance"] == 93522.57
    own = equity_frame.read_chair_day_start(
        SimpleNamespace(get_account_balance=lambda: (_ for _ in ()).throw(AssertionError("again"))),
        NOW,
        rule_name="Europe/Prague",
        login=0,
        record=False,
    )
    assert own["day_start_source"] == "recorded"
    assert own["day_start_balance"] == 93522.57
    del reset


def test_a_friend_card_does_not_read_this_accounts_file(tmp_path, monkeypatch):
    baseline, equity = _paths(monkeypatch, tmp_path)
    now = datetime.now(timezone.utc)
    reset = daily_reset_instant_utc(now, "Europe/Prague")
    assert reset is not None
    stamp = reset.strftime("%Y-%m-%dT%H:%M:%SZ")
    baseline.write_text(
        json.dumps({"login": 0, "balance": 93670.92, "reset_utc": stamp}),
        encoding="utf-8",
    )
    equity.write_text(
        json.dumps({
            "login": 0,
            "equity": 93678.44,
            "reset_utc": stamp,
            "source": "recorded_at_reset",
            "invented": False,
        }),
        encoding="utf-8",
    )
    friend = equity_frame.attach_account(
        {"identity": {"login": 0, "reset_rule": "Europe/Prague"}},
    )
    assert friend["account"]["day_start_balance"] is None
    assert friend["account"]["day_start_equity"] is None
    nameless = equity_frame.attach_account({"identity": {"reset_rule": "Europe/Prague"}})
    assert nameless["account"]["day_start_balance"] is None
    own = equity_frame.attach_account(
        {"identity": {"login": 0, "reset_rule": "Europe/Prague"}},
    )
    assert own["account"]["day_start_balance"] == 93670.92
    assert own["account"]["day_start_equity"] == 93678.44
    baseline.write_text(
        json.dumps({"balance": 93670.92, "reset_utc": stamp}),
        encoding="utf-8",
    )
    unsigned = equity_frame.attach_account(
        {"identity": {"login": 0, "reset_rule": "Europe/Prague"}},
    )
    assert unsigned["account"]["day_start_balance"] is None
    assert baseline.read_text(encoding="utf-8") == json.dumps(
        {"balance": 93670.92, "reset_utc": stamp},
    )


class _Market:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TIMEFRAME_M1 = 1
    SYMBOL_SWAP_MODE_POINTS = 1

    def __init__(self, deals, bars, info, positions):
        self._deals = deals
        self._bars = bars
        self._info = info
        self._positions = positions
        self.prices = []

    def positions_get(self):
        return list(self._positions)

    def history_deals_get(self, position=None):
        return [deal for deal in self._deals if int(deal.position_id) == int(position)]

    def copy_rates_range(self, _symbol, _timeframe, _start, _end):
        return list(self._bars)

    def symbol_info(self, _symbol):
        return self._info

    def order_calc_profit(self, order_type, _symbol, volume, price_open, price_close):
        self.prices.append(price_close)
        if order_type == self.ORDER_TYPE_BUY:
            return (price_close - price_open) * volume
        if order_type == self.ORDER_TYPE_SELL:
            return (price_open - price_close) * volume
        raise RuntimeError("pending type")


def _held_book(balance, market):
    book = _Book(balance, [], market._positions)
    book._mt5 = market
    book.get_broker_offset_seconds = lambda: 0
    return book


def _info(swap_long=0.0, swap_short=0.0, point=1.0):
    return SimpleNamespace(
        point=point,
        swap_mode=1,
        swap_long=swap_long,
        swap_short=swap_short,
        swap_rollover3days=3,
        trade_contract_size=1.0,
    )


def test_a_missing_reset_bar_leaves_equity_unset(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    opened = reset - timedelta(hours=2)
    deal = _deal(opened, entry=0, position_id=7)
    deal.price = 10.0
    deal.volume = 1.0
    deal.type = 0
    deal.symbol = "EURUSD"
    market = _Market(
        [deal],
        [{"time": int(reset.timestamp()) + 120, "high": 12.0, "low": 9.0, "spread": 0.0}],
        _info(),
        [SimpleNamespace(time=opened, ticket=7, symbol="EURUSD")],
    )
    day = equity_frame.read_chair_day_start(
        _held_book(1000.0, market),
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert day["day_start_balance"] == 1000.0
    assert day["day_start_equity"] is None
    assert binding_room_usd(_room(day)) == (None, "unset")


def test_held_equity_uses_the_higher_side_of_the_reset_bar(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    opened = reset - timedelta(hours=2)
    deal = _deal(opened, entry=0, position_id=7)
    deal.price = 10.0
    deal.volume = 2.0
    deal.type = 0
    deal.symbol = "EURUSD"
    market = _Market(
        [deal],
        [
            {"time": int(reset.timestamp()) - 60, "high": 99.0, "low": 1.0, "spread": 0.0},
            {"time": int(reset.timestamp()), "high": 12.0, "low": 9.0, "spread": 0.0},
        ],
        _info(),
        [SimpleNamespace(time=opened, ticket=7, symbol="EURUSD")],
    )
    day = equity_frame.read_chair_day_start(
        _held_book(1000.0, market),
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert market.prices == [12.0]
    assert day["day_start_equity"] == 1004.0
    assert day["day_start_equity_source"] == "reset_bar"
    room = {
        "equity": 1004.0,
        "balance": 1000.0,
        "initial_balance": 1000.0,
        "overall_loss_pct": 10.0,
        "daily_percent_external": 5.0,
        "day_start_balance": day["day_start_balance"],
        "day_start_equity": day["day_start_equity"],
        "positions_total": 0,
        "open_risk_usd": 0.0,
    }
    assert binding_room_usd(room) == (50.0, "bound")


def test_a_halted_minute_keeps_the_last_bar_and_a_short_uses_its_ask(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    opened = reset - timedelta(hours=2)
    deal = _deal(opened, entry=0, position_id=8)
    deal.price = 10.0
    deal.volume = 1.0
    deal.type = 1
    deal.symbol = "EURUSD"
    market = _Market(
        [deal],
        [{"time": int(reset.timestamp()) - 60, "high": 11.0, "low": 8.0, "spread": 5.0}],
        _info(point=0.1),
        [SimpleNamespace(time=opened, ticket=8, symbol="EURUSD")],
    )
    day = equity_frame.read_chair_day_start(
        _held_book(1000.0, market),
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert market.prices == [8.5]
    assert day["day_start_equity"] == 1001.5


def test_swap_is_included_only_after_the_server_midnight(tmp_path, monkeypatch):
    _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 21, 22, 0, tzinfo=timezone.utc)
    opened = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    deal = _deal(opened, entry=0, position_id=7)
    deal.price = 10.0
    deal.volume = 1.0
    deal.type = 0
    deal.symbol = "XAUUSD"
    market = _Market(
        [deal],
        [{"time": int(reset.timestamp()), "high": 10.0, "low": 10.0, "spread": 0.0}],
        _info(swap_long=-2.0),
        [SimpleNamespace(time=opened, ticket=7, symbol="XAUUSD")],
    )
    day = equity_frame.read_chair_day_start(
        _held_book(1000.0, market),
        reset + timedelta(hours=2),
        rule_name="Europe/Prague",
        server_offset_hours=0.0,
        record=False,
    )
    assert day["day_start_equity"] == 998.0
    later_reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    deal.time = later_reset - timedelta(hours=2)
    market._bars = [{"time": int(later_reset.timestamp()), "high": 10.0, "low": 10.0, "spread": 0.0}]
    market._positions = [SimpleNamespace(time=deal.time, ticket=7, symbol="XAUUSD")]
    later = equity_frame.read_chair_day_start(
        _held_book(1000.0, market),
        NOW,
        rule_name="Europe/Prague",
        record=False,
    )
    assert later["day_start_equity"] == 1000.0


def test_an_awake_reset_records_live_equity_and_a_record_wins(tmp_path, monkeypatch):
    baseline, equity = _paths(monkeypatch, tmp_path)
    reset = datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc)
    opened = reset - timedelta(hours=2)
    deal = _deal(opened, entry=0, position_id=7)
    deal.price = 10.0
    deal.volume = 1.0
    deal.type = 0
    deal.symbol = "EURUSD"
    market = _Market([deal], [], _info(), [SimpleNamespace(time=opened, ticket=7, symbol="EURUSD")])
    book = _held_book(1000.0, market)
    book.get_account_equity = lambda: 250.0
    day = equity_frame.read_chair_day_start(
        book,
        reset + timedelta(seconds=20),
        rule_name="Europe/Prague",
        login=0,
        record=True,
    )
    assert day["day_start_equity"] == 250.0
    assert day["day_start_equity_source"] == "awake_at_reset"
    assert json.loads(equity.read_text(encoding="utf-8"))["equity"] == 250.0
    market.prices = []

    def _refuse(*_args, **_kwargs):
        raise AssertionError("derived")

    market.copy_rates_range = _refuse
    stored = equity_frame.read_chair_day_start(
        SimpleNamespace(get_account_balance=lambda: (_ for _ in ()).throw(AssertionError("again"))),
        NOW,
        rule_name="Europe/Prague",
        login=0,
        record=False,
    )
    assert stored["day_start_source"] == "recorded"
    assert stored["day_start_equity"] == 250.0
    assert baseline.exists()
