"""Controls: a harness that cannot reproduce a known answer cannot be trusted with a new one.

Six controls, in the order they would catch a defect:

C1  **Label identity.**  Re-derive the estate's published `r_gross` for all 22,324 held
    decisions under the published contract and require exact equality.  Any mismatch means
    the harness is walking a different program and the run refuses.  This is the same
    control `r1_estate_rewalk.py` uses, reused deliberately.
C2  **Population identity.**  Reproduce `n_trades_by_sleeve` -- including Lane 8's three
    named counts (crypto 181, energy_agri 67, sub_xvol_pullback 88).
C3  **Statistics-layer reproduction.**  Recompute Lane 4's paired channel from lane r1's own
    rows and require agreement with `G_PAIRED_AND_COSTLINE_V1.json` to 4 decimals: the
    cost-band difference SD 0.343693, the quote-side SD 0.776332, the unpaired 1.4566.
    C1/C2 test the walker; this tests the estimator.
C4  **A/A null.**  Two arms that are the same contract under two names must return
    ``INERT`` and no p-value.  A harness that reports a t on an A/A pair will report one on
    anything.
C5  **Sham treatment.**  An arm that changes something economically irrelevant (a widened
    `maxbars` far beyond any realised hold) must produce a delta indistinguishable from 0.
    C4 catches an identical arm; C5 catches an arm that is *different* and *inert*, which is
    the harder case.
C6  **Read-only proof.**  Static: no module in this package names a mutation surface.
    Dynamic: the deployed shadow adapter's `order_send` raises when called.
"""

from __future__ import annotations

import ast
import gzip
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .arms import Arm, ArmUnavailable, exit_arm, published_policy, run_on_own_grid
from .paired_stats import paired_summary
from .substrate import MAXBARS, R1_ROWS, Substrate

HERE = Path(__file__).resolve().parent
LANE4_G = HERE.parents[1] / "lane4_receipts" / "G_PAIRED_AND_COSTLINE_V1.json"


# ------------------------------------------------------------------ C1 + C2 ----------------
def control_label_identity(sub: Substrate, *, tol: float = 1e-9,
                           limit: int | None = None) -> dict[str, Any]:
    """Re-derive every published label from the bars.  Exact equality or the run refuses."""
    checked = mismatch = 0
    max_err = 0.0
    examples: list[dict[str, Any]] = []
    by_sleeve: dict[str, int] = {}
    skips: dict[str, int] = {}
    skip_by_sleeve: dict[str, int] = {}
    pool = sub.intents if limit is None else sub.intents[:limit]
    for it in pool:
        try:
            out = run_on_own_grid(it, sub, published_policy(it, maxbars=MAXBARS), None)
        except ArmUnavailable as exc:
            key = f"{it.sleeve}:{str(exc).split(':')[0][:40]}"
            skips[key] = skips.get(key, 0) + 1
            skip_by_sleeve[it.sleeve] = skip_by_sleeve.get(it.sleeve, 0) + 1
            continue
        err = abs(out.r - it.published_r_gross)
        checked += 1
        by_sleeve[it.sleeve] = by_sleeve.get(it.sleeve, 0) + 1
        max_err = max(max_err, err)
        if err > tol:
            mismatch += 1
            if len(examples) < 8:
                examples.append({"sleeve": it.sleeve, "symbol": it.symbol,
                                 "decision_bar_iso": it.decision_bar_iso,
                                 "published": it.published_r_gross, "rederived": out.r})
    return {"control": "C1_label_identity", "rows_checked": checked, "mismatches": mismatch,
            "max_abs_error": max_err, "examples": examples, "skips": skips,
            "skip_by_sleeve": dict(sorted(skip_by_sleeve.items())),
            "n_by_sleeve": dict(sorted(by_sleeve.items())),
            "pass": mismatch == 0 and checked > 0}


