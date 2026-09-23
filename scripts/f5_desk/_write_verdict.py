from pathlib import Path
import sys
import json
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common
src = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\_incoming.json")
dst = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
payload = json.loads(src.read_text(encoding="utf-8"))
common.write_json_atomic(dst, payload)
src.unlink(missing_ok=True)
print("inbox_ok", payload["slate_id"], payload["fingerprint"], len(payload["verdicts"]))
