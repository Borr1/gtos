#!/usr/bin/env python3
"""Execute branch-local shadow scorer over unified code-candidate rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_replay_shadow_scorer import score_code_candidate


CODE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION"

CODE_RESULT = ROUTE_DIR / f"{CODE_PREFIX}_RESULT_2026-05-17.json"
CODE_UNIFIED = ROUTE_DIR / f"{CODE_PREFIX}_UNIFIED_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
SCORER_MODULE = REPO / "src/research_infra/moonshot_replay_shadow_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
IMPLEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENT_ENABLE_LEDGER_2026-05-17.jsonl"
SOURCE_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MATERIALIZATION_QUEUE_LEDGER_2026-05-17.jsonl"
CONTROL_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_GUARD_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified shadow scorer execution packet only. It scores branch-local code/spec candidates into "
    "mechanical shadow actions, source-materialization actions, controls, and denominator guards. It does "
    "not change live behavior, place orders, or claim broker R/PnL, realized expectancy, win-rate, "
    "validation, live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-SHADOW-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def compact_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def code_candidate_id(row: dict[str, Any]) -> str | None:
    for key in (
        "source_materialization_code_id",
        "entry_variant_code_id",
        "avoid_inverse_code_id",
        "market_gap_code_id",
        "branch_system_code_id",
        "scorer_patch_code_id",
        "concentration_guard_code_id",
    ):
        if row.get(key):
            return str(row[key])
    return None


def build_row_ledger(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        scored = score_code_candidate(row)
        output.append(
            with_common(
                {
                    "shadow_scorer_execution_id": f"OHLC-GTOS-UNIFIED-SHADOW-ROW-{index:05d}",
                    "source_code_candidate_id": code_candidate_id(row),
                    "code_candidate_kind": row.get("code_candidate_kind"),
                    "code_candidate_status": row.get("code_candidate_status"),
                    "code_candidate_action": row.get("code_candidate_action"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "mechanical_scope_key": row.get("mechanical_scope_key"),
                    "mechanical_rule_expression": row.get("mechanical_rule_expression"),
                    "source_rows_needed_to_n20": row.get("source_rows_needed_to_n20"),
                    **scored,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            str(row.get("symbol") or "NA"),
            str(row.get("route_session") or "NA"),
            str(row.get("shadow_scorer_action_family") or "NA"),
        )
        groups[key].append(row)
    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session, action_family), members) in enumerate(sorted(groups.items()), 1):
        output.append(
            with_common(
                {
                    "symbol_session_action_id": f"OHLC-GTOS-UNIFIED-SHADOW-SSH-{index:05d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "shadow_scorer_action_family": action_family,
                    "row_count": len(members),
                    "implementation_enable_rows": sum(
                        1 for row in members if row.get("shadow_scorer_action_family") == "IMPLEMENT_SHADOW_RULE"
                    ),
                    "source_materialization_rows": sum(
                        1 for row in members if row.get("shadow_scorer_action_family") == "MATERIALIZE_SOURCE"
                    ),
                    "outside_branch_rows": sum(1 for row in members if row.get("outside_gbpjpy_xauusd_current_branch_box")),
                    "max_shadow_scorer_score": max(float(row.get("shadow_scorer_score") or 0.0) for row in members),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "shadow_scorer_action_family": compact_counter(groups["rows"], "shadow_scorer_action_family"),
        "shadow_scorer_action": compact_counter(groups["rows"], "shadow_scorer_action"),
        "implementation_eligibility": compact_counter(groups["rows"], "implementation_eligibility"),
        "shadow_scorer_component": compact_counter(groups["rows"], "shadow_scorer_component"),
        "shadow_scorer_score_band": compact_counter(groups["rows"], "shadow_scorer_score_band"),
        "symbol_session_action_family": compact_counter(groups["symbol_session"], "shadow_scorer_action_family"),
    }
    bucket_rows: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-SHADOW-BUCKET-{len(bucket_rows) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return bucket_rows, distributions


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append({"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True})
    manifest["latest_unified_shadow_scorer_execution"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_shadow_scorer_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Executed branch-local shadow scorer over all unified code candidates.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows([CODE_RESULT, CODE_UNIFIED, SCORER_MODULE], generated_at)
    code_result = read_json(CODE_RESULT)
    code_rows = read_jsonl(CODE_UNIFIED)

    row_ledger = build_row_ledger(code_rows, generated_at, manifest_hash)
    implement_rows = [row for row in row_ledger if row.get("shadow_scorer_action_family") == "IMPLEMENT_SHADOW_RULE"]
    source_queue_rows = [row for row in row_ledger if row.get("shadow_scorer_action_family") == "MATERIALIZE_SOURCE"]
    control_guard_rows = [
        row
        for row in row_ledger
        if row.get("shadow_scorer_action_family") not in {"IMPLEMENT_SHADOW_RULE", "MATERIALIZE_SOURCE"}
    ]
    symbol_session_rows = build_symbol_session_rows(row_ledger, generated_at, manifest_hash)
    bucket_rows, distributions = build_bucket_rows(
        {"rows": row_ledger, "symbol_session": symbol_session_rows}, generated_at, manifest_hash
    )
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SHADOW-Q-001",
                "question": "Did the scorer execute every code-candidate row?",
                "answer_route": "Yes: every 1,545 unified code-candidate row is emitted into the shadow scorer row ledger.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SHADOW-Q-002",
                "question": "Which actions are immediately enableable in branch-local shadow scoring?",
                "answer_route": "Rows with action family IMPLEMENT_SHADOW_RULE are emitted into the implementation enable ledger; controls, guards, and source materialization stay separate.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-SHADOW-Q-003",
                "question": "Does outside-market concentration pressure remain actionable?",
                "answer_route": "Yes: outside-branch rows remain marked through the row, implementation, source, and symbol/session ledgers.",
            },
            generated_at,
            manifest_hash,
        ),
    ]
    counts = {
        "input_unified_code_candidate_rows": len(code_rows),
        "shadow_scorer_row_rows": len(row_ledger),
        "implementation_enable_rows": len(implement_rows),
        "source_materialization_queue_rows": len(source_queue_rows),
        "control_guard_rows": len(control_guard_rows),
        "symbol_session_action_rows": len(symbol_session_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "outside_branch_shadow_scorer_rows": sum(1 for row in row_ledger if row.get("outside_gbpjpy_xauusd_current_branch_box")),
        "outside_branch_implementation_enable_rows": sum(
            1 for row in implement_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "source_rows_needed_to_n20_total": sum(int(row.get("source_rows_needed_to_n20") or 0) for row in source_queue_rows),
    }
    system_decision = {
        "shadow_scorer_action_family_counts": distributions["shadow_scorer_action_family"],
        "implementation_eligibility_counts": distributions["implementation_eligibility"],
        "system_recommendation": (
            "UNIFIED_SHADOW_SCORER_EXECUTION_RESULT: branch-local shadow scorer can enable the implementation "
            "ledger while keeping source materialization, controls, and denominator guards separate; outside-branch "
            "rows remain actionable and must not be dropped."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"unified_replay_code_candidate": code_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    generated_files = [
        ROW_LEDGER,
        IMPLEMENT_LEDGER,
        SOURCE_QUEUE_LEDGER,
        CONTROL_GUARD_LEDGER,
        SYMBOL_SESSION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(ROW_LEDGER, row_ledger)
    write_jsonl(IMPLEMENT_LEDGER, implement_rows)
    write_jsonl(SOURCE_QUEUE_LEDGER, source_queue_rows)
    write_jsonl(CONTROL_GUARD_LEDGER, control_guard_rows)
    write_jsonl(SYMBOL_SESSION_LEDGER, symbol_session_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Shadow Scorer Execution",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Shadow scorer rows: `{counts['shadow_scorer_row_rows']}`",
                f"- Implementation enable rows: `{counts['implementation_enable_rows']}`",
                f"- Source materialization queue rows: `{counts['source_materialization_queue_rows']}`",
                f"- Control/guard rows: `{counts['control_guard_rows']}`",
                f"- Outside-branch implementation enable rows: `{counts['outside_branch_implementation_enable_rows']}`",
                "",
                "Core result: code-candidate rows are now executable shadow-scorer actions with implementation, source, control, and guard paths separated.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
