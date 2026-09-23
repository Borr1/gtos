"""Verify the entry-offset 0.50R shadow-scorer output projection."""

from __future__ import annotations

import ast
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
BUILDER = ROUTE_DIR / "build_main_orchestrator_entry_offset_050r_shadow_scorer_outputs_2026_05_16.py"
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_050R_SHADOW_SCORER_OUTPUT_VERIFICATION_RESULT_{DATE}.json"
STRATEGY_ID = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
EXPECTED_STRATEGY_STATUS_COUNTS = {
    "KILLED_ENTRY_OFFSET_050R_NO_FILL": 82,
    "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR": 177,
    "SCORED_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_PROXY": 10,
    "SCORED_ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_DEFAULT_OFF": 3,
    "SOURCE_REPAIR_REQUIRED_TICK_REPLAY_INCOMPLETE": 2,
}
EXPECTED_SCORE_STATUS_COUNTS = {
    "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY": 95,
    "NOT_APPLICABLE": 177,
    "SOURCE_REPAIR_REQUIRED": 2,
}
EXPECTED_OUTCOME_STATUS_COUNTS = {
    "NOT_SCORED": 179,
    "NO_FILL_AT_SHIFT": 82,
    "TP1_AFTER_SHIFT_FILL": 13,
}
EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 3,
    "KEEP": 177,
    "KILL": 82,
    "REDESIGN": 10,
    "SOURCE_REPAIR": 2,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def approx_equal(left: float | None, right: float | None, tol: float = 1e-9) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tol


