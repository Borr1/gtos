from pathlib import Path

p = Path(r"host-local\redacted_host\repo\src\components\ultimate_book\minimal_size.py")
t = p.read_text(encoding="utf-8")
old = """    occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
    if sym in occupied:
        return \"same_symbol_stack_keep_working_ticket\"
"""
new = """    occupied = {f5_norm_symbol(s) for s in occupied_symbols if f5_norm_symbol(s)}
    if sym in occupied:
        d = f5_norm_direction(direction)
        for row in occupied_book or ():
            if not isinstance(row, Mapping):
                continue
            if f5_norm_symbol(row.get(\"symbol\")) != sym:
                continue
            o_dir = f5_norm_direction(row.get(\"direction\") or row.get(\"side\"))
            if d and o_dir and d != o_dir:
                return \"same_symbol_opposite_lock\"
        return \"same_symbol_stack_keep_working_ticket\"
"""
if old not in t:
    raise SystemExit("block missing")
bak = p.with_name(p.name + ".pre_opp_lock_20260827")
if not bak.exists():
    bak.write_text(t, encoding="utf-8")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("named opposite lock")
