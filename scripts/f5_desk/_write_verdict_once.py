from pathlib import Path
import sys, json
sys.path.insert(0, r"host-local\redacted_host\repo")
from scripts.f5_desk import common
tmp = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json.tmp")
payload = json.loads(tmp.read_text(encoding="utf-8"))
path = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\verdict.json")
common.write_json_atomic(path, payload)
print("wrote", path, "verdicts", len(payload.get("verdicts", [])), "slate", payload.get("slate_id"))
