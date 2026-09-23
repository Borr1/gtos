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
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_REPLAY_LEDGER_{DATE}.jsonl"
    noncomputable_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_FVG_OB_EXACT_COUNTABLE_VERIFICATION_RESULT_{DATE}.json"

    checks = []
    for path in [ledger_path, noncomputable_path, split_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    noncomputable = read_jsonl(noncomputable_path)
    splits = read_jsonl(split_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    proxy_rows = [row for row in ledger if isinstance(row.get("proxy_r"), (int, float))]
    proxy_values = [float(row["proxy_r"]) for row in proxy_rows]
    computed_mean = sum(proxy_values) / len(proxy_values) if proxy_values else None

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("latest_audit_candidate_count_274", summary.get("all_latest_audit_candidates") == 274, summary.get("all_latest_audit_candidates")))
    checks.append(check("exact_bounds_count_67", summary.get("exact_bounds_captured_rows_all_latest") == 67, summary.get("exact_bounds_captured_rows_all_latest")))
    checks.append(check("duplicate_countable_count_25", summary.get("duplicate_aware_countable_rows_all_latest") == 25, summary.get("duplicate_aware_countable_rows_all_latest")))
    checks.append(check("eligible_union_rows_91", len(ledger) == 91 and summary.get("eligible_union_rows") == 91, {"ledger": len(ledger), "summary": summary.get("eligible_union_rows")}))
    checks.append(check("proxy_rows_66", len(proxy_rows) == 66 and summary.get("proxy_r_rows") == 66, {"ledger_proxy": len(proxy_rows), "summary": summary.get("proxy_r_rows")}))
    checks.append(check("noncomputable_rows_25", len(noncomputable) == 25 and summary.get("noncomputable_rows") == 25, {"noncomputable": len(noncomputable), "summary": summary.get("noncomputable_rows")}))
    checks.append(check("proxy_mean_matches_current_disk", round(float(summary.get("proxy_r_summary", {}).get("mean")), 12) == round(0.3409090909090909, 12), summary.get("proxy_r_summary")))
    checks.append(check("computed_mean_matches_summary", computed_mean is not None and round(computed_mean, 12) == round(float(summary.get("proxy_r_summary", {}).get("mean")), 12), computed_mean))
    checks.append(check("all_rows_no_exact_r", all(row.get("exact_r") is None for row in ledger)))
    checks.append(check("noncomputable_rows_have_no_proxy", all(row.get("proxy_r") is None for row in ledger if row["row_id"] in {item["row_id"] for item in noncomputable})))
    checks.append(check("split_rows_nonempty", len(splits) > 0, len(splits)))

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
            "eligible_union_rows": len(ledger),
            "proxy_r_rows": len(proxy_rows),
            "noncomputable_rows": len(noncomputable),
            "split_rows": len(splits),
            "proxy_r_mean": summary.get("proxy_r_summary", {}).get("mean"),
        },
        "can_mark_fvg_ob_exact_countable_replay_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
