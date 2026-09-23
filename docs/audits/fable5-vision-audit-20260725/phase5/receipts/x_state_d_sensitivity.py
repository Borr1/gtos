"""Does the exit rule decide the verdict on the armed sleeves? Measured, not argued.

    python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/x_state_d_sensitivity.py

THE QUESTION
------------
`x_estate_generate.py` labels every trade with `primitives.simulate_detail(stop, target,
maxbars)` — the sanctioned single fill authority (`admission.py:29`: "ALL fills go through
geometry_lib.simulate ... never hand-rolled"), and the geometry the live path actually
places (`order_router.py:47-55` sets `risk_distance = intent.stop_dist`;
`execution_packets.py` emits `final_target_r`). `metals.py:39-43` says the runner target is
carried on the intent for exactly that reason: "the book carries this as the intent's
target_dist so the live broker TP / final_target_r reproduces the runner geometry".

But `metals_core` and `energy_agri` were VALIDATED under a different exit — the STATE_D
scale-out (`primitives.exit_state_d:126`), which takes a partial at 1.0-1.5R and moves the
remainder to break-even. A trade that runs +1.5R and reverses books **-1.0 R** under a plain
stop/TP and roughly **+0.5R or a scratch** under STATE_D. That asymmetry is one-directional
and it is not small, so a negative verdict on `metals_core` could be the exit rule rather
than the sleeve.

`primitives.exit_state_d` is a vendored byte-faithful copy kept for parity, and **nothing in
`src/` or `scripts/` calls it** — the live decision path places a stop and a runner TP and
never scales out. Its ROUTE ORIGINAL is a different matter and an earlier revision of this
docstring got it wrong by saying "no caller anywhere in the repo":
`compounding_sleeve.exit_state_d` is called throughout the June route
(`INTEG_portfolio_build.py:75,83,89,116,139`, `INTEG_portfolio_build_w3.py:114`,
`KB7_leadlag_stated.py:66`, `KB7_reinstate_sleeves.py:57`), and that machinery is exactly what
produced the W7 validation these two sleeves were admitted on.

So the honest statement is the narrower and more useful one: **the exit the sleeves were
validated under and the exit the live path places are different, and no one has measured the
gap on a common trade set.** This does.

THE `vr` INVERSION IS EXACT, NOT A GUESS
-----------------------------------------
`exit_state_d` reads `vr` only to pick `(scaleR, runR)` on the thresholds `vr<1.35 -> 4.0`,
`vr<1.6 -> 3.0`, `else 2.5` (`primitives.py:128-130`) — and `metals._runner_R` uses the
**same three thresholds** to set `target_dist = _runner_R(vr) * sd` (`metals.py:39-44,204`).
So `target_dist / stop_dist` recovers the tier exactly, and any `vr` inside that tier gives
`exit_state_d` the same `(scaleR, runR)`. No information is lost.

`sub_xvol_pullback` and `sub_mid_dn_revert` are NOT re-labelled: their geometry is a fixed
1:3R (`substrate.py` `XVOL_GEOM`), which `simulate_detail` already models exactly.
"""

from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import os
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.primitives import Bar, exit_state_d, simulate_detail  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

BARS = "/Users/borr/GTOSActive/vps-bars-20260727"
IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_ESTATE_TRADES.json.gz"
OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase5/receipts/X_STATE_D_SENSITIVITY.json"

#: The two FVG-cascade sleeves whose research validation used the STATE_D scale-out.
STATE_D_SLEEVES = ("metals_core", "energy_agri")
TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
MAXBARS = 80


def _vr_for_tier(run_r: float) -> float:
    """A `vr` inside the tier `run_r` came from. Exact for `exit_state_d`'s purposes."""
    if run_r >= 3.5:
        return 1.2       # vr < 1.35  -> scaleR 1.5, runR 4.0
    if run_r >= 2.75:
        return 1.45      # vr < 1.60  -> scaleR 1.5, runR 3.0
    return 1.8           # else       -> scaleR 1.0, runR 2.5


