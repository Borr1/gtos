#!/usr/bin/env python3
"""Session CL incubation dossiers: registerable governance, fail-closed arming.

This tool reads already-billed aggregate receipts only.  It does not run a gate, decode bars,
touch TEST, execute a broker path, or arm anything.  ``--register`` appends PROPOSED rows through
the ratified Training Lane registry; proposals consume no capacity.  Runtime-contract mismatches
remain explicit arming vetoes in both the proposal receipt and the registry note.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from src.components.ultimate_book import admission as ADM  # noqa: E402
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    FRONTIER_EXIT_OVERRIDES,
)
from src.components.ultimate_book.sleeves import candidate_registry as CR  # noqa: E402
from src.research_infra.training_lane.incubation import (  # noqa: E402
    Incubant,
    IncubationRegistry,
    PreRegisteredRule,
)
from src.research_infra.training_lane.iteration_ledger import IterationLedger  # noqa: E402


AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
AL_ASIA = AUDIT / "phase9/receipts/AL_ASIA_PDL_FRONTIER_V1.json"
AL_CLOSER = AUDIT / "phase9/receipts/ADMISSION_CLOSER_V1.json"
CH = AUDIT / "phase15/receipts/CH_PROMOTION_MILESTONES_V1.json"
OWNER = AUDIT / "phase17/OD_ALL_IN_20260801.md"
REGISTRY = AUDIT / "phase14/receipts/TRAINING_LANE_INCUBATION_REGISTRY.jsonl"
ITERATIONS = AUDIT / "phase14/receipts/TRAINING_LANE_ITERATION_LEDGER.jsonl"
OUT = HERE / "CL_INCUBATION_PROPOSALS_V1.json"
MD_OUT = HERE / "CL_INCUBATION_PROPOSALS_V1.md"

PROPOSED_UTC = "2026-07-31T18:04:17+00:00"
ETH = "mx_ethusd_d1_donchian_20_breakout"
ASIA = "asia_pdl_fade"
WEIGHT = 0.025


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rule(
    rule_id: str,
    what: str,
    class_: str,
    action: str,
    threshold: Any,
    basis: str,
    *,
    why: str = "",
) -> PreRegisteredRule:
    return PreRegisteredRule(
        rule_id=rule_id,
        what=what,
        class_=class_,
        action=action,
        threshold=threshold,
        basis=basis,
        pre_registered_utc=PROPOSED_UTC,
        why_not_inference=why,
    )


def shared_rules(sleeve: str, risk_floor_r: float, basis: str) -> tuple[tuple[PreRegisteredRule, ...], tuple[PreRegisteredRule, ...]]:
    action = (
        f"remove {sleeve} from the account's exact --tags at a decision-day boundary; "
        "do not flatten a healthy adopted position"
    )
    stops = (
        rule(
            "S0_contract_fidelity",
            "any live target, stop, time-stop, account, symbol or effective-confidence mismatch",
            "CRITICAL",
            action,
            {"mismatches_allowed": 0},
            basis,
            why="contract identity is an operational veto, not evidence about edge",
        ),
        rule(
            "S1_risk_budget",
            "cumulative broker-net R reaches the pre-declared loss budget",
            "RISK_BOUND_not_inference",
            action,
            {"cumulative_net_r_lte": -risk_floor_r},
            basis,
            why="the stop says what the owner will pay to learn; it does not test the edge",
        ),
        rule(
            "S2_gross_negative",
            "gross expectancy is non-positive after a minimally interpretable live sample",
            "RISK_BOUND_not_inference",
            action,
            {"min_fills": 20, "min_distinct_day_blocks": 8, "mean_gross_r_lte": 0.0},
            "phase14/receipts/CA_MX_INCUBATION_V1.json::STOP_RULES.S2_gross_negative",
            why="inherited family-wide veto; twenty fills still do not establish an edge",
        ),
    )
    promotion = (
        rule(
            "P1_historical_factory_then_owner",
            "historical-primary graduation on the exact live contract at both firms, with no live veto",
            "ECONOMIC",
            "open an owner ceremony; never auto-promote or auto-reweight",
            {
                "exact_contract_required": True,
                "firm_true_accounts": ["FTMO", "redacted_account"],
                "cost_bands_required": ["low", "mid", "high"],
                "factory_verdict_required": "ADMIT",
                "live_veto_must_be_absent": True,
            },
            "phase15/OD_HISTORICAL_FIRST_SCALING.md and phase17/OD_ALL_IN_20260801.md",
            why="the live record is veto-only; historical factory evidence remains the promotion clock",
        ),
    )
    return stops, promotion


def proposals() -> tuple[list[Incubant], dict[str, Any]]:
    asia_doc = json.loads(AL_ASIA.read_text())
    ch_doc = json.loads(CH.read_text())
    asia = asia_doc["cells"]["stop_2.5x_tgt_native_ts_none"]
    eth = ch_doc["members"][ETH]["bands"]["mid"]

    eth_floor = round(max(3.0, 12.0 * abs(float(eth["oos_mean_r_per_trade"]))), 3)
    asia_floor = round(max(3.0, 12.0 * abs(float(asia["oos_mean_r_per_trade"]))), 3)
    eth_basis = "phase15/receipts/CH_PROMOTION_MILESTONES_V1.json::members.mx_ethusd...bands.mid"
    asia_basis = "phase9/receipts/AL_ASIA_PDL_FRONTIER_V1.json::cells.stop_2.5x_tgt_native_ts_none"
    eth_stops, eth_promotion = shared_rules(ETH, eth_floor, eth_basis)
    asia_stops, asia_promotion = shared_rules(ASIA, asia_floor, asia_basis)

    owner_basis = (
        "phase17/OD_ALL_IN_20260801.md: owner approved more sleeves and live testing on the two "
        "existing accounts; this remains OWNER_RISK_ACCEPTED, never GRADUATED"
    )
    incubants = [
        Incubant(
            incubant_id=f"{ETH}@target_5R@FTMO",
            sleeve=ETH,
            account="FTMO",
            proposed_weight=WEIGHT,
            admission_basis="OWNER_RISK_ACCEPTED",
            evidence=(
                "CH broker-true mid: n=217, +0.456628 R/day, +0.502914 R/trade, "
                "recent-two +1.010822; REJECT robustness and significance (q=1.0)."
            ),
            stop_rules=eth_stops,
            promotion_rules=eth_promotion,
            expected_economics={
                "historical_mid_r_per_day": eth["pooled_oos_mean_r"],
                "historical_mid_r_per_trade": eth["oos_mean_r_per_trade"],
                "recent_two_fold_mean_r_per_day": eth["recent_two_fold_mean"],
                "verdict": eth["verdict"],
                "failing_gates": eth["failing_gates"],
                "interpretation": "positive near-admission arithmetic; not an admission",
            },
            owner_risk_acceptance=owner_basis,
            proposed_by="Session CL",
            note="PROPOSED only; arming vetoed until the exact target-5R live contract has parity proof.",
        ),
        Incubant(
            incubant_id=f"{ASIA}@stop2.5_native_no_ts@FTMO",
            sleeve=ASIA,
            account="FTMO",
            proposed_weight=WEIGHT,
            admission_basis="OWNER_RISK_ACCEPTED",
            evidence=(
                "AL broker-true best cell: n=2827, +0.084626 R/day, +0.048010 R/trade, "
                "5/5 OOS folds positive; REJECT significance (p=0.065893, q=0.576567)."
            ),
            stop_rules=asia_stops,
            promotion_rules=asia_promotion,
            expected_economics={
                "historical_mid_r_per_day": asia["pooled_oos_mean_r"],
                "historical_mid_r_per_trade": asia["oos_mean_r_per_trade"],
                "lifetime_mean_r_per_trade": asia["lifetime_mean_r_per_trade"],
                "oos_positive_fold_fraction": asia["oos_positive_fold_frac"],
                "cost_coverage_fraction": asia["coverage_frac"],
                "verdict": asia["verdict"],
                "failing_gates": asia["failing_gates"],
                "interpretation": "stable positive repaired cell; not an admission",
            },
            owner_risk_acceptance=owner_basis,
            proposed_by="Session CL",
            note=(
                "PROPOSED only; arming vetoed until stop2.5/native/no-time-stop and 0.025 "
                "effective confidence are runtime-addressable and parity-proved."
            ),
        ),
    ]
    meta = {
        incubants[0].incubant_id: {
            "arming_vetoes": [
                "target_5R is absent from FRONTIER_EXIT_OVERRIDES for mx_ethusd; current live contract is target_2R",
                "no trade-by-trade research-to-live parity receipt exists for mx_ethusd@target_5R",
                "redacted_account broker-local target-5R measurement is absent; factory approval on both firms is impossible today",
            ],
            "runtime_checks": {
                "known_market_expansion_tag": ETH in ADM.market_expansion_registry(
                    ADM.resolve_market_expansion_sleeves(
                        policy="positive_weighted12_after_swap", explicit_sleeves=()
                    )[0]
                ),
                "runtime_confidence": ADM.market_expansion_registry(
                    ADM.resolve_market_expansion_sleeves(
                        policy="positive_weighted12_after_swap", explicit_sleeves=()
                    )[0]
                )[ETH].confidence,
                "target5_frontier_override_present": float(
                    FRONTIER_EXIT_OVERRIDES.get(ETH, {}).get("final_target_r", 0.0)
                ) == 5.0,
                "current_frontier_override": FRONTIER_EXIT_OVERRIDES.get(ETH),
                "decision_timeframe": 16408,
                "new_timeframe_needed_on_current_FTMO_worker": False,
            },
        },
        incubants[1].incubant_id: {
            "arming_vetoes": [
                "runtime candidate confidence is 0.25, ten times the 0.025 dossier weight; no per-launch weight override exists",
                "the measured stop2.5/native/no-time-stop contract is not a runtime-selectable contract",
                "the current execution packet uses a time stop while the measured winner uses none",
                "no trade-by-trade research-to-live parity receipt exists for the repaired cell",
            ],
            "runtime_checks": {
                "known_candidate_tag": ASIA in ADM.candidate_book_registry(),
                "runtime_confidence": CR.CANDIDATE_CONFIDENCE[ASIA],
                "proposed_confidence": WEIGHT,
                "decision_timeframe": 15,
                "new_timeframe_needed_on_current_FTMO_worker": True,
            },
        },
    }
    return incubants, meta


def build() -> dict[str, Any]:
    for path in (AL_ASIA, AL_CLOSER, CH, OWNER, REGISTRY, ITERATIONS):
        if not path.is_file():
            raise FileNotFoundError(path)
    incubants, meta = proposals()  # Incubant construction is the registry-shape validation.
    registry = IncubationRegistry(REGISTRY, session="CL", now_utc=PROPOSED_UTC)
    cap = registry.capacity()
    state = registry.state()
    iteration_rows = [json.loads(line) for line in ITERATIONS.read_text().splitlines() if line.strip()]
    proposed = []
    for incubant in incubants:
        row = incubant.as_dict()
        row.update(meta[incubant.incubant_id])
        row["registry_shape_validated"] = True
        row["official_registry_state"] = state.get(incubant.incubant_id, {}).get("state")
        row["ready_to_arm"] = not row["arming_vetoes"]
        row["iteration_disclosure"] = next((
            {
                "candidate_id": carried.get("candidate_id"),
                "candidate_id_windowed": carried.get("candidate_id_windowed"),
                "billed": carried.get("billed"),
                "surface": carried.get("surface"),
            }
            for carried in reversed(iteration_rows)
            if carried.get("extra", {}).get("cl_incubation_proposal") == incubant.incubant_id
        ), None)
        proposed.append(row)
    return {
        "schema": "gtos.phase17.cl.incubation_proposals.v1",
        "session": "CL",
        "blocks": "B2670-B2679",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": PROPOSED_UTC,
        "arms_nothing": True,
        "capacity_before_any_new_arm": cap,
        "capacity_if_both_vetoes_clear_and_owner_arms": {
            "armed": cap["armed"] + len(incubants),
            "headroom": cap["headroom"] - len(incubants),
            "max_concurrent": cap["max_concurrent"],
        },
        "proposals": proposed,
        "approved_for_arming_now": [],
        "screened_not_proposed": {
            "thr_sub_xvol_pullback_vr14_s125_ac015": (
                "not a distinct runtime sleeve, parent sub_xvol_pullback is already armed at 0.45, "
                "and AL REJECTS the variant; an incubation row could not independently stop it"
            ),
            "mx_btcusd_target5_redacted_account": (
                "CH REJECTS all cost bands with negative OOS and lifetime means; live testing is "
                "not a substitute for negative historical-primary evidence"
            ),
            "asia_pdl_fade_redacted_account": (
                "no account-local broker-true dossier exists; the FTMO proposal is not transferred"
            ),
        },
        "inputs": {
            str(path.relative_to(REPO)): sha256(path)
            for path in (AL_ASIA, AL_CLOSER, CH, OWNER, REGISTRY, ITERATIONS)
        },
    }


def render_markdown(doc: Mapping[str, Any]) -> str:
    cap = doc["capacity_before_any_new_arm"]
    lines = [
        "# CL incubation proposals",
        "",
        "Two dossiers are valid for registration and **neither is ready to arm**. Filing them "
        "uses zero capacity. The registry currently has "
        f"**{cap['armed']} armed / {cap['max_concurrent']}**, leaving {cap['headroom']} live slots.",
        "",
    ]
    for row in doc["proposals"]:
        lines += [
            f"## `{row['incubant_id']}`",
            "",
            f"Proposed confidence **{row['proposed_weight']:.3f}**; basis "
            f"`{row['admission_basis']}`. {row['evidence']}",
            "",
            "Arming vetoes:",
            "",
        ]
        lines += [f"- {item}" for item in row["arming_vetoes"]]
        lines += ["", "Pre-registered exit rules:", ""]
        for stop in row["stop_rules"]:
            lines.append(f"- `{stop['rule_id']}`: {stop['what']} — `{stop['threshold']}`")
        for promotion in row["promotion_rules"]:
            lines.append(
                f"- `{promotion['rule_id']}`: {promotion['what']} — owner ceremony only"
            )
        lines.append("")
    lines += ["## Screened out", ""]
    lines += [f"- `{name}`: {reason}" for name, reason in doc["screened_not_proposed"].items()]
    lines += [
        "",
        "The exact next build is therefore contract parity, not a tag ceremony: wire and prove "
        "ETH target-5R; add a bounded, addressable Asia stop/exit/weight contract; then obtain "
        "account-local redacted_account economics before either can qualify for the owner-approved "
        "both-account direct path.",
        "",
    ]
    return "\n".join(lines)


def register_proposals() -> list[str]:
    incubants, meta = proposals()
    registry = IncubationRegistry(REGISTRY, session="CL", now_utc=PROPOSED_UTC)
    written = []
    for incubant in incubants:
        if incubant.incubant_id in registry.state():
            continue
        registry.register(
            incubant,
            note=(
                "Session CL proposal only; consumes zero capacity and MUST NOT arm while "
                + "; ".join(meta[incubant.incubant_id]["arming_vetoes"])
            ),
        )
        written.append(incubant.incubant_id)
    return written


def disclose_unbilled_carries() -> list[str]:
    """Log the two already-taken AL/CH measurements without creating or billing a look."""
    existing = [json.loads(line) for line in ITERATIONS.read_text().splitlines() if line.strip()]
    disclosed = {
        row.get("extra", {}).get("cl_incubation_proposal")
        for row in existing
    }
    ledger = IterationLedger(
        ITERATIONS, session="CL", run_id="CL-existing-measurement-carries",
        now_utc=PROPOSED_UTC,
    )
    rows = []
    specs = (
        {
            "id": f"{ETH}@target_5R@FTMO",
            "sleeve": ETH,
            "spec": {"target_r": 5.0, "account": "FTMO", "cost_band": "mid"},
            "start": "2017-02-19",
            "end": "2026-07-27",
            "metric": 0.4566281699340766,
            "receipt": "docs/audits/fable5-vision-audit-20260725/phase15/receipts/CH_PROMOTION_MILESTONES_V1.json",
            "engine": "CH_PROMOTION_MILESTONES_V1-existing-result",
        },
        {
            "id": f"{ASIA}@stop2.5_native_no_ts@FTMO",
            "sleeve": ASIA,
            "spec": {
                "stop_mult": 2.5, "target": "native", "time_stop_bars": None,
                "account": "FTMO",
            },
            "start": "1992-02-18",
            "end": "2026-07-27",
            "metric": 0.08462647486216306,
            "receipt": "docs/audits/fable5-vision-audit-20260725/phase9/receipts/AL_ASIA_PDL_FRONTIER_V1.json",
            "engine": "AL_ASIA_PDL_FRONTIER_V1-existing-result",
        },
    )
    for item in specs:
        if item["id"] in disclosed:
            continue
        ledger.record(
            mechanism="cl_incubation_existing_measurement_carry",
            sleeve=item["sleeve"],
            spec=item["spec"],
            engine_version=item["engine"],
            start=item["start"],
            end=item["end"],
            verdict="evaluated",
            metric=item["metric"],
            metric_name="broker_true_pooled_oos_r_per_day_existing_receipt",
            note=(
                "EXISTING MEASUREMENT CARRY for a CL incubation proposal. No new outcome was "
                "generated, no new gate was run, and this row bills nothing."
            ),
            receipt=item["receipt"],
            acknowledge_uncovered=("gap_2026H1_tail_pre_arming",),
            engine_reserved_blackout=(("2026-03-01", "2026-03-31"),),
            extra={
                "cl_incubation_proposal": item["id"],
                "existing_measurement_carry": True,
                "new_look": False,
            },
        )
        rows.append(item["id"])
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", action="store_true", help="append PROPOSED rows; never arm")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--md-out", type=Path, default=MD_OUT)
    args = ap.parse_args(argv)
    if args.register:
        print("registered", register_proposals())
        print("unbilled_carries", disclose_unbilled_carries())
    doc = build()
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    args.md_out.write_text(render_markdown(doc))
    print(f"wrote {args.out.relative_to(REPO)}")
    print("approved_for_arming_now", doc["approved_for_arming_now"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
