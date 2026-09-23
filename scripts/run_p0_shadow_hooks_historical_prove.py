#!/usr/bin/env python3
"""P0 warroom_shadow historical prove — Challenge 0 fixtures.

No live bars. No host-mesh. No order_send. APPLY stays unset.

Chair enable (SHADOW only — never flip APPLY)::

    GTOS_JEV_FLUID_GATES_SHADOW=1 python3 scripts/run_p0_shadow_hooks_historical_prove.py \
      --log-dir /tmp/p0-shadow --score-out /tmp/p0-shadow/scorecard.json

``--force`` is the CI dry-run analog when the env flag is unset. Still
shadow-only. Never set ``GTOS_JEV_FLUID_GATES_APPLY`` or
``GTOS_DIG_MULTI_STAGE_GUARD_APPLY``.

Walks CF D bank + S15 Close Loop tickets on the existing
``jev_fluid_gate_v1`` sidecar and stamps P0 SHADOW fields.
Emits FIRE 1201 ``conf_gate_band`` disposition counts versus residual
tickets (291087142, 293128383) and KEEP wins (291816474, 293540988,
291794419). LABEL only. ``apply`` is false on every row.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.judgment.cf_d import question_bank_rows  # noqa: E402
from src.judgment.challenge import CHALLENGE_LOGIN  # noqa: E402
from src.judgment.conf_gate import TICKET_SUBCLASS  # noqa: E402
from src.judgment.cycle import run_fluid_gate_cycle  # noqa: E402
from src.judgment.flags import APPLY_ENV, SHADOW_ENV  # noqa: E402
from src.judgment.inventory import collect_live_inventory  # noqa: E402
from src.judgment.p0_hist_prove import (  # noqa: E402
    apply_env_refused,
    fire_1201_cohort,
    stacked_band_row,
    summarize_fire_1201,
)
from src.judgment.p0_shadow_hooks import keep_signature_from_state  # noqa: E402
from src.judgment.s14_tape import gold_state as s14_gold_state  # noqa: E402
from src.judgment.s15_tape import s15_historical_tape_rows  # noqa: E402
from src.judgment.s16_flags import APPLY_ENV as DIG_APPLY_ENV  # noqa: E402
from src.judgment.veto import forbidden_jev_keys_in  # noqa: E402

MIN_STAMPED = 10


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


def _inventory():
    return collect_live_inventory(
        sleeves=("spring", "vss", "metals_core"),
        workers=(f"challenge:{CHALLENGE_LOGIN}",),
        handlers=("shadow_log",),
        include_w7_armed=False,
        include_launcher_workers=False,
    )


def _name_only_keep_probe() -> dict:
    gold = s14_gold_state(
        sleeve="spring",
        symbol="XAUUSD",
        side="long",
        candidate_id=f"challenge:{CHALLENGE_LOGIN}:name-only:spring:long",
        close_ret_1=0.01,
        close_ret_5bar=0.02,
        vol_ratio=1.0,
        htf_slope_norm=0.5,
        mom_20_atr=0.4,
    )
    return keep_signature_from_state(gold)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--score-out", type=Path, default=None)
    parser.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        help="Optional FIRE 1201 Chair receipt JSON (same payload as score fire_1201)",
    )
    args = parser.parse_args(argv)

    gate = apply_env_refused()
    if gate["refused"]:
        sys.stderr.write(
            f"REFUSE: {gate['refuse_reason']}. Chair path is "
            f"{SHADOW_ENV}=1 only — never set {APPLY_ENV} or {DIG_APPLY_ENV}.\n"
        )
        return 2

    inventory = _inventory()
    rows = list(question_bank_rows()) + list(s15_historical_tape_rows())
    stamped = 0
    apply_true = 0
    invented_high = 0
    dispositions: Counter[str] = Counter()
    keep_present = 0
    name_allowlist = 0
    fire_rows: list[dict] = []

    for row in rows:
        gold = row.get("gold_state") if isinstance(row, dict) else None
        if not isinstance(gold, dict):
            continue
        ticket = row.get("ticket")
        subclass = row.get("subclass")
        answers = row.get("system_one_answers")
        # Close Loop subclass wins for FIRE 1201 tickets so S15 bands
        # stack with P0 STATE keep. CF D miss→fs_half is not the residual band.
        s15_sub = None
        if ticket and str(ticket) in TICKET_SUBCLASS:
            s15_sub = TICKET_SUBCLASS[str(ticket)]
        elif subclass:
            s15_sub = str(subclass)
        result = run_fluid_gate_cycle(
            inventory=inventory,
            gold_state=gold,
            s14_answers=answers if isinstance(answers, dict) else None,
            s15_ticket=str(ticket) if ticket else None,
            s15_subclass=s15_sub,
            log_dir=args.log_dir,
            force=args.force,
            stake="sleeve_admit",
        )
        pack = result.warroom_shadow.as_dict() if result.warroom_shadow else {}
        if pack:
            stamped += 1
            if pack.get("apply") is True or (result.apply and result.apply.apply):
                apply_true += 1
            disp = pack.get("conf_gate_band_disposition")
            if disp:
                dispositions[str(disp)] += 1
            sig = pack.get("P0_CFD_SLEEVE_FAMILY_KEEP_SIG") or {}
            if sig.get("present"):
                keep_present += 1
            if sig.get("name_allowlist_used"):
                name_allowlist += 1
            if forbidden_jev_keys_in(pack):
                invented_high += 1
            if fire_1201_cohort(str(ticket) if ticket else None):
                labeled = stacked_band_row(
                    ticket=str(ticket),
                    tape_row=row,
                    pack=pack,
                )
                if labeled:
                    fire_rows.append(labeled)

    name_probe = _name_only_keep_probe()
    order_send = _judgment_has_order_send()
    fire = summarize_fire_1201(fire_rows)
    shadow_on = str(os.environ.get(SHADOW_ENV, "")).strip() in {"1", "true", "yes", "on"}
    score = {
        "schema": "gtos.judgment.p0_warroom_shadow_prove.v1",
        "login": CHALLENGE_LOGIN,
        "chair_enable": f"{SHADOW_ENV}=1",
        "shadow_env_set": shadow_on,
        "force": bool(args.force),
        "apply_env_set": False,
        "dig_apply_env_set": False,
        "n_rows": len(rows),
        "n_stamped": stamped,
        "apply_true": apply_true,
        "n_order_send": order_send,
        "invented_high": invented_high,
        "name_allowlist_used": name_allowlist,
        "keep_present_from_state": keep_present,
        "name_only_spring_keep_present": bool(name_probe.get("present")),
        "dispositions": dict(dispositions),
        "fire_1201": fire,
        "wins_preserved": bool(fire.get("wins_preserved")),
        "residual_shadow_parked": bool(fire.get("residual_shadow_parked")),
        "research_candidate": fire.get("research_candidate"),
        "broker_effect": False,
        "never_place": True,
        "apply": False,
        "pass": bool(
            stamped >= MIN_STAMPED
            and apply_true == 0
            and order_send == 0
            and invented_high == 0
            and name_allowlist == 0
            and name_probe.get("present") is False
            and fire.get("wins_preserved") is True
            and fire.get("residual_shadow_parked") is True
            and (fire.get("research_candidate") or {}).get("hard_off_keep_research") is False
        ),
    }
    text = json.dumps(score, indent=2, sort_keys=True) + "\n"
    if args.score_out:
        args.score_out.parent.mkdir(parents=True, exist_ok=True)
        args.score_out.write_text(text, encoding="utf-8")
    if args.receipt_out:
        args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_out.write_text(
            json.dumps(fire, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    sys.stdout.write(text)
    return 0 if score["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
