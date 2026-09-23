from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_final_full_selector_condition_challenger_recheck"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research.moonshot_default_off_policy_router import (  # noqa: E402
    ASOF_DISPLACEMENT_POLICY_MAP,
    DEFAULT_POLICY,
    select_asof_displacement_policy,
)
from build_vnext_replacement_stage13_full_moonshot_production_selector import (  # noqa: E402
    production_route_session_for_row,
)
from build_vnext_replacement_stage13_full_moonshot_branch_origin_audit import (  # noqa: E402
    ACTIVATED_FRAMEWORKS,
    ACTIVATED_POLICY,
    STAGE05_SHARD_MANIFEST,
    STAGE08_MAP,
    iter_gzip_jsonl as iter_stage05_gzip_jsonl,
    kill_zone_bucket,
    load_broker_map,
    load_feature_map,
    load_repo_schedules,
    policy_value as stage05_policy_value,
)


ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

FINAL_SELECTOR_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
)
FINAL_SELECTOR_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{DATE}.jsonl"
)
OLD_THREE_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_ORIGIN_AUDIT_SUMMARY_{DATE}.json"
)
OLD_THREE_BRANCH_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_REPAIR_LEDGER_{DATE}.jsonl"
)
BROADER_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"
)
BROADER_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
)
BROADER_ALLOWLIST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"
)
UPSTREAM_CONDITION_LEDGER = (
    MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_ROW_REPLAY_LEDGER_{DATE}.jsonl"
)
UPSTREAM_CONDITION_MAP = (
    MOONSHOT_DIR / f"VNEXT_MOONSHOT_STAGE11_CONDITION_ROUTER_INTEGRATION_MAP_{DATE}.json"
)

OUTPUT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_LEDGER_{DATE}.jsonl"
)
OUTPUT_BLOCKERS = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_BLOCKER_LEDGER_{DATE}.jsonl"
)
OUTPUT_CELLS = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_CELL_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_CONDITION_CHALLENGER_RECHECK_SUMMARY_{DATE}.json"
)

