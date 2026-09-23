#!/usr/bin/env python3
"""Live F5 book-event sidecar. Does NOT touch GTOS_F5_FTMO.

Source of truth: THIS login's MT5 positions/orders/deals + writer's placed_decisions TAIL.
Not harvest. Not trade_records glob. Not latest.json candidate_id strings.

Emits:
  - candidate: new live pending order, or a new placed_decisions.jsonl line
  - fill: new live open position, or new IN deal on this login
  - close: live open ticket vanished, or new OUT deal on this login
  - pair_dead: heartbeat missing/stale (live pair only)

Identity: login 0 (Challenge; verification quarantined), magic 0.
emit() also refuses ghosts, so CLI catch-ups cannot bypass.
Persistent cursor: placed_bytes (eof-only), last_deal_ticket, open/pending sets.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from emit_book_event import LIVE_LOGIN, emit, live_ticket  # noqa: E402

REPO = Path(r"host-local\redacted_host\repo")
NS = REPO / r"pipeline_state\ultimate_book\operator"
LIVE = REPO / r"judgment\live"
PLACED = NS / "placed_decisions.jsonl"
TRADES = NS / "trade_records"
HEARTBEAT = NS / "heartbeat.json"
STATE_PATH = LIVE / "book_event_watch_state.json"
LOG_PATH = LIVE / "book_event_watch.log"
PID_PATH = LIVE / "book_event_watch.pid"
POLL_SEC = float(os.environ.get("BOOK_EVENT_POLL_SEC", "8"))
HB_STALE_SEC = 180.0
MT5_PATH = r"C:\MT5\FTMO\terminal64.exe"
MAGIC = 0
STATE_VERSION = 4  # deal cursor + no harvest glob
DEAL_IN = 0
DEAL_OUT = {1, 2, 3}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    line = f"{utc_now()} {msg}"
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def load_state() -> dict:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "version": 0,
        "placed_bytes": 0,
        "seen_tickets": {},
        "open_tickets": [],
        "pending_tickets": [],
        "last_deal_ticket": 0,
        "pair_dead_sent": False,
        "emitted": {},
    }


def save_state(st: dict) -> None:
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
    tmp.replace(STATE_PATH)


def _copy_fp(kind: str, payload: dict) -> str | None:
    if kind not in {"fill", "close"}:
        return None
    return f"{payload.get('sl')}|{payload.get('tp')}|{payload.get('volume')}"


def already(st: dict, kind: str, ticket, fp: str | None = None) -> bool:
    key = f"{kind}:{ticket}" if not fp else f"{kind}:{ticket}:{fp}"
    em = st.get("emitted")
    if isinstance(em, dict):
        return key in em
    return key in (em or [])


def mark(st: dict, kind: str, ticket, fp: str | None = None) -> None:
    key = f"{kind}:{ticket}" if not fp else f"{kind}:{ticket}:{fp}"
    em = st.get("emitted")
    if not isinstance(em, dict):
        em = {k: True for k in (em or [])}
        st["emitted"] = em
    em[key] = True


def post(st: dict, kind: str, payload: dict) -> None:
    payload = dict(payload)
    payload.setdefault("login", LIVE_LOGIN)
    payload.setdefault("source", "f5_writer")
    ticket = payload.get("ticket")
    fp = _copy_fp(kind, payload)
    if kind != "pair_dead" and live_ticket(ticket) is None:
        log(f"skip {kind} ticket={ticket!r} login={payload.get('login')!r} reason=not_live_ticket")
        mark(st, kind, ticket, fp)
        return
    if already(st, kind, ticket, fp):
        return
    result = emit(kind, **payload)
    skipped = bool(result.get("skipped"))
    ok = bool(result.get("ok"))
    status = result.get("status")
    log(
        f"emit {kind} ticket={ticket} login={payload.get('login')} "
        f"ok={ok} skipped={skipped} status={status} mill={result.get('mill')} "
        f"fleet={result.get('fleet')} reason={result.get('reason')} "
        f"err={result.get('error')} exhausted={result.get('exhausted')}"
    )
    if ok or skipped or status == 200:
        mark(st, kind, ticket, fp)


def parse_trade_record(path: Path) -> dict | None:
    """Enrich a live close. Never used as a fire source."""
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    ex = d.get("execution") or {}
    inst = d.get("instrumentation") or {}
    flow = inst.get("gtos_live_flow_execution") or {}
    req = flow.get("request") or {}
    ticket = ex.get("ticket") or d.get("ticket")
    if not ticket:
        try:
            ticket = int(path.stem)
        except Exception:
            return None
    return {
        "ticket": int(ticket) if str(ticket).isdigit() else ticket,
        "symbol": ex.get("broker_symbol") or inst.get("symbol") or d.get("symbol") or "",
        "side": inst.get("direction") or d.get("direction"),
        "price": ex.get("broker_position_fill_price") or ex.get("broker_position_price_open"),
        "sl": ex.get("broker_position_sl") or inst.get("f5_original_stop") or inst.get("stop_loss"),
        "tp": ex.get("broker_position_tp") or inst.get("take_profit_1"),
        "volume": (flow.get("lots_placed") or req.get("volume")),
        "comment": d.get("sleeve") or inst.get("sleeve") or path.stem,
    }


def scan_placed(st: dict) -> None:
    """Tail only. Never rewind into harvest."""
    if not PLACED.is_file():
        return
    size = PLACED.stat().st_size
    start = int(st.get("placed_bytes") or 0)
    if start > size:
        log(f"placed_rewind blocked start={start} size={size}; pin to eof")
        st["placed_bytes"] = size
        return
    with PLACED.open("r", encoding="utf-8", errors="replace") as f:
        if start:
            f.seek(start)
        chunk = f.read()
        st["placed_bytes"] = f.tell()
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        raw = row.get("ticket")
        ticket = live_ticket(raw)
        if ticket is None:
            log(f"skip placed ticket={raw!r} login={LIVE_LOGIN} reason=not_live_ticket")
            continue
        post(st, "candidate", {
            "ticket": ticket,
            "symbol": row.get("symbol") or row.get("broker_symbol"),
            "side": row.get("direction") or row.get("side"),
            "comment": row.get("sleeve") or row.get("candidate_id"),
            "session": row.get("decision_day"),
            "login": LIVE_LOGIN,
        })
        st.setdefault("seen_tickets", {})[str(ticket)] = {"via": "placed", "ts": utc_now()}


def scan_heartbeat(st: dict) -> None:
    if not HEARTBEAT.is_file():
        if not st.get("pair_dead_sent"):
            post(st, "pair_dead", {"ticket": "pair", "comment": "heartbeat missing"})
            st["pair_dead_sent"] = True
        return
    try:
        hb = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
        mtime = HEARTBEAT.stat().st_mtime
    except Exception:
        return
    age = time.time() - mtime
    healthy = bool(hb.get("healthy"))
    if age > HB_STALE_SEC or not healthy:
        if not st.get("pair_dead_sent"):
            post(st, "pair_dead", {
                "ticket": "pair",
                "comment": f"hb_age={age:.0f}s healthy={healthy} pid={hb.get('pid')}",
            })
            st["pair_dead_sent"] = True
    else:
        st["pair_dead_sent"] = False


def _row_from_pos(p) -> dict | None:
    if int(getattr(p, "magic", 0) or 0) != MAGIC:
        return None
    t = live_ticket(p.ticket)
    if t is None:
        return None
    return {
        "ticket": t,
        "symbol": p.symbol,
        "side": "LONG" if int(p.type) == 0 else "SHORT",
        "price": float(p.price_open),
        "sl": float(p.sl or 0),
        "tp": float(p.tp or 0),
        "volume": float(p.volume),
        "comment": p.comment,
    }


def _row_from_order(o) -> dict | None:
    if int(getattr(o, "magic", 0) or 0) != MAGIC:
        return None
    t = live_ticket(o.ticket)
    if t is None:
        return None
    return {
        "ticket": t,
        "symbol": o.symbol,
        "side": "LONG" if int(o.type) in (0, 2, 4) else "SHORT",
        "price": float(o.price_open),
        "sl": float(o.sl or 0),
        "tp": float(o.tp or 0),
        "volume": float(o.volume_current or o.volume_initial or 0),
        "comment": o.comment,
        "order_type": int(o.type),
    }


def mt5_snapshot() -> dict | None:
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    if not mt5.initialize(path=MT5_PATH):
        return None
    try:
        acc = mt5.account_info()
        login = int(acc.login) if acc else 0
        if login != LIVE_LOGIN:
            log(f"mt5_wrong_login {login} want {LIVE_LOGIN} — refuse snapshot")
            return {"login": login, "open": [], "pending": [], "deals": [], "reject": True}
        open_rows = []
        for p in (mt5.positions_get() or []):
            row = _row_from_pos(p)
            if row:
                open_rows.append(row)
        pending_rows = []
        for o in (mt5.orders_get() or []):
            row = _row_from_order(o)
            if row:
                pending_rows.append(row)
        now = datetime.now(timezone.utc)
        deals = mt5.history_deals_get(now - timedelta(hours=24), now + timedelta(minutes=30)) or []
        deal_rows = []
        for d in deals:
            if int(getattr(d, "magic", 0) or 0) != MAGIC:
                continue
            deal_rows.append({
                "deal": int(d.ticket),
                "order": int(getattr(d, "order", 0) or 0),
                "position_id": int(getattr(d, "position_id", 0) or 0),
                "entry": int(getattr(d, "entry", 0) or 0),
                "symbol": d.symbol,
                "volume": float(d.volume),
                "price": float(d.price),
                "profit": float(getattr(d, "profit", 0) or 0),
                "comment": d.comment,
                "side": "LONG" if int(d.type) == 0 else "SHORT",
            })
        deal_rows.sort(key=lambda r: r["deal"])
        return {
            "login": login,
            "open": open_rows,
            "pending": pending_rows,
            "deals": deal_rows,
            "reject": False,
        }
    except Exception:
        log("mt5_snap_err " + traceback.format_exc().splitlines()[-1])
        return None
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def scan_mt5(st: dict) -> None:
    snap = mt5_snapshot()
    if snap is None or snap.get("reject"):
        return
    now_open = {int(r["ticket"]): r for r in snap["open"]}
    now_pending = {int(r["ticket"]): r for r in snap["pending"]}
    prev_open = {int(t) for t in (st.get("open_tickets") or [])}
    prev_pending = {int(t) for t in (st.get("pending_tickets") or [])}

    for ticket, row in now_pending.items():
        if ticket not in prev_pending and ticket not in now_open:
            post(st, "candidate", {
                "ticket": ticket,
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "price": row.get("price"),
                "sl": row.get("sl"),
                "tp": row.get("tp"),
                "volume": row.get("volume"),
                "comment": row.get("comment"),
                "login": LIVE_LOGIN,
            })

    for ticket, row in now_open.items():
        payload = {
            "ticket": ticket,
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "price": row.get("price"),
            "sl": row.get("sl"),
            "tp": row.get("tp"),
            "volume": row.get("volume"),
            "comment": row.get("comment"),
            "login": LIVE_LOGIN,
        }
        # New fill, or SL/TP/volume fingerprint change. already() dedupes.
        post(st, "fill", payload)

    for ticket in prev_open - set(now_open):
        payload = {"ticket": ticket, "comment": "position gone", "login": LIVE_LOGIN}
        rec_path = TRADES / f"{ticket}.json"
        rec = parse_trade_record(rec_path) if rec_path.is_file() else None
        if rec and live_ticket(rec.get("ticket")):
            payload.update({k: rec.get(k) for k in ("symbol", "side", "price", "sl", "tp", "volume", "comment")})
        post(st, "close", payload)

    last_deal = int(st.get("last_deal_ticket") or 0)
    max_seen = last_deal
    for d in snap.get("deals") or []:
        deal_id = int(d["deal"])
        if deal_id <= last_deal:
            continue
        max_seen = max(max_seen, deal_id)
        pos = live_ticket(d.get("position_id")) or live_ticket(d.get("order"))
        if pos is None:
            log(
                f"skip deal deal={deal_id} position_id={d.get('position_id')!r} "
                f"order={d.get('order')!r} login={LIVE_LOGIN} reason=not_live_ticket"
            )
            continue
        open_row = now_open.get(int(pos)) if pos is not None else None
        payload = {
            "ticket": pos,
            "symbol": d.get("symbol"),
            "side": d.get("side"),
            "price": d.get("price"),
            "sl": (open_row or {}).get("sl"),
            "tp": (open_row or {}).get("tp"),
            "volume": d.get("volume") or (open_row or {}).get("volume"),
            "comment": d.get("comment"),
            "login": LIVE_LOGIN,
        }
        entry = int(d.get("entry") or 0)
        if entry == DEAL_IN:
            post(st, "fill", payload)
        elif entry in DEAL_OUT:
            post(st, "close", payload)
    st["last_deal_ticket"] = max_seen
    st["open_tickets"] = sorted(now_open)
    st["pending_tickets"] = sorted(now_pending)


def seed_live_only(st: dict) -> None:
    """Pin cursors to NOW. Mark current live book as already seen. Never POST harvest."""
    if st.get("version") == STATE_VERSION and st.get("seeded_live"):
        return
    if PLACED.is_file():
        st["placed_bytes"] = PLACED.stat().st_size
    snap = mt5_snapshot()
    current_open = set()
    current_pending = set()
    max_deal = int(st.get("last_deal_ticket") or 0)
    if snap and not snap.get("reject"):
        current_open = {int(r["ticket"]) for r in snap["open"]}
        current_pending = {int(r["ticket"]) for r in snap["pending"]}
        st["open_tickets"] = sorted(current_open)
        st["pending_tickets"] = sorted(current_pending)
        for t in current_open:
            mark(st, "fill", t)
            mark(st, "candidate", t)
        for t in current_pending:
            mark(st, "candidate", t)
        for d in snap.get("deals") or []:
            max_deal = max(max_deal, int(d["deal"]))
            pos = live_ticket(d.get("position_id")) or live_ticket(d.get("order"))
            if pos is None:
                continue
            if int(d.get("entry") or 0) == DEAL_IN:
                mark(st, "fill", pos)
            elif int(d.get("entry") or 0) in DEAL_OUT:
                mark(st, "close", pos)
    st["last_deal_ticket"] = max_deal
    st["version"] = STATE_VERSION
    st["seeded_live"] = True
    st["seeded"] = True
    log(
        f"seed_live open={st.get('open_tickets')} pending={st.get('pending_tickets')} "
        f"placed_bytes={st.get('placed_bytes')} last_deal={st.get('last_deal_ticket')}"
    )


def loop() -> int:
    LIVE.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    log(
        f"watch start pid={os.getpid()} poll={POLL_SEC}s v{STATE_VERSION} "
        f"live-login={LIVE_LOGIN} magic={MAGIC} no-harvest"
    )
    st = load_state()
    seed_live_only(st)
    save_state(st)
    n = 0
    while True:
        try:
            scan_placed(st)
            scan_heartbeat(st)
            scan_mt5(st)
            save_state(st)
            n += 1
            if n % 15 == 0:
                log(
                    f"hb n={n} open={st.get('open_tickets')} pending={st.get('pending_tickets')} "
                    f"last_deal={st.get('last_deal_ticket')}"
                )
        except Exception:
            log("loop_err " + traceback.format_exc().splitlines()[-1])
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    try:
        sys.exit(loop())
    except KeyboardInterrupt:
        log("watch stop")
        sys.exit(0)
    except Exception:
        log("fatal " + traceback.format_exc())
        raise
