"""Probability Debate-Team Engine V4.

Deterministic V4 arbitration for competing trade/lifecycle actions.  This
module does not call external services, place orders, mutate broker state, or
change live execution unless a caller separately enables apply-to-execution in
configuration.
"""

from __future__ import annotations

import json
import logging
import math
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

ProbabilityAction = Literal[
    "long",
    "short",
    "no-trade",
    "wait",
    "scale",
    "reduce",
    "close",
    "reverse",
]

DebateStance = Literal["FOLLOW", "AVOID", "MIXED", "DIRECT"]

ALL_ACTIONS: tuple[ProbabilityAction, ...] = (
    "long",
    "short",
    "no-trade",
    "wait",
    "scale",
    "reduce",
    "close",
    "reverse",
)
RISK_ACTIONS = {"long", "short", "scale", "reverse"}
MANAGEMENT_ACTIONS = {"scale", "reduce", "close", "reverse"}
CAPITAL_PRESERVING_ACTIONS = {"no-trade", "wait", "reduce", "close"}
DEFAULT_REQUIRED_SOURCE_FAMILIES = (
    "selector",
    "market_state",
    "cost",
    "lifecycle",
    "source_completeness",
)
DEFAULT_LOG_PATH = "shadow_logs/probability_debate_team_engine_v4.jsonl"
SCHEMA_VERSION = "probability_debate_team_engine_v4"
FORBIDDEN_SOURCE_EVIDENCE_TOKENS = (
    "actual",
    "broker_real_cash",
    "broker_real_pnl",
    "exact_r",
    "final_r",
    "hindsight",
    "outcome",
    "post_decision",
    "realized",
    "result_row",
    "validation_result",
)


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _clamp(value: Any, low: float = 0.0, high: float = 1.0, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if not math.isfinite(number):
        number = default
    return max(low, min(high, number))


def _positive_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return max(0.0, number)


def _logit(probability: float) -> float:
    p = _clamp(probability, 0.001, 0.999, 0.5)
    return math.log(p / (1.0 - p))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, value))))


def _normalize_direction(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if text in {"LONG", "BUY", "BULL", "BULLISH"}:
        return "LONG"
    if text in {"SHORT", "SELL", "BEAR", "BEARISH"}:
        return "SHORT"
    return None


def _normalize_action(value: Any) -> ProbabilityAction | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace("_", "-")
    aliases = {
        "buy": "long",
        "bull": "long",
        "bullish": "long",
        "sell": "short",
        "bear": "short",
        "bearish": "short",
        "notrade": "no-trade",
        "no_trade": "no-trade",
        "none": "no-trade",
        "hold": "wait",
        "hold-existing": "wait",
        "stand-aside": "no-trade",
        "scale-in": "scale",
        "reduce-existing": "reduce",
        "close-existing": "close",
        "close-and-reverse": "reverse",
    }
    text = aliases.get(text, text)
    if text in ALL_ACTIONS:
        return text  # type: ignore[return-value]
    return None


def _source_contract_violation(evidence_class: Any) -> str | None:
    text = str(evidence_class or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not text:
        return "missing_evidence_class"
    for token in FORBIDDEN_SOURCE_EVIDENCE_TOKENS:
        if token in {"broker_real_cash", "broker_real_pnl"} and (
            f"not_{token}" in text or "not_broker_real" in text
        ):
            continue
        if token in text:
            return f"forbidden_future_or_result_evidence_class:{token}"
    return None


def _action_from_direction(direction: Any) -> ProbabilityAction | None:
    normalized = _normalize_direction(direction)
    if normalized == "LONG":
        return "long"
    if normalized == "SHORT":
        return "short"
    return None


def _runtime_cfg(config: dict[str, Any] | None) -> dict[str, Any]:
    runtime = (config or {}).get("gtos_vnext_runtime", {}) or {}
    cfg = runtime.get("probability_debate_team_engine_v4", {}) or {}
    return cfg if isinstance(cfg, dict) else {}


@dataclass(frozen=True)
class ProbabilityDebateSource:
    """One source-bound input to the V4 debate engine."""

    source_id: str
    source_family: str
    stance: DebateStance
    action: ProbabilityAction | None = None
    direction: str | None = None
    strength: float = 0.0
    confidence: float = 0.0
    reliability: float = 0.0
    freshness: float = 1.0
    source_completeness: float = 0.0
    cost_sensitivity: float = 0.0
    evidence_class: str = "source_bound_runtime_evidence"
    conflict_reason: str = ""
    invalidation_type: str = ""
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    as_of_utc: str | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any], *, fallback_id: str) -> "ProbabilityDebateSource":
        stance_text = str(
            payload.get("stance")
            or payload.get("decision")
            or payload.get("source_decision")
            or "DIRECT"
        ).strip().upper()
        if stance_text not in {"FOLLOW", "AVOID", "MIXED", "DIRECT"}:
            stance_text = "DIRECT"
        direction = _normalize_direction(payload.get("direction") or payload.get("side"))
        action = _normalize_action(payload.get("action") or payload.get("candidate_action"))
        if action is None and stance_text == "FOLLOW":
            action = _action_from_direction(direction)
        if action is None and stance_text == "AVOID":
            action = "no-trade"
        if action is None and stance_text == "MIXED":
            action = "wait"
        missing = payload.get("missing_fields") or ()
        if isinstance(missing, str):
            missing_fields = (missing,)
        else:
            missing_fields = tuple(str(item) for item in missing if item)
        return cls(
            source_id=str(payload.get("source_id") or payload.get("id") or fallback_id),
            source_family=str(payload.get("source_family") or payload.get("family") or "unknown"),
            stance=stance_text,  # type: ignore[arg-type]
            action=action,
            direction=direction,
            strength=_clamp(payload.get("strength"), default=0.0),
            confidence=_clamp(payload.get("confidence"), default=0.0),
            reliability=_clamp(payload.get("reliability"), default=0.0),
            freshness=_clamp(payload.get("freshness"), default=1.0),
            source_completeness=_clamp(payload.get("source_completeness"), default=0.0),
            cost_sensitivity=_clamp(payload.get("cost_sensitivity"), default=0.0),
            evidence_class=str(payload.get("evidence_class") or "source_bound_runtime_evidence"),
            conflict_reason=str(payload.get("conflict_reason") or ""),
            invalidation_type=str(payload.get("invalidation_type") or ""),
            missing_fields=missing_fields,
            as_of_utc=payload.get("as_of_utc"),
        )

    @property
    def usable_weight(self) -> float:
        if self.source_contract_violation:
            return 0.0
        base = self.strength * self.confidence * self.reliability * self.freshness
        completeness = 0.25 + 0.75 * self.source_completeness
        cost_drag = 1.0 - (0.35 * self.cost_sensitivity)
        return _clamp(base * completeness * cost_drag, 0.0, 1.5, 0.0)

    @property
    def source_contract_violation(self) -> str | None:
        return _source_contract_violation(self.evidence_class)

    def to_record(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_family": self.source_family,
            "stance": self.stance,
            "action": self.action,
            "direction": self.direction,
            "strength": self.strength,
            "confidence": self.confidence,
            "reliability": self.reliability,
            "freshness": self.freshness,
            "source_completeness": self.source_completeness,
            "cost_sensitivity": self.cost_sensitivity,
            "evidence_class": self.evidence_class,
            "conflict_reason": self.conflict_reason,
            "invalidation_type": self.invalidation_type,
            "missing_fields": list(self.missing_fields),
            "as_of_utc": self.as_of_utc,
            "source_contract_status": (
                "source_contract_violation"
                if self.source_contract_violation
                else "predecision_source_allowed"
            ),
            "source_contract_violation": self.source_contract_violation,
            "usable_weight": self.usable_weight,
        }


