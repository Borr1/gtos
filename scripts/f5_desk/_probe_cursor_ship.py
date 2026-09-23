from pathlib import Path
from datetime import datetime, timezone
import json, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
root = Path(r"C:host-local/redacted_host/repo")
ub = root / "src/components/ultimate_book"
print("===PYCACHE===")
pc = ub / "__pycache__"
if pc.exists():
    for p in sorted(pc.glob("*")):
        if any(x in p.name for x in ["book_engine","sleeve_geometry","admission","minimal_size","registry","xasset"]):
            print(datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(), p.name)
print("===PAIR===")
ps = r"Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_book.py' -and $_.CommandLine -match 'operator' } | Select-Object ProcessId,CreationDate | ConvertTo-Json"
try:
    out = subprocess.check_output(["powershell","-NoProfile","-Command", ps], text=True, encoding="utf-8", errors="replace")
    print(out[:2000])
except Exception as e:
    print("pair err", e)
print("===GEOM JSON===")
gj_path = ub / "data/SLEEVE_GEOMETRY_V1.json"
print("exists", gj_path.exists(), "bytes", gj_path.stat().st_size if gj_path.exists() else 0)
gj = json.loads(gj_path.read_text(encoding="utf-8"))
print("type", type(gj).__name__)
if isinstance(gj, dict):
    print("top_keys", list(gj.keys())[:30], "n", len(gj))
    inner = gj.get("sleeves") or gj.get("geometry") or gj.get("classes") or gj
    if isinstance(inner, dict):
        print("inner_n", len(inner), "sample", list(inner.items())[:3])
print("===GEOM PY===")
g = (ub / "sleeve_geometry.py").read_text(encoding="utf-8")
print("bytes", len(g), "apply", "apply_class_geometry" in g)
print("---geom first 90---")
print("\n".join(g.splitlines()[:90]))
print("===CALENDAR===")
ms = (ub / "minimal_size.py").read_text(encoding="utf-8")
idx = ms.find("f5_calendar_prime_window")
print("found", idx)
print(ms[idx:idx+2000] if idx>=0 else "NO CAL FN")
print("===TRAIL===")
ex = (root / "src/components/execution.py").read_text(encoding="utf-8")
print("trailing_runner count", ex.count("trailing_runner"))
idx = ex.find("def ") 
# find trailing functions
for i,line in enumerate(ex.splitlines(),1):
    if "trailing_runner" in line or "type_time" in line or "ORDER_TIME" in line:
        print(f"{i}|{line[:160]}")
print("===DECIDE===")
d = (root / "scripts/f5_desk/decide.py").read_text(encoding="utf-8")
print("bytes", len(d), "lines", d.count("\n")+1)
print(d)
print("===J2B MODULES===")
sl = ub / "sleeves"
mods = sorted(p.name for p in sl.glob("dsp_*.py"))
print("dsp_py", len(mods))
print("\n".join(mods))
print("===ARMING===")
ad = (ub / "admission.py").read_text(encoding="utf-8")
print("NOT ARMED", ad.count("NOT ARMED"), "J2B", "J2B_V2_LEFTOVER_PACK" in ad)
reg = (ub / "sleeves/registry.py").read_text(encoding="utf-8")
print("registry DISPLACEMENT_BUILT", "DISPLACEMENT_BUILT" in reg)
idx = reg.find("DISPLACEMENT_BUILT")
print(reg[idx:idx+800] if idx>=0 else "no DISPLACEMENT_BUILT")
print("===UNTRACKED NEW CODE===")
for rel in [
    "src/components/ultimate_book/sleeve_geometry.py",
    "src/components/ultimate_book/data/SLEEVE_GEOMETRY_V1.json",
    "scripts/f5_desk/decide.py",
    "scripts/f5_desk/DECISIONS.md",
    "src/components/ultimate_book/replay_sleeves.py",
]:
    p = root/rel
    print(("Y" if p.exists() else "N"), rel)
print("===TESTS===")
for p in sorted((root/"tests").glob("test_f5*")):
    print(p.name, datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat())
print("DONE")
