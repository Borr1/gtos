#!/usr/bin/env python3
"""Recover completed B7.5 scorecards from exact terminal signed authority.

This tool never enters the economic reducer.  It exists only for a completed
run whose scorecard was serialized after repeated normalization dropped
hash-bound empty container projections.  Every repaired row must join an exact
terminal order/trade instance, preserve every non-authority field byte-for-
semantic-value, and pass the current full-row authority verifier.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra import (  # noqa: E402
    replay_acceleration_attempt5_typed_sparse_runner as replay,
)
from src.research_infra import (  # noqa: E402
    v4_timewarp_simulated_live_research_loop as timewarp,
)


RECEIPT_SCHEMA = "gtos.b7_5.completed_scorecard_authority_recovery.v1"
VALID_SIGNED_STATUS = "valid_signed_predecision_new_entry_authority"
RECOVERABLE_SIGNED_RECONCILIATION_STATUS = (
    "exact_terminal_signed_authority_reconciled"
)
EXECUTABLE_CLAIM_FIELDS = (
    "ledger_namespace_synthesized_executable_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "ultimate_package_effective_executable_authority_allowed",
    "executable_finalized",
    "risk_finalizer_executable_finalized",
)


class CompletedScorecardAuthorityRecoveryError(RuntimeError):
    """Fail-closed recovery rejection."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CompletedScorecardAuthorityRecoveryError(code)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _instance_key(row: Mapping[str, Any]) -> str:
    for field in (
        "terminal_execution_truth_reconciliation_instance_key",
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
    ):
        value = str(row.get(field) or "").strip()
        if value:
            return value
    candidate_id = str(
        row.get("candidate_id") or row.get("selected_candidate_id") or ""
    ).strip()
    decision_time = str(
        row.get("decision_time_utc") or row.get("candidate_instance_time_utc") or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""


def _iter_jsonl(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CompletedScorecardAuthorityRecoveryError(
                    f"jsonl_invalid:{path.name}:{line_number}"
                ) from exc
            _require(
                isinstance(row, Mapping),
                f"jsonl_row_not_mapping:{path.name}:{line_number}",
            )
            yield line_number, dict(row)


def _terminal_index(
    *,
    order_path: Path,
    trade_path: Path,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    index: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: {"order": [], "trade": []}
    )
    for role, path in (("order", order_path), ("trade", trade_path)):
        for line_number, row in _iter_jsonl(path):
            key = _instance_key(row)
            _require(
                bool(key),
                f"terminal_instance_key_missing:{role}:{line_number}",
            )
            index[key][role].append(row)
    return dict(index)


def _is_recoverable_row(row: Mapping[str, Any]) -> bool:
    failures = timewarp.package_new_entry_authority_immutable_payload_failures(row)
    projection_failure = any(
        str(reason).startswith("authority_payload_projection_missing:")
        for reason in failures
    )
    blocked_signed_claim = bool(
        row.get("package_new_entry_authority_valid") is False
        and str(row.get("package_new_entry_authority_status") or "").strip()
        == "invalid_or_missing_signed_new_entry_authority"
        and any(row.get(field) is True for field in EXECUTABLE_CLAIM_FIELDS)
    )
    return bool(
        row.get(
            "terminal_execution_truth_reconciliation_signed_authority_status"
        )
        == RECOVERABLE_SIGNED_RECONCILIATION_STATUS
        and (projection_failure or blocked_signed_claim)
    )


def _authority_field(field: str) -> bool:
    return bool(
        field.startswith("package_new_entry_authority_")
        or field.startswith("expected_package_new_entry_authority_")
        or field == "terminal_execution_truth_reconciliation_changed_fields"
    )


def _non_authority_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if not _authority_field(str(key))
    }


def _exact_terminal_authority_matches(
    *,
    repaired: Mapping[str, Any],
    terminals: Mapping[str, Sequence[Mapping[str, Any]]],
) -> bool:
    repaired_identity = (
        repaired.get("package_new_entry_authority_candidate_id"),
        repaired.get(
            "package_new_entry_authority_canonical_replay_candidate_instance_key"
        ),
        repaired.get("package_new_entry_authority_hash_sha256"),
        repaired.get("package_new_entry_authority_payload"),
    )
    for role in ("trade", "order"):
        for source_row in terminals.get(role, ()):
            normalized = timewarp.normalize_package_new_entry_authority_ledger_row(
                copy.deepcopy(dict(source_row))
            )
            authority = timewarp.package_new_entry_authority_attribution_fields(
                normalized
            )
            terminal_identity = (
                authority.get("package_new_entry_authority_candidate_id"),
                authority.get(
                    "package_new_entry_authority_canonical_replay_candidate_instance_key"
                ),
                authority.get("package_new_entry_authority_hash_sha256"),
                authority.get("package_new_entry_authority_payload"),
            )
            if (
                authority.get("package_new_entry_authority_valid") is True
                and authority.get("package_new_entry_authority_status")
                == VALID_SIGNED_STATUS
                and terminal_identity == repaired_identity
            ):
                return True
    return False


def repair_scorecard_authority(
    *,
    scorecard_path: Path,
    order_path: Path,
    trade_path: Path,
) -> dict[str, Any]:
    """Atomically repair only exact terminal authority projections."""

    scorecard_path = Path(scorecard_path)
    order_path = Path(order_path)
    trade_path = Path(trade_path)
    for role, path in (
        ("scorecard", scorecard_path),
        ("order", order_path),
        ("trade", trade_path),
    ):
        _require(path.is_file(), f"{role}_ledger_missing")
        _require(not path.is_symlink(), f"{role}_ledger_symlink_forbidden")

    terminal_by_instance = _terminal_index(
        order_path=order_path,
        trade_path=trade_path,
    )
    before_bytes = scorecard_path.stat().st_size
    before_sha256 = _file_sha256(scorecard_path)
    temporary = scorecard_path.with_name(
        f".{scorecard_path.name}.{os.getpid()}.authority-repair.tmp"
    )
    _require(
        not temporary.exists() and not temporary.is_symlink(),
        "repair_temporary_path_exists",
    )

    repaired_rows: list[dict[str, Any]] = []
    changed_fields: Counter[str] = Counter()
    row_count = 0
    non_authority_projection_change_count = 0
    try:
        with temporary.open("x", encoding="utf-8") as output:
            for line_number, row in _iter_jsonl(scorecard_path):
                row_count = line_number
                if _is_recoverable_row(row):
                    key = _instance_key(row)
                    _require(bool(key), f"scorecard_instance_key_missing:{line_number}")
                    terminals = terminal_by_instance.get(key)
                    _require(
                        isinstance(terminals, Mapping),
                        f"scorecard_terminal_join_missing:{line_number}:{key}",
                    )
                    before = copy.deepcopy(row)
                    before_projection_root = _stable_sha256(
                        _non_authority_projection(before)
                    )
                    counts = timewarp.reconcile_terminal_package_execution_truth(
                        {
                            "candidate": [],
                            "scorecard": [row],
                            "order": list(terminals.get("order", ())),
                            "trade": list(terminals.get("trade", ())),
                        }
                    )
                    _require(
                        int(counts.get("scorecard_rows_reconciled") or 0) == 1,
                        f"scorecard_terminal_reconciliation_missing:{line_number}:{key}",
                    )
                    changed = sorted(
                        field
                        for field in set(before) | set(row)
                        if before.get(field, object()) != row.get(field, object())
                    )
                    unexpected = [
                        field for field in changed if not _authority_field(field)
                    ]
                    _require(
                        not unexpected,
                        "scorecard_non_authority_field_changed:"
                        f"{line_number}:{'|'.join(unexpected)}",
                    )
                    after_projection_root = _stable_sha256(
                        _non_authority_projection(row)
                    )
                    if before_projection_root != after_projection_root:
                        non_authority_projection_change_count += 1
                    _require(
                        before_projection_root == after_projection_root,
                        f"scorecard_non_authority_projection_changed:{line_number}",
                    )
                    _require(
                        row.get("package_new_entry_authority_valid") is True
                        and row.get("package_new_entry_authority_status")
                        == VALID_SIGNED_STATUS
                        and not timewarp.package_new_entry_authority_immutable_payload_failures(
                            row
                        ),
                        f"scorecard_authority_still_invalid:{line_number}:{key}",
                    )
                    _require(
                        _exact_terminal_authority_matches(
                            repaired=row,
                            terminals=terminals,
                        ),
                        f"scorecard_terminal_authority_not_exact:{line_number}:{key}",
                    )
                    replay.current_summary_v2_contract_for_rows(
                        [("scorecard", row)]
                    )
                    for field in changed:
                        changed_fields[field] += 1
                    repaired_rows.append(
                        {
                            "line_number": line_number,
                            "candidate_instance_key": key,
                            "terminal_source_ledger": row.get(
                                "terminal_execution_truth_reconciliation_source_ledger"
                            ),
                            "authority_hash_sha256": row.get(
                                "package_new_entry_authority_hash_sha256"
                            ),
                            "before_non_authority_projection_root_sha256": (
                                before_projection_root
                            ),
                            "after_non_authority_projection_root_sha256": (
                                after_projection_root
                            ),
                            "changed_fields": changed,
                        }
                    )
                output.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            output.flush()
            os.fsync(output.fileno())
        _require(row_count > 0, "scorecard_ledger_empty")
        _require(bool(repaired_rows), "no_recoverable_scorecard_rows")
        os.replace(temporary, scorecard_path)
    except BaseException:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
        raise

    after_bytes = scorecard_path.stat().st_size
    after_sha256 = _file_sha256(scorecard_path)
    core = {
        "schema": RECEIPT_SCHEMA,
        "status": "COMPLETED_SCORECARD_TERMINAL_AUTHORITY_RECOVERED",
        "valid": True,
        "scorecard_path": str(scorecard_path.resolve()),
        "order_path": str(order_path.resolve()),
        "trade_path": str(trade_path.resolve()),
        "row_count": row_count,
        "repaired_row_count": len(repaired_rows),
        "pre_repair_bytes": before_bytes,
        "pre_repair_sha256": before_sha256,
        "post_repair_bytes": after_bytes,
        "post_repair_sha256": after_sha256,
        "changed_field_counts": dict(sorted(changed_fields.items())),
        "non_authority_projection_change_count": (
            non_authority_projection_change_count
        ),
        "repaired_rows": repaired_rows,
        "economic_reducer_rerun": False,
        "source_rows_changed": False,
        "order_rows_changed": False,
        "trade_rows_changed": False,
        "scorecard_non_authority_fields_changed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "real_order_transmission_possible": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def rebind_partial_scorecard_checkpoint(
    *,
    partial_summary_path: Path,
    recovery_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Rebind only the completed checkpoint's scorecard byte count."""

    partial_summary_path = Path(partial_summary_path)
    _require(
        partial_summary_path.is_file() and not partial_summary_path.is_symlink(),
        "partial_summary_missing_or_symlink",
    )
    _require(
        recovery_receipt.get("schema") == RECEIPT_SCHEMA
        and recovery_receipt.get("valid") is True,
        "recovery_receipt_invalid",
    )
    partial_before_sha256 = _file_sha256(partial_summary_path)
    partial = json.loads(partial_summary_path.read_text(encoding="utf-8"))
    _require(isinstance(partial, dict), "partial_summary_not_mapping")
    _require(
        partial.get("status") == "partial_in_progress_not_final_proof",
        "partial_summary_status_invalid",
    )
    counts = partial.get("ledger_write_row_counts_so_far")
    byte_counts = partial.get("ledger_file_bytes_flushed_before_partial_summary")
    _require(
        isinstance(counts, Mapping) and isinstance(byte_counts, dict),
        "partial_summary_ledger_checkpoint_missing",
    )
    _require(
        int(counts.get("scorecard") or 0)
        == int(recovery_receipt.get("row_count") or -1),
        "partial_summary_scorecard_row_count_mismatch",
    )
    _require(
        int(byte_counts.get("scorecard") or 0)
        == int(recovery_receipt.get("pre_repair_bytes") or -1),
        "partial_summary_scorecard_pre_repair_bytes_mismatch",
    )
    byte_counts["scorecard"] = int(recovery_receipt["post_repair_bytes"])
    timewarp.atomic_write_json(partial_summary_path, partial)
    rebound = json.loads(partial_summary_path.read_text(encoding="utf-8"))
    rebound_bytes = rebound.get("ledger_file_bytes_flushed_before_partial_summary")
    _require(
        isinstance(rebound_bytes, Mapping)
        and int(rebound_bytes.get("scorecard") or 0)
        == int(recovery_receipt["post_repair_bytes"]),
        "partial_summary_scorecard_rebind_not_persisted",
    )
    return {
        "status": "COMPLETED_CHECKPOINT_SCORECARD_BYTES_REBOUND",
        "valid": True,
        "partial_summary_path": str(partial_summary_path.resolve()),
        "partial_summary_pre_rebind_sha256": partial_before_sha256,
        "partial_summary_post_rebind_sha256": _file_sha256(partial_summary_path),
        "scorecard_rows": int(counts["scorecard"]),
        "scorecard_pre_repair_bytes": int(recovery_receipt["pre_repair_bytes"]),
        "scorecard_post_repair_bytes": int(recovery_receipt["post_repair_bytes"]),
        "other_checkpoint_fields_changed": False,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorecard", type=Path, required=True)
    parser.add_argument("--order", type=Path, required=True)
    parser.add_argument("--trade", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--partial-summary", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    receipt = repair_scorecard_authority(
        scorecard_path=args.scorecard,
        order_path=args.order,
        trade_path=args.trade,
    )
    if args.partial_summary is not None:
        receipt["partial_summary_checkpoint_rebind"] = (
            rebind_partial_scorecard_checkpoint(
                partial_summary_path=args.partial_summary,
                recovery_receipt=receipt,
            )
        )
        receipt_without_root = {
            key: value
            for key, value in receipt.items()
            if key != "receipt_root_sha256"
        }
        receipt["receipt_root_sha256"] = _stable_sha256(receipt_without_root)
    timewarp.atomic_write_json(args.receipt, receipt)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
