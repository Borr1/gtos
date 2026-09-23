"""Session LO: refusal census on the redacted_account error log, with dated context."""
import pathlib
import re

p = pathlib.Path("shadow_logs/run_book_fn_console.log.err")
txt = p.read_bytes().replace(b"\x00", b"").decode("utf-8", "replace")
lines = txt.splitlines()

refusals = [i for i, l in enumerate(lines) if "activation_token_namespace_mismatch" in l]
print(f"file: {p}  ({p.stat().st_size} B)  mtime={p.stat().st_mtime}")
print(f"total namespace-mismatch refusals: {len(refusals)}")

# Nearest preceding timestamped line for the first and last refusal.
stamp = re.compile(r"(20\d\d-\d\d-\d\d[ T]\d\d:\d\d:\d\d)")
for label, idx in (("first", refusals[0]), ("last", refusals[-1])):
    found = None
    for j in range(idx, max(-1, idx - 60), -1):
        m = stamp.search(lines[j])
        if m:
            found = m.group(1)
            break
    print(f"  {label} refusal near line {idx}: nearest timestamp = {found}")

print("\nlast 6 lines of the file:")
for l in lines[-6:]:
    print("   ", l.strip()[:160])
