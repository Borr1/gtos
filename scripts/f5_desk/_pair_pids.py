import os
try:
    import psutil
except ImportError:
    psutil = None
    print("NO_PSUTIL")
keys = ("ftmo_f5", "book_owner", "ultimate_book", "judge_daemon", "GTOS_F5")
if psutil:
    xs = []
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        n = (p.info.get("name") or "").lower()
        cl = " ".join(p.info.get("cmdline") or [])
        if "python" in n and any(k.lower() in cl.lower() for k in keys):
            xs.append((p.info["pid"], cl[:180]))
    print("PAIR", ",".join(str(a[0]) for a in xs) or "none")
    for a in xs:
        print(a[0], a[1])
else:
    print("PAIR none")
