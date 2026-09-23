import os, json, pathlib
base = pathlib.Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator")
shadow = pathlib.Path(r"host-local\redacted_host\repo\shadow_logs")
hits = []
for root, dirs, files in os.walk(base):
    for f in files:
        fl = f.lower()
        if any(x in fl for x in ("reconcil", "governor", "health", "immutable", "ready")):
            hits.append(os.path.join(root, f))
for p in hits[:40]:
    print("HIT", p, os.path.getsize(p))
    try:
        raw = open(p, encoding="utf-8", errors="replace").read()[:500]
        print(raw.replace("\n", " ")[:400])
    except Exception as e:
        print("ERR", e)
# last non-ERROR verification lines
log = shadow / "f5_verification.log"
if log.exists():
    lines = log.read_text(errors="replace").splitlines()
    interesting = [l for l in lines if any(x in l for x in ("FAILED", "governor", "reconcil", "immutable", "PASS", "healthy", "READY", "OK"))]
    print("INTERESTING", len(interesting))
    for l in interesting[-20:]:
        print(l[:240])
# console log tail for close attempts context
for name in ("run_book_console.log", "run_book_ftmo_f5_console.log", "f5_writer.log"):
    p = shadow / name
    if p.exists():
        print("LOG", name, "size", p.stat().st_size)
        for l in p.read_text(errors="replace").splitlines()[-8:]:
            print(l[:220])
