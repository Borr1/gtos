"""One-shot, broker-inert P1 offline complete-path runner.

The public boundary is deliberately split in two.  ``preflight`` may inspect only
source/control projections and opaque file bindings.  ``run`` is default-off and
is the only boundary allowed to decode fill, exit, cost, or economic fields after
an independent audit has frozen the exact source commit.

Nothing in this module contacts a broker, runtime, network, or production service.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import csv
import ctypes
import errno
import gzip
import hashlib
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import types
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from array import array
from typing import Any, Iterable, Iterator, Mapping, Sequence

from src.components.current_breaker_re_entry_repair import (
    ORIGIN_FAMILY,
    STOP_DISTANCE_D,
    TRANSFORM_ID,
    apply_current_breaker_re_entry_repair,
)
from src.research_infra.exit_overlay import (
    ExitOverlaySpec,
    ExitPathPoint,
    SignedM1Bar,
    replay_m1_conservative,
    replay_signed_path,
    true_utc_tick_time_us,
)
from src.research_infra.p1_upstream_packet_verifier import (
    VerificationError,
    project_pool_control_json,
    strict_json_loads,
    verify_packet,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SOURCE_COMMIT = "9059cfa0659f710dc56ba779181770468d5450f1"
BASE_SOURCE_PARENT = "f59fbb829a5561b7e7b78bed324d67a8c01d6e74"
CANONICAL_EVIDENCE_COMMIT = "502d906167cd85a84720f1777454cd9ccb7abc64"
HN_EVIDENCE_COMMIT = "97d4c7da1d67314e1474225b5d8484d782e5750e"
CANONICAL_EVIDENCE_PATHS = frozenset(
    {
        "docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HP_CONTEXT_ANCHOR.md",
        "docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HP_P1_UPSTREAM_FALSIFIER_REDUCTION_RESULT.md",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HP_AB_RECEIPT.md",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HP_COMPLETE.json",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_M1_PROVENANCE.json",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_PACKET_ADVERSARIAL_MATRIX.json",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_PACKET_INDEPENDENT_FALSIFICATION.json",
    }
)
PACKET = Path(
    "/Users/borr/GTOSActive/p1-upstream-source-packet-canonical-hold-20260802/"
    "p1-source-packet-sha256-e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f"
)
PACKET_MANIFEST_SHA256 = "70f4c5dde50774f34e248b9d56af604b827c165bea5f76eb8f4a9ad0bc52cbf2"
PACKET_PAYLOAD_ROOT_SHA256 = "e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f"
SOURCE_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
OUTPUT_PARENT = Path("/Users/borr/GTOSActive/p1-offline-result-hold-20260802")
PREREGISTRATION_PATH = REPO_ROOT / (
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/"
    "P1_FILL_AUTHORITY_PREREGISTRATION.json"
)
ADAPTER_RELATIVE = (
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/"
    "wave20_complete_path_shadow.py"
)
ADAPTER_SHA256 = "4512f15f82b81dc1fb52d65d1c68e71929de3d95e683f80ce990e2121c1d9dd4"
ADAPTER_BYTES = 47_434
HN_PROFILE_RELATIVE = (
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/"
    "P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json"
)
HN_PROFILE_SHA256 = "47fe19e1743a83ffd69fcb0c7948a76e8a2ac0ac1d7c5561996d1306f04e0d8a"
HN_PROFILE_BYTES = 40_171
HN_ROUTE_RELATIVE = (
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/"
    "P1_INERT_ROUTE_PARAMETER_BUNDLE.json"
)
HN_ROUTE_SHA256 = "988a139e21bf8621a84ddafbfaff4cd9dfb39bcebf2ab6d9d228d9ffdffa4b52"
HN_ROUTE_BYTES = 12_265

FIXED_CANDIDATE = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
ORDER_TYPE = "INTERNAL_SOFTWARE_LIMIT_INTENT_WITH_MARKET_ON_TRIGGER"
CANCELLATION_POLICY = "NONE_CAPTURE_ONLY"
EXIT_VARIANT_ID = "p1_fixed_breaker_minus1_plus20_timebox_v1"
HORIZON_MINUTES = 120
EXPECTED_TOTAL = 73_999
EXPECTED_FAMILY = 11_305
EXPECTED_NON_FAMILY = 62_694
EXPECTED_STAGE_ROWS = 813_989
EXPECTED_WINDOWS = {"january": 27_658, "april": 25_056, "may": 21_285}
EXPECTED_FAMILY_WINDOWS = {"january": 4_263, "april": 3_671, "may": 3_371}
EXPECTED_AUTHORITY = {"FULL_TICK": 492, "M1_ONLY": 10_810, "PATH_START_GAP": 3}
IDENTITY_FIELDS = ("candidate_id", "symbol", "side", "decision_time_utc")
STAGES = (
    "source_opportunity",
    "candidate_generation",
    "fixed_breaker_transform",
    "permission",
    "dynamic_router",
    "scheduler_capture_only",
    "order_preimage",
    "fill_or_no_fill",
    "hde_cost",
    "hdf_exit_or_terminal",
    "unchanged_frozen_gate_disposition",
)
POOL_BINDINGS = (
    (
        "january",
        "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/"
        "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
        "ee920fb0e28713f28cf85322d6b6494beef07c27235db9e6ba59dd6e5097fc8f",
        5_696_917,
    ),
    (
        "april",
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_APRIL_S0R0_POOL_V1.jsonl.gz",
        "d587e99ebdbc0f56b3501719e05dfec45902e9013ee8c32392e344bc51c9e4d9",
        5_504_482,
    ),
    (
        "may",
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_MAY_S0R0_POOL_V1.jsonl.gz",
        "1bba6662644d0424ff5a360f987ddd81bb1b0f176b7547b6626853d166cb5633",
        4_600_824,
    ),
)
SIDECAR_BINDINGS = {
    "january": (
        "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/"
        "CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        "ffa2a2151e79ab81202fab07706f859579e453e0b00784c1e69b381903e9ba61",
        34_134_117,
    ),
    "april": (
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_APRIL_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        "eccadb15d5e6a3a97b178b2e3267b79e5792feeca49f61c157ba86bca05ad2cd",
        30_817_431,
    ),
    "may": (
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_MAY_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz",
        "bdab3988ce6960a6e25b29a29ca4bd1498698c0495222191c34e00c0d6baf5b4",
        26_415_775,
    ),
}
PATH_MANIFEST_BINDINGS = {
    "january": (
        "docs/audits/fable5-vision-audit-20260725/phase18/receipts/"
        "CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json",
        "87e8a086565ef9a2fd20aca55b4ed575dc48cbd5f07bcf3ade2ada74f9882c85",
        9_647,
    ),
    "april": (
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
        "CS_APRIL_PATH_POOL_V1.json",
        "5fc38c24746763d943619f6b8b6e3ac9ffa64b34cbe0a8fb73a024556c88e102",
        10_147,
    ),
    "may": (
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/"
        "CS_MAY_PATH_POOL_V1.json",
        "803cf08ce72f0ce6745f92f8b02a08ba796f51707fc98a611c57f8ab61d6c1e5",
        9_371,
    ),
}
LANE_MANIFEST_BINDINGS = {
    "january": (
        "manifests/january_2026.json",
        "74ee97e4d379854697920abd7a4ee22693dc2ab72b922e0756b1342053fa5fbc",
        97_175,
    ),
    "april": (
        "manifests/april_2026.json",
        "3940c286fed76489bc748cb58453f5172bd32da69c7900df2b5454ac34723344",
        97_320,
    ),
    "may": (
        "manifests/may_2026.json",
        "23ebf0592746c55811a5457d3d120460c80ed317c8a5a51637be4579238edf7f",
        92_799,
    ),
}
COMMISSIONED_PATHS = frozenset(
    {
        "src/research_infra/p1_offline_complete_path_runner.py",
        "tests/research_infra/test_p1_offline_complete_path_runner.py",
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/"
        "P1_FILL_AUTHORITY_PREREGISTRATION.json",
    }
)
FORBIDDEN_IMPORTS = (
    "MetaTrader5",
    "src.mt5.mt5_real",
    "src.components.execution",
    "src.components.orchestrator",
)
UK100_GAPS = frozenset(
    {
        "2026-01-02T00:15:00+00:00",
        "2026-01-02T00:30:00+00:00",
        "2026-01-02T00:45:00+00:00",
    }
)

MECHANICAL_SYMBOL_FIELDS = frozenset(
    {
        "mt5_symbol",
        "digits",
        "point",
        "tick_size",
        "trade_tick_size",
        "execution_mode",
        "filling_mode",
        "order_mode",
        "trade_mode",
        "trade_stops_level",
        "trade_freeze_level",
    }
)
REQUIRED_MECHANICAL_SYMBOL_FIELDS = frozenset(
    {
        "mt5_symbol",
        "digits",
        "point",
        "tick_size",
        "trade_tick_size",
        "trade_mode",
        "trade_stops_level",
        "trade_freeze_level",
    }
)
PROFILE_NAMES = ("operator_profile", "redacted_account")
CANDIDATE_PREDECISION_FIELDS = frozenset(
    {
        "candidate_id",
        "symbol",
        "side",
        "direction",
        "decision_time_utc",
        "origin_family",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "risk_reward_ratio",
        "rr",
        "predecision_features",
        "source_fields",
    }
)
OUTPUT_BYTE_LIMIT = 4 * 1024**3
FREE_DISK_FLOOR = 8 * 1024**3
PERMISSION_EVIDENCE_CLASS = "SYNTHETIC/PREREGISTERED_NOT_HISTORICAL"


class P1RunnerRefusal(RuntimeError):
    """A frozen authority, safety, or completeness invariant did not hold."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_json(payload: str | bytes, *, label: str) -> Any:
    try:
        return strict_json_loads(payload, label=label)
    except VerificationError as exc:
        raise P1RunnerRefusal(str(exc)) from exc


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _lexically_contained(path: Path, root: Path) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    root_absolute = Path(os.path.abspath(os.fspath(root)))
    try:
        absolute.relative_to(root_absolute)
    except ValueError as exc:
        raise P1RunnerRefusal(f"path_escape:{path}:{root}") from exc


