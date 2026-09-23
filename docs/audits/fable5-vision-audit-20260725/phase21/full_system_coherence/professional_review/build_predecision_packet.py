#!/usr/bin/env python3
"""Build the Wave 21 professional review packet without reading outcomes.

This program deliberately opens only:

* the three retained 875037f1b candidate-stage ledgers;
* their run receipts and source-authority receipts;
* the registered true-UTC bar sources needed to reconstruct causal state; and
* current production market-state and candidate-generator code.

It never reads a non-candidate stage row.  The deterministic sample is selected
before target/stop geometry is projected into the review packet.

This builder intentionally reproduces the original freeze-bound bytes.  Their
provisional ``target_through`` and ``source_owned_target`` labels are superseded
by POST_FALSIFICATION_SEMANTIC_CORRECTION.json; do not interpret them directly.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[6]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.broader_origin_generators import (
    LEAD_LAG_PAIRS,
    generate_live_broader_origin_candidates,
)
from src.components.learned_edge_layer_v4 import ASSET_CLASS_BY_SYMBOL
from src.components.market_state import compute_market_state
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


SCHEMA_PREFIX = "gtos.wave21.professional_predecision_review.v2"
SEED = "gtos-wave21-professional-predecision-v2"
MIN_WITNESSES_PER_LEVEL = 2
LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
PACKET_ROOT = Path(
    "/Users/borr/GTOSActive/p1-upstream-source-packet-hold-20260802/"
    "p1-source-packet-sha256-"
    "e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f"
)

RUNS = (
    {
        "day": "2025-10-28",
        "label": "20251028_875037f1b_r4",
        "root": Path("/private/tmp/wave21-minimal-repair-20251028-875037f1b-r4"),
        "ledger_sha256": "89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991",
        "receipt_sha256": "3c3d138d1b6d73961206e8bbfed2138d076d546cbad85536aa29d86eac3bc06c",
        "lane_manifest": LANE_ROOT / "manifests/october_2025.json",
        "lane_manifest_sha256": "72b967b4cbd5c7624337b5f3479784907bf04092624fe52daad5c1dd0c816af2",
    },
    {
        "day": "2025-11-03",
        "label": "20251103_875037f1b_r1",
        "root": Path("/private/tmp/wave21-minimal-repair-20251103-875037f1b-r1"),
        "ledger_sha256": "db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8",
        "receipt_sha256": "b6a50510a779f5871eb374d6d9ec01b9994348b56df7c520e880b6d4d2915323",
        "lane_manifest": LANE_ROOT / "manifests/november_2025.json",
        "lane_manifest_sha256": "2941ed91eb069e09d43e17d9c1773ca21a779f2efefc050707289ee96c1355b4",
    },
    {
        "day": "2025-11-07",
        "label": "20251107_875037f1b_r1",
        "root": Path("/private/tmp/wave21-minimal-repair-20251107-875037f1b-r1"),
        "ledger_sha256": "e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835",
        "receipt_sha256": "00f45e4dca469fcb39ee6cb3dbca266bdb33cce81b0abcc96e8af594820b6c1c",
        "lane_manifest": LANE_ROOT / "manifests/november_2025.json",
        "lane_manifest_sha256": "2941ed91eb069e09d43e17d9c1773ca21a779f2efefc050707289ee96c1355b4",
    },
)

# These identifiers had already appeared in committed, outcome-bearing prose
# before the review was preregistered.  Excluding them prevents recognition of
# a remembered result from contaminating a nominally blind judgment.
PREVIOUSLY_EXPOSED_CANDIDATE_IDS = frozenset(
    {
        "broadorigin_337d02bc39b4f0b395bf016d",
        "broadorigin_3383a28e518c5f2efdd4f006",
        "broadorigin_3909abaeaae5f79851700c89",
        "broadorigin_5d023073a6de9a88946c97de",
    }
)

# Frozen before packet construction and explicitly accepted by the owner after
# the plan's fe5ab2b15 blindness correction.  Keeping the exact occurrence
# keys here prevents a later change in iteration order or tie implementation
# from silently drawing a different review estate.
APPROVED_SAMPLE_OCCURRENCE_KEYS = frozenset(
    {
        "broadorigin_3247866a456bae417fa61818@@2025-10-28T03:45:00+00:00",
        "broadorigin_6c6c6e24eafc9b7c2d522b39@@2025-10-28T03:00:00+00:00",
        "broadorigin_7bbbaa0ec76c972b79409acd@@2025-10-28T13:45:00+00:00",
        "broadorigin_8764308361e8a27f40edb032@@2025-10-28T09:15:00+00:00",
        "broadorigin_8efda9359f2f4e7d113bfcb5@@2025-10-28T10:00:00+00:00",
        "broadorigin_a3f5a88e91c4c4f3b0b505f3@@2025-10-28T00:45:00+00:00",
        "broadorigin_bc1c47ca9850946e60f55c96@@2025-10-28T09:00:00+00:00",
        "broadorigin_c05a46f86c0278032c63bc6d@@2025-10-28T15:00:00+00:00",
        "broadorigin_dfd825721926203035370f15@@2025-10-28T14:45:00+00:00",
        "broadorigin_0d2c5313f56b7119517bf341@@2025-11-03T01:15:00+00:00",
        "broadorigin_24b0ad4b55fef439369a4934@@2025-11-03T23:45:00+00:00",
        "broadorigin_73b70a818a520a1a0b24c517@@2025-11-03T08:45:00+00:00",
        "broadorigin_ba90adeb7ec8008cf92911ce@@2025-11-03T15:30:00+00:00",
        "broadorigin_f6477fed943714c61e6e38bb@@2025-11-03T03:45:00+00:00",
        "broadorigin_37fd17a9e784ae5e91a3a770@@2025-11-07T05:15:00+00:00",
        "broadorigin_5b0c28651940e16864f9b92d@@2025-11-07T20:45:00+00:00",
        "broadorigin_989c1f8880584b7aaeaaa7b9@@2025-11-07T03:00:00+00:00",
        "broadorigin_b02d4de35cff65f07ba262b5@@2025-11-07T20:00:00+00:00",
        "broadorigin_e85accf10021b78002639421@@2025-11-07T01:45:00+00:00",
        "broadorigin_ebf87136cac34202a76282c8@@2025-11-07T15:15:00+00:00",
    }
)

AXES = ("day", "origin_family", "side", "asset_class", "session", "cost_band", "raw_selector_action")
BAR_CONTEXT_COUNTS = {"D1": 10, "H4": 12, "H1": 24, "M15": 64}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"mapping_required:{path}")
    return value


def dump_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def dump_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def receipt_paths(run: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    label = str(run["label"])
    root = Path(run["root"])
    return (
        root / f"harness_wave21_minimal_repair_{label}_stage_ledger.jsonl.gz",
        root / f"harness_wave21_minimal_repair_{label}_run_receipt.json",
        root / f"harness_wave21_minimal_repair_{label}_source_authority.json",
    )


def verify_run_bindings(run: Mapping[str, Any]) -> dict[str, Any]:
    ledger, receipt, source_authority = receipt_paths(run)
    expected = {
        ledger: str(run["ledger_sha256"]),
        receipt: str(run["receipt_sha256"]),
        Path(run["lane_manifest"]): str(run["lane_manifest_sha256"]),
    }
    actual: dict[str, str] = {}
    for path, expected_sha in expected.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(f"bound_file_sha256_mismatch:{path}:{expected_sha}:{actual_sha}")
        actual[str(path)] = actual_sha
    if not source_authority.is_file():
        raise FileNotFoundError(source_authority)
    actual[str(source_authority)] = sha256_file(source_authority)
    return actual


def cost_band(observables: Mapping[str, Any]) -> str:
    # Refused broker packets omit the executable rounded field but retain the
    # causal quote as expected_cost_r.  A refusal is a high-cost observation,
    # not a source gap.
    raw = observables.get("broker_pretrade_cost_r")
    if raw is None:
        raw = observables.get("expected_cost_r")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return "source_gap"
    if not math.isfinite(value):
        return "source_gap"
    if value <= 0.10:
        return "le_0p10"
    if value <= 0.20:
        return "gt_0p10_le_0p20"
    if value <= 0.35:
        return "gt_0p20_le_0p35"
    if value <= 0.45:
        return "gt_0p35_le_0p45"
    return "gt_0p45"


def preselection_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    identity = row.get("identity") or {}
    observables = row.get("observables") or {}
    symbol = str(identity.get("symbol") or "")
    occurrence_key = str(identity.get("canonical_replay_candidate_instance_key") or "")
    if not occurrence_key:
        occurrence_key = f"{identity.get('candidate_id')}@@{identity.get('decision_time_utc')}"
    return {
        "occurrence_key": occurrence_key,
        "candidate_id": str(identity.get("candidate_id") or ""),
        "day": str(identity.get("trading_day") or ""),
        "decision_time_utc": str(identity.get("decision_time_utc") or ""),
        "symbol": symbol,
        "origin_family": str(identity.get("origin_family") or ""),
        "side": str(identity.get("side") or "").upper(),
        "asset_class": str(ASSET_CLASS_BY_SYMBOL.get(symbol) or "unmapped"),
        "session": str(identity.get("route_session") or ""),
        "cost_band": cost_band(observables),
        "raw_selector_action": str(observables.get("raw_selector_action") or ""),
        "raw_selector_reason": str(observables.get("raw_selector_reason") or ""),
        "_row": row,
    }


def load_candidate_population() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    population: list[dict[str, Any]] = []
    receipts: dict[str, Any] = {}
    bindings: dict[str, Any] = {}
    for run in RUNS:
        bindings[str(run["day"])] = verify_run_bindings(run)
        ledger, receipt_path, _source_authority = receipt_paths(run)
        receipt = load_json(receipt_path)
        receipts[str(run["day"])] = receipt
        with gzip.open(ledger, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                raw = json.loads(line)
                if raw.get("stage") != "candidate":
                    # Do not retain, project, count, or inspect any downstream row.
                    continue
                row = preselection_projection(raw)
                row["_source_line_number"] = line_number
                population.append(row)
    return population, receipts, bindings


def select_sample(population: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    universe: dict[str, set[str]] = {axis: set() for axis in AXES}
    level_population: Counter[tuple[str, str]] = Counter()
    for row in population:
        for axis in AXES:
            level = str(row[axis])
            universe[axis].add(level)
            level_population[(axis, level)] += 1
    insufficient = {
        f"{axis}:{level}": count
        for (axis, level), count in sorted(level_population.items())
        if count < MIN_WITNESSES_PER_LEVEL
    }
    if insufficient:
        raise ValueError(f"population_level_cannot_supply_two_witnesses:{insufficient}")

    by_key = {str(row["occurrence_key"]): row for row in population}
    if len(by_key) != len(population):
        raise ValueError("eligible_population_composite_occurrence_key_not_unique")
    missing = sorted(APPROVED_SAMPLE_OCCURRENCE_KEYS - set(by_key))
    if missing:
        raise ValueError(f"approved_sample_occurrence_missing:{missing}")
    selected = [dict(by_key[key]) for key in sorted(APPROVED_SAMPLE_OCCURRENCE_KEYS)]
    counts: Counter[tuple[str, str]] = Counter(
        (axis, str(row[axis])) for row in selected for axis in AXES
    )
    uncovered = {
        f"{axis}:{level}": counts[(axis, level)]
        for axis, levels in universe.items()
        for level in levels
        if counts[(axis, level)] < MIN_WITNESSES_PER_LEVEL
    }
    if uncovered:
        raise ValueError(f"approved_sample_does_not_cover_every_level_twice:{uncovered}")

    selected.sort(key=lambda row: (row["day"], row["decision_time_utc"], row["occurrence_key"]))
    coverage = {
        axis: {
            level: {
                "population_count": level_population[(axis, level)],
                "sample_count": counts[(axis, level)],
            }
            for level in sorted(universe[axis])
        }
        for axis in AXES
    }
    return selected, coverage


class CausalSourceLoader:
    def __init__(self, receipts: Mapping[str, Mapping[str, Any]]) -> None:
        self.receipts = receipts
        self._rows_cache: dict[tuple[str, str], tuple[dict[str, Any], ...]] = {}
        self._source_cache: dict[tuple[str, str, str], timewarp.ResolvedSource] = {}
        self._lane_manifest_cache: dict[str, dict[str, Any]] = {}
        self._packet_manifest = load_json(PACKET_ROOT / "PACKET_MANIFEST.json")

    @staticmethod
    def _canonical_symbol(value: str) -> str:
        return str(value).upper().replace(".", "_")

    def registered_symbol(self, day: str, symbol: str) -> str:
        entries = self.receipts[day]["inputs"]["source_manifest"]["sources"]
        matches = sorted(
            {
                str(entry.get("symbol"))
                for entry in entries
                if self._canonical_symbol(str(entry.get("symbol")))
                == self._canonical_symbol(symbol)
            }
        )
        if len(matches) != 1:
            raise ValueError(f"one_registered_symbol_required:{day}:{symbol}:{matches}")
        return matches[0]

    def _receipt_source_entry(self, day: str, symbol: str, timeframe: str) -> dict[str, Any]:
        entries = self.receipts[day]["inputs"]["source_manifest"]["sources"]
        matches = [
            dict(entry)
            for entry in entries
            if entry.get("symbol") == symbol and entry.get("timeframe") == timeframe
        ]
        if len(matches) != 1:
            raise ValueError(f"one_receipt_source_required:{day}:{symbol}:{timeframe}:{len(matches)}")
        return matches[0]

    def _lane_entry(self, day: str, symbol: str, timeframe: str) -> dict[str, Any]:
        run = next(item for item in RUNS if item["day"] == day)
        manifest_path = Path(run["lane_manifest"])
        cache_key = str(manifest_path)
        manifest = self._lane_manifest_cache.setdefault(cache_key, load_json(manifest_path))
        matches = [
            dict(entry)
            for entry in manifest["bar_sources"]
            if entry.get("symbol") == symbol and entry.get("timeframe") == timeframe
        ]
        if len(matches) != 1:
            raise ValueError(f"one_lane_source_required:{day}:{symbol}:{timeframe}:{len(matches)}")
        return matches[0]

    def _physical_binding(self, day: str, symbol: str, timeframe: str) -> tuple[Path, str, str]:
        receipt_entry = self._receipt_source_entry(day, symbol, timeframe)
        if timeframe in {"D1", "H4"}:
            lane_entry = self._lane_entry(day, symbol, timeframe)
            path = LANE_ROOT / str(lane_entry["lane_relpath"])
            return path, str(lane_entry["sha256"]), str(receipt_entry["resolved_source_identity_sha256"])
        descriptor = self._packet_manifest["series"][symbol][timeframe]
        path = PACKET_ROOT / str(descriptor["path"])
        return path, str(descriptor["sha256"]), str(receipt_entry["resolved_source_identity_sha256"])

    def _load_rows(self, path: Path, symbol: str, timeframe: str, expected_sha: str) -> tuple[dict[str, Any], ...]:
        cache_key = (str(path), symbol)
        if cache_key in self._rows_cache:
            return self._rows_cache[cache_key]
        actual_sha = sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(f"causal_source_sha256_mismatch:{path}:{expected_sha}:{actual_sha}")
        if timeframe in {"H1", "M15"}:
            rows: list[dict[str, Any]] = []
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    raw = json.loads(line)
                    normalized = timewarp.normalize_row(raw, symbol=symbol)
                    if normalized is None:
                        raise ValueError(f"causal_source_row_invalid:{path}:{line_number}")
                    rows.append(normalized)
            result = tuple(rows)
        else:
            result = timewarp.load_csv_rows(path, symbol=symbol)
        self._rows_cache[cache_key] = result
        return result

    def source(self, day: str, symbol: str, timeframe: str) -> timewarp.ResolvedSource:
        cache_key = (day, symbol, timeframe)
        if cache_key in self._source_cache:
            return self._source_cache[cache_key]
        path, physical_sha, resolved_identity = self._physical_binding(day, symbol, timeframe)
        rows = self._load_rows(path, symbol, timeframe, physical_sha)
        grouped = timewarp.rows_by_day(rows)
        source = timewarp.ResolvedSource(
            spec=timewarp.SourceSpec(
                symbol=symbol,
                mapped_symbol=symbol,
                timeframe=timeframe,
                path=path,
                source_family="professional_review_hash_bound_causal_source",
                source_broker="FTMO",
                source_role="outcome_blind_causal_reconstruction",
                row_count=len(rows),
                sha256=physical_sha,
                source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
                not_redacted_account_native=True,
            ),
            rows=rows,
            rows_by_day=grouped,
            sha256=resolved_identity,
            day_counts={key: len(value) for key, value in grouped.items()},
            selected_status="hash_bound_physical_source_loaded_for_predecision_review",
            min_required_rows_per_day=1,
        )
        self._source_cache[cache_key] = source
        return source

    def raw_data(self, day: str, symbol: str, asof: datetime, config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        symbol = self.registered_symbol(day, symbol)
        sources = {
            timeframe: self.source(day, symbol, timeframe)
            for timeframe in timewarp.PRIMARY_DECISION_TIMEFRAMES
        }
        return timewarp.raw_data_for_asof(
            symbol=symbol,
            sources=sources,
            asof=asof,
            config=config,
        )


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if is_dataclass(value):
        return canonical_json_safe(asdict(value))
    if hasattr(value, "model_dump"):
        return canonical_json_safe(value.model_dump())
    if isinstance(value, Mapping):
        return {str(key): canonical_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, float):
        return value
    if hasattr(value, "__dict__"):
        return canonical_json_safe(vars(value))
    return value


def compact_market_state(mso: Any) -> dict[str, Any]:
    timeframes = getattr(mso, "timeframes", {}) or {}
    tf_projection: dict[str, Any] = {}
    for timeframe, state in sorted(timeframes.items()):
        structure = getattr(state, "structure", None)
        order_blocks = list(getattr(state, "order_blocks", []) or [])
        fair_value_gaps = list(getattr(state, "fair_value_gaps", []) or [])
        tf_projection[str(timeframe)] = {
            "structure_direction": getattr(structure, "direction", None),
            "structure_broken": getattr(structure, "broken", None),
            "bos_direction": getattr(structure, "bos_direction", None),
            "choch_direction": getattr(structure, "choch_direction", None),
            "order_block_count": len(order_blocks),
            "fair_value_gap_count": len(fair_value_gaps),
        }
    pools = list(getattr(mso, "liquidity_pools", []) or [])
    return {
        "timestamp_utc": str(getattr(mso, "timestamp_utc", "") or ""),
        "timeframes": tf_projection,
        "liquidity_pool_count": len(pools),
        "liquidity_pools": [
            {
                "type": getattr(pool, "type", None),
                "price": getattr(pool, "price", None),
                "side": getattr(pool, "side", None),
            }
            for pool in pools
        ],
        "session_levels": canonical_json_safe(getattr(mso, "session_levels", None)),
    }


def compact_source_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    nested_keys = {
        "poi_state": (
            "poi_id",
            "poi_type",
            "poi_timeframe",
            "poi_direction",
            "poi_created_at_utc",
            "poi_age_hours",
            "poi_zone_high",
            "poi_zone_low",
            "poi_filled",
            "poi_invalidated",
            "poi_mitigation_status",
            "poi_max_mitigation_fraction",
            "poi_touch_count",
            "poi_touch_episode_count",
            "poi_terminal_frozen",
            "poi_state_contract_status",
        ),
        "causal_poi_lifecycle": (
            "poi_lifecycle_state",
            "poi_proximity_state",
            "distance_to_limit_atr",
            "distance_to_limit_risk",
            "execution_fill_probability",
            "execution_allowed_by_poi_lifecycle",
            "scheduler_rankable_now",
            "primary_reason",
            "uses_outcome_fields",
        ),
        "predecision_limit_fillability": (
            "current_price",
            "entry_price",
            "stop_loss",
            "unit_risk",
            "distance_to_limit_atr",
            "distance_to_limit_risk",
            "fill_probability",
            "limit_marketable_at_decision",
            "reason",
            "used_only_predecision_fields",
        ),
    }
    for key, value in fields.items():
        if isinstance(value, Mapping):
            if key in nested_keys:
                compact[key] = {
                    nested_key: canonical_json_safe(value.get(nested_key))
                    for nested_key in nested_keys[key]
                    if nested_key in value
                }
            continue
        if isinstance(value, (list, tuple)):
            if len(value) <= 10 and all(
                item is None or isinstance(item, (str, int, float, bool)) for item in value
            ):
                compact[key] = canonical_json_safe(value)
            continue
        compact[key] = canonical_json_safe(value)
    return compact


def compact_source_candidate(candidate: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if candidate is None:
        return None
    keys = (
        "candidate_id",
        "origin_family",
        "candidate_origin_family",
        "framework",
        "symbol",
        "side",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit_1",
        "risk_reward_ratio",
        "session",
        "route_session",
        "candle_open_utc",
        "candle_close_utc",
        "timeframe",
        "entry_reference",
        "stop_or_invalidation",
        "target_reference",
        "rr",
        "predecision_features",
    )
    compact = {key: canonical_json_safe(candidate.get(key)) for key in keys if key in candidate}
    fields = candidate.get("source_fields")
    compact["source_fields"] = compact_source_fields(fields) if isinstance(fields, Mapping) else {}
    return compact


def causal_bars(raw_data: Mapping[str, Any]) -> dict[str, Any]:
    candles = raw_data.get("candles") or {}
    return {
        timeframe: [
            {
                key: row.get(key)
                for key in ("time_utc", "time", "open", "high", "low", "close", "volume")
                if row.get(key) is not None
            }
            for row in list(candles.get(timeframe) or [])[-count:]
        ]
        for timeframe, count in BAR_CONTEXT_COUNTS.items()
    }


def leaders_for(symbol: str) -> tuple[str, ...]:
    canonical = symbol.upper().replace(".", "_")
    return tuple(
        leader
        for leader, lag in LEAD_LAG_PAIRS
        if lag.upper().replace(".", "_") == canonical
    )


def reconstruct_sample_row(
    sampled: Mapping[str, Any],
    receipt: Mapping[str, Any],
    loader: CausalSourceLoader,
) -> dict[str, Any]:
    day = str(sampled["day"])
    symbol = str(sampled["symbol"])
    asof = parse_utc(str(sampled["decision_time_utc"]))
    config = copy.deepcopy(receipt["inputs"]["effective_config_payload"])
    # Side effects are already disabled in the bound receipt; enforce that the
    # review never silently upgrades an unsafe receipt.
    market_state_cfg = config.get("market_state") or {}
    if market_state_cfg.get("side_effect_writes_enabled") is not False:
        raise ValueError(f"market_state_side_effect_boundary_not_false:{day}")
    raw_data, metadata = loader.raw_data(day, symbol, asof, config)
    mso = compute_market_state(copy.deepcopy(raw_data), config)
    cross_raw: dict[str, Any] = {symbol: raw_data}
    for leader in leaders_for(symbol):
        registered_leader = loader.registered_symbol(day, leader)
        leader_raw, _leader_metadata = loader.raw_data(day, registered_leader, asof, config)
        cross_raw[registered_leader] = leader_raw
    generated = generate_live_broader_origin_candidates(
        raw_data=copy.deepcopy(raw_data),
        mso=mso,
        config=config,
        symbol=symbol,
        kill_zone=str(sampled["session"]),
        cross_asset_raw_data={"raw_data_by_symbol": cross_raw},
        now_utc=asof,
    )
    matches = [
        candidate
        for candidate in generated
        if candidate.get("candidate_id") == sampled["candidate_id"]
        and candidate.get("origin_family") == sampled["origin_family"]
        and str(candidate.get("side") or "").upper() == sampled["side"]
    ]
    reconstruction_status = "exact_candidate_identity_reconstructed" if len(matches) == 1 else "not_evaluable_candidate_identity_not_unique"
    source_candidate = matches[0] if len(matches) == 1 else None
    stage = sampled["_row"]
    stage_observables = stage.get("observables") or {}
    runtime_config = config.get("gtos_vnext_runtime") or {}
    public_strata = {axis: sampled[axis] for axis in AXES}
    review_id = "W21-PRE-" + hashlib.sha256(str(sampled["occurrence_key"]).encode()).hexdigest()[:10].upper()
    packet = {
        "schema": f"{SCHEMA_PREFIX}.review_row",
        "review_id": review_id,
        "identity": {
            "occurrence_key": sampled["occurrence_key"],
            "candidate_id": sampled["candidate_id"],
            "decision_time_utc": sampled["decision_time_utc"],
            "symbol": symbol,
            "origin_family": sampled["origin_family"],
            "side": sampled["side"],
        },
        "sample_strata": public_strata,
        "allowed_selector_context": {
            "raw_selector_action": sampled["raw_selector_action"],
            "raw_selector_reason": sampled["raw_selector_reason"],
            "pretrade_cost_band": sampled["cost_band"],
            "pretrade_cost_r": stage_observables.get("broker_pretrade_cost_r"),
            "pretrade_cost_r_refused_packet_quote": stage_observables.get("expected_cost_r"),
            "pretrade_cost_source": stage_observables.get("broker_pretrade_cost_source"),
        },
        "candidate_reconstruction": {
            "status": reconstruction_status,
            "generated_candidate_count": len(generated),
            "matching_candidate_count": len(matches),
            "source_owned_candidate": compact_source_candidate(source_candidate),
            "final_predecision_candidate_geometry": {
                "entry_price": stage_observables.get("entry_price"),
                "stop_loss": stage_observables.get("stop_loss"),
                "take_profit_1": stage_observables.get("take_profit_1"),
                "risk_reward_ratio": stage_observables.get("risk_reward_ratio"),
                "dynamic_geometry_applied": stage_observables.get("dynamic_geometry_applied"),
                "geometry_contract_hash_sha256": stage_observables.get("geometry_contract_hash_sha256"),
            },
        },
        "candidate_policy_context": {
            "source_candidate_min_rr": (config.get("risk") or {}).get("min_rr"),
            "family_target_policy_enabled": bool(
                runtime_config.get("broad_origin_target_policy_enabled", False)
            ),
            "dynamic_geometry_policy_id": runtime_config.get(
                "moonshot_dynamic_target_stop_geometry_v4_policy_id"
            ),
            "dynamic_geometry_default_thesis_horizon_m15_bars": runtime_config.get(
                "moonshot_dynamic_target_stop_geometry_v4_default_thesis_horizon_m15_bars"
            ),
            "exit_policy_time_stop_m15_bars": runtime_config.get(
                "moonshot_exit_policy_v4_time_stop_bars"
            ),
            "dynamic_router_momentum_final_target_r": runtime_config.get(
                "moonshot_dynamic_execution_router_momentum_final_target_r"
            ),
        },
        "market_state": compact_market_state(mso),
        "causal_bar_context": causal_bars(raw_data),
        "source_chronology": {
            "decision_rows_used_by_timeframe": metadata.get("decision_rows_used_by_timeframe"),
            "decision_max_source_time_utc_by_timeframe": metadata.get("decision_max_source_time_utc_by_timeframe"),
            "m1_or_tick_attached_to_decision": metadata.get("m1_or_tick_attached_to_decision"),
            "raw_data_hash_sha256_review_reconstruction": metadata.get("raw_data_hash_sha256"),
            "receipt_raw_source_authority_root_sha256": receipt["inputs"].get("raw_source_authority_fields_by_symbol_root_sha256"),
        },
        "hidden_field_contract": {
            "predicted_probability_hidden": True,
            "predicted_fill_probability_hidden": True,
            "expected_value_hidden": True,
            "ordered_fill_exit_cost_account_stages_read": False,
            "realized_outcome_fields_present": False,
        },
    }
    packet["review_row_root_sha256"] = stable_sha256(packet)
    return packet


def current_poi_target_through_census(
    population: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    loader: CausalSourceLoader,
) -> dict[str, Any]:
    current_rows = [
        row for row in population if str(row["origin_family"]).startswith("current_")
    ]
    by_family: Counter[str] = Counter()
    by_action: Counter[str] = Counter()
    by_family_action: Counter[tuple[str, str]] = Counter()
    by_day: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    for row in current_rows:
        day = str(row["day"])
        receipt_config = receipts[day]["inputs"]["effective_config_payload"]
        runtime = receipt_config.get("gtos_vnext_runtime") or {}
        if runtime.get("broad_origin_target_policy_enabled") not in (None, False):
            raise ValueError(f"declared_family_target_policy_unexpectedly_enabled:{day}")
        source_rr = float((receipt_config.get("risk") or {}).get("min_rr"))
        if source_rr != 1.5:
            raise ValueError(f"unexpected_source_candidate_rr:{day}:{source_rr}")
        observables = row["_row"].get("observables") or {}
        entry = float(observables["entry_price"])
        stop = float(observables["stop_loss"])
        risk = abs(entry - stop)
        side = str(row["side"])
        source_target = entry + source_rr * risk if side == "LONG" else entry - source_rr * risk
        asof = parse_utc(str(row["decision_time_utc"]))
        source = loader.source(day, str(row["symbol"]), "M15")
        closed = timewarp.closed_bar_rows_until(
            source.rows,
            timeframe="M15",
            asof=asof,
            max_rows=1,
        )
        if not closed:
            raise ValueError(f"current_poi_current_price_missing:{row['occurrence_key']}")
        current_price = float(closed[-1]["close"])
        target_through = (
            current_price >= source_target if side == "LONG" else current_price <= source_target
        )
        if not target_through:
            continue
        family = str(row["origin_family"])
        action = str(row["raw_selector_action"])
        by_family[family] += 1
        by_action[action] += 1
        by_family_action[(family, action)] += 1
        by_day[day] += 1
        if len(examples) < 12:
            examples.append(
                {
                    "occurrence_key": row["occurrence_key"],
                    "family": family,
                    "side": side,
                    "symbol": row["symbol"],
                    "current_price": current_price,
                    "source_entry": entry,
                    "source_stop": stop,
                    "source_target_1p5r": source_target,
                    "raw_selector_action": action,
                }
            )
    risk_bearing_actions = {"trade", "reduce-risk", "open-reduced-risk"}
    return {
        "scope": "current_origin_candidates_only_source_owned_1p5R_target_and_latest_closed_m15_price",
        "current_origin_candidate_occurrence_count": len(current_rows),
        "target_already_traversed_occurrence_count": sum(by_family.values()),
        "target_already_traversed_fraction": (
            sum(by_family.values()) / len(current_rows) if current_rows else None
        ),
        "target_already_traversed_risk_bearing_raw_selector_action_count": sum(
            count for action, count in by_action.items() if action in risk_bearing_actions
        ),
        "by_family": dict(sorted(by_family.items())),
        "by_raw_selector_action": dict(sorted(by_action.items())),
        "by_family_and_raw_selector_action": {
            f"{family}|{action}": count
            for (family, action), count in sorted(by_family_action.items())
        },
        "by_day": dict(sorted(by_day.items())),
        "examples_first_12_in_ledger_order_not_quality_ranked": examples,
        "uses_outcome_fields": False,
    }


def population_counts(
    population: Sequence[Mapping[str, Any]],
    receipts: Mapping[str, Mapping[str, Any]],
    loader: CausalSourceLoader,
) -> dict[str, Any]:
    keys = [str(row["occurrence_key"]) for row in population]
    geometry = Counter()
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in population:
        observables = row["_row"].get("observables") or {}
        rr = observables.get("risk_reward_ratio")
        dynamic = observables.get("dynamic_geometry_applied")
        geometry[f"rr={rr}|dynamic={dynamic}"] += 1
        by_family[str(row["origin_family"])][f"rr={rr}|dynamic={dynamic}"] += 1
    return {
        "schema": f"{SCHEMA_PREFIX}.population_counts",
        "full_candidate_occurrence_count": len(population),
        "previously_exposed_candidate_id_count": len(PREVIOUSLY_EXPOSED_CANDIDATE_IDS),
        "previously_exposed_candidate_occurrence_count": sum(
            row["candidate_id"] in PREVIOUSLY_EXPOSED_CANDIDATE_IDS
            for row in population
        ),
        "unique_composite_occurrence_key_count": len(set(keys)),
        "duplicate_composite_occurrence_key_count": len(keys) - len(set(keys)),
        "axis_counts": {
            axis: dict(sorted(Counter(str(row[axis]) for row in population).items()))
            for axis in AXES
        },
        "predecision_geometry_contract_counts": dict(sorted(geometry.items())),
        "predecision_geometry_contract_counts_by_family": {
            family: dict(sorted(counter.items())) for family, counter in sorted(by_family.items())
        },
        "current_poi_target_through_census": current_poi_target_through_census(
            population,
            receipts,
            loader,
        ),
    }


def build(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    full_population, receipts, bindings = load_candidate_population()
    eligible_population = [
        row
        for row in full_population
        if row["candidate_id"] not in PREVIOUSLY_EXPOSED_CANDIDATE_IDS
    ]
    selected, coverage = select_sample(eligible_population)
    loader = CausalSourceLoader(receipts)
    packet_rows = [
        reconstruct_sample_row(row, receipts[str(row["day"])], loader)
        for row in selected
    ]
    if any(
        row["candidate_reconstruction"]["status"] != "exact_candidate_identity_reconstructed"
        for row in packet_rows
    ):
        # The packet is still written, but the affected judgment must remain NE.
        reconstruction_status = "contains_not_evaluable_reconstruction_rows"
    else:
        reconstruction_status = "all_sample_candidate_identities_exactly_reconstructed"

    public_selected = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in selected
    ]
    manifest = {
        "schema": f"{SCHEMA_PREFIX}.sample_manifest",
        "seed": SEED,
        "policy_arm": "retained_875037f1b_0p20R_all_three_days",
        "sampling_input_stage": "candidate_only",
        "sampling_prohibited_fields": [
            "target",
            "stop",
            "time_stop",
            "ordered",
            "fill_or_no_fill",
            "realized_holding",
            "realized_cost",
            "terminal_disposition",
            "outcome",
        ],
        "sampling_axes": list(AXES),
        "algorithm": "pre_artifact_owner_approved_greedy_maximum_marginal_coverage_output_frozen_by_occurrence_key",
        "tie_rule_at_selection": "sha256_seed_pipe_occurrence_key",
        "minimum_witnesses_per_observed_level": MIN_WITNESSES_PER_LEVEL,
        "previously_exposed_candidate_ids_excluded": sorted(PREVIOUSLY_EXPOSED_CANDIDATE_IDS),
        "full_candidate_occurrence_count": len(full_population),
        "candidate_occurrence_count_after_exclusion": len(eligible_population),
        "sample_count": len(selected),
        "coverage": coverage,
        "selected_rows": public_selected,
        "source_bindings": bindings,
        "reconstruction_status": reconstruction_status,
    }
    manifest["sample_manifest_root_sha256"] = stable_sha256(manifest)
    counts = population_counts(full_population, receipts, loader)
    counts["population_counts_root_sha256"] = stable_sha256(counts)

    manifest_path = output_dir / "PREDECISION_SAMPLE_MANIFEST.json"
    packet_path = output_dir / "PREDECISION_REVIEW_PACKET.jsonl"
    counts_path = output_dir / "PREDECISION_POPULATION_COUNTS.json"
    dump_json(manifest_path, manifest)
    dump_jsonl(packet_path, packet_rows)
    dump_json(counts_path, counts)
    receipt_body = {
        "schema": f"{SCHEMA_PREFIX}.packet_receipt",
        "blind_judgments_frozen": False,
        "unblinding_allowed": False,
        "sample_manifest": {"path": manifest_path.name, "sha256": sha256_file(manifest_path)},
        "review_packet": {"path": packet_path.name, "sha256": sha256_file(packet_path), "row_count": len(packet_rows)},
        "population_counts": {"path": counts_path.name, "sha256": sha256_file(counts_path)},
        "downstream_stage_rows_read": 0,
        "outcome_fields_read": 0,
    }
    receipt = {**receipt_body, "receipt_root_sha256": stable_sha256(receipt_body)}
    dump_json(output_dir / "PREDECISION_PACKET_RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
    )
    args = parser.parse_args()
    build(args.output_dir.resolve())


if __name__ == "__main__":
    main()
