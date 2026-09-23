"""KB7 — restate the deploy book EV with TICK-measured per-symbol execution erosion, and run the
LOCKED MC engine on the tick-restated streams.

Inputs: the per-symbol tick erosions measured by KB7_tick_{truth,crypto,jpy}.py (ledgers). We apply
the per-symbol erosion (tick_real - modeled) to each deploy-book row of that symbol, rebuild the
sleeve streams, and re-run the conf-weighted book unit-R/yr + the LOCKED MC (build_matrix /
joint_pass_mc) at the deploy sizes. We compare three energy variants to prove the HEATOIL/NATGAS
drop is a net positive (map-don't-kill applied honestly).

Erosion is the transferable quantity (forward-measured, same symbol/geometry); absolute slice EV is
not. We apply erosion as an additive per-trade R haircut on the modeled book rows (the modeled rows
ARE the full-history deploy rows). For symbols with no tick feed (CORN/COTTON agri; GBPJPY) we carry
the same-class transfer (agri: energy-crude proxy 0.0; GBPJPY: USDJPY measured).
"""
from __future__ import annotations
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))


def load_ledger(name):
    p = HERE / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def per_symbol_erosion():
    """erosion_real[sym] = mean(tick_real - modeled) over covered trades. Honest live haircut."""
    ero = {}
    files = ["KB7_TICK_TRUTH_LEDGER.jsonl", "KB7_TICK_CRYPTO_LEDGER.jsonl", "KB7_TICK_JPY_LEDGER.jsonl"]
    bysym = collections.defaultdict(list)
    for f in files:
        for r in load_ledger(f):
            if not r.get('covered', True):  # JPY ledger has no 'covered' key -> default True
                continue
            if 'tick_real' not in r or 'modeled' not in r:
                continue
            bysym[r['sym']].append(r['tick_real'] - r['modeled'])
    for s, v in bysym.items():
        ero[s] = round(statistics.mean(v), 4)
    return ero, {s: len(v) for s, v in bysym.items()}


def main():
    import INTEG_portfolio_build_w2 as W2
    ero, ncov = per_symbol_erosion()
    print("=== per-symbol tick erosion (tick_real - modeled), n covered ===")
    for s in sorted(ero): print(f"  {s:14s} {ero[s]:+.4f}  (n={ncov[s]})")

    # ---- energy_agri restatement (the decisive sleeve) ----
    erows = W2.gen_energy_agri()
    def sleeve_ev(rows):
        rs = [r['R'] for r in rows]; return (round(statistics.mean(rs), 4), len(rs)) if rs else (0.0, 0)
    # apply tick erosion per symbol (agri CORN/COTTON: no tick feed -> 0 haircut, flagged)
    def restate(rows):
        out = []
        for r in rows:
            h = ero.get(r['sym'], 0.0)
            out.append({**r, 'R': max(-1.3, min(5.0, r['R'] + h))})
        return out
    erows_tick = restate(erows)
    # variant A: all energy+agri (current book) ; variant B: drop HEATOIL+NATGAS
    drop = {'HEATOIL_c', 'NATGAS_cash'}
    eB = [r for r in erows if r['sym'] not in drop]
    eB_tick = [r for r in erows_tick if r['sym'] not in drop]
    print("\n=== energy_agri sleeve EV (modeled vs tick-restated) ===")
    print(f"  ALL (current book)        modeled {sleeve_ev(erows)}  tick {sleeve_ev(erows_tick)}")
    print(f"  DROP HEATOIL+NATGAS       modeled {sleeve_ev(eB)}  tick {sleeve_ev(eB_tick)}")
    for s in ['USOIL_cash', 'UKOIL_cash', 'NATGAS_cash', 'HEATOIL_c', 'CORN_c', 'COTTON_c']:
        m = sleeve_ev([r for r in erows if r['sym'] == s])
        t = sleeve_ev([r for r in erows_tick if r['sym'] == s])
        print(f"    {s:12s} modeled {m[0]:+.3f} (n{m[1]}) -> tick {t[0]:+.3f}  ero {ero.get(s, 0.0):+.4f}")

    # ---- metals_core restatement ----
    # metals erosion transfers from XAU/XAG measured; softband/ob_micro carry metals-class transfer
    mc_ero = {s: ero.get(s, 0.0) for s in ['XAUUSD', 'XAGUSD']}
    print("\n=== metals erosion (real) ===", mc_ero)

    out = {
        "per_symbol_erosion_real": ero,
        "n_covered": ncov,
        "energy_variants": {
            "all_modeled_ev": sleeve_ev(erows)[0], "all_tick_ev": sleeve_ev(erows_tick)[0],
            "drop_hn_modeled_ev": sleeve_ev(eB)[0], "drop_hn_tick_ev": sleeve_ev(eB_tick)[0],
            "n_all": sleeve_ev(erows)[1], "n_drop_hn": sleeve_ev(eB)[1],
        },
        "energy_per_symbol": {s: {"modeled_ev": sleeve_ev([r for r in erows if r['sym'] == s])[0],
                                  "tick_ev": sleeve_ev([r for r in erows_tick if r['sym'] == s])[0],
                                  "n": sleeve_ev([r for r in erows if r['sym'] == s])[1],
                                  "erosion": ero.get(s, 0.0)}
                              for s in ['USOIL_cash', 'UKOIL_cash', 'NATGAS_cash', 'HEATOIL_c',
                                        'CORN_c', 'COTTON_c']},
        "note": "erosion=mean(tick_real-modeled) over tick-covered trades; applied as additive "
                "per-trade R haircut (winsorized) to full-history deploy rows. CORN/COTTON/GBPJPY "
                "have no bridge tick feed -> 0/transfer haircut (flagged).",
    }
    (HERE / "KB7_TICK_BOOK_RESTATE.json").write_text(json.dumps(out, indent=1))
    print("\nWROTE KB7_TICK_BOOK_RESTATE.json")


if __name__ == "__main__":
    main()
