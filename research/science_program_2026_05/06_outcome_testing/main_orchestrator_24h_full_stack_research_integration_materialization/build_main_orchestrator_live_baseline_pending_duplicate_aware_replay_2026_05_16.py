from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
INPUT = Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl")
STRATEGIES = {"LIVE_AI_J46_J49_BASELINE_COMPARATOR", "PENDING_LIMIT_LIFECYCLE"}
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


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_utc(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iter_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
    return rows


def stable_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "positive": 0, "negative": 0, "zero": 0, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "positive": sum(1 for value in values if value > 0),
        "negative": sum(1 for value in values if value < 0),
        "zero": sum(1 for value in values if value == 0),
        "min": min(values),
        "max": max(values),
    }


def latest_numeric_rows() -> tuple[list[dict[str, Any]], int, int]:
    input_path = REPO_ROOT / INPUT
    raw_seen = 0
    numeric_rows: list[dict[str, Any]] = []
    for line_no, row in iter_jsonl(input_path):
        if row.get("strategy_id") not in STRATEGIES:
            continue
        raw_seen += 1
        proxy_r = safe_float(row.get("strategy_proxy_r"))
        if proxy_r is None:
            continue
        numeric_rows.append({**row, "_line_no": line_no, "_proxy_r": proxy_r})

    latest: dict[tuple[Any, Any], dict[str, Any]] = {}
    for row in numeric_rows:
        key = (row.get("candidate_id"), row.get("strategy_id"))
        current_key = (parse_utc(row.get("asof_latest_candle_utc")), int(row.get("_line_no") or 0))
        previous = latest.get(key)
        previous_key = (
            parse_utc((previous or {}).get("asof_latest_candle_utc")),
            int((previous or {}).get("_line_no") or 0),
        )
        if previous is None or current_key >= previous_key:
            latest[key] = row
    return list(latest.values()), raw_seen, len(numeric_rows)


def split_summary(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in rows:
        key = tuple(row.get(field) for field in fields)
        groups[key].append(row["_proxy_r"])
    output = []
    for key, values in sorted(groups.items(), key=lambda item: tuple(str(part) for part in item[0])):
        output.append(
            {
                "split_fields": fields,
                "split_key": {field: value for field, value in zip(fields, key)},
                "proxy_r_summary": summarize(values),
                "safe_flags": SAFE_FLAGS,
            }
        )
    return output


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path) if path.exists() else None,
    }


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows, raw_seen, numeric_seen = latest_numeric_rows()
    source_sha = sha256(REPO_ROOT / INPUT)

    ledger_rows = []
    for row in sorted(rows, key=lambda item: (str(item.get("strategy_id")), str(item.get("candidate_id")))):
        ledger_rows.append(
            {
                "row_id": "MAIN-ORCH24-LIVE-BASELINE-PENDING-DUPAWARE-" + stable_id(row.get("candidate_id"), row.get("strategy_id")),
                "candidate_id": row.get("candidate_id"),
                "strategy_id": row.get("strategy_id"),
                "strategy_family": row.get("strategy_family"),
                "symbol": row.get("symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "decision_time_utc": row.get("decision_time_utc"),
                "asof_latest_candle_utc": row.get("asof_latest_candle_utc"),
                "source_line_no": row.get("_line_no"),
                "proxy_r": row.get("_proxy_r"),
                "outcome_status": row.get("outcome_status"),
                "path_label": row.get("path_label"),
                "score_status": row.get("score_status"),
                "strategy_status": row.get("strategy_status"),
                "evidence_class": row.get("evidence_class"),
                "duplicate_policy": "latest_numeric_proxy_row_per_candidate_id_strategy_id_by_asof_latest_candle_utc",
                "source_file": str(INPUT),
                "source_sha256": source_sha,
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
            }
        )

    split_rows: list[dict[str, Any]] = []
    for fields in (
        ["strategy_id"],
        ["strategy_id", "symbol"],
        ["strategy_id", "side"],
        ["strategy_id", "outcome_status"],
        ["strategy_id", "score_status"],
        ["symbol"],
        ["side"],
    ):
        split_rows.extend(split_summary(rows, fields))

    values = [row["_proxy_r"] for row in rows]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "input": str(INPUT),
        "input_sha256": source_sha,
        "strategies": sorted(STRATEGIES),
        "raw_strategy_rows_seen": raw_seen,
        "raw_numeric_proxy_rows_seen": numeric_seen,
        "duplicate_aware_numeric_rows": len(rows),
        "duplicate_policy": "latest_numeric_proxy_row_per_candidate_id_strategy_id_by_asof_latest_candle_utc",
        "proxy_r_summary": summarize(values),
        "by_strategy": {
            strategy: summarize([row["_proxy_r"] for row in rows if row.get("strategy_id") == strategy])
            for strategy in sorted(STRATEGIES)
        },
        "outcome_status_counts": dict(Counter(str(row.get("outcome_status")) for row in rows)),
        "symbol_counts": dict(Counter(str(row.get("symbol")) for row in rows)),
        "side_counts": dict(Counter(str(row.get("side")) for row in rows)),
        "decision": "MATERIALIZE_LIVE_BASELINE_AND_PENDING_DUPLICATE_AWARE_PROXY_ROWS_NO_PROMOTION",
        "interpretation": "Baseline and pending-lifecycle rows are live/shadow duplicate-aware proxy rows only; no broker actual-R, validation-safe, or promotion claim is opened.",
        "safe_flags": SAFE_FLAGS,
    }

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_BASELINE_PENDING_DUPLICATE_AWARE_REPLAY_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, ledger_rows)
    write_jsonl(split_path, split_rows)
    write_json(summary_path, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 3,
        "artifacts": [
            artifact_record("live_baseline_pending_duplicate_aware_replay_ledger", ledger_path),
            artifact_record("split_summary", split_path),
            artifact_record("summary_json", summary_path),
        ],
        "input_artifacts": [artifact_record("live_mechanical_strategy_shadow_outcomes", REPO_ROOT / INPUT)],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"ok": True, "duplicate_aware_numeric_rows": len(rows), "mean": summary["proxy_r_summary"]["mean"]}, sort_keys=True))


if __name__ == "__main__":
    main()
