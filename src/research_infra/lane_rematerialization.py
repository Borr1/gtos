"""True-UTC, relocatable replay inputs for the unsealed training lane.

This module is deliberately offline.  It never imports MetaTrader5, opens a
broker connection, or calls an exporter.  It consumes already-captured FTMO
research files, applies the sanctioned :mod:`src.utils.broker_clock` conversion,
and writes a new LANE namespace whose runtime identities are paths relative to
the repository root.

The historical B7.5 bundle remains immutable.  ``campaign_sealed`` is false in
every authority emitted here: the word ``SEALED`` inside a prepared-day-pack is
the pack format's byte-integrity marker, not a campaign/economic seal.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import fcntl
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import stat
import threading
import time
from array import array
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from src.costs.model import (
    CostTruthError,
    SpreadGeometryEvidence,
    VerifiedQuoteGeometryReceipt,
)

from src.research_infra import (
    replay_acceleration_attempt5_typed_sparse_runner as attempt5,
)
from src.research_infra import replay_acceleration_integrated_source as integrated
from src.research_infra import replay_prepared_day_pack
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
from src.research_infra.completed_bar_witness import (
    observed_successor_closed_bar_rows_until,
)
from src.research_infra.train_engine import TRAIN_ENGINE_VERSION, guard, lane
from src.research_infra.train_engine import march_one_shot
from src.research_infra.train_engine import repairs as repairs_mod
from src.research_infra.wave21_full_flow_truth import (
    wave21_full_flow_truth_mode_enabled,
)
from src.utils.broker_clock import (
    NEW_YORK_PLUS_7,
    UsDstAnchor,
    broker_epoch_to_utc,
    utc_to_broker_naive,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LANE_ROOT = (
    REPO_ROOT
    / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
DEFAULT_REGISTRY_NAME = "LANE_INPUT_REGISTRY.json"
CATALOG_NAME = "SOURCE_CATALOG.json"
REGISTRY_SCHEMA = "gtos.lane.rematerialization.input_registry.v1"
SOURCE_SCHEMA = "gtos.lane.rematerialization.source_manifest.v1"
CATALOG_SCHEMA = "gtos.lane.rematerialization.source_catalog.v1"
MATERIALIZATION_SCHEMA = "gtos.lane.rematerialization.receipt.v1"
PACK_BUILD_SCHEMA = "gtos.lane.rematerialization.pack_build.v1"
VALIDATION_SCHEMA = "gtos.lane.rematerialization.validation.v1"
SMOKE_SCHEMA = "gtos.lane.rematerialization.pack_smoke.v1"
FEATURE_SHIFT_SCHEMA = "gtos.lane.rematerialization.january_feature_shift.v1"
ARM_INVARIANCE_SCHEMA = "gtos.lane.rematerialization.january_arm_invariance.v1"
BASELINE_ECONOMICS_SCHEMA = (
    "gtos.lane.rematerialization.baseline_economics_authority.v1"
)
LANE_EVIDENCE = "LANE_ITERATION_EVIDENCE - unbilled exploration, never admission-grade"

DEFAULT_BAR_ROOTS = {
    "D1_H4": Path(
        "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/"
        "deep_universe_h4d1_2014_2026"
    ),
    "M15": Path(
        "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/"
        "bridge_ftmo_m15_20250601_20260610"
    ),
}
DEFAULT_M1_PARENT = Path(
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports"
)
DEFAULT_TICK_ROOT = Path(
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/"
    "bridge_ftmo_ticks_micro_2025_2026"
)
FROZEN_JANUARY_LEGACY = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/.hermes/evidence/"
    "phase-d/january-post-acceleration-source-20260723T225928Z/"
    "materialization-current/bundle/legacy"
)
FROZEN_JANUARY_EXECUTION_SEAL = Path(
    "/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/.hermes/evidence/"
    "phase-d/january-post-acceleration-source-20260723T225928Z/"
    "JANUARY_EXECUTION_SEAL_R3.json"
)
CD_S0R0_REPORT = (
    REPO_ROOT
    / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/"
    "CD_ARM_REPORT_S0R0_V1.json"
)
CD_S0R0_POOL_SUMMARY = (
    REPO_ROOT
    / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/"
    "CD_REPAIRED_POOL_S0R0_V1.json"
)
PACK_CONFIG_IDENTITY_ROUTE = (
    REPO_ROOT
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "attempt_5_typed_sparse/CJ_PACK_CONFIG_IDENTITY_ONLY"
)

TICK_SYMBOLS = ("EURUSD", "USDJPY", "XAGUSD", "XAUUSD")
RAW_CAMPAIGN_SYMBOLS = tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
RAW_CAMPAIGN_DECISION_TIMEFRAMES = ("D1", "H4", "H1", "M15")
RAW_CAMPAIGN_REQUIRED_TIMEFRAMES = (
    *RAW_CAMPAIGN_DECISION_TIMEFRAMES,
    "M1",
)
RAW_CAMPAIGN_WINDOW_IDS = frozenset({"october_2025", "november_2025"})
RAW_CAMPAIGN_DEVELOPMENT_DAYS = (
    "2025-10-27",
    "2025-10-28",
    "2025-10-29",
    "2025-11-03",
    "2025-11-04",
    "2025-11-07",
)
RAW_CAMPAIGN_DECISION_DAYS = (
    "2025-10-30",
    "2025-11-06",
)
RAW_CAMPAIGN_RESERVE_DAYS = (
    "2025-10-31",
    "2025-11-05",
)
RAW_CAMPAIGN_APPROVED_DAYS = (
    *RAW_CAMPAIGN_DEVELOPMENT_DAYS,
    *RAW_CAMPAIGN_DECISION_DAYS,
)
RAW_CAMPAIGN_ESTATE_PATH = REPO_ROOT / (
    "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
    "verification/DEVELOPMENT_AND_UNTOUCHED_ESTATES_V1.json"
)
RAW_CAMPAIGN_ESTATE_FILE_SHA256 = (
    "c075d09e8ba8372d776500d8a1c9dc4bb42fad964498e8fd61b6cc00ce1d262c"
)
RAW_CAMPAIGN_ESTATE_PAYLOAD_SHA256 = (
    "d446e7480cd9db7c7fa6a550c9472238c8cacb6aa7b6a1d27d387fa84bce5f58"
)
RAW_CAMPAIGN_REGISTRY_PATH = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json"
)
RAW_CAMPAIGN_REGISTRY_FILE_SHA256 = (
    "fc505c32344247ad76790b92281bc3d9ff65d6e6d85c5a3843ce07f5e2a0b797"
)
RAW_CAMPAIGN_REGISTRY_ROOT_SHA256 = (
    "b2760cdefa8786cb5d430f5f81c9458a48c87e01e4317d78b4b87b1d64394502"
)
_RAW_CAMPAIGN_WITNESS_LOCK = threading.RLock()


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    start: str
    end: str
    split: str
    month: str

    @property
    def days(self) -> tuple[str, ...]:
        first = date.fromisoformat(self.start)
        last = date.fromisoformat(self.end)
        return tuple(
            (first + timedelta(days=offset)).isoformat()
            for offset in range((last - first).days + 1)
        )

    @property
    def start_utc(self) -> datetime:
        return datetime.fromisoformat(self.start).replace(tzinfo=timezone.utc)

    @property
    def end_exclusive_utc(self) -> datetime:
        return datetime.fromisoformat(self.end).replace(tzinfo=timezone.utc) + timedelta(days=1)


WINDOWS: dict[str, WindowSpec] = {
    "october_2025": WindowSpec(
        "october_2025", "2025-10-01", "2025-10-31", "lane_validation", "202510"
    ),
    "november_2025": WindowSpec(
        "november_2025", "2025-11-01", "2025-11-29", "lane_validation", "202511"
    ),
    "january_2026": WindowSpec(
        "january_2026", "2026-01-01", "2026-01-31", "development", "202601"
    ),
    "february_2026": WindowSpec(
        "february_2026", "2026-02-01", "2026-02-28", "lane_validation", "202602"
    ),
    "april_2026": WindowSpec(
        "april_2026", "2026-04-01", "2026-04-30", "adverse_development", "202604"
    ),
    "may_2026": WindowSpec(
        "may_2026", "2026-05-01", "2026-05-31", "lane_validation", "202605"
    ),
    # The estate's only outcome-unread month. Registering it here does NOT make
    # it readable: `guard.authorize_window` refuses every March day unless the
    # process carries the `march_one_shot` authorization (the prereg's own
    # digest), and `LaneInputRegistry` refuses a registry whose
    # `march_window_registered` is true for the same reason. Both fuses are
    # independent of this table; this entry only gives the one authorized event
    # a window id to name.
    "march_2026": WindowSpec(
        "march_2026", "2026-03-01", "2026-03-31", "reserved_unread_one_shot", "202603"
    ),
    # ---------------------------------------------------------------------
    # The 2025 extension (Session LM-MAT, OD-BROAD-FORENSIC-2). CJ materialized
    # five windows out of a catalog that spans 2025-06-01T21:00Z..2026-06-09T20:45Z
    # -- twelve-plus months of sha256-verified M15 bars. These seven entries name
    # the rest of the covered 2025 calendar so it can be materialized as lane
    # INPUT the same way. Registering a window here reads nothing: `WINDOWS` is a
    # naming table, and every fuse (blackout, surface, registry) is independent
    # of it, exactly as the `march_2026` comment above says.
    #
    # `june_2025` starts on the 3rd, and both days it gives up were measured
    # rather than guessed.
    #
    # 2025-06-01 is out because the M15 catalog's per-symbol `first_utc` is
    # staggered across 2025-05-31T22:00Z / 06-01T21:00Z / 06-01T22:00Z /
    # 06-02T00:00Z -- no window starting on the 1st has complete 24-symbol
    # coverage, and `materialize_lane_window_sources`' own coverage assertion
    # refuses it.
    #
    # 2025-06-02 is out because starting there builds sources fine and then
    # fails in `build-packs` with
    # `prepared_timestamp_invalid:$.symbols[UKOIL_cash].asof_row.
    # decision_max_source_time_utc_by_timeframe.H1`. UKOIL_cash is precisely the
    # symbol with the LATEST M15 start in the whole archive (2025-06-02T00:00Z),
    # H1 is derived from M15 here (`use_native_h1=False`), and a symbol with no
    # M15 history before the first decision has no H1 as-of stamp to write. One
    # day of lead-in is the cheapest fix that gives every symbol a complete
    # prior H1.
    "june_2025": WindowSpec(
        "june_2025", "2025-06-03", "2025-06-30", "lane_validation", "202506"
    ),
    "july_2025": WindowSpec(
        "july_2025", "2025-07-01", "2025-07-31", "lane_validation", "202507"
    ),
    # August and November end one day short of the calendar month, and the reason
    # is the same mechanical fact for both: 2025-08-31 and 2025-11-30 are SUNDAYS.
    #
    # A UTC Sunday holds only the 21:00-24:00 week-open sliver. The engine folds
    # such a fragment into its ENCLOSING broker day via `lane_authority_rebind`
    # -- which works for every mid-month Sunday (January bound with 3 such
    # rebinds) because the enclosing Monday is inside the window's own M1 source
    # family. For a month-FINAL Sunday the enclosing Monday is in the NEXT month,
    # whose M1 family this manifest does not bind, so the day cannot rebind, sits
    # below the session-scaled floor, and `static_source_authority_plan` returns
    # `valid: False` with `status: invalid_static_source_authority_plan`.
    # Measured, not inferred: november_2025 failed with exactly 21 unresolved
    # symbol-days, all of them 2025-11-30, all
    # `selected_day_source_below_session_scaled_floor`.
    #
    # `may_2026` (2026-05-31, also a Sunday) carries the identical latent defect
    # and is the ONE pre-existing window with no bound canonical source-plan
    # digest. That is not a coincidence and it is not this session's to repair.
    "august_2025": WindowSpec(
        "august_2025", "2025-08-01", "2025-08-30", "lane_validation", "202508"
    ),
    "september_2025": WindowSpec(
        "september_2025", "2025-09-01", "2025-09-30", "lane_validation", "202509"
    ),
    "october_2025": WindowSpec(
        "october_2025", "2025-10-01", "2025-10-31", "lane_validation", "202510"
    ),
    "november_2025": WindowSpec(  # 2025-11-30 is a Sunday -- see august_2025 above
        "november_2025", "2025-11-01", "2025-11-29", "lane_validation", "202511"
    ),
    "december_2025": WindowSpec(
        "december_2025", "2025-12-01", "2025-12-31", "lane_validation", "202512"
    ),
}

#: The windows `materialize_lane_window_sources` is allowed to add. Naming them
#: rather than "anything not already registered" is deliberate: `march_2026` has
#: its own one-shot path and its own fuses, and the four CJ windows must never be
#: re-materialized under any code path at all.
LANE_EXTENSION_WINDOW_IDS = (
    "june_2025",
    "july_2025",
    "august_2025",
    "september_2025",
    "october_2025",
    "november_2025",
    "december_2025",
)

#: The four windows CJ materialized. The March one-shot must leave every one of
#: them byte-identical -- `MARCH_PREREG_V1` §2.3 -- so the extension path names
#: them rather than trusting itself not to touch them.
PRE_MARCH_WINDOW_IDS = ("january_2026", "february_2026", "april_2026", "may_2026")


class LaneRematerializationError(RuntimeError):
    """A source, registry, or pack failed a fail-closed LANE check."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
        default=str,
    ).encode("utf-8")


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_root(payload: Mapping[str, Any], field: str) -> str:
    core = dict(payload)
    core.pop(field, None)
    return _stable_sha256(core)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = json.dumps(payload, indent=1, sort_keys=True, default=str) + "\n"
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _repo_relative(path: Path, *, repo_root: Path | None = None) -> str:
    repo_root = REPO_ROOT if repo_root is None else repo_root
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise LaneRematerializationError(
            f"lane_root_must_be_inside_repo:{path}"
        ) from exc


def _logical_repo_root_for_registry(
    *, registry_path: Path, manifest: Mapping[str, Any]
) -> Path:
    """Recover the worktree that owns a relocatable machine-local registry.

    CJ persisted source identities relative to its worktree. A successor must
    reference that content-addressed estate in place, not copy it. If the
    registry is local, use this module's root. Otherwise derive the owning root
    from the manifest's bound ``lane_root_repo_relpath`` and prove that it
    resolves exactly to the registry parent.
    """

    resolved_registry = registry_path.resolve()
    try:
        resolved_registry.relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        return REPO_ROOT.resolve()

    raw = Path(str(manifest.get("lane_root_repo_relpath") or ""))
    if (
        raw.is_absolute()
        or not raw.parts
        or any(part in ("", ".", "..") for part in raw.parts)
    ):
        raise LaneRematerializationError("lane_logical_repo_root_binding_missing")
    candidate = resolved_registry.parent
    for _part in raw.parts:
        candidate = candidate.parent
    if (candidate / raw).resolve() != resolved_registry.parent:
        raise LaneRematerializationError("lane_logical_repo_root_binding_mismatch")
    return candidate.resolve()


