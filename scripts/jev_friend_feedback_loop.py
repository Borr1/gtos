#!/usr/bin/env python3
"""Friend feedback loop. Log only. Default-off. No place / flatten / agent-place."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.friend_feedback_loop import (  # noqa: E402
    DEFAULT_FIXTURE_DIR,
    LabelStore,
    maybe_run_friend_feedback,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sit",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--from-records",
        action="store_true",
        help="Record the open Challenge fill through one hop. No sit JSON.",
    )
    parser.add_argument("--heartbeat", type=Path, default=None)
    parser.add_argument("--login", default="0")
    parser.add_argument("--namespace", default="operator")
    parser.add_argument(
        "--store",
        type=Path,
        default=ROOT / "judgment/astra/lab/friend_feedback_loop/last_run.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "judgment/astra/lab/friend_feedback_loop/last_run.summary.json",
    )
    args = parser.parse_args()
    sit = None if args.from_records else (
        args.sit if args.sit is not None else DEFAULT_FIXTURE_DIR / "sit_in_system_copy.json"
    )
    pack = maybe_run_friend_feedback(
        sit_path=sit,
        login=args.login,
        namespace=args.namespace,
        heartbeat_path=args.heartbeat,
        store=LabelStore(args.store),
    )
    compact = {
        "schema": pack["schema"],
        "printer": pack.get("printer"),
        "friends": pack.get("friends"),
        "enabled": pack["enabled"],
        "skipped": pack.get("skipped"),
        "fail_closed": pack["fail_closed"],
        "fail_closed_reason": pack.get("fail_closed_reason"),
        "extra_pass": pack["extra_pass"],
        "recommendation_emitted": pack["recommendation_emitted"],
        "apply": pack["apply"],
        "never_place": pack["never_place"],
        "never_agent_place": pack.get("never_agent_place"),
        "never_invent_min_lot": pack.get("never_invent_min_lot"),
        "never_flatten": pack["never_flatten"],
        "never_bounce_challenge": pack.get("never_bounce_challenge"),
        "persist_weight": pack["persist_weight"],
        "pin_window": pack["pin_window"],
        "overlay_77_copied": pack["overlay_77_copied"],
        "n_in_system_copy": pack.get("n_in_system_copy"),
        "n_agent_place": pack.get("n_agent_place"),
        "copy_recommendations": pack.get("copy_recommendations"),
        "recommendations": pack["recommendations"],
        "label_store": pack.get("label_store"),
        "learning_row": pack.get("learning_row"),
        "proved": pack.get("proved"),
        "write": pack.get("write"),
        "decision": pack["decision"],
        "do_not_flatten_tickets": pack["do_not_flatten_tickets"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(compact, indent=2) + "\n", encoding="utf-8")
    print(
        f"printer {pack.get('printer')} enabled {pack['enabled']} "
        f"fail_closed {pack['fail_closed']} extra_pass {pack['extra_pass']} "
        f"apply {pack['apply']} persist {pack['persist_weight']} "
        f"copies {pack.get('n_in_system_copy')} agent_place {pack.get('n_agent_place')} "
        f"choice {(pack.get('learning_row') or {}).get('decision_choice')} "
        f"p {(pack.get('learning_row') or {}).get('decision_probability')}"
    )
    for rec in pack.get("copy_recommendations") or []:
        print(
            f"  {rec.get('action')} {rec.get('name')} "
            f"ok={rec.get('n_ok')} agent_place={rec.get('n_agent_place')}"
        )
    for rec in pack.get("recommendations") or []:
        print(
            f"  {rec.get('action')} {rec.get('sleeve')} "
            f"n={rec.get('n_closes')} size_up={rec.get('size_up')}"
        )
    if pack.get("skipped"):
        print(f"skipped {pack['skipped']}")
    if pack.get("fail_closed"):
        print(f"fail_closed_reason {pack.get('fail_closed_reason')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
