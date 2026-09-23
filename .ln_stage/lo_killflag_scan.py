"""Session LO: did the kill flag actually register during LN's 2026-08-06T01:06-01:09Z window?

If launcher rows in that window carry killed=true, the flag was SEEN (path correct, poll
reached it) and the only reason the processes survived is that nothing exits on it.
"""
import json
import pathlib

p = pathlib.Path("shadow_logs/ultimate_book_launcher.jsonl")
size = p.stat().st_size
# Tail only -- the file is ~32 MB.
with p.open("rb") as fh:
    fh.seek(max(0, size - 4_000_000))
    chunk = fh.read()

lines = chunk.replace(b"\x00", b"").decode("utf-8", "replace").splitlines()[1:]
rows = []
for line in lines:
    try:
        row = json.loads(line)
    except ValueError:
        continue
    ts = str(row.get("ts") or "")
    if ts.startswith("2026-08-06T01:0") or ts.startswith("2026-08-06T01:1"):
        rows.append(row)

print(f"launcher rows in 2026-08-06T01:0x-01:1x : {len(rows)}")
killed_rows = [r for r in rows if r.get("killed")]
print(f"  rows with killed=true                 : {len(killed_rows)}")
print(f"  rows with place=false                 : {len([r for r in rows if r.get('place') is False])}")
print()
for r in rows:
    print(f"  {r.get('ts')}  ns={r.get('namespace')}  action={r.get('action')} "
          f"killed={r.get('killed')} halted={r.get('halted')} place={r.get('place')}")
