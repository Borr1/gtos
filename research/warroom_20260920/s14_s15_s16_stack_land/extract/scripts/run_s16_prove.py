#!/usr/bin/env python3
"""S16 MULTI_STAGE_GUARD offline prove — Dig/Chair fixtures only.

No network. No host-mesh. No place / broker / order_send. APPLY stays off.

    python3 scripts/run_s16_prove.py --offline --jev-fixture-mode --shadow \
      --no-place --no-host-mesh --no-network \
      --fixtures judgment/astra/lab/s16_prove_fixtures \
      --score-out /tmp/s16-prove/scorecard.json

Scorecard bars (PROVE_PLAN): decidable ≥ 20, moved ≥ 5, broker_tools = 0,
failMode_open_on_write = 0, heuristics_clears_jev_block = 0,
confidence_as_permission = 0, invented_high_forbidden, place_path_untouched.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.judgment.s16_flags import (  # noqa: E402
    APPLY_ENV,
    SHADOW_ENV,
    default_s16_fixtures_dir,
    s16_apply_enabled,
)
from src.judgment.s16_fixtures import run_prove_pack  # noqa: E402
from src.judgment.s16_guard import DIG_PACK_PATHS, is_forbidden_dig_tool  # noqa: E402


def _judgment_has_order_send() -> int:
    banned = ("order_send", "open_trade")
    count = 0
    for path in (REPO / "src" / "judgment").glob("s16_*.py"):
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


def _s16_imports_admit_sidecar() -> int:
    banned = ("cycle", "conf_gate", "regime_gate", "regime_compose", "s15_tape", "s14_tape")
    count = 0
    for path in (REPO / "src" / "judgment").glob("s16_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.judgment"):
                mod = node.module or ""
                if any(mod.endswith(f".{name}") or mod.endswith(name) for name in banned):
                    count += 1
            if isinstance(node, ast.ImportFrom) and node.module in {None, ".", ".."}:
                names = {alias.name for alias in node.names}
                if names & set(banned):
                    count += 1
    return count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", default=str(default_s16_fixtures_dir()), help="Offline fixture directory")
    parser.add_argument("--log-dir", default="", help="Shadow log directory (optional)")
    parser.add_argument("--score-out", default="", help="Write scorecard JSON here")
    parser.add_argument("--offline", action="store_true", default=True)
    parser.add_argument("--jev-fixture-mode", action="store_true", default=True)
    parser.add_argument("--shadow", action="store_true", help="Write S16 shadow rows (still not APPLY)")
    parser.add_argument("--force", action="store_true", help="Alias for --shadow")
    parser.add_argument("--no-place", action="store_true", default=True)
    parser.add_argument("--no-host-mesh", action="store_true", default=True)
    parser.add_argument("--no-network", action="store_true", default=True)
    parser.add_argument("--no-coverage", action="store_true", help="Official 8 fixtures only (bars may fail)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if s16_apply_enabled():
        print(f"{APPLY_ENV} is on — prove refuses APPLY. Unset it.", file=sys.stderr)
        return 2
    if not args.no_place or not args.no_host-mesh or not args.no_network or not args.offline:
        print("Prove walls: --offline --no-place --no-host-mesh --no-network are required.", file=sys.stderr)
        return 2

    force = bool(args.shadow or args.force)
    log_dir = Path(args.log_dir) if args.log_dir else None
    with tempfile.TemporaryDirectory(prefix="s16-prove-") as tmp:
        card_obj = run_prove_pack(
            args.fixtures,
            tmp=Path(tmp),
            log_dir=log_dir,
            include_coverage=not args.no_coverage,
            force_shadow=force,
        )
    card = card_obj.as_dict()
    card["n_order_send"] = _judgment_has_order_send()
    card["admit_sidecar_imports"] = _s16_imports_admit_sidecar()
    card["pass"] = bool(
        card["pass"]
        and card["n_order_send"] == 0
        and card["admit_sidecar_imports"] == 0
        and not any(is_forbidden_dig_tool(str(row.get("id"))) for row in card["rows"])
    )
    card["how_to_run"] = (
        "python3 scripts/run_s16_prove.py --offline --jev-fixture-mode --shadow "
        "--no-place --no-host-mesh --no-network "
        "--fixtures judgment/astra/lab/s16_prove_fixtures "
        "--score-out /tmp/s16-prove/scorecard.json"
    )
    card["dig_pack"] = list(DIG_PACK_PATHS)
    text = json.dumps(card, indent=2, sort_keys=True)
    print(text)
    if args.score_out:
        out = Path(args.score_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    if not force:
        print(
            f"Shadow flag off — prove computed fixtures but wrote no logs. "
            f"Re-run with --shadow or {SHADOW_ENV}=1.",
            file=sys.stderr,
        )
    return 0 if card["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
