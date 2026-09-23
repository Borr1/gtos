from pathlib import Path
p = Path(r"host-local\redacted_host\repo\scripts\f5_desk\chair_desk.py")
text = p.read_text(encoding="utf-8", errors="replace")
print("size", len(text))
for i, line in enumerate(text.splitlines(), 1):
    low = line.lower()
    if any(k in low for k in ("digit", "format", "mark=", "print(", "f5_norm", "price", ":.", "round(")):
        if i < 250 or "digit" in low or "format" in low:
            print(f"{i}:{line[:180]}")
