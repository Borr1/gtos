"""Judge every mechanism family — as a family, and as its members, on the same bill.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/af_family_gate.py

WHAT IS BEING DECIDED, AND HOW THE TWO RUNS DIFFER
----------------------------------------------------
`AA_ESTATE_WALK` produced 22 `BREADTH` rows: sleeves whose measured edge is real-looking and
whose q cannot clear a 69-look family bill alone. `mx_btcusd_d1_donchian_20_breakout` is the
sharpest — `+0.2446 R/day OOS, 100 % folds, raw p 0.0124, q 0.149`, i.e. it clears alpha raw
and fails only the multiplicity. Breadth is the answer the Fundamental Law gives, and this
script asks it as a measurement rather than an argument:

  MEMBER RUN   every (mechanism, symbol, timeframe) cell judged as its own sleeve. This is
               what W did to the twelve `mx_*` sleeves, generalised to 246 cells.
  FAMILY RUN   each mechanism x asset class x timeframe pooled into ONE sleeve, so the day
               panel takes the equal-weight cross-section and the standard error falls by
               sqrt(k). One hypothesis about the mechanism, not k hypotheses about symbols.

THE BILL IS THE SAME FOR BOTH, AND THAT IS DELIBERATE
-------------------------------------------------------
Both runs are corrected against `declared_family_size = grid.n_looks` — every member cell
AND every family, 276 hypotheses. It is the conservative reading, and it is affordable:
pooling k members multiplies the t-statistic by sqrt(k) while doubling the look count moves
the Bonferroni z by about 0.2. So if breadth wins here it wins against the whole bill, and
the family-vs-standalone comparison changes ONE thing — the hypothesis — instead of two.

The optimistic reading (correct only across the 30 families) is also published, labelled,
because a reader is entitled to see the size of the choice.

WHICH COST CONFIGURATION IS THE VERDICT — DECLARED BEFORE THE RESULTS
-----------------------------------------------------------------------
Four are run: the flat 37-day snapshot every prior estate number used, and Session AG's
`low` / `mid` / `high` era bands. **`mid` is the verdict** — it is the best available
estimate of what a trade's own quarter actually cost, and AG measured that the snapshot's
bias has no consistent sign (EURUSD 2002 at 50x, XAUUSD 2022 at 0.18x), so "charge the flat
snapshot and note the caveat" is not available. `snapshot` is reported beside it for
comparability with `W_MX_PILOT.json` and `AA_ESTATE_WALK.json`; `low`/`high` are the
robustness envelope, and anything whose verdict moves inside it is stamped BAND_UNSTABLE
rather than quoted at its best band.

Offline and pure: reads the trades artifact, the cost artifacts and the spread model; writes
`FAMILY_ADMISSION_V1.json` and appends to the repair queue and the trial ledger.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
TRADES = HERE / "AF_FAMILY_TRADES.json.gz"
OUT = HERE / "FAMILY_ADMISSION_V1.json"
QUEUE = HERE / "AF_REPAIR_QUEUE_FULL.json.gz"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

TFN = {"D1": 16408, "H4": 16388}
BANDS = (None, "low", "mid", "high")
VERDICT_BAND = "mid"
SERVER = "FTMO-Server3"


def load_members(art: dict, res) -> list[fam.FamilyMember]:
    """Rebuild the grid's members from the artifact, so the two scripts cannot drift apart."""
    supports = getattr(res, "supports", None)
    out = []
    for f, info in art["grid"]["families"].items():
        key = f.split("_", 1)[1].rsplit("_", 2)[0]
        tf = TFN[info["timeframe"]]
        for sym in info["symbols"]:
            out.append(fam.FamilyMember(
                member=fam.member_name(key, sym, tf), mechanism_key=key,
                mechanism=info["mechanism"], parent_sleeve=info["parent_sleeve"],
                symbol=sym, broker_symbol=res(sym), timeframe=tf,
                asset_class=info["asset_class"],
                is_authored_cell=(info["timeframe"] == info["authored_timeframe"]),
                profile_supported=(bool(supports(sym)) if callable(supports) else True)))
    assert len(out) == art["grid"]["n_members"], (len(out), art["grid"]["n_members"])
    return out


