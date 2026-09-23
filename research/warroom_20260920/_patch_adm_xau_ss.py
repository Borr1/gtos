from pathlib import Path
import ast

p = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\admission.py")
t = p.read_text(encoding="utf-8")
if "should_stand_three_fresh_xau_conflict" in t:
    print("ADM_ALREADY")
else:
    idx = t.find("A_STAND_DOWN")
    if idx < 0:
        idx = t.find("evaluate_policy_c_admit")
    if idx < 0:
        raise SystemExit("NO_INSERT")
    ra = t.find("retained.append(it)", idx)
    if ra < 0:
        # search any retained.append after policy import region
        ra = t.find("retained.append(it)")
    if ra < 0:
        raise SystemExit("NO_APPEND")
    line_start = t.rfind("\n", 0, ra) + 1
    indent = ""
    while line_start + len(indent) < len(t) and t[line_start + len(indent)] in " \t":
        indent += t[line_start + len(indent)]
    hook = f'''{indent}# SCOPED JEV_SLEEVE_SELECT XAU conflict: stand three_fresh when spring also alive
{indent}try:
{indent}    from src.judgment.sleeve_select import should_stand_three_fresh_xau_conflict
{indent}    _tag = str(getattr(it, "sleeve", None) or getattr(it, "tag", None) or getattr(it, "name", None) or "")
{indent}    _sym = str(getattr(it, "symbol", None) or getattr(it, "instrument", None) or "")
{indent}    _alive_guess = [_tag]
{indent}    try:
{indent}        _alive_guess += [str(getattr(x, "sleeve", None) or getattr(x, "tag", None) or "") for x in retained]
{indent}    except Exception:
{indent}        pass
{indent}    if "three_fresh" in _tag and should_stand_three_fresh_xau_conflict(_alive_guess, symbol=_sym):
{indent}        continue
{indent}except Exception:
{indent}    pass
'''
    t = t[:line_start] + hook + t[line_start:]
    p.write_text(t, encoding="utf-8")
    print("ADM_PATCHED")
ast.parse(p.read_text(encoding="utf-8"))
print("AST_OK")
# smoke helper
import os
os.environ["GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT"] = "1"
from src.judgment.sleeve_select import should_stand_three_fresh_xau_conflict
print("stand", should_stand_three_fresh_xau_conflict(
    ["dsp_three_fresh_lower_lows", "dsp_spring_close_on_20low_through_the_box"],
    symbol="XAUUSD",
))
print("nostand", should_stand_three_fresh_xau_conflict(
    ["dsp_three_fresh_lower_lows"],
    symbol="XAUUSD",
))
