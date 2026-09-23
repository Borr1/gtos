"""Build the broker-inert Wave 20 P1 predecision source packet.

This module is intentionally narrower than the replay stack.  It reads only
the commissioned January/April/May opportunity identity fields, verifies the
preserved Wave 16 true-UTC M15 authority, and reconstructs the exact market
state used by the hash-bound broader-origin generator.  It never reads a path
result, computes economics, selects a candidate, or imports a live-capable
execution surface.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import copy
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE20_ROOT = REPO_ROOT / "docs/audits/fable5-vision-audit-20260725/phase20"
DEFAULT_SOURCE_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
DEFAULT_PACKET_PARENT = Path(
    "/Users/borr/GTOSActive/p1-upstream-source-packet-hold-20260802"
)

SOURCE_CONTROL_FIELDS = (
    "candidate_id",
    "symbol",
    "side",
    "direction",
    "decision_time_utc",
    "kill_zone",
    "origin_family",
    "framework",
    "route_family",
)
IDENTITY_FIELDS = ("candidate_id", "symbol", "side", "decision_time_utc")
EXPECTED_IDENTITY_COUNT = 73_999
EXPECTED_WINDOW_COUNTS = {"january": 27_658, "april": 25_056, "may": 21_285}
WINDOW_BOUNDS = {
    "january": ("2026-01-01", "2026-01-30"),
    "april": ("2026-04-01", "2026-04-30"),
    "may": ("2026-05-01", "2026-05-30"),
}
MIN_FREE_BYTES = 8 * 1024**3
M15_LOOKBACK = 672
H1_LOOKBACK = 168
MIN_CLOSED_M15 = 51
BAR_SCHEMA = ("time", "open", "high", "low", "close", "volume")
RESULT_USE_STATUS = "SOURCE_CONTROL_ONLY_NO_OUTCOME_READ"
IMMUTABLE_HN_SOURCE_COMMIT = "f59fbb829a5561b7e7b78bed324d67a8c01d6e74"

POOL_SPECS = (
    {
        "window": "january",
        "path": "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/"
        "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz",
        "sha256": "ee920fb0e28713f28cf85322d6b6494beef07c27235db9e6ba59dd6e5097fc8f",
        "bytes": 5_696_917,
        "rows": 27_658,
    },
    {
        "window": "april",
        "path": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_APRIL_S0R0_POOL_V1.jsonl.gz",
        "sha256": "d587e99ebdbc0f56b3501719e05dfec45902e9013ee8c32392e344bc51c9e4d9",
        "bytes": 5_504_482,
        "rows": 25_056,
    },
    {
        "window": "may",
        "path": "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/"
        "CS_MAY_S0R0_POOL_V1.jsonl.gz",
        "sha256": "1bba6662644d0424ff5a360f987ddd81bb1b0f176b7547b6626853d166cb5633",
        "bytes": 4_600_824,
        "rows": 21_285,
    },
)

COMMISSIONED_SOURCE_PAYLOADS = (
    ("docs/audits/fable5-vision-audit-20260725/phase18/receipts/CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json", "87e8a086565ef9a2fd20aca55b4ed575dc48cbd5f07bcf3ade2ada74f9882c85", 9_647),
    (POOL_SPECS[0]["path"], POOL_SPECS[0]["sha256"], POOL_SPECS[0]["bytes"]),
    ("docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "ffa2a2151e79ab81202fab07706f859579e453e0b00784c1e69b381903e9ba61", 34_134_117),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_APRIL_S0R0_POOL_V1.json", "8665b88e65902d2ee982f382a7d23ceaf045a2e8e7e657d644376d86c84f739c", 8_633),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_APRIL_PATH_POOL_V1.json", "5fc38c24746763d943619f6b8b6e3ac9ffa64b34cbe0a8fb73a024556c88e102", 10_147),
    (POOL_SPECS[1]["path"], POOL_SPECS[1]["sha256"], POOL_SPECS[1]["bytes"]),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_APRIL_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "eccadb15d5e6a3a97b178b2e3267b79e5792feeca49f61c157ba86bca05ad2cd", 30_817_431),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_MAY_S0R0_POOL_V1.json", "d126bbab4f1399945343c403c76be1c98ab38d4e249e1e3eeb0dc05575c6b38e", 8_404),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/CS_MAY_PATH_POOL_V1.json", "803cf08ce72f0ce6745f92f8b02a08ba796f51707fc98a611c57f8ab61d6c1e5", 9_371),
    (POOL_SPECS[2]["path"], POOL_SPECS[2]["sha256"], POOL_SPECS[2]["bytes"]),
    ("docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/CS_MAY_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz", "bdab3988ce6960a6e25b29a29ca4bd1498698c0495222191c34e00c0d6baf5b4", 26_415_775),
)

SOURCE_MANIFEST_BINDINGS = {
    "LANE_INPUT_REGISTRY.json": "6415ae522dc48cd85f33a5f35223ce375c07214ad4416df60502d2ec0f10b5de",
    "SOURCE_CATALOG.json": "a1a8c5d05a87d1e5a486bdcfea2b23ac082cdb899da51ec2f3e45a37269582e1",
    "manifests/january_2026.json": "74ee97e4d379854697920abd7a4ee22693dc2ab72b922e0756b1342053fa5fbc",
    "manifests/april_2026.json": "3940c286fed76489bc748cb58453f5172bd32da69c7900df2b5454ac34723344",
    "manifests/may_2026.json": "23ebf0592746c55811a5457d3d120460c80ed317c8a5a51637be4579238edf7f",
}

CODE_AUTHORITY_BINDINGS = {
    "src/__init__.py": "1bcd101c48c28c58352dd2211955e607bc83d821b626b007d7b5136bf3e638a2",
    "src/components/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "src/components/broader_origin_generators.py": "6e274d22a72c945fa495c2b85408f0495acf6158caa2edb0d34bae108b859fba",
    "src/components/market_state.py": "c59e1d5ea2e4f2758129bca6b67b1ed86379e3278e5c0d44321542425fc680ee",
    "src/components/current_breaker_re_entry_repair.py": "465ae93d54ee532021f16963e0cc956f5fee26e5c79276d09a636c634cc7192b",
    "src/components/candidate_geometry.py": "d16c953346d067502d80013c03bc0d00dd9f314f31902f3bef3f86d43ec15855",
    "src/components/poi_state_contract.py": "7f24b0d8b9280b0a62c26a73f137c5437bfbf274cda114237ea648d0b60d10fc",
    "src/components/poi_execution_lifecycle.py": "224ee0a62b0e423f070ddca8198078056a4cb51b695b86077eab9146949a3351",
    "src/components/structure_detector_shadow_logger.py": "870fa9c17c83ba1ab693de77220eaa88824dee7a1eb1783e39303469071259b9",
    "src/models/market_state_models.py": "65c752ed3301ced7c3898643d178de1b2f7b8f62f6107e6227ec8722b45dc438",
    "src/models/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "src/research_infra/__init__.py": "37700001021d71975d2d55ff3609a36da6d35ff16ff9c7a3e76e32dade133d9b",
    "src/research_infra/train_engine/__init__.py": "d9ae15c68e691d33c3ec5b869c6a575fe1bcd44ad91b9bf1b657272618698de6",
    "src/utils/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "src/utils/file_io.py": "8b91a5e7808a5091b532cd4383a0869dc9760ae3668e050bbf0a02c5973a2704",
    "src/utils/jsonl_rotation.py": "50287ee4aa4e0c91ac0345f69d5a25355577d75571e943f78b2c2f4763d031a7",
    "src/utils/broker_clock.py": "0f97bbb64bc55b0213e47a018c2e884d83b2059b61de7941a171fd3cf2fef552",
    "src/research_infra/replay_acceleration_slice.py": "5736302c6a3efe32a40ca6e2f205448eb6ff7ab1a78f63e9b9c00ff54679008b",
    "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py": "9733f402149dba5d65ac513476495b6c3e84a813cb8f3c0587238eeb5e3884c6",
    "src/research_infra/v4_timewarp_simulated_live_research_loop.py": "824cf572b33f96cf3ff00cb979d3c60035ce1e8623df03c30937162ffa30cc24",
    "config/agent_config.yaml": "175f6b3bc1a692a5c5add776845281ee92fad71e11074e0a3f38d72a619eff7d",
    "config/profiles/operator_profile.yaml": "ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8",
    "config/profiles/redacted_account.yaml": "b856f0ee7f13c59dd407949c6937275da57c3e797ab2bae256755560bbd21305",
}

IMMUTABLE_EVIDENCE_AUTHORITIES = {
    "hg_preregistration": {
        "commit": "6b72de84d27e10563da102237be46e5a0180c7d6",
        "parent": "7c494e73a5504615ff6ca917926760cf17697cff",
        "artifacts": [
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/WAVE20_SCIENCE_PREREGISTRATION.md",
                "sha256": "078209d0226bf428d0767e175293f23a72c11f91726b221a5c8cb6f8c71d3735",
                "bytes": 26_164,
            },
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/WAVE20_SCIENCE_PREREGISTRATION.json",
                "sha256": "684933c6641c31056146be0e4598d05b25676aa8e3b83ccc054e92ce0668e90b",
                "bytes": 92_694,
            },
        ],
    },
    "hk_evidence_closeout": {
        "commit": "11594419a197e278263565ac7677ecfc3e317c31",
        "parent": "a1cf205de52a7f279932e4436196a255ae5e7b9b",
        "artifacts": [
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_IMPLEMENTATION_COMMISSION.json",
                "sha256": "f46c376872aeea6a5c5c513c5575e090fcdf0d815c42493a95454c10bc6c4ec8",
                "bytes": 20_503,
            },
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HK_COMPLETE.json",
                "sha256": "b9aeac7fc8e7c77e63565bbfdb13f73bfc5cfd8280ef501dab7f009dcad02591",
                "bytes": 8_086,
            },
        ],
    },
    "hl_evidence_closeout": {
        "commit": "5c94d2caa8c0764fccd6fc8dc1f353a83d6ef094",
        "parent": "41534770fa338f12b34d79c9625fd406219a41fe",
        "artifacts": [
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_IMPLEMENTATION.json",
                "sha256": "c6b6975191a52fd43a2bc7ae4fb58b0736f09c9f795ca7710622b5d5fe885222",
                "bytes": 10_963,
            },
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_SOURCE_CONFORMANCE.json",
                "sha256": "6e2266875f8def65815fd39a911e856a7fb672e5cd6fa9f4be4878b21b2c14e8",
                "bytes": 17_646,
            },
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HL_COMPLETE.json",
                "sha256": "f3b8ebd52c8331d058266469536c4a535e5ac6bed073068f5b1fbc32f7da0afa",
                "bytes": 7_537,
            },
        ],
    },
    "hm_evidence_closeout": {
        "commit": "ec4555696b21e50a928106ebf0f9089f9a8f2538",
        "parent": "1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51",
        "artifacts": [
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_ADAPTER_INDEPENDENT_FALSIFICATION.json",
                "sha256": "11f860b790e8aed897c6510b034b77166e1dbb50768f80c0941b8d93dbd81d80",
                "bytes": 27_849,
            },
            {
                "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HM_COMPLETE.json",
                "sha256": "606eb58779d859b81ab43275d2c9ea8ba789977cf37aa66c06727d40c284c186",
                "bytes": 6_628,
            },
        ],
    },
    "hn_evidence_closeout": {
        "commit": "97d4c7da1d67314e1474225b5d8484d782e5750e",
        "parent": "f59fbb829a5561b7e7b78bed324d67a8c01d6e74",
        "artifacts": [
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HN_CONTEXT_ANCHOR.md", "sha256": "a55529791254999ca80b3ec3817a7b3124d8b70b91196c6a2f54ad9037d0ed93", "bytes": 4_020},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/SESSION_HN_P1_UPSTREAM_RECONSTRUCTION_RESULT.md", "sha256": "c711b706127670439295e7091d66c7136ed55bae03b14c0b35d69ce9de4d0755", "bytes": 8_751},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HN_AB_RECEIPT.md", "sha256": "f1b5c161f652b142e9436b016b313cfc72faa4c28c2513162a1c8e489654767c", "bytes": 1_779},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/SESSION_HN_COMPLETE.json", "sha256": "a9e66330d79ab611303d22ea4102a2d3b3d8c0627431264d52d7086c6f96da5f", "bytes": 11_548},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json", "sha256": "47fe19e1743a83ffd69fcb0c7948a76e8a2ac0ac1d7c5561996d1306f04e0d8a", "bytes": 40_171},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_INERT_ROUTE_PARAMETER_BUNDLE.json", "sha256": "988a139e21bf8621a84ddafbfaff4cd9dfb39bcebf2ab6d9d228d9ffdffa4b52", "bytes": 12_265},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_SOURCE_SEARCH_AND_RECONSTRUCTION_LEDGER.json", "sha256": "8e8c7f442feb92d3907c58bf0cb9aefe4d49a44fbe0579a3f021837b98313956", "bytes": 44_305},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_SOURCE_COVERAGE.json", "sha256": "53816ef4dddae4758be86001eae200bb594210c53953dcdea3fed0cfb28dc020", "bytes": 3_321},
            {"path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/P1_UPSTREAM_SOURCE_PACKET_MANIFEST.json", "sha256": "6ca34c80781de72acdcc2377f105be2895ce29932691e880a3469dfc2674f25d", "bytes": 46_353},
        ],
    },
}

EVIDENCE_ANCESTRY_ROLES = {
    "hg_preregistration": "SOURCE_ANCESTOR_AND_IMMUTABLE_PREREGISTRATION_AUTHORITY",
    "hk_evidence_closeout": "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED",
    "hl_evidence_closeout": "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED",
    "hm_evidence_closeout": "AUTHORITY_ONLY_NOT_MERGED_OR_REBASED",
    "hn_evidence_closeout": "AUTHORITY_ONLY_EVIDENCE_CLOSEOUT_NOT_SOURCE_ANCESTRY",
}

FIXED_BREAKER_MEMBER_CANONICAL_SHA256 = (
    "0de66ebe5b67e7b3352d98624acb50c69ab116b1c46d58c422b887e5583a650f"
)
B0_BREAKER_ROUTE_BINDING = {
    "commit": "11594419a197e278263565ac7677ecfc3e317c31",
    "path": "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/B0_BREAKER_ROUTE.json",
    "bytes": 3_482,
    "sha256": "4befaece894d3c8f05f6d8ab1d3abb4a25e0646cac9a2ea491614b9a1adeaeef",
    "json_pointer": "/candidate/family_member_record",
    "canonicalization": "json_sort_keys_compact_utf8_no_trailing_newline",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "MetaTrader5",
    "src.mt5.mt5_real",
    "src.components.execution",
    "src.components.orchestrator",
)
FORBIDDEN_PATH_TOKENS = (
    "march_2026",
    "/march/",
    "live_forward",
    "live-forward",
)


class ReconstructionError(RuntimeError):
    """Fail-closed source or reconstruction contract violation."""


@dataclass(frozen=True, slots=True)
class IdentityRow:
    window: str
    candidate_id: str
    symbol: str
    side: str
    decision_time_utc: str
    decision_time: datetime
    kill_zone: str
    origin_family: str
    framework: str
    route_family: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.candidate_id,
            self.symbol,
            self.side,
            self.decision_time_utc,
        )


@dataclass(frozen=True, slots=True)
class Bar:
    time: datetime
    time_utc: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def as_row(self) -> dict[str, Any]:
        return {
            "time": self.time_utc,
            "time_utc": self.time_utc,
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def file_binding(path: Path, *, relative_to: Path | None = None) -> dict[str, Any]:
    display = path.relative_to(relative_to).as_posix() if relative_to else path.as_posix()
    return {"path": display, "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def require_file_binding(path: Path, expected_sha256: str, expected_bytes: int | None = None) -> None:
    if not path.is_file():
        raise ReconstructionError(f"required_file_missing:{path}")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise ReconstructionError(f"required_file_size_mismatch:{path}")
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise ReconstructionError(
            f"required_file_sha256_mismatch:{path}:expected={expected_sha256}:observed={observed}"
        )


def parse_true_utc(value: Any, *, field: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ReconstructionError(f"missing_timestamp:{field}")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ReconstructionError(f"invalid_timestamp:{field}:{value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReconstructionError(f"naive_timestamp_refused:{field}:{value}")
    if parsed.utcoffset() != timedelta(0):
        raise ReconstructionError(f"non_utc_offset_refused:{field}:{value}")
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ReconstructionError("naive_datetime_refused")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def source_control_envelope(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(payload),
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": False,
        "result_use_status": RESULT_USE_STATUS,
    }


def validate_clock_contract(clock: Mapping[str, Any], *, label: str) -> None:
    if (
        clock.get("time_column_basis") != "true_utc"
        or clock.get("broker_clock_rule") != "new_york_plus_7"
        or clock.get("conversion_function") != "src.utils.broker_clock.broker_epoch_to_utc"
        or float(clock.get("broker_clock_anchor_offset_hours", -1)) != 7.0
        or clock.get("broker_clock_anchor_zone") != "America/New_York"
    ):
        raise ReconstructionError(f"source_manifest_timebase_invalid:{label}")


def validate_composite_identities(rows: Iterable[IdentityRow]) -> dict[str, int]:
    seen: set[tuple[str, str, str, str]] = set()
    candidate_counts: Counter[str] = Counter()
    row_count = 0
    for row in rows:
        if row.key in seen:
            raise ReconstructionError(f"duplicate_composite_identity:{row.key}")
        seen.add(row.key)
        candidate_counts[row.candidate_id] += 1
        row_count += 1
    return {
        "rows": row_count,
        "unique_composite_identities": len(seen),
        "candidate_ids_reused": sum(1 for count in candidate_counts.values() if count > 1),
        "rows_under_reused_candidate_ids": sum(
            count for count in candidate_counts.values() if count > 1
        ),
    }


def require_exact_symbol_domain(
    identities: Iterable[IdentityRow], authoritative_symbols: Iterable[str]
) -> None:
    authority = set(authoritative_symbols)
    observed = {row.symbol for row in identities}
    aliases_or_missing = sorted(observed - authority)
    if aliases_or_missing:
        raise ReconstructionError(
            f"symbol_alias_or_unbound_symbol_refused:{aliases_or_missing}"
        )


def require_warmup(*, m15_count: int, h1_count: int, label: str) -> None:
    if m15_count < MIN_CLOSED_M15 or h1_count < H1_LOOKBACK:
        raise ReconstructionError(
            f"insufficient_warmup:{label}:m15={m15_count}:h1={h1_count}"
        )


def require_single_generator_match(matches: Sequence[Any], *, label: str) -> Any:
    if len(matches) != 1:
        raise ReconstructionError(
            f"generator_identity_multiplicity_invalid:{label}:matches={len(matches)}"
        )
    return matches[0]


def assert_path_scope(
    path: Path,
    *,
    raw_warmup_source: bool = False,
    source_root: Path | None = None,
    allowed_raw_paths: set[Path] | None = None,
) -> None:
    text = path.as_posix().lower()
    if raw_warmup_source:
        if source_root is None or allowed_raw_paths is None:
            raise ReconstructionError(f"raw_warmup_binding_required:{path}")
        if ".." in path.parts:
            raise ReconstructionError(f"raw_warmup_path_traversal:{path}")
        root = source_root.resolve(strict=False)
        candidate = path.resolve(strict=False)
        allowed = {item.resolve(strict=False) for item in allowed_raw_paths}
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ReconstructionError(f"raw_warmup_outside_source_root:{path}") from exc
        if candidate not in allowed:
            raise ReconstructionError(f"raw_warmup_path_not_hash_bound:{path}")
        if "/sources/bars/" not in candidate.as_posix().lower():
            raise ReconstructionError(f"raw_warmup_not_bar_source:{path}")
        return
    for token in FORBIDDEN_PATH_TOKENS:
        if token in text:
            raise ReconstructionError(f"forbidden_window_or_live_path:{path}")


def _static_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_string(node.left)
        right = _static_string(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _static_dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _static_dotted_name(node.value)
        if base is not None:
            return f"{base}.{node.attr}"
    return None


def _static_git_command_allowed(node: ast.AST) -> bool:
    def identity_arg(value: ast.AST) -> bool:
        return isinstance(value, (ast.Name, ast.Subscript)) or (
            isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and len(value.value) == 40
            and all(character in "009abcdef" for character in value.value)
        ) or (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "str"
            and len(value.args) == 1
            and not value.keywords
            and identity_arg(value.args[0])
        )

    if not isinstance(node, (ast.List, ast.Tuple)):
        return False
    items = list(node.elts)
    values = [_static_string(item) for item in items]
    if values == ["git", "status", "--porcelain", "--untracked-files=normal"]:
        return True
    if values == ["git", "rev-parse", "HEAD"]:
        return True
    if len(items) == 3 and values[:2] == ["git", "show"]:
        target = items[2]
        def exact_value(part: ast.AST) -> bool:
            return (
                isinstance(part, ast.FormattedValue)
                and part.conversion == -1
                and part.format_spec is None
                and isinstance(part.value, (ast.Name, ast.Subscript))
            )
        return (
            isinstance(target, ast.JoinedStr)
            and len(target.values) == 3
            and exact_value(target.values[0])
            and isinstance(target.values[1], ast.Constant)
            and target.values[1].value == ":"
            and exact_value(target.values[2])
        )
    if len(items) == 5 and values[:4] == ["git", "show", "-s", "--format=%P"]:
        return identity_arg(items[4])
    if len(items) == 5 and values[:3] == ["git", "merge-base", "--is-ancestor"]:
        return all(identity_arg(item) for item in items[3:])
    return False


def verify_static_import_boundary(paths: Sequence[Path]) -> dict[str, Any]:
    """Task-specific static audit; builder writes are containment-audited separately."""

    network_roots = {"socket", "requests", "urllib", "http", "ftplib", "paramiko"}
    outcome_fields = {
        "profit", "pnl", "return", "return_r", "exact_r", "proxy_r",
        "expectancy", "fill_result", "cost_result", "terminal_result",
    }
    checked: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        aliases: dict[str, str] = {}
        trusted_git_reader = path.resolve() in {
            Path(__file__).resolve(),
            (REPO_ROOT / "src/research_infra/p1_upstream_packet_verifier.py").resolve(),
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    raise ReconstructionError(f"forbidden_relative_import:{path}")
                module = node.module or ""
                for alias in node.names:
                    aliases[alias.asname or alias.name] = f"{module}.{alias.name}".strip(".")
        imported = set(aliases.values())
        for name in imported:
            if any(name == prefix or name.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORT_PREFIXES):
                raise ReconstructionError(f"forbidden_import:{path}:{name}")
            if name.split(".", 1)[0] in network_roots:
                raise ReconstructionError(f"forbidden_network_import:{path}:{name}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "order_send":
                raise ReconstructionError(f"forbidden_order_send_attribute:{path}")
            if isinstance(node, ast.Name) and node.id == "order_send":
                raise ReconstructionError(f"forbidden_order_send_name:{path}")
            if isinstance(node, ast.Subscript):
                field = _static_string(node.slice)
                if field is not None and field.lower() in outcome_fields:
                    raise ReconstructionError(f"forbidden_outcome_field:{path}:{field}")
            if not isinstance(node, ast.Call):
                continue
            dotted = _static_dotted_name(node.func) or ""
            first, dot, remainder = dotted.partition(".")
            resolved = aliases.get(first, first) + (dot + remainder if dot else "")
            call_name = resolved.rsplit(".", 1)[-1] if resolved else ""
            if resolved in {"__import__", "builtins.__import__", "importlib.import_module"} or call_name == "import_module":
                target = _static_string(node.args[0]) if node.args else None
                raise ReconstructionError(f"forbidden_dynamic_import:{path}:{target or 'dynamic'}")
            if call_name in {"exec", "eval", "compile"}:
                raise ReconstructionError(f"forbidden_dynamic_execution:{path}:{call_name}")
            if call_name == "getattr" and len(node.args) >= 2:
                target = _static_string(node.args[1])
                if target == "order_send":
                    raise ReconstructionError(f"forbidden_order_send_getattr:{path}")
                if target in {"__import__", "import_module", "system", "popen"} or (target or "").startswith(("exec", "spawn", "posix_spawn")):
                    raise ReconstructionError(f"forbidden_dynamic_surface:{path}:{target}")
            if call_name == "get" and node.args:
                field = _static_string(node.args[0])
                if field is not None and field.lower() in outcome_fields:
                    raise ReconstructionError(f"forbidden_outcome_field:{path}:{field}")
            if resolved.startswith("subprocess."):
                unsafe = {keyword.arg for keyword in node.keywords} & {"shell", "executable", "env", "preexec_fn"}
                if (
                    not trusted_git_reader or call_name not in {"check_output", "run"}
                    or unsafe or not node.args or not _static_git_command_allowed(node.args[0])
                ):
                    raise ReconstructionError(f"forbidden_subprocess:{path}")
            if resolved in {"os.system", "os.popen", "pty.spawn"} or resolved.startswith(("os.exec", "os.spawn", "os.posix_spawn")):
                raise ReconstructionError(f"forbidden_process_escape:{path}:{resolved}")
        try:
            checked.append(path.relative_to(REPO_ROOT).as_posix())
        except ValueError:
            checked.append(path.as_posix())
    return {
        "checked_paths": checked,
        "forbidden_findings": 0,
        "builder_writes": "SEPARATELY_PACKET_ROOT_CONTAINMENT_AUDITED",
    }


def verify_repo_authorities() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative, expected in CODE_AUTHORITY_BINDINGS.items():
        path = REPO_ROOT / relative
        require_file_binding(path, expected)
        rows.append(file_binding(path, relative_to=REPO_ROOT))
    for relative, expected, size in COMMISSIONED_SOURCE_PAYLOADS:
        path = REPO_ROOT / relative
        require_file_binding(path, str(expected), int(size))
        rows.append(file_binding(path, relative_to=REPO_ROOT))
    return rows


def verify_immutable_evidence_authorities(source_commit: str) -> dict[str, Any]:
    verified: dict[str, Any] = {}
    for label, authority in IMMUTABLE_EVIDENCE_AUTHORITIES.items():
        commit = str(authority["commit"])
        parents = subprocess.check_output(
            ["git", "show", "-s", "--format=%P", commit], cwd=REPO_ROOT, text=True
        ).strip().split()
        if parents != [authority["parent"]]:
            raise ReconstructionError(f"evidence_commit_parent_mismatch:{label}:{parents}")
        artifact_rows: list[dict[str, Any]] = []
        for artifact in authority["artifacts"]:
            payload = subprocess.check_output(
                ["git", "show", f"{commit}:{artifact['path']}"], cwd=REPO_ROOT
            )
            observed = hashlib.sha256(payload).hexdigest()
            if observed != artifact["sha256"] or len(payload) != artifact["bytes"]:
                raise ReconstructionError(
                    f"immutable_evidence_blob_mismatch:{label}:{artifact['path']}"
                )
            artifact_rows.append(dict(artifact))
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, source_commit],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        ).returncode == 0
        role = EVIDENCE_ANCESTRY_ROLES[label]
        should_be_ancestor = role.startswith("SOURCE_ANCESTOR_")
        if ancestry is not should_be_ancestor:
            raise ReconstructionError(
                f"evidence_ancestry_role_mismatch:{label}:ancestor={ancestry}:role={role}"
            )
        verified[label] = {
            "commit": commit,
            "parent": authority["parent"],
            "one_parent_verified": True,
            "artifacts": artifact_rows,
            "implementation_ancestry_role": role,
        }
    return verified


def verify_b0_member_binding() -> dict[str, Any]:
    payload = subprocess.check_output(
        ["git", "show", f"{B0_BREAKER_ROUTE_BINDING['commit']}:{B0_BREAKER_ROUTE_BINDING['path']}"],
        cwd=REPO_ROOT,
    )
    if (
        len(payload) != B0_BREAKER_ROUTE_BINDING["bytes"]
        or hashlib.sha256(payload).hexdigest() != B0_BREAKER_ROUTE_BINDING["sha256"]
    ):
        raise ReconstructionError("b0_breaker_route_blob_mismatch")
    member = json.loads(payload)["candidate"]["family_member_record"]
    if canonical_sha256(member) != FIXED_BREAKER_MEMBER_CANONICAL_SHA256:
        raise ReconstructionError("b0_breaker_member_canonical_hash_mismatch")
    return dict(B0_BREAKER_ROUTE_BINDING)


def _scan_json_value_end(text: str, start: int) -> int:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise ReconstructionError("invalid_json_value:missing")
    opening = text[index]
    if opening == '"':
        escaped = False
        index += 1
        while index < len(text):
            character = text[index]
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                return index + 1
            index += 1
        raise ReconstructionError("invalid_json_value:unterminated_string")
    if opening in "[{":
        stack = [opening]
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
                    raise ReconstructionError("invalid_json_value:mismatched_container")
            index += 1
        if stack:
            raise ReconstructionError("invalid_json_value:unterminated_container")
        return index
    while index < len(text) and text[index] not in ",}":
        index += 1
    if not text[start:index].strip():
        raise ReconstructionError("invalid_json_value:empty")
    return index


def project_source_control_json(text: str) -> dict[str, Any]:
    """Decode only allowlisted top-level control values; skip all other value bytes."""

    decoder = json.JSONDecoder()
    index = 0
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text) or text[index] != "{":
        raise ReconstructionError("source_row_not_json_object")
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
            raise ReconstructionError("invalid_json_key") from exc
        if not isinstance(key, str):
            raise ReconstructionError("invalid_json_key_type")
        if key in seen:
            raise ReconstructionError(f"duplicate_json_key:{key}")
        seen.add(key)
        index = key_end
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != ":":
            raise ReconstructionError(f"invalid_json_missing_colon:{key}")
        value_start = index + 1
        value_end = _scan_json_value_end(text, value_start)
        if key in SOURCE_CONTROL_FIELDS:
            try:
                output[key] = json.loads(text[value_start:value_end])
            except json.JSONDecodeError as exc:
                raise ReconstructionError(f"invalid_control_json_value:{key}") from exc
        index = value_end
        while index < len(text) and text[index].isspace():
            index += 1
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            index += 1
            break
        raise ReconstructionError("invalid_json_object_separator")
    if text[index:].strip():
        raise ReconstructionError("invalid_json_trailing_data")
    return output


def load_identity_domain() -> list[IdentityRow]:
    rows: list[IdentityRow] = []
    seen: set[tuple[str, str, str, str]] = set()
    by_window: Counter[str] = Counter()
    for spec in POOL_SPECS:
        path = REPO_ROOT / str(spec["path"])
        assert_path_scope(path)
        require_file_binding(path, str(spec["sha256"]), int(spec["bytes"]))
        start_day, end_day = WINDOW_BOUNDS[str(spec["window"])]
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                projected = project_source_control_json(line)
                missing = [field for field in SOURCE_CONTROL_FIELDS if field not in projected]
                if missing:
                    raise ReconstructionError(f"pool_source_control_fields_missing:{path}:{line_number}:{missing}")
                decision = parse_true_utc(projected["decision_time_utc"], field="decision_time_utc")
                day = decision.date().isoformat()
                if not start_day <= day <= end_day:
                    raise ReconstructionError(f"pool_row_out_of_window:{path}:{line_number}:{day}")
                side = str(projected["side"]).upper()
                if side not in {"LONG", "SHORT"} or side != str(projected["direction"]).upper():
                    raise ReconstructionError(f"pool_side_direction_invalid:{path}:{line_number}")
                row = IdentityRow(
                    window=str(spec["window"]),
                    candidate_id=str(projected["candidate_id"]),
                    symbol=str(projected["symbol"]),
                    side=side,
                    decision_time_utc=iso_utc(decision),
                    decision_time=decision,
                    kill_zone=str(projected["kill_zone"]),
                    origin_family=str(projected["origin_family"]),
                    framework=str(projected["framework"]),
                    route_family=str(projected["route_family"]),
                )
                if row.key in seen:
                    raise ReconstructionError(f"duplicate_composite_identity:{row.key}")
                seen.add(row.key)
                rows.append(row)
                by_window[row.window] += 1
        if by_window[str(spec["window"])] != int(spec["rows"]):
            raise ReconstructionError(f"pool_row_count_mismatch:{spec['window']}")
    if len(rows) != EXPECTED_IDENTITY_COUNT or dict(by_window) != EXPECTED_WINDOW_COUNTS:
        raise ReconstructionError(
            f"identity_domain_count_mismatch:total={len(rows)}:windows={dict(by_window)}"
        )
    rows.sort(key=lambda row: (row.decision_time, row.symbol, row.candidate_id, row.side))
    return rows


def load_source_manifest_authority(source_root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    authority_rows: list[dict[str, Any]] = []
    manifests: dict[str, dict[str, Any]] = {}
    for relative, expected in SOURCE_MANIFEST_BINDINGS.items():
        path = source_root / relative
        assert_path_scope(path)
        require_file_binding(path, expected)
        authority_rows.append(file_binding(path, relative_to=source_root))
        manifests[relative] = json.loads(path.read_bytes())
    for relative in ("manifests/january_2026.json", "manifests/april_2026.json", "manifests/may_2026.json"):
        manifest = manifests[relative]
        clock = manifest.get("clock") or {}
        validate_clock_contract(clock, label=relative)
        if manifest.get("economic_outcomes_read") is not False:
            raise ReconstructionError(f"source_manifest_outcome_boundary_invalid:{relative}")
    per_window: list[dict[str, dict[str, Any]]] = []
    for relative in ("manifests/january_2026.json", "manifests/april_2026.json", "manifests/may_2026.json"):
        entries = {
            str(row["symbol"]): dict(row)
            for row in manifests[relative].get("bar_sources", [])
            if row.get("timeframe") == "M15"
        }
        if len(entries) != 24:
            raise ReconstructionError(f"m15_manifest_symbol_count_invalid:{relative}:{len(entries)}")
        per_window.append(entries)
    baseline = per_window[0]
    binding_fields = (
        "symbol", "mapped_symbol", "timeframe", "lane_relpath", "sha256",
        "row_count", "first_utc", "last_utc", "time_column_basis",
        "broker_clock_rule", "clock_conversion", "source_snapshot_name",
    )
    for other in per_window[1:]:
        for symbol in sorted(baseline):
            if {key: baseline[symbol].get(key) for key in binding_fields} != {
                key: other[symbol].get(key) for key in binding_fields
            }:
                raise ReconstructionError(f"cross_window_m15_authority_mismatch:{symbol}")
    return baseline, authority_rows


def load_m15_series(source_root: Path, entries: Mapping[str, Mapping[str, Any]]) -> dict[str, list[Bar]]:
    by_symbol: dict[str, list[Bar]] = {}
    for symbol, entry in sorted(entries.items()):
        if entry.get("time_column_basis") != "true_utc":
            raise ReconstructionError(f"mixed_or_unverified_timebase:{symbol}")
        path = source_root / str(entry["lane_relpath"])
        assert_path_scope(
            path,
            raw_warmup_source=True,
            source_root=source_root,
            allowed_raw_paths={path},
        )
        require_file_binding(path, str(entry["sha256"]))
        rows: list[Bar] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != BAR_SCHEMA:
                raise ReconstructionError(f"m15_schema_mismatch:{path}:{reader.fieldnames}")
            previous: datetime | None = None
            for line_number, raw in enumerate(reader, 2):
                timestamp = parse_true_utc(raw["time"], field=f"{path}:{line_number}:time")
                if previous is not None and timestamp <= previous:
                    raise ReconstructionError(f"m15_nonmonotonic_or_duplicate:{path}:{line_number}")
                previous = timestamp
                try:
                    open_, high, low, close, volume = (
                        float(raw["open"]), float(raw["high"]), float(raw["low"]),
                        float(raw["close"]), float(raw["volume"]),
                    )
                except (TypeError, ValueError) as exc:
                    raise ReconstructionError(f"m15_numeric_invalid:{path}:{line_number}") from exc
                if min(open_, high, low, close) <= 0 or high < max(open_, close) or low > min(open_, close):
                    raise ReconstructionError(f"m15_ohlc_invalid:{path}:{line_number}")
                rows.append(Bar(timestamp, iso_utc(timestamp), symbol, open_, high, low, close, volume))
        if len(rows) != int(entry["row_count"]):
            raise ReconstructionError(f"m15_row_count_mismatch:{symbol}:{len(rows)}")
        if rows[0].time_utc != str(entry["first_utc"]) or rows[-1].time_utc != str(entry["last_utc"]):
            raise ReconstructionError(f"m15_coverage_mismatch:{symbol}")
        by_symbol[symbol] = rows
    return by_symbol


def aggregate_h1_from_m15(rows: Sequence[Bar], *, symbol: str) -> list[Bar]:
    """Exact UTC-hour OHLCV aggregation used by the bound replay runner."""

    output: list[Bar] = []
    bucket_rows: list[Bar] = []
    bucket_time: datetime | None = None
    for row in rows:
        current_bucket = row.time.replace(minute=0, second=0, microsecond=0)
        if bucket_time is not None and current_bucket != bucket_time:
            output.append(_aggregate_bucket(bucket_time, bucket_rows, symbol))
            bucket_rows = []
        bucket_time = current_bucket
        bucket_rows.append(row)
    if bucket_time is not None:
        output.append(_aggregate_bucket(bucket_time, bucket_rows, symbol))
    return output


def _aggregate_bucket(bucket: datetime, rows: Sequence[Bar], symbol: str) -> Bar:
    return Bar(
        time=bucket,
        time_utc=iso_utc(bucket),
        symbol=symbol,
        open=rows[0].open,
        high=max(row.high for row in rows),
        low=min(row.low for row in rows),
        close=rows[-1].close,
        volume=sum(row.volume for row in rows),
    )


def closed_slice_indices(
    rows: Sequence[Bar], *, decision: datetime, minutes: int, lookback: int
) -> tuple[int, int]:
    closes = [row.time + timedelta(minutes=minutes) for row in rows]
    return closed_slice_indices_from_closes(
        closes,
        decision=decision,
        lookback=lookback,
    )


def closed_slice_indices_from_closes(
    closes: Sequence[datetime], *, decision: datetime, lookback: int
) -> tuple[int, int]:
    if decision.tzinfo is None or decision.utcoffset() is None:
        raise ReconstructionError("naive_decision_timestamp_refused")
    stop = bisect.bisect_right(closes, decision)
    start = max(0, stop - lookback)
    if stop <= start:
        raise ReconstructionError("missing_closed_bar_slice")
    if closes[stop - 1] > decision:
        raise ReconstructionError("postdecision_bar_read")
    return start, stop


def _deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(dict(base))
    for key, value in override.items():
        if key in output and isinstance(output[key], dict) and isinstance(value, Mapping):
            output[key] = _deep_merge(output[key], value)
        else:
            output[key] = copy.deepcopy(value)
    return output


def build_inert_generation_config() -> dict[str, Any]:
    base = yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text()) or {}
    profile = yaml.safe_load(
        (REPO_ROOT / "config/profiles/operator_profile.yaml").read_text()
    ) or {}
    output = copy.deepcopy(base)
    merged_instruments = copy.deepcopy(profile.get("instruments") or {})
    for symbol, base_row in (base.get("instruments") or {}).items():
        if not isinstance(base_row, Mapping):
            continue
        merged_row = merged_instruments.setdefault(str(symbol), {})
        if not isinstance(merged_row, dict):
            merged_row = {}
            merged_instruments[str(symbol)] = merged_row
        for key, value in base_row.items():
            if key == "market" and isinstance(value, Mapping):
                market = copy.deepcopy(merged_row.get("market") or {})
                market.update(copy.deepcopy(value))
                merged_row["market"] = market
            elif key == "risk" and isinstance(value, Mapping):
                risk = copy.deepcopy(merged_row.get("risk") or {})
                for risk_key, risk_value in value.items():
                    risk.setdefault(risk_key, copy.deepcopy(risk_value))
                merged_row["risk"] = risk
            elif key not in merged_row:
                merged_row[key] = copy.deepcopy(value)
    output["instruments"] = merged_instruments
    market_state = output.setdefault("market_state", {})
    market_state["side_effect_writes_enabled"] = False
    market_state["structure_shadow_log_enabled"] = False
    runtime = output.setdefault("gtos_vnext_runtime", {})
    runtime["phase18_current_breaker_re_entry_repair_enabled"] = False
    return output


def symbol_generation_config(config: Mapping[str, Any], symbol: str) -> dict[str, Any]:
    output = copy.deepcopy(dict(config))
    market = output.setdefault("market", {})
    market["symbol"] = symbol
    market["mt5_symbol"] = str(
        ((output.get("instruments") or {}).get(symbol) or {}).get("market", {}).get("mt5_symbol")
        or symbol
    )
    return output


def _raw_packet(symbol: str, decision: datetime, m15: Sequence[Bar], h1: Sequence[Bar]) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "timestamp_utc": iso_utc(decision),
        "candles": {
            "D1": [],
            "H4": [],
            "H1": [row.as_row() for row in h1],
            "M15": [row.as_row() for row in m15],
        },
        "session_levels": {},
        "data_quality": {
            "all_timeframes_complete": False,
            "spread_normal": False,
            "mt5_connected": False,
            "timestamp_utc": iso_utc(decision),
        },
        "candle_open_utc": m15[-1].time_utc,
        "candle_close_utc": iso_utc(m15[-1].time + timedelta(minutes=15)),
    }


def project_breakers(mso: Any) -> list[dict[str, Any]]:
    fields = (
        "zone_high", "zone_low", "direction", "original_ob_direction",
        "formation_time", "mitigation_time", "causing_event", "is_retested",
    )
    output: list[dict[str, Any]] = []
    for breaker in mso.timeframes["H1"].breaker_blocks:
        output.append({field: getattr(breaker, field) for field in fields})
    return output


class DeterministicJsonlGzipWriter:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._raw = path.open("wb")
        self._gzip = gzip.GzipFile(filename="", mode="wb", fileobj=self._raw, mtime=0)
        self._text = io.TextIOWrapper(self._gzip, encoding="utf-8", newline="\n")
        self.rows = 0

    def write(self, row: Mapping[str, Any]) -> None:
        self._text.write(canonical_json_bytes(dict(row)).decode("utf-8"))
        self._text.write("\n")
        self.rows += 1

    def close(self) -> None:
        self._text.flush()
        self._text.detach()
        self._gzip.close()
        self._raw.close()

    def __enter__(self) -> "DeterministicJsonlGzipWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()


def require_builder_write_target(target: Path, *, root: Path) -> None:
    """Allow a builder write only below its explicit packet or staging root."""

    if root.exists() and root.is_symlink():
        raise ReconstructionError(f"builder_write_root_symlink_refused:{root}")
    try:
        lexical_relative = target.absolute().relative_to(root.absolute())
    except ValueError as exc:
        raise ReconstructionError(f"builder_write_outside_root:{target}") from exc
    cursor = root
    for part in lexical_relative.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ReconstructionError(f"builder_write_symlink_ancestor_refused:{cursor}")
    resolved_root = root.resolve(strict=False)
    resolved_target = target.resolve(strict=False)
    try:
        relative = resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise ReconstructionError(f"builder_write_outside_root:{target}") from exc
    if not relative.parts:
        raise ReconstructionError(f"builder_write_root_itself_refused:{target}")


def _write_series_files(
    stage: Path,
    m15_by_symbol: Mapping[str, Sequence[Bar]],
    h1_by_symbol: Mapping[str, Sequence[Bar]],
) -> dict[str, dict[str, dict[str, Any]]]:
    bindings: dict[str, dict[str, dict[str, Any]]] = {}
    for symbol in sorted(m15_by_symbol):
        bindings[symbol] = {}
        for timeframe, rows in (("M15", m15_by_symbol[symbol]), ("H1", h1_by_symbol[symbol])):
            relative = Path("series") / f"{symbol}.{timeframe.lower()}.jsonl.gz"
            path = stage / relative
            require_builder_write_target(path, root=stage)
            with DeterministicJsonlGzipWriter(path) as writer:
                for row in rows:
                    writer.write(row.as_row())
            bindings[symbol][timeframe] = {
                **file_binding(path, relative_to=stage),
                "row_count": len(rows),
                "first_utc": rows[0].time_utc,
                "last_utc": rows[-1].time_utc,
                "time_column_basis": "true_utc",
                "timeframe_minutes": 15 if timeframe == "M15" else 60,
            }
    return bindings


def available_bytes(path: Path) -> int:
    probe = path if path.exists() else path.parent
    return int(shutil.disk_usage(probe).free)


def estimate_materialization_bytes(source_root: Path) -> dict[str, Any]:
    entries, _ = load_source_manifest_authority(source_root)
    source_bytes = sum((source_root / str(entry["lane_relpath"])).stat().st_size for entry in entries.values())
    compressed_identity_bytes = sum(int(spec["bytes"]) for spec in POOL_SPECS)
    estimate = source_bytes * 4 + compressed_identity_bytes * 8 + 256 * 1024**2
    free = available_bytes(DEFAULT_PACKET_PARENT)
    return {
        "source_m15_bytes": source_bytes,
        "compressed_identity_bytes": compressed_identity_bytes,
        "conservative_materialization_estimate_bytes": estimate,
        "free_bytes": free,
        "free_after_estimate_bytes": free - estimate,
        "minimum_free_bytes": MIN_FREE_BYTES,
        "safe_to_materialize": free - estimate >= MIN_FREE_BYTES,
    }


def _group_by_decision(rows: Sequence[IdentityRow]) -> Iterator[tuple[datetime, list[IdentityRow]]]:
    current: datetime | None = None
    grouped: list[IdentityRow] = []
    for row in rows:
        if current is not None and row.decision_time != current:
            yield current, grouped
            grouped = []
        current = row.decision_time
        grouped.append(row)
    if current is not None:
        yield current, grouped


def verify_source_commit_bindings(source_commit: str) -> dict[str, Any]:
    if len(source_commit) != 40 or any(character not in "009abcdef" for character in source_commit):
        raise ReconstructionError("source_commit_format_invalid")
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=REPO_ROOT,
        text=True,
    )
    if status:
        raise ReconstructionError("source_worktree_not_clean")
    parents = subprocess.check_output(
        ["git", "show", "-s", "--format=%P", source_commit],
        cwd=REPO_ROOT,
        text=True,
    ).strip().split()
    if parents != [IMMUTABLE_HN_SOURCE_COMMIT]:
        raise ReconstructionError(
            f"source_commit_parent_mismatch:expected={IMMUTABLE_HN_SOURCE_COMMIT}:observed={parents}"
        )
    paths = sorted({
        *CODE_AUTHORITY_BINDINGS,
        "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py",
        "src/research_infra/_p1_upstream_packet_expectations.py",
        "src/research_infra/p1_upstream_m1_provenance_verifier.py",
        "src/research_infra/p1_upstream_reconstruction.py",
        "src/research_infra/p1_upstream_packet_verifier.py",
    })
    for relative in paths:
        current = (REPO_ROOT / relative).read_bytes()
        try:
            committed = subprocess.check_output(
                ["git", "show", f"{source_commit}:{relative}"], cwd=REPO_ROOT
            )
        except subprocess.CalledProcessError as exc:
            raise ReconstructionError(f"source_commit_blob_missing:{relative}") from exc
        if current != committed:
            raise ReconstructionError(f"source_commit_blob_mismatch:{relative}")
    return {
        "clean_worktree": True,
        "source_parent": IMMUTABLE_HN_SOURCE_COMMIT,
        "commit_bound_paths": paths,
    }


def build_packet(*, source_root: Path, packet_parent: Path, source_commit: str) -> dict[str, Any]:
    if packet_parent.is_symlink() or not packet_parent.is_dir():
        raise ReconstructionError(f"packet_parent_must_be_existing_regular_directory:{packet_parent}")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip() != source_commit:
        raise ReconstructionError("source_commit_is_not_current_head")
    verify_source_commit_bindings(source_commit)
    static_audit = verify_static_import_boundary(
        [
            Path(__file__),
            REPO_ROOT / "src/research_infra/_p1_upstream_packet_expectations.py",
            REPO_ROOT / "src/research_infra/p1_upstream_m1_provenance_verifier.py",
            REPO_ROOT / "src/research_infra/p1_upstream_packet_verifier.py",
            REPO_ROOT / "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py",
        ]
    )
    repo_authorities = verify_repo_authorities()
    immutable_evidence = verify_immutable_evidence_authorities(source_commit)
    b0_binding = verify_b0_member_binding()
    entries, source_manifest_bindings = load_source_manifest_authority(source_root)
    estimate = estimate_materialization_bytes(source_root)
    free = available_bytes(packet_parent)
    estimate["free_bytes"] = free
    estimate["free_after_estimate_bytes"] = free - int(estimate["conservative_materialization_estimate_bytes"])
    estimate["safe_to_materialize"] = estimate["free_after_estimate_bytes"] >= MIN_FREE_BYTES
    if not estimate["safe_to_materialize"]:
        raise ReconstructionError("materialization_would_cross_8_gib_floor")
    identities = load_identity_domain()
    m15_by_symbol = load_m15_series(source_root, entries)
    require_exact_symbol_domain(identities, m15_by_symbol)
    h1_by_symbol = {
        symbol: aggregate_h1_from_m15(rows, symbol=symbol)
        for symbol, rows in m15_by_symbol.items()
    }
    m15_closes_by_symbol = {
        symbol: [row.time + timedelta(minutes=15) for row in rows]
        for symbol, rows in m15_by_symbol.items()
    }
    h1_closes_by_symbol = {
        symbol: [row.time + timedelta(minutes=60) for row in rows]
        for symbol, rows in h1_by_symbol.items()
    }
    stage = packet_parent / f".p1-hn-staging-{os.getpid()}"
    require_builder_write_target(stage, root=packet_parent)
    if stage.exists():
        raise ReconstructionError(f"staging_path_already_exists:{stage}")
    stage.mkdir()
    try:
        series_bindings = _write_series_files(stage, m15_by_symbol, h1_by_symbol)
        states_path = stage / "states/predecision_market_state.jsonl.gz"
        index_path = stage / "identity_to_slice.jsonl.gz"
        require_builder_write_target(states_path, root=stage)
        require_builder_write_target(index_path, root=stage)
        generation_config = build_inert_generation_config()
        generated_match_count = 0
        state_count = 0
        duplicate_generated_matches = 0
        unmatched: list[tuple[str, str, str, str]] = []
        source_multiplicity: Counter[str] = Counter()
        reused_candidate_ids: Counter[str] = Counter(row.candidate_id for row in identities)
        from src.components.broader_origin_generators import generate_live_broader_origin_candidates
        from src.components.market_state import compute_market_state

        with DeterministicJsonlGzipWriter(states_path) as state_writer, DeterministicJsonlGzipWriter(index_path) as index_writer:
            for decision_number, (decision, decision_rows) in enumerate(_group_by_decision(identities), 1):
                raw_by_symbol: dict[str, dict[str, Any]] = {}
                slices: dict[str, dict[str, Any]] = {}
                for symbol in sorted(m15_by_symbol):
                    m15_start, m15_stop = closed_slice_indices_from_closes(
                        m15_closes_by_symbol[symbol], decision=decision, lookback=M15_LOOKBACK
                    )
                    h1_start, h1_stop = closed_slice_indices_from_closes(
                        h1_closes_by_symbol[symbol], decision=decision, lookback=H1_LOOKBACK
                    )
                    m15_slice = m15_by_symbol[symbol][m15_start:m15_stop]
                    h1_slice = h1_by_symbol[symbol][h1_start:h1_stop]
                    raw_by_symbol[symbol] = _raw_packet(symbol, decision, m15_slice, h1_slice)
                    slices[symbol] = {
                        "m15_start": m15_start,
                        "m15_stop": m15_stop,
                        "h1_start": h1_start,
                        "h1_stop": h1_stop,
                        "m15_count": len(m15_slice),
                        "h1_count": len(h1_slice),
                    }
                cross_asset = {"raw_data_by_symbol": raw_by_symbol}
                rows_by_symbol: dict[str, list[IdentityRow]] = defaultdict(list)
                for row in decision_rows:
                    rows_by_symbol[row.symbol].append(row)
                for symbol, target_rows in sorted(rows_by_symbol.items()):
                    if symbol not in raw_by_symbol:
                        raise ReconstructionError(f"identity_symbol_without_source:{symbol}")
                    require_warmup(
                        m15_count=slices[symbol]["m15_count"],
                        h1_count=slices[symbol]["h1_count"],
                        label=f"{symbol}:{iso_utc(decision)}",
                    )
                    kill_zones = {row.kill_zone for row in target_rows}
                    if len(kill_zones) != 1:
                        raise ReconstructionError(f"mixed_kill_zone_for_symbol_decision:{symbol}:{iso_utc(decision)}")
                    symbol_config = symbol_generation_config(generation_config, symbol)
                    raw = raw_by_symbol[symbol]
                    mso = compute_market_state(raw, symbol_config)
                    generated = generate_live_broader_origin_candidates(
                        raw, mso, symbol_config, symbol, next(iter(kill_zones)),
                        cross_asset_raw_data=cross_asset, now_utc=decision,
                    )
                    generated_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
                    for candidate in generated:
                        generated_by_key[(
                            str(candidate.get("candidate_id")),
                            str(candidate.get("symbol")),
                            str(candidate.get("side")).upper(),
                        )].append(candidate)
                    state_id = "state_" + canonical_sha256(
                        {"symbol": symbol, "decision_time_utc": iso_utc(decision)}
                    )[:24]
                    breakers = project_breakers(mso)
                    state_payload = {
                        "state_id": state_id,
                        "symbol": symbol,
                        "decision_time_utc": iso_utc(decision),
                        "m15_slice": {
                            **{key: slices[symbol][key] for key in ("m15_start", "m15_stop", "m15_count")},
                            "first_open_utc": raw["candles"]["M15"][0]["time_utc"],
                            "last_open_utc": raw["candles"]["M15"][-1]["time_utc"],
                            "last_close_utc": iso_utc(m15_by_symbol[symbol][slices[symbol]["m15_stop"] - 1].time + timedelta(minutes=15)),
                        },
                        "h1_slice": {
                            **{key: slices[symbol][key] for key in ("h1_start", "h1_stop", "h1_count")},
                            "first_open_utc": raw["candles"]["H1"][0]["time_utc"],
                            "last_open_utc": raw["candles"]["H1"][-1]["time_utc"],
                            "last_close_utc": iso_utc(h1_by_symbol[symbol][slices[symbol]["h1_stop"] - 1].time + timedelta(minutes=60)),
                        },
                        "m15_atr_14": mso.timeframes["M15"].atr_14,
                        "h1_breaker_blocks": breakers,
                        "h1_breaker_blocks_sha256": canonical_sha256(breakers),
                        "uses_outcome_fields": False,
                    }
                    state_payload["state_sha256"] = canonical_sha256(state_payload)
                    state_writer.write(state_payload)
                    state_count += 1
                    for row in target_rows:
                        matches = generated_by_key[(row.candidate_id, row.symbol, row.side)]
                        exact = [
                            candidate for candidate in matches
                            if str(candidate.get("origin_family")) == row.origin_family
                            and str(candidate.get("framework")) == row.framework
                            and str(candidate.get("kill_zone")) == row.kill_zone
                        ]
                        if len(exact) != 1:
                            if len(exact) > 1:
                                duplicate_generated_matches += 1
                            unmatched.append(row.key)
                            continue
                        generated_match_count += 1
                        source_multiplicity[symbol] += 1
                        index_payload = {
                            "identity": dict(zip(IDENTITY_FIELDS, row.key)),
                            "window": row.window,
                            "state_id": state_id,
                            "symbol": symbol,
                            "decision_time_utc": row.decision_time_utc,
                            "kill_zone": row.kill_zone,
                            "origin_family": row.origin_family,
                            "framework": row.framework,
                            "route_family": row.route_family,
                            "m15_series_path": series_bindings[symbol]["M15"]["path"],
                            "h1_series_path": series_bindings[symbol]["H1"]["path"],
                            "m15_slice": [slices[symbol]["m15_start"], slices[symbol]["m15_stop"]],
                            "h1_slice": [slices[symbol]["h1_start"], slices[symbol]["h1_stop"]],
                            "generator_match_count": 1,
                            "uses_outcome_fields": False,
                        }
                        index_payload["identity_slice_sha256"] = canonical_sha256(index_payload)
                        index_writer.write(index_payload)
                if decision_number % 500 == 0:
                    if available_bytes(packet_parent) < MIN_FREE_BYTES:
                        raise ReconstructionError("disk_floor_crossed_during_materialization")
                    print(
                        json.dumps({
                            "progress_decision_groups": decision_number,
                            "states": state_count,
                            "identity_matches": generated_match_count,
                        }, sort_keys=True),
                        file=sys.stderr,
                        flush=True,
                    )
        if unmatched or generated_match_count != EXPECTED_IDENTITY_COUNT or duplicate_generated_matches:
            raise ReconstructionError(
                "identity_generation_coverage_failed:"
                f"matches={generated_match_count}:unmatched={len(unmatched)}:"
                f"duplicate_matches={duplicate_generated_matches}:sample={unmatched[:5]}"
            )
        payload_files: list[dict[str, Any]] = []
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                payload_files.append(file_binding(path, relative_to=stage))
        payload_root = canonical_sha256({"schema": "gtos.p1-upstream-packet-payload.v1", "files": payload_files})
        packet_dir_name = f"p1-source-packet-sha256-{payload_root}"
        coverage = source_control_envelope({
            "schema": "gtos.p1-upstream-source-coverage.v1",
            "status": "COMPLETE",
            "identity_rows": EXPECTED_IDENTITY_COUNT,
            "identity_matches": generated_match_count,
            "unique_composite_identities": EXPECTED_IDENTITY_COUNT,
            "duplicate_composite_identities": 0,
            "unmatched_identities": 0,
            "duplicate_generator_matches": 0,
            "predecision_state_count": state_count,
            "window_counts": EXPECTED_WINDOW_COUNTS,
            "minimum_closed_m15_bars": min(M15_LOOKBACK, min(len(rows) for rows in m15_by_symbol.values())),
            "required_minimum_closed_m15_bars": MIN_CLOSED_M15,
            "h1_lookback": H1_LOOKBACK,
            "postdecision_reads": 0,
            "out_of_window_rows": 0,
            "source_multiplicity_by_symbol": dict(sorted(source_multiplicity.items())),
            "candidate_ids_reused": sum(1 for count in reused_candidate_ids.values() if count > 1),
            "rows_under_reused_candidate_ids": sum(count for count in reused_candidate_ids.values() if count > 1),
        })
        coverage_path = stage / "SOURCE_COVERAGE.json"
        require_builder_write_target(coverage_path, root=stage)
        coverage_path.write_bytes(canonical_json_bytes(coverage) + b"\n")
        payload_files.append(file_binding(coverage_path, relative_to=stage))
        payload_files.sort(key=lambda row: row["path"])
        payload_root = canonical_sha256({"schema": "gtos.p1-upstream-packet-payload.v1", "files": payload_files})
        packet_dir_name = f"p1-source-packet-sha256-{payload_root}"
        manifest = source_control_envelope({
            "schema": "gtos.p1-upstream-source-packet.v2",
            "status": "FROZEN",
            "packet_payload_root_sha256": payload_root,
            "packet_directory_name": packet_dir_name,
            "tested_source_commit": source_commit,
            "source_root": source_root.as_posix(),
            "source_manifests": source_manifest_bindings,
            "commissioned_source_payload_count": len(COMMISSIONED_SOURCE_PAYLOADS),
            "repo_authorities": repo_authorities,
            "packet_tooling": [
                file_binding(REPO_ROOT / relative, relative_to=REPO_ROOT)
                for relative in (
                    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py",
                    "src/research_infra/_p1_upstream_packet_expectations.py",
                    "src/research_infra/p1_upstream_m1_provenance_verifier.py",
                    "src/research_infra/p1_upstream_packet_verifier.py",
                    "src/research_infra/p1_upstream_reconstruction.py",
                )
            ],
            "immutable_evidence_authorities": immutable_evidence,
            "series": series_bindings,
            "payload_files": payload_files,
            "timebase_authority": {
                "time_column_basis": "true_utc",
                "broker_clock_rule": "new_york_plus_7",
                "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
                "conversion_code_sha256": CODE_AUTHORITY_BINDINGS["src/utils/broker_clock.py"],
            },
            "asof_contract": {
                "m15_bar_close_minutes": 15,
                "h1_bar_close_minutes": 60,
                "close_tolerance_seconds": 0,
                "m15_lookback": M15_LOOKBACK,
                "h1_lookback": H1_LOOKBACK,
                "postdecision_reads_allowed": False,
            },
            "generator": {
                "path": "src/components/broader_origin_generators.py",
                "sha256": CODE_AUTHORITY_BINDINGS["src/components/broader_origin_generators.py"],
                "market_state_path": "src/components/market_state.py",
                "market_state_sha256": CODE_AUTHORITY_BINDINGS["src/components/market_state.py"],
                "h1_aggregation_reference_path": "src/research_infra/replay_acceleration_slice.py",
                "h1_aggregation_reference_sha256": CODE_AUTHORITY_BINDINGS["src/research_infra/replay_acceleration_slice.py"],
                "transitive_authority": [
                    row for row in repo_authorities
                    if row["path"] in CODE_AUTHORITY_BINDINGS
                ],
            },
            "route_identity": {
                "candidate": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
                "candidate_family": "CANDIDATE_BOOK_V1_V27",
                "origin_family": "current_breaker_re_entry",
                "transform_id": "cq_current_breaker_inverted_target_5d_stop_0p25d_v1",
                "identity_fields": list(IDENTITY_FIELDS),
                "denominator_rows": EXPECTED_IDENTITY_COUNT,
                "windows": WINDOW_BOUNDS,
                "disposition": "ADMIT_UNCHANGED_NOT_ACTIVATION",
                "family_member_record_canonical_sha256": FIXED_BREAKER_MEMBER_CANONICAL_SHA256,
                "b0_breaker_route_binding": b0_binding,
            },
            "coverage": coverage,
            "external_packet_immutable": True,
        })
        manifest_path = stage / "PACKET_MANIFEST.json"
        require_builder_write_target(manifest_path, root=stage)
        manifest_path.write_bytes(canonical_json_bytes(manifest) + b"\n")
        final = packet_parent / packet_dir_name
        require_builder_write_target(final, root=packet_parent)
        if final.exists():
            def inventory(root: Path) -> list[dict[str, Any]]:
                rows: list[dict[str, Any]] = []
                for candidate in sorted(root.rglob("*")):
                    if candidate.is_symlink():
                        raise ReconstructionError(f"existing_packet_symlink_refused:{candidate}")
                    if candidate.is_dir():
                        continue
                    if not candidate.is_file():
                        raise ReconstructionError(f"existing_packet_nonregular_refused:{candidate}")
                    rows.append(file_binding(candidate, relative_to=root))
                return rows

            if inventory(final) != inventory(stage):
                raise ReconstructionError(f"existing_packet_byte_inventory_conflict:{final}")
            shutil.rmtree(stage)
        else:
            stage.rename(final)
        return {
            "packet_path": final.as_posix(),
            "packet_payload_root_sha256": payload_root,
            "packet_manifest_sha256": sha256_file(final / "PACKET_MANIFEST.json"),
            "coverage": coverage,
            "materialization_estimate": estimate,
            "static_source_audit": static_audit,
        }
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    estimate = sub.add_parser("estimate")
    estimate.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    build = sub.add_parser("build")
    build.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    build.add_argument("--packet-parent", type=Path, default=DEFAULT_PACKET_PARENT)
    build.add_argument("--source-commit", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "estimate":
        print(json.dumps(estimate_materialization_bytes(args.source_root), sort_keys=True, indent=2))
        return 0
    if args.command == "build":
        print(json.dumps(build_packet(
            source_root=args.source_root,
            packet_parent=args.packet_parent,
            source_commit=args.source_commit,
        ), sort_keys=True, indent=2))
        return 0
    raise ReconstructionError(f"unsupported_command:{args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
