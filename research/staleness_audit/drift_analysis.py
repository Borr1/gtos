"""Drift analysis: stale Apr-2026 (Apr 4) JSON vs fresh Apr-25 24x24.

Compares per-pair correlations and produces:
- Drift table (sorted by |drift|)
- Pairs that flip the 0.4 threshold
- Pairs in DEFAULT_CORRELATION_GROUPS that are now uncorrelated
- Pairs missing from groups that should be added
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
STALE = ROOT / "exports" / "multi_instrument" / "screening_results" / "correlation_matrix.json"
FRESH = ROOT / "research" / "staleness_audit" / "fresh_correlation_matrix_2026-04-25.json"
OUT = ROOT / "research" / "staleness_audit"

GROUPS = {
    "EUR_GBP": ["EURUSD", "GBPUSD"],
    "AUD_NZD": ["AUDUSD", "NZDUSD"],
    "US_INDICES": ["US30_cash", "US500"],  # Note: bug — should be US500_cash
    "PRECIOUS_METALS": ["XAUUSD", "XAGUSD"],
    "JPY_CROSSES": ["USDJPY", "EURJPY", "GBPJPY"],
}

THRESHOLD = 0.4


def load_stale() -> dict:
    return json.load(open(STALE, encoding="utf-8"))


def load_fresh() -> dict:
    data = json.load(open(FRESH, encoding="utf-8"))
    return data["matrix"]


def lookup(matrix: dict, a: str, b: str) -> float | None:
    if a in matrix and b in matrix[a]:
        return matrix[a][b]
    if b in matrix and a in matrix[b]:
        return matrix[b][a]
    return None


def main():
    stale = load_stale()
    fresh = load_fresh()

    stale_instruments = sorted(stale.keys())
    fresh_instruments = sorted(fresh.keys())
    print(f"Stale matrix: {len(stale_instruments)} instruments {stale_instruments}")
    print(f"Fresh matrix: {len(fresh_instruments)} instruments")

    stale_pairs = []
    seen = set()
    for a in stale_instruments:
        for b, r in stale[a].items():
            if a == b:
                continue
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            seen.add(key)
            stale_pairs.append((a, b, float(r)))

    drift_rows = []
    for a, b, sr in stale_pairs:
        fr = lookup(fresh, a, b)
        if fr is None:
            drift = None
        else:
            drift = fr - sr
        drift_rows.append({
            "pair": f"{a}<->{b}",
            "stale_r": sr,
            "fresh_r": fr,
            "drift": drift,
        })

    drift_rows.sort(
        key=lambda x: abs(x["drift"]) if x["drift"] is not None else 0,
        reverse=True
    )

    print(f"\n=== Drift Table (top 30 by |drift|) ===")
    print(f"{'Pair':35s} {'Stale':>10s} {'Fresh':>10s} {'Drift':>10s} {'AbsD':>10s}")
    for row in drift_rows[:30]:
        sr = f"{row['stale_r']:+.4f}"
        fr = f"{row['fresh_r']:+.4f}" if row["fresh_r"] is not None else "  N/A  "
        d = f"{row['drift']:+.4f}" if row["drift"] is not None else "  N/A  "
        ad = f"{abs(row['drift']):.4f}" if row["drift"] is not None else "  N/A  "
        print(f"{row['pair']:35s} {sr:>10s} {fr:>10s} {d:>10s} {ad:>10s}")

    flips = []
    for row in drift_rows:
        if row["fresh_r"] is None or row["drift"] is None:
            continue
        sr = abs(row["stale_r"])
        fr = abs(row["fresh_r"])
        s_above = sr >= THRESHOLD
        f_above = fr >= THRESHOLD
        if s_above != f_above:
            flips.append({
                "pair": row["pair"],
                "stale_r": row["stale_r"],
                "fresh_r": row["fresh_r"],
                "from": "ABOVE" if s_above else "below",
                "to": "ABOVE" if f_above else "below",
            })

    print(f"\n=== Threshold Flips (|r| crosses {THRESHOLD}) ===")
    print(f"  Total: {len(flips)} pairs flip threshold under fresh data")
    for f in flips:
        print(f"  {f['pair']:35s} stale_r={f['stale_r']:+.4f} ({f['from']:5s}) -> "
              f"fresh_r={f['fresh_r']:+.4f} ({f['to']})")

    print(f"\n=== DEFAULT_CORRELATION_GROUPS Audit ===")
    for gname, members in GROUPS.items():
        print(f"\n  {gname}: {members}")
        for i, a in enumerate(members):
            for b in members[i+1:]:
                a_lookup = a if a in fresh else (
                    {"US500": "US500_cash"}.get(a, a)
                )
                b_lookup = b if b in fresh else (
                    {"US500": "US500_cash"}.get(b, b)
                )
                fresh_r = lookup(fresh, a_lookup, b_lookup)
                stale_r = lookup(stale, a_lookup, b_lookup)
                fr = f"{fresh_r:+.4f}" if fresh_r is not None else "MISSING"
                sr = f"{stale_r:+.4f}" if stale_r is not None else "MISSING"
                strong = (fresh_r is not None and abs(fresh_r) >= THRESHOLD)
                tag = "OK" if strong else "WEAK!"
                print(f"    {a:12s} <-> {b:12s} fresh={fr:>10s}  stale={sr:>10s}  {tag}")

    # Hardcoded fallback verify
    HARDCODED_FALLBACK = {
        ("XAUUSD", "AUDUSD"): 0.391,
        ("XAUUSD", "GBPUSD"): 0.284,
        ("XAUUSD", "US30_cash"): 0.097,
        ("XAUUSD", "USDJPY"): -0.415,
        ("XAUUSD", "XAGUSD"): 0.772,
        ("XAUUSD", "EURUSD"): 0.369,
        ("AUDUSD", "NZDUSD"): 0.831,
        ("US30_cash", "US500_cash"): 0.937,
        ("EURJPY", "GBPJPY"): 0.740,
        ("USDJPY", "GBPJPY"): 0.593,
        ("EURUSD", "GBPUSD"): 0.635,
        ("EURUSD", "USDCAD"): -0.450,
        ("AUDUSD", "USDCAD"): -0.683,
        ("GBPUSD", "USDCAD"): -0.488,
        ("NZDUSD", "USDCAD"): -0.614,
    }
    print(f"\n=== Hardcoded Gate Fallback vs Stale JSON ===")
    for (a, b), gate_val in HARDCODED_FALLBACK.items():
        sr = lookup(stale, a, b)
        match = (round(sr, 3) == gate_val) if sr is not None else False
        flag = "MATCH" if match else "MISMATCH"
        print(f"  {a:12s} <-> {b:12s} gate={gate_val:+.3f}  stale_json={sr:+.4f}  {flag}")

    with open(OUT / "drift_table.csv", "w", encoding="utf-8") as f:
        f.write("pair,stale_r,fresh_r,abs_drift,signed_drift,stale_above_thresh,fresh_above_thresh,flips\n")
        for row in drift_rows:
            sr = row["stale_r"]
            fr = row["fresh_r"]
            d = row["drift"]
            if fr is None or d is None:
                f.write(f"{row['pair']},{sr},,,,,\n")
                continue
            s_above = abs(sr) >= THRESHOLD
            f_above = abs(fr) >= THRESHOLD
            f.write(f"{row['pair']},{sr:.4f},{fr:.4f},{abs(d):.4f},{d:.4f},{s_above},{f_above},{s_above != f_above}\n")
    print(f"\nWrote drift table to {OUT / 'drift_table.csv'}")


if __name__ == "__main__":
    main()
