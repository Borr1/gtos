"""H29 — Drawdown-based position size reduction.

When cumulative account drawdown from equity peak reaches a configurable
threshold, risk per trade moves from the resolved profile/instrument risk to
the configured drawdown-reduced risk.
Normal risk resumes when equity makes a new high.

Evidence: Monte Carlo (10k iterations, 5 seeds) — P(DD>10%) drops
from 0.94% to 0.22% (4.3x reduction). Cost: $101 avg equity sacrifice.

This module is purely a risk adjuster. It does NOT gate trades —
it reduces position size. Trade selection logic is untouched.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE = "knowledge_base/meta/equity_peak_state.json"


class DrawdownManager:
    """Track equity peak and apply drawdown-based risk reduction."""

    def __init__(self, config: dict, state_file: str = STATE_FILE):
        risk_cfg = config.get("risk", {})
        dd_cfg = config.get("drawdown_reduction", {})

        self.dd_threshold = dd_cfg.get("threshold", 0.08)
        self.reduced_risk = dd_cfg.get("reduced_risk_pct", 0.5)
        self.normal_risk = risk_cfg.get("risk_per_trade_pct", 1.0)
        self._state_file = Path(state_file)

        # Load persisted equity peak (survives session restarts)
        self._equity_peak = self._load_peak()
        self._is_reduced = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_risk_pct(self, current_equity: float) -> float:
        """Return the risk % to use for the next trade.

        Updates the equity peak and determines whether drawdown-based
        reduction applies.

        Args:
            current_equity: Current account equity from MT5.

        Returns:
            Configured risk percentage for the active profile/instrument state.
        """
        if current_equity <= 0:
            return self.normal_risk

        # Update equity peak
        old_peak = self._equity_peak
        if self._equity_peak is None or current_equity > self._equity_peak:
            self._equity_peak = current_equity
            if old_peak is not None and old_peak < current_equity:
                self._persist_peak()
                if self._is_reduced:
                    self._log_state_change("reduced", "normal",
                                           current_equity, self._equity_peak)
                    self._is_reduced = False
            elif old_peak is None:
                self._persist_peak()

        # Calculate drawdown from peak
        dd_pct = self._calc_drawdown(current_equity)

        if dd_pct >= self.dd_threshold:
            if not self._is_reduced:
                self._log_state_change("normal", "reduced",
                                       current_equity, self._equity_peak)
                self._is_reduced = True
            return self.reduced_risk
        else:
            if self._is_reduced:
                self._log_state_change("reduced", "normal",
                                       current_equity, self._equity_peak)
                self._is_reduced = False
            return self.normal_risk

    def get_drawdown_pct(self, current_equity: float) -> float:
        """Return current drawdown from peak as a fraction (0.0 to 1.0)."""
        if self._equity_peak is None or self._equity_peak <= 0:
            return 0.0
        return self._calc_drawdown(current_equity)

    @property
    def equity_peak(self) -> float | None:
        return self._equity_peak

    @property
    def is_reduced(self) -> bool:
        return self._is_reduced

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _calc_drawdown(self, current_equity: float) -> float:
        if self._equity_peak is None or self._equity_peak <= 0:
            return 0.0
        return (self._equity_peak - current_equity) / self._equity_peak

    def _load_peak(self) -> float | None:
        try:
            if self._state_file.exists():
                with open(self._state_file) as f:
                    data = json.load(f)
                peak = data.get("equity_peak")
                if peak is not None:
                    logger.info("Loaded equity peak from state: $%.2f", peak)
                return peak
        except Exception as e:
            logger.warning("Failed to load equity peak state: %s", e)
        return None

    def _persist_peak(self):
        try:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "equity_peak": self._equity_peak,
                "updated": datetime.now(timezone.utc).isoformat(),
            }
            with open(self._state_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Failed to persist equity peak: %s", e)

    def _log_state_change(self, from_state: str, to_state: str,
                          equity: float, peak: float):
        dd_pct = self._calc_drawdown(equity)
        logger.info(
            "DRAWDOWN_RISK_CHANGE: %s -> %s | equity=$%.2f peak=$%.2f "
            "dd=%.2f%% threshold=%.1f%%",
            from_state, to_state, equity, peak,
            dd_pct * 100, self.dd_threshold * 100,
        )
        # Also persist state change to a log file for audit
        try:
            log_path = Path("shadow_logs/drawdown_state_changes.jsonl")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from_state": from_state,
                "to_state": to_state,
                "equity": equity,
                "equity_peak": peak,
                "drawdown_pct": round(dd_pct * 100, 4),
                "threshold_pct": self.dd_threshold * 100,
                "risk_applied": self.reduced_risk if to_state == "reduced" else self.normal_risk,
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # Non-blocking
