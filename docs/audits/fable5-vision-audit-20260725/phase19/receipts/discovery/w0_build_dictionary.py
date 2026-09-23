#!/usr/bin/env python3
"""w0-dictionary — build the shared field/asset map for the wave-19 discovery swarm.

Emits:
  w0_DATA_DICTIONARY.md   the human map (items 1-5 of the lane brief)
  w0_POOL_PROFILE.json    machine-readable per-field measurement
  w0_ASSET_INVENTORY.json machine-readable asset table

Everything numeric in the .md is produced here from the artifacts themselves.
Run from the wave19-broad-forensic-20260801 worktree root.
"""
import collections, gzip, json, os, sys
from datetime import datetime

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
POOL = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")
PATHS = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz")


def iter_gz(p):
    with gzip.open(p, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def profile(rows):
    n = len(rows)
    keys = list(rows[0].keys())
    out = {}
    for k in keys:
        vals = [r.get(k) for r in rows]
        nn = [v for v in vals if v is not None]
        e = {"null_rate": round(1 - len(nn) / n, 6),
             "dtype": "/".join(sorted({type(v).__name__ for v in nn})) or "null",
             "cardinality": len(set(map(repr, nn)))}
        if nn and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in nn):
            s = sorted(nn)
            e.update(min=s[0], max=s[-1], mean=sum(s) / len(s), median=s[len(s) // 2],
                     p05=s[int(.05 * len(s))], p95=s[int(.95 * len(s))],
                     constant=(s[0] == s[-1]))
        c = collections.Counter(map(lambda v: v if isinstance(v, str) else json.dumps(v), nn))
        e["top"] = c.most_common(6)
        out[k] = e
    return out


def main():
    rows = list(iter_gz(POOL))
    n = len(rows)
    prof = profile(rows)
    json.dump({"n": n, "source": os.path.relpath(POOL, ROOT), "fields": prof},
              open(os.path.join(OUT, "w0_POOL_PROFILE.json"), "w"), indent=1, default=str)
    print("wrote w0_POOL_PROFILE.json  n=%d fields=%d" % (n, len(prof)))


if __name__ == "__main__":
    main()