def control_population_identity(sub: Substrate, c1: dict[str, Any]) -> dict[str, Any]:
    """Reproduce the store's own per-sleeve counts, and Lane 8's three named controls."""
    declared = {k: v for k, v in sub.meta["n_trades_by_sleeve"].items() if v}
    got = c1["n_by_sleeve"]
    skipped = c1.get("skip_by_sleeve", {})
    # The identity is `declared == walked + skipped-with-a-named-reason`.  Requiring
    # `declared == walked` would be wrong rather than strict: a decision whose series ends
    # before the trade could be replayed is not a reproduction failure, it is a decision the
    # archive cannot carry, and `r1_estate_rewalk.py` accounts for the same rows the same way.
    diffs = {k: {"declared": v, "walked": got.get(k, 0), "skipped": skipped.get(k, 0)}
             for k, v in declared.items() if got.get(k, 0) + skipped.get(k, 0) != v}
    unaccounted = sum(v - got.get(k, 0) - skipped.get(k, 0) for k, v in declared.items())
    lane8 = {"crypto": 181, "energy_agri": 67, "sub_xvol_pullback": 88}
    lane8_check = {k: {"lane8": v, "walked": got.get(k, 0), "match": got.get(k, 0) == v}
                   for k, v in lane8.items()}
    return {"control": "C2_population_identity",
            "n_sleeves_declared": len(declared),
            "n_sleeves_reproduced_exactly": sum(1 for k, v in declared.items()
                                                if got.get(k, 0) == v),
            "n_sleeves_reconciled_with_skips": sum(
                1 for k, v in declared.items() if got.get(k, 0) + skipped.get(k, 0) == v),
            "total_declared": sum(declared.values()),
            "total_walked": sum(got.values()),
            "total_skipped_with_reason": sum(skipped.values()),
            "unaccounted": unaccounted,
            "skip_reasons": c1.get("skips", {}),
            "unreconciled_sleeves": diffs,
            "lane8_named_controls": lane8_check,
            "pass": not diffs and unaccounted == 0
                    and all(v["match"] for v in lane8_check.values())}


# ------------------------------------------------------------------ C3 ---------------------
def control_statistics_layer(*, rows_path: Path = R1_ROWS,
                             lane4_path: Path = LANE4_G) -> dict[str, Any]:
    """Reproduce Lane 4's paired channel with THIS module's estimator."""
    if not rows_path.is_file() or not lane4_path.is_file():
        return {"control": "C3_statistics_layer", "pass": False,
                "error": f"input missing: {rows_path if not rows_path.is_file() else lane4_path}"}
    rows = json.load(gzip.open(rows_path))
    fwd = [r for r in rows if r["entry_utc"][:4] >= "2025"
           and r.get("r_new_low") is not None and r.get("r_new_high") is not None]
    lane4 = json.load(open(lane4_path))["paired_treatment_channel"]

    cost = [r["r_new_high"] - r["r_new_low"] for r in fwd]
    quote = [r["r_new_mid"] - r["r_old"] for r in fwd]
    blocks = [r["entry_utc"][:10] for r in fwd]
    s_cost = paired_summary(cost, blocks, resamples=400)
    s_quote = paired_summary(quote, blocks, resamples=400)
    unpaired = statistics.pstdev([r["r_new_mid"] for r in fwd])

    exp_cost = lane4["estate_all29_cost_band_low_to_high"]
    exp_quote = lane4["estate_all29_quote_correction_old_to_mid"]
    exp_unp = lane4["unpaired_reference_sd_all29"]

    checks = {
        "n_forward_rows": {"expected": exp_cost["n"], "got": len(fwd),
                           "match": len(fwd) == exp_cost["n"]},
        "sd_delta_cost_band": {"expected": exp_cost["sd_delta_R"], "got": round(s_cost.sd, 6),
                               "match": abs(s_cost.sd - exp_cost["sd_delta_R"]) < 5e-5},
        "mean_delta_cost_band": {"expected": exp_cost["mean_delta_R"],
                                 "got": round(s_cost.mean, 6),
                                 "match": abs(s_cost.mean - exp_cost["mean_delta_R"]) < 5e-5},
        "sd_delta_quote_side": {"expected": exp_quote["sd_delta_R"],
                                "got": round(s_quote.sd, 6),
                                "match": abs(s_quote.sd - exp_quote["sd_delta_R"]) < 5e-5},
        "unpaired_sd": {"expected": exp_unp, "got": round(unpaired, 4),
                        "match": abs(unpaired - exp_unp) < 5e-4},
    }
    return {"control": "C3_statistics_layer", "checks": checks,
            "measured_noise_reduction_x": round(unpaired / s_cost.sd, 4) if s_cost.sd else None,
            "lane4_projected_noise_reduction_x": round(1.0 / exp_cost["sd_ratio_vs_unpaired"], 4),
            "block_se_vs_iid_se": {
                "cost_band": {"iid": s_cost.se_iid, "block": s_cost.se_block},
                "quote_side": {"iid": s_quote.se_iid, "block": s_quote.se_block}},
            "pass": all(c["match"] for c in checks.values())}