@dataclass(frozen=True)
class ProbabilityThesis:
    """Numeric thesis for one V4 action."""

    action: ProbabilityAction
    direction: str | None
    probability: float
    uncalibrated_probability: float
    ev_r: float
    reward_r: float
    loss_r: float
    cost_r: float
    uncertainty: float
    missing_source_penalty: float
    confidence_calibration: dict[str, Any]
    source_completeness: float
    evidence_class: str
    support: float
    opposition: float
    disagreement_state: str
    vetoes: tuple[str, ...] = field(default_factory=tuple)
    source_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def selected_allowed(self) -> bool:
        return not self.vetoes

    @property
    def selection_score(self) -> float:
        veto_penalty = 10.0 if self.vetoes else 0.0
        return self.ev_r - self.uncertainty - self.missing_source_penalty - veto_penalty

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "direction": self.direction,
            "probability": self.probability,
            "uncalibrated_probability": self.uncalibrated_probability,
            "EV": self.ev_r,
            "ev_r": self.ev_r,
            "reward_r": self.reward_r,
            "loss_r": self.loss_r,
            "cost_r": self.cost_r,
            "uncertainty": self.uncertainty,
            "missing_source_penalty": self.missing_source_penalty,
            "confidence_calibration": self.confidence_calibration,
            "source_completeness": self.source_completeness,
            "evidence_class": self.evidence_class,
            "support": self.support,
            "opposition": self.opposition,
            "disagreement_state": self.disagreement_state,
            "vetoes": list(self.vetoes),
            "selected_allowed": self.selected_allowed,
            "selection_score": self.selection_score,
            "source_ids": list(self.source_ids),
        }


@dataclass(frozen=True)
class ProbabilityDebateDecision:
    """Final V4 debate-team decision packet."""

    enabled: bool
    apply_to_execution: bool
    selected_action: ProbabilityAction
    selected_direction: str | None
    selected_thesis: ProbabilityThesis
    theses: tuple[ProbabilityThesis, ...]
    ranked_actions: tuple[ProbabilityAction, ...]
    rejected_alternatives: tuple[dict[str, Any], ...]
    source_summary: dict[str, Any]
    debate_controls: dict[str, Any]
    runtime_disposition: str
    reason: str
    artifact_paths: tuple[str, ...] = field(default_factory=tuple)

    def to_record(self) -> dict[str, Any]:
        record = {
            "schema_version": SCHEMA_VERSION,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "selected_action": self.selected_action,
            "selected_direction": self.selected_direction,
            "selected_thesis": self.selected_thesis.to_record(),
            "theses": [thesis.to_record() for thesis in self.theses],
            "ranked_actions": list(self.ranked_actions),
            "rejected_alternatives": list(self.rejected_alternatives),
            "source_summary": self.source_summary,
            "debate_controls": self.debate_controls,
            "runtime_disposition": self.runtime_disposition,
            "reason": self.reason,
            "artifact_paths": list(self.artifact_paths),
            "broker_runtime_change_status": False,
            "validation_result_status": False,
            "outcome_result_rows_status": False,
        }
        source_material = {
            "source_summary": record["source_summary"],
            "selected_action": record["selected_action"],
            "ranked_actions": record["ranked_actions"],
            "thesis_source_ids": {
                thesis["action"]: thesis["source_ids"]
                for thesis in record["theses"]
            },
        }
        record["source_event_hash_sha256"] = _stable_sha256(source_material)
        record["field_group_statuses"] = {
            "sources": {
                "status": (
                    "source_bound"
                    if record["source_summary"].get("source_count", 0) > 0
                    else "source_gap"
                ),
                "source_count": record["source_summary"].get("source_count", 0),
                "missing_source_families": record["source_summary"].get(
                    "missing_source_families", []
                ),
                "missing_field_count": record["source_summary"].get(
                    "missing_field_count", 0
                ),
            },
            "theses": {
                "status": "all_actions_materialized",
                "action_count": len(record["theses"]),
                "ranked_actions": record["ranked_actions"],
            },
            "selected_action": {
                "status": "bound",
                "selected_action": record["selected_action"],
                "selected_direction": record["selected_direction"],
            },
        }
        record["packet_hash_sha256"] = _stable_sha256(record)
        return record


