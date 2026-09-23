from pathlib import Path
import re
# Add helper in sleeve_select.py
p = Path(r"host-local\redacted_host\repo\src\judgment\sleeve_select.py")
t = p.read_text(encoding="utf-8")
if "xau_conflict_stand_three_fresh" not in t:
    t += '''

def xau_conflict_stand_three_fresh_enabled(*, environ=None) -> bool:
    """SCOPED APPLY: stand three_fresh when spring also alive on XAU. Global APPLY stays 0."""
    return _env_on("GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT", environ, default=False)


def should_stand_three_fresh_xau_conflict(alive_sleeves: Sequence[str] | None, *, symbol: str, environ=None) -> bool:
    if not xau_conflict_stand_three_fresh_enabled(environ=environ):
        return False
    if str(symbol).upper() not in {"XAUUSD", "XAU", "GOLD"}:
        return False
    alive = {str(s) for s in (alive_sleeves or ())}
    has_tf = any("three_fresh" in s for s in alive)
    has_spring = any("spring" in s for s in alive)
    return bool(has_tf and has_spring)
'''
    p.write_text(t, encoding="utf-8")
    print("SLEEVE_SELECT_HELPER_OK")
else:
    print("HELPER_PRESENT")
