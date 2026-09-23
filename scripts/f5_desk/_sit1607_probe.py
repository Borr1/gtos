from pathlib import Path
import json, subprocess, re

slate_ptr = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
d = json.loads(slate_ptr.read_text(encoding="utf-8"))
print("PTR", json.dumps({k: d.get(k) for k in ("slate_id","fingerprint","built_at_utc","built_at","clock") if k in d or True}))
print("PTR_KEYS", sorted(d.keys()))
print("PTR_RAW", json.dumps(d)[:1500])

# resolve archived slate
sid = d.get("slate_id") or ""
fp = d.get("fingerprint") or ""
slates = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\slates")
hit = None
if slates.exists():
    cands = sorted(slates.glob("slate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    print("SLATE_N", len(cands), "newest", cands[0].name if cands else None)
    for p in cands[:8]:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print("BAD", p.name, e)
            continue
        print("FILE", p.name, "id", s.get("slate_id"), "fp", s.get("fingerprint"))
        if s.get("slate_id") == sid or (sid and sid in p.name):
            hit = s
            hit_name = p.name
            break
    if hit is None and cands:
        hit = json.loads(cands[0].read_text(encoding="utf-8"))
        hit_name = cands[0].name
if hit:
    print("HIT", hit_name)
    print("HIT_KEYS", sorted(hit.keys()))
    cands = hit.get("candidates") or hit.get("candidate_set") or hit.get("candidate_ids") or []
    opens = hit.get("opens") or hit.get("open_set") or hit.get("open_positions") or []
    print("cand_type", type(cands).__name__, "open_type", type(opens).__name__)
    def show(label, obj, n=60):
        if isinstance(obj, list):
            print(label, "n", len(obj))
            for c in obj[:n]:
                if isinstance(c, dict):
                    print(label, c.get("candidate_id") or c.get("id"), c.get("status"), c.get("symbol"), c.get("direction") or c.get("side"), c.get("ticket"))
                else:
                    print(label, c)
        elif isinstance(obj, dict):
            print(label, "n", len(obj))
            for k, v in list(obj.items())[:n]:
                if isinstance(v, dict):
                    print(label, k, v.get("status"), v.get("symbol"), v.get("direction") or v.get("side"), v.get("ticket"))
                else:
                    print(label, k, v)
    show("CAND", cands)
    show("OPEN", opens)

# writer pair
raw = subprocess.check_output(
    "wmic process where \"CommandLine like '%%operator%%'\" get ProcessId,CommandLine /FORMAT:LIST",
    shell=True, text=True, errors="replace",
)
pids = re.findall(r"ProcessId=(\d+)", raw)
print("PAIR", "/".join(pids) if pids else "none", "count", len(pids))
for line in raw.splitlines():
    if "CommandLine=" in line or "ProcessId=" in line:
        print(line[:220])

# recon / governor hints in latest verification isn't here; peek consume/flow
for name in ("governor_ready", "reconciliation"):
    pass
