"""Stage 06 ablation, robustness, prop metrics, forensics, and final map.

This route-local builder consumes Stage04/Stage05 replay shards from disk and
writes terminal replay metrics. It does not change production config, prompts,
broker/account state, orders, deals, positions, history, or source data.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
STAGE_ID = "STAGE_06_ABLATION_AND_MIXED_RESOLUTION"
STAGE_SCOPE = (
    "ablation, MIXED final classification, robustness, prop metrics, behavioral "
    "forensics, independent disk review, and final implementation decision map"
)
PREVIOUS_STAGE_ID = "STAGE_05_DOMINANCE_POLLUTION_MIXED"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


STAGE05_STATUS_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
STAGE05_VERIFIER_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE05_VERIFIER_{DATE_ID}.json"
SESSION_STATE_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json"
ACTIVE_QUESTION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl"
EXTRA_STEP_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl"
PROMPT_APPLICATION_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl"
LINE_AUDIT_PATH = ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl"

OUTPUTS = {
    "ablation_metrics": ROUTE_DIR / f"VNEXT_FULL_REPLAY_ABLATION_METRICS_LEDGER_{DATE_ID}.jsonl",
    "robustness_prop_metrics": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_ROBUSTNESS_PROP_METRICS_LEDGER_{DATE_ID}.jsonl"
    ),
    "behavioral_forensics": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_BEHAVIORAL_FORENSICS_LEDGER_{DATE_ID}.jsonl"
    ),
    "final_decision_map": ROUTE_DIR / f"VNEXT_FULL_REPLAY_FINAL_DECISION_MAP_{DATE_ID}.jsonl",
    "prop_firm_metrics": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROP_FIRM_METRICS_{DATE_ID}.jsonl",
    "stage06_summary": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_FINAL_SUMMARY_{DATE_ID}.json",
    "stage06_verifier": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_VERIFIER_{DATE_ID}.json",
    "stage06_independent_review": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_INDEPENDENT_REVIEW_{DATE_ID}.json"
    ),
    "stage06_shard_contract": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_SHARD_CONTRACT_{DATE_ID}.json"
    ),
    "stage06_heartbeat": ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_HEARTBEAT_{DATE_ID}.json",
    "stage06_shard_status": (
        ROUTE_DIR / f"VNEXT_FULL_REPLAY_STAGE06_SHARD_STATUS_LEDGER_{DATE_ID}.jsonl"
    ),
}

SHARD_DIR = ROUTE_DIR / "stage06_shards"
SHARDED_ARTIFACT_KEYS = (
    "ablation_metrics",
    "robustness_prop_metrics",
    "behavioral_forensics",
    "final_decision_map",
)
STRESS_VARIANTS = (
    "base",
    "cost_minus_0_10r",
    "slippage_minus_0_25r",
    "delayed_entry_minus_0_50r",
    "missed_fill_winners_zero",
    "same_bar_conservative",
    "placebo_sign_flip",
)
PROP_RISK_PCTS = (0.5, 1.0, 2.0)
PROP_PHASE_TARGETS = (("phase1_8pct", 8.0), ("phase2_5pct", 5.0))
PROP_SCENARIOS = (
    "all_candidate_best_available",
    "current_shadow_follow_only",
    "hypothetical_follow_only",
    "current_shadow_avoid_blocked_context",
)
MISSING_VALUES = {None, "", "UNKNOWN", "unknown", "null", "None"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def repo_path(path: str | Path | None) -> Path:
    if path is None:
        return REPO_ROOT / "__missing__"
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def iter_gzip_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(raw).hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    return f"{prefix}_{stable_hash(payload)[:length]}"


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def safe_str(value: Any, fallback: str) -> str:
    if is_missing(value):
        return fallback
    return str(value)


def is_missing(value: Any) -> bool:
    if isinstance(value, (dict, list, tuple, set)):
        return False
    return value in MISSING_VALUES


def date_bucket(value: Any) -> dict[str, str]:
    raw = safe_str(value, "")
    date_part = raw[:10] if len(raw) >= 10 else "unknown_date"
    year = date_part[:4] if len(date_part) >= 4 else "unknown_year"
    month = date_part[:7] if len(date_part) >= 7 else "unknown_month"
    quarter = "unknown_quarter"
    try:
        q = (int(date_part[5:7]) - 1) // 3 + 1
        quarter = f"{year}-Q{q}"
    except Exception:
        pass
    old_recent = "recent_2025_plus" if year >= "2025" else "old_pre_2025"
    return {
        "date_utc": date_part,
        "month": month,
        "quarter": quarter,
        "old_recent_split": old_recent,
    }


class AtomicGzipJsonlWriter:
    def __init__(self, final_path: Path) -> None:
        self.final_path = final_path
        self.tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
        self.count = 0
        self._handle: gzip.GzipFile | None = None

    def __enter__(self) -> "AtomicGzipJsonlWriter":
        self.final_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = gzip.open(self.tmp_path, "wt", encoding="utf-8", newline="\n")
        return self

    def write(self, row: dict[str, Any]) -> None:
        if self._handle is None:
            raise RuntimeError("writer is not open")
        self._handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.count += 1

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._handle is not None:
            self._handle.close()
        if exc_type is None:
            self.tmp_path.replace(self.final_path)
        elif self.tmp_path.exists():
            self.tmp_path.unlink()


@dataclass
class RunningStats:
    denominator_count: int = 0
    performance_count: int = 0
    excluded_count: int = 0
    null_r_count: int = 0
    sum_r: float = 0.0
    sum_positive_r: float = 0.0
    sum_negative_r: float = 0.0
    min_r: float | None = None
    max_r: float | None = None
    win_count: int = 0
    loss_count: int = 0
    zero_count: int = 0
    equity_r: float = 0.0
    peak_r: float = 0.0
    max_drawdown_r: float = 0.0
    current_loss_streak: int = 0
    max_loss_streak: int = 0
    buckets: Counter[float] = field(default_factory=Counter)

    def update(self, value: float | None, included: bool = True) -> None:
        self.denominator_count += 1
        if value is None or not included:
            self.excluded_count += 1
            if value is None:
                self.null_r_count += 1
            return
        r = float(value)
        self.performance_count += 1
        self.sum_r += r
        self.min_r = r if self.min_r is None else min(self.min_r, r)
        self.max_r = r if self.max_r is None else max(self.max_r, r)
        self.buckets[round(r, 4)] += 1
        if r > 0:
            self.win_count += 1
            self.sum_positive_r += r
            self.current_loss_streak = 0
        elif r < 0:
            self.loss_count += 1
            self.sum_negative_r += r
            self.current_loss_streak += 1
            self.max_loss_streak = max(self.max_loss_streak, self.current_loss_streak)
        else:
            self.zero_count += 1
            self.current_loss_streak = 0
        self.equity_r += r
        self.peak_r = max(self.peak_r, self.equity_r)
        self.max_drawdown_r = max(self.max_drawdown_r, self.peak_r - self.equity_r)

    def median(self) -> float | None:
        if not self.performance_count:
            return None
        midpoint = (self.performance_count - 1) / 2
        running = 0
        lower = None
        upper = None
        for bucket, count in sorted(self.buckets.items()):
            previous = running
            running += count
            if lower is None and previous <= midpoint < running:
                lower = bucket
            if previous <= self.performance_count / 2 < running:
                upper = bucket
                break
        if lower is None:
            lower = next(iter(sorted(self.buckets)))
        if upper is None:
            upper = lower
        return (lower + upper) / 2

    def as_metrics(self) -> dict[str, Any]:
        profit_factor = None
        if self.sum_negative_r < 0:
            profit_factor = self.sum_positive_r / abs(self.sum_negative_r)
        return {
            "denominator_count": self.denominator_count,
            "performance_count": self.performance_count,
            "excluded_count": self.excluded_count,
            "null_r_count": self.null_r_count,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "zero_count": self.zero_count,
            "win_rate": self.win_count / self.performance_count if self.performance_count else None,
            "mean_r": self.sum_r / self.performance_count if self.performance_count else None,
            "median_r": self.median(),
            "total_r": self.sum_r,
            "expectancy_r": self.sum_r / self.performance_count if self.performance_count else None,
            "profit_factor": profit_factor,
            "min_r": self.min_r,
            "max_r": self.max_r,
            "max_drawdown_r": self.max_drawdown_r,
            "max_loss_streak": self.max_loss_streak,
        }


@dataclass
class AblationAccumulator:
    dims: dict[str, Any]
    row_count: int = 0
    candidate_ids: set[str] = field(default_factory=set)
    baseline_decisions: Counter[str] = field(default_factory=Counter)
    baseline_actions: Counter[str] = field(default_factory=Counter)
    dominant_decisions: Counter[str] = field(default_factory=Counter)
    terminal_outcomes: Counter[str] = field(default_factory=Counter)
    classifications: Counter[str] = field(default_factory=Counter)
    replay_modes: Counter[str] = field(default_factory=Counter)
    matched_rows_total: int = 0
    ltf_change_count: int = 0
    counterfactual_change_count: int = 0
    pollution_rows: Counter[str] = field(default_factory=Counter)
    variant_rows: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    stats: RunningStats = field(default_factory=RunningStats)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def update(self, row: dict[str, Any]) -> None:
        self.row_count += 1
        cid = safe_str(row.get("candidate_id"), "unknown_candidate")
        self.candidate_ids.add(cid)
        self.baseline_decisions[safe_str(row.get("baseline_decision"), "unknown_decision")] += 1
        self.baseline_actions[safe_str(row.get("baseline_action"), "unknown_action")] += 1
        self.dominant_decisions[safe_str(row.get("dominant_decision"), "unknown_dominant")] += 1
        path_context = row.get("path_context") or {}
        terminal = safe_str(
            path_context.get("best_available_terminal_outcome"),
            safe_str(row.get("dominant_decision"), "unknown_terminal"),
        )
        self.terminal_outcomes[terminal] += 1
        classification = safe_str(
            path_context.get("missed_winner_avoided_loser_classification"),
            "unclassified",
        )
        self.classifications[classification] += 1
        self.replay_modes[
            safe_str(path_context.get("best_available_replay_mode"), "unknown_replay_mode")
        ] += 1
        self.matched_rows_total += int(row.get("matched_rows") or 0)
        if row.get("would_change_execution_with_ltf_source") or path_context.get(
            "would_change_decision_or_execution_with_ltf_source"
        ):
            self.ltf_change_count += 1
        if row.get("changed_action_or_decision_under_counterfactual"):
            self.counterfactual_change_count += 1
        pollution = row.get("pollution_flags") or {}
        for key in (
            "broad_unanchored_rows",
            "stale_legacy_rows",
            "source_required_rows",
            "current_source_bound_rows",
        ):
            self.pollution_rows[key] += int(pollution.get(key) or 0)
        for variant, payload in (row.get("counterfactual_variants") or {}).items():
            counts = self.variant_rows[str(variant)]
            counts["rows"] += 1
            counts["rows_selected_total"] += int((payload or {}).get("rows_selected") or 0)
            counts["source_required_rows_total"] += int(
                (payload or {}).get("source_required_rows") or 0
            )
            if (payload or {}).get("changed_decision"):
                counts["decision_changed"] += 1
            if (payload or {}).get("changed_action"):
                counts["action_changed"] += 1
            counts[f"decision::{safe_str((payload or {}).get('decision'), 'unknown')}"] += 1
        self.stats.update(fnum(path_context.get("best_available_simulated_r")), included=True)
        if len(self.examples) < 5:
            self.examples.append(
                {
                    "dominance_row_id": row.get("dominance_row_id"),
                    "candidate_id": row.get("candidate_id"),
                    "dominant_row_id": row.get("dominant_row_id"),
                    "best_path_row_id": path_context.get("best_path_row_id"),
                }
            )

    def row(self) -> dict[str, Any]:
        variant_payload = {
            variant: dict(sorted(counts.items())) for variant, counts in sorted(self.variant_rows.items())
        }
        return {
            "schema_version": "vnext_full_replay_stage06_ablation_metrics_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "metric_row_id": stable_id("abl06", [self.dims, self.row_count, self.baseline_decisions]),
            **self.dims,
            "dominance_row_count": self.row_count,
            "candidate_count": len(self.candidate_ids),
            "baseline_decision_counts": dict(sorted(self.baseline_decisions.items())),
            "baseline_action_counts": dict(sorted(self.baseline_actions.items())),
            "dominant_decision_counts": dict(sorted(self.dominant_decisions.items())),
            "terminal_outcome_counts": dict(sorted(self.terminal_outcomes.items())),
            "missed_winner_avoided_loser_counts": dict(sorted(self.classifications.items())),
            "replay_mode_counts": dict(sorted(self.replay_modes.items())),
            "matched_rows_total": self.matched_rows_total,
            "ltf_change_count": self.ltf_change_count,
            "counterfactual_change_count": self.counterfactual_change_count,
            "pollution_row_sums": dict(sorted(self.pollution_rows.items())),
            "counterfactual_variant_metrics": variant_payload,
            "best_available_r_metrics": self.stats.as_metrics(),
            "example_row_links": self.examples,
            "metric_scope": "surface_evidence_family_ablation",
            "no_live_trading_or_broker_mutation": True,
        }


@dataclass
class RobustnessAccumulator:
    dims: dict[str, Any]
    stats: RunningStats = field(default_factory=RunningStats)
    terminal_outcomes: Counter[str] = field(default_factory=Counter)
    source_statuses: Counter[str] = field(default_factory=Counter)
    confidence_classes: Counter[str] = field(default_factory=Counter)
    exclusion_reasons: Counter[str] = field(default_factory=Counter)

    def update(self, row: dict[str, Any], value: float | None, included: bool) -> None:
        self.stats.update(value, included=included)
        self.terminal_outcomes[safe_str(row.get("terminal_outcome"), "unknown_terminal")] += 1
        self.source_statuses[safe_str(row.get("path_source_status"), "unknown_source_status")] += 1
        self.confidence_classes[safe_str(row.get("confidence"), "unknown_confidence")] += 1
        if not included:
            if value is None:
                reason = "null_simulated_r"
            elif not row.get("trade_performance_denominator_inclusion"):
                reason = "trade_performance_denominator_excluded"
            else:
                reason = "excluded_by_metric_contract"
            self.exclusion_reasons[reason] += 1

    def row(self) -> dict[str, Any]:
        return {
            "schema_version": "vnext_full_replay_stage06_robustness_metrics_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "metric_row_id": stable_id("rob06", [self.dims, self.stats.denominator_count]),
            **self.dims,
            "terminal_outcome_counts": dict(sorted(self.terminal_outcomes.items())),
            "source_status_counts": dict(sorted(self.source_statuses.items())),
            "source_mode_confidence_counts": dict(sorted(self.confidence_classes.items())),
            "exclusion_reason_counts": dict(sorted(self.exclusion_reasons.items())),
            "performance_metrics": self.stats.as_metrics(),
            "metric_contract": "stage04_path_outcome_r_streamed_source_mode_metrics",
            "no_live_trading_or_broker_mutation": True,
        }


@dataclass
class ForensicsAccumulator:
    dims: dict[str, Any]
    row_count: int = 0
    candidate_ids: set[str] = field(default_factory=set)
    stats: RunningStats = field(default_factory=RunningStats)
    decisions: Counter[str] = field(default_factory=Counter)
    classifications: Counter[str] = field(default_factory=Counter)
    source_modes: Counter[str] = field(default_factory=Counter)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def update(self, row: dict[str, Any], value: float | None, example_id: str | None = None) -> None:
        self.row_count += 1
        self.candidate_ids.add(safe_str(row.get("candidate_id"), "unknown_candidate"))
        self.stats.update(value, included=value is not None)
        self.decisions[
            safe_str(
                row.get("baseline_decision")
                or row.get("current_shadow_route_decision")
                or row.get("hypothetical_route_decision"),
                "unknown_decision",
            )
        ] += 1
        self.classifications[
            safe_str(
                row.get("classification")
                or (row.get("path_context") or {}).get("missed_winner_avoided_loser_classification"),
                "unclassified",
            )
        ] += 1
        self.source_modes[
            safe_str((row.get("path_context") or {}).get("best_available_replay_mode"), "unknown")
        ] += 1
        if len(self.examples) < 10:
            self.examples.append(
                {
                    "row_id": example_id
                    or row.get("dominance_row_id")
                    or row.get("path_row_id")
                    or row.get("mixed_resolution_row_id"),
                    "candidate_id": row.get("candidate_id"),
                    "best_path_row_id": (row.get("path_context") or {}).get("best_path_row_id")
                    or row.get("best_path_row_id"),
                }
            )

    def row(self) -> dict[str, Any]:
        return {
            "schema_version": "vnext_full_replay_stage06_behavioral_forensics_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "forensics_row_id": stable_id("for06", [self.dims, self.row_count]),
            **self.dims,
            "row_count": self.row_count,
            "candidate_count": len(self.candidate_ids),
            "decision_counts": dict(sorted(self.decisions.items())),
            "classification_counts": dict(sorted(self.classifications.items())),
            "source_mode_counts": dict(sorted(self.source_modes.items())),
            "r_impact_metrics": self.stats.as_metrics(),
            "example_row_links": self.examples,
            "no_live_trading_or_broker_mutation": True,
        }


def stage05_manifests() -> list[dict[str, Any]]:
    rows = list(iter_jsonl(STAGE05_STATUS_PATH))
    rows.sort(key=lambda row: int(row.get("source_index") or 0))
    return rows


def source_inventory_hash(manifests: list[dict[str, Any]]) -> str:
    payload = [
        {
            "source_index": row.get("source_index"),
            "source_path": row.get("source_path"),
            "stage05_shard_id": row.get("shard_id"),
            "outputs": row.get("outputs"),
        }
        for row in manifests
    ]
    return stable_hash(payload)


def source_stage06_shard_id(manifest: dict[str, Any]) -> str:
    payload = {
        "stage": STAGE_ID,
        "source_index": manifest.get("source_index"),
        "source_path": manifest.get("source_path"),
        "stage05_shard_id": manifest.get("shard_id"),
    }
    return stable_id("stage06src", payload, 16)


def stage06_shard_paths(shard_id: str) -> dict[str, Path]:
    base = SHARD_DIR / shard_id
    return {
        "ablation_metrics": base / "ablation_metrics.jsonl.gz",
        "robustness_prop_metrics": base / "robustness_prop_metrics.jsonl.gz",
        "behavioral_forensics": base / "behavioral_forensics.jsonl.gz",
        "final_decision_map": base / "final_decision_map.jsonl.gz",
        "manifest": base / "manifest.json",
        "heartbeat": base / "heartbeat.json",
    }


def write_stage06_heartbeat(payload: dict[str, Any]) -> None:
    heartbeat = {
        "schema_version": "vnext_full_replay_stage06_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "updated_at_utc": utc_now(),
        "status": payload.get("status", "running"),
        "current_shard_id": payload.get("shard_id"),
        "source_index": payload.get("source_index"),
        "source_path": payload.get("source_path"),
        "resume_cursor": payload.get("resume_cursor"),
    }
    write_json(OUTPUTS["stage06_heartbeat"], heartbeat)


def write_shard_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)


def validate_previous_stage() -> None:
    if not STAGE05_VERIFIER_PATH.exists():
        raise FileNotFoundError(f"missing Stage05 verifier: {STAGE05_VERIFIER_PATH}")
    verifier = read_json(STAGE05_VERIFIER_PATH)
    if str(verifier.get("status") or "").upper() != "OK" or int(
        verifier.get("failure_count") or 0
    ):
        raise RuntimeError("Stage05 verifier is not OK; refusing Stage06")


def group_key(prefix: str, dims: dict[str, Any], fields: tuple[str, ...]) -> tuple[tuple[str, Any], ...]:
    payload = {"group_scope": prefix}
    for field_name in fields:
        payload[field_name] = dims.get(field_name)
    return tuple(sorted(payload.items()))


def key_to_dims(key: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return dict(key)


def update_ablation_groups(
    groups: dict[tuple[tuple[str, Any], ...], AblationAccumulator], row: dict[str, Any]
) -> None:
    dims = {
        "source_path": safe_str(row.get("source_path"), "unknown_source"),
        "symbol": safe_str(row.get("symbol") or row.get("source_symbol"), "unknown_symbol"),
        "session_bucket": safe_str(row.get("session_bucket"), "unknown_session_bucket"),
        "route_session": safe_str(row.get("route_session"), "unknown_route_session"),
        "side": safe_str(row.get("side"), "unknown_side"),
        "framework": safe_str(row.get("framework") or row.get("route_family"), "unknown_framework"),
        "surface": safe_str(row.get("surface"), "unknown_surface"),
        "runtime_mode": safe_str(row.get("runtime_mode"), "unknown_runtime_mode"),
        "evidence_family": safe_str(row.get("dominant_evidence_family"), "unknown_or_no_match_family"),
        "source_component": safe_str(row.get("dominant_source_component"), "unknown_component"),
        "action_class": safe_str(row.get("dominant_action_class"), "unknown_action_class"),
        "baseline_decision": safe_str(row.get("baseline_decision"), "unknown_decision"),
    }
    scopes = (
        ("surface_family_source", (
            "source_path",
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "surface",
            "runtime_mode",
            "evidence_family",
            "source_component",
            "action_class",
            "baseline_decision",
        )),
        ("surface_family", (
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "surface",
            "runtime_mode",
            "evidence_family",
            "source_component",
            "baseline_decision",
        )),
        ("surface_decision", ("surface", "runtime_mode", "baseline_decision")),
        ("family_global", ("evidence_family", "source_component", "action_class")),
    )
    for scope, fields in scopes:
        key = group_key(scope, dims, fields)
        if key not in groups:
            groups[key] = AblationAccumulator(key_to_dims(key))
        groups[key].update(row)


def adjusted_r(row: dict[str, Any], variant: str) -> float | None:
    base = fnum(row.get("simulated_r"))
    if base is None:
        return None
    if variant == "base":
        return base
    if variant == "cost_minus_0_10r":
        return base - 0.10
    if variant == "slippage_minus_0_25r":
        return base - 0.25
    if variant == "delayed_entry_minus_0_50r":
        return base - 0.50 if row.get("entry_touched") else base
    if variant == "missed_fill_winners_zero":
        return 0.0 if base > 0 else base
    if variant == "same_bar_conservative":
        terminal = safe_str(row.get("terminal_outcome"), "")
        if row.get("same_bar_ambiguity") or "same_bar" in terminal:
            conservative = fnum(row.get("conservative_ambiguous_r"))
            return conservative if conservative is not None else min(base, -1.0)
        return base
    if variant == "placebo_sign_flip":
        return -base
    return base


def update_robustness_groups(
    groups: dict[tuple[tuple[str, Any], ...], RobustnessAccumulator], row: dict[str, Any]
) -> None:
    buckets = date_bucket(row.get("date_utc") or row.get("candle_time_utc"))
    dims = {
        "source_path": safe_str(row.get("market_bar_source_path") or row.get("source_path"), "unknown_source"),
        "symbol": safe_str(row.get("symbol") or row.get("source_symbol"), "unknown_symbol"),
        "session_bucket": safe_str(row.get("session_bucket"), "unknown_session_bucket"),
        "side": safe_str(row.get("side"), "unknown_side"),
        "framework": safe_str(row.get("framework"), "unknown_framework"),
        "replay_mode": safe_str(row.get("replay_mode"), "unknown_replay_mode"),
        "source_mode": safe_str(row.get("source_mode"), "unknown_source_mode"),
        "terminal_outcome": safe_str(row.get("terminal_outcome"), "unknown_terminal"),
        "old_recent_split": buckets["old_recent_split"],
        "month": buckets["month"],
        "quarter": buckets["quarter"],
        "confidence": safe_str(row.get("confidence"), "unknown_confidence"),
    }
    base_scopes = (
        ("overall", ()),
        ("symbol", ("symbol",)),
        ("session", ("session_bucket",)),
        ("side", ("side",)),
        ("framework", ("framework",)),
        ("source_mode", ("replay_mode", "source_mode")),
        ("symbol_session_side_framework", ("symbol", "session_bucket", "side", "framework")),
        ("old_recent_split", ("old_recent_split",)),
        ("calendar_month", ("month",)),
        ("walk_forward_quarter", ("quarter",)),
    )
    stress_scopes = {
        "overall",
        "symbol",
        "source_mode",
        "old_recent_split",
        "walk_forward_quarter",
    }
    included = bool(row.get("trade_performance_denominator_inclusion")) and fnum(
        row.get("simulated_r")
    ) is not None
    for scope, fields in base_scopes:
        variants = STRESS_VARIANTS if scope in stress_scopes else ("base",)
        for variant in variants:
            payload = dict(dims)
            payload["group_scope"] = scope
            payload["stress_variant"] = variant
            key = group_key(scope, payload, tuple(["stress_variant", *fields]))
            if key not in groups:
                groups[key] = RobustnessAccumulator(key_to_dims(key))
            groups[key].update(row, adjusted_r(row, variant), included=included)


def forensic_cluster_for_dominance(row: dict[str, Any]) -> str | None:
    path_context = row.get("path_context") or {}
    classification = safe_str(
        path_context.get("missed_winner_avoided_loser_classification"),
        "unclassified",
    )
    pollution = row.get("pollution_flags") or {}
    if int(pollution.get("source_required_rows") or 0) > 0:
        return "source_required_cluster"
    if int(pollution.get("broad_unanchored_rows") or 0) > 0:
        return "broad_unanchored_pressure_cluster"
    if int(pollution.get("stale_legacy_rows") or 0) > 0:
        return "stale_legacy_pollution_cluster"
    if row.get("would_change_execution_with_ltf_source") or path_context.get(
        "would_change_decision_or_execution_with_ltf_source"
    ):
        return "m15_blindness_or_ltf_change_cluster"
    if classification in {
        "captured_winner",
        "missed_winner",
        "avoided_loser",
        "accepted_loser",
        "no_fill_pending",
        "same_bar_ambiguous",
        "timeout_mark_to_market",
    }:
        return classification
    if row.get("changed_action_or_decision_under_counterfactual"):
        return "counterfactual_sensitive_pressure_cluster"
    return None


def update_forensics_from_dominance(
    groups: dict[tuple[tuple[str, Any], ...], ForensicsAccumulator], row: dict[str, Any]
) -> None:
    cluster = forensic_cluster_for_dominance(row)
    if not cluster:
        return
    dims = {
        "cluster_type": cluster,
        "symbol": safe_str(row.get("symbol") or row.get("source_symbol"), "unknown_symbol"),
        "session_bucket": safe_str(row.get("session_bucket"), "unknown_session_bucket"),
        "side": safe_str(row.get("side"), "unknown_side"),
        "framework": safe_str(row.get("framework") or row.get("route_family"), "unknown_framework"),
        "surface": safe_str(row.get("surface"), "unknown_surface"),
        "evidence_family": safe_str(row.get("dominant_evidence_family"), "unknown_or_no_match_family"),
        "source_component": safe_str(row.get("dominant_source_component"), "unknown_component"),
    }
    key = group_key(
        "behavioral_cluster",
        dims,
        (
            "cluster_type",
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "surface",
            "evidence_family",
            "source_component",
        ),
    )
    if key not in groups:
        groups[key] = ForensicsAccumulator(key_to_dims(key))
    groups[key].update(row, fnum((row.get("path_context") or {}).get("best_available_simulated_r")))


def update_forensics_from_mixed(
    groups: dict[tuple[tuple[str, Any], ...], ForensicsAccumulator], row: dict[str, Any]
) -> None:
    dims = {
        "cluster_type": f"mixed_{safe_str(row.get('resolution_class'), 'unknown_resolution')}",
        "symbol": safe_str(row.get("symbol"), "unknown_symbol"),
        "session_bucket": safe_str(row.get("route_session"), "unknown_route_session"),
        "side": safe_str(row.get("side"), "unknown_side"),
        "framework": safe_str(row.get("framework"), "unknown_framework"),
        "surface": safe_str(row.get("surface"), "unknown_surface"),
        "evidence_family": safe_str(row.get("evidence_family"), "unknown_family"),
        "source_component": safe_str(row.get("source_component"), "unknown_component"),
    }
    key = group_key(
        "mixed_resolution_cluster",
        dims,
        (
            "cluster_type",
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "surface",
            "evidence_family",
            "source_component",
        ),
    )
    if key not in groups:
        groups[key] = ForensicsAccumulator(key_to_dims(key))
    synthetic = {
        "candidate_id": row.get("mixed_resolution_row_id"),
        "baseline_decision": "MIXED",
        "classification": row.get("resolution_class"),
    }
    groups[key].update(synthetic, fnum(row.get("best_available_simulated_r_mean")), row.get("mixed_resolution_row_id"))


def classify_final_decision(metrics: dict[str, Any]) -> tuple[str, str, str]:
    count = int(metrics.get("candidate_count") or metrics.get("dominance_row_count") or 0)
    r_metrics = metrics.get("best_available_r_metrics") or metrics.get("r_impact_metrics") or {}
    mean_r = fnum(r_metrics.get("mean_r"))
    pollution = metrics.get("pollution_row_sums") or {}
    broad = int(pollution.get("broad_unanchored_rows") or 0)
    stale = int(pollution.get("stale_legacy_rows") or 0)
    source_required = int(pollution.get("source_required_rows") or 0)
    changed = int(metrics.get("counterfactual_change_count") or 0)
    class_counts = metrics.get("missed_winner_avoided_loser_counts") or metrics.get(
        "classification_counts"
    ) or {}
    missed = int(class_counts.get("missed_winner") or 0)
    accepted_loser = int(class_counts.get("accepted_loser") or 0)
    captured = int(class_counts.get("captured_winner") or 0)
    avoided = int(class_counts.get("avoided_loser") or 0)
    harmful = missed + accepted_loser
    useful = captured + avoided
    if source_required > 0:
        return (
            "REPAIR_SOURCE_OR_RUNTIME_CONTRACT",
            "source-required pressure remains; exact source/parser/export/runtime field must be repaired before promotion",
            "source_required_guard",
        )
    if (broad > 0 or stale > 0) and changed > 0:
        return (
            "KILL_OR_REMOVE_NOISY_PRESSURE",
            "broad/unanchored or stale legacy pressure changes action under counterfactual removal",
            "pollution_remove_candidate",
        )
    if count < 20:
        return (
            "KEEP_SHADOW",
            "effective replay count below 20; retain as shadow evidence only",
            "small_sample_shadow",
        )
    if mean_r is not None and mean_r > 0.15 and useful >= harmful:
        return (
            "PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER",
            "positive replay R and useful catch/avoid counts dominate harmful miss/accept counts",
            "promotion_candidate_requires_owner_review",
        )
    if mean_r is not None and mean_r < -0.10 and harmful > useful:
        return (
            "KILL_OR_REDESIGN_BEFORE_USE",
            "negative replay R with harmful miss/accepted-loser dominance",
            "redesign_or_remove_candidate",
        )
    if useful > harmful and mean_r is not None and mean_r >= 0:
        return (
            "KEEP_SHADOW_OR_GUARD_ONLY",
            "useful context is nonnegative but not strong enough for direct promotion",
            "guard_or_shadow_candidate",
        )
    return (
        "KEEP_SHADOW",
        "mixed or weak replay effect; preserve row evidence but do not promote",
        "shadow_only",
    )


def final_decision_from_ablation(row: dict[str, Any]) -> dict[str, Any]:
    decision, rationale, next_action = classify_final_decision(row)
    dims = {
        key: row.get(key)
        for key in (
            "group_scope",
            "surface",
            "runtime_mode",
            "evidence_family",
            "source_component",
            "action_class",
            "symbol",
            "session_bucket",
            "side",
            "framework",
            "baseline_decision",
        )
        if key in row
    }
    return {
        "schema_version": "vnext_full_replay_stage06_final_decision_map_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "decision_map_row_id": stable_id("dec06", [dims, row.get("metric_row_id")]),
        "decision_source": "stage06_ablation_metrics",
        "source_metric_row_id": row.get("metric_row_id"),
        **dims,
        "implementation_decision": decision,
        "decision_rationale": rationale,
        "next_required_action": next_action,
        "candidate_count": row.get("candidate_count"),
        "r_metrics": row.get("best_available_r_metrics"),
        "counterfactual_change_count": row.get("counterfactual_change_count"),
        "pollution_row_sums": row.get("pollution_row_sums"),
        "example_row_links": row.get("example_row_links"),
        "production_change_allowed_by_this_row": False,
        "requires_owner_review_before_runtime_effect": True,
        "no_live_trading_or_broker_mutation": True,
    }


def build_shard_contract(manifests: list[dict[str, Any]], source_hash: str) -> None:
    rows = []
    for index, manifest in enumerate(manifests, start=1):
        shard_id = source_stage06_shard_id(manifest)
        paths = stage06_shard_paths(shard_id)
        rows.append(
            {
                "shard_id": shard_id,
                "source_index": index,
                "source_count": len(manifests),
                "source_path": manifest.get("source_path"),
                "stage05_shard_id": manifest.get("shard_id"),
                "input_stage05_outputs": manifest.get("outputs"),
                "outputs": {key: rel(paths[key]) for key in SHARDED_ARTIFACT_KEYS},
                "temp_outputs": {
                    key: rel(paths[key].with_suffix(paths[key].suffix + ".tmp"))
                    for key in SHARDED_ARTIFACT_KEYS
                },
                "atomic_rename": "write .tmp then replace final after full gzip jsonl close",
                "heartbeat_path": rel(paths["heartbeat"]),
                "manifest_path": rel(paths["manifest"]),
                "resume_rule": "skip shard only when manifest/source_inventory_hash/input count/output sha256 all match",
                "source_inventory_hash": source_hash,
            }
        )
    write_json(
        OUTPUTS["stage06_shard_contract"],
        {
            "schema_version": "vnext_full_replay_stage06_shard_contract_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "previous_stage_id": PREVIOUS_STAGE_ID,
            "created_at_utc": utc_now(),
            "stage_scope": STAGE_SCOPE,
            "source_shard_count": len(rows),
            "shards": rows,
        },
    )


def output_matches_manifest(manifest: dict[str, Any], source_hash: str) -> bool:
    if manifest.get("shard_status") != "complete":
        return False
    if manifest.get("source_inventory_hash") != source_hash:
        return False
    for key in SHARDED_ARTIFACT_KEYS:
        output = (manifest.get("outputs") or {}).get(key) or {}
        path = repo_path(output.get("path"))
        if not path.exists():
            return False
        if sha256_file(path) != output.get("sha256"):
            return False
    return True


def stage04_manifest_for_stage05(stage05_manifest: dict[str, Any]) -> dict[str, Any]:
    path = repo_path(stage05_manifest.get("input_stage04_manifest_path"))
    if not path.exists():
        raise FileNotFoundError(f"missing Stage04 manifest referenced by Stage05: {path}")
    return read_json(path)


def write_one_source_shard(
    source_index: int,
    source_count: int,
    stage05_manifest: dict[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    shard_id = source_stage06_shard_id(stage05_manifest)
    paths = stage06_shard_paths(shard_id)
    existing_manifest = paths["manifest"]
    if existing_manifest.exists():
        existing = read_json(existing_manifest)
        if output_matches_manifest(existing, source_hash):
            return existing

    started_at = utc_now()
    heartbeat = {
        "schema_version": "vnext_full_replay_stage06_shard_heartbeat_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "shard_id": shard_id,
        "source_index": source_index,
        "source_count": source_count,
        "source_path": stage05_manifest.get("source_path"),
        "status": "running",
        "started_at_utc": started_at,
        "updated_at_utc": started_at,
        "resume_cursor": {"source_index": source_index, "dominance_rows_processed": 0},
    }
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage06_heartbeat(heartbeat)

    stage04_manifest = stage04_manifest_for_stage05(stage05_manifest)
    stage05_outputs = stage05_manifest.get("outputs") or {}
    dominance_path = repo_path((stage05_outputs.get("dominance_and_pollution") or {}).get("path"))
    mixed_path = repo_path((stage05_outputs.get("mixed_resolution") or {}).get("path"))
    path_outcome_path = repo_path((stage04_manifest.get("outputs") or {}).get("path_outcome_r", {}).get("path"))

    ablation_groups: dict[tuple[tuple[str, Any], ...], AblationAccumulator] = {}
    robustness_groups: dict[tuple[tuple[str, Any], ...], RobustnessAccumulator] = {}
    forensics_groups: dict[tuple[tuple[str, Any], ...], ForensicsAccumulator] = {}
    row_counts: Counter[str] = Counter()
    final_decision_counts: Counter[str] = Counter()
    mixed_resolution_counts: Counter[str] = Counter()

    for row in iter_gzip_jsonl(dominance_path):
        update_ablation_groups(ablation_groups, row)
        update_forensics_from_dominance(forensics_groups, row)
        row_counts["dominance_rows_processed"] += 1
        if row_counts["dominance_rows_processed"] % 50000 == 0:
            heartbeat["updated_at_utc"] = utc_now()
            heartbeat["resume_cursor"] = {
                "source_index": source_index,
                "dominance_rows_processed": row_counts["dominance_rows_processed"],
                "path_outcome_rows_processed": row_counts.get("path_outcome_rows_processed", 0),
            }
            write_shard_json(paths["heartbeat"], heartbeat)
            write_stage06_heartbeat(heartbeat)

    if mixed_path.exists():
        for row in iter_gzip_jsonl(mixed_path):
            mixed_resolution_counts[safe_str(row.get("resolution_class"), "unknown")] += 1
            update_forensics_from_mixed(forensics_groups, row)
            row_counts["mixed_resolution_rows_processed"] += 1

    for row in iter_gzip_jsonl(path_outcome_path):
        update_robustness_groups(robustness_groups, row)
        row_counts["path_outcome_rows_processed"] += 1
        if row_counts["path_outcome_rows_processed"] % 100000 == 0:
            heartbeat["updated_at_utc"] = utc_now()
            heartbeat["resume_cursor"] = {
                "source_index": source_index,
                "dominance_rows_processed": row_counts["dominance_rows_processed"],
                "path_outcome_rows_processed": row_counts["path_outcome_rows_processed"],
            }
            write_shard_json(paths["heartbeat"], heartbeat)
            write_stage06_heartbeat(heartbeat)

    with AtomicGzipJsonlWriter(paths["ablation_metrics"]) as writer:
        for accumulator in sorted(
            ablation_groups.values(), key=lambda item: json.dumps(item.dims, sort_keys=True)
        ):
            row = accumulator.row()
            writer.write(row)
            row_counts["ablation_metrics"] += 1
    ablation_rows = [
        accumulator.row()
        for accumulator in sorted(
            ablation_groups.values(), key=lambda item: json.dumps(item.dims, sort_keys=True)
        )
    ]

    with AtomicGzipJsonlWriter(paths["robustness_prop_metrics"]) as writer:
        for accumulator in sorted(
            robustness_groups.values(), key=lambda item: json.dumps(item.dims, sort_keys=True)
        ):
            writer.write(accumulator.row())
            row_counts["robustness_prop_metrics"] += 1

    with AtomicGzipJsonlWriter(paths["behavioral_forensics"]) as writer:
        for accumulator in sorted(
            forensics_groups.values(), key=lambda item: json.dumps(item.dims, sort_keys=True)
        ):
            writer.write(accumulator.row())
            row_counts["behavioral_forensics"] += 1

    with AtomicGzipJsonlWriter(paths["final_decision_map"]) as writer:
        for row in ablation_rows:
            if row.get("group_scope") not in {"surface_family_source", "family_global"}:
                continue
            decision_row = final_decision_from_ablation(row)
            writer.write(decision_row)
            final_decision_counts[decision_row["implementation_decision"]] += 1
            row_counts["final_decision_map"] += 1

    outputs: dict[str, dict[str, Any]] = {}
    for key in SHARDED_ARTIFACT_KEYS:
        path = paths[key]
        outputs[key] = {
            "path": rel(path),
            "row_count": row_counts[key],
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    completed_at = utc_now()
    manifest = {
        "schema_version": "vnext_full_replay_stage06_shard_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "stage_scope": STAGE_SCOPE,
        "shard_id": shard_id,
        "shard_status": "complete",
        "source_index": source_index,
        "source_count": source_count,
        "source_path": stage05_manifest.get("source_path"),
        "stage04_shard_id": stage04_manifest.get("shard_id"),
        "stage05_shard_id": stage05_manifest.get("shard_id"),
        "input_stage05_manifest_path": rel(repo_path(stage05_manifest.get("outputs", {}).get("dominance_and_pollution", {}).get("path")).parent / "manifest.json"),
        "input_stage04_manifest_path": stage05_manifest.get("input_stage04_manifest_path"),
        "outputs": outputs,
        "row_counts": dict(row_counts),
        "mixed_resolution_class_counts": dict(sorted(mixed_resolution_counts.items())),
        "final_decision_counts": dict(sorted(final_decision_counts.items())),
        "source_inventory_hash": source_hash,
        "started_at_utc": started_at,
        "completed_at_utc": completed_at,
        "heartbeat_updated_at_utc": completed_at,
        "resume_cursor": {
            "next_source_index": source_index + 1,
            "completed_source_path": stage05_manifest.get("source_path"),
            "dominance_rows_processed": row_counts["dominance_rows_processed"],
            "path_outcome_rows_processed": row_counts["path_outcome_rows_processed"],
        },
    }
    write_shard_json(paths["manifest"], manifest)
    heartbeat.update(
        {
            "updated_at_utc": completed_at,
            "status": "complete",
            "resume_cursor": manifest["resume_cursor"],
        }
    )
    write_shard_json(paths["heartbeat"], heartbeat)
    write_stage06_heartbeat(heartbeat)
    return manifest


def write_master_indices_from_shards(manifests: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for key in SHARDED_ARTIFACT_KEYS:
        rows = []
        for chunk_index, manifest in enumerate(manifests, start=1):
            output = (manifest.get("outputs") or {}).get(key) or {}
            rows.append(
                {
                    "schema_version": "vnext_full_replay_chunk_index_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "logical_artifact_path": rel(OUTPUTS[key]),
                    "chunk_index": chunk_index,
                    "chunk_path": output.get("path"),
                    "row_count": int(output.get("row_count") or 0),
                    "bytes": output.get("bytes"),
                    "sha256": output.get("sha256"),
                    "source_index": manifest.get("source_index"),
                    "source_path": manifest.get("source_path"),
                    "shard_id": manifest.get("shard_id"),
                    "shard_status": manifest.get("shard_status"),
                }
            )
            counts[key] += int(output.get("row_count") or 0)
        write_jsonl(OUTPUTS[key], rows)
    write_jsonl(OUTPUTS["stage06_shard_status"], manifests)
    counts["stage06_source_shards_completed"] = len(manifests)
    return dict(counts)


def prop_events_from_stage04(manifests: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {scenario: [] for scenario in PROP_SCENARIOS}
    for manifest in manifests:
        stage04_manifest = stage04_manifest_for_stage05(manifest)
        path = repo_path((stage04_manifest.get("outputs") or {}).get("missed_winner_avoided_loser", {}).get("path"))
        for row in iter_gzip_jsonl(path):
            r = fnum(row.get("best_available_simulated_r"))
            if r is None:
                continue
            base_event = {
                "time": safe_str(row.get("candle_time_utc"), "1900-01-01 00:00:00"),
                "date": safe_str(row.get("candle_time_utc"), "1900-01-01")[:10],
                "symbol": row.get("symbol") or row.get("source_symbol"),
                "framework": row.get("framework"),
                "side": row.get("side"),
                "classification": row.get("classification"),
                "r": r,
            }
            events["all_candidate_best_available"].append(base_event)
            if row.get("current_shadow_route_decision") == "FOLLOW":
                events["current_shadow_follow_only"].append(base_event)
            if row.get("hypothetical_route_decision") == "FOLLOW":
                events["hypothetical_follow_only"].append(base_event)
            if row.get("current_shadow_route_decision") == "AVOID":
                events["current_shadow_avoid_blocked_context"].append(base_event)
    for rows in events.values():
        rows.sort(key=lambda item: item["time"])
    return events


def simulate_prop_path(events: list[dict[str, Any]], risk_pct: float) -> dict[str, Any]:
    equity_pct = 0.0
    peak_pct = 0.0
    max_drawdown_pct = 0.0
    daily_returns: Counter[str] = Counter()
    monthly_returns: Counter[str] = Counter()
    loss_streak = 0
    max_loss_streak = 0
    for event in events:
        ret = float(event["r"]) * risk_pct
        equity_pct += ret
        peak_pct = max(peak_pct, equity_pct)
        max_drawdown_pct = max(max_drawdown_pct, peak_pct - equity_pct)
        daily_returns[event["date"]] += ret
        monthly_returns[event["date"][:7]] += ret
        if ret < 0:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        else:
            loss_streak = 0
    daily_loss_breach = any(value <= -5.0 for value in daily_returns.values())
    max_drawdown_breach = max_drawdown_pct >= 10.0
    return {
        "trade_count": len(events),
        "final_return_pct": equity_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "daily_loss_breach": daily_loss_breach,
        "max_drawdown_breach": max_drawdown_breach,
        "max_loss_streak": max_loss_streak,
        "active_day_count": len(daily_returns),
        "active_month_count": len(monthly_returns),
        "mean_monthly_return_pct": (
            sum(monthly_returns.values()) / len(monthly_returns) if monthly_returns else None
        ),
        "calendar_clustering_max_trades_day": (
            max(Counter(event["date"] for event in events).values()) if events else 0
        ),
        "monthly_returns_pct": dict(sorted(monthly_returns.items())),
    }


def monthly_bootstrap_pass_probability(
    monthly_returns_pct: dict[str, float],
    target_pct: float,
    *,
    seed: int = 20260524,
    trials: int = 500,
) -> float | None:
    values = list(monthly_returns_pct.values())
    if not values:
        return None
    rng = random.Random(seed)
    passes = 0
    for _ in range(trials):
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for _month in values:
            ret = rng.choice(values)
            equity += ret
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        if equity >= target_pct and max_dd < 10.0:
            passes += 1
    return passes / trials


def build_prop_metrics(manifests: list[dict[str, Any]]) -> tuple[int, Counter[str]]:
    events_by_scenario = prop_events_from_stage04(manifests)
    rows = []
    decision_counts: Counter[str] = Counter()
    for scenario, events in events_by_scenario.items():
        for risk_pct in PROP_RISK_PCTS:
            path = simulate_prop_path(events, risk_pct)
            for phase_name, target_pct in PROP_PHASE_TARGETS:
                pass_prob = monthly_bootstrap_pass_probability(
                    path["monthly_returns_pct"], target_pct
                )
                passed_deterministic = (
                    path["final_return_pct"] >= target_pct
                    and not path["daily_loss_breach"]
                    and not path["max_drawdown_breach"]
                )
                if passed_deterministic and pass_prob is not None and pass_prob >= 0.55:
                    decision = "prop_viable_in_replay_proxy"
                elif path["max_drawdown_breach"] or path["daily_loss_breach"]:
                    decision = "prop_risk_breach_in_replay_proxy"
                else:
                    decision = "prop_inconclusive_or_shadow_only"
                decision_counts[decision] += 1
                row = {
                    "schema_version": "vnext_full_replay_stage06_prop_firm_metrics_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "prop_metric_row_id": stable_id(
                        "prop06", [scenario, risk_pct, phase_name, len(events)]
                    ),
                    "scenario": scenario,
                    "risk_per_trade_pct": risk_pct,
                    "phase_target": phase_name,
                    "target_return_pct": target_pct,
                    "trade_count": path["trade_count"],
                    "final_return_pct": path["final_return_pct"],
                    "passed_deterministic_sequence": passed_deterministic,
                    "monthly_bootstrap_pass_probability_proxy": pass_prob,
                    "daily_loss_breach_rate_deterministic": 1.0
                    if path["daily_loss_breach"]
                    else 0.0,
                    "max_drawdown_breach_rate_deterministic": 1.0
                    if path["max_drawdown_breach"]
                    else 0.0,
                    "max_drawdown_pct": path["max_drawdown_pct"],
                    "max_loss_streak": path["max_loss_streak"],
                    "active_day_count": path["active_day_count"],
                    "active_month_count": path["active_month_count"],
                    "mean_monthly_return_pct": path["mean_monthly_return_pct"],
                    "calendar_clustering_max_trades_day": path[
                        "calendar_clustering_max_trades_day"
                    ],
                    "prop_metric_confidence": "simulated_replay_proxy_not_broker_account_truth",
                    "implementation_decision": decision,
                    "no_live_trading_or_broker_mutation": True,
                }
                rows.append(row)
    return write_jsonl(OUTPUTS["prop_firm_metrics"], rows), decision_counts


def aggregate_summary(manifests: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(write_master_indices_from_shards(manifests))
    final_decision_counts: Counter[str] = Counter()
    mixed_resolution_counts: Counter[str] = Counter()
    for manifest in manifests:
        final_decision_counts.update(manifest.get("final_decision_counts") or {})
        mixed_resolution_counts.update(manifest.get("mixed_resolution_class_counts") or {})
    prop_count, prop_decisions = build_prop_metrics(stage05_manifests())
    counts["prop_firm_metrics"] = prop_count
    summary = {
        "schema_version": "vnext_full_replay_stage06_final_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "previous_stage_id": PREVIOUS_STAGE_ID,
        "created_at_utc": utc_now(),
        "stage_scope": STAGE_SCOPE,
        "counts": dict(sorted(counts.items())),
        "source_shards": len(manifests),
        "final_decision_counts": dict(sorted(final_decision_counts.items())),
        "mixed_resolution_class_counts": dict(sorted(mixed_resolution_counts.items())),
        "prop_metric_decision_counts": dict(sorted(prop_decisions.items())),
        "completion_boundary": "replay_outputs_complete_no_live_trading_or_production_change",
    }
    write_json(OUTPUTS["stage06_summary"], summary)
    return summary


def audit_chunked_artifact(path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    id_field = {
        "ablation_metrics": "metric_row_id",
        "robustness_prop_metrics": "metric_row_id",
        "behavioral_forensics": "forensics_row_id",
        "final_decision_map": "decision_map_row_id",
    }[artifact_key]
    for index_row in iter_jsonl(path):
        chunk_path = repo_path(index_row.get("chunk_path"))
        parse_errors = 0
        row_count = 0
        first_row = None
        last_row = None
        required_missing: Counter[str] = Counter()
        duplicate_ids: Counter[str] = Counter()
        with gzip.open(chunk_path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                row_count += 1
                first_row = first_row or row
                last_row = row
                rid = row.get(id_field)
                if rid:
                    duplicate_ids[str(rid)] += 1
                for field_name in ("route_id", "stage_id", id_field):
                    if is_missing(row.get(field_name)):
                        required_missing[field_name] += 1
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "artifact_key": artifact_key,
                "logical_artifact_path": rel(path),
                "file_path": rel(chunk_path),
                "row_count": row_count,
                "manifest_row_count": int(index_row.get("row_count") or 0),
                "byte_count": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path),
                "first_row": first_row,
                "last_row": last_row,
                "parse_error_count": parse_errors,
                "required_missing_counts": dict(required_missing),
                "duplicate_id_count": sum(1 for value in duplicate_ids.values() if value > 1),
                "audit_status": (
                    "PASS"
                    if parse_errors == 0
                    and row_count == int(index_row.get("row_count") or 0)
                    and not required_missing
                    else "FAIL"
                ),
                "source_builder": rel(Path(__file__).resolve()),
            }
        )
    return rows


def audit_simple_artifact(path: Path, artifact_key: str) -> dict[str, Any]:
    parse_errors = 0
    row_count = 0
    first_row = None
    last_row = None
    if path.exists() and path.suffix == ".jsonl":
        for row in iter_jsonl(path):
            row_count += 1
            first_row = first_row or row
            last_row = row
    elif path.exists():
        try:
            first_row = read_json(path)
            last_row = first_row
            row_count = 1
        except Exception:
            parse_errors += 1
    return {
        "schema_version": "vnext_full_replay_line_accountability_audit_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "artifact_key": artifact_key,
        "file_path": rel(path),
        "row_count": row_count,
        "byte_count": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if path.exists() else None,
        "first_row": first_row,
        "last_row": last_row,
        "parse_error_count": parse_errors,
        "audit_status": "PASS" if path.exists() and parse_errors == 0 else "FAIL",
        "source_builder": rel(Path(__file__).resolve()),
    }


def update_line_audit() -> None:
    existing = [
        row
        for row in (list(iter_jsonl(LINE_AUDIT_PATH)) if LINE_AUDIT_PATH.exists() else [])
        if row.get("stage_id") != STAGE_ID
    ]
    stage_rows: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        stage_rows.extend(audit_chunked_artifact(OUTPUTS[key], key))
    for key in (
        "prop_firm_metrics",
        "stage06_summary",
        "stage06_verifier",
        "stage06_independent_review",
        "stage06_shard_contract",
        "stage06_heartbeat",
        "stage06_shard_status",
    ):
        stage_rows.append(audit_simple_artifact(OUTPUTS[key], key))
    write_jsonl(LINE_AUDIT_PATH, existing + stage_rows)


def independent_review(summary: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    failures: list[str] = []
    for key in SHARDED_ARTIFACT_KEYS:
        logical_path = OUTPUTS[key]
        logical_rows = list(iter_jsonl(logical_path))
        if not logical_rows:
            failures.append(f"{key}_chunk_index_empty")
            continue
        sample_count = 0
        null_id_count = 0
        for index_row in logical_rows:
            chunk_path = repo_path(index_row.get("chunk_path"))
            parsed = 0
            for row in iter_gzip_jsonl(chunk_path):
                parsed += 1
                sample_count += 1
                if key == "final_decision_map" and is_missing(row.get("implementation_decision")):
                    null_id_count += 1
                if key == "ablation_metrics" and is_missing(row.get("best_available_r_metrics")):
                    null_id_count += 1
            if parsed != int(index_row.get("row_count") or 0):
                failures.append(f"{key}_review_row_count_mismatch:{chunk_path}")
        findings.append(
            {
                "artifact_key": key,
                "logical_index_rows": len(logical_rows),
                "reviewed_data_rows": sample_count,
                "null_or_missing_material_field_count": null_id_count,
                "review_status": "PASS" if null_id_count == 0 else "WARN",
            }
        )
    prop_rows = list(iter_jsonl(OUTPUTS["prop_firm_metrics"]))
    if not prop_rows:
        failures.append("prop_firm_metrics_empty")
    decision_counts = summary.get("final_decision_counts") or {}
    if not decision_counts:
        failures.append("final_decision_counts_empty")
    review = {
        "schema_version": "vnext_full_replay_stage06_independent_review_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "reviewed_at_utc": utc_now(),
        "review_method": "independent_disk_read_verifier_pass_over_stage06_outputs",
        "status": "OK" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures[:100],
        "findings": findings,
        "summary_counts": summary.get("counts"),
        "review_scope": STAGE_SCOPE,
    }
    write_json(OUTPUTS["stage06_independent_review"], review)
    return review


def chunk_artifact_manifest(logical_path: Path, artifact_key: str) -> list[dict[str, Any]]:
    rows = []
    logical_count = 0
    if not logical_path.exists():
        return rows
    for index_row in iter_jsonl(logical_path):
        chunk_path = repo_path(index_row["chunk_path"])
        logical_count += int(index_row.get("row_count") or 0)
        rows.append(
            {
                "artifact_key": f"{artifact_key}_chunk",
                "path": rel(chunk_path),
                "logical_artifact_path": rel(logical_path),
                "bytes": chunk_path.stat().st_size if chunk_path.exists() else None,
                "sha256": sha256_file(chunk_path) if chunk_path.exists() else None,
                "row_count": int(index_row.get("row_count") or 0),
                "logical_row_count": None,
                "source_kind": "generated_replay_shard",
            }
        )
    rows.append(
        {
            "artifact_key": artifact_key,
            "path": rel(logical_path),
            "bytes": logical_path.stat().st_size,
            "sha256": sha256_file(logical_path),
            "row_count": sum(1 for _ in iter_jsonl(logical_path)),
            "logical_row_count": logical_count,
            "source_kind": "logical_chunk_index",
        }
    )
    return rows


def update_output_manifest(summary: dict[str, Any]) -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {
        "schema_version": "vnext_full_replay_output_manifest_v1",
        "route_id": ROUTE_ID,
        "artifacts": [],
    }
    stage_keys = set(OUTPUTS) | {f"{key}_chunk" for key in SHARDED_ARTIFACT_KEYS}
    stage_keys.update(
        {
            "active_questions",
            "extra_step",
            "prompt_application",
            "line_audit",
            "completion_audit",
        }
    )
    old = [row for row in existing.get("artifacts", []) if row.get("artifact_key") not in stage_keys]
    artifacts: list[dict[str, Any]] = []
    for key in SHARDED_ARTIFACT_KEYS:
        artifacts.extend(chunk_artifact_manifest(OUTPUTS[key], key))
    for key, path in OUTPUTS.items():
        if key in SHARDED_ARTIFACT_KEYS:
            continue
        artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": (
                    sum(1 for _ in iter_jsonl(path))
                    if path.exists() and path.suffix == ".jsonl"
                    else (1 if path.exists() else 0)
                ),
                "logical_row_count": summary.get("counts", {}).get(key),
                "source_kind": "generated_replay_output",
            }
        )
    for key, path in (
        ("active_questions", ACTIVE_QUESTION_PATH),
        ("extra_step", EXTRA_STEP_PATH),
        ("prompt_application", PROMPT_APPLICATION_PATH),
        ("line_audit", LINE_AUDIT_PATH),
        ("completion_audit", COMPLETION_AUDIT_PATH),
    ):
        artifacts.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
                "row_count": sum(1 for _ in iter_jsonl(path)) if path.suffix == ".jsonl" else 1,
                "logical_row_count": None,
                "source_kind": "route_control_output",
            }
        )
    existing["artifacts"] = old + artifacts
    existing["updated_at_utc"] = utc_now()
    write_json(OUTPUT_MANIFEST_PATH, existing)


def verify_outputs(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = summary or (
        read_json(OUTPUTS["stage06_summary"]) if OUTPUTS["stage06_summary"].exists() else {}
    )
    failures: list[str] = []
    manifests = list(iter_jsonl(OUTPUTS["stage06_shard_status"]))
    if len(manifests) != len(stage05_manifests()):
        failures.append("stage06_shard_count_does_not_match_stage05")
    counts = summary.get("counts") or {}
    for key in SHARDED_ARTIFACT_KEYS:
        if int(counts.get(key) or 0) <= 0:
            failures.append(f"{key}_rows_missing")
        logical_total = 0
        for index_row in iter_jsonl(OUTPUTS[key]):
            chunk_path = repo_path(index_row.get("chunk_path"))
            if not chunk_path.exists():
                failures.append(f"{key}_chunk_missing:{chunk_path}")
                continue
            parsed = sum(1 for _ in iter_gzip_jsonl(chunk_path))
            expected = int(index_row.get("row_count") or 0)
            logical_total += expected
            if parsed != expected:
                failures.append(f"{key}_row_count_mismatch:{chunk_path}:{parsed}!={expected}")
            if sha256_file(chunk_path) != index_row.get("sha256"):
                failures.append(f"{key}_sha_mismatch:{chunk_path}")
        if logical_total != int(counts.get(key) or 0):
            failures.append(f"{key}_logical_total_mismatch:{logical_total}!={counts.get(key)}")
    if int(counts.get("prop_firm_metrics") or 0) <= 0:
        failures.append("prop_firm_metrics_missing")
    review = independent_review(summary)
    if review.get("status") != "OK":
        failures.extend([f"independent_review:{item}" for item in review.get("failures", [])])
    verifier = {
        "schema_version": "vnext_full_replay_stage06_verifier_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "checked_at_utc": utc_now(),
        "status": "OK" if not failures else "FAIL",
        "failure_count": len(failures),
        "failures": failures[:100],
        "counts": counts,
        "final_decision_counts": summary.get("final_decision_counts"),
        "prop_metric_decision_counts": summary.get("prop_metric_decision_counts"),
        "independent_review_status": review.get("status"),
    }
    write_json(OUTPUTS["stage06_verifier"], verifier)
    if failures:
        raise RuntimeError(json.dumps(verifier, indent=2, sort_keys=True))
    return verifier


def update_session_state(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    state = read_json(SESSION_STATE_PATH) if SESSION_STATE_PATH.exists() else {}
    counts = state.get("counts") or {}
    counts.update(
        {
            "stage06_ablation_metric_rows": summary["counts"].get("ablation_metrics"),
            "stage06_robustness_prop_metric_rows": summary["counts"].get(
                "robustness_prop_metrics"
            ),
            "stage06_behavioral_forensics_rows": summary["counts"].get(
                "behavioral_forensics"
            ),
            "stage06_final_decision_map_rows": summary["counts"].get("final_decision_map"),
            "stage06_prop_firm_metric_rows": summary["counts"].get("prop_firm_metrics"),
            "stage06_source_shards_completed": summary["counts"].get(
                "stage06_source_shards_completed"
            ),
        }
    )
    state.update(
        {
            "schema_version": "vnext_full_replay_session_state_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "git_head": git_head(),
            "current_stage": STAGE_ID,
            "active_invariant": STAGE_SCOPE,
            "first_incomplete_invariant": "none_same_evidence_class_replay_outputs_verified",
            "next_action": "owner review of final replay decision map and any separate production-change dossier",
            "goal_complete": True,
            "counts": counts,
            "stage06_output_paths": {key: rel(path) for key, path in OUTPUTS.items()},
            "stage06_verifier_status": verifier.get("status"),
            "stage06_independent_review_status": verifier.get("independent_review_status"),
            "stage06_final_decision_counts": summary.get("final_decision_counts"),
            "stage06_prop_metric_decision_counts": summary.get("prop_metric_decision_counts"),
            "stage06_completion_boundary": summary.get("completion_boundary"),
        }
    )
    write_json(SESSION_STATE_PATH, state)


def update_completion_audit(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    audit = read_json(COMPLETION_AUDIT_PATH) if COMPLETION_AUDIT_PATH.exists() else {}
    completed = list(audit.get("completed_requirements_stage06") or [])
    for item in (
        "Stage06 terminal metrics builder built route-locally",
        "Ablation metrics computed by behavior surface, evidence family, component, action class, symbol, session, side, framework, and runtime mode",
        "Robustness metrics computed across old/recent, walk-forward quarter, calendar month, market/session/side/framework/source-mode holdouts, and stress/placebo variants",
        "Prop-firm replay proxy metrics computed for 8% phase-1 and 5% phase-2 targets across 0.5%, 1.0%, and 2.0% risk",
        "Behavioral forensics clusters written for catches, misses, overblocks, underblocks, M15/LTF changes, source-required rows, and pollution",
        "Final promote/kill/repair/keep-shadow decision map written from row-backed metrics",
        "Independent disk-read review and verifier passed over Stage06 outputs",
    ):
        if item not in completed:
            completed.append(item)
    audit.update(
        {
            "schema_version": "vnext_full_replay_completion_audit_v1",
            "route_id": ROUTE_ID,
            "updated_at_utc": utc_now(),
            "completion_status": "COMPLETE_REPLAY_OUTPUTS_VERIFIED",
            "goal_may_be_marked_complete": True,
            "completed_requirements_stage06": completed,
            "remaining_prompt_requirements_not_complete": [],
            "same_evidence_class_next_action": "none; owner review/production-change dossier is a separate boundary",
            "stage06_counts": summary.get("counts"),
            "stage06_verifier_status": verifier.get("status"),
            "stage06_independent_review_status": verifier.get("independent_review_status"),
            "stage06_final_decision_counts": summary.get("final_decision_counts"),
        }
    )
    write_json(COMPLETION_AUDIT_PATH, audit)


def update_route_control_ledgers(summary: dict[str, Any], verifier: dict[str, Any]) -> None:
    existing_questions = [
        row
        for row in (list(iter_jsonl(ACTIVE_QUESTION_PATH)) if ACTIVE_QUESTION_PATH.exists() else [])
        if row.get("question_id")
        not in {
            "Q011_STAGE05_ABLATION_METRICS_NEXT",
            "Q012_STAGE06_FINAL_OWNER_REVIEW_BOUNDARY",
        }
    ]
    question_rows = [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q011_STAGE05_ABLATION_METRICS_NEXT",
            "question": "Which decision surfaces survive ablation, robustness, prop-firm, concentration, and behavioral forensics?",
            "status": "answered_stage06",
            "evidence_path": rel(OUTPUTS["stage06_summary"]),
            "row_count": summary["counts"].get("final_decision_map"),
            "created_at_utc": utc_now(),
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "question_id": "Q012_STAGE06_FINAL_OWNER_REVIEW_BOUNDARY",
            "question": "Which final replay decisions require owner review or a separate production-change dossier?",
            "status": "open_separate_boundary_after_replay_completion",
            "evidence_path": rel(OUTPUTS["final_decision_map"]),
            "created_at_utc": utc_now(),
        },
    ]
    write_jsonl(ACTIVE_QUESTION_PATH, existing_questions + question_rows)

    extra_rows = list(iter_jsonl(EXTRA_STEP_PATH)) if EXTRA_STEP_PATH.exists() else []
    extra_rows.append(
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "pursuit_id": stable_id("extra06", summary.get("counts")),
            "requirement": "Run ablations, robustness/prop metrics, behavioral forensics, independent review, and final decision map",
            "actions_executed": [
                "read Stage05 dominance and MIXED shards",
                "read Stage04 path outcome and missed-winner/avoided-loser shards",
                "compute ablation metrics by surface/evidence family/action class",
                "compute source-mode, time-split, holdout, stress, placebo, and prop-firm replay proxy metrics",
                "write behavioral forensics and final decision-map shards",
                "run independent disk-read review and verifier",
            ],
            "result": "completed_stage06_terminal_replay_outputs",
            "evidence_path": rel(OUTPUTS["stage06_summary"]),
            "created_at_utc": utc_now(),
        }
    )
    write_jsonl(EXTRA_STEP_PATH, extra_rows)

    prompt_rows = list(iter_jsonl(PROMPT_APPLICATION_PATH)) if PROMPT_APPLICATION_PATH.exists() else []
    prompt_rows.append(
        {
            "schema_version": "vnext_full_replay_prompt_application_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "prompt_requirement": "Finish the replay spine through ablation, robustness, prop metrics, behavioral forensics, independent review, and final decision map without reopening already-proven Stage02 nudges",
            "application_status": "applied_complete_replay_outputs_verified",
            "evidence_path": rel(OUTPUTS["stage06_summary"]),
            "row_count": summary["counts"].get("final_decision_map"),
            "created_at_utc": utc_now(),
        }
    )
    write_jsonl(PROMPT_APPLICATION_PATH, prompt_rows)

    update_line_audit()
    update_session_state(summary, verifier)
    update_completion_audit(summary, verifier)
    update_output_manifest(summary)


def build_outputs() -> dict[str, Any]:
    validate_previous_stage()
    manifests = stage05_manifests()
    source_hash = source_inventory_hash(manifests)
    build_shard_contract(manifests, source_hash)
    completed: list[dict[str, Any]] = []
    for index, manifest in enumerate(manifests, start=1):
        completed.append(write_one_source_shard(index, len(manifests), manifest, source_hash))
    summary = aggregate_summary(completed)
    verifier = verify_outputs(summary)
    update_route_control_ledgers(summary, verifier)
    return summary


def check_outputs() -> dict[str, Any]:
    summary = read_json(OUTPUTS["stage06_summary"])
    verifier = verify_outputs(summary)
    update_line_audit()
    return {"summary": summary, "verifier": verifier}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify existing outputs only")
    args = parser.parse_args(argv)
    if args.check:
        result = check_outputs()
    else:
        summary = build_outputs()
        result = {"summary": summary, "verifier": read_json(OUTPUTS["stage06_verifier"])}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
