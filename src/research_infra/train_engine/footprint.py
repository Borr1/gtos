"""CG-5: reproduce the training lane's storage waterfall and disk ceiling.

There are two evidence surfaces and they are kept separate:

* ``bounded_waterfall`` replays each pure output projector over CG's own frozen
  two-day JSONL and measures the exact bytes it would write. It then compares
  that offline waterfall with CG's observed final namespace.
* ``month_references`` reads completed CD January namespaces without modifying
  them. CD's decision/scorecard projection is already present; the original
  compact missed rows remain in authenticated shards, so the reader-complete
  v2 missed projection can be priced exactly before the semantic sidecar and
  resident-sink cuts are applied.

This is footprint evidence, never replay or admission evidence. It neither
imports nor invokes a broker-capable entrypoint and never writes into a replay
namespace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from src.research_infra import replay_compact_event_sink as frozen_sink
from src.research_infra.train_engine import cuts


SCHEMA = "gtos.train_engine.lane_footprint.v1"
DECISION_SUFFIX = "_DECISION_LEDGER.jsonl"
SCORECARD_SUFFIX = "_SCORECARD_LEDGER.jsonl"
MISSED_SUFFIX = "_MISSED_OPPORTUNITY_LEDGER.jsonl"
SEMANTIC_SUFFIXES = tuple(sorted(cuts.SEMANTIC_SIDECAR_PROJECTIONS))


def _allocated_file_bytes(path: Path) -> int:
    stat = path.stat()
    blocks = getattr(stat, "st_blocks", None)
    return int(blocks * 512) if blocks is not None else int(stat.st_size)


def _estimated_allocated_bytes(byte_count: int, *, block_size: int) -> int:
    if byte_count <= 0:
        return 0
    return ((int(byte_count) + block_size - 1) // block_size) * block_size


def inventory(root: Path) -> dict[str, Any]:
    """Inventory regular files under one namespace; symlinks fail closed."""

    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"footprint_root_invalid:{root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"footprint_symlink_refused:{path}")
        if not path.is_file():
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "logical_bytes": int(path.stat().st_size),
                "allocated_bytes": _allocated_file_bytes(path),
            }
        )
    return {
        "root": str(root.resolve()),
        "file_count": len(files),
        "logical_bytes": sum(row["logical_bytes"] for row in files),
        "allocated_bytes": sum(row["allocated_bytes"] for row in files),
        "files": files,
    }


def _inventory_without_cold_archives(root: Path) -> dict[str, Any]:
    """Inventory live namespace files while excluding ``*.jsonl.cold`` trees.

    A demoted arm replaces three raw ledgers with compressed archives.  Those
    archive bytes describe today's preservation footprint, not the raw arm that
    the lane cuts transform.  Their manifests carry the exact pre-demotion
    logical and allocated sizes; this inventory supplies everything else.
    """

    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"footprint_root_invalid:{root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"footprint_symlink_refused:{path}")
        relative = path.relative_to(root)
        if any(part.endswith(".jsonl.cold") for part in relative.parts):
            continue
        if not path.is_file():
            continue
        files.append(
            {
                "path": relative.as_posix(),
                "logical_bytes": int(path.stat().st_size),
                "allocated_bytes": _allocated_file_bytes(path),
            }
        )
    return {
        "root": str(root.resolve()),
        "file_count": len(files),
        "logical_bytes": sum(row["logical_bytes"] for row in files),
        "allocated_bytes": sum(row["allocated_bytes"] for row in files),
        "files": files,
    }


def _cold_preimage(root: Path, suffix: str) -> dict[str, Any]:
    """Read one verified cold manifest as its original raw-ledger geometry."""

    matches = sorted(
        path
        for path in Path(root).iterdir()
        if path.is_dir() and path.name.endswith(f"{suffix}.cold")
    )
    if len(matches) != 1:
        raise ValueError(
            f"cold_preimage_cardinality:{root}:{suffix}:{len(matches)}"
        )
    archive = matches[0]
    manifest_path = archive / "manifest.json"
    if archive.is_symlink() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError(f"cold_preimage_manifest_invalid:{archive}")
    raw = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cold_preimage_manifest_invalid:{archive}") from exc
    source = manifest.get("logical_source") if isinstance(manifest, Mapping) else None
    if (
        manifest.get("schema") != "gtos.b7_5.cold_jsonl_archive.v1"
        or manifest.get("status") != "PASS_COLD_ARCHIVE_LOGICAL_BYTES_VERIFIED"
        or not isinstance(source, Mapping)
        or not str(source.get("name") or "").endswith(suffix)
    ):
        raise ValueError(f"cold_preimage_contract_invalid:{archive}")
    metadata = source.get("source_metadata_before_demotion")
    if not isinstance(metadata, Mapping):
        raise ValueError(f"cold_preimage_metadata_absent:{archive}")
    logical_bytes = int(source.get("logical_bytes") or -1)
    allocated_bytes = int(metadata.get("physical_bytes") or -1)
    rows = int(source.get("json_object_row_count") or -1)
    if min(logical_bytes, allocated_bytes, rows) < 0:
        raise ValueError(f"cold_preimage_measurement_invalid:{archive}")
    return {
        "archive": str(archive.resolve()),
        "archive_inventory": inventory(archive),
        "manifest": str(manifest_path.resolve()),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "source_name": source["name"],
        "source_sha256": source.get("sha256"),
        "rows": rows,
        "logical_bytes": logical_bytes,
        "allocated_bytes": allocated_bytes,
    }


def _unique_suffix(root: Path, suffix: str) -> Path:
    matches = sorted(
        path for path in Path(root).rglob(f"*{suffix}") if path.is_file()
    )
    if len(matches) != 1:
        raise ValueError(
            f"footprint_suffix_cardinality:{root}:{suffix}:{len(matches)}"
        )
    return matches[0]


def _jsonl_projection(
    path: Path,
    projector: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure a projector using the exact append_jsonl encoding contract."""

    path = Path(path)
    digest = hashlib.sha256()
    rows = 0
    projected_bytes = 0
    source_canonical = True
    with path.open("rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                raise ValueError(f"jsonl_unterminated_row:{path}:{rows + 1}")
            digest.update(raw)
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"jsonl_invalid:{path}:{rows + 1}") from exc
            if not isinstance(row, Mapping):
                raise ValueError(f"jsonl_row_not_mapping:{path}:{rows + 1}")
            canonical = (
                json.dumps(row, sort_keys=True, default=str) + "\n"
            ).encode("utf-8")
            source_canonical = source_canonical and canonical == raw
            projected = projector(row)
            projected_bytes += len(
                (json.dumps(projected, sort_keys=True, default=str) + "\n").encode(
                    "utf-8"
                )
            )
            rows += 1
    block_size = max(512, int(path.stat().st_blksize or 4096))
    return {
        "path": str(path.resolve()),
        "rows": rows,
        "source_bytes": int(path.stat().st_size),
        "source_allocated_bytes": _allocated_file_bytes(path),
        "source_sha256": digest.hexdigest(),
        "source_is_canonical_append_jsonl": source_canonical,
        "projected_bytes": projected_bytes,
        "projected_allocated_bytes_estimate": _estimated_allocated_bytes(
            projected_bytes,
            block_size=block_size,
        ),
        "allocation_block_size": block_size,
    }


