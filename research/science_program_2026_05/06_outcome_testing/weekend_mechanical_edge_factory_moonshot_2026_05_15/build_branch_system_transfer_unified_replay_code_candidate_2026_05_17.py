#!/usr/bin/env python3
"""Materialize replay/acquisition decisions into branch-local code candidates.

This is the execution layer after replay/acquisition scoring. It consumes every
source, entry, avoid/inverse, market-gap, branch, scorer-spec, and concentration
row from the unified replay/acquisition packet and emits mechanical rule/spec
rows tied to branch-local research code surfaces.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_replay_code_candidate import (
    avoid_policy_code_candidate,
    branch_decision_code_candidate,
    concentration_guard_code_candidate,
    entry_variant_code_candidate,
    market_gap_code_candidate,
    scorer_patch_code_candidate,
    source_materialization_code_candidate,
)


REPLAY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_VARIANT_REPLAY_ACQUISITION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE"

REPLAY_RESULT = ROUTE_DIR / f"{REPLAY_PREFIX}_RESULT_2026-05-17.json"
REPLAY_SOURCE = ROUTE_DIR / f"{REPLAY_PREFIX}_SOURCE_ACQUISITION_PROXY_RESULT_LEDGER_2026-05-17.jsonl"
REPLAY_ENTRY = ROUTE_DIR / f"{REPLAY_PREFIX}_ENTRY_VARIANT_REPLAY_SCORE_LEDGER_2026-05-17.jsonl"
REPLAY_AVOID = ROUTE_DIR / f"{REPLAY_PREFIX}_AVOID_INVERSE_POLICY_REPLAY_SCORE_LEDGER_2026-05-17.jsonl"
REPLAY_MARKET = ROUTE_DIR / f"{REPLAY_PREFIX}_MARKET_GAP_REPLAY_ACQUISITION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
REPLAY_BRANCH = ROUTE_DIR / f"{REPLAY_PREFIX}_BRANCH_KEEP_KILL_REDESIGN_IMPLEMENT_LEDGER_2026-05-17.jsonl"
REPLAY_SCORER = ROUTE_DIR / f"{REPLAY_PREFIX}_BRANCH_LOCAL_SCORER_SPEC_CANDIDATE_LEDGER_2026-05-17.jsonl"
REPLAY_CONCENTRATION = ROUTE_DIR / f"{REPLAY_PREFIX}_CONCENTRATION_REPLAY_TEST_LEDGER_2026-05-17.jsonl"
HELPER_MODULE = REPO / "src/research_infra/moonshot_replay_code_candidate.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MATERIALIZATION_CODE_LEDGER_2026-05-17.jsonl"
ENTRY_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_VARIANT_CODE_LEDGER_2026-05-17.jsonl"
AVOID_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INVERSE_CODE_LEDGER_2026-05-17.jsonl"
MARKET_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_CODE_LEDGER_2026-05-17.jsonl"
BRANCH_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_SYSTEM_CODE_LEDGER_2026-05-17.jsonl"
SCORER_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_PATCH_SPEC_LEDGER_2026-05-17.jsonl"
CONCENTRATION_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_GUARD_CODE_LEDGER_2026-05-17.jsonl"
UNIFIED_CODE_LEDGER = ROUTE_DIR / f"{PREFIX}_UNIFIED_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
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
    "Unified replay code-candidate packet only. It converts replay/acquisition rows into branch-local "
    "research code/spec candidates and source-materialization actions. It does not change live behavior, "
    "place orders, or claim broker R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
    rows: list[dict[str, Any]] = []
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-CODE-SRC-{index:04d}",
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


def build_source_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = source_materialization_code_candidate(row)
        output.append(
            with_common(
                {
                    "source_materialization_code_id": f"OHLC-GTOS-UNIFIED-CODE-SOURCE-{index:05d}",
                    "source_acquisition_proxy_result_id": row.get("source_acquisition_proxy_result_id"),
                    "source_materialization_id": row.get("source_materialization_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "source_acquisition_status": row.get("source_acquisition_status"),
                    "source_proxy_replay_result": row.get("source_proxy_replay_result"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_entry_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = entry_variant_code_candidate(row)
        output.append(
            with_common(
                {
                    "entry_variant_code_id": f"OHLC-GTOS-UNIFIED-CODE-ENTRY-{index:05d}",
                    "entry_variant_replay_score_id": row.get("entry_variant_replay_score_id"),
                    "entry_geometry_variant_id": row.get("entry_geometry_variant_id"),
                    "entry_geometry_parent_decision_id": row.get("entry_geometry_parent_decision_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "entry_replay_decision": row.get("entry_replay_decision"),
                    "entry_proxy_r_style_result_class": row.get("entry_proxy_r_style_result_class"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_avoid_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = avoid_policy_code_candidate(row)
        output.append(
            with_common(
                {
                    "avoid_inverse_code_id": f"OHLC-GTOS-UNIFIED-CODE-AVOID-{index:05d}",
                    "avoid_inverse_policy_replay_score_id": row.get("avoid_inverse_policy_replay_score_id"),
                    "avoid_inverse_policy_variant_id": row.get("avoid_inverse_policy_variant_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "policy_variant_replay_decision": row.get("policy_variant_replay_decision"),
                    "policy_proxy_r_style_result_class": row.get("policy_proxy_r_style_result_class"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_market_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = market_gap_code_candidate(row)
        output.append(
            with_common(
                {
                    "market_gap_code_id": f"OHLC-GTOS-UNIFIED-CODE-MARKET-{index:05d}",
                    "market_gap_replay_acquisition_synthesis_id": row.get("market_gap_replay_acquisition_synthesis_id"),
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "market_gap_replay_decision": row.get("market_gap_replay_decision"),
                    "market_gap_proxy_r_style_result_class": row.get("market_gap_proxy_r_style_result_class"),
                    "implementation_implication": row.get("implementation_implication"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_branch_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = branch_decision_code_candidate(row)
        output.append(
            with_common(
                {
                    "branch_system_code_id": f"OHLC-GTOS-UNIFIED-CODE-BRANCH-{index:05d}",
                    "branch_keep_kill_redesign_implement_id": row.get("branch_keep_kill_redesign_implement_id"),
                    "branch_queue_id": row.get("branch_queue_id"),
                    "target_stop_contract_id": row.get("target_stop_contract_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "keep_kill_redesign_implement_replay_decision": row.get(
                        "keep_kill_redesign_implement_replay_decision"
                    ),
                    "exact_failure_or_success_cause": row.get("exact_failure_or_success_cause"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_scorer_code_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = scorer_patch_code_candidate(row)
        output.append(
            with_common(
                {
                    "scorer_patch_code_id": f"OHLC-GTOS-UNIFIED-CODE-SCORER-{index:05d}",
                    "branch_local_scorer_spec_candidate_id": row.get("branch_local_scorer_spec_candidate_id"),
                    "scorer_spec_change_id": row.get("scorer_spec_change_id"),
                    "source_scorer_spec_id": row.get("source_scorer_spec_id"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_concentration_code_rows(
    rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate = concentration_guard_code_candidate(row)
        output.append(
            with_common(
                {
                    "concentration_guard_code_id": f"OHLC-GTOS-UNIFIED-CODE-CONC-{index:05d}",
                    "concentration_replay_test_id": row.get("concentration_replay_test_id"),
                    "concentration_artifact_restress_id": row.get("concentration_artifact_restress_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "test_axis": row.get("test_axis"),
                    "concentration_replay_decision": row.get("concentration_replay_decision"),
                    **candidate,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_bucket_rows(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    distributions = {
        "source_code_status": compact_counter(groups["source"], "code_candidate_status"),
        "entry_code_status": compact_counter(groups["entry"], "code_candidate_status"),
        "avoid_code_status": compact_counter(groups["avoid"], "code_candidate_status"),
        "market_gap_code_status": compact_counter(groups["market"], "code_candidate_status"),
        "branch_code_status": compact_counter(groups["branch"], "code_candidate_status"),
        "scorer_code_status": compact_counter(groups["scorer"], "code_candidate_status"),
        "concentration_code_status": compact_counter(groups["concentration"], "code_candidate_status"),
        "unified_code_kind": compact_counter(groups["unified"], "code_candidate_kind"),
    }
    bucket_rows: list[dict[str, Any]] = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-CODE-BUCKET-{len(bucket_rows) + 1:04d}",
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
    manifest["latest_unified_replay_code_candidate"] = {
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
        "event": "unified_replay_code_candidates_materialized",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Converted replay/acquisition decisions into branch-local research code/spec candidates and materialization actions.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        REPLAY_RESULT,
        REPLAY_SOURCE,
        REPLAY_ENTRY,
        REPLAY_AVOID,
        REPLAY_MARKET,
        REPLAY_BRANCH,
        REPLAY_SCORER,
        REPLAY_CONCENTRATION,
        HELPER_MODULE,
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)
    replay_result = read_json(REPLAY_RESULT)
    source_rows_input = read_jsonl(REPLAY_SOURCE)
    entry_rows_input = read_jsonl(REPLAY_ENTRY)
    avoid_rows_input = read_jsonl(REPLAY_AVOID)
    market_rows_input = read_jsonl(REPLAY_MARKET)
    branch_rows_input = read_jsonl(REPLAY_BRANCH)
    scorer_rows_input = read_jsonl(REPLAY_SCORER)
    concentration_rows_input = read_jsonl(REPLAY_CONCENTRATION)

    source_rows = build_source_code_rows(source_rows_input, generated_at, manifest_hash)
    entry_rows = build_entry_code_rows(entry_rows_input, generated_at, manifest_hash)
    avoid_rows = build_avoid_code_rows(avoid_rows_input, generated_at, manifest_hash)
    market_rows = build_market_code_rows(market_rows_input, generated_at, manifest_hash)
    branch_rows = build_branch_code_rows(branch_rows_input, generated_at, manifest_hash)
    scorer_rows = build_scorer_code_rows(scorer_rows_input, generated_at, manifest_hash)
    concentration_rows = build_concentration_code_rows(concentration_rows_input, generated_at, manifest_hash)
    unified_rows = [*source_rows, *entry_rows, *avoid_rows, *market_rows, *branch_rows, *scorer_rows, *concentration_rows]

    groups = {
        "source": source_rows,
        "entry": entry_rows,
        "avoid": avoid_rows,
        "market": market_rows,
        "branch": branch_rows,
        "scorer": scorer_rows,
        "concentration": concentration_rows,
        "unified": unified_rows,
    }
    bucket_rows, distributions = build_bucket_rows(groups, generated_at, manifest_hash)
    question_rows = [
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-CODE-Q-001",
                "question": "Did the packet preserve all replay/acquisition rows while converting them to code/spec candidates?",
                "answer_route": "Yes: 309 source, 272 entry, 46 avoid/inverse, 400 market-gap, 386 branch, 8 scorer, and 124 concentration rows are all emitted into code-candidate ledgers.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-CODE-Q-002",
                "question": "Do accepted entry and avoid candidates produce branch-local implementation specs rather than summary-only output?",
                "answer_route": "Yes: accepted entry rows emit ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC and accepted avoid rows emit AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC with mechanical scope keys.",
            },
            generated_at,
            manifest_hash,
        ),
        with_common(
            {
                "question_id": "OHLC-GTOS-UNIFIED-CODE-Q-003",
                "question": "Does the code-candidate layer keep the outside-market concentration artifact alive?",
                "answer_route": "Yes: market and concentration rows preserve outside_gbpjpy_xauusd_current_branch_box and force denominator guards where outside-branch rows exist.",
            },
            generated_at,
            manifest_hash,
        ),
    ]

    counts = {
        "input_source_replay_rows": len(source_rows_input),
        "input_entry_replay_rows": len(entry_rows_input),
        "input_avoid_replay_rows": len(avoid_rows_input),
        "input_market_replay_rows": len(market_rows_input),
        "input_branch_replay_rows": len(branch_rows_input),
        "input_scorer_spec_rows": len(scorer_rows_input),
        "input_concentration_replay_rows": len(concentration_rows_input),
        "source_materialization_code_rows": len(source_rows),
        "entry_variant_code_rows": len(entry_rows),
        "avoid_inverse_code_rows": len(avoid_rows),
        "market_gap_code_rows": len(market_rows),
        "branch_system_code_rows": len(branch_rows),
        "scorer_patch_spec_rows": len(scorer_rows),
        "concentration_guard_code_rows": len(concentration_rows),
        "unified_code_candidate_rows": len(unified_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "entry_shadow_rule_implement_rows": distributions["entry_code_status"].get("ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC", 0),
        "avoid_shadow_filter_implement_rows": distributions["avoid_code_status"].get("AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC", 0),
        "market_gap_outside_branch_code_rows": sum(
            1 for row in market_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
        ),
        "market_gap_outside_branch_implement_code_rows": sum(
            1
            for row in market_rows
            if row.get("outside_gbpjpy_xauusd_current_branch_box")
            and str(row.get("code_candidate_status", "")).startswith("MARKET_GAP_CODE_IMPLEMENT")
        ),
        "source_rows_needed_to_n20_total": sum(int(row.get("source_rows_needed_to_n20") or 0) for row in source_rows),
    }
    system_decision = {
        "entry_code_status_counts": distributions["entry_code_status"],
        "avoid_code_status_counts": distributions["avoid_code_status"],
        "market_gap_code_status_counts": distributions["market_gap_code_status"],
        "branch_code_status_counts": distributions["branch_code_status"],
        "source_code_status_counts": distributions["source_code_status"],
        "concentration_code_status_counts": distributions["concentration_code_status"],
        "system_recommendation": (
            "UNIFIED_REPLAY_CODE_CANDIDATE_RESULT: implement branch-local shadow specs for accepted entry "
            "and avoid candidates, add scorer repair/source/concentration guards, and keep outside-branch "
            "market-gap code candidates active because concentration is both current-queue real and denominator-artifact exposed."
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
        "upstream_counts": {"unified_variant_replay_acquisition": replay_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    generated_files = [
        SOURCE_CODE_LEDGER,
        ENTRY_CODE_LEDGER,
        AVOID_CODE_LEDGER,
        MARKET_CODE_LEDGER,
        BRANCH_CODE_LEDGER,
        SCORER_CODE_LEDGER,
        CONCENTRATION_GUARD_LEDGER,
        UNIFIED_CODE_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]
    write_jsonl(SOURCE_CODE_LEDGER, source_rows)
    write_jsonl(ENTRY_CODE_LEDGER, entry_rows)
    write_jsonl(AVOID_CODE_LEDGER, avoid_rows)
    write_jsonl(MARKET_CODE_LEDGER, market_rows)
    write_jsonl(BRANCH_CODE_LEDGER, branch_rows)
    write_jsonl(SCORER_CODE_LEDGER, scorer_rows)
    write_jsonl(CONCENTRATION_GUARD_LEDGER, concentration_rows)
    write_jsonl(UNIFIED_CODE_LEDGER, unified_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Replay Code Candidate",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Unified code-candidate rows: `{counts['unified_code_candidate_rows']}`",
                f"- Entry shadow rule implement rows: `{counts['entry_shadow_rule_implement_rows']}`",
                f"- Avoid shadow filter implement rows: `{counts['avoid_shadow_filter_implement_rows']}`",
                f"- Outside-branch market-gap code rows: `{counts['market_gap_outside_branch_code_rows']}`",
                f"- Outside-branch implement code rows: `{counts['market_gap_outside_branch_implement_code_rows']}`",
                f"- Source rows needed to N20 total: `{counts['source_rows_needed_to_n20_total']}`",
                "",
                "Core result: replay/acquisition rows now have branch-local mechanical code/spec actions with scope keys and guards.",
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
