"""Variant C Partial Close Shadow Logger — observation-only.

Tracks hypothetical outcome if 33% of position was closed at +1.0R.
Does NOT actually close any portion. Shadow data collection only.

Variant C design (from Patrick podcast / FTMO survival analysis):
- At +1.0R: close 33% of position, move stop to entry (BE)
- Remaining 67% rides to original TP or BE stop

Evidence from simulation (n=129 backtest trades):
- P(pass FTMO) improves 93.4% → 98.3%
- 0% DD breach (vs 0.5% current)
- Terminal equity $134,784 (vs $131,655)
- But WR/expectancy impact is INCONCLUSIVE (+4.9pp, gate was 5pp)

Promotion criteria (after 30+ triggered trades):
- Compute cumulative delta_r = sum(variant_c_r - actual_r)
- If delta_r > 0 with p < 0.05 (Wilcoxon signed-rank): promote to live
- If delta_r <= 0 after 30 trades: kill and document
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/partial_close_shadow_log.jsonl"

# Variant C parameters
PARTIAL_CLOSE_FRACTION = 0.33  # Close 33% at trigger
TRIGGER_R = 1.0  # Trigger at +1.0R


class PartialCloseShadowTracker:
    """Track hypothetical Variant C partial close outcome."""

    def __init__(
        self,
        trade_id: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        direction: str,
        sl_distance: float,
        partial_close_fraction: float = PARTIAL_CLOSE_FRACTION,
        trigger_r: float = TRIGGER_R,
        source_evidence: dict | None = None,
    ):
        self.trade_id = trade_id
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.direction = direction
        self.sl_distance = sl_distance
        self.partial_close_fraction = float(partial_close_fraction)
        self.trigger_r = float(trigger_r)
        self.source_evidence = dict(source_evidence or {})

        self.trigger_activated = False
        self.timestamp_triggered: str | None = None
        self.price_at_trigger: float | None = None

        # After trigger: track if remaining position would hit BE
        self._reversed_past_entry = False
        self._min_favorable: float | None = None

    def update(self, current_price: float) -> bool:
        """Check price updates. Returns True on first +1R trigger.

        Call on every tick/price update (same cadence as BE shadow tracker).
        """
        if self.sl_distance <= 0:
            return False

        current_r = self._compute_r(current_price)

        if not self.trigger_activated:
            if current_r >= self.trigger_r:
                self.trigger_activated = True
                self.timestamp_triggered = datetime.now(timezone.utc).isoformat()
                self.price_at_trigger = current_price
                self._min_favorable = current_price
                logger.info(
                    "PARTIAL_CLOSE_SHADOW: +%.1fR trigger for %s at %.5f",
                    self.trigger_r, self.trade_id, current_price,
                )
                return True
            return False

        # After trigger: track if price reversed past entry (BE stop)
        if self.direction == "LONG":
            if current_price <= self.entry_price:
                self._reversed_past_entry = True
            if self._min_favorable is None or current_price < self._min_favorable:
                self._min_favorable = current_price
        else:
            if current_price >= self.entry_price:
                self._reversed_past_entry = True
            if self._min_favorable is None or current_price > self._min_favorable:
                self._min_favorable = current_price

        return False

    def _compute_r(self, price: float) -> float:
        if self.sl_distance <= 0:
            return 0.0
        if self.direction == "LONG":
            return (price - self.entry_price) / self.sl_distance
        return (self.entry_price - price) / self.sl_distance

    def compute_hypothetical(
        self,
        actual_exit_price: float,
        actual_r_multiple: float,
    ) -> dict | None:
        """Compute Variant C hypothetical outcome at trade close.

        Returns dict with shadow analysis, or None if trigger never fired.
        """
        if not self.trigger_activated:
            return None

        # Partial close component: 33% closed at +1.0R
        partial_r = self.trigger_r  # locked in at trigger

        # Remaining 67%: what would have happened?
        if self._reversed_past_entry:
            # Price hit entry → BE stop on remaining portion → 0R
            remaining_r = 0.0
        else:
            # Price never reversed past entry → same exit as actual
            remaining_r = self._compute_r(actual_exit_price)

        # Blended R
        variant_c_r = (
            self.partial_close_fraction * partial_r
            + (1.0 - self.partial_close_fraction) * remaining_r
        )

        delta_r = variant_c_r - actual_r_multiple

        return {
            "trade_id": self.trade_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "sl_distance": self.sl_distance,
            "timestamp_triggered": self.timestamp_triggered,
            "price_at_trigger": self.price_at_trigger,
            "actual_exit_price": actual_exit_price,
            "actual_r_multiple": round(actual_r_multiple, 4),
            "reversed_past_entry": self._reversed_past_entry,
            "partial_close_r": round(partial_r, 4),
            "partial_close_fraction": self.partial_close_fraction,
            "trigger_r": self.trigger_r,
            "remaining_r": round(remaining_r, 4),
            "variant_c_blended_r": round(variant_c_r, 4),
            "delta_r": round(delta_r, 4),
            "variant_c_better": delta_r > 0,
            "source_evidence": dict(self.source_evidence),
            "timestamp_closed": datetime.now(timezone.utc).isoformat(),
        }


def write_partial_close_shadow_log(
    entry: dict,
    log_path: str = SHADOW_LOG_PATH,
) -> None:
    """Append a Variant C shadow entry to the JSONL log."""
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(
            "PARTIAL_CLOSE_SHADOW: trade=%s actual=%.4fR variant_c=%.4fR delta=%.4fR",
            entry.get("trade_id", "?"),
            entry.get("actual_r_multiple", 0),
            entry.get("variant_c_blended_r", 0),
            entry.get("delta_r", 0),
        )
    except Exception as e:
        logger.warning("Failed to write partial close shadow log (non-blocking): %s", e)