def main() -> dict:
    with gzip.open(IN, "rt") as fh:
        raw = json.load(fh)

    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    files = {}
    for p in glob.glob(f"{BARS}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = {v: k for k, v in TF_NAME.items()}.get(tfs)
        if tf is not None:
            files[(res(sym), tf)] = p
    src = CsvBarSource(files, label="vps-bars-20260727-FTMO")

    series: dict[tuple, tuple] = {}
    index: dict[tuple, dict] = {}

    def _load(key):
        if key not in series:
            rows = src._load(key)
            series[key] = ([Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                            for r in rows],
                           [dt.datetime.fromisoformat(r["time"]) for r in rows])
            index[key] = {ts: i for i, ts in enumerate(series[key][1])}
        return series[key], index[key]

    per_sleeve: dict[str, dict] = {}
    relabelled: dict[str, list[TradeRecord]] = {}
    reasons: dict[str, dict] = {}

    for sleeve in STATE_D_SLEEVES:
        rows = raw["trades"].get(sleeve) or []
        out_rows, deltas, reason_counts = [], [], {}
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            (bars, times), idx = _load(key)
            i = idx.get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None or i + 2 >= len(bars):
                continue
            sd = float(r["sl_distance_price"])
            td = r["target_dist"]
            run_r = (float(td) / sd) if td else 2.5
            vr = _vr_for_tier(run_r)
            d = exit_state_d(bars, i, int(r["direction"]), sd, vr, 0.0, maxbars=MAXBARS)
            r_state_d = winsorize_R(float(d["R"]))
            r_plain, xi = simulate_detail(
                bars, i, int(r["direction"]), stop_dist=sd,
                target_dist=(float(td) if td else None), maxbars=MAXBARS, cost=0.0)
            r_plain = winsorize_R(r_plain)
            reason_counts[d.get("reason") or "?"] = reason_counts.get(d.get("reason") or "?", 0) + 1
            deltas.append(r_state_d - r_plain)
            ivl = dt.timedelta(minutes=TF_MINUTES[tf])
            # `exit_state_d` returns no exit index, so the hold is taken from the plain
            # simulation's exit bar. That is the ONE approximation here and it is stated:
            # STATE_D's scaled leg exits earlier than the runner, so the cost charged below
            # is an UPPER bound on the swap the scaled portion would really pay.
            out_rows.append(TradeRecord(
                sleeve=sleeve, symbol=r["symbol"],
                entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                exit_utc=times[xi] + ivl,
                direction=int(r["direction"]),
                sl_distance_price=sd, entry_price=float(r["entry_price"]),
                r_gross=r_state_d,
                features={"decision_day": r["decision_day"], "timeframe": tf,
                          "state_d_reason": d.get("reason")},
            ))
        relabelled[sleeve] = out_rows
        reasons[sleeve] = reason_counts
        per_sleeve[sleeve] = {
            "n": len(out_rows),
            "mean_delta_r_state_d_minus_plain": (
                round(sum(deltas) / len(deltas), 5) if deltas else None),
            "sum_delta_r": round(sum(deltas), 3) if deltas else None,
            "state_d_exit_reasons": reason_counts,
        }
        print(f"{sleeve}: n={len(out_rows)} mean delta R (STATE_D - plain) = "
              f"{per_sleeve[sleeve]['mean_delta_r_state_d_minus_plain']}  {reason_counts}")

    # Re-run the gate on the WHOLE family with the two sleeves re-labelled, so the
    # multiplicity correction sees the same family it saw before.
    from src.research_infra.walkforward.registry import build_symbol_allowlist  # noqa: PLC0415

    allow = build_symbol_allowlist()
    from src.components.ultimate_book.admission import effective_registry  # noqa: PLC0415
    for name, spec in effective_registry(include_clean3=True).items():
        allow.setdefault(name, tuple(sorted({res(s) for s in (spec.symbols or ())})))

    family: dict[str, list[TradeRecord]] = {}
    for sleeve, rows in raw["trades"].items():
        if sleeve in relabelled:
            family[sleeve] = relabelled[sleeve]
            continue
        family[sleeve] = [
            TradeRecord(
                sleeve=r["sleeve"], symbol=r["symbol"],
                entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
                direction=int(r["direction"]),
                sl_distance_price=float(r["sl_distance_price"]),
                entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
                features={"decision_day": r["decision_day"], "timeframe": r["timeframe"]},
            ) for r in rows
        ]

    declared = len(family) + 12   # + Session W's 12 prior looks; see x_estate_walk.py
    runs = {}
    for name, base in OPTIONS.items():
        spec = base.with_(spec_id=f"{base.spec_id}_x_state_d",
                          sleeve_symbol_allowlist=allow, declared_family_size=declared)
        g = run_gate(family, spec)
        runs[name] = {
            "spec_sha256": spec.seal(), "admitted": g.admitted,
            "rows": {s: {"verdict": v.verdict.value, "n_trades": v.n_trades,
                         "pooled_oos_mean_r": v.pooled_oos_mean_r,
                         "oos_mean_r_per_trade": v.gates.get(
                             "expectancy", {}).get("oos_mean_r_per_trade"),
                         "lifetime_mean_r": v.gates.get(
                             "lifetime", {}).get("mean_r_net_per_trade_all_folds"),
                         "q_value": v.q_value,
                         "first_reason": (v.reasons[0] if v.reasons else None)}
                     for s, v in g.verdicts.items() if s in STATE_D_SLEEVES},
        }
        print(f"\n--- {name} (STATE_D exit) --- ADMIT={g.admitted}")
        for s, r in runs[name]["rows"].items():
            print(f"  {s:16s} {r['verdict']:14s} n={r['n_trades']:4d} "
                  f"R/day={r['pooled_oos_mean_r']}  R/trade={r['oos_mean_r_per_trade']}  "
                  f"life={r['lifetime_mean_r']}")

    out = {
        "schema": "gtos.walkforward.state_d_sensitivity.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase5/receipts/"
                         "x_state_d_sensitivity.py"),
        "question": ("Do metals_core and energy_agri reject because of the sleeve or because "
                     "of the exit rule? They were validated under the STATE_D scale-out "
                     "(primitives.exit_state_d:126, which has no caller anywhere in the repo) "
                     "and the estate walk labels them with a plain stop/runner-TP, which is "
                     "the geometry the live order router actually places."),
        "approximation": ("exit_state_d returns no exit index, so holding time — and "
                          "therefore the swap charged — is taken from the plain simulation's "
                          "exit bar. STATE_D's scaled leg exits earlier, so the cost charged "
                          "here is an UPPER bound for it."),
        "per_sleeve_delta": per_sleeve,
        "gate_under_state_d": runs,
        "declared_family_size": declared,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