def _reject_symlink_components(path: Path, *, allow_missing_leaf: bool = False) -> None:
    """Use lexical lstat before resolve/open; reject ancestor and leaf symlinks."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    cursor = Path(absolute.anchor)
    for index, part in enumerate(absolute.parts[1:]):
        cursor = cursor / part
        try:
            info = os.lstat(cursor)
        except FileNotFoundError:
            if allow_missing_leaf and index == len(absolute.parts[1:]) - 1:
                return
            raise P1RunnerRefusal(f"path_component_missing:{cursor}")
        if stat.S_ISLNK(info.st_mode):
            raise P1RunnerRefusal(f"symlink_component_refused:{cursor}")


def _open_regular_fd(path: Path, *, root: Path) -> tuple[int, os.stat_result]:
    _lexically_contained(path, root)
    _reject_symlink_components(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        os.close(fd)
        raise P1RunnerRefusal(f"bound_path_not_regular:{path}")
    return fd, info


def _verify_same_inode(path: Path, fd: int, before: os.stat_result) -> None:
    after = os.fstat(fd)
    current = os.lstat(path)
    identity_before = (before.st_dev, before.st_ino, before.st_size)
    identity_after = (after.st_dev, after.st_ino, after.st_size)
    identity_path = (current.st_dev, current.st_ino, current.st_size)
    if identity_after != identity_before or identity_path != identity_before:
        raise P1RunnerRefusal(f"bound_file_toctou_or_size_drift:{path}")


def _read_bound_bytes(
    path: Path, *, root: Path, digest: str, size: int | None = None
) -> bytes:
    fd, before = _open_regular_fd(path, root=root)
    try:
        chunks: list[bytes] = []
        hasher = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                chunks.append(chunk)
                hasher.update(chunk)
        _verify_same_inode(path, fd, before)
    finally:
        os.close(fd)
    payload = b"".join(chunks)
    if (size is not None and len(payload) != size) or hasher.hexdigest() != digest:
        raise P1RunnerRefusal(f"bound_file_hash_or_size_drift:{path}")
    return payload


def _read_stable_bytes(path: Path, *, root: Path) -> tuple[bytes, str]:
    """Read and hash from one regular-file descriptor, then recheck its inode."""
    fd, before = _open_regular_fd(path, root=root)
    try:
        chunks: list[bytes] = []
        hasher = hashlib.sha256()
        with os.fdopen(fd, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                chunks.append(chunk)
                hasher.update(chunk)
        _verify_same_inode(path, fd, before)
    finally:
        os.close(fd)
    return b"".join(chunks), hasher.hexdigest()


def _git_blob(commit: str, path: str, *, digest: str, size: int) -> bytes:
    """Read only one of the three immutable, predeclared authority blobs."""
    allowed = {
        (CANONICAL_EVIDENCE_COMMIT, ADAPTER_RELATIVE, ADAPTER_SHA256, ADAPTER_BYTES),
        (HN_EVIDENCE_COMMIT, HN_PROFILE_RELATIVE, HN_PROFILE_SHA256, HN_PROFILE_BYTES),
        (HN_EVIDENCE_COMMIT, HN_ROUTE_RELATIVE, HN_ROUTE_SHA256, HN_ROUTE_BYTES),
    }
    if (commit, path, digest, size) not in allowed:
        raise P1RunnerRefusal("git_blob_not_in_frozen_allowlist")
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = result.stdout
    if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
        raise P1RunnerRefusal(f"git_blob_hash_or_size_drift:{commit}:{path}")
    return payload


def parse_utc(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("+00:00"):
        raise P1RunnerRefusal(f"true_utc_required:{label}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise P1RunnerRefusal(f"utc_invalid:{label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise P1RunnerRefusal(f"true_utc_required:{label}")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def strict_number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise P1RunnerRefusal(f"numeric_required:{label}")
    number = float(value)
    if not math.isfinite(number):
        raise P1RunnerRefusal(f"finite_required:{label}")
    return number


@dataclass(frozen=True)
class CompositeIdentity:
    candidate_id: str
    symbol: str
    side: str
    decision_time_utc: str

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "CompositeIdentity":
        candidate_id = str(row.get("candidate_id") or "")
        symbol = str(row.get("symbol") or "")
        side = str(row.get("side") or "").upper()
        decision = iso_utc(parse_utc(row.get("decision_time_utc"), label="decision_time_utc"))
        if not candidate_id or not symbol or side not in {"LONG", "SHORT"}:
            raise P1RunnerRefusal("composite_identity_invalid")
        return cls(candidate_id, symbol, side, decision)

    def key(self) -> tuple[str, str, str, str]:
        return self.candidate_id, self.symbol, self.side, self.decision_time_utc

    def source_id(self, window: str) -> str:
        return f"{window}:" + canonical_sha256(dict(zip(IDENTITY_FIELDS, self.key())))


@dataclass(frozen=True)
class TickQuote:
    time_utc: str
    bid: float
    ask: float


@dataclass(frozen=True)
class M1Bar:
    time_utc: str
    open: float
    high: float
    low: float
    close: float
    quote_basis: str = "BID_OHLC"
    time_semantics: str = "BAR_CLOSE_UTC"


@dataclass(frozen=True)
class FillClassification:
    status: str
    reason: str
    authority: str
    fill_time_utc: str | None
    fill_price: float | None
    expiry_time_utc: str
    cancel_time_utc: None = None
    cancel_reason: None = None


@dataclass(frozen=True)
class ExitClassification:
    status: str
    reason: str
    exit_time_utc: str
    exit_price: float
    gross_r: float
    net_r: float
    ambiguity: bool
    variant_id: str = EXIT_VARIANT_ID


def limit_intent(
    identity: CompositeIdentity,
    *,
    repaired_side: str,
    entry: Any,
    stop: Any,
    target: Any,
) -> dict[str, Any]:
    side = str(repaired_side).upper()
    entry_n = strict_number(entry, label="entry")
    stop_n = strict_number(stop, label="stop")
    target_n = strict_number(target, label="target")
    if side == "LONG":
        valid = stop_n < entry_n < target_n
    elif side == "SHORT":
        valid = target_n < entry_n < stop_n
    else:
        valid = False
    risk = abs(entry_n - stop_n)
    if (
        not valid
        or entry_n <= 0
        or risk <= 0
        or not math.isclose(abs(target_n - entry_n), 20.0 * risk, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise P1RunnerRefusal("repaired_geometry_not_exact_minus1_plus20")
    decision = parse_utc(identity.decision_time_utc, label="identity.decision_time_utc")
    return {
        "schema": "gtos.p1-internal-limit-intent.v1",
        "effective_order_type": ORDER_TYPE,
        "executable": False,
        "composite_identity": asdict(identity),
        "repaired_side": side,
        "entry_price": entry_n,
        "stop_loss": stop_n,
        "take_profit": target_n,
        "decision_time_utc": iso_utc(decision),
        "expiry_time_utc": iso_utc(decision + timedelta(minutes=HORIZON_MINUTES)),
        "observation_interval": "(decision_time_utc,expiry_time_utc]",
        "cancellation_policy": CANCELLATION_POLICY,
        "cancel_time_utc": None,
        "cancel_reason": None,
        "market_fallback": False,
        "broker_pending_order_created": False,
    }


def stitch_m1(parts: Iterable[Iterable[M1Bar]]) -> tuple[M1Bar, ...]:
    rows = sorted((row for part in parts for row in part), key=lambda row: parse_utc(row.time_utc, label="m1.time"))
    seen: set[str] = set()
    previous: datetime | None = None
    for row in rows:
        stamp = parse_utc(row.time_utc, label="m1.time")
        normalized = iso_utc(stamp)
        if normalized in seen or (previous is not None and stamp <= previous):
            raise P1RunnerRefusal("m1_stitch_duplicate_or_order_drift")
        if row.quote_basis != "BID_OHLC":
            raise P1RunnerRefusal("m1_quote_basis_drift")
        values = tuple(strict_number(getattr(row, name), label=f"m1.{name}") for name in ("open", "high", "low", "close"))
        if values[2] > min(values[0], values[3]) or values[1] < max(values[0], values[3]):
            raise P1RunnerRefusal("m1_ohlc_geometry_invalid")
        seen.add(normalized)
        previous = stamp
    return tuple(rows)


def _m1_authority_complete(
    bindings: Sequence[Mapping[str, Any]], decision: datetime, expiry: datetime
) -> bool:
    """Prove source interval coverage without inventing civil-minute prints.

    Sparse authenticated M1 is legitimate.  Completeness is therefore a property
    of exact source hashes, declared file bounds, and stitched interval coverage,
    never of one bar per wall-clock minute.
    """
    spans: list[tuple[datetime, datetime]] = []
    for number, binding in enumerate(bindings):
        digest = binding.get("sha256")
        expected = binding.get("expected_sha256")
        contract = binding.get("completion_contract")
        if (
            binding.get("authenticated") is not True
            or not isinstance(digest, str)
            or len(digest) != 64
            or digest != expected
            or not isinstance(contract, Mapping)
        ):
            return False
        window = str(contract.get("window") or "")
        if window not in LANE_MANIFEST_BINDINGS or (
            contract.get("schema")
            != "gtos.p1-hash-bound-sparse-m1-completion.v1"
            or contract.get("path_manifest_sha256")
            != PATH_MANIFEST_BINDINGS[window][1]
            or contract.get("lane_manifest_sha256")
            != LANE_MANIFEST_BINDINGS[window][1]
            or contract.get("sparse_no_print_minutes_valid") is not True
            or contract.get("civil_minute_continuity_required") is not False
        ):
            return False
        start = parse_utc(binding.get("start_utc"), label=f"m1.binding.{number}.start")
        end = parse_utc(binding.get("end_utc"), label=f"m1.binding.{number}.end")
        if end < start:
            raise P1RunnerRefusal("m1_authority_interval_invalid")
        spans.append((start, end))
    if not spans:
        return False
    spans.sort()
    covered_until = decision
    for start, end in spans:
        if end < decision or start > expiry:
            continue
        if start > covered_until:
            return False
        covered_until = max(covered_until, end)
        if covered_until >= expiry:
            return True
    return False


def _not_evaluable(authority: str, reason: str, expiry: datetime) -> FillClassification:
    return FillClassification(
        status="NOT_EVALUABLE",
        reason=reason,
        authority=authority,
        fill_time_utc=None,
        fill_price=None,
        expiry_time_utc=iso_utc(expiry),
    )


def classify_fill(
    intent: Mapping[str, Any],
    *,
    authority: str,
    ticks: Sequence[TickQuote] = (),
    m1_parts: Sequence[Sequence[M1Bar]] = (),
    m1_authority_bindings: Sequence[Mapping[str, Any]] = (),
    authority_start_utc: str | None = None,
    authority_end_utc: str | None = None,
) -> FillClassification:
    if intent.get("effective_order_type") != ORDER_TYPE:
        raise P1RunnerRefusal("effective_order_type_drift")
    if intent.get("cancellation_policy") != CANCELLATION_POLICY or intent.get("cancel_time_utc") is not None or intent.get("cancel_reason") is not None:
        raise P1RunnerRefusal("cancellation_policy_drift")
    if intent.get("market_fallback") is not False or intent.get("executable") is not False:
        raise P1RunnerRefusal("invented_market_or_execution_authority")
    side = str(intent.get("repaired_side") or "").upper()
    entry = strict_number(intent.get("entry_price"), label="intent.entry")
    decision = parse_utc(intent.get("decision_time_utc"), label="intent.decision")
    expiry = parse_utc(intent.get("expiry_time_utc"), label="intent.expiry")
    if expiry != decision + timedelta(minutes=HORIZON_MINUTES):
        raise P1RunnerRefusal("expiry_drift")
    if authority == "PATH_START_GAP":
        return _not_evaluable(authority, "NOT_EVALUABLE_PATH_START_GAP", expiry)
    if authority == "FULL_TICK":
        if authority_start_utc is None or authority_end_utc is None:
            raise P1RunnerRefusal("full_tick_bounds_required")
        if parse_utc(authority_start_utc, label="tick.bound.start") > decision or parse_utc(authority_end_utc, label="tick.bound.end") < expiry:
            raise P1RunnerRefusal("full_tick_not_fully_bounded")
        previous: datetime | None = None
        for quote in ticks:
            stamp = parse_utc(quote.time_utc, label="tick.time")
            bid = strict_number(quote.bid, label="tick.bid")
            ask = strict_number(quote.ask, label="tick.ask")
            if ask < bid or (previous is not None and stamp < previous) or stamp > expiry:
                raise P1RunnerRefusal("tick_quote_basis_time_or_order_drift")
            previous = stamp
            if stamp <= decision:
                continue
            touched = ask <= entry if side == "LONG" else bid >= entry
            if touched:
                price = ask if side == "LONG" else bid
                return FillClassification("FILLED", "FIRST_EXECUTABLE_QUOTE_TOUCH", authority, iso_utc(stamp), price, iso_utc(expiry))
        return FillClassification("NO_FILL", "EXPIRED_UNFILLED", authority, None, None, iso_utc(expiry))
    if authority != "M1_ONLY":
        raise P1RunnerRefusal("fill_authority_unknown")
    bars = stitch_m1(m1_parts)
    if not _m1_authority_complete(m1_authority_bindings, decision, expiry):
        return _not_evaluable(authority, "NOT_EVALUABLE_M1_SOURCE_OR_SESSION_GAP", expiry)
    for bar in bars:
        stamp = parse_utc(bar.time_utc, label="m1.time")
        if not decision < stamp <= expiry:
            raise P1RunnerRefusal("m1_observation_outside_strict_interval")
        touched = bar.low <= entry if side == "LONG" else bar.high >= entry
        if touched:
            return _not_evaluable(authority, "NOT_EVALUABLE_M1_TOUCH_WITHOUT_EXECUTABLE_TICK", expiry)
    return FillClassification("NO_FILL", "EXPIRED_UNFILLED", authority, None, None, iso_utc(expiry))


def resolve_fill_authority(
    identity: CompositeIdentity,
    *,
    tick_pointer_present: bool,
    archive_start_utc: str | None,
    archive_end_utc: str | None,
) -> str:
    """Resolve only the frozen path authority class; never infer a fill."""
    if identity.symbol == "UK100" and identity.decision_time_utc in UK100_GAPS:
        return "PATH_START_GAP"
    if not tick_pointer_present:
        return "M1_ONLY"
    if archive_start_utc is None or archive_end_utc is None:
        return "M1_ONLY"
    decision = parse_utc(identity.decision_time_utc, label="authority.decision")
    expiry = decision + timedelta(minutes=HORIZON_MINUTES)
    start = parse_utc(archive_start_utc, label="authority.archive_start")
    end = parse_utc(archive_end_utc, label="authority.archive_end")
    return "FULL_TICK" if start <= decision and end >= expiry else "M1_ONLY"


def require_unique_identities(rows: Iterable[Mapping[str, Any]]) -> int:
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        key = CompositeIdentity.from_row(row).key()
        if key in seen:
            raise P1RunnerRefusal("duplicate_composite_identity")
        seen.add(key)
    return len(seen)


def evaluate_tick_exit(
    intent: Mapping[str, Any],
    fill: FillClassification,
    quotes: Sequence[TickQuote],
    *,
    cost_r: float = 0.0,
) -> ExitClassification:
    if fill.status != "FILLED" or fill.fill_time_utc is None or fill.fill_price is None:
        raise P1RunnerRefusal("filled_authority_required_for_exit")
    side = str(intent["repaired_side"])
    entry = strict_number(intent["entry_price"], label="exit.entry")
    stop = strict_number(intent["stop_loss"], label="exit.stop")
    target = strict_number(intent["take_profit"], label="exit.target")
    risk = abs(entry - stop)
    if not math.isclose(abs(target - entry), 20 * risk, rel_tol=1e-12, abs_tol=1e-12):
        raise P1RunnerRefusal("exit_plus2_or_geometry_drift")
    fill_time = parse_utc(fill.fill_time_utc, label="fill.time")
    horizon = parse_utc(intent["expiry_time_utc"], label="exit.horizon")
    points: list[ExitPathPoint] = []
    prices: dict[int, float] = {}
    times: dict[int, datetime] = {}
    for quote in quotes:
        stamp = parse_utc(quote.time_utc, label="exit.quote.time")
        bid = strict_number(quote.bid, label="exit.quote.bid")
        ask = strict_number(quote.ask, label="exit.quote.ask")
        if ask < bid:
            raise P1RunnerRefusal("exit_quote_basis_drift")
        if fill_time < stamp <= horizon:
            price = bid if side == "LONG" else ask
            signed_r = (price - entry) / risk if side == "LONG" else (entry - price) / risk
            source_index = len(points)
            points.append(
                ExitPathPoint(
                    time_us=int(round(stamp.timestamp() * 1_000_000)),
                    signed_r=signed_r,
                    deadline_eligible=True,
                    source_index=source_index,
                )
            )
            prices[source_index] = price
            times[source_index] = stamp
    if not points:
        raise P1RunnerRefusal("exit_terminal_quote_missing")
    spec = ExitOverlaySpec(
        variant_id=EXIT_VARIANT_ID,
        kind="time_box",
        time_box_minutes=HORIZON_MINUTES,
        hard_stop_r=-1.0,
        hard_target_r=20.0,
        horizon_minutes=HORIZON_MINUTES,
    )
    spec.validate()
    replay = replay_signed_path(
        spec,
        points,
        decision_time_us=int(round(parse_utc(intent["decision_time_utc"], label="exit.decision").timestamp() * 1_000_000)),
        cost_r=strict_number(cost_r, label="exit.cost_r"),
        source_mode="ORDERED_TICK",
    )
    index = replay.exit_source_index
    if replay.status != "REPLAYED" or index is None or replay.gross_r is None or replay.net_r is None:
        raise P1RunnerRefusal(f"shared_hdf_tick_refused:{replay.exit_reason}")
    if replay.exit_reason == "horizon_terminal_mark" and times[index] < horizon:
        raise P1RunnerRefusal("shared_hdf_tick_path_truncated_before_horizon")
    return ExitClassification(
        "REPLAYED",
        replay.exit_reason,
        iso_utc(times[index]),
        prices[index],
        float(replay.gross_r),
        float(replay.net_r),
        replay.ambiguity,
    )


def evaluate_m1_exit_bar(
    intent: Mapping[str, Any],
    fill: FillClassification,
    bar: M1Bar,
    *,
    cost_r: float = 0.0,
) -> ExitClassification:
    """Direct +20R shared-HDF conservative M1 helper; never protocol-cell mapped."""
    if bar.time_semantics != "BAR_CLOSE_UTC":
        raise P1RunnerRefusal("m1_exit_timestamp_not_executable_bar_close")
    stamp_value = parse_utc(bar.time_utc, label="exit.m1.time")
    horizon = parse_utc(intent["expiry_time_utc"], label="exit.horizon")
    if (
        fill.fill_time_utc is None
        or stamp_value <= parse_utc(fill.fill_time_utc, label="fill.time")
        or stamp_value > horizon
    ):
        raise P1RunnerRefusal("exit_path_not_strictly_after_fill")
    side = str(intent["repaired_side"])
    entry = strict_number(intent["entry_price"], label="exit.entry")
    risk = abs(entry - strict_number(intent["stop_loss"], label="exit.stop"))
    values = {
        key: ((strict_number(getattr(bar, key), label=f"exit.m1.{key}") - entry) / risk)
        for key in ("open", "high", "low", "close")
    }
    if side == "SHORT":
        values = {key: -value for key, value in values.items()}
    high_r = max(values["high"], values["low"])
    low_r = min(values["high"], values["low"])
    signed_bar = SignedM1Bar(
        time_us=int(round(stamp_value.timestamp() * 1_000_000)),
        open_r=values["open"],
        high_r=high_r,
        low_r=low_r,
        close_r=values["close"],
        source_index=0,
    )
    spec = ExitOverlaySpec(
        variant_id=EXIT_VARIANT_ID,
        kind="time_box",
        time_box_minutes=HORIZON_MINUTES,
        hard_stop_r=-1.0,
        hard_target_r=20.0,
        horizon_minutes=HORIZON_MINUTES,
    )
    spec.validate()
    conservative = replay_m1_conservative(
        spec,
        [signed_bar],
        decision_time_us=int(round(parse_utc(intent["decision_time_utc"], label="exit.decision").timestamp() * 1_000_000)),
        cost_r=strict_number(cost_r, label="exit.cost_r"),
    )
    replay = conservative.selected
    if replay.gross_r is None or replay.net_r is None:
        raise P1RunnerRefusal(f"shared_hdf_m1_refused:{replay.exit_reason}")
    if replay.exit_reason == "horizon_terminal_mark" and stamp_value < horizon:
        raise P1RunnerRefusal("shared_hdf_m1_path_truncated_before_horizon")
    gross = float(replay.gross_r)
    exit_price = entry + gross * risk if side == "LONG" else entry - gross * risk
    return ExitClassification(
        "REPLAYED",
        replay.exit_reason,
        iso_utc(stamp_value),
        exit_price,
        gross,
        float(replay.net_r),
        conservative.outcomes_differ,
    )


def expected_non_family_stage_rows(identity: CompositeIdentity, window: str) -> Iterator[dict[str, Any]]:
    """Test/support wrapper; real runs always provide literal frozen source hashes."""
    yield from _non_family_stage_rows(
        identity,
        window,
        source_container_sha256="0" * 64,
        source_row_sha256=canonical_sha256(asdict(identity)),
    )


def _require_file(
    path: Path, digest: str, size: int | None = None, *, root: Path = REPO_ROOT
) -> None:
    _read_bound_bytes(path, root=root, digest=digest, size=size)


def _load_preregistration() -> dict[str, Any]:
    raw, _digest = _read_stable_bytes(PREREGISTRATION_PATH, root=REPO_ROOT)
    payload = _strict_json(raw, label="p1_fill_authority_preregistration")
    if payload.get("schema") != "gtos.p1-fill-authority-preregistration.v1":
        raise P1RunnerRefusal("preregistration_schema_drift")
    if payload.get("execution_authority") is not False or payload.get("activation_authority") is not False:
        raise P1RunnerRefusal("preregistration_authority_drift")
    nulls = payload.get("predecode_null_fields")
    if not isinstance(nulls, Mapping) or any(value is not None for value in nulls.values()):
        raise P1RunnerRefusal("preregistration_fill_or_output_value_not_null")
    if payload.get("authority_accounting") != {**EXPECTED_AUTHORITY, "TOTAL": EXPECTED_FAMILY}:
        raise P1RunnerRefusal("preregistration_authority_accounting_drift")
    if payload.get("classifier_spec_sha256") != canonical_sha256(
        payload.get("classifier_state_machine")
    ):
        raise P1RunnerRefusal("preregistration_classifier_spec_hash_drift")
    return payload


def _git(*args: str) -> str:
    allowed = False
    if args in {("rev-parse", "HEAD"), ("status", "--porcelain")}:
        allowed = True
    elif len(args) == 4 and args[:3] == ("show", "-s", "--format=%P"):
        allowed = len(args[3]) == 40 and all(character in "009abcdef" for character in args[3])
    elif len(args) == 6 and args[:5] == (
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "--root",
    ):
        allowed = len(args[5]) == 40 and all(character in "009abcdef" for character in args[5])
    elif len(args) == 5 and args[:4] == (
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
    ):
        allowed = len(args[4]) == 40 and all(character in "009abcdef" for character in args[4])
    if not allowed:
        raise P1RunnerRefusal(f"git_command_shape_refused:{args!r}")
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout.decode("utf-8").strip()


def _verify_static_boundary(paths: Sequence[Path]) -> dict[str, Any]:
    scanned: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imported = None
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for imported in names:
                if any(imported == prefix or imported.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORTS):
                    raise P1RunnerRefusal(f"forbidden_import:{path}:{imported}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "order_send":
                raise P1RunnerRefusal(f"forbidden_order_send_call:{path}")
        scanned.append(path.relative_to(REPO_ROOT).as_posix())
    return {"status": "PASS", "scanned": scanned}


def _scan_json_value_end(text: str, start: int) -> int:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise P1RunnerRefusal("sidecar_json_value_missing")
    if text[index] == '"':
        index += 1
        escaped = False
        while index < len(text):
            character = text[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                return index + 1
            index += 1
        raise P1RunnerRefusal("sidecar_json_string_unterminated")
    if text[index] in "[{":
        stack = [text[index]]
        index += 1
        in_string = False
        escaped = False
        while index < len(text) and stack:
            character = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
            elif character == '"':
                in_string = True
            elif character in "[{":
                stack.append(character)
            elif character in "]}":
                expected = "[" if character == "]" else "{"
                if not stack or stack.pop() != expected:
                    raise P1RunnerRefusal("sidecar_json_container_mismatch")
            index += 1
        if stack:
            raise P1RunnerRefusal("sidecar_json_container_unterminated")
        return index
    while index < len(text) and text[index] not in ",}":
        index += 1
    return index


_JSON_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")
_UNSELECTED = object()


def _json_string_end(text: str, start: int, *, label: str) -> int:
    if start >= len(text) or text[start] != '"':
        raise P1RunnerRefusal(f"json_string_expected:{label}")
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == '"':
            return index + 1
        if ord(character) < 0x20:
            raise P1RunnerRefusal(f"json_string_control_character:{label}")
        if character == "\\":
            index += 1
            if index >= len(text) or text[index] not in '"\\/bfnrtu':
                raise P1RunnerRefusal(f"json_string_escape_invalid:{label}")
            if text[index] == "u":
                digits = text[index + 1 : index + 5]
                if len(digits) != 4 or any(ch not in "009abcdefABCDEF" for ch in digits):
                    raise P1RunnerRefusal(f"json_string_unicode_escape_invalid:{label}")
                index += 4
        index += 1
    raise P1RunnerRefusal(f"json_string_unterminated:{label}")


def _profile_path_selected(path: tuple[str, ...]) -> bool:
    """Select only mechanical U4 data; cost, spread, swap and tick value stay opaque."""
    if len(path) == 1:
        return path[0] in {
            "schema",
            "status",
            "tested_source_commit",
            "execution_authority",
            "activation_authority",
            "result_bearing_science_executed",
            "result_use_status",
            "profiles",
        }
    if path[0] != "profiles" or len(path) < 2 or path[1] not in PROFILE_NAMES:
        return False
    if len(path) == 2:
        return True
    if len(path) == 3:
        return path[2] in {"profile_name", "symbols"}
    if path[2] != "symbols":
        return False
    if len(path) == 4:
        return True
    return len(path) == 5 and path[4] in MECHANICAL_SYMBOL_FIELDS


class _SelectiveJsonParser:
    """Strict JSON syntax/duplicate validator with selective value materialization."""

    def __init__(self, text: str, *, label: str):
        self.text = text
        self.label = label
        self.index = 0

    def _space(self) -> None:
        while self.index < len(self.text) and self.text[self.index].isspace():
            self.index += 1

    def parse(self) -> dict[str, Any]:
        value = self._value((), selected=True)
        self._space()
        if self.index != len(self.text) or not isinstance(value, dict):
            raise P1RunnerRefusal(f"json_projector_root_invalid:{self.label}")
        return value

    def _value(self, path: tuple[str, ...], *, selected: bool) -> Any:
        self._space()
        if self.index >= len(self.text):
            raise P1RunnerRefusal(f"json_value_missing:{self.label}")
        character = self.text[self.index]
        if character == "{":
            return self._object(path, selected=selected)
        if character == "[":
            return self._array(path, selected=selected)
        start = self.index
        if character == '"':
            self.index = _json_string_end(self.text, start, label=self.label)
        elif self.text.startswith("true", start):
            self.index += 4
        elif self.text.startswith("false", start):
            self.index += 5
        elif self.text.startswith("null", start):
            self.index += 4
        else:
            match = _JSON_NUMBER.match(self.text, start)
            if match is None:
                raise P1RunnerRefusal(f"json_scalar_invalid_or_nonfinite:{self.label}")
            self.index = match.end()
        if self.index < len(self.text) and self.text[self.index] not in " \t\r\n,]}":
            raise P1RunnerRefusal(f"json_scalar_trailing_garbage:{self.label}")
        if not selected:
            return _UNSELECTED
        return _strict_json(self.text[start : self.index], label=f"{self.label}:{'.'.join(path)}")

    def _object(self, path: tuple[str, ...], *, selected: bool) -> Any:
        self.index += 1
        output: dict[str, Any] = {}
        seen: set[str] = set()
        self._space()
        if self.index < len(self.text) and self.text[self.index] == "}":
            self.index += 1
            return output if selected else _UNSELECTED
        while True:
            self._space()
            start = self.index
            end = _json_string_end(self.text, start, label=f"{self.label}:key")
            key = _strict_json(self.text[start:end], label=f"{self.label}:key")
            if not isinstance(key, str) or key in seen:
                raise P1RunnerRefusal(f"duplicate_json_key:{self.label}:{key}")
            seen.add(key)
            self.index = end
            self._space()
            if self.index >= len(self.text) or self.text[self.index] != ":":
                raise P1RunnerRefusal(f"json_colon_missing:{self.label}:{key}")
            self.index += 1
            child_path = (*path, key)
            child_selected = selected and _profile_path_selected(child_path)
            value = self._value(child_path, selected=child_selected)
            if child_selected and value is not _UNSELECTED:
                output[key] = value
            self._space()
            if self.index < len(self.text) and self.text[self.index] == ",":
                self.index += 1
                continue
            if self.index < len(self.text) and self.text[self.index] == "}":
                self.index += 1
                return output if selected else _UNSELECTED
            raise P1RunnerRefusal(f"json_object_separator_invalid:{self.label}")

    def _array(self, path: tuple[str, ...], *, selected: bool) -> Any:
        self.index += 1
        output: list[Any] = []
        self._space()
        if self.index < len(self.text) and self.text[self.index] == "]":
            self.index += 1
            return output if selected else _UNSELECTED
        while True:
            value = self._value(path, selected=selected)
            if selected and value is not _UNSELECTED:
                output.append(value)
            self._space()
            if self.index < len(self.text) and self.text[self.index] == ",":
                self.index += 1
                continue
            if self.index < len(self.text) and self.text[self.index] == "]":
                self.index += 1
                return output if selected else _UNSELECTED
            raise P1RunnerRefusal(f"json_array_separator_invalid:{self.label}")


def project_mechanical_profile_snapshot(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise P1RunnerRefusal("hn_profile_utf8_invalid") from exc
    projected = _SelectiveJsonParser(text, label="hn_profile_mechanical").parse()
    if (
        projected.get("schema") != "gtos.p1-inert-profile-symbol-snapshot.v1"
        or projected.get("status") != "U4_CLOSED_INERT_PROFILE_SYMBOL_SNAPSHOT_BOUND"
        or projected.get("tested_source_commit") != BASE_SOURCE_PARENT
        or projected.get("execution_authority") is not False
        or projected.get("activation_authority") is not False
        or projected.get("result_bearing_science_executed") is not False
        or projected.get("result_use_status") != "SOURCE_CONTROL_ONLY_NO_OUTCOME_READ"
        or set(projected.get("profiles") or {}) != set(PROFILE_NAMES)
    ):
        raise P1RunnerRefusal("hn_profile_mechanical_projection_authority_drift")
    profiles = projected["profiles"]
    for profile_name in PROFILE_NAMES:
        profile = profiles.get(profile_name)
        if (
            not isinstance(profile, Mapping)
            or profile.get("profile_name") != profile_name
            or not isinstance(profile.get("symbols"), Mapping)
            or not profile["symbols"]
        ):
            raise P1RunnerRefusal(f"hn_profile_mechanical_projection_drift:{profile_name}")
        for symbol, fields in profile["symbols"].items():
            if (
                not isinstance(fields, Mapping)
                or not REQUIRED_MECHANICAL_SYMBOL_FIELDS.issubset(fields)
                or not set(fields).issubset(MECHANICAL_SYMBOL_FIELDS)
            ):
                raise P1RunnerRefusal(f"hn_profile_mechanical_symbol_schema_drift:{profile_name}:{symbol}")
            for field in set(fields) - {"mt5_symbol"}:
                strict_number(fields[field], label=f"hn_profile.{profile_name}.{symbol}.{field}")
            if not str(fields.get("mt5_symbol") or ""):
                raise P1RunnerRefusal(f"hn_profile_broker_symbol_missing:{profile_name}:{symbol}")
    return projected


def _load_adapter() -> types.ModuleType:
    payload = _git_blob(
        CANONICAL_EVIDENCE_COMMIT,
        ADAPTER_RELATIVE,
        digest=ADAPTER_SHA256,
        size=ADAPTER_BYTES,
    )
    module_name = f"_gtos_p1_shadow_{ADAPTER_SHA256}"
    existing = sys.modules.get(module_name)
    if isinstance(existing, types.ModuleType):
        return existing
    module = types.ModuleType(module_name)
    module.__file__ = f"git:{CANONICAL_EVIDENCE_COMMIT}:{ADAPTER_RELATIVE}"
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        code = compile(payload, module.__file__, "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    required = (
        "source_bound_candidate_generator",
        "apply_current_breaker_re_entry_repair",
        "evaluate_inert_permission",
        "inert_admit_unchanged_router",
        "inert_scheduler_capture",
        "scheduler_capture_only",
        "project_order_preimage",
        "project_hde_cost",
        "account_claim_scope",
    )
    if any(not callable(getattr(module, name, None)) for name in required):
        raise P1RunnerRefusal("adapter_required_callable_missing")
    if (
        getattr(module, "DEFAULT_ENABLED", None) is not False
        or getattr(module, "EXECUTION_AUTHORITY", None) is not False
        or getattr(module, "ACTIVATION_AUTHORITY", None) is not False
        or getattr(module, "FROZEN_GATE_DISPOSITION", None)
        != "RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED"
        or getattr(module, "VOLUME_STATUS", None)
        != "NOT_EVALUABLE_OWNER_INPUT_REQUIRED"
    ):
        raise P1RunnerRefusal("adapter_frozen_constant_drift")
    return module


def _permission_inputs(*, decision_time_utc: str, symbol: str) -> dict[str, Any]:
    return {
        "evidence_class": PERMISSION_EVIDENCE_CLASS,
        "session_state": {
            "asof_utc": decision_time_utc,
            "session_open": True,
            "daily_loss_blocked": False,
        },
        "account_headroom": {
            "snapshot_status": "VALID",
            "daily_headroom_pct": 2.0,
            "overall_headroom_pct": 4.0,
        },
        "symbol_state": {
            "symbol": symbol,
            "trade_mode": "ENABLED",
            "position_conflict": False,
        },
        "mt5_interface_response": {
            "interface_status": "INERT_OK",
            "symbol_visible": True,
        },
    }


def _load_shared_authorities() -> tuple[types.ModuleType, dict[str, Any], dict[str, Any]]:
    adapter = _load_adapter()
    route = _strict_json(
        _git_blob(
            HN_EVIDENCE_COMMIT,
            HN_ROUTE_RELATIVE,
            digest=HN_ROUTE_SHA256,
            size=HN_ROUTE_BYTES,
        ),
        label="hn_route_parameter_bundle",
    )
    if (
        not isinstance(route, Mapping)
        or route.get("schema") != "gtos.p1-inert-route-parameter-bundle.v1"
        or route.get("status") != "U11_CLOSED_HASH_BOUND_INERT_ROUTE_PARAMETERS"
        or route.get("tested_source_commit") != BASE_SOURCE_PARENT
        or route.get("execution_authority") is not False
        or route.get("activation_authority") is not False
        or route.get("result_bearing_science_executed") is not False
        or (route.get("router") or {}).get("deterministic") is not True
        or (route.get("router") or {}).get("learned_probability_or_value_consumer")
        is not False
        or (route.get("scheduler") or {}).get("authority") != "CAPTURE_ONLY"
        or (route.get("scheduler") or {}).get("may_select_rank_suppress_or_size")
        is not False
        or (route.get("inertness") or {}).get("broker_operations") != 0
        or (route.get("inertness") or {}).get("network_calls") != 0
        or (route.get("inertness") or {}).get("runtime_writes") != 0
    ):
        raise P1RunnerRefusal("hn_route_parameter_authority_drift")
    profile = project_mechanical_profile_snapshot(
        _git_blob(
            HN_EVIDENCE_COMMIT,
            HN_PROFILE_RELATIVE,
            digest=HN_PROFILE_SHA256,
            size=HN_PROFILE_BYTES,
        )
    )
    known_answer = adapter.evaluate_inert_permission(
        _permission_inputs(
            decision_time_utc="2026-01-02T00:00:00+00:00", symbol="EURUSD"
        )
    )
    if known_answer != {
        "status": "PERMITTED",
        "reason": "deterministic_in_memory_permission_pass",
        "missing_fields": [],
    }:
        raise P1RunnerRefusal("adapter_preregistered_permission_known_answer_drift")
    for account_scope in PROFILE_NAMES:
        claim = adapter.account_claim_scope(account_scope)
        if claim.get("economic_verdict_emitted") is not False or claim.get(
            "mechanical_compatibility_allowed"
        ) is not True:
            raise P1RunnerRefusal(f"adapter_account_scope_drift:{account_scope}")
        if account_scope == "redacted_account" and (
            claim.get("economic_gate_allowed") is not False
            or claim.get("promotion_or_veto_allowed") is not False
        ):
            raise P1RunnerRefusal("adapter_redacted_account_scope_drift")
    return adapter, dict(route), profile


def _minimal_source_candidate(pool_row: Mapping[str, Any]) -> dict[str, Any]:
    projected = {
        key: pool_row[key] for key in CANDIDATE_PREDECISION_FIELDS if key in pool_row
    }
    for field in ("entry_price", "stop_loss", "take_profit_1"):
        strict_number(projected.get(field), label=f"source_geometry.{field}")
    if projected.get("origin_family") != ORIGIN_FAMILY:
        raise P1RunnerRefusal("minimal_candidate_origin_family_drift")
    return projected


def _candidate_route(
    adapter: types.ModuleType,
    pool_row: Mapping[str, Any],
    identity: CompositeIdentity,
    *,
    window: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    minimal = _minimal_source_candidate(pool_row)
    generated = adapter.source_bound_candidate_generator(
        {"synthetic_candidate": minimal}
    )
    if not isinstance(generated, list) or len(generated) != 1 or generated[0] != minimal:
        raise P1RunnerRefusal("adapter_candidate_generator_not_exactly_one_source_projection")
    candidate = generated[0]
    if CompositeIdentity.from_row(candidate) != identity:
        raise P1RunnerRefusal("adapter_candidate_generator_identity_drift")
    transformed = adapter.apply_current_breaker_re_entry_repair(candidate, enabled=True)
    if transformed.get("candidate_transform_id") != TRANSFORM_ID:
        raise P1RunnerRefusal("adapter_fixed_breaker_transform_drift")
    permission_inputs = _permission_inputs(
        decision_time_utc=identity.decision_time_utc, symbol=identity.symbol
    )
    permission = adapter.evaluate_inert_permission(permission_inputs)
    if permission.get("status") != "PERMITTED":
        raise P1RunnerRefusal(f"adapter_preregistered_permission_refused:{permission}")
    permission = {
        **dict(permission),
        "evidence_class": PERMISSION_EVIDENCE_CLASS,
        "historical_permission_claim": False,
    }
    route_source = {
        "source_window_id": f"{window}_2026",
        "source_opportunity_id": identity.source_id(window),
    }
    routed = adapter.inert_admit_unchanged_router(transformed, route_source)
    if (
        routed.get("disposition") != "ADMIT"
        or canonical_sha256(routed.get("candidate")) != canonical_sha256(transformed)
    ):
        raise P1RunnerRefusal("adapter_inert_router_changed_candidate_or_disposition")
    scheduler_packet = adapter.inert_scheduler_capture(transformed, route_source)
    capture = adapter.scheduler_capture_only(
        scheduler_packet, incoming_disposition=str(routed["disposition"])
    )
    if (
        capture.get("mode") != "CAPTURE_ONLY"
        or capture.get("effect") != "NONE"
        or capture.get("output_disposition") != routed.get("disposition")
        or any(
            capture.get(field) is not False
            for field in (
                "selection_authority",
                "ranking_authority",
                "suppression_authority",
                "sizing_authority",
            )
        )
    ):
        raise P1RunnerRefusal("adapter_scheduler_capture_authority_drift")
    return candidate, transformed, permission, {"route": routed, "capture": capture}


def _account_preimages(
    adapter: types.ModuleType,
    profile: Mapping[str, Any],
    transformed: Mapping[str, Any],
    identity: CompositeIdentity,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    profiles = profile.get("profiles") or {}
    for account_scope in PROFILE_NAMES:
        account = profiles.get(account_scope) or {}
        symbols = account.get("symbols") or {}
        mechanical = symbols.get(identity.symbol)
        if not isinstance(mechanical, Mapping):
            raise P1RunnerRefusal(
                f"account_mechanical_symbol_missing:{account_scope}:{identity.symbol}"
            )
        mechanical = dict(mechanical)
        snapshot = {
            "account_scope": account_scope,
            "profile_id": account_scope,
            "profile_snapshot_sha256": HN_PROFILE_SHA256,
            "symbol_snapshot_sha256": canonical_sha256(mechanical),
            "broker_symbol": mechanical["mt5_symbol"],
            "filling_mode": mechanical.get("filling_mode"),
        }
        preimage = adapter.project_order_preimage(
            transformed,
            order_kind="limit",
            account_snapshot=snapshot,
            account_scope=account_scope,
        )
        mismatches: list[str] = []
        expected = {
            "schema": "gtos-wave20-p1-order-preimage-v1",
            "executable": False,
            "account_scope": account_scope,
            "account_profile": account_scope,
            "account_authority_status": "INJECTED_RESEARCH_SNAPSHOT_BOUND",
            "missing_account_authority": [],
            "symbol": mechanical["mt5_symbol"],
            "source_symbol": identity.symbol,
            "request_kind": "limit",
            "action": "STORE_INTERNAL_PENDING_LIMIT_INTENT",
            "direction": transformed["side"],
            "limit_price": transformed["entry_price"],
            "stop_loss": transformed["stop_loss"],
            "take_profit_1": transformed["take_profit_1"],
            "pending_order_mode": "internal_software_limit",
            "broker_pending_order_created": False,
            "native_pending_order_type": None,
            "volume": None,
            "volume_status": "NOT_EVALUABLE_OWNER_INPUT_REQUIRED",
        }
        for field, expected_value in expected.items():
            if preimage.get(field) != expected_value:
                mismatches.append(field)
        mechanical_mismatches: list[str] = []
        if strict_number(mechanical["point"], label="account.point") <= 0:
            mechanical_mismatches.append("point_nonpositive")
        if strict_number(mechanical["tick_size"], label="account.tick_size") <= 0:
            mechanical_mismatches.append("tick_size_nonpositive")
        if strict_number(mechanical["trade_tick_size"], label="account.trade_tick_size") <= 0:
            mechanical_mismatches.append("trade_tick_size_nonpositive")
        if int(strict_number(mechanical["trade_mode"], label="account.trade_mode")) <= 0:
            mechanical_mismatches.append("trade_mode_disabled")
        mismatches.extend(mechanical_mismatches)
        claim = adapter.account_claim_scope(account_scope)
        account_result = {
            "claim_scope": claim,
            "profile_container_sha256": HN_PROFILE_SHA256,
            "mechanical_symbol_snapshot": mechanical,
            "mechanical_symbol_snapshot_sha256": snapshot[
                "symbol_snapshot_sha256"
            ],
            "unavailable_mechanical_fields": sorted(
                MECHANICAL_SYMBOL_FIELDS - set(mechanical)
            ),
            "order_preimage": preimage,
            "mechanical_compatible": not mismatches,
            "mechanical_mismatches": mismatches,
        }
        if account_scope == "redacted_account" and "economics" in account_result:
            raise P1RunnerRefusal("redacted_account_economics_key_forbidden")
        result[account_scope] = account_result
    return result


SIDECAR_CONTROL_FIELDS = frozenset(
    {
        "schema",
        "candidate_id",
        "decision_time_utc",
        "horizon_end_utc",
        "symbol",
        "side",
        "source_timeframe",
        "source_path",
        "source_sha256",
        "ordered_tick_source",
    }
)


def project_sidecar_control_json(text: str, *, label: str) -> dict[str, Any]:
    """Project metadata only; ordered_path_observations bytes are never decoded."""
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] != "{":
        raise P1RunnerRefusal(f"sidecar_row_not_object:{label}")
    index += 1
    output: dict[str, Any] = {}
    seen: set[str] = set()
    while True:
        while index < len(text) and text[index].isspace():
            index += 1
        if index < len(text) and text[index] == "}":
            index += 1
            break
        try:
            key, key_end = decoder.raw_decode(text, index)
        except json.JSONDecodeError as exc:
            raise P1RunnerRefusal(f"sidecar_json_key_invalid:{label}") from exc
        if not isinstance(key, str) or key in seen:
            raise P1RunnerRefusal(f"duplicate_json_key:{label}:{key}")
        seen.add(key)
        index = key_end
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != ":":
            raise P1RunnerRefusal(f"sidecar_json_colon_missing:{label}:{key}")
        start = index + 1
        end = _scan_json_value_end(text, start)
        if key in SIDECAR_CONTROL_FIELDS:
            output[key] = _strict_json(text[start:end], label=f"{label}:{key}")
        index = end
        while index < len(text) and text[index].isspace():
            index += 1
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            index += 1
            break
        raise P1RunnerRefusal(f"sidecar_json_separator_invalid:{label}")
    if text[index:].strip() or set(output) != SIDECAR_CONTROL_FIELDS:
        raise P1RunnerRefusal(f"sidecar_control_projection_schema_drift:{label}")
    return output


def _bound_gzip_lines(
    path: Path, *, digest: str, size: int, root: Path = REPO_ROOT
) -> Iterator[str]:
    payload = _read_bound_bytes(path, root=root, digest=digest, size=size)
    with gzip.open(io.BytesIO(payload), "rt", encoding="utf-8") as handle:
        yield from handle


def _lane_manifest(window: str) -> dict[str, Any]:
    relative, digest, size = LANE_MANIFEST_BINDINGS[window]
    path = SOURCE_ROOT / relative
    payload = _strict_json(
        _read_bound_bytes(path, root=SOURCE_ROOT, digest=digest, size=size),
        label=f"lane_manifest:{window}",
    )
    if (
        not isinstance(payload, Mapping)
        or payload.get("economic_outcomes_read") is not False
        or payload.get("broker_live_authority") is not False
        or payload.get("broker_mutation_enabled") is not False
    ):
        raise P1RunnerRefusal(f"lane_manifest_boundary_drift:{window}")
    clock = payload.get("clock") or {}
    if clock.get("time_column_basis") != "true_utc":
        raise P1RunnerRefusal(f"lane_manifest_timebase_drift:{window}")
    return dict(payload)


def _source_control_proof() -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    counts = {window: 0 for window in EXPECTED_WINDOWS}
    families = {window: 0 for window in EXPECTED_WINDOWS}
    authority_counts = {name: 0 for name in EXPECTED_AUTHORITY}
    false_april_tick_references: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    dry_day: list[tuple[str, dict[str, Any]]] = []
    for window, pool_relative, pool_digest, pool_size in POOL_BINDINGS:
        side_relative, side_digest, side_size = SIDECAR_BINDINGS[window]
        pool_lines = iter(
            _bound_gzip_lines(
                REPO_ROOT / pool_relative, digest=pool_digest, size=pool_size
            )
        )
        side_lines = iter(
            _bound_gzip_lines(
                REPO_ROOT / side_relative, digest=side_digest, size=side_size
            )
        )
        authority = _window_authority(window)
        inventory = authority["source_inventory"]
        lane_ticks = authority["lane_tick_sources"]
        for line_number in range(1, EXPECTED_WINDOWS[window] + 1):
            try:
                pool_line = next(pool_lines)
                side_line = next(side_lines)
            except StopIteration as exc:
                raise P1RunnerRefusal(
                    f"source_control_pool_or_sidecar_ended_early:{window}:{line_number}"
                ) from exc
            try:
                row = project_pool_control_json(
                    pool_line, label=f"{pool_relative}:{line_number}"
                )
            except VerificationError as exc:
                raise P1RunnerRefusal(str(exc)) from exc
            sidecar = project_sidecar_control_json(
                side_line, label=f"{side_relative}:{line_number}"
            )
            identity = CompositeIdentity.from_row(row)
            if _sidecar_identity(sidecar) != identity:
                raise P1RunnerRefusal(
                    f"source_control_pool_sidecar_identity_drift:{window}:{line_number}"
                )
            if identity.key() in seen:
                raise P1RunnerRefusal("duplicate_composite_identity")
            seen.add(identity.key())
            counts[window] += 1
            if row.get("origin_family") == ORIGIN_FAMILY:
                families[window] += 1
                symbol_authority = inventory.get(identity.symbol) or {}
                expected_tick = symbol_authority.get("tick")
                pointer = sidecar.get("ordered_tick_source")
                if pointer is not None and not isinstance(pointer, Mapping):
                    raise P1RunnerRefusal("sidecar_tick_pointer_metadata_invalid")
                if pointer is None:
                    if expected_tick is not None:
                        raise P1RunnerRefusal("sidecar_tick_pointer_metadata_missing")
                    tick_metadata = None
                else:
                    tick_metadata = lane_ticks.get(identity.symbol)
                    if not isinstance(expected_tick, Mapping) or not isinstance(
                        tick_metadata, Mapping
                    ):
                        raise P1RunnerRefusal("tick_pointer_without_bound_manifest_metadata")
                    if (
                        pointer.get("path") != expected_tick.get("path")
                        or pointer.get("source_sha256") != expected_tick.get("sha256")
                        or pointer.get("row_count") != expected_tick.get("rows")
                        or pointer.get("path") != tick_metadata.get("lane_relpath")
                        or pointer.get("source_sha256") != tick_metadata.get("sha256")
                        or pointer.get("row_count") != tick_metadata.get("row_count")
                    ):
                        raise P1RunnerRefusal("tick_pointer_lane_path_manifest_drift")
                fill_authority = resolve_fill_authority(
                    identity,
                    tick_pointer_present=tick_metadata is not None,
                    archive_start_utc=(
                        str(tick_metadata["first_utc"])
                        if tick_metadata is not None
                        else None
                    ),
                    archive_end_utc=(
                        str(tick_metadata["last_utc"])
                        if tick_metadata is not None
                        else None
                    ),
                )
                authority_counts[fill_authority] += 1
                if window == "april" and pointer is not None and fill_authority == "M1_ONLY":
                    false_april_tick_references.append(
                        {
                            "composite_identity": asdict(identity),
                            "tick_path": pointer["path"],
                            "archive_first_utc": tick_metadata["first_utc"],
                            "archive_last_utc": tick_metadata["last_utc"],
                        }
                    )
            if identity.decision_time_utc.startswith("2026-01-02"):
                dry_day.append((window, row))
        try:
            next(pool_lines)
            raise P1RunnerRefusal(f"source_control_pool_extra_rows:{window}")
        except StopIteration:
            pass
        try:
            next(side_lines)
            raise P1RunnerRefusal(f"source_control_sidecar_extra_rows:{window}")
        except StopIteration:
            pass
    if counts != EXPECTED_WINDOWS or families != EXPECTED_FAMILY_WINDOWS:
        raise P1RunnerRefusal(f"source_denominator_drift:{counts}:{families}")
    if len(seen) != EXPECTED_TOTAL or sum(families.values()) != EXPECTED_FAMILY:
        raise P1RunnerRefusal("source_total_or_family_drift")
    if authority_counts != EXPECTED_AUTHORITY or len(false_april_tick_references) != 5:
        raise P1RunnerRefusal(
            f"metadata_fill_authority_reconciliation_drift:{authority_counts}:"
            f"false_april={len(false_april_tick_references)}"
        )
    return {
        "total": len(seen),
        "window_counts": counts,
        "family_window_counts": families,
        "family": sum(families.values()),
        "non_family": len(seen) - sum(families.values()),
        "stage_rows": len(seen) * len(STAGES),
        "authority_counts": authority_counts,
        "false_april_tick_references": false_april_tick_references,
    }, dry_day


def _dry_run_digest(rows: Sequence[tuple[str, Mapping[str, Any]]]) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for window, row in rows:
        identity = CompositeIdentity.from_row(row)
        family = row.get("origin_family") == ORIGIN_FAMILY
        for stage in STAGES:
            payload = {
                "source_id": identity.source_id(window),
                "composite_identity": asdict(identity),
                "stage": stage,
                "disposition": "SOURCE_ONLY_FAMILY_PENDING_DECODE" if family else "EXPECTED_NON_FAMILY_NO_P1_MUTATION",
            }
            digest.update(canonical_bytes(payload) + b"\n")
            count += 1
    return digest.hexdigest(), count


def preflight(*, verify_packet_structure: bool = True) -> dict[str, Any]:
    _reject_symlink_components(REPO_ROOT)
    _reject_symlink_components(SOURCE_ROOT)
    prereg = _load_preregistration()
    for binding in prereg.get("repo_file_bindings") or []:
        _require_file(REPO_ROOT / binding["path"], binding["sha256"], binding.get("bytes"))
    evidence_parents = _git("show", "-s", "--format=%P", CANONICAL_EVIDENCE_COMMIT).split()
    if evidence_parents != [BASE_SOURCE_COMMIT]:
        raise P1RunnerRefusal("canonical_evidence_parent_drift")
    evidence_paths = frozenset(
        _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            CANONICAL_EVIDENCE_COMMIT,
        ).splitlines()
    )
    if evidence_paths != CANONICAL_EVIDENCE_PATHS:
        raise P1RunnerRefusal("canonical_evidence_path_set_drift")
    packet_result: dict[str, Any] | None = None
    if verify_packet_structure:
        packet_result = verify_packet(
            PACKET,
            full_generator=False,
            expected_manifest_sha256=PACKET_MANIFEST_SHA256,
            expected_payload_root_sha256=PACKET_PAYLOAD_ROOT_SHA256,
            expected_tested_source_commit=BASE_SOURCE_COMMIT,
        )
    denominator, dry_rows = _source_control_proof()
    first_digest, dry_count = _dry_run_digest(dry_rows)
    second_digest, second_count = _dry_run_digest(dry_rows)
    if (first_digest, dry_count) != (second_digest, second_count):
        raise P1RunnerRefusal("one_day_dry_run_nondeterministic")
    expected_denominator = {
        "total": EXPECTED_TOTAL,
        "window_counts": EXPECTED_WINDOWS,
        "family_window_counts": EXPECTED_FAMILY_WINDOWS,
        "family": EXPECTED_FAMILY,
        "non_family": EXPECTED_NON_FAMILY,
        "stage_rows": EXPECTED_STAGE_ROWS,
    }
    if any(denominator.get(key) != value for key, value in expected_denominator.items()):
        raise P1RunnerRefusal("complete_denominator_reconciliation_failed")
    if denominator.get("authority_counts") != EXPECTED_AUTHORITY:
        raise P1RunnerRefusal("metadata_authority_accounting_reconciliation_failed")
    _adapter, route_authority, profile_authority = _load_shared_authorities()
    static = _verify_static_boundary(
        (
            Path(__file__),
            REPO_ROOT / "src/components/current_breaker_re_entry_repair.py",
            REPO_ROOT / "src/research_infra/exit_overlay.py",
            REPO_ROOT / "src/research_infra/train_engine/decision_semantics.py",
        )
    )
    _reject_symlink_components(OUTPUT_PARENT.parent)
    _reject_symlink_components(OUTPUT_PARENT, allow_missing_leaf=True)
    marker = OUTPUT_PARENT.with_name(OUTPUT_PARENT.name + ".RUN_STARTED")
    if _lexists(OUTPUT_PARENT):
        raise P1RunnerRefusal("output_parent_must_be_absent_before_authorized_run")
    if _lexists(marker):
        raise P1RunnerRefusal("run_marker_must_be_absent_before_authorized_run")
    staging_prefix = f".{OUTPUT_PARENT.name}.staging-"
    if any(path.name.startswith(staging_prefix) for path in OUTPUT_PARENT.parent.iterdir()):
        raise P1RunnerRefusal("staging_target_must_be_absent_before_authorized_run")
    estimate = {
        "stage_rows": EXPECTED_STAGE_ROWS,
        "uncompressed_upper_bound_bytes": EXPECTED_STAGE_ROWS * 1_024,
        "large_output_limit_bytes": 4 * 1024**3,
        "rss_limit_bytes": 6 * 1024**3,
    }
    return {
        "schema": "gtos.p1-offline-complete-path-preflight.v1",
        "status": "P1_PREDECODE_PREFLIGHT_PASS",
        "result_bearing_science_executed": False,
        "execution_authority": False,
        "activation_authority": False,
        "packet": packet_result,
        "denominator": denominator,
        "authority_accounting": EXPECTED_AUTHORITY,
        "metadata_authority_reconciliation": {
            "counts": denominator["authority_counts"],
            "false_april_tick_references": denominator[
                "false_april_tick_references"
            ],
        },
        "one_day_source_only_dry_run": {
            "date": "2026-01-02",
            "source_rows": len(dry_rows),
            "stage_rows": dry_count,
            "sha256": first_digest,
            "deterministic_repetition_match": True,
        },
        "account_roles": prereg["account_roles"],
        "shared_authority_bindings": {
            "adapter": {
                "commit": CANONICAL_EVIDENCE_COMMIT,
                "path": ADAPTER_RELATIVE,
                "sha256": ADAPTER_SHA256,
                "bytes": ADAPTER_BYTES,
            },
            "u4_mechanical_profile": {
                "commit": HN_EVIDENCE_COMMIT,
                "path": HN_PROFILE_RELATIVE,
                "sha256": HN_PROFILE_SHA256,
                "bytes": HN_PROFILE_BYTES,
                "status": profile_authority["status"],
                "economic_values_decoded": False,
                "profile_symbol_counts": {
                    name: len(profile_authority["profiles"][name]["symbols"])
                    for name in PROFILE_NAMES
                },
            },
            "u11_route": {
                "commit": HN_EVIDENCE_COMMIT,
                "path": HN_ROUTE_RELATIVE,
                "sha256": HN_ROUTE_SHA256,
                "bytes": HN_ROUTE_BYTES,
                "status": route_authority["status"],
            },
            "permission_known_answer": {
                "status": "PASS",
                "evidence_class": PERMISSION_EVIDENCE_CLASS,
            },
        },
        "static_boundary": static,
        "resource_estimate": estimate,
    }


@dataclass
class OutputBudget:
    limit_bytes: int = OUTPUT_BYTE_LIMIT
    observed_uncompressed_bytes: int = 0

    def consume(self, amount: int) -> None:
        if amount < 0:
            raise P1RunnerRefusal("output_budget_negative_increment")
        self.observed_uncompressed_bytes += amount
        if self.observed_uncompressed_bytes > self.limit_bytes:
            raise P1RunnerRefusal("online_output_byte_budget_exceeded_marker_preserved")


class DeterministicJsonlGzipWriter:
    """Streaming canonical JSONL with a deterministic gzip header."""

    def __init__(self, path: Path, *, budget: OutputBudget | None = None):
        self.path = path
        self._budget = budget
        self._raw = path.open("xb")
        self._gzip = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, mtime=0)
        self._text = io.TextIOWrapper(self._gzip, encoding="utf-8", newline="\n")
        self.rows = 0

    def write(self, row: Mapping[str, Any]) -> None:
        raw = canonical_bytes(dict(row)) + b"\n"
        if self._budget is not None:
            self._budget.consume(len(raw))
        self._text.write(raw.decode("utf-8"))
        self.rows += 1

    def close(self) -> None:
        self._text.flush()
        self._text.detach()
        self._gzip.close()
        self._raw.flush()
        os.fsync(self._raw.fileno())
        self._raw.close()

    def __enter__(self) -> "DeterministicJsonlGzipWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def _iter_full_jsonl(payload: bytes, *, label: str) -> Iterator[dict[str, Any]]:
    with gzip.open(io.BytesIO(payload), "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = _strict_json(line, label=f"{label}:{line_number}")
            if not isinstance(row, dict):
                raise P1RunnerRefusal(f"jsonl_nonobject:{label}:{line_number}")
            yield row


def _contained_source(logical: str) -> Path:
    relative = Path(str(logical))
    if relative.is_absolute() or ".." in relative.parts:
        raise P1RunnerRefusal(f"source_path_not_relative:{logical}")
    target = SOURCE_ROOT / relative
    _lexically_contained(target, SOURCE_ROOT)
    _reject_symlink_components(target)
    return target


def _window_authority(window: str) -> dict[str, Any]:
    relative, digest, size = PATH_MANIFEST_BINDINGS[window]
    path = REPO_ROOT / relative
    payload = _strict_json(
        _read_bound_bytes(path, root=REPO_ROOT, digest=digest, size=size),
        label=f"path_manifest:{window}",
    )
    invariants = payload.get("invariants") or {}
    required = (
        "all_source_hashes_authenticated",
        "first_observation_strictly_after_decision",
        "last_observation_at_or_before_120_minute_horizon",
        "one_sidecar_row_per_pool_row",
        "ordered_tick_priority_content_bound_where_available",
        "strictly_increasing_observation_times",
        "unique_join_key",
    )
    if any(invariants.get(key) is not True for key in required):
        raise P1RunnerRefusal(f"path_manifest_invariant_drift:{window}")
    sidecar = payload.get("sidecar") or {}
    expected_relative, expected_digest, _expected_size = SIDECAR_BINDINGS[window]
    if sidecar.get("path") != expected_relative or sidecar.get("sha256") != expected_digest:
        raise P1RunnerRefusal(f"path_manifest_sidecar_binding_drift:{window}")
    inventory = payload.get("source_inventory")
    if not isinstance(inventory, Mapping):
        raise P1RunnerRefusal(f"path_manifest_source_inventory_missing:{window}")
    lane = _lane_manifest(window)
    lane_ticks = {
        str(row.get("mapped_symbol") or row.get("symbol") or ""): row
        for row in lane.get("tick_sources") or []
        if isinstance(row, Mapping) and row.get("lane_relpath")
    }
    lane_m1 = {
        str(row.get("mapped_symbol") or row.get("symbol") or ""): row
        for row in lane.get("bar_sources") or []
        if isinstance(row, Mapping) and row.get("timeframe") == "M1"
    }
    for symbol, source in inventory.items():
        m1 = source.get("m1") if isinstance(source, Mapping) else None
        lane_record = lane_m1.get(str(symbol))
        if not isinstance(m1, Mapping) or not isinstance(lane_record, Mapping):
            raise P1RunnerRefusal(f"m1_lane_path_manifest_record_missing:{window}:{symbol}")
        if (
            m1.get("path") != lane_record.get("lane_relpath")
            or m1.get("sha256") != lane_record.get("sha256")
            or m1.get("rows") != lane_record.get("row_count")
            or lane_record.get("time_column_basis") != "true_utc"
        ):
            raise P1RunnerRefusal(f"m1_lane_path_manifest_record_drift:{window}:{symbol}")
        first = parse_utc(lane_record.get("first_utc"), label="lane.m1.first")
        last = parse_utc(lane_record.get("last_utc"), label="lane.m1.last")
        if first > last:
            raise P1RunnerRefusal(f"m1_lane_bounds_drift:{window}:{symbol}")
        tick = source.get("tick") if isinstance(source, Mapping) else None
        lane_tick = lane_ticks.get(str(symbol))
        if tick is None:
            continue
        if not isinstance(tick, Mapping) or not isinstance(lane_tick, Mapping):
            raise P1RunnerRefusal(f"tick_lane_path_manifest_record_missing:{window}:{symbol}")
        tick_rows = tick.get("rows") if "rows" in tick else tick.get("row_count")
        if (
            tick.get("path") != lane_tick.get("lane_relpath")
            or tick.get("sha256") != lane_tick.get("sha256")
            or tick_rows != lane_tick.get("row_count")
            or lane_tick.get("time_column_basis") != "true_utc"
        ):
            raise P1RunnerRefusal(f"tick_lane_path_manifest_record_drift:{window}:{symbol}")
        tick_first = parse_utc(lane_tick.get("first_utc"), label="lane.tick.first")
        tick_last = parse_utc(lane_tick.get("last_utc"), label="lane.tick.last")
        if tick_first > tick_last:
            raise P1RunnerRefusal(f"tick_lane_bounds_drift:{window}:{symbol}")
    result = dict(payload)
    result["lane_manifest"] = lane
    result["lane_tick_sources"] = lane_ticks
    result["lane_m1_sources"] = lane_m1
    result["path_manifest_sha256"] = digest
    result["lane_manifest_sha256"] = LANE_MANIFEST_BINDINGS[window][1]
    return result


@dataclass
class TickArchive:
    times_us: array
    bids: array
    asks: array
    source_sha256: str

    @classmethod
    def load(cls, pointer: Mapping[str, Any]) -> "TickArchive":
        logical = str(pointer.get("path") or "")
        expected_sha = str(pointer.get("source_sha256") or "")
        expected_rows = pointer.get("row_count")
        if (
            len(expected_sha) != 64
            or isinstance(expected_rows, bool)
            or not isinstance(expected_rows, int)
            or expected_rows <= 0
        ):
            raise P1RunnerRefusal("tick_pointer_binding_invalid")
        path = _contained_source(logical)
        digest = hashlib.sha256()
        times = array("q")
        bids = array("d")
        asks = array("d")
        previous: int | None = None
        fd, before = _open_regular_fd(path, root=SOURCE_ROOT)
        try:
            handle = os.fdopen(fd, "rb", closefd=False)
            for line_number, raw in enumerate(handle, 1):
                digest.update(raw)
                if not raw.strip():
                    continue
                try:
                    row = _strict_json(raw, label=f"tick_archive:{logical}:{line_number}")
                    stamp = true_utc_tick_time_us(row)
                    bid = strict_number(row.get("bid"), label="tick_archive.bid")
                    ask = strict_number(row.get("ask"), label="tick_archive.ask")
                except (KeyError, TypeError, ValueError) as exc:
                    raise P1RunnerRefusal(f"tick_archive_row_invalid:{logical}:{line_number}") from exc
                if ask < bid or (previous is not None and stamp < previous):
                    raise P1RunnerRefusal(f"tick_archive_order_or_quote_drift:{logical}:{line_number}")
                times.append(stamp)
                bids.append(bid)
                asks.append(ask)
                previous = stamp
            handle.close()
            _verify_same_inode(path, fd, before)
        finally:
            os.close(fd)
        if len(times) != expected_rows or digest.hexdigest() != expected_sha:
            raise P1RunnerRefusal(f"tick_archive_binding_drift:{logical}")
        return cls(times, bids, asks, expected_sha)

    @property
    def start_utc(self) -> str:
        if not self.times_us:
            raise P1RunnerRefusal("tick_archive_empty")
        return datetime.fromtimestamp(self.times_us[0] / 1_000_000, tz=timezone.utc).isoformat()

    @property
    def end_utc(self) -> str:
        if not self.times_us:
            raise P1RunnerRefusal("tick_archive_empty")
        return datetime.fromtimestamp(self.times_us[-1] / 1_000_000, tz=timezone.utc).isoformat()

    def slice(self, decision: datetime, expiry: datetime) -> list[TickQuote]:
        lo = bisect.bisect_left(self.times_us, int(decision.timestamp() * 1_000_000))
        hi = bisect.bisect_right(self.times_us, int(expiry.timestamp() * 1_000_000))
        return [
            TickQuote(
                datetime.fromtimestamp(self.times_us[index] / 1_000_000, tz=timezone.utc).isoformat(),
                self.bids[index],
                self.asks[index],
            )
            for index in range(lo, hi)
        ]


def _m1_binding(
    record: Mapping[str, Any],
    lane_record: Mapping[str, Any],
    *,
    window: str,
    path_manifest_sha256: str,
    lane_manifest_sha256: str,
    cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    logical = str(record.get("path") or "")
    expected_sha = str(record.get("sha256") or "")
    expected_rows = record.get("rows") if "rows" in record else record.get("row_count")
    cache_key = f"{logical}:{expected_sha}"
    if cache_key in cache:
        return cache[cache_key]
    if len(expected_sha) != 64 or isinstance(expected_rows, bool) or not isinstance(expected_rows, int):
        raise P1RunnerRefusal("m1_source_binding_invalid")
    if (
        lane_record.get("lane_relpath") != logical
        or lane_record.get("sha256") != expected_sha
        or lane_record.get("row_count") != expected_rows
    ):
        raise P1RunnerRefusal("m1_lane_record_binding_drift")
    path = _contained_source(logical)
    first: datetime | None = None
    last: datetime | None = None
    rows = 0
    payload = _read_bound_bytes(
        path, root=SOURCE_ROOT, digest=expected_sha, size=None
    )
    with io.StringIO(payload.decode("utf-8"), newline="") as handle:
        reader = csv.DictReader(handle)
        if "time" not in set(reader.fieldnames or ()):
            raise P1RunnerRefusal(f"m1_time_column_missing:{logical}")
        for row in reader:
            stamp = parse_utc(str(row.get("time") or ""), label="m1_source.time")
            if last is not None and stamp <= last:
                raise P1RunnerRefusal(f"m1_source_order_drift:{logical}")
            first = stamp if first is None else first
            last = stamp
            rows += 1
    if rows != expected_rows or first is None or last is None:
        raise P1RunnerRefusal(f"m1_source_binding_drift:{logical}")
    if (
        iso_utc(first) != str(lane_record.get("first_utc"))
        or iso_utc(last) != str(lane_record.get("last_utc"))
    ):
        raise P1RunnerRefusal(f"m1_source_bound_drift:{logical}")
    result = {
        "sha256": expected_sha,
        "expected_sha256": expected_sha,
        "authenticated": True,
        "completion_contract": {
            "schema": "gtos.p1-hash-bound-sparse-m1-completion.v1",
            "window": window,
            "path_manifest_sha256": path_manifest_sha256,
            "lane_manifest_sha256": lane_manifest_sha256,
            "sparse_no_print_minutes_valid": True,
            "civil_minute_continuity_required": False,
        },
        "start_utc": iso_utc(first),
        "end_utc": iso_utc(last),
    }
    cache[cache_key] = result
    return result


def _sidecar_identity(sidecar: Mapping[str, Any]) -> CompositeIdentity:
    if sidecar.get("schema") != "gtos-session-ck-ordered-path-sidecar-v1":
        raise P1RunnerRefusal("sidecar_schema_drift")
    return CompositeIdentity.from_row(sidecar)


def _m1_bars(sidecar: Mapping[str, Any]) -> tuple[M1Bar, ...]:
    observations = sidecar.get("ordered_path_observations")
    if not isinstance(observations, list):
        raise P1RunnerRefusal("sidecar_m1_observations_invalid")
    return tuple(
        M1Bar(
            time_utc=str(row.get("time_utc") or ""),
            open=strict_number(row.get("open"), label="sidecar.m1.open"),
            high=strict_number(row.get("high"), label="sidecar.m1.high"),
            low=strict_number(row.get("low"), label="sidecar.m1.low"),
            close=strict_number(row.get("close"), label="sidecar.m1.close"),
        )
        for row in observations
    )


def _family_stage_rows(
    *,
    identity: CompositeIdentity,
    window: str,
    source_container_sha256: str,
    source_row_sha256: str,
    stages: Sequence[tuple[str, str, str, Any]],
) -> Iterator[dict[str, Any]]:
    if tuple(item[0] for item in stages) != STAGES:
        raise P1RunnerRefusal("stage_sequence_not_exact_once_per_source")
    source_id = identity.source_id(window)
    prior_hash = source_row_sha256
    for stage, disposition, reason, output in stages:
        output_hash = canonical_sha256(output)
        yield {
            "source_id": source_id,
            "composite_identity": asdict(identity),
            "stage": stage,
            "disposition": disposition,
            "reason": reason,
            "asof_utc": identity.decision_time_utc,
            "source_container_sha256": source_container_sha256,
            "source_row_sha256": source_row_sha256,
            "input_sha256": prior_hash,
            "output_sha256": output_hash,
        }
        prior_hash = output_hash


def _non_family_stage_rows(
    identity: CompositeIdentity,
    window: str,
    *,
    source_container_sha256: str,
    source_row_sha256: str,
) -> Iterator[dict[str, Any]]:
    stages = [
        (
            stage,
            "EXPECTED_NON_FAMILY_NO_P1_MUTATION",
            "origin_family_not_current_breaker_re_entry_preserved",
            {
                "source_id": identity.source_id(window),
                "stage": stage,
                "status": "EXPECTED_NON_FAMILY_NO_P1_MUTATION",
            },
        )
        for stage in STAGES
    ]
    yield from _family_stage_rows(
        identity=identity,
        window=window,
        source_container_sha256=source_container_sha256,
        source_row_sha256=source_row_sha256,
        stages=stages,
    )


def _descriptor(path: Path, rows: int | None = None) -> dict[str, Any]:
    fd, before = _open_regular_fd(path, root=path.parent)
    digest = hashlib.sha256()
    observed_bytes = 0
    try:
        with os.fdopen(fd, "rb", closefd=False) as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                observed_bytes += len(chunk)
                digest.update(chunk)
        _verify_same_inode(path, fd, before)
    finally:
        os.close(fd)
    result: dict[str, Any] = {
        "path": path.name,
        "bytes": observed_bytes,
        "sha256": digest.hexdigest(),
    }
    if rows is not None:
        result["rows"] = rows
    return result


def _fsync_dir(path: Path) -> None:
    _reject_symlink_components(path)
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode):
        raise P1RunnerRefusal(f"fsync_target_not_directory:{path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _exclusive_rename(source: Path, destination: Path) -> None:
    """Atomically install a directory without replacing any destination."""
    _reject_symlink_components(source)
    _reject_symlink_components(destination, allow_missing_leaf=True)
    before = os.lstat(source)
    if not stat.S_ISDIR(before.st_mode):
        raise P1RunnerRefusal("staging_inode_not_directory")
    if _lexists(destination):
        raise P1RunnerRefusal("output_collision_before_exclusive_install_marker_preserved")
    source_parent = Path(os.path.abspath(os.fspath(source.parent)))
    destination_parent = Path(os.path.abspath(os.fspath(destination.parent)))
    if source_parent != destination_parent:
        raise P1RunnerRefusal("exclusive_install_requires_one_parent_dirfd")
    parent_fd = os.open(
        source_parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    )
    libc = ctypes.CDLL(None, use_errno=True)
    source_raw = os.fsencode(source.name)
    destination_raw = os.fsencode(destination.name)
    try:
        if sys.platform == "darwin" and hasattr(libc, "renameatx_np"):
            rename = libc.renameatx_np
            rename.argtypes = [
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            ]
            rename.restype = ctypes.c_int
            # RENAME_EXCL | RENAME_NOFOLLOW_ANY | RENAME_RESOLVE_BENEATH.
            result = rename(parent_fd, source_raw, parent_fd, destination_raw, 0x34)
        elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
            rename = libc.renameat2
            rename.argtypes = [
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            ]
            rename.restype = ctypes.c_int
            result = rename(parent_fd, source_raw, parent_fd, destination_raw, 1)
        else:
            raise P1RunnerRefusal(
                "dirfd_atomic_no_replace_rename_unavailable_marker_preserved"
            )
        code = ctypes.get_errno() if result != 0 else 0
    finally:
        os.close(parent_fd)
    if result != 0:
        if code in {errno.EEXIST, errno.ENOTEMPTY}:
            raise P1RunnerRefusal(
                "output_collision_during_exclusive_install_marker_preserved"
            )
        if code in {errno.ENOTSUP, errno.EINVAL, errno.ENOSYS}:
            raise P1RunnerRefusal(
                "preregistered_dirfd_exclusive_nofollow_beneath_rename_unavailable"
            )
        raise P1RunnerRefusal(f"exclusive_install_failed:{os.strerror(code)}")
    if _lexists(source):
        raise P1RunnerRefusal("exclusive_install_source_still_present")
    after = os.lstat(destination)
    if (
        (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
        or not stat.S_ISDIR(after.st_mode)
    ):
        raise P1RunnerRefusal("exclusive_install_inode_mismatch")


def _write_exclusive_json(path: Path, payload: Mapping[str, Any]) -> None:
    _reject_symlink_components(path, allow_missing_leaf=True)
    flags = (
        os.O_CREAT
        | os.O_EXCL
        | os.O_WRONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise P1RunnerRefusal(f"exclusive_json_target_exists:{path}") from exc
    raw = canonical_bytes(payload) + b"\n"
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _contains_mapping_key(value: Any, forbidden: str) -> bool:
    if isinstance(value, Mapping):
        return forbidden in value or any(
            _contains_mapping_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_mapping_key(item, forbidden) for item in value)
    return False


def _require_run_anchors(tested_source_commit: str, enabled: bool) -> None:
    if enabled is not True:
        raise P1RunnerRefusal("result_run_default_off_explicit_true_required")
    if tested_source_commit != _git("rev-parse", "HEAD"):
        raise P1RunnerRefusal("tested_source_commit_not_head")
    if _git("status", "--porcelain"):
        raise P1RunnerRefusal("result_run_requires_clean_worktree")
    parents = _git("show", "-s", "--format=%P", tested_source_commit).split()
    if parents != [BASE_SOURCE_COMMIT]:
        raise P1RunnerRefusal("tested_source_commit_parent_drift")
    changed = frozenset(_git("diff-tree", "--no-commit-id", "--name-only", "-r", tested_source_commit).splitlines())
    if changed != COMMISSIONED_PATHS:
        raise P1RunnerRefusal(f"tested_source_commit_scope_drift:{sorted(changed)}")
    prereg = _load_preregistration()
    if prereg.get("tested_source_binding") != {
        "mode": "RUN_ARGUMENT_MUST_EQUAL_EXACT_CLEAN_HEAD",
        "sole_parent": BASE_SOURCE_COMMIT,
        "commissioned_paths": sorted(COMMISSIONED_PATHS),
    }:
        raise P1RunnerRefusal("preregistration_tested_source_binding_drift")
    preflight(verify_packet_structure=True)


def run_once(*, tested_source_commit: str, enabled: bool = False) -> dict[str, Any]:
    """Execute the one authorized decode, then durably install five outputs."""
    _require_run_anchors(tested_source_commit, enabled)
    if shutil.disk_usage(OUTPUT_PARENT.parent).free < FREE_DISK_FLOOR:
        raise P1RunnerRefusal("free_disk_below_8_gib_before_run")

    # All shared authority is rebound before the irreversible run marker.  U4's
    # economic values remain opaque; only its mechanical projector is retained.
    adapter, _route_authority, profile_authority = _load_shared_authorities()
    _prereg_raw, prereg_sha = _read_stable_bytes(PREREGISTRATION_PATH, root=REPO_ROOT)
    marker = OUTPUT_PARENT.with_name(OUTPUT_PARENT.name + ".RUN_STARTED")
    stage = OUTPUT_PARENT.with_name(
        f".{OUTPUT_PARENT.name}.staging-{tested_source_commit[:12]}"
    )
    _reject_symlink_components(OUTPUT_PARENT.parent)
    _reject_symlink_components(OUTPUT_PARENT, allow_missing_leaf=True)
    _reject_symlink_components(marker, allow_missing_leaf=True)
    _reject_symlink_components(stage, allow_missing_leaf=True)
    if _lexists(OUTPUT_PARENT):
        raise P1RunnerRefusal("output_parent_preexists_before_marker")
    if _lexists(marker):
        raise P1RunnerRefusal("single_run_marker_already_exists_no_rerun")
    marker_payload = {
        "schema": "gtos.p1-offline-single-run-marker.v1",
        "tested_source_commit": tested_source_commit,
        "canonical_evidence_commit": CANONICAL_EVIDENCE_COMMIT,
        "adapter_sha256": ADAPTER_SHA256,
        "hn_evidence_commit": HN_EVIDENCE_COMMIT,
        "hn_profile_sha256": HN_PROFILE_SHA256,
        "hn_route_sha256": HN_ROUTE_SHA256,
        "packet_path": PACKET.as_posix(),
        "packet_manifest_sha256": PACKET_MANIFEST_SHA256,
        "packet_payload_root_sha256": PACKET_PAYLOAD_ROOT_SHA256,
        "preregistration_path": PREREGISTRATION_PATH.relative_to(REPO_ROOT).as_posix(),
        "preregistration_sha256": prereg_sha,
        "output_parent": OUTPUT_PARENT.as_posix(),
        "execution_authority": False,
        "activation_authority": False,
    }
    _write_exclusive_json(marker, marker_payload)
    _fsync_dir(marker.parent)

    if _lexists(stage):
        raise P1RunnerRefusal("single_run_staging_target_preexists_marker_preserved")
    os.mkdir(stage, mode=0o700)
    stage_inode = os.lstat(stage)
    _fsync_dir(stage.parent)
    ledger_path = stage / "stage_ledger.jsonl.gz"
    identities_path = stage / "identity_results.jsonl.gz"
    missed_path = stage / "missed_opportunities.jsonl.gz"
    fills_path = stage / "P1_FILL_CLASSIFICATION.jsonl.gz"

    source_count = family_count = non_family_count = stage_count = 0
    missed_count = fill_rows = 0
    authority_counts = {name: 0 for name in EXPECTED_AUTHORITY}
    classification_counts = {"FILLED": 0, "NO_FILL": 0, "NOT_EVALUABLE": 0}
    missing_reason_counts: Counter[str] = Counter()
    missing_stage_counts: Counter[str] = Counter()
    window_counts = {name: 0 for name in EXPECTED_WINDOWS}
    family_window_counts = {name: 0 for name in EXPECTED_WINDOWS}
    seen_identities: set[tuple[str, str, str, str]] = set()
    seen_source_ids: set[str] = set()
    m1_cache: dict[str, dict[str, Any]] = {}
    budget = OutputBudget()

    with (
        DeterministicJsonlGzipWriter(ledger_path, budget=budget) as ledger,
        DeterministicJsonlGzipWriter(identities_path, budget=budget) as identities,
        DeterministicJsonlGzipWriter(missed_path, budget=budget) as missed,
        DeterministicJsonlGzipWriter(fills_path, budget=budget) as fills,
    ):
        for window, pool_relative, pool_sha, pool_size in POOL_BINDINGS:
            pool_path = REPO_ROOT / pool_relative
            side_relative, side_sha, side_size = SIDECAR_BINDINGS[window]
            side_path = REPO_ROOT / side_relative
            pool_payload = _read_bound_bytes(
                pool_path, root=REPO_ROOT, digest=pool_sha, size=pool_size
            )
            side_payload = _read_bound_bytes(
                side_path, root=REPO_ROOT, digest=side_sha, size=side_size
            )
            authority_manifest = _window_authority(window)
            inventory = authority_manifest["source_inventory"]
            lane_m1 = authority_manifest["lane_m1_sources"]
            lane_ticks = authority_manifest["lane_tick_sources"]
            pool_iterator = _iter_full_jsonl(pool_payload, label=pool_relative)
            side_iterator = _iter_full_jsonl(side_payload, label=side_relative)
            tick_cache: dict[str, TickArchive] = {}
            for row_number in range(1, EXPECTED_WINDOWS[window] + 1):
                try:
                    pool_row = next(pool_iterator)
                    sidecar = next(side_iterator)
                except StopIteration as exc:
                    raise P1RunnerRefusal(
                        f"pool_or_sidecar_ended_early:{window}:{row_number}"
                    ) from exc
                identity = CompositeIdentity.from_row(pool_row)
                if _sidecar_identity(sidecar) != identity:
                    raise P1RunnerRefusal(
                        f"pool_sidecar_identity_mismatch:{window}:{row_number}"
                    )
                decision = parse_utc(identity.decision_time_utc, label="run.decision")
                expiry = decision + timedelta(minutes=HORIZON_MINUTES)
                if parse_utc(sidecar.get("horizon_end_utc"), label="sidecar.horizon") != expiry:
                    raise P1RunnerRefusal(f"sidecar_horizon_drift:{window}:{row_number}")
                identity_key = identity.key()
                source_id = identity.source_id(window)
                if identity_key in seen_identities:
                    raise P1RunnerRefusal("postdecode_duplicate_global_composite_identity")
                if source_id in seen_source_ids:
                    raise P1RunnerRefusal("postdecode_duplicate_global_source_id")
                seen_identities.add(identity_key)
                seen_source_ids.add(source_id)
                source_row_sha = canonical_sha256(pool_row)
                source_count += 1
                window_counts[window] += 1

                if pool_row.get("origin_family") != ORIGIN_FAMILY:
                    non_family_count += 1
                    rows = tuple(
                        _non_family_stage_rows(
                            identity,
                            window,
                            source_container_sha256=pool_sha,
                            source_row_sha256=source_row_sha,
                        )
                    )
                    if len(rows) != len(STAGES):
                        raise P1RunnerRefusal("non_family_stage_sequence_drift")
                    for stage_row in rows:
                        ledger.write(stage_row)
                        stage_count += 1
                    redacted_account = {
                        "scope": "MECHANICAL_ONLY",
                        "promotion_or_veto": False,
                        "status": "NOT_APPLICABLE_NON_FAMILY",
                    }
                    if _contains_mapping_key(redacted_account, "economics"):
                        raise P1RunnerRefusal("redacted_account_economics_key_forbidden")
                    identities.write(
                        {
                            "schema": "gtos.p1-offline-identity-result.v1",
                            "source_id": source_id,
                            "source_container_sha256": pool_sha,
                            "source_row_sha256": source_row_sha,
                            "composite_identity": asdict(identity),
                            "window": window,
                            "family_status": "EXPECTED_NON_FAMILY_NO_P1_MUTATION",
                            "fill": None,
                            "exit": None,
                            "ftmo_economics": None,
                            "redacted_account": redacted_account,
                        }
                    )
                    continue

                family_count += 1
                family_window_counts[window] += 1
                candidate, repaired, permission, route_capture = _candidate_route(
                    adapter, pool_row, identity, window=window
                )
                intent = limit_intent(
                    identity,
                    repaired_side=str(repaired.get("side") or ""),
                    entry=repaired.get("entry_price"),
                    stop=repaired.get("stop_loss"),
                    target=repaired.get("take_profit_1"),
                )
                accounts = _account_preimages(
                    adapter, profile_authority, repaired, identity
                )
                redacted_account = accounts["redacted_account"]
                if _contains_mapping_key(redacted_account, "economics"):
                    raise P1RunnerRefusal("redacted_account_economics_key_forbidden")

                symbol_authority = inventory.get(identity.symbol)
                if not isinstance(symbol_authority, Mapping):
                    raise P1RunnerRefusal(
                        f"symbol_source_authority_missing:{window}:{identity.symbol}"
                    )
                m1_record = symbol_authority.get("m1")
                lane_m1_record = lane_m1.get(identity.symbol)
                if not isinstance(m1_record, Mapping) or not isinstance(
                    lane_m1_record, Mapping
                ):
                    raise P1RunnerRefusal(
                        f"m1_source_authority_missing:{window}:{identity.symbol}"
                    )
                if (
                    sidecar.get("source_path") != m1_record.get("path")
                    or sidecar.get("source_sha256") != m1_record.get("sha256")
                ):
                    raise P1RunnerRefusal(
                        f"sidecar_m1_binding_drift:{window}:{row_number}"
                    )
                m1_binding = _m1_binding(
                    m1_record,
                    lane_m1_record,
                    window=window,
                    path_manifest_sha256=authority_manifest["path_manifest_sha256"],
                    lane_manifest_sha256=authority_manifest["lane_manifest_sha256"],
                    cache=m1_cache,
                )

                pointer = sidecar.get("ordered_tick_source")
                expected_tick = symbol_authority.get("tick")
                lane_tick_record = lane_ticks.get(identity.symbol)
                archive: TickArchive | None
                if pointer is None:
                    if expected_tick is not None:
                        raise P1RunnerRefusal(
                            f"sidecar_tick_pointer_missing:{window}:{row_number}"
                        )
                    archive = None
                else:
                    if (
                        not isinstance(pointer, Mapping)
                        or not isinstance(expected_tick, Mapping)
                        or not isinstance(lane_tick_record, Mapping)
                    ):
                        raise P1RunnerRefusal(
                            f"sidecar_tick_pointer_unexpected:{window}:{row_number}"
                        )
                    expected_rows = expected_tick.get("rows")
                    if (
                        pointer.get("path") != expected_tick.get("path")
                        or pointer.get("source_sha256") != expected_tick.get("sha256")
                        or pointer.get("row_count") != expected_rows
                        or pointer.get("path") != lane_tick_record.get("lane_relpath")
                        or pointer.get("source_sha256") != lane_tick_record.get("sha256")
                        or pointer.get("row_count") != lane_tick_record.get("row_count")
                    ):
                        raise P1RunnerRefusal(
                            f"sidecar_tick_binding_drift:{window}:{row_number}"
                        )
                    cache_key = f"{pointer['path']}:{pointer['source_sha256']}"
                    archive = tick_cache.get(cache_key)
                    if archive is None:
                        archive = TickArchive.load(pointer)
                        if (
                            archive.start_utc != lane_tick_record.get("first_utc")
                            or archive.end_utc != lane_tick_record.get("last_utc")
                        ):
                            raise P1RunnerRefusal(
                                f"tick_archive_lane_bounds_drift:{window}:{identity.symbol}"
                            )
                        tick_cache[cache_key] = archive

                fill_authority = resolve_fill_authority(
                    identity,
                    tick_pointer_present=archive is not None,
                    archive_start_utc=archive.start_utc if archive else None,
                    archive_end_utc=archive.end_utc if archive else None,
                )
                authority_counts[fill_authority] += 1
                ticks: list[TickQuote] = []
                if fill_authority == "FULL_TICK":
                    if archive is None:
                        raise P1RunnerRefusal("full_tick_archive_missing")
                    ticks = archive.slice(decision, expiry)
                    fill = classify_fill(
                        intent,
                        authority=fill_authority,
                        ticks=ticks,
                        authority_start_utc=archive.start_utc,
                        authority_end_utc=archive.end_utc,
                    )
                elif fill_authority == "M1_ONLY":
                    fill = classify_fill(
                        intent,
                        authority=fill_authority,
                        m1_parts=[_m1_bars(sidecar)],
                        m1_authority_bindings=[m1_binding],
                    )
                else:
                    fill = classify_fill(intent, authority=fill_authority)
                classification_counts[fill.status] += 1
                fill_rows += 1
                fill_record = {
                    "schema": "gtos.p1-fill-classification.v1",
                    "source_id": source_id,
                    "source_container_sha256": pool_sha,
                    "source_row_sha256": source_row_sha,
                    "window": window,
                    "composite_identity": asdict(identity),
                    "repaired_candidate_id": repaired["candidate_id"],
                    "fixed_candidate": FIXED_CANDIDATE,
                    "transform_id": TRANSFORM_ID,
                    "intent": intent,
                    "classification": asdict(fill),
                }
                fills.write(fill_record)

                miss_stage: str | None = None
                miss_reason: str | None = None
                cost_r: float | None = None
                hde_output: dict[str, Any]
                exit_result: ExitClassification | None = None
                exit_output: dict[str, Any]
                if fill.status == "NOT_EVALUABLE":
                    miss_stage, miss_reason = "fill_or_no_fill", fill.reason
                    hde_output = {
                        "state": "not_reached_prior_stage_miss",
                        "authoritative_cost_r": None,
                    }
                    exit_output = {
                        "status": "NOT_REACHED_PRIOR_STAGE_MISS",
                        "reason": fill.reason,
                    }
                    cost_disposition = exit_disposition = "NOT_REACHED_PRIOR_STAGE_MISS"
                    cost_reason = exit_reason = f"prior_stage_miss:fill_or_no_fill:{fill.reason}"
                elif fill.status == "NO_FILL":
                    hde_output = {
                        "state": "not_applicable_no_fill",
                        "authoritative_cost_r": None,
                    }
                    exit_output = {
                        "status": "NO_FILL_TERMINAL",
                        "exit_reason": "not_filled",
                    }
                    cost_disposition = "NOT_APPLICABLE_NO_FILL"
                    cost_reason = "no_fill_has_no_realized_cost_authority"
                    exit_disposition = "NO_FILL_TERMINAL"
                    exit_reason = "explicit_no_fill_terminal"
                else:
                    hde_projected = adapter.project_hde_cost(pool_row)
                    if not isinstance(hde_projected, Mapping):
                        raise P1RunnerRefusal("adapter_hde_projection_not_mapping")
                    hde_output = dict(hde_projected)
                    if hde_output.get("state") != "complete":
                        reasons = [str(item) for item in hde_output.get("refusal_reasons") or []]
                        exact = ",".join(reasons) if reasons else "component_authority_unavailable"
                        miss_stage = "hde_cost"
                        miss_reason = f"NOT_EVALUABLE_HDE_{hde_output.get('state')}:{exact}"
                        cost_disposition = "NOT_EVALUABLE"
                        cost_reason = miss_reason
                        exit_disposition = "NOT_REACHED_PRIOR_STAGE_MISS"
                        exit_reason = f"prior_stage_miss:hde_cost:{miss_reason}"
                        exit_output = {
                            "status": "NOT_REACHED_PRIOR_STAGE_MISS",
                            "reason": miss_reason,
                        }
                    else:
                        source_cost = strict_number(
                            hde_output.get("authoritative_cost_r"),
                            label="hde.authoritative_cost_r",
                        )
                        if source_cost < 0:
                            raise P1RunnerRefusal("hde_authoritative_cost_negative")
                        cost_r = source_cost / STOP_DISTANCE_D
                        hde_output["source_geometry_cost_r"] = source_cost
                        hde_output["source_stop_distance_D"] = STOP_DISTANCE_D
                        hde_output["p1_rebased_cost_r"] = cost_r
                        cost_disposition = "COMPLETE"
                        cost_reason = "adapter_hde_complete_rebased_by_stop_distance_D"
                        try:
                            exit_result = evaluate_tick_exit(
                                intent, fill, ticks, cost_r=cost_r
                            )
                        except Exception as exc:
                            miss_stage = "hdf_exit_or_terminal"
                            miss_reason = (
                                f"NOT_EVALUABLE_HDF:{type(exc).__name__}:{exc}"
                            )
                            exit_disposition = "NOT_EVALUABLE"
                            exit_reason = miss_reason
                            exit_output = {
                                "status": "NOT_EVALUABLE",
                                "reason": miss_reason,
                            }
                        else:
                            exit_disposition = "TERMINAL_CAPTURED"
                            exit_reason = exit_result.reason
                            exit_output = asdict(exit_result)

                if miss_reason is not None and miss_stage is not None:
                    missed_count += 1
                    missing_reason_counts[miss_reason] += 1
                    missing_stage_counts[miss_stage] += 1
                    missed.write(
                        {
                            "schema": "gtos.p1-missed-opportunity.v1",
                            "source_id": source_id,
                            "source_container_sha256": pool_sha,
                            "source_row_sha256": source_row_sha,
                            "composite_identity": asdict(identity),
                            "window": window,
                            "first_missing_stage": miss_stage,
                            "reason": miss_reason,
                        }
                    )

                account_compatible = all(
                    value["mechanical_compatible"] for value in accounts.values()
                )
                order_disposition = (
                    "PROJECTED_INERT_COMPATIBLE"
                    if account_compatible
                    else "PROJECTED_INERT_WITH_MISMATCHES"
                )
                stages = (
                    (
                        "source_opportunity",
                        "OBSERVED",
                        "source_opportunity_identity_and_hash_bound",
                        {
                            "source_id": source_id,
                            "source_row_sha256": source_row_sha,
                            "origin_family": ORIGIN_FAMILY,
                        },
                    ),
                    (
                        "candidate_generation",
                        "GENERATED_ONE",
                        "exactly_one_minimal_source_candidate_generated_by_adapter",
                        candidate,
                    ),
                    (
                        "fixed_breaker_transform",
                        "APPLIED",
                        TRANSFORM_ID,
                        repaired,
                    ),
                    (
                        "permission",
                        "PERMITTED",
                        "synthetic_preregistered_known_answer_not_historical",
                        permission,
                    ),
                    (
                        "dynamic_router",
                        "ADMIT",
                        "fixed_preregistered_member_admit_unchanged",
                        route_capture["route"],
                    ),
                    (
                        "scheduler_capture_only",
                        "CAPTURED_NO_EFFECT",
                        "scheduler_telemetry_captured_without_route_effect",
                        route_capture["capture"],
                    ),
                    (
                        "order_preimage",
                        order_disposition,
                        "both_account_scopes_mechanically_compared",
                        accounts,
                    ),
                    (
                        "fill_or_no_fill",
                        fill.status,
                        fill.reason,
                        asdict(fill),
                    ),
                    ("hde_cost", cost_disposition, cost_reason, hde_output),
                    (
                        "hdf_exit_or_terminal",
                        exit_disposition,
                        exit_reason,
                        exit_output,
                    ),
                    (
                        "unchanged_frozen_gate_disposition",
                        "UNCHANGED",
                        adapter.FROZEN_GATE_DISPOSITION,
                        {
                            "fixed_breaker_member": FIXED_CANDIDATE,
                            "disposition": adapter.FROZEN_GATE_DISPOSITION,
                            "armed": False,
                        },
                    ),
                )
                emitted = tuple(
                    _family_stage_rows(
                        identity=identity,
                        window=window,
                        source_container_sha256=pool_sha,
                        source_row_sha256=source_row_sha,
                        stages=stages,
                    )
                )
                if len(emitted) != len(STAGES):
                    raise P1RunnerRefusal("family_stage_sequence_drift")
                for stage_row in emitted:
                    ledger.write(stage_row)
                    stage_count += 1

                gross_r = exit_result.gross_r if exit_result is not None else None
                net_r = exit_result.net_r if exit_result is not None else None
                identities.write(
                    {
                        "schema": "gtos.p1-offline-identity-result.v1",
                        "source_id": source_id,
                        "source_container_sha256": pool_sha,
                        "source_row_sha256": source_row_sha,
                        "composite_identity": asdict(identity),
                        "window": window,
                        "family_status": "P1_FIXED_BREAKER_MEMBER",
                        "permission_evidence_class": PERMISSION_EVIDENCE_CLASS,
                        "fill": asdict(fill),
                        "exit": asdict(exit_result) if exit_result else None,
                        "ftmo_economics": {
                            "scope": "SOLE_ECONOMIC_ROLE",
                            "authoritative_cost_r": cost_r,
                            "gross_r": gross_r,
                            "net_r": net_r,
                        },
                        "operator_profile": accounts[
                            "operator_profile"
                        ],
                        "redacted_account": redacted_account,
                    }
                )

            try:
                next(pool_iterator)
                raise P1RunnerRefusal(f"pool_has_extra_rows:{window}")
            except StopIteration:
                pass
            try:
                next(side_iterator)
                raise P1RunnerRefusal(f"sidecar_has_extra_rows:{window}")
            except StopIteration:
                pass

    if authority_counts != EXPECTED_AUTHORITY:
        raise P1RunnerRefusal(
            f"postdecode_fill_authority_drift_marker_and_staging_preserved:{authority_counts}"
        )
    if (
        source_count != EXPECTED_TOTAL
        or family_count != EXPECTED_FAMILY
        or non_family_count != EXPECTED_NON_FAMILY
        or stage_count != EXPECTED_STAGE_ROWS
        or stage_count != source_count * len(STAGES)
        or fill_rows != EXPECTED_FAMILY
        or window_counts != EXPECTED_WINDOWS
        or family_window_counts != EXPECTED_FAMILY_WINDOWS
        or len(seen_identities) != source_count
        or len(seen_source_ids) != source_count
        or sum(missing_reason_counts.values()) != missed_count
        or sum(missing_stage_counts.values()) != missed_count
    ):
        raise P1RunnerRefusal("postdecode_complete_denominator_drift_marker_preserved")
    if adapter.FROZEN_GATE_DISPOSITION != "RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED":
        raise P1RunnerRefusal("postdecode_frozen_gate_disposition_drift")

    terminal = "P1_OFFLINE_NOT_EVALUABLE_HIGHER_INFORMATION_STOP"
    descriptors = [
        _descriptor(ledger_path, stage_count),
        _descriptor(identities_path, source_count),
        _descriptor(missed_path, missed_count),
        _descriptor(fills_path, fill_rows),
    ]
    payload_root = canonical_sha256(
        {"schema": "gtos.p1-offline-result-payload.v1", "files": descriptors}
    )
    exact_stop_reasons = (
        dict(sorted(missing_reason_counts.items()))
        if missed_count
        else {adapter.FROZEN_GATE_DISPOSITION: 1}
    )
    manifest = {
        "schema": "gtos.p1-offline-run-manifest.v1",
        "status": terminal,
        "tested_source_commit": tested_source_commit,
        "canonical_evidence_commit": CANONICAL_EVIDENCE_COMMIT,
        "adapter_binding": {
            "path": ADAPTER_RELATIVE,
            "sha256": ADAPTER_SHA256,
            "bytes": ADAPTER_BYTES,
        },
        "hn_evidence_commit": HN_EVIDENCE_COMMIT,
        "hn_profile_sha256": HN_PROFILE_SHA256,
        "hn_route_sha256": HN_ROUTE_SHA256,
        "packet_path": PACKET.as_posix(),
        "packet_manifest_sha256": PACKET_MANIFEST_SHA256,
        "packet_payload_root_sha256": PACKET_PAYLOAD_ROOT_SHA256,
        "preregistration_sha256": prereg_sha,
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": True,
        "broker_orders": 0,
        "complete_denominator": {
            "source_rows": source_count,
            "family_rows": family_count,
            "non_family_rows": non_family_count,
            "stage_rows": stage_count,
            "window_counts": window_counts,
            "family_window_counts": family_window_counts,
            "globally_unique_composite_identities": len(seen_identities),
            "globally_unique_source_ids": len(seen_source_ids),
            "exact_stage_sequence_once_per_source": True,
        },
        "fill_authority_counts": authority_counts,
        "fill_authority_expected": EXPECTED_AUTHORITY,
        "fill_authority_drift": False,
        "classification_counts": classification_counts,
        "missing_rows": missed_count,
        "missing_reason_counts": dict(sorted(missing_reason_counts.items())),
        "missing_stage_counts": dict(sorted(missing_stage_counts.items())),
        "higher_information_stop_reason_counts": exact_stop_reasons,
        "gate_status": adapter.FROZEN_GATE_DISPOSITION,
        "permission_evidence_class": PERMISSION_EVIDENCE_CLASS,
        "redacted_account_role": "MECHANICAL_ONLY_NEVER_ECONOMIC_VERDICT",
        "u5_volume_status": adapter.VOLUME_STATUS,
        "partial_economic_summary": None,
        "online_uncompressed_output_bytes": budget.observed_uncompressed_bytes,
        "online_output_limit_bytes": budget.limit_bytes,
        "output_payload_root_sha256": payload_root,
        "files": descriptors,
    }
    manifest_path = stage / "RUN_MANIFEST.json"
    budget.consume(len(canonical_bytes(manifest)) + 1)
    _write_exclusive_json(manifest_path, manifest)
    expected_inventory = {
        "stage_ledger.jsonl.gz",
        "identity_results.jsonl.gz",
        "missed_opportunities.jsonl.gz",
        "P1_FILL_CLASSIFICATION.jsonl.gz",
        "RUN_MANIFEST.json",
    }
    if set(path.name for path in stage.iterdir()) != expected_inventory:
        raise P1RunnerRefusal("result_output_inventory_drift_marker_preserved")
    current_stage = os.lstat(stage)
    if (current_stage.st_dev, current_stage.st_ino) != (
        stage_inode.st_dev,
        stage_inode.st_ino,
    ):
        raise P1RunnerRefusal("staging_inode_changed_marker_preserved")
    _fsync_dir(stage)
    output_bytes = sum(path.stat().st_size for path in stage.iterdir())
    if (
        output_bytes > OUTPUT_BYTE_LIMIT
        or budget.observed_uncompressed_bytes > OUTPUT_BYTE_LIMIT
        or shutil.disk_usage(stage.parent).free < FREE_DISK_FLOOR
    ):
        raise P1RunnerRefusal("result_resource_limit_or_disk_floor_failed_marker_preserved")
    if _lexists(OUTPUT_PARENT):
        raise P1RunnerRefusal("output_collision_before_install_marker_preserved")
    _exclusive_rename(stage, OUTPUT_PARENT)
    if set(path.name for path in OUTPUT_PARENT.iterdir()) != expected_inventory:
        raise P1RunnerRefusal("installed_output_inventory_drift")
    _fsync_dir(OUTPUT_PARENT)
    _fsync_dir(OUTPUT_PARENT.parent)
    manifest_descriptor = _descriptor(OUTPUT_PARENT / "RUN_MANIFEST.json")
    return {
        "status": terminal,
        "output_parent": OUTPUT_PARENT.as_posix(),
        "output_payload_root_sha256": payload_root,
        "run_manifest_sha256": manifest_descriptor["sha256"],
        "execution_authority": False,
        "activation_authority": False,
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight")
    pre.add_argument("--skip-structural-packet", action="store_true", help=argparse.SUPPRESS)
    run = sub.add_parser("run")
    run.add_argument("--tested-source-commit", required=True)
    run.add_argument("--enable-result-bearing-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "preflight":
        result = preflight(verify_packet_structure=not args.skip_structural_packet)
    else:
        result = run_once(
            tested_source_commit=args.tested_source_commit,
            enabled=args.enable_result_bearing_run,
        )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
