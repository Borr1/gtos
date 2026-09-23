"""Verify NOFILL USDJPY quote-event sequence source-access artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


TARGET_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
DATE = "2026-05-09"
PROMOTION = "NO_PROMOTION_VERDICT"


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent

REQUIRED = [
    f"NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_TARGET_ROW_RECONSTRUCTION_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json",
    f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json",
    f"NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.jsonl",
    f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.json",
    f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_ACCESS_REQUEST_OR_IMPOSSIBILITY_LEDGER_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.md",
    f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status_paths() -> list[str]:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    paths = []
    for line in out.splitlines():
        if line.strip():
            paths.append(line[3:].strip() if len(line) > 3 else line.strip())
    return paths


def git_committed_paths() -> list[str]:
    try:
        out = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def verify() -> dict[str, Any]:
    issues: list[str] = []
    missing = [name for name in REQUIRED if not (ROUTE_DIR / name).exists()]
    if missing:
        issues.append(f"missing_required_artifacts:{missing}")

    source_ledger = load_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_SEARCH_LEDGER_{DATE}.json")
    proof = load_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_EVENT_ORDER_PROOF_PACKET_{DATE}.json")
    decisions = load_jsonl(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.jsonl")
    manifest = load_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_SOURCE_HASH_MANIFEST_{DATE}.json")
    noleak = load_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_NO_LEAK_AND_DUPLICATE_AUDIT_{DATE}.json")
    completion = load_json(ROUTE_DIR / f"NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json")

    decision_ids = {row.get("packet_row_id") for row in decisions}
    proof_ids = {row.get("packet_row_id") for row in proof.get("row_proofs", [])}
    if decision_ids != TARGET_ROWS:
        issues.append(f"decision_target_mismatch:{sorted(decision_ids)}")
    if proof_ids != TARGET_ROWS:
        issues.append(f"proof_target_mismatch:{sorted(proof_ids)}")

    for row in decisions:
        if row.get("terminal_decision") != "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES":
            issues.append(f"unexpected_terminal_decision:{row.get('packet_row_id')}:{row.get('terminal_decision')}")
        if row.get("promotion_verdict") != PROMOTION:
            issues.append(f"promotion_missing:{row.get('packet_row_id')}")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False:
            issues.append(f"unsafe_flag:{row.get('packet_row_id')}")
        if row.get("source_safe_input_only") is not False:
            issues.append(f"source_safe_input_only_should_be_false:{row.get('packet_row_id')}")

    for row in proof.get("row_proofs", []):
        if row.get("exact_timestamp_row_count") != 1:
            issues.append(f"exact_row_count_not_one:{row.get('packet_row_id')}")
        preds = set(row.get("simultaneous_predicates_on_first_row", []))
        if preds != {"entry_touch", "protective_level"}:
            issues.append(f"predicate_set_unexpected:{row.get('packet_row_id')}:{sorted(preds)}")
        precision = row.get("timestamp_precision", {})
        if precision.get("sequence_like_columns"):
            issues.append(f"sequence_like_columns_present:{row.get('packet_row_id')}:{precision.get('sequence_like_columns')}")

    if source_ledger.get("source_search_conclusion") != "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND":
        issues.append("source_search_conclusion_not_negative")
    if proof.get("official_source_contract", {}).get("facts", {}).get("sub_row_sequence_field_found") is not False:
        issues.append("official_contract_sequence_field_not_false")
    if completion.get("can_mark_goal_complete") is not True:
        issues.append("completion_audit_not_complete")
    if noleak.get("forbidden_key_hits"):
        issues.append(f"forbidden_key_hits:{noleak.get('forbidden_key_hits')}")
    if any(noleak.get("unsafe_flag_hits", {}).values()):
        issues.append(f"unsafe_flag_hits:{noleak.get('unsafe_flag_hits')}")

    hash_failures = []
    for rec in manifest.get("records", []):
        if not rec.get("strict_hash"):
            continue
        path = Path(rec["path"])
        if not path.exists():
            hash_failures.append({"path": str(path), "reason": "missing"})
            continue
        actual = sha256_file(path)
        if actual != rec.get("sha256"):
            hash_failures.append({"path": str(path), "expected": rec.get("sha256"), "actual": actual})
    if hash_failures:
        issues.append(f"hash_failures:{hash_failures}")

    committed_paths = git_committed_paths()
    allowed_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/",
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
    ]
    forbidden_prefixes = [
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "scripts/mt5",
        "run_agent.py",
        "start_all.bat",
    ]
    forbidden_dirty = [
        p for p in committed_paths
        if any(p.replace("\\", "/").startswith(prefix) for prefix in forbidden_prefixes)
        and not any(p.replace("\\", "/").startswith(prefix) for prefix in allowed_prefixes)
    ]
    if forbidden_dirty:
        issues.append(f"forbidden_committed_paths:{forbidden_dirty}")

    result = {
        "artifact_family": "NOFILL_USDJPY_SEQ_VERIFICATION",
        "ok": not issues,
        "issues": issues,
        "target_rows": sorted(TARGET_ROWS),
        "decision_rows": len(decisions),
        "strict_hash_records": manifest.get("strict_hash_record_count"),
        "source_search_conclusion": source_ledger.get("source_search_conclusion"),
        "forbidden_dirty_paths": forbidden_dirty,
        "workspace_dirty_policy": "unrelated_workspace_dirt_is_informational",
        "can_mark_goal_complete": not issues,
    }
    out_path = ROUTE_DIR / f"NOFILL_USDJPY_SEQ_VERIFICATION_{DATE}.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
