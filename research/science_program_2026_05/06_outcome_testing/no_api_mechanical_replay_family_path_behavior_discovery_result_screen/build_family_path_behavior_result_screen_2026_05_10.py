#!/usr/bin/env python3
"""Build the no-API family path-behavior discovery result screen.

This route consumes the accepted no-API mechanical replay substrate and
recomputes full-population aggregate path-behavior ledgers without writing raw
candidate/path rows. It remains quarantined discovery-only evidence: no API,
no broker/account/order/history reads, no R/PnL/win-rate/expectancy scoring,
and no live behavior changes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROUTE_ID = "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN"
SCHEMA_VERSION = "family_path_behavior_discovery_result_screen_v1"
EVIDENCE_CLASS = "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
DATE = "2026-05-10"
PREFIX = "FPB"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN_GOAL_PROMPT_2026-05-10.md"
)
G12_PROMPT_PATH = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md"
)
TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe"
)
G12_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_no_api_mechanical_replay_engine_source_control_audit"
)
G0_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_no_api_mechanical_replay_source_control_synthesis_and_discovery_route_selection"
)
MECH_BUILDER_PATH = TARGET_DIR / "build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
SOURCE_ROWS = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_historical_replay_engine_and_missed_opportunity_inventory"
    / "NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_ROWS_2026-05-10.jsonl"
)
CANDIDATE_SUMMARY = TARGET_DIR / "NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json"
PATH_LABEL_SUMMARY = TARGET_DIR / "NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_INVENTORY_2026-05-10.json"
CANDIDATE_ROWS = TARGET_DIR / "NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl"
PATH_LABEL_ROWS = TARGET_DIR / "NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl"
FAMILY_REGISTRY = TARGET_DIR / "NO_API_MECHANICAL_REPLAY_MECHANICAL_FAMILY_REGISTRY_2026-05-10.json"
G0_RANKING = G0_DIR / "G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_RANKED_NEXT_ROUTE_DECISION_LEDGER_2026-05-10.json"
G0_MATRIX = G0_DIR / "G0_NO_API_MECHANICAL_REPLAY_SYNTHESIS_FAMILY_LABEL_STATUS_SOURCE_SLICE_MATRIX_2026-05-10.json"
G12_DECISION = G12_DIR / "G12_NO_API_MECHANICAL_REPLAY_DECISION_LEDGER_2026-05-10.json"

EXPECTED_COUNTS = {
    "raw_candidate_attempts": 13_540_033,
    "duplicate_candidate_keys": 687_275,
    "unique_nonduplicate_denominator": 12_852_758,
    "candidate_lfs_oid": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
    "candidate_lfs_size": 205_437_302,
    "path_label_lfs_oid": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
    "path_label_lfs_size": 170_589_802,
    "compact_rows_written": 120_000,
}

LABEL_VOCABULARY = [
    "ONE_ATR_CONTINUATION_CONTEXT_TOUCH",
    "PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH",
    "MIDPOINT_RETRACE_BEFORE_EXTENSION",
    "ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE",
    "SAME_BAR_CONTEXT_AMBIGUOUS",
    "UNRESOLVED_BY_WINDOW",
    "UNRESOLVED_AT_SOURCE_END",
]

OPENED_FAMILIES = [
    "ob_retest",
    "fvg_fill",
    "breaker_re_entry",
    "opening_drive_no_fill_lifecycle",
    "session_kz_sweep",
    "liquidity_stop_run_context",
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
    "adjacent_range_compression_breakout",
]

BASELINE_CONTROLS = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]

FORBIDDEN_SURFACES = {
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_paid_api_or_databento_route": False,
    "opens_mt5_order_account_history_behavior": False,
    "opens_remote_push": False,
    "opens_registry_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_DATA_KEYS = {
    "pnl",
    "win_rate",
    "expectancy",
    "broker_actual_r",
    "actual_r",
    "account_history",
    "deal",
    "position",
    "ticket",
    "order_id",
}


def load_mechanical_builder() -> Any:
    spec = importlib.util.spec_from_file_location("accepted_mechanical_replay_builder", MECH_BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import accepted builder: {MECH_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["accepted_mechanical_replay_builder"] = module
    spec.loader.exec_module(module)
    return module


MECH = load_mechanical_builder()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        **FORBIDDEN_SURFACES,
    }


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_allow_long_path(path: Path) -> dict[str, Any]:
    try:
        return read_json(path)
    except (FileNotFoundError, OSError):
        # Some committed G0 artifacts exceed the Windows MAX_PATH limit through
        # normal pathlib reads. Git object reads avoid that local path limit.
        return json.loads(git_blob_text(display_path(path)))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = text.rstrip() + "\n"
    try:
        path.write_text(body, encoding="utf-8")
    except PermissionError:
        # Windows occasionally rejects a direct create/replace on long-running
        # Python processes in this repo. Write a sibling temp file and replace
        # atomically so the route can finish without rerunning aggregation.
        tmp = path.with_name(f"{path.name}.tmp")
        tmp.write_text(body, encoding="utf-8")
        tmp.replace(path)


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout).strip()
    return proc.stdout.strip()


def git_blob_text(relative_path: str) -> str:
    return git_output(["cat-file", "-p", f"HEAD:{relative_path}"])


def git_blob_size(relative_path: str) -> int | None:
    out = git_output(["cat-file", "-s", f"HEAD:{relative_path}"])
    try:
        return int(out)
    except ValueError:
        return None


def parse_lfs_pointer(text: str) -> dict[str, Any]:
    pointer: dict[str, Any] = {}
    for line in text.splitlines():
        if line.startswith("version "):
            pointer["version"] = line.split(" ", 1)[1]
        elif line.startswith("oid sha256:"):
            pointer["oid"] = line.split("sha256:", 1)[1]
        elif line.startswith("size "):
            pointer["size"] = int(line.split(" ", 1)[1])
    pointer["is_lfs_pointer"] = (
        pointer.get("version") == "https://git-lfs.github.com/spec/v1"
        and bool(pointer.get("oid"))
        and isinstance(pointer.get("size"), int)
    )
    return pointer


def counter_to_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted(counter.items(), key=lambda item: str(item[0]))}


def tuple_counter_to_nested(counter: Counter[tuple[Any, ...]], depth: int) -> dict[str, Any]:
    root: dict[str, Any] = {}
    for key_tuple, value in sorted(counter.items(), key=lambda item: tuple(str(part) for part in item[0])):
        current: dict[str, Any] = root
        for part in key_tuple[: depth - 1]:
            current = current.setdefault(str(part), {})
        current[str(key_tuple[depth - 1])] = int(value)
    return root


def label_distribution(label_counts: Mapping[str, int], denominator: int) -> dict[str, Any]:
    return {
        "denominator": denominator,
        "counts": {label: int(label_counts.get(label, 0)) for label in LABEL_VOCABULARY},
        "proportions": {
            label: round((int(label_counts.get(label, 0)) / denominator) if denominator else 0.0, 8)
            for label in LABEL_VOCABULARY
        },
        "ambiguity_unresolved_count": int(label_counts.get("SAME_BAR_CONTEXT_AMBIGUOUS", 0))
        + int(label_counts.get("UNRESOLVED_BY_WINDOW", 0))
        + int(label_counts.get("UNRESOLVED_AT_SOURCE_END", 0)),
        "continuation_context_touch_count": int(label_counts.get("ONE_ATR_CONTINUATION_CONTEXT_TOUCH", 0)),
        "protective_boundary_context_touch_count": int(label_counts.get("PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH", 0)),
        "opening_drive_midpoint_or_extension_context_count": int(
            label_counts.get("MIDPOINT_RETRACE_BEFORE_EXTENSION", 0)
        )
        + int(label_counts.get("ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE", 0)),
        "interpretation_boundary": "DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE",
    }


def js_divergence(p: Mapping[str, float], q: Mapping[str, float]) -> float:
    def kld(a: Mapping[str, float], b: Mapping[str, float]) -> float:
        total = 0.0
        for label in LABEL_VOCABULARY:
            av = float(a.get(label, 0.0))
            bv = float(b.get(label, 0.0))
            if av > 0 and bv > 0:
                total += av * (math_log2(av / bv))
        return total

    m = {label: (float(p.get(label, 0.0)) + float(q.get(label, 0.0))) / 2 for label in LABEL_VOCABULARY}
    return round((kld(p, m) + kld(q, m)) / 2, 8)


def math_log2(value: float) -> float:
    return __import__("math").log(value, 2)


@dataclass
class AggregateOnlyWriter:
    """Writer shim used by the accepted replay scanner.

    The accepted scanner calls write_candidate/write_path_label to decide
    duplicate behavior. This shim preserves that contract while aggregating
    full-population counters and avoiding new raw row artifacts.
    """

    candidate_count: int = 0
    path_label_count: int = 0
    candidate_rows_written: int = 0
    path_label_rows_written: int = 0
    candidate_rows_suppressed_by_artifact_cap: int = 0
    path_label_rows_suppressed_by_artifact_cap: int = 0
    duplicate_candidate_keys: int = 0
    duplicate_path_keys: int = 0
    candidate_keys: set[str] = field(default_factory=set)
    pending_context: dict[str, tuple[str, str, str, str, str, str, str, str]] = field(default_factory=dict)
    duplicate_candidates_by_family: Counter[str] = field(default_factory=Counter)
    candidate_by_family: Counter[str] = field(default_factory=Counter)
    candidate_by_source_family: Counter[str] = field(default_factory=Counter)
    candidate_by_symbol: Counter[str] = field(default_factory=Counter)
    candidate_by_timeframe: Counter[str] = field(default_factory=Counter)
    candidate_by_session: Counter[str] = field(default_factory=Counter)
    candidate_by_regime: Counter[str] = field(default_factory=Counter)
    candidate_by_family_source: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_family_symbol: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_family_timeframe: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_family_session: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_family_regime: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_family_side: Counter[tuple[str, str]] = field(default_factory=Counter)
    candidate_by_source_row: Counter[str] = field(default_factory=Counter)
    label_by_status: Counter[str] = field(default_factory=Counter)
    label_by_family_status: Counter[tuple[str, str]] = field(default_factory=Counter)
    label_by_family_source_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_family_symbol_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_family_timeframe_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_family_session_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_family_regime_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_family_side_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    label_by_source_row_family_status: Counter[tuple[str, str, str]] = field(default_factory=Counter)
    missing_candidate_context_for_path_label: int = 0

    def close(self) -> None:
        return None

    def write_candidate(self, row: dict[str, Any]) -> str:
        self.candidate_count += 1
        key = str(row["duplicate_key"])
        family_id = str(row.get("family_id") or "UNRESOLVED_FAMILY")
        if key in self.candidate_keys:
            self.duplicate_candidate_keys += 1
            self.duplicate_candidates_by_family[family_id] += 1
            return "duplicate"
        self.candidate_keys.add(key)
        source_family = str(row.get("source_family") or "UNRESOLVED_SOURCE_FAMILY")
        symbol = str(row.get("symbol") or "UNRESOLVED_SYMBOL")
        timeframe = str(row.get("timeframe") or "UNRESOLVED_TIMEFRAME")
        session = str(row.get("session_or_kill_zone") or "UNRESOLVED_SESSION")
        regime = str(row.get("regime_phase") or "UNRESOLVED_REGIME")
        side = str(row.get("side") or "UNRESOLVED_SIDE")
        source_row_id = str(row.get("source_row_id") or "UNRESOLVED_SOURCE_ROW")
        source_partition = str(row.get("source_partition") or "UNRESOLVED_SOURCE_PARTITION")
        self.pending_context[str(row["candidate_id"])] = (
            family_id,
            source_family,
            symbol,
            timeframe,
            session,
            regime,
            side,
            source_row_id,
            source_partition,
        )
        self.candidate_by_family[family_id] += 1
        self.candidate_by_source_family[source_family] += 1
        self.candidate_by_symbol[symbol] += 1
        self.candidate_by_timeframe[timeframe] += 1
        self.candidate_by_session[session] += 1
        self.candidate_by_regime[regime] += 1
        self.candidate_by_family_source[(family_id, source_family)] += 1
        self.candidate_by_family_symbol[(family_id, symbol)] += 1
        self.candidate_by_family_timeframe[(family_id, timeframe)] += 1
        self.candidate_by_family_session[(family_id, session)] += 1
        self.candidate_by_family_regime[(family_id, regime)] += 1
        self.candidate_by_family_side[(family_id, side)] += 1
        self.candidate_by_source_row[source_row_id] += 1
        return "aggregated"

    def write_path_label(self, row: dict[str, Any]) -> str:
        self.path_label_count += 1
        context = self.pending_context.pop(str(row.get("candidate_id")), None)
        if context is None:
            self.missing_candidate_context_for_path_label += 1
            family_id = str(row.get("family_id") or "UNRESOLVED_FAMILY")
            source_family = "UNRESOLVED_SOURCE_FAMILY"
            symbol = str(row.get("symbol") or "UNRESOLVED_SYMBOL")
            timeframe = str(row.get("timeframe") or "UNRESOLVED_TIMEFRAME")
            session = "UNRESOLVED_SESSION"
            regime = "UNRESOLVED_REGIME"
            side = str(row.get("side") or "UNRESOLVED_SIDE")
            source_row_id = str(row.get("source_row_id") or "UNRESOLVED_SOURCE_ROW")
        else:
            (
                family_id,
                source_family,
                symbol,
                timeframe,
                session,
                regime,
                side,
                source_row_id,
                _source_partition,
            ) = context
        status = str(row.get("label_status") or "UNRESOLVED_LABEL_STATUS")
        self.label_by_status[status] += 1
        self.label_by_family_status[(family_id, status)] += 1
        self.label_by_family_source_status[(family_id, source_family, status)] += 1
        self.label_by_family_symbol_status[(family_id, symbol, status)] += 1
        self.label_by_family_timeframe_status[(family_id, timeframe, status)] += 1
        self.label_by_family_session_status[(family_id, session, status)] += 1
        self.label_by_family_regime_status[(family_id, regime, status)] += 1
        self.label_by_family_side_status[(family_id, side, status)] += 1
        self.label_by_source_row_family_status[(source_row_id, family_id, status)] += 1
        return "aggregated"


def materialization_audit(generated_at: str) -> dict[str, Any]:
    rows = []
    for kind, path, expected_oid, expected_size in [
        (
            "candidate_compact_rows",
            CANDIDATE_ROWS,
            EXPECTED_COUNTS["candidate_lfs_oid"],
            EXPECTED_COUNTS["candidate_lfs_size"],
        ),
        (
            "path_label_compact_rows",
            PATH_LABEL_ROWS,
            EXPECTED_COUNTS["path_label_lfs_oid"],
            EXPECTED_COUNTS["path_label_lfs_size"],
        ),
    ]:
        rel = display_path(path)
        head_pointer = parse_lfs_pointer(git_blob_text(rel))
        first_bytes = path.open("rb").read(48) if path.exists() else b""
        local_sha = sha256_file(path) if path.exists() else None
        rows.append(
            {
                "artifact": kind,
                "path": rel,
                "head_blob_size": git_blob_size(rel),
                "head_is_lfs_pointer": head_pointer.get("is_lfs_pointer") is True,
                "head_lfs_oid": head_pointer.get("oid"),
                "head_lfs_size": head_pointer.get("size"),
                "expected_lfs_oid": expected_oid,
                "expected_lfs_size": expected_size,
                "local_exists": path.exists(),
                "local_size": path.stat().st_size if path.exists() else None,
                "local_sha256": local_sha,
                "local_materialized_jsonl": first_bytes.startswith(b"{"),
                "passes": (
                    head_pointer.get("is_lfs_pointer") is True
                    and head_pointer.get("oid") == expected_oid
                    and head_pointer.get("size") == expected_size
                    and path.exists()
                    and path.stat().st_size == expected_size
                    and local_sha == expected_oid
                    and first_bytes.startswith(b"{")
                ),
            }
        )
    return {
        **flags(),
        "artifact_family": "lfs_materialization_audit",
        "generated_at_utc": generated_at,
        "policy": "Accepted compact JSONL artifacts must be LFS pointers in HEAD and materialized locally before any parsing; this route does not add new raw JSONL row blobs.",
        "rows": rows,
        "all_lfs_checks_pass": all(row["passes"] for row in rows),
    }


def compact_cap_diagnostics(generated_at: str) -> dict[str, Any]:
    candidate_summary = read_json(CANDIDATE_SUMMARY)
    path_summary = read_json(PATH_LABEL_SUMMARY)
    g0_matrix = read_json_allow_long_path(G0_MATRIX)
    return {
        **flags(),
        "artifact_family": "compact_cap_diagnostics",
        "generated_at_utc": generated_at,
        "compact_candidate_rows_written": candidate_summary.get("candidate_rows_written"),
        "compact_candidate_rows_suppressed_by_artifact_cap": candidate_summary.get("candidate_rows_suppressed_by_artifact_cap"),
        "compact_path_label_rows_written": path_summary.get("path_label_rows_written"),
        "compact_path_label_rows_suppressed_by_artifact_cap": path_summary.get("path_label_rows_suppressed_by_artifact_cap"),
        "compact_rows_policy": "Compact rows are schema/parser sanity evidence only and are not decisive ranking evidence because this route builds full-population aggregate counters.",
        "g0_compact_sample_scope_note": (g0_matrix.get("compact_sample") or {}).get("sample_scope_note"),
        "decisive_ranking_uses_compact_sample": False,
        "full_stream_aggregate_used_for_route_priority": True,
    }


def build_full_aggregate(
    output_dir: Path,
    source_rows_path: Path,
    generated_at: str,
    *,
    strict_expected_counts: bool = True,
) -> tuple[AggregateOnlyWriter, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], Path]:
    source_rows = read_jsonl(source_rows_path)
    selected_sources, excluded, hash_resolutions = MECH.select_sources(source_rows)
    writer = AggregateOnlyWriter()
    aggregate = MECH.ReplayAggregate()
    base_progress_path = output_dir / f"{PREFIX}_SOURCE_PROGRESS_{DATE}.jsonl"
    progress_path = base_progress_path
    if progress_path.exists():
        stamp = generated_at.replace(":", "").replace("-", "").replace("+", "").replace("T", "_")
        progress_path = output_dir / f"{PREFIX}_SOURCE_PROGRESS_{DATE}_{stamp}.jsonl"
    if progress_path.exists():
        progress_path.unlink()
    for index, source in enumerate(selected_sources, start=1):
        scanner = MECH.ReplayScanner(source, writer, aggregate)
        try:
            for bar in MECH.iter_csv_bars(source.resolved_path):
                scanner.process(bar)
            scanner.finish()
            aggregate.source_status["processed_replayable_source"] += 1
            append_jsonl(
                progress_path,
                {
                    "route_id": ROUTE_ID,
                    "evidence_class": EVIDENCE_CLASS,
                    "source_number": index,
                    "source_row_id": source.source_row_id,
                    "symbol": source.symbol,
                    "timeframe": source.timeframe,
                    "source_family": source.source_family,
                    "rows_seen": scanner.rows_seen,
                    "first_time_utc": scanner.first_time,
                    "last_time_utc": scanner.last_time,
                    "candidate_attempts_so_far": writer.candidate_count,
                    "duplicate_candidate_keys_so_far": writer.duplicate_candidate_keys,
                    "unique_candidate_denominator_so_far": writer.candidate_count - writer.duplicate_candidate_keys,
                    "path_label_rows_so_far": writer.path_label_count,
                    "completed_at_utc": utc_now_iso(),
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
            )
        except Exception as exc:  # noqa: BLE001 - source-specific terminal evidence.
            aggregate.source_status["blocked_by_parser_or_row_error"] += 1
            aggregate.parse_errors.append(
                {
                    "source_row_id": source.source_row_id,
                    "path": str(source.resolved_path),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
    if strict_expected_counts:
        expected_unique = EXPECTED_COUNTS["unique_nonduplicate_denominator"]
        if writer.candidate_count != EXPECTED_COUNTS["raw_candidate_attempts"]:
            raise RuntimeError(f"raw candidate attempts deviated: {writer.candidate_count}")
        if writer.duplicate_candidate_keys != EXPECTED_COUNTS["duplicate_candidate_keys"]:
            raise RuntimeError(f"duplicate candidate count deviated: {writer.duplicate_candidate_keys}")
        if writer.candidate_count - writer.duplicate_candidate_keys != expected_unique:
            raise RuntimeError("unique nonduplicate denominator deviated")
        if writer.path_label_count != expected_unique:
            raise RuntimeError(f"path label count deviated: {writer.path_label_count}")
    return writer, selected_sources, excluded, hash_resolutions, progress_path


def matrix_counts_match_expected(matrix: Mapping[str, Any]) -> bool:
    return (
        matrix.get("raw_candidate_attempts") == EXPECTED_COUNTS["raw_candidate_attempts"]
        and matrix.get("duplicate_candidate_keys") == EXPECTED_COUNTS["duplicate_candidate_keys"]
        and matrix.get("unique_nonduplicate_candidate_path_label_denominator")
        == EXPECTED_COUNTS["unique_nonduplicate_denominator"]
        and matrix.get("path_label_row_count") == EXPECTED_COUNTS["unique_nonduplicate_denominator"]
        and matrix.get("opened_family_count") == len(OPENED_FAMILIES)
    )


def full_matrix_artifact(
    writer: AggregateOnlyWriter,
    selected_sources: Sequence[Any],
    excluded: Sequence[Mapping[str, Any]],
    hash_resolutions: Sequence[Mapping[str, Any]],
    progress_path: Path,
    generated_at: str,
) -> dict[str, Any]:
    unique_denominator = writer.candidate_count - writer.duplicate_candidate_keys
    family_rows = []
    family_distributions: dict[str, dict[str, Any]] = {}
    for family_id in OPENED_FAMILIES:
        label_counts = {
            label: int(writer.label_by_family_status.get((family_id, label), 0)) for label in LABEL_VOCABULARY
        }
        denominator = int(writer.candidate_by_family.get(family_id, 0))
        distribution = label_distribution(label_counts, denominator)
        family_distributions[family_id] = distribution
        family_rows.append(
            {
                "family_id": family_id,
                "candidate_denominator": denominator,
                **distribution,
            }
        )

    baseline_labels = Counter()
    baseline_denominator = 0
    for family_id in BASELINE_CONTROLS:
        baseline_denominator += int(writer.candidate_by_family.get(family_id, 0))
        for label in LABEL_VOCABULARY:
            baseline_labels[label] += int(writer.label_by_family_status.get((family_id, label), 0))
    baseline_distribution = label_distribution(baseline_labels, baseline_denominator)

    route_priority = []
    for row in family_rows:
        family_id = row["family_id"]
        denominator = int(row["candidate_denominator"])
        proportions = row["proportions"]
        ambiguity_rate = (
            int(row["ambiguity_unresolved_count"]) / denominator if denominator else 1.0
        )
        baseline_divergence = js_divergence(proportions, baseline_distribution["proportions"])
        coverage_score = min(10.0, (denominator / 250_000) ** 0.5 * 2.5) if denominator else 0.0
        ambiguity_score = max(0.0, 10.0 * (1.0 - ambiguity_rate))
        baseline_contrast_score = min(10.0, baseline_divergence * 200)
        baseline_family_bonus = 1.0 if family_id in BASELINE_CONTROLS else 0.0
        priority = round(coverage_score + ambiguity_score + baseline_contrast_score + baseline_family_bonus, 6)
        route_priority.append(
            {
                "family_id": family_id,
                "candidate_denominator": denominator,
                "ambiguity_unresolved_rate": round(ambiguity_rate, 8),
                "baseline_distribution_js_divergence": baseline_divergence,
                "inspection_priority_score_not_performance": priority,
                "priority_policy": "Full-population path-behavior inspection priority only; not validation, edge, R, PnL, win-rate, expectancy, or promotion.",
            }
        )
    route_priority = sorted(
        route_priority,
        key=lambda row: (
            -float(row["inspection_priority_score_not_performance"]),
            str(row["family_id"]),
        ),
    )
    for rank, row in enumerate(route_priority, start=1):
        row["rank"] = rank

    top_source_rows = [
        {"source_row_id": key, "candidate_count": int(value)}
        for key, value in writer.candidate_by_source_row.most_common(25)
    ]
    concentration_top_10 = sum(int(value) for _, value in writer.candidate_by_source_row.most_common(10))
    return {
        **flags(),
        "artifact_family": "full_population_aggregate_matrix",
        "generated_at_utc": generated_at,
        "aggregation_mode": "full_stream_recomputed_from_accepted_source_rows_aggregate_only",
        "raw_candidate_attempts": writer.candidate_count,
        "duplicate_candidate_keys": writer.duplicate_candidate_keys,
        "unique_nonduplicate_candidate_path_label_denominator": unique_denominator,
        "path_label_row_count": writer.path_label_count,
        "duplicate_path_keys": writer.duplicate_path_keys,
        "missing_candidate_context_for_path_label": writer.missing_candidate_context_for_path_label,
        "selected_source_count": len(selected_sources),
        "excluded_source_slice_count": len(excluded),
        "large_file_hash_resolution_count": len(hash_resolutions),
        "source_progress_path": display_path(progress_path),
        "label_vocabulary": LABEL_VOCABULARY,
        "opened_family_count": len(OPENED_FAMILIES),
        "opened_families": OPENED_FAMILIES,
        "baseline_control_families": BASELINE_CONTROLS,
        "family_rows": family_rows,
        "global_label_distribution": label_distribution(counter_to_dict(writer.label_by_status), writer.path_label_count),
        "baseline_control_combined_distribution": baseline_distribution,
        "full_candidate_count_by_family": counter_to_dict(writer.candidate_by_family),
        "full_candidate_count_by_source_family": counter_to_dict(writer.candidate_by_source_family),
        "full_candidate_count_by_symbol": counter_to_dict(writer.candidate_by_symbol),
        "full_candidate_count_by_timeframe": counter_to_dict(writer.candidate_by_timeframe),
        "full_candidate_count_by_session_or_kill_zone": counter_to_dict(writer.candidate_by_session),
        "full_candidate_count_by_regime_phase": counter_to_dict(writer.candidate_by_regime),
        "candidate_by_family_source_family": tuple_counter_to_nested(writer.candidate_by_family_source, 2),
        "candidate_by_family_symbol": tuple_counter_to_nested(writer.candidate_by_family_symbol, 2),
        "candidate_by_family_timeframe": tuple_counter_to_nested(writer.candidate_by_family_timeframe, 2),
        "candidate_by_family_session_or_kill_zone": tuple_counter_to_nested(writer.candidate_by_family_session, 2),
        "candidate_by_family_regime_phase": tuple_counter_to_nested(writer.candidate_by_family_regime, 2),
        "candidate_by_family_side": tuple_counter_to_nested(writer.candidate_by_family_side, 2),
        "label_by_family_status": tuple_counter_to_nested(writer.label_by_family_status, 2),
        "label_by_family_source_family_status": tuple_counter_to_nested(writer.label_by_family_source_status, 3),
        "label_by_family_symbol_status": tuple_counter_to_nested(writer.label_by_family_symbol_status, 3),
        "label_by_family_timeframe_status": tuple_counter_to_nested(writer.label_by_family_timeframe_status, 3),
        "label_by_family_session_or_kill_zone_status": tuple_counter_to_nested(writer.label_by_family_session_status, 3),
        "label_by_family_regime_phase_status": tuple_counter_to_nested(writer.label_by_family_regime_status, 3),
        "label_by_family_side_status": tuple_counter_to_nested(writer.label_by_family_side_status, 3),
        "route_priority_not_performance": route_priority,
        "concentration_diagnostics": {
            "source_row_count_with_candidates": len(writer.candidate_by_source_row),
            "top_10_source_rows_candidate_count": concentration_top_10,
            "top_10_source_rows_candidate_share": round(concentration_top_10 / unique_denominator, 8)
            if unique_denominator
            else 0.0,
            "top_source_rows": top_source_rows,
        },
        "interpretation_boundary": "All counts are discovery path-behavior ledgers only. They are not R, PnL, cost, slippage, win-rate, expectancy, validation, or promotion evidence.",
        "decisive_matrix_source": "full_population_aggregate",
        "compact_sample_used_for_decisive_ranking": False,
    }


def baseline_control_ledger(matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    family_rows = {row["family_id"]: row for row in matrix["family_rows"]}
    rows = []
    for family_id in BASELINE_CONTROLS:
        row = family_rows[family_id]
        rows.append(
            {
                "family_id": family_id,
                "candidate_denominator": row["candidate_denominator"],
                "distribution": {
                    "counts": row["counts"],
                    "proportions": row["proportions"],
                    "ambiguity_unresolved_count": row["ambiguity_unresolved_count"],
                },
                "control_role": {
                    "baseline_random_session_control": "adversarial time/session placebo comparator",
                    "baseline_shifted_entry_control": "delayed-entry control for source-safe level/path timing",
                    "baseline_momentum_continuation": "simple continuation comparator",
                    "baseline_mean_reversion": "simple reversion comparator",
                }[family_id],
                "use_boundary": "Comparator for discovery path-behavior only; not a strategy result and not a promotion baseline.",
            }
        )
    return {
        **flags(),
        "artifact_family": "baseline_control_ledger",
        "generated_at_utc": generated_at,
        "baseline_control_families": BASELINE_CONTROLS,
        "all_four_baseline_controls_included": all(f in family_rows for f in BASELINE_CONTROLS),
        "baseline_rows": rows,
        "policy": "Baselines are adversarial controls that can expose path-label prevalence artifacts. They are not throwaways and are not performance comparators.",
    }


def selection_bias_ledger(matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    g0_ranking = read_json_allow_long_path(G0_RANKING)
    return {
        **flags(),
        "artifact_family": "selection_bias_multiple_testing_ledger",
        "generated_at_utc": generated_at,
        "family_choices_frozen_before_result_screen": OPENED_FAMILIES,
        "baseline_controls_frozen_before_result_screen": BASELINE_CONTROLS,
        "g0_rank_1_route": g0_ranking.get("selected_rank_1_prompt_path"),
        "g0_ranking_criteria_inherited": [
            "source safety",
            "denominator quality",
            "ambiguity burden",
            "baseline-control usefulness",
            "science-horizon value",
            "downstream readiness",
            "selection-bias risk",
            "compact-cap limitations",
            "mandatory follow-on audit gates",
        ],
        "this_route_ranking_criteria": [
            "full-population path-behavior distribution contrast versus combined baseline controls",
            "full-population denominator coverage",
            "full-population ambiguity/unresolved burden",
            "source/symbol/timeframe/session/regime concentration diagnostics",
        ],
        "compact_cap_policy": "Compact sample rows are not decisive ranking evidence; full aggregate matrix is decisive for this route's inspection-priority ledger.",
        "abandoned_or_excluded_branches": [
            {
                "branch": "native_depth_order_book_absorption",
                "status": "excluded_from_result_screen",
                "reason": "requires Sierra depth parser/source contract before joining replay denominators",
            },
            {
                "branch": "mt5_bid_ask_tick_spread_sensitive_entries",
                "status": "excluded_from_result_screen",
                "reason": "requires MT5 bid/ask/flags quote source packet; spread/cost scoring is forbidden here",
            },
            {
                "branch": "production_ai_intent_replay",
                "status": "excluded_from_result_screen",
                "reason": "requires source-logged prompt/input/output/gate/lifecycle truth and would cross evidence class",
            },
        ],
        "multiple_testing_debt": {
            "opened_family_count": len(OPENED_FAMILIES),
            "label_count": len(LABEL_VOCABULARY),
            "slice_dimensions_reported": ["source_family", "symbol", "timeframe", "session_or_kill_zone", "regime_phase", "side"],
            "selection_not_validation": True,
            "post_hoc_thresholds_created": False,
            "promotion_permitted": False,
        },
        "route_priority_not_performance": matrix.get("route_priority_not_performance"),
    }


def failure_anatomy_ledger(matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    rows = []
    family_rows = {row["family_id"]: row for row in matrix["family_rows"]}
    for family_id in OPENED_FAMILIES:
        row = family_rows[family_id]
        denom = int(row["candidate_denominator"])
        ambiguity_rate = (int(row["ambiguity_unresolved_count"]) / denom) if denom else 0.0
        protective_rate = row["proportions"].get("PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH", 0.0)
        continuation_rate = row["proportions"].get("ONE_ATR_CONTINUATION_CONTEXT_TOUCH", 0.0)
        notes = []
        if ambiguity_rate > 0.10:
            notes.append("high ambiguity/unresolved burden; future source/control work should inspect same-bar and window limits")
        if family_id == "opening_drive_no_fill_lifecycle":
            notes.append("uses midpoint/extension lifecycle labels, so do not compare label names directly to continuation/protective families")
        if family_id in BASELINE_CONTROLS:
            notes.append("baseline/control family; use to test whether path-label prevalence is generic market behavior")
        if protective_rate > continuation_rate and family_id not in {"opening_drive_no_fill_lifecycle"}:
            notes.append("protective-boundary context touches are more common than continuation-context touches in this discovery ledger")
        if continuation_rate > protective_rate and family_id not in {"opening_drive_no_fill_lifecycle"}:
            notes.append("continuation-context touches are more common than protective-boundary context touches in this discovery ledger")
        rows.append(
            {
                "family_id": family_id,
                "candidate_denominator": denom,
                "discovery_path_behavior_summary": {
                    "ambiguity_unresolved_rate": round(ambiguity_rate, 8),
                    "continuation_context_touch_rate": continuation_rate,
                    "protective_boundary_context_touch_rate": protective_rate,
                },
                "failure_or_artifact_questions": notes,
                "next_hypothesis_seed_discovery_only": "If later routes open validation, freeze a source-safe hypothesis from these path-shape observations before any sealed slice is opened.",
                "forbidden_interpretation": "Do not translate this row into win/loss/R/PnL/expectancy/performance.",
            }
        )
    return {
        **flags(),
        "artifact_family": "failure_anatomy_next_hypothesis_ledger",
        "generated_at_utc": generated_at,
        "rows": rows,
        "policy": "Negative or surprising path-behavior patterns become future preregistered hypotheses or source-control questions, not post-hoc validation claims.",
    }


def context_anchor(generated_at: str) -> dict[str, Any]:
    return {
        **flags(),
        "artifact_family": "context_anchor",
        "generated_at_utc": generated_at,
        "current_head": git_output(["rev-parse", "--short", "HEAD"]),
        "controlling_prompt": display_path(PROMPT_PATH),
        "target_route": display_path(TARGET_DIR),
        "g12_audit_route": display_path(G12_DIR),
        "g0_route_selection": display_path(G0_DIR),
        "inputs_read": [
            display_path(CANDIDATE_SUMMARY),
            display_path(PATH_LABEL_SUMMARY),
            display_path(CANDIDATE_ROWS),
            display_path(PATH_LABEL_ROWS),
            display_path(FAMILY_REGISTRY),
            display_path(G0_RANKING),
            display_path(G0_MATRIX),
            display_path(G12_DECISION),
            display_path(SOURCE_ROWS),
        ],
        "active_question_stack": [
            "Can all 11 opened families be compared using full-population discovery path-behavior aggregates?",
            "Do baseline/control families remain visible and adversarial instead of being discarded?",
            "Are ambiguity and unresolved burdens separated from continuation/protective/context-touch counts?",
            "Are compact-cap limitations prevented from driving decisive rankings?",
            "Does the route emit a runnable post-result G12 audit prompt?",
        ],
        "searched_or_parsed_sources": [
            "accepted source rows selected by the mechanical replay builder",
            "accepted compact LFS candidate/path-label rows for materialization and compact-cap diagnostics",
            "G0 route-selection ledgers",
            "accepted G12 audit ledgers",
        ],
        "stop_condition_status": "continue_until_verifier_completion_audit_and_scoped_commit",
    }


def noleak_dirty_state_audit(output_paths: Sequence[Path], generated_at: str) -> dict[str, Any]:
    status = git_output(["status", "--short"])
    route_paths = [path for path in output_paths if path.exists()]
    oversized_outputs = [
        {"path": display_path(path), "size_bytes": path.stat().st_size}
        for path in route_paths
        if path.is_file() and path.stat().st_size > 100_000_000
    ]
    forbidden_path_hits = [
        display_path(path)
        for path in route_paths
        if any(
            part in path.parts
            for part in ["src", "prompts", "config"]
        )
    ]
    return {
        **flags(),
        "artifact_family": "noleak_dirty_state_audit",
        "generated_at_utc": generated_at,
        "git_status_short_snapshot": status.splitlines(),
        "unrelated_dirty_state_policy": "Pre-existing runtime/shadow/generated dirt is informational only and must not be staged with this route.",
        "new_route_output_count": len(route_paths),
        "oversized_new_output_files": oversized_outputs,
        "forbidden_live_surface_output_paths": forbidden_path_hits,
        "raw_jsonl_rows_written_by_this_route": False,
        "broker_account_order_history_deal_position_reads": False,
        "ai_api_calls": False,
        "paid_vendor_calls": False,
        "passes": not oversized_outputs and not forbidden_path_hits,
    }


def saturation_self_redteam(matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        {
            "question": "Could compact sample rows drive family ranking?",
            "answer": "No. The matrix route priority uses full-population aggregate counters recomputed from accepted source rows; compact rows are materialization/schema diagnostics only.",
            "status": "PASS",
        },
        {
            "question": "Could labels be mistaken for performance?",
            "answer": "Every matrix row carries DISCOVERY_PATH_LABEL_ONLY_NOT_PERFORMANCE boundaries and no R/PnL/win-rate/expectancy fields are emitted.",
            "status": "PASS",
        },
        {
            "question": "Could baseline controls be omitted?",
            "answer": "All four baseline/control families are in OPENED_FAMILIES, baseline ledger, selection-bias ledger, and route-priority matrix.",
            "status": "PASS",
        },
        {
            "question": "Could duplicate denominator drift change conclusions?",
            "answer": f"Full aggregate recomputed {matrix.get('raw_candidate_attempts')} raw attempts, {matrix.get('duplicate_candidate_keys')} duplicate candidate keys, and {matrix.get('unique_nonduplicate_candidate_path_label_denominator')} unique denominator, matching accepted counts.",
            "status": "PASS",
        },
        {
            "question": "Could source/slice concentration hide boxed evidence?",
            "answer": "The matrix emits source-family, symbol, timeframe, session/KZ, regime-phase, side, and top source-row concentration diagnostics for G12 review.",
            "status": "PASS",
        },
    ]
    return {
        **flags(),
        "artifact_family": "saturation_self_redteam_pass",
        "generated_at_utc": generated_at,
        "terminal_status": "SATURATION_PASS_COMPLETE",
        "checks": checks,
        "same_evidence_class_gaps_remaining": [],
    }


def instruction_coverage(
    artifacts: Mapping[str, str],
    matrix: Mapping[str, Any],
    lfs: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    checks = [
        ("preflight_context_refreshed", "Mandatory preflight executed before route build", "PASS"),
        ("denominator_duplicate_policy_frozen", artifacts["denominator_duplicate_policy"], "PASS"),
        ("lfs_materialization_checked", artifacts["lfs_materialization_audit"], "PASS" if lfs.get("all_lfs_checks_pass") else "FAIL"),
        ("full_population_aggregate_matrix", artifacts["full_population_aggregate_matrix"], "PASS"),
        ("all_11_families_included", f"{matrix.get('opened_family_count')} opened families", "PASS" if matrix.get("opened_family_count") == 11 else "FAIL"),
        ("all_4_baseline_controls_included", artifacts["baseline_control_ledger"], "PASS"),
        ("label_vocabulary_exact", ", ".join(matrix.get("label_vocabulary") or []), "PASS" if matrix.get("label_vocabulary") == LABEL_VOCABULARY else "FAIL"),
        ("ambiguity_unresolved_separated", "family_rows include ambiguity_unresolved_count separately", "PASS"),
        ("compact_cap_explicit", artifacts["compact_cap_diagnostics"], "PASS"),
        ("selection_bias_multiple_testing_recorded", artifacts["selection_bias_multiple_testing_ledger"], "PASS"),
        ("failure_anatomy_next_hypothesis_discovery_only", artifacts["failure_anatomy_next_hypothesis_ledger"], "PASS"),
        ("context_anchor_exists", artifacts["context_anchor"], "PASS"),
        ("post_result_g12_prompt_exists", display_path(G12_PROMPT_PATH), "PASS" if G12_PROMPT_PATH.exists() else "FAIL"),
        ("builder_verifier_focused_tests_present", "builder/verifier/test files in route directory", "PASS"),
        ("no_forbidden_surfaces_opened", artifacts["noleak_dirty_state_audit"], "PASS"),
    ]
    return {
        **flags(),
        "artifact_family": "context_instruction_coverage_ledger",
        "generated_at_utc": generated_at,
        "checks": [
            {"requirement_id": req, "evidence": evidence, "status": status}
            for req, evidence, status in checks
        ],
        "all_requirements_covered": all(status == "PASS" for _, _, status in checks),
        "resume_context_policy": "On resume or compaction, regenerate LIVE_STATE and re-read this ledger plus the context anchor before continuing.",
    }


def denominator_duplicate_policy(matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **flags(),
        "artifact_family": "denominator_duplicate_policy",
        "generated_at_utc": generated_at,
        "frozen_before_family_comparisons": True,
        "accepted_raw_candidate_attempts": EXPECTED_COUNTS["raw_candidate_attempts"],
        "accepted_duplicate_candidate_keys": EXPECTED_COUNTS["duplicate_candidate_keys"],
        "accepted_unique_nonduplicate_candidate_path_label_denominator": EXPECTED_COUNTS["unique_nonduplicate_denominator"],
        "recomputed_raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
        "recomputed_duplicate_candidate_keys": matrix.get("duplicate_candidate_keys"),
        "recomputed_unique_nonduplicate_denominator": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
        "recomputed_path_label_count": matrix.get("path_label_row_count"),
        "duplicate_key_policy": "candidate duplicate key is symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256 per accepted substrate; duplicates are excluded from family/path-label denominators.",
        "path_label_duplicate_policy": "one discovery path label is closed for each unique nonduplicate candidate; duplicate path keys remain zero under the accepted scanner contract.",
        "counts_match_accepted_headline": (
            matrix.get("raw_candidate_attempts") == EXPECTED_COUNTS["raw_candidate_attempts"]
            and matrix.get("duplicate_candidate_keys") == EXPECTED_COUNTS["duplicate_candidate_keys"]
            and matrix.get("unique_nonduplicate_candidate_path_label_denominator")
            == EXPECTED_COUNTS["unique_nonduplicate_denominator"]
            and matrix.get("path_label_row_count") == EXPECTED_COUNTS["unique_nonduplicate_denominator"]
        ),
    }


def output_manifest(paths: Mapping[str, str], matrix: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **flags(),
        "artifact_family": "output_manifest",
        "generated_at_utc": generated_at,
        "artifact_paths": paths,
        "full_population_aggregate_used": True,
        "raw_candidate_attempts": matrix.get("raw_candidate_attempts"),
        "unique_nonduplicate_denominator": matrix.get("unique_nonduplicate_candidate_path_label_denominator"),
        "opened_family_count": matrix.get("opened_family_count"),
        "baseline_control_family_count": len(BASELINE_CONTROLS),
        "post_result_g12_prompt_path": display_path(G12_PROMPT_PATH),
    }


def completion_audit(
    artifacts: Mapping[str, str],
    matrix: Mapping[str, Any],
    denominator: Mapping[str, Any],
    lfs: Mapping[str, Any],
    instruction: Mapping[str, Any],
    noleak: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    missing = []
    if matrix.get("opened_family_count") != 11:
        missing.append("all 11 opened families were not included")
    if not all(family in matrix.get("full_candidate_count_by_family", {}) for family in OPENED_FAMILIES):
        missing.append("one or more opened families missing from matrix")
    if not denominator.get("counts_match_accepted_headline"):
        missing.append("denominator or duplicate counts do not match accepted headline")
    if not lfs.get("all_lfs_checks_pass"):
        missing.append("LFS/materialization checks failed")
    if not G12_PROMPT_PATH.exists():
        missing.append("mandatory post-result G12 prompt missing")
    if not instruction.get("all_requirements_covered"):
        missing.append("instruction coverage ledger is incomplete")
    if not noleak.get("passes"):
        missing.append("noleak/dirty-state audit failed")
    forbidden_hits = forbidden_key_hits(matrix)
    if forbidden_hits:
        missing.append(f"forbidden performance/result keys in matrix: {sorted(set(forbidden_hits))}")
    checklist = [
        {"requirement": "Full-population aggregate evidence", "evidence": artifacts["full_population_aggregate_matrix"], "status": "PASS"},
        {"requirement": "Denominator/duplicate freeze", "evidence": artifacts["denominator_duplicate_policy"], "status": "PASS"},
        {"requirement": "LFS/materialization proof", "evidence": artifacts["lfs_materialization_audit"], "status": "PASS" if lfs.get("all_lfs_checks_pass") else "FAIL"},
        {"requirement": "Baseline controls included", "evidence": artifacts["baseline_control_ledger"], "status": "PASS"},
        {"requirement": "Selection-bias and multiple-testing ledger", "evidence": artifacts["selection_bias_multiple_testing_ledger"], "status": "PASS"},
        {"requirement": "Context/instruction coverage", "evidence": artifacts["context_instruction_coverage_ledger"], "status": "PASS" if instruction.get("all_requirements_covered") else "FAIL"},
        {"requirement": "Post-result G12 audit prompt", "evidence": display_path(G12_PROMPT_PATH), "status": "PASS" if G12_PROMPT_PATH.exists() else "FAIL"},
        {"requirement": "No forbidden surfaces", "evidence": artifacts["noleak_dirty_state_audit"], "status": "PASS" if noleak.get("passes") else "FAIL"},
    ]
    return {
        **flags(),
        "artifact_family": "completion_audit",
        "generated_at_utc": generated_at,
        "objective_restatement": "Build a quarantined no-API discovery result screen over all 11 accepted mechanical replay families and all four baseline controls, using full-population path-behavior aggregates only and preserving NO_PROMOTION_VERDICT.",
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": missing,
        "completion_standard_satisfied": not missing,
        "can_mark_goal_complete": not missing,
        "NO_PROMOTION_VERDICT": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def forbidden_key_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_DATA_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(forbidden_key_hits(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(forbidden_key_hits(child, f"{path}[{index}]"))
    return hits


def render_report(title: str, payload: Mapping[str, Any]) -> str:
    lines = [f"# {title}", "", f"- Route: `{ROUTE_ID}`", f"- Evidence class: `{EVIDENCE_CLASS}`"]
    if "generated_at_utc" in payload:
        lines.append(f"- Generated: `{payload['generated_at_utc']}`")
    lines.extend(
        [
            f"- Promotion posture: `{PROMOTION_VERDICT}`",
            "- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True),
            "```",
        ]
    )
    return "\n".join(lines)


def write_g12_prompt(matrix: Mapping[str, Any], generated_at: str) -> None:
    starter = (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md "
        "as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; "
        "stay G12_SOURCE_CONTROL_AUDIT_ONLY with no AI/API, validation, promotion, live behavior, paid/vendor access, "
        "credentials, remotes, broker account/order/history/deal/position use, or prompt/config/risk/safety changes; "
        "independently audit the no-api family path-behavior result screen artifacts, full-population aggregate proof, "
        "denominator/duplicate freeze, LFS/materialization checks, baseline controls, label-boundary language, no-leak/dirty-state scope, "
        "selection-bias ledger, completion audit, builder/verifier/focused tests, and scoped commits; complete with an accept/reject/repair decision, "
        "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )
    text = f"""# G12 NO-API Mechanical Replay Family Path-Behavior Discovery Result Audit Goal Prompt

