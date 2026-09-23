import json
from pathlib import Path
from datetime import datetime, timezone

root = Path(r"host-local\redacted_host\repo")
live = root / "judgment" / "live"
live.mkdir(parents=True, exist_ok=True)
TERM = r"C:\MT5\FTMO\terminal64.exe"


def _as_ticket(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float) and value.is_integer() and value > 0:
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        n = int(value.strip())
        return n if n > 0 else None
    return None


def extract_ticket(packet, prev):
    roots = []
    br = packet.get("broker") if isinstance(packet.get("broker"), dict) else {}
    roots.append(br)
    oso = br.get("order_send_observation") if isinstance(br.get("order_send_observation"), dict) else {}
    roots.append(oso)
    roots.append(oso.get("result") if isinstance(oso.get("result"), dict) else {})
    ident = br.get("identity") if isinstance(br.get("identity"), dict) else {}
    roots.append(ident)
    for root in roots:
        if not isinstance(root, dict):
            continue
        for key in ("order_ticket", "position_ticket", "ticket", "ticket_id"):
            t = _as_ticket(root.get(key))
            if t:
                return t
    if packet.get("candidate_id") and packet.get("candidate_id") == (prev or {}).get("candidate_id"):
        return _as_ticket((prev or {}).get("ticket_id"))
    return None


def open_tickets():
    """FTMO open tickets. None = could not see MT5 (do not invent spent)."""
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    if not mt5.initialize(path=TERM):
        return None
    try:
        pos = mt5.positions_get() or []
        out = set()
        for p in pos:
            t = _as_ticket(getattr(p, "ticket", None))
            if t:
                out.add(t)
        return out
    except Exception:
        return None
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


for day in ("2026-08-23", "2026-08-24"):
    src = root / "judgment" / ("flow_%s.json" % day)
    if src.is_file():
        (live / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

p = root / "shadow_logs" / "execution_manager_v4_decisions.jsonl"
with open(p, "rb") as f:
    f.seek(0, 2)
    n = f.tell()
    f.seek(max(0, n - 2500000))
    data = f.read().decode("utf-8", "replace")

seen = []
have = set()
last_allow = None
for ln in reversed(data.splitlines()):
    if "allow" not in ln:
        continue
    try:
        o = json.loads(ln)
    except Exception:
        continue
    if o.get("action") != "allow":
        continue
    if last_allow is None:
        last_allow = o
    ident = o.get("identity") or {}
    cid = ident.get("candidate_id")
    if not cid or cid in have:
        continue
    have.add(cid)
    et = o.get("entry_timing") or {}
    seen.append({
        "candidate_id": cid,
        "symbol": ident.get("symbol"),
        "generated_at_utc": o.get("generated_at_utc"),
        "action": o.get("action"),
        "selected_cell": (o.get("selected_cell_context") or {}).get("selected_cell_id"),
        "spread_r": (o.get("cost_context") or {}).get("spread_r"),
        "entry": et.get("entry_price"),
        "sl": et.get("stop_loss"),
    })
    if len(seen) >= 8:
        break
seen.reverse()
(live / "recent_allows.json").write_text(json.dumps(seen, indent=2) + "\n", encoding="utf-8")

if last_allow is not None:
    br_path = root / "shadow_logs" / "broker_order_lifecycle_capture_v4.jsonl"
    cid = (last_allow.get("identity") or {}).get("candidate_id")
    br = None
    with open(br_path, "rb") as f:
        f.seek(0, 2)
        n = f.tell()
        f.seek(max(0, n - 2500000))
        bdata = f.read().decode("utf-8", "replace")
    for ln in reversed(bdata.splitlines()):
        if cid and cid in ln:
            try:
                br = json.loads(ln)
                break
            except Exception:
                pass
    prev = {}
    prev_path = live / "latest.json"
    if prev_path.is_file():
        try:
            prev = json.loads(prev_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    keep_view = prev.get("candidate_id") == cid and isinstance(prev.get("market_view"), dict)
    packet = {
        "candidate_id": cid,
        "execution": {
            "identity": last_allow.get("identity"),
            "action": last_allow.get("action"),
            "generated_at_utc": last_allow.get("generated_at_utc"),
            "geometry_contract": last_allow.get("geometry_contract"),
            "selected_cell_context": last_allow.get("selected_cell_context"),
            "cost_context": last_allow.get("cost_context"),
            "entry_timing": last_allow.get("entry_timing"),
            "scheduler_v4": {
                "selected_action_class": (last_allow.get("scheduler_v4") or {}).get("selected_action_class"),
                "selected_candidate_id": (last_allow.get("scheduler_v4") or {}).get("selected_candidate_id"),
            },
            "source_completeness": last_allow.get("source_completeness"),
        },
        "broker": None if br is None else {
            "stage": br.get("stage"),
            "status": br.get("status"),
            "generated_at_utc": br.get("generated_at_utc"),
            "identity": br.get("identity"),
            "order_send_observation": br.get("order_send_observation"),
            "pretrade_cost_model": br.get("pretrade_cost_model"),
        },
    }
    if keep_view:
        packet["market_view"] = prev.get("market_view")
        packet["market_view_status"] = prev.get("market_view_status") or "present"
    same = prev.get("candidate_id") == cid and bool(cid)
    if same and isinstance(prev.get("news_tape"), dict):
        packet["news_tape"] = prev.get("news_tape")
    ticket = extract_ticket(packet, prev)
    opens = open_tickets()
    if ticket is not None:
        packet["ticket_id"] = ticket
    if opens is None:
        # Missing fire_status is not spent. Keep prior stamp on same cid.
        if same and prev.get("fire_status") in ("live", "spent"):
            packet["fire_status"] = prev["fire_status"]
            packet["ticket_live"] = bool(prev.get("ticket_live"))
        elif ticket is None:
            pass
        else:
            packet["fire_status"] = "live"
            packet["ticket_live"] = False
    elif ticket is not None and ticket in opens:
        packet["fire_status"] = "live"
        packet["ticket_live"] = True
    elif ticket is not None:
        packet["fire_status"] = "spent"
        packet["ticket_live"] = False
    elif same and prev.get("fire_status") in ("live", "spent"):
        packet["fire_status"] = prev["fire_status"]
        packet["ticket_live"] = bool(prev.get("ticket_live"))
    (live / "latest.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

view_present = False
if last_allow is not None:
    view_present = bool((packet.get("market_view") or {}).get("present"))
status = {
    "written_at_utc": datetime.now(timezone.utc).isoformat(),
    "namespace": "operator",
    "size_usd": 75,
    "magic": 0,
    "market_view_on_live_path": view_present,
    "latest_candidate_id": (last_allow.get("identity") or {}).get("candidate_id") if last_allow else None,
    "recent_allow_count": len(seen),
    "note": "latest.json is the newest allow. fire_status spent means that ticket is dead.",
}
(live / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
print("ok latest", status["latest_candidate_id"])