POLICY_NAME = "condition_asof_displacement_v1"
SYMBOL_ALIASES = {
    "US30": "US30_cash",
    "US30.CASH": "US30_cash",
    "US30_CASH": "US30_cash",
    "UKOIL": "UKOIL_cash",
    "USOIL": "USOIL_cash",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def canonical_symbol(value: Any) -> str:
    raw = str(value or "")
    return SYMBOL_ALIASES.get(raw.upper().replace(".", "_"), raw)


def normalize_session(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"london", "london_broad", "in_london_early", "in_london_late"}:
        return "london_broad"
    if raw in {"ny", "new_york", "ny_broad", "in_ny_early", "in_ny_late"}:
        return "ny_broad"
    if raw in {"tokyo", "tokyo_broad", "in_tokyo_early", "in_tokyo_late"}:
        return "tokyo_broad"
    if raw in {"off_configured_session", "off_kz", "off_kz_broad", "missing_session", ""}:
        return "off_kz_broad" if raw != "missing_session" else "missing_session"
    return raw


def parse_time(value: Any) -> datetime | None:
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
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def time_key(value: Any) -> str | None:
    parsed = parse_time(value)
    if parsed is None:
        return None
    return parsed.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def utc_hour_bucket(value: Any) -> str | None:
    parsed = parse_time(value)
    if parsed is None:
        return None
    return f"h{parsed.hour:02d}_{(parsed.hour + 1) % 24:02d}"


def production_route_session_for_condition_row(row: dict[str, Any]) -> tuple[str, str, str | None]:
    route_session, session_allowed, session_status = production_route_session_for_row(row)
    if session_allowed:
        return route_session, session_status, None
    bucket = utc_hour_bucket(row.get("decision_time_utc") or row.get("candle_time_utc"))
    if session_status == "outside_configured_session_not_production_executable" and bucket:
        return (
            f"moonshot_{bucket}",
            "outside_configured_session_repaired_to_named_moonshot_hour_bucket",
            bucket,
        )
    return route_session, session_status, bucket


def broad_group_key_from_row(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    route_session, _session_status, hour_bucket = production_route_session_for_condition_row(row)
    return (
        str(row.get("origin_family") or ""),
        canonical_symbol(row.get("symbol")),
        route_session,
        str(row.get("side") or ""),
        str(hour_bucket or ""),
    )


def broad_group_key_from_selector(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("origin_family") or ""),
        canonical_symbol(row.get("symbol")),
        str(row.get("route_session") or "missing_session"),
        str(row.get("side") or ""),
        str(row.get("utc_hour_bucket") or ""),
    )


@dataclass
class Stats:
    rows: int = 0
    total_r: float = 0.0
    wins: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0

    def add(self, value: Any) -> None:
        number = fnum(value)
        if number is None:
            return
        self.rows += 1
        self.total_r += number
        if number > 0:
            self.wins += 1
            self.gross_win_r += number
        elif number < 0:
            self.gross_loss_r += abs(number)

    def record(self) -> dict[str, Any]:
        return {
            "performance_rows": self.rows,
            "selected_count": self.rows,
            "total_r": self.total_r,
            "expectancy_r": self.total_r / self.rows if self.rows else None,
            "win_rate": self.wins / self.rows if self.rows else None,
            "profit_factor": self.gross_win_r / self.gross_loss_r if self.gross_loss_r else None,
            "wins": self.wins,
            "gross_win_r": self.gross_win_r,
            "gross_loss_r": self.gross_loss_r,
        }


@dataclass
class CohortStats:
    denominator_rows: int = 0
    computed_rows: int = 0
    blocked_rows: int = 0
    missing_timestamp_rows: int = 0
    be_full: Stats = None  # type: ignore[assignment]
    be_computable: Stats = None  # type: ignore[assignment]
    condition: Stats = None  # type: ignore[assignment]
    condition_policy_counts: Counter[str] = None  # type: ignore[assignment]
    blocker_counts: Counter[str] = None  # type: ignore[assignment]
    selector_domain_counts: Counter[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.be_full = Stats()
        self.be_computable = Stats()
        self.condition = Stats()
        self.condition_policy_counts = Counter()
        self.blocker_counts = Counter()
        self.selector_domain_counts = Counter()

    def add_row(
        self,
        *,
        be_r: Any,
        condition_r: Any,
        condition_policy: str | None,
        status: str,
        blocker_class: str | None,
        has_timestamp: bool,
        selector_domain: str,
    ) -> None:
        self.denominator_rows += 1
        self.be_full.add(be_r)
        if not has_timestamp:
            self.missing_timestamp_rows += 1
        self.selector_domain_counts[selector_domain] += 1
        if status == "computed":
            self.computed_rows += 1
            self.be_computable.add(be_r)
            self.condition.add(condition_r)
            self.condition_policy_counts[str(condition_policy)] += 1
        else:
            self.blocked_rows += 1
            self.blocker_counts[str(blocker_class or "missing_blocker_class")] += 1

    def record(self) -> dict[str, Any]:
        be = self.be_computable.record()
        condition = self.condition.record()
        return {
            "denominator_rows": self.denominator_rows,
            "condition_computed_rows": self.computed_rows,
            "condition_blocked_rows": self.blocked_rows,
            "missing_timestamp_rows": self.missing_timestamp_rows,
            "be_baseline_on_full_denominator": self.be_full.record(),
            "be_baseline_on_condition_computable_rows": be,
            "condition_challenger_on_computable_rows": condition,
            "condition_vs_be_delta_on_computable_rows": metric_delta(condition, be),
            "condition_policy_counts": dict(sorted(self.condition_policy_counts.items())),
            "condition_blocker_counts": dict(sorted(self.blocker_counts.items())),
            "condition_selector_domain_counts": dict(sorted(self.selector_domain_counts.items())),
        }


def metric_delta(condition: dict[str, Any], be: dict[str, Any]) -> dict[str, Any]:
    def delta(name: str) -> float | None:
        left = condition.get(name)
        right = be.get(name)
        if left is None or right is None:
            return None
        return float(left) - float(right)

    return {
        "total_r_delta": delta("total_r"),
        "expectancy_r_delta": delta("expectancy_r"),
        "profit_factor_delta": delta("profit_factor"),
        "win_rate_delta": delta("win_rate"),
    }


def combine_records(*records: dict[str, Any]) -> dict[str, Any]:
    combined = CohortStats()
    for record in records:
        combined.denominator_rows += int(record.get("denominator_rows") or 0)
        combined.computed_rows += int(record.get("condition_computed_rows") or 0)
        combined.blocked_rows += int(record.get("condition_blocked_rows") or 0)
        combined.missing_timestamp_rows += int(record.get("missing_timestamp_rows") or 0)
        for key, value in (record.get("condition_policy_counts") or {}).items():
            combined.condition_policy_counts[key] += int(value)
        for key, value in (record.get("condition_blocker_counts") or {}).items():
            combined.blocker_counts[key] += int(value)
        for key, value in (record.get("condition_selector_domain_counts") or {}).items():
            combined.selector_domain_counts[key] += int(value)
        for source_name, target in (
            ("be_baseline_on_full_denominator", combined.be_full),
            ("be_baseline_on_condition_computable_rows", combined.be_computable),
            ("condition_challenger_on_computable_rows", combined.condition),
        ):
            source = record.get(source_name) or {}
            target.rows += int(source.get("performance_rows") or 0)
            target.total_r += float(source.get("total_r") or 0.0)
            target.wins += int(source.get("wins") or 0)
            target.gross_win_r += float(source.get("gross_win_r") or 0.0)
            target.gross_loss_r += float(source.get("gross_loss_r") or 0.0)
    return combined.record()


def load_condition_rows() -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    duplicates: Counter[str] = Counter()
    for row in iter_jsonl(UPSTREAM_CONDITION_LEDGER):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        if candidate_id in by_candidate:
            duplicates[candidate_id] += 1
            continue
        by_candidate[candidate_id] = row
    return by_candidate, duplicates


def load_final_selector_groups() -> tuple[dict[str, Any], Counter[str], set[tuple[str, str, str, str, str]]]:
    summary = read_json(FINAL_SELECTOR_SUMMARY)
    row_type_counts: Counter[str] = Counter()
    broader_groups: set[tuple[str, str, str, str, str]] = set()
    for row in iter_jsonl(FINAL_SELECTOR_LEDGER):
        row_type_counts[str(row.get("row_type"))] += 1
        if (
            row.get("row_type") == "broader_origin_group_decision"
            and row.get("final_action") == "activate_broader_origin_group"
        ):
            broader_groups.add(broad_group_key_from_selector(row))
    return summary, row_type_counts, broader_groups


def load_broader_allowlist_groups() -> set[tuple[str, str, str, str, str]]:
    allowlist = read_json(BROADER_ALLOWLIST)
    return {broad_group_key_from_selector(row) for row in allowlist.get("entries", [])}


def displacement_from_source_fields(source_fields: dict[str, Any]) -> tuple[float | None, str]:
    direct = fnum(source_fields.get("current_bar_displacement_atr14"))
    if direct is not None:
        return abs(direct), "source_current_bar_displacement_atr14"
    body = fnum(source_fields.get("body_atr14"))
    if body is not None:
        return abs(body), "source_body_atr14"
    open_ = fnum(source_fields.get("open"))
    close = fnum(source_fields.get("close"))
    atr14 = fnum(source_fields.get("atr14"))
    if open_ is not None and close is not None and atr14 and atr14 > 0:
        return abs(close - open_) / atr14, "computed_abs_close_open_over_atr14"
    range_value = fnum(source_fields.get("range_atr14"))
    if range_value is not None:
        return abs(range_value), "fallback_range_atr14_proxy"
    return None, "missing_displacement_source"


def condition_event_for_broader(row: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    source_fields = row.get("source_fields") or {}
    displacement, displacement_source = displacement_from_source_fields(source_fields)
    route_session, _session_status, hour_bucket = production_route_session_for_condition_row(row)
    session_bucket = normalize_session(route_session)
    origin_family = str(row.get("origin_family") or "")
    event = {
        "framework": origin_family,
        "route_family": origin_family,
        "session_bucket": session_bucket,
        "route_session": session_bucket,
        "current_bar_displacement_atr14": displacement,
    }
    if hour_bucket:
        event["utc_hour_bucket"] = hour_bucket
    key = (
        str(event["framework"]).lower(),
        str(event["session_bucket"]).lower(),
        "missing_disp" if displacement is None else ("high_disp" if displacement >= 1.0 else "low_disp"),
    )
    selector_domain = (
        "broader_origin_no_stage11_policy_override_defaulted_to_be"
        if key not in ASOF_DISPLACEMENT_POLICY_MAP
        else "broader_origin_stage11_policy_override"
    )
    return event, selector_domain, displacement_source


def policy_result_final_r(row: dict[str, Any], policy: str) -> tuple[float | None, str | None]:
    replay = row.get("origin_native_dynamic_policy_replay") or {}
    policy_results = replay.get("policy_results") or {}
    policy_payload = policy_results.get(policy) or {}
    value = fnum(policy_payload.get("final_r"))
    if value is not None:
        return value, "origin_native_dynamic_policy_replay.policy_results"
    if policy == DEFAULT_POLICY:
        value = fnum(row.get("origin_native_dynamic_final_r"))
        if value is not None:
            return value, "origin_native_dynamic_final_r"
    return None, None


def make_cell_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("denominator_component")),
        str(row.get("family")),
        canonical_symbol(row.get("symbol")),
        str(row.get("session_bucket") or row.get("route_session") or "missing_session"),
        str(row.get("side") or ""),
    )


def load_old_three_allow_counts() -> dict[tuple[str, str, str, str, str], int]:
    allow_counts: dict[tuple[str, str, str, str, str], int] = {}
    for row in iter_jsonl(OLD_THREE_BRANCH_LEDGER):
        if row.get("final_action") not in {
            "activate_existing_follow_semantics",
            "activate_with_moonshot_repaired_branch_semantics",
        }:
            continue
        key = (
            str(row.get("symbol")),
            str(row.get("framework")),
            str(row.get("candidate_origin_family")),
            str(row.get("session_bucket")),
            str(row.get("kill_zone_bucket")),
        )
        metrics = row.get("metrics") or {}
        allow_counts[key] = int(metrics.get("performance_rows") or 0)
    return allow_counts


def old_three_condition_row_from_stage05(
    *,
    row: dict[str, Any],
    selected_index: int,
) -> dict[str, Any]:
    candidate_id = str(row.get("candidate_id") or "")
    value = stage05_policy_value(row, ACTIVATED_POLICY)
    be_r = fnum(value)
    condition = row.get("condition_router_projection") or {}
    timestamp = time_key(row.get("candle_time_utc"))
    blocker_class = None
    blocker_detail = None
    condition_policy = condition.get("selected_policy")
    condition_r = fnum(condition.get("selected_policy_final_r"))
    selector_key = condition.get("selector_condition_key")
    displacement_bucket = condition.get("current_bar_displacement_bucket")
    final_r_source = None
    if be_r is None:
        blocker_class = "old_three_be_final_r_missing"
        blocker_detail = "Old-three selected Stage05 row lacks be_after_trigger final R."
    elif not condition_policy:
        blocker_class = "old_three_condition_selected_policy_missing"
        blocker_detail = "Stage05 condition projection exists but has no selected_policy."
    elif condition_r is None:
        blocker_class = "old_three_condition_selected_policy_final_r_missing"
        blocker_detail = "Stage05 condition projection selected a policy but selected_policy_final_r is null."
    else:
        final_r_source = rel(STAGE05_SHARD_MANIFEST)
    status = "computed" if blocker_class is None else "blocked"
    return {
        "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_type": "condition_recheck_denominator_row",
        "denominator_component": "old_three",
        "denominator_row_index": selected_index,
        "source_row_id": candidate_id,
        "candidate_id": candidate_id,
        "family": f"origin_current_{row.get('framework')}",
        "framework": row.get("framework"),
        "symbol": canonical_symbol(row.get("symbol")),
        "session_bucket": row.get("session_bucket"),
        "side": row.get("side"),
        "decision_time_utc": timestamp,
        "be_policy": DEFAULT_POLICY,
        "be_policy_final_r": be_r,
        "condition_policy_name": POLICY_NAME,
        "condition_selector_key": selector_key,
        "current_bar_displacement_bucket": displacement_bucket,
        "condition_selected_policy": condition_policy,
        "condition_selected_policy_final_r": condition_r,
        "condition_vs_be_delta_r": (
            condition_r - be_r if condition_r is not None and be_r is not None else None
        ),
        "condition_recheck_status": status,
        "condition_blocker_class": blocker_class,
        "condition_blocker_detail": blocker_detail,
        "condition_final_r_source": final_r_source,
        "condition_router_r_from_old_three_overlay": None,
        "condition_router_overlay_consistency_delta": None,
        "condition_selector_domain": "old_three_stage11_condition_router",
        "activation_effect": "condition_challenger_recheck_only_default_off",
    }


def old_three_denominator_gap_row(
    *,
    key: tuple[str, str, str, str, str],
    selected_index: int,
    gap_index: int,
) -> dict[str, Any]:
    symbol, framework, candidate_origin_family, session_bucket, kill_zone_bucket = key
    return {
        "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_row_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "row_type": "condition_recheck_denominator_row",
        "denominator_component": "old_three",
        "denominator_row_index": selected_index,
        "source_row_id": (
            "old_three_denominator_gap::"
            f"{symbol}::{framework}::{candidate_origin_family}::{session_bucket}::"
            f"{kill_zone_bucket}::{gap_index}"
        ),
        "candidate_id": None,
        "family": candidate_origin_family,
        "framework": framework,
        "symbol": canonical_symbol(symbol),
        "session_bucket": session_bucket,
        "kill_zone_bucket": kill_zone_bucket,
        "side": "UNKNOWN_SELECTOR_GAP",
        "decision_time_utc": None,
        "be_policy": DEFAULT_POLICY,
        "be_policy_final_r": None,
        "condition_policy_name": POLICY_NAME,
        "condition_selector_key": None,
        "current_bar_displacement_bucket": None,
        "condition_selected_policy": None,
        "condition_selected_policy_final_r": None,
        "condition_vs_be_delta_r": None,
        "condition_recheck_status": "blocked",
        "condition_blocker_class": (
            "old_three_selector_denominator_row_not_reconstructable_from_current_stage05_snapshot"
        ),
        "condition_blocker_detail": (
            "The Stage13 final old-three selector expected this row from the branch repair "
            "ledger, but the mutable Stage05 shard reconstruction no longer emits a matching "
            "computable row. The row remains in the denominator as blocked instead of being "
            "silently dropped."
        ),
        "condition_final_r_source": None,
        "condition_router_r_from_old_three_overlay": None,
        "condition_router_overlay_consistency_delta": None,
        "condition_selector_domain": "old_three_stage11_condition_router_denominator_gap",
        "activation_effect": "condition_challenger_recheck_only_default_off",
    }


def build_old_three_rows() -> Iterator[dict[str, Any]]:
    stage08 = read_json(STAGE08_MAP)
    eligible_symbols = set(stage08["broker_native_activation_eligible_symbols"])
    allow_counts = load_old_three_allow_counts()
    features = load_feature_map()
    broker = load_broker_map()
    schedules = load_repo_schedules()
    rows_by_key: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
        shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
        for row in iter_stage05_gzip_jsonl(shard_path):
            symbol = str(row.get("symbol"))
            feature = features.get(str(row.get("candidate_id")), {})
            broker_info = broker.get(symbol, {})
            kill_bucket, _schedule_class = kill_zone_bucket(
                symbol=symbol,
                row=row,
                feature=feature,
                schedules=schedules,
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status")
                    or "missing_session_hours_status"
                ),
            )
            key = (
                symbol,
                str(row.get("framework")),
                str(row.get("candidate_origin_family")),
                str(row.get("session_bucket")),
                kill_bucket,
            )
            if key not in allow_counts:
                continue
            dynamic = row.get("dynamic_policy_replay") or {}
            if dynamic.get("available") is not True:
                continue
            if symbol not in eligible_symbols:
                continue
            if row.get("framework") not in ACTIVATED_FRAMEWORKS:
                continue
            if not kill_bucket.startswith("in_"):
                continue
            if feature.get("selected_policy_same_bar_ambiguous"):
                continue
            value = stage05_policy_value(row, ACTIVATED_POLICY)
            if value is None:
                continue
            rows_by_key[key].append(row)
    selected_index = 0
    for key, expected_count in sorted(allow_counts.items()):
        actual_rows = rows_by_key.get(key, [])
        for row in actual_rows[:expected_count]:
            selected_index += 1
            yield old_three_condition_row_from_stage05(
                row=row,
                selected_index=selected_index,
            )
        for gap_index in range(max(0, expected_count - len(actual_rows))):
            selected_index += 1
            yield old_three_denominator_gap_row(
                key=key,
                selected_index=selected_index,
                gap_index=gap_index,
            )


