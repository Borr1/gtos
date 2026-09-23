from datetime import datetime, timezone
from types import SimpleNamespace

from scripts.capture_live_broker_day_truth import compact_pending_order, compact_position
from src.utils.broker_clock import resolve_rule


class _Mt5:
    ORDER_TYPE_BUY = 0

    @staticmethod
    def order_calc_profit(*_args):
        return -9.27


def _broker_wall_epoch(hour: int) -> int:
    return int(datetime(2026, 8, 13, hour, 1, 2, tzinfo=timezone.utc).timestamp())


def test_open_position_time_uses_broker_clock_rule() -> None:
    position = SimpleNamespace(
        ticket=1,
        identifier=1,
        time=_broker_wall_epoch(20),
        type=0,
        magic=0,
        symbol="US30.cash",
        volume=0.04,
        price_open=53734.55,
        price_current=53766.45,
        sl=53502.76,
        tp=53908.77,
        profit=1.28,
        swap=0.0,
        comment="F5:idxrev",
    )

    row = compact_position(position, _Mt5(), 108_324.83, resolve_rule("FTMO-Server3"))

    assert row["time_utc"] == "2026-08-13T17:01:02Z"


def test_pending_order_time_uses_broker_clock_rule() -> None:
    order = SimpleNamespace(
        ticket=2,
        time_setup=_broker_wall_epoch(20),
        type=2,
        state=1,
        magic=0,
        symbol="US30.cash",
        volume_current=0.04,
        volume_initial=0.04,
        price_open=53734.55,
        sl=53502.76,
        tp=53908.77,
        comment="F5:idxrev",
    )

    row = compact_pending_order(order, _Mt5(), 108_324.83, resolve_rule("FTMO-Server3"))

    assert row["time_setup_utc"] == "2026-08-13T17:01:02Z"
