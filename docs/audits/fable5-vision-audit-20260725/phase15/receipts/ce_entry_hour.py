"""CE-2: does the ratified hour-01 entry convention reach the ARMED book, and what is it worth?

    python3 docs/audits/fable5-vision-audit-20260725/phase15/receipts/ce_entry_hour.py

THE QUESTION THE COMMISSION ASKED, AND WHY IT IS NOT THE ONE THE DECISION ANSWERED
----------------------------------------------------------------------------------
`phase9/OWNER_DECISION_ENTRY_HOUR.md` (ratified 2026-07-30) says the FX D1 cohort enters at
broker hour 01, and its own scope note says *"the armed three sleeves are not in this cohort,
so nothing armed changes."* That sentence was true when it was written and is **false since
2026-07-31 ~01:26 UTC**: `mx_btcusd_d1_donchian_20_breakout` was armed on FTMO that morning,
it is a D1 sleeve, and this driver measures whether it fills at the rollover hour.

It is deliberately NOT assumed from the cohort label. AH measured the FX D1 cohort; BTCUSD is
not FX, quotes 24/7, and AY's census puts its `spread_r` exceedance at 0.0 % — so it is
entirely possible the lever is worthless here. That is a measurement, not a guess.

THE INSTRUMENT, AND WHAT IT DOES AND DOES NOT CAPTURE
-----------------------------------------------------
An hour-01 fill needs a bar closing at broker 01:00. On the matched FTMO feed the D1 grid
closes at 00:00 and H4 at 00/04/08/12/16/20 — neither contains it at any date. Only M15 does,
and the BTCUSD M15 archive starts 2024-01-01 (AQ's `the_data_constraint`, unchanged here).

So this measures, on the trades the M15 archive covers:

  1. **entry displacement** — `direction * (p01 - p00) / stop_dist`. First-order this IS the
     gross R change: the whole trajectory shifts by that amount in R units.
  2. **whether the shift is exact for that trade** — if the 00:00-01:00 window contains no stop
     or target touch, nothing happened in the hour we skipped and (1) is exact rather than
     first-order. Counted, not assumed.
  3. **the spread bill at hour 00 vs hour 01**, from the M15 archive's own `spread` column.
     AH established that column is the WITHIN-BAR MINIMUM, so at hour 00 it UNDERSTATES the
     rollover spike — which makes any cost saving computed from it a **lower bound**. Stated
     rather than corrected: this driver must not invent an hour profile the data does not have.

It does NOT capture the path/hold/carry consequences of the shifted entry the way AH's
end-to-end re-simulation did. It is a first-order instrument on one sleeve, reported as one.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

ESTATE = ROOT / ("docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                 "AQ_ESTATE_TRADES_V2.json.gz")
BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
OUT = ROOT / "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CE_ENTRY_HOUR_V1.json"

SERVER = "FTMO-Server3"
RULE = resolve_rule(SERVER)
ARMED_FTMO = ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
              "mx_btcusd_d1_donchian_20_breakout"]
ARMED_FN = ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_m15(symbol: str) -> dict[dt.datetime, dict]:
    """broker-naive bar OPEN time -> row. The M15 file's `time` is a raw MT5 epoch whose
    UTC decoding IS the broker wall clock (the `.timebase.json` sidecar says so).

    The archive spells the cash indices and oils with an UNDERSCORE (`UKOIL_cash`) and the
    trade rows with a DOT (`UKOIL.cash`). The first version of this driver did not map them
    and silently counted 39 of `sub_mid_dn_revert`'s hour-00 trades as "no feed" -- an absence
    produced by a filename convention, reported as a data gap. A symbol that is genuinely
    renamed rather than re-punctuated (US500 -> SPX500?) is NOT guessed at; it stays
    unmapped and is counted honestly.
    """
    p = BARS / f"FTMO_{symbol}_M15.csv.gz"
    if not p.is_file() and "." in symbol:
        p = BARS / f"FTMO_{symbol.replace('.', '_')}_M15.csv.gz"
    if not p.is_file():
        raise FileNotFoundError(str(p))
    out: dict[dt.datetime, dict] = {}
    with gzip.open(p, "rt") as fh:
        for row in csv.DictReader(fh):
            t = dt.datetime.fromtimestamp(int(row["time"]), tz=dt.timezone.utc).replace(tzinfo=None)
            out[t] = {"o": float(row["open"]), "h": float(row["high"]),
                      "l": float(row["low"]), "c": float(row["close"]),
                      "spread": float(row["spread"] or 0.0)}
    return out


def main() -> int:                                              # noqa: C901
    estate = json.load(gzip.open(ESTATE))
    trades = estate["trades"]
    tf_by = estate["timeframe_by_sleeve"]

    # ---- stage 1: WHICH armed members fill at the rollover hour. Measured, per sleeve. ----
    census = {}
    for s in sorted(set(ARMED_FTMO) | set(ARMED_FN)):
        rows = trades.get(s) or []
        hist: collections.Counter = collections.Counter()
        for r in rows:
            e = dt.datetime.fromisoformat(r["entry_utc"])
            hist[utc_to_broker_naive(e, RULE).hour] += 1
        n = sum(hist.values())
        census[s] = {
            "timeframe": tf_by.get(s),
            "n_trades": n,
            "broker_entry_hour_histogram": {str(k): v for k, v in sorted(hist.items())},
            "share_at_broker_hour_00": round(hist.get(0, 0) / n, 6) if n else None,
            "armed_ftmo": s in ARMED_FTMO,
            "armed_redacted_account": s in ARMED_FN,
            "in_ratified_cohort": None,     # filled below
        }
    for s, c in census.items():
        # The ratified decision's cohort is "the FX D1 cohort ... the mx_* D1 cohort and any
        # future D1 FX sleeve whose generation clock fills at hour 00". mx_btcusd is IN the
        # `mx_*` D1 cohort and is NOT FX, so the decision is ambiguous exactly where it now
        # matters. Recorded as an owner question rather than resolved here.
        c["in_ratified_cohort"] = (
            "AMBIGUOUS — an mx_* D1 sleeve, but BTCUSD is not FX"
            if s.startswith("mx_") else
            ("no — not D1" if c["timeframe"] != "D1" else "yes"))

    # EVERY armed sleeve with ANY fills at the rollover hour, not just the D1 one. The ratified
    # decision scoped the cohort by TIMEFRAME; the phenomenon is a property of the BAR CLOSE
    # HOUR, and an H4 bar closes at broker 00:00 too. `sub_mid_dn_revert` -- armed on both
    # accounts -- puts 44.1 % of its fills there. Scoping by timeframe would have missed it.
    touched = [s for s, c in census.items()
               if (c["share_at_broker_hour_00"] or 0) > 0.0]

    # ---- stage 2: what hour-01 is worth, per armed sleeve, on its hour-00 subset ----
    per_sleeve = {}
    for s in touched:
        rows = trades[s]
        symbols = sorted({r["symbol"] for r in rows})
        m15_by: dict[str, dict] = {}
        for sym in symbols:
            try:
                m15_by[sym] = load_m15(sym)
            except FileNotFoundError:
                m15_by[sym] = {}
        first_by = {k: (min(v) if v else None) for k, v in m15_by.items()}
        covered, uncovered, no_bar, no_feed = [], 0, 0, 0
        breaches = {"stop": 0, "target": 0}
        for r in rows:
            e_utc = dt.datetime.fromisoformat(r["entry_utc"])
            b = utc_to_broker_naive(e_utc, RULE)
            if b.hour != 0:
                continue
            m15 = m15_by.get(r["symbol"]) or {}
            first = first_by.get(r["symbol"])
            if not m15 or first is None:
                no_feed += 1
                continue
            if b < first:
                uncovered += 1
                continue
            # the M15 bar OPENING at broker 00:45 CLOSES at 01:00 -> its close is the h01 fill
            k = b.replace(minute=45)
            bar = m15.get(k)
            if bar is None:
                no_bar += 1
                continue
            p00 = float(r["entry_price"])
            p01 = bar["c"]
            sl = float(r["sl_distance_price"])
            d = int(r["direction"])
            if not (sl > 0):
                continue
            disp = d * (p01 - p00) / sl
            # (2) did anything happen in the skipped hour? The stop is at entry -/+ sl. The
            # target is the TRADE'S OWN (`target_dist`) where it has one -- using a single
            # constant here would have priced every sleeve at mx_btcusd's frontier 5R, which
            # is the contract of exactly one of them.
            stop_px = p00 - d * sl
            td = r.get("target_dist")
            tgt_px = (p00 + d * float(td)) if td else None
            hi = lo = None
            for mm in (0, 15, 30, 45):
                w = m15.get(b.replace(minute=mm))
                if w is None:
                    continue
                hi = w["h"] if hi is None else max(hi, w["h"])
                lo = w["l"] if lo is None else min(lo, w["l"])
            touched_stop = touched_tgt = False
            if hi is not None:
                touched_stop = (lo <= stop_px) if d > 0 else (hi >= stop_px)
                if tgt_px is not None:
                    touched_tgt = (hi >= tgt_px) if d > 0 else (lo <= tgt_px)
            breaches["stop"] += int(touched_stop)
            breaches["target"] += int(touched_tgt)
            # (3) the spread bill, in R, at each hour. `spread` is in POINTS on this feed;
            # convert with the D1 point size implied by the price scale is NOT safe, so the
            # column is reported in its own units and as a RATIO, never as an R figure.
            spread00 = m15.get(b.replace(minute=45))
            covered.append({
                "decision_day": r["decision_day"], "direction": d,
                "symbol": r["symbol"],
                "displacement_r": disp,
                "spread_h00_points": (m15.get(b) or {}).get("spread"),
                "spread_h01_points": (spread00 or {}).get("spread"),
                "touched_stop_in_skipped_hour": touched_stop,
                "touched_target_in_skipped_hour": touched_tgt,
            })
        n = len(covered)
        disps = [c["displacement_r"] for c in covered]
        s00 = [c["spread_h00_points"] for c in covered if c["spread_h00_points"] is not None]
        s01 = [c["spread_h01_points"] for c in covered if c["spread_h01_points"] is not None]
        mean = (sum(disps) / n) if n else None
        pos = sum(1 for x in disps if x > 0)
        # The BROKER-HOUR SPREAD PROFILE per symbol, which is the thing that decides whether
        # the lever has anything to work on. This is the half AH could not see at H4 (a
        # four-hour minimum cannot resolve a one-hour spike) and the half that separates
        # BTCUSD from NZDJPY.
        profile = {}
        for sym, m15 in m15_by.items():
            byh: dict[int, list[float]] = collections.defaultdict(list)
            for t, bar in m15.items():
                if bar["spread"] > 0:
                    byh[t.hour].append(bar["spread"])
            if not byh:
                continue
            med = {h: sorted(v)[len(v) // 2] for h, v in byh.items()}
            others = sorted(v for h, v in med.items() if h != 0)
            base = others[len(others) // 2] if others else None
            profile[sym] = {
                "median_spread_points_by_broker_hour": {str(h): med[h] for h in sorted(med)},
                "hour_00": med.get(0), "median_of_other_hours": base,
                "hour_00_premium_ratio": (round(med[0] / base, 4)
                                          if base and med.get(0) is not None else None),
            }
        per_sleeve[s] = {
            "symbols": symbols,
            "n_trades_total": len(rows),
            "n_at_broker_hour_00": census[s]["broker_entry_hour_histogram"].get("0", 0),
            "n_measurable_on_m15": n,
            "n_before_m15_archive": uncovered,
            "n_missing_bar": no_bar,
            "n_symbol_has_no_m15_feed": no_feed,
            "broker_hour_spread_profile": profile,
            # The premium is a per-SYMBOL property, so the sleeve-level answer is a weighted
            # one: how many of this sleeve's hour-00 fills land on a symbol that actually pays
            # a rollover premium. `sub_mid_dn_revert` is the whole point -- it is armed, it is
            # H4 (outside the ratified D1 cohort), and most of its hour-00 fills are on JPY
            # crosses at x8-x20.
            "hour_00_fills_by_symbol": dict(collections.Counter(
                r["symbol"] for r in rows
                if utc_to_broker_naive(dt.datetime.fromisoformat(r["entry_utc"]),
                                       RULE).hour == 0).most_common()),
            "mean_displacement_r_per_trade": round(mean, 6) if mean is not None else None,
            "median_displacement_r_per_trade": (
                round(sorted(disps)[n // 2], 6) if n else None),
            "sd_displacement_r": (
                round((sum((x - mean) ** 2 for x in disps) / (n - 1)) ** 0.5, 6)
                if n > 1 else None),
            "share_displacement_positive": round(pos / n, 4) if n else None,
            "mean_abs_displacement_r": round(sum(abs(x) for x in disps) / n, 6) if n else None,
            "breaches_in_the_skipped_hour": breaches,
            "first_order_estimate_is_exact_for": (
                n - breaches["stop"] - breaches["target"]),
            "spread_points_mean_h00": round(sum(s00) / len(s00), 4) if s00 else None,
            "spread_points_mean_h01": round(sum(s01) / len(s01), 4) if s01 else None,
            "spread_points_median_h00": sorted(s00)[len(s00) // 2] if s00 else None,
            "spread_points_median_h01": sorted(s01)[len(s01) // 2] if s01 else None,
            "spread_ratio_h00_over_h01_mean": (
                round((sum(s00) / len(s00)) / (sum(s01) / len(s01)), 4)
                if s00 and s01 and sum(s01) else None),
            "rows": covered,
        }

    out = {
        "schema": "gtos.phase15.ce_entry_hour.v1",
        "session": "CE",
        "blocks": "B2310-B2313",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase15/receipts/ce_entry_hour.py",
        "ratified_decision": "phase9/OWNER_DECISION_ENTRY_HOUR.md (Borhen 2026-07-30)",
        "the_stale_scope_note": (
            "The decision says 'the armed three sleeves are not in this cohort, so nothing "
            "armed changes.' True on 2026-07-30; FALSE since 2026-07-31 ~01:26 UTC, when "
            "mx_btcusd_d1_donchian_20_breakout -- a D1 sleeve -- was armed on FTMO."),
        "sources": {
            "estate_trades": str(ESTATE.relative_to(ROOT)),
            "estate_trades_sha256": sha(ESTATE),
            "bars": str(BARS),
            "broker_clock_rule": SERVER,
        },
        "armed_sets": {"FTMO": ARMED_FTMO, "redacted_account": ARMED_FN},
        "census": census,
        "sleeves_the_lever_reaches": touched,
        "measurement": per_sleeve,
        "what_this_does_not_capture": [
            "the path/hold/carry consequences of the shifted entry (AH's end-to-end "
            "re-simulation did; this is first-order on the entry price)",
            "any trade before the M15 archive's first bar",
            "the true hour-00 spread SPIKE: the bar `spread` column is the within-bar MINIMUM "
            "(AH, 0.999 median exact-match over 30 symbols), so a cost saving computed from it "
            "is a LOWER BOUND at hour 00",
        ],
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    for s, c in census.items():
        print(f"  {s:38s} tf={c['timeframe']:>3s} n={c['n_trades']:5d} "
              f"h00={c['share_at_broker_hour_00']}")
    for s, m in per_sleeve.items():
        print(f"\n  {s} ({','.join(m['symbols'])}):")
        print(f"    at broker hour 00: {m['n_at_broker_hour_00']} of {m['n_trades_total']}; "
              f"measurable on M15: {m['n_measurable_on_m15']} "
              f"({m['n_before_m15_archive']} predate the archive, "
              f"{m['n_symbol_has_no_m15_feed']} no feed)")
        print(f"    mean displacement {m['mean_displacement_r_per_trade']} R/trade, "
              f"median {m['median_displacement_r_per_trade']}, "
              f"{m['share_displacement_positive']} positive")
        print(f"    breaches in the skipped hour: {m['breaches_in_the_skipped_hour']}")
        for sym, pr in m["broker_hour_spread_profile"].items():
            print(f"    {sym}: hour-00 median spread {pr['hour_00']} vs "
                  f"{pr['median_of_other_hours']} elsewhere -> "
                  f"premium x{pr['hour_00_premium_ratio']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
