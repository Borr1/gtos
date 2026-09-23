"""Persistent SPRT-style watcher for side-aware sizing auto-revert.

Tracks the rolling window of LONG trade outcomes ACROSS ALL SYMBOLS
(portfolio-level — the LONG-WR-watch SPRT operates on the aggregate, not
per-symbol). When the win rate over the window falls below the threshold,
latches a ``disabled_at`` timestamp into the state file. Once latched, the
side-aware multiplier path is bypassed by the orchestrator until the CEO
manually clears the state file (or calls ``reset()``).

State file: ``pipeline_state/side_aware_sprt_state.json``

Schema:

    {
      "long_outcomes": [
        {"win": true, "symbol": "XAUUSD", "ts": "2026-04-27T14:07:12Z"},
        ...
      ],
      "disabled_at": "2026-04-29T18:30:00Z" | null,
      "disable_reason": "wr=0.45 over n=20 (threshold=0.50)" | null,
      "version": 1
    }

Multi-process safety
--------------------
Each orchestrator (one per symbol, ~7 in production) runs its own watcher
instance and writes outcomes atomically via ``src.utils.file_io.atomic_write``.
The window of races is tiny — at most one LONG fill per ~hour across the
portfolio — so we accept best-effort eventual consistency without a file lock.
A reader sees either the pre-write state or the post-write state, never a
torn write (atomic_write uses tmp+rename semantics).

The disable latch is monotonic (once set, never auto-cleared). This is by
design — if WR drifts back above threshold by chance after the disable, we
still require human review before re-enabling.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.utils.file_io import atomic_write


logger = logging.getLogger(__name__)


# Module-level path — patch via ``monkeypatch.setattr(module, "STATE_PATH", ...)`` in tests.
STATE_PATH: Path = Path("pipeline_state/side_aware_sprt_state.json")

DEFAULT_WINDOW_SIZE: int = 20
DEFAULT_WR_THRESHOLD: float = 0.50
SCHEMA_VERSION: int = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SideAwareSprtWatcher:
    """Persistent rolling-window LONG-WR auto-revert watcher.

    Lifecycle:
      - Construct (loads state from disk; empty if file missing).
      - On each LONG trade close: ``record_long_outcome(symbol, was_win)``.
      - Before applying side-aware multiplier: ``is_disabled()``.
      - For tests / CEO manual reset: ``reset()``.
    """

    DEFAULT_WINDOW_SIZE = DEFAULT_WINDOW_SIZE
    DEFAULT_WR_THRESHOLD = DEFAULT_WR_THRESHOLD

    def __init__(
        self,
        config: Mapping[str, Any] | None,
        state_path: Optional[str | Path] = None,
    ) -> None:
        self.config = config or {}
        # Resolve state path with monkeypatch-friendly module fallback.
        if state_path is not None:
            self._state_path: Path = Path(state_path)
        else:
            # Re-read the module-level constant each construction so tests
            # that monkeypatch ``STATE_PATH`` are honored. Avoid capturing a
            # stale reference at import time.
            self._state_path = STATE_PATH
        sub = self._cfg_section()
        self._window_size: int = int(
            sub.get("sprt_window_size", DEFAULT_WINDOW_SIZE)
        )
        try:
            self._wr_threshold: float = float(
                sub.get("sprt_wr_threshold", DEFAULT_WR_THRESHOLD)
            )
        except (TypeError, ValueError):
            self._wr_threshold = DEFAULT_WR_THRESHOLD
        self._state: dict = self._load_state()

    # -- internal helpers --------------------------------------------------

    def _cfg_section(self) -> Mapping[str, Any]:
        if not isinstance(self.config, Mapping):
            return {}
        risk = self.config.get("risk", {})
        if not isinstance(risk, Mapping):
            return {}
        sub = risk.get("side_aware_sizing", {})
        if not isinstance(sub, Mapping):
            return {}
        return sub

    def _load_state(self) -> dict:
        """Read state from disk; return empty schema on missing/corrupt file."""
        if not self._state_path.exists():
            return self._empty_state()
        try:
            with self._state_path.open("r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            logger.warning(
                "side_aware_sprt_state.json unreadable, treating as empty: %s",
                e,
            )
            return self._empty_state()
        if not isinstance(state, dict):
            logger.warning(
                "side_aware_sprt_state.json not a dict (got %s); resetting view",
                type(state).__name__,
            )
            return self._empty_state()
        # Backfill any missing fields so the rest of the class doesn't have to
        # check existence.
        state.setdefault("long_outcomes", [])
        state.setdefault("disabled_at", None)
        state.setdefault("disable_reason", None)
        state.setdefault("version", SCHEMA_VERSION)
        if not isinstance(state["long_outcomes"], list):
            state["long_outcomes"] = []
        return state

    @staticmethod
    def _empty_state() -> dict:
        return {
            "long_outcomes": [],
            "disabled_at": None,
            "disable_reason": None,
            "version": SCHEMA_VERSION,
        }

    def _persist(self) -> None:
        """Atomically write the in-memory state to disk."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(self._state_path, self._state)

    # -- public API --------------------------------------------------------

    def record_long_outcome(self, symbol: str, was_win: bool) -> None:
        """Append a LONG outcome to the rolling window and recompute WR.

        Truncates ``long_outcomes`` to the last ``window_size`` entries.
        Latches ``disabled_at`` if the window is full and WR < threshold.
        Once disabled, the state stays disabled even if subsequent outcomes
        push WR back above threshold (monotonic, by design).

        Non-blocking — the orchestrator wraps the call in try/except and a
        warning log so a state-write failure can't kill a trade flow.
        """
        # Always reload from disk first so cross-process writes (each
        # orchestrator instantiates its own watcher) compose correctly.
        self._state = self._load_state()

        outcome = {
            "win": bool(was_win),
            "symbol": str(symbol or ""),
            "ts": _now_iso(),
        }
        outcomes: list = list(self._state.get("long_outcomes") or [])
        outcomes.append(outcome)
        # Truncate to last window_size entries.
        if len(outcomes) > self._window_size:
            outcomes = outcomes[-self._window_size:]
        self._state["long_outcomes"] = outcomes

        # Evaluate auto-disable only when the window is full and not already
        # disabled (latch is monotonic).
        if not self._state.get("disabled_at") and len(outcomes) >= self._window_size:
            wins = sum(1 for o in outcomes if o.get("win"))
            wr = wins / float(len(outcomes))
            if wr < self._wr_threshold:
                self._state["disabled_at"] = _now_iso()
                self._state["disable_reason"] = (
                    f"wr={wr:.2f} over n={len(outcomes)} "
                    f"(threshold={self._wr_threshold:.2f})"
                )
                logger.critical(
                    "SIDE_AWARE_SPRT_AUTO_DISABLED — %s. The flag now no-ops "
                    "until pipeline_state/side_aware_sprt_state.json is "
                    "manually cleared.",
                    self._state["disable_reason"],
                )

        self._persist()

    def is_disabled(self) -> bool:
        """Return True iff the watcher state has ``disabled_at`` set.

        Reads from disk every call so cross-process disables are visible
        without re-instantiation.
        """
        try:
            state = self._load_state()
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("side_aware sprt is_disabled load failed: %s", e)
            return False
        return bool(state.get("disabled_at"))

    def reset(self) -> None:
        """Clear the state file (delete it). Used by tests and CEO manual reset."""
        self._state = self._empty_state()
        try:
            self._state_path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(
                "Failed to unlink side_aware sprt state: %s", e,
            )

    # -- introspection / diagnostics --------------------------------------

    @property
    def window_size(self) -> int:
        return self._window_size

    @property
    def wr_threshold(self) -> float:
        return self._wr_threshold

    @property
    def state_path(self) -> Path:
        return self._state_path
