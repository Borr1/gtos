"""Runtime bridge for class-aware LONG-WR SPRT halt rules.

The pure threshold checker lives in ``src.safety.sprt_class_halt_check``.
This module turns those thresholds into live system behavior by persisting
the first-N LONG outcomes per symbol and exposing an orchestrator gate that
can block future evaluation when automation is enabled.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.safety.sprt_class_halt_check import HaltCheckResult, check
from src.components.sprt_halt_alert_template import dispatch_alert
from src.utils.file_io import atomic_write


logger = logging.getLogger(__name__)

STATE_PATH: Path = Path("pipeline_state/sprt_class_halt_state.json")
SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _config_block(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    block = config.get("sprt_halt") or {}
    return block if isinstance(block, Mapping) else {}


def _trigger_n(config: Mapping[str, Any] | None) -> int:
    try:
        return max(1, int(_config_block(config).get("trigger_n", 20)))
    except (TypeError, ValueError):
        return 20


def _result_to_record(result: HaltCheckResult | None) -> dict[str, Any]:
    if result is None:
        return {}
    return {
        "verdict": result.verdict,
        "class_name": result.class_name,
        "threshold_breached": result.threshold_breached,
        "actual_wr": result.actual_wr,
        "n": result.n,
        "message": result.message,
    }


@dataclass(frozen=True)
class SprtClassHaltDecision:
    enabled: bool
    automation_enabled: bool
    symbol: str
    should_block: bool
    would_block: bool
    reason: str
    verdict: str = "OK"
    class_name: str | None = None
    actual_wr: float | None = None
    threshold_breached: float | None = None
    n: int = 0
    source_path: str = ".context/02_session_handoffs/39_apr25_session_40_KICKOFF_MONDAY_DEPLOY_AND_POWERFUL_MACHINE_VISION.md"
    source_line_no: int = 79
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "automation_enabled": self.automation_enabled,
            "symbol": self.symbol,
            "should_block": self.should_block,
            "would_block": self.would_block,
            "reason": self.reason,
            "verdict": self.verdict,
            "class_name": self.class_name,
            "actual_wr": self.actual_wr,
            "threshold_breached": self.threshold_breached,
            "n": self.n,
            "source_path": self.source_path,
            "source_line_no": self.source_line_no,
            "evidence": dict(self.evidence or {}),
        }


class SprtClassHaltRuntime:
    """Persistent first-N LONG outcome tracker plus active halt gate."""

    def __init__(
        self,
        config: Mapping[str, Any] | None,
        state_path: str | Path | None = None,
    ) -> None:
        self.config = config or {}
        self._state_path = Path(state_path) if state_path is not None else STATE_PATH

    def _empty_state(self) -> dict[str, Any]:
        return {
            "version": SCHEMA_VERSION,
            "long_outcomes_by_symbol": {},
            "last_verdict_by_symbol": {},
            "halted_symbols": {},
        }

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._empty_state()
        try:
            with self._state_path.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("sprt_class_halt_state unreadable, treating as empty: %s", exc)
            return self._empty_state()
        if not isinstance(state, dict):
            return self._empty_state()
        state.setdefault("version", SCHEMA_VERSION)
        state.setdefault("long_outcomes_by_symbol", {})
        state.setdefault("last_verdict_by_symbol", {})
        state.setdefault("halted_symbols", {})
        if not isinstance(state["long_outcomes_by_symbol"], dict):
            state["long_outcomes_by_symbol"] = {}
        if not isinstance(state["last_verdict_by_symbol"], dict):
            state["last_verdict_by_symbol"] = {}
        if not isinstance(state["halted_symbols"], dict):
            state["halted_symbols"] = {}
        return state

    def _persist(self, state: Mapping[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(self._state_path, dict(state))

    def record_long_outcome(
        self,
        symbol: str,
        *,
        was_win: bool,
        direction: str = "LONG",
        dispatch: bool = True,
    ) -> SprtClassHaltDecision:
        """Record one live LONG outcome and return the updated halt decision.

        Only the first ``sprt_halt.trigger_n`` LONG outcomes are used for the
        hard halt. Later outcomes do not erase or create a first-N halt decision;
        ongoing all-trade SPRT/CUSUM remains handled by ``SPRTMonitor``.
        """
        normalized_symbol = str(symbol or "")
        if str(direction or "").upper() != "LONG":
            return self.evaluate_gate(normalized_symbol)

        state = self._load_state()
        outcomes_by_symbol = state["long_outcomes_by_symbol"]
        outcomes = list(outcomes_by_symbol.get(normalized_symbol) or [])
        max_n = _trigger_n(self.config)
        if len(outcomes) < max_n:
            outcomes.append({"win": bool(was_win), "ts": _now_iso()})
            outcomes_by_symbol[normalized_symbol] = outcomes

        wins = sum(1 for item in outcomes if isinstance(item, Mapping) and item.get("win"))
        result = check(
            normalized_symbol,
            LONG_n=len(outcomes),
            LONG_wins=wins,
            config=dict(self.config),
        )
        result_record = _result_to_record(result)
        result_record["updated_at"] = _now_iso()
        result_record["first_n_locked"] = len(outcomes) >= max_n
        result_record["long_wins"] = wins
        state["last_verdict_by_symbol"][normalized_symbol] = result_record

        if result.verdict == "HALT_TRIGGERED":
            halted = dict(state["halted_symbols"].get(normalized_symbol) or {})
            halted.setdefault("halted_at", _now_iso())
            halted.update(result_record)
            state["halted_symbols"][normalized_symbol] = halted

        self._persist(state)

        if dispatch and result.verdict in {"HALT_TRIGGERED", "EARLY_WARNING"}:
            dispatch_alert(result)

        return self._decision_from_result(normalized_symbol, result, state=state)

    def evaluate_gate(self, symbol: str) -> SprtClassHaltDecision:
        """Return the current runtime gate decision for ``symbol``."""
        state = self._load_state()
        record = (
            state.get("halted_symbols", {}).get(symbol)
            or state.get("last_verdict_by_symbol", {}).get(symbol)
            or {}
        )
        return self._decision_from_record(str(symbol or ""), record, state=state)

    def _decision_from_result(
        self,
        symbol: str,
        result: HaltCheckResult,
        *,
        state: Mapping[str, Any],
    ) -> SprtClassHaltDecision:
        record = _result_to_record(result)
        return self._decision_from_record(symbol, record, state=state)

    def _decision_from_record(
        self,
        symbol: str,
        record: Mapping[str, Any],
        *,
        state: Mapping[str, Any],
    ) -> SprtClassHaltDecision:
        block = _config_block(self.config)
        enabled = bool(block.get("enabled", False))
        automation_enabled = bool(block.get("automation_enabled", False))
        verdict = str(record.get("verdict") or "OK")
        would_block = enabled and verdict == "HALT_TRIGGERED"
        should_block = bool(would_block and automation_enabled)
        if not enabled:
            reason = "sprt_class_halt_disabled"
        elif should_block:
            reason = "sprt_class_halt_active_block"
        elif would_block:
            reason = "shadow_sprt_class_halt_would_block"
        elif record:
            reason = f"sprt_class_halt_{verdict.lower()}"
        else:
            reason = "sprt_class_halt_no_state"
        return SprtClassHaltDecision(
            enabled=enabled,
            automation_enabled=automation_enabled,
            symbol=symbol,
            should_block=should_block,
            would_block=would_block,
            reason=reason,
            verdict=verdict,
            class_name=record.get("class_name"),
            actual_wr=record.get("actual_wr"),
            threshold_breached=record.get("threshold_breached"),
            n=int(record.get("n") or 0),
            evidence={
                "state_path": str(self._state_path),
                "last_verdict": dict(record or {}),
                "halted_symbols": sorted((state.get("halted_symbols") or {}).keys()),
            },
        )

    @property
    def state_path(self) -> Path:
        return self._state_path
