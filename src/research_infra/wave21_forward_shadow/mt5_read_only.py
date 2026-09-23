"""Read-only MetaTrader5 adapter for the forward-shadow lane.

Serves the same call surface the research replay's ``HistoricalMT5Adapter``
serves to ``ingest_live_data`` — ``get_candles`` returning closed-bar row
dicts with aware-UTC times and attached successor completion witnesses — but
backed by live ``MetaTrader5.copy_rates_from_pos``.  Three disciplines:

  * **Clock truth**: MT5 stamps bars in broker wall time encoded as epoch.
    Every timestamp is converted through ``src.utils.broker_clock``
    (fails closed on an unregistered server; never hardcode +3).
  * **Closed-bar truth**: bar N is served only once bar N+1's open has printed
    (`observed_successor_closed_bar_rows_until`, witness attached) — the same
    truth-mode witness the frozen rule's generation ran under.  The forming
    bar contributes its open time as witness evidence only; its market values
    are never served.
  * **H1 is derived from M15**, hour-floor OHLCV aggregation, because the
    research substrate that trained and validated the funnel used
    ``use_native_h1=False`` — native broker H1 is deliberately not fetched.

Zero mutation surface: this class exposes no ``order_send``; the guard method
raises on any attempt, and the runner asserts the raw module's ``order_send``
is never referenced by shadow code.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from src.research_infra.completed_bar_witness import (
    observed_successor_closed_bar_rows_until,
)
from src.utils import broker_clock

_TF_NAMES = {1: "M1", 5: "M5", 15: "M15", 16385: "H1", 16388: "H4", 16408: "D1"}
_FETCH_MARGIN = 4


class ShadowMutationRefused(RuntimeError):
    """Any broker-mutating call inside the shadow lane is a contract breach."""


def aggregate_h1_rows_from_m15_rows(
    rows: Sequence[Mapping[str, Any]], *, symbol: str
) -> list[dict[str, Any]]:
    """Hour-floor OHLCV aggregation, mirroring the lane resolver's derived H1.

    (`replay_acceleration_attempt5_typed_sparse_runner.aggregate_h1_from_m15`;
    equivalence pinned by a unit test on the research machine.)
    """

    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        ts = datetime.fromisoformat(str(row["time_utc"]).replace("Z", "+00:00"))
        bucket = ts.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        buckets[bucket].append(row)
    out: list[dict[str, Any]] = []
    for bucket, items in sorted(buckets.items()):
        ordered = sorted(items, key=lambda item: str(item["time_utc"]))
        out.append(
            {
                "time": bucket.isoformat(),
                "time_utc": bucket.isoformat(),
                "symbol": symbol,
                "open": float(ordered[0]["open"]),
                "high": max(float(row["high"]) for row in ordered),
                "low": min(float(row["low"]) for row in ordered),
                "close": float(ordered[-1]["close"]),
                "volume": sum(float(row.get("volume") or 0.0) for row in ordered),
                "source_records": len(ordered),
            }
        )
    return out


class ShadowReadOnlyMT5Adapter:
    """Read-only candle/tick source over a connected MetaTrader5 module."""

    def __init__(self, mt5_module: Any, *, server: str):
        if not server:
            raise ValueError("broker server name required for clock resolution")
        for banned in ("order_send", "order_check"):
            # The injected object may be the raw MetaTrader5 module (which does
            # export order_send); the adapter simply never calls it.  What we
            # refuse here is an injected FAKE that only models mutation — a
            # test wiring error.
            if hasattr(mt5_module, banned) and not hasattr(
                mt5_module, "copy_rates_from_pos"
            ):
                raise ShadowMutationRefused(
                    "injected mt5 object exposes mutation without read surface"
                )
        self._mt5 = mt5_module
        self._clock_rule = broker_clock.resolve_rule(server)
        self._server = server
        self._asof: datetime | None = None
        self._last_calls: dict[str, dict[str, Any]] = {}

    # -- cycle context ----------------------------------------------------
    def set_cycle_context(self, *, asof: datetime) -> None:
        if asof.tzinfo is None or asof.utcoffset() is None:
            raise ValueError("cycle asof must be aware UTC")
        self._asof = asof.astimezone(timezone.utc)

    def _require_asof(self) -> datetime:
        if self._asof is None:
            raise RuntimeError("shadow adapter cycle context not set")
        return self._asof

    # -- conversion -------------------------------------------------------
    def _rates_to_rows(self, rates: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if rates is None:
            return rows
        for rate in rates:
            opened = broker_clock.broker_epoch_to_utc(
                float(rate["time"]), self._clock_rule
            ).isoformat()
            rows.append(
                {
                    "time": opened,
                    "time_utc": opened,
                    "open": float(rate["open"]),
                    "high": float(rate["high"]),
                    "low": float(rate["low"]),
                    "close": float(rate["close"]),
                    "volume": float(rate["tick_volume"]),
                }
            )
        return rows

    def _fetch_rows(self, symbol: str, tf_const: int, count: int) -> list[dict[str, Any]]:
        rates = self._mt5.copy_rates_from_pos(symbol, tf_const, 0, int(count))
        return self._rates_to_rows(rates)

    # -- the ingestion surface -------------------------------------------
    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict[str, Any]]:
        asof = self._require_asof()
        tf_name = _TF_NAMES.get(int(timeframe))
        if not tf_name:
            raise RuntimeError(f"unsupported shadow timeframe constant: {timeframe}")
        if tf_name == "H1":
            m15_rows = self._fetch_rows(
                symbol, 15, 4 * (int(count) + _FETCH_MARGIN) + 8
            )
            raw_rows = aggregate_h1_rows_from_m15_rows(m15_rows, symbol=symbol)
            derivation = "derived_h1_from_m15_hourly_ohlcv"
        else:
            raw_rows = self._fetch_rows(symbol, int(timeframe), int(count) + _FETCH_MARGIN)
            derivation = "native"
        witnessed = observed_successor_closed_bar_rows_until(
            raw_rows,
            timeframe=tf_name,
            asof=asof,
            max_rows=int(count),
            attach_witness=True,
        )
        selected = [dict(row) for row in witnessed]
        self._last_calls[tf_name] = {
            "requested_broker_symbol": symbol,
            "timeframe": tf_name,
            "derivation": derivation,
            "requested_count": int(count),
            "returned_count": len(selected),
            "latest_closed_time": selected[-1]["time_utc"] if selected else None,
            "broker_clock_rule": self._clock_rule.name,
        }
        return selected

    def get_tick(self, symbol: str = "XAUUSD") -> None:
        # Predecision parity with the replay contract: raw_data is built from
        # D1/H4/H1/M15 closed bars only.  The live tick enters exclusively
        # through ``live_cost_quote`` for the pretrade cost packet.
        return None

    def get_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime) -> list:
        return []

    def get_positions(self, symbol: str = "XAUUSD") -> list[Any]:
        return []

    def get_margin_mode(self) -> str:
        return "hedging"

    def last_calls(self) -> dict[str, dict[str, Any]]:
        return {key: dict(value) for key, value in self._last_calls.items()}

    # -- live cost quote (NOT part of raw_data) ---------------------------
    def live_cost_quote(self, symbol: str) -> dict[str, Any] | None:
        """Live bid/ask for the pretrade cost packet, with staleness metadata."""

        asof = self._require_asof()
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        raw_epoch = getattr(tick, "time_msc", None)
        if raw_epoch:
            epoch = float(raw_epoch) / 1000.0
        else:
            epoch = float(getattr(tick, "time", 0.0) or 0.0)
        if epoch <= 0:
            return None
        tick_utc = broker_clock.broker_epoch_to_utc(epoch, self._clock_rule)
        return {
            "bid": bid,
            "ask": ask,
            "time_utc": tick_utc.isoformat(),
            "stale_seconds": max(0.0, (asof - tick_utc).total_seconds()),
            "quote_source": "live_ftmo_predecision_tick",
        }

    # -- mutation refusal -------------------------------------------------
    def order_send(self, request: Any) -> Any:
        raise ShadowMutationRefused(
            "forward-shadow lane must never transmit an order"
        )

    def get_account_balance(self) -> float:
        return 0.0

    def get_account_equity(self) -> float:
        return 0.0
