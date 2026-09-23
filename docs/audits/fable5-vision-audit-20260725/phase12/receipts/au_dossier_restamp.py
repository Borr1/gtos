"""Session AU (B1580) — restamp `SLEEVE_DOSSIER_V1.json`'s time-stop block at the repaired spec.

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/au_dossier_restamp.py
    ... --check      # report the drift and write nothing

THE DEBT

`SLEEVE_DOSSIER_V1.json` is the estate's ONE-TRUTH-PER-SLEEVE artifact (AI, rules R0-R11), and it
carries `archive.time_stop.time_stop_bars_m15: 96` for **12** sleeves as a CURRENT claim, with three
derived fields that are false with it. AQ found it in a completeness sweep for other consumers of the
repaired value and filed
`THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_STALE_ON_THE_REPAIRED_FIELD` -- noting that there are **no code
consumers** of the old value anywhere in the tree, *"which is precisely why that one is easy to miss."*

WHY THE FIX IS HERE AND NOT IN `AD_TIMESTOP_UNITS_V1.json`

The dossier's generator (`ai_sleeve_dossier.py:420-424`) copies the block straight out of AD's units
artifact, so the obvious repair is to regenerate that. It would be the wrong repair.
`AD_TIMESTOP_UNITS_V1.json` is AD's **measurement of the defect at B750** and it is correct as one --
AQ's own hardest-won lesson is that *"a measurement of a defect that dies when the defect is fixed is
not a measurement"* (its driver freezes the pre-repair declaration for exactly this reason). Rewriting
AD's units artifact would destroy the record that 96 was ever declared.

So the defect is a PROVENANCE defect in the dossier: it presents a historical snapshot as a current
claim. This restamps the dossier's own block from the LIVE `SLEEVE_EXIT_PROFILES`, recomputes the three
derived fields, and keeps the superseded value beside the new one under `restamped_from`. AD's artifact
is not touched, and neither is any other field of the dossier.

THE DERIVED FIELDS, RECOMPUTED RATHER THAN SCALED

    time_stop_in_own_bars                    = m15 / the MEASURED per-symbol printed ratio AD stored
    time_stop_trading_hours                  = m15 * 0.25   (M15 printed bars are 15 minutes each)
    time_stop_binds_before_maxbars           = own_bars < maxbars_research
    frac_trades_the_time_stop_would_truncate = recomputed over AA's own walked trades, as the fraction
                                               whose `exit_bar_offset` exceeds the stop in own bars --
                                               AD's definition, re-run rather than rescaled, because a
                                               truncation fraction is not linear in the horizon.

BOUNDARY. Reads AA's stored intents and the live spec. No bars, no cost model, no gate, no broker.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)

DOSSIER = REPO / "docs/audits/fable5-vision-audit-20260725/phase8/receipts/SLEEVE_DOSSIER_V1.json"
UNITS = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/AD_TIMESTOP_UNITS_V1.json"
AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AM_SUBMID = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AM_SUBMID_TRADES.json.gz"
RECEIPT = HERE / "AU_DOSSIER_RESTAMP_V1.json"
MAXBARS_RESEARCH = 80
SUBMID = "sub_mid_dn_revert"
#: Calendar M15 bars per bar of each decision grid — the fallback when AD measured no printed ratio.
M15_PER_BAR_CALENDAR = {"M15": 1, "H4": 16, "D1": 96}


def truncation_frac(rows: list, own_bars: float | None) -> float | None:
    """Fraction of walked trades the time stop would have cut short. AD's definition, re-run."""
    if not rows or not own_bars:
        return None
    n = len(rows)
    return round(sum(1 for r in rows if float(r["exit_bar_offset"]) > float(own_bars)) / n, 6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report drift, write nothing")
    a = ap.parse_args()

    doc = json.loads(DOSSIER.read_text(encoding="utf-8"))
    units = json.loads(UNITS.read_text(encoding="utf-8"))["sleeve_contracts"]
    raw = json.load(gzip.open(AA_IN, "rt"))
    trades = {s: list(r) for s, r in raw["trades"].items() if r}
    #: the re-clocked population, as every session since AM has used
    trades[SUBMID] = json.load(gzip.open(AM_SUBMID, "rt"))["trades"]["server_repaired"]

    changed, unchanged, absent = {}, [], []
    for sleeve, rec in (doc.get("sleeves") or {}).items():
        blk = ((rec.get("archive") or {}).get("time_stop") or {})
        if not blk:
            absent.append(sleeve)
            continue
        live = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE).get("time_stop_bars")
        was = blk.get("time_stop_bars_m15")
        if live is None or was is None or int(live) == int(was):
            unchanged.append(sleeve)
            continue
        # The MEASURED per-symbol printed ratio where AD has one; the CALENDAR ratio for the sleeve's
        # own grid otherwise. The first draft of this line fell back to 1.0, which turned the two
        # sleeves that generate no trades (`mx_eu50_cash`, `mx_fra40_cash` -- the archive has no such
        # series) into "7680 own D1 bars". A fallback that produces a number no reader would question
        # is worse than one that fails, so the fallback is now the right ratio and it is labelled.
        measured = (units.get(sleeve) or {}).get("m15_per_own_bar_trade_weighted")
        grid = str(blk.get("timeframe") or (units.get(sleeve) or {}).get("timeframe") or "")
        cal = M15_PER_BAR_CALENDAR.get(grid)
        if not measured and cal is None:
            raise ValueError(f"{sleeve}: no measured printed ratio and no known grid "
                             f"({grid!r}); refusing to invent one")
        ratio = float(measured or cal)
        ratio_source = "measured_trade_weighted" if measured else f"calendar_{grid}"
        own = round(float(live) / ratio, 4)
        new = {
            "time_stop_bars_m15": int(live),
            "time_stop_in_own_bars": own,
            "time_stop_trading_hours": round(float(live) * 0.25, 4),
            "maxbars_research": blk.get("maxbars_research", MAXBARS_RESEARCH),
            "time_stop_binds_before_maxbars": bool(own < float(
                blk.get("maxbars_research") or MAXBARS_RESEARCH)),
            "frac_trades_the_time_stop_would_truncate": truncation_frac(
                trades.get(sleeve) or [], own),
        }
        changed[sleeve] = {
            "restamped_from": {k: blk.get(k) for k in (
                "time_stop_bars_m15", "time_stop_in_own_bars", "time_stop_trading_hours",
                "time_stop_binds_before_maxbars", "frac_trades_the_time_stop_would_truncate")},
            "restamped_to": new,
            "m15_per_own_bar_used": ratio,
            "m15_per_own_bar_source": ratio_source,
        }
        if not a.check:
            blk.update(new)
            blk["restamped_by"] = ("Session AU B1580 from the repaired "
                                  "execution_packets.SLEEVE_EXIT_PROFILES")
            blk["restamped_from"] = changed[sleeve]["restamped_from"]
            blk["restamp_note"] = (
                "The superseded value is AD's B750 MEASUREMENT of the pre-repair declaration and is "
                "correct as one; AD_TIMESTOP_UNITS_V1.json is deliberately NOT rewritten. What was "
                "wrong here was presenting a historical snapshot as a current claim.")

    receipt = {
        "schema": "gtos.au.dossier_restamp.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
                        "au_dossier_restamp.py",
        "session": "AU", "block": "B1580",
        "target": str(DOSSIER.relative_to(REPO)),
        "closes_repair_row": "THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_STALE_ON_THE_REPAIRED_FIELD",
        "ad_units_artifact_deliberately_untouched": str(UNITS.relative_to(REPO)),
        "n_sleeves_in_dossier": len(doc.get("sleeves") or {}),
        "n_restamped": len(changed), "n_unchanged": len(unchanged),
        "n_without_a_time_stop_block": len(absent),
        "restamped": changed,
        "mode": "check" if a.check else "written",
    }
    RECEIPT.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    if not a.check:
        doc["restamped_fields"] = doc.get("restamped_fields", [])
        doc["restamped_fields"].append({
            "session": "AU", "block": "B1580", "field": "archive.time_stop.*",
            "n_sleeves": len(changed),
            "receipt": str(RECEIPT.relative_to(REPO)),
            "why": ("the block was copied from AD's B750 units measurement and presented as a "
                    "current claim; `time_stop_bars_m15` had read 96 (the M15-per-D1 conversion "
                    "ratio) since before AQ's B1404 repair"),
        })
        DOSSIER.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"{'checked' if a.check else 'restamped'} {len(changed)} sleeve(s); "
          f"{len(unchanged)} already current; {len(absent)} carry no time-stop block")
    for s, c in sorted(changed.items()):
        f, t = c["restamped_from"], c["restamped_to"]
        print(f"  {s:40s} m15 {f['time_stop_bars_m15']} -> {t['time_stop_bars_m15']}   "
              f"own {f['time_stop_in_own_bars']} -> {t['time_stop_in_own_bars']}   "
              f"trunc {f['frac_trades_the_time_stop_would_truncate']} -> "
              f"{t['frac_trades_the_time_stop_would_truncate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
