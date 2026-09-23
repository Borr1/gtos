"""B7 — does adding ETHUSD change the crypto cluster's RISK, not just its return?

Lane 8 asserts: "It does not add a cluster, so under the one-unit-per-cluster-per-day cap total
daily risk is unchanged — the unit splits across more symbols, it does not stack."

That is a claim about live code, so it is tested against live code:

  * `admission.py:1171-1177` buckets by (decision_day, cluster) and `:1256` sets
    per_trade = unit_risk / n  -> members of ONE sizing call share one unit's risk.
  * BUT the single production call site is `admission.py:1523`, inside `decide()`, which the engine
    calls ONCE PER DECISION CYCLE with that cycle's intents (`book_engine._generate_intents`).
    Two crypto symbols firing on DIFFERENT H4 closes of the same day are therefore two separate
    sizing calls, each n=1, each at FULL cluster unit risk.
  * The only thing that stops a repeat is the per-(symbol, sleeve) duplicate guard
    (`book_owner.py:413-428` `_broker_holds`, plus the active_trade guard), which is per SYMBOL —
    it cannot stop BTCUSD and ETHUSD being open at once.

So the honest question is CONCURRENCY: how many crypto units are open simultaneously, and how
much does adding a third symbol change that. Simulated chronologically with the duplicate guard
applied, which no estate walk applies.
"""
from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics as stat
from pathlib import Path

OUT = Path("/Users/borr/.claude/jobs/adb9e69b/tmp")
ROWS = json.load(gzip.open(OUT / "B7_CRYPTO_ROWS.json.gz"))


def simulate(syms, label):
    """Chronological placement with the live per-(sleeve,symbol) duplicate guard."""
    trades = []
    for s in syms:
        for r in ROWS.get(s, []):
            e = dt.datetime.fromisoformat(r["entry_utc"])
            trades.append({**r, "_entry": e,
                           "_exit": e + dt.timedelta(hours=r["hold_hours"])})
    trades.sort(key=lambda r: (r["_entry"], r["symbol"]))

    open_until: dict[str, dt.datetime] = {}
    placed, skipped = [], 0
    for t in trades:
        u = open_until.get(t["symbol"])
        if u is not None and t["_entry"] < u:
            skipped += 1          # duplicate guard: this symbol already holds a W7:crypto position
            continue
        open_until[t["symbol"]] = t["_exit"]
        placed.append(t)

    # cycle grouping: intents on the SAME H4 close share one cluster unit (risk / n).
    cycles = collections.defaultdict(list)
    for t in placed:
        cycles[t["_entry"]].append(t)
    unit_weight = {}      # per trade: share of one cluster unit's risk
    for stamp, grp in cycles.items():
        for t in grp:
            unit_weight[id(t)] = 1.0 / len(grp)

    # concurrency in UNITS of cluster risk, sampled at every event boundary
    events = sorted({t["_entry"] for t in placed} | {t["_exit"] for t in placed})
    peak = 0.0
    weighted = 0.0
    total_h = 0.0
    hist = collections.Counter()
    for a, b in zip(events, events[1:]):
        conc = sum(unit_weight[id(t)] for t in placed if t["_entry"] <= a < t["_exit"])
        h = (b - a).total_seconds() / 3600.0
        peak = max(peak, conc)
        weighted += conc * h
        total_h += h
        hist[round(conc, 2)] += h
    span_y = (events[-1] - events[0]).days / 365.25
    frac_above_1 = sum(h for c, h in hist.items() if c > 1.0001) / total_h
    return {
        "label": label, "symbols": syms,
        "signals_walked": len(trades), "placed": len(placed),
        "skipped_by_duplicate_guard": skipped,
        "n_cycles": len(cycles),
        "peak_concurrent_cluster_units": round(peak, 3),
        "mean_concurrent_cluster_units": round(weighted / total_h, 4),
        "pct_time_above_1_unit": round(100 * frac_above_1, 2),
        "span_y": round(span_y, 2),
        "mean_r_placed": round(stat.fmean([t["r_gross"] for t in placed]), 5),
        "mean_r_all_walked": round(stat.fmean([t["r_gross"] for t in trades]), 5),
        "total_r_placed": round(sum(t["r_gross"] for t in placed), 2),
        "R_per_month_placed_unit_weighted": round(
            sum(t["r_gross"] * unit_weight[id(t)] for t in placed) / (span_y * 12), 4),
        "R_per_month_placed_unweighted": round(
            sum(t["r_gross"] for t in placed) / (span_y * 12), 4),
    }


if __name__ == "__main__":
    out = {}
    for label, syms in [("BTC only", ["BTCUSD"]),
                        ("LIVE BTC+DASH", ["BTCUSD", "DASHUSD"]),
                        ("+ETH BTC+DASH+ETH", ["BTCUSD", "DASHUSD", "ETHUSD"]),
                        ("swap BTC+ETH", ["BTCUSD", "ETHUSD"]),
                        ("family9", list(ROWS))]:
        r = simulate(syms, label)
        out[label] = r
        print(f"{label:20s} walked={r['signals_walked']:4d} placed={r['placed']:4d} "
              f"skipped={r['skipped_by_duplicate_guard']:3d} "
              f"peak={r['peak_concurrent_cluster_units']:5.2f}u "
              f"mean={r['mean_concurrent_cluster_units']:.3f}u "
              f"time>1u={r['pct_time_above_1_unit']:5.2f}%  "
              f"meanR(placed)={r['mean_r_placed']:+.4f}")
    json.dump(out, open(OUT / "B7_RISK_CONCURRENCY.json", "w"), indent=1)
