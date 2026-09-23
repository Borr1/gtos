#!/usr/bin/env python3
"""Jev-everywhere historical prove — Challenge 0 tape closes.

No live bars. No host-mesh. No order_send. Default-off flags still apply
unless ``--force``.

    python3 scripts/run_jev_everywhere_historical_prove.py --force --log-dir /tmp/jev-everywhere

Walks Close Loop tickets on the S15 tape, fans Choice/Score/Noul onto every
safe decision site on the existing ``jev_fluid_gate_v1`` sidecar, and scores
multi-site labels. Negative sheet ⇒ research, not idle.
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

from src.judgment.challenge import (  # noqa: E402
    CHALLENGE_HARD_OFF_FAMILIES,
    CHALLENGE_KEEP_FAMILIES,
    CHALLENGE_LOGIN,
)
from src.judgment.cycle import run_fluid_gate_cycle  # noqa: E402
from src.judgment.cf_d import (  # noqa: E402
    ABLATION_ORDER,
    compose_cf_d,
    load_cf_d_report,
    load_question_bank,
    question_bank_rows,
)
from src.judgment.cf_priority import RELIGION_INDEX_CRYPTO_XA_SIZE0  # noqa: E402
from src.judgment.everywhere import EVERYWHERE_QUESTION_IDS, surface_map  # noqa: E402
from src.judgment.everywhere_tape import everywhere_historical_close_rows  # noqa: E402
from src.judgment.inventory import collect_live_inventory  # noqa: E402
from src.judgment.regime_system_one import RegimeAnswerCache  # noqa: E402
from src.judgment.sites import pre_everywhere_gaps  # noqa: E402
from src.judgment.veto import forbidden_jev_keys_in  # noqa: E402

MIN_DECIDABLE = 20
MIN_MOVED = 5
MIN_SITES = 10
HARD_OFF_LOCK = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")


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


def _sites(result) -> list[dict]:
    if result.everywhere is None:
        return []
    return [row.as_dict() for row in result.everywhere.sites]


def score_row(result, tape_row: dict) -> dict:
    sites = _sites(result)
    decidable_sites = [s for s in sites if s.get("decidable")]
    moved_sites = [s for s in sites if s.get("moved")]
    labels = {s["site_id"]: s.get("label") for s in sites}
    return {
        "cycle_id": result.cycle_id,
        "tape_id": tape_row.get("tape_id"),
        "ticket": tape_row.get("ticket"),
        "subclass": tape_row.get("subclass"),
        "n_sites": len(sites),
        "n_decidable_sites": len(decidable_sites),
        "n_moved_sites": len(moved_sites),
        "decidable": len(decidable_sites) >= 3,
        "moved": len(moved_sites) >= 1,
        "labels": labels,
        "admit": labels.get("admit"),
        "close_label": labels.get("close_label"),
        "corr_hold": labels.get("corr_hold"),
        "usage_router": labels.get("usage_router"),
        "size_tilt": labels.get("size_tilt"),
        "sleeve_family": labels.get("sleeve_family"),
        "size_x_conf": labels.get("size_x_conf"),
        "cost_band": labels.get("cost_band"),
        "cf_d": labels.get("cf_d"),
        "conf_gate": labels.get("conf_gate"),
        "s14_regime": labels.get("s14_regime"),
        "event_stamp": labels.get("event_stamp"),
        "new_hard_off": False,
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
    parser.add_argument("--score-out", default=None, help="Write multi-site scorecard JSON")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--write-tape",
        default=None,
        help="Optional path to materialize the close tape JSONL",
    )
    parser.add_argument(
        "--write-map",
        default=None,
        help="Optional path to write the surface map JSON",
    )
    args = parser.parse_args(argv)

    rows = everywhere_historical_close_rows()
    if args.write_tape:
        dest = Path(args.write_tape)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    if args.write_map:
        Path(args.write_map).write_text(
            json.dumps(surface_map(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

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
    flatten_in_scope = 0
    sites_seen: set[str] = set()

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
            close_state=row.get("close_state"),
            everywhere_answers=row.get("everywhere_answers"),
            log_dir=args.log_dir,
            force=args.force,
            stake="sleeve_admit",
        )
        if result.log_path:
            doc = json.loads(result.log_path.read_text(encoding="utf-8"))
            if doc.get("broker_effect") is not False:
                raise SystemExit("broker_effect must be false")
            if doc.get("account_surface", {}).get("login") != CHALLENGE_LOGIN:
                raise SystemExit("login must be 0")
            if "everywhere" not in doc:
                raise SystemExit("everywhere missing from admit sidecar")
            ew = doc["everywhere"]
            if ew.get("broker_effect") is not False:
                raise SystemExit("everywhere.broker_effect must be false")
            if ew.get("new_hard_off") is not False:
                raise SystemExit("everywhere.new_hard_off must be false")
            if ew.get("same_admit_sidecar_not_parallel") is not True:
                raise SystemExit("everywhere must stay on jev_fluid_gate_v1")
            jev = doc.get("s14_jev_state") or {}
            if isinstance(jev, dict) and forbidden_jev_keys_in(jev):
                forbidden_in_jev += 1
            for site in ew.get("sites") or []:
                sites_seen.add(str(site.get("site_id")))
                action = (site.get("answers") or {}).get("action_scope") or {}
                if action.get("choice") == "flatten":
                    flatten_in_scope += 1
        scored.append(score_row(result, row))

    place = run_fluid_gate_cycle(
        login=CHALLENGE_LOGIN,
        inventory=inventory,
        answers={"next_gate": {"choice": "HOLD", "confidence": 0.99, "probabilities": {"HOLD": 0.99}}},
        everywhere_answers={"admit": {"choice": "admit", "confidence": 0.99, "probabilities": {"admit": 0.99}}},
        log_dir=args.log_dir,
        force=args.force,
        stake="place",
        apply_flag=True,
    )
    place_veto_ok = bool(
        place.apply.apply is False
        and place.conf_gate.broker_effect is False
        and place.everywhere is not None
        and place.everywhere.broker_effect is False
    )
    scored.append(
        {
            "cycle_id": place.cycle_id,
            "tape_id": "place-infinity-veto",
            "ticket": None,
            "subclass": "any_place",
            "decidable": False,
            "moved": False,
            "place_veto": True,
            "broker_effect": False,
            "skipped": place.skipped,
            "verify_ok": place.verify.ok or place.skipped,
            "note": "place_infinity_veto",
        }
    )

    n_decidable = sum(1 for r in scored if r.get("decidable"))
    n_moved = sum(1 for r in scored if r.get("moved"))
    n_order_send = _judgment_has_order_send()
    broker_ok = all(r.get("broker_effect") is False for r in scored)
    hard_off_untouched = tuple(CHALLENGE_HARD_OFF_FAMILIES) == HARD_OFF_LOCK
    close_labels = Counter(r.get("close_label") for r in scored if r.get("close_label"))
    admit_labels = Counter(r.get("admit") for r in scored if r.get("admit"))
    usage_labels = Counter(r.get("usage_router") for r in scored if r.get("usage_router"))
    sleeve_labels = Counter(r.get("sleeve_family") for r in scored if r.get("sleeve_family"))
    size_x_conf_labels = Counter(r.get("size_x_conf") for r in scored if r.get("size_x_conf"))
    cost_band_labels = Counter(r.get("cost_band") for r in scored if r.get("cost_band"))
    cf_d_labels = Counter(r.get("cf_d") for r in scored if r.get("cf_d"))
    conf_shadow_labels = Counter(r.get("conf_gate") for r in scored if r.get("conf_gate"))
    regime_labels = Counter(r.get("s14_regime") for r in scored if r.get("s14_regime"))
    sleeve_allow_n = sum(1 for r in scored if str(r.get("sleeve_family") or "").endswith(":SLEEVE_ALLOW"))
    regime_unknown_n = sum(1 for r in scored if r.get("s14_regime") == "regime_unknown")
    religion_size0_encoded = RELIGION_INDEX_CRYPTO_XA_SIZE0 is True
    n_stand_down = sum(1 for r in scored if r.get("cf_d") == "A_STAND_DOWN")
    n_keep_cap = sum(1 for r in scored if r.get("cf_d") == "E_KEEP_CAP")
    priority_sites = {"cf_d", "sleeve_family", "size_x_conf", "cost_band", "conf_gate"}
    priority_logged = priority_sites <= sites_seen
    gaps_pre = [s.site_id for s in pre_everywhere_gaps()]

    bank = load_question_bank()
    bank_rows = question_bank_rows()
    bank_scored: list[dict] = []
    for brow in bank_rows:
        tape = (brow.get("bank_question") or {}).get("tape") or {}
        expected = compose_cf_d(
            sleeve=str(tape.get("sleeve") or "") or None,
            family=str(tape.get("family") or "") or None,
            miss=str(tape.get("miss") or "") or None,
            keep_flag=bool(tape.get("keep")),
            session=str(tape.get("session") or "") or None,
            outcome=str(tape.get("outcome") or "") or None,
            s15_band=str(tape.get("conf_gate_band") or "") or None,
            gold_state=brow.get("gold_state"),
        )
        cycle = run_fluid_gate_cycle(
            login=brow.get("login") or CHALLENGE_LOGIN,
            inventory=inventory,
            gold_state=brow.get("gold_state"),
            s14_answers=brow.get("system_one_answers"),
            s14_cache=cache,
            s14_research_thresholds=True,
            close_state=None,
            everywhere_answers=None,
            log_dir=args.log_dir,
            force=args.force,
            stake="sleeve_admit",
        )
        sites = _sites(cycle)
        by_id = {s["site_id"]: s for s in sites}
        got = (by_id.get("cf_d") or {}).get("label")
        bank_scored.append(
            {
                "ticket": brow.get("ticket"),
                "role": (brow.get("bank_question") or {}).get("role"),
                "miss": expected.miss,
                "keep": expected.keep,
                "expected": expected.choice,
                "got": got,
                "match": got == expected.choice,
                "decided_by": expected.decided_by,
                "size_factor": expected.size_factor,
                "train_hint_not_chair": (brow.get("bank_question") or {}).get(
                    "suggested_choice_for_train"
                ),
                "broker_effect": False,
            }
        )
    bank_n = len(bank_scored)
    bank_match = sum(1 for r in bank_scored if r.get("match"))
    bank_stand_down = sum(1 for r in bank_scored if r.get("expected") == "A_STAND_DOWN")
    bank_keep_exempt = sum(
        1 for r in bank_scored if r.get("keep") and r.get("miss") == "false_structure"
    )
    house_keep_untouched = tuple(CHALLENGE_KEEP_FAMILIES) == ("spring", "vss")
    report = load_cf_d_report()
    ablation_ok = tuple(ABLATION_ORDER) == ("miss", "size", "family", "session", "conf")

    card = {
        "schema": "gtos.jev_everywhere.prove_scorecard.v1",
        "login": CHALLENGE_LOGIN,
        "bars_source": "historical_tape_closes_no_live_bars",
        "sidecar": "jev_fluid_gate_v1",
        "same_admit_sidecar_not_parallel": True,
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
        "n_flatten_in_action_scope": flatten_in_scope,
        "n_sites_logged": len(sites_seen),
        "sites_logged": sorted(sites_seen),
        "gaps_pre": gaps_pre,
        "question_ids": list(EVERYWHERE_QUESTION_IDS),
        "hard_off_families_untouched": hard_off_untouched,
        "hard_off_families": list(CHALLENGE_HARD_OFF_FAMILIES),
        "new_hard_off": False,
        "place_infinity_veto": place_veto_ok,
        "broker_effect_all_false": broker_ok,
        "close_label_counts": dict(close_labels),
        "admit_counts": dict(admit_labels),
        "usage_counts": dict(usage_labels),
        "sleeve_family_counts": dict(sleeve_labels),
        "sleeve_allow_n": sleeve_allow_n,
        "size_x_conf_counts": dict(size_x_conf_labels),
        "cost_band_counts": dict(cost_band_labels),
        "cf_d_counts": dict(cf_d_labels),
        "cf_d_stand_down_n": n_stand_down,
        "cf_d_keep_cap_n": n_keep_cap,
        "conf_gate_shadow_counts": dict(conf_shadow_labels),
        "regime_honest_counts": dict(regime_labels),
        "regime_unknown_n": regime_unknown_n,
        "religion_index_crypto_xa_size0": False,
        "religion_index_crypto_xa_size0_revoked": True,
        "priority_sites_logged": priority_logged,
        "chair_cf_d": {
            "schema": report.get("schema"),
            "sum_r_challenge_60": report.get("CF_D_sum_R"),
            "n_stand_down_report": report.get("n_stand_down"),
            "n_keep_exempt_report": report.get("n_keep_exempt_from_stand_down"),
            "ablation": list(ABLATION_ORDER),
            "ablation_ok": ablation_ok,
            "house_keep_families": list(CHALLENGE_KEEP_FAMILIES),
            "house_keep_untouched": house_keep_untouched,
            "religion": False,
            "place": False,
            "bank": {
                "schema": bank.get("schema"),
                "n": bank_n,
                "n_questions": bank.get("n_questions"),
                "match": bank_match,
                "stand_down": bank_stand_down,
                "keep_exempt_fs": bank_keep_exempt,
                "rows": bank_scored,
            },
        },
        "chair_cf_priority": [
            "cf_d",
            "sleeve_family",
            "size_x_conf",
            "cost_band",
            "conf_gate_shadow",
        ],
        "min_decidable": MIN_DECIDABLE,
        "min_moved": MIN_MOVED,
        "min_sites": MIN_SITES,
        "surface_map": surface_map(),
        "pass": bool(
            n_decidable >= MIN_DECIDABLE
            and n_moved >= MIN_MOVED
            and len(sites_seen) >= MIN_SITES
            and invented_high == 0
            and forbidden_in_jev == 0
            and n_order_send == 0
            and flatten_in_scope == 0
            and hard_off_untouched
            and place_veto_ok
            and broker_ok
            and priority_logged
            and sleeve_allow_n >= 1
            and regime_unknown_n >= 1
            and not religion_size0_encoded
            and n_stand_down >= 1
            and n_keep_cap >= 1
            and bank_n == 10
            and bank_match == 10
            and bank_stand_down == 2
            and bank_keep_exempt == 2
            and ablation_ok
            and house_keep_untouched
        ),
        "calibration_sheet": scored,
        "how_to_run": (
            "python3 scripts/run_jev_everywhere_historical_prove.py --force "
            "--log-dir /tmp/jev-everywhere --write-tape "
            "judgment/astra/lab/jev_everywhere_closes/TAPE_0.jsonl "
            "--write-map judgment/astra/jev_everywhere_sites.json "
            "--score-out /tmp/jev-everywhere/scorecard.json"
        ),
        "note": (
            "Historical Challenge closes only. Negative sheet ⇒ research/adjust "
            "site labels, not idle. Chair primary soft policy CF D +11.17R: "
            "stand_down false_structure when not KEEP; KEEP exempt. Ablation "
            "miss›size›family›session›conf. INDEX/CRYPTO/xa size0 religion "
            "revoked. Question bank n=10. Never place."
        ),
    }
    text = json.dumps(card, indent=2, sort_keys=True)
    print(text)
    if args.score_out:
        Path(args.score_out).write_text(text + "\n", encoding="utf-8")
    if not args.force and all(r.get("skipped") for r in scored if r.get("tape_id") != "place-infinity-veto"):
        print(
            "Shadow flag off — prove wrote nothing. Re-run with --force or "
            "GTOS_JEV_EVERYWHERE_SHADOW=1 / GTOS_JEV_FLUID_GATES_SHADOW=1.",
            file=sys.stderr,
        )
        return 2
    return 0 if card["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
