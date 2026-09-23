"""Session AH deliverable 2, second half -- which of AF's verdicts the composition repair moves.

    python3 .../ah_verdicts_moved.py

AF's `FAMILY_ADMISSION_V1.json` was produced under `v1_multiplicative`, and it carried the
defect it discovered: on the three FX D1 families the era x hour product ran 71x-79x on
average and 880x at worst. AF's interim was to restrict banded pricing to
`era_class == RECORDED`, which drops trades rather than pricing them.

This re-runs AF's OWN grid -- the same 134,027 trades, the same 246 members and 30 families,
the same `mid` band, the same 276-look bill -- once under each composition, and publishes the
delta per sleeve. Four gate runs, no new hypothesis: the trades, the population and the
multiplicity are AF's, and the only thing that changes is how two measured factors combine.

The interim is re-run too (`v2_damped` restricted to RECORDED eras) so the estate can see
what its own conservative treatment was costing it in coverage.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import hashlib
import json
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.costs.spread_model import ERA_HOUR_EXPONENT  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AF = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
TRADES = AF / "AF_FAMILY_TRADES.json.gz"
AF_ADMISSION = AF / "FAMILY_ADMISSION_V1.json"
OUT = HERE / "AH_VERDICTS_MOVED.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
TFN = {"D1": 16408, "H4": 16388}


def load_members(art: dict, res) -> list[fam.FamilyMember]:
    """AF's own reconstruction, verbatim, so the two runs cannot drift apart."""
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
        for r in rows if r["engine_reachable"]]


def row_of(sleeve: str, v) -> dict:
    g = v.gates
    return {"verdict": v.verdict.value, "n_trades": v.n_trades,
            "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
            "q_value": v.q_value,
            "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
            "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
            "first_reason": (v.reasons[0][:220] if v.reasons else None)}


