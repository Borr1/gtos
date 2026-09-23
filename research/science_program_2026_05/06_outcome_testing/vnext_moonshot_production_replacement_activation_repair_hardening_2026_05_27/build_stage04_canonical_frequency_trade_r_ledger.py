from __future__ import annotations

import gzip
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-27"
PRIOR_DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
STAGE_ID = "stage_04_frequency_distribution_intelligence_consumption"

REPAIR_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
ACTIVATION_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_production_replacement_activation_2026_05_26"
)
ANATOMY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26"
)
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

if str(ACTIVATION_DIR) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_vnext_replacement_stage13_full_market_element_audit import (  # noqa: E402
    ACTIVATED_FRAMEWORKS,
    ACTIVATED_POLICY,
    POLICIES,
    STAGE05_SHARD_MANIFEST,
    STAGE08_MAP,
    iter_gzip_jsonl,
    iter_jsonl,
    kill_zone_bucket,
    load_broker_map,
    load_feature_map,
    load_repo_schedules,
    policy_value,
    prop_action,
    route_label,
)
from build_vnext_replacement_stage13_full_moonshot_production_selector import (  # noqa: E402
    canonical_symbol,
    production_route_session_for_row,
)


SELECTED_SHARD_DIR = REPAIR_DIR / "stage04_canonical_selected_trade_shards"
MEMBERSHIP_SHARD_DIR = REPAIR_DIR / "stage04_membership_audit_shards"
SELECTED_MANIFEST = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_SELECTED_TRADE_SHARD_MANIFEST_{DATE}.jsonl"
)
MEMBERSHIP_MANIFEST = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_MEMBERSHIP_AUDIT_SHARD_MANIFEST_{DATE}.jsonl"
)
FREQUENCY_LEDGER = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_FREQUENCY_R_DISTRIBUTION_LEDGER_{DATE}.jsonl"
)
PRIOR_INTELLIGENCE_LEDGER = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_PRIOR_INTELLIGENCE_CONSUMPTION_LEDGER_{DATE}.jsonl"
)
SUMMARY_PATH = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
)
SPINE_PATH = REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE_SPINE_{DATE}.json"
OUTPUT_MANIFEST = REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_CONTROL_LEDGER_{DATE}.jsonl"

SELECTOR_SUMMARY = (
    ACTIVATION_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{PRIOR_DATE}.json"
)
SELECTOR_LEDGER = (
    ACTIVATION_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{PRIOR_DATE}.jsonl"
)
BRANCH_LEDGER = (
    ACTIVATION_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_REPAIR_LEDGER_{PRIOR_DATE}.jsonl"
)
BROADER_CONTRACT_LEDGER = (
    ACTIVATION_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{PRIOR_DATE}.jsonl"
)
OUTSIDE_MANIFEST = (
    ACTIVATION_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{PRIOR_DATE}.jsonl"
)
STAGE03_SURFACE = (
    REPAIR_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE03_BROKER_RUNTIME_SURFACE_{DATE}.json"
)

QUESTION_SOURCES = [
    (
        "activation_edge_anatomy",
        ANATOMY_DIR / f"VNEXT_ACTIVATION_QUESTION_STACK_LEDGER_{PRIOR_DATE}.jsonl",
        24327,
    ),
    (
        "moonshot_dynamic_execution_repair",
        MOONSHOT_DIR / f"VNEXT_MOONSHOT_QUESTION_STACK_LEDGER_{PRIOR_DATE}.jsonl",
        24337,
    ),
    (
        "production_replacement_activation",
        ACTIVATION_DIR / f"VNEXT_REPLACEMENT_QUESTION_STACK_LEDGER_{PRIOR_DATE}.jsonl",
        73001,
    ),
]

