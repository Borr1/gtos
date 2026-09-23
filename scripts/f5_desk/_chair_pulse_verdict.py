# -*- coding: utf-8 -*-
import json, os, subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

ROOT = Path(r"host-local\redacted_host\repo")
BOOK = ROOT / "pipeline_state" / "ultimate_book" / "operator"
INBOX = BOOK / "judgment" / "inbox" / "verdict.json"
LATEST = BOOK / "judgment" / "state" / "latest_slate.json"

# --- pulse ---
procs = []
try:
    import psutil
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cl = p.info.get("cmdline") or []
            s = " ".join(cl).lower()
            if any(k in s for k in ("book_owner", "ultimate_book", "gtos_f5", "judge_daemon", "ftmo_f5")):
                procs.append({"pid": p.info["pid"], "cmd": " ".join(cl)[:200]})
        except Exception:
            pass
except Exception as e:
    procs = [{"error": str(e)}]

r = subprocess.run(["schtasks", "/Query", "/TN", "GTOS_F5_FTMO", "/FO", "LIST"], capture_output=True, text=True)
task = (r.stdout or r.stderr or "")[:600]

gov_path = BOOK / "governor_ready.json"
gov = None
if gov_path.exists():
    try:
        gov = json.loads(gov_path.read_text(encoding="utf-8"))
    except Exception as e:
        gov = {"error": str(e)}

# --- slate ---
ptr = json.loads(LATEST.read_text(encoding="utf-8"))
slate_id = ptr["slate_id"]
fingerprint = ptr["fingerprint"]
slate_path = Path(ptr.get("path") or "")
if not slate_path.exists():
    # fallback from pointer fields
    slate_path = BOOK / "judgment" / "slates" / f"slate_{ptr.get('built_at_utc','')[:19].replace('-','').replace(':','')}Z_{slate_id}.json"

slate = {}
if slate_path.exists():
    slate = json.loads(slate_path.read_text(encoding="utf-8"))
else:
    # glob
    cands = list((BOOK / "judgment" / "slates").glob(f"slate_*_{slate_id}.json"))
    if cands:
        slate = json.loads(cands[0].read_text(encoding="utf-8"))

verdicts = []
for c in slate.get("candidates") or []:
    cid = c.get("candidate_id")
    sym = (c.get("symbol") or "").replace("_cash", "")
    status = c.get("status")
    direction = c.get("direction")
    if not cid:
        continue
    # USDJPY scrub
    if sym == "USDJPY":
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "usd_jpy_named_scrub",
            "confidence": 0.7,
        })
        continue
    # second ticket / opposite on occupied
    occupied = {"EURUSD", "GBPUSD", "UK100", "US30", "XAUUSD"}
    if sym in occupied and status == "intent":
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "correlation",
            "why_code": "same_symbol_stack_keep_working_ticket",
            "confidence": 0.8,
        })
        continue
    # filled / already live path: abstain leave
    verdicts.append({
        "candidate_id": cid,
        "verdict": "abstain",
        "mechanism": "",
        "why_code": "sit_leave_same_tickets_no_named_mechanism",
        "confidence": 0.5,
    })

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": slate_id,
    "fingerprint": fingerprint,
    "written_at_utc": now,
    "verdicts": verdicts,
    "manage": [],
    "notes": "08:55 ICT sit: leave UK100/US30/GBPUSD/XAUUSD + EURUSD BUY_LIMIT; HOLD USDJPY scrub + intent stacks on occupied; no manage; day_net -579.",
}
common.write_json_atomic(INBOX, payload)

out = {
    "pulse_procs": procs,
    "task_head": task,
    "governor": gov,
    "slate_id": slate_id,
    "fingerprint": fingerprint,
    "n_verdicts": len(verdicts),
    "inbox": str(INBOX),
    "written_at_utc": now,
}
print(json.dumps(out, indent=2))
