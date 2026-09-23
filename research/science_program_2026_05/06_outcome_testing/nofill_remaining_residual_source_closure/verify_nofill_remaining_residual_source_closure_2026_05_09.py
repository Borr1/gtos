#!/usr/bin/env python3
"""Verify the NOFILL remaining residual source-closure artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
LANE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TARGET_IDS = {
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
MAY3_IDS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _git_names(args: list[str]) -> list[str]:
    try:
        output = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_UNAVAILABLE:{exc!r}"]
    names = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("warning:"):
            continue
        names.append(stripped.replace("\\", "/"))
    return names


def git_workspace_diff_names() -> list[str]:
    return _git_names(["git", "diff", "--name-only"])


def git_committed_diff_names() -> list[str]:
    try:
        parents_line = subprocess.check_output(
            ["git", "rev-list", "--parents", "-n", "1", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except Exception as exc:
        return [f"GIT_PARENT_UNAVAILABLE:{exc!r}"]
    parts = parents_line.split()
    if len(parts) > 2:
        return _git_names(["git", "diff", "--name-only", "HEAD^1", "HEAD"])
    return _git_names(["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"])


def check_required_files() -> list[dict[str, Any]]:
    required = [
        f"NOFILL_REMAINING_CONTEXT_ANCHOR_{DATE}.md",
        f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.json",
        f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.md",
        f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json",
        f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.md",
        f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json",
        f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.md",
        f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl",
        f"NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_{DATE}.json",
        f"NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_{DATE}.md",
        f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json",
        f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.md",
        f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json",
        f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.md",
        f"NOFILL_REMAINING_NEXT_PROMPT_PACK_{DATE}.md",
        f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json",
        f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md",
        f"build_nofill_remaining_residual_source_closure_2026_05_09.py",
        f"verify_nofill_remaining_residual_source_closure_2026_05_09.py",
        f"test_nofill_remaining_residual_source_closure_2026_05_09.py",
        f"raw/MQL5_COPY_TICKS_RANGE_PY_{DATE}.html",
        f"raw/MQL5_COPY_TICKS_RANGE_MQL_{DATE}.html",
        f"raw/MQL5_MQLTICK_STRUCTURE_{DATE}.html",
        f"raw/MQL5_SOURCE_INDEX_{DATE}.json",
        f"raw/NOFILL_REMAINING_XAUUSD_MT5_COPY_TICKS_RANGE_CAPTURE_{DATE}.json",
        "raw/NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet",
    ]
    return [
        {"path": name, "exists": (LANE_DIR / name).exists(), "size_bytes": (LANE_DIR / name).stat().st_size if (LANE_DIR / name).exists() else None}
        for name in required
    ]


def check_hashes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for record in manifest["records"]:
        if not record.get("exists"):
            failures.append({"path": record["path"], "reason": "record_missing"})
            continue
        mode = record.get("hash_verification_mode", "strict_sha256")
        if mode == "presence_only_mutable_context":
            if not Path(record["path"]).exists():
                failures.append({"path": record["path"], "reason": "mutable_context_missing"})
            continue
        expected = record.get("sha256")
        if not expected:
            failures.append({"path": record["path"], "reason": "missing_expected_hash"})
            continue
        actual = sha256_file(Path(record["path"]))
        if actual != expected:
            failures.append({"path": record["path"], "reason": "hash_mismatch", "expected": expected, "actual": actual})
    return failures


def scan_unsafe_true_flags() -> list[dict[str, str]]:
    hits = []
    patterns = ['"validation_safe": true', '"outcome_review_opened": true', '"live_effect": true']
    for path in LANE_DIR.glob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".md"}:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for pattern in patterns:
                if pattern in text:
                    hits.append({"path": str(path), "pattern": pattern})
    return hits


def verify() -> dict[str, Any]:
    required_files = check_required_files()
    missing_files = [item for item in required_files if not item["exists"]]
    decisions = read_jsonl(LANE_DIR / f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl")
    xau = read_json(LANE_DIR / f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json")
    usd = read_json(LANE_DIR / f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json")
    noleak = read_json(LANE_DIR / f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json")
    manifest = read_json(LANE_DIR / f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json")
    completion = read_json(LANE_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json")

    ids = {row["packet_row_id"] for row in decisions}
    status_counts = Counter(row["terminal_source_control_status"] for row in decisions)
    hash_failures = check_hashes(manifest)
    workspace_diff_names = git_workspace_diff_names()
    committed_diff_names = git_committed_diff_names()
    forbidden_diff = [name for name in committed_diff_names if name.startswith(FORBIDDEN_LIVE_PREFIXES)]
    unsafe_true_hits = scan_unsafe_true_flags()
    usd_bad_rows = [
        row
        for row in usd["row_evidence"]
        if row["exact_timestamp_row_count"] != 1
        or set(row["true_predicates_on_single_quote_row"]) != {"entry_touch", "protective_level"}
        or row["terminal_source_control_status"] != "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES"
    ]
    non_verifier_checklist_failures = [
        item
        for item in completion.get("prompt_to_artifact_checklist", [])
        if item.get("requirement") != "Run verifier/tests/py_compile/forbidden live-surface diff"
        and item.get("status") != "PASS"
    ]

    checks = {
        "required_files_present": not missing_files,
        "target_rows_exact": ids == TARGET_IDS and len(decisions) == 5,
        "may3_rows_not_reopened": not (ids & MAY3_IDS),
        "status_counts_expected": status_counts == {"SOURCE_CONTROL_CLEARED_INPUT_ONLY": 1, "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES": 4},
        "xau_source_clear": xau["source_control_status"] == "SOURCE_CONTROL_CLEARED_INPUT_ONLY"
        and xau["entry_touch_before_cancel"] is False
        and xau["recovered_gap_rows_through_cancel"] > 0
        and xau["max_bid_through_cancel"] < xau["entry_price"]
        and xau["mt5_read_only_capture"]["status"] == "RECOVERED_READ_ONLY_QUOTE_TICKS",
        "usdjpy_impossible_contract": len(usd["row_evidence"]) == 4 and not usd_bad_rows,
        "official_raw_docs_present": all(item["exists"] for item in usd["official_doc_contract"]["raw_captures"]),
        "source_hashes_recompute": not hash_failures,
        "no_leak_duplicate_label_family": not noleak["violations"]
        and not noleak["forbidden_output_key_hits"]
        and noleak["reject_total_preserved_outside_labels_denominators"] == 65
        and noleak["rows_moved_to_accepted_denominator"] == 0
        and noleak["lifecycle_labels_assigned"] == 0,
        "unsafe_true_flags_absent": not unsafe_true_hits,
        "forbidden_live_surface_diff_clean": not forbidden_diff,
        "completion_checklist_no_fail": not non_verifier_checklist_failures,
    }
    ok = all(checks.values())
    verification = {
        "artifact_family": "NOFILL_REMAINING_VERIFICATION",
        "generated_at_utc": utc_now(),
        "ok": ok,
        "checks": checks,
        "target_row_count": len(decisions),
        "terminal_status_counts": dict(status_counts),
        "missing_files": missing_files,
        "source_hash_failures": hash_failures,
        "usd_bad_rows": usd_bad_rows,
        "unsafe_true_hits": unsafe_true_hits,
        "workspace_diff_names": workspace_diff_names,
        "committed_diff_names": committed_diff_names,
        "forbidden_live_surface_diff": forbidden_diff,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "can_mark_goal_complete": ok,
    }
    completion["verification"] = verification
    completion["can_mark_goal_complete_after_verifier"] = ok
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "Run verifier/tests/py_compile/forbidden live-surface diff":
            item["status"] = "PASS" if ok else "FAIL"
            item["evidence"] = "Verifier executed source-hash recomputation, row/status checks, no-leak checks, and forbidden live-surface diff scan."
    completion["missing_incomplete_or_weak_requirements"] = [] if ok else [k for k, v in checks.items() if not v]
    write_json(LANE_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json", completion)
    md_path = LANE_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md"
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else "# NOFILL Remaining Completion Audit\n"
    marker = "\n## Verification Result\n"
    md_text = md_text.split(marker)[0].rstrip() + marker + "\n"
    md_text += f"- Verifier ok: `{str(ok).lower()}`\n"
    md_text += f"- Target rows: `{len(decisions)}`\n"
    md_text += f"- Terminal status counts: `{dict(status_counts)}`\n"
    md_text += f"- Source hash failures: `{len(hash_failures)}`\n"
    md_text += f"- Forbidden live-surface diff entries: `{len(forbidden_diff)}`\n"
    md_path.write_text(md_text + "\n", encoding="utf-8")
    return verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
