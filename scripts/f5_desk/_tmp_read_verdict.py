from pathlib import Path
p = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\inbox\applied")
files = sorted(p.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
print(files[0] if files else "none")
if files:
    print(files[0].read_text(encoding="utf-8")[:8000])
