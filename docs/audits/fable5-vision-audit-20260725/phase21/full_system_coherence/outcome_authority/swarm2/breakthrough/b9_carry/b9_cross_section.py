"""B9 step 3 — the carry cross-section, built properly.

Every instrument the two brokers quote, both sides, both accounts, in the estate's own R
unit, using the SAME arithmetic the cost engine uses (`broker_net_cost_engine._swap_cost_packet`
:485-504 and `costs/model.swap_price_drag_per_night` :1037-1048) but WITHOUT the sign clamp.

  mode 1 (points):      drag_price_per_night = swap_points * point
  modes 5/6 (annual %): drag_price_per_night = price * (swap_pct / 100) / days_per_year
  other modes:          currency-denominated -- source gap, reported as such

  R per night = drag_price_per_night / sl_distance
              = drag_price_per_night / (risk_fraction_of_entry * price)

Two risk-fraction bases are reported, because the answer depends on the stop and that is the
honest uncertainty:
  * `cache`  -- median `risk_fraction_of_entry` for that symbol in the 632,934-row candidate
                cache (Lane 5's basis; only defined for symbols the funnel actually proposed)
  * `pooled` -- the cross-symbol median of the above, applied to every instrument, so the
                167-instrument FTMO surface can be ranked at all

Also reports, per instrument:
  * `sum_both_sides` -- the broker's total take. Negative on every instrument means a
    market-neutral carry harvest is arithmetically impossible; this column is the proof.
  * whether the two accounts agree on sign and magnitude.

Writes B9_CARRY_CROSS_SECTION_V1.json.
"""
from __future__ import annotations

import collections
import gzip
import json
import pathlib
import pickle
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
BTC = REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"
CACHE = pathlib.Path("/private/tmp/w21-puzzle-cache")
MONTHS = ("feb", "apr", "may", "jun", "jul")
DAYS_PER_YEAR = 360.0  # broker_net_cost_engine:496 literal default