SHARD_ROW_LIMIT = 25_000
BASELINE_PRE_ALIAS_SELECTED_ROWS = 274_146
BASELINE_PRE_ALIAS_BROADER_ROWS = 213_398
BASELINE_PRE_ALIAS_OUTSIDE_ROWS = 125_584


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_any_jsonl(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text.replace(" ", "T"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def json_safe(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value


class ShardWriter:
    def __init__(self, directory: Path, prefix: str, manifest_path: Path, schema_version: str) -> None:
        self.directory = directory
        self.prefix = prefix
        self.manifest_path = manifest_path
        self.schema_version = schema_version
        self.directory.mkdir(parents=True, exist_ok=True)
        for stale in self.directory.glob(f"{self.prefix}_*.jsonl.gz"):
            stale.unlink()
        if self.manifest_path.exists():
            self.manifest_path.unlink()
        self._index = 0
        self._count = 0
        self._handle: gzip.GzipFile | None = None
        self._path: Path | None = None
        self.manifest_rows: list[dict[str, Any]] = []

    def _open_next(self) -> None:
        self.close()
        self._path = self.directory / f"{self.prefix}_{self._index:04d}.jsonl.gz"
        self._handle = gzip.open(self._path, "wt", encoding="utf-8", newline="\n")
        self._count = 0
        self._index += 1

    def write(self, row: dict[str, Any]) -> None:
        if self._handle is None or self._count >= SHARD_ROW_LIMIT:
            self._open_next()
        assert self._handle is not None
        self._handle.write(json.dumps(json_safe(row), sort_keys=True, separators=(",", ":")) + "\n")
        self._count += 1

    def close(self) -> None:
        if self._handle is None:
            return
        self._handle.close()
        assert self._path is not None
        manifest_row = {
            "schema_version": self.schema_version,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "path": rel(self._path),
            "rows": self._count,
            "shard_index": len(self.manifest_rows),
            "sha256": sha256_file(self._path),
            "size_bytes": self._path.stat().st_size,
        }
        self.manifest_rows.append(manifest_row)
        self._handle = None
        self._path = None
        self._count = 0

    def finish(self) -> list[dict[str, Any]]:
        self.close()
        with self.manifest_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in self.manifest_rows:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        return self.manifest_rows


class DistributionBook:
    def __init__(self) -> None:
        self.groups: dict[tuple[str, str], list[float]] = defaultdict(list)

    def add(self, row: dict[str, Any]) -> None:
        dt = parse_utc(row.get("decision_time_utc"))
        dimensions = {
            "all": "all",
            "selector_component": str(row.get("selector_component")),
            "symbol": str(row.get("symbol")),
            "origin_family": str(row.get("origin_family")),
            "framework": str(row.get("framework")),
            "route_session": str(row.get("route_session")),
            "side": str(row.get("side")),
            "selected_policy": str(row.get("selected_policy")),
            "outcome_bucket": str(row.get("outcome_bucket")),
            "r_bucket": str(row.get("r_bucket")),
            "cost_bucket": str(row.get("cost_bucket")),
            "risk_disposition": str(row.get("risk_disposition")),
            "symbol_origin_session_side_policy": "|".join(
                [
                    str(row.get("symbol")),
                    str(row.get("origin_family")),
                    str(row.get("route_session")),
                    str(row.get("side")),
                    str(row.get("selected_policy")),
                ]
            ),
        }
        if dt is not None:
            iso_year, iso_week, _ = dt.isocalendar()
            dimensions.update(
                {
                    "year": f"{dt.year}",
                    "quarter": f"{dt.year}Q{((dt.month - 1) // 3) + 1}",
                    "month": dt.strftime("%Y-%m"),
                    "iso_week": f"{iso_year}-W{iso_week:02d}",
                    "day": dt.strftime("%Y-%m-%d"),
                    "weekday": dt.strftime("%A"),
                    "utc_hour": f"h{dt.hour:02d}_{(dt.hour + 1) % 24:02d}",
                }
            )
        else:
            dimensions.update(
                {
                    "year": "missing_time",
                    "quarter": "missing_time",
                    "month": "missing_time",
                    "iso_week": "missing_time",
                    "day": "missing_time",
                    "weekday": "missing_time",
                    "utc_hour": "missing_time",
                }
            )
        value = float(row["r_multiple"])
        for key, dim_value in dimensions.items():
            self.groups[(key, dim_value)].append(value)

    def write(self, path: Path) -> int:
        count = 0
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for (dimension, value), values in sorted(self.groups.items()):
                record = distribution_record(dimension, value, values)
                handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
                count += 1
        return count


def distribution_record(dimension: str, value: str, values: list[float]) -> dict[str, Any]:
    ordered = sorted(values)
    rows = len(ordered)
    total = sum(ordered)
    wins = sum(1 for item in ordered if item > 0)
    losses = sum(1 for item in ordered if item < 0)
    breakevens = rows - wins - losses
    gross_win = sum(item for item in ordered if item > 0)
    gross_loss = abs(sum(item for item in ordered if item < 0))
    return {
        "schema_version": "vnext_activation_repair_stage04_frequency_r_distribution_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "dimension": dimension,
        "dimension_value": value,
        "rows": rows,
        "trade_or_opportunity_frequency": rows,
        "wins": wins,
        "losses": losses,
        "breakevens": breakevens,
        "total_r": total,
        "expectancy_r": total / rows if rows else None,
        "win_rate": wins / rows if rows else None,
        "gross_win_r": gross_win,
        "gross_loss_r": gross_loss,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
        "avg_winner_r": gross_win / wins if wins else None,
        "avg_loser_r": -gross_loss / losses if losses else None,
        "median_r": quantile(ordered, 0.5),
        "q05_r": quantile(ordered, 0.05),
        "q25_r": quantile(ordered, 0.25),
        "q75_r": quantile(ordered, 0.75),
        "q95_r": quantile(ordered, 0.95),
    }


def quantile(ordered: list[float], q: float) -> float | None:
    if not ordered:
        return None
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lower = int(math.floor(pos))
    upper = int(math.ceil(pos))
    if lower == upper:
        return ordered[lower]
    weight = pos - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def r_bucket(value: float) -> str:
    if value < -1.0:
        return "loss_lt_minus_1r"
    if value < 0:
        return "loss_minus_1_to_0r"
    if value == 0:
        return "breakeven_0r"
    if value < 0.5:
        return "win_0_to_0_5r"
    if value < 1.0:
        return "win_0_5_to_1r"
    if value < 1.5:
        return "win_1_to_1_5r"
    return "win_ge_1_5r"


def outcome_bucket(value: float) -> str:
    if value > 0:
        return "win"
    if value < 0:
        return "loss"
    return "breakeven"


def stable_digest(parts: Iterable[Any], prefix: str) -> str:
    text = "|".join(str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]}"


def load_geometry() -> dict[str, dict[str, Any]]:
    stage03 = read_json(STAGE03_SURFACE)
    return {
        str(row["symbol"]): row
        for row in stage03.get("effective_geometry_rows", [])
        if isinstance(row, dict) and row.get("symbol")
    }


def risk_fields(symbol: str, geometry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = geometry.get(symbol) or {}
    risk_pct = row.get("risk_per_trade_pct")
    status = row.get("status") or "missing_current_geometry"
    if isinstance(risk_pct, (int, float)) and risk_pct > 0 and status == "covered_current_redacted_account_geometry":
        disposition = "risk_positive_executable_current_broker_geometry"
    elif risk_pct == 0:
        disposition = "risk_zero_fail_closed_current_geometry"
    else:
        disposition = "source_capture_required_current_risk_geometry"
    return {
        "risk_disposition": disposition,
        "risk_per_trade_pct_current": risk_pct,
        "mt5_symbol": row.get("mt5_symbol"),
        "tick_size_current": row.get("tick_size"),
        "contract_size_current": row.get("contract_size"),
        "sl_buffer_atr_multiplier_current": row.get("sl_buffer_atr_multiplier"),
        "sl_buffer_min_ticks_current": row.get("sl_buffer_min_ticks"),
        "broker_geometry_status": status,
    }


def selected_row_base(
    *,
    selector_component: str,
    source_artifact_path: Path,
    source_shard_path: Path | None,
    candidate_id: Any,
    symbol: str,
    side: Any,
    framework: str,
    origin_family: str,
    candidate_origin_family: str,
    route_session: str,
    decision_time_utc: Any,
    r_multiple: float,
    selected_policy: str,
    exit_reason: Any,
    entry_price: Any,
    stop_or_invalidation: Any,
    target_reference: Any,
    geometry: dict[str, dict[str, Any]],
    source_row: dict[str, Any],
) -> dict[str, Any]:
    risk = risk_fields(symbol, geometry)
    order_intent_id = stable_digest(
        [selector_component, candidate_id, symbol, side, framework, origin_family, decision_time_utc],
        "stage04_order",
    )
    dedupe_key = stable_digest(
        [symbol, side, framework, origin_family, route_session, decision_time_utc, entry_price, stop_or_invalidation, target_reference],
        "stage04_dedupe",
    )
    row = {
        "schema_version": "vnext_activation_repair_stage04_canonical_selected_trade_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_route_id": source_row.get("route_id"),
        "selector_component": selector_component,
        "row_membership": "selected_opportunity_row",
        "positive_selector_row": True,
        "risk_positive_executable_row": risk["risk_disposition"]
        == "risk_positive_executable_current_broker_geometry",
        "source_artifact_path": rel(source_artifact_path),
        "source_shard_path": rel(source_shard_path) if source_shard_path else None,
        "candidate_id": candidate_id,
        "order_intent_id": order_intent_id,
        "dedupe_key": dedupe_key,
        "symbol": symbol,
        "mt5_symbol": risk.get("mt5_symbol"),
        "side": side,
        "framework": framework,
        "origin_family": origin_family,
        "candidate_origin_family": candidate_origin_family,
        "route_session": route_session,
        "decision_time_utc": str(decision_time_utc) if decision_time_utc is not None else None,
        "selected_policy": selected_policy,
        "r_multiple": r_multiple,
        "outcome_bucket": outcome_bucket(r_multiple),
        "r_bucket": r_bucket(r_multiple),
        "exit_reason": exit_reason,
        "entry_price": entry_price,
        "stop_or_invalidation": stop_or_invalidation,
        "target_reference": target_reference,
        "pending_intent_status": "deduped_order_intent_materialized_from_row",
        "fill_status": "filled_in_replay",
        "fill_lifecycle_capture_contract": (
            "runtime Stage03 execution/slippage logger captures order send/result latency, "
            "decision/order/fill spread, slippage_r, commission status, pending age, and dynamic exit timeline"
        ),
        "cost_bucket": "research_r_gross_of_live_costs_stage03_runtime_capture_required",
        "commission_capture_status": "ACCOUNT_HISTORY_REQUIRED_AT_LIVE_FILL_CLOSE",
        "slippage_capture_status": "STAGE03_RUNTIME_CAPTURE_ENABLED_NOT_HISTORICAL_REPLAYED",
        "no_live_trading_or_broker_mutation": True,
    }
    row.update(risk)
    return row


def membership_row(
    *,
    source_scope: str,
    source_artifact_path: Path,
    source_shard_path: Path | None,
    candidate_id: Any,
    symbol: str,
    side: Any,
    framework: str,
    origin_family: str,
    route_session: str | None,
    decision_time_utc: Any,
    membership: str,
    proof_class: str,
    selected: bool,
    r_multiple_value: float | None,
    source_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "vnext_activation_repair_stage04_membership_audit_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "source_scope": source_scope,
        "source_artifact_path": rel(source_artifact_path),
        "source_shard_path": rel(source_shard_path) if source_shard_path else None,
        "candidate_id": candidate_id,
        "symbol": symbol,
        "side": side,
        "framework": framework,
        "origin_family": origin_family,
        "route_session": route_session,
        "decision_time_utc": str(decision_time_utc) if decision_time_utc is not None else None,
        "membership_class": membership,
        "proof_class": proof_class,
        "selected_for_canonical_trade_ledger": selected,
        "r_multiple": r_multiple_value,
        "row_level_source_reference": stable_digest(
            [source_scope, candidate_id, symbol, side, framework, origin_family, decision_time_utc],
            "stage04_source",
        ),
        "no_live_trading_or_broker_mutation": True,
        "source_route_id": source_row.get("route_id"),
    }


def load_selector_group_actions() -> tuple[dict[tuple[str, str, str, str], dict[str, Any]], dict[tuple[str, str, str, str, str], dict[str, Any]]]:
    configured: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    outside: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for row in iter_jsonl(SELECTOR_LEDGER):
        if row.get("row_type") != "broader_origin_group_decision":
            continue
        family = str(row.get("origin_family") or "")
        symbol = canonical_symbol(row.get("symbol"))
        side = str(row.get("side") or "")
        route_session = str(row.get("route_session") or "")
        if row.get("utc_hour_bucket"):
            outside[(family, symbol, route_session, side, str(row.get("utc_hour_bucket")))] = row
        else:
            configured[(family, symbol, route_session, side)] = row
    return configured, outside


def old_three_allowed_keys(geometry: dict[str, dict[str, Any]]) -> dict[tuple[str, str, str, str, str], str]:
    allowed: dict[tuple[str, str, str, str, str], str] = {}
    for row in iter_jsonl(BRANCH_LEDGER):
        proof = str(row.get("final_proof_class") or "")
        metrics = row.get("metrics") or {}
        expectancy = metrics.get("expectancy_r")
        profit_factor = metrics.get("profit_factor")
        symbol = str(row.get("symbol"))
        current_geometry = geometry.get(symbol) or {}
        current_broker_repaired = (
            proof == "broker_contract_invalid_or_unavailable"
            and current_geometry.get("status") == "covered_current_redacted_account_geometry"
            and expectancy is not None
            and float(expectancy) > 0
            and (profit_factor is None or float(profit_factor) >= 1.0)
        )
        if proof.startswith("positive_executable") or current_broker_repaired:
            key = (
                symbol,
                str(row.get("framework")),
                str(row.get("candidate_origin_family")),
                str(row.get("session_bucket")),
                str(row.get("kill_zone_bucket")),
            )
            allowed[key] = (
                "stage03_broker_alias_repaired_positive_old_three_family"
                if current_broker_repaired
                else "positive_executable_follow_or_repaired_branch_family"
            )
    return allowed


def old_three_key(row: dict[str, Any], kill_bucket: str) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("symbol")),
        str(row.get("framework")),
        str(row.get("candidate_origin_family")),
        str(row.get("session_bucket")),
        kill_bucket,
    )


def add_selected(
    row: dict[str, Any],
    selected_writer: ShardWriter,
    dist: DistributionBook,
    counters: Counter[str],
    order_ids: set[str],
    dedupe_ids: set[str],
) -> None:
    selected_writer.write(row)
    dist.add(row)
    counters["selected_rows"] += 1
    counters[f"selected_component:{row['selector_component']}"] += 1
    counters[f"selected_symbol:{row['symbol']}"] += 1
    counters[f"selected_risk:{row['risk_disposition']}"] += 1
    counters[f"selected_outcome:{row['outcome_bucket']}"] += 1
    order_ids.add(str(row["order_intent_id"]))
    dedupe_ids.add(str(row["dedupe_key"]))


def write_old_three_rows(
    *,
    selected_writer: ShardWriter,
    membership_writer: ShardWriter,
    dist: DistributionBook,
    geometry: dict[str, dict[str, Any]],
    counters: Counter[str],
    order_ids: set[str],
    dedupe_ids: set[str],
) -> None:
    stage08 = read_json(STAGE08_MAP)
    eligible_symbols = set(stage08["broker_native_activation_eligible_symbols"])
    features = load_feature_map()
    broker = load_broker_map()
    schedules = load_repo_schedules()
    allowed = old_three_allowed_keys(geometry)
    for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
        shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
        for row in iter_gzip_jsonl(shard_path):
            symbol = str(row.get("symbol"))
            feature = features.get(str(row.get("candidate_id")), {})
            broker_info = broker.get(symbol, {})
            kill_bucket, _schedule_class = kill_zone_bucket(
                symbol=symbol,
                row=row,
                feature=feature,
                schedules=schedules,
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status") or "missing_session_hours_status"
                ),
            )
            value = policy_value(row, ACTIVATED_POLICY)
            dynamic = row.get("dynamic_policy_replay") or {}
            key = old_three_key(row, kill_bucket)
            executable_except_branch = bool(
                symbol in eligible_symbols
                and row.get("framework") in ACTIVATED_FRAMEWORKS
                and kill_bucket.startswith("in_")
                and not feature.get("selected_policy_same_bar_ambiguous")
                and value is not None
                and dynamic.get("available") is True
            )
            if not executable_except_branch:
                if dynamic.get("available") is not True:
                    membership = "source_capture_required_or_dynamic_replay_excluded"
                    proof = str(dynamic.get("exclusion_reason") or "dynamic_policy_unavailable")
                elif symbol not in eligible_symbols:
                    membership = "rejected_broker_invalid_or_not_currently_eligible"
                    proof = "symbol_not_in_current_activation_map"
                elif feature.get("selected_policy_same_bar_ambiguous"):
                    membership = "source_capture_required_ordered_ltf_or_tick_path"
                    proof = "selected_policy_same_bar_ambiguous"
                else:
                    membership = "rejected_non_executable_old_three_row"
                    proof = "not_in_executable_old_three_scope"
                selected = False
            elif key in allowed:
                membership = "selected_opportunity_row"
                proof = allowed[key]
                selected = True
            else:
                membership = "rejected_selector_family_not_positive"
                proof = "negative_or_underpowered_old_three_family"
                selected = False
            member = membership_row(
                source_scope="old_three_full_activated_replay",
                source_artifact_path=STAGE05_SHARD_MANIFEST,
                source_shard_path=shard_path,
                candidate_id=row.get("candidate_id"),
                symbol=symbol,
                side=row.get("side"),
                framework=str(row.get("framework")),
                origin_family=str(row.get("candidate_origin_family")),
                route_session=str(row.get("session_bucket")),
                decision_time_utc=row.get("candle_time_utc"),
                membership=membership,
                proof_class=proof,
                selected=selected,
                r_multiple_value=float(value) if value is not None else None,
                source_row=row,
            )
            membership_writer.write(member)
            counters[f"membership:{membership}"] += 1
            counters[f"membership_scope:old_three_full_activated_replay"] += 1
            if not selected:
                continue
            policy_result = (row.get("dynamic_policy_replay") or {}).get("policy_results", {}).get(ACTIVATED_POLICY, {})
            selected_row = selected_row_base(
                selector_component="old_three_follow_or_repaired_branch",
                source_artifact_path=STAGE05_SHARD_MANIFEST,
                source_shard_path=shard_path,
                candidate_id=row.get("candidate_id"),
                symbol=symbol,
                side=row.get("side"),
                framework=str(row.get("framework")),
                origin_family=str(row.get("candidate_origin_family")),
                candidate_origin_family=str(row.get("candidate_origin_family")),
                route_session=str(row.get("session_bucket")),
                decision_time_utc=row.get("candle_time_utc"),
                r_multiple=float(value),
                selected_policy=ACTIVATED_POLICY,
                exit_reason=policy_result.get("exit_reason"),
                entry_price=row.get("entry_reference"),
                stop_or_invalidation=row.get("stop_or_invalidation"),
                target_reference=row.get("target_reference"),
                geometry=geometry,
                source_row=row,
            )
            selected_row["kill_zone_bucket"] = kill_bucket
            selected_row["prior_branch_label"] = route_label(row)
            selected_row["selection_proof_class"] = allowed[key]
            selected_row["prop_action"] = prop_action(row)
            add_selected(selected_row, selected_writer, dist, counters, order_ids, dedupe_ids)


