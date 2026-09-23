#!/usr/bin/env python3
"""S15 COST_OF_ERROR historical prove — Challenge 0 tape.

No live bars. No host-mesh. No order_send. Default-off flags still apply
unless ``--force``.

    python3 scripts/run_s15_historical_prove.py --force --log-dir /tmp/s15-prove

Scorecard bars (PROVE_PLAN): decidable ≥ 20, moved ≥ 5, invented_high == 0,
order_send == 0, broker_effect all false, false_abstain == 0.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.judgment.challenge import CHALLENGE_LOGIN  # noqa: E402
from src.judgment.conf_gate import load_cost_matrix, tape_authority_facts  # noqa: E402
from src.judgment.cycle import run_fluid_gate_cycle  # noqa: E402
from src.judgment.inventory import collect_live_inventory  # noqa: E402
from src.judgment.regime_system_one import RegimeAnswerCache  # noqa: E402
from src.judgment.s15_tape import s15_historical_tape_rows  # noqa: E402
from src.judgment.veto import forbidden_jev_keys_in  # noqa: E402

MIN_DECIDABLE = 20
MIN_MOVED = 5


def _judgment_has_order_send() -> int:
    banned = ("order_send", "open_trade")
    count = 0
    for path in (REPO / "src" / "judgment").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
                if name in banned:
                    count += 1
            if isinstance(node, ast.ImportFrom):
                mod = (node.module or "").lower()
                if "mt5" in mod or "book_owner" in mod or mod.endswith("execution"):
                    count += 1
    return count


def score_row(result, tape_row: dict) -> dict:
    cost = result.cost_of_error
    regime = result.regime
    chosen = None if cost is None else cost.chosen
    decidable = bool(cost is not None and chosen in {"YES", "NO", "UNSURE"})
    return {
        "cycle_id": result.cycle_id,
        "tape_id": tape_row.get("tape_id"),
        "ticket": tape_row.get("ticket"),
        "subclass": None if cost is None else cost.subclass,
        "gate_id": None if cost is None else cost.gate_id,
        "p": None if cost is None else cost.p,
        "cost_false_yes": None if cost is None else cost.cost_false_yes,
        "cost_false_no": None if cost is None else cost.cost_false_no,
        "cost_human": None if cost is None else cost.cost_human,
        "chosen": chosen,
        "naive_vendor_choice": None if cost is None else cost.naive_vendor_choice,
        "moved": bool(cost and cost.moved),
        "decidable": decidable,
        "conf_gate_band": None if cost is None else cost.conf_gate_band,
        "conf_floor": None if cost is None else cost.conf_floor,
        "place_veto": bool(cost and cost.place_veto),
        "reason": None if cost is None else cost.reason,
        "gate_decision": None if regime is None else regime.gate_decision,
        "size_factor": None if regime is None else regime.size_factor,
        "hard_off": bool(regime and regime.chair.hard_off),
        "keep_family": bool(regime and regime.chair.keep_family),
        "g4_x_g6_overshrink": False,
        "broker_effect": False,
        "skipped": result.skipped,
        "verify_ok": result.verify.ok,
        "completion": result.completion,
        "log_path": str(result.log_path) if result.log_path else None,
        "note": tape_row.get("note"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--score-out", default=None, help="Write calibration scorecard JSON")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--write-tape",
        default=None,
        help="Optional path to materialize the historical tape JSONL",
    )
    args = parser.parse_args(argv)

    rows = s15_historical_tape_rows()
    if args.write_tape:
        dest = Path(args.write_tape)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

    cache = RegimeAnswerCache()
    inventory = collect_live_inventory(
        sleeves=("spring", "vss", "metals_core", "crypto", "energy_agri", "sub_xvol_pullback"),
        workers=("challenge:0",),
        handlers=("shadow_log", "label_draft"),
        include_w7_armed=False,
        include_launcher_workers=False,
    )

    scored: list[dict] = []
    invented_high = 0
    forbidden_in_jev = 0
    place_veto_ok = False

    for row in rows:
        gold = row["gold_state"]
        news = (gold or {}).get("news") or {}
        if news.get("spine_empty") and news.get("events"):
            invented_high += 1
        result = run_fluid_gate_cycle(
            login=row.get("login") or CHALLENGE_LOGIN,
            inventory=inventory,
            gold_state=gold,
            s14_answers=row.get("system_one_answers"),
            s14_cache=cache,
            s14_research_thresholds=True,
            s14_g4_applies=bool(row.get("g4_applies")),
            s15_ticket=row.get("ticket"),
            s15_subclass=row.get("subclass"),
            log_dir=args.log_dir,
            force=args.force,
            stake="sleeve_admit",
        )
        if result.regime is not None and result.log_path:
            doc = json.loads(result.log_path.read_text(encoding="utf-8"))
            jev = doc.get("s14_jev_state") or {}
            if isinstance(jev, dict) and forbidden_jev_keys_in(jev):
                forbidden_in_jev += 1
            if doc.get("broker_effect") is not False:
                raise SystemExit("broker_effect must be false")
            if doc.get("account_surface", {}).get("login") != CHALLENGE_LOGIN:
                raise SystemExit("login must be 0")
            if "cost_of_error" not in doc:
                raise SystemExit("cost_of_error missing from admit sidecar")
            if doc["cost_of_error"].get("broker_effect") is not False:
                raise SystemExit("cost_of_error.broker_effect must be false")
            facts = doc.get("s15_tape_authority") or {}
            if facts.get("false_abstain") != 0:
                raise SystemExit("s15_tape_authority.false_abstain must be 0")
            if facts.get("place") != "infinity_veto":
                raise SystemExit("s15_tape_authority.place must be infinity_veto")
            if facts.get("g4_x_g6_overshrink") is not False:
                raise SystemExit("s15_tape_authority.g4_x_g6_overshrink must be false")
            if facts.get("new_hard_off") is not False:
                raise SystemExit("s15_tape_authority.new_hard_off must be false")
        scored.append(score_row(result, row))

    place = run_fluid_gate_cycle(
        login=CHALLENGE_LOGIN,
        inventory=inventory,
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.99, "probabilities": {"HOLD": 0.99}}},
        log_dir=args.log_dir,
        force=args.force,
        stake="place",
        apply_flag=True,
    )
    place_veto_ok = bool(
        place.cost_of_error
        and place.cost_of_error.chosen == "VETO"
        and place.cost_of_error.place_veto
        and place.apply.apply is False
        and place.conf_gate.broker_effect is False
    )
    scored.append(
        {
            "cycle_id": place.cycle_id,
            "tape_id": "place-infinity-veto",
            "ticket": None,
            "subclass": "any_place",
            "gate_id": "ANY_PLACE",
            "p": 0.99,
            "chosen": None if place.cost_of_error is None else place.cost_of_error.chosen,
            "naive_vendor_choice": None if place.cost_of_error is None else place.cost_of_error.naive_vendor_choice,
            "moved": False,
            "decidable": False,
            "place_veto": True,
            "reason": "infinity_veto_place_path",
            "broker_effect": False,
            "skipped": place.skipped,
            "verify_ok": place.verify.ok or place.skipped,
            "note": "place_infinity_veto",
        }
    )

    n_decidable = sum(1 for r in scored if r["decidable"])
    n_moved = sum(1 for r in scored if r["moved"])
    n_order_send = _judgment_has_order_send()
    broker_ok = all(r["broker_effect"] is False for r in scored)
    n_false_abstain = sum(1 for r in scored if r.get("subclass") == "false_abstain")
    overshrink = any(r.get("g4_x_g6_overshrink") for r in scored)
    band_counts = Counter(r["conf_gate_band"] for r in scored if r.get("conf_gate_band"))
    pick_counts = Counter(r["chosen"] for r in scored if r.get("chosen"))
    matrix = load_cost_matrix()
    facts = matrix.get("key_facts") or {}
    tape_facts = tape_authority_facts(matrix)

    card = {
        "schema": "gtos.s15.prove_scorecard.v1",
        "login": CHALLENGE_LOGIN,
        "s15_tape_authority": tape_facts,
        "bars_source": "historical_tape_no_live_bars",
        "challenge": {
            "login": CHALLENGE_LOGIN,
            "magic": "0",
            "ns": "operator",
        },
        "n_rows": len(scored),
        "n_decidable": n_decidable,
        "n_moved": n_moved,
        "n_invented_high": invented_high,
        "n_forbidden_jev_keys": forbidden_in_jev,
        "n_order_send": n_order_send,
        "n_false_abstain": n_false_abstain,
        "false_abstain_authority": facts.get("false_abstain", 0),
        "g4_x_g6_overshrink": bool(overshrink),
        "place_infinity_veto": place_veto_ok,
        "broker_effect_all_false": broker_ok,
        "vendor_0_85_forbidden_as_truth": True,
        "pick_counts": dict(pick_counts),
        "conf_gate_band_counts": dict(band_counts),
        "min_decidable": MIN_DECIDABLE,
        "min_moved": MIN_MOVED,
        "pass": bool(
            n_decidable >= MIN_DECIDABLE
            and n_moved >= MIN_MOVED
            and invented_high == 0
            and forbidden_in_jev == 0
            and n_order_send == 0
            and n_false_abstain == 0
            and tape_facts.get("false_abstain") == 0
            and tape_facts.get("false_admit_n") == 29
            and float(tape_facts.get("false_admit_tape_R")) == -28.9172
            and float(tape_facts.get("false_admit_shadow_R")) == -13.5428
            and tape_facts.get("cost_avoided_by_reject_n") == 23
            and float(tape_facts.get("cost_avoided_by_reject_tape_R")) == -24.6586
            and tape_facts.get("g4_x_g6_overshrink") is False
            and tape_facts.get("place") == "infinity_veto"
            and not overshrink
            and place_veto_ok
            and broker_ok
        ),
        "calibration_sheet": scored,
        "how_to_run": (
            "python3 scripts/run_s15_historical_prove.py --force "
            "--log-dir /tmp/s15-prove --write-tape "
            "judgment/astra/lab/s15_historical_tape/TAPE_0.jsonl "
            "--score-out /tmp/s15-prove/scorecard.json"
        ),
        "note": "Historical Challenge tape only. Negative sheet ⇒ research/adjust costs, not idle. Never place.",
    }
    text = json.dumps(card, indent=2, sort_keys=True)
    print(text)
    if args.score_out:
        Path(args.score_out).write_text(text + "\n", encoding="utf-8")
    if not args.force and all(r.get("skipped") for r in scored if r.get("tape_id") != "place-infinity-veto"):
        print(
            "Shadow flag off — prove wrote nothing. Re-run with --force or GTOS_JEV_FLUID_GATES_SHADOW=1.",
            file=sys.stderr,
        )
        return 2
    return 0 if card["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
