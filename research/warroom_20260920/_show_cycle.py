from pathlib import Path
lines = Path(r"host-local\redacted_host\repo\src\judgment\cycle.py").read_text(encoding="utf-8").splitlines()
for i in range(300, min(430, len(lines))):
    print(f"{i+1}|{lines[i]}")