def assert_ast_parse(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing python artifact: {path.name}")
        return
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        errors.append(f"syntax parse failed for {path.name}: {exc}")


def main() -> None:
    errors: list[str] = []
    for path in [BUILDER, LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            errors.append(f"missing artifact: {path.name}")
    assert_ast_parse(BUILDER, errors)
    assert_ast_parse(Path(__file__), errors)

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != 274:
        errors.append(f"expected 274 scorer rows, got {len(rows)}")
    if summary.get("rows") != len(rows):
        errors.append(f"summary row count mismatch: {summary.get('rows')} vs {len(rows)}")
    if summary.get("candidate_rows") != 274 or len({row.get("candidate_id") for row in rows}) != 274:
        errors.append("candidate denominator must remain 274 unique rows")
    if summary.get("strategy_id") != STRATEGY_ID or any(row.get("strategy_id") != STRATEGY_ID for row in rows):
        errors.append("strategy id mismatch")
    if any(row.get("exact_r") is not None for row in rows) or summary.get("exact_r_rows") != 0:
        errors.append("exact_r must remain unavailable for this proxy scorer output")

    strategy_status_counts = Counter(str(row.get("strategy_status")) for row in rows)
    score_status_counts = Counter(str(row.get("score_status")) for row in rows)
    outcome_status_counts = Counter(str(row.get("outcome_status")) for row in rows)
    action_counts = Counter(str(row.get("action_class")) for row in rows)
    if dict(strategy_status_counts) != EXPECTED_STRATEGY_STATUS_COUNTS:
        errors.append(f"strategy status counts mismatch: {dict(strategy_status_counts)}")
    if summary.get("strategy_status_counts") != EXPECTED_STRATEGY_STATUS_COUNTS:
        errors.append(f"summary strategy status counts mismatch: {summary.get('strategy_status_counts')}")
    if dict(score_status_counts) != EXPECTED_SCORE_STATUS_COUNTS:
        errors.append(f"score status counts mismatch: {dict(score_status_counts)}")
    if summary.get("score_status_counts") != EXPECTED_SCORE_STATUS_COUNTS:
        errors.append(f"summary score status counts mismatch: {summary.get('score_status_counts')}")
    if dict(outcome_status_counts) != EXPECTED_OUTCOME_STATUS_COUNTS:
        errors.append(f"outcome status counts mismatch: {dict(outcome_status_counts)}")
    if summary.get("outcome_status_counts") != EXPECTED_OUTCOME_STATUS_COUNTS:
        errors.append(f"summary outcome status counts mismatch: {summary.get('outcome_status_counts')}")
    if dict(action_counts) != EXPECTED_ACTION_COUNTS:
        errors.append(f"action counts mismatch: {dict(action_counts)}")
    if summary.get("action_class_counts") != EXPECTED_ACTION_COUNTS:
        errors.append(f"summary action counts mismatch: {summary.get('action_class_counts')}")

    numeric = [float(row["strategy_proxy_r"]) for row in rows if safe_float(row.get("strategy_proxy_r")) is not None]
    if len(numeric) != 95 or summary.get("numeric_proxy_rows") != 95:
        errors.append(f"expected 95 numeric scorer proxy rows, got ledger={len(numeric)} summary={summary.get('numeric_proxy_rows')}")
    if not approx_equal(sum(numeric), 8.66977687):
        errors.append(f"proxy R sum mismatch: {sum(numeric)}")
    if not approx_equal(safe_float(summary.get("proxy_r_sum")), 8.66977687):
        errors.append(f"summary proxy R sum mismatch: {summary.get('proxy_r_sum')}")
    if not approx_equal(safe_float(summary.get("proxy_r_mean")), 0.09126080915789474):
        errors.append(f"summary proxy R mean mismatch: {summary.get('proxy_r_mean')}")

    scored_tp = [row for row in rows if row.get("outcome_status") == "TP1_AFTER_SHIFT_FILL"]
    killed_no_fill = [row for row in rows if row.get("strategy_status") == "KILLED_ENTRY_OFFSET_050R_NO_FILL"]
    source_repair = [
        row for row in rows if row.get("strategy_status") == "SOURCE_REPAIR_REQUIRED_TICK_REPLAY_INCOMPLETE"
    ]
    if len(scored_tp) != 13:
        errors.append(f"expected 13 TP-after-fill scorer rows, got {len(scored_tp)}")
    if any(row.get("score_status") != "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY" for row in scored_tp):
        errors.append("TP-after-fill rows must be computed from spread-aware tick replay")
    if len(killed_no_fill) != 82 or any(safe_float(row.get("strategy_proxy_r")) != 0.0 for row in killed_no_fill):
        errors.append("killed 0.50R no-fill rows must be 82 zero-proxy rows")
    if len(source_repair) != 2 or any(row.get("strategy_proxy_r") is not None for row in source_repair):
        errors.append("source repair rows must be two nonnumeric rows")

    if any(row.get("safe_flags") != EXPECTED_SAFE_FLAGS for row in rows):
        errors.append("row safe flags mismatch")
    if summary.get("safe_flags") != EXPECTED_SAFE_FLAGS or manifest.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        errors.append("summary or manifest safe flags mismatch")
    if any(row.get("no_shadow_log_append") is not True for row in rows):
        errors.append("scorer projection must not append to shadow logs")
    if any(row.get("no_live_behavior") is not True for row in rows):
        errors.append("scorer projection must not open live behavior")

    for group_name in ("inputs", "outputs"):
        for name, artifact in (manifest.get(group_name) or {}).items():
            path = Path(str(artifact.get("path") or ""))
            if not path.exists():
                errors.append(f"manifest {group_name} path missing: {name}")
                continue
            if artifact.get("bytes") != path.stat().st_size:
                errors.append(f"manifest byte mismatch: {name}")
            if artifact.get("sha256") != sha256_file(path):
                errors.append(f"manifest hash mismatch: {name}")

    result = {
        "ok": not errors,
        "errors": errors,
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "strategy_id": summary.get("strategy_id"),
        "strategy_status_counts": dict(strategy_status_counts),
        "score_status_counts": dict(score_status_counts),
        "outcome_status_counts": dict(outcome_status_counts),
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": sum(numeric),
        "plate_decision": summary.get("plate_decision"),
        "safe_flags": summary.get("safe_flags"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
