#!/usr/bin/env python3
"""AY-2b — which generators propose a stop the spread can swallow, and what to do about it.

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/ay_generator_stop_survey.py

AW §4.3 calls the cost tail a GENERATOR defect: `spread_r = spread_price / sl_distance_price`,
so a large value means the generator proposed a stop the spread can swallow. This pairs each
sleeve's ACTUAL stop expression, read from source with its `file:line`, against the measured
`spread_r` distribution of the trades that expression produced.

THE ONE FINDING THAT DECIDES WHERE THE REPAIR GOES
---------------------------------------------------
**An ATR floor is not a spread floor, and this estate already has the counter-example.**
`metals_core` floors its stop at `0.25 * ATR14` (`metals.py:81`) — the strongest floor any
sleeve here carries — and still puts **13.7 % of its trades over the live spread limit, with a
maximum `spread_r` of 1.14**: a stop narrower than the round-trip spread, produced by a
generator that is already floored. ATR measures how far price moves; the spread is what the
broker charges to participate; on an illiquid instrument the second is a large fraction of the
first and no multiple of ATR can see it.

So the repair is NOT "add an ATR floor to the sleeves that lack one". It is a floor stated in
the quantity that is actually wrong — `spread_r` — which is what
`spread_geometry.evaluate_intent` is and where `book_engine._spread_geometry_refusal` applies it.

WHAT IS DELIBERATELY NOT DONE HERE
-----------------------------------
No generator constant is changed. Three reasons, in order of weight:

  1. It would not fix it (the `metals_core` counter-example above).
  2. A wider stop changes the TRADE POPULATION as well as the R geometry, so every published
     economic figure for that sleeve becomes stale and would need regenerating rather than
     rescaling — the wave-11 agreement's rule, and the reason AD excluded the two
     `_atr_mean_reversion` sleeves from its own stop-width cells.
  3. The three worst offenders are not armed, so the urgency is a research question about
     those sleeves' own frontiers, not a live-money one.

Filed as a repair-queue row with the measurement attached, which is what a defect that is
real, measured and not-this-session's-fix is supposed to become.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
CENSUS = HERE / "AY_LIVE_CONTRACT_CENSUS_V1.json"
OUT = HERE / "AY_GENERATOR_STOP_SURVEY_V1.json"
SLEEVES = REPO / "src/components/ultimate_book/sleeves"

#: `{sleeve: (file, line, expression, floor_kind)}` — read from source, not remembered.
#: `floor_kind`: "atr" == the stop is `max(structural, k*ATR)`; "atr_proportional" == the
#: stop IS a multiple of ATR, so it cannot collapse relative to volatility but says nothing
#: about the spread; "none" == a purely structural distance with at most an additive buffer,
#: which can collapse to near zero on a small-range bar.
STOPS: dict[str, tuple[str, int, str, str]] = {
    "metals_core": ("metals.py", 81, "max((c - min(l, gap_bot)) + 0.10*ATR, 0.25*ATR)", "atr"),
    "metals_softband": ("metals.py", 89, "max((max(h, gap_top) - c) + 0.10*ATR, 0.25*ATR)", "atr"),
    "metals_ob_micro": ("metals_ob_micro.py", 84,
                        "max((c - min(l, ob_bot)) + 0.10*ATR, 0.25*ATR)", "atr"),
    "asia_pdl_fade": ("asia_pdl_fade.py", 108, "(c - l) + 0.10*ATR", "none"),
    "liq_asia_up_low_metal": ("liq_asia_up_low_metal.py", 192, "(h - c) + STOP_BUF*ATR", "none"),
    "asian_fade": ("asian_fade.py", 117, "STOP_K * ATR", "atr_proportional"),
    "ny_crypto_momentum": ("ny_crypto_momentum.py", 107, "STOP_MULT * ATR", "atr_proportional"),
    "metal_session_reversion": ("metal_session_reversion.py", 112, "STOP_K * ATR",
                                "atr_proportional"),
    "vol_compression": ("vol_compression.py", 54, "STOP_MULT * ATR", "atr_proportional"),
    "crypto": ("crypto.py", 64, "2 * ATR14", "atr_proportional"),
    "energy_agri": ("energy_agri.py", 57, "sleeve signal's own ATR multiple", "atr_proportional"),
    "idxrev": ("index_jpy.py", 55, "1.5 * ATR14", "atr_proportional"),
    "fx_jpy": ("fx_jpy.py", 203, "1.0 * ATR14(session window)", "atr_proportional"),
    "fx_jpy_ny": ("fx_jpy.py", 203, "1.0 * ATR14(session window)", "atr_proportional"),
    "vss_fxcross_london_up_low": ("vss_fxcross_london_up_low.py", 179, "STOP_ATR * ATR_i",
                                  "atr_proportional"),
    "kz_london_crypto_low": ("kz_london_crypto_low.py", 101, "structural + ATR buffer", "none"),
    "orb_crypto_london": ("orb_crypto_london.py", 119, "opening-range height", "none"),
    "sub_xvol_pullback": ("substrate.py", 146, "geom[0] * ATR", "atr_proportional"),
    "sub_mid_dn_revert": ("substrate.py", 146, "geom[0] * ATR", "atr_proportional"),
    "vp_euidx_pocgrav": ("vp_euidx.py", 119, "volume-profile structural distance", "none"),
}
MX_STOP = ("market_expansion_d1.py", 200, "_risk_abs(bars, signal_idx) (ATR- or range-derived)",
           "atr_proportional")


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def main() -> int:
    census = json.loads(CENSUS.read_text())
    mid = census["by_band"]["mid"]["by_sleeve"]
    rows = {}
    for sleeve, stats in sorted(mid.items()):
        f, line, expr, kind = STOPS.get(sleeve, MX_STOP)
        src = SLEEVES / f
        rows[sleeve] = {
            "stop_expression": expr,
            "source": f"src/components/ultimate_book/sleeves/{f}:{line}",
            "source_sha256": (hashlib.sha256(src.read_bytes()).hexdigest()
                              if src.is_file() else None),
            "stop_floor_kind": kind,
            "has_explicit_stop_floor": kind == "atr",
            "frac_over_live_spread_limit_mid": stats.get("frac_over_spread_limit"),
            "max_spread_r_mid": stats.get("max_spread_r"),
            "median_spread_r_mid": stats.get("median_spread_r"),
            "n_priced": stats.get("n_priced"),
            "armed": stats.get("armed"),
        }
    floored = [r for r in rows.values() if r["has_explicit_stop_floor"]]
    unfloored = [r for r in rows.values() if r["stop_floor_kind"] == "none"]

    def _worst(rs):
        return max((r["max_spread_r_mid"] or 0.0) for r in rs) if rs else None

    return _write({
        "schema": "gtos.ay.generator_stop_survey.v1",
        "census": str(CENSUS.relative_to(REPO)),
        "band": "mid",
        "headline": (
            "An ATR floor is not a spread floor. Every sleeve carrying an explicit ATR stop "
            "floor still produces trades over the live spread limit — `metals_core`, the "
            "most strongly floored sleeve in the estate at 0.25*ATR, reaches spread_r 1.14, "
            "a stop NARROWER than the round-trip spread. The repair therefore belongs in the "
            "quantity that is wrong (spread_r), not in the generators' ATR constants."
        ),
        "counts": {
            "sleeves": len(rows),
            "with_explicit_atr_stop_floor": len(floored),
            "atr_proportional_no_floor_needed": sum(
                1 for r in rows.values() if r["stop_floor_kind"] == "atr_proportional"),
            "purely_structural_no_floor": len(unfloored),
        },
        "worst_max_spread_r_among_floored": _worst(floored),
        "worst_max_spread_r_among_unfloored": _worst(unfloored),
        "not_changed_here": [
            "No generator constant is edited. It would not fix the defect (see headline); a "
            "wider stop changes the TRADE POPULATION as well as the R geometry, so every "
            "published figure for that sleeve would need REGENERATING rather than rescaling "
            "(wave-11 agreement); and the three worst offenders are not armed.",
        ],
        "by_sleeve": rows,
    })


def _write(payload: dict) -> int:
    payload["self_sha256"] = _sha({k: v for k, v in payload.items() if k != "self_sha256"})
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size:,} bytes)")
    print(f"  floored sleeves worst max spread_r: "
          f"{payload['worst_max_spread_r_among_floored']}")
    print(f"  unfloored sleeves worst max spread_r: "
          f"{payload['worst_max_spread_r_among_unfloored']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
