from pathlib import Path
import re
reg = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\sleeves\registry.py")
text = reg.read_text(encoding="utf-8")
# find ACTIVE / ALL dicts
for m in re.finditer(r"^(ACTIVE_|ALL_|CANDIDATE_|DSP_|XA_|RESEARCH_|DRAFT_|SLEEVE_)\w*\s*[:=]", text, re.M):
    print("DICT", m.group(0), "at", m.start())
# print around line with ACTIVE
lines = text.splitlines()
for i,l in enumerate(lines):
    if "ACTIVE" in l or l.startswith("ALL_") or "def active" in l.lower() or "RESEARCH" in l:
        if i < 500 or "ACTIVE" in l:
            print(f"{i+1}: {l[:120]}")
print("--- dataclass ---")
for i,l in enumerate(lines[90:105], start=91):
    print(f"{i}: {l}")
print("--- end of file last 40 ---")
for i,l in enumerate(lines[-40:], start=len(lines)-39):
    print(f"{i}: {l}")
print("module landed", Path(r"host-local\redacted_host\repo\src\components\ultimate_book\sleeves\sub_mid_dn_re_proxy_eurusd_short_m15_atr.py").exists())
