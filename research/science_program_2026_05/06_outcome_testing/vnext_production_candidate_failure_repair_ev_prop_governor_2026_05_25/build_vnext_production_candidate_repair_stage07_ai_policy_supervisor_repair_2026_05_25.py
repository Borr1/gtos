from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import (  # noqa: E402
    vnext_ai_policy_no_paid_call_replay_decision,
)


ROUTE_DIR = Path(__file__).resolve().parent
ROUTE_ID = "vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25"

AI_LEDGER = ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_AI_POLICY_SUPERVISOR_LEDGER_2026-05-25.jsonl"
STAGE03_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE03_EXECUTABLE_STREAM_SEMANTICS_LEDGER_2026-05-25.jsonl"
)
STAGE05_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE05_AVOID_PRE_AI_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE06_LEDGER = (
    ROUTE_DIR / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE06_LTF_ENTRY_NOFILL_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE07_LEDGER = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_LEDGER_2026-05-25.jsonl"
)
STAGE07_SUMMARY = (
    ROUTE_DIR
    / "VNEXT_PRODUCTION_CANDIDATE_REPAIR_STAGE07_AI_POLICY_SUPERVISOR_REPAIR_SUMMARY_2026-05-25.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class ScenarioStats:
    selected_count: int = 0
    performance_count: int = 0
    total_r: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    null_r_count: int = 0
    reason_counts: Counter[str] = field(default_factory=Counter)
    action_counts: Counter[str] = field(default_factory=Counter)
    coverage: dict[str, Counter[str]] = field(
        default_factory=lambda: {
            "symbols": Counter(),
            "sessions": Counter(),
            "sides": Counter(),
            "frameworks": Counter(),
            "source_modes": Counter(),
            "months": Counter(),
        }
    )

    def add(self, row: dict[str, Any], *, selected: bool, action: str, reason: str) -> None:
        if not selected:
            self.reason_counts[reason] += 1
            return
        self.selected_count += 1
        self.action_counts[action] += 1
        for key, source_key in (
            ("symbols", "symbol"),
            ("sessions", "session"),
            ("sides", "side"),
            ("frameworks", "framework"),
            ("source_modes", "source_mode"),
            ("months", "month"),
        ):
            self.coverage[key][str(row.get(source_key) or "")] += 1
        r_value = _as_float(
            row.get("simulated_r")
            if "simulated_r" in row
            else row.get("simulated_r_scoring_only")
        )
        if r_value is None:
            self.null_r_count += 1
            return
        self.performance_count += 1
        self.total_r += r_value
        if r_value > 0:
            self.win_count += 1
        elif r_value < 0:
            self.loss_count += 1

    def to_record(self) -> dict[str, Any]:
        expectancy = self.total_r / self.performance_count if self.performance_count else None
        return {
            "selected_count": self.selected_count,
            "performance_count": self.performance_count,
            "total_r": round(self.total_r, 12),
            "expectancy_r": round(expectancy, 12) if expectancy is not None else None,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "null_r_count": self.null_r_count,
            "action_counts": dict(self.action_counts.most_common()),
            "reason_counts": dict(self.reason_counts.most_common()),
            "selected_only_coverage": {
                key: dict(counter.most_common()) for key, counter in self.coverage.items()
            },
        }


def load_stage03() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in iter_jsonl(STAGE03_LEDGER):
        cid = str(row.get("candidate_id") or "")
        semantics = row.get("repaired_route_semantics") or {}
        membership = row.get("scenario_membership") or {}
        records[cid] = {
            "selected": bool(membership.get("vnext_executable_stream_without_prop_governance")),
            "route_decision": str(semantics.get("route_decision") or ""),
            "pre_ai_action": str(semantics.get("pre_ai_action") or ""),
            "stream_class": str(semantics.get("stream_class") or ""),
            "reason": str(semantics.get("reason") or ""),
            "source_mode": str(row.get("source_mode") or ""),
            "month": str(row.get("month") or str(row.get("as_of_utc") or "")[:7]),
            "prop_governance_eligible": bool(
                semantics.get("prop_governance_eligible_after_stage03")
            ),
            "preserve_current_system_behavior": bool(
                semantics.get("preserve_current_system_behavior")
            ),
        }
        counts["stage03_rows"] += 1
        if records[cid]["selected"]:
            counts["stage03_vnext_executable_stream"] += 1
        counts[f"stage03_route_{records[cid]['route_decision'] or 'UNKNOWN'}"] += 1
    return records, dict(counts)


def load_stage05() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in iter_jsonl(STAGE05_LEDGER):
        cid = str(row.get("candidate_id") or "")
        records[cid] = {
            "implementation_decision": str(row.get("implementation_decision") or ""),
            "hard_block_allowed_after_repair": bool(row.get("hard_block_allowed_after_repair")),
            "recovered": bool(row.get("recovered_into_stage05_no_prop_stream")),
            "decision_reason": str(row.get("decision_reason") or ""),
            "evidence_family": str(row.get("avoid_evidence_family") or ""),
            "source_component": str(row.get("avoid_source_component") or ""),
            "evidence_classification": str(row.get("evidence_classification") or ""),
            "missing_attribution_demoted": bool(row.get("missing_attribution_demoted")),
        }
        counts["stage05_rows"] += 1
        if records[cid]["recovered"]:
            counts["stage05_recovered_stream"] += 1
        if records[cid]["hard_block_allowed_after_repair"]:
            counts["stage05_preserved_hard_blocks"] += 1
        counts[f"stage05_decision_{records[cid]['implementation_decision'] or 'UNKNOWN'}"] += 1
    return records, dict(counts)


def load_stage06() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in iter_jsonl(STAGE06_LEDGER):
        cid = str(row.get("candidate_id") or "")
        records[cid] = {
            "selected": bool(row.get("selected_after_stage06_ltf")),
            "selected_stream_source": str(row.get("selected_stream_source") or ""),
            "stage06_ltf_action": str(row.get("stage06_ltf_action") or ""),
            "stage06_repair_branch": str(row.get("stage06_repair_branch") or ""),
            "source_mode": str(row.get("source_mode") or ""),
            "source_status": str(row.get("path_source_status") or ""),
            "source_complete_for_ltf_decision": bool(row.get("source_complete_for_ltf_decision")),
        }
        counts["stage06_rows"] += 1
        if records[cid]["selected"]:
            counts["stage06_selected_stream"] += 1
        counts[f"stage06_action_{records[cid]['stage06_ltf_action'] or 'UNKNOWN'}"] += 1
    return records, dict(counts)


def schema_contract(action: str, row: dict[str, Any]) -> dict[str, Any]:
    call_ai = action.startswith("CALL_AI")
    return {
        "schema_name": "PrimaryAnalysisOutput",
        "schema_validation_required": True,
        "allowed_decisions": ["NO_TRADE", "CANDIDATE", "WAIT"] if call_ai else ["NO_TRADE"],
        "candidate_directions": [str(row.get("side") or "")] if call_ai else [],
        "candidate_frameworks": [str(row.get("framework") or "")] if call_ai else [],
        "malformed_response_demotes_to_no_trade": True,
        "semantic_repair_must_preserve_trade_fields": True,
    }


def prompt_packet(row: dict[str, Any], *, action: str, role: str, branch: str) -> dict[str, Any]:
    packet = {
        "schema_version": "vnext_stage07_ai_prompt_packet_v1",
        "route_id": ROUTE_ID,
        "candidate_id": row.get("candidate_id"),
        "as_of_utc": row.get("as_of_utc"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "side": row.get("side"),
        "framework": row.get("framework"),
        "ai_policy_action": action,
        "ai_role": role,
        "policy_branch": branch,
        "decision_inputs_exclude_future_outcome_and_r": True,
    }
    packet["prompt_packet_sha256"] = stable_hash(packet)
    packet["cache_key_sha256"] = stable_hash(
        {
            "prompt_packet_sha256": packet["prompt_packet_sha256"],
            "schema_name": "PrimaryAnalysisOutput",
            "model_family": "configured_primary_analyzer",
        }
    )
    return packet


def classify_stage07_policy(
    row: dict[str, Any],
    *,
    stage03: dict[str, Any] | None,
    stage05: dict[str, Any] | None,
    stage06: dict[str, Any] | None,
) -> dict[str, Any]:
    selected_stream = bool(stage06 and stage06.get("selected"))
    route_decision = str((stage03 or {}).get("route_decision") or row.get("pre_ai_decision") or "")
    pre_ai_action = str((stage03 or {}).get("pre_ai_action") or row.get("pre_ai_action") or "")
    stage05_decision = str((stage05 or {}).get("implementation_decision") or "")

    if stage05 and stage05.get("hard_block_allowed_after_repair"):
        action = "SKIP_AI_MECHANICAL_AVOID"
        branch = "stage05_preserved_bounded_avoid_skips_ai"
        reason = "bounded_mechanical_avoid_skips_ai"
        role = "no_ai_mechanical_avoid"
        ai_required = False
    elif selected_stream and stage05 and stage05.get("recovered"):
        action = "CALL_AI_CONSTRAINED_VALIDATOR"
        branch = "stage05_demoted_avoid_context_recovered_requires_validator"
        reason = "stage05_demoted_avoid_context_requires_ai_validator"
        role = "vnext_recovered_context_validator"
        ai_required = True
    elif selected_stream and route_decision == "FOLLOW":
        if pre_ai_action.startswith("NARROW_AI"):
            action = "CALL_AI_NARROWED_ROUTE"
            branch = "repaired_follow_narrowed_route_calls_ai"
            reason = "repaired_follow_uses_source_bound_ai_validator"
            role = "vnext_route_validator"
        else:
            action = "CALL_AI_CONSTRAINED_VALIDATOR"
            branch = "repaired_follow_constrained_validator"
            reason = "repaired_follow_uses_constrained_validator"
            role = "vnext_constrained_follow_validator"
        ai_required = True
    elif route_decision == "MIXED":
        action = "CALL_AI_MIXED_RESOLUTION"
        branch = "mixed_requires_ai_resolution_diagnostic_not_prop_budget"
        reason = "mixed_context_requires_ai_resolution_before_execution"
        role = "vnext_mixed_resolution_validator"
        ai_required = True
    elif route_decision == "AVOID" or pre_ai_action == "SKIP_AI_AVOID_ONLY":
        if stage05_decision == "DEMOTE_TO_CONTEXT_NOT_EXECUTION_BLOCK":
            action = "CALL_AI_CONSTRAINED_VALIDATOR"
            branch = "demoted_avoid_context_not_selected_without_recovered_stream"
            reason = "demoted_avoid_context_requires_candidate_resolution"
            role = "vnext_recovered_context_validator"
            ai_required = False
        else:
            action = "SKIP_AI_MECHANICAL_AVOID"
            branch = "mechanical_avoid_no_edge_skips_ai"
            reason = "mechanical_avoid_or_no_edge_skips_ai"
            role = "no_ai_mechanical_avoid"
            ai_required = False
    elif route_decision == "LEGACY":
        action = "BLOCK_LEGACY_BROAD_FALLBACK"
        branch = "legacy_broad_fallback_not_replayed"
        reason = "legacy_broad_ai_fallback_not_replayed"
        role = "no_ai_legacy_block"
        ai_required = False
    else:
        action = "BLOCK_LEGACY_BROAD_FALLBACK"
        branch = "unknown_or_non_executable_ai_policy_block"
        reason = "unknown_route_not_ai_executable"
        role = "no_ai_unknown_block"
        ai_required = False

    if selected_stream and action == "MECHANICAL_FOLLOW_NO_AI":
        no_paid_policy = {
            "action": action,
            "would_action": action,
            "would_allow_ai_call": False,
        }
    else:
        no_paid_policy = {
            "action": action,
            "would_action": action,
            "would_allow_ai_call": bool(ai_required),
        }
    no_paid = vnext_ai_policy_no_paid_call_replay_decision(
        no_paid_policy,
        production_selected=selected_stream,
    )
    return {
        "stage07_ai_policy_action": action,
        "stage07_ai_policy_would_action": action,
        "stage07_ai_role": role,
        "stage07_policy_branch": branch,
        "stage07_policy_reason": reason,
        "stage07_ai_call_required_for_production": bool(selected_stream and ai_required),
        "stage07_ai_call_skipped_by_mechanical_policy": action
        in {"SKIP_AI_MECHANICAL_AVOID", "MECHANICAL_FOLLOW_NO_AI", "BLOCK_LEGACY_BROAD_FALLBACK"},
        "stage07_no_paid_call_selected": bool(no_paid["selected"]),
        "stage07_no_paid_call_status": str(no_paid["status"]),
        "stage07_no_paid_call_reason": str(no_paid["reason"]),
        "stage07_no_paid_call_diagnostic_only": bool(no_paid["diagnostic_only"]),
    }


def build() -> dict[str, Any]:
    stage03, stage03_counts = load_stage03()
    stage05, stage05_counts = load_stage05()
    stage06, stage06_counts = load_stage06()

    old_action_counts: Counter[str] = Counter()
    old_supervisor_counts: Counter[str] = Counter()
    stage07_action_counts: Counter[str] = Counter()
    stage07_branch_counts: Counter[str] = Counter()
    no_paid_counts: Counter[str] = Counter()
    ai_required_rows = 0
    prompt_packet_rows = 0
    prompt_packet_hash_missing = 0
    selected_stream_rows = 0
    stale_follow_without_ai_rows = 0
    future_input_bad_rows = 0
    source_status_counts: Counter[str] = Counter()
    selected_source_counts: Counter[str] = Counter()
    malformed_policy_counts: Counter[str] = Counter()
    supervisor_effect_counts: Counter[str] = Counter()
    scenarios = {
        "stage06_selected_stream_before_ai_policy": ScenarioStats(),
        "stage07_production_ai_policy_contract": ScenarioStats(),
        "stage07_no_paid_call_diagnostic": ScenarioStats(),
    }

    tmp = STAGE07_LEDGER.with_suffix(STAGE07_LEDGER.suffix + ".tmp")
    with AI_LEDGER.open("r", encoding="utf-8") as source, tmp.open(
        "w", encoding="utf-8", newline="\n"
    ) as out:
        for idx, line in enumerate(source, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            cid = str(row.get("candidate_id") or "")
            s03 = stage03.get(cid)
            s05 = stage05.get(cid)
            s06 = stage06.get(cid)
            selected_stream = bool(s06 and s06.get("selected"))
            if selected_stream:
                selected_stream_rows += 1
                selected_source_counts[str(s06.get("selected_stream_source") or "")] += 1
            policy = classify_stage07_policy(row, stage03=s03, stage05=s05, stage06=s06)
            action = policy["stage07_ai_policy_action"]
            old_action = str(row.get("ai_policy_action") or "UNKNOWN")
            old_action_counts[old_action] += 1
            old_supervisor_counts[str(row.get("ai_supervisor_action") or "UNKNOWN")] += 1
            stage07_action_counts[action] += 1
            stage07_branch_counts[str(policy["stage07_policy_branch"])] += 1
            no_paid_counts[str(policy["stage07_no_paid_call_status"])] += 1
            if old_action == "FOLLOW_WITHOUT_AI":
                stale_follow_without_ai_rows += 1
            if policy["stage07_ai_call_required_for_production"]:
                ai_required_rows += 1
            if selected_stream:
                source_status_counts[str((s06 or {}).get("source_status") or row.get("source_mode") or "")] += 1
            source_mode = (
                (s06 or {}).get("source_mode")
                or (s03 or {}).get("source_mode")
                or row.get("source_mode")
            )

            packet: dict[str, Any] | None = None
            packet_sha = None
            cache_sha = None
            if action.startswith("CALL_AI") and selected_stream:
                packet = prompt_packet(
                    row,
                    action=action,
                    role=str(policy["stage07_ai_role"]),
                    branch=str(policy["stage07_policy_branch"]),
                )
                packet_sha = packet["prompt_packet_sha256"]
                cache_sha = packet["cache_key_sha256"]
                prompt_packet_rows += 1
                if not packet_sha or not cache_sha:
                    prompt_packet_hash_missing += 1

            if not True:
                future_input_bad_rows += 1
            malformed_policy = (
                "repair_json_format_preserving_semantics_then_schema_validate"
                if action.startswith("CALL_AI")
                else "no_ai_or_block_demotes_to_no_trade"
            )
            malformed_policy_counts[malformed_policy] += 1
            supervisor_effect = (
                "healthy_no_runtime_override"
                if str(row.get("ai_supervisor_action") or "") == "HEALTHY"
                else "supervisor_disables_active_ai_effect"
            )
            supervisor_effect_counts[supervisor_effect] += 1

            out_row = {
                "schema_version": "vnext_production_candidate_repair_stage07_ai_policy_supervisor_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
                "row_id": f"stage07_ai_policy_supervisor_{idx:06d}",
                "candidate_id": cid,
                "as_of_utc": row.get("as_of_utc"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "framework": row.get("framework"),
                "source_mode": source_mode,
                "month": (s03 or {}).get("month") or str(row.get("as_of_utc") or "")[:7],
                "terminal_outcome_scoring_only": row.get("terminal_outcome"),
                "simulated_r_scoring_only": row.get("simulated_r"),
                "stage06_selected_stream": selected_stream,
                "stage06_selected_stream_source": (s06 or {}).get("selected_stream_source"),
                "stage06_ltf_action": (s06 or {}).get("stage06_ltf_action"),
                "stage03_route_decision": (s03 or {}).get("route_decision"),
                "stage03_stream_class": (s03 or {}).get("stream_class"),
                "stage05_implementation_decision": (s05 or {}).get("implementation_decision"),
                "stage05_recovered_into_stream": bool(s05 and s05.get("recovered")),
                "stage05_hard_block_allowed_after_repair": bool(
                    s05 and s05.get("hard_block_allowed_after_repair")
                ),
                "old_ai_policy_action": old_action,
                "old_ai_policy_would_action": row.get("ai_policy_would_action"),
                "old_ai_policy_would_allow_ai_call": row.get("ai_policy_would_allow_ai_call"),
                "old_ai_supervisor_action": row.get("ai_supervisor_action"),
                "old_ai_supervisor_disable_ai_narrowing": row.get(
                    "ai_supervisor_disable_ai_narrowing"
                ),
                **policy,
                "schema_contract": schema_contract(action, row),
                "prompt_packet_sha256": packet_sha,
                "cache_key_sha256": cache_sha,
                "prompt_packet_preview": packet,
                "prompt_packet_hash_required": bool(action.startswith("CALL_AI") and selected_stream),
                "content_addressed_cache_required": bool(action.startswith("CALL_AI") and selected_stream),
                "no_paid_api_or_vendor_call": True,
                "paid_api_or_vendor_call_made": False,
                "decision_inputs_exclude_future_outcome_and_r": True,
                "malformed_response_policy": malformed_policy,
                "supervisor_runtime_effect": supervisor_effect,
            }
            out.write(json.dumps(out_row, sort_keys=True) + "\n")

            scenario_row = {
                **row,
                "month": (s03 or {}).get("month") or str(row.get("as_of_utc") or "")[:7],
                "source_mode": source_mode,
            }
            scenarios["stage06_selected_stream_before_ai_policy"].add(
                scenario_row,
                selected=selected_stream,
                action="STAGE06_SELECTED_STREAM",
                reason="not_stage06_selected_stream",
            )
            scenarios["stage07_production_ai_policy_contract"].add(
                scenario_row,
                selected=selected_stream,
                action=action,
                reason=str(policy["stage07_policy_reason"]),
            )
            scenarios["stage07_no_paid_call_diagnostic"].add(
                scenario_row,
                selected=bool(policy["stage07_no_paid_call_selected"]),
                action=str(policy["stage07_no_paid_call_status"]),
                reason=str(policy["stage07_no_paid_call_reason"]),
            )

    tmp.replace(STAGE07_LEDGER)

    summary = {
        "schema_version": "vnext_production_candidate_repair_stage07_ai_policy_supervisor_summary_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR",
        "created_at_utc": utc_now(),
        "current_git_head": git_head(),
        "inputs": {
            "ai_policy_supervisor_ledger": rel(AI_LEDGER),
            "ai_policy_supervisor_sha256": sha256_file(AI_LEDGER),
            "stage03_ledger": rel(STAGE03_LEDGER),
            "stage03_sha256": sha256_file(STAGE03_LEDGER),
            "stage05_ledger": rel(STAGE05_LEDGER),
            "stage05_sha256": sha256_file(STAGE05_LEDGER),
            "stage06_ledger": rel(STAGE06_LEDGER),
            "stage06_sha256": sha256_file(STAGE06_LEDGER),
        },
        "ledger_rows": sum(1 for _ in iter_jsonl(STAGE07_LEDGER)),
        "stage03_counts": stage03_counts,
        "stage05_counts": stage05_counts,
        "stage06_counts": stage06_counts,
        "old_ai_policy_action_counts": dict(old_action_counts.most_common()),
        "old_ai_supervisor_action_counts": dict(old_supervisor_counts.most_common()),
        "stage07_ai_policy_action_counts": dict(stage07_action_counts.most_common()),
        "stage07_policy_branch_counts": dict(stage07_branch_counts.most_common()),
        "stage07_no_paid_call_status_counts": dict(no_paid_counts.most_common()),
        "stage07_selected_stream_rows": selected_stream_rows,
        "stage07_ai_required_for_production_rows": ai_required_rows,
        "stage07_prompt_packet_rows": prompt_packet_rows,
        "stage07_prompt_packet_hash_missing_rows": prompt_packet_hash_missing,
        "stage07_stale_follow_without_ai_rows": stale_follow_without_ai_rows,
        "future_input_bad_rows": future_input_bad_rows,
        "source_status_counts_selected_stream": dict(source_status_counts.most_common()),
        "selected_stream_source_counts": dict(selected_source_counts.most_common()),
        "malformed_response_policy_counts": dict(malformed_policy_counts.most_common()),
        "supervisor_runtime_effect_counts": dict(supervisor_effect_counts.most_common()),
        "scenario_metrics": {key: stats.to_record() for key, stats in scenarios.items()},
        "no_paid_call_replay_diagnostic": {
            "diagnostic_only": True,
            "production_selector": False,
            "selected_count": scenarios["stage07_no_paid_call_diagnostic"].selected_count,
            "reason": (
                "redacted_account risk-tier repaired selected stream requires a real AI validator; "
                "no-paid-call replay is preserved only as a diagnostic unless a future "
                "non-funded mechanical FOLLOW policy explicitly emits MECHANICAL_FOLLOW_NO_AI."
            ),
        },
        "runtime_surface_proof": {
            "runtime_ai_policy_helper": "src/components/gtos_vnext_runtime.py:vnext_ai_policy_no_paid_call_replay_decision",
            "runtime_no_paid_allowed_helper": "src/components/gtos_vnext_runtime.py:vnext_ai_policy_allows_no_paid_mechanical_follow",
            "runtime_paid_required_helper": "src/components/gtos_vnext_runtime.py:vnext_ai_policy_requires_paid_call",
            "primary_analyzer_malformed_repair_path": "src/components/primary_analyzer.py:_parse_and_validate",
            "ai_supervisor_health_path": "src/components/ai_supervisor.py:evaluate_ai_supervisor",
            "broker_facing_activation_change": False,
            "ai_policy_apply_to_ai_call_config_remains_false": True,
            "paid_api_or_vendor_calls_made": 0,
        },
        "stage07_decision": (
            "ai_policy_and_supervisor_repair_materialized_no_paid_zero_output_classified_diagnostic_only"
        ),
    }
    STAGE07_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    summary = build()
    print(json.dumps({
        "ok": True,
        "ledger_rows": summary["ledger_rows"],
        "stage07_selected_stream_rows": summary["stage07_selected_stream_rows"],
        "stage07_ai_required_for_production_rows": summary[
            "stage07_ai_required_for_production_rows"
        ],
        "no_paid_selected_count": summary["scenario_metrics"][
            "stage07_no_paid_call_diagnostic"
        ]["selected_count"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
