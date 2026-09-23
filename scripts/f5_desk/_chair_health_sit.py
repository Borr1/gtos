import json, sys, subprocess
from pathlib import Path

def out(s=""):
    sys.stdout.buffer.write((str(s) + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()

log = Path(r"host-local\redacted_host\repo\shadow_logs\f5_verification.log")
raw = log.read_bytes()
text = None
for enc in ("utf-16", "utf-16-le", "utf-8"):
    try:
        text = raw.decode(enc)
        if "book[" in text or "INFO" in text:
            out("log_enc %s bytes %d" % (enc, len(raw)))
            break
    except Exception:
        continue
if text is None:
    text = raw.decode("utf-8", errors="replace")
lines = [L for L in text.splitlines() if L.strip()]
out("---VERIF_TAIL---")
for L in lines[-40:]:
    out(L.encode("ascii", "replace").decode("ascii")[:400])
out("---VERIF_GREP---")
keys = ("FAILED", "immutable_entry_risk_unavailable", "governor_ready", "reconciliation", "writer healthy", "DEAD", "restart")
for L in lines[-200:]:
    low = L.lower()
    if any(k.lower() in L or k.lower() in low for k in keys):
        out(L.encode("ascii", "replace").decode("ascii")[:400])

out("---TASK---")
r = subprocess.run(["schtasks", "/query", "/tn", "GTOS_F5_FTMO", "/fo", "LIST"], capture_output=True, text=True, encoding="utf-8", errors="replace")
out((r.stdout or r.stderr or "")[:1500])

out("---PIDS---")
r = subprocess.run(["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"], capture_output=True, text=True, encoding="utf-8", errors="replace")
for line in (r.stdout or "").splitlines():
    low = line.lower()
    if "operator" in low or "judge_daemon" in low or "gtos_f5" in low:
        # compress
        pid = ""
        parts = line.split()
        if parts and parts[-1].isdigit():
            pid = parts[-1]
        ns = "f5" if "operator" in low else ("judge" if "judge" in low else "other")
        out("PID %s ns=%s" % (pid, ns))

out("---SLATE_PTR---")
ptr = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
d = json.loads(ptr.read_text(encoding="utf-8"))
out(json.dumps(d, default=str)[:2000])
p = d.get("path")
out("path %s" % p)
if p:
    sp = Path(p)
    if not sp.exists():
        # try relative to repo
        sp2 = Path(r"host-local\redacted_host\repo") / p
        out("try %s exists %s" % (sp2, sp2.exists()))
        if sp2.exists():
            sp = sp2
    out("slate_file_exists %s" % sp.exists())
    if sp.exists():
        slate = json.loads(sp.read_text(encoding="utf-8"))
        out("slate_keys %s" % list(slate.keys())[:40])
        out("slate_id %s fp %s" % (slate.get("slate_id") or slate.get("id"), slate.get("fingerprint")))
        cands = slate.get("candidates") or slate.get("candidate_set") or []
        if isinstance(cands, dict):
            cands = cands.get("items") or list(cands.values())
        opens = slate.get("open_positions") or slate.get("opens") or []
        if isinstance(opens, dict):
            opens = opens.get("items") or list(opens.values())
        out("CANDS %d OPENS %d" % (len(cands) if isinstance(cands, list) else -1, len(opens) if isinstance(opens, list) else -1))
        if isinstance(cands, list):
            for c in cands[:40]:
                if isinstance(c, dict):
                    out("CAND %s st=%s sym=%s dir=%s" % (c.get("candidate_id") or c.get("id"), c.get("status") or c.get("state"), c.get("symbol") or c.get("broker_symbol"), c.get("direction") or c.get("side")))
                else:
                    out("CAND %s" % str(c)[:240])
        if isinstance(opens, list):
            for o in opens[:20]:
                out("OPEN %s" % json.dumps(o, default=str)[:400])
        snip = {
            "slate_id": slate.get("slate_id") or d.get("slate_id"),
            "fingerprint": slate.get("fingerprint") or d.get("fingerprint"),
            "candidates": cands[:40] if isinstance(cands, list) else cands,
            "opens": opens[:20] if isinstance(opens, list) else opens,
            "governor_ready": slate.get("governor_ready"),
        }
        Path(r"host-local\redacted_host\repo\scripts\f5_desk\_slate_snip.json").write_text(json.dumps(snip, default=str), encoding="utf-8")
        out("wrote snip")