def build_broader_rows(selected_groups: set[tuple[str, str, str, str, str]]) -> Iterator[dict[str, Any]]:
    selected_index = 0
    for row in iter_jsonl(BROADER_LEDGER):
        if row.get("row_type") != "candidate_contract" or row.get("activation_ready") is not True:
            continue
        key = broad_group_key_from_row(row)
        if key not in selected_groups:
            continue
        selected_index += 1
        be_r = fnum(row.get("origin_native_dynamic_final_r"))
        event, selector_domain, displacement_source = condition_event_for_broader(row)
        condition_policy, bucket = select_asof_displacement_policy(event)
        condition_r, final_r_source = policy_result_final_r(row, condition_policy)
        blocker_class = None
        blocker_detail = None
        if be_r is None:
            blocker_class = "broader_origin_be_final_r_missing"
            blocker_detail = "Selected broader-origin row lacks origin_native_dynamic_final_r."
        elif condition_r is None:
            blocker_class = "broader_origin_condition_selected_policy_final_r_missing"
            blocker_detail = (
                f"condition_asof_displacement_v1 selected {condition_policy}, but the broader-origin "
                "row only carries final R for available origin-native policy replay results."
            )
        status = "computed" if blocker_class is None else "blocked"
        route_session, session_status, hour_bucket = production_route_session_for_condition_row(row)
        yield {
            "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_row_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "row_type": "condition_recheck_denominator_row",
            "denominator_component": "broader_origin",
            "denominator_row_index": selected_index,
            "source_row_id": row.get("row_id"),
            "candidate_id": row.get("row_id"),
            "family": row.get("candidate_origin_family") or f"origin_{row.get('origin_family')}",
            "framework": row.get("origin_family"),
            "origin_family": row.get("origin_family"),
            "symbol": canonical_symbol(row.get("symbol")),
            "session_bucket": route_session,
            "utc_hour_bucket": hour_bucket,
            "condition_session_bucket": event["session_bucket"],
            "production_session_repair_status": session_status,
            "side": row.get("side"),
            "decision_time_utc": time_key(row.get("decision_time_utc")),
            "be_policy": DEFAULT_POLICY,
            "be_policy_final_r": be_r,
            "condition_policy_name": POLICY_NAME,
            "condition_selector_key": [
                str(event.get("framework")).lower(),
                str(event.get("session_bucket")).lower(),
                bucket,
            ],
            "current_bar_displacement_atr14": event.get("current_bar_displacement_atr14"),
            "current_bar_displacement_bucket": bucket,
            "current_bar_displacement_source": displacement_source,
            "condition_selected_policy": condition_policy,
            "condition_selected_policy_final_r": condition_r,
            "condition_vs_be_delta_r": (
                condition_r - be_r if condition_r is not None and be_r is not None else None
            ),
            "condition_recheck_status": status,
            "condition_blocker_class": blocker_class,
            "condition_blocker_detail": blocker_detail,
            "condition_final_r_source": final_r_source,
            "condition_selector_domain": selector_domain,
            "activation_effect": "condition_challenger_recheck_only_default_off",
        }