def to_records(rows: list[dict], sleeve: str | None = None) -> list[TradeRecord]:
    """Engine-reachable trades only — see `af_family_generate.engine_reachable`."""
    return [
        TradeRecord(
            sleeve=(sleeve or r["member"]), symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"entry_hour_utc": r["entry_hour_utc"], "mfe_r": r["mfe_r"],
                      "mae_r": r["mae_r"], "hold_hours": r["hold_hours"],
                      "exit_reason": r["exit_reason"]})
        for r in rows if r["engine_reachable"]
    ]


def row_of(sleeve: str, v, *, folds: bool = False) -> dict:
    g = v.gates
    return {
        "sleeve": sleeve, "verdict": v.verdict.value, "n_trades": v.n_trades,
        "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw, "q_value": v.q_value,
        "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
        "n_folds_evaluable": g.get("sample", {}).get("n_folds_evaluable"),
        "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
        "lifetime_mean_r_per_trade": (v.telemetry.get("lifetime", {})
                                      .get("mean_r_net_per_trade_all_folds")),
        "first_reason": (v.reasons[0][:400] if v.reasons else None),
        # Folds are 7 fields x 6 folds x 276 sleeves x 26 runs if carried everywhere. Kept
        # only on the diagnose runs, which is where anything reads them.
        **({"folds": [{"fold_id": f["fold_id"], "oos_start": f["oos_start"],
                       "oos_end": f["oos_end"], "status": f["status"],
                       "is_initial_train": f["is_initial_train"],
                       "n_test_trades": f["n_test_trades"], "test_mean_r": f["test_mean_r"]}
                      for f in v.folds]} if folds else {}),
    }


