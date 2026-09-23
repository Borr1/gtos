"""Session AH item 5 -- `idxrev`'s inverse, RE-SIMULATED rather than sign-flipped.

    python3 .../ah_idxrev_inverse.py

WHY THIS SLEEVE AND WHY NOW
----------------------------
`idxrev` is AA's standing `INVERSE` row and the one sleeve in the estate with genuinely no
excursion worth keeping: AD re-confirmed it across 1,631 gated exit cells, best cell
+0.0004 R/day. A rule that neither makes money nor leaves money on the table on either exit
geometry is either dead or backwards, and only one of those is testable cheaply.

WHY SIGN-FLIPPING WOULD ANSWER THE WRONG QUESTION -- AF's method note, and it matters here
-------------------------------------------------------------------------------------------
`idxrev`'s contract is NOT symmetric: its stored `target_dist` is 0.75x its `sl_distance_price`
(measured below and published in the artifact). Negating a stored R therefore describes an
instrument with a 0.75R stop and a 1.0R target, which does not exist. The inverse has to be
re-walked through the same labeller on the same bars: same decision bar, same stop distance,
same target distance, direction flipped.

Everything else is held: `winsorize_R` from the book's own bounds, `maxbars` from AA's own
artifact, and only trades AA generated (so the population is AA's, not a re-derivation).
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import hashlib
import json
import os
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
AFDIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AFDIR))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4  # noqa: E402
from src.components.ultimate_book.primitives import Bar, atr14, autocorr, vol_ratio  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AA = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
OUT = HERE / "AH_IDXREV_INVERSE_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
SLEEVE = "idxrev"
#: `fidelity.register_surface_expansion` refuses any name that could be mistaken for a
#: production sleeve -- it must start with `mxf_` or `fam_`. That guard is right: `idxrev` IS a
#: production sleeve and `idxrev_inverse` is not, so the two must never share a namespace.
ARM_SLEEVE = {"forward": "mxf_idxrev_forward", "inverse": "mxf_idxrev_inverse"}


def series_for(symbols: set[str], tf: int) -> dict:
    files = {}
    for p in sorted(glob.glob(f"{BARS}/FTMO_*.csv.gz")):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        if sym in symbols and {"D1": TF_D1, "H4": TF_H4}.get(tfs) == tf:
            files[(sym, tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")
    out = {}
    for key in files:
        rows = src._load(key)
        if rows:
            out[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                         for r in rows],
                        [dt.datetime.fromisoformat(r["time"]) for r in rows])
    return out


def main() -> int:
    with gzip.open(AA, "rt") as fh:
        aa = json.load(fh)
    rows = aa["trades"][SLEEVE]
    maxbars = int(aa.get("maxbars", 80))
    tfs = sorted({r["timeframe"] for r in rows})
    assert len(tfs) == 1, tfs
    tf = tfs[0]
    syms = {r["symbol_canonical"] for r in rows}
    print(f"{SLEEVE}: {len(rows)} AA trades, timeframe {tf}, symbols {sorted(syms)}, "
          f"maxbars {maxbars}")
    ser = series_for(syms, tf)
    idx = {k: {t: i for i, t in enumerate(v[1])} for k, v in ser.items()}

    # AB's three dials at each decision bar, computed here from the same bars the generator
    # saw, so the pre-declared gate below is a rule the live book could apply at decision time.
    atrs = {k: [atr14(v[0], j) for j in range(len(v[0]))] for k, v in ser.items()}

    tr = {"forward": [], "inverse": []}
    misses = collections.Counter()
    ratios = []
    for r in rows:
        key = (r["symbol_canonical"], tf)
        if key not in ser:
            misses["no bars"] += 1
            continue
        bars, times = ser[key]
        i = idx[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
        if i is None:
            misses["decision bar not in archive"] += 1
            continue
        sd = float(r["sl_distance_price"])
        td = r.get("target_dist")
        td = float(td) if td else None
        if td:
            ratios.append(td / sd)
        a = atrs[key][i]
        reg = {"VOL_REGIME": vol_ratio(atrs[key], i),
               "PERSISTENCE": autocorr(bars, i, 60),
               "TREND_STATE": ((bars[i].c - bars[i - 50].c) / a
                               if i >= 50 and a > 0 else None)}
        pol = ExitPolicy(target_dist=td, maxbars=maxbars, label="plain")
        for arm, direction in (("forward", int(r["direction"])),
                               ("inverse", -int(r["direction"]))):
            pr = replay(bars, i, direction, stop_dist=sd, policy=pol)
            tr[arm].append({
                "sleeve": ARM_SLEEVE[arm], "symbol": r["symbol"],
                "entry_utc": r["entry_utc"],
                "exit_utc": (times[pr.exit_index] + dt.timedelta(
                    minutes=(240 if tf == TF_H4 else 1440))).isoformat(),
                "direction": direction, "sl_distance_price": sd,
                "entry_price": float(bars[i].c),
                "r_gross": float(winsorize_R(pr.r_gross)),
                "exit_reason": pr.exit_reason, "mfe_r": round(pr.mfe_r, 6),
                "mae_r": round(pr.mae_r, 6),
                "hold_hours": round((pr.exit_index - i)
                                    * (4.0 if tf == TF_H4 else 24.0), 4),
                "regime": reg,
            })
    print(f"re-walked {len(tr['forward'])} trades; misses {dict(misses)}")
    print(f"target/stop ratio: median {statistics.median(ratios):.4f} over {len(ratios)} "
          f"trades -- so a sign flip would answer a question about a different instrument")

    # Parity: the forward re-walk must reproduce AA's own R, or the inverse is not comparable.
    aa_by = {(r["symbol"], r["entry_utc"]): r["r_gross"] for r in rows}
    exact = sum(1 for t in tr["forward"]
                if abs(aa_by.get((t["symbol"], t["entry_utc"]), 1e9) - t["r_gross"]) < 1e-9)
    print(f"forward parity vs AA: {exact}/{len(tr['forward'])} exact on r_gross")

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    build_broker_symbol_resolver(prof)
    costs = load_broker_true_costs(COSTS)
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AH")
    # PRE-DECLARED, and declared here rather than chosen: `idxrev` is an index REVERSION
    # sleeve, so AB's `revert` band (PERSISTENCE < -0.10) is the tape it needs. One dial, one
    # bucket, both directions, the look logged. This is what turns "dead" into "dead unless the
    # regime it was designed for rescues it", which is the only ending this programme accepts.
    import af_repairs as AFR  # noqa: PLC0415
    for base in ("forward", "inverse"):
        sel = [t for t in tr[base]
               if AFR.bucket("PERSISTENCE", t["regime"]["PERSISTENCE"]) == "revert"]
        tr[f"{base}_revert"] = sel
        ARM_SLEEVE[f"{base}_revert"] = f"mxf_idxrev_{base}_revert"
    print(f"pre-declared PERSISTENCE==revert: forward {len(tr['forward_revert'])}, "
          f"inverse {len(tr['inverse_revert'])} of {len(tr['forward'])}")

    runs = {}
    import src.research_infra.walkforward.fidelity as _fid
    for arm in ("forward", "inverse", "forward_revert", "inverse_revert"):
        recs = [TradeRecord(
            sleeve=ARM_SLEEVE[arm], symbol=t["symbol"],
            entry_utc=dt.datetime.fromisoformat(t["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(t["exit_utc"]),
            direction=t["direction"], sl_distance_price=t["sl_distance_price"],
            entry_price=t["entry_price"], r_gross=t["r_gross"],
            features={"hold_hours": t["hold_hours"], "mfe_r": t["mfe_r"],
                      "mae_r": t["mae_r"], "exit_reason": t["exit_reason"]})
            for t in tr[arm]]
        spec = OPTIONS["C_exploratory"].with_(
            spec_id=f"C_exploratory_ah_idxrev_{arm}", spread_band="mid",
            declared_family_size=456,
            sleeve_symbol_allowlist={ARM_SLEEVE[arm]:
                                     tuple(sorted({t["symbol"] for t in tr[arm]}))})
        _fid.register_surface_expansion(
            ARM_SLEEVE[arm], parent=SLEEVE,
            symbol=", ".join(sorted({t["symbol"] for t in tr[arm]})),
            timeframe=("H4" if tf == TF_H4 else "D1"),
            surface_note=f"AH item 5: {arm}, re-simulated"
            + (", pre-declared PERSISTENCE==revert gate" if arm.endswith("_revert") else ""))
        try:
            g = run_gate({ARM_SLEEVE[arm]: recs}, spec, costs=costs, server=SERVER)
        finally:
            _fid.clear_surface_expansions()
        v = g.verdicts[ARM_SLEEVE[arm]]
        runs[arm] = {
            "n_trades": v.n_trades, "verdict": v.verdict.value,
            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
            "q_value": v.q_value,
            "oos_positive_fold_frac": v.gates.get("stability", {})
            .get("oos_positive_fold_frac"),
            "fold_test_means": [fd.get("test_mean_r") for fd in v.folds],
            "mean_r_gross": statistics.mean(t["r_gross"] for t in tr[arm]),
            "mean_mfe_r": statistics.mean(t["mfe_r"] for t in tr[arm]),
            "mean_mae_r": statistics.mean(t["mae_r"] for t in tr[arm]),
            "exit_reasons": dict(collections.Counter(t["exit_reason"] for t in tr[arm])),
            "first_reason": (v.reasons[0][:260] if v.reasons else None),
        }
        ledger.record(
            mechanism="idxrev", sleeve=ARM_SLEEVE[arm],
            variant={"scope": "direction_arm", "direction": arm,
                     "regime_gate": ("PERSISTENCE==revert (pre_declared)"
                                     if arm.endswith("_revert") else None),
                     "method": "re-simulated, not sign-flipped",
                     "declared_family_size": 456, "verdict_band": "mid"},
            window="AA's own idxrev population",
            outcome=("positive" if (v.pooled_oos_mean_r or 0) > 0 else "negative"),
            metric=v.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
            spec_sha256=spec.seal(), note="AH item 5: idxrev inverse test")
        print(f"  {arm:8s} n={v.n_trades:5d} pooled={v.pooled_oos_mean_r:+.5f} "
              f"p={v.p_raw:.4f} folds+={runs[arm]['oos_positive_fold_frac']} "
              f"gross={runs[arm]['mean_r_gross']:+.5f} {v.verdict.value}")

    out = {"schema": "gtos.ah.idxrev_inverse.v1",
           "generated_by": str(Path(__file__).relative_to(REPO)),
           "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "source": str(AA.relative_to(REPO)),
           "method": ("re-simulated through walkforward.exits.replay on the same bars, same "
                      "decision bar, same stop and target distances, direction flipped. NOT "
                      "a sign flip: the contract is asymmetric."),
           "target_over_stop_median": statistics.median(ratios),
           "n_aa_trades": len(rows), "n_rewalked": len(tr["forward"]),
           "misses": dict(misses),
           "forward_parity_exact_r_gross": exact,
           "maxbars": maxbars, "timeframe": tf,
           "symbols": sorted(syms), "runs": runs,
           "pre_declared_gate": {"dial": "PERSISTENCE", "bucket": "revert",
                                 "why": ("idxrev is an index REVERSION sleeve, so AB's "
                                         "`revert` band is the tape it was designed for"),
                                 "basis": "pre_declared"},
           "entry_hour_note": ("the entry-hour lever does NOT apply to this sleeve: every "
                               "index CFD has no quote at the broker rollover at all (AG "
                               "§5), so its hour multiplier is absent and AH item 1's "
                               "+0.16 R cost saving is an FX-only result"),
           "verdict": ("inverse is positive" if (runs["inverse"]["pooled_oos_mean_r"] or 0) > 0
                       else "inverse is negative too -- the rule is dead in both directions"),
           }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\n{out['verdict']}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