def _safe_relative(root: Path, raw: str) -> Path:
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise LaneRematerializationError(f"non_relocatable_path:{raw}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise LaneRematerializationError(f"lane_path_escape:{raw}") from exc
    return resolved


def _lane_argument_shell_prefix(output_prefix: str, arm_id: str) -> str:
    """Return a historical-builder-only prefix without leaking its claim to runtime."""

    if (
        not isinstance(output_prefix, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", output_prefix)
        or ".." in output_prefix
        or "_B7_5_" in output_prefix.upper()
    ):
        raise LaneRematerializationError(
            "lane_output_prefix_must_be_safe_and_omit_historical_B7_5_claim"
        )
    if arm_id not in {"S0R0", "S1R0", "S0R1", "S1R1"}:
        raise LaneRematerializationError(f"lane_arm_unknown:{arm_id}")
    return f"CJ_LANE_ARGUMENT_SHELL_B7_5_{arm_id}"


def _parse_broker_bar_time(value: str) -> datetime:
    try:
        wall = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LaneRematerializationError(f"bar_timestamp_invalid:{value}") from exc
    # Historical exports decoded the broker epoch as UTC. Reconstruct that raw
    # epoch and use the same sanctioned function as the repaired exporter.
    epoch = wall.replace(tzinfo=timezone.utc).timestamp()
    return broker_epoch_to_utc(epoch, NEW_YORK_PLUS_7)


def _transform_bar_file(
    *,
    source: Path,
    destination: Path,
    symbol: str,
    mapped_symbol: str,
    timeframe: str,
    source_family: str,
    lane_root: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    if not source.is_file() or source.is_symlink():
        raise LaneRematerializationError(f"bar_source_invalid:{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    first_utc: str | None = None
    last_utc: str | None = None
    with source.open("r", newline="", encoding="utf-8") as src:
        reader = csv.DictReader(src)
        if not reader.fieldnames or "time" not in reader.fieldnames:
            raise LaneRematerializationError(f"bar_time_column_missing:{source}")
        with destination.open("w", newline="", encoding="utf-8") as dst:
            writer = csv.DictWriter(dst, fieldnames=list(reader.fieldnames))
            writer.writeheader()
            for raw in reader:
                true_utc = _parse_broker_bar_time(str(raw.get("time") or ""))
                stamp = true_utc.isoformat()
                row = dict(raw)
                row["time"] = stamp
                writer.writerow(row)
                row_count += 1
                first_utc = first_utc or stamp
                last_utc = stamp
            dst.flush()
            os.fsync(dst.fileno())
    if row_count <= 0:
        raise LaneRematerializationError(f"bar_source_empty:{source}")
    return {
        "symbol": symbol,
        "mapped_symbol": mapped_symbol,
        "timeframe": timeframe,
        "source_family": source_family,
        "lane_relpath": destination.relative_to(lane_root).as_posix(),
        "repo_relpath": _repo_relative(destination, repo_root=repo_root),
        "row_count": row_count,
        "first_utc": first_utc,
        "last_utc": last_utc,
        "source_snapshot_name": source.parent.name,
        "source_file_name": source.name,
        "source_sha256": _file_sha256(source),
        "sha256": _file_sha256(destination),
        "time_column_basis": "true_utc",
        "clock_conversion": "broker_epoch_to_utc",
        "broker_clock_rule": NEW_YORK_PLUS_7.name,
        "economic_columns_rewritten": [],
    }


def _find_bar_source(root: Path, symbol: str, timeframe: str) -> tuple[Path, str]:
    for mapped in attempt5.symbol_aliases(symbol):
        candidate = root / f"{mapped}_{timeframe}.csv"
        if candidate.is_file() and not candidate.is_symlink():
            return candidate, mapped
    raise LaneRematerializationError(
        f"bar_source_missing:{root.name}:{symbol}:{timeframe}"
    )


def _tick_source_path(root: Path, symbol: str) -> Path:
    base = root / "ticks" / symbol / "microstructure_ticks.jsonl"
    if base.is_file() and not base.is_symlink():
        return base
    compressed = Path(f"{base}.gz")
    if compressed.is_file() and not compressed.is_symlink():
        return compressed
    raise LaneRematerializationError(f"tick_source_missing:{symbol}:{root}")


def _extract_time_msc(raw_line: bytes) -> int | None:
    marker = b'"time_msc"'
    start = raw_line.find(marker)
    if start < 0:
        return None
    start = raw_line.find(b":", start + len(marker))
    if start < 0:
        return None
    start += 1
    while start < len(raw_line) and raw_line[start] in b" \t":
        start += 1
    end = start
    while end < len(raw_line) and 48 <= raw_line[end] <= 57:
        end += 1
    try:
        return int(raw_line[start:end])
    except ValueError:
        return None


def _transform_tick_file(
    *,
    source: Path,
    symbol: str,
    lane_root: Path,
    destination_by_window: Mapping[str, Path],
    source_metadata: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    handles: dict[str, Any] = {}
    digests = {window_id: hashlib.sha256() for window_id in destination_by_window}
    counts = {window_id: 0 for window_id in destination_by_window}
    first: dict[str, str | None] = {window_id: None for window_id in destination_by_window}
    last: dict[str, str | None] = {window_id: None for window_id in destination_by_window}
    intervals = {
        window_id: (WINDOWS[window_id].start_utc, WINDOWS[window_id].end_exclusive_utc)
        for window_id in destination_by_window
    }
    for window_id, destination in destination_by_window.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        handles[window_id] = destination.open("wb")
    opener = gzip.open if source.suffix == ".gz" else open
    try:
        with opener(source, "rb") as src:
            for raw_line in src:
                time_msc = _extract_time_msc(raw_line)
                if time_msc is None:
                    continue
                true_utc = broker_epoch_to_utc(time_msc / 1000.0, NEW_YORK_PLUS_7)
                selected = next(
                    (
                        window_id
                        for window_id, (start, end) in intervals.items()
                        if start <= true_utc < end
                    ),
                    None,
                )
                if selected is None:
                    continue
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    raise LaneRematerializationError(
                        f"tick_json_invalid:{symbol}:{time_msc}"
                    ) from exc
                stamp = true_utc.isoformat()
                payload["time"] = stamp
                payload["ts_utc"] = stamp
                # The raw broker epoch is evidence and the dedup key. Never alter it.
                payload["time_msc"] = time_msc
                encoded = _canonical_bytes(payload) + b"\n"
                handles[selected].write(encoded)
                digests[selected].update(encoded)
                counts[selected] += 1
                first[selected] = first[selected] or stamp
                last[selected] = stamp
    finally:
        for handle in handles.values():
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
    output: dict[str, dict[str, Any]] = {}
    for window_id, destination in destination_by_window.items():
        if counts[window_id] <= 0:
            destination.unlink()
            continue
        output[window_id] = {
            "symbol": symbol,
            "mapped_symbol": timewarp.ftmo_symbol(symbol),
            "timeframe": "TICK",
            "source_family": "bridge_ftmo_ticks_micro_2025_2026_true_utc",
            "lane_relpath": destination.relative_to(lane_root).as_posix(),
            "repo_relpath": _repo_relative(destination, repo_root=repo_root),
            "row_count": counts[window_id],
            "first_utc": first[window_id],
            "last_utc": last[window_id],
            "sha256": digests[window_id].hexdigest(),
            "source_snapshot_name": source.parent.parent.parent.name,
            "source_file_name": source.name,
            "source_sha256": str(source_metadata.get("sha256") or _file_sha256(source)),
            "source_server_redacted": source_metadata.get("source_server_redacted"),
            "source_server_hash": source_metadata.get("source_server_hash"),
            "source_account_redacted": source_metadata.get("source_account_redacted"),
            "source_account_hash": source_metadata.get("source_account_hash"),
            "time_column_basis": "true_utc",
            "clock_conversion": "broker_epoch_to_utc",
            "broker_clock_rule": NEW_YORK_PLUS_7.name,
            "raw_broker_epoch_preserved": True,
            "economic_columns_rewritten": [],
        }
    return output


def _load_tick_manifest(root: Path) -> dict[str, Mapping[str, Any]]:
    manifest = root / "manifest.json"
    if not manifest.is_file() or manifest.is_symlink():
        raise LaneRematerializationError(f"tick_manifest_invalid:{manifest}")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, Mapping):
        raise LaneRematerializationError("tick_manifest_files_invalid")
    output: dict[str, Mapping[str, Any]] = {}
    for raw in files.values():
        if not isinstance(raw, Mapping):
            continue
        symbol = str(raw.get("file_symbol") or raw.get("symbol") or "")
        if symbol:
            output[symbol] = raw
    return output


def _source_manifest(
    *,
    lane_root: Path,
    window: WindowSpec,
    bars: Sequence[Mapping[str, Any]],
    ticks: Sequence[Mapping[str, Any]],
    repo_root: Path | None = None,
    tick_gap_status: str | None = None,
) -> dict[str, Any]:
    tick_symbols = {str(row["symbol"]) for row in ticks}
    gaps = [
        {
            "symbol": symbol,
            "timeframe": "TICK",
            # `tick_gap_status` is how a caller states a WHOLE-WINDOW absence it
            # established from capture metadata. Defaulting to None preserves
            # CJ's five manifests byte-for-byte; without it, a 2025 window with
            # no captured ticks at all would label 24 symbols
            # "no_captured_tick_source_for_symbol", which is false -- all four
            # tick symbols ARE captured, just not in that calendar period.
            "status": tick_gap_status
            or (
                "captured_tick_archive_ends_before_window"
                if window.window_id == "may_2026"
                else "no_captured_tick_source_for_symbol"
            ),
            "ordered_tick_truth_satisfied": False,
        }
        for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
        if symbol not in tick_symbols
    ]
    core: dict[str, Any] = {
        "schema": SOURCE_SCHEMA,
        "status": "LANE_TRUE_UTC_SOURCE_AUTHORITY_VALID",
        "evidence_class": LANE_EVIDENCE,
        "campaign_sealed": False,
        "economic_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "path_binding": "repo_relative_logical_paths_resolved_from_registry",
        "lane_root_repo_relpath": _repo_relative(lane_root, repo_root=repo_root),
        "window_id": window.window_id,
        "window": [window.start, window.end],
        "surface": "VAL",
        "clock": {
            **NEW_YORK_PLUS_7.provenance(),
            "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
            "time_column_basis": "true_utc",
        },
        "bar_sources": sorted(
            (dict(row) for row in bars),
            key=lambda row: (str(row["symbol"]), str(row["timeframe"])),
        ),
        "tick_sources": sorted(
            (dict(row) for row in ticks), key=lambda row: str(row["symbol"])
        ),
        "tick_gaps": gaps,
        "bar_symbol_count": len({str(row["symbol"]) for row in bars}),
        "bar_source_count": len(bars),
        "tick_symbol_count": len(tick_symbols),
        "tick_gap_count": len(gaps),
        "march_source_only_disclosure": (
            "April static-bar lookback mechanically includes March source rows; no March "
            "pack, candidate outcome, ledger, result, or economics is read or emitted."
            if window.window_id == "april_2026"
            else (
                "MARCH ONE-SHOT (MARCH_PREREG_V1, OD-FA2-1, owner word 2026-08-05). This "
                "manifest binds March 2026 INPUTS only -- bars and ticks, clock-converted, "
                "no candidate, outcome, ledger, result or economics is read or emitted at "
                "materialization. The decode event that reads March outcomes is the "
                "prereg's six-arm event and is separately authorized."
                if window.window_id == "march_2026"
                else None
            )
        ),
    }
    return {**core, "manifest_root_sha256": _stable_sha256(core)}


def materialize_sources(
    *,
    lane_root: Path = DEFAULT_LANE_ROOT,
    d1_h4_root: Path = DEFAULT_BAR_ROOTS["D1_H4"],
    m15_root: Path = DEFAULT_BAR_ROOTS["M15"],
    m1_parent: Path = DEFAULT_M1_PARENT,
    tick_root: Path = DEFAULT_TICK_ROOT,
) -> dict[str, Any]:
    """Create all four source authorities in one new, atomic LANE namespace."""

    lane_root = lane_root.resolve()
    _repo_relative(lane_root)
    if lane_root.exists() or lane_root.is_symlink():
        raise LaneRematerializationError(f"lane_root_must_be_new:{lane_root}")
    staging = lane_root.with_name(f".{lane_root.name}.{os.getpid()}.building")
    if staging.exists() or staging.is_symlink():
        raise LaneRematerializationError(f"lane_staging_root_exists:{staging}")
    staging.mkdir(parents=True)
    started = time.perf_counter()

    all_bars: list[dict[str, Any]] = []
    static_entries: dict[tuple[str, str], dict[str, Any]] = {}
    for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
        for timeframe, source_root, family in (
            ("D1", d1_h4_root, d1_h4_root.name),
            ("H4", d1_h4_root, d1_h4_root.name),
            ("M15", m15_root, m15_root.name),
        ):
            source, mapped = _find_bar_source(source_root, symbol, timeframe)
            destination = (
                staging / "sources/bars" / family / f"{mapped}_{timeframe}.csv"
            )
            row = _transform_bar_file(
                source=source,
                destination=destination,
                symbol=symbol,
                mapped_symbol=mapped,
                timeframe=timeframe,
                source_family=family,
                lane_root=staging,
            )
            # Logical paths describe the FINAL root, not the atomic staging name.
            final_destination = lane_root / row["lane_relpath"]
            row["repo_relpath"] = _repo_relative(final_destination)
            static_entries[(symbol, timeframe)] = row
            all_bars.append(row)

    m1_by_window: dict[str, list[dict[str, Any]]] = {}
    for window_id, window in WINDOWS.items():
        family = f"bridge_ftmo_m1_{window.month}"
        source_root = m1_parent / family
        rows: list[dict[str, Any]] = []
        for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
            source, mapped = _find_bar_source(source_root, symbol, "M1")
            destination = staging / "sources/bars" / family / f"{mapped}_M1.csv"
            row = _transform_bar_file(
                source=source,
                destination=destination,
                symbol=symbol,
                mapped_symbol=mapped,
                timeframe="M1",
                source_family=family,
                lane_root=staging,
            )
            final_destination = lane_root / row["lane_relpath"]
            row["repo_relpath"] = _repo_relative(final_destination)
            rows.append(row)
            all_bars.append(row)
        m1_by_window[window_id] = rows

    tick_manifest = _load_tick_manifest(tick_root)
    ticks_by_window: dict[str, list[dict[str, Any]]] = {
        window_id: [] for window_id in WINDOWS
    }
    tick_materialization_windows = {
        window_id: window
        for window_id, window in WINDOWS.items()
        if window.window_id != "may_2026"
    }
    for symbol in TICK_SYMBOLS:
        source = _tick_source_path(tick_root, symbol)
        destinations = {
            window_id: (
                staging
                / "sources/ticks"
                / window.month
                / symbol
                / "microstructure_ticks.jsonl"
            )
            for window_id, window in tick_materialization_windows.items()
        }
        transformed = _transform_tick_file(
            source=source,
            symbol=symbol,
            lane_root=staging,
            destination_by_window=destinations,
            source_metadata=tick_manifest.get(symbol) or {},
        )
        for window_id, row in transformed.items():
            final_destination = lane_root / row["lane_relpath"]
            row["repo_relpath"] = _repo_relative(final_destination)
            ticks_by_window[window_id].append(row)

    catalog_core = {
        "schema": CATALOG_SCHEMA,
        "status": "LANE_TRUE_UTC_SOURCE_CATALOG_VALID",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "lane_root_repo_relpath": _repo_relative(lane_root),
        "clock": {
            **NEW_YORK_PLUS_7.provenance(),
            "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
        },
        "bar_sources": sorted(
            all_bars,
            key=lambda row: (
                str(row["source_family"]),
                str(row["symbol"]),
                str(row["timeframe"]),
            ),
        ),
        "tick_source_count": sum(len(rows) for rows in ticks_by_window.values()),
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
    }
    catalog = {
        **catalog_core,
        "catalog_root_sha256": _stable_sha256(catalog_core),
    }
    _write_json(staging / CATALOG_NAME, catalog)

    registry_windows: dict[str, Any] = {}
    for window_id, window in WINDOWS.items():
        bars = [
            *(static_entries[(symbol, timeframe)]
              for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
              for timeframe in ("D1", "H4", "M15")),
            *m1_by_window[window_id],
        ]
        manifest = _source_manifest(
            lane_root=lane_root,
            window=window,
            bars=bars,
            ticks=ticks_by_window[window_id],
        )
        manifest_rel = Path("manifests") / f"{window_id}.json"
        _write_json(staging / manifest_rel, manifest)
        registry_windows[window_id] = {
            "window": [window.start, window.end],
            "split": window.split,
            "surface": "VAL",
            "source_manifest": manifest_rel.as_posix(),
            "source_manifest_root_sha256": manifest["manifest_root_sha256"],
            "pack_root": (Path("packs") / window_id).as_posix(),
            "pack_roots": {},
            "pack_status": "NOT_BUILT",
            "campaign_sealed": False,
        }
    registry_core = {
        "schema": REGISTRY_SCHEMA,
        "status": "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "path_binding": "all_authority_paths_relative_to_registry_parent",
        "catalog": CATALOG_NAME,
        "catalog_root_sha256": catalog["catalog_root_sha256"],
        "clock_rule": NEW_YORK_PLUS_7.name,
        "windows": registry_windows,
        "march_window_registered": False,
        "march_pack_built": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    registry = {
        **registry_core,
        "registry_root_sha256": _stable_sha256(registry_core),
    }
    _write_json(staging / DEFAULT_REGISTRY_NAME, registry)
    lane_root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging, lane_root)

    receipt_core = {
        "schema": MATERIALIZATION_SCHEMA,
        "status": "LANE_TRUE_UTC_SOURCE_MATERIALIZATION_COMPLETE",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "lane_root_repo_relpath": _repo_relative(lane_root),
        "registry_repo_relpath": _repo_relative(lane_root / DEFAULT_REGISTRY_NAME),
        "registry_root_sha256": registry["registry_root_sha256"],
        "catalog_root_sha256": catalog["catalog_root_sha256"],
        "bar_source_count": len(all_bars),
        "bar_row_count": sum(int(row["row_count"]) for row in all_bars),
        "tick_source_count": sum(len(rows) for rows in ticks_by_window.values()),
        "tick_row_count": sum(
            int(row["row_count"])
            for rows in ticks_by_window.values()
            for row in rows
        ),
        "window_completeness": {
            window_id: {
                "bar_symbols": 24,
                "bar_timeframes_per_symbol": 4,
                "tick_symbols": len(ticks_by_window[window_id]),
                "tick_gaps": 24 - len(ticks_by_window[window_id]),
            }
            for window_id in WINDOWS
        },
        "clock_conversion": "src.utils.broker_clock.broker_epoch_to_utc",
        "broker_clock_rule": NEW_YORK_PLUS_7.name,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "wall_seconds": round(time.perf_counter() - started, 3),
    }
    return {**receipt_core, "receipt_root_sha256": _stable_sha256(receipt_core)}


def materialize_march_sources(
    *,
    registry_path: Path,
    m1_parent: Path = DEFAULT_M1_PARENT,
    tick_root: Path = DEFAULT_TICK_ROOT,
) -> dict[str, Any]:
    """Add the `march_2026` window to an EXISTING lane root. Outcome-blind.

    `materialize_sources` builds a whole new namespace atomically and refuses an
    existing root (`lane_root_must_be_new`), which is right for a first
    materialization and useless for the March one-shot: the four CJ windows and
    their 17 GB of packs must survive untouched, and `MARCH_PREREG_V1` §2.3
    requires their digests to come out unchanged. So this function extends.

    What it adds, and nothing else:

    * `sources/bars/bridge_ftmo_m1_202603/` -- the 24 March M1 files, converted
      by the same `broker_epoch_to_utc` the other four windows used;
    * `sources/ticks/202603/<SYMBOL>/microstructure_ticks.jsonl` -- March slices
      of the four captured ordered-tick symbols;
    * `manifests/march_2026.json`;
    * one `windows["march_2026"]` entry in the registry, plus
      `march_window_registered: true`.

    The 24x3 STATIC bar rows (D1/H4/M15) are reused by reference from the
    existing catalog -- they are the same physical files the other four windows
    bind, already converted, and re-transforming them would rewrite bytes four
    other windows' manifest digests depend on.

    Outcome-blindness: bars and ticks are market inputs. No candidate, order,
    trade, ledger, economic field or summary statistic of any March outcome is
    computed, printed or logged here; the receipt carries counts and digests
    only. The decode event is separate and separately authorized.
    """

    authorization = march_one_shot.current()
    if authorization is None:
        raise LaneRematerializationError(
            "march_materialization_requires_one_shot_authorization"
        )
    started = time.perf_counter()
    registry_path = registry_path.resolve()
    lane_root = registry_path.parent
    window = WINDOWS["march_2026"]

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("registry_root_sha256") != _manifest_root(
        payload, "registry_root_sha256"
    ):
        raise LaneRematerializationError("lane_input_registry_invalid")
    if "march_2026" in (payload.get("windows") or {}):
        raise LaneRematerializationError("lane_march_window_already_registered")
    pre_march = {
        window_id: dict(entry)
        for window_id, entry in (payload.get("windows") or {}).items()
    }
    if set(pre_march) != set(PRE_MARCH_WINDOW_IDS):
        raise LaneRematerializationError(
            f"lane_pre_march_window_set_unexpected:{sorted(pre_march)}"
        )

    # The logical repo root the four existing manifests already encode. Every
    # new March artifact is written against the same one, so the extension is
    # indistinguishable from CJ's own output in shape.
    reference_manifest = json.loads(
        _safe_relative(
            lane_root, str(pre_march["january_2026"]["source_manifest"])
        ).read_text(encoding="utf-8")
    )
    logical_repo_root = _logical_repo_root_for_registry(
        registry_path=registry_path, manifest=reference_manifest
    )

    catalog = json.loads((lane_root / CATALOG_NAME).read_text(encoding="utf-8"))
    static_rows = {
        (str(row["symbol"]), str(row["timeframe"])): dict(row)
        for row in catalog.get("bar_sources") or ()
        if str(row["timeframe"]) in ("D1", "H4", "M15")
    }
    missing_static = [
        (symbol, timeframe)
        for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
        for timeframe in ("D1", "H4", "M15")
        if (symbol, timeframe) not in static_rows
    ]
    if missing_static:
        raise LaneRematerializationError(f"lane_static_bar_rows_missing:{missing_static}")

    family = f"bridge_ftmo_m1_{window.month}"
    source_root = m1_parent / family
    m1_rows: list[dict[str, Any]] = []
    for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
        source, mapped = _find_bar_source(source_root, symbol, "M1")
        destination = lane_root / "sources/bars" / family / f"{mapped}_M1.csv"
        if destination.exists() or destination.is_symlink():
            raise LaneRematerializationError(f"lane_march_bar_exists:{destination}")
        m1_rows.append(
            _transform_bar_file(
                source=source,
                destination=destination,
                symbol=symbol,
                mapped_symbol=mapped,
                timeframe="M1",
                source_family=family,
                lane_root=lane_root,
                repo_root=logical_repo_root,
            )
        )

    tick_manifest = _load_tick_manifest(tick_root)
    tick_rows: list[dict[str, Any]] = []
    for symbol in TICK_SYMBOLS:
        source = _tick_source_path(tick_root, symbol)
        destination = (
            lane_root / "sources/ticks" / window.month / symbol
            / "microstructure_ticks.jsonl"
        )
        if destination.exists() or destination.is_symlink():
            raise LaneRematerializationError(f"lane_march_tick_exists:{destination}")
        transformed = _transform_tick_file(
            source=source,
            symbol=symbol,
            lane_root=lane_root,
            destination_by_window={"march_2026": destination},
            source_metadata=tick_manifest.get(symbol) or {},
            repo_root=logical_repo_root,
        )
        row = transformed.get("march_2026")
        if row is not None:
            tick_rows.append(row)

    bars = [
        *(
            static_rows[(symbol, timeframe)]
            for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
            for timeframe in ("D1", "H4", "M15")
        ),
        *m1_rows,
    ]
    manifest = _source_manifest(
        lane_root=lane_root,
        window=window,
        bars=bars,
        ticks=tick_rows,
        repo_root=logical_repo_root,
    )
    manifest_rel = Path("manifests") / f"{window.window_id}.json"
    manifest_path = lane_root / manifest_rel
    if manifest_path.exists() or manifest_path.is_symlink():
        raise LaneRematerializationError(f"lane_march_manifest_exists:{manifest_path}")
    _write_json(manifest_path, manifest)

    with _registry_write_lock(registry_path):
        current = json.loads(registry_path.read_text(encoding="utf-8"))
        core = dict(current)
        core.pop("registry_root_sha256", None)
        windows = {key: dict(value) for key, value in core["windows"].items()}
        if set(windows) != set(PRE_MARCH_WINDOW_IDS):
            raise LaneRematerializationError("lane_registry_moved_under_march_extension")
        windows[window.window_id] = {
            "window": [window.start, window.end],
            "split": window.split,
            "surface": "VAL",
            "source_manifest": manifest_rel.as_posix(),
            "source_manifest_root_sha256": manifest["manifest_root_sha256"],
            "pack_root": (Path("packs") / window.window_id).as_posix(),
            "pack_roots": {},
            "pack_status": "NOT_BUILT",
            "campaign_sealed": False,
        }
        core["windows"] = windows
        core["march_window_registered"] = True
        core["march_one_shot"] = authorization.as_dict()
        core["status"] = "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY"
        updated = {**core, "registry_root_sha256": _stable_sha256(core)}
        _write_json(registry_path, updated)

    unchanged = {
        window_id: (
            updated["windows"][window_id] == pre_march[window_id]
        )
        for window_id in PRE_MARCH_WINDOW_IDS
    }
    if not all(unchanged.values()):
        raise LaneRematerializationError(
            f"lane_pre_march_windows_mutated:{sorted(k for k, v in unchanged.items() if not v)}"
        )

    receipt_core = {
        "schema": MATERIALIZATION_SCHEMA,
        "status": "LANE_TRUE_UTC_MARCH_SOURCE_EXTENSION_COMPLETE",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "march_one_shot": authorization.as_dict(),
        "window_id": window.window_id,
        "window": [window.start, window.end],
        "surface": "VAL",
        "lane_root_repo_relpath": _repo_relative(
            lane_root, repo_root=logical_repo_root
        ),
        "logical_source_repo_root": str(logical_repo_root),
        "registry_root_sha256": updated["registry_root_sha256"],
        "source_manifest_root_sha256": manifest["manifest_root_sha256"],
        "m1_source_family": family,
        "m1_source_count": len(m1_rows),
        "m1_row_count": sum(int(row["row_count"]) for row in m1_rows),
        "static_bar_rows_reused_by_reference": len(bars) - len(m1_rows),
        "tick_source_count": len(tick_rows),
        "tick_row_count": sum(int(row["row_count"]) for row in tick_rows),
        "tick_gap_count": int(manifest["tick_gap_count"]),
        "bar_symbol_count": int(manifest["bar_symbol_count"]),
        "pre_march_window_entries_unchanged": unchanged,
        "pre_march_source_manifest_root_sha256": {
            window_id: pre_march[window_id]["source_manifest_root_sha256"]
            for window_id in PRE_MARCH_WINDOW_IDS
        },
        "clock_conversion": "src.utils.broker_clock.broker_epoch_to_utc",
        "broker_clock_rule": NEW_YORK_PLUS_7.name,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "march_outcome_summary_statistics_computed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "wall_seconds": round(time.perf_counter() - started, 3),
    }
    receipt = {**receipt_core, "receipt_root_sha256": _stable_sha256(receipt_core)}
    _write_json(lane_root / "receipts" / "SOURCES_march_2026.json", receipt)
    return receipt


def _tick_capture_span(tick_root: Path) -> tuple[datetime, datetime] | None:
    """The captured tick archive's own declared coverage. Metadata only.

    Reads the export manifest's per-file `first`/`last` stamps -- the same
    fields the exporter wrote -- and never a tick row. A window that does not
    intersect this span needs no corpus pass at all, which is worth roughly
    11.6 GB of reads and a CPU-hour per window on this machine, and lets the
    manifest record WHY the gap exists instead of guessing.
    """

    manifest = _load_tick_manifest(tick_root)
    firsts: list[datetime] = []
    lasts: list[datetime] = []
    for row in manifest.values():
        for key, sink in (("first", firsts), ("last", lasts)):
            raw = row.get(key)
            if not raw:
                continue
            try:
                sink.append(
                    datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                )
            except ValueError:
                continue
    if not firsts or not lasts:
        return None
    return min(firsts), max(lasts)


def materialize_lane_window_sources(
    *,
    registry_path: Path,
    window_id: str,
    m1_parent: Path = DEFAULT_M1_PARENT,
    tick_root: Path = DEFAULT_TICK_ROOT,
) -> dict[str, Any]:
    """Add one `LANE_EXTENSION_WINDOW_IDS` window to an EXISTING lane root.

    The generalisation of `materialize_march_sources`, with the one-shot removed
    because there is nothing here to unlock: these windows are ordinary VAL-band
    calendar, outside every blackout. Everything else is deliberately identical,
    including the invariant that matters most -- every window already in the
    registry must come out of this call byte-for-byte unchanged, asserted rather
    than hoped for.

    Outcome-blindness, stated as a property and not an intention: this function
    reads bar CSVs and tick JSONL, rewrites one timestamp column through
    `broker_epoch_to_utc`, and writes counts and digests. It constructs no
    candidate, walks no trade, and computes no economic quantity of any kind.
    """

    if window_id not in LANE_EXTENSION_WINDOW_IDS:
        raise LaneRematerializationError(
            f"lane_extension_window_not_authorized:{window_id}"
        )
    started = time.perf_counter()
    registry_path = registry_path.resolve()
    lane_root = registry_path.parent
    window = WINDOWS[window_id]

    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("registry_root_sha256") != _manifest_root(
        payload, "registry_root_sha256"
    ):
        raise LaneRematerializationError("lane_input_registry_invalid")
    prior = {
        existing_id: dict(entry)
        for existing_id, entry in (payload.get("windows") or {}).items()
    }
    # A cheap early refusal so a doomed call does not first spend an hour
    # converting bars. The AUTHORITATIVE check is re-taken inside the write
    # lock below, because this one is a TOCTOU read: between here and the write
    # a sibling process can register anything.
    if window_id in prior:
        raise LaneRematerializationError(f"lane_window_already_registered:{window_id}")
    unknown = sorted(set(prior) - set(WINDOWS))
    if unknown:
        raise LaneRematerializationError(f"lane_registry_window_unknown:{unknown}")
    if "january_2026" not in prior:
        raise LaneRematerializationError("lane_reference_window_missing:january_2026")

    reference_manifest = json.loads(
        _safe_relative(
            lane_root, str(prior["january_2026"]["source_manifest"])
        ).read_text(encoding="utf-8")
    )
    logical_repo_root = _logical_repo_root_for_registry(
        registry_path=registry_path, manifest=reference_manifest
    )

    catalog = json.loads((lane_root / CATALOG_NAME).read_text(encoding="utf-8"))
    static_rows = {
        (str(row["symbol"]), str(row["timeframe"])): dict(row)
        for row in catalog.get("bar_sources") or ()
        if str(row["timeframe"]) in ("D1", "H4", "M15")
    }
    missing_static = [
        (symbol, timeframe)
        for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
        for timeframe in ("D1", "H4", "M15")
        if (symbol, timeframe) not in static_rows
    ]
    if missing_static:
        raise LaneRematerializationError(f"lane_static_bar_rows_missing:{missing_static}")

    # Coverage, from the catalog's own metadata rather than from a row scan: the
    # static M15 authority must actually span this window or the window is a
    # NOT_EVALUABLE fiction. D1/H4 reach back to 2014 and are checked the same way.
    coverage: dict[str, Any] = {}
    for timeframe in ("D1", "H4", "M15"):
        firsts = [
            str(static_rows[(symbol, timeframe)]["first_utc"])
            for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
        ]
        lasts = [
            str(static_rows[(symbol, timeframe)]["last_utc"])
            for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
        ]
        coverage[timeframe] = {
            "max_first_utc": max(firsts),
            "min_last_utc": min(lasts),
            "symbol_count": len(firsts),
        }
        if datetime.fromisoformat(max(firsts)) > window.start_utc:
            raise LaneRematerializationError(
                f"lane_static_coverage_starts_after_window:{timeframe}:{max(firsts)}"
            )
        if datetime.fromisoformat(min(lasts)) < window.end_exclusive_utc - timedelta(
            days=1
        ):
            raise LaneRematerializationError(
                f"lane_static_coverage_ends_before_window:{timeframe}:{min(lasts)}"
            )

    family = f"bridge_ftmo_m1_{window.month}"
    source_root = m1_parent / family
    m1_rows: list[dict[str, Any]] = []
    for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
        source, mapped = _find_bar_source(source_root, symbol, "M1")
        destination = lane_root / "sources/bars" / family / f"{mapped}_M1.csv"
        if destination.exists() or destination.is_symlink():
            raise LaneRematerializationError(f"lane_extension_bar_exists:{destination}")
        m1_rows.append(
            _transform_bar_file(
                source=source,
                destination=destination,
                symbol=symbol,
                mapped_symbol=mapped,
                timeframe="M1",
                source_family=family,
                lane_root=lane_root,
                repo_root=logical_repo_root,
            )
        )

    capture_span = _tick_capture_span(tick_root)
    tick_rows: list[dict[str, Any]] = []
    tick_gap_status: str | None = None
    if capture_span is None:
        tick_gap_status = "captured_tick_archive_coverage_undeclared"
    elif window.end_exclusive_utc <= capture_span[0]:
        tick_gap_status = "captured_tick_archive_begins_after_window"
    elif window.start_utc >= capture_span[1]:
        tick_gap_status = "captured_tick_archive_ends_before_window"
    else:
        tick_manifest = _load_tick_manifest(tick_root)
        for symbol in TICK_SYMBOLS:
            source = _tick_source_path(tick_root, symbol)
            destination = (
                lane_root / "sources/ticks" / window.month / symbol
                / "microstructure_ticks.jsonl"
            )
            if destination.exists() or destination.is_symlink():
                raise LaneRematerializationError(
                    f"lane_extension_tick_exists:{destination}"
                )
            transformed = _transform_tick_file(
                source=source,
                symbol=symbol,
                lane_root=lane_root,
                destination_by_window={window_id: destination},
                source_metadata=tick_manifest.get(symbol) or {},
                repo_root=logical_repo_root,
            )
            row = transformed.get(window_id)
            if row is not None:
                tick_rows.append(row)

    bars = [
        *(
            static_rows[(symbol, timeframe)]
            for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
            for timeframe in ("D1", "H4", "M15")
        ),
        *m1_rows,
    ]
    manifest = _source_manifest(
        lane_root=lane_root,
        window=window,
        bars=bars,
        ticks=tick_rows,
        repo_root=logical_repo_root,
        tick_gap_status=tick_gap_status,
    )
    manifest_rel = Path("manifests") / f"{window.window_id}.json"
    manifest_path = lane_root / manifest_rel
    if manifest_path.exists() or manifest_path.is_symlink():
        raise LaneRematerializationError(f"lane_extension_manifest_exists:{manifest_path}")
    _write_json(manifest_path, manifest)

    with _registry_write_lock(registry_path):
        current = json.loads(registry_path.read_text(encoding="utf-8"))
        if current.get("registry_root_sha256") != _manifest_root(
            current, "registry_root_sha256"
        ):
            raise LaneRematerializationError("lane_input_registry_invalid")
        core = dict(current)
        core.pop("registry_root_sha256", None)
        # `before` is taken INSIDE the lock, and it -- not the pre-work `prior`
        # snapshot -- is what the invariance assertion below compares against.
        #
        # The earlier version compared against `prior`, which made the function
        # unsafe to run concurrently with any sibling: a second extension, or
        # merely another window's `bind-source-plan` landing a digest, would
        # move the registry between the snapshot and the write and this call
        # would then raise AFTER having already written its own entry. Comparing
        # against `before` states the property that is actually this function's
        # to guarantee -- *this call* mutated exactly one entry, its own -- and
        # leaves "nothing else moved the five pre-existing windows" to the
        # separate rule-2 fence, which is where that guarantee belongs.
        before = {key: dict(value) for key, value in core["windows"].items()}
        if window.window_id in before:
            raise LaneRematerializationError(
                f"lane_window_already_registered:{window.window_id}"
            )
        raced = sorted(set(before) - set(WINDOWS))
        if raced:
            raise LaneRematerializationError(f"lane_registry_window_unknown:{raced}")
        windows = {key: dict(value) for key, value in before.items()}
        windows[window.window_id] = {
            "window": [window.start, window.end],
            "split": window.split,
            "surface": "VAL",
            "source_manifest": manifest_rel.as_posix(),
            "source_manifest_root_sha256": manifest["manifest_root_sha256"],
            "pack_root": (Path("packs") / window.window_id).as_posix(),
            "pack_roots": {},
            "pack_status": "NOT_BUILT",
            "campaign_sealed": False,
        }
        core["windows"] = windows
        core["status"] = "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY"
        updated = {**core, "registry_root_sha256": _stable_sha256(core)}
        _write_json(registry_path, updated)

    unchanged = {
        existing_id: (updated["windows"][existing_id] == before[existing_id])
        for existing_id in before
    }
    if not all(unchanged.values()):
        raise LaneRematerializationError(
            "lane_pre_existing_windows_mutated:"
            f"{sorted(k for k, v in unchanged.items() if not v)}"
        )

    receipt_core = {
        "schema": MATERIALIZATION_SCHEMA,
        "status": "LANE_TRUE_UTC_WINDOW_SOURCE_EXTENSION_COMPLETE",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "window_id": window.window_id,
        "window": [window.start, window.end],
        "surface": "VAL",
        "day_count": len(window.days),
        "lane_root_repo_relpath": _repo_relative(
            lane_root, repo_root=logical_repo_root
        ),
        "logical_source_repo_root": str(logical_repo_root),
        "registry_root_sha256": updated["registry_root_sha256"],
        "source_manifest_root_sha256": manifest["manifest_root_sha256"],
        "m1_source_family": family,
        "m1_source_count": len(m1_rows),
        "m1_row_count": sum(int(row["row_count"]) for row in m1_rows),
        "static_bar_rows_reused_by_reference": len(bars) - len(m1_rows),
        "static_bar_coverage": coverage,
        "tick_source_count": len(tick_rows),
        "tick_row_count": sum(int(row["row_count"]) for row in tick_rows),
        "tick_gap_count": int(manifest["tick_gap_count"]),
        "tick_gap_status": tick_gap_status,
        "captured_tick_archive_span": (
            [capture_span[0].isoformat(), capture_span[1].isoformat()]
            if capture_span is not None
            else None
        ),
        "bar_symbol_count": int(manifest["bar_symbol_count"]),
        "pre_existing_window_entries_unchanged": unchanged,
        "pre_existing_source_manifest_root_sha256": {
            existing_id: before[existing_id]["source_manifest_root_sha256"]
            for existing_id in before
        },
        "pre_existing_canonical_source_plan_digest_sha256": {
            existing_id: before[existing_id].get(
                "canonical_source_plan_digest_sha256"
            )
            for existing_id in before
        },
        "clock_conversion": "src.utils.broker_clock.broker_epoch_to_utc",
        "broker_clock_rule": NEW_YORK_PLUS_7.name,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "outcome_summary_statistics_computed": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "wall_seconds": round(time.perf_counter() - started, 3),
    }
    receipt = {**receipt_core, "receipt_root_sha256": _stable_sha256(receipt_core)}
    _write_json(lane_root / "receipts" / f"SOURCES_{window.window_id}.json", receipt)
    return receipt


def unregister_lane_window_sources(
    *, registry_path: Path, window_id: str
) -> dict[str, Any]:
    """Remove an extension window that failed before its packs were built.

    "Never register a partial window" needs a way to UN-register one, or the
    rule degrades into hand-run `rm` against a hashed registry. A window whose
    source-plan binding failed is exactly that case: its sources and registry
    entry exist, its digest does not, and leaving it in place would offer a
    downstream reader a window that cannot be resolved.

    Refuses on the two things worth refusing on: any window outside
    `LANE_EXTENSION_WINDOW_IDS` (the five CJ/March windows are not removable by
    any code path), and any window whose packs are built -- a built window is
    evidence, and deleting evidence is not a repair.

    Deliberately does NOT go through `LaneInputRegistry.resolve`: the usual
    reason to call this is that the window's declared span is about to change,
    and `resolve` refuses a span mismatch, so routing the cleanup through it
    would make the tool unusable in precisely the case it exists for.
    """

    if window_id not in LANE_EXTENSION_WINDOW_IDS:
        raise LaneRematerializationError(
            f"lane_extension_window_not_authorized:{window_id}"
        )
    registry_path = registry_path.resolve()
    lane_root = registry_path.parent
    window = WINDOWS[window_id]
    removed: list[str] = []

    with _registry_write_lock(registry_path):
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        if payload.get("registry_root_sha256") != _manifest_root(
            payload, "registry_root_sha256"
        ):
            raise LaneRematerializationError("lane_input_registry_invalid")
        core = dict(payload)
        core.pop("registry_root_sha256", None)
        before = {key: dict(value) for key, value in core["windows"].items()}
        entry = before.get(window_id)
        if entry is None:
            raise LaneRematerializationError(f"lane_window_not_registered:{window_id}")
        if entry.get("pack_status") == "BUILT_AND_VALIDATED":
            raise LaneRematerializationError(
                f"lane_refuse_unregister_built_window:{window_id}"
            )
        prior_entry = dict(entry)
        windows = {k: dict(v) for k, v in before.items() if k != window_id}
        core["windows"] = windows
        core["status"] = "LANE_TRUE_UTC_INPUT_REGISTRY_SOURCE_READY"
        updated = {**core, "registry_root_sha256": _stable_sha256(core)}
        _write_json(registry_path, updated)

    unchanged = {
        other: (updated["windows"][other] == before[other])
        for other in before
        if other != window_id
    }
    if not all(unchanged.values()):
        raise LaneRematerializationError(
            "lane_other_windows_mutated_under_unregister:"
            f"{sorted(k for k, v in unchanged.items() if not v)}"
        )

    manifest_path = lane_root / "manifests" / f"{window_id}.json"
    if manifest_path.is_file():
        manifest_path.unlink()
        removed.append(manifest_path.name)
    for relative in (
        Path("sources/bars") / f"bridge_ftmo_m1_{window.month}",
        Path("sources/ticks") / window.month,
    ):
        target = lane_root / relative
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
            removed.append(relative.as_posix())
    for name in (f"SOURCES_{window_id}.json", f"SOURCE_PLAN_{window_id}.json"):
        receipt = lane_root / "receipts" / name
        if receipt.is_file():
            receipt.unlink()
            removed.append(f"receipts/{name}")
    pack_root = lane_root / "packs" / window_id
    if pack_root.is_dir() and not pack_root.is_symlink():
        shutil.rmtree(pack_root)
        removed.append(f"packs/{window_id}")

    core_receipt = {
        "schema": MATERIALIZATION_SCHEMA,
        "status": "LANE_TRUE_UTC_WINDOW_UNREGISTERED",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "window_id": window_id,
        "unregistered_entry": prior_entry,
        "removed_paths": sorted(removed),
        "registry_root_sha256": updated["registry_root_sha256"],
        "other_window_entries_unchanged": unchanged,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core_receipt, "receipt_root_sha256": _stable_sha256(core_receipt)}


class LaneReplaySourceAccelerator:
    """Bundle adapter whose logical source identities never contain absolute paths."""

    def __init__(
        self,
        *,
        repo_root: Path,
        manifest_path: Path,
        source_plan_digest_sha256: str | None = None,
    ):
        self.repo_root = repo_root.resolve()
        self.manifest_path = manifest_path.resolve()
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if (
            payload.get("schema") != SOURCE_SCHEMA
            or payload.get("campaign_sealed") is not False
            or payload.get("manifest_root_sha256")
            != _manifest_root(payload, "manifest_root_sha256")
        ):
            raise LaneRematerializationError("lane_source_manifest_invalid")
        self.manifest = payload
        self.source_plan_digest_sha256 = (
            str(source_plan_digest_sha256)
            if source_plan_digest_sha256 is not None
            else str(payload["manifest_root_sha256"])
        )
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_plan_digest_sha256):
            raise LaneRematerializationError("lane_source_plan_digest_invalid")
        self.entries = tuple(dict(row) for row in payload.get("bar_sources") or ())
        self.by_path = {str(row["repo_relpath"]): row for row in self.entries}
        if len(self.by_path) != len(self.entries):
            raise LaneRematerializationError("lane_source_path_duplicate")
        self._cache: dict[str, tuple[dict[str, Any], ...]] = {}
        self._lock = threading.Lock()
        self._metrics = {
            "physical_parse_count": 0,
            "physical_normalized_row_count": 0,
            "physical_source_bytes_read": 0,
        }
        self._prewarm: dict[str, Any] = {
            "requested": False,
            "barrier_complete": False,
            "worker_count": 0,
        }

    def _entry(self, path: Path, *, symbol: str) -> dict[str, Any]:
        entry = self.by_path.get(path.as_posix())
        if entry is None or str(entry.get("symbol")) != symbol:
            raise LaneRematerializationError(f"lane_source_not_bound:{symbol}:{path}")
        return entry

    def _actual(self, entry: Mapping[str, Any]) -> Path:
        raw = str(entry["repo_relpath"])
        path = _safe_relative(self.repo_root, raw)
        if not path.is_file() or path.is_symlink():
            raise LaneRematerializationError(f"lane_source_file_invalid:{raw}")
        return path

    def _load(self, path: Path, *, symbol: str) -> tuple[dict[str, Any], ...]:
        key = path.as_posix()
        with self._lock:
            cached = self._cache.get(key)
        if cached is not None:
            return cached
        entry = self._entry(path, symbol=symbol)
        actual = self._actual(entry)
        if _file_sha256(actual) != entry.get("sha256"):
            raise LaneRematerializationError(f"lane_source_sha256_mismatch:{key}")
        rows = integrated.legacy.load_csv_rows(actual, symbol=symbol)
        if len(rows) != int(entry.get("row_count") or -1):
            raise LaneRematerializationError(f"lane_source_row_count_mismatch:{key}")
        with self._lock:
            existing = self._cache.setdefault(key, rows)
            if existing is rows:
                self._metrics["physical_parse_count"] += 1
                self._metrics["physical_normalized_row_count"] += len(rows)
                self._metrics["physical_source_bytes_read"] += actual.stat().st_size
            return existing

    def accepted_source_candidates(
        self,
        *,
        symbol: str,
        physical_timeframe: str,
        source_family_order: Iterable[str],
    ) -> tuple[integrated.AcceptedSourceCandidate, ...]:
        order = {str(family): index for index, family in enumerate(source_family_order)}
        candidates = [
            row
            for row in self.entries
            if str(row.get("symbol")) == symbol
            and str(row.get("timeframe")).upper() == physical_timeframe.upper()
            and str(row.get("source_family")) in order
        ]
        candidates.sort(
            key=lambda row: (
                order[str(row["source_family"])],
                str(row["mapped_symbol"]),
                str(row["repo_relpath"]),
            )
        )
        return tuple(
            integrated.AcceptedSourceCandidate(
                source_path=Path(str(row["repo_relpath"])),
                symbol=symbol,
                mapped_symbol=str(row["mapped_symbol"]),
                physical_timeframe=physical_timeframe.upper(),
                source_family=str(row["source_family"]),
            )
            for row in candidates
        )

    def load_file(
        self, path: Path, *, symbol: str
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        rows = self._load(path, symbol=symbol)
        return rows, integrated.legacy.rows_by_day(rows), str(self._entry(path, symbol=symbol)["sha256"])

    def load_file_days(
        self, path: Path, *, symbol: str, days: Iterable[str]
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
    ]:
        rows = self._load(path, symbol=symbol)
        selected, grouped = integrated.select_days(rows, days=days)
        return selected, grouped, str(self._entry(path, symbol=symbol)["sha256"])

    def load_file_replay_lookback_window(
        self,
        path: Path,
        *,
        symbol: str,
        timeframe: str,
        days: Iterable[str],
        min_total_rows: int,
    ) -> tuple[
        tuple[dict[str, Any], ...],
        dict[str, tuple[dict[str, Any], ...]],
        str,
        dict[str, Any],
    ]:
        rows = self._load(path, symbol=symbol)
        selected, grouped, metadata = integrated.select_replay_lookback_window(
            rows,
            timeframe=timeframe,
            days=days,
            min_total_rows=min_total_rows,
        )
        metadata["bounded_replay_source_path"] = path.as_posix()
        valid = [integrated.legacy.parse_row_time(row) for row in selected]
        valid = [value for value in valid if value is not None]
        bounds = (
            (integrated.legacy.iso(min(valid)), integrated.legacy.iso(max(valid)))
            if valid
            else (None, None)
        )
        digest = integrated.legacy.stable_sha256(
            {**metadata, "first_last": bounds, "rows": selected}
        )
        return selected, grouped, digest, metadata

    def prewarm_all(self, *, workers: int) -> dict[str, Any]:
        count = int(workers)
        if count < 1 or count > 2:
            raise LaneRematerializationError("lane_prewarm_workers_out_of_bounds:1..2")
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=count) as executor:
            lengths = list(
                executor.map(
                    lambda row: len(
                        self._load(
                            Path(str(row["repo_relpath"])),
                            symbol=str(row["symbol"]),
                        )
                    ),
                    self.entries,
                )
            )
        self._prewarm = {
            "requested": True,
            "worker_count": count,
            "partition_count": len(lengths),
            "partition_set_root_sha256": _stable_sha256(lengths),
            "barrier_complete": len(lengths) == len(self.entries),
            "seconds": round(time.perf_counter() - started, 3),
        }
        return dict(self._prewarm)

    def authority(self) -> dict[str, Any]:
        root = str(self.manifest["manifest_root_sha256"])
        return {
            "schema": "gtos.lane.rematerialization.source_acceleration_authority.v1",
            "evidence_class": LANE_EVIDENCE,
            "campaign_sealed": False,
            "source_bundle_root_sha256": root,
            "selection_root_sha256": root,
            "source_plan_digest_sha256": self.source_plan_digest_sha256,
            "config_projection_root_sha256": _stable_sha256(
                {"clock_rule": NEW_YORK_PLUS_7.name, "time_basis": "true_utc"}
            ),
            "normalizer_code_root_sha256": _stable_sha256(
                {"normalizer": "v4_timewarp.normalize_row", "clock_preconverted": True}
            ),
            "partition_count": len(self.entries),
            "symbol_count": len({str(row["symbol"]) for row in self.entries}),
            "policy_execution_entered": False,
            "candidate_cache_enabled": False,
            "policy_state_cache_enabled": False,
            "cross_symbol_prewarm_barrier": dict(self._prewarm),
            "typed_cache_metrics": dict(self._metrics),
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
        }


def _tick_authority(
    *,
    repo_root: Path,
    manifest: Mapping[str, Any],
    manifest_path: Path,
) -> tuple[dict[str, tuple[timewarp.SourceSpec, ...]], dict[str, Any]]:
    specs: dict[str, tuple[timewarp.SourceSpec, ...]] = {}
    contract_sources: list[dict[str, Any]] = []
    logical_manifest_path = _repo_relative(manifest_path, repo_root=repo_root)
    for row in manifest.get("tick_sources") or ():
        raw = dict(row)
        logical = Path(str(raw["repo_relpath"]))
        actual = _safe_relative(repo_root, logical.as_posix())
        if not actual.is_file() or actual.is_symlink() or _file_sha256(actual) != raw.get("sha256"):
            raise LaneRematerializationError(
                f"lane_tick_source_invalid:{logical.as_posix()}"
            )
        spec = timewarp.SourceSpec(
            symbol=str(raw["symbol"]),
            mapped_symbol=str(raw["mapped_symbol"]),
            timeframe="TICK",
            path=logical,
            source_family=str(raw["source_family"]),
            source_broker="FTMO",
            source_role="owner_authorized_research_hydration",
            start_utc=str(raw["first_utc"]),
            end_utc=str(raw["last_utc"]),
            row_count=int(raw["row_count"]),
            sha256=str(raw["sha256"]),
            export_tool="src.research_infra.lane_rematerialization",
            manifest_path=logical_manifest_path,
            source_server_redacted=raw.get("source_server_redacted"),
            source_server_hash=raw.get("source_server_hash"),
            source_account_redacted=raw.get("source_account_redacted"),
            source_account_hash=raw.get("source_account_hash"),
            source_truth_scope=attempt5.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=True,
        )
        specs[str(raw["symbol"])] = (spec,)
        contract_sources.append(
            {
                "symbol": raw["symbol"],
                "source_path": logical.as_posix(),
                "declared_row_count": raw["row_count"],
                "declared_sha256": raw["sha256"],
                "start_utc": raw["first_utc"],
                "end_utc": raw["last_utc"],
            }
        )
    core = {
        "schema": "gtos.lane.rematerialization.bound_tick_source_authority.v1",
        "status": "repo_relative_true_utc_tick_sources_bound",
        "campaign_sealed": False,
        "manifest_root_sha256": manifest["manifest_root_sha256"],
        # Runtime context only. Persisted source identities remain relative;
        # the absolute machine-local root says which worktree owns those bytes.
        "logical_repo_root": str(repo_root.resolve()),
        "source_count": len(contract_sources),
        "symbols": sorted(specs),
        "sources": sorted(contract_sources, key=lambda row: str(row["symbol"])),
        "broad_retired_repo_scan_enabled": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return specs, {**core, "contract_root_sha256": _stable_sha256(core)}


def _tick_gaps(manifest: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    return {
        str(row["symbol"]): (str(row["status"]),)
        for row in manifest.get("tick_gaps") or ()
    }


def _broker_day_counts(
    rows: Iterable[Mapping[str, Any]],
) -> Counter[str]:
    """Count already-repaired rows by the measured FTMO broker day."""

    counts: Counter[str] = Counter()
    for row in rows:
        stamp = timewarp.parse_row_time(row)
        if stamp is None:
            continue
        counts[
            utc_to_broker_naive(stamp, NEW_YORK_PLUS_7).date().isoformat()
        ] += 1
    return counts


def _broker_day_utc_dates(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, set[str]]:
    """Return the true-UTC dates contributing rows to each broker day."""

    dates: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        stamp = timewarp.parse_row_time(row)
        if stamp is None:
            continue
        broker_day = utc_to_broker_naive(stamp, NEW_YORK_PLUS_7).date().isoformat()
        dates[broker_day].add(stamp.date().isoformat())
    return dates


def _rebind_complete_broker_day_fragments(
    source: timewarp.ResolvedSource,
    *,
    m15_source: timewarp.ResolvedSource,
) -> tuple[timewarp.ResolvedSource, tuple[dict[str, Any], ...]]:
    """Repair a false UTC-day floor failure using the enclosing broker day.

    The historical M1 completeness gate grouped rows by the timestamp's stated
    UTC date.  Once broker-wall labels are repaired, the opening hours of a
    broker day can sit on the preceding UTC date.  Any such UTC fragment --
    including a Sunday-open fragment inside a month -- can therefore miss the
    per-UTC-day 80% floor even when its complete broker day is present across
    the adjacent UTC day.  This rebind changes authority, never rows: it is
    allowed only when the fragment maps to exactly one broker day, both M1 and
    M15 prove that broker day spans at least two UTC dates, and the complete
    broker day independently passes the unchanged M1/M15 floor.
    """

    populated_days = tuple(
        sorted(day for day, rows in source.rows_by_day.items() if rows)
    )
    if not populated_days:
        return source, ()
    m1_broker_counts = _broker_day_counts(source.rows)
    m15_broker_counts = _broker_day_counts(m15_source.rows)
    m1_broker_utc_dates = _broker_day_utc_dates(source.rows)
    m15_broker_utc_dates = _broker_day_utc_dates(m15_source.rows)
    authorities = {
        str(day): dict(authority)
        for day, authority in source.day_source_authority.items()
    }
    rebinds: list[dict[str, Any]] = []
    for day, authority in sorted(authorities.items()):
        if (
            day not in populated_days
            or authority.get("diagnostic_fallback_only") is not True
        ):
            continue
        fragment_broker_days = {
            utc_to_broker_naive(stamp, NEW_YORK_PLUS_7).date().isoformat()
            for row in (
                *tuple(source.rows_by_day.get(day, ())),
                *tuple(m15_source.rows_by_day.get(day, ())),
            )
            if (stamp := timewarp.parse_row_time(row)) is not None
        }
        if len(fragment_broker_days) != 1:
            continue
        broker_day = next(iter(fragment_broker_days))
        if (
            len(m1_broker_utc_dates.get(broker_day, ())) < 2
            or len(m15_broker_utc_dates.get(broker_day, ())) < 2
        ):
            continue
        broker_day_authority = timewarp.m1_symbol_day_source_authority(
            symbol=source.spec.symbol,
            trading_day=broker_day,
            m1_row_count=m1_broker_counts[broker_day],
            m15_row_count=m15_broker_counts[broker_day],
            source_day_sha256=_stable_sha256(
                {
                    "clock_rule": NEW_YORK_PLUS_7.name,
                    "broker_day": broker_day,
                    "m1_row_count": m1_broker_counts[broker_day],
                    "m15_row_count": m15_broker_counts[broker_day],
                    "base_source_sha256": source.sha256,
                }
            ),
            source_path=str(source.spec.path),
            source_family=source.spec.source_family,
            source_file_sha256=source.sha256,
        )
        if broker_day_authority.get("diagnostic_fallback_only") is not False:
            continue
        original_hash = authority.get("source_day_authority_hash_sha256")
        rebound = timewarp.source_day_authority_with_updates(
            authority,
            status="lane_true_utc_fragment_bound_by_complete_broker_day",
            source_session_status="true_utc_fragment_of_complete_broker_day",
            diagnostic_fallback_only=False,
            source_gaps=[],
            path_replay_allowed=True,
            terminal_lifecycle_close_allowed=True,
            lane_authority_rebind=True,
            lane_authority_rebind_reason=(
                "corrected_true_utc_day_boundary_splits_complete_broker_day"
            ),
            lane_broker_clock_rule=NEW_YORK_PLUS_7.name,
            lane_enclosing_broker_day=broker_day,
            lane_enclosing_broker_day_m1_row_count=m1_broker_counts[
                broker_day
            ],
            lane_enclosing_broker_day_m15_row_count=m15_broker_counts[
                broker_day
            ],
            lane_enclosing_broker_day_authority_id=broker_day_authority[
                "source_day_authority_id"
            ],
            lane_enclosing_broker_day_authority_hash_sha256=(
                broker_day_authority["source_day_authority_hash_sha256"]
            ),
            lane_original_utc_fragment_authority_hash_sha256=original_hash,
        )
        authorities[day] = rebound
        rebinds.append(
            {
                "symbol": source.spec.symbol,
                "utc_fragment_day": day,
                "utc_fragment_m1_row_count": authority.get("m1_row_count"),
                "utc_fragment_m15_row_count": authority.get("m15_row_count"),
                "utc_fragment_effective_min_rows": authority.get(
                    "effective_min_rows"
                ),
                "original_utc_fragment_authority_hash_sha256": original_hash,
                "enclosing_broker_day": broker_day,
                "enclosing_broker_day_m1_row_count": m1_broker_counts[
                    broker_day
                ],
                "enclosing_broker_day_m15_row_count": m15_broker_counts[
                    broker_day
                ],
                "enclosing_broker_day_authority_id": broker_day_authority[
                    "source_day_authority_id"
                ],
                "rebound_source_day_authority_id": rebound[
                    "source_day_authority_id"
                ],
                "rows_added_or_synthesized": 0,
            }
        )
    if not rebinds:
        return source, ()
    labels = tuple(
        {
            **dict(label),
            **(
                {
                    key: authorities[str(label["trading_day"])].get(key)
                    for key in (
                        "status",
                        "source_session_status",
                        "diagnostic_fallback_only",
                        "source_gaps",
                        "path_replay_allowed",
                        "terminal_lifecycle_close_allowed",
                        "source_day_authority_id",
                        "source_day_authority_hash_sha256",
                    )
                }
                if str(label.get("trading_day")) in {
                    row["utc_fragment_day"] for row in rebinds
                }
                else {}
            ),
        }
        for label in source.component_source_labels
    )
    unresolved = any(
        row.get("diagnostic_fallback_only") is True
        for row in authorities.values()
    )
    return (
        replace(
            source,
            selected_status=(
                source.selected_status
                if unresolved
                else "selected_composite_m1_days_for_broad_live_as_if_replay"
            ),
            component_source_labels=labels,
            day_source_authority=authorities,
        ),
        tuple(rebinds),
    )


class LaneBroadSourceResolver(attempt5.BroadSourceResolver):
    """Unsealed resolver with a true-UTC/broker-day completeness rebind."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # A LANE manifest is an exhaustive authority declaration, including
        # when its tick set is empty.  The upstream default interprets an empty
        # bound mapping as permission to scan retired repo tick estates.  That
        # would silently add undeclared path data and make runtime disagree with
        # the read-only canonical-plan inspector.
        if kwargs.get("bound_tick_source_specs") is not None:
            kwargs["sealed_tick_full_component_set"] = True
        super().__init__(*args, **kwargs)

    def build_sources_for_days(
        self,
        days: tuple[str, ...],
        *,
        symbols: tuple[str, ...] | None = None,
        source_authority_days: tuple[str, ...] | None = None,
    ) -> dict[str, dict[str, timewarp.ResolvedSource]]:
        execution_days = tuple(sorted(set(days)))
        authority_days = tuple(
            sorted(set(source_authority_days or execution_days))
        )
        # The historical chunk resolver projects M1 to the execution UTC day.
        # A corrected window-edge fragment needs its adjacent UTC day to prove
        # the enclosing broker day, and the engine subsequently checks that the
        # chunk authority hash equals the full-window canonical hash.  Resolve
        # the complete authority scope here; static_source_authority_plan still
        # projects its comparison back to `execution_days`, while path queries
        # remain bounded by their explicit as-of/until timestamps.
        resolved_days = (
            authority_days if execution_days != authority_days else execution_days
        )
        return super().build_sources_for_days(
            resolved_days,
            symbols=symbols,
            source_authority_days=authority_days,
        )

    def resolve_m1_for_days(
        self,
        *,
        symbol: str,
        days: tuple[str, ...],
        m15_source: timewarp.ResolvedSource,
    ) -> timewarp.ResolvedSource | None:
        source = super().resolve_m1_for_days(
            symbol=symbol,
            days=days,
            m15_source=m15_source,
        )
        if source is None:
            return None
        rebound, rebinds = _rebind_complete_broker_day_fragments(
            source,
            m15_source=m15_source,
        )
        if not rebinds:
            return rebound
        by_day = {str(row["utc_fragment_day"]): row for row in rebinds}
        for index, row in enumerate(self.source_rows):
            if (
                row.get("row_type") == "m1_symbol_day_source"
                and row.get("symbol") == symbol
                and str(row.get("trading_day")) in by_day
            ):
                authority = rebound.day_source_authority[
                    str(row["trading_day"])
                ]
                self.source_rows[index] = {
                    **dict(row),
                    **{
                        key: authority.get(key)
                        for key in (
                            "status",
                            "source_session_status",
                            "diagnostic_fallback_only",
                            "source_gaps",
                            "path_replay_allowed",
                            "terminal_lifecycle_close_allowed",
                            "source_day_authority_id",
                            "source_day_authority_hash_sha256",
                        )
                    },
                    "lane_authority_rebind": True,
                }
        for row in rebinds:
            self.emit_source_row(
                {
                    "row_type": "lane_m1_utc_fragment_authority_rebind",
                    **row,
                    "clock_rule": NEW_YORK_PLUS_7.name,
                    "campaign_sealed": False,
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                    "evidence_class": LANE_EVIDENCE,
                }
            )
        return rebound


def _prefix_pack_binding_rebind_allowed(
    *,
    differences: Mapping[str, Any],
    proof: Any,
    reader: replay_prepared_day_pack.PreparedDayPackReader,
    days: Sequence[str],
    runtime_source_root: str,
    expected_pack_root: str | None,
    expected_window_id: str,
    expected_effective_window: Sequence[str],
    expected_source_manifest_root: str,
    expected_source_plan_digest: str | None,
    expected_pack_count: int,
) -> bool:
    """Accept only the one measured binding delta for an authenticated pack."""

    if not isinstance(proof, Mapping) or len(days) != 1:
        return False
    proof_core = dict(proof)
    proof_root = proof_core.pop("authority_root_sha256", None)
    registered_root = proof.get("registered_source_identity_root_sha256")
    effective_root = proof.get("effective_source_identity_root_sha256")
    expected_difference = {
        "source_identity_root_sha256": {
            "pack": registered_root,
            "runtime": effective_root,
        }
    }
    registered_window = list(proof.get("registered_window") or ())
    effective_window = list(proof.get("effective_window") or ())
    day = str(days[0])
    return bool(
        proof.get("schema")
        == "gtos.lane.rematerialization.prefix_pack_source_rebind.v1"
        and proof.get("status") == "VERIFIED_PREFIX_PACK_SOURCE_IDENTITY_REBIND"
        and isinstance(proof_root, str)
        and proof_root == _stable_sha256(proof_core)
        and proof.get("window_id") == expected_window_id
        and effective_window == list(expected_effective_window)
        and len(effective_window) == 2
        and len(registered_window) == 2
        and registered_window[0] == effective_window[0]
        and effective_window[1] < registered_window[1]
        and proof.get("source_manifest_root_sha256")
        == expected_source_manifest_root
        and proof.get("effective_source_plan_digest_sha256")
        == expected_source_plan_digest
        and proof.get("retained_pack_count") == expected_pack_count
        and proof.get("allowed_binding_difference")
        == ["source_identity_root_sha256"]
        and proof.get("source_manifest_unchanged") is True
        and proof.get("retained_daily_pack_roots_are_exact_registry_subset") is True
        and proof.get("pack_contents_remain_authenticated_per_reader_before_use")
        is True
        and proof.get("economic_outcomes_read") is False
        and proof.get("march_outcomes_read") is False
        and proof.get("broker_live_authority") is False
        and proof.get("broker_mutation_enabled") is False
        and dict(differences) == expected_difference
        and runtime_source_root == effective_root
        and reader.bindings.get("source_identity_root_sha256") == registered_root
        and reader.bindings.get("days") == [day]
        and len(effective_window) == 2
        and effective_window[0] <= day <= effective_window[1]
        and isinstance(expected_pack_root, str)
        and reader.external_root_authenticated is True
        and reader.pack_root_sha256 == expected_pack_root
    )


@dataclass(frozen=True)
class LaneWindowInputs:
    registry_path: Path
    registry: Mapping[str, Any]
    window_id: str
    window: WindowSpec
    entry: Mapping[str, Any]
    source_manifest_path: Path
    source_manifest: Mapping[str, Any]
    pack_root: Path
    pack_roots: Mapping[tuple[str, str, str], str]
    contract: Path
    logical_repo_root: Path = REPO_ROOT
    runtime_evidence: dict[str, Any] = field(
        default_factory=dict,
        compare=False,
        repr=False,
    )

    @property
    def seal(self) -> dict[str, Any]:
        root = str(self.source_manifest["manifest_root_sha256"])
        return {
            "source_authority_binding": {
                "authority_root_sha256": root,
                "bundle_root_sha256": root,
                "source_plan_digest_sha256": root,
            }
        }

    @property
    def window_start(self) -> str:
        return self.window.start

    @property
    def window_end(self) -> str:
        return self.window.end

    def accelerator(self) -> LaneReplaySourceAccelerator:
        return LaneReplaySourceAccelerator(
            repo_root=self.logical_repo_root,
            manifest_path=self.source_manifest_path,
            source_plan_digest_sha256=self.entry.get(
                "canonical_source_plan_digest_sha256"
            ),
        )

    def with_canonical_source_plan_digest(self, digest: str) -> "LaneWindowInputs":
        """Apply a read-only sidecar digest without mutating the source registry."""

        normalized = str(digest or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise LaneRematerializationError("lane_source_plan_override_invalid")
        existing = self.entry.get("canonical_source_plan_digest_sha256")
        if existing is not None and str(existing) != normalized:
            raise LaneRematerializationError(
                f"lane_source_plan_override_drift:{existing}:{normalized}"
            )
        entry = dict(self.entry)
        entry["canonical_source_plan_digest_sha256"] = normalized
        return replace(self, entry=entry)

    def for_prefix(self, end_day: str) -> "LaneWindowInputs":
        """Return a read-only prefix view of one registered LANE window.

        The registry and manifest stay untouched.  A full-window canonical plan
        cannot authorize a shorter source scope, so an inherited plan digest is
        cleared and must be recomputed for the prefix before an arm can run.
        Only already-authenticated daily pack roots inside the prefix survive.
        """

        try:
            end = date.fromisoformat(str(end_day))
            start = date.fromisoformat(self.window.start)
            registered_end = date.fromisoformat(self.window.end)
        except ValueError as exc:
            raise LaneRematerializationError(
                f"lane_prefix_end_invalid:{end_day}"
            ) from exc
        if end < start or end > registered_end:
            raise LaneRematerializationError(
                f"lane_prefix_out_of_range:{end.isoformat()}:"
                f"{start.isoformat()}..{registered_end.isoformat()}"
            )
        if end == registered_end:
            return self
        normalized = end.isoformat()
        bounded_window = replace(self.window, end=normalized)
        entry = dict(self.entry)
        entry.pop("canonical_source_plan_digest_sha256", None)
        roots = {
            key: value
            for key, value in self.pack_roots.items()
            if key[1] >= self.window.start and key[2] <= normalized
        }
        expected = {
            (self.window.split, day, day) for day in bounded_window.days
        }
        if set(roots) != expected:
            missing = sorted(":".join(key) for key in expected - set(roots))
            raise LaneRematerializationError(
                f"lane_prefix_pack_roots_incomplete:{missing[:5]}"
            )
        return replace(
            self,
            window=bounded_window,
            entry=entry,
            pack_roots=roots,
        )

    def _rebind_authority(self) -> dict[str, Any]:
        root = str(self.source_manifest["manifest_root_sha256"])
        plan = str(self.entry.get("canonical_source_plan_digest_sha256") or root)
        return {
            "schema": "gtos.lane.rematerialization.source_consumer_rebind.v1",
            "campaign_sealed": False,
            "verified_successor_bundle": {"bundle_root_sha256": root},
            "verified_successor_selection": {"selection_root_sha256": root},
            "source_plan_digest_sha256": plan,
            "path_binding": "repo_relative",
        }

    def build_args(
        self,
        *,
        arm_id: str,
        output_dir: Path,
        output_prefix: str,
        stop_after_day: str | None,
    ) -> Any:
        from src.research_infra.fast_engine import sealed_inputs

        # The lane replaces `prepared_day_pack_root` with its own at :2475 below,
        # before the value is read, so January's packs are an argument shell here
        # and not this run's authority. Requiring them on disk made the lane arm
        # die of a parked campaign's 20 GB of bulk evidence it never opens.
        historical = sealed_inputs.resolve_sealed_january(
            REPO_ROOT, require_prepared_day_packs=False
        )
        argument_shell_prefix = _lane_argument_shell_prefix(output_prefix, arm_id)
        args = sealed_inputs.build_january_args(
            repo_root=REPO_ROOT,
            arm_id=arm_id,
            output_dir=output_dir,
            output_prefix=argument_shell_prefix,
            stop_after_day=stop_after_day,
            sealed=historical,
        )
        # Bind the unchanged economic/execution surface while the historical
        # authority is still present, then deliberately replace only source and
        # prepared-pack authority. This is the owner's explicit seal break.
        sealed_inputs.prelude(args)
        # The bound historical builder validates only `_B7_5_` names.  That is
        # an argument-construction shell, not this run's authority.  Replacing
        # it before attempt5 derives any output paths is what makes the runtime
        # preflight say `b7_5_contract_binding.required: false` rather than
        # falsely claiming the re-materialized source matches R2's sealed bytes.
        args.output_prefix = output_prefix
        args.window_id = f"lane_{self.window_id}"
        args.start = self.window.start
        args.end = self.window.end
        args.engineering_stop_after_day = stop_after_day
        root = str(self.source_manifest["manifest_root_sha256"])
        accelerator = self.accelerator()
        authority = accelerator.authority()
        rebind = self._rebind_authority()
        authority["source_bundle_consumer_rebind_authority"] = dict(rebind)
        args.source_acceleration_bundle_dir = self.source_manifest_path.parent
        args.source_acceleration_selection = self.source_manifest_path
        args.expected_source_bundle_root_sha256 = root
        # This is recomputed from the new source rows by `bind-source-plan`; it
        # is neither R2's sealed source-plan digest nor the manifest hash.
        plan_digest = str(
            self.entry.get("canonical_source_plan_digest_sha256") or ""
        )
        if not re.fullmatch(r"[0-9a-f]{64}", plan_digest):
            raise LaneRematerializationError(
                "lane_canonical_source_plan_must_be_bound_before_arm"
            )
        args.expected_source_plan_digest_sha256 = plan_digest
        # The commissioned CJ estate is read-only. Cache only inside this run's
        # new local output namespace; never write beside the foreign registry.
        args.source_acceleration_cache_root = output_dir / "_lane_source_cache"
        args.source_acceleration_authority = authority
        args.bound_source_bundle_consumer_rebind_authority = rebind
        args.expected_shared_execution_contract_sha256 = None
        args.prepared_day_pack_root = self.pack_root
        roots = dict(self.pack_roots)
        if stop_after_day is not None:
            roots = {key: value for key, value in roots.items() if key[1] <= stop_after_day}
        args.expected_prepared_day_pack_roots = roots
        args.tick_source_manifest = self.source_manifest_path
        args.expected_tick_source_manifest_sha256 = _file_sha256(
            self.source_manifest_path
        )
        args.sealed_tick_source_ledger = None
        args.expected_sealed_tick_source_ledger_sha256 = None
        args.sealed_tick_full_component_set = False
        args.tick_diagnostic_manifests = []
        args.expected_tick_diagnostic_manifest_sha256s = []
        # Relative tick identities are read from repo root by the lazy indexed
        # reader. Sparse-cache attestations require absolute identities and are
        # intentionally not used in this relocatable lane.
        args.tick_sparse_cache_root = None
        args.source_prewarm_workers = min(2, int(args.source_prewarm_workers or 1))
        return args

    def fingerprint_args(
        self,
        *,
        arm_id: str,
        stop_after_day: str | None,
    ) -> argparse.Namespace:
        """Describe the executed lane args without re-running the namespace prelude."""

        _lane_argument_shell_prefix("CJ_FINGERPRINT_ONLY", arm_id)
        return argparse.Namespace(
            arm_id=arm_id,
            start=self.window.start,
            end=self.window.end,
            engineering_stop_after_day=stop_after_day,
            decision_contract=self.contract,
            expected_shared_execution_contract_sha256=None,
        )

    def _verified_prefix_pack_source_rebind(self) -> dict[str, Any] | None:
        """Prove a shorter prefix may reuse its registered daily packs.

        Prepared packs bind the source identity of the complete registered
        window.  A prefix changes that root because source identity includes
        window-wide day counts, even though every retained daily pack is
        byte-identical and the underlying authenticated source manifest is
        unchanged.  Reuse is allowed only after recomputing both roots and
        proving the retained pack-root mapping is an exact registry subset.
        """

        registered = tuple(str(value) for value in self.entry.get("window") or ())
        effective = (self.window.start, self.window.end)
        if not registered or registered == effective:
            return None
        if (
            len(registered) != 2
            or registered[0] != effective[0]
            or not effective[0] <= effective[1] < registered[1]
            or self.entry.get("pack_status") != "BUILT_AND_VALIDATED"
        ):
            raise LaneRematerializationError(
                f"lane_prefix_pack_rebind_scope_invalid:{registered}:{effective}"
            )

        full = LaneInputRegistry(self.registry_path).resolve(
            window_id=self.window_id,
            purpose=guard.PURPOSE_LANE_ITERATION,
        )
        if (
            full.window.start != registered[0]
            or full.window.end != registered[1]
            or full.source_manifest.get("manifest_root_sha256")
            != self.source_manifest.get("manifest_root_sha256")
            or full.logical_repo_root != self.logical_repo_root
        ):
            raise LaneRematerializationError(
                "lane_prefix_pack_rebind_registered_authority_mismatch"
            )
        expected_prefix_roots = {
            key: value
            for key, value in full.pack_roots.items()
            if key[1] >= effective[0] and key[2] <= effective[1]
        }
        if dict(self.pack_roots) != expected_prefix_roots:
            raise LaneRematerializationError(
                "lane_prefix_pack_rebind_pack_subset_mismatch"
            )

        symbols = tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
        full_resolver = _resolver_for(full)
        full_sources = full_resolver.build_sources_for_days(
            full.window.days,
            symbols=symbols,
            source_authority_days=full.window.days,
        )
        effective_resolver = _resolver_for(self)
        effective_sources = effective_resolver.build_sources_for_days(
            self.window.days,
            symbols=symbols,
            source_authority_days=self.window.days,
        )
        registered_source_root = replay_prepared_day_pack.source_identity_root(
            full_sources
        )
        effective_source_root = replay_prepared_day_pack.source_identity_root(
            effective_sources
        )

        pack_source_roots: set[str] = set()
        for (split, start, end), expected_root in sorted(self.pack_roots.items()):
            manifest_path = (
                self.pack_root
                / split
                / f"{start}_{end}"
                / replay_prepared_day_pack.MANIFEST_NAME
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            bindings = manifest.get("bindings") or {}
            if (
                manifest.get("pack_root_sha256") != expected_root
                or bindings.get("days") != [start]
                or start != end
            ):
                raise LaneRematerializationError(
                    f"lane_prefix_pack_rebind_manifest_mismatch:{start}"
                )
            pack_source_roots.add(
                str(bindings.get("source_identity_root_sha256") or "")
            )
        if pack_source_roots != {registered_source_root}:
            raise LaneRematerializationError(
                "lane_prefix_pack_rebind_registered_source_root_mismatch"
            )

        excluded = sorted(set(full.pack_roots) - set(self.pack_roots))
        core = {
            "schema": "gtos.lane.rematerialization.prefix_pack_source_rebind.v1",
            "status": "VERIFIED_PREFIX_PACK_SOURCE_IDENTITY_REBIND",
            "window_id": self.window_id,
            "registered_window": list(registered),
            "effective_window": list(effective),
            "registered_source_identity_root_sha256": registered_source_root,
            "effective_source_identity_root_sha256": effective_source_root,
            "source_manifest_root_sha256": self.source_manifest[
                "manifest_root_sha256"
            ],
            "effective_source_plan_digest_sha256": self.entry.get(
                "canonical_source_plan_digest_sha256"
            ),
            "retained_pack_count": len(self.pack_roots),
            "retained_pack_roots_sha256": _stable_sha256(
                sorted((list(key), value) for key, value in self.pack_roots.items())
            ),
            "excluded_registered_packs": [list(key) for key in excluded],
            "allowed_binding_difference": ["source_identity_root_sha256"],
            "source_manifest_unchanged": True,
            "retained_daily_pack_roots_are_exact_registry_subset": True,
            "pack_contents_remain_authenticated_per_reader_before_use": True,
            "economic_outcomes_read": False,
            "march_outcomes_read": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
        }
        return {**core, "authority_root_sha256": _stable_sha256(core)}

    @contextlib.contextmanager
    def runtime_bindings(self) -> Iterator[None]:
        # Tick SourceSpecs deliberately retain repo-relative logical identities.
        # The upstream lazy tick reader and source-plan hasher open those paths
        # relative to the process cwd, so a registry consumed from a successor
        # worktree must enter the registry's owning repo for the duration of the
        # run.  All output paths and source-accelerator physical paths are
        # already absolute.  Restore the caller's cwd even when replay fails.
        original_cwd = Path.cwd()
        real_class = integrated.RealReplaySourceAccelerator
        original_factory = real_class.__dict__["from_accepted_bundle"]
        original_tick_loader = attempt5.bound_tick_source_authority
        original_resolver = attempt5.BroadSourceResolver
        original_split_ranges = attempt5.SPLIT_RANGES
        pack_reader_class = replay_prepared_day_pack.PreparedDayPackReader
        original_pack_assert = pack_reader_class.assert_compatible
        window_inputs = self
        prefix_pack_rebind = self._verified_prefix_pack_source_rebind()
        if prefix_pack_rebind is not None:
            self.runtime_evidence["prefix_pack_source_identity_rebind"] = (
                prefix_pack_rebind
            )
            self.runtime_evidence["prefix_pack_rebind_accepted_days"] = []

        def factory(_cls: Any, **_kwargs: Any) -> LaneReplaySourceAccelerator:
            return window_inputs.accelerator()

        def tick_loader(
            *, manifest_path: Path, expected_manifest_sha256: str
        ) -> tuple[dict[str, tuple[timewarp.SourceSpec, ...]], dict[str, Any]]:
            if Path(manifest_path).resolve() != window_inputs.source_manifest_path:
                raise LaneRematerializationError("lane_tick_manifest_path_mismatch")
            if _file_sha256(window_inputs.source_manifest_path) != expected_manifest_sha256:
                raise LaneRematerializationError("lane_tick_manifest_sha256_mismatch")
            return _tick_authority(
                repo_root=window_inputs.logical_repo_root,
                manifest=window_inputs.source_manifest,
                manifest_path=window_inputs.source_manifest_path,
            )

        def diagnostic_pack_assert(
            reader: replay_prepared_day_pack.PreparedDayPackReader,
            *,
            days: Sequence[str],
            symbols: Sequence[str],
            factor_neutral_config_root_sha256: str,
            source_identity_root_sha256: str,
            max_candidates_per_symbol_window: int | None,
        ) -> None:
            try:
                original_pack_assert(
                    reader,
                    days=days,
                    symbols=symbols,
                    factor_neutral_config_root_sha256=(
                        factor_neutral_config_root_sha256
                    ),
                    source_identity_root_sha256=source_identity_root_sha256,
                    max_candidates_per_symbol_window=(
                        max_candidates_per_symbol_window
                    ),
                )
            except replay_prepared_day_pack.PreparedDayPackError as exc:
                observed = {
                    "days": list(days),
                    "symbols": list(symbols),
                    "factor_neutral_config_root_sha256": (
                        factor_neutral_config_root_sha256
                    ),
                    "source_identity_root_sha256": source_identity_root_sha256,
                    "max_candidates_per_symbol_window": (
                        max_candidates_per_symbol_window
                    ),
                }
                differences = {
                    key: {
                        "pack": reader.bindings.get(key),
                        "runtime": observed.get(key),
                    }
                    for key in sorted(set(reader.bindings) | set(observed))
                    if reader.bindings.get(key) != observed.get(key)
                }
                proof = window_inputs.runtime_evidence.get(
                    "prefix_pack_source_identity_rebind"
                )
                expected_pack_root = window_inputs.pack_roots.get(
                    (
                        window_inputs.window.split,
                        str(days[0]) if days else "",
                        str(days[-1]) if days else "",
                    )
                )
                if _prefix_pack_binding_rebind_allowed(
                    differences=differences,
                    proof=proof,
                    reader=reader,
                    days=days,
                    runtime_source_root=source_identity_root_sha256,
                    expected_pack_root=expected_pack_root,
                    expected_window_id=window_inputs.window_id,
                    expected_effective_window=(
                        window_inputs.window.start,
                        window_inputs.window.end,
                    ),
                    expected_source_manifest_root=str(
                        window_inputs.source_manifest["manifest_root_sha256"]
                    ),
                    expected_source_plan_digest=window_inputs.entry.get(
                        "canonical_source_plan_digest_sha256"
                    ),
                    expected_pack_count=len(window_inputs.pack_roots),
                ):
                    accepted = window_inputs.runtime_evidence[
                        "prefix_pack_rebind_accepted_days"
                    ]
                    for day in days:
                        if str(day) not in accepted:
                            accepted.append(str(day))
                    return
                raise LaneRematerializationError(
                    "lane_prepared_pack_binding_mismatch:"
                    + json.dumps(differences, sort_keys=True, separators=(",", ":"))
                ) from exc

        setattr(real_class, "from_accepted_bundle", classmethod(factory))
        attempt5.bound_tick_source_authority = tick_loader
        attempt5.BroadSourceResolver = LaneBroadSourceResolver
        attempt5.SPLIT_RANGES = (
            (
                window_inputs.window.split,
                window_inputs.window.start,
                window_inputs.window.end,
            ),
        )
        pack_reader_class.assert_compatible = diagnostic_pack_assert
        try:
            os.chdir(self.logical_repo_root)
            yield
        finally:
            os.chdir(original_cwd)
            pack_reader_class.assert_compatible = original_pack_assert
            attempt5.SPLIT_RANGES = original_split_ranges
            attempt5.BroadSourceResolver = original_resolver
            attempt5.bound_tick_source_authority = original_tick_loader
            setattr(real_class, "from_accepted_bundle", original_factory)

    def input_authority(self) -> dict[str, Any]:
        authority = {
            "registry": _repo_relative(
                self.registry_path, repo_root=self.logical_repo_root
            ),
            "registry_absolute_machine_local": str(self.registry_path),
            "registry_access": "read_only",
            "logical_source_repo_root": str(self.logical_repo_root),
            "registry_root_sha256": self.registry["registry_root_sha256"],
            "window_id": self.window_id,
            "window": [self.window.start, self.window.end],
            "surface": "VAL",
            "source_manifest": _repo_relative(
                self.source_manifest_path, repo_root=self.logical_repo_root
            ),
            "source_manifest_root_sha256": self.source_manifest[
                "manifest_root_sha256"
            ],
            "canonical_source_plan_digest_sha256": self.entry.get(
                "canonical_source_plan_digest_sha256"
            ),
            "pack_root": _repo_relative(
                self.pack_root, repo_root=self.logical_repo_root
            ),
            "pack_count": len(self.pack_roots),
            "campaign_sealed": False,
            "clock_rule": NEW_YORK_PLUS_7.name,
            "evidence_class": LANE_EVIDENCE,
            "runtime_verified_rebinds": self.runtime_evidence,
        }
        registered_window = list(self.entry.get("window") or ())
        if registered_window and registered_window != authority["window"]:
            authority["registered_window"] = registered_window
            authority["prefix_bounded"] = True
        return authority

    def load_raw_campaign_sources(
        self,
        *,
        days: Sequence[str],
    ) -> dict[str, dict[str, timewarp.ResolvedSource]]:
        """Load the exact registered 24-symbol source denominator."""

        return _load_raw_campaign_sources(self, days=days)

    def validate_raw_campaign_sources(
        self,
        *,
        days: Sequence[str],
        sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
    ) -> None:
        """Independently reopen and exact-compare one loaded source bundle."""

        _validate_raw_campaign_sources(
            self,
            days=days,
            sources=sources,
        )

    def quote_source_resolver(
        self,
        *,
        days: Sequence[str],
    ) -> "LaneQuoteSourceResolver":
        """Open the A1-bound ordered-tick authority for one raw run scope."""

        return LaneQuoteSourceResolver(self, days=days)

    def run_raw_campaign(
        self,
        *,
        campaign: timewarp.CampaignConfig,
        config: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Call the native campaign with the strict raw-source truth guards."""

        if not wave21_full_flow_truth_mode_enabled(config):
            raise LaneRematerializationError(
                "raw_campaign_truth_mode_required"
            )
        if campaign.run_smoke_subset is not False:
            raise LaneRematerializationError("raw_campaign_smoke_refused")
        candidate_cap = campaign.max_candidates_per_symbol_window
        if isinstance(candidate_cap, bool) or candidate_cap != 0:
            raise LaneRematerializationError("raw_campaign_candidate_cap_refused")
        sources = self.load_raw_campaign_sources(days=campaign.days)
        self.validate_raw_campaign_sources(
            days=campaign.days,
            sources=sources,
        )
        with (
            _RAW_CAMPAIGN_WITNESS_LOCK,
            self.runtime_bindings(),
            _installed_raw_campaign_successor_witness(sources) as used_streams,
        ):
            result = timewarp.run_campaign(
                campaign=campaign,
                config=config,
                sources=sources,
                prepared_day_pack=None,
            )
        expected_streams = len(RAW_CAMPAIGN_SYMBOLS) * len(
            RAW_CAMPAIGN_DECISION_TIMEFRAMES
        )
        if len(used_streams) != expected_streams:
            raise LaneRematerializationError(
                "raw_campaign_decision_source_stream_not_consumed"
            )
        return result


class LaneInputRegistry:
    def __init__(
        self,
        path: Path,
        *,
        allow_registered_march_metadata: bool = False,
    ):
        self.path = path.resolve()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            payload.get("schema") != REGISTRY_SCHEMA
            or payload.get("campaign_sealed") is not False
            or payload.get("registry_root_sha256")
            != _manifest_root(payload, "registry_root_sha256")
        ):
            raise LaneRematerializationError("lane_input_registry_invalid")
        # The March fuse. A registry that carries March is refused outright
        # unless this process holds the one-shot authorization, so an
        # un-armed successor picking up this registry gets the same hard stop
        # CJ's did -- the fuse survives the registry being extended.
        if payload.get("march_window_registered") is not False:
            if payload.get("march_window_registered") is not True:
                raise LaneRematerializationError("lane_input_registry_invalid")
            if (
                not allow_registered_march_metadata
                and march_one_shot.current() is None
            ):
                raise LaneRematerializationError(
                    "lane_input_registry_march_registered_without_authorization"
                )
        self.payload = payload

    def resolve(self, *, window_id: str, purpose: str) -> LaneWindowInputs:
        if window_id not in WINDOWS:
            raise LaneRematerializationError(f"lane_window_unknown:{window_id}")
        window = WINDOWS[window_id]
        guard.authorize_window(
            start=window.start,
            end=window.end,
            purpose=purpose,
            context=f"lane_input_registry:{window_id}",
            note="true-UTC re-materialized LANE source and pack authority",
        )
        raw = (self.payload.get("windows") or {}).get(window_id)
        if not isinstance(raw, Mapping):
            raise LaneRematerializationError(f"lane_window_not_registered:{window_id}")
        entry = dict(raw)
        if entry.get("window") != [window.start, window.end] or entry.get("surface") != "VAL":
            raise LaneRematerializationError(f"lane_window_binding_mismatch:{window_id}")
        plan_digest = entry.get("canonical_source_plan_digest_sha256")
        if plan_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(plan_digest)):
            raise LaneRematerializationError(
                f"lane_canonical_source_plan_digest_invalid:{window_id}"
            )
        manifest_path = _safe_relative(self.path.parent, str(entry["source_manifest"]))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("manifest_root_sha256")
            != entry.get("source_manifest_root_sha256")
            or manifest.get("manifest_root_sha256")
            != _manifest_root(manifest, "manifest_root_sha256")
            or manifest.get("window_id") != window_id
        ):
            raise LaneRematerializationError(f"lane_source_authority_mismatch:{window_id}")
        logical_repo_root = _logical_repo_root_for_registry(
            registry_path=self.path,
            manifest=manifest,
        )
        pack_root = _safe_relative(self.path.parent, str(entry["pack_root"]))
        raw_roots = entry.get("pack_roots") or {}
        pack_roots: dict[tuple[str, str, str], str] = {}
        for raw_key, value in raw_roots.items():
            key = tuple(str(raw_key).split(":"))
            if len(key) != 3 or len(str(value)) != 64:
                raise LaneRematerializationError(f"lane_pack_root_invalid:{raw_key}")
            pack_roots[(key[0], key[1], key[2])] = str(value)
        if entry.get("pack_status") == "BUILT_AND_VALIDATED":
            expected = {(window.split, day, day) for day in window.days}
            if set(pack_roots) != expected:
                raise LaneRematerializationError(
                    f"lane_pack_root_set_incomplete:{window_id}"
                )
        contract = (
            REPO_ROOT
            / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
            "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
        )
        return LaneWindowInputs(
            registry_path=self.path,
            registry=self.payload,
            window_id=window_id,
            window=window,
            entry=entry,
            source_manifest_path=manifest_path,
            source_manifest=manifest,
            pack_root=pack_root,
            pack_roots=pack_roots,
            contract=contract,
            logical_repo_root=logical_repo_root,
        )


def resolve_registered_raw_campaign_window(
    *,
    registry_path: Path,
    window_id: str,
) -> LaneWindowInputs:
    """Resolve only the approved Oct/Nov source window from the held registry."""

    if window_id not in RAW_CAMPAIGN_WINDOW_IDS:
        raise LaneRematerializationError(
            f"raw_campaign_window_not_approved:{window_id}"
        )
    candidate = Path(registry_path)
    if (
        candidate.is_symlink()
        or candidate.resolve() != RAW_CAMPAIGN_REGISTRY_PATH.resolve()
        or not candidate.is_file()
        or _file_sha256(candidate) != RAW_CAMPAIGN_REGISTRY_FILE_SHA256
    ):
        raise LaneRematerializationError("raw_campaign_registry_authority_mismatch")
    registry = LaneInputRegistry(
        candidate,
        allow_registered_march_metadata=True,
    )
    inputs = registry.resolve(
        window_id=window_id,
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    _validate_raw_campaign_frozen_authority(inputs)
    return inputs


def _resolver_for(inputs: LaneWindowInputs) -> LaneBroadSourceResolver:
    specs, _contract = _tick_authority(
        repo_root=inputs.logical_repo_root,
        manifest=inputs.source_manifest,
        manifest_path=inputs.source_manifest_path,
    )
    return LaneBroadSourceResolver(
        use_native_h1=False,
        skip_tick_source=False,
        verbose=False,
        source_accelerator=inputs.accelerator(),
        bound_tick_source_specs=specs,
        bound_tick_source_gaps=_tick_gaps(inputs.source_manifest),
        bound_tick_logical_repo_root=inputs.logical_repo_root,
        sealed_tick_full_component_set=True,
        tick_sparse_cache_root=None,
    )


def _validate_raw_campaign_frozen_authority(
    inputs: LaneWindowInputs,
) -> tuple[str, ...]:
    reopened_registry = json.loads(inputs.registry_path.read_text(encoding="utf-8"))
    if (
        inputs.registry_path != RAW_CAMPAIGN_REGISTRY_PATH.resolve()
        or _file_sha256(inputs.registry_path) != RAW_CAMPAIGN_REGISTRY_FILE_SHA256
        or inputs.registry.get("registry_root_sha256")
        != RAW_CAMPAIGN_REGISTRY_ROOT_SHA256
        or inputs.registry.get("status") != "LANE_TRUE_UTC_INPUT_REGISTRY_COMPLETE"
        or dict(inputs.registry) != reopened_registry
        or dict(inputs.entry)
        != (reopened_registry.get("windows") or {}).get(inputs.window_id)
    ):
        raise LaneRematerializationError("raw_campaign_registry_authority_mismatch")
    if (
        RAW_CAMPAIGN_ESTATE_PATH.is_symlink()
        or not RAW_CAMPAIGN_ESTATE_PATH.is_file()
        or _file_sha256(RAW_CAMPAIGN_ESTATE_PATH)
        != RAW_CAMPAIGN_ESTATE_FILE_SHA256
    ):
        raise LaneRematerializationError("raw_campaign_estate_authority_mismatch")
    estate = json.loads(RAW_CAMPAIGN_ESTATE_PATH.read_text(encoding="utf-8"))
    reopened_manifest = json.loads(
        inputs.source_manifest_path.read_text(encoding="utf-8")
    )
    estate_core = dict(estate)
    estate_root = estate_core.pop("payload_sha256", None)
    estate_days = tuple(
        (estate.get("development_estate") or {}).get("days_utc") or ()
    )
    decision_days = tuple(
        (estate.get("decision_estate") or {}).get("chosen_days_utc") or ()
    )
    reserve_days = tuple(
        (estate.get("decision_estate") or {}).get("held_reserve_days_utc") or ()
    )
    frozen_manifests = (estate.get("source_estate") or {}).get("manifests") or ()
    frozen = next(
        (
            row
            for row in frozen_manifests
            if isinstance(row, Mapping)
            and row.get("window_id") == inputs.window_id
        ),
        None,
    )
    if (
        estate.get("schema")
        != "gtos.wave21.full_system_coherence.development_and_untouched_estates.v1"
        or estate.get("status") != "PREREGISTERED_OUTCOME_BLIND"
        or estate_root != RAW_CAMPAIGN_ESTATE_PAYLOAD_SHA256
        or estate_root != _stable_sha256(estate_core)
        or estate_days != RAW_CAMPAIGN_DEVELOPMENT_DAYS
        or decision_days != RAW_CAMPAIGN_DECISION_DAYS
        or reserve_days != RAW_CAMPAIGN_RESERVE_DAYS
        or len(frozen_manifests) != len(RAW_CAMPAIGN_WINDOW_IDS)
        or not isinstance(frozen, Mapping)
        or dict(inputs.source_manifest) != reopened_manifest
        or inputs.logical_repo_root
        != _logical_repo_root_for_registry(
            registry_path=inputs.registry_path,
            manifest=reopened_manifest,
        )
    ):
        raise LaneRematerializationError("raw_campaign_estate_authority_mismatch")
    components: list[dict[str, Any]] = []
    for kind, field_name in (("bar", "bar_sources"), ("tick", "tick_sources")):
        for row in inputs.source_manifest.get(field_name) or ():
            actual = _safe_relative(
                inputs.logical_repo_root,
                str(row.get("repo_relpath") or ""),
            )
            if not actual.is_file() or actual.is_symlink():
                raise LaneRematerializationError(
                    "raw_campaign_component_authority_mismatch"
                )
            components.append(
                {
                    "bytes": actual.stat().st_size,
                    "first_utc": row.get("first_utc"),
                    "kind": kind,
                    "last_utc": row.get("last_utc"),
                    "path": row.get("lane_relpath"),
                    "row_count": row.get("row_count"),
                    "sha256": row.get("sha256"),
                }
            )
    component_root = _stable_sha256(
        sorted(components, key=lambda row: (str(row["kind"]), str(row["path"])))
    )
    if (
        inputs.source_manifest_path.resolve() != Path(str(frozen["path"])).resolve()
        or _file_sha256(inputs.source_manifest_path) != frozen.get("file_sha256")
        or inputs.source_manifest.get("manifest_root_sha256")
        != frozen.get("manifest_root_sha256")
        or inputs.entry.get("canonical_source_plan_digest_sha256")
        != frozen.get("registered_source_plan_digest_sha256")
        or component_root != frozen.get("component_bindings_root_sha256")
        or len(components) != frozen.get("member_count")
    ):
        raise LaneRematerializationError("raw_campaign_manifest_authority_mismatch")
    return (*estate_days, *decision_days)


def _validate_raw_campaign_manifest(
    inputs: LaneWindowInputs,
    *,
    days: Sequence[str],
) -> tuple[str, ...]:
    normalized_days = tuple(days)
    if inputs.window_id not in RAW_CAMPAIGN_WINDOW_IDS:
        raise LaneRematerializationError("raw_campaign_window_not_approved")
    if (
        not normalized_days
        or any(not isinstance(day, str) for day in normalized_days)
        or normalized_days != tuple(sorted(set(normalized_days)))
    ):
        raise LaneRematerializationError("raw_campaign_days_invalid")
    approved_days = _validate_raw_campaign_frozen_authority(inputs)
    if not set(normalized_days).issubset(approved_days):
        raise LaneRematerializationError("raw_campaign_day_not_approved")
    if not set(normalized_days).issubset(inputs.window.days):
        raise LaneRematerializationError("raw_campaign_days_outside_window")
    symbols = tuple(RAW_CAMPAIGN_SYMBOLS)
    manifest = inputs.source_manifest
    if (
        not symbols
        or len(symbols) != len(set(symbols))
        or manifest.get("window_id") != inputs.window_id
        or manifest.get("window") != [inputs.window.start, inputs.window.end]
        or manifest.get("economic_outcomes_read") is not False
        or manifest.get("broker_live_authority") is not False
        or manifest.get("broker_mutation_enabled") is not False
    ):
        raise LaneRematerializationError("raw_campaign_manifest_invalid")
    bar_rows = manifest.get("bar_sources") or ()
    expected_bars = {
        (symbol, timeframe)
        for symbol in symbols
        for timeframe in ("D1", "H4", "M15", "M1")
    }
    observed_bars = [
        (str(row.get("symbol")), str(row.get("timeframe")))
        for row in bar_rows
        if isinstance(row, Mapping)
    ]
    if (
        len(observed_bars) != len(expected_bars)
        or set(observed_bars) != expected_bars
        or any(
            row.get("time_column_basis") != "true_utc"
            or row.get("broker_clock_rule") != NEW_YORK_PLUS_7.name
            for row in bar_rows
        )
    ):
        raise LaneRematerializationError("raw_campaign_bar_authority_invalid")
    tick_rows = [
        row
        for row in manifest.get("tick_sources") or ()
        if isinstance(row, Mapping)
    ]
    ticks = {str(row.get("symbol")) for row in tick_rows}
    gaps = [
        row for row in manifest.get("tick_gaps") or () if isinstance(row, Mapping)
    ]
    gap_symbols = {str(row.get("symbol")) for row in gaps}
    expected_gaps = set(symbols) - set(TICK_SYMBOLS)
    if (
        ticks != set(TICK_SYMBOLS)
        or len(tick_rows) != len(TICK_SYMBOLS)
        or any(
            row.get("time_column_basis") != "true_utc"
            or row.get("broker_clock_rule") != NEW_YORK_PLUS_7.name
            for row in tick_rows
        )
        or gap_symbols != expected_gaps
        or len(gaps) != len(expected_gaps)
        or any(
            row.get("status") != "no_captured_tick_source_for_symbol"
            or row.get("ordered_tick_truth_satisfied") is not False
            for row in gaps
        )
    ):
        raise LaneRematerializationError("raw_campaign_tick_coverage_invalid")
    return normalized_days


_QUOTE_OFFSET_STRIDE = 4096


def _strict_quote_component_path(root: Path, raw: str) -> tuple[Path, Path]:
    """Resolve one logical component only after lstat rejects link traversal."""

    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise LaneRematerializationError(f"non_relocatable_path:{raw}")
    cursor = root.absolute()
    try:
        if stat.S_ISLNK(cursor.lstat().st_mode):
            raise LaneRematerializationError(
                f"lane_quote_source_component_symlink_refused:{raw}"
            )
        for part in relative.parts:
            cursor /= part
            if stat.S_ISLNK(cursor.lstat().st_mode):
                raise LaneRematerializationError(
                    f"lane_quote_source_component_symlink_refused:{raw}"
                )
    except OSError as exc:
        raise LaneRematerializationError(
            f"lane_quote_source_component_unresolvable:{raw}"
        ) from exc
    resolved = cursor.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise LaneRematerializationError(f"lane_path_escape:{raw}") from exc
    if not stat.S_ISREG(resolved.stat().st_mode):
        raise LaneRematerializationError(
            f"lane_quote_source_component_not_regular:{raw}"
        )
    return cursor, resolved


def _open_file_sha256(handle: Any) -> str:
    position = handle.tell()
    digest = hashlib.sha256()
    try:
        handle.seek(0)
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    finally:
        handle.seek(position)
    return digest.hexdigest()


def _strict_quote_row(
    raw_line: bytes,
    *,
    label: str,
) -> tuple[dict[str, Any], datetime, float, float]:
    """Parse one exact LF-terminated UTF-8 quote row."""

    if not raw_line.endswith(b"\n") or b"\r" in raw_line:
        raise LaneRematerializationError(f"{label}:strict_lf_record_required")
    try:
        text = raw_line.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise LaneRematerializationError(f"{label}:strict_utf8_required") from exc

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for key, value in pairs:
            if key in row:
                raise LaneRematerializationError(f"{label}:duplicate_json_key:{key}")
            row[key] = value
        return row

    def finite_float(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise LaneRematerializationError(f"{label}:nonfinite_json_number")
        return number

    try:
        row = json.loads(
            text,
            object_pairs_hook=unique,
            parse_float=finite_float,
            parse_constant=lambda value: (_ for _ in ()).throw(
                LaneRematerializationError(
                    f"{label}:nonfinite_json_constant:{value}"
                )
            ),
        )
    except json.JSONDecodeError as exc:
        raise LaneRematerializationError(f"{label}:strict_json_required") from exc
    if not isinstance(row, dict):
        raise LaneRematerializationError(f"{label}:json_object_required")

    instants: list[datetime] = []
    for key in timewarp.CSV_TIME_KEYS:
        value = row.get(key)
        if value in (None, ""):
            continue
        if not isinstance(value, str):
            raise LaneRematerializationError(f"{label}:{key}_must_be_iso8601_text")
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LaneRematerializationError(f"{label}:{key}_invalid_iso8601") from exc
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise LaneRematerializationError(f"{label}:{key}_must_be_explicit_true_utc")
        instants.append(instant.astimezone(timezone.utc))
    if not instants:
        raise LaneRematerializationError(f"{label}:true_utc_timestamp_missing")
    if any(instant != instants[0] for instant in instants[1:]):
        raise LaneRematerializationError(f"{label}:true_utc_timestamps_disagree")

    quotes: list[float] = []
    for field_name in ("bid", "ask"):
        value = row.get(field_name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise LaneRematerializationError(f"{label}:{field_name}_must_be_number")
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise LaneRematerializationError(
                f"{label}:{field_name}_must_be_finite_positive"
            )
        quotes.append(number)
    bid, ask = quotes
    if ask < bid:
        raise LaneRematerializationError(f"{label}:crossed_quote_refused")
    return row, instants[0], bid, ask


@dataclass
class _LaneQuoteComponentIndex:
    spec: timewarp.SourceSpec
    logical_path: Path
    path: Path
    handle: Any
    offsets: array
    byte_count: int
    row_count: int
    stride: int
    device: int
    inode: int

    def raw_row(self, physical_row_index: int) -> bytes:
        if (
            isinstance(physical_row_index, bool)
            or not isinstance(physical_row_index, int)
            or physical_row_index < 0
            or physical_row_index >= self.row_count
        ):
            raise LaneRematerializationError(
                "lane_quote_source_physical_row_index_out_of_range"
            )
        checkpoint, remainder = divmod(physical_row_index, self.stride)
        self.handle.seek(int(self.offsets[checkpoint]))
        raw_line = b""
        for _ in range(remainder + 1):
            raw_line = self.handle.readline()
        if not raw_line:
            raise LaneRematerializationError(
                "lane_quote_source_component_changed_during_row_read"
            )
        return raw_line


class LaneQuoteSourceResolver:
    """One run-scoped LF offset index over A1's exact frozen tick components."""

    def __init__(self, inputs: LaneWindowInputs, *, days: Sequence[str]) -> None:
        if type(inputs) is not LaneWindowInputs:
            raise TypeError("LaneQuoteSourceResolver requires LaneWindowInputs")
        self.inputs = inputs
        self.days = tuple(days)
        self._active = False
        self._registry_sha256 = ""
        self._manifest_sha256 = ""
        self._authority_root_sha256 = ""
        self._components: dict[str, _LaneQuoteComponentIndex] = {}
        self._issued_receipts: dict[object, VerifiedQuoteGeometryReceipt] = {}

    @property
    def authority_root_sha256(self) -> str:
        if not self._active:
            raise LaneRematerializationError("lane_quote_source_resolver_not_active")
        return self._authority_root_sha256

    def _build_component(
        self,
        spec: timewarp.SourceSpec,
    ) -> _LaneQuoteComponentIndex:
        if (
            not re.fullmatch(r"[0-9a-f]{64}", str(spec.sha256 or ""))
            or not re.fullmatch(r"[0-9a-f]{64}", str(spec.source_server_hash or ""))
            or not re.fullmatch(r"[0-9a-f]{64}", str(spec.source_account_hash or ""))
        ):
            raise LaneRematerializationError(
                f"lane_quote_source_component_identity_invalid:{spec.symbol}"
            )
        logical_path, path = _strict_quote_component_path(
            self.inputs.logical_repo_root,
            spec.path.as_posix(),
        )
        offsets = array("Q")
        first: datetime | None = None
        last: datetime | None = None
        previous: datetime | None = None
        path_stat = logical_path.lstat()
        resolved_stat = path.stat()
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(logical_path, flags)
        try:
            handle = os.fdopen(descriptor, "rb")
        except BaseException:
            os.close(descriptor)
            raise
        try:
            opened_stat = os.fstat(handle.fileno())
            identity = (opened_stat.st_dev, opened_stat.st_ino)
            if (
                identity != (path_stat.st_dev, path_stat.st_ino)
                or identity != (resolved_stat.st_dev, resolved_stat.st_ino)
            ):
                raise LaneRematerializationError(
                    f"lane_quote_source_component_open_identity_mismatch:{spec.symbol}"
                )
            component_digest = hashlib.sha256()
            row_count = 0
            while True:
                offset = handle.tell()
                raw_line = handle.readline()
                if not raw_line:
                    byte_count = offset
                    break
                component_digest.update(raw_line)
                if row_count % _QUOTE_OFFSET_STRIDE == 0:
                    offsets.append(offset)
                label = f"lane_quote_source:{spec.symbol}:row:{row_count}"
                row, observed, _bid, _ask = _strict_quote_row(
                    raw_line,
                    label=label,
                )
                if row.get("symbol") not in (
                    None,
                    "",
                    spec.symbol,
                    spec.mapped_symbol,
                ):
                    raise LaneRematerializationError(
                        f"{label}:row_symbol_binding_mismatch"
                    )
                if previous is not None and observed < previous:
                    raise LaneRematerializationError(f"{label}:timestamp_order_decreased")
                first = first or observed
                last = observed
                previous = observed
                row_count += 1
            closed_scan_stat = os.fstat(handle.fileno())
            current_path_stat = logical_path.lstat()
            current_resolved_stat = path.stat()
            if (
                component_digest.hexdigest() != spec.sha256
                or byte_count != opened_stat.st_size
                or (closed_scan_stat.st_dev, closed_scan_stat.st_ino)
                != identity
                or closed_scan_stat.st_size != byte_count
                or (current_path_stat.st_dev, current_path_stat.st_ino)
                != identity
                or (current_resolved_stat.st_dev, current_resolved_stat.st_ino)
                != identity
            ):
                raise LaneRematerializationError(
                    f"lane_quote_source_component_open_bytes_mismatch:{spec.symbol}"
                )
            declared_first = datetime.fromisoformat(
                str(spec.start_utc).replace("Z", "+00:00")
            )
            declared_last = datetime.fromisoformat(
                str(spec.end_utc).replace("Z", "+00:00")
            )
            if (
                declared_first.tzinfo is None
                or declared_first.utcoffset() != timedelta(0)
                or declared_last.tzinfo is None
                or declared_last.utcoffset() != timedelta(0)
            ):
                raise LaneRematerializationError(
                    f"lane_quote_source_component_interval_invalid:{spec.symbol}"
                )
            declared_first = declared_first.astimezone(timezone.utc)
            declared_last = declared_last.astimezone(timezone.utc)
            if (
                row_count != spec.row_count
                or first != declared_first
                or last != declared_last
            ):
                raise LaneRematerializationError(
                    f"lane_quote_source_component_content_mismatch:{spec.symbol}"
                )
            handle.seek(0)
            return _LaneQuoteComponentIndex(
                spec=spec,
                logical_path=logical_path,
                path=path,
                handle=handle,
                offsets=offsets,
                byte_count=byte_count,
                row_count=row_count,
                stride=_QUOTE_OFFSET_STRIDE,
                device=opened_stat.st_dev,
                inode=opened_stat.st_ino,
            )
        except BaseException:
            handle.close()
            raise

    def __enter__(self) -> "LaneQuoteSourceResolver":
        if self._active or self._components:
            raise LaneRematerializationError(
                "lane_quote_source_resolver_cannot_be_reentered"
            )
        _validate_raw_campaign_manifest(self.inputs, days=self.days)
        if self.inputs.registry_path.is_symlink() or self.inputs.source_manifest_path.is_symlink():
            raise LaneRematerializationError("lane_quote_source_authority_symlink_refused")
        specs, _authority = _tick_authority(
            repo_root=self.inputs.logical_repo_root,
            manifest=self.inputs.source_manifest,
            manifest_path=self.inputs.source_manifest_path,
        )
        registry_sha = _file_sha256(self.inputs.registry_path)
        manifest_sha = _file_sha256(self.inputs.source_manifest_path)
        components: list[_LaneQuoteComponentIndex] = []
        try:
            for symbol in TICK_SYMBOLS:
                candidates = specs.get(symbol) or ()
                if len(candidates) != 1:
                    raise LaneRematerializationError(
                        f"lane_quote_source_component_denominator_invalid:{symbol}"
                    )
                components.append(
                    self._build_component(candidates[0])
                )
            self._registry_sha256 = registry_sha
            self._manifest_sha256 = manifest_sha
            self._authority_root_sha256 = _stable_sha256(
                {
                    "registry_file_sha256": registry_sha,
                    "registry_root_sha256": self.inputs.registry[
                        "registry_root_sha256"
                    ],
                    "manifest_file_sha256": manifest_sha,
                    "manifest_root_sha256": self.inputs.source_manifest[
                        "manifest_root_sha256"
                    ],
                    "window_id": self.inputs.window_id,
                    "days": list(self.days),
                    "components": sorted(
                        (
                            component.spec.path.as_posix(),
                            component.spec.sha256,
                            component.spec.symbol,
                            component.spec.mapped_symbol,
                            component.spec.source_broker,
                            component.spec.source_server_hash,
                            component.spec.source_account_hash,
                            "true_utc",
                            NEW_YORK_PLUS_7.name,
                        )
                        for component in components
                    ),
                }
            )
            self._components = {
                component.spec.symbol: component for component in components
            }
            self._active = True
            return self
        except BaseException:
            for component in components:
                component.handle.close()
            raise

    def resolve_geometry(
        self,
        *,
        trade_id: str,
        account: str,
        symbol: str,
        entry_physical_row_index: int,
        exit_physical_row_index: int,
    ) -> VerifiedQuoteGeometryReceipt:
        if not self._active:
            raise LaneRematerializationError("lane_quote_source_resolver_not_active")
        component = self._components.get(symbol)
        if component is None or component.spec.source_broker != account:
            raise LaneRematerializationError(
                "lane_quote_geometry_row_binding_mismatch"
            )
        entry_raw = component.raw_row(entry_physical_row_index)
        exit_raw = component.raw_row(exit_physical_row_index)
        _, entry_utc, entry_bid, entry_ask = _strict_quote_row(
            entry_raw,
            label=f"lane_quote_source:{symbol}:row:{entry_physical_row_index}",
        )
        _, exit_utc, exit_bid, exit_ask = _strict_quote_row(
            exit_raw,
            label=f"lane_quote_source:{symbol}:row:{exit_physical_row_index}",
        )
        if (
            entry_utc.date().isoformat() not in self.days
            or exit_utc.date().isoformat() not in self.days
        ):
            raise LaneRematerializationError(
                "lane_quote_geometry_row_outside_approved_run_days"
            )
        if (exit_utc, exit_physical_row_index) <= (
            entry_utc,
            entry_physical_row_index,
        ):
            raise LaneRematerializationError(
                "lane_quote_geometry_exit_not_after_entry"
            )
        try:
            token = object()
            receipt = VerifiedQuoteGeometryReceipt(
                source_path=component.spec.path.as_posix(),
                source_sha256=str(component.spec.sha256),
                row_index=entry_physical_row_index,
                trade_id=trade_id,
                source_authority_root_sha256=self.authority_root_sha256,
                exit_source=SpreadGeometryEvidence(
                    component.spec.path.as_posix(),
                    str(component.spec.sha256),
                    exit_physical_row_index,
                    trade_id,
                ),
                entry_row_sha256=hashlib.sha256(entry_raw).hexdigest(),
                exit_row_sha256=hashlib.sha256(exit_raw).hexdigest(),
                entry_utc=entry_utc.isoformat(),
                entry_bid_price=entry_bid,
                entry_ask_price=entry_ask,
                exit_utc=exit_utc.isoformat(),
                exit_bid_price=exit_bid,
                exit_ask_price=exit_ask,
                _resolver_token=token,
            )
            self._issued_receipts[token] = receipt
            return receipt
        except (CostTruthError, TypeError, ValueError) as exc:
            raise LaneRematerializationError(
                f"lane_quote_geometry_receipt_issue_failed:{exc}"
            ) from exc

    def _validate_verified_quote_geometry_receipt_for_cost(
        self,
        receipt: VerifiedQuoteGeometryReceipt,
    ) -> bool:
        """Validate one exact in-memory receipt while this resolver is active."""

        if not self._active:
            raise LaneRematerializationError("lane_quote_source_resolver_not_active")
        if type(receipt) is not VerifiedQuoteGeometryReceipt:
            raise LaneRematerializationError(
                "lane_quote_geometry_verified_receipt_required"
            )
        token = receipt._resolver_token
        if self._issued_receipts.get(token) is not receipt:
            raise LaneRematerializationError(
                "lane_quote_geometry_receipt_not_issued_by_active_resolver"
            )
        return True

    def verify_unchanged(self) -> None:
        if not self._active:
            raise LaneRematerializationError("lane_quote_source_resolver_not_active")
        if (
            self.inputs.registry_path.is_symlink()
            or self.inputs.source_manifest_path.is_symlink()
            or _file_sha256(self.inputs.registry_path) != self._registry_sha256
            or _file_sha256(self.inputs.source_manifest_path) != self._manifest_sha256
        ):
            raise LaneRematerializationError(
                "lane_quote_source_registry_or_manifest_drift"
            )
        for component in self._components.values():
            logical_path, current_path = _strict_quote_component_path(
                self.inputs.logical_repo_root,
                component.spec.path.as_posix(),
            )
            logical_stat = logical_path.lstat()
            resolved_stat = current_path.stat()
            descriptor_stat = os.fstat(component.handle.fileno())
            identity = (component.device, component.inode)
            if (
                logical_path != component.logical_path
                or current_path != component.path
                or (logical_stat.st_dev, logical_stat.st_ino) != identity
                or (resolved_stat.st_dev, resolved_stat.st_ino) != identity
                or (descriptor_stat.st_dev, descriptor_stat.st_ino) != identity
                or descriptor_stat.st_size != component.byte_count
                or _open_file_sha256(component.handle) != component.spec.sha256
            ):
                raise LaneRematerializationError(
                    "lane_quote_source_component_drift"
                )

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        verification_error: BaseException | None = None
        try:
            self.verify_unchanged()
        except BaseException as caught:
            verification_error = caught
        finally:
            for component in self._components.values():
                component.handle.close()
            self._issued_receipts.clear()
            self._active = False
        if verification_error is not None:
            raise verification_error from exc
        return False


def _with_loader_component_authority(
    inputs: LaneWindowInputs,
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> dict[str, dict[str, timewarp.ResolvedSource]]:
    """Add byte/parser bindings to the component labels the resolver emits."""

    entries = {
        (str(row["symbol"]), str(row.get("timeframe") or "TICK")): row
        for row in (
            *(inputs.source_manifest.get("bar_sources") or ()),
            *(inputs.source_manifest.get("tick_sources") or ()),
        )
    }
    common = {
        "loader_manifest_file_sha256": _file_sha256(inputs.source_manifest_path),
        "loader_registry_file_sha256": _file_sha256(inputs.registry_path),
        "loader_development_estate_file_sha256": _file_sha256(
            RAW_CAMPAIGN_ESTATE_PATH
        ),
        "loader_parser_module_file_sha256": _file_sha256(
            Path(str(integrated.legacy.__file__))
        ),
    }
    enriched: dict[str, dict[str, timewarp.ResolvedSource]] = {}
    for symbol in RAW_CAMPAIGN_SYMBOLS:
        by_timeframe = sources[symbol]
        enriched[symbol] = {}
        for timeframe, source in by_timeframe.items():
            physical_timeframe = "M15" if timeframe == "H1" else timeframe
            entry = entries.get((symbol, physical_timeframe))
            if entry is None:
                raise LaneRematerializationError(
                    f"raw_campaign_component_not_manifest_bound:{symbol}:{timeframe}"
                )
            authority = {
                **common,
                "loader_component_file_sha256": entry["sha256"],
                "loader_time_column_basis": entry.get("time_column_basis"),
                "loader_broker_clock_rule": entry.get("broker_clock_rule"),
                "loader_naive_timestamp_interpretation_allowed": False,
            }
            if timeframe == "H1":
                authority.update(
                    authority_role=(
                        "deterministic_h1_derived_from_manifest_bound_m15"
                    ),
                    p1_packet_equivalence_claimed=False,
                )
            elif timeframe == "TICK":
                authority["loader_parse_mode"] = (
                    "lazy_ordered_tick_rows_reparsed_on_causal_query"
                )
            labels = tuple(
                {**dict(label), **authority}
                for label in source.component_source_labels
            )
            enriched[symbol][timeframe] = replace(
                source,
                component_source_labels=labels,
            )
    return enriched


def _verify_raw_parent_times(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Prove physical timestamps are aware, ordered, and parser-preserved."""

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = [field for field in timewarp.CSV_TIME_KEYS if field in (reader.fieldnames or ())]
        if len(fields) != 1:
            raise LaneRematerializationError("raw_campaign_time_field_invalid")
        prior: datetime | None = None
        count = 0
        for ordinal, raw in enumerate(reader):
            if ordinal >= len(rows):
                raise LaneRematerializationError("raw_campaign_parser_row_mismatch")
            text = str(raw.get(fields[0]) or "").replace("Z", "+00:00")
            try:
                observed = datetime.fromisoformat(text)
            except ValueError as exc:
                raise LaneRematerializationError("raw_campaign_time_invalid") from exc
            parsed = integrated.legacy.parse_row_time(rows[ordinal])
            if (
                observed.tzinfo is None
                or observed.utcoffset() is None
                or parsed != observed.astimezone(timezone.utc)
                or (prior is not None and observed <= prior)
            ):
                raise LaneRematerializationError("raw_campaign_timebase_invalid")
            prior = observed
            count += 1
        if count != len(rows):
            raise LaneRematerializationError("raw_campaign_parser_row_mismatch")


def _load_raw_campaign_sources(
    inputs: LaneWindowInputs,
    *,
    days: Sequence[str],
) -> dict[str, dict[str, timewarp.ResolvedSource]]:
    normalized_days = _validate_raw_campaign_manifest(inputs, days=days)
    resolver = _resolver_for(inputs)
    sources = resolver.build_sources_for_days(
        normalized_days,
        symbols=tuple(RAW_CAMPAIGN_SYMBOLS),
        source_authority_days=normalized_days,
    )
    if set(sources) != set(RAW_CAMPAIGN_SYMBOLS):
        raise LaneRematerializationError(
            "raw_campaign_resolved_symbol_denominator_invalid"
        )
    tick_symbols: set[str] = set()
    for symbol, by_timeframe in sources.items():
        for timeframe in RAW_CAMPAIGN_REQUIRED_TIMEFRAMES:
            if not isinstance(by_timeframe.get(timeframe), timewarp.ResolvedSource):
                raise LaneRematerializationError(
                    f"raw_campaign_resolved_source_missing:{symbol}:{timeframe}"
                )
        if isinstance(by_timeframe.get("TICK"), timewarp.ResolvedSource):
            tick_symbols.add(symbol)
    if tick_symbols != set(TICK_SYMBOLS):
        raise LaneRematerializationError(
            "raw_campaign_resolved_tick_denominator_invalid"
        )
    accelerator = resolver.source_accelerator
    if not isinstance(accelerator, LaneReplaySourceAccelerator):
        raise LaneRematerializationError(
            "raw_campaign_loader_accelerator_missing"
        )
    for entry in inputs.source_manifest.get("bar_sources") or ():
        logical = Path(str(entry["repo_relpath"]))
        rows = accelerator._load(logical, symbol=str(entry["symbol"]))
        _verify_raw_parent_times(accelerator._actual(entry), rows)
    return _with_loader_component_authority(inputs, sources)


def _source_state(source: timewarp.ResolvedSource, timeframe: str) -> tuple[Any, ...]:
    return (
        source.spec,
        source.rows,
        None if timeframe == "TICK" else dict(source.rows_by_day),
        source.sha256,
        source.day_counts,
        source.selected_status,
        source.min_required_rows_per_day,
        source.source_gaps,
        source.component_source_labels,
        source.day_source_authority,
    )


def _validate_raw_campaign_sources(
    inputs: LaneWindowInputs,
    *,
    days: Sequence[str],
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> None:
    reopened_inputs = resolve_registered_raw_campaign_window(
        registry_path=inputs.registry_path,
        window_id=inputs.window_id,
    )
    reopened = _load_raw_campaign_sources(
        reopened_inputs,
        days=days,
    )
    if set(sources) != set(reopened):
        raise LaneRematerializationError(
            "raw_campaign_source_reopen_mismatch:symbols"
        )
    for symbol, expected_by_timeframe in reopened.items():
        observed_by_timeframe = sources[symbol]
        if set(observed_by_timeframe) != set(expected_by_timeframe):
            raise LaneRematerializationError(
                f"raw_campaign_source_reopen_mismatch:{symbol}:timeframes"
            )
        for timeframe, expected in expected_by_timeframe.items():
            if _source_state(
                observed_by_timeframe[timeframe], timeframe
            ) != _source_state(expected, timeframe):
                raise LaneRematerializationError(
                    f"raw_campaign_source_reopen_mismatch:{symbol}:{timeframe}"
                )


@contextlib.contextmanager
def _installed_raw_campaign_successor_witness(
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> Iterator[set[tuple[str, str]]]:
    """Attach the shared adjacent-successor witness before live ingestion."""

    streams: dict[tuple[int, str], tuple[str, str]] = {}
    for symbol in RAW_CAMPAIGN_SYMBOLS:
        for timeframe in RAW_CAMPAIGN_DECISION_TIMEFRAMES:
            rows = sources[symbol][timeframe].rows
            key = (id(rows), timeframe)
            if key in streams:
                raise LaneRematerializationError(
                    "raw_campaign_decision_source_rows_identity_reused"
                )
            streams[key] = (symbol, timeframe)
    used_streams: set[tuple[str, str]] = set()

    def causal_rows(
        rows: Iterable[Mapping[str, Any]],
        *,
        timeframe: str,
        asof: datetime,
        max_rows: int | None = None,
        attach_witness: bool = True,
    ) -> tuple[dict[str, Any], ...]:
        if attach_witness is not True:
            raise LaneRematerializationError(
                "raw_campaign_completed_bar_witness_required"
            )
        tf_name = str(timeframe).upper()
        stream = streams.get((id(rows), tf_name))
        if stream is None:
            raise LaneRematerializationError(
                "raw_campaign_unregistered_decision_source_stream"
            )
        selected = observed_successor_closed_bar_rows_until(
            rows,
            timeframe=tf_name,
            asof=asof,
            max_rows=max_rows,
            attach_witness=True,
        )
        used_streams.add(stream)
        return selected

    original = timewarp.closed_bar_rows_until
    original_observed = timewarp.observed_successor_closed_bar_rows_until
    timewarp.closed_bar_rows_until = causal_rows
    timewarp.observed_successor_closed_bar_rows_until = causal_rows
    try:
        yield used_streams
    finally:
        timewarp.observed_successor_closed_bar_rows_until = original_observed
        timewarp.closed_bar_rows_until = original


def _register_pack_roots(
    registry_path: Path,
    *,
    window_id: str,
    pack_roots: Mapping[str, str],
    pack_root: Path | None = None,
) -> dict[str, Any]:
    with _registry_write_lock(registry_path):
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        core = dict(payload)
        core.pop("registry_root_sha256", None)
        windows = {key: dict(value) for key, value in core["windows"].items()}
        entry = dict(windows[window_id])
        if pack_root is not None:
            entry["pack_root"] = pack_root.resolve().relative_to(
                registry_path.parent.resolve()
            ).as_posix()
        entry["pack_roots"] = dict(sorted(pack_roots.items()))
        entry["pack_status"] = "BUILT_AND_VALIDATED"
        windows[window_id] = entry
        core["windows"] = windows
        if all(
            dict(value).get("pack_status") == "BUILT_AND_VALIDATED"
            for value in windows.values()
        ):
            core["status"] = "LANE_TRUE_UTC_INPUT_REGISTRY_COMPLETE"
        updated = {**core, "registry_root_sha256": _stable_sha256(core)}
        _write_json(registry_path, updated)
    return updated


@contextlib.contextmanager
def _registry_write_lock(registry_path: Path) -> Iterator[None]:
    lock_path = registry_path.with_name(f".{registry_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _register_source_plan_digest(
    registry_path: Path,
    *,
    window_id: str,
    digest: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LaneRematerializationError("canonical_source_plan_digest_invalid")
    with _registry_write_lock(registry_path):
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        core = dict(payload)
        core.pop("registry_root_sha256", None)
        windows = {key: dict(value) for key, value in core["windows"].items()}
        entry = dict(windows[window_id])
        existing = entry.get("canonical_source_plan_digest_sha256")
        if existing is not None and existing != digest:
            raise LaneRematerializationError(
                f"canonical_source_plan_digest_drift:{window_id}:{existing}:{digest}"
            )
        entry["canonical_source_plan_digest_sha256"] = digest
        windows[window_id] = entry
        core["windows"] = windows
        updated = {**core, "registry_root_sha256": _stable_sha256(core)}
        _write_json(registry_path, updated)
    return updated


def _measure_canonical_source_plan(inputs: LaneWindowInputs) -> dict[str, Any]:
    """Measure one canonical plan without mutating its registry or reading outcomes."""

    resolver = _resolver_for(inputs)
    started = time.perf_counter()
    with inputs.runtime_bindings():
        sources = resolver.build_sources_for_days(
            inputs.window.days,
            symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
            source_authority_days=inputs.window.days,
        )
        # Tick component labels are intentionally repo-relative.  Hash their
        # physical bytes while the owning logical repo is the active path
        # context, exactly as the replay runtime does.
        plan = attempt5.static_source_authority_plan(
            sources=sources,
            source_authority_days=inputs.window.days,
            requested_symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
        )
    if set(sources) != set(timewarp.GTOS_24_SYMBOL_SURFACE):
        missing = sorted(set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(sources))
        raise LaneRematerializationError(f"canonical_source_plan_incomplete:{missing}")
    digest = str(plan.get("plan_digest_sha256") or "")
    if plan.get("valid") is not True or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise LaneRematerializationError("canonical_source_plan_invalid")
    fragment_rebinds = [
        {
            key: row.get(key)
            for key in (
                "symbol",
                "trading_day",
                "m1_row_count",
                "m15_row_count",
                "effective_min_rows",
                "source_day_authority_id",
                "lane_authority_rebind_reason",
                "lane_broker_clock_rule",
                "lane_enclosing_broker_day",
                "lane_enclosing_broker_day_m1_row_count",
                "lane_enclosing_broker_day_m15_row_count",
                "lane_enclosing_broker_day_authority_id",
                "lane_original_utc_fragment_authority_hash_sha256",
            )
        }
        for row in plan.get("m1_symbol_day_authority_rows") or ()
        if isinstance(row, Mapping) and row.get("lane_authority_rebind") is True
    ]
    return {
        "canonical_source_plan_digest_sha256": digest,
        "lane_true_utc_fragment_rebinds": fragment_rebinds,
        "symbol_count": len(sources),
        "source_authority_day_count": len(inputs.window.days),
        "wall_seconds": round(time.perf_counter() - started, 3),
    }


def inspect_canonical_source_plan(
    *, registry_path: Path, window_id: str, stop_after_day: str | None = None
) -> dict[str, Any]:
    """Produce a read-only sidecar authority for a foreign LANE registry."""

    inputs = LaneInputRegistry(registry_path).resolve(
        window_id=window_id, purpose=guard.PURPOSE_LANE_ITERATION
    )
    if stop_after_day is not None:
        inputs = inputs.for_prefix(stop_after_day)
    measured = _measure_canonical_source_plan(inputs)
    core = {
        "schema": "gtos.lane.rematerialization.canonical_source_plan.v1",
        "status": "LANE_CANONICAL_SOURCE_PLAN_INSPECTED_READ_ONLY",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "window_id": window_id,
        "window": [inputs.window.start, inputs.window.end],
        "surface": "VAL",
        **measured,
        "lane_true_utc_fragment_rebind_count": len(
            measured["lane_true_utc_fragment_rebinds"]
        ),
        "lane_true_utc_fragment_rebind_contract": (
            "rows_unchanged; fragment maps to exactly one broker day; M1 and M15 "
            "prove that broker day spans adjacent UTC dates; unchanged M1/M15 "
            "floor must pass on the complete broker day"
        ),
        "source_manifest_root_sha256": inputs.source_manifest[
            "manifest_root_sha256"
        ],
        "registry_root_sha256": inputs.registry["registry_root_sha256"],
        "registry_absolute_machine_local": str(inputs.registry_path),
        "registry_access": "read_only",
        "logical_source_repo_root": str(inputs.logical_repo_root),
        "r2_source_plan_claimed": False,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def bind_canonical_source_plan(
    *,
    registry_path: Path,
    window_id: str,
    log_look: bool = True,
) -> dict[str, Any]:
    """Recompute and persist the canonical plan in its owning LANE registry."""

    inputs = LaneInputRegistry(registry_path).resolve(
        window_id=window_id, purpose=guard.PURPOSE_LANE_ITERATION
    )
    measured = _measure_canonical_source_plan(inputs)
    digest = str(measured["canonical_source_plan_digest_sha256"])
    fragment_rebinds = list(measured["lane_true_utc_fragment_rebinds"])
    updated = _register_source_plan_digest(
        inputs.registry_path,
        window_id=window_id,
        digest=digest,
    )
    core = {
        "schema": "gtos.lane.rematerialization.canonical_source_plan.v1",
        "status": "LANE_CANONICAL_SOURCE_PLAN_BOUND",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "window_id": window_id,
        "window": [inputs.window.start, inputs.window.end],
        "surface": "VAL",
        "source_authority_day_count": measured["source_authority_day_count"],
        "symbol_count": measured["symbol_count"],
        "canonical_source_plan_digest_sha256": digest,
        "lane_true_utc_fragment_rebind_count": len(fragment_rebinds),
        "lane_true_utc_fragment_rebinds": fragment_rebinds,
        "lane_true_utc_fragment_rebind_contract": (
            "rows_unchanged; fragment maps to exactly one broker day; M1 and M15 "
            "prove that broker day spans adjacent UTC dates; unchanged M1/M15 "
            "floor must pass on the complete broker day"
        ),
        "source_manifest_root_sha256": inputs.source_manifest[
            "manifest_root_sha256"
        ],
        "registry_root_sha256": updated["registry_root_sha256"],
        "r2_source_plan_claimed": False,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "wall_seconds": measured["wall_seconds"],
    }
    receipt = {**core, "receipt_root_sha256": _stable_sha256(core)}
    receipt_path = (
        inputs.registry_path.parent / "receipts" / f"SOURCE_PLAN_{window_id}.json"
    )
    _write_json(receipt_path, receipt)
    if log_look:
        authorization = guard.authorize_window(
            start=inputs.window.start,
            end=inputs.window.end,
            purpose=guard.PURPOSE_LANE_ITERATION,
            context=f"lane_source_plan:{window_id}",
        )
        lane.log_look(
            authorization=authorization,
            spec={
                "family": "true_utc_canonical_source_plan_binding",
                "window_id": window_id,
                "canonical_source_plan_digest_sha256": digest,
                "source_manifest_root_sha256": inputs.source_manifest[
                    "manifest_root_sha256"
                ],
            },
            session="CJ",
            verdict="evaluated",
            note="Canonical source-plan binding only; no economic outcome read.",
            receipt=_repo_relative(
                receipt_path, repo_root=inputs.logical_repo_root
            ),
            engine_version=TRAIN_ENGINE_VERSION,
            mechanism="true_utc_lane_source_plan",
        )
    return receipt


def _runtime_pack_config(
    inputs: LaneWindowInputs,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Reconstruct the exact factor-neutral config the lane arm will assert.

    The prepared-pack format removes the S/R economic fields from its config
    fingerprint, but the historical builder still derives several non-factor
    runtime fields while installing a valid factorial binding.  Building from a
    bare repaired profile therefore produces a different fingerprint even for
    an ARM_NEUTRAL pack.  Reuse S0R0 only as the validated argument shell, then
    record that the pack fingerprint itself is factor-neutral.
    """

    from src.research_infra import b7_5_post_acceleration_runner as b7_runner
    from src.research_infra.fast_engine import sealed_inputs

    historical = sealed_inputs.resolve_sealed_january(REPO_ROOT)
    args = sealed_inputs.build_january_args(
        repo_root=REPO_ROOT,
        arm_id="S0R0",
        output_dir=PACK_CONFIG_IDENTITY_ROUTE,
        output_prefix=_lane_argument_shell_prefix(
            "CJ_PACK_CONFIG_IDENTITY_ONLY", "S0R0"
        ),
        stop_after_day=None,
        sealed=historical,
    )
    # `sealed_inputs.prelude` configures a must-be-new output namespace after
    # binding the config.  A pack-config fingerprint emits no replay output, so
    # execute only the binding half and avoid creating disposable route dirs.
    attempt5.bind_attempt5_finalizer_conflict_key_order()
    attempt5.configure_runtime_evidence_root(attempt5.ATTEMPT5_RUNTIME_EVIDENCE_ROOT)
    b7_runner.bind_fresh_source(args)
    factorial = attempt5.selection_sizing_factorial_binding_from_args(args)
    if (
        not isinstance(factorial, Mapping)
        or factorial.get("valid") is not True
        or factorial.get("arm_id") != "S0R0"
    ):
        raise LaneRematerializationError("lane_pack_factorial_shell_invalid")
    config = attempt5.build_config(
        attempt5.PROFILE_REPAIRED,
        factorial_arm_binding=factorial,
    )
    factor_root = replay_prepared_day_pack.factor_neutral_config_root(config)
    authority = {
        "schema": "gtos.lane.rematerialization.pack_config_authority.v1",
        "profile": attempt5.PROFILE_REPAIRED,
        "factorial_argument_shell_arm": "S0R0",
        "factorial_economics_in_pack_fingerprint": False,
        "factor_neutral_config_root_sha256": factor_root,
        "decision_contract_sha256": factorial.get("decision_contract_sha256"),
        "campaign_sealed": False,
    }
    return config, authority


def build_packs(
    *,
    registry_path: Path,
    window_id: str,
    encoding_workers: int = 1,
    log_look: bool = True,
    successor_tag: str | None = None,
) -> dict[str, Any]:
    """Build immutable per-day packs; campaign authority remains explicitly unsealed."""

    if encoding_workers < 1 or encoding_workers > 2:
        raise LaneRematerializationError("encoding_workers_out_of_bounds:1..2")
    registry = LaneInputRegistry(registry_path)
    inputs = registry.resolve(window_id=window_id, purpose=guard.PURPOSE_LANE_ITERATION)
    if successor_tag is not None and (
        not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", successor_tag)
        or ".." in successor_tag
    ):
        raise LaneRematerializationError("lane_pack_successor_tag_invalid")
    if (
        inputs.entry.get("pack_status") == "BUILT_AND_VALIDATED"
        and successor_tag is None
    ):
        raise LaneRematerializationError(f"lane_packs_already_registered:{window_id}")
    prior_pack_root = inputs.pack_root
    pack_root = (
        inputs.registry_path.parent
        / "packs"
        / f"{window_id}_{successor_tag}"
        if successor_tag is not None
        else prior_pack_root
    )
    resolver = _resolver_for(inputs)
    days = inputs.window.days
    with inputs.runtime_bindings():
        sources = resolver.build_sources_for_days(
            days,
            symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
            source_authority_days=days,
        )
    if set(sources) != set(timewarp.GTOS_24_SYMBOL_SURFACE):
        missing = sorted(set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(sources))
        raise LaneRematerializationError(f"lane_pack_sources_incomplete:{missing}")
    config, pack_config_authority = _runtime_pack_config(inputs)
    roots: dict[str, str] = {}
    builds: list[dict[str, Any]] = []
    started = time.perf_counter()
    with timewarp.own_campaign_exact_caches():
        for day in days:
            key = f"{inputs.window.split}:{day}:{day}"
            destination = pack_root / inputs.window.split / f"{day}_{day}"
            if destination.exists() or destination.is_symlink():
                raise LaneRematerializationError(
                    f"lane_pack_destination_must_be_new:{destination}"
                )
            campaign = timewarp.CampaignConfig(
                name=f"cj_true_utc_{window_id}_{day}",
                phase=f"lane_arm_neutral_{inputs.window.split}",
                days=(day,),
                pending_expiry_minutes=attempt5.REPAIRED_PENDING_EXPIRY_MINUTES,
                use_repaired_pending_expiry=True,
                profile="ARM_NEUTRAL",
                partial_be_runner=True,
                max_candidates_per_symbol_window=0,
                run_smoke_subset=False,
                materialize_packet_sidecars=False,
                materialize_semantic_diagnostics=True,
            )
            build = replay_prepared_day_pack.build_campaign_prepared_day_pack(
                output_dir=destination,
                campaign=campaign,
                config=config,
                sources=sources,
                encoding_worker_count=encoding_workers,
                borrow_campaign_cache_owner=True,
            )
            reader = replay_prepared_day_pack.PreparedDayPackReader(
                destination,
                expected_pack_root_sha256=str(build["pack_root_sha256"]),
            )
            roots[key] = reader.pack_root_sha256
            builds.append(
                {
                    "day": day,
                    "pack_path": destination.relative_to(registry_path.parent).as_posix(),
                    "pack_root_sha256": reader.pack_root_sha256,
                    "record_count": int(build["record_count"]),
                    "compressed_bytes": int(build["compressed_bytes"]),
                    "preparation_wall_seconds": round(
                        float(build["preparation_wall_seconds"]), 3
                    ),
                    "factor_reads_detected": build["factor_reads_detected"],
                    "broker_mutation_enabled": build["broker_mutation_enabled"],
                }
            )
    updated = _register_pack_roots(
        registry_path.resolve(),
        window_id=window_id,
        pack_roots=roots,
        pack_root=pack_root,
    )
    receipt_core = {
        "schema": PACK_BUILD_SCHEMA,
        "status": "LANE_TRUE_UTC_PACKS_BUILT_AND_VALIDATED",
        "campaign_sealed": False,
        "prepared_pack_sealed_marker_semantics": "byte_integrity_only_not_campaign_seal",
        "evidence_class": LANE_EVIDENCE,
        "window_id": window_id,
        "window": [inputs.window.start, inputs.window.end],
        "surface": "VAL",
        "source_manifest_root_sha256": inputs.source_manifest[
            "manifest_root_sha256"
        ],
        # Relocatable, exactly like the read path. `_logical_repo_root_for_registry`
        # already recovers the worktree that owns a moved registry; a writer that
        # still bound to this module's own REPO_ROOT would refuse to extend a
        # registry it can read (`lane_root_must_be_inside_repo`) -- which is what
        # happened the first time the lane hold moved outside the repo.
        "pack_root_repo_relpath": _repo_relative(
            pack_root, repo_root=inputs.logical_repo_root
        ),
        "successor_tag": successor_tag,
        "successor_of_pack_root_repo_relpath": (
            _repo_relative(prior_pack_root, repo_root=inputs.logical_repo_root)
            if successor_tag is not None
            else None
        ),
        "pack_count": len(builds),
        "record_count": sum(int(row["record_count"]) for row in builds),
        "compressed_bytes": sum(int(row["compressed_bytes"]) for row in builds),
        "pack_config_authority": pack_config_authority,
        "wall_seconds": round(time.perf_counter() - started, 3),
        "builds": builds,
        "registry_root_sha256": updated["registry_root_sha256"],
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
    }
    receipt = {**receipt_core, "receipt_root_sha256": _stable_sha256(receipt_core)}
    successor_suffix = f"_{successor_tag}" if successor_tag is not None else ""
    receipt_path = (
        registry_path.parent
        / "receipts"
        / f"PACKS_{window_id}{successor_suffix}.json"
    )
    _write_json(receipt_path, receipt)
    if log_look:
        authorization = guard.authorize_window(
            start=inputs.window.start,
            end=inputs.window.end,
            purpose=guard.PURPOSE_LANE_ITERATION,
            context=f"lane_pack_build:{window_id}",
        )
        lane.log_look(
            authorization=authorization,
            spec={
                "family": "true_utc_source_and_prepared_pack_materialization",
                "window_id": window_id,
                "clock_rule": NEW_YORK_PLUS_7.name,
                "pack_count": len(builds),
                "successor_tag": successor_tag,
                "source_manifest_root_sha256": inputs.source_manifest[
                    "manifest_root_sha256"
                ],
            },
            session="CJ",
            verdict="evaluated",
            note="Input/feature materialization only; no economic outcome read.",
            receipt=_repo_relative(
                receipt_path, repo_root=inputs.logical_repo_root
            ),
            engine_version=TRAIN_ENGINE_VERSION,
            mechanism="true_utc_lane_rematerialization",
        )
    return receipt


def smoke_pack(
    *, registry_path: Path, window_id: str, log_look: bool = True
) -> dict[str, Any]:
    registry = LaneInputRegistry(registry_path)
    inputs = registry.resolve(window_id=window_id, purpose=guard.PURPOSE_LANE_ITERATION)
    if inputs.entry.get("pack_status") != "BUILT_AND_VALIDATED":
        raise LaneRematerializationError(f"lane_pack_not_built:{window_id}")
    resolver = _resolver_for(inputs)
    with inputs.runtime_bindings():
        sources = resolver.build_sources_for_days(
            inputs.window.days,
            symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
            source_authority_days=inputs.window.days,
        )
    config, pack_config_authority = _runtime_pack_config(inputs)
    factor_root = replay_prepared_day_pack.factor_neutral_config_root(config)
    source_root = replay_prepared_day_pack.source_identity_root(sources)
    validated_packs: list[dict[str, Any]] = []
    for day in inputs.window.days:
        key = (inputs.window.split, day, day)
        root = inputs.pack_root / inputs.window.split / f"{day}_{day}"
        reader = replay_prepared_day_pack.PreparedDayPackReader(
            root, expected_pack_root_sha256=inputs.pack_roots[key]
        )
        reader.assert_compatible(
            days=[day],
            symbols=list(timewarp.INCLUDED_SYMBOLS),
            factor_neutral_config_root_sha256=factor_root,
            source_identity_root_sha256=source_root,
            max_candidates_per_symbol_window=0,
        )
        inventory = reader.manifest["window_inventory"]
        first = inventory[0]
        record = reader.next_window(
            trading_day=str(first["trading_day"]),
            decision_time_utc=str(first["decision_time_utc"]),
            window_ordinal=int(first["window_ordinal"]),
        )
        validated_packs.append(
            {
                "day": day,
                "pack_root_sha256": reader.pack_root_sha256,
                "record_count": int(reader.manifest["record_count"]),
                "loaded_record_identity": {
                    "trading_day": record["trading_day"],
                    "decision_time_utc": record["decision_time_utc"],
                    "window_ordinal": record["window_ordinal"],
                    "symbol_count": len(record["symbols"]),
                },
            }
        )
    first_pack = validated_packs[0]
    core = {
        "schema": SMOKE_SCHEMA,
        "status": "LANE_PREPARED_PACK_FIRST_WINDOW_LOADED",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "window_id": window_id,
        "smoke_day": inputs.window.days[0],
        "pack_root_sha256": first_pack["pack_root_sha256"],
        "record_count": first_pack["record_count"],
        "validated_pack_count": len(validated_packs),
        "validated_packs": validated_packs,
        "runtime_binding_compatible": True,
        "factor_neutral_config_root_sha256": factor_root,
        "pack_config_authority": pack_config_authority,
        "source_identity_root_sha256": source_root,
        "loaded_record_identity": first_pack["loaded_record_identity"],
        "economics_run": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "march_outcomes_read": False,
    }
    receipt = {**core, "receipt_root_sha256": _stable_sha256(core)}
    receipt_path = (
        registry_path.parent
        / "receipts"
        / f"SMOKE_{window_id}_{inputs.registry['registry_root_sha256'][:16]}.json"
    )
    _write_json(receipt_path, receipt)
    if log_look:
        authorization = guard.authorize_window(
            start=inputs.window.start,
            end=inputs.window.end,
            purpose=guard.PURPOSE_LANE_ITERATION,
            context=f"lane_pack_smoke:{window_id}",
        )
        lane.log_look(
            authorization=authorization,
            spec={
                "family": "prepared_pack_load_smoke",
                "window_id": window_id,
                "pack_root_sha256": first_pack["pack_root_sha256"],
                "validated_pack_count": len(validated_packs),
                "economics_run": False,
            },
            session="CJ",
            verdict="evaluated",
            note=(
                "Every per-day pack binding authenticated and one record per pack "
                "deserialized; no economics evaluated."
            ),
            receipt=_repo_relative(
                receipt_path, repo_root=inputs.logical_repo_root
            ),
            engine_version=TRAIN_ENGINE_VERSION,
            mechanism="true_utc_lane_pack_smoke",
        )
    return receipt


_HOUR_TOKEN = re.compile(r"^(?P<prefix>moonshot_)?h(?P<start>\d{2})_(?P<end>\d{2})$")
_SESSION_FEATURE_KEYS = ("session", "session_bucket", "kill_zone")


def _utc_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _shift_hour_token(value: str, hours: int = -2) -> str | None:
    match = _HOUR_TOKEN.fullmatch(value)
    if match is None:
        return None
    start = int(match.group("start"))
    end = int(match.group("end"))
    if not (0 <= start < 24 and end == (start + 1) % 24):
        return None
    prefix = match.group("prefix") or ""
    shifted = (start + hours) % 24
    return f"{prefix}h{shifted:02d}_{(shifted + 1) % 24:02d}"


def _scalar_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _scalar_strings(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            yield from _scalar_strings(child)


def _clock_feature_census(record: Mapping[str, Any]) -> dict[str, list[str]]:
    census = {
        "timestamps": [],
        "utc_hour_bucket": [],
        "session": [],
        "session_bucket": [],
        "kill_zone": [],
    }

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                if key == "utc_hour_bucket":
                    census[key].extend(_scalar_strings(child))
                if key in _SESSION_FEATURE_KEYS:
                    census[key].extend(_scalar_strings(child))
                if (
                    key.endswith("_time_utc")
                    or key.endswith("_time_utc_values")
                    or key == "timestamp_utc"
                ):
                    census["timestamps"].extend(
                        raw
                        for raw in _scalar_strings(child)
                        if _utc_datetime(raw) is not None
                    )
                visit(child)
        elif isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            for child in value:
                visit(child)

    visit(record)
    return census


def _pack_record_stream(
    *,
    root: Path,
    split: str,
    days: Sequence[str],
    roots: Mapping[tuple[str, str, str], str],
) -> Iterator[dict[str, Any]]:
    for day in days:
        key = (split, day, day)
        expected = roots.get(key)
        if expected is None:
            raise LaneRematerializationError(f"prepared_pack_root_missing:{key}")
        reader = replay_prepared_day_pack.PreparedDayPackReader(
            root / split / f"{day}_{day}",
            expected_pack_root_sha256=expected,
        )
        yield from reader._iter_records()


def compare_january_pack_features(
    *,
    registry_path: Path,
    frozen_execution_seal: Path = FROZEN_JANUARY_EXECUTION_SEAL,
    log_look: bool = True,
) -> dict[str, Any]:
    """Measure the two-hour feature shift on physically aligned January windows."""

    inputs = LaneInputRegistry(registry_path).resolve(
        window_id="january_2026", purpose=guard.PURPOSE_LANE_ITERATION
    )
    if inputs.entry.get("pack_status") != "BUILT_AND_VALIDATED":
        raise LaneRematerializationError("lane_pack_not_built:january_2026")
    frozen = json.loads(frozen_execution_seal.read_text(encoding="utf-8"))
    binding = frozen.get("prepared_day_pack_binding") or {}
    frozen_root = Path(str(binding.get("prepared_day_pack_root") or ""))
    raw_roots = binding.get("prepared_day_pack_roots") or {}
    frozen_roots = {
        tuple(str(key).split(":")): str(value) for key, value in raw_roots.items()
    }
    expected_keys = {
        (inputs.window.split, day, day) for day in inputs.window.days
    }
    if (
        frozen.get("valid") is not True
        or frozen.get("march_outcome_read") is not False
        or not frozen_root.is_dir()
        or set(frozen_roots) != expected_keys
    ):
        raise LaneRematerializationError("frozen_january_pack_authority_invalid")

    old_records = iter(
        _pack_record_stream(
            root=frozen_root,
            split=inputs.window.split,
            days=inputs.window.days,
            roots=frozen_roots,
        )
    )
    new_records = iter(
        _pack_record_stream(
            root=inputs.pack_root,
            split=inputs.window.split,
            days=inputs.window.days,
            roots=inputs.pack_roots,
        )
    )
    old_record = next(old_records, None)
    new_record = next(new_records, None)
    aligned = 0
    unmatched_old = 0
    unmatched_new = 0
    unmatched_examples: list[dict[str, str]] = []
    first_aligned: dict[str, str] | None = None
    last_aligned: dict[str, str] | None = None
    timestamp_occurrences = 0
    timestamp_mismatch_records = 0
    hour_bucket_occurrences = 0
    hour_bucket_mismatch_records = 0
    invalid_hour_bucket_occurrences = 0
    candidate_count_mismatch_records = 0
    session_length_mismatch_records: Counter[str] = Counter()
    session_transitions: dict[str, Counter[tuple[str, str]]] = {
        key: Counter() for key in _SESSION_FEATURE_KEYS
    }

    def outer_time(record: Mapping[str, Any]) -> datetime:
        stamp = _utc_datetime(record.get("decision_time_utc"))
        if stamp is None:
            raise LaneRematerializationError("prepared_pack_decision_time_invalid")
        return stamp

    while old_record is not None or new_record is not None:
        if old_record is None:
            unmatched_new += 1
            if len(unmatched_examples) < 12:
                unmatched_examples.append(
                    {"side": "fresh_only", "decision_time_utc": str(new_record["decision_time_utc"])}
                )
            new_record = next(new_records, None)
            continue
        if new_record is None:
            unmatched_old += 1
            if len(unmatched_examples) < 12:
                unmatched_examples.append(
                    {"side": "frozen_only", "decision_time_utc": str(old_record["decision_time_utc"])}
                )
            old_record = next(old_records, None)
            continue
        physical_old = outer_time(old_record) - timedelta(hours=2)
        physical_new = outer_time(new_record)
        if physical_old < physical_new:
            unmatched_old += 1
            if len(unmatched_examples) < 12:
                unmatched_examples.append(
                    {"side": "frozen_only", "decision_time_utc": str(old_record["decision_time_utc"])}
                )
            old_record = next(old_records, None)
            continue
        if physical_new < physical_old:
            unmatched_new += 1
            if len(unmatched_examples) < 12:
                unmatched_examples.append(
                    {"side": "fresh_only", "decision_time_utc": str(new_record["decision_time_utc"])}
                )
            new_record = next(new_records, None)
            continue

        aligned += 1
        pair = {
            "frozen_label": str(old_record["decision_time_utc"]),
            "true_utc": str(new_record["decision_time_utc"]),
        }
        if first_aligned is None:
            first_aligned = pair
        last_aligned = pair
        old_census = _clock_feature_census(old_record)
        new_census = _clock_feature_census(new_record)

        expected_timestamps = Counter()
        for value in old_census["timestamps"]:
            parsed = _utc_datetime(value)
            if parsed is not None:
                expected_timestamps[(parsed - timedelta(hours=2)).isoformat()] += 1
        observed_timestamps = Counter(
            parsed.isoformat()
            for value in new_census["timestamps"]
            if (parsed := _utc_datetime(value)) is not None
        )
        timestamp_occurrences += sum(expected_timestamps.values())
        if expected_timestamps != observed_timestamps:
            timestamp_mismatch_records += 1

        expected_buckets: Counter[str] = Counter()
        for value in old_census["utc_hour_bucket"]:
            shifted = _shift_hour_token(value)
            if shifted is None:
                invalid_hour_bucket_occurrences += 1
            else:
                expected_buckets[shifted] += 1
        observed_buckets = Counter(new_census["utc_hour_bucket"])
        hour_bucket_occurrences += sum(expected_buckets.values())
        if expected_buckets != observed_buckets:
            hour_bucket_mismatch_records += 1

        old_candidates = sum(
            len(dict(symbol).get("candidates") or ())
            for symbol in old_record.get("symbols") or ()
        )
        new_candidates = sum(
            len(dict(symbol).get("candidates") or ())
            for symbol in new_record.get("symbols") or ()
        )
        if old_candidates != new_candidates:
            candidate_count_mismatch_records += 1

        for key in _SESSION_FEATURE_KEYS:
            old_values = old_census[key]
            new_values = new_census[key]
            if len(old_values) != len(new_values):
                session_length_mismatch_records[key] += 1
                continue
            session_transitions[key].update(zip(old_values, new_values, strict=True))

        old_record = next(old_records, None)
        new_record = next(new_records, None)

    timestamp_exact = timestamp_mismatch_records == 0
    bucket_exact = (
        hour_bucket_mismatch_records == 0 and invalid_hour_bucket_occurrences == 0
    )
    core = {
        "schema": FEATURE_SHIFT_SCHEMA,
        "status": (
            "JANUARY_PHYSICAL_FEATURES_SHIFT_EXACTLY_TWO_HOURS"
            if timestamp_exact and bucket_exact
            else "JANUARY_PHYSICAL_FEATURE_SHIFT_DIVERGED"
        ),
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "comparison_basis": (
            "physically aligned prepared windows: frozen decision label minus two hours "
            "equals the fresh true-UTC decision time"
        ),
        "aligned_record_count": aligned,
        "frozen_boundary_only_records": unmatched_old,
        "fresh_boundary_only_records": unmatched_new,
        "unmatched_examples": unmatched_examples,
        "first_aligned": first_aligned,
        "last_aligned": last_aligned,
        "timestamp_features": {
            "occurrences": timestamp_occurrences,
            "mismatched_record_count": timestamp_mismatch_records,
            "old_label_minus_true_utc_hours": 2,
            "exact": timestamp_exact,
        },
        "utc_hour_bucket": {
            "occurrences": hour_bucket_occurrences,
            "mismatched_record_count": hour_bucket_mismatch_records,
            "invalid_frozen_occurrences": invalid_hour_bucket_occurrences,
            "old_label_minus_true_utc_hours": 2,
            "exact": bucket_exact,
        },
        "candidate_generation": {
            "aligned_records_with_count_change": candidate_count_mismatch_records,
        },
        "configured_session_membership": {
            key: {
                "length_mismatch_records": session_length_mismatch_records[key],
                "changed_occurrences": sum(
                    count
                    for (old, new), count in session_transitions[key].items()
                    if old != new
                ),
                "transitions": [
                    {"frozen": old, "true_utc": new, "occurrences": count}
                    for (old, new), count in sorted(
                        session_transitions[key].items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                ],
            }
            for key in _SESSION_FEATURE_KEYS
        },
        "frozen_pack_authority_sha256": binding.get("authority_root_sha256"),
        "fresh_registry_root_sha256": inputs.registry["registry_root_sha256"],
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    receipt = {**core, "receipt_root_sha256": _stable_sha256(core)}
    receipt_path = (
        inputs.registry_path.parent
        / "receipts"
        / (
            "JANUARY_FEATURE_SHIFT_"
            f"{inputs.registry['registry_root_sha256'][:16]}.json"
        )
    )
    _write_json(receipt_path, receipt)
    if log_look:
        authorization = guard.authorize_window(
            start=inputs.window.start,
            end=inputs.window.end,
            purpose=guard.PURPOSE_LANE_ITERATION,
            context="lane_pack_feature_shift:january_2026",
        )
        lane.log_look(
            authorization=authorization,
            spec={
                "family": "true_utc_prepared_pack_feature_shift",
                "window_id": "january_2026",
                "aligned_record_count": aligned,
                "timestamp_exact": timestamp_exact,
                "utc_hour_bucket_exact": bucket_exact,
            },
            session="CJ",
            verdict="evaluated",
            note="Feature/provenance comparison only; no economic outcome read.",
            receipt=_repo_relative(receipt_path),
            engine_version=TRAIN_ENGINE_VERSION,
            mechanism="true_utc_lane_pack_feature_shift",
        )
    return receipt


def _physical_net_r(
    *, report: Mapping[str, Any], economics_authority: Mapping[str, Any]
) -> float:
    counts = dict(economics_authority.get("counts") or {})
    expected_counts = dict(report.get("economics_counts") or {})
    if counts != expected_counts:
        raise LaneRematerializationError("arm_economics_authority_count_mismatch")
    summary = dict(economics_authority.get("summary_economics") or {})
    raw = summary.get("split_profile_stats[0].physical_net_r")
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise LaneRematerializationError(
            "arm_economics_authority_physical_net_r_invalid"
        ) from exc


def capture_baseline_economics_authority(
    *,
    committed_report_path: Path,
    lane_receipt_path: Path,
    full_economics_path: Path,
) -> dict[str, Any]:
    """Preserve the small economic authority from a machine-local arm export.

    CD committed its complete runner report and pool summary, but its lane receipt
    and 178 MiB economics export remained machine-local.  Preserve the counts and
    realized physical net R with hashes of both original files; do not copy the
    bulky duplicate export into git.
    """

    report = json.loads(committed_report_path.read_text(encoding="utf-8"))
    lane_receipt = json.loads(lane_receipt_path.read_text(encoding="utf-8"))
    full_economics = json.loads(full_economics_path.read_text(encoding="utf-8"))
    if (
        report.get("arm") != "S0R0"
        or report.get("error") is not None
        or report.get("stop_after_day") is not None
        or lane_receipt.get("counts") != report.get("economics_counts")
        or full_economics.get("counts") != report.get("economics_counts")
        or lane_receipt.get("missed_opportunity_pool") != report.get("missed_digest")
        or full_economics.get("missed_digest") != report.get("missed_digest")
        or lane_receipt.get("fingerprint") != report.get("fingerprint")
        or full_economics.get("output_prefix") != report.get("output_prefix")
    ):
        raise LaneRematerializationError("baseline_economics_authority_mismatch")
    lane_summary = dict(lane_receipt.get("summary_economics") or {})
    full_summary = dict(full_economics.get("summary_economics") or {})
    if lane_summary != full_summary:
        raise LaneRematerializationError("baseline_economics_summary_mismatch")
    _physical_net_r(report=report, economics_authority=lane_receipt)
    core = {
        "schema": BASELINE_ECONOMICS_SCHEMA,
        "status": "BASELINE_ECONOMICS_AUTHORITY_PRESERVED",
        "arm": "S0R0",
        "window": ["2026-01-01", "2026-01-31"],
        "output_prefix": report["output_prefix"],
        "counts": dict(report["economics_counts"]),
        "missed_digest": dict(report["missed_digest"]),
        "summary_economics": lane_summary,
        "fingerprint_root_sha256": _stable_sha256(report["fingerprint"]),
        "source_authority": {
            "committed_report": _repo_relative(committed_report_path),
            "committed_report_sha256": _file_sha256(committed_report_path),
            "machine_local_lane_receipt_original_path": str(lane_receipt_path),
            "machine_local_lane_receipt_sha256": _file_sha256(lane_receipt_path),
            "machine_local_lane_receipt_bytes": lane_receipt_path.stat().st_size,
            "machine_local_full_economics_original_path": str(full_economics_path),
            "machine_local_full_economics_sha256": _file_sha256(full_economics_path),
            "machine_local_full_economics_bytes": full_economics_path.stat().st_size,
        },
        "cross_checks": {
            "counts_match_committed_report": True,
            "missed_digest_matches_committed_report": True,
            "fingerprint_matches_committed_report": True,
            "lane_and_full_economics_summaries_match": True,
        },
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def _pool_arm_metrics(
    *,
    report: Mapping[str, Any],
    pool: Mapping[str, Any],
    economics_authority: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cost = dict(pool.get("cost") or {})
    gross = dict(pool.get("gross") or {})
    report_counts = dict(report.get("economics_counts") or {})
    missed = dict(report.get("missed_digest") or {})
    metrics = {
        "candidate_rows": int((report.get("receipt_counts") or {}).get("candidate_rows") or 0),
        "missed_physical_rows": int(missed.get("rows") or 0),
        "diagnostic_scoreable_rows": int(pool.get("diagnostic_scoreable_rows") or 0),
        "trade_rows": int(report_counts.get("trade") or 0),
        "order_rows": int(report_counts.get("order") or 0),
        "scorecard_rows": int(report_counts.get("scorecard") or 0),
        "pool_net_r": float(pool.get("net_r") or 0.0),
        "pool_mean_r_per_scoreable_row": float(pool.get("mean_r_per_row") or 0.0),
        "gross_mean_r_per_scoreable_row": float(gross.get("mean_gross_r") or 0.0),
        "cost_mean_r_per_scoreable_row": float(cost.get("mean_cost_r") or 0.0),
        "commission_mean_r": float(
            (cost.get("components_mean_r") or {}).get("commission_r") or 0.0
        ),
        "spread_mean_r": float(
            (cost.get("components_mean_r") or {}).get("spread_r") or 0.0
        ),
        "slippage_mean_r": float(
            (cost.get("components_mean_r") or {}).get("expected_slippage_r") or 0.0
        ),
        "swap_mean_r": float(
            (cost.get("components_mean_r") or {}).get("swap_cost_r") or 0.0
        ),
        "negative_days": int(pool.get("n_days_negative") or 0),
        "day_count": int(pool.get("n_days") or 0),
    }
    if economics_authority is not None:
        metrics["physical_net_r"] = _physical_net_r(
            report=report, economics_authority=economics_authority
        )
    return metrics


def compare_january_arm_economics(
    *,
    candidate_report_path: Path,
    candidate_pool_summary_path: Path,
    baseline_report_path: Path = CD_S0R0_REPORT,
    baseline_pool_summary_path: Path = CD_S0R0_POOL_SUMMARY,
    baseline_economics_authority_path: Path | None = None,
    candidate_economics_authority_path: Path | None = None,
) -> dict[str, Any]:
    """Compare one re-clocked January S0R0 arm with CD's repaired S0R0 arm."""

    baseline_report = json.loads(baseline_report_path.read_text(encoding="utf-8"))
    candidate_report = json.loads(candidate_report_path.read_text(encoding="utf-8"))
    baseline_pool = json.loads(
        baseline_pool_summary_path.read_text(encoding="utf-8")
    )
    candidate_pool = json.loads(
        candidate_pool_summary_path.read_text(encoding="utf-8")
    )
    if (baseline_economics_authority_path is None) != (
        candidate_economics_authority_path is None
    ):
        raise LaneRematerializationError(
            "january_arm_economics_authorities_must_be_paired"
        )
    baseline_economics = (
        json.loads(baseline_economics_authority_path.read_text(encoding="utf-8"))
        if baseline_economics_authority_path is not None
        else None
    )
    candidate_economics = (
        json.loads(candidate_economics_authority_path.read_text(encoding="utf-8"))
        if candidate_economics_authority_path is not None
        else None
    )
    if (
        baseline_report.get("arm") != "S0R0"
        or candidate_report.get("arm") != "S0R0"
        or baseline_report.get("stop_after_day") is not None
        or candidate_report.get("stop_after_day") is not None
        or candidate_report.get("purpose") != guard.PURPOSE_LANE_ITERATION
        or candidate_report.get("error") is not None
        or (candidate_report.get("lane_input_authority") or {}).get("campaign_sealed")
        is not False
    ):
        raise LaneRematerializationError("january_arm_comparison_contract_invalid")

    baseline = _pool_arm_metrics(
        report=baseline_report,
        pool=baseline_pool,
        economics_authority=baseline_economics,
    )
    candidate = _pool_arm_metrics(
        report=candidate_report,
        pool=candidate_pool,
        economics_authority=candidate_economics,
    )
    count_fields = (
        "candidate_rows",
        "missed_physical_rows",
        "diagnostic_scoreable_rows",
        "trade_rows",
        "order_rows",
        "scorecard_rows",
        "negative_days",
        "day_count",
    )
    numeric_fields = tuple(key for key in baseline if key not in count_fields)
    count_deltas = {
        key: int(candidate[key]) - int(baseline[key]) for key in count_fields
    }
    numeric_deltas = {
        key: round(float(candidate[key]) - float(baseline[key]), 12)
        for key in numeric_fields
    }
    strict_tolerance_r = 1e-8
    strict_invariant = all(delta == 0 for delta in count_deltas.values()) and all(
        abs(delta) <= strict_tolerance_r for delta in numeric_deltas.values()
    )

    # Declared here, before the regenerated arm is inspected. A full trade-set
    # change is decision-material; a pool move needs either 0.01 R/row or a 1%
    # denominator change to receive the stronger economic-materiality label.
    materiality = {
        "absolute_mean_r_per_scoreable_row": 0.01,
        "absolute_gross_r_per_scoreable_row": 0.01,
        "relative_scoreable_row_count": 0.01,
        "any_trade_count_change": True,
        "physical_net_r": "strict_1e-8_comparison; no post-hoc material threshold",
    }
    reasons: list[str] = []
    if abs(numeric_deltas["pool_mean_r_per_scoreable_row"]) >= 0.01:
        reasons.append("pool_mean_r_per_scoreable_row_moved_at_least_0p01")
    if abs(numeric_deltas["gross_mean_r_per_scoreable_row"]) >= 0.01:
        reasons.append("gross_mean_r_per_scoreable_row_moved_at_least_0p01")
    baseline_scoreable = max(int(baseline["diagnostic_scoreable_rows"]), 1)
    if abs(count_deltas["diagnostic_scoreable_rows"]) / baseline_scoreable >= 0.01:
        reasons.append("diagnostic_scoreable_row_count_moved_at_least_1pct")
    if count_deltas["trade_rows"] != 0:
        reasons.append("trade_count_changed")

    if strict_invariant:
        status = "JANUARY_RECLOCKED_ECONOMICS_INVARIANT"
    elif reasons:
        status = "JANUARY_RECLOCKED_ECONOMICS_MOVED_MATERIALLY"
    else:
        status = "JANUARY_RECLOCKED_ECONOMICS_MOVED_BELOW_MATERIALITY"
    core = {
        "schema": ARM_INVARIANCE_SCHEMA,
        "status": status,
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "arm": "S0R0",
        "window": ["2026-01-01", "2026-01-31"],
        "baseline": baseline,
        "candidate": candidate,
        "count_deltas": count_deltas,
        "numeric_deltas": numeric_deltas,
        "strict_invariance_tolerance_r": strict_tolerance_r,
        "strict_invariant": strict_invariant,
        "materiality_definition": materiality,
        "material_movement_reasons": reasons,
        "session_conditioned_pipeline_finding": not strict_invariant,
        "baseline_authority": {
            "report": _repo_relative(baseline_report_path),
            "report_sha256": _file_sha256(baseline_report_path),
            "pool_summary": _repo_relative(baseline_pool_summary_path),
            "pool_summary_sha256": _file_sha256(baseline_pool_summary_path),
            **(
                {
                    "economics_authority": _repo_relative(
                        baseline_economics_authority_path
                    ),
                    "economics_authority_sha256": _file_sha256(
                        baseline_economics_authority_path
                    ),
                }
                if baseline_economics_authority_path is not None
                else {}
            ),
        },
        "candidate_authority": {
            "report": _repo_relative(candidate_report_path),
            "report_sha256": _file_sha256(candidate_report_path),
            "pool_summary": _repo_relative(candidate_pool_summary_path),
            "pool_summary_sha256": _file_sha256(candidate_pool_summary_path),
            **(
                {
                    "economics_authority": _repo_relative(
                        candidate_economics_authority_path
                    ),
                    "economics_authority_sha256": _file_sha256(
                        candidate_economics_authority_path
                    ),
                }
                if candidate_economics_authority_path is not None
                else {}
            ),
            "lane_input_authority": candidate_report["lane_input_authority"],
        },
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_january(
    *, registry_path: Path, frozen_legacy_root: Path = FROZEN_JANUARY_LEGACY
) -> dict[str, Any]:
    """Prove the repaired January source is clock-only relative to frozen bytes."""

    inputs = LaneInputRegistry(registry_path).resolve(
        window_id="january_2026", purpose=guard.PURPOSE_LANE_ITERATION
    )
    manifest = inputs.source_manifest
    entries = {
        (str(row["symbol"]), str(row["timeframe"])): dict(row)
        for row in manifest["bar_sources"]
    }
    file_results: list[dict[str, Any]] = []
    total_overlap = 0
    offsets: set[float] = set()
    payload_residuals = 0
    for frozen in sorted(frozen_legacy_root.glob("*.csv")):
        stem = frozen.stem.split("_", 1)[1]
        symbol, timeframe = stem.rsplit("_", 1)
        entry = entries.get((symbol, timeframe))
        if entry is None:
            raise LaneRematerializationError(
                f"january_overlap_source_missing:{symbol}:{timeframe}"
            )
        repaired = REPO_ROOT / str(entry["repo_relpath"])
        old_rows = _load_csv(frozen)
        new_rows = _load_csv(repaired)
        if len(old_rows) != len(new_rows):
            raise LaneRematerializationError(
                f"january_overlap_row_count_changed:{frozen.name}"
            )
        overlap = 0
        local_offsets: set[float] = set()
        local_residuals = 0
        for old, new in zip(old_rows, new_rows, strict=True):
            old_payload = {key: value for key, value in old.items() if key != "time"}
            new_payload = {key: value for key, value in new.items() if key != "time"}
            if old_payload != new_payload:
                local_residuals += 1
                continue
            old_label = datetime.fromisoformat(old["time"]).replace(tzinfo=timezone.utc)
            true_utc = datetime.fromisoformat(new["time"]).astimezone(timezone.utc)
            if inputs.window.start_utc <= true_utc < inputs.window.end_exclusive_utc:
                delta = (old_label - true_utc).total_seconds() / 3600.0
                local_offsets.add(delta)
                overlap += 1
        if local_residuals or (overlap and local_offsets != {2.0}):
            raise LaneRematerializationError(
                f"january_overlap_nonuniform_residual:{frozen.name}:"
                f"offsets={sorted(local_offsets)}:payload={local_residuals}"
            )
        total_overlap += overlap
        offsets.update(local_offsets)
        payload_residuals += local_residuals
        file_results.append(
            {
                "frozen_file": frozen.name,
                "repaired_repo_relpath": entry["repo_relpath"],
                "full_row_count": len(old_rows),
                "january_overlap_rows": overlap,
                "old_label_minus_true_utc_hours": sorted(local_offsets),
                "non_time_residual_rows": local_residuals,
            }
        )
    if len(file_results) != 96 or offsets != {2.0} or payload_residuals != 0:
        raise LaneRematerializationError("january_overlap_gate_failed")

    audusd = REPO_ROOT / entries[("AUDUSD", "M15")]["repo_relpath"]
    old_audusd = next(frozen_legacy_root.glob("*_AUDUSD_M15.csv"))
    old_rows = _load_csv(old_audusd)
    new_rows = _load_csv(audusd)
    weekly: list[dict[str, Any]] = []
    for old, new in zip(old_rows, new_rows, strict=True):
        old_stamp = datetime.fromisoformat(old["time"])
        if old_stamp.weekday() != 0 or old_stamp.time() != datetime.min.time():
            continue
        true_utc = datetime.fromisoformat(new["time"]).astimezone(timezone.utc)
        daylight = UsDstAnchor.is_daylight(true_utc)
        expected_hour = 21 if daylight else 22
        valid = true_utc.weekday() == 6 and true_utc.hour == expected_hour
        weekly.append(
            {
                "old_broker_label": old["time"],
                "true_utc": true_utc.isoformat(),
                "us_daylight": daylight,
                "expected_true_utc_hour": expected_hour,
                "new_york_market_anchor": "Sunday 17:00",
                "valid": valid,
            }
        )
    if len(weekly) != 54 or not all(row["valid"] for row in weekly):
        raise LaneRematerializationError(
            f"january_weekly_open_gate_failed:{sum(row['valid'] for row in weekly)}/{len(weekly)}"
        )
    core = {
        "schema": VALIDATION_SCHEMA,
        "status": "LANE_TRUE_UTC_JANUARY_VALID",
        "campaign_sealed": False,
        "evidence_class": LANE_EVIDENCE,
        "source_manifest_root_sha256": manifest["manifest_root_sha256"],
        "weekly_open_check": {
            "valid": 54,
            "total": 54,
            "winter_true_utc": "Sunday 22:00 UTC",
            "daylight_true_utc": "Sunday 21:00 UTC",
            "dst_invariant_anchor": "Sunday 17:00 America/New_York",
            "rows": weekly,
        },
        "bar_overlap_check": {
            "frozen_file_count": 96,
            "repaired_file_count": 96,
            "january_overlap_rows": total_overlap,
            "old_label_minus_true_utc_hours": sorted(offsets),
            "non_time_residual_rows": payload_residuals,
            "files": file_results,
        },
        "economic_outcomes_read": False,
        "march_outcomes_read": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def hour_correction_table() -> dict[str, Any]:
    rows = []
    for old_hour in range(24):
        true_hour = (old_hour - 2) % 24
        rows.append(
            {
                "sealed_january_old_label": f"{old_hour:02d}:00",
                "true_utc_label": f"{true_hour:02d}:00",
                "day_delta": -1 if old_hour < 2 else 0,
                "old_label_minus_true_utc_hours": 2,
            }
        )
    aw_map_path = (
        REPO_ROOT
        / "docs/audits/fable5-vision-audit-20260725/phase12/receipts/"
        "AW_SEPARABILITY_MAP_V1.json"
    )
    aw_cells: list[Mapping[str, Any]] = []
    if aw_map_path.is_file():
        aw_payload = json.loads(aw_map_path.read_text(encoding="utf-8"))
        aw_cells = [
            row
            for row in aw_payload.get("cells") or ()
            if isinstance(row, Mapping) and row.get("axis_family") == "B_TIME"
        ]
    core = {
        "schema": "gtos.lane.rematerialization.hour_axis_correction.v1",
        "status": "SEALED_JANUARY_HOUR_LABEL_CORRECTION_DECLARED",
        "scope": "January 2026 broker-wall labels formerly presented as UTC",
        "direction": "true_utc = old_label - 2 hours",
        "inverse_wording": "old sealed label is +2 hours ahead of true UTC",
        "rows": rows,
        "estate_impact": {
            "aw_b_time": {
                "result_document_cell_count": 81,
                "committed_map_cell_count": len(aw_cells),
                "committed_map_axis_counts": {
                    axis: sum(1 for row in aw_cells if row.get("axis") == axis)
                    for axis in sorted({str(row.get("axis")) for row in aw_cells})
                },
                "correction": (
                    "hour labels move by this table; session and day memberships must be "
                    "regenerated because the 00/01 broker labels cross a true-UTC day boundary"
                ),
                "economic_verdict": "deferred_to_CJ_regenerated_January_arm",
            },
            "ah_entry_hour": {
                "axis": "broker_server_hour",
                "correction": "none",
                "reason": (
                    "AH states broker hour 00 and moves to broker hour 04; it does not claim "
                    "those labels are UTC"
                ),
            },
            "ce_entry_hour": {
                "axis": "broker_server_hour",
                "correction": "none",
                "reason": (
                    "CE's implemented deferral is broker 00 to broker 01 and resolves the "
                    "registered broker clock explicitly"
                ),
            },
            "ch_jpy_gate": {
                "axis": "broker_server_hour",
                "correction": "none_to_declared_axis",
                "reason": (
                    "CH's commission asks for the ratified one-hour-off-rollover broker-hour "
                    "gate; no completed CH result document was present when this receipt was built"
                ),
            },
        },
        "economics_changed_by_table": False,
        "march_outcomes_read": False,
    }
    return {**core, "receipt_root_sha256": _stable_sha256(core)}


def _emit(payload: Mapping[str, Any], output: Path | None) -> None:
    if output is not None:
        _write_json(output, payload)
    print(json.dumps(payload, indent=1, sort_keys=True, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    materialize = sub.add_parser("materialize", help="offline true-UTC source materialization")
    materialize.add_argument("--lane-root", type=Path, default=DEFAULT_LANE_ROOT)
    materialize.add_argument("--out", type=Path)

    march = sub.add_parser(
        "materialize-march",
        help=(
            "extend an existing lane root with the march_2026 window "
            "(MARCH_PREREG_V1 one-shot; requires the arming environment)"
        ),
    )
    march.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    march.add_argument("--out", type=Path)

    extension = sub.add_parser(
        "materialize-window",
        help=(
            "extend an existing lane root with one LANE_EXTENSION_WINDOW_IDS "
            "window (2025 calendar; outcome-blind, no one-shot involved)"
        ),
    )
    extension.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    extension.add_argument(
        "--window", choices=tuple(LANE_EXTENSION_WINDOW_IDS), required=True
    )
    extension.add_argument("--out", type=Path)

    unregister = sub.add_parser(
        "unregister-window",
        help=(
            "remove an extension window whose packs are NOT built (the "
            "'never register a partial window' rule needs an undo)"
        ),
    )
    unregister.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    unregister.add_argument(
        "--window", choices=tuple(LANE_EXTENSION_WINDOW_IDS), required=True
    )
    unregister.add_argument("--out", type=Path)

    validate = sub.add_parser("validate-january", help="54/54 + clock-only overlap gates")
    validate.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    validate.add_argument("--out", type=Path)

    packs = sub.add_parser("build-packs", help="build one window's per-day prepared packs")
    packs.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    packs.add_argument("--window", choices=tuple(WINDOWS), required=True)
    packs.add_argument("--encoding-workers", type=int, default=1)
    packs.add_argument(
        "--successor-tag",
        help="build a new immutable pack root and atomically repoint the registry",
    )
    packs.add_argument("--no-log", action="store_true")
    packs.add_argument("--out", type=Path)

    source_plan = sub.add_parser(
        "bind-source-plan",
        help="bind the engine-recomputed canonical plan for one LANE window",
    )
    source_plan.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    source_plan.add_argument("--window", choices=tuple(WINDOWS), required=True)
    source_plan.add_argument("--no-log", action="store_true")
    source_plan.add_argument("--out", type=Path)

    inspect_plan = sub.add_parser(
        "inspect-source-plan",
        help=(
            "compute a canonical plan into a read-only sidecar without "
            "mutating the registry"
        ),
    )
    inspect_plan.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    inspect_plan.add_argument("--window", choices=tuple(WINDOWS), required=True)
    inspect_plan.add_argument(
        "--stop-after-day",
        help="inspect a read-only prefix and bind its own canonical source-plan digest",
    )
    inspect_plan.add_argument("--out", type=Path)

    smoke = sub.add_parser("smoke-pack", help="authenticate and load one prepared window")
    smoke.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    smoke.add_argument("--window", choices=tuple(WINDOWS), required=True)
    smoke.add_argument("--no-log", action="store_true")
    smoke.add_argument("--out", type=Path)

    features = sub.add_parser(
        "compare-features",
        help="measure January's physical two-hour pack-feature shift",
    )
    features.add_argument(
        "--registry", type=Path, default=DEFAULT_LANE_ROOT / DEFAULT_REGISTRY_NAME
    )
    features.add_argument("--no-log", action="store_true")
    features.add_argument("--out", type=Path)

    arm = sub.add_parser(
        "compare-arm",
        help="compare one full re-clocked January S0R0 arm with CD's baseline",
    )
    arm.add_argument("--candidate-report", type=Path, required=True)
    arm.add_argument("--candidate-pool-summary", type=Path, required=True)
    arm.add_argument("--baseline-economics-authority", type=Path)
    arm.add_argument("--candidate-economics-authority", type=Path)
    arm.add_argument("--out", type=Path)

    baseline = sub.add_parser(
        "capture-baseline-economics",
        help="preserve CD's small economic summary from machine-local exports",
    )
    baseline.add_argument(
        "--committed-report", type=Path, default=CD_S0R0_REPORT
    )
    baseline.add_argument("--lane-receipt", type=Path, required=True)
    baseline.add_argument("--full-economics", type=Path, required=True)
    baseline.add_argument("--out", type=Path)

    hours = sub.add_parser("hour-table", help="emit the old-label -> true-UTC table")
    hours.add_argument("--out", type=Path)

    ns = parser.parse_args()
    if ns.command == "materialize":
        payload = materialize_sources(lane_root=ns.lane_root)
    elif ns.command == "materialize-march":
        payload = materialize_march_sources(registry_path=ns.registry)
    elif ns.command == "materialize-window":
        payload = materialize_lane_window_sources(
            registry_path=ns.registry, window_id=ns.window
        )
    elif ns.command == "unregister-window":
        payload = unregister_lane_window_sources(
            registry_path=ns.registry, window_id=ns.window
        )
    elif ns.command == "validate-january":
        payload = validate_january(registry_path=ns.registry)
    elif ns.command == "build-packs":
        payload = build_packs(
            registry_path=ns.registry,
            window_id=ns.window,
            encoding_workers=ns.encoding_workers,
            log_look=not ns.no_log,
            successor_tag=ns.successor_tag,
        )
    elif ns.command == "bind-source-plan":
        payload = bind_canonical_source_plan(
            registry_path=ns.registry,
            window_id=ns.window,
            log_look=not ns.no_log,
        )
    elif ns.command == "inspect-source-plan":
        payload = inspect_canonical_source_plan(
            registry_path=ns.registry,
            window_id=ns.window,
            stop_after_day=ns.stop_after_day,
        )
    elif ns.command == "smoke-pack":
        payload = smoke_pack(
            registry_path=ns.registry,
            window_id=ns.window,
            log_look=not ns.no_log,
        )
    elif ns.command == "compare-features":
        payload = compare_january_pack_features(
            registry_path=ns.registry,
            log_look=not ns.no_log,
        )
    elif ns.command == "compare-arm":
        payload = compare_january_arm_economics(
            candidate_report_path=ns.candidate_report,
            candidate_pool_summary_path=ns.candidate_pool_summary,
            baseline_economics_authority_path=ns.baseline_economics_authority,
            candidate_economics_authority_path=ns.candidate_economics_authority,
        )
    elif ns.command == "capture-baseline-economics":
        payload = capture_baseline_economics_authority(
            committed_report_path=ns.committed_report,
            lane_receipt_path=ns.lane_receipt,
            full_economics_path=ns.full_economics,
        )
    else:
        payload = hour_correction_table()
    _emit(payload, ns.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