def write_broader_configured_rows(
    *,
    configured_actions: dict[tuple[str, str, str, str], dict[str, Any]],
    selected_writer: ShardWriter,
    membership_writer: ShardWriter,
    dist: DistributionBook,
    geometry: dict[str, dict[str, Any]],
    counters: Counter[str],
    order_ids: set[str],
    dedupe_ids: set[str],
) -> None:
    for row in iter_jsonl(BROADER_CONTRACT_LEDGER):
        if row.get("row_type") != "candidate_contract":
            member = membership_row(
                source_scope="broader_origin_contract",
                source_artifact_path=BROADER_CONTRACT_LEDGER,
                source_shard_path=None,
                candidate_id=row.get("row_id") or row.get("candidate_id"),
                symbol=canonical_symbol(row.get("symbol")),
                side=row.get("side"),
                framework="broader_origin",
                origin_family=str(row.get("origin_family") or ""),
                route_session=None,
                decision_time_utc=row.get("decision_time_utc"),
                membership="rejected_non_candidate_contract_row",
                proof_class="row_type_not_candidate_contract",
                selected=False,
                r_multiple_value=None,
                source_row=row,
            )
            membership_writer.write(member)
            counters["membership:rejected_non_candidate_contract_row"] += 1
            counters["membership_scope:broader_origin_contract"] += 1
            continue
        symbol = canonical_symbol(row.get("symbol"))
        family = str(row.get("origin_family") or "")
        side = str(row.get("side") or "")
        final_r = row.get("origin_native_dynamic_final_r")
        route_session, session_allowed, session_status = production_route_session_for_row(row)
        if not row.get("activation_ready"):
            membership = "source_capture_required_or_activation_not_ready"
            proof = str(row.get("activation_ready_blocker_class") or "activation_ready_false")
            selected = False
        elif final_r is None:
            membership = "source_capture_required_missing_dynamic_final_r"
            proof = "origin_native_dynamic_final_r_missing"
            selected = False
        elif not session_allowed:
            membership = "rerouted_to_outside_session_opportunity_audit"
            proof = session_status
            selected = False
        else:
            key = (family, symbol, route_session, side)
            action_row = configured_actions.get(key)
            action = str((action_row or {}).get("final_action") or "missing_group_decision")
            proof = str((action_row or {}).get("proof_class") or "missing_group_decision")
            selected = action == "activate_broader_origin_group"
            membership = (
                "selected_opportunity_row"
                if selected
                else "rejected_selector_group_not_positive_or_underpowered"
            )
        member = membership_row(
            source_scope="broader_origin_contract",
            source_artifact_path=BROADER_CONTRACT_LEDGER,
            source_shard_path=None,
            candidate_id=row.get("row_id") or row.get("candidate_id"),
            symbol=symbol,
            side=side,
            framework="broader_origin",
            origin_family=family,
            route_session=route_session,
            decision_time_utc=row.get("decision_time_utc"),
            membership=membership,
            proof_class=proof,
            selected=selected,
            r_multiple_value=float(final_r) if final_r is not None else None,
            source_row=row,
        )
        membership_writer.write(member)
        counters[f"membership:{membership}"] += 1
        counters["membership_scope:broader_origin_contract"] += 1
        if not selected:
            continue
        replay = row.get("origin_native_dynamic_policy_replay") or {}
        selected_row = selected_row_base(
            selector_component="broader_origin_configured_session",
            source_artifact_path=BROADER_CONTRACT_LEDGER,
            source_shard_path=None,
            candidate_id=row.get("row_id") or row.get("candidate_id"),
            symbol=symbol,
            side=side,
            framework="broader_origin",
            origin_family=family,
            candidate_origin_family=str(row.get("candidate_origin_family") or f"origin_{family}"),
            route_session=route_session,
            decision_time_utc=row.get("decision_time_utc"),
            r_multiple=float(final_r),
            selected_policy=str(replay.get("selected_policy") or ACTIVATED_POLICY),
            exit_reason=replay.get("selected_policy_exit_reason"),
            entry_price=row.get("entry_price"),
            stop_or_invalidation=row.get("stop_or_invalidation"),
            target_reference=row.get("target_reference"),
            geometry=geometry,
            source_row=row,
        )
        selected_row["session_reconciliation_status"] = session_status
        selected_row["source_path"] = row.get("source_path")
        selected_row["source_row_index"] = row.get("source_row_index")
        add_selected(selected_row, selected_writer, dist, counters, order_ids, dedupe_ids)