def main() -> dict:
    t0 = dt.datetime.now(dt.timezone.utc)
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AF")
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    members = load_members(art, res)
    fams = fam._by_family(members)
    n_looks = len(members) + len(fams)
    costs = load_broker_true_costs(COSTS)
    cost_sha = hashlib.sha256(COSTS.read_bytes()).hexdigest()
    print(f"{len(members)} members, {len(fams)} families, {n_looks} looks; "
          f"cost artifact {COSTS.name} {cost_sha[:12]}")

    by_member = {m.member: to_records(art["trades"][m.member]) for m in members}
    pooled: dict[str, list[TradeRecord]] = {}
    with fam.fidelity_scope(members):
        for f, ms in sorted(fams.items()):
            pooled[f] = fam.pool_family(f, by_member, ms)
    print(f"member trades {sum(len(v) for v in by_member.values())}, "
          f"pooled {sum(len(v) for v in pooled.values())}")

    allow_member = {m.member: (m.broker_symbol,) for m in members}
    allow_family = {f: tuple(sorted({m.broker_symbol for m in ms}))
                    for f, ms in fams.items()}

    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    print(f"measured n_trials = {nt['n_trials']} ({nt.get('basis')})")

    runs: dict[str, dict] = {}
    queue_rows: dict[str, dict] = {}
    with fam.fidelity_scope(members):
        for opt, base in OPTIONS.items():
            for band in BANDS:
                bname = band or "snapshot"
                for scope, trades, allow, declared in (
                    ("member", by_member, allow_member, n_looks),
                    ("family", pooled, allow_family, n_looks),
                    ("family_optimistic", pooled, allow_family, None),
                ):
                    if scope == "family_optimistic" and (opt != "C_exploratory"
                                                         or band != VERDICT_BAND):
                        continue    # the optimistic bill is published once, not everywhere
                    spec = base.with_(
                        spec_id=f"{base.spec_id}_af_{scope}_{bname}",
                        spread_band=band, cost_artifact_sha256=cost_sha,
                        declared_family_size=declared, n_trials=int(nt["n_trials"]),
                        n_trials_basis=(
                            f"MEASURED from the shared prospective trial ledger "
                            f"({DEFAULT_TRIAL_LEDGER}) — {nt.get('basis')}"),
                        sleeve_symbol_allowlist=allow)
                    diag = (opt == "C_exploratory" and band == VERDICT_BAND
                            and scope in ("member", "family"))
                    r = run_gate(trades, spec, costs=costs, diagnose=diag, server=SERVER)
                    key = f"{scope}|{opt}|{bname}"
                    runs[key] = {
                        "scope": scope, "option": opt, "band": bname,
                        "spec_sha256": spec.seal(), "spec_id": spec.spec_id,
                        "declared_family_size": declared,
                        "admitted": r.admitted, "rejected_n": len(r.rejected),
                        "not_evaluable_n": len(r.not_evaluable),
                        "family": {k: v for k, v in r.family.items()
                                   if k not in ("n_trials_basis",)},
                        "rows": {s: row_of(s, v, folds=diag)
                                 for s, v in sorted(r.verdicts.items())},
                    }
                    if diag:
                        queue_rows[scope] = r.repair_queue(
                            server=SERVER,
                            run_label=f"AF family expansion {scope} {opt} @ {bname}",
                            extra={"session": "AF",
                                   "population": "engine-reachable trades only"})
                    print(f"  {key:34s} ADMIT {len(r.admitted):3d}  REJECT "
                          f"{len(r.rejected):3d}  N/E {len(r.not_evaluable):3d}"
                          f"{'  [diagnose]' if diag else ''}", flush=True)

    verdicts = assemble(members, fams, runs, art, by_member, pooled)
    for f, ms in sorted(fams.items()):
        v = verdicts["families"][f]
        ledger.record(
            mechanism=ms[0].mechanism, sleeve=f,
            variant={"scope": "pooled_family", "asset_class": ms[0].asset_class,
                     "timeframe": fam.TF_NAME[ms[0].timeframe], "n_members": len(ms),
                     "declared_family_size": n_looks, "verdict_band": VERDICT_BAND},
            window=v.get("window", ""), outcome=_outcome(v["verdict_at_mid"]),
            metric=v.get("pooled_oos_mean_r_mid"), metric_name="pooled_oos_mean_r",
            spec_sha256=runs[f"family|C_exploratory|{VERDICT_BAND}"]["spec_sha256"],
            note="AF family-level hypothesis over the whole asset class")

    out = {
        "schema": "gtos.walkforward.family_admission.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                         "af_family_gate.py"),
        "generated_utc": t0.isoformat(),
        "trades_artifact": str(TRADES.relative_to(REPO)),
        "trades_generated_utc": art.get("generated_utc"),
        "cost_artifact": {"path": str(COSTS.relative_to(REPO)), "sha256": cost_sha},
        "population": ("engine-reachable trades only — bars the live engine can hand a "
                       "generator. See af_family_generate.engine_reachable and "
                       "bar_provider.py:60-80."),
        "verdict_band": VERDICT_BAND,
        "bands": [b or "snapshot" for b in BANDS],
        "multiplicity": {
            "declared_family_size": n_looks,
            "composition": f"{len(members)} member cells + {len(fams)} families",
            "why": ("both runs pay the same bill so the family-vs-standalone comparison "
                    "changes the hypothesis and nothing else. The 30-family-only "
                    "correction is published as `family_optimistic`."),
            "n_trials": int(nt["n_trials"]), "n_trials_basis": nt.get("basis"),
        },
        "grid": art["grid"],
        "parity": art["parity"],
        "pre_gap_population": art["pre_gap_population"],
        **verdicts,
        "runs": runs,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    with gzip.open(QUEUE, "wt") as fh:
        json.dump(queue_rows, fh, indent=1, default=str)
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.1f} MB)")
    print(f"wrote {QUEUE.relative_to(REPO)}")
    print(f"ledger: {ledger.n_written} rows, {ledger.write_errors} errors")
    return out


def _outcome(v: str) -> str:
    return {"ADMIT": "admitted", "REJECT": "rejected",
            "NOT_EVALUABLE": "not_evaluable"}.get(v, "evaluated")


