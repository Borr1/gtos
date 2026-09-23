import os, glob
try:
    import psutil
except ImportError:
    psutil = None
hits = []
if psutil:
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cl = " ".join(p.info["cmdline"] or [])
        except Exception:
            continue
        if any(x in cl for x in ("GTOS_F5", "operator", "book_owner", "chair_desk")):
            hits.append((p.info["pid"], p.info["name"], cl[:220]))
else:
    import subprocess
    out = subprocess.check_output(["tasklist", "/FO", "CSV", "/V"], text=True, errors="replace")
    print("tasklist_head", "\n".join(out.splitlines()[:5]))

print("hits", len(hits))
for h in hits:
    print("PID", h[0], "NAME", h[1], "CMD", h[2])

paths = []
for pat in (
    r"host-local\redacted_host\**\f5_verification.log",
    r"C:\Users\MSI\Documents\ai-trading-agent\**\f5_verification.log",
):
    paths.extend(glob.glob(pat, recursive=True))
if not paths:
    print("NO_VERIF_LOG")
for g in paths[:5]:
    print("LOG", g, os.path.getmtime(g))
    try:
        lines = open(g, encoding="utf-8", errors="replace").read().splitlines()[-20:]
        for ln in lines:
            print(ln)
    except Exception as e:
        print("read_err", e)
