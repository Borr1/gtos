from pathlib import Path
import re, ast
sleeves = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\sleeves")
af = sleeves / "asian_fade.py"
print("asian_fade exists", af.exists(), af.stat().st_size if af.exists() else 0)
if af.exists():
    src = af.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("ON_SURFACE","TAG","DIRECTION","_DIRECTION"):
                    try: print(t.id, ast.literal_eval(node.value))
                    except Exception as e: print(t.id, "err", e)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in ("ON_SURFACE","TAG") and node.value is not None:
                try: print(node.target.id, ast.literal_eval(node.value))
                except Exception as e: print(node.target.id, e)
reg = (sleeves / "registry.py").read_text(encoding="utf-8")
print("CANDIDATE has asian_fade", "asian_fade" in reg)
# find SleeveSpec line
for i,l in enumerate(reg.splitlines()):
    if "asian_fade" in l:
        print(f"{i+1}: {l[:140]}")
