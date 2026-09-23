"""KB5_report.py — parse KB5_CROSS_LAYER_RESULT.json into the ranked cross-layer
confluence frontier. Applies the discipline filters (n-gate both/forward, per-year
stability, permutation-null, positive incremental lift) and prints the honest top
setups + the anti-confluent conditions (negative lift) for completeness."""
import sys, json, math
from pathlib import Path
HERE = Path(__file__).resolve().parent

MIN_FWD_N = 30          # forward n-gate for a reportable confluent cell
MIN_BOTH_N = 25         # both-sides floor where train sample exists

def fwd_years_pos(per_year):
    fy = {y: s for y, s in per_year.items() if int(y) >= 2025 and s and s.get("n", 0) >= 5}
    pos = sum(1 for s in fy.values() if s["meanR"] is not None and s["meanR"] > 0)
    return pos, len(fy)

def main():
    res = json.load(open(HERE / "KB5_CROSS_LAYER_RESULT.json"))
    winners = []     # disciplined positive-lift confluent cells
    anti = []        # anti-confluent (negative lift) — reported for SIGN honesty
    for bname, b in res.items():
        btr = b["base_train"]; bfw = b["base_fwd"]
        base_line = (f"BASE {bname}: train n{btr['n']} R{btr['meanR']} | "
                     f"fwd n{bfw['n']} R{bfw['meanR']} win{bfw['win']} odds{bfw['odds']}")
        print("=" * 100)
        print(base_line)
        print(f"  cell: {b['cell']}")
        # base per-year fwd
        bpy = {y: s for y, s in b["base_per_year"].items() if int(y) >= 2025 and s}
        print("  base fwd per-year: " + ", ".join(
            f"{y}:n{s['n']}R{s['meanR']}" for y, s in sorted(bpy.items())))
        conds = b["conditions"]
        # rank conditions by fwd lift
        rows = []
        for ck, c in conds.items():
            ctr = c["cond_train"]; cfw = c["cond_fwd"]
            rows.append((c.get("fwd_lift_vs_base"), ck, c, ctr, cfw))
        rows.sort(key=lambda r: (r[0] if r[0] is not None else -9))
        for lift, ck, c, ctr, cfw in reversed(rows):
            if cfw["n"] is None:
                continue
            pos, tot = fwd_years_pos(c["cond_per_year"])
            pn = c["perm_null_p_fwd"]
            tag = ""
            disciplined = (cfw["n"] >= MIN_FWD_N and lift is not None and lift > 0
                           and cfw["meanR"] is not None and cfw["meanR"] > 0
                           and tot >= 1 and pos >= math.ceil(tot / 2)
                           and (pn is not None and pn <= 0.10))
            if disciplined:
                tag = " <== CONFLUENT(+)"
                winners.append(dict(base=bname, cond=ck, base_fwd_R=bfw["meanR"],
                                    cond_fwd_R=cfw["meanR"], lift=lift, n_fwd=cfw["n"],
                                    n_tr=ctr["n"], tr_R=ctr["meanR"], win=cfw["win"],
                                    odds=cfw["odds"], perm_p=pn, fwd_pos_yrs=f"{pos}/{tot}",
                                    tr_lift=c["tr_lift_vs_base"], phi=c["phi_cond_vs_win"]))
            if lift is not None and lift < -0.10 and cfw["n"] >= MIN_FWD_N:
                anti.append(dict(base=bname, cond=ck, lift=lift, n_fwd=cfw["n"],
                                 cond_fwd_R=cfw["meanR"]))
            lift_s = f"{lift:+.3f}" if lift is not None else " na"
            trl = c["tr_lift_vs_base"]
            trl_s = f"{trl:+.2f}" if trl is not None else "na"
            print(f"    {ck:26} | trn n{str(ctr['n']):>4} R{str(ctr['meanR']):>7} | "
                  f"fwd n{str(cfw['n']):>4} R{str(cfw['meanR']):>7} win{str(cfw['win']):>5} "
                  f"odds{str(cfw['odds']):>6} | lift{lift_s:>7} trlift{trl_s:>6} "
                  f"pY{pos}/{tot} permp{pn}{tag}")

    print("\n" + "#" * 100)
    print(f"DISCIPLINED CONFLUENT (+) CELLS: {len(winners)}  (fwd n>={MIN_FWD_N}, lift>0, "
          f"fwd R>0, majority fwd yrs +, perm-p<=0.10)")
    print("#" * 100)
    winners.sort(key=lambda w: -w["cond_fwd_R"])
    for w in winners:
        print(f"  [{w['base']}] +{w['cond']:24} fwd R{w['cond_fwd_R']:+.3f} "
              f"(base {w['base_fwd_R']:+.3f}, lift {w['lift']:+.3f}) n{w['n_fwd']} "
              f"win{w['win']} odds{w['odds']} | trn n{w['n_tr']} R{w['tr_R']} trlift{w['tr_lift']} "
              f"| fwdYrs {w['fwd_pos_yrs']} perm-p{w['perm_p']} phi{w['phi']}")

    print(f"\nANTI-CONFLUENT (-) conditions (lift<-0.10, n>={MIN_FWD_N}) — DROP these from stacks:")
    anti.sort(key=lambda a: a["lift"])
    for a in anti[:25]:
        print(f"  [{a['base']}] {a['cond']:26} lift {a['lift']:+.3f} (fwd R{a['cond_fwd_R']}) n{a['n_fwd']}")

    json.dump({"winners": winners, "anti": anti},
              open(HERE / "KB5_FRONTIER.json", "w"), indent=1, default=str)
    print(f"\nwrote KB5_FRONTIER.json ({len(winners)} winners, {len(anti)} anti)")

if __name__ == "__main__":
    main()
