import json
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

pointer = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
d = json.loads(pointer.read_text(encoding="utf-8"))
slate = json.loads(Path(d["path"]).read_text(encoding="utf-8"))
print("governor", json.dumps(slate.get("governor"), default=str)[:500])
print("flow", json.dumps(slate.get("flow_state"), default=str)[:400])
# occupied open tickets from sit (broker truth this wake)
occupied = {"EURUSD", "GBPUSD", "UK100", "US30", "USDCAD", "US30_cash"}
# GBPUSD just filled age~0 this sit -> microstructure hold on other GBPUSD rows still intent/refused
verdicts = []
for c in slate.get("candidates") or []:
    cid = c.get("id") or c.get("candidate_id")
    sym = (c.get("symbol") or "").replace("_cash", "")
    status = c.get("status")
    if not cid:
        continue
    # filled rows: leave alone (no word needed) — still abstain so daemon has a word
    if status == "filled":
        verdicts.append({
            "candidate_id": cid,
            "verdict": "abstain",
            "mechanism": "",
            "why_code": "already_filled_path",
            "confidence": 0.55,
        })
        continue
    if sym == "GBPUSD" and status in ("intent", "refused"):
        # just-closed/family remint window: live GBPUSD ticket age~0
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "just_filled_same_symbol_within_15m",
            "confidence": 0.7,
        })
        continue
    if sym in occupied and status == "intent":
        # no second ticket on live/pending occupied symbol
        verdicts.append({
            "candidate_id": cid,
            "verdict": "hold",
            "mechanism": "microstructure",
            "why_code": "occupied_no_second_ticket",
            "confidence": 0.65,
        })
        continue
    if status in ("intent", "refused"):
        verdicts.append({
            "candidate_id": cid,
            "verdict": "abstain",
            "mechanism": "",
            "why_code": "chair_sit_no_named_veto",
            "confidence": 0.45,
        })

# keep payload lean: prefer holds + key abstains; cap at ~20
holds = [v for v in verdicts if v["verdict"] == "hold"]
absts = [v for v in verdicts if v["verdict"] == "abstain"]
# always include GBPUSD walkhigh + EURUSD pending family
prefer = []
for v in holds + absts:
    if len(prefer) >= 18:
        break
    prefer.append(v)

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": d["slate_id"],
    "fingerprint": d["fingerprint"],
    "written_at_utc": now,
    "verdicts": prefer,
    "manage": [],
    "notes": "22:56Z sit: UK100/US30/USDCAD/GBPUSD live + EURUSD BUY_LIMIT 179489256. day_net -12.5. No tape veto. HOLD microstructure on occupied/same-symbol remint intents. Writer pair 15552/16640 GTOS_F5_FTMO Running. No place.",
}
out = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
common.write_json_atomic(out, payload)
print("WROTE", out, "n=", len(prefer), "holds", sum(1 for v in prefer if v["verdict"]=="hold"))
print(json.dumps({"slate_id": d["slate_id"], "fingerprint": d["fingerprint"], "written_at_utc": now}, indent=2))
