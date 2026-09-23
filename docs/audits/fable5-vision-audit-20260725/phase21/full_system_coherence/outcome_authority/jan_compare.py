#!/usr/bin/env python3
"""Compare a regenerated January-05 run against the original on decision-bearing fields."""
import sys, json
sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from pathlib import Path

ORIG_ROOT = Path("/private/tmp/w21-expanded-development-jan-6a31.OaqMpQ")
ORIG_AUTH = "caac9f4a052315faf62f0e2d2c3cb575c353c04257f9965d8f465b7001277509"
FIELDS = ["cost_r", "spread_r", "expected_slippage_r", "swap_cost_r", "commission_r",
          "entry_price", "stop_loss", "take_profit_1", "risk_reward_ratio", "broker_pretrade_cost_r"]

def rows(root, day, auth=None):
    r = Path(root) / day / "compact_events"
    if auth is None:
        auth = json.loads((r.parent / "run_summary.json").read_text())["authority_root_sha256"]
    sink = ReplayCompactEventSink.open_sealed(root=r, expected_authority_root_sha256=auth)
    return list(sink.ledger("missed"))

def key(row):
    return (row.get("candidate_id"), row.get("asof_utc"), row.get("symbol"), row.get("side"))

def main():
    repro_root = sys.argv[1]
    day = sys.argv[2] if len(sys.argv) > 2 else "2026-01-05"
    O = {key(x): x for x in rows(ORIG_ROOT, day, ORIG_AUTH)}
    R = {key(x): x for x in rows(repro_root, day)}
    shared = set(O) & set(R)
    print(f"keys: orig {len(O)} repro {len(R)} shared {len(shared)}")
    identical, diff_fields, samples = 0, {}, []
    from collections import Counter
    degraded_sym = Counter()
    for k in shared:
        a, b = O[k], R[k]
        rd = []
        for f in FIELDS:
            va, vb = a.get(f), b.get(f)
            if va is None and vb is None:
                continue
            try:
                if va is None or vb is None or abs(float(va) - float(vb)) > 1e-9:
                    rd.append((f, va, vb))
            except (TypeError, ValueError):
                if va != vb:
                    rd.append((f, va, vb))
        if not rd:
            identical += 1
        else:
            degraded_sym[a.get("symbol")] += 1
            for f, va, vb in rd:
                diff_fields[f] = diff_fields.get(f, 0) + 1
            if len(samples) < 3:
                samples.append((a.get("symbol"), a.get("origin_family"), rd[:4]))
    print(f"decision-field-identical rows: {identical} / {len(shared)}")
    print("differing fields:", dict(sorted(diff_fields.items())))
    print("degraded rows by symbol (top 8):", degraded_sym.most_common(8))
    for s in samples:
        print("sample:", s)

if __name__ == "__main__":
    main()
