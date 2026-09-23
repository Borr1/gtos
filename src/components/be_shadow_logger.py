"""BE (Break-Even) Shadow Logger — observation-only.

For every trade that reaches +1R from entry, logs what would have happened
if the stop had been moved to entry price (0R). Does NOT actually move
the stop. This is shadow data collection only.

Evidence: +2.76R net benefit from 8 affected trades in backtest
(5 losses saved, 3 winners cut). Not statistically significant (p=0.375)
but only positive-direction management modification found.

Promotion criteria (after 30+ BE-triggered trades):
- If cumulative delta_r > 0 with p < 0.05 on Wilcoxon signed-rank: promote to live
- If cumulative delta_r <= 0 after 30 trades: kill and document
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/be_shadow_log.jsonl"


class BEShadowTracker:
    """Track whether a trade reaches +1R and compute hypothetical BE outcome."""

    def __init__(self, trade_id: str, entry_price: float, stop_loss: float,
                 direction: str, sl_distance: float):
        self.trade_id = trade_id
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.direction = direction
        self.sl_distance = sl_distance

        self.be_trigger_activated = False
        self.timestamp_1r_reached: str | None = None
        self.price_at_1r: float | None = None

        # Track minimum favorable excursion after trigger (for detailed analysis)
        self._min_price_after_trigger: float | None = None

    def update(self, current_price: float) -> bool:
        """Check if +1R is reached. Call on every price update.

        Returns True if the +1R trigger fires on this update (one-shot).
        """
        if self.be_trigger_activated:
            # Already triggered — track if price reversed past entry
            if self._min_price_after_trigger is None:
                self._min_price_after_trigger = current_price
            if self.direction == "LONG":
                if current_price < self._min_price_after_trigger:
                    self._min_price_after_trigger = current_price
            else:
                if current_price > self._min_price_after_trigger:
                    self._min_price_after_trigger = current_price
            return False

        if self.sl_distance <= 0:
            return False

        # Calculate current R-multiple
        if self.direction == "LONG":
            current_r = (current_price - self.entry_price) / self.sl_distance
        else:
            current_r = (self.entry_price - current_price) / self.sl_distance

        if current_r >= 1.0:
            self.be_trigger_activated = True
            self.timestamp_1r_reached = datetime.now(timezone.utc).isoformat()
            self.price_at_1r = current_price
            self._min_price_after_trigger = current_price
            logger.info("BE_SHADOW: +1R reached for %s at price %.5f",
                        self.trade_id, current_price)
            return True

        return False

    def compute_hypothetical(self, actual_exit_price: float,
                             actual_r_multiple: float) -> dict | None:
        """Compute what would have happened with a BE stop.

        Returns a dict with the shadow analysis, or None if +1R was never reached.
        """
        if not self.be_trigger_activated:
            return None

        # Would the trade have been stopped at BE (entry price)?
        reversed_past_entry = False
        if self.direction == "LONG":
            reversed_past_entry = (self._min_price_after_trigger is not None
                                   and self._min_price_after_trigger <= self.entry_price)
        else:
            reversed_past_entry = (self._min_price_after_trigger is not None
                                   and self._min_price_after_trigger >= self.entry_price)

        if reversed_past_entry:
            hypothetical_be_r = 0.0  # Stopped at BE
        else:
            hypothetical_be_r = actual_r_multiple  # Same outcome

        delta_r = hypothetical_be_r - actual_r_multiple
        be_would_have_helped = delta_r > 0  # Loss that would have been saved

        return {
            "trade_id": self.trade_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "sl_distance": self.sl_distance,
            "timestamp_1r_reached": self.timestamp_1r_reached,
            "price_at_1r": self.price_at_1r,
            "actual_exit_price": actual_exit_price,
            "actual_r_multiple": round(actual_r_multiple, 4),
            "reversed_past_entry": reversed_past_entry,
            "hypothetical_be_r": round(hypothetical_be_r, 4),
            "delta_r": round(delta_r, 4),
            "be_would_have_helped": be_would_have_helped,
            "timestamp_closed": datetime.now(timezone.utc).isoformat(),
        }


def write_be_shadow_log(entry: dict, log_path: str = SHADOW_LOG_PATH):
    """Append a BE shadow analysis entry to the JSONL log."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info("BE_SHADOW_LOG: trade=%s delta_r=%.4f helped=%s",
                     entry.get("trade_id", "?"),
                     entry.get("delta_r", 0),
                     entry.get("be_would_have_helped", False))
    except Exception as e:
        logger.warning("Failed to write BE shadow log (non-blocking): %s", e)
