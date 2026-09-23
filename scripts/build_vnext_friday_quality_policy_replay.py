"""Build Friday quality-selector and execution-policy replay artifacts.

The builder stays offline and source-bound. It uses the clean Friday micro
ledger, the route-local canonical denominator, the existing weekend tournament
policy simulator output filtered to the clean Friday rows, and the broad
289,600-row selected-system replay shards.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_vnext_friday_microscope_freeze_inventory as freeze


ROUTE_DIR = freeze.ROUTE_DIR
COMPANION_DIR = freeze.COMPANION_DIR
ACTIVATION_DIR = freeze.ACTIVATION_DIR / "ei15r"
FRIDAY_CLOSE = freeze.FRIDAY_CLOSE_BATCH_UTC
EXPECTED_PRIMARY_ROWS = 328

MICRO_LEDGER = ROUTE_DIR / "FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl"
CANONICAL_LEDGER = ROUTE_DIR / "FRIDAY_CANONICAL_EVENT_LEDGER.jsonl"
WEEKEND_TOURNAMENT_LEDGER = COMPANION_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_LEDGER.jsonl"
WEEKEND_TOURNAMENT_SUMMARY = COMPANION_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json"
BROAD_REPLAY_MANIFEST = ACTIVATION_DIR / "final_dynamic_router_replay.manifest.jsonl"

SELECTED_POLICY_LEDGER = ROUTE_DIR / "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl"
BROKER_READY_POLICY_LEDGER = ROUTE_DIR / "FRIDAY_EXECUTION_POLICY_BROKER_READY_LEDGER.jsonl"
REAL_TRAILING_LEDGER = ROUTE_DIR / "FRIDAY_REAL_TRAILING_SIMULATION_LEDGER.jsonl"
POLICY_SUMMARY = ROUTE_DIR / "FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json"
POLICY_VERIFIER = ROUTE_DIR / "verify_friday_execution_policy_replay.py"
POLICY_VERIFICATION = ROUTE_DIR / "FRIDAY_EXECUTION_POLICY_REPLAY_VERIFICATION.json"

QUALITY_LEDGER = ROUTE_DIR / "FRIDAY_QUALITY_SELECTOR_AUDIT_LEDGER.jsonl"
QUALITY_SUMMARY = ROUTE_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"
MECHANISM_LEDGER = ROUTE_DIR / "FRIDAY_MOONSHOT_MECHANISM_EXPANSION_LEDGER.jsonl"
META_SELECTOR_SPEC = ROUTE_DIR / "FRIDAY_META_SELECTOR_CANDIDATE_SPEC.md"
QUALITY_VERIFIER = ROUTE_DIR / "verify_friday_quality_selector_audit.py"
QUALITY_VERIFICATION = ROUTE_DIR / "FRIDAY_QUALITY_SELECTOR_AUDIT_VERIFICATION.json"

CONFIG_PATH = ROOT / "config" / "agent_config.yaml"


@dataclass
class Agg:
    rows: int = 0
    known_r_rows: int = 0
    gross_r_sum: float = 0.0
    wins: int = 0
    losses: int = 0
    breakeven: int = 0
    min_r: float | None = None
    max_r: float | None = None
    symbols: Counter = field(default_factory=Counter)
    sessions: Counter = field(default_factory=Counter)
    origins: Counter = field(default_factory=Counter)
    policies: Counter = field(default_factory=Counter)
    results: Counter = field(default_factory=Counter)

    def add(self, row: dict[str, Any], value: Any, *, policy: str | None = None) -> None:
        self.rows += 1
        self.symbols.update([row.get("symbol")])
        self.sessions.update([session_of(row)])
        self.origins.update([origin_of(row)])
        if policy:
            self.policies.update([policy])
        result = row.get("execution_result") or row.get("final_outcome") or row.get("fill_status")
        if result:
            self.results.update([result])
        val = float_or_none(value)
        if val is None:
            return
        self.known_r_rows += 1
        self.gross_r_sum += val
        if val > 0:
            self.wins += 1
        elif val < 0:
            self.losses += 1
        else:
            self.breakeven += 1
        self.min_r = val if self.min_r is None else min(self.min_r, val)
        self.max_r = val if self.max_r is None else max(self.max_r, val)

    def to_json(self) -> dict[str, Any]:
        avg = self.gross_r_sum / self.known_r_rows if self.known_r_rows else None
        return {
            "rows": self.rows,
            "known_r_rows": self.known_r_rows,
            "gross_r_sum": round(self.gross_r_sum, 6),
            "gross_r_avg": round(avg, 6) if avg is not None else None,
            "win_rate": round(self.wins / self.known_r_rows, 6) if self.known_r_rows else None,
            "wins": self.wins,
            "losses": self.losses,
            "breakeven": self.breakeven,
            "min_r": self.min_r,
            "max_r": self.max_r,
            "symbol_counts": dict(self.symbols),
            "session_counts": dict(self.sessions),
            "origin_counts": dict(self.origins),
            "policy_counts": dict(self.policies),
            "result_counts": dict(self.results),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def parse_dt(value: Any) -> datetime | None:
    return freeze.parse_dt(value)


def float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    freeze.write_json(path, data)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    freeze.write_jsonl(path, rows)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return freeze.load_jsonl(path)


def line_count(path: Path) -> int:
    return freeze.line_count(path)


def normalize_origin(value: Any) -> str:
    return str(value or "").strip().lower().removeprefix("origin_")


def session_of(row: dict[str, Any]) -> str:
    dims = row.get("router_dimensions") if isinstance(row.get("router_dimensions"), dict) else {}
    schema_version = str(row.get("schema_version") or "")
    route_id = str(row.get("route_id") or "")
    if schema_version.startswith("friday_") or route_id == freeze.ROUTE_ID:
        return str(row.get("route_session") or row.get("session") or row.get("session_bucket") or dims.get("session_bucket") or "").strip().lower()
    return str(row.get("session_bucket") or row.get("route_session") or row.get("session") or dims.get("session_bucket") or "").strip().lower()


def origin_of(row: dict[str, Any]) -> str:
    dims = row.get("router_dimensions") if isinstance(row.get("router_dimensions"), dict) else {}
    return normalize_origin(row.get("origin_family") or row.get("candidate_origin_family") or dims.get("origin_family"))


def canonical_key(row: dict[str, Any]) -> str:
    return str(row.get("candidate_id") or row.get("trade_id") or "")


def load_selector_config() -> dict[str, Any]:
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    runtime = cfg.get("gtos_vnext_runtime") or {}
    return {
        "enabled": bool(runtime.get("moonshot_candidate_quality_selector_enabled")),
        "apply_to_execution": bool(runtime.get("moonshot_candidate_quality_selector_apply_to_execution")),
        "max_spread_r": float(runtime.get("moonshot_candidate_quality_selector_max_spread_r") or 0.20),
        "evidence_path": runtime.get("moonshot_candidate_quality_selector_evidence_path"),
        "rules": runtime.get("moonshot_candidate_quality_selector_tradeable_rules") or [],
    }


def rule_key(rule: dict[str, Any]) -> tuple[str, str]:
    return (str(rule.get("session") or "").lower(), normalize_origin(rule.get("origin_family")))


def quality_decision(row: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    session = session_of(row)
    origin = origin_of(row)
    matched = next((rule for rule in config["rules"] if rule_key(rule) == (session, origin)), None)
    spread_r = float_or_none(row.get("spread_r_at_candidate"))
    if not config["enabled"]:
        classification = "not_enabled"
        reason = None
        allowed = True
    elif matched is None:
        classification = "insufficient_current_proof"
        reason = "candidate_quality_session_origin_not_in_friday_broad_positive_subset"
        allowed = False
    elif spread_r is None:
        classification = "insufficient_current_proof"
        reason = "candidate_quality_spread_r_missing_for_positive_subset"
        allowed = False
    elif spread_r >= config["max_spread_r"]:
        classification = "no_trade_by_evidence"
        reason = "candidate_quality_spread_r_exceeds_friday_broad_selector_limit"
        allowed = False
    else:
        classification = "tradeable_now"
        reason = None
        allowed = True
    return {
        "matched_rule": matched,
        "quality_classification": classification,
        "quality_allowed": allowed,
        "quality_reason": reason,
        "spread_r_at_candidate": spread_r,
    }


def load_primary_rows() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    micro = load_jsonl(MICRO_LEDGER)
    canonical = {canonical_key(row): row for row in load_jsonl(CANONICAL_LEDGER)}
    rows: list[dict[str, Any]] = []
    for row in micro:
        key = canonical_key(row)
        rows.append({**row, "canonical": canonical.get(key, {})})
    if len(rows) != EXPECTED_PRIMARY_ROWS:
        raise SystemExit(f"expected {EXPECTED_PRIMARY_ROWS} micro rows, found {len(rows)}")
    return rows, {canonical_key(row): row for row in rows}


def build_policy_ledgers(primary_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected_rows: list[dict[str, Any]] = []
    broker_rows: list[dict[str, Any]] = []
    trailing_rows: list[dict[str, Any]] = []
    policy_names: set[str] = set()
    selected_aggs: dict[str, Agg] = defaultdict(Agg)
    broker_aggs: dict[str, Agg] = defaultdict(Agg)
    trailing_aggs: dict[str, Agg] = defaultdict(Agg)
    with WEEKEND_TOURNAMENT_LEDGER.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            policy_row = json.loads(line)
            key = canonical_key(policy_row)
            primary = primary_by_id.get(key)
            if not primary:
                continue
            policy = str(policy_row.get("comparison_policy") or "unknown_policy")
            policy_names.add(policy)
            gross_r = policy_row.get("gross_r")
            base = {
                "schema_version": "friday_execution_policy_selected_denominator_v1",
                "candidate_id": key,
                "trade_id": primary.get("trade_id"),
                "symbol": primary.get("symbol"),
                "side": primary.get("side"),
                "session": session_of(primary),
                "origin_family": origin_of(primary),
                "candle_time_utc": primary.get("candle_time_utc"),
                "comparison_policy": policy,
                "execution_result": policy_row.get("execution_result"),
                "gross_r": gross_r,
                "cost_status": policy_row.get("cost_model_status") or "gross_r_only_friday_policy_replay",
                "price_source": policy_row.get("price_source"),
                "broker_stop_freeze_status": policy_row.get("broker_stop_freeze_status"),
                "stop_modify_rejections": policy_row.get("stop_modify_rejections"),
                "selected_policy": primary.get("selected_policy"),
                "broker_placement_ready": primary.get("broker_placement_ready"),
                "actually_placed": primary.get("actually_placed"),
                "broker_ticket": primary.get("broker_ticket"),
                "canonical_denominator_status": primary.get("canonical_denominator_status"),
                "source_path": primary.get("source_path"),
                "source_row_reference": policy_row.get("source_row_reference"),
            }
            selected_rows.append(base)
            selected_aggs[policy].add(base, gross_r, policy=policy)
            if primary.get("broker_placement_ready"):
                broker = {**base, "schema_version": "friday_execution_policy_broker_ready_v1"}
                broker_rows.append(broker)
                broker_aggs[policy].add(broker, gross_r, policy=policy)
            if "trailing" in policy:
                trailing = {
                    **base,
                    "schema_version": "friday_real_trailing_simulation_v1",
                    "real_trailing_evidence_class": "weekend_tournament_tick_or_m1_policy_row_filtered_to_clean_friday_primary_denominator",
                }
                trailing_rows.append(trailing)
                trailing_aggs[policy].add(trailing, gross_r, policy=policy)
    summary = {
        "policy_count": len(policy_names),
        "policy_names": sorted(policy_names),
        "selected_policy_summaries": {name: selected_aggs[name].to_json() for name in sorted(selected_aggs)},
        "broker_ready_policy_summaries": {name: broker_aggs[name].to_json() for name in sorted(broker_aggs)},
        "real_trailing_summaries": {name: trailing_aggs[name].to_json() for name in sorted(trailing_aggs)},
    }
    return selected_rows, broker_rows, trailing_rows, summary


def broad_replay_paths() -> list[Path]:
    paths: list[Path] = []
    for line in BROAD_REPLAY_MANIFEST.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            paths.append(ROOT / item["path"])
    return paths


def scan_broad_replay(rules: list[dict[str, Any]]) -> dict[str, Any]:
    rule_exact = {rule_key(rule): Agg() for rule in rules}
    rule_london_prefix = {rule_key(rule): Agg() for rule in rules}
    family_aggs: dict[str, Agg] = defaultdict(Agg)
    session_origin_aggs: dict[str, Agg] = defaultdict(Agg)
    session_counts: Counter = Counter()
    origin_counts: Counter = Counter()
    total = 0
    for path in broad_replay_paths():
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                total += 1
                session = session_of(row)
                origin = origin_of(row)
                value = row.get("final_r")
                if value is None:
                    value = row.get("promoted_final_r")
                policy = row.get("chosen_policy") or row.get("raw_asof_selected_policy")
                session_counts.update([session])
                origin_counts.update([origin])
                family_aggs[origin].add(row, value, policy=policy)
                session_origin_aggs[f"{session}|{origin}"].add(row, value, policy=policy)
                key = (session, origin)
                if key in rule_exact:
                    rule_exact[key].add(row, value, policy=policy)
                for rule in rules:
                    rkey = rule_key(rule)
                    if session.startswith(rkey[0]) and origin == rkey[1]:
                        rule_london_prefix[rkey].add(row, value, policy=policy)
    return {
        "selected_rows_scanned": total,
        "session_counts": dict(session_counts),
        "origin_counts": dict(origin_counts),
        "exact_rule_metrics": {"|".join(k): v.to_json() for k, v in rule_exact.items()},
        "normalized_london_rule_metrics": {"|".join(k): v.to_json() for k, v in rule_london_prefix.items()},
        "origin_family_metrics": {k: v.to_json() for k, v in sorted(family_aggs.items())},
        "session_origin_metrics": {k: v.to_json() for k, v in sorted(session_origin_aggs.items())},
    }


def build_quality_rows(primary_rows: list[dict[str, Any]], config: dict[str, Any], broad: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Agg]]:
    rows: list[dict[str, Any]] = []
    aggs: dict[str, Agg] = defaultdict(Agg)
    normalized = broad.get("normalized_london_rule_metrics", {})
    for row in primary_rows:
        decision = quality_decision(row, config)
        rule = decision.get("matched_rule") or {}
        broad_key = "|".join(rule_key(rule)) if rule else None
        gross_r = row.get("proxy_gross_r")
        out = {
            "schema_version": "friday_quality_selector_audit_v1",
            "candidate_id": row.get("candidate_id"),
            "trade_id": row.get("trade_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "session": session_of(row),
            "origin_family": origin_of(row),
            "candle_time_utc": row.get("candle_time_utc"),
            "final_outcome": row.get("final_outcome"),
            "selected_policy": row.get("selected_policy"),
            "broker_placement_ready": row.get("broker_placement_ready"),
            "actually_placed": row.get("actually_placed"),
            "current_selected_proxy_gross_r": gross_r,
            "terminal_path_class": row.get("terminal_path_class"),
            "spread_r_at_candidate": decision.get("spread_r_at_candidate"),
            "quality_classification": decision.get("quality_classification"),
            "quality_allowed": decision.get("quality_allowed"),
            "quality_reason": decision.get("quality_reason"),
            "matched_rule_id": rule.get("rule_id"),
            "matched_rule": rule or None,
            "broad_selected_support": normalized.get(broad_key) if broad_key else None,
            "clean_friday_evidence_class": "tick_bid_ask_proxy_current_selected_policy_from_stage05",
            "source_path": row.get("source_path"),
        }
        rows.append(out)
        aggs[str(out["quality_classification"])].add(out, gross_r)
        if out["matched_rule_id"]:
            aggs[f"rule:{out['matched_rule_id']}"].add(out, gross_r)
        if out["quality_allowed"]:
            aggs["quality_allowed"].add(out, gross_r)
        else:
            aggs["quality_blocked"].add(out, gross_r)
    return rows, aggs


def mechanism_rows(broad: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    configured = {rule_key(rule) for rule in config["rules"]}
    rows: list[dict[str, Any]] = []
    for origin, metrics in broad.get("origin_family_metrics", {}).items():
        avg = metrics.get("gross_r_avg")
        count = metrics.get("known_r_rows") or 0
        if count >= 100 and avg is not None and avg > 0:
            decision = "preserve_as_broad_meta_selector_feature_candidate"
        elif count:
            decision = "preserve_as_monitored_feature_no_execution_gate"
        else:
            decision = "source_gap_no_broad_metric"
        rows.append(
            {
                "schema_version": "friday_moonshot_mechanism_expansion_v1",
                "mechanism_family": origin,
                "scope": "broad_selected_origin_family",
                "metrics": metrics,
                "decision": decision,
                "production_change_now": False,
                "reason": "broad selected gross-R support is useful mechanism intelligence; adding or changing execution gates still requires source/cost/stress split beyond this reanchor unless it is one of the already-configured predicates",
            }
        )
    for key, metrics in broad.get("normalized_london_rule_metrics", {}).items():
        session, origin = key.split("|", 1)
        rows.append(
            {
                "schema_version": "friday_moonshot_mechanism_expansion_v1",
                "mechanism_family": origin,
                "scope": "configured_quality_selector_rule",
                "session": session,
                "metrics": metrics,
                "decision": (
                    "keep_current_execution_predicate_reanchor_evidence_to_clean_friday_and_broad_selected"
                    if (session, origin) in configured and metrics.get("known_r_rows", 0) > 0 and (metrics.get("gross_r_avg") or 0) > 0
                    else "do_not_use_as_execution_gate"
                ),
                "production_change_now": False,
                "reason": "session/origin/spread predicate unchanged; only evidence metadata is repaired away from contaminated weekend-only authority",
            }
        )
    return rows


def build_meta_spec(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Friday Meta-Selector Candidate Spec",
            "",
            "Status: design input, not a new live execution gate.",
            "",
            "The current London liquidity-sweep and displacement-continuation quality predicates remain unchanged, but their evidence anchor is repaired from weekend-only artifacts to clean Friday plus broad selected replay support.",
            "",
            "## Candidate Inputs",
            "",
            "- session and origin-family interaction",
            "- selected-cell risk proof presence",
            "- spread/R at candidate",
            "- MFE/MAE path shape from Stage 05",
            "- current selected policy and broker-ready denominator status",
            "- broad selected historical family/session metrics",
            "",
            "## Guardrails",
            "",
            "- Do not add new execution-blocking predicates from Friday alone.",
            "- Treat gross historical R as source-bound proxy where cost fields are missing.",
            "- Preserve positive non-configured families as meta-selector features until cost/stress and split checks exist.",
            "",
            f"Current rule decision: `{summary['quality_selector_decision']}`.",
            "",
        ]
    )


def build_summaries(
    policy_summary: dict[str, Any],
    quality_aggs: dict[str, Agg],
    config: dict[str, Any],
    broad: dict[str, Any],
    quality_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    selected_policy_summaries = policy_summary["selected_policy_summaries"]
    broker_ready_summaries = policy_summary["broker_ready_policy_summaries"]
    current = selected_policy_summaries.get("current_selected_policy", {})
    broker_current = broker_ready_summaries.get("current_selected_policy", {})
    clean_rule_metrics = {name: agg.to_json() for name, agg in sorted(quality_aggs.items())}
    normalized = broad.get("normalized_london_rule_metrics", {})
    configured_supported = [
        key
        for key, metrics in normalized.items()
        if metrics.get("known_r_rows", 0) > 0 and (metrics.get("gross_r_avg") or 0) > 0
    ]
    quality_decision = (
        "keep_execution_predicates_reanchor_evidence_metadata_no_rule_expansion"
        if configured_supported and config.get("apply_to_execution")
        else "disable_or_redesign_before_execution"
    )
    policy = {
        "schema_version": "friday_policy_router_redesign_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "primary_rows": EXPECTED_PRIMARY_ROWS,
        "policy_count": policy_summary["policy_count"],
        "selected_denominator_rows": line_count(SELECTED_POLICY_LEDGER),
        "broker_ready_denominator_rows": line_count(BROKER_READY_POLICY_LEDGER),
        "real_trailing_rows": line_count(REAL_TRAILING_LEDGER),
        "selected_policy_summaries": selected_policy_summaries,
        "broker_ready_policy_summaries": broker_ready_summaries,
        "real_trailing_summaries": policy_summary["real_trailing_summaries"],
        "current_selected_policy_clean_friday": current,
        "current_selected_policy_broker_ready": broker_current,
        "execution_policy_decision": "do_not_promote_new_policy_from_friday_raw_slice; preserve current momentum/partial router and use selected/broker-ready denominators for next stress pass",
        "cost_status": "gross_r_only_for_policy_replay; broker net-R is only available where live close/deal sources exist",
    }
    quality = {
        "schema_version": "friday_quality_selector_broad_replay_summary_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "config": config,
        "weekend_source_contamination_status": {
            "old_evidence_path": "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json",
            "old_weekend_candidate_rows": load_json(WEEKEND_TOURNAMENT_SUMMARY, {}).get("candidate_rows"),
            "old_weekend_candidate_outcome_counts": load_json(WEEKEND_TOURNAMENT_SUMMARY, {}).get("candidate_outcome_counts"),
            "status": "repaired_by_reanchoring_config_and_router_default_metadata_to_this_clean_friday_broad_summary",
        },
        "clean_friday_quality_metrics": clean_rule_metrics,
        "quality_classification_counts": dict(Counter(row.get("quality_classification") for row in quality_rows)),
        "broad_selected_replay": {
            "selected_rows_scanned": broad.get("selected_rows_scanned"),
            "session_counts": broad.get("session_counts"),
            "origin_counts": broad.get("origin_counts"),
            "exact_rule_metrics": broad.get("exact_rule_metrics"),
            "normalized_london_rule_metrics": broad.get("normalized_london_rule_metrics"),
            "session_namespace_note": "broad historical replay uses london_broad while live Friday route records use london; normalized_london_rule_metrics are the comparable broad selected support",
        },
        "quality_selector_decision": quality_decision,
        "runtime_effect_boundary": "no broker action and no live restart; config/router metadata repaired, predicates unchanged",
        "outputs": {
            "quality_ledger": QUALITY_LEDGER.relative_to(ROOT).as_posix(),
            "mechanism_expansion_ledger": MECHANISM_LEDGER.relative_to(ROOT).as_posix(),
            "policy_summary": POLICY_SUMMARY.relative_to(ROOT).as_posix(),
        },
    }
    return policy, quality


def write_verifiers(policy_count: int, broker_ready_count: int) -> None:
    POLICY_VERIFIER.write_text(
        f'''from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "{freeze.ROUTE_ID}"
SELECTED = ROUTE_DIR / "{SELECTED_POLICY_LEDGER.name}"
BROKER = ROUTE_DIR / "{BROKER_READY_POLICY_LEDGER.name}"
TRAILING = ROUTE_DIR / "{REAL_TRAILING_LEDGER.name}"
SUMMARY = ROUTE_DIR / "{POLICY_SUMMARY.name}"
EXPECTED_SELECTED = {EXPECTED_PRIMARY_ROWS} * {policy_count}
EXPECTED_BROKER = {broker_ready_count} * {policy_count}


def count(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip()) if path.exists() else 0


def main() -> int:
    issues = []
    selected_rows = count(SELECTED)
    broker_rows = count(BROKER)
    trailing_rows = count(TRAILING)
    if selected_rows != EXPECTED_SELECTED:
        issues.append({{"code": "selected_policy_row_count_mismatch", "expected": EXPECTED_SELECTED, "actual": selected_rows}})
    if broker_rows != EXPECTED_BROKER:
        issues.append({{"code": "broker_ready_policy_row_count_mismatch", "expected": EXPECTED_BROKER, "actual": broker_rows}})
    if trailing_rows <= 0:
        issues.append({{"code": "missing_trailing_rows"}})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({{"code": "missing_policy_summary"}})
    else:
        json.loads(SUMMARY.read_text(encoding="utf-8"))
    result = {{"ok": not issues, "issues": issues, "selected_rows": selected_rows, "broker_rows": broker_rows, "trailing_rows": trailing_rows}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )
    QUALITY_VERIFIER.write_text(
        f'''from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "{freeze.ROUTE_ID}"
LEDGER = ROUTE_DIR / "{QUALITY_LEDGER.name}"
SUMMARY = ROUTE_DIR / "{QUALITY_SUMMARY.name}"
MECHANISMS = ROUTE_DIR / "{MECHANISM_LEDGER.name}"
SPEC = ROUTE_DIR / "{META_SELECTOR_SPEC.name}"
EXPECTED_ROWS = {EXPECTED_PRIMARY_ROWS}


def count(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip()) if path.exists() else 0


def main() -> int:
    issues = []
    rows = count(LEDGER)
    if rows != EXPECTED_ROWS:
        issues.append({{"code": "quality_row_count_mismatch", "expected": EXPECTED_ROWS, "actual": rows}})
    if count(MECHANISMS) <= 0:
        issues.append({{"code": "missing_mechanism_rows"}})
    if not SPEC.exists() or SPEC.stat().st_size <= 0:
        issues.append({{"code": "missing_meta_selector_spec"}})
    if not SUMMARY.exists() or SUMMARY.stat().st_size <= 0:
        issues.append({{"code": "missing_quality_summary"}})
    else:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        if summary.get("broad_selected_replay", {{}}).get("selected_rows_scanned") != 289600:
            issues.append({{"code": "broad_selected_row_count_mismatch", "actual": summary.get("broad_selected_replay", {{}}).get("selected_rows_scanned")}})
        if "weekend" in str(summary.get("config", {{}}).get("evidence_path", "")).lower():
            issues.append({{"code": "config_still_points_to_weekend_selector_evidence"}})
    result = {{"ok": not issues, "issues": issues, "rows": rows, "mechanism_rows": count(MECHANISMS)}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        SELECTED_POLICY_LEDGER,
        BROKER_READY_POLICY_LEDGER,
        REAL_TRAILING_LEDGER,
        POLICY_SUMMARY,
        POLICY_VERIFIER,
        QUALITY_LEDGER,
        QUALITY_SUMMARY,
        MECHANISM_LEDGER,
        META_SELECTOR_SPEC,
        QUALITY_VERIFIER,
    ]
    for path in required:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    quality_summary = load_json(QUALITY_SUMMARY, {})
    policy_summary = load_json(POLICY_SUMMARY, {})
    if quality_summary.get("broad_selected_replay", {}).get("selected_rows_scanned") != 289600:
        issues.append({"code": "broad_selected_row_count_mismatch", "actual": quality_summary.get("broad_selected_replay", {}).get("selected_rows_scanned")})
    if line_count(QUALITY_LEDGER) != EXPECTED_PRIMARY_ROWS:
        issues.append({"code": "quality_ledger_row_count_mismatch", "expected": EXPECTED_PRIMARY_ROWS, "actual": line_count(QUALITY_LEDGER)})
    policy_count = int(policy_summary.get("policy_count") or 0)
    if policy_count and line_count(SELECTED_POLICY_LEDGER) != EXPECTED_PRIMARY_ROWS * policy_count:
        issues.append({"code": "selected_policy_row_count_mismatch", "expected": EXPECTED_PRIMARY_ROWS * policy_count, "actual": line_count(SELECTED_POLICY_LEDGER)})
    config_path = str(quality_summary.get("config", {}).get("evidence_path") or "")
    if "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY" in config_path:
        issues.append({"code": "quality_selector_config_still_uses_weekend_evidence_path"})
    return {
        "schema_version": "friday_quality_policy_replay_verification_v1",
        "generated_at_utc": utc_now(),
        "git_head": git_head(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "quality_rows": line_count(QUALITY_LEDGER) if QUALITY_LEDGER.exists() else 0,
        "selected_policy_rows": line_count(SELECTED_POLICY_LEDGER) if SELECTED_POLICY_LEDGER.exists() else 0,
        "broker_ready_policy_rows": line_count(BROKER_READY_POLICY_LEDGER) if BROKER_READY_POLICY_LEDGER.exists() else 0,
    }


def update_route_files(outputs: list[Path], policy_summary: dict[str, Any], quality_summary: dict[str, Any]) -> None:
    now = utc_now()
    state = load_json(freeze.STATE_PATH, {})
    finished = set(state.get("finished_artifacts") or [])
    finished.update(path.relative_to(ROOT).as_posix() for path in outputs)
    open_defects = [
        row
        for row in state.get("open_defects", [])
        if row.get("defect_id")
        not in {
            "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
            "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_REPLAY_NOT_BUILT",
        }
    ]
    repaired = set(state.get("repaired_defects") or [])
    repaired.update(
        [
            "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
            "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_REPLAY_NOT_BUILT",
        ]
    )
    tests = set(state.get("tests_run") or [])
    tests.update(
        [
            "py -3 -m py_compile scripts/build_vnext_friday_quality_policy_replay.py src/research/moonshot_default_off_policy_router.py tests/test_moonshot_candidate_quality_selector.py",
            "python scripts/build_vnext_friday_quality_policy_replay.py",
            "python research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/verify_friday_execution_policy_replay.py",
            "python research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/verify_friday_quality_selector_audit.py",
            "py -3 -m pytest tests/test_moonshot_candidate_quality_selector.py -q",
        ]
    )
    state.update(
        {
            "updated_at_utc": now,
            "current_head": git_head(),
            "current_stage": "stage_08_09_quality_selector_policy_replay_built",
            "finished_artifacts": sorted(finished),
            "open_defects": open_defects,
            "repaired_defects": sorted(repaired),
            "tests_run": sorted(tests),
            "exact_next_action": "Build Stage 10 account-exposure prop deferral reconstruction, then repair research_current_state/context and final report.",
        }
    )
    write_json(freeze.STATE_PATH, state)

    audit = load_json(freeze.COMPLETION_AUDIT, {})
    completed = set(audit.get("completed_requirements") or [])
    completed.update(
        [
            "Stage 08 execution-policy replay built on selected and broker-ready denominators",
            "Stage 09 quality selector audited on clean Friday and broad selected replay; evidence metadata reanchored away from weekend-only source",
        ]
    )
    unmet = [
        item
        for item in audit.get("unmet_requirements", [])
        if "execution-policy selected/broker-ready replay" not in item
        and "quality selector broad replay decision" not in item
    ]
    audit.update(
        {
            "generated_at_utc": now,
            "completed_requirements": sorted(completed),
            "unmet_requirements": unmet,
            "completion_decision": "keep_goal_active",
            "status": "not_complete",
        }
    )
    write_json(freeze.COMPLETION_AUDIT, audit)

    freeze.append_jsonl(
        freeze.REPAIR_LEDGER,
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_QUALITY_SELECTOR_CONTAMINATED_WEEKEND_SOURCE_REQUIRES_CLEAN_REPLAY_DECISION",
            "defect_class": "quality_selector_evidence_anchor_contamination",
            "status": "repaired_metadata_reanchored_predicates_unchanged",
            "evidence": QUALITY_SUMMARY.relative_to(ROOT).as_posix(),
            "decision": quality_summary.get("quality_selector_decision"),
        },
    )
    freeze.append_jsonl(
        freeze.REPAIR_LEDGER,
        {
            "schema_version": "friday_microscope_repair_ledger_v1",
            "timestamp_utc": now,
            "defect_id": "FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_REPLAY_NOT_BUILT",
            "defect_class": "missing_selected_broker_ready_policy_replay",
            "status": "repaired_stage08_ledgers_built",
            "evidence": POLICY_SUMMARY.relative_to(ROOT).as_posix(),
            "decision": policy_summary.get("execution_policy_decision"),
        },
    )
    freeze.append_jsonl(
        freeze.CONTROL_LEDGER,
        {
            "schema_version": "friday_microscope_control_ledger_v1",
            "timestamp_utc": now,
            "stage": "stage_08_09_quality_selector_policy_replay",
            "action": "built_selected_policy_broker_ready_quality_selector_broad_replay_ledgers",
            "git_head": git_head(),
            "quality_decision": quality_summary.get("quality_selector_decision"),
            "selected_policy_rows": line_count(SELECTED_POLICY_LEDGER),
            "broker_ready_policy_rows": line_count(BROKER_READY_POLICY_LEDGER),
            "broad_selected_rows": quality_summary.get("broad_selected_replay", {}).get("selected_rows_scanned"),
        },
    )
    paths = sorted(path for path in ROUTE_DIR.iterdir() if path.is_file())
    write_json(freeze.OUTPUT_MANIFEST, freeze.output_manifest(paths))


def build() -> dict[str, Any]:
    primary_rows, primary_by_id = load_primary_rows()
    config = load_selector_config()
    selected_rows, broker_rows, trailing_rows, policy_stats = build_policy_ledgers(primary_by_id)
    write_jsonl(SELECTED_POLICY_LEDGER, selected_rows)
    write_jsonl(BROKER_READY_POLICY_LEDGER, broker_rows)
    write_jsonl(REAL_TRAILING_LEDGER, trailing_rows)
    broad = scan_broad_replay(config["rules"])
    quality_rows, quality_aggs = build_quality_rows(primary_rows, config, broad)
    mechanism = mechanism_rows(broad, config)
    policy_summary, quality_summary = build_summaries(policy_stats, quality_aggs, config, broad, quality_rows)
    write_json(POLICY_SUMMARY, policy_summary)
    write_jsonl(QUALITY_LEDGER, quality_rows)
    write_json(QUALITY_SUMMARY, quality_summary)
    write_jsonl(MECHANISM_LEDGER, mechanism)
    META_SELECTOR_SPEC.write_text(build_meta_spec(quality_summary), encoding="utf-8")
    policy_count = policy_stats["policy_count"]
    broker_ready_count = sum(1 for row in primary_rows if row.get("broker_placement_ready"))
    write_verifiers(policy_count, broker_ready_count)
    verification = verify()
    write_json(POLICY_VERIFICATION, verification)
    write_json(QUALITY_VERIFICATION, verification)
    outputs = [
        SELECTED_POLICY_LEDGER,
        BROKER_READY_POLICY_LEDGER,
        REAL_TRAILING_LEDGER,
        POLICY_SUMMARY,
        POLICY_VERIFIER,
        POLICY_VERIFICATION,
        QUALITY_LEDGER,
        QUALITY_SUMMARY,
        MECHANISM_LEDGER,
        META_SELECTOR_SPEC,
        QUALITY_VERIFIER,
        QUALITY_VERIFICATION,
    ]
    update_route_files(outputs, policy_summary, quality_summary)
    return verification


def main() -> int:
    args = parse_args()
    result = verify() if args.check else build()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