def chrono_splits(rows: list[dict[str, Any]], *, folds: int = 5) -> dict[str, Any]:
    timestamped = [
        row for row in rows
        if row.get("condition_recheck_status") == "computed" and row.get("decision_time_utc")
    ]
    timestamped.sort(key=lambda item: str(item.get("decision_time_utc")))
    if not timestamped:
        return {
            "fold_count": 0,
            "row_count": 0,
            "missing_timestamp_rows": sum(1 for row in rows if not row.get("decision_time_utc")),
            "fold_results": [],
        }
    fold_count = min(folds, len(timestamped))
    results: list[dict[str, Any]] = []
    for fold in range(fold_count):
        lo = len(timestamped) * fold // fold_count
        hi = len(timestamped) * (fold + 1) // fold_count
        be = Stats()
        condition = Stats()
        for row in timestamped[lo:hi]:
            be.add(row.get("be_policy_final_r"))
            condition.add(row.get("condition_selected_policy_final_r"))
        be_record = be.record()
        condition_record = condition.record()
        results.append(
            {
                "fold_index": fold,
                "row_count": condition.rows,
                "start_time_utc": timestamped[lo].get("decision_time_utc"),
                "end_time_utc": timestamped[hi - 1].get("decision_time_utc"),
                "be_baseline": be_record,
                "condition_challenger": condition_record,
                "condition_vs_be_delta": metric_delta(condition_record, be_record),
            }
        )
    return {
        "fold_count": fold_count,
        "row_count": len(timestamped),
        "missing_timestamp_rows": sum(1 for row in rows if not row.get("decision_time_utc")),
        "fold_results": results,
    }


