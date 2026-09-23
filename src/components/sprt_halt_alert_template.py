"""C.3 — Telegram alert template for class-aware LONG-WR-watch SPRT halts.

Companion to ``src/safety/sprt_class_halt_check.py``. Takes a
``HaltCheckResult`` and returns a Telegram-ready message string.

Usage::

    from src.safety.sprt_class_halt_check import check
    from src.components.sprt_halt_alert_template import format_telegram_alert

    result = check("XAUUSD", LONG_n=20, LONG_wins=10, config=cfg)
    msg = format_telegram_alert(result)
    bot.send_message(chat_id=..., text=msg)

The template is intentionally a pure function with no Telegram coupling —
the bot lives in the Claw Empire codebase and consumes the formatted text.

Severity glyph table:

    HALT_TRIGGERED     -> alarm-bell glyph
    EARLY_WARNING      -> warning glyph
    OK                 -> check-mark glyph
    INSUFFICIENT_DATA  -> hourglass glyph
    CLASS_EXCLUDED     -> info glyph
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.safety.sprt_class_halt_check import HaltCheckResult


# Map verdict -> (glyph, header). Glyphs are unicode emoji to match the
# other Telegram alert templates in this codebase (see
# ``src/safety/heartbeat_monitor.py`` for the existing convention).
_VERDICT_FORMATS = {
    "HALT_TRIGGERED": ("\U0001F6A8", "HALT TRIGGERED"),       # 🚨
    "EARLY_WARNING":  ("⚠️", "EARLY WARNING"),       # ⚠️
    "OK":              ("✅", "OK"),                       # ✅
    "INSUFFICIENT_DATA": ("⏳", "INSUFFICIENT DATA"),       # ⏳
    "CLASS_EXCLUDED":   ("ℹ️", "CLASS EXCLUDED"),     # ℹ️
}


def format_telegram_alert(check_result: "HaltCheckResult") -> str:
    """Return a Telegram-ready alert string for a halt-check result.

    The output is plain text (no Markdown / HTML escaping required) and
    safe to send directly to ``@gold_trader_os_bot``. Lines wrap naturally
    on a phone screen.

    Format:

        <glyph> <HEADER>: <instrument> (<class>)

        LONG WR: <wr>% (n=<n>)
        Threshold: <halt_threshold>% (early-warning <early>%)

        <full message from HaltCheckResult>

    For ``CLASS_EXCLUDED`` and ``INSUFFICIENT_DATA``, the WR/threshold
    block is omitted.
    """
    glyph, header = _VERDICT_FORMATS.get(
        check_result.verdict, ("", check_result.verdict)
    )

    lines = []
    cls_label = (
        f" ({check_result.class_name})" if check_result.class_name else ""
    )

    # Title line — extract the instrument from the message if it begins with one.
    # We don't carry the instrument on the dataclass to keep it pure-data;
    # the message already contains it as the first whitespace-delimited token
    # in every branch.
    instrument_token = check_result.message.split(" ", 1)[0].rstrip(":")
    # Strip any leading verdict prefix like "HALT:" / "EARLY WARNING:" /
    # "OK:" so we don't print it twice.
    for prefix in ("HALT:", "EARLY", "OK:"):
        if instrument_token == prefix:
            # Use the next token instead.
            parts = check_result.message.split(" ", 2)
            if len(parts) >= 3:
                instrument_token = parts[1].rstrip(":")
            break

    lines.append(f"{glyph} {header}: {instrument_token}{cls_label}".strip())

    if check_result.actual_wr is not None:
        lines.append("")
        lines.append(
            f"LONG WR: {check_result.actual_wr:.1f}% (n={check_result.n})"
        )
        if check_result.threshold_breached is not None:
            lines.append(
                f"Threshold: {check_result.threshold_breached:.1f}%"
            )

    lines.append("")
    lines.append(check_result.message)

    if check_result.verdict == "HALT_TRIGGERED":
        lines.append("")
        lines.append("ACTION: Stop this instrument now. Convene CEO council.")
    elif check_result.verdict == "EARLY_WARNING":
        lines.append("")
        lines.append("ACTION: Continue but flag CEO. Halt threshold is close.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Persistent dispatch (H7, 2026-04-26)
# ---------------------------------------------------------------------------


def dispatch_alert(check_result: "HaltCheckResult") -> str:
    """Format + send the SPRT-halt alert via the persistent notification queue.

    Routing matrix:

    * ``HALT_TRIGGERED``    -> CRITICAL (indefinite retry, 24h age-out)
    * ``EARLY_WARNING``     -> HIGH (5-retry exponential backoff)
    * Everything else       -> no-op (returns the formatted string for
      logging/logging-only paths but does not enqueue)

    Returns the formatted alert text (the same string ``format_telegram_alert``
    would return) so callers that want both the side effect and the rendered
    text can keep one call site.

    The queue subsystem is imported lazily so this module remains importable
    in test contexts that don't pull in ``src.utils.notification_queue``.
    A failure in the queue path falls back to a logged warning — the SPRT
    halt verdict is also persisted in the watchdog logs and post-trade
    diagnostics, so an outright dispatch failure is recoverable.
    """
    text = format_telegram_alert(check_result)
    verdict = check_result.verdict
    if verdict not in ("HALT_TRIGGERED", "EARLY_WARNING"):
        return text
    try:
        from src.utils.notification_queue import Level, send as _q_send
        level = (
            Level.CRITICAL
            if verdict == "HALT_TRIGGERED"
            else Level.HIGH
        )
        _q_send(text, level=level)
    except Exception as e:
        logger.warning(
            "sprt_halt_alert_template.dispatch_alert: queue dispatch failed "
            "(%s); alert NOT delivered: %s",
            e,
            text[:80],
        )
    return text