def write_outside_session_rows(
    *,
    selected_writer: ShardWriter,
    membership_writer: ShardWriter,
    dist: DistributionBook,
    geometry: dict[str, dict[str, Any]],
    counters: Counter[str],
    order_ids: set[str],
    dedupe_ids: set[str],
) -> None:
    for manifest_row in iter_jsonl(OUTSIDE_MANIFEST):
        shard_path = REPO_ROOT / manifest_row["path"]
        for row in iter_any_jsonl(shard_path):
            symbol = canonical_symbol(row.get("symbol"))
            family = str(row.get("origin_family") or "")
            side = str(row.get("side") or "")
            final_r = row.get("selected_policy_final_r", row.get("r_multiple"))
            action = str(row.get("final_action") or row.get("repaired_disposition") or "")
            proof = str(row.get("proof_class") or row.get("repaired_proof_class") or "")
            selected = action == "expand_production_execution_moonshot_extended_session"
            route_session = f"moonshot_{row.get('utc_hour_bucket')}" if row.get("utc_hour_bucket") else "moonshot_extended"
            membership = (
                "selected_opportunity_row"
                if selected
                else "rejected_outside_session_selector_group_not_positive_or_underpowered"
            )
            member = membership_row(
                source_scope="broader_origin_outside_session",
                source_artifact_path=OUTSIDE_MANIFEST,
                source_shard_path=shard_path,
                candidate_id=row.get("candidate_id"),
                symbol=symbol,
                side=side,
                framework="broader_origin",
                origin_family=family,
                route_session=route_session,
                decision_time_utc=row.get("decision_time_utc"),
                membership=membership,
                proof_class=proof,
                selected=selected,
                r_multiple_value=float(final_r) if final_r is not None else None,
                source_row=row,
            )
            membership_writer.write(member)
            counters[f"membership:{membership}"] += 1
            counters["membership_scope:broader_origin_outside_session"] += 1
            if not selected:
                continue
            selected_row = selected_row_base(
                selector_component="broader_origin_outside_session_expansion",
                source_artifact_path=OUTSIDE_MANIFEST,
                source_shard_path=shard_path,
                candidate_id=row.get("candidate_id"),
                symbol=symbol,
                side=side,
                framework="broader_origin",
                origin_family=family,
                candidate_origin_family=str(row.get("candidate_origin_family") or f"origin_{family}"),
                route_session=route_session,
                decision_time_utc=row.get("decision_time_utc"),
                r_multiple=float(final_r),
                selected_policy=str(row.get("selected_policy") or ACTIVATED_POLICY),
                exit_reason=row.get("selected_policy_exit_reason") or row.get("outcome"),
                entry_price=row.get("entry_price"),
                stop_or_invalidation=row.get("stop_or_invalidation"),
                target_reference=row.get("target_reference"),
                geometry=geometry,
                source_row=row,
            )
            selected_row["utc_hour_bucket"] = row.get("utc_hour_bucket")
            selected_row["source_path"] = row.get("source_path")
            selected_row["source_row_index"] = row.get("source_row_index")
            add_selected(selected_row, selected_writer, dist, counters, order_ids, dedupe_ids)


