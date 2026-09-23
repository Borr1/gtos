#!/usr/bin/env python3
"""Session CI: inherited CA P1-P5 gate for the extended vp M1 surface.

The cut rule is not re-authored here.  This driver imports CA's declared-family verifier and
``gate_arm`` implementation, then runs only ``vp_euidx_pocgrav`` at the same RECORDED,
``B_balanced`` alpha=0.10, ``CANDIDATE_BOOK_V1`` all-declared rule.  It publishes all three real
cost bands plus the flat control, the 80-H4 research horizon beside the live 60-H4 time stop,
measured FTMO swap beside zero-carry, chronological folds, and maxbars share.

Third-party M1 changes signal availability, not the H4 entry/exit labels.  Every gate arm therefore
carries the same caveat: Dukascopy BID index-CFD M1 is not FTMO M1, while costs are FTMO-priced.
"""

from __future__ import annotations

import collections
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.training_lane import IterationLedger  # noqa: E402
from src.research_infra.training_lane.iteration_ledger import spec_digest  # noqa: E402


HERE = Path(__file__).resolve().parent
CA_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
CA_GATE_PATH = CA_DIR / "ca_revival_gate.py"
TRADES = HERE / "CI_VP_TRADES_V1.json.gz"
GENERATION = HERE / "CI_VP_GENERATION_V1.json"
OVERLAP = HERE / "CI_THIRD_PARTY_OVERLAP_V1.json"
SOURCE = HERE / "CI_THIRD_PARTY_SOURCE_V1.json"
OUT = HERE / "CI_VP_GATE_V1.json"

SLEEVE = "vp_euidx_pocgrav"
REAL_BANDS = ("low", "mid", "high")
CAVEAT = (
    "Signal availability before the join uses Dukascopy Bank BID Germany 40 / UK 100 index-CFD "
    "M1, not FTMO broker bars. Entries/exits are labelled on the FTMO H4 archive and every trade "
    "is FTMO-priced through the broker-true commission, spread-era, slippage and swap models. "
    "Provider divergence is measured in CI_THIRD_PARTY_OVERLAP_V1.json."
)


