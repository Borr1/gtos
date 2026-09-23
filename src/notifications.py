"""Telegram trade signal notifications.

Sends trade events to Telegram with clear, scannable formatting.
Uses only stdlib — no external dependencies. Runs in background threads
to never block the trading pipeline.

Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment / .env.
If either is missing, all calls silently no-op.

Daily P&L state persisted to shadow_logs/daily_pnl.json — resets each day.

Formatting policy (HTML-ESCAPE BUG, 2026-04-28)
-----------------------------------------------
This module sends messages as **plain text** — ``parse_mode`` is NOT set on
the Telegram POST. Rationale:

* Trade alerts and system alerts interpolate runtime values (P&L strings,
  comparison operators, dollar amounts, free-text reasons). Any one of
  these may legitimately contain ``<``, ``>``, or ``&``.
* Under ``parse_mode=HTML`` an unescaped ``&`` (e.g. literal ``P&L:``) or
  ``<=`` (e.g. ``-4.00% <= cap``) yields a Telegram 400 Bad Request, which
  the queue retries indefinitely → log spam + the CEO never sees the
  alert.
* Live-fired root cause: 2026-04-27 23:00 UTC GBPJPY daily-loss-stop
  produced 100+ HTTP 400 storms in ``pipeline_state/notification_queue.jsonl``
  because the alert body contained literal ``P&L:`` and ``<= -4.00%``.

Policy: alert templates may contain unicode emoji glyphs but MUST NOT
contain HTML tags (``<b>``, ``<i>``, ``<code>``, etc.). New call sites
should follow this convention to keep the wire format escape-free.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import logging
import os
import ssl
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
_PNL_PATH = Path("shadow_logs/daily_pnl.json")
# Append-only audit ledger — never overwritten on date rollover, never
# deduplicated. Every recorded close-event lands here as one JSON line so
# post-hoc audits and FN compliance reviews have a tamper-evident trail
# that survives both the daily-rollover wipe of ``_PNL_PATH`` and the
# trade_id dedup applied to that path.
_PNL_HISTORY_PATH = Path("shadow_logs/daily_pnl_history.jsonl")
_PNL_R_EVIDENCE_CLASS = "LOCAL_NOTIFICATION_R_INPUT"
_PNL_DOLLAR_EVIDENCE_CLASS = "LOCAL_RISK_DOLLAR_PROJECTION"
_PNL_BROKER_DOLLAR_EVIDENCE_CLASS = "BROKER_DEAL_RECONCILED_PROFIT"
_PNL_ACCOUNT_TRUTH_STATUS = "NOT_ACCOUNT_HISTORY_RECONCILED_AT_NOTIFICATION_TIME"
_PNL_BROKER_ACCOUNT_TRUTH_STATUS = "BROKER_DEAL_RECONCILED_AT_NOTIFICATION_TIME"
_PNL_THREAD_LOCK = threading.RLock()

# Dollar conversion for operator cards. Unset until the caller passes the
# account balance and the risk percent. A missing balance is not $100,000
# and a missing risk is not 2%. Nothing here asks for a number.
_ACCOUNT_BALANCE: float | None = None
_RISK_PCT: float | None = None
_RISK_DOLLARS: float | None = None


def configure_notifications(
    risk_per_trade_pct: float, account_balance: float | None = None,
) -> None:
    """Set the risk$ conversion used by dollar formatting.

    Args:
        risk_per_trade_pct: Risk per trade in PERCENT UNITS (e.g. 2.0 for 2%),
            matching ``config['risk']['risk_per_trade_pct']``.
        account_balance: Starting equity in USD. Omitted means the balance
            was not passed. The conversion stays unset. It does not invent one.

    Call once at orchestrator startup AFTER apply_profile_overrides +
    apply_instrument_overrides have resolved the effective risk%.
    """
    global _ACCOUNT_BALANCE, _RISK_PCT, _RISK_DOLLARS
    if account_balance is None:
        logger.info("notifications dollar conversion unchanged: balance not passed")
        return
    _ACCOUNT_BALANCE = float(account_balance)
    _RISK_PCT = float(risk_per_trade_pct) / 100.0
    _RISK_DOLLARS = _ACCOUNT_BALANCE * _RISK_PCT
    logger.info(
        "notifications configured: account=$%s, risk=%.2f%%, $/R=$%s",
        f"{_ACCOUNT_BALANCE:,.0f}", risk_per_trade_pct,
        f"{_RISK_DOLLARS:,.0f}",
    )

# Reusable SSL context — Windows systems may have cert chain issues
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


# ── Telegram transport ──────────────────────────────────────────────────────

def _send(text: str) -> None:
    """POST a plain-text message to Telegram.

    NOTE: ``parse_mode`` is intentionally NOT set — see the module docstring
    for the rationale. All callers may interpolate raw runtime values
    (including ``<``, ``>``, ``&``) without escaping.

    Refuses outright unless this process has been positively authorized to
    page the operator (F30 / Q7). Credential presence is not an authorization
    decision — this is the legacy fire-and-forget path that every ``notify_*``
    helper falls back to when the queue subsystem is unavailable, so an
    unauthorized process reaching here must send nothing. See
    ``src/safety/notification_authorization.py``.
    """
    from src.safety.notification_authorization import delivery_authorization

    _auth = delivery_authorization()
    if not _auth.allowed:
        logger.error(
            "Telegram send REFUSED (unauthorized process): %s | preview=%r",
            _auth.detail, text[:120],
        )
        return
    if not _TOKEN or not _CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": _CHAT_ID,
        "text": text,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # The post has no bar and no cycle expiry, and _send_async already
        # runs it off the book thread. No static socket cut.
        with urllib.request.urlopen(req, timeout=None, context=_SSL_CTX) as resp:
            if resp.status != 200:
                logger.warning("Telegram send returned %d", resp.status)
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)


def _send_async(text: str) -> None:
    """Fire-and-forget in daemon thread — never blocks the pipeline."""
    t = threading.Thread(target=_send, args=(text,), daemon=True)
    t.start()


# ── Daily P&L tracker ──────────────────────────────────────────────────────

@contextmanager
def _exclusive_file_lock(fh):
    if os.name == "nt":
        import msvcrt

        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@contextmanager
def _pnl_state_lock():
    lock_path = _PNL_PATH.parent / "daily_pnl.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _PNL_THREAD_LOCK:
        with lock_path.open("a+", encoding="utf-8") as fh:
            with _exclusive_file_lock(fh):
                yield


def _load_pnl_unlocked() -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        if _PNL_PATH.exists():
            data = json.loads(_PNL_PATH.read_text(encoding="utf-8"))
            if data.get("date") == today:
                return data
    except Exception:
        pass
    return {"date": today, "trades": [], "total_r": 0.0, "wins": 0, "losses": 0}


def _load_pnl() -> dict:
    with _pnl_state_lock():
        return _load_pnl_unlocked()


def _save_pnl_unlocked(data: dict) -> None:
    try:
        _PNL_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = _PNL_PATH.with_name(
            f".{_PNL_PATH.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        try:
            tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            os.replace(tmp_path, _PNL_PATH)
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
    except Exception as e:
        logger.warning("Failed to save daily P&L state: %s", e)


def _save_pnl(data: dict) -> None:
    with _pnl_state_lock():
        _save_pnl_unlocked(data)


def _append_history_unlocked(entry: dict) -> None:
    """Append one close-event row to ``daily_pnl_history.jsonl``.

    This file is the audit-grade ledger: append-only, never deduplicated,
    never wiped on date rollover. Survives BUG #31-class double-fires,
    process restarts, and date boundaries; the ``daily_pnl.json`` file
    can be rebuilt from it offline if the in-flight aggregation ever
    diverges from broker reality. Failure here is best-effort — the
    Telegram notification path must never block.
    """
    try:
        _PNL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _PNL_HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except Exception as e:
        logger.warning("Failed to append daily P&L history: %s", e)


def _append_history(entry: dict) -> None:
    with _pnl_state_lock():
        _append_history_unlocked(entry)


def _recompute_pnl_aggregates(pnl: dict) -> None:
    trades = pnl.get("trades") or []
    pnl["total_r"] = round(sum(t["result_r"] for t in trades), 4)
    pnl["total_local_projected_usd"] = round(sum(
        (
            t.get("local_projected_usd")
            if t.get("local_projected_usd") is not None
            else (t.get("realized_usd") or 0.0)
        )
        for t in trades
    ), 2)
    actual_values = [
        float(t.get("realized_usd") or 0.0)
        for t in trades
        if t.get("actual_dollar_claim_allowed") is True
        and t.get("realized_usd") is not None
    ]
    pnl["total_actual_realized_usd"] = (
        round(sum(actual_values), 2) if actual_values else None
    )
    all_actual = bool(trades) and all(
        t.get("actual_dollar_claim_allowed") is True
        and t.get("realized_usd") is not None
        for t in trades
    )
    pnl["total_usd"] = pnl["total_actual_realized_usd"] if all_actual else None
    pnl["total_actual_dollar_claim_allowed"] = all_actual
    if all_actual:
        pnl["total_usd_evidence_class"] = _PNL_BROKER_DOLLAR_EVIDENCE_CLASS
    elif actual_values:
        pnl["total_usd_evidence_class"] = "MIXED_BROKER_REALIZED_AND_LOCAL_PROJECTION"
    else:
        pnl["total_usd_evidence_class"] = _PNL_DOLLAR_EVIDENCE_CLASS
    wins = 0
    losses = 0
    for trade in trades:
        outcome_value = float(trade.get("result_r") or 0.0)
        if outcome_value == 0 and trade.get("realized_usd") is not None:
            outcome_value = float(trade.get("realized_usd") or 0.0)
        if outcome_value > 0:
            wins += 1
        else:
            losses += 1
    pnl["wins"] = wins
    pnl["losses"] = losses


def _record_trade(*args, **kwargs) -> dict:
    with _pnl_state_lock():
        return _record_trade_unlocked(*args, **kwargs)


def _record_trade_unlocked(
    symbol: str, result_r: float, exit_type: str,
    trade_id: str = "", entry_price: float = 0.0, exit_price: float = 0.0,
    hold_minutes: float | None = None,
    vnext_context: dict | None = None,
    broker_profit: float | None = None,
    broker_net_profit: float | None = None,
    broker_deal_reconciled: bool = False,
    broker_deal_id: int | str | None = None,
    broker_close_order_id: int | str | None = None,
    broker_commission: float | None = None,
    broker_swap: float | None = None,
    broker_fee: float | None = None,
) -> dict:
    """Record a trade result and return updated P&L state.

    Behavior:
        * Loads today's ``daily_pnl.json`` (resets on UTC date rollover).
        * If ``trade_id`` is non-empty AND already present in today's
          ``pnl["trades"]``, this is a duplicate dispatch (orchestrator
          + execution-engine both fired ``notify_trade_closed`` for the
          same close — see ``_notify_close_if_unsent`` rationale). In
          that case the file is NOT mutated and the existing pnl state
          is returned. The Telegram message still goes out so the
          operator sees a consistent total even on the duplicate.
        * Otherwise, appends a new entry with full metadata
          (``trade_id``, ``realized_usd``, ``hold_minutes``,
          ``entry_price``, ``exit_price``) and updates aggregates.
        * Always appends one row to ``daily_pnl_history.jsonl`` — that
          file is the audit-grade ledger and is intentionally NOT
          deduplicated. Forensic tools post-hoc collapse duplicates by
          ``trade_id``; the operator-facing aggregates use the
          dedup-enforced ``daily_pnl.json``.

    Args:
        symbol: instrument code, e.g. ``"GBPJPY"``.
        result_r: realized R-multiple (signed).
        exit_type: free-form exit reason — ``"tp_hit"``, ``"sl_hit"``,
            ``"sl_modification_failed"``, ``"j46_j49_time_stop"``,
            ``"broker_closed"``, ``"manual"``, ``"timeout"``, etc.
        trade_id: stable identifier for this position. Recommended:
            the ``metadata.trade_id`` from the trade record (e.g.
            ``"GBPJPY_2026-04-28_london_0900"``) or the
            ``"adopted_{ticket}"`` form for orphan-adopted positions.
            When empty, dedup is skipped (legacy callers).
        entry_price: optional fill price for audit trail.
        exit_price: optional close price for audit trail.
        hold_minutes: optional hold duration (minutes).

    Returns:
        The current pnl state dict (post-mutation if a record was added,
        unchanged if dedup hit).
    """
    pnl = _load_pnl_unlocked()
    now_utc = datetime.now(timezone.utc)
    local_projected_usd = (
        None if _RISK_DOLLARS is None else round(result_r * _RISK_DOLLARS, 2)
    )
    broker_profit_value = None
    broker_net_profit_value = None
    if broker_deal_reconciled and broker_net_profit is not None:
        try:
            broker_net_profit_value = float(broker_net_profit)
        except (TypeError, ValueError):
            broker_net_profit_value = None
    if broker_deal_reconciled and broker_profit is not None:
        try:
            broker_profit_value = float(broker_profit)
        except (TypeError, ValueError):
            broker_profit_value = None
    realized_broker_value = (
        broker_net_profit_value
        if broker_net_profit_value is not None
        else broker_profit_value
    )
    realized_usd = (
        round(realized_broker_value, 2)
        if realized_broker_value is not None
        else None
    )
    dollar_evidence_class = (
        _PNL_BROKER_DOLLAR_EVIDENCE_CLASS
        if realized_broker_value is not None
        else _PNL_DOLLAR_EVIDENCE_CLASS
    )
    account_truth_status = (
        _PNL_BROKER_ACCOUNT_TRUTH_STATUS
        if realized_broker_value is not None
        else _PNL_ACCOUNT_TRUTH_STATUS
    )
    actual_dollar_claim_allowed = realized_broker_value is not None

    # Always log to the audit ledger BEFORE dedup. Even duplicate dispatches
    # have forensic value (they confirm both the orchestrator path and the
    # BUG #31 fallback fired for the same close — useful for tuning the
    # dedup set's lifecycle).
    history_entry = {
        "ts_utc": now_utc.isoformat(),
        "symbol": symbol,
        "trade_id": trade_id,
        "result_r": round(result_r, 4),
        "realized_usd": realized_usd,
        "local_projected_usd": local_projected_usd,
        "r_evidence_class": _PNL_R_EVIDENCE_CLASS,
        "dollar_evidence_class": dollar_evidence_class,
        "actual_r_claim_allowed": False,
        "actual_dollar_claim_allowed": actual_dollar_claim_allowed,
        "account_truth_status": account_truth_status,
        "exit_type": exit_type,
        "entry_price": float(entry_price) if entry_price else None,
        "exit_price": float(exit_price) if exit_price else None,
        "hold_minutes": (
            round(float(hold_minutes), 2) if hold_minutes is not None else None
        ),
        "risk_dollars": None if _RISK_DOLLARS is None else round(_RISK_DOLLARS, 2),
    }
    if broker_profit_value is not None:
        history_entry.update({
            "broker_profit": round(broker_profit_value, 2),
            "broker_deal_reconciled": True,
            "broker_deal_id": broker_deal_id,
            "broker_close_order_id": broker_close_order_id,
            "broker_commission": broker_commission,
            "broker_swap": broker_swap,
            "broker_fee": broker_fee,
        })
    if broker_net_profit_value is not None:
        history_entry["broker_net_profit"] = round(broker_net_profit_value, 2)
    if vnext_context:
        history_entry["gtos_vnext_notification_context"] = vnext_context
    _append_history_unlocked(history_entry)

    trade_entry = {
        "symbol": symbol,
        "trade_id": trade_id,
        "result_r": round(result_r, 4),
        "realized_usd": realized_usd,
        "local_projected_usd": local_projected_usd,
        "r_evidence_class": _PNL_R_EVIDENCE_CLASS,
        "dollar_evidence_class": dollar_evidence_class,
        "actual_r_claim_allowed": False,
        "actual_dollar_claim_allowed": actual_dollar_claim_allowed,
        "account_truth_status": account_truth_status,
        "exit_type": exit_type,
        "entry_price": float(entry_price) if entry_price else None,
        "exit_price": float(exit_price) if exit_price else None,
        "hold_minutes": (
            round(float(hold_minutes), 2) if hold_minutes is not None else None
        ),
        "time": now_utc.strftime("%H:%M:%S"),
    }
    if broker_profit_value is not None:
        trade_entry.update({
            "broker_profit": round(broker_profit_value, 2),
            "broker_deal_reconciled": True,
            "broker_deal_id": broker_deal_id,
            "broker_close_order_id": broker_close_order_id,
            "broker_commission": broker_commission,
            "broker_swap": broker_swap,
            "broker_fee": broker_fee,
        })
    if broker_net_profit_value is not None:
        trade_entry["broker_net_profit"] = round(broker_net_profit_value, 2)
    if vnext_context:
        trade_entry["gtos_vnext_notification_context"] = vnext_context

    # Idempotency: skip mutation if this trade_id is already recorded
    # today. Returns the existing aggregate so callers (Telegram message
    # builder) still display a consistent total.
    if trade_id:
        for existing in pnl.get("trades", []):
            if existing.get("trade_id") == trade_id:
                upgrade_entry = dict(trade_entry)
                if (
                    upgrade_entry.get("result_r") == 0
                    and existing.get("result_r") not in (None, 0, 0.0)
                ):
                    upgrade_entry["result_r"] = existing.get("result_r")
                    upgrade_entry["local_projected_usd"] = existing.get("local_projected_usd")
                if (
                    actual_dollar_claim_allowed
                    and (
                        existing.get("actual_dollar_claim_allowed") is not True
                        or existing.get("realized_usd") != upgrade_entry.get("realized_usd")
                        or existing.get("broker_net_profit") != upgrade_entry.get("broker_net_profit")
                    )
                ):
                    existing.update(upgrade_entry)
                    _recompute_pnl_aggregates(pnl)
                    _save_pnl_unlocked(pnl)
                    logger.info(
                        "daily_pnl: upgraded deduped trade_id=%s with broker account truth "
                        "(history.jsonl row appended for audit)",
                        trade_id,
                    )
                    return pnl
                logger.info(
                    "daily_pnl: dedup hit on trade_id=%s — file unchanged "
                    "(history.jsonl row appended for audit)",
                    trade_id,
                )
                return pnl

    pnl["trades"].append(trade_entry)
    _recompute_pnl_aggregates(pnl)
    _save_pnl_unlocked(pnl)
    return pnl


def record_trade_closed_pnl(
    symbol: str,
    result: str,
    *,
    actual_r: float | None = None,
    hold_minutes: float | None = None,
    trade_id: str = "",
    entry_price: float = 0,
    exit_price: float = 0,
    vnext_context: dict | None = None,
    broker_profit: float | None = None,
    broker_net_profit: float | None = None,
    broker_deal_reconciled: bool = False,
    broker_deal_id: int | str | None = None,
    broker_close_order_id: int | str | None = None,
    broker_commission: float | None = None,
    broker_swap: float | None = None,
    broker_fee: float | None = None,
) -> dict:
    """Record close PnL without dispatching an additional close-card message."""
    return _record_trade(
        symbol,
        actual_r if actual_r is not None else 0.0,
        result,
        trade_id=trade_id,
        entry_price=entry_price,
        exit_price=exit_price,
        hold_minutes=hold_minutes,
        vnext_context=vnext_context,
        broker_profit=broker_profit,
        broker_net_profit=broker_net_profit,
        broker_deal_reconciled=broker_deal_reconciled,
        broker_deal_id=broker_deal_id,
        broker_close_order_id=broker_close_order_id,
        broker_commission=broker_commission,
        broker_swap=broker_swap,
        broker_fee=broker_fee,
    )


# ── Formatting helpers ──────────────────────────────────────────────────────

def _fmt_price(price: float, symbol: str = "") -> str:
    """Format price with appropriate decimals for the instrument."""
    if any(s in symbol.upper() for s in ("JPY", "US30", "XAU")):
        if "JPY" in symbol.upper():
            return f"{price:.3f}"
        return f"{price:.2f}"  # US30, XAUUSD
    return f"{price:.5f}"  # GBPUSD, etc.


def _fmt_dollars(r_value: float) -> str:
    if _RISK_DOLLARS is None:
        return ""
    dollars = r_value * _RISK_DOLLARS
    if dollars >= 0:
        return f"+${dollars:,.0f}"
    return f"-${abs(dollars):,.0f}"


def _fmt_money(dollars: float) -> str:
    if dollars >= 0:
        return f"+${dollars:,.2f}"
    return f"-${abs(dollars):,.2f}"


def _pnl_total_money_text(pnl: dict, r_value: float | None = None) -> str:
    total_usd = pnl.get("total_usd")
    if total_usd is not None:
        return _fmt_money(float(total_usd))
    if pnl.get("total_local_projected_usd") is not None:
        return f"{_fmt_money(float(pnl['total_local_projected_usd']))} projected"
    if r_value is None:
        r_value = float(pnl.get("total_r", 0.0) or 0.0)
    return f"{_fmt_dollars(float(r_value))} projected"


def _fmt_hold_time(minutes: float | None) -> str:
    if minutes is None:
        return "?"
    if minutes < 0:
        return "?"
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def _pnl_line(pnl: dict) -> str:
    """One-line daily summary for appending to trade close messages."""
    r = pnl["total_r"]
    w, l = pnl["wins"], pnl["losses"]
    icon = "\U0001F4C8" if r >= 0 else "\U0001F4C9"  # chart up/down
    dollars_text = _pnl_total_money_text(pnl, r)
    return f"{icon} Today: {r:+.2f}R ({dollars_text}) | {w}W {l}L"


def _has_value(value: Any) -> bool:
    return value is not None and value != ""


def _object_mappings(source: Any) -> list[dict]:
    if source is None:
        return []
    if isinstance(source, dict):
        mappings = [source]
    else:
        try:
            mappings = [vars(source)]
        except TypeError:
            mappings = []

    for mapping in list(mappings):
        for nested_key in (
            "instrumentation",
            "limit_intent",
            "metadata",
            "decision_pipeline",
            "trade_params",
            "gtos_vnext_moonshot_dynamic_execution",
            "gtos_vnext_prop_safe_selector",
            "gtos_vnext_selected_cell_risk",
        ):
            nested = mapping.get(nested_key)
            if isinstance(nested, dict):
                mappings.append(nested)
    return mappings


def _first_context_value(source: Any, *keys: str) -> Any:
    for mapping in _object_mappings(source):
        for key in keys:
            if key in mapping and _has_value(mapping.get(key)):
                return mapping.get(key)
    return None


def _clean_context_value(value: Any) -> str:
    text = str(value)
    for needle, replacement in (
        ("live_current_j46_j49", "superseded_legacy_policy"),
        ("J46-J49", "superseded legacy policy"),
        ("j46_j49", "superseded_legacy_policy"),
        ("J46", "legacy policy"),
        ("J49", "legacy policy"),
        ("fixed 1.5R", "legacy fixed target"),
        ("fixed-1.5R", "legacy fixed target"),
        ("fixed_1_5r", "legacy_fixed_target"),
    ):
        text = text.replace(needle, replacement)
    return text


def _fmt_context_r(value: Any) -> str:
    try:
        return f"{float(value):.2f}R"
    except (TypeError, ValueError):
        return _clean_context_value(value)


def build_vnext_notification_context(
    source: Any = None,
    *,
    lifecycle_event: str | None = None,
    prop_risk_action: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Extract vNext execution truth for Telegram lifecycle notifications."""
    ctx: dict[str, Any] = {}
    field_specs = {
        "selected_policy": (
            "selected_policy",
            "policy",
            "dynamic_policy",
            "gtos_vnext_dynamic_policy_selected",
        ),
        "execution_policy_id": (
            "execution_policy_id",
            "gtos_vnext_execution_policy_id",
        ),
        "origin_family": ("origin_family", "gtos_vnext_origin_family"),
        "activation_family": ("activation_family", "gtos_vnext_activation_family"),
        "selector_row_id": ("selector_row_id", "gtos_vnext_selector_row_id"),
        "selector_proof_hash": (
            "selector_proof_hash",
            "gtos_vnext_selector_proof_hash",
        ),
        "source_event_hash": (
            "source_event_hash",
            "gtos_vnext_source_event_hash",
        ),
        "be_trigger_r": ("be_trigger_r", "gtos_vnext_dynamic_be_trigger_r"),
        "final_target_r": (
            "final_target_r",
            "gtos_vnext_dynamic_final_target_r",
        ),
        "pullback_r": (
            "pullback_r",
            "gtos_vnext_dynamic_momentum_pullback_r",
        ),
        "trail_gap_r": ("trail_gap_r", "gtos_vnext_dynamic_trail_gap_r"),
        "time_stop_bars": (
            "time_stop_bars",
            "gtos_vnext_dynamic_time_stop_bars",
        ),
        "be_trigger_price": (
            "be_trigger_price",
            "gtos_vnext_dynamic_be_trigger_price",
            "gtos_vnext_dynamic_placement_be_trigger_price",
        ),
        "final_target_price": (
            "final_target_price",
            "gtos_vnext_dynamic_final_target_price",
            "gtos_vnext_dynamic_placement_final_target_price",
        ),
        "risk_pct": (
            "risk_pct",
            "gtos_vnext_selected_cell_risk_pct",
            "gtos_vnext_prop_safe_selector_after_risk_pct",
        ),
        "risk_cell": (
            "risk_cell",
            "gtos_vnext_selected_cell_risk_cell_id",
        ),
        "risk_basis": (
            "risk_basis",
            "gtos_vnext_selected_cell_risk_decision_basis",
            "gtos_vnext_risk_reason",
            "gtos_vnext_prop_safe_selector_reason",
        ),
        "risk_selected_policy": (
            "risk_selected_policy",
            "gtos_vnext_selected_cell_risk_selected_policy",
        ),
        "risk_source_policy": (
            "risk_source_policy",
            "gtos_vnext_selected_cell_risk_source_policy",
        ),
        "risk_identity": (
            "risk_identity",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
        ),
        "prop_action": (
            "prop_action",
            "gtos_vnext_dynamic_policy_prop_action",
            "gtos_vnext_prop_safe_selector_action",
        ),
        "production_execution_path": (
            "production_execution_path",
            "gtos_vnext_production_execution_path",
        ),
    }
    for target_key, source_keys in field_specs.items():
        value = _first_context_value(source, *source_keys)
        if _has_value(value):
            ctx[target_key] = value

    if extra:
        for key, value in extra.items():
            if _has_value(value):
                ctx[key] = value
    if prop_risk_action:
        ctx["prop_risk_action"] = prop_risk_action

    has_execution_truth = any(
        key in ctx
        for key in (
            "selected_policy",
            "execution_policy_id",
            "origin_family",
            "selector_row_id",
            "selector_proof_hash",
            "source_event_hash",
            "be_trigger_r",
            "final_target_r",
            "risk_pct",
            "prop_action",
            "production_execution_path",
        )
    )
    if lifecycle_event and has_execution_truth:
        ctx["lifecycle_event"] = lifecycle_event
    return ctx


