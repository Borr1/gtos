from pathlib import Path
paths = [
    Path(r"host-local\redacted_host\repo\scripts\f5_desk\chair_stack_hold.py"),
    Path(r"host-local\redacted_host\repo\src\components\ultimate_book\minimal_size.py"),
]
keys = ("just_closed", "sibling", "same_symbol", "USDJPY", "standing_hold", "F5_STANDING")
for p in paths:
    print("===", p, p.exists())
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if any(k.lower() in low for k in keys):
            print(f"{i}:{line[:160]}")
