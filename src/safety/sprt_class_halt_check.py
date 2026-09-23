"""C.3 — Per-class LONG-WR-watch SPRT halt check (2026-04-26).

Stateless checker layered ALONGSIDE the existing per-instrument
``src/components/sprt_monitor.py``. Caller passes
``(instrument, LONG_n, LONG_wins, config)`` and gets a verdict per the
per-class thresholds in ``config/agent_config.yaml`` ``sprt_halt`` block.

Pure function, no side effects, no disk I/O. The caller (operator on
Monday, or the orchestrator post-trade callback in week 1) is
responsible for any alerting / halt enforcement.

Class definitions (per CEO C.3 brief, 2026-04-26):

    metals     : XAUUSD, XAGUSD
                  Wilson 95% LB 56.31% on n=186 batch; halt at <55%
                  (<1pp safety margin), early-warning at <50%
    indices    : US30, US30_cash, NAS100
                  Wilson 95% LB 46.04% on n=132 batch; halt at <40%
                  (<6pp safety margin — conservative), early-warning at <35%
    jpy_pairs  : USDJPY, GBPJPY
                  Wilson 95% LB 44.90% on n=61 batch; halt at <45% (~LB),
                  early-warning at <40%
    tight_fx   : EXCLUDED — n=5 batch insufficient to calibrate threshold.
                  GBPUSD (observer-only) + EURUSD (deferred) report
                  ``CLASS_EXCLUDED``; the operator should NOT halt on these.

Verdicts:

    OK                  — within thresholds OR feature disabled
    EARLY_WARNING       — WR below early_warning_wr_pct (n >= early_warning_n)
    HALT_TRIGGERED      — n >= trigger_n AND WR < halt_wr_pct
    INSUFFICIENT_DATA   — n < early_warning_n
    CLASS_EXCLUDED      — instrument not in any configured class

Manual usage (Monday)::

    import yaml
    from src.safety.sprt_class_halt_check import check
    config = yaml.safe_load(open("config/agent_config.yaml"))
    print(check("XAUUSD", LONG_n=20, LONG_wins=10, config=config).message)

Automated usage (week 1):
    Hook into orchestrator post-trade callback; emit Telegram alert on
    ``EARLY_WARNING`` and trigger ``ExecutionDenial`` on ``HALT_TRIGGERED``.
    The orchestrator runtime bridge enforces this when
    ``sprt_halt.automation_enabled: true``.

CLI usage::

    python -m src.safety.sprt_class_halt_check XAUUSD 20 10
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Literal, Optional

logger = logging.getLogger(__name__)

Verdict = Literal[
    "OK",
    "EARLY_WARNING",
    "HALT_TRIGGERED",
    "INSUFFICIENT_DATA",
    "CLASS_EXCLUDED",
]


@dataclass
class HaltCheckResult:
    """Outcome of a class-aware LONG-WR-watch SPRT halt check.

    Attributes:
        verdict             — one of the ``Verdict`` literal strings
        class_name          — resolved class (``"metals"``/``"indices"``/
                              ``"jpy_pairs"``) or ``None`` when the
                              instrument is not configured
        threshold_breached  — the threshold value compared against (None
                              for OK / INSUFFICIENT_DATA / CLASS_EXCLUDED)
        actual_wr           — observed WR percentage (0-100) or None
        n                   — LONG_n echoed back for caller convenience
        message             — human-readable diagnostic line; safe to
                              forward to Telegram (see
                              ``src/components/sprt_halt_alert_template.py``
                              for emoji-formatted variant)
    """

    verdict: Verdict
    class_name: Optional[str]
    threshold_breached: Optional[float]
    actual_wr: Optional[float]
    n: int
    message: str


def find_class_for_instrument(instrument: str, config: dict) -> Optional[str]:
    """Return class name for ``instrument``, or ``None`` if not in any class.

    Lookup is case-sensitive against the ``instruments`` list of each
    ``sprt_halt.per_class_thresholds.<class>`` block. Returns the first
    matching class name. ``None`` means either the instrument is in the
    EXCLUDED tight-FX bucket (e.g. GBPUSD, EURUSD) or the class config is
    missing entirely.
    """
    if not isinstance(config, dict):
        return None
    sprt_cfg = config.get("sprt_halt") or {}
    per_class = sprt_cfg.get("per_class_thresholds") or {}
    for cls_name, cls_data in per_class.items():
        if not isinstance(cls_data, dict):
            continue
        instruments = cls_data.get("instruments") or []
        if instrument in instruments:
            return cls_name
    return None


def check(
    instrument: str,
    LONG_n: int,
    LONG_wins: int,
    config: dict,
) -> HaltCheckResult:
    """Class-aware LONG-WR-watch SPRT halt check.

    Pure function — no side effects, no I/O. See module docstring for the
    verdict table + class definitions.

    Args:
        instrument:  symbol identifier (e.g. ``"XAUUSD"``); compared
                     case-sensitively against the per-class instrument
                     lists.
        LONG_n:      number of LONG fills observed for this instrument so
                     far. Must be >= 0.
        LONG_wins:   number of LONG wins among ``LONG_n``. Must satisfy
                     ``0 <= LONG_wins <= LONG_n``.
        config:      parsed ``agent_config.yaml`` dict. Reads the
                     ``sprt_halt`` block; everything else ignored.

    Returns:
        ``HaltCheckResult`` — see attribute docstring.
    """
    # --- Defensive input handling ------------------------------------------
    if LONG_n < 0:
        raise ValueError(f"LONG_n must be >= 0, got {LONG_n}")
    if LONG_wins < 0 or LONG_wins > LONG_n:
        raise ValueError(
            f"LONG_wins must be in [0, LONG_n={LONG_n}], got {LONG_wins}"
        )

    sprt_cfg = (config or {}).get("sprt_halt") or {}

    # --- Master switch -----------------------------------------------------
    if not sprt_cfg.get("enabled", False):
        return HaltCheckResult(
            verdict="OK",
            class_name=None,
            threshold_breached=None,
            actual_wr=None,
            n=LONG_n,
            message="sprt_halt disabled in config (enabled=false)",
        )

    # --- Class lookup ------------------------------------------------------
    cls_name = find_class_for_instrument(instrument, config)
    if cls_name is None:
        return HaltCheckResult(
            verdict="CLASS_EXCLUDED",
            class_name=None,
            threshold_breached=None,
            actual_wr=None,
            n=LONG_n,
            message=(
                f"{instrument} not in any class (tight-FX excluded by "
                f"design or instrument not configured); no halt threshold"
            ),
        )

    # cls_name is guaranteed valid here; per_class block guaranteed dict.
    cls_thresholds = sprt_cfg["per_class_thresholds"][cls_name]
    trigger_n = int(sprt_cfg.get("trigger_n", 20))
    early_n = int(sprt_cfg.get("early_warning_n", 10))
    halt_threshold = float(cls_thresholds["halt_wr_pct"])
    early_threshold = float(cls_thresholds["early_warning_wr_pct"])

    # --- Insufficient sample ----------------------------------------------
    if LONG_n < early_n:
        return HaltCheckResult(
            verdict="INSUFFICIENT_DATA",
            class_name=cls_name,
            threshold_breached=None,
            actual_wr=None,
            n=LONG_n,
            message=(
                f"{instrument} ({cls_name}): n={LONG_n} < "
                f"early_warning_n={early_n} (need more samples)"
            ),
        )

    # --- WR computation ---------------------------------------------------
    wr = (LONG_wins / LONG_n) * 100.0 if LONG_n > 0 else 0.0

    # --- HALT check (only at >= trigger_n) -------------------------------
    if LONG_n >= trigger_n and wr < halt_threshold:
        return HaltCheckResult(
            verdict="HALT_TRIGGERED",
            class_name=cls_name,
            threshold_breached=halt_threshold,
            actual_wr=wr,
            n=LONG_n,
            message=(
                f"HALT: {instrument} ({cls_name}) LONG WR {wr:.1f}% "
                f"< {halt_threshold:.1f}% threshold (n={LONG_n}). "
                f"Per C.3 class-aware SPRT, halt {instrument} pending "
                f"CEO council."
            ),
        )

    # --- EARLY WARNING (any n >= early_n with WR below early threshold) --
    if wr < early_threshold:
        return HaltCheckResult(
            verdict="EARLY_WARNING",
            class_name=cls_name,
            threshold_breached=early_threshold,
            actual_wr=wr,
            n=LONG_n,
            message=(
                f"EARLY WARNING: {instrument} ({cls_name}) LONG WR "
                f"{wr:.1f}% < {early_threshold:.1f}% (n={LONG_n}). "
                f"Halt threshold is {halt_threshold:.1f}%. Monitor closely."
            ),
        )

    # --- All clear ---------------------------------------------------------
    return HaltCheckResult(
        verdict="OK",
        class_name=cls_name,
        threshold_breached=halt_threshold,
        actual_wr=wr,
        n=LONG_n,
        message=(
            f"OK: {instrument} ({cls_name}) LONG WR {wr:.1f}% n={LONG_n} "
            f"(halt threshold {halt_threshold:.1f}%, "
            f"early-warning {early_threshold:.1f}%)"
        ),
    )


# --------------------------------------------------------------------------
# CLI entry point — for Monday operator use
# --------------------------------------------------------------------------

def _cli_main(argv: Optional[list] = None) -> int:
    """CLI for manual operator enforcement on Monday.

    Example::

        python -m src.safety.sprt_class_halt_check XAUUSD 20 10
        # => HALT_TRIGGERED: XAUUSD (metals) LONG WR 50.0% < 55.0% threshold...

    Exit codes:
        0  — OK or INSUFFICIENT_DATA or CLASS_EXCLUDED (no action required)
        1  — EARLY_WARNING (operator action: monitor + flag CEO)
        2  — HALT_TRIGGERED (operator action: stop instrument, ping CEO)
        3  — bad arguments
    """
    parser = argparse.ArgumentParser(
        prog="python -m src.safety.sprt_class_halt_check",
        description=(
            "C.3 class-aware LONG-WR-watch SPRT halt checker. Loads "
            "agent_config.yaml and prints the verdict for the given "
            "instrument + LONG fill counts."
        ),
    )
    parser.add_argument("instrument", help="Symbol, e.g. XAUUSD")
    parser.add_argument("long_n", type=int, help="Number of LONG fills observed")
    parser.add_argument("long_wins", type=int, help="Number of LONG wins")
    parser.add_argument(
        "--config",
        default="config/agent_config.yaml",
        help="Path to agent_config.yaml (default: config/agent_config.yaml)",
    )
    args = parser.parse_args(argv)

    try:
        # Lazy-import yaml so the unit tests can call ``check()`` directly
        # without requiring PyYAML on the module-import path.
        import yaml  # type: ignore

        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: config file not found: {args.config}", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"ERROR: failed to load config: {e}", file=sys.stderr)
        return 3

    try:
        result = check(args.instrument, args.long_n, args.long_wins, config)
    except ValueError as e:
        print(f"ERROR: invalid arguments: {e}", file=sys.stderr)
        return 3

    print(f"{result.verdict}: {result.message}")

    if result.verdict == "HALT_TRIGGERED":
        return 2
    if result.verdict == "EARLY_WARNING":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli_main())