def assemble(members, fams, runs, art, by_member, pooled) -> dict:
    """Per-family and per-member rows: the verdict, the band envelope, the comparison."""
    def cell(scope, opt, band, sleeve, field):
        r = runs.get(f"{scope}|{opt}|{band}", {}).get("rows", {}).get(sleeve)
        return None if r is None else r.get(field)

    fam_rows: dict[str, dict] = {}
    for f, ms in sorted(fams.items()):
        band_v = {b or "snapshot": cell("family", "C_exploratory", b or "snapshot", f,
                                        "verdict") for b in BANDS}
        band_m = {b or "snapshot": cell("family", "C_exploratory", b or "snapshot", f,
                                        "pooled_oos_mean_r") for b in BANDS}
        tr = pooled[f]
        per_member = {}
        for m in sorted(ms, key=lambda x: x.symbol):
            rows = by_member[m.member]
            per_member[m.member] = {
                "symbol": m.symbol, "broker_symbol": m.broker_symbol,
                "n_trades": len(rows),
                "mean_r_gross": (round(statistics.fmean(t.r_gross for t in rows), 5)
                                 if rows else None),
                "first_entry": (min(t.entry_utc for t in rows).date().isoformat()
                                if rows else None),
                "profile_supported": m.profile_supported,
                "standalone_verdict_mid": cell("member", "C_exploratory", VERDICT_BAND,
                                               m.member, "verdict"),
                "standalone_q_mid": cell("member", "C_exploratory", VERDICT_BAND,
                                         m.member, "q_value"),
                "standalone_oos_mean_r_mid": cell("member", "C_exploratory", VERDICT_BAND,
                                                  m.member, "pooled_oos_mean_r"),
            }
        best_member_q = [x["standalone_q_mid"] for x in per_member.values()
                         if x["standalone_q_mid"] is not None]
        fam_rows[f] = {
            "mechanism": ms[0].mechanism, "mechanism_key": ms[0].mechanism_key,
            "parent_sleeve": ms[0].parent_sleeve, "asset_class": ms[0].asset_class,
            "timeframe": fam.TF_NAME[ms[0].timeframe],
            "is_authored_timeframe": ms[0].is_authored_cell,
            "n_members": len(ms), "n_trades": len(tr),
            "window": (f"{min(t.entry_utc for t in tr).date()}.."
                       f"{max(t.entry_utc for t in tr).date()}" if tr else ""),
            "verdict_at_mid": band_v[VERDICT_BAND],
            "verdict_by_band": band_v,
            "band_unstable": len({v for v in band_v.values() if v}) > 1,
            "pooled_oos_mean_r_mid": band_m[VERDICT_BAND],
            "pooled_oos_mean_r_by_band": band_m,
            "q_mid": cell("family", "C_exploratory", VERDICT_BAND, f, "q_value"),
            "p_raw_mid": cell("family", "C_exploratory", VERDICT_BAND, f, "p_raw"),
            "q_mid_optimistic_bill": cell("family_optimistic", "C_exploratory",
                                          VERDICT_BAND, f, "q_value"),
            "verdict_by_option_at_mid": {
                o: cell("family", o, VERDICT_BAND, f, "verdict") for o in OPTIONS},
            "first_reason_mid": cell("family", "C_exploratory", VERDICT_BAND, f,
                                     "first_reason"),
            "best_member_q_mid": (min(best_member_q) if best_member_q else None),
            "n_members_admitting_standalone_mid": sum(
                1 for x in per_member.values() if x["standalone_verdict_mid"] == "ADMIT"),
            "family_beats_best_member": (
                None if (fam_q := cell("family", "C_exploratory", VERDICT_BAND, f,
                                       "q_value")) is None or not best_member_q
                else bool(fam_q < min(best_member_q))),
            "members": per_member,
            "composition_by_fold": fam.family_composition_by_fold(
                tr, _fold_ranges(runs, f)),
        }
    return {"families": fam_rows}


def _fold_ranges(runs, sleeve) -> list[tuple[dt.date, dt.date]]:
    r = runs.get(f"family|C_exploratory|{VERDICT_BAND}", {})
    row = r.get("rows", {}).get(sleeve) or {}
    folds = row.get("folds") or []
    out = []
    for f in folds:
        try:
            out.append((dt.date.fromisoformat(f["oos_start"]),
                        dt.date.fromisoformat(f["oos_end"])))
        except Exception:  # noqa: BLE001 - folds are telemetry, never a verdict
            continue
    return out


if __name__ == "__main__":
    main()