def _scalar_projector(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return cuts._project_scalar_row(row, frozenset())


def _stage(
    name: str,
    logical_bytes: int,
    allocated_bytes: int,
    *,
    prior_logical_bytes: int | None = None,
    prior_allocated_bytes: int | None = None,
    basis: str,
) -> dict[str, Any]:
    return {
        "stage": name,
        "logical_bytes": int(logical_bytes),
        "allocated_bytes": int(allocated_bytes),
        "logical_delta_bytes": (
            None
            if prior_logical_bytes is None
            else int(logical_bytes - prior_logical_bytes)
        ),
        "allocated_delta_bytes": (
            None
            if prior_allocated_bytes is None
            else int(allocated_bytes - prior_allocated_bytes)
        ),
        "logical_ratio_to_prior": (
            None
            if not prior_logical_bytes
            else round(logical_bytes / prior_logical_bytes, 6)
        ),
        "basis": basis,
    }


def bounded_waterfall(
    *,
    baseline_route: Path,
    candidate_route: Path,
) -> dict[str, Any]:
    """Exact offline cut waterfall plus observed candidate namespace."""

    baseline_route = Path(baseline_route)
    candidate_route = Path(candidate_route)
    baseline_sidecar = Path(f"{baseline_route}.semantic-diagnostic")
    candidate_sidecar = Path(f"{candidate_route}.semantic-diagnostic")
    base_route = inventory(baseline_route)
    base_side = inventory(baseline_sidecar)
    candidate_route_inventory = inventory(candidate_route)
    candidate_side_inventory = inventory(candidate_sidecar)

    base_logical = base_route["logical_bytes"] + base_side["logical_bytes"]
    base_allocated = base_route["allocated_bytes"] + base_side["allocated_bytes"]
    stages = [
        _stage(
            "frozen_namespace",
            base_logical,
            base_allocated,
            basis="observed CG frozen route plus semantic namespace",
        )
    ]

    ledger = [
        _jsonl_projection(
            _unique_suffix(baseline_route, suffix),
            _scalar_projector,
        )
        for suffix in (DECISION_SUFFIX, SCORECARD_SUFFIX)
    ]
    logical = base_logical + sum(
        row["projected_bytes"] - row["source_bytes"] for row in ledger
    )
    allocated = base_allocated + sum(
        row["projected_allocated_bytes_estimate"]
        - row["source_allocated_bytes"]
        for row in ledger
    )
    stages.append(
        _stage(
            "ledger_scalar_projection",
            logical,
            allocated,
            prior_logical_bytes=base_logical,
            prior_allocated_bytes=base_allocated,
            basis="exact reserialization of frozen DECISION and SCORECARD rows",
        )
    )

    missed = _jsonl_projection(
        _unique_suffix(baseline_route, MISSED_SUFFIX),
        cuts.project_missed_pool_row,
    )
    prior_logical, prior_allocated = logical, allocated
    logical += missed["projected_bytes"] - missed["source_bytes"]
    allocated += (
        missed["projected_allocated_bytes_estimate"]
        - missed["source_allocated_bytes"]
    )
    stages.append(
        _stage(
            "missed_pool_projection_v2",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="exact reader-complete v2 reserialization of frozen MISSED rows",
        )
    )

    semantic = [
        _jsonl_projection(
            _unique_suffix(baseline_sidecar, suffix),
            cuts.project_semantic_sidecar_row,
        )
        for suffix in SEMANTIC_SUFFIXES
    ]
    prior_logical, prior_allocated = logical, allocated
    logical += sum(
        row["projected_bytes"] - row["source_bytes"] for row in semantic
    )
    allocated += sum(
        row["projected_allocated_bytes_estimate"]
        - row["source_allocated_bytes"]
        for row in semantic
    )
    stages.append(
        _stage(
            "semantic_sidecar_projection",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="exact zero-field disclosure-row reserialization",
        )
    )

    compact_root = baseline_route / "compact-event-shards"
    compact = inventory(compact_root)
    prior_logical, prior_allocated = logical, allocated
    logical -= compact["logical_bytes"]
    allocated -= compact["allocated_bytes"]
    stages.append(
        _stage(
            "train_resident_event_sink",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis=(
                "remove the frozen compact proof spool; empty resident transport "
                "directories contain zero files"
            ),
        )
    )

    observed_candidate_logical = (
        candidate_route_inventory["logical_bytes"]
        + candidate_side_inventory["logical_bytes"]
    )
    observed_candidate_allocated = (
        candidate_route_inventory["allocated_bytes"]
        + candidate_side_inventory["allocated_bytes"]
    )
    return {
        "fixture": "January S1R1 prefix, 2026-01-01..2026-01-02",
        "scope": "all regular files in route plus .semantic-diagnostic namespace",
        "stages": stages,
        "projections": {
            "ledger": ledger,
            "missed": missed,
            "semantic": semantic,
            "compact_event_shards": compact,
        },
        "observed_candidate": {
            "logical_bytes": observed_candidate_logical,
            "allocated_bytes": observed_candidate_allocated,
            "route": candidate_route_inventory,
            "semantic_sidecar": candidate_side_inventory,
            "logical_minus_offline_floor_bytes": observed_candidate_logical - logical,
            "note": (
                "The offline floor substitutes only cut-addressable payload files. "
                "The observed namespace also carries different summary/authority metadata."
            ),
        },
    }


def _iter_compact_role_rows_at_root(
    compact_root: Path, role: str
) -> Iterable[dict[str, Any]]:
    roots = sorted(
        path.parent
        for path in Path(compact_root).rglob(frozen_sink.COMPACT_EVENT_MANIFEST)
    )
    if not roots:
        raise ValueError(f"compact_event_manifests_absent:{compact_root}")
    for root in roots:
        authority = json.loads((root / frozen_sink.COMPACT_EVENT_MANIFEST).read_text())
        sink = frozen_sink.ReplayCompactEventSink.open_sealed(
            root=root,
            expected_authority_root_sha256=str(
                authority.get("authority_root_sha256") or ""
            ),
        )
        yield from sink.iter_rows(role)


def _iter_compact_role_rows(route: Path, role: str) -> Iterable[dict[str, Any]]:
    yield from _iter_compact_role_rows_at_root(
        Path(route) / "compact-event-shards", role
    )


def _projected_stream_bytes(
    rows: Iterable[Mapping[str, Any]],
    projector: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[int, int]:
    count = 0
    byte_count = 0
    for row in rows:
        projected = projector(row)
        byte_count += len(
            (json.dumps(projected, sort_keys=True, default=str) + "\n").encode(
                "utf-8"
            )
        )
        count += 1
    return count, byte_count


def _projected_cold_preimage_bytes(
    preimage: Mapping[str, Any],
    projector: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> tuple[int, int]:
    """Stream a verified cold archive when an old compact role is absent."""

    from src.research_infra import b7_5_diagnostic_pool

    archive = Path(str(preimage["archive"]))
    if not archive.name.endswith(".cold"):
        raise ValueError(f"cold_preimage_archive_suffix_invalid:{archive}")
    logical_path = archive.with_name(archive.name[: -len(".cold")])
    resolver = b7_5_diagnostic_pool.cold_evidence_module().RawOrColdResolver()

    def rows() -> Iterable[Mapping[str, Any]]:
        for ordinal, raw in enumerate(
            resolver.iter_binary_lines(logical_path), start=1
        ):
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"cold_preimage_json_invalid:{logical_path}:{ordinal}"
                ) from exc
            if not isinstance(row, Mapping):
                raise ValueError(
                    f"cold_preimage_row_not_mapping:{logical_path}:{ordinal}"
                )
            yield row

    return _projected_stream_bytes(rows(), projector)


def month_reference(route: Path) -> dict[str, Any]:
    """Price CG's cuts over one completed CD full-January namespace, read-only."""

    route = Path(route)
    sidecar = Path(f"{route}.semantic-diagnostic")
    route_before = inventory(route)
    side_before = inventory(sidecar)
    missed_path = _unique_suffix(route, MISSED_SUFFIX)
    missed_rows, missed_v2_bytes = _projected_stream_bytes(
        _iter_compact_role_rows(route, "missed"),
        cuts.project_missed_pool_row,
    )
    semantic = [
        _jsonl_projection(
            _unique_suffix(sidecar, suffix),
            cuts.project_semantic_sidecar_row,
        )
        for suffix in SEMANTIC_SUFFIXES
    ]
    compact = inventory(route / "compact-event-shards")

    before_logical = route_before["logical_bytes"] + side_before["logical_bytes"]
    after_missed = before_logical - missed_path.stat().st_size + missed_v2_bytes
    after_semantic = after_missed + sum(
        row["projected_bytes"] - row["source_bytes"] for row in semantic
    )
    after_resident = after_semantic - compact["logical_bytes"]
    return {
        "route": str(route.resolve()),
        "arm_prefix": route.name,
        "source_contract": (
            "completed CD full-January route with ledger_scalar_projection and "
            "CD missed_pool_projection_v1 already applied"
        ),
        "source_namespace_logical_bytes": before_logical,
        "after_reader_complete_missed_v2_logical_bytes": after_missed,
        "after_semantic_projection_logical_bytes": after_semantic,
        "after_resident_sink_logical_bytes": after_resident,
        "missed_v1": {
            "path": str(missed_path.resolve()),
            "logical_bytes": int(missed_path.stat().st_size),
        },
        "missed_v2": {
            "rows": missed_rows,
            "logical_bytes": missed_v2_bytes,
            "keep_field_count": len(cuts._missed_keep_names()),
            "basis": "authenticated compact missed rows, streamed read-only",
        },
        "semantic": semantic,
        "compact_event_shards": compact,
        "caveat": (
            "This is an exact payload-byte transformation of CD's existing files, "
            "not a new economic run. Summary metadata is retained conservatively."
        ),
    }


def cold_month_reference(route: Path, compact_root: Path) -> dict[str, Any]:
    """Transform one cold-demoted frozen January arm without rehydrating it.

    The cold manifests provide the exact raw-ledger preimage sizes.  The
    separately preserved compact-event authority provides the authenticated
    original rows, so all three projectors can be priced using actual full-arm
    content.  Neither source is written or reconstituted on disk.
    """

    route = Path(route)
    compact_root = Path(compact_root)
    sidecar = Path(f"{route}.semantic-diagnostic")
    cold = {
        "decision": _cold_preimage(route, DECISION_SUFFIX),
        "scorecard": _cold_preimage(route, SCORECARD_SUFFIX),
        "missed": _cold_preimage(route, MISSED_SUFFIX),
    }
    route_remainder = _inventory_without_cold_archives(route)
    side_before = inventory(sidecar)
    compact = inventory(compact_root)

    projected: dict[str, dict[str, Any]] = {}
    for role, projector in (
        ("decision", _scalar_projector),
        ("scorecard", _scalar_projector),
        ("missed", cuts.project_missed_pool_row),
    ):
        rows, byte_count = _projected_stream_bytes(
            _iter_compact_role_rows_at_root(compact_root, role),
            projector,
        )
        source = "authenticated_compact_event_role"
        if rows == 0 and cold[role]["rows"] > 0:
            # The January v3 compact authority predates scorecard retention.
            # Its verified cold archive remains complete, so stream that role
            # rather than weakening the cross-source row-count assertion.
            rows, byte_count = _projected_cold_preimage_bytes(
                cold[role], projector
            )
            source = "verified_cold_archive_fallback"
        if rows != cold[role]["rows"]:
            raise ValueError(
                f"cold_projection_row_count_mismatch:{role}:"
                f"{cold[role]['rows']}:{rows}"
            )
        projected[role] = {
            "rows": rows,
            "logical_bytes": byte_count,
            "row_source": source,
        }

    semantic = [
        _jsonl_projection(
            _unique_suffix(sidecar, suffix),
            cuts.project_semantic_sidecar_row,
        )
        for suffix in SEMANTIC_SUFFIXES
    ]
    block_size = max(512, int(route.stat().st_blksize or 4096))

    raw_ledger_logical = sum(row["logical_bytes"] for row in cold.values())
    raw_ledger_allocated = sum(row["allocated_bytes"] for row in cold.values())
    logical = (
        route_remainder["logical_bytes"]
        + raw_ledger_logical
        + side_before["logical_bytes"]
        + compact["logical_bytes"]
    )
    allocated = (
        route_remainder["allocated_bytes"]
        + raw_ledger_allocated
        + side_before["allocated_bytes"]
        + compact["allocated_bytes"]
    )
    stages = [
        _stage(
            "frozen_namespace_pre_cold_demotion",
            logical,
            allocated,
            basis=(
                "verified cold-manifest raw preimages plus current non-cold "
                "files, semantic namespace and preserved compact authority"
            ),
        )
    ]

    prior_logical, prior_allocated = logical, allocated
    for role in ("decision", "scorecard"):
        logical += projected[role]["logical_bytes"] - cold[role]["logical_bytes"]
        allocated += _estimated_allocated_bytes(
            projected[role]["logical_bytes"], block_size=block_size
        ) - cold[role]["allocated_bytes"]
    stages.append(
        _stage(
            "ledger_scalar_projection",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="authenticated full-month decision and scorecard rows",
        )
    )

    prior_logical, prior_allocated = logical, allocated
    logical += projected["missed"]["logical_bytes"] - cold["missed"]["logical_bytes"]
    allocated += _estimated_allocated_bytes(
        projected["missed"]["logical_bytes"], block_size=block_size
    ) - cold["missed"]["allocated_bytes"]
    stages.append(
        _stage(
            "missed_pool_projection_v2",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="authenticated full-month missed rows, reader-complete v2",
        )
    )

    prior_logical, prior_allocated = logical, allocated
    logical += sum(row["projected_bytes"] - row["source_bytes"] for row in semantic)
    allocated += sum(
        row["projected_allocated_bytes_estimate"] - row["source_allocated_bytes"]
        for row in semantic
    )
    stages.append(
        _stage(
            "semantic_sidecar_projection",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="exact full-month zero-field disclosure-row reserialization",
        )
    )

    prior_logical, prior_allocated = logical, allocated
    logical -= compact["logical_bytes"]
    allocated -= compact["allocated_bytes"]
    stages.append(
        _stage(
            "train_resident_event_sink",
            logical,
            allocated,
            prior_logical_bytes=prior_logical,
            prior_allocated_bytes=prior_allocated,
            basis="remove preserved compact proof spool from lane output",
        )
    )
    return {
        "route": str(route.resolve()),
        "compact_authority_root": str(compact_root.resolve()),
        "arm_prefix": route.name,
        "source_contract": (
            "cold-demoted frozen full-January S1R1 raw-ledger preimages plus "
            "the separately preserved authenticated compact-event authority"
        ),
        "stages": stages,
        "after_resident_sink_logical_bytes": logical,
        "after_resident_sink_allocated_bytes": allocated,
        "cold_preimages": cold,
        "projected_ledgers": projected,
        "semantic": semantic,
        "route_remainder": route_remainder,
        "semantic_sidecar": side_before,
        "compact_event_shards": compact,
        "caveat": (
            "Exact storage transformation of the frozen January arm, not a new "
            "economic run. The source strategy generation differs from CD's "
            "repaired book and is used only as full-arm storage geometry."
        ),
    }


def build_receipt(
    *,
    baseline_report: Path,
    candidate_report: Path,
    profiled_report: Path | None = None,
    month_routes: Iterable[Path] = (),
    cold_month_references: Iterable[tuple[Path, Path]] = (),
) -> dict[str, Any]:
    baseline = json.loads(Path(baseline_report).read_text())
    candidate = json.loads(Path(candidate_report).read_text())
    if baseline.get("error") or candidate.get("error"):
        raise ValueError("footprint_run_errored")
    bounded = bounded_waterfall(
        baseline_route=Path(baseline["route"]),
        candidate_route=Path(candidate["route"]),
    )
    months = [month_reference(path) for path in month_routes]
    months.extend(
        cold_month_reference(route, compact_root)
        for route, compact_root in cold_month_references
    )
    free = int(shutil.disk_usage(Path(candidate["route"])).free)
    worst_month = max(
        (
            row.get(
                "after_resident_sink_allocated_bytes",
                row["after_resident_sink_logical_bytes"],
            )
            for row in months
        ),
        default=bounded["observed_candidate"]["allocated_bytes"],
    )
    hard_ceiling = free // worst_month if worst_month else 0
    operational_ceiling = max(0, hard_ceiling - 1)
    profiled = (
        json.loads(Path(profiled_report).read_text()) if profiled_report else None
    )
    return {
        "schema": SCHEMA,
        "evidence_class": (
            "TRAINING_FOOTPRINT_EVIDENCE - never sealed or admission-grade"
        ),
        "bounded_waterfall": bounded,
        "runtime": {
            "baseline": {
                "report": str(Path(baseline_report).resolve()),
                "wall_seconds": baseline.get("wall_seconds"),
                "maxrss_bytes": (baseline.get("rusage") or {}).get("maxrss_bytes"),
            },
            "candidate": {
                "report": str(Path(candidate_report).resolve()),
                "wall_seconds": candidate.get("wall_seconds"),
                "maxrss_bytes": (candidate.get("rusage") or {}).get("maxrss_bytes"),
                "cut_report": candidate.get("cut_report"),
            },
            "profiled_candidate": (
                None
                if profiled is None
                else {
                    "report": str(Path(profiled_report).resolve()),
                    "wall_seconds": profiled.get("wall_seconds"),
                    "maxrss_bytes": (profiled.get("rusage") or {}).get(
                        "maxrss_bytes"
                    ),
                    "profile": profiled.get("profile"),
                }
            ),
        },
        "month_references": months,
        "disk_ceiling": {
            "free_bytes_at_measurement": free,
            "per_arm_planning_bytes": worst_month,
            "planning_basis": (
                "largest transformed full-month allocated footprint when a "
                "month reference exists; otherwise observed bounded allocation"
            ),
            "hard_arithmetic_arm_count": hard_ceiling,
            "operational_arm_count_with_one_full_arm_reserved": operational_ceiling,
            "rule": (
                "floor(actual_free/per_arm); operational ceiling subtracts one "
                "full-arm slot so the plan never targets a full filesystem"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--profiled")
    parser.add_argument("--month-reference", action="append", default=[])
    parser.add_argument("--cold-month-route", action="append", default=[])
    parser.add_argument("--cold-month-compact-root", action="append", default=[])
    parser.add_argument("--out", required=True)
    ns = parser.parse_args()
    if len(ns.cold_month_route) != len(ns.cold_month_compact_root):
        parser.error(
            "--cold-month-route and --cold-month-compact-root must be paired"
        )
    receipt = build_receipt(
        baseline_report=Path(ns.baseline),
        candidate_report=Path(ns.candidate),
        profiled_report=Path(ns.profiled) if ns.profiled else None,
        month_routes=(Path(item) for item in ns.month_reference),
        cold_month_references=(
            (Path(route), Path(compact_root))
            for route, compact_root in zip(
                ns.cold_month_route,
                ns.cold_month_compact_root,
                strict=True,
            )
        ),
    )
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True, default=str) + "\n")
    print(f"[footprint] {out} hard_disk_ceiling={receipt['disk_ceiling']['hard_arithmetic_arm_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
