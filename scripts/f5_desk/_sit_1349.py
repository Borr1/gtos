# -*- coding: utf-8 -*-
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

ROOT = Path(r"host-local\redacted_host\repo")
BOOK = ROOT / "pipeline_state" / "ultimate_book" / "operator"
INBOX = BOOK / "judgment" / "inbox" / "verdict.json"
LATEST = BOOK / "judgment" / "state" / "latest_slate.json"

# pair pids
raw = subprocess.check_output(
    ["wmic", "process", "where", "CommandLine like '%%operator%%'", "get", "ProcessId,CommandLine", "/FORMAT:LIST"],
    text=True, errors="replace",
)
pids = re.findall(r"ProcessId=(\d+)", raw)
print("pair", "/".join(pids) if pids else "none", "count", len(pids))

task = subprocess.run(["schtasks", "/Query", "/TN", "GTOS_F5_FTMO", "/FO", "LIST"], capture_output=True, text=True)
print("task_head", (task.stdout or task.stderr or "")[:400])

gov_path = BOOK / "governor_ready.json"
if gov_path.exists():
    gov = json.loads(gov_path.read_text(encoding="utf-8"))
    print("governor_ready", gov)
else:
    print("governor_ready missing")

# recon files
for name in ("reconciliation.json", "immutable_entry_risk.json", "writer_health.json"):
    p = BOOK / name
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            print(name, json.dumps(d)[:300])
        except Exception as e:
            print(name, "err", e)

ptr = json.loads(LATEST.read_text(encoding="utf-8"))
slate_id = ptr["slate_id"]
fingerprint = ptr["fingerprint"]
slate_path = Path(ptr.get("path") or "")
if not slate_path.exists():
    cands = list((BOOK / "judgment" / "slates").glob(f"slate_*_{slate_id}.json"))
    slate_path = cands[0] if cands else slate_path
slate = json.loads(slate_path.read_text(encoding="utf-8")) if slate_path.exists() else {}

OCCUPIED = {"ETHUSD", "EURUSD", "GER40", "UK100", "US30", "XAUUSD"}
LIVE_CIDS_LEAVE = {
    "W7_BOOK::index::UK100::2026-08-27::LONG::idxrev",
    "W7_BOOK::index::US30_cash::2026-08-27::LONG::idxrev",
    "W7_BOOK::index::US30::2026-08-27::LONG::idxrev",
}

verdicts = []
seen = set()
cands = slate.get("candidates") or []
print("n_cands", len(cands), "slate", slate_id, "fp", fingerprint)
for c in cands:
    cid = c.get("candidate_id") or c.get("id")
    if not cid or cid in seen:
        continue
    seen.add(cid)
    raw_sym = (c.get("symbol") or "")
    # parse from cid if needed
    parts = cid.split("::")
    sym = raw_sym.replace("_cash", "") or (parts[2].replace("_cash", "") if len(parts) > 2 else "")
    status = (c.get("status") or "").lower()
    if "USDJPY" in cid or sym == "USDJPY":
        verdicts.append({"candidate_id": cid, "verdict": "hold", "mechanism": "microstructure", "why_code": "named_usdjpy_scrub", "confidence": 0.95})
        continue
    if sym in OCCUPIED and status in ("intent", "candidate", "armed", ""):
        # live working ticket leave vs second intent hold
        if cid in LIVE_CIDS_LEAVE or status in ("live", "filled", "open"):
            verdicts.append({"candidate_id": cid, "verdict": "abstain", "mechanism": "", "why_code": "live_ticket_leave", "confidence": 0.55})
            continue
        verdicts.append({"candidate_id": cid, "verdict": "hold", "mechanism": "correlation", "why_code": "occupied_no_second_ticket", "confidence": 0.88})
        continue
    if sym in OCCUPIED:
        verdicts.append({"candidate_id": cid, "verdict": "hold", "mechanism": "correlation", "why_code": "occupied_no_second_ticket", "confidence": 0.88})
        continue
    verdicts.append({"candidate_id": cid, "verdict": "abstain", "mechanism": "", "why_code": "no_named_mechanism_writer_prints", "confidence": 0.45})

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": slate_id,
    "fingerprint": fingerprint,
    "written_at_utc": now,
    "verdicts": verdicts,
    "manage": [],
    "notes": "13:49 ICT sit: same 6 lives leave (UK100 179453732 / US30 179453737 / EUR 179489256 / GER40 179553082 / XAU 179563723 BE-lock / ETH 179566918). HOLD USDJPY scrub + occupied no-second. pending 0. day_net -562.44 eq 98828.74. Writer 10011 orphan-close noise, no flatten. No place.",
}
common.write_json_atomic(INBOX, payload)
print("wrote", str(INBOX), "n", len(verdicts), "slate", slate_id, "fp", fingerprint, "at", now)
holds = sum(1 for v in verdicts if v["verdict"] == "hold")
print("holds", holds, "abstain", len(verdicts) - holds)
print("cids", [v["candidate_id"][:80] for v in verdicts[:12]])