def _default_disabled_decision(config: dict[str, Any] | None) -> ProbabilityDebateDecision:
    thesis = ProbabilityThesis(
        action="wait",
        direction=None,
        probability=0.0,
        uncalibrated_probability=0.0,
        ev_r=0.0,
        reward_r=0.0,
        loss_r=0.0,
        cost_r=0.0,
        uncertainty=1.0,
        missing_source_penalty=1.0,
        confidence_calibration={
            "method": "disabled",
            "calibration_source_status": "engine_disabled_by_config",
        },
        source_completeness=0.0,
        evidence_class="production_code_integration_disabled_by_config",
        support=0.0,
        opposition=0.0,
        disagreement_state="disabled",
        vetoes=("engine_disabled_by_config",),
    )
    cfg = _runtime_cfg(config)
    return ProbabilityDebateDecision(
        enabled=False,
        apply_to_execution=False,
        selected_action="wait",
        selected_direction=None,
        selected_thesis=thesis,
        theses=(thesis,),
        ranked_actions=("wait",),
        rejected_alternatives=(),
        source_summary={"source_count": 0, "required_source_families": []},
        debate_controls={"engine_status": "disabled"},
        runtime_disposition=str(cfg.get("runtime_disposition") or "disabled_by_config"),
        reason="probability_debate_team_engine_v4_disabled",
    )


