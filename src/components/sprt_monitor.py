"""SPRT (Sequential Probability Ratio Test) and CUSUM monitoring.

Provides statistical boundaries for confirm/kill/continue decisions
per instrument based on cumulative trade outcomes. Uses parameters from
kb_validation_and_monitoring_framework.md.

Usage:
    monitor = SPRTMonitor(config)
    result = monitor.update("XAUUSD", won=True)
    # result.status in ("CONTINUE", "CONFIRM", "KILL")
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# SPRT parameters from validation framework (Section 2.4)
# α = 0.05 (Type I error), β = 0.20 (Type II error)
ALPHA = 0.05
BETA = 0.20
UPPER_BOUNDARY = math.log((1 - BETA) / ALPHA)   # ≈ 2.773
LOWER_BOUNDARY = math.log(BETA / (1 - ALPHA))    # ≈ -1.556

# Per-instrument breakeven WRs (H0) and batch WRs (H1)
# From validation framework Section 2
INSTRUMENT_PARAMS = {
    "XAUUSD":   {"p0": 0.357, "p1": 0.620},
    "US30":     {"p0": 0.345, "p1": 0.585},
    "USDJPY":   {"p0": 0.400, "p1": 0.758},
    "GBPJPY":   {"p0": 0.417, "p1": 0.571},
    "GBPUSD":   {"p0": 0.400, "p1": 0.550},  # Observer — conservative defaults
    "PORTFOLIO": {"p0": 0.377, "p1": 0.628},
}

# CUSUM parameters
CUSUM_THRESHOLD = 5.0  # Signal when cumulative deviation exceeds this


@dataclass
class SPRTResult:
    instrument: str
    status: str  # "CONTINUE", "CONFIRM", "KILL"
    cumulative_lambda: float
    upper_boundary: float
    lower_boundary: float
    total_trades: int
    wins: int
    losses: int


@dataclass
class CUSUMResult:
    instrument: str
    deterioration_signal: bool
    improvement_signal: bool
    s_plus: float   # Deterioration accumulator
    s_minus: float  # Improvement accumulator


@dataclass
class InstrumentState:
    wins: int = 0
    losses: int = 0
    cumulative_lambda: float = 0.0
    cusum_s_plus: float = 0.0
    cusum_s_minus: float = 0.0
    trade_log: list = field(default_factory=list)


class SPRTMonitor:
    """SPRT + CUSUM monitoring for live trading instruments."""

    def __init__(self, config: dict | None = None, state_path: str = "knowledge_base/meta/sprt_state.json"):
        self._state_path = Path(state_path)
        self._states: dict[str, InstrumentState] = {}
        self._load_state()

    def _load_state(self):
        """Load persisted SPRT state from disk."""
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                for instrument, s in data.items():
                    self._states[instrument] = InstrumentState(
                        wins=s.get("wins", 0),
                        losses=s.get("losses", 0),
                        cumulative_lambda=s.get("cumulative_lambda", 0.0),
                        cusum_s_plus=s.get("cusum_s_plus", 0.0),
                        cusum_s_minus=s.get("cusum_s_minus", 0.0),
                        trade_log=s.get("trade_log", []),
                    )
            except Exception as e:
                logger.warning("Failed to load SPRT state: %s", e)

    def _save_state(self):
        """Persist SPRT state to disk."""
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            for instrument, s in self._states.items():
                data[instrument] = {
                    "wins": s.wins,
                    "losses": s.losses,
                    "cumulative_lambda": s.cumulative_lambda,
                    "cusum_s_plus": s.cusum_s_plus,
                    "cusum_s_minus": s.cusum_s_minus,
                    "trade_log": s.trade_log[-100:],  # Keep last 100
                }
            self._state_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning("Failed to save SPRT state: %s", e)

    def _get_params(self, instrument: str) -> dict:
        """Get SPRT parameters for an instrument."""
        return INSTRUMENT_PARAMS.get(instrument, INSTRUMENT_PARAMS["XAUUSD"])

    def update(self, instrument: str, won: bool) -> SPRTResult:
        """Record a trade result and compute SPRT status.

        Args:
            instrument: e.g. "XAUUSD"
            won: True if trade was a winner

        Returns:
            SPRTResult with current status
        """
        if instrument not in self._states:
            self._states[instrument] = InstrumentState()

        state = self._states[instrument]
        params = self._get_params(instrument)
        p0, p1 = params["p0"], params["p1"]

        # Compute log-likelihood ratio for this trade
        if won:
            state.wins += 1
            lambda_i = math.log(p1 / p0)
        else:
            state.losses += 1
            lambda_i = math.log((1 - p1) / (1 - p0))

        state.cumulative_lambda += lambda_i

        # Log the trade
        state.trade_log.append({
            "time": datetime.now(timezone.utc).isoformat(),
            "won": won,
            "lambda_i": round(lambda_i, 4),
            "cumulative_lambda": round(state.cumulative_lambda, 4),
        })

        # Determine status
        if state.cumulative_lambda >= UPPER_BOUNDARY:
            status = "CONFIRM"
        elif state.cumulative_lambda <= LOWER_BOUNDARY:
            status = "KILL"
        else:
            status = "CONTINUE"

        self._save_state()

        return SPRTResult(
            instrument=instrument,
            status=status,
            cumulative_lambda=round(state.cumulative_lambda, 4),
            upper_boundary=round(UPPER_BOUNDARY, 4),
            lower_boundary=round(LOWER_BOUNDARY, 4),
            total_trades=state.wins + state.losses,
            wins=state.wins,
            losses=state.losses,
        )

    def update_cusum(self, instrument: str, won: bool) -> CUSUMResult:
        """Update CUSUM change-point detection for an instrument.

        Uses the instrument's batch WR as the expected rate.
        Detects both deterioration (WR dropping) and improvement (WR rising).
        """
        if instrument not in self._states:
            self._states[instrument] = InstrumentState()

        state = self._states[instrument]
        params = self._get_params(instrument)
        expected_wr = params["p1"]

        # Observation: 1 for win, 0 for loss
        obs = 1.0 if won else 0.0
        deviation = obs - expected_wr

        # Deterioration detector (WR dropping below expected)
        state.cusum_s_plus = max(0.0, state.cusum_s_plus + (-deviation))

        # Improvement detector (WR rising above expected)
        state.cusum_s_minus = max(0.0, state.cusum_s_minus + deviation)

        self._save_state()

        return CUSUMResult(
            instrument=instrument,
            deterioration_signal=state.cusum_s_plus >= CUSUM_THRESHOLD,
            improvement_signal=state.cusum_s_minus >= CUSUM_THRESHOLD,
            s_plus=round(state.cusum_s_plus, 4),
            s_minus=round(state.cusum_s_minus, 4),
        )

    def update_all(self, instrument: str, won: bool) -> tuple[SPRTResult, CUSUMResult]:
        """Convenience: update both SPRT and CUSUM in one call."""
        sprt = self.update(instrument, won)
        cusum = self.update_cusum(instrument, won)
        return sprt, cusum

    def get_status(self, instrument: str) -> Optional[SPRTResult]:
        """Get current SPRT status without recording a new trade."""
        state = self._states.get(instrument)
        if state is None:
            return None

        if state.cumulative_lambda >= UPPER_BOUNDARY:
            status = "CONFIRM"
        elif state.cumulative_lambda <= LOWER_BOUNDARY:
            status = "KILL"
        else:
            status = "CONTINUE"

        return SPRTResult(
            instrument=instrument,
            status=status,
            cumulative_lambda=round(state.cumulative_lambda, 4),
            upper_boundary=round(UPPER_BOUNDARY, 4),
            lower_boundary=round(LOWER_BOUNDARY, 4),
            total_trades=state.wins + state.losses,
            wins=state.wins,
            losses=state.losses,
        )

    def get_all_statuses(self) -> dict[str, SPRTResult]:
        """Get SPRT status for all tracked instruments."""
        return {inst: self.get_status(inst) for inst in self._states if self.get_status(inst)}
