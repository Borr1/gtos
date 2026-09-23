from pathlib import Path
from datetime import datetime, timezone
state = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state")
print("exists", state.exists())
for p in sorted(state.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
    print(f"{p.name}\t{datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()}\t{p.stat().st_size}")
