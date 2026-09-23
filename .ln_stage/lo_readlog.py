"""Session LO scratch: read mixed-encoding console logs (LN lesson 1: NUL-strip first)."""
import pathlib
import sys

pattern = sys.argv[1] if len(sys.argv) > 1 else "activation context declared"
tail = int(sys.argv[2]) if len(sys.argv) > 2 else 3
names = sys.argv[3:] or ["run_book_fn_console.log", "run_book_console.log",
                         "run_book_fn_console.log.err", "run_book_console.log.err"]

for name in names:
    p = pathlib.Path("shadow_logs") / name
    if not p.is_file():
        print(f"=== {name}: ABSENT ===")
        continue
    raw = p.read_bytes().replace(b"\x00", b"")
    txt = raw.decode("utf-8", "replace")
    hits = [l for l in txt.splitlines() if pattern in l]
    print(f"=== {name} ({p.stat().st_size} B) -- {len(hits)} lines matching {pattern!r} ===")
    for l in hits[-tail:]:
        print("   ", l.strip())