def _load_ca():
    spec = importlib.util.spec_from_file_location("gtos_ci_ca_gate", CA_GATE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CA_GATE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _stamp_caveat(arm: dict) -> dict:
    arm["thirdparty_caveat"] = CAVEAT
    for verdict in (arm.get("verdicts") or {}).values():
        verdict["thirdparty_caveat"] = CAVEAT
    return arm


def _share(rows: list[dict], field: str = "exit_reason") -> dict:
    counts = collections.Counter(r.get(field) or "?" for r in rows)
    n = sum(counts.values())
    return {
        "n": n,
        "exit_reasons": dict(counts.most_common()),
        "maxbars_share": round(counts.get("maxbars", 0) / n, 6) if n else None,
        "horizon_share": round(
            (counts.get("maxbars", 0) + counts.get("time_stop", 0)) / n, 6
        ) if n else None,
        "thirdparty_caveat": CAVEAT,
    }


def _session_verdict(*, admits: list[str], not_evaluable: list[str],
                     live_admits: list[str]) -> str:
    """Apply CA's predeclared vocabulary; flat and zero-carry arms never enter these lists."""
    if len(admits) >= 2:
        return "REVIVAL_CANDIDATE"
    if len(not_evaluable) >= 2:
        return "NOT_EVALUABLE"
    if len(live_admits) >= 2:
        return "CONDITIONAL"
    return "STAYS_DEAD"


def _load_trades() -> tuple[dict, list[dict]]:
    payload = json.loads(gzip.open(TRADES, "rt").read())
    rows = payload["trades"][SLEEVE]
    if not rows:
        raise SystemExit("generation returned no vp trades")
    for row in rows:
        for key in ("decision_day", "entry_utc", "exit_utc"):
            if str(row[key])[:7] == "2026-03":
                raise SystemExit(f"protected March outcome present in gate input: {key}={row[key]}")
    return payload, rows


def _record_iteration(*, doc: dict, rows: list[dict]) -> dict:
    ledger = IterationLedger(session="CI", run_id="CI_THIRDPARTY_M1_VP_V1")
    receipt = str(OUT.relative_to(REPO))
    existing = [r for r in ledger.rows() if r.get("session") == "CI" and r.get("receipt") == receipt]
    if existing:
        return {"status": "already_recorded", "row": existing[-1]}
    mid = doc["P1_primary_arms"]["FTMO|mid"]["verdicts"][SLEEVE]
    variant = {
        "member": SLEEVE,
        "same_declared_member_look": True,
        "candidate_family": "CANDIDATE_BOOK_V1",
        "family_self_sha256": doc["family_self_sha256"],
        "rule": "RECORDED|B_balanced|alpha=0.10|all-declared|all-real-bands",
        "m1_source_receipt_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "overlap_receipt_sha256": hashlib.sha256(OVERLAP.read_bytes()).hexdigest(),
        "maxbars": 80,
        "live_stop_own_h4_bars": 60,
    }
    row = ledger.record(
        mechanism="vp_euidx_pocgrav_thirdparty_m1_data_continuation",
        sleeve=SLEEVE,
        spec=variant,
        start=min(r["decision_day"][:10] for r in rows),
        end=max(r["exit_utc"][:10] for r in rows),
        engine_reserved_blackout=[["2026-03-01", "2026-03-31"]],
        acknowledge_uncovered=("gap_2026H1_tail_pre_arming",),
        engine_version="CA-gate-pattern+CI-provenance-splice-v1",
        verdict="evaluated" if mid.get("pooled_oos_mean_r") is not None else "not_evaluable",
        metric=(mid.get("pooled_oos_mean_r")
                if mid.get("pooled_oos_mean_r") is not None else float(len(rows))),
        metric_name=("pooled_oos_mean_r_per_day_FTMO_mid"
                     if mid.get("pooled_oos_mean_r") is not None else "n_trades"),
        note=(
            "Same declared CANDIDATE_BOOK_V1 member whose look CA already marked TAKEN. "
            "The data continuation is logged unbilled; it adds no member and cannot move the "
            "family high-water. VAL is the survivor book's used-once selection surface; no "
            "headline expectancy is asserted from VAL alone. " + CAVEAT
        ),
        receipt=receipt,
        extra={
            "sealed_gate_outcome": doc["VERDICT"],
            "family_bill_delta": 0,
            "family_member_delta": 0,
            "look_was_already_taken_by": "Session CA / CANDIDATE_FAMILY_V12",
            "spec_digest_recomputed": spec_digest(variant),
        },
    )
    return {"status": "recorded", "row": row}


def gate() -> dict:
    t0 = time.time()
    ca = _load_ca()
    family_doc = ca._verify_family()
    generated, rows = _load_trades()
    overlap = json.loads(OVERLAP.read_text())
    if not overlap.get("gate_permitted"):
        raise SystemExit("CI-3 comparability gate is false; refusing to run CI-4")

    import ad_exit_sweep as AD
    from src.research_infra.walkforward import candidate_family as CF

    costs = AD.load_broker_true_costs(ca.COSTS)
    costs_zero = AD.zero_carry_costs(ca.COSTS)
    allow = AD.allowlist()
    family = CF.load_candidate_family(ca.FAMILY)
    pool = {SLEEVE: rows}

    primary: dict[str, dict] = {}
    for band in (None, *REAL_BANDS):
        key = f"FTMO|{band or 'flat_CONTROL'}"
        primary[key] = _stamp_caveat(
            ca.gate_arm(
                pool,
                account="FTMO",
                band=band,
                costs=costs,
                allow=allow,
                fam=family,
                label=f"ci_vp_{band or 'flat'}",
            )
        )
        v = primary[key]["verdicts"].get(SLEEVE) or {}
        print(
            f"P1 {key:18s} {v.get('verdict')} n={v.get('n_trades')} "
            f"R/day={v.get('pooled_oos_mean_r')} p={v.get('p_raw')} "
            f"fail={v.get('failing_core_gates')}",
            flush=True,
        )

    live_stop: dict[str, dict] = {}
    for band in REAL_BANDS:
        key = f"FTMO|{band}|live_stop_60H4"
        live_stop[key] = _stamp_caveat(
            ca.gate_arm(
                pool,
                account="FTMO",
                band=band,
                costs=costs,
                allow=allow,
                fam=family,
                label=f"ci_vp_{band}_live_stop",
                r_field="r_gross_live_stop",
                diagnose=False,
            )
        )

    zero_carry = _stamp_caveat(
        ca.gate_arm(
            pool,
            account="FTMO",
            band="mid",
            costs=costs_zero,
            allow=allow,
            fam=family,
            label="ci_vp_mid_zero_carry",
            zero_carry=True,
            diagnose=False,
        )
    )

    admits = [
        band for band in REAL_BANDS
        if primary[f"FTMO|{band}"]["verdicts"][SLEEVE]["verdict"] == "ADMIT"
    ]
    not_evaluable = [
        band for band in REAL_BANDS
        if primary[f"FTMO|{band}"]["verdicts"][SLEEVE]["verdict"] == "NOT_EVALUABLE"
    ]
    live_admits = [
        band for band in REAL_BANDS
        if live_stop[f"FTMO|{band}|live_stop_60H4"]["verdicts"][SLEEVE]["verdict"]
        == "ADMIT"
    ]
    verdict = _session_verdict(
        admits=admits, not_evaluable=not_evaluable, live_admits=live_admits
    )

    by_provenance = collections.Counter(r["m1_aux_provenance"] for r in rows)
    maxbars = _share(rows)
    live_maxbars = _share(rows, field="exit_reason_live_stop")
    mid = primary["FTMO|mid"]["verdicts"][SLEEVE]
    zmid = zero_carry["verdicts"][SLEEVE]
    doc = {
        "schema": "gtos.wave15.ci.vp_gate.v1",
        "session": "CI",
        "blocks": "B2515-B2529",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "rule": (
            "Inherited CA rule without a new cut: RECORDED population with AN conditions; "
            "B_balanced alpha 0.10; CANDIDATE_BOOK_V1 all-declared; flat control plus all "
            "low/mid/high real bands; chronological folds."
        ),
        "thirdparty_caveat": CAVEAT,
        "family_artifact": str(ca.FAMILY.relative_to(REPO)),
        "family_self_sha256": family_doc[ca.FAMILY_SHA_FIELD],
        "candidate_family_ratchet": {
            "member": SLEEVE,
            "look_status_before_ci": "TAKEN by Session CA in CANDIDATE_FAMILY_V12",
            "ci_action": "extend data on the same declared member",
            "new_member": False,
            "new_family_look": False,
            "high_water_delta": 0,
            "why": (
                "The family ratchet counts declared members whose look is taken, not data "
                "extensions. CA already converted this member from declared-not-taken to TAKEN; "
                "CI adds no member and cannot un-take or take it again."
            ),
        },
        "cost_artifact": str(ca.COSTS.relative_to(REPO)),
        "cost_reading": (
            "FTMO costs are applied to every trade, including those whose prior-day volume "
            "profile came from third-party M1. No Dukascopy spread or commission is substituted."
        ),
        "population": {
            "n_trades": len(rows),
            "by_symbol": dict(sorted(collections.Counter(r["symbol"] for r in rows).items())),
            "by_m1_aux_provenance": dict(sorted(by_provenance.items())),
            "decision_span": [min(r["decision_day"] for r in rows),
                              max(r["decision_day"] for r in rows)],
            "march_2026_outcomes_read": False,
            "ca_post_join_reproduction_control": generated["ca_post_join_reproduction_control"],
            "thirdparty_caveat": CAVEAT,
        },
        "P1_primary_arms": primary,
        "P2_short_history_sensitivity": {
            "declared_rule": family_doc["ca_declaration_note"]
            ["the_cut_rules_are_declared_not_just_the_axes"]
            ["P2_short_history_is_a_sensitivity_never_an_admission_basis"],
            "application_to_vp": (
                "No vp member has >5 years of M1 availability in this ingest (both begin in "
                "2024), so the mechanical deep-history subset contains zero of two members. "
                "It is NOT_EVALUABLE and barred from admission by P2; the full declared "
                "surface remains primary."
            ),
            "eligible_members": [],
            "members_on_primary_surface": ["GER40", "UK100"],
            "verdict": "NOT_EVALUABLE",
            "can_produce_revival_candidate": False,
            "thirdparty_caveat": CAVEAT,
        },
        "P3_exit_contract": {
            "research_maxbars_80": maxbars,
            "live_time_stop_60H4": live_maxbars,
            "live_stop_gate_arms": live_stop,
            "live_stop_admits_at_bands": live_admits,
            "thirdparty_caveat": CAVEAT,
        },
        "P4_carry": {
            "measured_ftmo_mid": {
                k: mid.get(k) for k in (
                    "verdict", "n_trades", "pooled_oos_mean_r", "swap_nights_mean",
                    "swap_r_mean", "swap_share_of_cost",
                )
            },
            "zero_carry_mid_counterfactual": zero_carry,
            "zero_carry_delta_r_per_day": (
                None if mid.get("pooled_oos_mean_r") is None
                or zmid.get("pooled_oos_mean_r") is None
                else round(zmid["pooled_oos_mean_r"] - mid["pooled_oos_mean_r"], 6)
            ),
            "counterfactual_can_produce_verdict": False,
            "thirdparty_caveat": CAVEAT,
        },
        "P5_controls": {
            "cheapest_drop": (
                "The primary arms' drop_best_retention is the gate's own chronological "
                "cheapest-drop robustness control."
            ),
            "additional_filter_run": False,
            "random_drop_required": False,
            "reason": (
                "No extra member filter was used in the primary arm. P2 is structurally empty "
                "and barred, so a random drop of two from a two-member surface would also be empty."
            ),
            "thirdparty_caveat": CAVEAT,
        },
        "VERDICT": verdict,
        "admits_at_real_bands": admits,
        "not_evaluable_at_real_bands": not_evaluable,
        "conditional_live_stop_admits_at_real_bands": live_admits,
        "verdict_sentence": (
            f"{verdict}: admits at {len(admits)} of 3 real FTMO cost bands under the standing "
            f"80-H4 contract; live 60-H4 alternative admits at {len(live_admits)} of 3. "
            + CAVEAT
        ),
        "used_once_disclosure": (
            "VAL is the survivor book's own used-once selection surface. Historical folds span "
            "TRAIN and VAL; no VAL-only headline expectancy is used for sizing."
        ),
        "seconds_total": round(time.time() - t0, 3),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    iteration = _record_iteration(doc=doc, rows=rows)
    doc["iteration_ledger"] = {
        "status": iteration["status"],
        "path": str(IterationLedger().path.relative_to(REPO)),
        "candidate_id": iteration["row"].get("candidate_id"),
        "surface": iteration["row"].get("surface"),
        "billed": iteration["row"].get("billed"),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    print(doc["verdict_sentence"], flush=True)
    print(f"wrote {OUT.relative_to(REPO)}", flush=True)
    return doc


if __name__ == "__main__":
    gate()
