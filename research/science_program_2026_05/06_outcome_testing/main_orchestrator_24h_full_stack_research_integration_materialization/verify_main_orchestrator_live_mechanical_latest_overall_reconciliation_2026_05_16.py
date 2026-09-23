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
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_RECONCILIATION_LEDGER_{DATE}.jsonl"
    proof_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_OUTPUT_MANIFEST_{DATE}.json"
    verification_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_VERIFICATION_RESULT_{DATE}.json"

    checks = []
    for path in [ledger_path, proof_path, split_path, summary_path, manifest_path]:
        checks.append(check(f"{path.name}_exists", path.exists(), str(path)))

    ledger = read_jsonl(ledger_path)
    proof = read_jsonl(proof_path)
    splits = read_jsonl(split_path)
    summary = read_json(summary_path)
    manifest = read_json(manifest_path)

    proxy_rows = [row for row in ledger if isinstance(row.get("proxy_r"), (int, float))]
    proxy_values = [float(row["proxy_r"]) for row in proxy_rows]
    proof_ids = {row.get("row_id") for row in proof}

    checks.append(check("route_id_matches", summary.get("route_id") == ROUTE_ID))
    checks.append(check("safe_flags_closed", summary.get("safe_flags") == SAFE_FLAGS))
    checks.append(check("strategy_count_16", summary.get("strategy_count") == 16, summary.get("strategy_count")))
    checks.append(check("latest_overall_rows_4384", len(ledger) == 4384 and summary.get("latest_overall_rows") == 4384, {"ledger": len(ledger), "summary": summary.get("latest_overall_rows")}))
    checks.append(check("numeric_proxy_rows_735", len(proxy_rows) == 735 and summary.get("numeric_proxy_rows") == 735, {"ledger_proxy": len(proxy_rows), "summary": summary.get("numeric_proxy_rows")}))
    checks.append(check("noncomputable_rows_3649", len(proof) == 3649 and summary.get("noncomputable_rows") == 3649, {"proof": len(proof), "summary": summary.get("noncomputable_rows")}))
    checks.append(check("mean_matches_expected_current_disk", round(float(summary.get("proxy_r_summary", {}).get("mean")), 12) == round(0.3224489795918367, 12), summary.get("proxy_r_summary")))
    checks.append(check("computed_mean_matches_summary", round(sum(proxy_values) / len(proxy_values), 12) == round(float(summary.get("proxy_r_summary", {}).get("mean")), 12)))
    checks.append(check("all_rows_no_exact_r", all(row.get("exact_r") is None for row in ledger)))
    checks.append(check("proof_rows_have_no_proxy", all(row.get("proxy_r") is None for row in ledger if row.get("row_id") in proof_ids)))
    checks.append(check("split_rows_nonempty", len(splits) > 0, len(splits)))

    for strategy, expected in {
        "LIVE_AI_J46_J49_BASELINE_COMPARATOR": {"latest_overall_rows": 274, "numeric_proxy_rows": 188, "noncomputable_rows": 86},
        "PENDING_LIMIT_LIFECYCLE": {"latest_overall_rows": 274, "numeric_proxy_rows": 197, "noncomputable_rows": 77},
        "V2_STRUCT_OB_BOUNDARY": {"latest_overall_rows": 274, "numeric_proxy_rows": 175, "noncomputable_rows": 99},
        "V2B_OB_BOUNDARY_PROSPECTIVE": {"latest_overall_rows": 274, "numeric_proxy_rows": 175, "noncomputable_rows": 99},
    }.items():
        actual = summary.get("by_strategy", {}).get(strategy, {})
        checks.append(check(f"{strategy}_counts_match", all(actual.get(k) == v for k, v in expected.items()), actual))

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
            "latest_overall_rows": len(ledger),
            "numeric_proxy_rows": len(proxy_rows),
            "noncomputable_rows": len(proof),
            "split_rows": len(splits),
            "proxy_r_mean": summary.get("proxy_r_summary", {}).get("mean"),
        },
        "can_mark_live_mechanical_latest_overall_reconciliation_plate_complete": ok,
        "can_mark_active_24h_goal_complete": False,
        "safe_flags": SAFE_FLAGS,
    }
    verification_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "verification": str(verification_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
