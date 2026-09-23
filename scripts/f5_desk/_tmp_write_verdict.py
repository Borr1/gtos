from pathlib import Path
import sys, json
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common
src = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\_verdict_incoming.json")
dst = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
payload = json.loads(src.read_text(encoding="utf-8"))
common.write_json_atomic(dst, payload)
print("wrote", dst, "slate", payload.get("slate_id"), "fp", payload.get("fingerprint"), "n", len(payload.get("verdicts") or []))
src.unlink(missing_ok=True)
