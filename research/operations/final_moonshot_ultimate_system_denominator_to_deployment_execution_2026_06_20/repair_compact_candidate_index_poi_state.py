#!/usr/bin/env python3
"""Rehydrate compact candidate POI atoms from exact terminal instance rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.poi_state_contract import (  # noqa: E402
    poi_state_contract_failures,
    poi_state_required,
)
from src.components.poi_execution_lifecycle import (  # noqa: E402
    causal_poi_lifecycle_contract_failures,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    atomic_write_json,
    candidate_poi_state_ledger_fields,
    file_sha256,
    utc_now,
)

SCHEMA = "gtos.broad_replay.compact_candidate_index_poi_rehydration.v1"


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for row_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"jsonl_row_not_object:{path}:{row_number}")
            yield row


def candidate_instance_key(row: Mapping[str, Any]) -> str:
    return str(
        row.get("canonical_replay_candidate_instance_key")
        or row.get("selected_candidate_instance_key")
        or ""
    ).strip()


def projection_lineage(projection: Mapping[str, Any]) -> tuple[str, str, str]:
    state = projection.get("poi_state")
    state = state if isinstance(state, Mapping) else {}
    lifecycle = projection.get("causal_poi_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    return (
        str(state.get("poi_id") or projection.get("poi_id") or "").strip(),
        str(
            state.get("poi_state_hash_sha256")
            or projection.get("poi_state_hash_sha256")
            or ""
        ).strip(),
        str(
            lifecycle.get("lifecycle_hash_sha256")
            or projection.get("causal_poi_lifecycle_hash_sha256")
            or ""
        ).strip(),
    )


def validate_projection(
    projection: Mapping[str, Any],
    *,
    decision_time_utc: Any,
    source: str,
    instance_key: str,
) -> None:
    state = projection.get("poi_state")
    state = state if isinstance(state, Mapping) else {}
    lifecycle = projection.get("causal_poi_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    failures = list(
        poi_state_contract_failures(
            state,
            decision_time_utc=decision_time_utc,
        )
    )
    failures.extend(
        f"causal_poi_lifecycle:{failure}"
        for failure in causal_poi_lifecycle_contract_failures(
            lifecycle,
            poi_state=state,
            decision_time_utc=decision_time_utc,
        )
    )
    if failures:
        raise ValueError(
            "invalid_terminal_poi_projection:"
            f"{source}:{instance_key}:{','.join(dict.fromkeys(failures))}"
        )


def build_terminal_projection_index(
    *,
    missed_path: Path,
    order_path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    projections: dict[str, dict[str, Any]] = {}
    lineage_by_key: dict[str, tuple[str, str, str]] = {}
    source_by_key: dict[str, str] = {}
    source_rows = Counter()
    duplicate_rows = Counter()

    for source, path in (("missed", missed_path), ("order", order_path)):
        for row in iter_jsonl(path):
            projection = candidate_poi_state_ledger_fields(row)
            if not isinstance(projection.get("poi_state"), Mapping):
                continue
            instance_key = candidate_instance_key(row)
            if not instance_key:
                raise ValueError(f"terminal_poi_candidate_instance_key_missing:{source}")
            validate_projection(
                projection,
                decision_time_utc=row.get("decision_time_utc"),
                source=source,
                instance_key=instance_key,
            )
            lineage = projection_lineage(projection)
            if instance_key in lineage_by_key:
                duplicate_rows[source] += 1
                if lineage_by_key[instance_key] != lineage:
                    raise ValueError(
                        "terminal_poi_lineage_conflict:"
                        f"{instance_key}:{lineage_by_key[instance_key]}:{lineage}"
                    )
                continue
            projections[instance_key] = dict(projection)
            lineage_by_key[instance_key] = lineage
            source_by_key[instance_key] = source
            source_rows[source] += 1

    return projections, {
        "terminal_projection_unique_candidate_instances": len(projections),
        "terminal_projection_source_unique_counts": dict(source_rows),
        "terminal_projection_duplicate_row_counts": dict(duplicate_rows),
        "terminal_projection_source_by_candidate_instance": source_by_key,
    }


def rehydrate_candidate_index(
    *,
    candidate_index_path: Path,
    missed_path: Path,
    order_path: Path,
    apply: bool,
) -> dict[str, Any]:
    projections, projection_summary = build_terminal_projection_index(
        missed_path=missed_path,
        order_path=order_path,
    )
    before_hash = file_sha256(candidate_index_path)
    temp_path = candidate_index_path.with_suffix(f".{os.getpid()}.poi.tmp")
    counts = Counter()
    seen_keys: set[str] = set()
    identity_before = hashlib.sha256()
    identity_after = hashlib.sha256()
    missing_projection_keys: list[str] = []

    try:
        with temp_path.open("w", encoding="utf-8") as target:
            for row in iter_jsonl(candidate_index_path):
                counts["candidate_rows"] += 1
                instance_key = candidate_instance_key(row)
                if not instance_key:
                    raise ValueError("candidate_index_instance_key_missing")
                if instance_key in seen_keys:
                    raise ValueError(
                        f"candidate_index_duplicate_instance_key:{instance_key}"
                    )
                seen_keys.add(instance_key)
                identity_before.update(f"{instance_key}\n".encode("utf-8"))

                updated = dict(row)
                if poi_state_required(row):
                    counts["poi_required_candidate_rows"] += 1
                    current = candidate_poi_state_ledger_fields(row)
                    if isinstance(current.get("poi_state"), Mapping):
                        counts["poi_state_present_before_rows"] += 1
                    else:
                        counts["poi_state_missing_before_rows"] += 1
                    projection = projections.get(instance_key)
                    if projection is None:
                        counts["poi_terminal_projection_missing_rows"] += 1
                        if len(missing_projection_keys) < 20:
                            missing_projection_keys.append(instance_key)
                    else:
                        if isinstance(current.get("poi_state"), Mapping) and (
                            projection_lineage(current)
                            != projection_lineage(projection)
                        ):
                            raise ValueError(
                                f"candidate_terminal_poi_lineage_conflict:{instance_key}"
                            )
                        changed_fields = [
                            field
                            for field, value in projection.items()
                            if updated.get(field) != value
                        ]
                        if changed_fields:
                            counts["candidate_rows_changed"] += 1
                            counts["candidate_fields_changed"] += len(changed_fields)
                        updated.update(projection)
                        validate_projection(
                            candidate_poi_state_ledger_fields(updated),
                            decision_time_utc=updated.get("decision_time_utc"),
                            source="rehydrated_candidate",
                            instance_key=instance_key,
                        )
                        counts["poi_terminal_projection_bound_rows"] += 1

                output_key = candidate_instance_key(updated)
                identity_after.update(f"{output_key}\n".encode("utf-8"))
                target.write(json.dumps(updated, sort_keys=True, default=str) + "\n")

        if counts["poi_terminal_projection_missing_rows"]:
            raise ValueError(
                "candidate_poi_terminal_projection_missing:"
                f"count={counts['poi_terminal_projection_missing_rows']}:"
                f"samples={missing_projection_keys}"
            )
        if identity_before.hexdigest() != identity_after.hexdigest():
            raise ValueError("candidate_identity_sequence_changed_during_rehydration")
        if apply:
            os.replace(temp_path, candidate_index_path)
        else:
            temp_path.unlink()
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise

    after_hash = file_sha256(candidate_index_path) if apply else before_hash
    return {
        "schema": SCHEMA,
        "generated_at_utc": utc_now(),
        "applied": bool(apply),
        "candidate_index_path": str(candidate_index_path),
        "missed_ledger_path": str(missed_path),
        "order_ledger_path": str(order_path),
        "candidate_index_sha256_before": before_hash,
        "candidate_index_sha256_after": after_hash,
        "candidate_identity_sequence_sha256_before": identity_before.hexdigest(),
        "candidate_identity_sequence_sha256_after": identity_after.hexdigest(),
        "counts": dict(counts),
        **{
            key: value
            for key, value in projection_summary.items()
            if key != "terminal_projection_source_by_candidate_instance"
        },
        "terminal_projection_lineage_conflict_rows": 0,
        "candidate_terminal_lineage_conflict_rows": 0,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-index", required=True, type=Path)
    parser.add_argument("--missed-ledger", required=True, type=Path)
    parser.add_argument("--order-ledger", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = rehydrate_candidate_index(
        candidate_index_path=args.candidate_index,
        missed_path=args.missed_ledger,
        order_path=args.order_ledger,
        apply=args.apply,
    )
    atomic_write_json(args.result, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