def _vnext_context_lines(vnext_context: dict | None) -> list[str]:
    if not vnext_context:
        return []
    ctx = {
        key: _clean_context_value(value)
        for key, value in vnext_context.items()
        if _has_value(value)
    }
    lines: list[str] = []
    lifecycle = ctx.get("lifecycle_event")
    if lifecycle:
        lines.append(f"Lifecycle: {lifecycle}")

    policy_parts = []
    if ctx.get("selected_policy"):
        policy_parts.append(f"policy={ctx['selected_policy']}")
    if ctx.get("execution_policy_id"):
        policy_parts.append(f"id={ctx['execution_policy_id']}")
    if policy_parts:
        lines.append("vNext: " + " | ".join(policy_parts))

    origin_parts = []
    if ctx.get("origin_family"):
        origin_parts.append(f"origin={ctx['origin_family']}")
    if ctx.get("activation_family"):
        origin_parts.append(f"activation={ctx['activation_family']}")
    if origin_parts:
        lines.append("Origin: " + " | ".join(origin_parts))

    selector_ref = (
        ctx.get("selector_row_id")
        or ctx.get("selector_proof_hash")
        or ctx.get("source_event_hash")
    )
    if selector_ref:
        lines.append(f"Selector/proof: {selector_ref}")

    dynamic_parts = []
    for label, key in (
        ("trigger", "be_trigger_r"),
        ("final", "final_target_r"),
        ("pullback", "pullback_r"),
        ("trail_gap", "trail_gap_r"),
    ):
        if key in vnext_context and _has_value(vnext_context.get(key)):
            dynamic_parts.append(f"{label}={_fmt_context_r(vnext_context[key])}")
    if ctx.get("time_stop_bars"):
        dynamic_parts.append(f"time_stop={ctx['time_stop_bars']} bars")
    price_parts = []
    if ctx.get("be_trigger_price"):
        price_parts.append(f"trigger_px={ctx['be_trigger_price']}")
    if ctx.get("final_target_price"):
        price_parts.append(f"final_px={ctx['final_target_price']}")
    if dynamic_parts:
        lines.append("Dynamic: " + " | ".join(dynamic_parts))
    if price_parts:
        lines.append("Dynamic prices: " + " | ".join(price_parts))

    risk_parts = []
    if "risk_pct" in vnext_context and _has_value(vnext_context.get("risk_pct")):
        try:
            risk_parts.append(f"pct={float(vnext_context['risk_pct']):.2f}%")
        except (TypeError, ValueError):
            risk_parts.append(f"pct={ctx['risk_pct']}")
    if ctx.get("risk_cell"):
        risk_parts.append(f"cell={ctx['risk_cell']}")
    if ctx.get("risk_basis"):
        risk_parts.append(f"basis={ctx['risk_basis']}")
    if ctx.get("risk_identity"):
        risk_parts.append(f"identity={ctx['risk_identity']}")
    if risk_parts:
        lines.append("Risk: " + " | ".join(risk_parts))

    prop_parts = []
    if ctx.get("prop_action"):
        prop_parts.append(f"prop={ctx['prop_action']}")
    if ctx.get("prop_risk_action"):
        prop_parts.append(f"action={ctx['prop_risk_action']}")
    if ctx.get("production_execution_path"):
        prop_parts.append(f"production_path={ctx['production_execution_path']}")
    if prop_parts:
        lines.append("Prop/risk: " + " | ".join(prop_parts))
    return lines


