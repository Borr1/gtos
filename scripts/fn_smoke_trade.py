"""redacted_account end-to-end smoke test — one minimum-volume market trade per
instrument, sequential, under the same config overlay stack the orchestrator
uses.

Verifies under --profile redacted_account:
    - Config overlay resolution (risk%, symbol, mt5_symbol per profile+instrument)
    - MT5 broker symbol resolution + volume + stop-distance acceptance
    - Market fill + SL/TP close mechanics against the FN broker
    - Telegram $/R conversion via configure_notifications() per-symbol
    - Chart signal file write (agent_signals_{broker_symbol}.jsonl)
    - daily_pnl.json update via notify_trade_closed

Uses MAGIC=99887766 so the orchestrator's concurrent tracker (which filters
on MAGIC=20260401) ignores these positions — won't collide with live gates.

Max loss per trade: ~$1-5 at 0.01 lot × ~10-pip SL.
Sequential: each symbol completes (fill → close) before next.

    python scripts/fn_smoke_trade.py
    python scripts/fn_smoke_trade.py --symbols XAUUSD,USDJPY
    python scripts/fn_smoke_trade.py --dry-run          # no orders placed
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    """Load .env into os.environ BEFORE src.notifications is imported.

    ``src/notifications.py`` reads ``TELEGRAM_BOT_TOKEN`` + ``TELEGRAM_CHAT_ID``
    at module import time. If we load .env after the import, the module-level
    constants freeze as empty strings and every ``_send_async`` call silently
    no-ops. Must run first.
    """
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_load_env()

import MetaTrader5 as mt5  # noqa: E402

from src.safety.activation_token import (  # noqa: E402
    ActivationTokenError,
    authorize_raw_broker_request,
)
from src.safety.runtime_halt import RuntimeHaltError  # noqa: E402

#: Which account this script is allowed to smoke-test, for the token binding.
NAMESPACE = "redacted_account_live_bee34003"
import yaml  # noqa: E402

from src import notifications  # noqa: E402
from src.utils.config import (  # noqa: E402
    apply_instrument_overrides, apply_profile_overrides, resolve_profile,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fn_smoke")

SMOKE_MAGIC = 99887766        # distinct from orchestrator's 20260401
VOLUME = 0.01                 # FN min (verified by mt5_preflight)
CLOSE_TIMEOUT_S = 120         # force-close cap
POLL_S = 1.0

# Per-symbol SL/TP price-distance (not pips — absolute price units).
# Tight enough to close within ~60s, wide enough to clear broker stops_level.
# Fleet expanded 2026-04-25 to 7 instruments (XAGUSD + NAS100); SL/TP added
# 2026-04-26 per Cluster 1 fleet expansion (B3). Distances tuned to clear
# typical FN broker stops_level (XAGUSD ~$0.05; NAS100 ~10 pts).
SL_TP_PX = {
    "XAUUSD":    1.5,     # $1.5 price distance (~15 "pips" of 0.10)
    "US30_cash": 10.0,    # 10 points
    "USDJPY":    0.08,    # 8 JPY pips
    "GBPJPY":    0.12,    # 12 JPY pips
    "GBPUSD":    0.0010,  # 10 pips
    "XAGUSD":    0.20,    # $0.20 silver (~20 cents; clears typical $0.05 stops_level)
    "NAS100":    30.0,    # 30 index points (~0.1% on ~20000 index)
}

DEFAULT_SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD",
                   "XAGUSD", "NAS100"]

MT5_FILES = (
    Path.home() / "AppData/Roaming/MetaQuotes/Terminal"
    / "D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files"
)


def load_symbol_config(symbol: str, profile_name: str) -> dict:
    with open(ROOT / "config/agent_config.yaml") as f:
        raw = yaml.safe_load(f)
    profile = resolve_profile(profile_name)
    cfg = apply_profile_overrides(raw, profile)
    cfg = apply_instrument_overrides(cfg, symbol)
    return cfg


def pick_filling_mode(info) -> int:
    # filling_mode is a bitfield; prefer IOC → FOK (return-only=4 is pending)
    mode = info.filling_mode
    if mode & 2:
        return mt5.ORDER_FILLING_IOC
    if mode & 1:
        return mt5.ORDER_FILLING_FOK
    return mt5.ORDER_FILLING_RETURN  # shouldn't happen for market order


def _check_position_status(ticket: int) -> str:
    """Return one of {"open", "closed", "unknown"} for a given MT5 ticket.

    `mt5.positions_get(ticket=...)` distinguishes three states:
      - non-empty tuple/list -> "open"
      - empty tuple ()       -> "closed" (no positions match the ticket)
      - None                 -> "unknown" (transient MT5 error / lib failure)

    Bug #24 root cause: the original code collapsed the second and third
    cases into "closed" via `if not pos: closed_by = SL_TP`. That produced a
    false CLOSED report whenever MT5 returned None during the poll loop,
    even though the position remained open server-side.
    """
    pos = mt5.positions_get(ticket=ticket)
    if pos is None:
        return "unknown"
    # mt5.positions_get returns a tuple; an empty tuple unambiguously means
    # the ticket has no matching open position.
    if len(pos) == 0:
        return "closed"
    return "open"


def _wait_for_close(ticket: int, timeout_s: int) -> tuple[str | None, str]:
    """Poll until the position closes or timeout.

    Returns (closed_by, final_position_status) where:
      - closed_by is "SL_TP" if we observed the position transition to closed
        via an explicit empty positions_get() response, else None.
      - final_position_status is "closed", "still_open", or "unknown"
        (unknown means we never got a successful positions_get during the
        poll window).

    A positions_get returning None during the poll is logged but does NOT
    break the loop -- we keep polling so a transient MT5 hiccup doesn't
    cause a false CLOSED report (Bug #24).
    """
    deadline = time.time() + timeout_s
    saw_open_at_least_once = False
    last_status = "unknown"
    while time.time() < deadline:
        status = _check_position_status(ticket)
        if status == "closed":
            return "SL_TP", "closed"
        if status == "open":
            saw_open_at_least_once = True
            last_status = "still_open"
        else:  # "unknown"
            log.debug("positions_get returned None for ticket=%d "
                      "(transient MT5 error) — retrying", ticket)
            # Don't update last_status on a None; preserve last good signal.
        time.sleep(POLL_S)

    # Timed out without seeing closure.
    if saw_open_at_least_once:
        return None, "still_open"
    return None, last_status  # could be "still_open" or "unknown"


def _force_close_position(ticket: int, mt5_symbol: str,
                          filling: int) -> tuple[bool, int | None]:
    """Best-effort force-close of an open position.

    Returns (success, retcode). `success` is True iff order_send returned a
    DONE retcode AND a follow-up positions_get confirms the position is gone.
    Returns (False, None) if the position is already gone OR if MT5 is
    unreachable.

    DELIBERATELY UNGATED, and the reason is the never-strand rule.
    ---------------------------------------------------------------
    The entry at `run_symbol` goes through `authorize_raw_broker_request`; this
    does not, and must not. That guard enforces the runtime **halt** before it
    classifies, and the halt blocks everything — risk-reducing requests
    included, by design, because it is an intentional act by an operator who is
    present. This function is the recovery path for a smoke trade that already
    filled: it is the code that gets a real position off a real funded account.
    Routing it through the halt would mean a stale flag file — including
    `AUTOSTART_DISABLED.flag`, whose semantics are "do not autostart" — could
    strand an open position.

    The token layer would pass this request anyway (it is a close), so the guard
    would add no authorization value here, only a way to fail. Recorded as a
    declared exemption in `tests/safety/test_raw_broker_script_guards.py` rather
    than left as an accident: the previous guard test could not see an unguarded
    `order_send` in a sibling function at all (B104).
    """
    pos = mt5.positions_get(ticket=ticket)
    if pos is None:
        log.warning("force-close: positions_get returned None for ticket=%d",
                    ticket)
        return False, None
    if len(pos) == 0:
        log.info("force-close: position %d already closed", ticket)
        return True, None  # nothing to do; treat as success

    p = pos[0]
    t2 = mt5.symbol_info_tick(mt5_symbol)
    if t2 is None:
        log.error("force-close: no tick for %s", mt5_symbol)
        return False, None

    close_req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": mt5_symbol,
        "volume": p.volume,
        "type": mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY
                else mt5.ORDER_TYPE_BUY,
        "position": p.ticket,
        "price": t2.bid if p.type == mt5.ORDER_TYPE_BUY else t2.ask,
        "deviation": 20,
        "magic": SMOKE_MAGIC,
        "comment": "FN_SMOKE_CLOSE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }
    cr = mt5.order_send(close_req)
    if cr is None:
        log.error("force-close order_send returned None: %s", mt5.last_error())
        return False, None
    if cr.retcode != mt5.TRADE_RETCODE_DONE:
        log.error("force-close retcode=%s (%s)", cr.retcode, cr.comment)
        return False, int(cr.retcode)

    # Confirm the position is actually gone -- a DONE retcode without
    # disappearance is a same-class bug to the original report.
    time.sleep(0.5)
    confirm = _check_position_status(ticket)
    if confirm == "closed":
        return True, int(cr.retcode)
    log.error("force-close: order_send DONE but position_status=%s after "
              "0.5s (ticket=%d)", confirm, ticket)
    return False, int(cr.retcode)


def write_chart_signal(mt5_symbol: str, decision: str, detail: str,
                       price: float) -> Path:
    """Mirror orchestrator._write_chart_signal transform (broker symbol)."""
    safe_sym = mt5_symbol.replace(".", "_")
    path = MT5_FILES / f"agent_signals_{safe_sym}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "decision": decision,
        "detail": detail[:80],
        "price": round(price, 5),
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return path


def run_symbol(symbol: str, profile_name: str,
               dry_run: bool = False) -> dict:
    result: dict = {
        "symbol": symbol,
        "profile": profile_name,
        "fill": False,
        "close": False,
        "telegram_sent": False,
        "chart_signal_written": False,
        "error": None,
    }

    cfg = load_symbol_config(symbol, profile_name)
    mt5_symbol = cfg.get("market", {}).get("mt5_symbol",
                   cfg.get("market", {}).get("symbol", symbol))
    risk_pct = float(cfg.get("risk", {}).get("risk_per_trade_pct", 1.0))
    result["mt5_symbol"] = mt5_symbol
    result["risk_pct"] = risk_pct
    result["expected_dollar_per_r"] = round(100_000 * risk_pct / 100, 2)

    notifications.configure_notifications(risk_pct, 100_000.0)

    info = mt5.symbol_info(mt5_symbol)
    if info is None:
        result["error"] = f"symbol_info({mt5_symbol}) returned None"
        return result

    if not info.visible:
        if not mt5.symbol_select(mt5_symbol, True):
            result["error"] = f"symbol_select({mt5_symbol}) failed"
            return result
        time.sleep(0.3)
        info = mt5.symbol_info(mt5_symbol)

    result["point"] = info.point
    result["stops_level_pts"] = info.trade_stops_level
    result["volume_min"] = info.volume_min
    result["volume_max"] = info.volume_max

    tick = mt5.symbol_info_tick(mt5_symbol)
    if tick is None or tick.ask <= 0:
        result["error"] = f"symbol_info_tick({mt5_symbol}) invalid"
        return result

    sl_tp_px = SL_TP_PX[symbol]
    min_stop_px = info.trade_stops_level * info.point
    if min_stop_px > sl_tp_px:
        # Bump to just above broker's minimum
        sl_tp_px = min_stop_px * 1.1
        log.info("%s: SL/TP widened to %.5f (stops_level=%d pts)",
                 symbol, sl_tp_px, info.trade_stops_level)

    # LONG side for all (simplest)
    entry_price = tick.ask
    sl = entry_price - sl_tp_px
    tp = entry_price + sl_tp_px

    # Round to tick size
    digits = info.digits
    sl = round(sl, digits)
    tp = round(tp, digits)
    entry_price = round(entry_price, digits)

    result["entry_price"] = entry_price
    result["sl"] = sl
    result["tp"] = tp
    result["sl_distance"] = round(sl_tp_px, digits)

    if dry_run:
        result["dry_run"] = True
        log.info("%s (dry): would send BUY %s @ %.5f SL=%.5f TP=%.5f vol=%.2f",
                 symbol, mt5_symbol, entry_price, sl, tp, VOLUME)
        return result

    filling = pick_filling_mode(info)
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": mt5_symbol,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": SMOKE_MAGIC,
        "comment": "FN_SMOKE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }
    log.info("%s: → BUY %s @ %.5f (SL %.5f / TP %.5f) vol=%.2f",
             symbol, mt5_symbol, entry_price, sl, tp, VOLUME)

    # F19: this script drives the RAW MetaTrader5 module, so it bypasses
    # create_mt5, RealMT5 and every engine guard -- including the activation
    # check that now sits inside RealMT5.order_send. It is not deleted because
    # it carries genuine behavioural tests and a live smoke trade is a real
    # canary-day need; instead it goes through the same authorization the engine
    # does. No token, or an active halt -> no order, and the script says which.
    try:
        authorize_raw_broker_request(
            req, mt5_module=mt5, namespace=NAMESPACE, action="fn_smoke_trade_entry"
        )
    except (RuntimeHaltError, ActivationTokenError) as guard_error:
        result["error"] = f"refused_by_guard: {guard_error}"
        log.error("%s: REFUSED before any broker mutation -- %s", symbol, guard_error)
        return result

    send = mt5.order_send(req)
    if send is None:
        result["error"] = f"order_send returned None: {mt5.last_error()}"
        return result
    if send.retcode != mt5.TRADE_RETCODE_DONE:
        result["error"] = f"retcode={send.retcode} ({send.comment})"
        return result

    result["fill"] = True
    result["ticket"] = int(send.order)
    result["fill_price"] = float(send.price)
    log.info("%s: ✓ FILLED ticket=%d @ %.5f", symbol, send.order, send.price)

    # Write EXECUTED chart signal (broker-symbol filename per orchestrator fix)
    try:
        path = write_chart_signal(
            mt5_symbol, "EXECUTED",
            f"FN_SMOKE BUY {VOLUME} lots",
            send.price,
        )
        result["chart_signal_written"] = True
        result["chart_signal_path"] = str(path.name)
    except Exception as e:
        result["chart_write_error"] = str(e)

    # Close lifecycle (Bug #24 fix):
    #
    # Original code mis-reported CLOSED with pnl=$0 / exit=0 because it:
    #   1. Treated `not pos` as "SL/TP closed" -- but `mt5.positions_get`
    #      returns None on transient MT5 errors AND empty tuple () when no
    #      positions match. Both were collapsed into "closed_by=SL_TP".
    #   2. Never confirmed via `history_deals_get` that an EXIT deal
    #      actually exists before claiming closure.
    #   3. The fallback force-close had the same `if pos:` blind spot --
    #      a None return silently skipped force-close, leaving position
    #      open AND `closed_by=None` (FAILED_TO_CLOSE) but no retry.
    #
    # Fix: poll only treats explicit empty tuple as closed; a None return is
    # logged + retried. After the poll exits, we ALWAYS verify closure by
    # checking both `positions_get` AND `history_deals_get` for an exit deal.
    # If the position is still open, force-close runs unconditionally and is
    # itself verified. If we cannot confirm closure, `result["close"]=False`
    # (FAILED_TO_CLOSE) -- no false CLOSED report.
    start = time.time()
    closed_by, position_status = _wait_for_close(send.order, CLOSE_TIMEOUT_S)
    result["position_status_after_poll"] = position_status
    result["close_retcodes"] = []  # all retcodes from any close attempts

    if closed_by is None and position_status == "still_open":
        log.warning("%s: no SL/TP close in %ds — force-closing", symbol,
                    CLOSE_TIMEOUT_S)
        force_closed, force_retcode = _force_close_position(
            send.order, mt5_symbol, filling,
        )
        result["close_retcodes"].append(force_retcode)
        if force_closed:
            closed_by = "MANUAL_TIMEOUT"
            position_status = "closed"
        else:
            log.error("%s: force-close FAILED (retcode=%s) — position may "
                      "still be open", symbol, force_retcode)
    elif closed_by is None and position_status == "unknown":
        # MT5 unreachable for the entire poll window. Try one last force-close
        # so the position isn't silently left open.
        log.warning("%s: position status unknown after %ds — attempting "
                    "force-close anyway", symbol, CLOSE_TIMEOUT_S)
        force_closed, force_retcode = _force_close_position(
            send.order, mt5_symbol, filling,
        )
        result["close_retcodes"].append(force_retcode)
        if force_closed:
            closed_by = "MANUAL_TIMEOUT"
            position_status = "closed"

    # Verify closure via history_deals_get -- the AUTHORITATIVE source.
    # Don't trust positions_get alone; also don't claim CLOSED unless we have
    # an EXIT deal in the history.
    t_from = int(start - 10)
    t_to = int(time.time() + 5)
    deals = mt5.history_deals_get(t_from, t_to)
    position_deals = [d for d in (deals or []) if d.position_id == send.order]
    exit_deal = next((d for d in position_deals
                      if d.entry == mt5.DEAL_ENTRY_OUT), None)
    pnl = sum(d.profit + d.swap + d.commission for d in position_deals)
    exit_price = exit_deal.price if exit_deal else 0.0

    # Final closure verdict combines all signals: position_status + exit deal.
    # Only claim CLOSED when (a) MT5 says position no longer exists AND
    # (b) an exit deal is in the history. This eliminates the false-CLOSED
    # report observed 2026-04-27 (issue #24).
    confirmed_closed = (position_status == "closed" and exit_deal is not None)
    result["close"] = confirmed_closed
    result["closed_by"] = closed_by if confirmed_closed else None
    result["exit_deal_found"] = exit_deal is not None

    if not confirmed_closed:
        # Last-resort verification: re-check positions_get directly so we can
        # surface a clear status string. Surfacing this in the JSON report
        # makes the operator's manual force-close decision unambiguous.
        still_open_pos = mt5.positions_get(ticket=send.order)
        if still_open_pos is None:
            result["final_position_check"] = "MT5_ERROR"
        elif len(still_open_pos) == 0:
            # Position gone but no exit deal yet — history may be lagging.
            result["final_position_check"] = "GONE_NO_EXIT_DEAL"
        else:
            result["final_position_check"] = "STILL_OPEN"
        result["error"] = ("FAILED_TO_CLOSE: position_status=%s "
                           "exit_deal=%s final=%s" % (
                               position_status,
                               exit_deal is not None,
                               result["final_position_check"],
                           ))

    result["pnl_dollars"] = round(pnl, 2)
    result["exit_price"] = exit_price
    sl_dist = abs(result["fill_price"] - sl)
    if sl_dist > 0 and exit_price:
        signed = exit_price - result["fill_price"]  # LONG
        result["actual_r"] = round(signed / sl_dist, 3)
    else:
        result["actual_r"] = 0.0

    if confirmed_closed:
        log.info("%s: ✓ CLOSED pnl=$%.2f exit=%.5f R=%.3f (%s)",
                 symbol, pnl, exit_price, result["actual_r"],
                 closed_by or "unknown")
    else:
        log.error("%s: ✗ FAILED_TO_CLOSE position_status=%s exit_deal=%s "
                  "final=%s — manual force-close may be required",
                  symbol, position_status, exit_deal is not None,
                  result.get("final_position_check"))

    # Fire Telegram close — this exercises configure_notifications $/R math.
    # Only fire when we have a CONFIRMED close; firing on FAILED_TO_CLOSE
    # would push a misleading $0 / 0R notification to the operator chat
    # while the position is still open.
    if confirmed_closed:
        exit_type = "tp_hit" if result["actual_r"] > 0 else "sl_hit"
        try:
            notifications.notify_trade_closed(
                symbol=symbol,
                result=exit_type,
                actual_r=result["actual_r"],
                entry_price=result["fill_price"],
                exit_price=exit_price,
            )
            result["telegram_sent"] = True
        except Exception as e:
            result["telegram_error"] = str(e)
    else:
        log.warning("%s: skipping Telegram close notify (no confirmed close)",
                    symbol)
        result["telegram_skipped_reason"] = "no_confirmed_close"

    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    p.add_argument("--profile", default="redacted_account",
                   choices=["redacted_account", "ftmo"],
                   help="profile overlay (drives mt5_symbol, risk%, etc.)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--gap-s", type=float, default=5.0,
                   help="sleep between symbols")
    args = p.parse_args()

    if not mt5.initialize():
        log.error("mt5.initialize() failed: %s", mt5.last_error())
        return 1

    acct = mt5.account_info()
    log.info("Connected login=%s server=%s balance=$%.2f equity=$%.2f profile=%s",
             acct.login, acct.server, acct.balance, acct.equity, args.profile)
    if abs(acct.balance - 100_000.0) > 0.01:
        log.warning("Balance != $100,000 — may not be a $100K demo account")
    if not acct.trade_expert:
        log.warning("account_info.trade_expert=False — orders will be rejected with retcode 10026")

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    results = []
    for i, sym in enumerate(symbols):
        log.info("")
        log.info("=" * 60)
        log.info("[%d/%d] %s (profile=%s)", i + 1, len(symbols), sym,
                 args.profile)
        log.info("=" * 60)
        try:
            r = run_symbol(sym, args.profile, dry_run=args.dry_run)
        except Exception as e:
            log.exception("%s: unhandled exception", sym)
            r = {"symbol": sym, "error": f"exception: {e}"}
        results.append(r)
        if i < len(symbols) - 1:
            time.sleep(args.gap_s)

    # Final report
    print()
    print("=" * 78)
    print("FN SMOKE TRADE RESULTS")
    print("=" * 78)
    hdr = f"{'SYMBOL':<12s} {'FILL':<5s} {'CLOSE':<6s} {'TG':<3s} {'CHART':<6s} {'PnL($)':<10s} {'R':<7s} {'NOTES'}"
    print(hdr)
    print("-" * 78)
    for r in results:
        sym = r["symbol"]
        # Pre-fill errors (e.g. symbol_info None, retcode != DONE on entry)
        # are rendered as a single ERROR line. Post-fill errors (e.g.
        # FAILED_TO_CLOSE) still render the columns so the operator can see
        # what state the position ended in -- the row's NOTES column carries
        # the error.
        if r.get("error") and not r.get("fill"):
            print(f"{sym:<12s} ERROR: {r['error']}")
            continue
        fill = "Y" if r.get("fill") else "N"
        close = "Y" if r.get("close") else "N"
        tg = "Y" if r.get("telegram_sent") else "N"
        ch = "Y" if r.get("chart_signal_written") else "N"
        pnl = r.get("pnl_dollars", 0)
        rr = r.get("actual_r", 0)
        notes = r.get("closed_by") or ""
        if r.get("dry_run"):
            notes = "DRY_RUN"
        if r.get("error"):
            # Surface FAILED_TO_CLOSE / similar in the NOTES column so the
            # operator immediately sees this is NOT a clean run.
            notes = r["error"]
        print(f"{sym:<12s} {fill:<5s} {close:<6s} {tg:<3s} {ch:<6s} "
              f"${pnl:<9.2f} {rr:<7.3f} {notes}")
    print("=" * 78)

    report_path = ROOT / f"shadow_logs/fn_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2, default=str))
    log.info("Full results → %s", report_path)

    # notifications._send_async() uses daemon threads that die with the
    # process. Without a drain window the LAST symbol's Telegram POST gets
    # killed mid-request (observed 2026-04-20: first 4 of 5 arrived, GBPUSD
    # dropped). 5s is enough for a Telegram sendMessage round-trip.
    time.sleep(5)
    mt5.shutdown()
    # Return nonzero if any failed
    return 0 if all(r.get("fill") and r.get("close") for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
