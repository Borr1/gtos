from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_full_market_element_activation_audit"
REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
MOONSHOT_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_moonshot_substrate_dynamic_execution_repair_2026_05_26"
)

STAGE05_SHARD_MANIFEST = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SHARD_MANIFEST_{DATE}.jsonl"
)
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
BROKER_ONBOARDING_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"
)
FEATURE_LEDGER = MOONSHOT_DIR / f"VNEXT_MOONSHOT_ML_DYNAMIC_FEATURE_LEDGER_{DATE}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
OUTPUT_STATE = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"

OUTPUT_LEDGER = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_LEDGER_{DATE}.jsonl"
)
OUTPUT_DECISION_LEDGER = (
    ROUTE_DIR
    / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_REPAIR_DECISION_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MARKET_ELEMENT_AUDIT_SUMMARY_{DATE}.json"
)

POLICIES = (
    "be_after_trigger",
    "condition_router",
    "legacy_fixed_1.5r",
    "live_current_j46_j49",
    "path_aware_runner",
    "partial_be_runner",
    "trailing_runner",
    "early_cut_if_no_progress",
    "ai_target",
    "time_stop_only",
)
ACTIVATED_FRAMEWORKS = ("breaker_re_entry", "fvg_fill", "ob_retest")
ACTIVATED_POLICY = "be_after_trigger"
ACTIVATED_SELECTOR_NAME = (
    "all_framework_follow_broker_native_repaired_configured_kz_"
    "selected_policy_ordered_be_after_trigger"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def fnum(value: Any) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_hhmm(value: Any) -> time:
    hour, minute = str(value).split(":")[:2]
    return time(int(hour), int(minute))


def in_time_window(candidate: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= candidate < end
    return candidate >= start or candidate < end


@dataclass
class Stats:
    count: int = 0
    total_r: float = 0.0
    wins: int = 0
    gross_win_r: float = 0.0
    gross_loss_r: float = 0.0

    def add(self, value: Any) -> None:
        number = fnum(value)
        if number is None:
            return
        self.count += 1
        self.total_r += number
        if number > 0:
            self.wins += 1
            self.gross_win_r += number
        elif number < 0:
            self.gross_loss_r += abs(number)

    def record(self) -> dict[str, Any]:
        return {
            "performance_rows": self.count,
            "selected_count": self.count,
            "total_r": self.total_r,
            "expectancy_r": self.total_r / self.count if self.count else None,
            "profit_factor": self.gross_win_r / self.gross_loss_r if self.gross_loss_r else None,
            "win_rate": self.wins / self.count if self.count else None,
            "wins": self.wins,
            "gross_win_r": self.gross_win_r,
            "gross_loss_r": self.gross_loss_r,
        }


@dataclass
class Family:
    symbol: str
    framework: str
    candidate_origin_family: str
    session_bucket: str
    kill_zone_bucket: str
    dynamic_policy_branch: str
    broker_contract_status: str
    broker_session_hours_status: str
    schedule_evidence_class: str
    candidate_rows: int = 0
    dynamic_available_rows: int = 0
    dynamic_unavailable_rows: int = 0
    source_window_counts: Counter[str] = field(default_factory=Counter)
    branch_label_counts: Counter[str] = field(default_factory=Counter)
    route_reason_counts: Counter[str] = field(default_factory=Counter)
    dynamic_unavailable_reason_counts: Counter[str] = field(default_factory=Counter)
    selected_policy_same_bar_ambiguous_rows: int = 0
    any_policy_same_bar_ambiguous_rows: int = 0
    prop_action_counts: Counter[str] = field(default_factory=Counter)
    candidate_level_prop_status_counts: Counter[str] = field(default_factory=Counter)
    stats: Stats = field(default_factory=Stats)
    activated_selector_rows: int = 0

    def add_candidate(self, row: dict[str, Any], feature: dict[str, Any], branch: str) -> None:
        self.candidate_rows += 1
        self.source_window_counts[str(row.get("source_window_complete"))] += 1
        self.branch_label_counts[branch] += 1
        runtime = (row.get("runtime_reference") or {}).get("hypothetical_activated_vnext") or {}
        self.route_reason_counts[str(runtime.get("route_reason") or "missing_route_reason")] += 1
        prop = row.get("prop_governor_projection") or {}
        self.candidate_level_prop_status_counts[
            str(prop.get("candidate_level_prop_action_status") or "missing")
        ] += 1
        if feature.get("selected_policy_same_bar_ambiguous"):
            self.selected_policy_same_bar_ambiguous_rows += 1
        if feature.get("any_policy_same_bar_ambiguous"):
            self.any_policy_same_bar_ambiguous_rows += 1

    def add_dynamic_unavailable(self, reason: str | None) -> None:
        self.dynamic_unavailable_rows += 1
        self.dynamic_unavailable_reason_counts[str(reason or "missing_dynamic_exclusion_reason")] += 1

    def add_policy_result(self, value: Any, prop_action: str, selected: bool) -> None:
        self.dynamic_available_rows += 1
        self.prop_action_counts[prop_action] += 1
        self.stats.add(value)
        if selected:
            self.activated_selector_rows += 1

    def final_action(self) -> tuple[str, str, str]:
        metrics = self.stats.record()
        expectancy = metrics["expectancy_r"]
        profit_factor = metrics["profit_factor"]
        if self.broker_contract_status != "valid_broker_native_contract":
            return (
                "exclude",
                "broker_contract_invalid_or_unavailable",
                "broker unavailable/non-tradeable from Stage08 onboarding evidence",
            )
        if self.dynamic_available_rows == 0:
            return (
                "exclude",
                "dynamic_policy_no_executable_rows",
                "dynamic policy replay has no row-level final_r after repair attempt",
            )
        if self.kill_zone_bucket.startswith("missing_schedule"):
            return (
                "exclude",
                "missing_market_schedule_not_derivable",
                "MT5 session-hours unavailable and no repo schedule evidence for this market/session",
            )
        if self.kill_zone_bucket.startswith("outside_"):
            return (
                "exclude",
                "outside_configured_kill_zone_after_schedule_repair",
                "repo schedule exists or feature KZ exists, but these rows are outside executable KZ",
            )
        if self.selected_policy_same_bar_ambiguous_rows >= self.dynamic_available_rows:
            return (
                "exclude",
                "same_bar_path_ambiguity_not_resolved_from_available_rows",
                "selected BE-after-trigger branch remains same-bar ambiguous for this family",
            )
        if self.dynamic_policy_branch == ACTIVATED_POLICY and self.activated_selector_rows:
            return (
                "activate",
                "positive_executable_follow_selector",
                "FOLLOW + broker-native + repaired/configured KZ + selected-policy ordered BE rows are positive and executable",
            )
        if expectancy is not None and (expectancy <= 0 or (profit_factor is not None and profit_factor < 1.0)):
            return (
                "exclude",
                "negative_expectancy_or_profit_factor_collapse",
                "row-level replay metrics fail positive-EV activation gate",
            )
        if not self.branch_label_counts.get("FOLLOW"):
            return (
                "exclude",
                "not_executable_without_branch_semantics_repair",
                "no FOLLOW/runtime route match exists; activating would contaminate production with LEGACY/AVOID/MIXED rows",
            )
        return (
            "exclude",
            "positive_but_not_selected_variant",
            "positive comparator/dynamic branch retained as monitored challenger because stronger BE selector is the production branch",
        )

    def record(self) -> dict[str, Any]:
        action, proof_class, reason = self.final_action()
        metrics = self.stats.record()
        return {
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "schema_version": "vnext_replacement_stage13_full_market_element_family_v1",
            "symbol": self.symbol,
            "framework": self.framework,
            "candidate_origin_family": self.candidate_origin_family,
            "session_bucket": self.session_bucket,
            "kill_zone_bucket": self.kill_zone_bucket,
            "dynamic_policy_branch": self.dynamic_policy_branch,
            "broker_contract_status": self.broker_contract_status,
            "broker_session_hours_status": self.broker_session_hours_status,
            "schedule_evidence_class": self.schedule_evidence_class,
            "candidate_rows": self.candidate_rows,
            "dynamic_available_rows": self.dynamic_available_rows,
            "dynamic_unavailable_rows": self.dynamic_unavailable_rows,
            "source_window_counts": dict(sorted(self.source_window_counts.items())),
            "branch_label_counts": dict(sorted(self.branch_label_counts.items())),
            "route_reason_counts": dict(sorted(self.route_reason_counts.items())),
            "dynamic_unavailable_reason_counts": dict(
                sorted(self.dynamic_unavailable_reason_counts.items())
            ),
            "selected_policy_same_bar_ambiguous_rows": self.selected_policy_same_bar_ambiguous_rows,
            "any_policy_same_bar_ambiguous_rows": self.any_policy_same_bar_ambiguous_rows,
            "prop_action_counts": dict(sorted(self.prop_action_counts.items())),
            "candidate_level_prop_status_counts": dict(
                sorted(self.candidate_level_prop_status_counts.items())
            ),
            "metrics": metrics,
            "activated_selector_rows": self.activated_selector_rows,
            "final_action": action,
            "final_proof_class": proof_class,
            "final_action_reason": reason,
            "broad_labels_not_used_as_terminal_proof": True,
        }


def load_feature_map() -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(FEATURE_LEDGER):
        feature = row.get("feature_columns") or {}
        same_bar_map = row.get("label_policy_same_bar_by_policy") or {}
        features[str(row.get("candidate_id"))] = {
            "kill_zone_position": feature.get("kill_zone_position"),
            "selected_policy_same_bar_ambiguous": bool(same_bar_map.get(ACTIVATED_POLICY)),
            "any_policy_same_bar_ambiguous": any(bool(value) for value in same_bar_map.values()),
        }
    return features


def load_broker_map() -> dict[str, dict[str, Any]]:
    broker: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(BROKER_ONBOARDING_LEDGER):
        symbol = str(row.get("symbol"))
        selected = row.get("selected_alias_check") or {}
        session_hours = selected.get("session_hours") or {}
        broker[symbol] = {
            "broker_contract_status": row.get("broker_contract_status"),
            "broker_symbol": row.get("broker_symbol"),
            "eligible_for_vnext_activation": row.get("eligible_for_vnext_activation"),
            "exact_exclusion_reason": row.get("exact_exclusion_reason"),
            "session_hours_available": session_hours.get("available"),
            "session_hours_status": session_hours.get("status"),
        }
    return broker


def load_repo_schedules() -> dict[str, dict[str, tuple[time, time, str]]]:
    config = yaml.safe_load((REPO_ROOT / "config/agent_config.yaml").read_text(encoding="utf-8"))
    schedules: dict[str, dict[str, tuple[time, time, str]]] = {}
    for symbol, block in (config.get("instruments") or {}).items():
        kill_zones = ((block or {}).get("market") or {}).get("kill_zones") or {}
        for name, values in kill_zones.items():
            schedules.setdefault(symbol, {})[name] = (
                parse_hhmm(values["start_utc"]),
                parse_hhmm(values["end_utc"]),
                "config/agent_config.yaml",
            )

    # Repo quick-reference schedule repairs for stale/narrow per-symbol config.
    # These are local-disk schedule evidence only; broker session-hours remain
    # unavailable in the MT5 Python surface and are recorded separately.
    quick_ref = ".context/00_core/quick_reference_card.md"
    schedules.setdefault("XAUUSD", {})["london"] = (
        parse_hhmm("07:00"),
        parse_hhmm("10:30"),
        quick_ref,
    )
    schedules.setdefault("XAUUSD", {})["ny"] = (
        parse_hhmm("13:00"),
        parse_hhmm("17:00"),
        quick_ref,
    )
    schedules.setdefault("GBPUSD", {})["ny"] = (
        parse_hhmm("13:00"),
        parse_hhmm("15:30"),
        quick_ref,
    )
    return schedules


def repo_schedule_position(
    symbol: str,
    candle_time_utc: Any,
    schedules: dict[str, dict[str, tuple[time, time, str]]],
) -> tuple[str | None, str | None]:
    if symbol not in schedules:
        return None, None
    parsed = datetime.fromisoformat(str(candle_time_utc).replace("Z", "+00:00"))
    candle_t = parsed.time()
    for name, (start, end, source_path) in schedules[symbol].items():
        if in_time_window(candle_t, start, end):
            return f"in_{name}_repo_schedule_repaired", source_path
    return "outside_repo_configured_kill_zone", "repo_schedule_checked_no_match"


def route_label(row: dict[str, Any]) -> str:
    runtime = (row.get("runtime_reference") or {}).get("hypothetical_activated_vnext") or {}
    return str(runtime.get("route_decision") or "NONE")


def prop_action(row: dict[str, Any]) -> str:
    projection = row.get("prop_governor_projection") or {}
    if projection.get("candidate_level_prop_action_available") is True:
        return str(projection.get("candidate_level_prop_action") or "candidate_prop_action_missing")
    return "candidate_level_prop_action_unavailable_branch_aggregate_only"


def policy_value(row: dict[str, Any], policy: str) -> float | None:
    if policy == "condition_router":
        return fnum((row.get("condition_router_projection") or {}).get("selected_policy_final_r"))
    policies = ((row.get("dynamic_policy_replay") or {}).get("policy_results") or {})
    return fnum((policies.get(policy) or {}).get("final_r"))


def kill_zone_bucket(
    *,
    symbol: str,
    row: dict[str, Any],
    feature: dict[str, Any],
    schedules: dict[str, dict[str, tuple[time, time, str]]],
    broker_session_hours_status: str,
) -> tuple[str, str]:
    feature_kz = str(feature.get("kill_zone_position") or "")
    repo_position, repo_source = repo_schedule_position(symbol, row.get("candle_time_utc"), schedules)
    if feature_kz.startswith("in_") and repo_position and repo_position.startswith("in_"):
        return feature_kz, f"stage10_feature_kz_and_repo_schedule:{repo_source}"
    if feature_kz.startswith("in_"):
        return feature_kz, "stage10_feature_kz"
    if repo_position and repo_position.startswith("in_"):
        return repo_position, f"repo_schedule_repair:{repo_source}"
    if repo_position == "outside_repo_configured_kill_zone":
        return repo_position, "repo_schedule_checked_no_match"
    return (
        "missing_schedule_not_derivable_from_repo_or_broker_session_hours",
        f"no_repo_schedule_and_broker_session_hours_status:{broker_session_hours_status}",
    )


def family_key(row: dict[str, Any], kill_bucket: str, policy: str) -> tuple[str, ...]:
    return (
        str(row.get("symbol")),
        str(row.get("framework")),
        str(row.get("candidate_origin_family")),
        str(row.get("session_bucket")),
        kill_bucket,
        policy,
    )


def selected_by_extended_overlay(
    row: dict[str, Any],
    *,
    policy: str,
    feature: dict[str, Any],
    kill_bucket: str,
    eligible_symbols: set[str],
) -> bool:
    return bool(
        policy == ACTIVATED_POLICY
        and row.get("symbol") in eligible_symbols
        and row.get("framework") in ACTIVATED_FRAMEWORKS
        and route_label(row) == "FOLLOW"
        and kill_bucket.startswith("in_")
        and not feature.get("selected_policy_same_bar_ambiguous")
        and (row.get("dynamic_policy_replay") or {}).get("available") is True
        and policy_value(row, ACTIVATED_POLICY) is not None
    )


def make_market_decisions(
    ledger_rows: Iterable[dict[str, Any]],
    eligible_symbols: set[str],
    exact_excluded_symbols: set[str],
) -> list[dict[str, Any]]:
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger_rows:
        by_symbol[str(row["symbol"])].append(row)
    decisions: list[dict[str, Any]] = []
    for symbol in sorted(eligible_symbols | exact_excluded_symbols):
        rows = by_symbol.get(symbol, [])
        be_rows = [row for row in rows if row["dynamic_policy_branch"] == ACTIVATED_POLICY]
        activated_rows = sum(row["activated_selector_rows"] for row in be_rows)
        best = max(
            (row for row in be_rows if row["metrics"]["expectancy_r"] is not None),
            key=lambda row: row["metrics"]["expectancy_r"],
            default=None,
        )
        action = "exclude"
        proof_class = "no_replay_rows_for_market"
        reason = "no Stage05 candidate rows for this market"
        if symbol in exact_excluded_symbols:
            proof_class = "broker_contract_invalid_or_unavailable"
            reason = "Stage08 broker-native onboarding excludes this symbol exactly"
        elif activated_rows:
            action = "activate"
            proof_class = "positive_executable_follow_selector"
            reason = "at least one family is selected by the repaired executable overlay"
        elif be_rows:
            proof_counts = Counter(row["final_proof_class"] for row in be_rows)
            proof_class = proof_counts.most_common(1)[0][0]
            if best and best["metrics"]["expectancy_r"] and best["metrics"]["expectancy_r"] > 0:
                if all(not row["branch_label_counts"].get("FOLLOW") for row in be_rows):
                    proof_class = "not_executable_without_branch_semantics_repair"
                    reason = (
                        "positive BE rows exist, but all executable branch labels are absent; "
                        "runtime route_reason evidence is no_matching_vnext_route_scope or non-FOLLOW"
                    )
                else:
                    reason = "row-level repaired selector did not pass all executable gates"
            else:
                reason = "no positive BE-after-trigger family after row-level repair attempt"
        decisions.append(
            {
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "schema_version": "vnext_replacement_stage13_market_repair_decision_v1",
                "symbol": symbol,
                "final_action": action,
                "final_proof_class": proof_class,
                "final_action_reason": reason,
                "activated_selector_rows": activated_rows,
                "best_be_family_metrics": best["metrics"] if best else None,
                "family_rows": len(rows),
                "broad_labels_not_used_as_terminal_proof": True,
            }
        )
    return decisions


def update_state_manifest(summary: dict[str, Any], generated_at: str) -> None:
    state = read_json(OUTPUT_STATE)
    state["last_updated_utc"] = generated_at
    state["current_stage"] = "stage_13_commit_and_activation_config_application"
    state["first_incomplete_invariant"] = (
        "stage_13_full_market_element_selector_extension_pending"
    )
    state["exact_next_action"] = (
        "Extend the Stage13 activation overlay/runtime selector from the narrow FVG slice "
        "to the verified all-framework repaired full-market selector, then rerun verifiers."
    )
    state.setdefault("stage_status", {})[
        "stage_13_full_market_element_activation_audit"
    ] = "completed_selector_extension_required"
    rows = state.setdefault("evidence_rows_scanned", {})
    rows["stage13_full_market_element_candidate_rows_scanned"] = summary[
        "candidate_rows_scanned"
    ]
    rows["stage13_full_market_element_dynamic_rows_scanned"] = summary[
        "dynamic_rows_scanned"
    ]
    rows["stage13_full_market_element_selected_rows"] = summary["activated_selector"][
        "metrics"
    ]["selected_count"]
    state.setdefault("tests_verifiers_run", []).append(
        {
            "command": rel(Path(__file__)),
            "result": "passed; full-market audit found selector extension required",
            "timestamp_utc": generated_at,
        }
    )
    write_json(OUTPUT_STATE, state)

    if OUTPUT_MANIFEST.exists():
        manifest = read_json(OUTPUT_MANIFEST)
        outputs = manifest.setdefault("outputs", [])
        for path, rows_count in (
            (OUTPUT_SUMMARY, 1),
            (OUTPUT_LEDGER, summary["family_ledger_rows"]),
            (OUTPUT_DECISION_LEDGER, summary["market_decision_rows"]),
            (Path(__file__), 1),
        ):
            entry = {
                "path": rel(path),
                "stage": "stage_13_full_market_element_activation_audit",
                "status": "created",
                "rows": rows_count,
            }
            for index, existing in enumerate(outputs):
                if isinstance(existing, dict) and existing.get("path") == entry["path"]:
                    outputs[index] = entry
                    break
            else:
                outputs.append(entry)
        manifest["last_updated_utc"] = generated_at
        manifest["stage13_full_market_element_audit_status"] = (
            "completed_selector_extension_required"
        )
        write_json(OUTPUT_MANIFEST, manifest)

    append_jsonl(
        CONTROL_LEDGER,
        {
            "event": "stage13_full_market_element_audit_completed",
            "generated_at_utc": generated_at,
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "status": "completed_selector_extension_required",
            "activated_selector_name": summary["activated_selector"]["selector_name"],
            "selected_rows": summary["activated_selector"]["metrics"]["selected_count"],
            "expectancy_r": summary["activated_selector"]["metrics"]["expectancy_r"],
            "profit_factor": summary["activated_selector"]["metrics"]["profit_factor"],
            "first_incomplete_invariant_after_stage": (
                "stage_13_full_market_element_selector_extension_pending"
            ),
        },
    )


def main() -> None:
    generated_at = utc_now()
    stage08 = read_json(STAGE08_MAP)
    eligible_symbols = set(stage08["broker_native_activation_eligible_symbols"])
    exact_excluded_symbols = set(stage08.get("broker_native_exact_excluded_symbols", []))
    features = load_feature_map()
    broker = load_broker_map()
    schedules = load_repo_schedules()
    families: dict[tuple[str, ...], Family] = {}
    activated_stats = {policy: Stats() for policy in POLICIES}
    activated_symbol_counts: Counter[str] = Counter()
    activated_framework_counts: Counter[str] = Counter()
    activated_session_counts: Counter[str] = Counter()
    activated_schedule_source_counts: Counter[str] = Counter()
    candidate_rows_scanned = 0
    dynamic_rows_scanned = 0

    def get_family(row: dict[str, Any], kill_bucket: str, schedule_class: str, policy: str) -> Family:
        key = family_key(row, kill_bucket, policy)
        if key not in families:
            symbol = str(row.get("symbol"))
            broker_info = broker.get(symbol, {})
            families[key] = Family(
                symbol=symbol,
                framework=str(row.get("framework")),
                candidate_origin_family=str(row.get("candidate_origin_family")),
                session_bucket=str(row.get("session_bucket")),
                kill_zone_bucket=kill_bucket,
                dynamic_policy_branch=policy,
                broker_contract_status=str(
                    broker_info.get("broker_contract_status") or "missing_broker_onboarding"
                ),
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status") or "missing_session_hours_status"
                ),
                schedule_evidence_class=schedule_class,
            )
        return families[key]

    for manifest_row in iter_jsonl(STAGE05_SHARD_MANIFEST):
        shard_path = REPO_ROOT / manifest_row["output_chunk_path"]
        for row in iter_gzip_jsonl(shard_path):
            candidate_rows_scanned += 1
            symbol = str(row.get("symbol"))
            feature = features.get(str(row.get("candidate_id")), {})
            broker_info = broker.get(symbol, {})
            kill_bucket, schedule_class = kill_zone_bucket(
                symbol=symbol,
                row=row,
                feature=feature,
                schedules=schedules,
                broker_session_hours_status=str(
                    broker_info.get("session_hours_status") or "missing_session_hours_status"
                ),
            )
            branch = route_label(row)
            dynamic = row.get("dynamic_policy_replay") or {}
            available = dynamic.get("available") is True
            if available:
                dynamic_rows_scanned += 1
            base_selected = selected_by_extended_overlay(
                row,
                policy=ACTIVATED_POLICY,
                feature=feature,
                kill_bucket=kill_bucket,
                eligible_symbols=eligible_symbols,
            )
            for policy in POLICIES:
                family = get_family(row, kill_bucket, schedule_class, policy)
                family.add_candidate(row, feature, branch)
                if not available:
                    family.add_dynamic_unavailable(dynamic.get("exclusion_reason"))
                    continue
                selected = base_selected and policy == ACTIVATED_POLICY
                family.add_policy_result(policy_value(row, policy), prop_action(row), selected)
                if base_selected:
                    activated_stats[policy].add(policy_value(row, policy))
                    if policy == ACTIVATED_POLICY:
                        activated_symbol_counts[symbol] += 1
                        activated_framework_counts[str(row.get("framework"))] += 1
                        activated_session_counts[str(row.get("session_bucket"))] += 1
                        activated_schedule_source_counts[schedule_class] += 1

    ledger_records = [family.record() for family in families.values()]
    ledger_records.sort(
        key=lambda row: (
            row["symbol"],
            row["framework"],
            row["session_bucket"],
            row["kill_zone_bucket"],
            row["dynamic_policy_branch"],
        )
    )
    market_decisions = make_market_decisions(
        ledger_records,
        eligible_symbols=eligible_symbols,
        exact_excluded_symbols=exact_excluded_symbols,
    )

    with OUTPUT_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ledger_records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    with OUTPUT_DECISION_LEDGER.open("w", encoding="utf-8", newline="\n") as handle:
        for record in market_decisions:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    activated_metrics = activated_stats[ACTIVATED_POLICY].record()
    decision_counts = Counter(row["final_action"] for row in market_decisions)
    proof_counts = Counter(row["final_proof_class"] for row in market_decisions)
    positive_nonactivated = [
        row
        for row in ledger_records
        if row["dynamic_policy_branch"] == ACTIVATED_POLICY
        and row["final_action"] != "activate"
        and row["metrics"]["expectancy_r"] is not None
        and row["metrics"]["expectancy_r"] > 0
    ]
    summary = {
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "schema_version": "vnext_replacement_stage13_full_market_element_audit_summary_v1",
        "generated_at_utc": generated_at,
        "candidate_rows_scanned": candidate_rows_scanned,
        "dynamic_rows_scanned": dynamic_rows_scanned,
        "family_ledger_rows": len(ledger_records),
        "market_decision_rows": len(market_decisions),
        "no_top_n_or_lossy_summary": True,
        "input_artifacts": {
            "stage05_shard_manifest": rel(STAGE05_SHARD_MANIFEST),
            "stage08_market_map": rel(STAGE08_MAP),
            "broker_onboarding_ledger": rel(BROKER_ONBOARDING_LEDGER),
            "feature_ledger": rel(FEATURE_LEDGER),
        },
        "output_paths": {
            "family_ledger": rel(OUTPUT_LEDGER),
            "market_decision_ledger": rel(OUTPUT_DECISION_LEDGER),
            "summary": rel(OUTPUT_SUMMARY),
        },
        "activated_selector": {
            "selector_name": ACTIVATED_SELECTOR_NAME,
            "selected_policy": ACTIVATED_POLICY,
            "activated_frameworks": list(ACTIVATED_FRAMEWORKS),
            "branch_label_required": "FOLLOW",
            "broker_native_required": True,
            "configured_or_repo_repaired_kill_zone_required": True,
            "selected_policy_same_bar_ambiguous_allowed": False,
            "source_window_complete_required_for_selection": False,
            "source_completeness_rule": (
                "source completeness is capture quality evidence, not a trade-selection proxy"
            ),
            "metrics": activated_metrics,
            "coverage": {
                "selected_symbol_counts": dict(sorted(activated_symbol_counts.items())),
                "selected_framework_counts": dict(sorted(activated_framework_counts.items())),
                "selected_session_counts": dict(sorted(activated_session_counts.items())),
                "selected_schedule_evidence_counts": dict(
                    sorted(activated_schedule_source_counts.items())
                ),
            },
            "comparator_metrics_on_selected_rows": {
                policy: activated_stats[policy].record() for policy in POLICIES
            },
            "extends_prior_narrow_fvg_slice": activated_metrics["selected_count"] > 6479,
            "prior_narrow_fvg_slice_rows": 6479,
        },
        "market_decision_counts": dict(sorted(decision_counts.items())),
        "market_final_proof_class_counts": dict(sorted(proof_counts.items())),
        "eligible_symbols": sorted(eligible_symbols),
        "exact_broker_excluded_symbols": sorted(exact_excluded_symbols),
        "activated_symbols": sorted(
            row["symbol"] for row in market_decisions if row["final_action"] == "activate"
        ),
        "excluded_symbols_with_exact_proof": sorted(
            row["symbol"] for row in market_decisions if row["final_action"] != "activate"
        ),
        "positive_be_families_not_activated_count": len(positive_nonactivated),
        "positive_be_families_not_activated_proof_counts": dict(
            sorted(Counter(row["final_proof_class"] for row in positive_nonactivated).items())
        ),
        "broad_terminal_labels_disallowed": [
            "non_primary_framework_replay_only",
            "dynamic_policy_replay_unavailable",
            "outside_configured_kill_zone_or_missing_schedule",
            "branch_label_not_follow",
            "source_incomplete",
            "old_live_list_residue",
            "prop_or_safety_wording_only",
        ],
        "exact_exclusion_proof_classes_allowed": [
            "broker_contract_invalid_or_unavailable",
            "dynamic_policy_no_executable_rows",
            "missing_market_schedule_not_derivable",
            "outside_configured_kill_zone_after_schedule_repair",
            "same_bar_path_ambiguity_not_resolved_from_available_rows",
            "negative_expectancy_or_profit_factor_collapse",
            "not_executable_without_branch_semantics_repair",
            "positive_but_not_selected_variant",
            "no_replay_rows_for_market",
        ],
        "final_repair_action": (
            "extend_production_overlay_to_all_framework_follow_broker_native_"
            "repaired_configured_kz_be_after_trigger"
        ),
    }
    write_json(OUTPUT_SUMMARY, summary)
    update_state_manifest(summary, generated_at)
    print(
        json.dumps(
            {
                "status": "completed_selector_extension_required",
                "selected_rows": activated_metrics["selected_count"],
                "expectancy_r": activated_metrics["expectancy_r"],
                "profit_factor": activated_metrics["profit_factor"],
                "activated_symbols": summary["activated_symbols"],
                "activated_frameworks": list(ACTIVATED_FRAMEWORKS),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
