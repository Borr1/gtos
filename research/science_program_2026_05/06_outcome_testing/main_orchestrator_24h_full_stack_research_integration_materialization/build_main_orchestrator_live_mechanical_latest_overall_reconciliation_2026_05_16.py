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


def latest_overall_rows() -> tuple[list[dict[str, Any]], int]:
    raw_seen = 0
    latest: dict[tuple[Any, Any], dict[str, Any]] = {}
    for line_no, row in iter_jsonl(REPO_ROOT / INPUT):
        raw_seen += 1
        key = (row.get("candidate_id"), row.get("strategy_id"))
        current_key = (parse_utc(row.get("asof_latest_candle_utc")), line_no)
        previous = latest.get(key)
        previous_key = (
            parse_utc((previous or {}).get("asof_latest_candle_utc")),
            int((previous or {}).get("_line_no") or 0),
        )
        if previous is None or current_key >= previous_key:
            latest[key] = {**row, "_line_no": line_no, "_proxy_r": safe_float(row.get("strategy_proxy_r"))}
    return list(latest.values()), raw_seen


def split_summary(rows: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    noncomputable_counts: Counter[tuple[Any, ...]] = Counter()
    for row in rows:
        key = tuple(row.get(field) for field in fields)
        if row.get("_proxy_r") is None:
            noncomputable_counts[key] += 1
        else:
            groups[key].append(float(row["_proxy_r"]))
    output = []
    for key in sorted(set(groups) | set(noncomputable_counts), key=lambda item: tuple(str(part) for part in item)):
        output.append(
            {
                "split_fields": fields,
                "split_key": {field: value for field, value in zip(fields, key)},
                "proxy_r_summary": summarize(groups.get(key, [])),
                "noncomputable_rows": noncomputable_counts.get(key, 0),
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
    rows, raw_seen = latest_overall_rows()
    source_sha = sha256(REPO_ROOT / INPUT)

    ledger_rows = []
    proof_rows = []
    for row in sorted(rows, key=lambda item: (str(item.get("strategy_id")), str(item.get("candidate_id")))):
        proxy_r = row.get("_proxy_r")
        ledger_row = {
            "row_id": "MAIN-ORCH24-LIVE-MECH-LATEST-OVERALL-" + stable_id(row.get("candidate_id"), row.get("strategy_id")),
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
            "proxy_r": proxy_r,
            "exact_r": None,
            "outcome_status": row.get("outcome_status"),
            "path_label": row.get("path_label"),
            "score_status": row.get("score_status"),
            "strategy_status": row.get("strategy_status"),
            "status_reason": row.get("status_reason"),
            "evidence_class": row.get("evidence_class"),
            "duplicate_policy": "latest_overall_row_per_candidate_id_strategy_id_by_asof_latest_candle_utc",
            "source_file": str(INPUT),
            "source_sha256": source_sha,
            "safe_flags": SAFE_FLAGS,
        }
        ledger_rows.append(ledger_row)
        if proxy_r is None:
            proof_rows.append(
                {
                    "row_id": ledger_row["row_id"],
                    "candidate_id": ledger_row["candidate_id"],
                    "strategy_id": ledger_row["strategy_id"],
                    "score_status": ledger_row["score_status"],
                    "strategy_status": ledger_row["strategy_status"],
                    "status_reason": ledger_row["status_reason"],
                    "artifact_paths_checked": [str(INPUT)],
                    "input_hashes": {str(INPUT): source_sha},
                    "missing_fields": ["strategy_proxy_r", "scoreable_strategy_geometry_or_context"] if ledger_row["score_status"] != "NOT_AN_ENTRY_STRATEGY" else ["entry_strategy_geometry_not_applicable"],
                    "why_no_weaker_proxy_r": "Latest overall strategy row has no numeric strategy_proxy_r; scoring it would invent an outcome or synthesize an entry for a context-only/nonimplemented/ambiguous strategy.",
                    "decision": "PRESERVE_AS_LATEST_OVERALL_NONCOMPUTABLE_PROOF_ROW",
                    "safe_flags": SAFE_FLAGS,
                }
            )

    proxy_values = [float(row["proxy_r"]) for row in ledger_rows if row.get("proxy_r") is not None]
    split_rows: list[dict[str, Any]] = []
    for fields in (
        ["strategy_id"],
        ["strategy_id", "score_status"],
        ["strategy_id", "strategy_status"],
        ["strategy_id", "symbol"],
        ["symbol"],
        ["side"],
    ):
        split_rows.extend(split_summary(rows, fields))

    by_strategy = {}
    for strategy in sorted({str(row.get("strategy_id")) for row in rows}):
        strat_rows = [row for row in rows if str(row.get("strategy_id")) == strategy]
        strat_values = [float(row["_proxy_r"]) for row in strat_rows if row.get("_proxy_r") is not None]
        by_strategy[strategy] = {
            "latest_overall_rows": len(strat_rows),
            "numeric_proxy_rows": len(strat_values),
            "noncomputable_rows": len(strat_rows) - len(strat_values),
            "proxy_r_summary": summarize(strat_values),
            "score_status_counts": dict(Counter(str(row.get("score_status")) for row in strat_rows)),
            "strategy_status_counts": dict(Counter(str(row.get("strategy_status")) for row in strat_rows)),
        }

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "input": str(INPUT),
        "input_sha256": source_sha,
        "raw_rows_seen": raw_seen,
        "strategy_count": len(by_strategy),
        "latest_overall_rows": len(ledger_rows),
        "numeric_proxy_rows": len(proxy_values),
        "noncomputable_rows": len(proof_rows),
        "duplicate_policy": "latest_overall_row_per_candidate_id_strategy_id_by_asof_latest_candle_utc",
        "proxy_r_summary": summarize(proxy_values),
        "by_strategy": by_strategy,
        "decision": "RECONCILE_LATEST_OVERALL_NUMERIC_AND_NONCOMPUTABLE_LIVE_MECHANICAL_ROWS_NO_PROMOTION",
        "interpretation": "Latest-overall reconciliation shows which strategy rows remain numeric versus ambiguous, context-only, non-applicable, or scorer-not-implemented. Latest-numeric replay ledgers are computable subsets, not current-latest denominators.",
        "safe_flags": SAFE_FLAGS,
    }

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_RECONCILIATION_LEDGER_{DATE}.jsonl"
    proof_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_NONCOMPUTABLE_PROOF_LEDGER_{DATE}.jsonl"
    split_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SPLIT_SUMMARY_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, ledger_rows)
    write_jsonl(proof_path, proof_rows)
    write_jsonl(split_path, split_rows)
    write_json(summary_path, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 4,
        "artifacts": [
            artifact_record("latest_overall_reconciliation_ledger", ledger_path),
            artifact_record("noncomputable_proof_ledger", proof_path),
            artifact_record("split_summary", split_path),
            artifact_record("summary_json", summary_path),
        ],
        "input_artifacts": [artifact_record("live_mechanical_strategy_shadow_outcomes", REPO_ROOT / INPUT)],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"ok": True, "latest_overall_rows": len(ledger_rows), "numeric_proxy_rows": len(proxy_values), "noncomputable_rows": len(proof_rows), "mean": summary["proxy_r_summary"]["mean"]}, sort_keys=True))


if __name__ == "__main__":
    main()