# ── Public API ──────────────────────────────────────────────────────────────

def notify_candidate(
    symbol: str, direction: str, grade: str, kill_zone: str,
) -> None:
    """No-op — limit order notification fires seconds later, no need to double-ping."""
    pass


def notify_limit_placed(
    symbol: str, direction: str, entry: float, sl: float, tp: float,
    rr: float, kill_zone: str, trade_id: str,
    *,
    dynamic_policy: str | None = None,
    risk_pct: float | None = None,
    origin_family: str | None = None,
    selector_ref: str | None = None,
    vnext_context: dict | None = None,
) -> None:
    sl_dist = abs(entry - sl)
    tp_dist = abs(tp - entry)
    p = lambda v: _fmt_price(v, symbol)
    arrow = "\u2B06\uFE0F" if direction == "LONG" else "\u2B07\uFE0F"

    explicit_context = {
        "dynamic_policy": dynamic_policy,
        "risk_pct": risk_pct,
        "origin_family": origin_family,
        "selector_row_id": selector_ref,
    }
    context = build_vnext_notification_context(
        vnext_context or explicit_context,
        lifecycle_event="limit_placed",
        extra=explicit_context if vnext_context else None,
    )
    extra_lines = _vnext_context_lines(context)
    extra_text = ("\n" + "\n".join(extra_lines)) if extra_lines else ""

    text = (
        f"\U0001F514 LIMIT ORDER  \u2014  {symbol}\n"
        f"{arrow} {direction} @ {p(entry)}\n"
        f"\U0001F6D1 SL: {p(sl)}  ({p(sl_dist)})\n"
        f"\U0001F3AF TP: {p(tp)}  (+{p(tp_dist)})\n"
        f"\U0001F4CA RR: {rr:.1f}"
        + (
            f"  |  Risk: ${_RISK_DOLLARS:,.0f}\n"
            if _RISK_DOLLARS is not None
            else "\n"
        )
        + f"\U0001F552 {kill_zone.capitalize()} KZ"
        f"{extra_text}"
    )
    _send_async(text)


