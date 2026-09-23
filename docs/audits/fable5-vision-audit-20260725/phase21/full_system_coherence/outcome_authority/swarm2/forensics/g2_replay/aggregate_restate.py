"""G2-M1/M2 aggregation: per-sleeve restatement, R and dollars, day-clustered intervals.

Reads `receipts/G2_M1_ROWS.json` (one row per estate decision, both cost geometries walked)
and produces the per-sleeve, per-year and armed-set restatement.

THE INTERVAL IS THE ESTATE'S OWN
--------------------------------
`b8_paired_shadow.paired_stats.paired_summary` — day-clustered block bootstrap, 2,000 draws,
seed 20260812 — the same instrument every B8 question is read through. Reusing it means a G2
number and a B8 number can be put on the same page without a footnote about which interval
is which.

DOLLARS
-------
R is unitless; the owner has rejected R-only framing. The conversion is DECLARED, not
inferred: `USD_PER_R` below is dollars of risk per 1 R on one unit. Every dollar figure in
the receipt scales linearly in it and the receipt carries the multiplier so a reader can
rescale without re-running anything.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[9]
B8 = REPO / ("docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
             "outcome_authority/swarm2/breakthrough")
for p in (str(REPO), str(B8)):
    if p not in sys.path:
        sys.path.insert(0, p)

from b8_paired_shadow.paired_stats import paired_summary  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "receipts"

RECON_ENTRY_LEG = 0.00663
EXIT_LEG = {"stop": 0.03932, "trail": 0.03932, "target": 0.0,
            "time_stop": 0.00141, "maxbars": 0.00141, "rollover_flat": 0.00141}
CHARGED_FLAT = 0.02

#: DECLARED. 0.5 % of a $100,000 FTMO challenge account = the `reduced_risk_pct` rung, and a
#: mid-point of the armed set's measured per-trade unit risk (registry confidence 0.15-0.45
#: against a 2.00 % nominal book ceiling). Linear: halve it for $250/R, double for $1,000/R.
USD_PER_R = 500.0

ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")  # sub_mid_dn_revert pulled 2026-08-12


def _slip(exit_reason: str | None) -> float:
    return EXIT_LEG.get(str(exit_reason), 0.0)


def summarise(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not rows:
        return {"label": label, "n": 0}
    days = [r["day"] for r in rows]

    # THE R LABEL IS NEARLY SPREAD-INVARIANT BY CONSTRUCTION, AND THAT IS THE FINDING.
    # `exits.replay`'s `entry_price` is "the anchor every level and every realised R is
    # measured from" (exits.py:317), so shifting the entry by the spread moves the stop AND
    # the target with it: a `stop` exit is exactly -1 R and a `target` exit exactly +kR
    # whatever spread was charged. A spread correction can only reach the R label on exits
    # NOT tied to a barrier -- `trail` and `maxbars`. Reporting only `d_spread_r_label`
    # would therefore report a structural property of the labeller as if it were a
    # statement about the tape. `d_spread_cost_r` is the price-domain quantity that
    # actually carries the correction, and it is the one to read.
    d_spread = [r["r_tape"] - r["r_ship"] for r in rows]
    d_cost = [-(r["spread_tape"] - r["spread_ship"]) / r["stop_dist"] for r in rows]
    s_cost = paired_summary(d_cost, days)
    nonbarrier = [r for r in rows if str(r["exit_ship"]) in ("trail", "maxbars")]
    # Slippage: exit-leg only (what the flat constant is meant to cover), then the
    # round-trip that includes the entry leg the constant never covered.
    d_slip_exit = [-(_slip(r["exit_ship"]) - CHARGED_FLAT) for r in rows]
    d_slip_full = [-(RECON_ENTRY_LEG + _slip(r["exit_ship"]) - CHARGED_FLAT) for r in rows]
    d_both = [a + b for a, b in zip(d_spread, d_slip_exit)]

    s_spread = paired_summary(d_spread, days)
    s_slip = paired_summary(d_slip_exit, days)
    s_both = paired_summary(d_both, days)

    mix = Counter(str(r["exit_ship"]) for r in rows)
    n = len(rows)
    ndays = len(set(days))
    span_days = 0
    try:
        ds = sorted(set(days))
        span_days = (dt.date.fromisoformat(ds[-1]) - dt.date.fromisoformat(ds[0])).days + 1
    except Exception:
        pass

    def blk(s) -> dict[str, Any]:
        return {"mean": round(s.mean, 6),
                "ci95_block": [round(s.ci95_block[0], 6), round(s.ci95_block[1], 6)]
                if s.ci95_block else None,
                "p_block": (round(s.p_block, 6) if s.p_block is not None else None),
                "n_blocks": s.n_blocks,
                "discordance": round(s.discordance, 4)}

    repaired = sum(1 for r in rows if r["why"] == "repaired")
    ratios = [r["ratio"] for r in rows if r["why"] == "repaired"]

    return {
        "label": label,
        "n": n,
        "n_days": ndays,
        "calendar_span_days": span_days,
        "level_r_per_trade": {
            "shipped_geometry": round(statistics.fmean(r["r_ship"] for r in rows), 6),
            "tape_hour_geometry": round(statistics.fmean(r["r_tape"] for r in rows), 6),
        },
        "barrier_mix": {k: round(v / n, 4) for k, v in sorted(mix.items())},
        "hour_repair": {
            "rows_repaired": repaired,
            "coverage": round(repaired / n, 4),
            "ratio_median": round(statistics.median(ratios), 4) if ratios else None,
            "ratio_p90": round(sorted(ratios)[int(0.9 * (len(ratios) - 1))], 4) if ratios else None,
            "ratio_max": round(max(ratios), 4) if ratios else None,
        },
        "delta_spread_cost_r_price_domain": blk(s_cost),
        "spread_cost_r_levels": {
            "shipped": round(statistics.fmean(r["spread_ship"] / r["stop_dist"] for r in rows), 6),
            "tape_hour": round(statistics.fmean(r["spread_tape"] / r["stop_dist"] for r in rows), 6),
        },
        "label_invariance": {
            "rows_whose_R_can_move": len(nonbarrier),
            "share": round(len(nonbarrier) / n, 4),
            "why": "exits.replay:317 anchors every level on entry_price, so a barrier exit "
                   "is +/-kR whatever spread is charged; only trail/maxbars can move",
        },
        "delta_spread_hour_repair": blk(s_spread),
        "delta_slippage_exit_leg": blk(s_slip),
        "delta_slippage_round_trip_mean": round(statistics.fmean(d_slip_full), 6),
        "delta_composed": blk(s_both),
        "usd": {
            "usd_per_r": USD_PER_R,
            "spread_repair_total_usd": round(s_spread.mean * n * USD_PER_R, 2),
            "slippage_exit_total_usd": round(s_slip.mean * n * USD_PER_R, 2),
            "composed_total_usd": round(s_both.mean * n * USD_PER_R, 2),
            "composed_usd_per_trade": round(s_both.mean * USD_PER_R, 2),
            "composed_usd_per_book_day": round(s_both.mean * n / ndays * USD_PER_R, 2)
            if ndays else None,
        },
    }


def main() -> None:
    rows = json.load(open(OUT / "G2_M1_ROWS.json"))
    by_sleeve: dict[str, list] = defaultdict(list)
    for r in rows:
        by_sleeve[r["sleeve"]].append(r)

    res: dict[str, Any] = {
        "measurement": "G2-M1/M2 sleeve-estate restatement at corrected geometry",
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "corrections": {
            "hour_surface": "by_symbol_hour_of_week substituted for by_class_hour_of_week "
                            "(SPREAD_MODEL_V1.json; spread_model.py:396 reads only the class "
                            "table; B10 validated the symbol table to a median 0.64% against "
                            "300,538,915 ticks)",
            "slippage": "RECON_SLIPPAGE_ADJUDICATION_V1 barrier-conditional legs "
                        f"(entry {RECON_ENTRY_LEG}, stop 0.03932, target 0.0, "
                        f"time/maxbars 0.00141) against the flat {CHARGED_FLAT} at "
                        "config/agent_config.yaml:740",
        },
        "sign_convention": "positive delta = the correction IMPROVES the restated economics",
        "estate": summarise(rows, "ESTATE_ALL"),
        "armed_set": summarise([r for r in rows if r["sleeve"] in ARMED], "ARMED_THREE"),
        "by_sleeve": {},
        "by_year": {},
    }
    for sl, rs in sorted(by_sleeve.items()):
        res["by_sleeve"][sl] = summarise(rs, sl)
    by_year: dict[str, list] = defaultdict(list)
    for r in rows:
        by_year[r["year"]].append(r)
    for y, rs in sorted(by_year.items()):
        res["by_year"][y] = summarise(rs, y)

    (OUT / "G2_M1_RESTATEMENT_V1.json").write_text(json.dumps(res, indent=1))

    e = res["estate"]
    print(f"ESTATE n={e['n']} days={e['n_days']}")
    print(f"  hour repair coverage {e['hour_repair']['coverage']:.1%}  "
          f"median ratio {e['hour_repair']['ratio_median']}")
    print(f"  spread repair   {e['delta_spread_hour_repair']}")
    print(f"  slippage exit   {e['delta_slippage_exit_leg']}")
    print(f"  composed        {e['delta_composed']}")
    print(f"  usd             {e['usd']}")
    print()
    print(f"{'sleeve':38s} {'n':>6s} {'dCostR':>9s} {'dSlip':>9s} {'dTotal':>9s} "
          f"{'$/trade':>9s} {'stop%':>6s} {'sprd_r':>7s}")
    order = sorted(res["by_sleeve"].items(),
                   key=lambda kv: kv[1]["delta_spread_cost_r_price_domain"]["mean"]
                   + kv[1]["delta_slippage_exit_leg"]["mean"])
    for sl, s in order:
        dc = s["delta_spread_cost_r_price_domain"]["mean"]
        ds = s["delta_slippage_exit_leg"]["mean"]
        print(f"{sl:38s} {s['n']:6d} {dc:+9.5f} {ds:+9.5f} {dc + ds:+9.5f} "
              f"{(dc + ds) * USD_PER_R:+9.2f} "
              f"{s['barrier_mix'].get('stop', 0) + s['barrier_mix'].get('trail', 0):6.2f} "
              f"{s['spread_cost_r_levels']['shipped']:7.4f}")


if __name__ == "__main__":
    main()
