import json, sys
from pathlib import Path
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common
inbox = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox")
src = inbox / "_verdict_incoming.json"
payload = json.loads(src.read_text(encoding="utf-8"))
common.write_json_atomic(inbox / "verdict.json", payload)
print("ok", payload.get("slate_id"), payload.get("fingerprint"), payload.get("written_at_utc"))
