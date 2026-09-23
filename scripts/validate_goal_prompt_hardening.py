#!/usr/bin/env python3
"""Validate GTOS goal-prompt hardening requirements.

This script is intentionally lightweight and local-only. It does not decide
whether a prompt is good, but it catches the common drift classes that weakened
prior goal sessions: missing active context use, weak stop-label pursuit,
arbitrary top-N framing, and boundary language that turns into a conservative
brake.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


ANY_OF_REQUIREMENTS: dict[str, list[str]] = {
    "mandatory_goal_discipline_context": [
        r"goal_session_research_discipline\.md",
    ],
    "mandatory_research_doctrine_context": [
        r"research_operating_doctrine\.md",
    ],
    "no_chat_memory": [
        r"do not rely on chat memory",
        r"no chat[- ]memory",
    ],
    "literal_impossibility_full_pursuit": [
        r"full same[- ]evidence[- ]class pursuit",
        r"literal impossibility means exactly",
        r"every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action",
    ],
    "same_evidence_class_pursuit": [
        r"same[- ]evidence[- ]class",
        r"same[- ]class",
    ],
    "non_conservative_builder_posture": [
        r"no conservative brake",
        r"not conservative",
        r"constructive",
        r"curiosity",
        r"active creativity",
    ],
    "active_context_embedding": [
        r"active instructions",
        r"not background",
        r"operationalize",
        r"instruction[- ]coverage",
    ],
    "completion_audit": [
        r"completion audit",
        r"completion_audit",
    ],
    "verifier_or_tests": [
        r"verifier",
        r"focused test",
        r"pytest",
    ],
    "artifact_outputs": [
        r"ledger",
        r"manifest",
        r"artifact",
    ],
}

ALL_OF_REQUIREMENTS: dict[str, list[str]] = {
    "result_materialization_standard_present": [
        r"result[-_ ]use[-_ ]status|result materialization|exact[- ]?R|proxy[- ]?R|expectancy",
        r"source[-/ ]capture|source completeness|branch decision|implementation decision",
    ],
    "forbidden_surfaces_core_present": [
        r"\bproduction[- ]change\b|\blive trading\b|\bbroker operation\b",
        r"\bpaid\b|\bapi\b|\bvendor\b",
        r"\bbroker\b|\baccount\b|\border\b|\bhistory\b|\bdeal\b|\bposition\b",
        r"\bprompt\b|\bconfig\b|\brisk\b|\bexecution\b|\bsafety\b|\bcanary\b|\bselector\b",
    ],
    "no_arbitrary_top_n": [
        r"no arbitrary top[- ]?n|no top[- ]?n|top\s*3/5/10|number[- ]limited cutoff",
        r"full ledger|all material rows|preserve all",
    ],
}


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def validate_prompt(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    checks: dict[str, bool] = {
        name: _matches_any(text, patterns) for name, patterns in ANY_OF_REQUIREMENTS.items()
    }
    for name, patterns in ALL_OF_REQUIREMENTS.items():
        checks[name] = all(
            re.search(pattern, text, flags=re.IGNORECASE) is not None
            for pattern in patterns
        )
    missing = [name for name, passed in checks.items() if not passed]
    return {
        "path": str(path),
        "ok": not missing,
        "missing": missing,
        "checks": checks,
        "line_count": text.count("\n") + 1 if text else 0,
        "char_count": len(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Prompt markdown/txt files to validate")
    parser.add_argument(
        "--kind",
        choices=("builder", "g0", "g12", "starter", "terminal"),
        default="builder",
        help=(
            "Prompt kind for reporting. The current control set is intentionally "
            "strict across kinds, but this label is emitted for launch-board records."
        ),
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return exit code 0 even when hardening checks are missing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    args = parser.parse_args()

    results = [validate_prompt(Path(raw)) | {"kind": args.kind} for raw in args.paths]
    all_ok = all(bool(result["ok"]) for result in results)

    if args.json:
        print(json.dumps({"ok": all_ok, "results": results}, indent=2, sort_keys=True))
    else:
        for result in results:
            status = "PASS" if result["ok"] else "FAIL"
            print(f"{status} {result['path']}")
            if result["missing"]:
                for missing in result["missing"]:
                    print(f"  missing: {missing}")
        print(f"overall_ok={all_ok}")

    return 0 if all_ok or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