def gate_decision(combined: dict[str, Any], chrono: dict[str, Any]) -> dict[str, Any]:
    delta = combined["condition_vs_be_delta_on_computable_rows"]
    condition = combined["condition_challenger_on_computable_rows"]
    be = combined["be_baseline_on_condition_computable_rows"]
    fold_deltas = [
        (row.get("condition_vs_be_delta") or {}).get("expectancy_r_delta")
        for row in chrono.get("fold_results", [])
    ]
    checks = {
        "full_denominator_condition_final_r_available": (
            combined["denominator_rows"] > 0
            and combined["condition_computed_rows"] == combined["denominator_rows"]
            and combined["condition_blocked_rows"] == 0
        ),
        "total_r_beaten": (delta.get("total_r_delta") or 0.0) > 0.0,
        "expectancy_beaten": (delta.get("expectancy_r_delta") or 0.0) > 0.0,
        "profit_factor_beaten": (
            delta.get("profit_factor_delta") is not None
            and delta.get("profit_factor_delta") > 0.0
        ),
        "win_rate_beaten": (
            delta.get("win_rate_delta") is not None
            and delta.get("win_rate_delta") > 0.0
        ),
        "condition_rows_match_be_rows": condition["performance_rows"] == be["performance_rows"],
        "chrono_oof_splits_nonnegative": bool(fold_deltas) and all(
            value is not None and value >= 0.0 for value in fold_deltas
        ),
    }
    passed = all(checks.values())
    return {
        "gate_name": "combined_full_selector_condition_asof_displacement_v1_vs_be_v1",
        "gate_checks": checks,
        "gate_passed": passed,
        "condition_activation_decision": (
            "enable_condition_challenger" if passed else "keep_condition_disabled"
        ),
        "condition_activation_reason": (
            "combined selected denominator beats BE on row availability, total R, expectancy, PF, WR, and chrono splits"
            if passed
            else "condition_asof_displacement_v1 remains disabled because combined proof does not beat BE under every gate check"
        ),
    }