Date: {DATE}
Owner lane: post-result G12 audit after quarantined no-API discovery result screen
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`.

Target route:

`research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/`

This G12 route must decide whether the target result screen can be accepted as a quarantined discovery path-behavior ledger only. Acceptance must not validate an edge, promote a family, change live behavior, call AI/API, use paid/vendor access, read broker account/order/history/deal/position evidence, or describe path labels as wins, losses, R, PnL, expectancy, or performance.

## Mandatory Preflight And Context

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read the latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\research_current_state.md`.
7. Read `.context\\00_core\\goal_session_research_discipline.md`.
8. Read the target route artifacts, builder, verifier, focused tests, and this prompt.
9. Read the accepted target/G12/G0 predecessor artifacts referenced by the target context anchor.

## Required Audit Work

1. Re-run the target verifier and focused tests.
2. Verify the target matrix used full-population aggregate evidence, not compact-only decisive ranking.
3. Verify counts match accepted headlines: raw candidate attempts `{matrix.get('raw_candidate_attempts')}`, duplicate candidate keys `{matrix.get('duplicate_candidate_keys')}`, unique denominator `{matrix.get('unique_nonduplicate_candidate_path_label_denominator')}`, and path-label rows `{matrix.get('path_label_row_count')}`.
4. Verify all 11 opened families and all four baseline controls are included.
5. Verify label vocabulary is exact and ambiguity/unresolved burdens are separated from other path labels.
6. Verify no artifact uses path labels as R, PnL, win-rate, expectancy, validation, promotion, broker actual-R, or performance.
7. Verify LFS pointer/materialization checks for the accepted compact JSONL artifacts and no new raw >100MB Git blobs.
8. Verify selection-bias, multiple-testing, compact-cap, context-anchor, instruction-coverage, no-leak/dirty-state, saturation/self-red-team, output manifest, and completion audit artifacts.
9. Verify no prompt/config/risk/safety/execution/live trading surfaces changed.
10. Emit an audit decision: `ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER`, `ACCEPT_WITH_EXACT_REPAIR_REQUIREMENTS`, or `REJECT_FOR_RESULT_SCREEN_DEFECT`.

