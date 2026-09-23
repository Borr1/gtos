#!/usr/bin/env python3
"""x2 step 6 - intra-bar microstructure of the DECISION bar, for all 27,658 pool rows.

Every feature is computed from the 15 M1 bars of the decision M15 bar ONLY (offsets 0..14),
i.e. strictly pre-decision, and NONE of them exists anywhere in the estate today: the pool's
28 pre-decision fields are all computed on the completed M15 bar and are blind to the order
in which it was built.

Writes DISCOVERY/x2_INTRABAR_FEATURES_V1.jsonl.gz
"""
import sys, os, json, gzip, collections, datetime as dt
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x2_bars, w0_ws

TIME, O, H, L, C, V = 0, 1, 2, 3, 4, 5


def main():
    rows = w0_ws.load()
    bysym = collections.defaultdict(list)
    for r in rows:
        bysym[r["symbol"]].append(r)
    out = []
    stats = collections.Counter()
    for sym, rs in sorted(bysym.items()):
        m15 = x2_bars.load_m15(sym)
        m15idx = {b[TIME]: i for i, b in enumerate(m15)}
        m1 = x2_bars.load_m1(sym, ("202601",))
        t1 = {b[TIME]: k for k, b in enumerate(m1)}
        for r in rs:
            bt = dt.datetime.fromisoformat(r["decision_time_utc"]) - dt.timedelta(minutes=15)
            i = m15idx.get(bt)
            if i is None or i < 51:
                stats["no_bar"] += 1; continue
            atr14 = sum(b[H] - b[L] for b in m15[i - 13:i + 1]) / 14.0
            mm = [t1.get(bt + dt.timedelta(minutes=o)) for o in range(15)]
            mm = [m1[k] if k is not None else None for k in mm]
            pres = [(o, b) for o, b in enumerate(mm) if b is not None]
            if len(pres) < 5 or atr14 <= 0:
                stats["thin"] += 1; continue
            offs = [o for o, _ in pres]; bars = [b for _, b in pres]
            o0 = bars[0][O]; cN = bars[-1][C]
            hh = max(b[H] for b in bars); ll = min(b[L] for b in bars)
            rng = hh - ll
            s = 1.0 if r["side"] == "LONG" else -1.0
            closes = [b[C] for b in bars]
            dif = [closes[k] - closes[k - 1] for k in range(1, len(closes))]
            path = sum(abs(d) for d in dif)
            eff = abs(cN - o0) / path if path > 0 else 0.0
            dirchg = sum(1 for k in range(1, len(dif)) if dif[k] * dif[k - 1] < 0)
            mo_h = offs[max(range(len(bars)), key=lambda k: bars[k][H])]
            mo_l = offs[min(range(len(bars)), key=lambda k: bars[k][L])]
            half = [k for k in range(len(bars)) if offs[k] >= 7]
            drift2 = (cN - closes[half[0] - 1]) / atr14 if half and half[0] > 0 else 0.0
            last5 = [b for o, b in pres if o >= 10]
            lr = (max(b[H] for b in last5) - min(b[L] for b in last5)) if last5 else 0.0
            mean_c = sum(closes) / len(closes)
            # excursion of the forming bar measured in the trade's own risk units,
            # anchored on the entry the decision will use
            rd = r["risk_distance"] or 1e-12
            fav_in_bar = max(s * (b[H] if s > 0 else b[L]) - s * r["entry_price"] for b in bars) / rd
            adv_in_bar = min(s * (b[L] if s > 0 else b[H]) - s * r["entry_price"] for b in bars) / rd
            rec = {
                "key": list(w0_ws.key(r)), "symbol": sym, "family": r["origin_family"], "side": r["side"],
                "bar_time": bt.isoformat(), "m1_present": len(bars), "atr14_m15": atr14,
                "ib_range_atr": rng / atr14,
                "ib_body_atr": abs(cN - o0) / atr14,
                "ib_clv": (cN - ll) / rng if rng > 0 else 0.5,
                "ib_signed_clv": ((cN - ll) / rng if rng > 0 else 0.5) if s > 0 else (1 - ((cN - ll) / rng if rng > 0 else 0.5)),
                "ib_efficiency": eff,
                "ib_path_atr": path / atr14,
                "ib_dir_changes": dirchg,
                "ib_minute_of_high": mo_h, "ib_minute_of_low": mo_l,
                "ib_extreme_late": max(mo_h, mo_l),
                "ib_signed_extreme_minute": (mo_h if s > 0 else mo_l),
                "ib_signed_adverse_minute": (mo_l if s > 0 else mo_h),
                "ib_second_half_drift_atr": s * drift2,
                "ib_late_range_share": lr / rng if rng > 0 else 0.0,
                "ib_close_vs_mean_atr": s * (cN - mean_c) / atr14,
                "ib_fav_excursion_r": fav_in_bar, "ib_adv_excursion_r": adv_in_bar,
                "ib_signed_bar_move_r": s * (cN - o0) / rd,
                "gross_r": r["gross_r"], "plain_walk_r": r["plain_walk_r"],
                "fill_honest_walk_r": r["fill_honest_walk_r"],
                "which_came_first": r["which_came_first"], "mfe_r": r["mfe_r"], "mae_r": r["mae_r"],
                "is_first_emission": r["is_first_emission"],
            }
            out.append(rec); stats["rows"] += 1
        print("done", sym, stats["rows"], flush=True)
    with gzip.open(os.path.join(D, "x2_INTRABAR_FEATURES_V1.jsonl.gz"), "wt") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print(json.dumps(dict(stats), indent=1))


if __name__ == "__main__":
    main()
