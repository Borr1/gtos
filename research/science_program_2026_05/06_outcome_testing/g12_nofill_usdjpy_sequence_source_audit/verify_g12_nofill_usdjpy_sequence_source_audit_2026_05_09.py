"""Verify G12 USDJPY quote-event sequence source audit artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION = "NO_PROMOTION_VERDICT"
TERMINAL_G12_VERDICT = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
TARGET_ROWS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repo root")


REPO_ROOT = find_repo_root()
ROUTE_DIR = Path(__file__).resolve().parent

REQUIRED = [
    f"G12_NOFILL_USDJPY_SEQ_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_{DATE}.json",
    f"G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_{DATE}.json",
    f"G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_{DATE}.json",
    f"G12_NOFILL_USDJPY_SEQ_EXTERNAL_ACCESS_REQUEST_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.md",
    f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json",
    "build_g12_nofill_usdjpy_sequence_source_audit_2026_05_09.py",
    "verify_g12_nofill_usdjpy_sequence_source_audit_2026_05_09.py",
    "test_g12_nofill_usdjpy_sequence_source_audit_2026_05_09.py",
]


def load_json(name: str) -> Any:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
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


def verify() -> dict[str, Any]:
    issues: list[str] = []
    missing = [name for name in REQUIRED if not (ROUTE_DIR / name).exists()]
    if missing:
        issues.append(f"missing_required_artifacts:{missing}")

    source_search = load_json(f"G12_NOFILL_USDJPY_SEQ_SOURCE_SEARCH_REAUDIT_{DATE}.json")
    hash_audit = load_json(f"G12_NOFILL_USDJPY_SEQ_SOURCE_HASH_AUDIT_{DATE}.json")
    noleak = load_json(f"G12_NOFILL_USDJPY_SEQ_NO_LEAK_DENOMINATOR_AUDIT_{DATE}.json")
    completion = load_json(f"G12_NOFILL_USDJPY_SEQ_COMPLETION_AUDIT_{DATE}.json")
    decision_md = (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_{DATE}.md").read_text(encoding="utf-8")
    mql_md = (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_MQL5_SOURCE_CONTRACT_AUDIT_{DATE}.md").read_text(encoding="utf-8")

    row_ids = {row.get("packet_row_id") for row in source_search.get("row_reaudits", [])}
    if row_ids != TARGET_ROWS:
        issues.append(f"target_row_mismatch:{sorted(row_ids)}")

    checks = source_search.get("central_claim_checks", {})
    expected_true = [
        "all_four_rows_reconstructed",
        "all_decisive_timestamps_single_snapshot",
        "all_single_rows_simultaneously_entry_and_protective",
    ]
    for key in expected_true:
        if checks.get(key) is not True:
            issues.append(f"central_claim_false:{key}")
    if checks.get("any_sequence_or_subrow_field_found") is not False:
        issues.append("sequence_or_subrow_field_found")
    if checks.get("source_access_lane_missed_source_safe_route") is not False:
        issues.append("missed_source_safe_route_not_false")
    if source_search.get("terminal_g12_verdict") != TERMINAL_G12_VERDICT:
        issues.append("terminal_verdict_mismatch")
    if source_search.get("source_search_conclusion") != "NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND":
        issues.append("source_search_conclusion_mismatch")

    for row in source_search.get("row_reaudits", []):
        if row.get("exact_timestamp_row_count") != 1:
            issues.append(f"row_count_not_one:{row.get('packet_row_id')}")
        if row.get("sequence_or_subrow_field_found") is not False:
            issues.append(f"sequence_field_on_row:{row.get('packet_row_id')}")
        if row.get("single_broker_snapshot_with_simultaneous_predicates") is not True:
            issues.append(f"simultaneous_predicates_missing:{row.get('packet_row_id')}")
        if row.get("promotion_verdict") != PROMOTION:
            issues.append(f"promotion_missing_on_row:{row.get('packet_row_id')}")
        if row.get("validation_safe") is not False or row.get("outcome_review_opened") is not False or row.get("live_effect") is not False:
            issues.append(f"unsafe_row_flag:{row.get('packet_row_id')}")

    if hash_audit.get("strict_hash_failures"):
        issues.append(f"recorded_hash_failures:{hash_audit.get('strict_hash_failures')}")
    recompute_failures = []
    for rec in hash_audit.get("records", []):
        if not rec.get("strict_hash"):
            continue
        path = Path(rec["path"])
        if not path.exists():
            recompute_failures.append({"path": str(path), "reason": "missing"})
            continue
        actual = sha256_file(path)
        if actual != rec.get("sha256"):
            recompute_failures.append({"path": str(path), "expected": rec.get("sha256"), "actual": actual})
    if recompute_failures:
        issues.append(f"recompute_hash_failures:{recompute_failures}")

    if noleak.get("accepted_denominator_movement") != 0:
        issues.append("accepted_denominator_moved")
    if noleak.get("source_safe_input_only_rows") != 0:
        issues.append("source_safe_input_rows_nonzero")
    if noleak.get("all_target_rows_in_source_impossible_exclusion_set") is not True:
        issues.append("target_rows_not_all_excluded_source_impossible")
    if any(noleak.get("unsafe_flag_hits", {}).values()):
        issues.append(f"unsafe_flag_hits:{noleak.get('unsafe_flag_hits')}")
    if noleak.get("forbidden_json_key_hits"):
        issues.append(f"forbidden_json_key_hits:{noleak.get('forbidden_json_key_hits')}")

    if completion.get("can_mark_goal_complete") is not True:
        issues.append("completion_audit_not_complete")
    if completion.get("missing_or_weak_requirements"):
        issues.append(f"completion_missing_or_weak:{completion.get('missing_or_weak_requirements')}")
    for payload_name, payload in [
        ("source_search", source_search),
        ("hash_audit", hash_audit),
        ("noleak", noleak),
        ("completion", completion),
    ]:
        if payload.get("promotion_verdict") != PROMOTION:
            issues.append(f"promotion_missing:{payload_name}")
        if payload.get("validation_safe") is not False or payload.get("outcome_review_opened") is not False or payload.get("live_effect") is not False:
            issues.append(f"unsafe_flags:{payload_name}")

    for name in REQUIRED:
        path = ROUTE_DIR / name
        if path.exists() and PROMOTION not in path.read_text(encoding="utf-8", errors="replace"):
            issues.append(f"artifact_missing_promotion_verdict:{name}")
    artifact_names = [name for name in REQUIRED if not name.endswith(".py")]
    generated_text = "\n".join((ROUTE_DIR / name).read_text(encoding="utf-8", errors="replace") for name in artifact_names if (ROUTE_DIR / name).exists())
    if '"validation_safe": true' in generated_text or "`validation_safe=true`" in generated_text:
        issues.append("validation_safe_true_text_found")
    if '"outcome_review_opened": true' in generated_text or "`outcome_review_opened=true`" in generated_text:
        issues.append("outcome_review_opened_true_text_found")
    if '"live_effect": true' in generated_text or "`live_effect=true`" in generated_text:
        issues.append("live_effect_true_text_found")

    if TERMINAL_G12_VERDICT not in decision_md:
        issues.append("decision_ledger_missing_terminal_verdict")
    if "PASS_SOURCE_CONTRACT_LIMIT_CONFIRMED" not in mql_md or "time_msc" not in mql_md:
        issues.append("mql_contract_md_missing_expected_terms")

    allowed_prefixes = [
        "research/science_program_2026_05/06_outcome_testing/g12_nofill_usdjpy_sequence_source_audit/",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    ]
    forbidden_prefixes = [
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "scripts/mt5",
        "run_agent.py",
        "start_all.bat",
        "knowledge_base/",
    ]
    dirty_paths = [p.replace("\\", "/") for p in git_status_paths()]
    forbidden_dirty = [
        p
        for p in dirty_paths
        if any(p.startswith(prefix) for prefix in forbidden_prefixes)
        and not any(p.startswith(prefix) for prefix in allowed_prefixes)
    ]
    if forbidden_dirty:
        issues.append(f"forbidden_dirty_paths:{forbidden_dirty}")

    result = {
        "artifact_family": "G12_NOFILL_USDJPY_SEQ_VERIFICATION",
        "ok": not issues,
        "issues": issues,
        "target_rows": sorted(TARGET_ROWS),
        "terminal_g12_verdict": source_search.get("terminal_g12_verdict"),
        "source_search_conclusion": source_search.get("source_search_conclusion"),
        "strict_hash_record_count": hash_audit.get("strict_hash_record_count"),
        "forbidden_dirty_paths": forbidden_dirty,
        "workspace_dirty_policy": "only audit route, research_current_state, and LIVE_STATE are permitted dirty surfaces",
        "can_mark_goal_complete": not issues,
    }
    (ROUTE_DIR / f"G12_NOFILL_USDJPY_SEQ_VERIFICATION_{DATE}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