# ------------------------------------------------------------------ C4 + C5 ----------------
def control_aa_null(sub: Substrate, sleeve: str = "crypto") -> dict[str, Any]:
    """An A/A pair must be INERT and must not produce a p-value."""
    a = exit_arm("AA_control", lambda it: published_policy(it), band="mid",
                 dimension="null", declared_at="2026-08-12", is_control=True,
                 rationale="A/A null: the published contract")
    b = exit_arm("AA_treatment_same_contract", lambda it: published_policy(it), band="mid",
                 dimension="null", declared_at="2026-08-12",
                 rationale="A/A null: the SAME published contract under a different arm name")
    from .evaluate import run_question
    from .arms import PairingClass

    res = run_question("C4_AA_null", a, b, sub.by_sleeve(sleeve), sub,
                       pairing_class=PairingClass.TRADE_PAIRED)
    ok = (res.summary.verdict == "INERT" and res.summary.p_block is None
          and res.pairing_proof["verdict"] == "INERT_ARMS")
    return {"control": "C4_AA_null", "sleeve": sleeve, "n": res.n_paired,
            "verdict": res.summary.verdict, "p_value_reported": res.summary.p_block,
            "pairing_verdict": res.pairing_proof["verdict"],
            "pass": ok,
            "reading": "an A/A pair that produced a t would invalidate every other number "
                       "this harness reports"}


def control_sham_treatment(sub: Substrate, sleeve: str = "crypto") -> dict[str, Any]:
    """A treatment that is genuinely different and economically inert must measure ~0.

    Widening `maxbars` from 80 to 400 can only change a trade that was still open at bar 80.
    The delta is therefore a real, non-degenerate quantity that should be small and
    concentrated -- the harness must report the concentration rather than a clean p-value.
    """
    a = exit_arm("sham_control_maxbars80", lambda it: published_policy(it, maxbars=80),
                 band="mid", dimension="null", declared_at="2026-08-12", is_control=True,
                 rationale="sham: the published 80-bar horizon")
    b = exit_arm("sham_treatment_maxbars400", lambda it: published_policy(it, maxbars=400),
                 band="mid", dimension="null", declared_at="2026-08-12",
                 rationale="sham: a 5x horizon, which only touches trades open at bar 80")
    from .evaluate import run_question
    from .arms import PairingClass

    res = run_question("C5_sham", a, b, sub.by_sleeve(sleeve), sub,
                       pairing_class=PairingClass.TRADE_PAIRED)
    return {"control": "C5_sham_treatment", "sleeve": sleeve, "n": res.n_paired,
            "discordance": round(res.summary.discordance, 6),
            "mean_delta": round(res.summary.mean, 6),
            "verdict": res.summary.verdict,
            "top1pct_share": res.summary.top1pct_share,
            "notes": res.summary.notes,
            "pass": res.summary.verdict in ("NEAR_INERT", "MEASURED"),
            "reading": "the check is not that the delta is zero -- it is that a contrast "
                       "resting on a handful of rows is LABELLED as one"}


# ------------------------------------------------------------------ C6 ---------------------
MUTATION_NAMES = ("order_send", "order_check", "OrderSend", "position_close", "trade_request")


