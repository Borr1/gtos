import hashlib
from pathlib import Path

root = Path(r"host-local\redacted_host\repo")
names = (
    r"src\components\ultimate_book\admission.py",
    r"src\judgment\admission_choices.py",
)
for name in names:
    path = root / name
    print("PATH", name)
    if not path.is_file():
        print("MISSING")
        continue
    data = path.read_bytes()
    print("SHA", hashlib.sha256(data).hexdigest())
    print("MTIME", path.stat().st_mtime)
    print("BYTES", len(data))