def notify_limit_filled(
    symbol: str, direction: str, entry: float, trade_id: str,
    sl: float = 0, tp: float = 0,
    outside_kz: bool = False,
    vnext_context: dict | None = None,
) -> None:
    p = lambda v: _fmt_price(v, symbol)
    arrow = "\u2B06\uFE0F" if direction == "LONG" else "\u2B07\uFE0F"
    location = " (between KZs)" if outside_kz else ""
    context = build_vnext_notification_context(
        vnext_context,
        lifecycle_event="fill",
    )
    lines = [f"\u2705 FILLED{location}  \u2014  {symbol} {arrow} @ {p(entry)}"]
    lines.extend(_vnext_context_lines(context))
    text = "\n".join(lines)
    _send_async(text)


def notify_trade_closed(
    symbol: str, result: str, actual_r: float | None = None,
    hold_minutes: float | None = None, trade_id: str = "",
    entry_price: float = 0, exit_price: float = 0,
    vnext_context: dict | None = None,
    broker_profit: float | None = None,
    broker_net_profit: float | None = None,
    broker_deal_reconciled: bool = False,
    broker_deal_id: int | str | None = None,
    broker_close_order_id: int | str | None = None,
    broker_commission: float | None = None,
    broker_swap: float | None = None,
    broker_fee: float | None = None,
) -> None:
    r = actual_r if actual_r is not None else 0
    p = lambda v: _fmt_price(v, symbol)
    context = build_vnext_notification_context(
        vnext_context,
        lifecycle_event=result,
    )

    # Determine win/loss/other
    if r > 0:
        icon = "\U0001F4B0"
        label = "WIN"
        r_display = f"+{r:.2f}R"
    elif r < 0:
        icon = "\U0001F534"
        label = "LOSS"
        r_display = f"{r:.2f}R"
    else:
        icon = "\u23F9\uFE0F"
        label = "CLOSED"
        r_display = f"{r:.2f}R"

    # Map exit types to readable names
    exit_map = {
        "tp": "TP Hit", "tp_hit": "TP Hit", "take_profit": "TP Hit",
        "sl": "SL Hit", "sl_hit": "SL Hit", "stop_loss": "SL Hit",
        "timeout_2h": "Timeout (2h)", "timeout": "Timeout",
        "manual": "Manual Close",
    }
    exit_label = exit_map.get(result.lower(), result)

    lines = [
        f"{icon} {label}  \u2014  {symbol}    {r_display}",
        f"Exit: {exit_label}  |  Hold: {_fmt_hold_time(hold_minutes)}",
    ]
    broker_profit_value = None
    broker_net_profit_value = None
    if broker_deal_reconciled and broker_net_profit is not None:
        try:
            broker_net_profit_value = float(broker_net_profit)
        except (TypeError, ValueError):
            broker_net_profit_value = None
    if broker_deal_reconciled and broker_profit is not None:
        try:
            broker_profit_value = float(broker_profit)
        except (TypeError, ValueError):
            broker_profit_value = None
    realized_broker_value = (
        broker_net_profit_value
        if broker_net_profit_value is not None
        else broker_profit_value
    )
    if realized_broker_value is not None:
        lines.insert(1, f"Broker P&L: {_fmt_money(realized_broker_value)}")
        lines.insert(2, f"Local R: {r_display}")
        if broker_deal_id not in (None, ""):
            lines.insert(3, f"Broker deal: {broker_deal_id}")
    else:
        lines.insert(1, f"Projected P&L: {_fmt_dollars(r)}")

    if entry_price and exit_price:
        lines.append(f"Entry {p(entry_price)}  \u2192  Exit {p(exit_price)}")
    lines.extend(_vnext_context_lines(context))

    # Update daily P&L and append summary. Pass full metadata so the
    # logger can dedup on trade_id (orchestrator + execution-engine
    # both fire this for the same close — see ``_notify_close_if_unsent``)
    # and so the audit-grade ``daily_pnl_history.jsonl`` ledger captures
    # rich per-event data.
    pnl = _record_trade(
        symbol, r, result,
        trade_id=trade_id,
        entry_price=entry_price,
        exit_price=exit_price,
        hold_minutes=hold_minutes,
        vnext_context=context or None,
        broker_profit=broker_profit,
        broker_net_profit=broker_net_profit,
        broker_deal_reconciled=broker_deal_reconciled,
        broker_deal_id=broker_deal_id,
        broker_close_order_id=broker_close_order_id,
        broker_commission=broker_commission,
        broker_swap=broker_swap,
        broker_fee=broker_fee,
    )
    lines.append("")
    lines.append(_pnl_line(pnl))

    # Trade closes are HIGH priority — operator P&L truth must survive a
    # process crash + restart cycle. Falls back to fire-and-forget if the
    # queue subsystem is unavailable, mirroring notify_alert's pattern.
    formatted = "\n".join(lines)
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(formatted, level=Level.HIGH)
    except Exception as e:
        logger.warning(
            "notify_trade_closed: queue dispatch failed (%s); falling back to fire-and-forget",
            e,
        )
        _send_async(formatted)


