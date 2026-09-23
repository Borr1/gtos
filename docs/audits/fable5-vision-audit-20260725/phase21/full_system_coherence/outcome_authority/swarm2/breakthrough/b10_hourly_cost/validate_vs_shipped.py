"""B10 -- what the shipped model charges vs what the tape says, per symbol x UTC hour.

Two comparisons, and they answer different questions:

  A. shipped CLASS term (what the code actually applies, `spread_model.py:396`)
     vs the tape.  This is the defect Lane 7 measured.

  B. shipped BY-SYMBOL term (present in `SPREAD_MODEL_V1.json`, read by NO code)
     vs the tape.  If these agree, the repair is a lookup-precedence change and not a
     re-measurement -- which is a very different (and much cheaper) prescription.
"""
from __future__ import annotations

import json
import statistics
import sys

SHIPPED = "research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"
# canonical -> the broker key the shipped artifact uses in by_symbol_hour_of_week
CANON_TO_BROKER = {
    "NAS100": "US100.cash", "SPX500": "US500.cash", "GER40": "GER40.cash",
    "JP225": "JP225.cash", "UK100": "UK100.cash", "US30_cash": "US30.cash",
    "USOIL_cash": "USOIL.cash", "UKOIL_cash": "UKOIL.cash",
}
CANON_TO_FILE = {
    "NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
    "JP225": "JP225_cash", "UK100": "UK100_cash", "US30_cash": "US30_cash",
    "USOIL_cash": "USOIL_cash", "UKOIL_cash": "UKOIL_cash",
}
SURFACE_24 = ("AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
              "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
              "SPX500", "UK100", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF",
              "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD")
BROKER_MINUS_UTC = 3   # broker wall = UTC + 3 for this window


def hour_profile(table: dict) -> dict[int, float]:
    """hour-of-week table (broker wall) -> median multiplier per UTC hour."""
    by = {}
    for k, v in table.items():
        bh = int(k) % 24
        uh = (bh - BROKER_MINUS_UTC) % 24
        by.setdefault(uh, []).append(float(v))
    return {h: statistics.median(v) for h, v in sorted(by.items())}


def main(tape_path: str, out_path: str) -> None:
    ship = json.load(open(SHIPPED))
    tape = json.load(open(tape_path))
    iw = ship["intraweek"]["FTMO"]
    by_sym = iw["by_symbol_hour_of_week"]
    by_cls = iw["by_class_hour_of_week"]
    cls_of = tape["instrument_class"]
    acc = tape["accounts"]["FTMO"]

    rows = []
    for canon in SURFACE_24:
        f = CANON_TO_FILE.get(canon, canon)
        blk = acc.get(f)
        if blk is None:
            continue
        klass = cls_of.get(canon)
        bkey = CANON_TO_BROKER.get(canon, canon)
        sym_prof = hour_profile(by_sym[bkey]) if bkey in by_sym else None
        cls_prof = hour_profile(by_cls[klass]) if klass in by_cls else None
        tape_prof = {int(h): c["median_mult"] for h, c in blk["by_hour_utc"].items()
                     if c["median_mult"]}
        hours = sorted(tape_prof)
        # error ratios: shipped / tape.  <1 means the model UNDERCHARGES.
        cls_err = [cls_prof[h] / tape_prof[h] for h in hours
                   if cls_prof and h in cls_prof]
        sym_err = [sym_prof[h] / tape_prof[h] for h in hours
                   if sym_prof and h in sym_prof]
        rows.append({
            "symbol": canon, "class": klass, "broker_key": bkey,
            "in_by_symbol_table": bkey in by_sym,
            "hours_measured": len(hours),
            "tape_hour_range": [min(tape_prof.values()), max(tape_prof.values())],
            "tape_hour_ratio": max(tape_prof.values()) / min(tape_prof.values()),
            "class_hour_ratio": (max(cls_prof.values()) / min(cls_prof.values())
                                 if cls_prof else None),
            "class_err_min": min(cls_err) if cls_err else None,
            "class_err_max": max(cls_err) if cls_err else None,
            "class_err_median": statistics.median(cls_err) if cls_err else None,
            "sym_err_min": min(sym_err) if sym_err else None,
            "sym_err_max": max(sym_err) if sym_err else None,
            "sym_err_median": statistics.median(sym_err) if sym_err else None,
            "worst_hour_utc": max(tape_prof, key=tape_prof.get),
            "worst_hour_tape_mult": max(tape_prof.values()),
            "worst_hour_class_mult": (cls_prof.get(max(tape_prof, key=tape_prof.get))
                                      if cls_prof else None),
            "worst_hour_sym_mult": (sym_prof.get(max(tape_prof, key=tape_prof.get))
                                    if sym_prof else None),
        })

    with_sym = [r for r in rows if r["sym_err_median"] is not None]
    doc = {
        "schema": "b10_shipped_vs_tape_v1",
        "code_path_that_decides": "src/costs/spread_model.py:396 -- reads ONLY "
                                  "by_class_hour_of_week; by_symbol_hour_of_week is present "
                                  "in the artifact and read by no code in the tree",
        "rows": rows,
        "summary": {
            "n_surface_symbols": len(rows),
            "class_undercharge_worst": min((r["class_err_min"] for r in rows
                                            if r["class_err_min"]), default=None),
            "symbols_class_undercharges_by_2x_or_more": sorted(
                r["symbol"] for r in rows
                if r["class_err_min"] and r["class_err_min"] < 0.5),
            "by_symbol_table_median_abs_log_error": (
                statistics.median([abs(r["sym_err_median"] - 1.0) for r in with_sym])
                if with_sym else None),
            "by_symbol_table_worst_hour_agreement": [
                {"symbol": r["symbol"], "tape": round(r["worst_hour_tape_mult"], 3),
                 "by_symbol": (round(r["worst_hour_sym_mult"], 3)
                               if r["worst_hour_sym_mult"] else None),
                 "by_class": (round(r["worst_hour_class_mult"], 3)
                              if r["worst_hour_class_mult"] else None)}
                for r in rows],
        },
    }
    json.dump(doc, open(out_path, "w"), indent=1)

    print(f"{'symbol':12s} {'cls':8s} {'tape_ratio':>10s} {'cls_ratio':>9s} "
          f"{'cls_err_min':>11s} {'sym_err_med':>11s} {'worstUTC':>8s} "
          f"{'tape':>7s} {'class':>7s} {'bysym':>7s}")
    for r in rows:
        print(f"{r['symbol']:12s} {str(r['class']):8s} {r['tape_hour_ratio']:10.2f} "
              f"{(r['class_hour_ratio'] or 0):9.2f} "
              f"{(r['class_err_min'] or 0):11.3f} "
              f"{(r['sym_err_median'] if r['sym_err_median'] is not None else float('nan')):11.3f} "
              f"{r['worst_hour_utc']:8d} {r['worst_hour_tape_mult']:7.2f} "
              f"{(r['worst_hour_class_mult'] or 0):7.2f} "
              f"{(r['worst_hour_sym_mult'] if r['worst_hour_sym_mult'] else float('nan')):7.2f}")
    print("\nsummary:", json.dumps(doc["summary"]["symbols_class_undercharges_by_2x_or_more"]))
    print("by_symbol median |err-1|:", doc["summary"]["by_symbol_table_median_abs_log_error"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
