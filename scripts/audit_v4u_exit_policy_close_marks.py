#!/usr/bin/env python3
"""Audit V4U stale/time-stop exit close-mark materialization requirements."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator, Mapping


GZIP_MAGIC = b"\x1f\x8b"
CLOSE_MARK_GAP_STATUS = "exit_policy_close_mark_source_gap_result_unadjusted"
CLOSE_MARK_BOUND_STATUS = "exit_policy_close_mark_replay_bound"
CLOSE_MARK_ACTIONS = {"CLOSE_STALE_THESIS", "CLOSE_TIME_STOP"}
REQUIRED_CLOSE_MARK_FIELDS = (
    "close_mark_r",
    "close_time_utc",
    "action",
    "close_reason",
    "bars_elapsed",
    "policy_id",
    "source_status",
    "source_path",
    "source_sha256",
)


def is_gzip(path: Path) -> bool:
    if path.suffix == ".gz":
        return True
    if not path.exists() or path.stat().st_size < 2:
        return False
    with path.open("rb") as handle:
        return handle.read(2) == GZIP_MAGIC


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if is_gzip(path) else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                yield row


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_close_mark_rows(result_ledger: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    action_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    bound_rows: list[dict[str, Any]] = []
    for row in iter_jsonl(result_ledger):
        if row.get("exit_policy_action") not in CLOSE_MARK_ACTIONS:
            continue
        action_rows.append(row)
        if row.get("exit_policy_result_source_status") == CLOSE_MARK_GAP_STATUS:
            gap_rows.append(row)
        elif row.get("exit_policy_result_source_status") == CLOSE_MARK_BOUND_STATUS:
            bound_rows.append(row)
    return gap_rows, bound_rows, action_rows


def load_dynamic_rows(rows: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    by_shard: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        shard = str(row.get("dynamic_shard_path") or "")
        cid = str(row.get("candidate_id") or "")
        if shard and cid:
            by_shard[shard].add(cid)

    dynamic_rows: dict[str, dict[str, Any]] = {}
    for shard_text, wanted in by_shard.items():
        shard = Path(shard_text)
        if not shard.exists():
            continue
        pending = set(wanted)
        for source_row in iter_jsonl(shard):
            cid = str(source_row.get("candidate_id") or "")
            if cid in pending:
                dynamic_rows[cid] = source_row
                pending.remove(cid)
                if not pending:
                    break
    return dynamic_rows


def hash_candidate_csv_sources(source_roots: list[Path], needed_hashes: set[str]) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = defaultdict(list)
    if not needed_hashes:
        return matches
    for root in source_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            upper = path.name.upper()
            if not any(suffix in upper for suffix in ("_M1.CSV", "_M5.CSV", "_M15.CSV")):
                continue
            digest = file_sha256(path)
            if digest in needed_hashes:
                matches[digest].append(str(path))
    return dict(matches)


def dynamic_policy_status(dynamic_row: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(dynamic_row, Mapping):
        return {
            "dynamic_row_status": "missing_dynamic_replay_row",
            "time_stop_only_present": False,
            "early_cut_if_no_progress_present": False,
            "reuse_status": "not_reusable_without_dynamic_row",
        }
    policy_results = ((dynamic_row.get("dynamic_policy_replay") or {}).get("policy_results") or {})
    time_stop = policy_results.get("time_stop_only")
    early_cut = policy_results.get("early_cut_if_no_progress")
    return {
        "dynamic_row_status": "found",
        "time_stop_only_present": isinstance(time_stop, Mapping),
        "time_stop_only_exit_reason": time_stop.get("exit_reason") if isinstance(time_stop, Mapping) else None,
        "time_stop_only_exit_time_utc": time_stop.get("exit_time_utc") if isinstance(time_stop, Mapping) else None,
        "time_stop_only_final_r": time_stop.get("final_r") if isinstance(time_stop, Mapping) else None,
        "early_cut_if_no_progress_present": isinstance(early_cut, Mapping),
        "early_cut_exit_reason": early_cut.get("exit_reason") if isinstance(early_cut, Mapping) else None,
        "early_cut_exit_time_utc": early_cut.get("exit_time_utc") if isinstance(early_cut, Mapping) else None,
        "early_cut_final_r": early_cut.get("final_r") if isinstance(early_cut, Mapping) else None,
        "reuse_status": (
            "not_reusable_as_v4_close_mark_without_v4_policy_id_action_reason_and_bar_clock"
        ),
    }


def build_audit(route_dir: Path, source_roots: list[Path]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    replay_dir = route_dir / "repaired_full_replay_wave4r_named"
    result_ledger = replay_dir / "WAVE4R_CANDIDATE_TRADE_MICROSCOPE_LEDGER.jsonl"
    rows, bound_rows, action_rows = collect_close_mark_rows(result_ledger)
    dynamic_rows = load_dynamic_rows(rows)
    needed_hashes = {str(row.get("source_sha256")) for row in rows if row.get("source_sha256")}
    hash_matches = hash_candidate_csv_sources(source_roots, needed_hashes)

    action_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    source_path_counts: Counter[str] = Counter()
    current_policy_source_counts: Counter[str] = Counter()
    dynamic_reuse_counts: Counter[str] = Counter()
    materialized_source_status_counts: Counter[str] = Counter()
    materialized_hash_status_counts: Counter[str] = Counter()
    requirement_rows: list[dict[str, Any]] = []

    for row in bound_rows:
        close_mark = row.get("exit_policy_close_mark")
        close_mark_payload = close_mark if isinstance(close_mark, Mapping) else {}
        materialized_source_status_counts[str(close_mark_payload.get("source_status") or "")] += 1
        materialized_hash_status_counts[
            str(close_mark_payload.get("source_hash_match_status") or "not_reported")
        ] += 1

    for row in rows:
        cid = str(row.get("candidate_id") or "")
        action = str(row.get("exit_policy_action") or "")
        source_hash = str(row.get("source_sha256") or "")
        dynamic_status = dynamic_policy_status(dynamic_rows.get(cid))
        action_counts[action] += 1
        symbol_counts[str(row.get("symbol") or "")] += 1
        source_path_counts[str(row.get("source_path") or "")] += 1
        current_policy_source_counts[str(row.get("current_v4_policy_result_source") or "")] += 1
        dynamic_reuse_counts[str(dynamic_status["reuse_status"])] += 1
        requirement_rows.append(
            {
                "schema_version": "v4u_exit_policy_close_mark_requirement_v1",
                "candidate_id": cid,
                "asof_utc": row.get("asof_utc"),
                "symbol": row.get("symbol"),
                "side": row.get("side"),
                "exit_policy_action": action,
                "exit_policy_close_reason": row.get("exit_policy_close_reason"),
                "source_path": row.get("source_path"),
                "source_sha256": source_hash,
                "source_hash_exact_local_matches": hash_matches.get(source_hash, []),
                "dynamic_shard_path": row.get("dynamic_shard_path"),
                "dynamic_policy_reuse_status": dynamic_status["reuse_status"],
                "dynamic_policy_status": dynamic_status,
                "required_close_mark_fields": list(REQUIRED_CLOSE_MARK_FIELDS),
                "required_policy_id": "v4_exit_policy_close_mark_v1",
                "required_source_status": (
                    "source_bound/replay_bound close mark with no broker-real cash claim"
                ),
                "decision_boundary": (
                    "close mark may only adjust replay labels after the decision; it must not enter selector, "
                    "probability, scheduler, lifecycle, or execution packets"
                ),
            }
        )

    report = {
        "schema_version": "v4u_exit_policy_close_mark_audit_v1",
        "generated_at_utc": utc_now(),
        "route_dir": str(route_dir),
        "result_ledger": str(result_ledger),
        "close_mark_action_rows": len(action_rows),
        "materialized_close_mark_rows": len(bound_rows),
        "close_mark_gap_rows": len(rows),
        "materialized_source_status_counts": dict(sorted(materialized_source_status_counts.items())),
        "materialized_source_hash_match_status_counts": dict(
            sorted(materialized_hash_status_counts.items())
        ),
        "action_counts": dict(sorted(action_counts.items())),
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "source_path_counts": dict(sorted(source_path_counts.items())),
        "source_hashes_required": len(needed_hashes),
        "source_hashes_with_exact_local_match": len(hash_matches),
        "source_roots_checked": [str(path) for path in source_roots],
        "source_hash_match_status": (
            "checked_explicit_source_roots"
            if source_roots
            else "not_checked_no_source_roots_supplied"
        ),
        "current_policy_source_counts": dict(sorted(current_policy_source_counts.items())),
        "dynamic_reuse_status_counts": dict(sorted(dynamic_reuse_counts.items())),
        "requirement_rows": len(requirement_rows),
        "source_boundary": (
            "stale/time-stop close marks are post-decision replay labels only; local M15 close marks may materialize proxy-R when source_path resolves, with exact source-hash matches and local source-hash mismatches labeled separately"
        ),
        "implementation_status": (
            "replay gate materializes stale/time-stop R from explicit V4 close-mark packets or labeled local M15 policy-clock close marks; remaining rows require exact source files/bars or explicit packets"
        ),
    }
    return report, requirement_rows


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--route-dir",
        type=Path,
        default=Path("research/operations/final_moonshot_v4_ultimate_system_repair_from_wave4r_2026_06_06"),
    )
    parser.add_argument(
        "--source-root",
        action="append",
        type=Path,
        default=[],
        help="Source roots to hash for exact M1/M5/M15 matches. Can be repeated.",
    )
    parser.add_argument(
        "--hash-default-source-roots",
        action="store_true",
        help=(
            "Hash the broad default data/export/package roots. This is intentionally "
            "opt-in because it can be slow on the Mac research workspace."
        ),
    )
    parser.add_argument("--write-artifacts", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_roots = args.source_root
    if not source_roots and args.hash_default_source_roots:
        source_roots = [
            Path("data"),
            Path("exports"),
            Path("/Users/borr/Documents/gtos/packages/GTOS_MAC_RESEARCH_MIGRATION_2026_06_04"),
        ]
    report, requirement_rows = build_audit(args.route_dir, source_roots)
    if args.write_artifacts:
        write_json(args.route_dir / "V4U_EXIT_POLICY_CLOSE_MARK_AUDIT.json", report)
        write_jsonl(
            args.route_dir / "V4U_EXIT_POLICY_CLOSE_MARK_REQUIREMENT_LEDGER.jsonl",
            requirement_rows,
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
