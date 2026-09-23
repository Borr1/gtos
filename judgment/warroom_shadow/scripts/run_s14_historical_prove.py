#!/usr/bin/env python3
"""S14 REGIME_GATE_SHADOW historical prove — Challenge 0 tape.

No live bars. No host-mesh. No order_send. Default-off flags still apply
unless ``--force``.

    python3 scripts/run_s14_historical_prove.py --force --log-dir /tmp/s14-prove

Scorecard bars (PROVE_PLAN): n_decidable ≥ 20, n_moved ≥ 5, n_distinct_gate ≥ 2,
n_invented_high == 0, broker_effect all false, n_order_send == 0.
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
from src.judgment.cycle import run_fluid_gate_cycle  # noqa: E402
from src.judgment.inventory import collect_live_inventory  # noqa: E402
from src.judgment.regime_system_one import RegimeAnswerCache  # noqa: E402
from src.judgment.s14_tape import historical_tape_rows  # noqa: E402
from src.judgment.veto import forbidden_jev_keys_in  # noqa: E402

MIN_DECIDABLE = 20
MIN_MOVED = 5
MIN_DISTINCT = 2


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


def score_row(result, tape_note: str, cache_hit: bool) -> dict:
    regime = result.regime
    gate = None if regime is None else regime.gate_decision
    size = None if regime is None else regime.size_factor
    moved = bool(
        regime
        and regime.decidable
        and not cache_hit
        and gate in {"stand_down", "half_size"}
    )
    return {
        "cycle_id": result.cycle_id,
        "tape_note": tape_note,
        "skipped": result.skipped,
        "decidable": bool(regime and regime.decidable),
        "consume": bool(regime and regime.consume),
        "gate_decision": gate,
        "size_factor": size,
        "moved": moved,
        "cache_hit": cache_hit,
        "broker_effect": False,
        "completion": result.completion,
        "verify_ok": result.verify.ok,
        "log_path": str(result.log_path) if result.log_path else None,
        "reason": None if regime is None else regime.reason,
        "hard_off": bool(regime and regime.chair.hard_off),
        "keep_family": bool(regime and regime.chair.keep_family),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--score-out", default=None, help="Write scorecard JSON")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--write-tape",
        default=None,
        help="Optional path to materialize the historical tape JSONL",
    )
    args = parser.parse_args(argv)

    rows = historical_tape_rows()
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
    seen_cache: set[str] = set()

    for row in rows:
        gold = row["gold_state"]
        news = gold.get("news") or {}
        if news.get("spine_empty") and news.get("events"):
            invented_high += 1
        result = run_fluid_gate_cycle(
            login=row.get("login") or CHALLENGE_LOGIN,
            inventory=inventory,
            gold_state=gold,
            s14_answers=row.get("system_one_answers"),
            s14_cache=cache,
            s14_research_thresholds=True,
            log_dir=args.log_dir,
            force=args.force,
            stake="sleeve_admit",
        )
        cache_key = result.regime.cache_key if result.regime else ""
        cache_hit = bool(cache_key and cache_key in seen_cache)
        if cache_key:
            seen_cache.add(cache_key)
        if result.regime is not None:
            jev = None
            if result.log_path:
                doc = json.loads(result.log_path.read_text(encoding="utf-8"))
                jev = doc.get("s14_jev_state") or {}
                if isinstance(jev, dict) and forbidden_jev_keys_in(jev):
                    forbidden_in_jev += 1
                if doc.get("broker_effect") is not False:
                    raise SystemExit("broker_effect must be false")
                if doc.get("account_surface", {}).get("login") != CHALLENGE_LOGIN:
                    raise SystemExit("login must be 0")
        scored.append(score_row(result, row.get("note") or "", cache_hit or (result.regime.cache_hit if result.regime else False)))

    gates = [r["gate_decision"] for r in scored if r["decidable"] and r["gate_decision"]]
    n_decidable = sum(1 for r in scored if r["decidable"])
    n_moved = sum(1 for r in scored if r["moved"])
    n_distinct = len(set(gates))
    n_order_send = _judgment_has_order_send()
    n_invented = invented_high
    broker_ok = all(r["broker_effect"] is False for r in scored)
    verify_ok = all((not r["decidable"]) or r["verify_ok"] or r["skipped"] for r in scored)

    card = {
        "schema": "gtos.s14.prove_scorecard.v1",
        "login": CHALLENGE_LOGIN,
        "bars_source": "historical_tape_no_live_bars",
        "n_rows": len(scored),
        "n_decidable": n_decidable,
        "n_moved": n_moved,
        "n_distinct_gate": n_distinct,
        "gate_counts": dict(Counter(gates)),
        "n_invented_high": n_invented,
        "n_forbidden_jev_keys": forbidden_in_jev,
        "n_order_send": n_order_send,
        "broker_effect_all_false": broker_ok,
        "done_outside_ok": verify_ok,
        "min_decidable": MIN_DECIDABLE,
        "min_moved": MIN_MOVED,
        "min_distinct": MIN_DISTINCT,
        "pass": bool(
            n_decidable >= MIN_DECIDABLE
            and n_moved >= MIN_MOVED
            and n_distinct >= MIN_DISTINCT
            and n_invented == 0
            and forbidden_in_jev == 0
            and n_order_send == 0
            and broker_ok
        ),
        "rows": scored,
        "how_to_run": (
            "python3 scripts/run_s14_historical_prove.py --force "
            "--log-dir /tmp/s14-prove --write-tape "
            "judgment/astra/lab/s14_historical_tape/TAPE_0.jsonl"
        ),
    }
    text = json.dumps(card, indent=2, sort_keys=True)
    print(text)
    if args.score_out:
        Path(args.score_out).write_text(text + "\n", encoding="utf-8")
    if not args.force and all(r["skipped"] for r in scored):
        print("Shadow flag off — prove wrote nothing. Re-run with --force or GTOS_JEV_FLUID_GATES_SHADOW=1.", file=sys.stderr)
        return 2
    return 0 if card["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