def main() -> None:
    generated_at = utc_now()
    final_summary, final_selector_row_types, final_selector_groups = load_final_selector_groups()
    old_summary = read_json(OLD_THREE_SUMMARY)
    broader_summary = read_json(BROADER_SUMMARY)
    upstream_condition_map = read_json(UPSTREAM_CONDITION_MAP)
    allowlist_groups = load_broader_allowlist_groups()
    selected_groups = final_selector_groups & allowlist_groups

    old_rows = list(build_old_three_rows())
    broader_rows = list(build_broader_rows(selected_groups))
    all_rows = old_rows + broader_rows

    cohorts = {
        "old_three": CohortStats(),
        "broader_origin": CohortStats(),
        "combined": CohortStats(),
    }
    cell_stats: dict[tuple[str, str, str, str, str], CohortStats] = defaultdict(CohortStats)
    blocker_rows: list[dict[str, Any]] = []
    for row in all_rows:
        component = str(row.get("denominator_component"))
        status = str(row.get("condition_recheck_status"))
        for cohort_name in (component, "combined"):
            cohorts[cohort_name].add_row(
                be_r=row.get("be_policy_final_r"),
                condition_r=row.get("condition_selected_policy_final_r"),
                condition_policy=row.get("condition_selected_policy"),
                status=status,
                blocker_class=row.get("condition_blocker_class"),
                has_timestamp=bool(row.get("decision_time_utc")),
                selector_domain=str(row.get("condition_selector_domain")),
            )
        cell_stats[make_cell_key(row)].add_row(
            be_r=row.get("be_policy_final_r"),
            condition_r=row.get("condition_selected_policy_final_r"),
            condition_policy=row.get("condition_selected_policy"),
            status=status,
            blocker_class=row.get("condition_blocker_class"),
            has_timestamp=bool(row.get("decision_time_utc")),
            selector_domain=str(row.get("condition_selector_domain")),
        )
        if status != "computed":
            blocker_rows.append(row)

    cohort_records = {name: cohort.record() for name, cohort in cohorts.items()}
    combined_record = combine_records(cohort_records["old_three"], cohort_records["broader_origin"])
    cohort_records["combined"] = combined_record
    chrono = {
        "old_three": chrono_splits(old_rows),
        "broader_origin": chrono_splits(broader_rows),
        "combined": chrono_splits(all_rows),
    }
    gate = gate_decision(combined_record, chrono["combined"])
    cell_rows = []
    for index, (key, stats) in enumerate(sorted(cell_stats.items()), start=1):
        component, family, symbol, session, side = key
        cell_rows.append(
            {
                "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_cell_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "row_type": "family_symbol_session_side_condition_cell",
                "condition_cell_id": f"STAGE13-CONDITION-CELL-{index:06d}",
                "denominator_component": component,
                "family": family,
                "symbol": symbol,
                "session_bucket": session,
                "side": side,
                "metrics": stats.record(),
            }
        )

    ledger_rows_written = write_jsonl(OUTPUT_LEDGER, all_rows)
    blocker_rows_written = write_jsonl(OUTPUT_BLOCKERS, blocker_rows)
    cell_rows_written = write_jsonl(OUTPUT_CELLS, cell_rows)

    expected_old_rows = int(final_summary.get("old_three_selected_rows") or 0)
    expected_broader_rows = int(final_summary.get("broader_origin_selected_rows") or 0)
    expected_combined_rows = int(final_summary.get("combined_selected_rows") or 0)
    summary = {
        "schema_version": "vnext_replacement_stage13_condition_challenger_recheck_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": generated_at,
        "condition_policy_name": POLICY_NAME,
        "condition_default_policy": DEFAULT_POLICY,
        "status": "condition_challenger_rechecked_default_off",
        "input_artifacts": {
            "final_selector_summary": rel(FINAL_SELECTOR_SUMMARY),
            "final_selector_ledger": rel(FINAL_SELECTOR_LEDGER),
            "old_three_summary": rel(OLD_THREE_SUMMARY),
            "old_three_branch_repair_ledger": rel(OLD_THREE_BRANCH_LEDGER),
            "stage05_shard_manifest_for_old_three_rows": rel(STAGE05_SHARD_MANIFEST),
            "broader_origin_summary": rel(BROADER_SUMMARY),
            "broader_origin_candidate_ledger": rel(BROADER_LEDGER),
            "broader_origin_allowlist": rel(BROADER_ALLOWLIST),
            "upstream_condition_map": rel(UPSTREAM_CONDITION_MAP),
        },
        "output_paths": {
            "condition_recheck_ledger": rel(OUTPUT_LEDGER),
            "condition_blocker_ledger": rel(OUTPUT_BLOCKERS),
            "condition_cell_ledger": rel(OUTPUT_CELLS),
            "summary": rel(OUTPUT_SUMMARY),
        },
        "denominator_rows_expected": {
            "old_three": expected_old_rows,
            "broader_origin": expected_broader_rows,
            "combined": expected_combined_rows,
        },
        "denominator_rows_written": {
            "old_three": len(old_rows),
            "broader_origin": len(broader_rows),
            "combined": ledger_rows_written,
            "blocker_rows": blocker_rows_written,
            "family_symbol_session_side_cells": cell_rows_written,
        },
        "final_selector_row_type_counts": dict(sorted(final_selector_row_types.items())),
        "final_selector_activated_broader_group_count": len(final_selector_groups),
        "allowlist_broader_group_count": len(allowlist_groups),
        "selected_broader_group_intersection_count": len(selected_groups),
        "upstream_condition_prop_terminal_decision": upstream_condition_map.get(
            "prop_aware_terminal_decision"
        ),
        "cohort_metrics": cohort_records,
        "chrono_oof_splits": chrono,
        "condition_activation_gate": gate,
        "condition_runtime_state": {
            "condition_challenger_enabled": False,
            "apply_to_execution": False,
            "reason": gate["condition_activation_reason"],
        },
        "source_boundary": {
            "live_broker_used": False,
            "paid_api_or_network_used": False,
            "runtime_config_or_src_touched": False,
            "selector_uses_only_asof_feature_columns": True,
            "broader_origin_policy_override_status": (
                "broader-origin families have no Stage11 condition override cells; "
                "condition_asof_displacement_v1 falls back to be_after_trigger where final R exists"
            ),
        },
        "old_three_reference": {
            "selector_metrics": old_summary.get("repaired_selector", {}).get("metrics"),
            "condition_router_prior_metrics": (
                old_summary.get("repaired_selector", {})
                .get("comparator_metrics_on_selected_rows", {})
                .get("condition_router")
            ),
        },
        "broader_origin_reference": {
            "selected_metrics": final_summary.get("broader_origin_selected_metrics"),
            "broader_summary_row_counts": broader_summary.get("row_counts"),
        },
    }
    write_json(OUTPUT_SUMMARY, summary)
    print(
        json.dumps(
            {
                "condition_activation_decision": gate["condition_activation_decision"],
                "combined_rows": ledger_rows_written,
                "old_three_rows": len(old_rows),
                "broader_origin_rows": len(broader_rows),
                "combined_expectancy_delta_vs_be": combined_record[
                    "condition_vs_be_delta_on_computable_rows"
                ]["expectancy_r_delta"],
                "combined_profit_factor_delta_vs_be": combined_record[
                    "condition_vs_be_delta_on_computable_rows"
                ]["profit_factor_delta"],
                "condition_blocker_rows": blocker_rows_written,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
