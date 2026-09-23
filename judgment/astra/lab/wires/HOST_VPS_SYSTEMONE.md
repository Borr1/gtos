# Host / VPS System One shadow

VPS `redacted_host` is wired (fingerprint sha256[:8]=`00000000`):

- User env `TYPESAFE_API_KEY` / `TYPESAFE_KEY`
- `secrets\TYPESAFE_API_KEY.txt`
- repo `.env.typesafe` (gitignored)

This Cloud Agent VM does **not** inherit those. It never POSTs. Not a 403.
Route the real calls through redacted_account box or the VPS.

```bat
cd host-local\redacted_host\repo
python scripts/jev_host_systemone_shadow.py --limit 28
```

Writes `judgment/astra/lab/wires/SYSTEMONE_SHADOW.jsonl` + `.summary.json`.
Ticket **293332188 leave orig**. `live_size_tilt=1.0`. APPLY stays closed.
Budget ≤200. Do not print the key. Do not place / remint / flatten.
