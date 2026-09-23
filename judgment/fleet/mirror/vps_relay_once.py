#!/usr/bin/env python3
"""VPS-side relay: judgment/live book_event*.jsonl → fleet_events.jsonl for mirror fanout."""
from __future__ import annotations
import argparse, json, uuid
from pathlib import Path
from datetime import datetime, timezone

SOURCE_LOGIN = 0
QUARANTINE = 0

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def normalize(row: dict) -> dict | None:
    kind = row.get("kind") or row.get("event") or row.get("type")
    if kind not in ("fill", "close", "mfe", "high", "candidate"):
        return None
    ticket = row.get("ticket") or row.get("order") or row.get("deal")
    if ticket is None:
        return None
    login = row.get("login") or row.get("source_login")
    # Prefer tagging source as Challenge lock; quarantine rows still emit as events
    # but mirror never places on those logins.
    return {
        "schema": "gtos.fleet_event.v0",
        "fleet_event_id": str(uuid.uuid4()),
        "ts_utc": row.get("ts_utc") or row.get("ts") or utc_now(),
        "kind": kind,
        "ticket": ticket,
        "symbol": row.get("symbol") or row.get("sym"),
        "side": row.get("side") or row.get("type_str"),
        "sleeve": row.get("sleeve") or row.get("tag"),
        "r_orig": row.get("r_orig") or row.get("r"),
        "mfe": row.get("mfe"),
        "exit_class": row.get("exit_class"),
        "note": row.get("note"),
        "source_login": SOURCE_LOGIN,
        "ledger_login": login,
        "relay_ts_utc": utc_now(),
        "ledger_source": "vps_judgment_live",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-dir", default=r"host-local\redacted_host\repo\judgment\live")
    ap.add_argument("--outbox", default=None)
    ap.add_argument("--state", default=None)
    args = ap.parse_args()
    live = Path(args.live_dir)
    outbox = Path(args.outbox) if args.outbox else live / "fleet_events.jsonl"
    state_p = Path(args.state) if args.state else live / "fleet_relay_state.json"
    candidates = sorted(live.glob("book_event*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    # Prefer ledger over spoken if both
    ledger = None
    for p in candidates:
        if "skip" in p.name:
            continue
        if p.name == "book_event_ledger.jsonl":
            ledger = p
            break
    if ledger is None:
        for p in candidates:
            if "skip" not in p.name and p.stat().st_size > 0:
                ledger = p
                break
    if ledger is None:
        print(json.dumps({"ok": False, "reason": "no_book_event_jsonl", "live": str(live)}))
        return 0
    st = {"offset_bytes": 0, "path": None}
    if state_p.is_file():
        st = json.loads(state_p.read_text(encoding="utf-8"))
    if st.get("path") != str(ledger):
        st = {"offset_bytes": 0, "path": str(ledger)}
    n = 0
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("rb") as fh:
        fh.seek(int(st.get("offset_bytes") or 0))
        while True:
            line = fh.readline()
            if not line:
                break
            st["offset_bytes"] = fh.tell()
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            ev = normalize(row)
            if not ev:
                continue
            with outbox.open("a", encoding="utf-8") as out:
                out.write(json.dumps(ev) + "\n")
            n += 1
    state_p.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "ledger": str(ledger), "emitted": n, "outbox": str(outbox), "offset": st["offset_bytes"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