def cache_risk_fractions() -> tuple[dict, float]:
    per = collections.defaultdict(list)
    for m in MONTHS:
        for r in pickle.load(gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb")):
            v = r.get("risk_fraction_of_entry")
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if v == v and v > 0:
                per[r["symbol"]].append(v)
    med = {k: statistics.median(v) for k, v in per.items()}
    return med, statistics.median(list(med.values()))


def drag_per_night(swap: float, mode, point, price):
    """Signed price drag per night. NEGATIVE means the broker PAYS you."""
    if swap is None or mode is None:
        return None, "missing_swap_or_mode"
    mode = int(float(mode))
    if mode == 1:
        if not point:
            return None, "missing_point"
        return -float(swap) * float(point), "points"
    if mode in (5, 6):
        if not price:
            return None, "missing_price"
        return -float(price) * (float(swap) / 100.0) / DAYS_PER_YEAR, "annual_pct"
    return None, f"currency_denominated_mode_{mode}"


def native_to_canonical() -> dict:
    """`USOIL.cash` -> `USOIL_cash`. The broker-truth artifact is keyed on BROKER-NATIVE names and
    the candidate cache on GTOS-CANONICAL ones, so a naive lookup silently falls back to the pooled
    stop for exactly the instruments this lane cares about -- and the pooled stop is ~9x tighter
    than crude's own, which inflates crude's R/night by ~9x. Caught by cross-reading this table
    against `b9_carry_signal.py`'s, which uses the estate's own stops."""
    d = json.loads(
        (REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/"
                "VERIFIED_BROKER_SYMBOL_SPECS.json").read_text()
    )
    out = {}
    for canon, rec in (d.get("symbols") or {}).items():
        for key in ("ftmo_native", "redacted_account_native"):
            n = rec.get(key)
            if n:
                out[str(n)] = canon
    return out


def main() -> int:
    d = json.loads(BTC.read_text())
    rf_by_symbol, rf_pooled = cache_risk_fractions()
    n2c = native_to_canonical()
    def canon_of(sym: str) -> str:
        if sym in rf_by_symbol:
            return sym
        c = n2c.get(sym)
        if c and c in rf_by_symbol:
            return c
        alt = sym.replace(".", "_")
        return alt if alt in rf_by_symbol else sym

    rows = []
    for acct in ("FTMO", "redacted_account"):
        for sym, rec in d["accounts"][acct]["instruments"].items():
            spec = rec.get("spec") or {}
            sp = rec.get("spread_price") or {}
            price = sp.get("mid_price_median")
            mode, point = spec.get("swap_mode"), spec.get("point")
            canon = canon_of(sym)
            rf_basis = "cache" if canon in rf_by_symbol else "pooled"
            rf = rf_by_symbol.get(canon, rf_pooled)
            for side, field in (("LONG", "swap_long"), ("SHORT", "swap_short")):
                swap = spec.get(field)
                drag, status = drag_per_night(swap, mode, point, price)
                r_night = None
                frac_night = None
                if drag is not None and price:
                    frac_night = drag / float(price)
                    r_night = frac_night / rf
                rows.append(
                    {
                        "account": acct,
                        "symbol": sym,
                        "canonical_symbol": canon,
                        "side": side,
                        "swap_raw": swap,
                        "swap_mode": mode,
                        "point": point,
                        "mid_price_median": price,
                        "favourable": (swap is not None and float(swap) >= 0),
                        # sign convention: R_per_night NEGATIVE = a credit the estate books as 0.0
                        "cost_r_per_night_true": r_night,
                        "cost_r_per_night_clamped": (
                            None if r_night is None else (r_night if r_night > 0 else 0.0)
                        ),
                        "carry_frac_per_night": frac_night,
                        "carry_ann_pct": (None if frac_night is None else -frac_night * 365.0 * 100.0),
                        "risk_fraction_used": rf,
                        "risk_fraction_basis": rf_basis,
                        "conversion_status": status,
                        "traded_in_export_window": rec.get("traded_in_export_window"),
                        "instrument_class": rec.get("instrument_class"),
                    }
                )

    # broker's total take per instrument/account
    take = {}
    for acct in ("FTMO", "redacted_account"):
        for sym, rec in d["accounts"][acct]["instruments"].items():
            spec = rec.get("spec") or {}
            sl, ss = spec.get("swap_long"), spec.get("swap_short")
            if sl is None or ss is None:
                continue
            take[f"{acct}|{sym}"] = {
                "swap_long": sl,
                "swap_short": ss,
                "sum": float(sl) + float(ss),
                "both_sides_negative": float(sl) < 0 and float(ss) < 0,
                "sum_negative": float(sl) + float(ss) < 0,
            }
    n_take = len(take)
    n_sum_neg = sum(1 for v in take.values() if v["sum_negative"])

    fav = [r for r in rows if r["favourable"] and r["cost_r_per_night_true"] is not None]
    fav.sort(key=lambda r: r["cost_r_per_night_true"])

    out = {
        "source_artifact": str(BTC),
        "source_generated_utc": d.get("generated_utc"),
        "swap_provenance": (
            d["accounts"]["FTMO"]["instruments"]["XAUUSD"].get("swap", {}).get("provenance")
        ),
        "days_per_year": DAYS_PER_YEAR,
        "risk_fraction_pooled_median": rf_pooled,
        "risk_fraction_cache_symbols": len(rf_by_symbol),
        "broker_take": {
            "instruments_with_both_sides": n_take,
            "sum_of_both_sides_negative": n_sum_neg,
            "sum_of_both_sides_nonnegative": n_take - n_sum_neg,
            "exceptions": {k: v for k, v in take.items() if not v["sum_negative"]},
            "claim": (
                "swap_long + swap_short < 0 means the broker takes the entire carry plus a "
                "markup; a market-neutral carry harvest is arithmetically impossible"
            ),
        },
        "favourable_sides_ranked": fav,
        "n_favourable_sides": len(fav),
        "n_sides_total": len(rows),
        "all_rows": rows,
    }
    (HERE / "B9_CARRY_CROSS_SECTION_V1.json").write_text(json.dumps(out, indent=1, sort_keys=True))

    print(f"generated_utc {out['source_generated_utc']}  swap provenance: {out['swap_provenance']}")
    print(f"broker take: {n_sum_neg}/{n_take} instrument-accounts have swap_long+swap_short < 0")
    for k, v in out["broker_take"]["exceptions"].items():
        print("   EXCEPTION:", k, v)
    print(f"\nfavourable (swap >= 0) sides: {len(fav)} of {len(rows)}")
    print(f"{'acct':<11}{'symbol':<14}{'side':<6}{'swap':>10}{'mode':>5}{'ann%':>9}{'R/night':>11}  rf-basis")
    for r in fav[:30]:
        if r["cost_r_per_night_true"] is None:
            continue
        print(
            f"{r['account']:<11}{r['symbol']:<14}{r['side']:<6}{r['swap_raw']:>10.3f}"
            f"{str(r['swap_mode']):>5}{r['carry_ann_pct']:>9.2f}{-r['cost_r_per_night_true']:>+11.5f}"
            f"  {r['risk_fraction_basis']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