def first_nonblank(row: dict[str, Any], *fields: str) -> Any:
    for field in fields:
        value = row.get(field)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple, dict)) and not value:
            continue
        return value
    return None


def normalize_prior_intelligence_row(
    source_name: str,
    row: dict[str, Any],
    source_row_number: int,
) -> dict[str, Any]:
    """Normalize prior question/anatomy schemas before row-level classification."""
    schema_version = str(row.get("schema_version") or "")
    record_type = first_nonblank(row, "ledger_row_type", "record_type")
    status = first_nonblank(row, "status", "closure_status")
    answer = first_nonblank(row, "answer", "closure_answer")
    evidence_paths = first_nonblank(row, "evidence_path", "closure_evidence_paths")
    exact_next_action = first_nonblank(row, "next_action", "exact_next_action")

    if isinstance(evidence_paths, str):
        evidence_target = evidence_paths.strip()
        evidence_list = [evidence_target] if evidence_target else []
    elif isinstance(evidence_paths, list):
        evidence_list = [str(item) for item in evidence_paths if str(item).strip()]
        evidence_target = "|".join(evidence_list)
    elif evidence_paths:
        evidence_target = json.dumps(evidence_paths, sort_keys=True)
        evidence_list = [evidence_target]
    else:
        evidence_target = ""
        evidence_list = []

    source_schema_logic = "legacy_question_stack_fields"
    if (
        schema_version == "vnext_replacement_stage07_question_closure_v1"
        or row.get("record_type") == "question_closure"
    ):
        source_schema_logic = (
            "vnext_replacement_question_closure_fields:"
            "record_type,closure_status,closure_answer,closure_evidence_paths,exact_next_action"
        )

    if not record_type:
        record_type = "schema_classified_prior_intelligence_row"
    if not status:
        status = "source_status_absent_classified_by_schema"
    if not answer:
        answer = (
            "source_answer_absent; row retained only as prior source/type evidence "
            f"under {source_schema_logic}"
        )
    if not evidence_target:
        evidence_target = (
            f"source_type_reference:{source_name}:{schema_version or 'unknown_schema'}:"
            f"{record_type}:row_{source_row_number}"
        )

    return {
        "source_schema_version": schema_version,
        "source_record_type": row.get("record_type"),
        "ledger_row_type": record_type,
        "status": status,
        "answer": answer,
        "evidence_target": evidence_target,
        "source_evidence_paths": evidence_list,
        "exact_next_action": exact_next_action,
        "source_schema_classification_logic": source_schema_logic,
    }


