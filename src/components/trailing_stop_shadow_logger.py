"""Trailing-stop V1 shadow logger.

Observation-only tracker for the T2.1 full-pop trailing-stop replay. It never
modifies broker stops; it records the hypothetical R path for a 0.5R activation
with a 0.5R trailing distance.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/trailing_stop_v1_shadow_log.jsonl"

DEFAULT_ACTIVATION_R = 0.5
DEFAULT_TRAIL_DISTANCE_R = 0.5


class TrailingStopShadowTracker:
    """Track a hypothetical fixed-R trailing stop for one open trade."""

    def __init__(
        self,
        trade_id: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        sl_distance: float,
        activation_r: float = DEFAULT_ACTIVATION_R,
        trail_distance_r: float = DEFAULT_TRAIL_DISTANCE_R,
        source_evidence: dict | None = None,
    ):
        self.trade_id = trade_id
        self.entry_price = float(entry_price)
        self.stop_loss = float(stop_loss)
        self.take_profit = float(take_profit)
        self.direction = str(direction).upper()
        self.sl_distance = float(sl_distance)
        self.activation_r = float(activation_r)
        self.trail_distance_r = float(trail_distance_r)
        self.source_evidence = dict(source_evidence or {})

        self.trigger_activated = False
        self.timestamp_triggered: str | None = None
        self.price_at_trigger: float | None = None
        self.best_r: float | None = None
        self.best_price: float | None = None
        self.trailing_stop_r: float | None = None
        self.trailing_stop_price: float | None = None
        self.trailing_exit_triggered = False
        self.timestamp_trailing_exit: str | None = None

    def update(self, current_price: float) -> bool:
        """Update the hypothetical trail. Returns True on first activation."""
        if self.sl_distance <= 0:
            return False

        price = float(current_price)
        current_r = self._compute_r(price)
        if self.best_r is None or current_r > self.best_r:
            self.best_r = current_r
            self.best_price = price

        if not self.trigger_activated:
            if current_r < self.activation_r:
                return False
            self.trigger_activated = True
            self.timestamp_triggered = datetime.now(timezone.utc).isoformat()
            self.price_at_trigger = price
            self._refresh_trailing_stop(current_r)
            logger.info(
                "TRAILING_STOP_V1_SHADOW: %.2fR activation for %s at %.5f",
                self.activation_r,
                self.trade_id,
                price,
            )
            return True

        if self.trailing_exit_triggered:
            return False

        self._refresh_trailing_stop(current_r)
        if (
            self.trailing_stop_r is not None
            and current_r <= self.trailing_stop_r
        ):
            self.trailing_exit_triggered = True
            self.timestamp_trailing_exit = datetime.now(timezone.utc).isoformat()
            logger.info(
                "TRAILING_STOP_V1_SHADOW: trail exit for %s at %.4fR",
                self.trade_id,
                self.trailing_stop_r,
            )
        return False

    def compute_hypothetical(
        self,
        actual_exit_price: float,
        actual_r_multiple: float,
    ) -> dict | None:
        """Return trailing-stop hypothetical outcome for a closed trade."""
        if not self.trigger_activated:
            return None

        actual_exit_r = float(actual_r_multiple)
        hypothetical_exit_price = float(actual_exit_price)
        hypothetical_exit_r = actual_exit_r
        stopped_by_trail = self.trailing_exit_triggered

        if self.trailing_stop_r is not None:
            actual_close_crossed_trail = actual_exit_r <= self.trailing_stop_r
            if stopped_by_trail or actual_close_crossed_trail:
                stopped_by_trail = True
                hypothetical_exit_r = self.trailing_stop_r
                hypothetical_exit_price = (
                    self.trailing_stop_price
                    if self.trailing_stop_price is not None
                    else self._price_for_r(self.trailing_stop_r)
                )

        delta_r = hypothetical_exit_r - actual_exit_r
        return {
            "trade_id": self.trade_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "sl_distance": self.sl_distance,
            "activation_r": self.activation_r,
            "trail_distance_r": self.trail_distance_r,
            "timestamp_triggered": self.timestamp_triggered,
            "price_at_trigger": self.price_at_trigger,
            "best_price": self.best_price,
            "best_r": round(self.best_r or 0.0, 4),
            "trailing_stop_price": self.trailing_stop_price,
            "trailing_stop_r": round(self.trailing_stop_r or 0.0, 4),
            "trailing_exit_triggered": stopped_by_trail,
            "timestamp_trailing_exit": self.timestamp_trailing_exit,
            "actual_exit_price": float(actual_exit_price),
            "actual_r_multiple": round(actual_exit_r, 4),
            "hypothetical_exit_price": round(hypothetical_exit_price, 5),
            "hypothetical_trailing_r": round(hypothetical_exit_r, 4),
            "delta_r": round(delta_r, 4),
            "trailing_stop_better": delta_r > 0,
            "source_evidence": dict(self.source_evidence),
            "timestamp_closed": datetime.now(timezone.utc).isoformat(),
        }

    def _refresh_trailing_stop(self, current_r: float) -> None:
        candidate_r = current_r - self.trail_distance_r
        if self.trailing_stop_r is None or candidate_r > self.trailing_stop_r:
            self.trailing_stop_r = candidate_r
            self.trailing_stop_price = self._price_for_r(candidate_r)

    def _compute_r(self, price: float) -> float:
        if self.sl_distance <= 0:
            return 0.0
        if self.direction == "LONG":
            return (price - self.entry_price) / self.sl_distance
        return (self.entry_price - price) / self.sl_distance

    def _price_for_r(self, r_value: float) -> float:
        if self.direction == "LONG":
            return self.entry_price + r_value * self.sl_distance
        return self.entry_price - r_value * self.sl_distance


def write_trailing_stop_shadow_log(
    entry: dict,
    log_path: str = SHADOW_LOG_PATH,
) -> None:
    """Append a trailing-stop shadow entry to the JSONL log."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        logger.info(
            "TRAILING_STOP_V1_SHADOW_LOG: trade=%s actual=%.4fR trail=%.4fR delta=%.4fR",
            entry.get("trade_id", "?"),
            entry.get("actual_r_multiple", 0),
            entry.get("hypothetical_trailing_r", 0),
            entry.get("delta_r", 0),
        )
    except Exception as exc:  # noqa: BLE001 - shadow logging is non-blocking
        logger.warning("Failed to write trailing-stop shadow log: %s", exc)
