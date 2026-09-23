from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line_no"] = line_no
            rows.append(row)
    return rows


def check(name: str, ok: bool, detail: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def main() -> None:
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_VERIFICATION_RESULT_{DATE}.json"

    checks = []
    for path in [ledger_path, split_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    splits = read_jsonl(split_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("duplicate_aware_row_count_545", len(ledger) == 545, len(ledger)))
    checks.append(check("summary_row_count_matches", summary.get("duplicate_aware_numeric_rows") == len(ledger), summary.get("duplicate_aware_numeric_rows")))
    checks.append(check("split_rows_nonempty", len(splits) > 0, len(splits)))
    checks.append(check("strategies_exact", set(summary.get("strategies") or []) == {"LIVE_AI_J46_J49_BASELINE_COMPARATOR", "PENDING_LIMIT_LIFECYCLE"}))
    checks.append(check("mean_matches_expected_current_disk", round(float(summary.get("proxy_r_summary", {}).get("mean")), 12) == round(-0.01651376146788991, 12), summary.get("proxy_r_summary")))
    checks.append(check("baseline_count_273", summary.get("by_strategy", {}).get("LIVE_AI_J46_J49_BASELINE_COMPARATOR", {}).get("count") == 273, summary.get("by_strategy", {}).get("LIVE_AI_J46_J49_BASELINE_COMPARATOR")))
    checks.append(check("pending_count_272", summary.get("by_strategy", {}).get("PENDING_LIMIT_LIFECYCLE", {}).get("count") == 272, summary.get("by_strategy", {}).get("PENDING_LIMIT_LIFECYCLE")))
    checks.append(check("all_rows_no_exact_r", all(row.get("exact_r") is None for row in ledger)))
    checks.append(check("all_rows_have_proxy_r", all(isinstance(row.get("proxy_r"), (int, float)) for row in ledger)))
    checks.append(check("duplicate_policy_recorded", all(row.get("duplicate_policy") == "latest_numeric_proxy_row_per_candidate_id_strategy_id_by_asof_latest_candle_utc" for row in ledger)))

    manifest_errors = []
    for section in ("artifacts", "input_artifacts"):
        for artifact in manifest.get(section, []):
            path = REPO_ROOT / artifact["path"]
            if not path.exists():
                manifest_errors.append({"path": artifact["path"], "error": "missing"})
                continue
            if path.stat().st_size != artifact.get("size_bytes"):
                manifest_errors.append({"path": artifact["path"], "error": "size_mismatch"})
            actual = sha256(path)
            if actual != artifact.get("sha256"):
                manifest_errors.append({"path": artifact["path"], "error": "sha256_mismatch", "actual": actual})
    checks.append(check("manifest_hashes_match", not manifest_errors, manifest_errors))

    ok = all(item["ok"] for item in checks)
    result = {
        "route_id": ROUTE_ID,
        "ok": ok,
        "checks": checks,
        "counts": {
            "duplicate_aware_rows": len(ledger),
            "split_rows": len(splits),
            "proxy_r_mean": summary.get("proxy_r_summary", {}).get("mean"),
        },
        "can_mark_live_baseline_pending_duplicate_aware_replay_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