def notify_limit_expired(
    symbol: str, trade_id: str, reason: str = "48h clock",
    vnext_context: dict | None = None,
) -> None:
    context = build_vnext_notification_context(
        vnext_context,
        lifecycle_event="expiry",
    )
    lines = [
        f"\u23F0 EXPIRED  \u2014  {symbol}",
        f"Limit order expired ({reason}). No fill.",
    ]
    lines.extend(_vnext_context_lines(context))
    text = "\n".join(lines)
    # Expiry/no-fill alerts are execution-adjacent state changes: the operator
    # must see that a pending order left the book even if the process restarts.
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(
            text,
            level=Level.HIGH,
            alert_id=f"limit_expired:{symbol}:{trade_id}:{reason}",
        )
    except Exception as e:
        logger.warning(
            "notify_limit_expired: queue dispatch failed (%s); falling back to fire-and-forget",
            e,
        )
        _send_async(text)


def notify_vnext_lifecycle_event(
    symbol: str,
    lifecycle_event: str,
    *,
    trade_id: str = "",
    direction: str | None = None,
    price: float | None = None,
    result_r: float | None = None,
    detail: str | None = None,
    vnext_context: dict | None = None,
) -> None:
    context = build_vnext_notification_context(
        vnext_context,
        lifecycle_event=lifecycle_event,
    )
    if not context:
        return
    lines = [f"\U0001F504 vNext LIFECYCLE  \u2014  {symbol}"]
    lines.append(f"Event: {_clean_context_value(lifecycle_event)}")
    if trade_id:
        lines.append(f"Trade: {_clean_context_value(trade_id)}")
    position_parts = []
    if direction:
        position_parts.append(_clean_context_value(direction))
    if price is not None:
        position_parts.append(f"price={_fmt_price(float(price), symbol)}")
    if result_r is not None:
        position_parts.append(f"result={result_r:+.2f}R")
    if position_parts:
        lines.append("Position: " + " | ".join(position_parts))
    if detail:
        lines.append(f"Detail: {_clean_context_value(detail)}")
    lines.extend(_vnext_context_lines(context))
    text = "\n".join(lines)
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(
            text,
            level=Level.HIGH,
            alert_id=f"vnext_lifecycle:{symbol}:{trade_id}:{lifecycle_event}",
        )
    except Exception as e:
        logger.warning(
            "notify_vnext_lifecycle_event: queue dispatch failed (%s); falling back to fire-and-forget",
            e,
        )
        _send_async(text)


