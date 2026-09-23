#!/usr/bin/env python3
"""Session CH — declare and bill every economic look before opening outcomes.

This file deliberately contains no gate import and no outcome reader.  It writes the fixed
protocol receipt, records the already-existing TRAIN/VAL provenance of each proposed gate
cell, and routes every bill through ``training_lane.graduation.graduate``.  Gate execution is
in ``ch_lever_measurements.py`` and refuses to run unless this declaration chain exists.

The four P1-HIST looks were named by CE before Session CH.  The eight entry-hour looks are
CH's prospective control family: committed behaviour, the ratified policy, a matched
inverse-cheapest shift, and five matched random-shift seeds.  A control is a look.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from src.research_infra.training_lane.graduation import Candidate, graduate  # noqa: E402
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    IterationLedger,
    candidate_id,
    spec_digest,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward.spec import GateSpec  # noqa: E402

PROTOCOL_OUT = HERE / "CH_MEASUREMENT_PROTOCOL_V1.json"
ITERATION_LEDGER = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
    / "TRAINING_LANE_ITERATION_LEDGER.jsonl"
)
GRADUATION_LEDGER = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
    / "TRAINING_LANE_GRADUATION_LEDGER.jsonl"
)
BASE_DECLARATION = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase14/receipts"
    / "CANDIDATE_FAMILY_V13.json"
)
DECLARED_DATE = "2026-07-31"
ENGINE_BLACKOUT = tuple(tuple(x) for x in GateSpec.__dataclass_fields__["reserved_blackout"].default)
GAP_ACK = ("gap_2026H1_tail_pre_arming",)
N_RANDOM_SEEDS = 5
RANDOM_SEEDS = tuple(20260731 + i for i in range(N_RANDOM_SEEDS))


def _sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _rel(path: Path) -> str:
    """Keep evidence portable across worktrees; every CH artifact is inside this repo."""
    return str(path.relative_to(REPO))


P1_LOOKS = (
    {
        "name": "ch_p1_hist::m1::mx_btcusd_target5_redacted_account",
        "mechanism": "p1_hist_cross_broker",
        "sleeve": "mx_btcusd_d1_donchian_20_breakout",
        "family": "CANDIDATE_BOOK_V1",
        "span": ("2017-06-12", "2026-07-27"),
        "spec": {
            "milestone": "M1_cross_broker",
            "account": "redacted_account",
            "server": "redacted_account-Server 2",
            "exit": "target_5R",
            "population": "RECORDED",
            "option": "B_balanced",
            "bands": ["flat_control", "low", "mid", "high"],
            "threshold": "ADMIT at >=2/3 real bands; positive sign; recent-two-fold mean >0",
        },
    },
    *(
        {
            "name": f"ch_p1_hist::m2::{sleeve}",
            "mechanism": "p1_hist_cross_instrument",
            "sleeve": sleeve,
            "family": "CANDIDATE_BOOK_V1",
            "span": span,
            "spec": {
                "milestone": "M2_cross_instrument_mechanism",
                "account": "FTMO",
                "server": "FTMO-Server3",
                "exit": "target_5R",
                "population": "RECORDED",
                "option": "B_balanced",
                "bands": ["flat_control", "low", "mid", "high"],
                "threshold": (
                    "pooled OOS mean R/day >0; strict form requires ADMIT at >=2/3 real "
                    "bands on every one of the three declared members"
                ),
            },
        }
        for sleeve, span in (
            ("mx_ethusd_d1_donchian_20_breakout", ("2017-09-14", "2026-07-15")),
            ("mx_avausd_d1_donchian_20_breakout", ("2021-04-14", "2026-06-19")),
            ("mx_nzdjpy_d1_donchian_20_breakout", ("2007-12-10", "2026-07-15")),
        )
    ),
)

ENTRY_ARMS = (
    "h00_control",
    "h01_ratified",
    "inverse_cheapest_shift_matched",
    *(f"random_shift_matched_s{i}" for i in range(N_RANDOM_SEEDS)),
)


def _entry_look(arm: str) -> dict:
    return {
        "name": f"ch_entry_hour::{arm}",
        "mechanism": "sub_mid_jpy_entry_hour",
        "sleeve": "sub_mid_dn_revert",
        "family": "B7_5_SEPARABILITY_MINE_V1",
        "span": ("2022-05-26", "2026-07-27"),
        "spec": {
            "arm": arm,
            "population": "RECORDED",
            "option": "B_balanced",
            "bands": ["flat_control", "low", "mid", "high"],
            "members": ["GBPJPY", "CHFJPY", "AUDJPY", "USDJPY", "EURJPY"],
            "entry_semantics": "implemented deferral_reason: only broker-hour-00 closes move to 01",
            "matched_control_rule": (
                "h01 shifts every shift-eligible broker-hour-00 row; inverse and each random "
                "arm shift the same count per member on the same full population"
            ),
        },
    }


LOOKS = tuple(P1_LOOKS) + tuple(_entry_look(a) for a in ENTRY_ARMS)


def protocol() -> dict:
    body = {
        "schema": "gtos.phase15.ch.measurement_protocol.v1",
        "session": "CH",
        "blocks": "B2450-B2499",
        "declared_date": DECLARED_DATE,
        "declared_before_outcome_access": True,
        "authority": [
            "phase15/SESSION_CH_LEVER_MEASUREMENTS.md",
            "phase15/receipts/CE_MX_PROMOTION_AMENDMENT_V1.json",
            "phase15/OD_HISTORICAL_FIRST_SCALING.md",
            "WAVE_11_WORKING_AGREEMENT.md sections 1 and 6",
        ],
        "p1_hist": {
            "looks": [x["name"] for x in P1_LOOKS],
            "n_looks": len(P1_LOOKS),
            "strict_m2_rule": (
                "all three members must have pooled OOS mean R/day > 0 AND each must ADMIT "
                "at >=2 of 3 real bands. If mx_avausd is NOT_EVALUABLE, M2 is UNREACHABLE; "
                "Session CH does not fall back to CE's looser one-of-three form."
            ),
            "m1_rule": (
                "redacted_account mx_btcusd@target_5R must ADMIT at >=2 of 3 real bands, keep the "
                "FTMO-positive sign, and have recent-two-fold mean R/day > 0."
            ),
            "m4_rule": "recent-two-fold mean R/day > 0 on every evaluable M1/M2 member",
        },
        "entry_hour": {
            "looks": list(ENTRY_ARMS),
            "n_looks": len(ENTRY_ARMS),
            "random_seeds": list(RANDOM_SEEDS),
            "universe": (
                "All five JPY member candidates for which both the committed entry and a +60 "
                "minute M15 close exist in the sanctioned fresh capture. A conservative "
                "max-horizon intersection removes every row whose potential label path can "
                "touch March 2026 before replay reads the path."
            ),
            "h01_ratified": (
                "Shift exactly the rows whose decision close is broker hour 00 to the close at "
                "+60 minutes; leave every other member row unchanged. This is the implemented "
                "entry_hour.deferral_reason population effect, not a new convention."
            ),
            "inverse_cheapest_shift_matched": (
                "Per member, shift the same number of rows as h01 but choose the lowest "
                "gate-native mid-band ENTRY spread-R rows among the shift-eligible universe. "
                "Entry spread is outcome-blind; total cost would leak the realised hold. This "
                "is AW's cheapest-drop inversion translated from deletion to timing."
            ),
            "random_shift_matched": (
                "Per member and seed, shift the same number of rows as h01, sampled without "
                "replacement from the shift-eligible universe. Same population, same number "
                "of one-hour path perturbations; only the cost-targeting axis changes."
            ),
            "arm_rule": (
                "Recommend ARM only if h01 has positive net delta versus h00 at >=2 of 3 real "
                "bands, its mid-band delta exceeds the inverse and every random control, its "
                "recent-two-fold mean R/day is positive, and at least 4 of 5 members have "
                "positive mid-band net delta with none <= -0.10 R/trade. Otherwise DO-NOT-ARM."
            ),
            "scope_boundary": (
                "The gate measures the five fetched JPY members. The current CLI selects the "
                "whole sleeve; metals/energy/index entries at market reopen are not silently "
                "credited to this result and remain a separate transfer boundary."
            ),
        },
        "multiplicity": {
            "total_new_looks": len(LOOKS),
            "p1_hist": len(P1_LOOKS),
            "entry_hour": len(ENTRY_ARMS),
            "billing": "one graduate() call per look; controls included; bands are sensitivities",
        },
        "march_2026": {
            "status": "OUTCOME_UNREAD",
            "engine_blackout": [list(x) for x in ENGINE_BLACKOUT],
            "stronger_driver_guard": (
                "candidate rows whose maximum possible replay horizon intersects March are "
                "dropped before any OHLC path is indexed or any stored outcome field is read"
            ),
        },
        "looks": list(LOOKS),
        "arms_nothing": True,
    }
    return {**body, "self_sha256": _sha(body)}


def write_protocol() -> None:
    PROTOCOL_OUT.write_text(json.dumps(protocol(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {PROTOCOL_OUT.relative_to(REPO)}")


def _latest_existing_head() -> Path:
    head = BASE_DECLARATION
    for n in range(14, 14 + len(LOOKS)):
        p = HERE / f"CANDIDATE_FAMILY_V{n}.json"
        if p.is_file():
            head = p
        else:
            break
    return head


def declare() -> None:
    write_protocol()
    ledger = IterationLedger(
        ITERATION_LEDGER,
        session="CH",
        run_id="CH_MEASUREMENT_PROTOCOL_V1",
        now_utc="2026-07-31T13:00:00+00:00",
    )
    head = _latest_existing_head()
    next_version = int(head.stem.rsplit("_V", 1)[-1]) + 1
    receipts = []
    for look in LOOKS:
        cid = candidate_id(
            mechanism=look["mechanism"], sleeve=look["sleeve"], spec=look["spec"]
        )
        if not ledger.provenance_for(cid):
            ledger.record(
                mechanism=look["mechanism"],
                sleeve=look["sleeve"],
                spec=look["spec"],
                engine_version="ch-measurement-protocol-v1",
                start=look["span"][0],
                end=look["span"][1],
                verdict="evaluated",
                metric=None,
                metric_name="outcome_blind_protocol_registration",
                note=(
                    "Prospective CH gate look over an already-generated historical candidate "
                    "surface. This row registers the fixed cell and source span; no outcome "
                    "or sealed gate verdict was read before the family bill."
                ),
                receipt=str(PROTOCOL_OUT.relative_to(REPO)),
                acknowledge_uncovered=GAP_ACK,
                engine_reserved_blackout=ENGINE_BLACKOUT,
                extra={"declared_look": look["name"], "outcome_read": False},
            )
        cand = Candidate(
            candidate_id=cid,
            name=look["name"],
            sleeve=look["sleeve"],
            spec_digest=spec_digest(look["spec"]),
            basis=(
                "P1-HIST milestone declared by CE before CH"
                if look in P1_LOOKS
                else "CH entry-hour hypothesis/control declared before gating; controls are looks"
            ),
            source=str(PROTOCOL_OUT.relative_to(REPO)),
            proposed_by="Session CH",
        )
        fam = CF.load_candidate_family(head)
        already = any(m.name == cand.name for m in fam.family(look["family"]).members)
        out = HERE / f"CANDIDATE_FAMILY_V{next_version}.json"
        rec = graduate(
            cand,
            family_id=look["family"],
            iteration_ledger=_rel(ITERATION_LEDGER),
            declaration=_rel(head),
            out_declaration=_rel(out),
            graduation_ledger=_rel(GRADUATION_LEDGER),
            declared_at=DECLARED_DATE,
            session="CH",
            blocks="B2452-B2454",
            why=(
                "Session CH prospective measurement bill. The gate has not run; March 2026 "
                "is engine-blackout and outcome-unread; one fixed arm, one look."
            ),
        )
        receipts.append(rec.as_dict())
        if not already:
            head = out
            next_version += 1
    print(json.dumps({
        "head": str(head.relative_to(REPO)),
        "n_looks": len(LOOKS),
        "n_billed_this_run": sum(r["billed_looks"] for r in receipts),
        "candidate_family_size": receipts[-1]["declared_family_size"],
        "looks_taken_size": receipts[-1]["looks_taken_size"],
    }, indent=1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("protocol", "declare"), default="protocol")
    args = ap.parse_args(argv)
    if args.stage == "protocol":
        write_protocol()
    else:
        declare()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