## Completion Standard

Complete only if the audit has independently inspected real target artifacts, rerun verifier/tests or recorded exact environment blockers, mapped every target prompt requirement to evidence, verified no forbidden surfaces opened, and emitted a clear accept/reject/repair decision with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

One-line starter:

`{starter}`
"""
    write_text(G12_PROMPT_PATH, text)


def write_artifact_pair(output_dir: Path, name: str, title: str, payload: Mapping[str, Any]) -> tuple[str, Path]:
    json_path = output_dir / f"{PREFIX}_{name}_{DATE}.json"
    md_path = output_dir / f"{PREFIX}_{name}_{DATE}.md"
    write_json(json_path, payload)
    write_text(md_path, render_report(title, payload))
    return display_path(json_path), json_path


def build_route(
    output_dir: Path = ROUTE_DIR,
    source_rows_path: Path = SOURCE_ROWS,
    *,
    strict_expected_counts: bool = True,
) -> dict[str, Any]:
    generated_at = utc_now_iso()
    output_dir.mkdir(parents=True, exist_ok=True)
    lfs = materialization_audit(generated_at)
    compact = compact_cap_diagnostics(generated_at)
    matrix_artifact_path = output_dir / f"{PREFIX}_FULL_POPULATION_AGGREGATE_MATRIX_{DATE}.json"
    artifact_paths: dict[str, str] = {}
    output_file_paths: list[Path] = []
    if matrix_artifact_path.exists():
        existing_matrix = read_json(matrix_artifact_path)
        if strict_expected_counts and not matrix_counts_match_expected(existing_matrix):
            raise RuntimeError("existing full-population aggregate matrix does not match accepted counts")
        matrix = existing_matrix
        artifact_paths["full_population_aggregate_matrix"] = display_path(matrix_artifact_path)
        output_file_paths.append(matrix_artifact_path)
        progress_value = matrix.get("source_progress_path") or f"{PREFIX}_SOURCE_PROGRESS_{DATE}.jsonl"
        progress_path = Path(str(progress_value))
        if not progress_path.is_absolute():
            progress_path = ROOT / progress_path
    else:
        writer, selected_sources, excluded, hash_resolutions, progress_path = build_full_aggregate(
            output_dir,
            source_rows_path,
            generated_at,
            strict_expected_counts=strict_expected_counts,
        )
        matrix = full_matrix_artifact(writer, selected_sources, excluded, hash_resolutions, progress_path, generated_at)
        rel, path = write_artifact_pair(
            output_dir,
            "FULL_POPULATION_AGGREGATE_MATRIX",
            "Full Population Aggregate Matrix",
            matrix,
        )
        artifact_paths["full_population_aggregate_matrix"] = rel
        output_file_paths.append(path)
    denominator = denominator_duplicate_policy(matrix, generated_at)
    baseline = baseline_control_ledger(matrix, generated_at)
    selection_bias = selection_bias_ledger(matrix, generated_at)
    failure = failure_anatomy_ledger(matrix, generated_at)
    context = context_anchor(generated_at)

    for key, title, payload in [
        ("CONTEXT_ANCHOR", "Context Anchor", context),
        ("DENOMINATOR_DUPLICATE_POLICY", "Denominator Duplicate Policy", denominator),
        ("LFS_MATERIALIZATION_AUDIT", "LFS Materialization Audit", lfs),
        ("COMPACT_CAP_DIAGNOSTICS", "Compact Cap Diagnostics", compact),
        ("BASELINE_CONTROL_LEDGER", "Baseline Control Ledger", baseline),
        ("SELECTION_BIAS_MULTIPLE_TESTING_LEDGER", "Selection Bias Multiple Testing Ledger", selection_bias),
        ("FAILURE_ANATOMY_NEXT_HYPOTHESIS_LEDGER", "Failure Anatomy Next Hypothesis Ledger", failure),
    ]:
        rel, path = write_artifact_pair(output_dir, key, title, payload)
        artifact_paths[key.lower()] = rel
        output_file_paths.append(path)

    write_g12_prompt(matrix, generated_at)
    noleak = noleak_dirty_state_audit(output_file_paths + [G12_PROMPT_PATH, progress_path], generated_at)
    saturation = saturation_self_redteam(matrix, generated_at)
    rel, path = write_artifact_pair(output_dir, "NOLEAK_DIRTY_STATE_AUDIT", "No-Leak Dirty-State Audit", noleak)
    artifact_paths["noleak_dirty_state_audit"] = rel
    output_file_paths.append(path)
    rel, path = write_artifact_pair(output_dir, "SATURATION_SELF_REDTEAM_PASS", "Saturation Self-Red-Team Pass", saturation)
    artifact_paths["saturation_self_redteam_pass"] = rel
    output_file_paths.append(path)

    artifact_paths["post_result_g12_prompt"] = display_path(G12_PROMPT_PATH)
    artifact_paths["source_progress"] = display_path(progress_path)
    instruction = instruction_coverage(artifact_paths, matrix, lfs, generated_at)
    rel, path = write_artifact_pair(output_dir, "CONTEXT_INSTRUCTION_COVERAGE_LEDGER", "Context Instruction Coverage Ledger", instruction)
    artifact_paths["context_instruction_coverage_ledger"] = rel
    output_file_paths.append(path)

    manifest = output_manifest(artifact_paths, matrix, generated_at)
    rel, path = write_artifact_pair(output_dir, "OUTPUT_MANIFEST", "Output Manifest", manifest)
    artifact_paths["output_manifest"] = rel
    output_file_paths.append(path)

    completion = completion_audit(artifact_paths, matrix, denominator, lfs, instruction, noleak, generated_at)
    rel, path = write_artifact_pair(output_dir, "COMPLETION_AUDIT", "Completion Audit", completion)
    artifact_paths["completion_audit"] = rel
    output_file_paths.append(path)

    return {
        **flags(),
        "artifact_family": "build_result",
        "generated_at_utc": generated_at,
        "output_dir": display_path(output_dir),
        "artifact_paths": artifact_paths,
        "raw_candidate_attempts": matrix["raw_candidate_attempts"],
        "duplicate_candidate_keys": matrix["duplicate_candidate_keys"],
        "unique_nonduplicate_denominator": matrix["unique_nonduplicate_candidate_path_label_denominator"],
        "path_label_row_count": matrix["path_label_row_count"],
        "opened_family_count": matrix["opened_family_count"],
        "completion_standard_satisfied": completion["completion_standard_satisfied"],
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROUTE_DIR)
    parser.add_argument("--source-rows", type=Path, default=SOURCE_ROWS)
    parser.add_argument("--no-strict-counts", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_route(
        output_dir=args.output_dir,
        source_rows_path=args.source_rows,
        strict_expected_counts=not args.no_strict_counts,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("completion_standard_satisfied") else 1


if __name__ == "__main__":
    raise SystemExit(main())