def _operator_alert_prefix() -> str:
    """Return the optional process-scoped operator label used by parallel books.

    The F5 wrapper sets ``GTOS_ALERT_LABEL`` so experiment alerts cannot be mistaken for
    armed-book alerts in the shared Telegram chat.  Keep the default empty to preserve armed
    production formatting byte-for-byte.
    """
    label = os.environ.get("GTOS_ALERT_LABEL", "").strip()
    return f"[{label}] " if label else ""


def notify_alert(text: str) -> None:
    """System alerts — API refusals, drawdown, daily-loss-stop, SPRT signals.

    Routes through ``src.utils.notification_queue`` at HIGH priority:
    file-backed retry queue with 5-retry exponential backoff. The alert
    survives a process crash + watchdog restart. CEO sees it eventually.

    Uses lazy import + best-effort error handling to keep the trading
    pipeline running even if the queue subsystem fails — a failed alert
    is preferable to a halted orchestrator.
    """
    formatted = f"{_operator_alert_prefix()}\u26A0\uFE0F SYSTEM ALERT\n{text}"
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(formatted, level=Level.HIGH)
    except Exception as e:
        logger.warning(
            "notify_alert: queue dispatch failed (%s); falling back to fire-and-forget",
            e,
        )
        _send_async(formatted)


