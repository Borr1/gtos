#!/usr/bin/env python3
"""POST a live F5 book event. Identity-gated. Does not print secrets.

Live book: login 0 only. Harvest / old-login / 175-177xxxxx tickets
are refused here so CLI catch-ups and the watcher cannot bypass.

Importable: emit_book_event.emit(kind=..., **fields)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

ENV_CANDIDATES = [
    Path(r"host-local\redacted_host\repo\judgment\live\.book_event.env"),
    Path("/workspace/gtos/live/.book_event.env"),
]
URL_KEYS = ("BOOK_WEBHOOK_URL", "GROK_BOOK_EVENT_URL")
KEY_KEYS = ("BOOK_WEBHOOK_KEY", "GROK_BOOK_EVENT_KEY")
KINDS = ("candidate", "fill", "close", "mfe", "pair_dead")
LIVE_LOGIN = 0  # Challenge cutover 2026-09-09/10
MIN_LIVE_TICKET = 180000000
SKIP_LOG = Path(r"host-local\redacted_host\repo\judgment\live\book_event_skip.jsonl")
BOX_SKIP_LOG = Path("/workspace/gtos/live/book_event_skip.jsonl")


def _parse_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_env(env_path: Path | None = None) -> dict[str, str]:
    merged: dict[str, str] = {}
    paths = [env_path] if env_path else ENV_CANDIDATES
    for p in paths:
        if p is None:
            continue
        merged.update(_parse_env_file(Path(p)))
    for k in (*URL_KEYS, *KEY_KEYS):
        if os.environ.get(k):
            merged[k] = os.environ[k]
    return merged


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _skip_log(row: dict) -> None:
    line = json.dumps(row, ensure_ascii=False) + "\n"
    for path in (SKIP_LOG, BOX_SKIP_LOG):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
            return
        except Exception:
            continue


def live_ticket(ticket) -> int | None:
    if ticket is None or ticket is False:
        return None
    try:
        t = int(str(ticket).strip())
    except (TypeError, ValueError):
        return None
    if t < MIN_LIVE_TICKET:
        return None
    return t


def identity_ok(kind: str, fields: dict) -> tuple[bool, str]:
    """Refuse harvest, old login, and non-tickets at the POST door."""
    if kind == "pair_dead":
        return True, "pair_dead"
    login = fields.get("login")
    if login is not None and str(login).strip() != "":
        try:
            if int(login) != LIVE_LOGIN:
                return False, f"login {login} != {LIVE_LOGIN}"
        except (TypeError, ValueError):
            return False, f"login_unreadable {login!r}"
    t = live_ticket(fields.get("ticket"))
    if t is None:
        return False, f"not_live_ticket {fields.get('ticket')!r}"
    return True, f"login {LIVE_LOGIN} ticket {t}"


def emit(kind: str, *, env_path: Path | None = None, timeout: float = 30.0, **fields) -> dict:
    if kind not in KINDS:
        return {"ok": False, "error": f"bad kind {kind!r}"}
    ok_id, reason = identity_ok(kind, fields)
    if not ok_id:
        _skip_log({
            "ts_utc": utc_now(),
            "kind": kind,
            "ticket": fields.get("ticket"),
            "login": fields.get("login"),
            "symbol": fields.get("symbol"),
            "reason": reason,
        })
        return {
            "ok": False,
            "skipped": True,
            "reason": reason,
            "kind": kind,
            "ticket": fields.get("ticket"),
            "login": fields.get("login"),
            "status": None,
        }
    env = load_env(env_path)
    url = ""
    key = ""
    for k in URL_KEYS:
        if env.get(k):
            url = env[k].strip()
            break
    for k in KEY_KEYS:
        if env.get(k):
            key = env[k].strip()
            break
    ticket = live_ticket(fields.get("ticket")) if kind != "pair_dead" else fields.get("ticket")
    body = {
        "kind": kind,
        "ticket": ticket,
        "symbol": fields.get("symbol"),
        "side": fields.get("side"),
        "price": fields.get("price"),
        "sl": fields.get("sl"),
        "tp": fields.get("tp"),
        "volume": fields.get("volume"),
        "R_orig": fields.get("R_orig") if fields.get("R_orig") is not None else fields.get("r_orig"),
        "MFE": fields.get("MFE") if fields.get("MFE") is not None else fields.get("mfe"),
        "session": fields.get("session"),
        "comment": fields.get("comment") or fields.get("note"),
        "source": fields.get("source") or "f5_writer",
        "login": LIVE_LOGIN,
        "ts_utc": fields.get("ts_utc") or utc_now(),
    }
    body = {k: v for k, v in body.items() if v is not None and v != ""}
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = key if key.lower().startswith("bearer ") else f"Bearer {key}"
    mill_ok = False
    mill_err = None
    try:
        mill = Path(r"host-local\redacted_host\repo\judgment\live\cursor-mill")
        mill.mkdir(parents=True, exist_ok=True)
        with (mill / "inbox.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, ensure_ascii=False) + "\n")
        mill_ok = True
    except Exception as e:
        mill_err = type(e).__name__
    ledger_ok = False
    try:
        ledger = Path(r"host-local\redacted_host\repo\judgment\live\book_event_ledger.jsonl")
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, ensure_ascii=False) + "\n")
        ledger_ok = True
    except Exception:
        ledger_ok = False
    fleet_ok = False
    fleet_err = None
    if kind in ("fill", "close"):
        try:
            repo = Path(r"host-local\redacted_host\repo")
            if str(repo) not in sys.path:
                sys.path.insert(0, str(repo))
            from judgment.fleet.book_event_emit import emit_book_event
            emit_book_event({**body, "source_login": LIVE_LOGIN, "login": LIVE_LOGIN})
            fleet_ok = True
        except Exception as e:
            fleet_err = type(e).__name__
    local_ok = bool(mill_ok or ledger_ok or fleet_ok)
    webhook_status = None
    webhook_err = None
    text = ""
    if url:
        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=timeout) as resp:
                webhook_status = int(resp.status)
                text = resp.read()[:400].decode("utf-8", errors="replace")
        except error.HTTPError as e:
            webhook_status = int(e.code)
            webhook_err = f"HTTP {webhook_status}"
        except Exception as e:
            webhook_err = type(e).__name__
    elif not local_ok:
        webhook_err = mill_err or "missing BOOK_WEBHOOK_URL"
    return {
        "ok": bool(local_ok or webhook_status == 200),
        "status": webhook_status,
        "kind": kind,
        "ticket": body.get("ticket"),
        "mill": mill_ok,
        "ledger": ledger_ok,
        "fleet": fleet_ok,
        "fleet_err": fleet_err,
        "error": None if local_ok or webhook_status == 200 else webhook_err,
        "resp_len": len(text),
        "exhausted": webhook_status in (429, 503) if webhook_status is not None else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=list(KINDS))
    ap.add_argument("--ticket", default="")
    ap.add_argument("--symbol", default="")
    ap.add_argument("--side", default="")
    ap.add_argument("--price", type=float, default=None)
    ap.add_argument("--sl", type=float, default=None)
    ap.add_argument("--tp", type=float, default=None)
    ap.add_argument("--volume", type=float, default=None)
    ap.add_argument("--r-orig", dest="r_orig", type=float, default=None)
    ap.add_argument("--mfe", dest="mfe", type=float, default=None)
    ap.add_argument("--session", default="")
    ap.add_argument("--comment", default="")
    ap.add_argument("--source", default="f5_writer")
    ap.add_argument("--login", default="")
    ap.add_argument("--env-path", default="")
    args = ap.parse_args(argv)
    env_path = Path(args.env_path) if args.env_path else None
    result = emit(
        args.kind,
        env_path=env_path,
        ticket=args.ticket or None,
        symbol=args.symbol or None,
        side=args.side or None,
        price=args.price,
        sl=args.sl,
        tp=args.tp,
        volume=args.volume,
        R_orig=args.r_orig,
        MFE=args.mfe,
        session=args.session or None,
        comment=args.comment or None,
        source=args.source,
        login=args.login or None,
    )
    print(json.dumps(result))
    return 0 if result.get("ok") or result.get("skipped") else 1


if __name__ == "__main__":
    sys.exit(main())

