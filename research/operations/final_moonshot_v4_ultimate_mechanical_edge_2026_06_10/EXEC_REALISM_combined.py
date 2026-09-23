"""EXEC_REALISM — restate the combined book NET of measured M1 fill erosion.

Takes the per-sleeve M1 erosion measured by EXEC_REALISM_reconcile.py + EXEC_REALISM_jpy_probe.py
and applies it to the PORTFOLIO_BUILD_W2 book to produce a live-realistic net-of-fills EV per
sleeve and a conf-weighted combined-book figure. This is the realism gate's bottom line.

Book inputs (from PORTFOLIO_BUILD_W2.md sec 2-3): per-sleeve conf, forward EV, trades/yr, and the
conf-weighted unit-R contribution share. We subtract the measured per-trade erosion (clean M1) from
the forward EV, recompute the conf-weighted contribution, and report the combined erosion.
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent

# ---- book (PORTFOLIO_BUILD_W2.md sec 2) ----
BOOK = {
    # sleeve: (conf, fwd_EV_modeled, trades_per_yr_fwd)
    "metals_core":    (1.00, 1.164, 24),
    "crypto":         (0.85, 0.950, 42),
    "energy_agri":    (0.80, 0.691, 49),
    "metals_softband":(0.50, 0.140, 20),
    "metals_ob_micro":(0.30, -0.171, 1),
    "fx_jpy_ny":      (0.15, 0.154, 98),
    "fx_jpy_london":  (0.15, 0.168, 265),
    "idxrev":         (0.15, 0.025, 1013),
}

# ---- measured M1 fill erosion (CLEAN, this track) ----
# EV-carrying sleeves measured directly; breadth/unmeasured sleeves assigned a conservative proxy.
EROSION = {
    "metals_core":    -0.006,   # measured (EXEC_REALISM_reconcile, EXEC_COMBO, n=47 clean)
    "crypto":         -0.030,   # measured (target4 + cascade, n=58 clean)
    "energy_agri":    +0.004,   # measured (STATE_D + cascade, n=61 clean)
    "fx_jpy_london":  -0.048,   # measured (JPY probe, n=530 clean)
    "fx_jpy_ny":      -0.050,   # measured (JPY probe, n=530 clean; transferable erosion magnitude)
    "idxrev":         -0.013,   # MEASURED (idxrev probe, n=2672 across 6 indices; wide-stop/
                                # tight-target geometry = LOW fill sensitivity, NOT JPY-like)
    # metals_softband/ob_micro not directly measured -> metals-class proxy (same geometry as core).
    "metals_softband":-0.010,   # proxy: metals geometry, slightly looser than core
    "metals_ob_micro":-0.010,   # proxy: metals geometry
}

def main():
    rows = []
    book_mod = 0.0; book_net = 0.0
    for s, (conf, ev, tpy) in BOOK.items():
        ero = EROSION[s]
        net = ev + ero
        # conf-weighted contribution ~ conf * ev * trades_per_yr (unit-R/yr proxy, matches W2 sec3)
        contrib_mod = conf * ev * tpy
        contrib_net = conf * net * tpy
        book_mod += contrib_mod; book_net += contrib_net
        rows.append(dict(sleeve=s, conf=conf, fwd_ev_modeled=ev, erosion=ero,
                         fwd_ev_net=round(net, 4), trades_yr=tpy,
                         contrib_modeled=round(contrib_mod, 2),
                         contrib_net=round(contrib_net, 2),
                         flips_negative=(ev > 0 and net < 0)))
    out = dict(per_sleeve=rows,
               book_conf_wtd_unitR_per_yr_modeled=round(book_mod, 2),
               book_conf_wtd_unitR_per_yr_net=round(book_net, 2),
               book_erosion_pct=round(100 * (book_mod - book_net) / book_mod, 2),
               note=("conf-weighted unit-R/yr = sum(conf*EV*trades_yr). Erosion MEASURED on M1 "
                     "for 6 sleeves (metals_core, crypto, energy_agri, fx_jpy_london, fx_jpy_ny, "
                     "idxrev); metals_softband/ob_micro use a metals-class proxy (same geometry as "
                     "core). Spread NOT double-counted (cost map embeds it); only entry "
                     "open-vs-close, same-bar M1 resolution, and exit-side half-spread stop buffer "
                     "are charged on top of the already-cost-netted book R."))
    print(json.dumps(out, indent=1))
    with open(HERE / "EXEC_REALISM_COMBINED_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    # human summary
    print("\n--- per-sleeve net-of-fills ---")
    for r in rows:
        flag = "  <== FLIPS NEGATIVE" if r["flips_negative"] else ""
        print(f"{r['sleeve']:16} conf{r['conf']:.2f} EV {r['fwd_ev_modeled']:+.3f} "
              f"-> net {r['fwd_ev_net']:+.3f} (ero {r['erosion']:+.3f}){flag}")
    print(f"\nBook conf-wtd unit-R/yr: modeled {book_mod:.1f} -> net {book_net:.1f} "
          f"(erosion {100*(book_mod-book_net)/book_mod:.1f}%)")

if __name__ == "__main__":
    main()
