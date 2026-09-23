from pathlib import Path
import json
p = Path(r"C:host-local/redacted_host/repo/pipeline_state/ultimate_book/operator/judgment/inbox/verdict.json")
print("exists", p.exists(), "size", p.stat().st_size if p.exists() else 0)
d = json.loads(p.read_text(encoding="utf-8"))
print(d["slate_id"], len(d["verdicts"]), d["written_at_utc"])