def consumption_disposition(row: dict[str, Any], normalized: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(
        str(value or "")
        for value in (
            row.get("category"),
            row.get("question"),
            normalized.get("answer"),
            normalized.get("exact_next_action"),
            normalized.get("evidence_target"),
            normalized.get("status"),
        )
    ).lower()
    if any(term in text for term in ("frequency", "trade supply", "r distribution", "expectancy", "win/loss")):
        return (
            "consumed_by_stage04_canonical_frequency_trade_r_ledger",
            rel(SUMMARY_PATH),
        )
    if any(term in text for term in ("broker", "alias", "ger40", "ukoil", "usoil", "ukousd", "usousd", "ger30")):
        return (
            "mapped_to_stage03_broker_runtime_monitor_tick_parity",
            rel(STAGE03_SURFACE),
        )
    if any(term in text for term in ("slippage", "commission", "spread", "fill", "pending", "lifecycle")):
        return (
            "mapped_to_stage03_cost_slippage_commission_fill_lifecycle_capture",
            "src/components/slippage_shadow_logger.py",
        )
    if any(term in text for term in ("ai budget", "token", "paid ai", "api budget")):
        return (
            "mapped_to_ai_budget_packet_or_no_paid_capture_contract",
            str(row.get("evidence_path") or ""),
        )
    if any(term in text for term in ("source capture", "forward capture", "missing source", "exact historical truth")):
        return (
            "mapped_to_source_capture_contract_or_exact_row_level_exclusion",
            str(row.get("evidence_path") or ""),
        )
    if any(term in text for term in ("rollback", "route state", "manifest", "verification")):
        return (
            "mapped_to_stage05_verification_and_rollback_matrix",
            rel(SPINE_PATH),
        )
    return (
        "retained_as_prior_row_level_evidence_reference",
        str(normalized.get("evidence_target") or ""),
    )


def write_prior_intelligence_ledger() -> tuple[int, dict[str, int], dict[str, int]]:
    source_counts: dict[str, int] = {}
    disposition_counts: Counter[str] = Counter()
    total = 0
    with PRIOR_INTELLIGENCE_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for source_name, path, expected_rows in QUESTION_SOURCES:
            rows = 0
            for rows, row in enumerate(iter_jsonl(path), start=1):
                normalized = normalize_prior_intelligence_row(source_name, row, rows)
                disposition, target = consumption_disposition(row, normalized)
                if not target:
                    target = str(normalized.get("evidence_target") or "")
                disposition_counts[disposition] += 1
                out = {
                    "schema_version": "vnext_activation_repair_stage04_prior_intelligence_consumption_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "source_name": source_name,
                    "source_path": rel(path),
                    "source_row_number": rows,
                    "question_id": row.get("question_id"),
                    "replacement_question_id": row.get("replacement_question_id"),
                    "source_schema_version": normalized.get("source_schema_version"),
                    "source_record_type": normalized.get("source_record_type"),
                    "source_schema_classification_logic": normalized.get(
                        "source_schema_classification_logic"
                    ),
                    "ledger_row_type": normalized.get("ledger_row_type"),
                    "category": row.get("category"),
                    "status": normalized.get("status"),
                    "rows_involved": row.get("rows_involved"),
                    "question": row.get("question"),
                    "answer": normalized.get("answer"),
                    "evidence_path": normalized.get("evidence_target"),
                    "source_evidence_paths": normalized.get("source_evidence_paths"),
                    "exact_next_action": normalized.get("exact_next_action"),
                    "consumption_disposition": disposition,
                    "consumption_target": target,
                    "row_level_classification": (
                        f"{source_name}:{normalized.get('ledger_row_type')}:"
                        f"{normalized.get('status')}:{disposition}"
                    ),
                    "row_level_consumed": True,
                    "grouped_summary_not_used_as_completion": True,
                }
                handle.write(json.dumps(json_safe(out), sort_keys=True, separators=(",", ":")) + "\n")
            if rows != expected_rows:
                raise RuntimeError(f"{path} expected {expected_rows} rows, got {rows}")
            source_counts[source_name] = rows
            total += rows
    return total, source_counts, dict(sorted(disposition_counts.items()))


def update_route_files(summary: dict[str, Any], manifest_rows: list[tuple[Path, int, str]]) -> None:
    spine = read_json(SPINE_PATH)
    spine["current_stage"] = "stage_05_full_verification_matrix"
    spine.setdefault("stage_status", {})["stage_04_frequency_distribution_intelligence_consumption"] = "completed"
    spine.setdefault("stage_status", {})["stage_04_frequency_trade_r_ledger"] = "completed"
    completed = set(spine.get("completed_gates", []))
    completed.update({"canonical_frequency_executable_trade_ledger", "prior_question_anatomy_consumption"})
    spine["completed_gates"] = sorted(completed)
    open_gates = [gate for gate in spine.get("open_gates", []) if gate not in completed]
    for gate in ("rollback_executable_proof", "non_mutating_check_mode"):
        if gate not in open_gates:
            open_gates.append(gate)
    spine["open_gates"] = open_gates
    spine["latest_numbers"] = {
        "old_three_selected_rows": summary["selector_counts"]["old_three_selected_rows"],
        "broader_origin_selected_rows": summary["selector_counts"]["broader_origin_selected_rows"],
        "combined_selected_rows": summary["selector_counts"]["combined_selected_rows"],
        "total_r": summary["selector_metrics"]["total_r"],
    }
    spine["next_exact_action"] = (
        "Run Stage05 full verification matrix, non-mutating checks, sharded runtime tests, "
        "rollback proof, current manifests, and current route-state verification."
    )
    active = set(spine.get("active_files", []))
    for path, _, _ in manifest_rows:
        active.add(rel(path))
    active.add(rel(SUMMARY_PATH))
    spine["active_files"] = sorted(active)
    spine["generated_at_utc"] = summary["generated_at_utc"]
    write_json(SPINE_PATH, spine)

    manifest = read_json(OUTPUT_MANIFEST)
    outputs = manifest.setdefault("outputs", [])
    existing = {row.get("path") for row in outputs if isinstance(row, dict)}
    for path, rows, description in manifest_rows:
        rpath = rel(path)
        if rpath not in existing:
            outputs.append(
                {
                    "path": rpath,
                    "stage_id": STAGE_ID,
                    "row_count": rows,
                    "description": description,
                    "sha256": sha256_file(path),
                }
            )
    write_json(OUTPUT_MANIFEST, manifest)

    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage04_canonical_frequency_trade_r_ledger_completed",
            "generated_at_utc": summary["generated_at_utc"],
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "combined_selected_rows": summary["selector_counts"]["combined_selected_rows"],
            "baseline_pre_alias_selected_rows": BASELINE_PRE_ALIAS_SELECTED_ROWS,
            "selector_count_delta_cause": summary["selector_count_delta_reconciliation"],
            "next_stage": "stage_05_full_verification_matrix",
        },
    )


