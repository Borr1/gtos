"""Equity-read sanity + median filter for transient MT5 read failures.

Problem (Bug #25 — 2026-04-27 GBPUSD orchestrator)
---------------------------------------------------
``MockMT5Real.get_account_equity()`` returns ``info.equity if info else 0.0``
— i.e. when ``mt5.account_info()`` transiently returns ``None`` (a known
under-load / connection-blip MT5 failure mode), the wrapper silently
substitutes ``0.0``. Downstream this is indistinguishable from a *real*
zero-equity account and produces ``daily_pnl_pct = -100%`` which trips
``_check_and_trigger_daily_loss_stop`` and writes the dormant marker.

A repeat occurrence loses an entire trading day per affected instrument.

Systemic fix
------------
1. **Hard guard** — ``safe_read_equity()`` treats ``equity <= 0`` as a
   transient failure (returns ``None``). Real MT5 accounts always have a
   non-zero equity float; a literal zero is the wrapper's fail-safe value,
   not a real account state. (FTMO/FN minimum sustained loss before account
   breach is 5-10%; reaching equity=0 would require ~100% loss which would
   already have hit the daily-loss-stop on a real read at -4%.)
2. **Soft guard** — ``EquityFilter.update_and_get_consensus()`` keeps a
   rolling window of recent valid reads and returns the median. Median is
   chosen over mean for robustness to a single-tick outlier.
3. **Recovery** — once normal reads resume, the median naturally returns
   to a healthy value within ``window_size // 2 + 1`` ticks. No manual
   marker cleanup required.
4. **Audit log** — every anomaly (zero, negative, None, large outlier)
   appends a JSONL row to ``shadow_logs/equity_read_anomalies.jsonl`` so
   we can quantify how often this happens in production.

Per-symbol state isolation
--------------------------
Each ``SessionOrchestrator`` instance owns its own ``EquityFilter``
(stored on the instance). The orchestrators are separate processes per
symbol so there is no cross-process state to coordinate; the filter only
needs to track recent history on the local instance.

Patchable for tests
-------------------
The audit log path is a module-level constant
(``EQUITY_ANOMALY_LOG_PATH``) so tests can redirect it via the canonical
``tmp_path`` + module-ref monkeypatch pattern.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.utils.jsonl_rotation import RotatingJsonlWriter

logger = logging.getLogger(__name__)


# Module-level path — patch via
#   ``monkeypatch.setattr(equity_guard, "EQUITY_ANOMALY_LOG_PATH", tmp_path / ...)``
# in tests. Never read through a fresh ``Path(...)`` literal elsewhere.
EQUITY_ANOMALY_LOG_PATH: Path = Path("shadow_logs/equity_read_anomalies.jsonl")


def _log_anomaly(record: dict) -> None:
    """Append one JSONL row to the anomaly log. Never raises.

    Best-effort observability — must not crash the trading loop if the
    log directory is unwritable or the disk is full.
    """
    try:
        path = EQUITY_ANOMALY_LOG_PATH
        # Multiple per-symbol orchestrator processes can hit the same MT5
        # equity-read anomaly on the same candle. Use the shared locked JSONL
        # writer so concurrent appends cannot interleave into malformed rows.
        RotatingJsonlWriter(path).write(record)
    except Exception as e:  # noqa: BLE001 — observability must never crash
        logger.debug("equity_anomaly_log write failed (non-blocking): %s", e)


def safe_read_equity(mt5, *, symbol: str = "unknown") -> Optional[float]:
    """Read account equity with hard sanity guard.

    Returns
    -------
    float
        A positive equity value when MT5 returned a real reading.
    None
        When MT5 raised, returned ``None``, or returned a non-positive
        value (treated as the wrapper's transient-failure sentinel).

    Side effects
    ------------
    Anomalies (raise / None / non-positive) are written to
    ``EQUITY_ANOMALY_LOG_PATH`` for production quantification. A
    ``logger.warning`` is also emitted so operators see it in real-time
    log streams.
    """
    raw: Optional[float]
    raised: Optional[str] = None
    try:
        raw = mt5.get_account_equity()
    except Exception as e:  # noqa: BLE001 — must never crash the loop
        raw = None
        raised = repr(e)

    if raw is None or not isinstance(raw, (int, float)) or raw <= 0:
        anomaly_kind = (
            "exception" if raised is not None
            else "none" if raw is None
            else "non_numeric" if not isinstance(raw, (int, float))
            else "zero" if raw == 0
            else "negative"
        )
        logger.warning(
            "EQUITY_READ_ANOMALY symbol=%s kind=%s raw=%r raised=%s",
            symbol, anomaly_kind, raw, raised,
        )
        _log_anomaly({
            "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "symbol": symbol,
            "kind": anomaly_kind,
            "raw_value": raw if isinstance(raw, (int, float)) else None,
            "raised": raised,
        })
        return None

    return float(raw)


class EquityFilter:
    """Rolling-median filter over recent valid equity reads.

    Median (rather than mean) so a single transient spike — say a 10x
    high read or one corrupt low read that slips past ``safe_read_equity``
    (e.g. account_info struct with stale data) — does not pollute the
    consensus value. With ``window_size=5`` the filter rejects up to 2
    outliers per window.

    Behavior
    --------
    - ``update_and_get_consensus(raw_or_none)`` is the only entry point.
      Pass ``None`` when ``safe_read_equity`` rejected the read; the
      filter retains its current history and returns the previous
      consensus (or ``None`` if no valid reads have ever been recorded).
    - Pass a positive float for a valid read. The filter appends, evicts
      the oldest if window is full, and returns the median.
    - Optionally pass ``raw`` and ``last_consensus`` together to detect a
      large outlier (e.g. equity dropped 80% in one tick when the
      previous read was healthy). Outliers are logged AND included in the
      window — the median absorbs them naturally.

    Thread-safety
    -------------
    NOT thread-safe. The orchestrator's main loop is single-threaded per
    symbol, and each symbol has its own instance, so no locking needed.
    """

    # Default 5 reads — covers M15-candle cadence (one read per ~minute
    # would give 5 minutes of history; one read per candle gives a
    # 75-minute window). Median of 5 means up to 2 outliers can be
    # transient before the consensus moves.
    DEFAULT_WINDOW_SIZE = 5

    # Reject reads that deviate >50% from the rolling consensus. Real
    # equity does not move 50% in one tick on a $100k account; this
    # catches struct-corruption that slipped past safe_read_equity.
    DEFAULT_OUTLIER_PCT = 0.50

    def __init__(
        self,
        *,
        window_size: int = DEFAULT_WINDOW_SIZE,
        outlier_pct: float = DEFAULT_OUTLIER_PCT,
        symbol: str = "unknown",
    ):
        if window_size < 1:
            raise ValueError("window_size must be >= 1")
        if outlier_pct <= 0:
            raise ValueError("outlier_pct must be > 0")
        self._window: deque[float] = deque(maxlen=window_size)
        self._outlier_pct = outlier_pct
        self._symbol = symbol

    def __len__(self) -> int:
        return len(self._window)

    @property
    def has_consensus(self) -> bool:
        """True iff at least one valid read has been recorded."""
        return len(self._window) > 0

    def get_consensus(self) -> Optional[float]:
        """Median of current window. Returns None if no reads recorded."""
        if not self._window:
            return None
        sorted_vals = sorted(self._window)
        n = len(sorted_vals)
        if n % 2 == 1:
            return sorted_vals[n // 2]
        return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

    def update_and_get_consensus(self, raw: Optional[float]) -> Optional[float]:
        """Append ``raw`` (if valid) and return the new median.

        Parameters
        ----------
        raw
            A positive float (valid reading), or ``None`` (transient
            failure already detected by ``safe_read_equity``). When
            ``None``, the window is unchanged and the previous consensus
            is returned (or ``None`` if no reads recorded yet).

        Returns
        -------
        Optional[float]
            The current median of the window, or ``None`` when no valid
            reads have ever been recorded.
        """
        if raw is None or raw <= 0:
            # No new datum — return the previous consensus unchanged.
            return self.get_consensus()

        prior = self.get_consensus()
        # Outlier detection AGAINST the existing consensus (if any).
        # We always append regardless — median absorbs single outliers.
        if prior is not None and prior > 0:
            deviation = abs(raw - prior) / prior
            if deviation > self._outlier_pct:
                logger.warning(
                    "EQUITY_OUTLIER_DETECTED symbol=%s raw=%.2f prior_consensus=%.2f "
                    "deviation_pct=%.1f%% — included in window, median absorbs",
                    self._symbol, raw, prior, deviation * 100,
                )
                _log_anomaly({
                    "ts_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "symbol": self._symbol,
                    "kind": "outlier",
                    "raw_value": raw,
                    "prior_consensus": prior,
                    "deviation_pct": deviation * 100,
                })

        self._window.append(float(raw))
        return self.get_consensus()