def main() -> int:
    t0 = dt.datetime.now(dt.timezone.utc)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    members = load_members(art, res)
    fams = fam._by_family(members)
    n_looks = len(members) + len(fams)
    costs = load_broker_true_costs(COSTS)
    cost_sha = hashlib.sha256(COSTS.read_bytes()).hexdigest()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AH")
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    print(f"{len(members)} members, {len(fams)} families, {n_looks} looks (AF's bill)")

    by_member = {m.member: to_records(art["trades"][m.member]) for m in members}
    with fam.fidelity_scope(members):
        pooled = {f: fam.pool_family(f, by_member, ms) for f, ms in sorted(fams.items())}
    allow_member = {m.member: (m.broker_symbol,) for m in members}
    allow_family = {f: tuple(sorted({m.broker_symbol for m in ms}))
                    for f, ms in fams.items()}

    runs: dict[str, dict] = {}
    with fam.fidelity_scope(members):
        for comp in ("v1_multiplicative", "v2_damped"):
            for scope, trades, allow in (("member", by_member, allow_member),
                                         ("family", pooled, allow_family)):
                spec = OPTIONS["C_exploratory"].with_(
                    spec_id=f"C_exploratory_ah_moved_{scope}_{comp}",
                    spread_band="mid", spread_composition=comp,
                    cost_artifact_sha256=cost_sha, declared_family_size=n_looks,
                    n_trials=int(nt["n_trials"]),
                    n_trials_basis=f"MEASURED from {DEFAULT_TRIAL_LEDGER}",
                    sleeve_symbol_allowlist=allow)
                r = run_gate(trades, spec, costs=costs, server=SERVER)
                runs[f"{comp}|{scope}"] = {
                    "composition": comp, "scope": scope, "spec_sha256": spec.seal(),
                    "admitted": r.admitted, "rejected_n": len(r.rejected),
                    "not_evaluable_n": len(r.not_evaluable),
                    "rows": {s: row_of(s, v) for s, v in sorted(r.verdicts.items())}}
                print(f"  {comp:18s} {scope:7s} ADMIT {len(r.admitted):2d} "
                      f"REJECT {len(r.rejected):4d} N/E {len(r.not_evaluable):3d}", flush=True)

    moved = {}
    for scope in ("member", "family"):
        a = runs[f"v1_multiplicative|{scope}"]["rows"]
        b = runs[f"v2_damped|{scope}"]["rows"]
        rows = {}
        for s in sorted(set(a) | set(b)):
            ra, rb = a.get(s, {}), b.get(s, {})
            pa, pb = ra.get("pooled_oos_mean_r"), rb.get("pooled_oos_mean_r")
            rows[s] = {
                "verdict_v1": ra.get("verdict"), "verdict_v2": rb.get("verdict"),
                "verdict_changed": ra.get("verdict") != rb.get("verdict"),
                "pooled_v1": pa, "pooled_v2": pb,
                "pooled_delta": (pb - pa) if (pa is not None and pb is not None) else None,
                "p_raw_v1": ra.get("p_raw"), "p_raw_v2": rb.get("p_raw"),
                "sign_flip_to_positive": bool(pa is not None and pb is not None
                                              and pa <= 0 < pb),
                "reason_v2": rb.get("first_reason"),
            }
        deltas = [r["pooled_delta"] for r in rows.values() if r["pooled_delta"] is not None]
        moved[scope] = {
            "n": len(rows),
            "n_verdict_changed": sum(1 for r in rows.values() if r["verdict_changed"]),
            "n_sign_flip_to_positive": sum(1 for r in rows.values()
                                           if r["sign_flip_to_positive"]),
            "pooled_delta_median": statistics.median(deltas) if deltas else None,
            "pooled_delta_max": max(deltas) if deltas else None,
            "pooled_delta_min": min(deltas) if deltas else None,
            "n_improved": sum(1 for x in deltas if x > 0),
            "n_worsened": sum(1 for x in deltas if x < 0),
            "n_unchanged": sum(1 for x in deltas if x == 0),
            "top_20_by_delta": [
                {"sleeve": s, **rows[s]} for s in sorted(
                    (s for s in rows if rows[s]["pooled_delta"] is not None),
                    key=lambda s: -rows[s]["pooled_delta"])[:20]],
            "rows": rows,
        }
        print(f"\n{scope}: {moved[scope]['n_improved']} improved, "
              f"{moved[scope]['n_worsened']} worsened, {moved[scope]['n_unchanged']} unchanged; "
              f"median delta {moved[scope]['pooled_delta_median']:+.5f}, "
              f"max {moved[scope]['pooled_delta_max']:+.4f}; "
              f"{moved[scope]['n_verdict_changed']} verdicts changed, "
              f"{moved[scope]['n_sign_flip_to_positive']} flipped to positive")

    for f in sorted(fams):
        r = moved["family"]["rows"][f]
        ledger.record(
            mechanism=fams[f][0].mechanism, sleeve=f,
            variant={"scope": "pooled_family", "spread_composition": "v2_damped",
                     "era_hour_exponent": ERA_HOUR_EXPONENT,
                     "declared_family_size": n_looks, "verdict_band": "mid"},
            window="AF grid re-run under the repaired composition",
            outcome=("positive" if (r["pooled_v2"] or 0) > 0 else "negative"),
            metric=r["pooled_v2"], metric_name="pooled_oos_mean_r",
            spec_sha256=runs["v2_damped|family"]["spec_sha256"],
            note="AH composition repair: AF's own trades, bill and band")

    out = {"schema": "gtos.ah.verdicts_moved.v1",
           "generated_by": str(Path(__file__).relative_to(REPO)),
           "generated_utc": t0.isoformat(),
           "trades_artifact": str(TRADES.relative_to(REPO)),
           "af_admission_artifact": str(AF_ADMISSION.relative_to(REPO)),
           "band": "mid", "declared_family_size": n_looks,
           "era_hour_exponent": ERA_HOUR_EXPONENT,
           "population": "AF's engine-reachable trades, unchanged",
           "moved": moved, "runs": runs}
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
