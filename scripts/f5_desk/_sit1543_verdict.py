
import json, subprocess
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

raw = subprocess.check_output(
    "wmic process where \"CommandLine like '%%operator%%run_book.py%%'\" get ProcessId /FORMAT:LIST",
    shell=True, text=True, errors="replace",
)
pids = []
for line in raw.splitlines():
    if line.startswith("ProcessId="):
        p = line.split("=",1)[1].strip()
        if p and p not in pids:
            pids.append(p)
pair = "/".join(pids[:2]) if pids else "none"
print("pair", pair)

slate_ptr = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
ptr = json.loads(slate_ptr.read_text(encoding="utf-8"))
slate_path = Path(ptr["path"])
slate = json.loads(slate_path.read_text(encoding="utf-8"))
slate_id = slate.get("slate_id") or ptr["slate_id"]
fingerprint = slate.get("fingerprint") or ptr["fingerprint"]
opens = slate.get("open_positions") or []
open_syms = set()
for o in opens:
    sym = (o.get("symbol") or "")
    open_syms.add(sym)
    open_syms.add(sym.replace("_cash", "").replace(".cash", ""))

# live occupied from this sit
for s in ("BTCUSD", "ETHUSD", "EURUSD", "GER40", "US30", "US30_cash"):
    open_syms.add(s)

cands = slate.get("candidates") or []
verdicts = []
seen = set()
for c in cands:
    cid = c.get("candidate_id") or ""
    if not cid or cid in seen:
        continue
    seen.add(cid)
    status = (c.get("status") or "").lower()
    if status == "filled":
        continue
    sym = (c.get("symbol") or c.get("broker_symbol") or "")
    sym_base = sym.replace("_cash", "").replace(".cash", "")
    if sym_base == "USDJPY":
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "usdjpy_scrub_full_verification_hold",
            "confidence": 0.85,
        })
        continue
    if sym_base in open_syms or sym in open_syms:
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "occupied_no_second_ticket",
            "confidence": 0.8,
        })
        continue
    if sym_base == "XAUUSD":
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "owner_spent_gold_no_remint_tonight",
            "confidence": 0.8,
        })
        continue
    verdicts.append({
        "candidate_id": cid,
        "verdict": "abstain",
        "mechanism": "",
        "why_code": "chair_sit_no_place_from_seat",
        "confidence": 0.55,
    })

holds = [v for v in verdicts if v["verdict"] == "hold"]
# keep all holds + up to 12 abstains
payload_verdicts = holds + [v for v in verdicts if v["verdict"] == "abstain"][:12]
now = datetime.now(timezone.utc)
notes = (
    f"15:43 ICT sit: bal99099.93 eq98697.65 day_net+784 to_pass~5900 open5 "
    f"US30/EURUSD/GER40/ETH/BTC leave; crypto NULL RULE; USDJPY scrub HOLD; "
    f"gold spent no remint; no place; writer pair {pair}; close-fail noise 10011; aim>100k"
)
payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": slate_id,
    "fingerprint": fingerprint,
    "written_at_utc": now.isoformat().replace("+00:00", "Z"),
    "verdicts": payload_verdicts,
    "manage": [],
    "notes": notes[:2000],
}
inbox = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
common.write_json_atomic(inbox, payload)
print("wrote", inbox)
print("slate", slate_id, "fp", fingerprint)
print("holds", len(holds), "rows", len(payload_verdicts))
print("notes", notes)