class ProbabilityDebateTeamEngineV4:
    """Deterministic numeric thesis and action-arbitration engine."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.cfg = _runtime_cfg(config)

    def evaluate(self, context: dict[str, Any]) -> ProbabilityDebateDecision:
        if not bool(self.cfg.get("enabled", False)):
            return _default_disabled_decision(self.config)

        sources = self._sources(context)
        required_families = tuple(
            str(item)
            for item in self.cfg.get(
                "required_source_families",
                DEFAULT_REQUIRED_SOURCE_FAMILIES,
            )
        )
        source_summary = self._source_summary(sources, required_families)
        support, opposition, action_sources, disagreement_load = self._support_tables(sources)
        theses = tuple(
            self._build_thesis(
                action=action,
                context=context,
                support=support[action],
                opposition=opposition[action],
                source_ids=tuple(action_sources[action]),
                source_summary=source_summary,
                disagreement_load=disagreement_load,
            )
            for action in ALL_ACTIONS
        )
        ranked = tuple(
            thesis.action
            for thesis in sorted(theses, key=lambda item: item.selection_score, reverse=True)
        )
        selected = next((thesis for thesis in theses if thesis.action == ranked[0]), theses[0])
        rejected = tuple(
            {
                "action": thesis.action,
                "direction": thesis.direction,
                "probability": thesis.probability,
                "EV": thesis.ev_r,
                "selection_score": thesis.selection_score,
                "vetoes": list(thesis.vetoes),
                "rejection_reason": self._rejection_reason(thesis, selected),
            }
            for thesis in sorted(theses, key=lambda item: item.selection_score, reverse=True)
            if thesis.action != selected.action
        )
        reason = (
            f"selected_{selected.action}_prob={selected.probability:.3f}_"
            f"ev={selected.ev_r:.3f}_uncertainty={selected.uncertainty:.3f}"
        )
        return ProbabilityDebateDecision(
            enabled=True,
            apply_to_execution=bool(self.cfg.get("apply_to_execution", False)),
            selected_action=selected.action,
            selected_direction=selected.direction,
            selected_thesis=selected,
            theses=theses,
            ranked_actions=ranked,
            rejected_alternatives=rejected,
            source_summary=source_summary,
            debate_controls=self._debate_controls(context, source_summary, disagreement_load),
            runtime_disposition=str(self.cfg.get("runtime_disposition") or "active_v4_authority"),
            reason=reason,
            artifact_paths=tuple(str(path) for path in self.cfg.get("artifact_paths", ())),
        )

    def _sources(self, context: dict[str, Any]) -> tuple[ProbabilityDebateSource, ...]:
        raw_sources = context.get("sources") or context.get("source_signals") or ()
        sources: list[ProbabilityDebateSource] = []
        for index, raw in enumerate(raw_sources):
            if isinstance(raw, ProbabilityDebateSource):
                sources.append(raw)
            elif isinstance(raw, dict):
                sources.append(ProbabilityDebateSource.from_mapping(raw, fallback_id=f"source_{index:03d}"))
        return tuple(sources)

    def _source_summary(
        self,
        sources: tuple[ProbabilityDebateSource, ...],
        required_families: tuple[str, ...],
    ) -> dict[str, Any]:
        allowed_sources = tuple(
            source for source in sources if source.source_contract_violation is None
        )
        present_families = {
            source.source_family
            for source in allowed_sources
            if source.source_completeness >= 0.25 or source.usable_weight > 0
        }
        missing_families = tuple(
            family for family in required_families if family not in present_families
        )
        avg_completeness = (
            sum(source.source_completeness for source in allowed_sources) / len(allowed_sources)
            if allowed_sources else 0.0
        )
        avg_reliability = (
            sum(source.reliability for source in allowed_sources) / len(allowed_sources)
            if allowed_sources else 0.0
        )
        invalid_source_fields = [
            f"sources.{source.source_id}.evidence_class:{source.source_contract_violation}"
            for source in sources
            if source.source_contract_violation
        ]
        missing_field_count = (
            sum(len(source.missing_fields) for source in sources)
            + len(invalid_source_fields)
        )
        family_penalty = _positive_float(self.cfg.get("missing_source_family_penalty"), 0.08)
        field_penalty = _positive_float(self.cfg.get("missing_field_penalty"), 0.015)
        completeness_penalty = _positive_float(
            self.cfg.get("source_completeness_penalty"),
            0.18,
        ) * (1.0 - avg_completeness)
        missing_source_penalty = min(
            _positive_float(self.cfg.get("max_missing_source_penalty"), 0.75),
            len(missing_families) * family_penalty
            + missing_field_count * field_penalty
            + completeness_penalty,
        )
        return {
            "source_count": len(sources),
            "required_source_families": list(required_families),
            "present_source_families": sorted(present_families),
            "missing_source_families": list(missing_families),
            "missing_field_count": missing_field_count,
            "invalid_source_evidence_class_fields": invalid_source_fields,
            "avg_source_completeness": avg_completeness,
            "avg_reliability": avg_reliability,
            "missing_source_penalty": missing_source_penalty,
            "sources": [source.to_record() for source in sources],
        }

    def _support_tables(
        self,
        sources: tuple[ProbabilityDebateSource, ...],
    ) -> tuple[
        dict[ProbabilityAction, float],
        dict[ProbabilityAction, float],
        dict[ProbabilityAction, list[str]],
        float,
    ]:
        support: dict[ProbabilityAction, float] = defaultdict(float)
        opposition: dict[ProbabilityAction, float] = defaultdict(float)
        action_sources: dict[ProbabilityAction, list[str]] = defaultdict(list)
        disagreement_load = 0.0
        for source in sources:
            weight = source.usable_weight
            action = source.action or _action_from_direction(source.direction) or "wait"
            if source.stance == "FOLLOW":
                support[action] += weight
                action_sources[action].append(source.source_id)
                if action == "long":
                    opposition["short"] += weight * 0.75
                    opposition["no-trade"] += weight * 0.25
                elif action == "short":
                    opposition["long"] += weight * 0.75
                    opposition["no-trade"] += weight * 0.25
            elif source.stance == "AVOID":
                support["no-trade"] += weight * 0.85
                support["wait"] += weight * 0.35
                action_sources["no-trade"].append(source.source_id)
                if source.invalidation_type in {"stale_thesis", "lifecycle", "opposite_signal"}:
                    support["reduce"] += weight * 0.35
                    support["close"] += weight * 0.35
                    action_sources["reduce"].append(source.source_id)
                    action_sources["close"].append(source.source_id)
                for risk_action in RISK_ACTIONS:
                    opposition[risk_action] += weight
            elif source.stance == "MIXED":
                support["wait"] += weight * 0.9
                support["no-trade"] += weight * 0.45
                opposition["long"] += weight * 0.35
                opposition["short"] += weight * 0.35
                action_sources["wait"].append(source.source_id)
                disagreement_load += weight
                if source.action:
                    support[source.action] += weight * 0.25
                    action_sources[source.action].append(source.source_id)
            else:
                support[action] += weight
                action_sources[action].append(source.source_id)
        return support, opposition, action_sources, disagreement_load

    def _build_thesis(
        self,
        *,
        action: ProbabilityAction,
        context: dict[str, Any],
        support: float,
        opposition: float,
        source_ids: tuple[str, ...],
        source_summary: dict[str, Any],
        disagreement_load: float,
    ) -> ProbabilityThesis:
        base_prior = self._action_prior(action, context)
        raw_probability = _sigmoid(
            _logit(base_prior)
            + support * 1.65
            - opposition * 1.45
            - source_summary["missing_source_penalty"] * self._missing_penalty_multiplier(action)
            - self._action_cost_penalty(action, context)
        )
        reliability = _clamp(source_summary.get("avg_reliability"), default=0.0)
        calibrated_probability = self._calibrate_probability(raw_probability, reliability)
        reward_r, loss_r, cost_r = self._reward_loss_cost(action, context)
        uncertainty = self._uncertainty(
            action=action,
            source_summary=source_summary,
            disagreement_load=disagreement_load,
            probability=calibrated_probability,
        )
        ev_r = (
            calibrated_probability * reward_r
            - (1.0 - calibrated_probability) * loss_r
            - cost_r
            - uncertainty * _positive_float(self.cfg.get("uncertainty_ev_penalty"), 0.20)
        )
        direction = self._thesis_direction(action, context)
        disagreement_state = self._disagreement_state(disagreement_load, support, opposition)
        vetoes = self._vetoes(
            action=action,
            direction=direction,
            probability=calibrated_probability,
            ev_r=ev_r,
            context=context,
            source_summary=source_summary,
            disagreement_state=disagreement_state,
            support=support,
            opposition=opposition,
        )
        return ProbabilityThesis(
            action=action,
            direction=direction,
            probability=calibrated_probability,
            uncalibrated_probability=raw_probability,
            ev_r=ev_r,
            reward_r=reward_r,
            loss_r=loss_r,
            cost_r=cost_r,
            uncertainty=uncertainty,
            missing_source_penalty=source_summary["missing_source_penalty"],
            confidence_calibration={
                "method": "reliability_weighted_shrinkage_to_base_rate",
                "reliability_weight": reliability,
                "calibration_source_status": (
                    "runtime_reliability_prior_no_outcome_calibration_claim"
                ),
                "required_validation_metrics": ["Brier", "ECE", "reliability_bins", "logloss"],
                "uncalibrated_probability": raw_probability,
                "calibrated_probability": calibrated_probability,
            },
            source_completeness=_clamp(source_summary.get("avg_source_completeness"), default=0.0),
            evidence_class="production_code_integration_source_bound_runtime_thesis",
            support=support,
            opposition=opposition,
            disagreement_state=disagreement_state,
            vetoes=tuple(vetoes),
            source_ids=source_ids,
        )

    def _action_prior(self, action: ProbabilityAction, context: dict[str, Any]) -> float:
        priors = self.cfg.get("action_priors", {}) or {}
        if isinstance(priors, dict) and action in priors:
            return _clamp(priors[action], 0.01, 0.99, 0.35)
        defaults: dict[ProbabilityAction, float] = {
            "long": 0.34,
            "short": 0.34,
            "no-trade": 0.52,
            "wait": 0.44,
            "scale": 0.22,
            "reduce": 0.34,
            "close": 0.32,
            "reverse": 0.18,
        }
        candidate_action = _action_from_direction(context.get("candidate_direction"))
        if candidate_action == action:
            return min(0.99, defaults[action] + 0.08)
        return defaults[action]

    def _missing_penalty_multiplier(self, action: ProbabilityAction) -> float:
        if action in RISK_ACTIONS:
            return _positive_float(self.cfg.get("risk_action_missing_penalty_multiplier"), 1.4)
        if action in CAPITAL_PRESERVING_ACTIONS:
            return _positive_float(self.cfg.get("capital_preserving_missing_penalty_multiplier"), 0.55)
        return 1.0

    def _action_cost_penalty(self, action: ProbabilityAction, context: dict[str, Any]) -> float:
        if action not in RISK_ACTIONS:
            return 0.0
        cost_r = _positive_float(context.get("cost_r") or context.get("estimated_cost_r"), 0.0)
        return cost_r * _positive_float(self.cfg.get("cost_probability_penalty_multiplier"), 0.7)

    def _calibrate_probability(self, raw_probability: float, reliability: float) -> float:
        shrinkage_floor = _clamp(self.cfg.get("calibration_shrinkage_floor"), default=0.35)
        weight = max(shrinkage_floor, reliability)
        base_rate = _clamp(self.cfg.get("base_rate_probability"), default=0.50)
        return _clamp((raw_probability * weight) + (base_rate * (1.0 - weight)))

    def _reward_loss_cost(
        self,
        action: ProbabilityAction,
        context: dict[str, Any],
    ) -> tuple[float, float, float]:
        rr = _positive_float(
            context.get("risk_reward_ratio")
            or context.get("reward_r")
            or context.get("target_r"),
            1.5,
        )
        cost_r = _positive_float(context.get("cost_r") or context.get("estimated_cost_r"), 0.0)
        if action in {"long", "short", "reverse"}:
            return rr, 1.0, cost_r
        if action == "scale":
            return max(0.0, rr * 0.65), 1.0, cost_r
        if action == "reduce":
            return _positive_float(context.get("stale_thesis_avoid_loss_r"), 0.25), 0.05, 0.0
        if action == "close":
            return _positive_float(context.get("close_preserved_r"), 0.20), 0.05, 0.0
        if action == "wait":
            return _positive_float(context.get("wait_information_value_r"), 0.05), 0.03, 0.0
        return 0.0, _positive_float(context.get("opportunity_cost_r"), 0.02), 0.0

    def _uncertainty(
        self,
        *,
        action: ProbabilityAction,
        source_summary: dict[str, Any],
        disagreement_load: float,
        probability: float,
    ) -> float:
        base = _positive_float(self.cfg.get("base_uncertainty"), 0.08)
        completeness_component = (1.0 - _clamp(source_summary.get("avg_source_completeness"), default=0.0)) * 0.30
        reliability_component = (1.0 - _clamp(source_summary.get("avg_reliability"), default=0.0)) * 0.18
        disagreement_component = min(0.35, disagreement_load * 0.30)
        probability_component = (1.0 - abs(probability - 0.5) * 2.0) * 0.12
        risk_multiplier = 1.15 if action in RISK_ACTIONS else 0.85
        return _clamp(
            (base + completeness_component + reliability_component + disagreement_component + probability_component)
            * risk_multiplier,
            0.0,
            1.0,
            0.5,
        )

    def _thesis_direction(self, action: ProbabilityAction, context: dict[str, Any]) -> str | None:
        if action == "long":
            return "LONG"
        if action == "short":
            return "SHORT"
        if action in {"scale", "reduce", "close"}:
            return _normalize_direction(
                context.get("open_position_direction") or context.get("candidate_direction")
            )
        if action == "reverse":
            current = _normalize_direction(context.get("open_position_direction"))
            if current == "LONG":
                return "SHORT"
            if current == "SHORT":
                return "LONG"
            return _normalize_direction(context.get("candidate_direction"))
        return None

    def _vetoes(
        self,
        *,
        action: ProbabilityAction,
        direction: str | None,
        probability: float,
        ev_r: float,
        context: dict[str, Any],
        source_summary: dict[str, Any],
        disagreement_state: str,
        support: float,
        opposition: float,
    ) -> list[str]:
        vetoes: list[str] = []
        min_source_completeness = _clamp(self.cfg.get("min_source_completeness"), default=0.45)
        source_completeness = _clamp(source_summary.get("avg_source_completeness"), default=0.0)
        missing_families = set(source_summary.get("missing_source_families") or ())
        if action in RISK_ACTIONS:
            if direction is None:
                vetoes.append("risk_action_requires_direction")
            if source_completeness < min_source_completeness:
                vetoes.append("source_completeness_below_risk_action_threshold")
            if bool(self.cfg.get("risk_actions_require_required_source_families", True)):
                for family in sorted(missing_families):
                    vetoes.append(f"risk_action_requires_{family}_source")
            if bool(self.cfg.get("risk_actions_require_cost_source", True)) and "cost" in missing_families:
                if "risk_action_requires_cost_source" not in vetoes:
                    vetoes.append("risk_action_requires_cost_source")
            if probability < _clamp(self.cfg.get("min_trade_probability"), default=0.55):
                vetoes.append("probability_below_trade_threshold")
            if ev_r < float(self.cfg.get("min_trade_ev_r", 0.0)):
                vetoes.append("EV_below_trade_threshold")
            if disagreement_state == "high_structured_disagreement":
                vetoes.append("risk_action_blocked_by_high_structured_disagreement")
            mixed_veto_ratio = _positive_float(
                self.cfg.get("mixed_disagreement_risk_veto_ratio"),
                0.45,
            )
            if (
                disagreement_state == "mixed_structured_disagreement"
                and support > 0.0
                and opposition / max(support, 0.001) >= mixed_veto_ratio
            ):
                vetoes.append("risk_action_blocked_by_mixed_structured_disagreement")
        if action == "scale" and not bool(context.get("ticket_bound_scale_in_allowed", False)):
            vetoes.append("scale_requires_ticket_bound_lifecycle_approval")
        if action in {"reduce", "close", "reverse"} and not bool(context.get("open_position_present", False)):
            vetoes.append(f"{action}_requires_open_position_snapshot")
        if action == "reverse" and not bool(context.get("close_reverse_lifecycle_allowed", False)):
            vetoes.append("reverse_requires_close_reverse_lifecycle_approval")
        if action == "wait" and probability < 0.05:
            vetoes.append("wait_probability_too_low")
        return vetoes

    @staticmethod
    def _disagreement_state(disagreement_load: float, support: float, opposition: float) -> str:
        if disagreement_load >= 0.50 or (support > 0.0 and opposition / max(support, 0.001) >= 0.75):
            return "high_structured_disagreement"
        if disagreement_load >= 0.20 or opposition > 0.0:
            return "mixed_structured_disagreement"
        return "low_disagreement"

    @staticmethod
    def _rejection_reason(thesis: ProbabilityThesis, selected: ProbabilityThesis) -> str:
        if thesis.vetoes:
            return "vetoed:" + ",".join(thesis.vetoes)
        if thesis.selection_score < selected.selection_score:
            return "lower_selection_score"
        return "not_selected_tie_break"

    def _debate_controls(
        self,
        context: dict[str, Any],
        source_summary: dict[str, Any],
        disagreement_load: float,
    ) -> dict[str, Any]:
        return {
            "actions_requiring_numeric_theses": list(ALL_ACTIONS),
            "debate_teams": [
                "bull thesis",
                "bear thesis",
                "no-trade thesis",
                "execution thesis",
                "cost/risk thesis",
                "lifecycle thesis",
                "source-completeness thesis",
            ],
            "FOLLOW_is_trade_permission": False,
            "AVOID_requires_invalidation_type": True,
            "MIXED_structured_disagreement": True,
            "missing_source_penalty_applied": source_summary["missing_source_penalty"],
            "disagreement_load": disagreement_load,
            "candidate_id": context.get("candidate_id"),
            "symbol": context.get("symbol"),
            "route_session": context.get("route_session") or context.get("kill_zone"),
        }


def _metric_sum(evidence: dict[str, Any], metric_name: str) -> float | None:
    try:
        value = ((evidence.get("metrics") or {}).get(metric_name) or {}).get("sum")
    except AttributeError:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def build_probability_debate_context_from_runtime(
    *,
    analysis: Any,
    raw_data: dict[str, Any] | None,
    vnext_decision: Any,
    symbol: str | None,
    source_symbol: str | None,
    kill_zone: str | None,
    record: dict[str, Any] | None = None,
    confidence_metrics: Any | None = None,
) -> dict[str, Any]:
    """Build a V4 debate context from the current runtime candidate path."""
    raw_data = raw_data if isinstance(raw_data, dict) else {}
    event = getattr(vnext_decision, "event", {}) or {}
    evidence = getattr(vnext_decision, "evidence", {}) or {}
    trade_params = getattr(analysis, "trade_parameters", None)
    direction = _normalize_direction(
        getattr(trade_params, "direction", None)
        or raw_data.get("direction")
        or raw_data.get("side")
        or event.get("side")
    )
    rr = _positive_float(
        getattr(trade_params, "risk_reward_ratio", None)
        or raw_data.get("risk_reward_ratio")
        or raw_data.get("rr")
        or 1.5,
        1.5,
    )
    effective_n = _metric_sum(evidence, "effective_n")
    cost_metric = _metric_sum(evidence, "cost_adjusted_simulated_r")
    proxy_metric = _metric_sum(evidence, "proxy_score")
    stress_metric = _metric_sum(evidence, "stress_simulated_r")
    cost_r = _positive_float(
        raw_data.get("selected_cell_pretrade_cost_r")
        or raw_data.get("decision_cost_r")
        or raw_data.get("estimated_cost_r")
        or raw_data.get("spread_r")
        or 0.0,
        0.0,
    )
    matched = bool(getattr(vnext_decision, "matched", False))
    decision_label = str(getattr(vnext_decision, "decision", "MIXED") or "MIXED").upper()
    reliability = _clamp((effective_n or 0.0) / 25.0, default=0.35 if matched else 0.15)
    strength = _clamp(abs(proxy_metric or stress_metric or cost_metric or 0.0) / 10.0, default=0.45 if matched else 0.15)
    source_complete = raw_data.get("source_complete")
    if source_complete is None:
        source_complete = raw_data.get("source_window_complete")
    source_completeness = 0.78 if source_complete is True else (0.45 if source_complete is not False else 0.20)
    sources: list[dict[str, Any]] = [
        {
            "source_id": "gtos_vnext_runtime_decision",
            "source_family": "selector",
            "stance": decision_label if decision_label in {"FOLLOW", "AVOID", "MIXED"} else "MIXED",
            "direction": direction,
            "strength": strength,
            "confidence": 0.72 if matched else 0.35,
            "reliability": reliability,
            "freshness": 1.0,
            "source_completeness": source_completeness,
            "cost_sensitivity": min(1.0, cost_r),
            "evidence_class": "production_code_runtime_evidence",
            "conflict_reason": str(getattr(vnext_decision, "reason", "") or ""),
            "missing_fields": [] if matched else ["matched_vnext_evidence"],
        },
        {
            "source_id": "runtime_source_completeness",
            "source_family": "source_completeness",
            "stance": "FOLLOW" if source_completeness >= 0.65 else "MIXED",
            "direction": direction,
            "strength": source_completeness,
            "confidence": source_completeness,
            "reliability": source_completeness,
            "freshness": 1.0,
            "source_completeness": source_completeness,
            "evidence_class": "runtime_source_completeness_evidence",
            "missing_fields": [] if source_completeness >= 0.65 else ["complete_source_window"],
        },
        {
            "source_id": "runtime_market_state",
            "source_family": "market_state",
            "stance": decision_label if decision_label in {"FOLLOW", "AVOID", "MIXED"} else "MIXED",
            "direction": direction,
            "strength": max(0.35, strength * 0.85),
            "confidence": 0.66 if matched else 0.32,
            "reliability": reliability,
            "freshness": 1.0,
            "source_completeness": source_completeness,
            "cost_sensitivity": min(1.0, cost_r),
            "evidence_class": "market_state_runtime_proxy_evidence",
            "conflict_reason": str(getattr(vnext_decision, "reason", "") or ""),
            "missing_fields": [] if source_completeness >= 0.65 else ["market_state_source_window"],
        },
    ]
    if cost_r > 0.0 or cost_metric is not None or raw_data.get("decision_spread_value_source_safe") is not None:
        cost_ok = cost_r <= _positive_float(raw_data.get("max_cost_r"), 0.20)
        sources.append(
            {
                "source_id": "pretrade_cost_source",
                "source_family": "cost",
                "stance": "FOLLOW" if cost_ok else "AVOID",
                "direction": direction,
                "strength": 0.70,
                "confidence": 0.70,
                "reliability": 0.65,
                "freshness": 1.0,
                "source_completeness": 0.70,
                "cost_sensitivity": min(1.0, cost_r),
                "evidence_class": "pretrade_cost_runtime_evidence",
                "invalidation_type": "cost_drag" if not cost_ok else "",
                "missing_fields": [],
            }
        )
    open_position_present = bool(raw_data.get("open_position_present"))
    if record:
        open_position_present = open_position_present or bool(
            ((record.get("decision_pipeline") or {}).get("same_symbol_lifecycle") or {}).get(
                "open_position_present"
            )
        )
    lifecycle_complete = source_completeness >= 0.65 or open_position_present
    sources.append(
        {
            "source_id": "same_symbol_lifecycle_snapshot",
            "source_family": "lifecycle",
            "stance": "DIRECT",
            "action": raw_data.get("same_symbol_lifecycle_action") or "wait",
            "direction": raw_data.get("open_position_direction") or direction,
            "strength": 0.65 if lifecycle_complete else 0.35,
            "confidence": 0.65 if lifecycle_complete else 0.35,
            "reliability": 0.65 if lifecycle_complete else 0.35,
            "freshness": 1.0,
            "source_completeness": 0.65 if lifecycle_complete else 0.25,
            "evidence_class": "ticket_bound_lifecycle_runtime_evidence",
            "missing_fields": [] if lifecycle_complete else ["same_symbol_lifecycle_snapshot"],
        }
    )
    if confidence_metrics is not None:
        grade = str(getattr(confidence_metrics, "confidence_grade", "") or "").upper()
        sources.append(
            {
                "source_id": "confidence_scorer_runtime",
                "source_family": "ai_confidence",
                "stance": "AVOID" if grade == "LOW" else ("MIXED" if grade == "MEDIUM" else "FOLLOW"),
                "direction": direction,
                "strength": 0.35,
                "confidence": 0.35 if grade == "LOW" else 0.55 if grade == "MEDIUM" else 0.70,
                "reliability": 0.45,
                "freshness": 1.0,
                "source_completeness": 0.55,
                "evidence_class": "confidence_scorer_runtime_evidence",
                "conflict_reason": f"confidence_grade={grade or 'UNKNOWN'}",
            }
        )
    return {
        "candidate_id": raw_data.get("candidate_id") or (record or {}).get("candidate_id"),
        "symbol": symbol or raw_data.get("symbol") or event.get("symbol"),
        "source_symbol": source_symbol or raw_data.get("source_symbol") or event.get("source_symbol"),
        "route_session": raw_data.get("route_session") or raw_data.get("session") or kill_zone,
        "kill_zone": kill_zone,
        "candidate_direction": direction,
        "risk_reward_ratio": rr,
        "cost_r": cost_r,
        "source_complete": source_complete,
        "open_position_present": open_position_present,
        "open_position_direction": raw_data.get("open_position_direction"),
        "ticket_bound_scale_in_allowed": bool(raw_data.get("ticket_bound_scale_in_allowed", False)),
        "close_reverse_lifecycle_allowed": bool(raw_data.get("close_reverse_lifecycle_allowed", False)),
        "sources": sources,
    }


def evaluate_probability_debate_team_v4(
    context: dict[str, Any],
    config: dict[str, Any] | None,
) -> ProbabilityDebateDecision:
    """Evaluate the V4 debate engine for a prepared context."""
    return ProbabilityDebateTeamEngineV4(config).evaluate(context)


def probability_debate_v4_execution_block_reason(
    decision: ProbabilityDebateDecision,
    config: dict[str, Any] | None,
) -> str | None:
    """Return the active V4 block reason if apply-to-execution is enabled."""
    if not decision.enabled or not decision.apply_to_execution:
        return None
    cfg = _runtime_cfg(config)
    if decision.selected_thesis.vetoes:
        return "probability_debate_v4_selected_thesis_veto"
    if decision.selected_action not in {"long", "short", "scale", "reverse"}:
        return f"probability_debate_v4_selected_{decision.selected_action}"
    if decision.selected_thesis.probability < _clamp(cfg.get("min_trade_probability"), default=0.55):
        return "probability_debate_v4_probability_below_trade_threshold"
    if decision.selected_thesis.ev_r < float(cfg.get("min_trade_ev_r", 0.0)):
        return "probability_debate_v4_EV_below_trade_threshold"
    return None


def attach_probability_debate_v4_to_record(
    record: dict[str, Any],
    decision: ProbabilityDebateDecision,
) -> dict[str, Any]:
    """Attach V4 debate output to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["probability_debate_team_engine_v4"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["probability_debate_v4_selected_action"] = decision.selected_action
    inst["probability_debate_v4_selected_probability"] = decision.selected_thesis.probability
    inst["probability_debate_v4_selected_ev_r"] = decision.selected_thesis.ev_r
    inst["probability_debate_v4_apply_to_execution"] = decision.apply_to_execution
    return record


def record_probability_debate_v4_decision(
    *,
    decision: ProbabilityDebateDecision,
    config: dict[str, Any] | None,
    phase: str,
    symbol: str | None,
    kill_zone: str | None,
    candle_time_utc: str | None = None,
    log_path: str | Path | None = None,
) -> None:
    """Append a V4 debate decision row without raising into runtime flow."""
    cfg = _runtime_cfg(config)
    if not bool(cfg.get("decision_log_enabled", True)):
        return
    path = Path(log_path or cfg.get("decision_log_path") or DEFAULT_LOG_PATH)
    row = {
        "schema_version": SCHEMA_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "symbol": symbol,
        "kill_zone": kill_zone,
        "candle_time_utc": candle_time_utc,
        "decision": decision.to_record(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception as exc:  # noqa: BLE001 - diagnostic logging cannot affect trading
        logger.warning("probability debate V4 decision log failed: %s", exc)


def calibration_metrics(
    rows: list[dict[str, Any]],
    *,
    probability_key: str = "probability",
    outcome_key: str = "outcome",
    bin_count: int = 10,
) -> dict[str, Any]:
    """Compute Brier, ECE, reliability bins, and logloss for sealed rows."""
    if bin_count <= 0:
        raise ValueError("bin_count must be positive")
    parsed: list[tuple[float, float]] = []
    for row in rows:
        if probability_key not in row or outcome_key not in row:
            continue
        p = _clamp(row.get(probability_key), default=0.5)
        outcome = row.get(outcome_key)
        if isinstance(outcome, str):
            outcome_text = outcome.strip().lower()
            if outcome_text in {"1", "true", "win", "success", "profitable"}:
                y = 1.0
            elif outcome_text in {"0", "false", "loss", "failure", "unprofitable"}:
                y = 0.0
            else:
                continue
        else:
            y = 1.0 if _positive_float(outcome, 0.0) >= 0.5 else 0.0
        parsed.append((p, y))
    if not parsed:
        return {
            "row_count": 0,
            "Brier": None,
            "ECE": None,
            "logloss": None,
            "reliability_bins": [],
            "status": "no_calibration_rows",
        }
    bins: list[list[tuple[float, float]]] = [[] for _ in range(bin_count)]
    for p, y in parsed:
        index = min(bin_count - 1, int(p * bin_count))
        bins[index].append((p, y))
    brier = sum((p - y) ** 2 for p, y in parsed) / len(parsed)
    logloss = sum(
        -(y * math.log(_clamp(p, 1e-12, 1.0 - 1e-12)) + (1 - y) * math.log(_clamp(1 - p, 1e-12, 1.0)))
        for p, y in parsed
    ) / len(parsed)
    reliability_bins = []
    ece = 0.0
    for index, bucket in enumerate(bins):
        if bucket:
            avg_p = sum(p for p, _ in bucket) / len(bucket)
            observed = sum(y for _, y in bucket) / len(bucket)
            contribution = (len(bucket) / len(parsed)) * abs(avg_p - observed)
        else:
            avg_p = None
            observed = None
            contribution = 0.0
        ece += contribution
        reliability_bins.append(
            {
                "bin": index,
                "lower": index / bin_count,
                "upper": (index + 1) / bin_count,
                "count": len(bucket),
                "avg_probability": avg_p,
                "observed_frequency": observed,
                "ece_contribution": contribution,
            }
        )
    return {
        "row_count": len(parsed),
        "Brier": brier,
        "ECE": ece,
        "logloss": logloss,
        "reliability_bins": reliability_bins,
        "status": "calibration_metrics_computed",
    }


__all__ = [
    "ALL_ACTIONS",
    "ProbabilityDebateDecision",
    "ProbabilityDebateSource",
    "ProbabilityDebateTeamEngineV4",
    "ProbabilityThesis",
    "attach_probability_debate_v4_to_record",
    "build_probability_debate_context_from_runtime",
    "calibration_metrics",
    "evaluate_probability_debate_team_v4",
    "probability_debate_v4_execution_block_reason",
    "record_probability_debate_v4_decision",
]