def notify_critical(text: str) -> None:
    """CRITICAL system alerts — SPRT halt, heartbeat-flatten, kill-switch.

    Routes through ``src.utils.notification_queue`` at CRITICAL priority:
    indefinite retry until success OR 24-hour age-out. The CEO MUST see
    these — if Telegram is briefly unreachable, the alert sits in the
    queue and retries every 30s automatically.

    Use sparingly: every CRITICAL alert ties up the queue retry budget
    and may pin the queue file open until acknowledged.
    """
    formatted = f"{_operator_alert_prefix()}\U0001F6A8 CRITICAL\n{text}"
    try:
        from src.utils.notification_queue import Level, send as _q_send
        _q_send(formatted, level=Level.CRITICAL)
    except Exception as e:
        logger.warning(
            "notify_critical: queue dispatch failed (%s); falling back to fire-and-forget",
            e,
        )
        _send_async(formatted)


def notify_daily_summary() -> None:
    """Send end-of-day P&L summary. Call from orchestrator at session end."""
    pnl = _load_pnl()
    trades = pnl.get("trades", [])
    if not trades:
        text = f"\U0001F4CB DAILY SUMMARY\nNo trades today."
        _send_async(text)
        return

    r = pnl["total_r"]
    w, l = pnl.get("wins", 0), pnl.get("losses", 0)
    total = w + l
    wr = (w / total * 100) if total > 0 else 0

    # Per-symbol breakdown
    breakdown = []
    for t in trades:
        sym = t["symbol"]
        tr = t["result_r"]
        icon = "\u2705" if tr > 0 else "\u274C"
        trade_usd = t.get("realized_usd")
        usd_text = (
            _fmt_money(float(trade_usd))
            if trade_usd is not None
            else _fmt_dollars(tr)
        )
        breakdown.append(f"  {icon} {sym}: {tr:+.2f}R ({usd_text})")

    lines = [
        f"\U0001F4CB DAILY SUMMARY  \u2014  {pnl['date']}",
        f"Trades: {total}  ({w}W / {l}L)  |  WR: {wr:.0f}%",
        f"P&L: {r:+.2f}R  ({_pnl_total_money_text(pnl, r)})",
        "",
    ] + breakdown

    _send_async("\n".join(lines))
