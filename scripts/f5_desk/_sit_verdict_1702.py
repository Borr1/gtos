import json, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common

ptr = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
s = json.loads(ptr.read_text(encoding="utf-8"))
slate_id = s["slate_id"]
fp = s["fingerprint"]
slate_path = Path(s["path"])
sl = json.loads(slate_path.read_text(encoding="utf-8"))

# find candidates / opens across known shapes
cands = []
opens = []
if isinstance(sl, dict):
    for k in ("candidates", "items", "rows"):
        v = sl.get(k)
        if isinstance(v, list):
            cands = v
            break
    body = sl.get("slate") or sl.get("body") or {}
    if not cands and isinstance(body, dict):
        cands = body.get("candidates") or body.get("items") or []
    opens = sl.get("open_positions") or sl.get("opens") or []
    if not opens and isinstance(body, dict):
        opens = body.get("open_positions") or body.get("opens") or []

print("SLATE", slate_id, fp, s.get("built_at_utc"))
print("N_CAND", len(cands) if isinstance(cands, list) else type(cands))
print("N_OPEN", len(opens) if isinstance(opens, list) else type(opens))
if isinstance(cands, list):
    for c in cands:
        if isinstance(c, dict):
            cid = c.get("candidate_id") or c.get("id") or ""
            print("CAND", cid, c.get("status"), c.get("symbol") or "", c.get("direction") or c.get("side") or "")
        else:
            print("CAND", c)
if isinstance(opens, list):
    for o in opens:
        if isinstance(o, dict):
            print("OPEN", o.get("ticket"), o.get("symbol"), o.get("direction") or o.get("side"))
        else:
            print("OPEN", o)

occupied = {"BTCUSD", "ETHUSD", "GER40", "US30", "US30_cash"}
spent = {"XAUUSD", "EURUSD"}
usdjpy = {"USDJPY"}

verdicts = []
if isinstance(cands, list):
    for c in cands:
        if not isinstance(c, dict):
            continue
        cid = c.get("candidate_id") or c.get("id") or ""
        if not cid:
            continue
        parts = cid.split("::")
        sym = ""
        if len(parts) >= 3:
            sym = parts[2]
        # also use explicit symbol
        sym = (c.get("symbol") or sym or "").replace(" ", "")
        if sym in usdjpy or "USDJPY" in cid:
            verdicts.append({
                "candidate_id": cid,
                "verdict": "hold",
                "mechanism": "microstructure",
                "why_code": "usdjpy_named_hold_scrub",
                "confidence": 0.9,
            })
        elif any(x in cid or sym == x for x in occupied):
            verdicts.append({
                "candidate_id": cid,
                "verdict": "hold",
                "mechanism": "microstructure",
                "why_code": "occupied_live_no_second_ticket",
                "confidence": 0.8,
            })
        elif any(x in cid or sym == x for x in spent):
            verdicts.append({
                "candidate_id": cid,
                "verdict": "abstain",
                "mechanism": "",
                "why_code": "owner_spent_tonight_no_remint",
                "confidence": 0.85,
            })
        else:
            verdicts.append({
                "candidate_id": cid,
                "verdict": "abstain",
                "mechanism": "",
                "why_code": "chair_no_place_from_seats",
                "confidence": 0.55,
            })

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload = {
    "schema": "gtos.f5.judge.verdict.v1",
    "slate_id": slate_id,
    "fingerprint": fp,
    "written_at_utc": now,
    "verdicts": verdicts,
    "manage": [],
    "notes": "sit 17:02 ICT eq 98724 bal 98817 day_net+502 to_pass 6183 open4 pend0; same tickets US30/GER40/ETH/BTC sit live tape; leave all; USDJPY HOLD; gold/EUR spent abstain; no place; writer GTOS_F5_FTMO Running 10011 ghost close; Japan FX intervention LAND no occupied name; aim 100k (~1.28k short)",
}
out = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
common.write_json_atomic(out, payload)
print("WROTE", out, "n_verdicts", len(verdicts), "slate", slate_id, "fp", fp)