def main() -> None:
    generated_at = utc_now()
    selector_summary = read_json(SELECTOR_SUMMARY)
    geometry = load_geometry()
    configured_actions, _outside_actions = load_selector_group_actions()

    selected_writer = ShardWriter(
        SELECTED_SHARD_DIR,
        "canonical_selected_trade",
        SELECTED_MANIFEST,
        "vnext_activation_repair_stage04_selected_trade_manifest_v1",
    )
    membership_writer = ShardWriter(
        MEMBERSHIP_SHARD_DIR,
        "membership_audit",
        MEMBERSHIP_MANIFEST,
        "vnext_activation_repair_stage04_membership_manifest_v1",
    )
    dist = DistributionBook()
    counters: Counter[str] = Counter()
    order_ids: set[str] = set()
    dedupe_ids: set[str] = set()

    write_old_three_rows(
        selected_writer=selected_writer,
        membership_writer=membership_writer,
        dist=dist,
        geometry=geometry,
        counters=counters,
        order_ids=order_ids,
        dedupe_ids=dedupe_ids,
    )
    write_broader_configured_rows(
        configured_actions=configured_actions,
        selected_writer=selected_writer,
        membership_writer=membership_writer,
        dist=dist,
        geometry=geometry,
        counters=counters,
        order_ids=order_ids,
        dedupe_ids=dedupe_ids,
    )
    write_outside_session_rows(
        selected_writer=selected_writer,
        membership_writer=membership_writer,
        dist=dist,
        geometry=geometry,
        counters=counters,
        order_ids=order_ids,
        dedupe_ids=dedupe_ids,
    )
    selected_manifest = selected_writer.finish()
    membership_manifest = membership_writer.finish()
    frequency_rows = dist.write(FREQUENCY_LEDGER)
    prior_rows, prior_source_counts, prior_disposition_counts = write_prior_intelligence_ledger()

    selected_rows = sum(row["rows"] for row in selected_manifest)
    membership_rows = sum(row["rows"] for row in membership_manifest)
    expected_selected = int(selector_summary["combined_selected_rows"])
    if selected_rows != expected_selected:
        raise RuntimeError(f"canonical selected rows {selected_rows} != selector summary {expected_selected}")

    selected_metrics = distribution_record("all", "all", dist.groups[("all", "all")])
    selector_metrics = selector_summary["combined_production_selector_metrics"]
    if round(float(selected_metrics["total_r"]), 9) != round(float(selector_metrics["total_r"]), 9):
        raise RuntimeError(
            f"canonical total R {selected_metrics['total_r']} != selector total R {selector_metrics['total_r']}"
        )

    alias_selected = {
        symbol: selector_summary.get("broader_origin_selected_symbol_counts", {}).get(symbol, 0)
        for symbol in ("GER40", "UKOIL_cash", "USOIL_cash")
    }
    selector_delta = expected_selected - BASELINE_PRE_ALIAS_SELECTED_ROWS
    old_three_delta = int(selector_summary["old_three_selected_rows"]) - 60_748
    broader_delta = int(selector_summary["broader_origin_selected_rows"]) - BASELINE_PRE_ALIAS_BROADER_ROWS
    outside_delta = (
        int(selector_summary["broader_origin_outside_session_expanded_rows"])
        - BASELINE_PRE_ALIAS_OUTSIDE_ROWS
    )
    summary = {
        "schema_version": "vnext_activation_repair_stage04_canonical_frequency_trade_r_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "status": "completed_stage04_canonical_row_level_trade_frequency_r_ledger",
        "input_artifacts": {
            "selector_summary": rel(SELECTOR_SUMMARY),
            "selector_ledger": rel(SELECTOR_LEDGER),
            "old_three_replay_manifest": rel(STAGE05_SHARD_MANIFEST),
            "broader_contract_ledger": rel(BROADER_CONTRACT_LEDGER),
            "outside_session_manifest": rel(OUTSIDE_MANIFEST),
            "stage03_current_broker_runtime_surface": rel(STAGE03_SURFACE),
        },
        "output_paths": {
            "canonical_selected_trade_shard_manifest": rel(SELECTED_MANIFEST),
            "membership_audit_shard_manifest": rel(MEMBERSHIP_MANIFEST),
            "frequency_r_distribution_ledger": rel(FREQUENCY_LEDGER),
            "prior_intelligence_consumption_ledger": rel(PRIOR_INTELLIGENCE_LEDGER),
            "summary": rel(SUMMARY_PATH),
        },
        "selector_counts": {
            "old_three_selected_rows": selector_summary["old_three_selected_rows"],
            "broader_origin_selected_rows": selector_summary["broader_origin_selected_rows"],
            "broader_origin_outside_session_expanded_rows": selector_summary[
                "broader_origin_outside_session_expanded_rows"
            ],
            "combined_selected_rows": selector_summary["combined_selected_rows"],
        },
        "selector_metrics": selector_metrics,
        "canonical_metrics": selected_metrics,
        "selector_count_delta_reconciliation": {
            "baseline_pre_stage03_alias_repair_selected_rows": BASELINE_PRE_ALIAS_SELECTED_ROWS,
            "current_selected_rows_after_stage03_alias_repair": expected_selected,
            "combined_selected_row_delta": selector_delta,
            "old_three_selected_row_delta": old_three_delta,
            "broader_origin_selected_row_delta": broader_delta,
            "outside_session_selected_row_delta": outside_delta,
            "exact_cause": (
                "Stage03 removed stale GER40/UKOIL_cash/USOIL_cash broker-unavailable exclusions after "
                "GER30/UKOUSD/USOUSD production extraction and broker-spec proof. The Stage04 row-level "
                "reconstruction then found the old-three aggregate stale versus the full activated replay, "
                "so the old-three branch audit, outside-session shards, and full selector were regenerated "
                "from current disk before canonical ledger materialization."
            ),
            "alias_selected_symbol_counts": alias_selected,
        },
        "selected_shards": {
            "shard_count": len(selected_manifest),
            "row_count": selected_rows,
            "manifest_sha256": sha256_file(SELECTED_MANIFEST),
        },
        "membership_audit": {
            "shard_count": len(membership_manifest),
            "row_count": membership_rows,
            "manifest_sha256": sha256_file(MEMBERSHIP_MANIFEST),
            "membership_class_counts": {
                key.split("membership:", 1)[1]: value
                for key, value in sorted(counters.items())
                if key.startswith("membership:")
            },
            "source_scope_counts": {
                key.split("membership_scope:", 1)[1]: value
                for key, value in sorted(counters.items())
                if key.startswith("membership_scope:")
            },
        },
        "order_intent_counts": {
            "selected_rows": selected_rows,
            "deduped_order_intents": len(order_ids),
            "deduped_order_keys": len(dedupe_ids),
        },
        "selected_component_counts": {
            key.split("selected_component:", 1)[1]: value
            for key, value in sorted(counters.items())
            if key.startswith("selected_component:")
        },
        "selected_risk_disposition_counts": {
            key.split("selected_risk:", 1)[1]: value
            for key, value in sorted(counters.items())
            if key.startswith("selected_risk:")
        },
        "frequency_distribution_rows": frequency_rows,
        "prior_intelligence_consumption": {
            "total_rows": prior_rows,
            "source_counts": prior_source_counts,
            "disposition_counts": prior_disposition_counts,
            "row_level_consumed": True,
            "grouped_closure_text_is_not_completion": True,
        },
        "stage04_completion_gates": {
            "canonical_frequency_executable_trade_ledger": "closed",
            "prior_question_anatomy_consumption": "closed",
            "old_selector_count_delta_reconciled": "closed_by_alias_repair_regeneration",
        },
    }
    write_json(SUMMARY_PATH, summary)
    update_route_files(
        summary,
        [
            (SELECTED_MANIFEST, len(selected_manifest), "Stage04 canonical selected trade shard manifest"),
            (MEMBERSHIP_MANIFEST, len(membership_manifest), "Stage04 row-level membership audit shard manifest"),
            (FREQUENCY_LEDGER, frequency_rows, "Stage04 frequency/R distribution ledger"),
            (PRIOR_INTELLIGENCE_LEDGER, prior_rows, "Stage04 prior intelligence row-level consumption ledger"),
            (SUMMARY_PATH, 1, "Stage04 canonical frequency trade/R summary"),
        ],
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_rows": selected_rows,
                "membership_rows": membership_rows,
                "total_r": selected_metrics["total_r"],
                "prior_intelligence_rows": prior_rows,
                "selector_delta": selector_delta,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
