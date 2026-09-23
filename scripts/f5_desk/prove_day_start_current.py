"""Read-only proof of the Challenge day start. Does not send and does not write.

Attach with the Challenge terminal path only. Login is checked before any
number is printed as the Challenge. The only terminal reads are
positions_get, orders_get, history_deals_get, account_info, and
order_calc_profit.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

TERMINAL = r"C:\MT5\FTMO\terminal64.exe"
CHALLENGE_LOGIN = 0
LIVE_REPO = Path(r"host-local\redacted_host\repo")
STATE = (
    LIVE_REPO
    / "pipeline_state"
    / "ultimate_book"
    / "operator"
    / "judgment"
    / "state"
)
JUDGMENT = STATE.parent
NEEDLE = "96520.44"
HERE = Path(__file__).resolve().parent


def _load(name, path, package=None):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if package:
        module.__package__ = package
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _stub(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _yaml_fact(text, key):
    prefix = key + ":"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped[len(prefix):].strip().strip("'\"")
            return value or None
    return None


def _print_file(path: Path) -> None:
    print("FILE", path)
    if not path.is_file():
        print("missing")
        return
    try:
        stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError as exc:
        print("unreadable", type(exc).__name__)
        return
    print("mtime_utc", stamp.strftime("%Y-%m-%dT%H:%M:%SZ"))
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print("unreadable", type(exc).__name__)
        return
    print(text[:4000])


def _scan_needle() -> None:
    print("NEEDLE", NEEDLE)
    roots = [JUDGMENT, STATE]
    seen = set()
    for root in roots:
        if not root.is_dir():
            print("missing_dir", root)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            name = path.name.lower()
            interesting = (
                name.startswith("equity_")
                or "equity" in name
                or name in {
                    "parameter_outcomes.jsonl",
                    "chair_wake.json",
                    "chair_health.json",
                    "chair_day_baseline.json",
                    "chair_day_equity.json",
                }
            )
            if not interesting:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError as exc:
                print("scan_unreadable", path, type(exc).__name__)
                continue
            hit = NEEDLE in text
            print(
                "scan",
                path,
                "mtime_utc",
                stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "contains_96520.44",
                hit,
            )


def _pending_risk(mt5, orders):
    calc = getattr(mt5, "order_calc_profit", None)
    if not callable(calc):
        return None
    buy_orders = []
    sell_orders = []
    for name in (
        "ORDER_TYPE_BUY",
        "ORDER_TYPE_BUY_LIMIT",
        "ORDER_TYPE_BUY_STOP",
        "ORDER_TYPE_BUY_STOP_LIMIT",
    ):
        value = getattr(mt5, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            buy_orders.append(value)
    for name in (
        "ORDER_TYPE_SELL",
        "ORDER_TYPE_SELL_LIMIT",
        "ORDER_TYPE_SELL_STOP",
        "ORDER_TYPE_SELL_STOP_LIMIT",
    ):
        value = getattr(mt5, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            sell_orders.append(value)
    total = 0.0
    for order in orders:
        symbol = getattr(order, "symbol", None)
        try:
            volume = float(getattr(order, "volume_current", 0) or 0)
            price = float(getattr(order, "price_open", 0) or 0)
            stop = float(getattr(order, "sl", 0) or 0)
        except (TypeError, ValueError):
            return None
        side = getattr(order, "type", None)
        buy = getattr(mt5, "ORDER_TYPE_BUY", 0)
        sell = getattr(mt5, "ORDER_TYPE_SELL", 1)
        if side in buy_orders:
            order_type = buy
        elif side in sell_orders:
            order_type = sell
        else:
            return None
        if side in (
            getattr(mt5, "ORDER_TYPE_BUY_STOP_LIMIT", None),
            getattr(mt5, "ORDER_TYPE_SELL_STOP_LIMIT", None),
        ):
            try:
                price = float(getattr(order, "price_stoplimit", 0) or 0)
            except (TypeError, ValueError):
                return None
        if not symbol or volume <= 0 or price <= 0 or stop <= 0:
            return None
        try:
            pnl = float(calc(order_type, symbol, volume, price, stop))
        except Exception:
            return None
        if pnl != pnl or pnl in (float("inf"), float("-inf")):
            return None
        if pnl < 0:
            total += -pnl
    return total


def _beside(name: str, repo_path: str) -> Path:
    sibling = HERE / name
    if sibling.is_file():
        return sibling
    return HERE.parents[1] / repo_path


def _load_modules():
    src = types.ModuleType("src")
    src.__path__ = []
    utils = types.ModuleType("src.utils")
    utils.__path__ = []
    sys.modules["src"] = src
    sys.modules["src.utils"] = utils
    clock = _load("src.utils.broker_clock", _beside("broker_clock.py", "src/utils/broker_clock.py"))
    sys.modules["src.utils.broker_clock"] = clock
    frame = _load("prove_equity_frame", _beside("equity_frame.py", "src/judgment/equity_frame.py"))
    frame._CHAIR_BASELINE = STATE / "chair_day_baseline.json"
    frame._CHAIR_EQUITY = STATE / "chair_day_equity.json"
    _stub(
        "src.judgment.compose",
        COST_TILT_MAX=0,
        COST_TILT_MIN=0,
        TILT_MAX=0,
        TILT_MIN=0,
        compose_shadow=lambda *_a, **_k: None,
    )
    _stub(
        "src.judgment.host_events",
        as_of_from_state=lambda *_a, **_k: None,
        coerce_as_of_utc=lambda *_a, **_k: None,
        news_inventory_extra=lambda *_a, **_k: None,
    )
    _stub(
        "src.judgment.process_lock",
        CA_TILT_MAX=0,
        CA_TILT_MIN=0,
        WIRE_CA_SIZE=None,
        WIRE_COST=None,
        WIRE_FLOW=None,
        leave_orig_ticket=lambda *_a, **_k: False,
        stamp_lock=lambda *_a, **_k: None,
        wire_apply_open=lambda *_a, **_k: None,
    )
    apply_size = _load(
        "prove_apply_size",
        _beside("apply_size.py", "src/judgment/apply_size.py"),
        package="src.judgment",
    )
    return clock, frame, apply_size


class _Shim:
    """Adapter over an already-open terminal. history_deals_get only, no tick."""

    def __init__(self, mt5, info, offset_seconds):
        self._mt5 = mt5
        self._info = info
        self._offset = int(offset_seconds)
        self.deals = None

    def get_account_balance(self):
        return getattr(self._info, "balance", None)

    def get_broker_offset_seconds(self):
        return self._offset

    def get_account_history_deals(self, from_date, to_date):
        query_from = from_date + timedelta(seconds=self._offset)
        query_to = to_date + timedelta(seconds=self._offset)
        deals = self._mt5.history_deals_get(query_from, query_to)
        if deals is None:
            self.deals = None
            return None
        rows = []
        for deal in deals:
            rows.append(
                {
                    "position_id": getattr(deal, "position_id", 0),
                    "entry": getattr(deal, "entry", 0),
                    "time": int(deal.time),
                    "profit": getattr(deal, "profit", None),
                    "commission": getattr(deal, "commission", None),
                    "swap": getattr(deal, "swap", None),
                    "fee": getattr(deal, "fee", None),
                }
            )
        self.deals = rows
        return rows


def main() -> int:
    import MetaTrader5 as mt5

    if not mt5.initialize(path=TERMINAL):
        print("initialize_failed")
        return 2
    try:
        info = mt5.account_info()
        login = getattr(info, "login", None) if info is not None else None
        try:
            login_n = int(login)
        except (TypeError, ValueError):
            login_n = None
        if login_n != CHALLENGE_LOGIN:
            print("not_the_challenge")
            print("login", login_n)
            return 2

        print("login", login_n)
        print("terminal", TERMINAL)
        clock, frame, apply_size = _load_modules()
        now = datetime.now(timezone.utc)
        offset = clock.offset_seconds_at_utc(now, clock.NEW_YORK_PLUS_7)
        profile = (
            LIVE_REPO / "config" / "profiles" / "operator_profile.yaml"
        ).read_text(encoding="utf-8")
        rule = _yaml_fact(profile, "prop_safe_selector_daily_reset_timezone")
        initial = _yaml_fact(profile, "prop_safe_selector_initial_balance")
        daily_pct = _yaml_fact(profile, "prop_safe_selector_external_daily_loss_limit_pct")
        overall_pct = _yaml_fact(profile, "prop_safe_selector_external_overall_max_loss_pct")
        print("profile_rule", rule)
        print("profile_initial_balance", initial)
        print("profile_daily_loss_pct", daily_pct)
        print("profile_overall_loss_pct", overall_pct)
        limit_type = getattr(mt5, "ORDER_TYPE_BUY_LIMIT", None)
        market_type = getattr(mt5, "ORDER_TYPE_BUY", None)
        try:
            limit_pnl = mt5.order_calc_profit(limit_type, "EURUSD", 0.01, 1.10, 1.09)
        except Exception as exc:
            limit_pnl = type(exc).__name__
        try:
            market_pnl = mt5.order_calc_profit(market_type, "EURUSD", 0.01, 1.10, 1.09)
        except Exception as exc:
            market_pnl = type(exc).__name__
        print("order_calc_profit_buy_limit_type", limit_type)
        print("order_calc_profit_buy_limit", limit_pnl)
        print("order_calc_profit_buy_type", market_type)
        print("order_calc_profit_buy", market_pnl)

        print("BEFORE file contents, not the live account")
        for name in (
            "chair_day_baseline.json",
            "chair_day_equity.json",
            "chair_wake.json",
            "chair_health.json",
        ):
            _print_file(STATE / name)
        _scan_needle()

        positions = mt5.positions_get()
        orders = mt5.orders_get()
        shim = _Shim(mt5, info, offset)
        day = frame.read_chair_day_start(
            shim,
            now,
            rule_name=rule,
            server_offset_hours=offset / 3600.0,
            login=login_n,
            record=False,
        )
        pending_count = None if orders is None else len(list(orders))
        pending_risk = None if orders is None else _pending_risk(mt5, list(orders))
        position_count = None if positions is None else len(list(positions))
        facts = {
            "equity": getattr(info, "equity", None),
            "balance": getattr(info, "balance", None),
            "initial_balance": initial,
            "overall_loss_pct": overall_pct,
            "daily_percent_external": daily_pct,
            "day_start_balance": day.get("day_start_balance"),
            "day_start_equity": day.get("day_start_equity"),
            "positions_total": position_count,
        }
        position_risk = None
        if positions is not None and pending_risk is not None:
            position_risk = _position_risk(mt5, list(positions))
        if position_risk is not None and pending_risk is not None:
            facts["open_risk_usd"] = position_risk + pending_risk
            facts["positions_total"] = position_count
        room, room_read = apply_size.binding_room_usd(facts)
        print("AFTER live read")
        print("reset_utc", day.get("day_start_reset_utc"))
        print("day_start_balance", day.get("day_start_balance"))
        print("day_start_balance_source", day.get("day_start_source"))
        print("day_start_equity", day.get("day_start_equity"))
        print("day_start_equity_source", day.get("day_start_equity_source"))
        print("equity", getattr(info, "equity", None))
        print("balance", getattr(info, "balance", None))
        print("positions_total", position_count)
        print("pending_orders_total", pending_count)
        print("pending_stop_risk_usd", pending_risk)
        print("position_stop_risk_usd", position_risk)
        print("open_risk_usd", facts.get("open_risk_usd"))
        print("binding_room_usd", room)
        print("binding_room_read", room_read)
        print("deals_read", None if shim.deals is None else len(shim.deals))
        print("server_offset_seconds", offset)
        history_ok = True
        for stamp, expect in (
            (datetime(2026, 9, 21, 22, 0, tzinfo=timezone.utc), 93670.92),
            (datetime(2026, 9, 22, 22, 0, tzinfo=timezone.utc), 93522.57),
        ):
            derived = frame._derive_day_start(shim, now, stamp, offset / 3600.0)
            cash = _window_cash(shim.deals, stamp, offset)
            print("historical_reset", stamp.strftime("%Y-%m-%dT%H:%M:%SZ"))
            print("historical_balance", derived.get("day_start_balance"))
            print("historical_balance_source", derived.get("day_start_source"))
            print("historical_equity", derived.get("day_start_equity"))
            print("historical_equity_source", derived.get("day_start_equity_source"))
            print("historical_deals", None if shim.deals is None else len(shim.deals))
            print("historical_cash", cash)
            got = derived.get("day_start_balance")
            try:
                matched = got is not None and abs(float(got) - expect) < 0.01
            except (TypeError, ValueError):
                matched = False
            print("historical_expected", expect)
            print("historical_match", matched)
            history_ok = history_ok and matched
        if not history_ok:
            return 3
        return 0
    finally:
        mt5.shutdown()


def _window_cash(deals, reset, offset_seconds):
    if deals is None:
        return None
    total = 0.0
    for deal in deals:
        raw = deal.get("time")
        if isinstance(raw, datetime):
            when = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        else:
            try:
                when = datetime.fromtimestamp(float(raw) - float(offset_seconds), tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                return None
        if when < reset:
            continue
        for name in ("profit", "commission", "swap", "fee"):
            try:
                total += float(deal.get(name) or 0)
            except (TypeError, ValueError):
                return None
    return total


def _position_risk(mt5, positions):
    calc = getattr(mt5, "order_calc_profit", None)
    if not callable(calc):
        return None
    buy = getattr(mt5, "ORDER_TYPE_BUY", 0)
    sell = getattr(mt5, "ORDER_TYPE_SELL", 1)
    total = 0.0
    for pos in positions:
        symbol = getattr(pos, "symbol", None)
        try:
            volume = float(getattr(pos, "volume", 0) or 0)
            price = float(getattr(pos, "price_open", 0) or 0)
            stop = float(getattr(pos, "sl", 0) or 0)
        except (TypeError, ValueError):
            return None
        side = getattr(pos, "type", None)
        if not symbol or volume <= 0 or price <= 0 or stop <= 0:
            return None
        if side in (0, buy):
            order_type = buy
        elif side in (1, sell):
            order_type = sell
        else:
            return None
        try:
            pnl = float(calc(order_type, symbol, volume, price, stop))
        except Exception:
            return None
        if pnl != pnl or pnl in (float("inf"), float("-inf")):
            return None
        if pnl < 0:
            total += -pnl
    return total


if __name__ == "__main__":
    sys.exit(main())