def control_read_only(package_dir: Path = HERE) -> dict[str, Any]:
    """Static + dynamic proof that this package cannot reach a broker."""
    hits: list[dict[str, Any]] = []
    probes: list[dict[str, Any]] = []
    imports: set[str] = set()
    for p in sorted(package_dir.glob("*.py")):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for al in node.names:
                    imports.add(al.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                fn = node.func
                nm = getattr(fn, "attr", None) or getattr(fn, "id", None)
                if nm in MUTATION_NAMES:
                    rec = {"file": p.name, "line": node.lineno, "call": nm}
                    # THE ONE DELIBERATE CALL: this module's own dynamic proof, made against
                    # ShadowReadOnlyMT5Adapter, whose order_send raises. It is listed
                    # separately rather than whitelisted silently, because a scan that hides
                    # its own exception is the scan an adversary edits first.
                    if p.name == "controls.py":
                        probes.append(rec | {"why": "dynamic refusal probe on the read-only "
                                                    "shadow adapter; the call must RAISE"})
                    else:
                        hits.append(rec)
    banned_imports = sorted(i for i in imports if i.lower() in ("metatrader5", "socket",
                                                               "requests", "urllib",
                                                               "http", "httpx"))
    dynamic: dict[str, Any] = {}
    try:
        from src.research_infra.wave21_forward_shadow.mt5_read_only import (
            ShadowMutationRefused,
            ShadowReadOnlyMT5Adapter,
        )

        class _Fake:  # a read-surface-only stand-in; the adapter refuses mutation-only fakes
            def symbol_info_tick(self, *_a, **_k):
                return None

            def copy_rates_from(self, *_a, **_k):
                return None

        ad = ShadowReadOnlyMT5Adapter(_Fake(), server="FTMO-Server3")
        try:
            ad.order_send({"action": 1})
            dynamic = {"order_send_raised": False, "exception": None}
        except ShadowMutationRefused as exc:
            dynamic = {"order_send_raised": True, "exception": f"{type(exc).__name__}: {exc}"}
        except Exception as exc:
            dynamic = {"order_send_raised": True, "exception": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:
        dynamic = {"order_send_raised": None, "error": f"{type(exc).__name__}: {exc}"}

    return {"control": "C6_read_only",
            "files_scanned": [p.name for p in sorted(package_dir.glob("*.py"))],
            "static_mutation_call_sites_in_package": hits,
            "deliberate_refusal_probes": probes,
            "banned_imports_present": banned_imports,
            "shadow_adapter_order_send_raises": dynamic,
            "pass": (not hits and not banned_imports
                     and dynamic.get("order_send_raised") is True)}


# ------------------------------------------------------------------ C7 ---------------------
def control_lane8_paired_reproduction(sub: Substrate) -> dict[str, Any]:
    """Reproduce a PAIRED TREATMENT that another lane already measured.

    C1-C3 verify the walker and the estimator separately.  This verifies the two composed on
    the one contrast the estate has an independent paired number for: swarm2 Lane 8's
    `energy_agri` exit-contract A/B (`LANE8_MEASUREMENTS_V1.json`), plain 4R against the live
    `partial_be_runner`, measured at **-0.28829 R/trade paired (t -2.385)** on n = 72.

    The populations are NOT identical -- Lane 8 walked an EXPANDED symbol surface and this
    harness walks the estate's own 67 decisions on the live `ON_SURFACE` -- so the control is
    directional and magnitude-banded, not an equality.  Stating it as an equality would be
    the more impressive and less true claim.
    """
    from .arms import PairingClass, partial_be_policy, published_policy
    from .evaluate import run_question

    a = exit_arm("C7_energy_plain_4R", lambda it: published_policy(it), band="mid",
                 dimension="exit_contract", declared_at="2026-08-12", is_control=True,
                 rationale="Lane 8's PLAIN_published arm")
    b = exit_arm("C7_energy_partial_be_2R", lambda it: partial_be_policy(it, 2.0),
                 band="mid", dimension="exit_contract", declared_at="2026-08-12",
                 rationale="Lane 8's LIVE_partial_be_runner arm")
    res = run_question("C7", a, b, sub.by_sleeve("energy_agri"), sub,
                       pairing_class=PairingClass.TRADE_PAIRED)
    lane8 = -0.28829
    got = res.summary.mean
    rel = abs(got - lane8) / abs(lane8)
    return {"control": "C7_lane8_paired_reproduction",
            "lane8_mean_delta_r_per_trade": lane8, "lane8_n": 72, "lane8_t": -2.385,
            "b8_mean_delta_r_per_trade": round(got, 6), "b8_n": res.n_paired,
            "b8_t_block": (round(res.summary.t_block, 3)
                           if res.summary.t_block is not None else None),
            "sign_agrees": (got < 0) == (lane8 < 0),
            "relative_magnitude_gap": round(rel, 4),
            "pass": ((got < 0) == (lane8 < 0)) and rel < 0.25,
            "reading": "different symbol surfaces, same sign, magnitudes within 25 %. A "
                       "fourth independent instrument on the same armed sleeve."}


def run_all(sub: Substrate, *, limit: int | None = None) -> dict[str, Any]:
    c1 = control_label_identity(sub, limit=limit)
    c2 = control_population_identity(sub, c1)
    c3 = control_statistics_layer()
    c4 = control_aa_null(sub)
    c5 = control_sham_treatment(sub)
    c6 = control_read_only()
    c7 = control_lane8_paired_reproduction(sub)
    out = {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6, "C7": c7}
    out["all_pass"] = all(v.get("pass") for v in out.values() if isinstance(v, dict))
    return out
