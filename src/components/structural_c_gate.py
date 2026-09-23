"""Mechanical structural C-gate for pre-AI routing.

Session 13 prompt-optimization evidence showed that the useful AI signal was
the structural C-gate: clear H1 directional bias and M15 not opposing it. This
module makes that contract executable before the PrimaryAnalyzer call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class StructuralCGateDecision:
    enabled: bool
    apply_to_ai_call: bool
    action: str
    would_action: str
    reason: str
    bias: str = ""
    side: str = ""
    h1_direction: str = ""
    m15_direction: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "apply_to_ai_call": self.apply_to_ai_call,
            "action": self.action,
            "would_action": self.would_action,
            "reason": self.reason,
            "bias": self.bias,
            "side": self.side,
            "h1_direction": self.h1_direction,
            "m15_direction": self.m15_direction,
            "evidence": dict(self.evidence),
        }


def _cfg(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    block = config.get("structural_c_gate", {})
    return block if isinstance(block, Mapping) else {}


def _direction_from_mso(mso: Any, tf_name: str) -> str:
    tfs = getattr(mso, "timeframes", {}) if mso is not None else {}
    tf = tfs.get(tf_name) if isinstance(tfs, Mapping) else None
    structure = getattr(tf, "structure", None) if tf is not None else None
    return str(getattr(structure, "direction", "") or "unavailable").strip().lower()


def _direction_from_bias_or_mso(
    *,
    bias_result: Mapping[str, Any] | None,
    mso: Any,
    key: str,
    tf_name: str,
) -> str:
    if isinstance(bias_result, Mapping):
        value = bias_result.get(key)
        if value not in (None, ""):
            return str(value).strip().lower()
    return _direction_from_mso(mso, tf_name)


def _directional(value: str) -> bool:
    return value in {"bullish", "bearish"}


def _resolved_action(*, would_action: str, apply_to_ai_call: bool) -> str:
    return would_action if apply_to_ai_call else "ALLOW_AI"


def _side_for_bias(bias: str) -> str:
    if bias == "bullish":
        return "LONG"
    if bias == "bearish":
        return "SHORT"
    return ""


def evaluate_structural_c_gate(
    *,
    mso: Any,
    bias_result: Mapping[str, Any] | None,
    config: Mapping[str, Any] | None,
) -> StructuralCGateDecision:
    """Evaluate H1-bias/M15-non-opposition before the AI call."""
    block = _cfg(config)
    enabled = bool(block.get("enabled", False))
    apply_to_ai_call = bool(block.get("apply_to_ai_call", False))
    source_path = ".context/02_session_handoffs/13_apr13_prompt_optimization_T5_T8_handoff.md"
    source_line_no = 85
    evidence = {
        "source_path": source_path,
        "source_line_no": source_line_no,
        "t6_cgate_pass_wr_pct": float(block.get("t6_cgate_pass_wr_pct", 69.4)),
        "t6_cgate_pass_total_r": float(block.get("t6_cgate_pass_total_r", 44.2)),
        "q_score_correlation_r": float(block.get("q_score_correlation_r", -0.06)),
        "q_score_correlation_p": float(block.get("q_score_correlation_p", 0.574)),
        "policy": "h1_bias_m15_non_opposition_pre_ai_route",
    }
    if not enabled:
        return StructuralCGateDecision(
            enabled=False,
            apply_to_ai_call=False,
            action="ALLOW_AI",
            would_action="ALLOW_AI",
            reason="structural_c_gate_disabled",
            evidence=evidence,
        )

    deterministic_bias = ""
    if isinstance(bias_result, Mapping):
        deterministic_bias = str(bias_result.get("bias") or "").strip().lower()
    only_no_bias = bool(block.get("only_when_deterministic_bias_absent", True))
    d1 = _direction_from_bias_or_mso(
        bias_result=bias_result,
        mso=mso,
        key="d1",
        tf_name="D1",
    )
    h4 = _direction_from_bias_or_mso(
        bias_result=bias_result,
        mso=mso,
        key="h4",
        tf_name="H4",
    )
    h1 = _direction_from_bias_or_mso(
        bias_result=bias_result,
        mso=mso,
        key="h1",
        tf_name="H1",
    )
    m15 = _direction_from_bias_or_mso(
        bias_result=bias_result,
        mso=mso,
        key="m15",
        tf_name="M15",
    )
    evidence.update({
        "deterministic_bias": deterministic_bias,
        "d1_direction": d1,
        "h4_direction": h4,
        "h1_direction": h1,
        "m15_direction": m15,
        "only_when_deterministic_bias_absent": only_no_bias,
        "d1_lag_h4_h1_consensus_enabled": bool(
            block.get("d1_lag_h4_h1_consensus_enabled", False)
        ),
    })

    d1_lag_h4_h1_consensus = (
        _directional(d1)
        and _directional(h4)
        and _directional(h1)
        and h4 == h1
        and d1 != h1
    )
    evidence["d1_lag_h4_h1_consensus"] = d1_lag_h4_h1_consensus

    if bool(block.get("d1_lag_h4_h1_consensus_enabled", False)) and d1_lag_h4_h1_consensus:
        evidence.update({
            "source_path": ".context/02_session_handoffs/33_apr19_session_close_handoff.md",
            "source_line_no": 87,
            "nas100_w14_blocked_candles": int(
                block.get("d1_lag_nas100_blocked_candles", 54)
            ),
            "nas100_w14_rally_pct": float(
                block.get("d1_lag_nas100_rally_pct", 4.20)
            ),
            "policy": "d1_lag_h4_h1_consensus_pre_ai_route",
        })
        if _directional(m15) and m15 != h1:
            would = "SKIP_AI_M15_OPPOSES_H1"
            return StructuralCGateDecision(
                enabled=True,
                apply_to_ai_call=apply_to_ai_call,
                action=_resolved_action(would_action=would, apply_to_ai_call=apply_to_ai_call),
                would_action=would,
                reason="structural_c_gate_d1_lag_m15_opposes_h4_h1_consensus",
                bias=h1,
                side=_side_for_bias(h1),
                h1_direction=h1,
                m15_direction=m15,
                evidence=evidence,
            )
        would = "NARROW_AI_TO_SIDE"
        return StructuralCGateDecision(
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            action=_resolved_action(would_action=would, apply_to_ai_call=apply_to_ai_call),
            would_action=would,
            reason="structural_c_gate_d1_lag_h4_h1_consensus",
            bias=h1,
            side=_side_for_bias(h1),
            h1_direction=h1,
            m15_direction=m15,
            evidence=evidence,
        )

    if only_no_bias and deterministic_bias and deterministic_bias != "no_bias":
        return StructuralCGateDecision(
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            action="ALLOW_AI",
            would_action="ALLOW_AI",
            reason="higher_timeframe_bias_already_available",
            bias=deterministic_bias,
            side=_side_for_bias(deterministic_bias),
            h1_direction=h1,
            m15_direction=m15,
            evidence=evidence,
        )

    if not _directional(h1):
        would = "SKIP_AI_NO_H1_BIAS"
        return StructuralCGateDecision(
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            action=_resolved_action(would_action=would, apply_to_ai_call=apply_to_ai_call),
            would_action=would,
            reason="structural_c_gate_no_h1_directional_bias",
            h1_direction=h1,
            m15_direction=m15,
            evidence=evidence,
        )

    if _directional(m15) and m15 != h1:
        would = "SKIP_AI_M15_OPPOSES_H1"
        return StructuralCGateDecision(
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            action=_resolved_action(would_action=would, apply_to_ai_call=apply_to_ai_call),
            would_action=would,
            reason="structural_c_gate_m15_opposes_h1",
            bias=h1,
            side=_side_for_bias(h1),
            h1_direction=h1,
            m15_direction=m15,
            evidence=evidence,
        )

    would = "NARROW_AI_TO_SIDE"
    return StructuralCGateDecision(
        enabled=True,
        apply_to_ai_call=apply_to_ai_call,
        action=_resolved_action(would_action=would, apply_to_ai_call=apply_to_ai_call),
        would_action=would,
        reason="structural_c_gate_h1_bias_m15_not_opposing",
        bias=h1,
        side=_side_for_bias(h1),
        h1_direction=h1,
        m15_direction=m15,
        evidence=evidence,
    )


__all__ = ["StructuralCGateDecision", "evaluate_structural_c_gate"]
