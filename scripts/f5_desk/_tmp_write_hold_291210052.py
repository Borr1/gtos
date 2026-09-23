import json
from datetime import datetime, timezone
from pathlib import Path

repo = Path(r"host-local\redacted_host\repo")
jdir = repo / "pipeline_state" / "ultimate_book" / "operator" / "judgment"
inbox = jdir / "inbox" / "verdict.json"
slate_ptr = jdir / "slates" / "latest_slate.json"
state_orig = jdir / "state" / "chair_orig_sl.json"
cand = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\_verdict_cand_291210052.json")

payload = json.loads(cand.read_text(encoding="utf-8"))
# bind to whatever latest_slate says if present, else keep payload
if slate_ptr.exists():
    try:
        ptr = json.loads(slate_ptr.read_text(encoding="utf-8"))
        if isinstance(ptr, dict):
            # may be pointer or body
            sid = ptr.get("slate_id") or payload.get("slate_id")
            fp = ptr.get("fingerprint") or payload.get("fingerprint")
            # if pointer has path, load body
            p = ptr.get("path")
            if p and Path(p).exists():
                body = json.loads(Path(p).read_text(encoding="utf-8"))
                sid = body.get("slate_id") or sid
                fp = body.get("fingerprint") or fp
            payload["slate_id"] = sid
            payload["fingerprint"] = fp
    except Exception as e:
        payload.setdefault("_slate_bind_err", str(e))

# prefer the slate we sat (43c541e17a08924e) if pointer is older — keep payload ids
# already set in file

payload["schema"] = "gtos.f5.judge.verdict.v1"
payload["written_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
payload.setdefault("verdicts", [])
payload.setdefault("manage", [])
payload.setdefault("memory", [])
inbox.parent.mkdir(parents=True, exist_ok=True)
inbox.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

# latch orig if missing for live fill
orig = {}
if state_orig.exists():
    try:
        orig = json.loads(state_orig.read_text(encoding="utf-8")) or {}
    except Exception:
        orig = {}
if not isinstance(orig, dict):
    orig = {}
tickets = orig.get("tickets") if isinstance(orig.get("tickets"), dict) else orig
key = "291210052"
if key not in tickets and 291210052 not in tickets:
    entry = {
        "ticket": 291210052,
        "symbol": "XAUUSD",
        "side": "SHORT",
        "sl": 4417.48,
        "tp": 4369.73,
        "entry": 4412.17,
        "volume": 0.28,
        "magic": 0,
        "login": 0,
        "comment": "dsp_two_bar_thrust_into_20high_continues",
        "latched_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "f5-book-event candidate hold (already filled)",
    }
    if "tickets" in orig and isinstance(orig["tickets"], dict):
        orig["tickets"][key] = entry
    else:
        # flat map style
        orig[key] = entry
    state_orig.parent.mkdir(parents=True, exist_ok=True)
    state_orig.write_text(json.dumps(orig, indent=2) + "\n", encoding="utf-8")
    print("orig_latched", key)
else:
    print("orig_already_present", key)

print("wrote", inbox)
print("slate_id", payload.get("slate_id"), "fp", payload.get("fingerprint"))
print("n_verdicts", len(payload.get("verdicts") or []))
