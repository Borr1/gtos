#!/usr/bin/env python3
"""Build runtime rows for the pre-AI/post-L2 routing policy residue wave."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_PRE_AI_POST_L2_ROUTING_BEHAVIOR"
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
BATCH_LEDGER_PATH = OUTPUT_DIR / f"GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
OUTPUT_ROWS = OUTPUT_DIR / f"GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = OUTPUT_DIR / f"GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_SUMMARY_{DATE}.json"
GENERATED_OUTPUT_PATHS = {
    OUTPUT_ROWS.relative_to(REPO_ROOT).as_posix(),
    OUTPUT_SUMMARY.relative_to(REPO_ROOT).as_posix(),
}

SYMBOL_TOKENS = (
    "US30_cash",
    "USOIL_cash",
    "UKOIL_cash",
    "XAUUSD",
    "XAGUSD",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "SPX500",
    "USDCAD",
    "CHFJPY",
    "US30",
    "DXY",
)
TIMEFRAME_TOKENS = ("M1", "M5", "M15", "H1", "H4", "D1")
SESSION_TOKEN_MAP = {
    "LONDON_CORE": "london_core",
    "LONDON": "london_core",
    "NY_CORE": "ny_core",
    "NEW_YORK": "ny_core",
    "NY": "ny_core",
    "TOKYO_KZ": "tokyo_kz",
    "TOKYO": "tokyo_kz",
    "OFF_CORE_SESSION": "off_core_session",
}
SIDE_TOKENS = ("LONG", "SHORT")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _repo_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _read_text_prefix(path: Path, *, byte_limit: int = 512_000) -> str:
    if not path.exists() or path.is_dir():
        return ""
    try:
        data = path.read_bytes()[:byte_limit]
    except OSError:
        return ""
    return data.decode("utf-8", errors="ignore")


def _read_batch_wave() -> dict[str, Any]:
    for line in BATCH_LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("wave_id") == WAVE_ID:
            return row
    raise SystemExit(f"missing batch wave: {WAVE_ID}")


def _source_family(path: str) -> str:
    lower = path.casefold()
    if "main_orchestrator_24h_full_stack_research_integration_materialization" in lower:
        return "main_orch48_current"
    if "v4_prompt_engineering" in lower:
        return "legacy_v4_prompt_engineering"
    if "academic_pipeline" in lower:
        return "academic_ai_pipeline"
    if "ai_behavior" in lower:
        return "ai_behavior_empirical"
    if path.startswith(".context/05_operations") or path.startswith(
        "research/science_program_2026_05/04_goal_prompts"
    ):
        return "goal_prompt_wrappers"
    if path.startswith("research/science_program_2026_05/05_synthesis"):
        return "science_synthesis"
    if "g0exp_r1_local_heavy_root_parser_hash_lineage" in lower:
        return "source_lineage_parser_control"
    if "scid_forward_capture" in lower:
        return "scid_forward_capture_contract"
    return "/".join(path.split("/")[:2])


def _detect_symbols(text: str) -> list[str]:
    upper = text.upper()
    values = [symbol for symbol in SYMBOL_TOKENS if symbol.upper() in upper]
    return sorted(set(values))


def _detect_timeframes(text: str) -> list[str]:
    upper = text.upper()
    values = [
        tf
        for tf in TIMEFRAME_TOKENS
        if re.search(rf"(?<![A-Z0-9]){re.escape(tf)}(?![A-Z0-9])", upper)
    ]
    return sorted(set(values), key=TIMEFRAME_TOKENS.index)


def _detect_sessions(text: str) -> list[str]:
    upper = text.upper()
    values = {
        canonical
        for token, canonical in SESSION_TOKEN_MAP.items()
        if re.search(rf"(?<![A-Z0-9]){re.escape(token)}(?![A-Z0-9])", upper)
    }
    return sorted(values)


def _detect_sides(text: str) -> list[str]:
    upper = text.upper()
    return [
        side
        for side in SIDE_TOKENS
        if re.search(rf"(?<![A-Z]){side}(?![A-Z])", upper)
    ]


def _policy_class(path: str, text: str) -> dict[str, str]:
    lower = f"{path}\n{text[:120000]}".casefold()
    if "recovered_v3" in lower or "v3_prompt_snapshot" in lower:
        return {
            "decision": "FOLLOW",
            "source_component": "ai_v3_cascade_preferred",
            "action_class": "pre_ai_post_l2_ai_route_follow_pressure",
            "runtime_effect_now": "pre_ai_post_l2_v3_cascade_route_pressure",
            "implementation_action": "REGISTER_PRE_AI_POST_L2_AI_ROUTE_PRESSURE",
            "r_evidence_class": "PRE_AI_POST_L2_ROUTING_FOLLOW_PRESSURE",
        }
    if "no_ai_shadow" in lower or "no-ai shadow" in lower:
        return {
            "decision": "FOLLOW",
            "source_component": "no_ai_shadow_observer",
            "action_class": "pre_ai_post_l2_ai_route_follow_pressure",
            "runtime_effect_now": "pre_ai_post_l2_no_ai_shadow_route_pressure",
            "implementation_action": "REGISTER_PRE_AI_POST_L2_NO_AI_SHADOW_ROUTE_PRESSURE",
            "r_evidence_class": "PRE_AI_POST_L2_NO_AI_SHADOW_FOLLOW_PRESSURE",
        }
    if (
        "hallucination" in lower
        or "blindspot" in lower
        or "flipping" in lower
        or "tolerance_sweep" in lower
        or "malformed" in lower
    ):
        return {
            "decision": "AVOID",
            "source_component": "ai_hallucination_guard",
            "action_class": "pre_ai_post_l2_ai_route_failure_filter",
            "runtime_effect_now": "pre_ai_post_l2_ai_hallucination_filter",
            "implementation_action": "REGISTER_PRE_AI_POST_L2_AI_ROUTE_AVOID_FILTER",
            "r_evidence_class": "PRE_AI_POST_L2_ROUTING_AVOID_FILTER",
        }
    if "v4_prompt_engineering" in lower or "lira" in lower:
        return {
            "decision": "AVOID",
            "source_component": "legacy_v4_lira_guard",
            "action_class": "legacy_v4_lira_avoid_filter",
            "runtime_effect_now": "pre_ai_post_l2_legacy_v4_lira_filter",
            "implementation_action": "REGISTER_PRE_AI_POST_L2_LEGACY_V4_LIRA_AVOID_FILTER",
            "r_evidence_class": "PRE_AI_POST_L2_LEGACY_V4_LIRA_AVOID_FILTER",
        }
    if (
        "source_root" in lower
        or "hash_lineage" in lower
        or "parser" in lower
        or "redaction" in lower
        or "asof" in lower
    ):
        return {
            "decision": "MIXED",
            "source_component": "ai_source_lineage_materialization_guard",
            "action_class": "pre_ai_post_l2_ai_context_guard",
            "runtime_effect_now": "pre_ai_post_l2_source_lineage_context_guard",
            "implementation_action": "MERGE_PRE_AI_POST_L2_SOURCE_LINEAGE_CONTEXT_GUARD",
            "r_evidence_class": "PRE_AI_POST_L2_ROUTING_CONTEXT_GUARD",
        }
    if "ai_narrowing" in lower or "pre_ai" in lower or "post_l2" in lower:
        return {
            "decision": "MIXED",
            "source_component": "ai_narrowing_policy_residue",
            "action_class": "pre_ai_post_l2_ai_context_guard",
            "runtime_effect_now": "pre_ai_post_l2_ai_narrowing_context_guard",
            "implementation_action": "MERGE_PRE_AI_POST_L2_AI_NARROWING_CONTEXT_GUARD",
            "r_evidence_class": "PRE_AI_POST_L2_ROUTING_CONTEXT_GUARD",
        }
    if "limit_order" in lower:
        return {
            "decision": "MIXED",
            "source_component": "ai_limit_order_prompt_context",
            "action_class": "pre_ai_post_l2_ai_context_guard",
            "runtime_effect_now": "pre_ai_post_l2_limit_order_context_guard",
            "implementation_action": "MERGE_PRE_AI_POST_L2_LIMIT_ORDER_CONTEXT_GUARD",
            "r_evidence_class": "PRE_AI_POST_L2_ROUTING_CONTEXT_GUARD",
        }
    return {
        "decision": "MIXED",
        "source_component": "ai_routing_architecture_context",
        "action_class": "pre_ai_post_l2_ai_context_guard",
        "runtime_effect_now": "pre_ai_post_l2_ai_architecture_context_guard",
        "implementation_action": "MERGE_PRE_AI_POST_L2_AI_ARCHITECTURE_CONTEXT_GUARD",
        "r_evidence_class": "PRE_AI_POST_L2_ROUTING_CONTEXT_GUARD",
    }


def _metric(value: float | int, *, source_field: str, source_shape: str) -> dict[str, Any]:
    numeric = float(value)
    return {
        "sum": numeric,
        "count": 1,
        "mean": numeric,
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "source_field": source_field,
        "source_shape": source_shape,
    }


def _share_counts(total: int, pieces: int) -> list[int]:
    if pieces <= 1:
        return [total]
    base = total // pieces
    remainder = total % pieces
    return [base + (1 if index < remainder else 0) for index in range(pieces)]


def _runtime_rows() -> list[dict[str, Any]]:
    wave = _read_batch_wave()
    rows: list[dict[str, Any]] = []
    for unit_index, item in enumerate(wave.get("unit_dispositions", []), start=1):
        source_path = _norm(item.get("source_artifact_path")).replace("\\", "/")
        if not source_path:
            continue
        if source_path in GENERATED_OUTPUT_PATHS:
            continue
        disk_path = _repo_path(source_path)
        text = _read_text_prefix(disk_path)
        scan_text = f"{source_path}\n{text}"
        source_family = _source_family(source_path)
        policy = _policy_class(source_path, text)
        symbols = _detect_symbols(scan_text) or [""]
        timeframes = _detect_timeframes(scan_text)
        sessions = _detect_sessions(scan_text)
        sides = _detect_sides(scan_text)
        timeframe = timeframes[0] if len(timeframes) == 1 else ""
        route_session = sessions[0] if len(sessions) == 1 else "ALL_SESSIONS"
        side = sides[0] if len(sides) == 1 else ""
        source_rows_represented = int(item.get("row_count") or 0)
        shares = _share_counts(source_rows_represented, len(symbols))
        source_hash = _norm(item.get("source_artifact_hash"))
        if not source_hash and disk_path.exists() and disk_path.is_file():
            source_hash = _sha256_file(disk_path)
        for symbol_index, (symbol, represented) in enumerate(
            zip(symbols, shares, strict=True),
            start=1,
        ):
            row_hash = _sha256_text(
                f"{item.get('unit_id')}|{source_path}|{symbol_index}|{symbol}"
            )[:24]
            row_id = f"pre_ai_post_l2_routing_policy:{row_hash}"
            event_scope = {
                "route_session": route_session,
                "route_family": "mechanical_ai_selector",
                "source_component": policy["source_component"],
            }
            if symbol:
                event_scope.update(
                    {
                        "symbol": symbol,
                        "source_symbol": symbol,
                        "market": symbol,
                        "symbol_family": resolve_vnext_symbol_family(symbol),
                    }
                )
            if timeframe:
                event_scope["timeframe"] = timeframe
                event_scope["market_timeframe"] = timeframe
            if side:
                event_scope["side"] = side
            proxy_unit = {
                "FOLLOW": 0.1,
                "AVOID": -0.1,
                "MIXED": 0.0,
            }[policy["decision"]]
            proxy_score = proxy_unit * max(1, represented)
            rows.append(
                {
                    "schema_version": "gtos_vnext_pre_ai_post_l2_routing_policy_runtime_row_v1",
                    "wave_id": WAVE_ID,
                    "pre_ai_post_l2_routing_policy_runtime_row_id": row_id,
                    "row_key": row_id,
                    "source_row_id": _norm(item.get("unit_id")) or f"wave_unit_{unit_index:05d}",
                    "source_unit_id": _norm(item.get("unit_id")),
                    "source_path": source_path,
                    "source_artifact": source_path,
                    "source_artifact_hash": source_hash,
                    "source_artifact_hash_algorithm": _norm(
                        item.get("source_artifact_hash_algorithm")
                    )
                    or "git_blob_or_sha256",
                    "source_family": source_family,
                    "source_group": source_family,
                    "source_role": source_family,
                    "source_name": "gtos_vnext_pre_ai_post_l2_routing_policy_wave",
                    "evidence_family": "gtos_vnext_pre_ai_post_l2_routing_policy",
                    "system_surface": "pre_ai_post_l2_ai_routing_policy",
                    "source_component": policy["source_component"],
                    "decision": policy["decision"],
                    "review_action": policy["decision"],
                    "action_class": policy["action_class"],
                    "runtime_effect_now": policy["runtime_effect_now"],
                    "implementation_action": policy["implementation_action"],
                    "runtime_candidate_use_permitted": policy["decision"] == "FOLLOW",
                    "candidate_use_allowed_now": False,
                    "runtime_score_allowed": policy["decision"] == "FOLLOW",
                    "live_effect": False,
                    "validation_safe": policy["decision"] != "AVOID",
                    "r_evidence_class": policy["r_evidence_class"],
                    "route_family": "mechanical_ai_selector",
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "market": symbol,
                    "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
                    "route_session": route_session,
                    "side": side,
                    "timeframe": timeframe,
                    "market_timeframe": timeframe,
                    "horizon_id": "",
                    "entry_variant": "",
                    "primitive": "",
                    "target_stop_order_class": "",
                    "event_scope": event_scope,
                    "detected_symbols": [value for value in symbols if value],
                    "detected_timeframes": timeframes,
                    "detected_sessions": sessions,
                    "detected_sides": sides,
                    "source_rows_represented": represented,
                    "source_event_rows": represented,
                    "row_bearing_status": _norm(item.get("row_bearing_status")),
                    "source_conversion_state_before_wave": _norm(item.get("conversion_state")),
                    "source_remaining_action": _norm(item.get("remaining_action")),
                    "source_exact_reason": _norm(item.get("exact_reason")),
                    "source_real_dependency": _norm(item.get("real_dependency")),
                    "r_metrics": {
                        "effective_n": _metric(
                            represented,
                            source_field="batch_unit_row_count",
                            source_shape="batch_unit_disposition",
                        ),
                        "proxy_score": _metric(
                            proxy_score,
                            source_field="policy_token_classification",
                            source_shape="pre_ai_post_l2_routing_policy",
                        ),
                    },
                    "row_type": "PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROW",
                }
            )
    return rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_norm(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _list_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        values = row.get(field)
        if isinstance(values, list):
            for value in values:
                text = _norm(value)
                if text:
                    counts[text] += 1
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    anchors = (
        "symbol",
        "source_symbol",
        "market",
        "route_session",
        "side",
        "timeframe",
        "market_timeframe",
        "horizon_id",
        "entry_variant",
        "primitive",
        "target_stop_order_class",
    )
    return {
        field: blank
        for field in anchors
        if (blank := sum(1 for row in rows if _norm(row.get(field)) == ""))
    }


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    runtime_counts = Counter(row["source_path"] for row in rows)
    represented = Counter()
    source_components: dict[str, set[str]] = defaultdict(set)
    decisions: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        path = row["source_path"]
        represented[path] += int(row.get("source_rows_represented") or 0)
        source_components[path].add(row["source_component"])
        decisions[path][row["decision"]] += 1
        by_path.setdefault(
            path,
            {
                "path": path,
                "unit_id": row.get("source_unit_id", ""),
                "rows": 0,
                "runtime_rows_read": 0,
                "rows_represented": 0,
                "sha256_or_git_blob": row.get("source_artifact_hash", ""),
                "source_family": row.get("source_family", ""),
                "source_components": [],
                "decision_counts": {},
            },
        )
    for path, item in by_path.items():
        item["rows"] = represented[path]
        item["runtime_rows_read"] = runtime_counts[path]
        item["rows_represented"] = represented[path]
        item["source_components"] = sorted(source_components[path])
        item["decision_counts"] = dict(sorted(decisions[path].items()))
    return [by_path[path] for path in sorted(by_path)]


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = _source_artifacts(rows)
    family_counts: Counter[str] = Counter()
    family_rows: Counter[str] = Counter()
    for item in artifacts:
        family = _norm(item.get("source_family"))
        if family:
            family_counts[family] += 1
            family_rows[family] += int(item.get("rows_represented") or 0)
    return {
        "schema_version": "gtos_vnext_pre_ai_post_l2_routing_policy_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "output_rows": _path_text(OUTPUT_ROWS),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 0) for row in rows
        ),
        "wave_source_artifact_count": len(artifacts),
        "wave_unit_count": len(artifacts),
        "wave_source_rows_counted": sum(int(item.get("rows") or 0) for item in artifacts),
        "decision_counts": _counts(rows, "decision"),
        "source_family_counts": dict(sorted(family_counts.items())),
        "source_family_row_counts": dict(sorted(family_rows.items())),
        "source_component_counts": _counts(rows, "source_component"),
        "source_role_counts": _counts(rows, "source_role"),
        "action_class_counts": _counts(rows, "action_class"),
        "implementation_action_counts": _counts(rows, "implementation_action"),
        "r_evidence_class_counts": _counts(rows, "r_evidence_class"),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "markets": _counts(rows, "market"),
            "source_symbols": _counts(rows, "source_symbol"),
            "symbol_families": _counts(rows, "symbol_family"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "market_timeframes": _counts(rows, "market_timeframe"),
            "horizons": _counts(rows, "horizon_id"),
            "source_components": _counts(rows, "source_component"),
            "detected_symbols": _list_counts(rows, "detected_symbols"),
            "detected_timeframes": _list_counts(rows, "detected_timeframes"),
            "detected_sessions": _list_counts(rows, "detected_sessions"),
            "detected_sides": _list_counts(rows, "detected_sides"),
        },
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "source_artifacts": artifacts,
    }


def build(*, check: bool = False) -> dict[str, Any]:
    rows = _runtime_rows()
    summary = _summary(rows)
    row_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        if not OUTPUT_ROWS.exists():
            raise SystemExit(f"missing output rows: {OUTPUT_ROWS}")
        if not OUTPUT_SUMMARY.exists():
            raise SystemExit(f"missing output summary: {OUTPUT_SUMMARY}")
        if OUTPUT_ROWS.read_text(encoding="utf-8") != row_text:
            raise SystemExit(f"stale output rows: {OUTPUT_ROWS}")
        if OUTPUT_SUMMARY.read_text(encoding="utf-8") != summary_text:
            raise SystemExit(f"stale output summary: {OUTPUT_SUMMARY}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_ROWS.write_text(row_text, encoding="utf-8")
        OUTPUT_SUMMARY.write_text(summary_text, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))


if __name__ == "__main__":
    main()
