"""Repair missing unit_placed runtime-learning packets from launcher evidence.

This is offline and observation-only. It reads launcher rows that already
contain redacted placement summaries, reconstructs missing unit_placed packets,
validates them, and appends only packets whose ticket hash is absent from the
runtime-learning ledger.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.ultimate_book.admission import cluster_of
from src.components.ultimate_book.placement_ledger import (
    PLACEMENT_CAPTURE_COMPLETE_STATUS,
    PLACEMENT_CAPTURE_CONTRACT_VERSION,
)
from src.components.ultimate_book.runtime_learning_packet import (
    DEFAULT_LOG_PATH,
    RuntimeLearningPacketWriter,
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)

DEFAULT_LAUNCHER_LOG_PATH = "shadow_logs/ultimate_book_launcher.jsonl"


def _iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any] | None, str | None]]:
    if not path.exists():
        yield 0, None, "missing_file"
        return
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for line_no, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                yield line_no, None, str(exc)
                continue
            if isinstance(row, dict):
                yield line_no, row, None
            else:
                yield line_no, None, "non_object_json"


def _candidate_part(candidate_id: Any, index: int) -> str | None:
    parts = str(candidate_id or "").split("::")
    if len(parts) >= 6 and parts[0] == "W7_BOOK" and parts[index]:
        return parts[index]
    return None


def _existing_unit_placed_keys(packet_log: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for _line_no, row, _error in _iter_jsonl(packet_log):
        if not isinstance(row, dict):
            continue
        if row.get("event_type") != "unit_placed":
            continue
        namespace = row.get("namespace")
        ticket_hash = row.get("ticket_hash_sha256")
        if namespace and ticket_hash:
            keys.add((str(namespace), str(ticket_hash)))
    return keys


def _repair_outcome(placed: dict[str, Any], launcher_row: dict[str, Any], line_no: int) -> dict[str, Any]:
    candidate_id = placed.get("candidate_id")
    sleeve = placed.get("sleeve")
    cluster = (
        placed.get("cluster")
        or _candidate_part(candidate_id, 1)
        or (cluster_of(str(sleeve)) if sleeve else None)
    )
    direction = placed.get("direction") or _candidate_part(candidate_id, 4)
    decision_day = placed.get("decision_day") or _candidate_part(candidate_id, 3)
    outcome = dict(placed)
    outcome.update({
        "cluster": cluster,
        "direction": direction,
        "decision_day": decision_day,
        "placement_status": "placed",
        "placement_observed_at_utc": placed.get("placement_observed_at_utc") or launcher_row.get("ts"),
        "placement_capture_contract_version": PLACEMENT_CAPTURE_CONTRACT_VERSION,
        "placement_source_completeness_status": PLACEMENT_CAPTURE_COMPLETE_STATUS,
        "placement_source_missing_fields": [],
        "source_completeness_status": "launcher_runtime_learning_write_repair",
        "runtime_learning_repair_status": "reconstructed_from_launcher_after_packet_write_failure",
        "runtime_learning_repair_source": DEFAULT_LAUNCHER_LOG_PATH,
        "runtime_learning_repair_source_line_no": line_no,
    })
    return outcome


def repair_missing_packets(
    *,
    repo_root: Path,
    packet_log_path: str,
    launcher_log_path: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    packet_log = repo_root / packet_log_path
    launcher_log = repo_root / launcher_log_path
    existing = _existing_unit_placed_keys(packet_log)
    packets: list[dict[str, Any]] = []
    skipped_existing = 0
    incomplete: list[dict[str, Any]] = []
    seen_new: set[tuple[str, str]] = set()

    for line_no, row, error in _iter_jsonl(launcher_log):
        if error or not isinstance(row, dict):
            continue
        namespace = row.get("namespace")
        if not namespace:
            continue
        runtime_learning = row.get("runtime_learning") if isinstance(row.get("runtime_learning"), dict) else {}
        packet_write_error_count = runtime_learning.get("packet_write_error_count") or 0
        try:
            packet_write_error_count = int(float(packet_write_error_count))
        except (TypeError, ValueError):
            packet_write_error_count = 0
        if not (
            runtime_learning.get("enabled") is True
            and runtime_learning.get("log_enabled") is True
            and (runtime_learning.get("error") or packet_write_error_count > 0)
        ):
            continue
        for placed in row.get("placed") or []:
            if not isinstance(placed, dict):
                continue
            ticket_hash = placed.get("ticket_hash_sha256")
            if not ticket_hash:
                continue
            key = (str(namespace), str(ticket_hash))
            if key in existing or key in seen_new:
                skipped_existing += 1
                continue
            outcome = _repair_outcome(placed, row, line_no)
            packet = build_runtime_learning_packet(
                namespace=str(namespace),
                event_type="unit_placed",
                ts=row.get("ts") or datetime.now(timezone.utc).isoformat(),
                bridge=row.get("bridge") if isinstance(row.get("bridge"), dict) else {},
                outcome=outcome,
                source="book_owner.run_cycle.launcher_runtime_learning_repair",
            )
            ok, issues = validate_runtime_learning_packet(packet)
            if not ok:
                incomplete.append({
                    "launcher_line_no": line_no,
                    "namespace": namespace,
                    "ticket_hash_sha256": ticket_hash,
                    "issues": issues,
                })
                continue
            packets.append(packet)
            seen_new.add(key)

    appended = 0
    if packets and not dry_run:
        appended = RuntimeLearningPacketWriter(repo_root, packet_log_path).append_many(packets)

    return {
        "schema": "gtos.runtime_learning_unit_placed_launcher_repair.v1",
        "runtime_effect_boundary": "offline_observation_no_broker_or_config_mutation",
        "packet_log_path": packet_log_path,
        "launcher_log_path": launcher_log_path,
        "dry_run": dry_run,
        "existing_unit_placed_key_count": len(existing),
        "skipped_existing_or_duplicate_count": skipped_existing,
        "repair_packet_candidate_count": len(packets),
        "repair_packet_appended_count": appended,
        "incomplete_repair_count": len(incomplete),
        "incomplete_repair_samples": incomplete[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-log-path", default=DEFAULT_LOG_PATH)
    parser.add_argument("--launcher-log-path", default=DEFAULT_LAUNCHER_LOG_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    summary = repair_missing_packets(
        repo_root=REPO_ROOT,
        packet_log_path=args.packet_log_path,
        launcher_log_path=args.launcher_log_path,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0 if summary["incomplete_repair_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
