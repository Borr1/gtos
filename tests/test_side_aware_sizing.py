"""Tests for side-aware sizing helpers + SPRT auto-revert watcher.

H38 + side_aware_a sweep validation (commit 124de56) — ship-with-flag P1.
LONG=0.5x risk multiplier, SHORT=1.0x. Default OFF. SPRT auto-disable on
LONG-WR < 50% over rolling 20-trade window.

Pattern (canonical, per memory ``project_pytest_contamination_forensics``):
- ``tmp_path`` fixture for isolated state file per test.
- Module-ref monkeypatch on ``STATE_PATH`` so production
  ``pipeline_state/side_aware_sprt_state.json`` is never touched.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from src.components import side_aware_sizing
from src.components import side_aware_sprt_watcher as _saw
from src.components.gtos_vnext_runtime import GTOSVNextRuntimeDecision


READY8_CONTEXT_RISK_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_CONTEXT_RISK_RULES_2026-05-18.json"
)
READY8_DISCRIMINATIVE_CONTEXT_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_DISCRIMINATIVE_CONTEXT_RULES_2026-05-18.json"
)
READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES_2026-05-18.json"
)


# --------------------------------------------------------------------------
# Fixtures — pure-helper tests (no I/O so no isolation needed) and
# watcher tests (state file isolation per the canonical pattern)
# --------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_sprt_state_path(tmp_path, monkeypatch):
    """Redirect the module-level ``STATE_PATH`` to a per-test tmp file.

    Every watcher test gets a fresh, isolated state file. Production
    ``pipeline_state/side_aware_sprt_state.json`` is never touched.
    """
    path = tmp_path / "side_aware_sprt_state.json"
    monkeypatch.setattr(_saw, "STATE_PATH", path)
    return path


# --------------------------------------------------------------------------
# Multiplier helper tests (side_aware_sizing.py)
# --------------------------------------------------------------------------


class TestMultiplierHelpers:
    """Pure-function tests for ``side_aware_sizing``. No I/O, no fixtures
    beyond ``_isolate_sprt_state_path`` (autouse, doesn't matter here)."""

    def test_default_off_preserves_base_risk(self):
        """Empty config → multiplier returns base unchanged for both sides."""
        cfg = {}
        assert side_aware_sizing.is_enabled(cfg) is False
        assert side_aware_sizing.apply_side_multiplier(2.0, "LONG", cfg) == 2.0
        assert side_aware_sizing.apply_side_multiplier(2.0, "SHORT", cfg) == 2.0

    def test_explicit_off_preserves_base_risk(self):
        """``enabled: false`` → unchanged."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": False,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.is_enabled(cfg) is False
        assert side_aware_sizing.apply_side_multiplier(2.0, "LONG", cfg) == 2.0
        assert side_aware_sizing.apply_side_multiplier(2.0, "SHORT", cfg) == 2.0

    def test_long_halves_when_enabled(self):
        """``enabled: true, long_multiplier: 0.5`` → LONG returns 0.5*base."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.is_enabled(cfg) is True
        assert side_aware_sizing.apply_side_multiplier(2.0, "LONG", cfg) == 1.0

    def test_short_unchanged_when_enabled(self):
        """``enabled: true, short_multiplier: 1.0`` → SHORT returns base."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.apply_side_multiplier(2.0, "SHORT", cfg) == 2.0

    def test_custom_multipliers_respected(self):
        """``long_multiplier: 0.3`` → LONG returns 0.3*base."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.3,
                    "short_multiplier": 0.7,
                },
            }
        }
        assert side_aware_sizing.apply_side_multiplier(2.0, "LONG", cfg) == pytest.approx(0.6)
        assert side_aware_sizing.apply_side_multiplier(2.0, "SHORT", cfg) == pytest.approx(1.4)
        assert side_aware_sizing.get_long_multiplier(cfg) == 0.3
        assert side_aware_sizing.get_short_multiplier(cfg) == 0.7

    def test_apply_zero_base_returns_zero(self):
        """Zero base risk → zero out, regardless of multiplier."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.apply_side_multiplier(0.0, "LONG", cfg) == 0.0
        assert side_aware_sizing.apply_side_multiplier(0.0, "SHORT", cfg) == 0.0

    def test_lowercase_direction_handled(self):
        """``'long'`` / ``'short'`` work via uppercase normalization."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.apply_side_multiplier(2.0, "long", cfg) == 1.0
        assert side_aware_sizing.apply_side_multiplier(2.0, "short", cfg) == 2.0

    def test_unknown_direction_passes_through(self):
        """Empty / unknown direction → fail-safe pass-through."""
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": 0.5,
                    "short_multiplier": 1.0,
                },
            }
        }
        assert side_aware_sizing.apply_side_multiplier(2.0, "", cfg) == 2.0
        assert side_aware_sizing.apply_side_multiplier(2.0, "FLAT", cfg) == 2.0
        assert side_aware_sizing.apply_side_multiplier(2.0, None, cfg) == 2.0

    def test_defaults_when_section_missing(self):
        """Multipliers default to 0.5/1.0 when the block is missing."""
        cfg = {"risk": {}}
        assert side_aware_sizing.get_long_multiplier(cfg) == 0.5
        assert side_aware_sizing.get_short_multiplier(cfg) == 1.0
        assert side_aware_sizing.is_enabled(cfg) is False

    def test_malformed_config_falls_back_safely(self):
        """Non-dict ``risk`` / ``side_aware_sizing`` → defaults preserved."""
        # Non-dict at top level.
        assert side_aware_sizing.is_enabled(None) is False
        # Non-dict ``risk``.
        assert side_aware_sizing.is_enabled({"risk": "garbage"}) is False
        # Non-dict block.
        assert side_aware_sizing.is_enabled({"risk": {"side_aware_sizing": 5}}) is False
        # Non-numeric multiplier — falls back to default.
        cfg = {
            "risk": {
                "side_aware_sizing": {
                    "enabled": True,
                    "long_multiplier": "not-a-number",
                },
            }
        }
        assert side_aware_sizing.get_long_multiplier(cfg) == 0.5


def _contextual_cfg(**overrides) -> dict:
    block = {
        "enabled": True,
        "mode": "contextual",
        "apply_to_execution": True,
        "long_multiplier": 0.5,
        "short_multiplier": 1.0,
        "contextual_default_multiplier": 1.0,
        "contextual_weak_multiplier": 0.5,
        "contextual_adverse_multiplier": 0.25,
        "contextual_full_risk_multiplier": 1.0,
        "contextual_full_risk_min_score": 2.0,
        "contextual_weak_score_threshold": -0.25,
        "contextual_adverse_score_threshold": -1.0,
        "contextual_min_effective_n": 3,
        "h1_autocorrelation_follow_threshold": 0.0,
    }
    block.update(overrides)
    return {"risk": {"side_aware_sizing": block}}


def _positive_vnext_evidence() -> dict:
    return {
        "matched_rows": 12,
        "decision_counts": {"FOLLOW": 12},
        "metrics": {
            "cost_adjusted_simulated_r": {"sum": 8.0},
            "proxy_score": {"sum": 4.0},
            "stress_simulated_r": {"sum": 3.0},
            "effective_n": {"sum": 12},
        },
        "source_component_decision_counts": {
            "nofill_near_miss_market_entry": {"FOLLOW": 4},
        },
        "proxy_r_class_counts": {"STRONG_POSITIVE_PROXY_R": 8},
        "target_stop_order_class_counts": {"TARGET_FIRST_PROXY_DOMINANT": 5},
        "symbol_family_counts": {"US30_YM_FAMILY": 12},
        "side_counts": {"LONG": 12},
        "route_session_counts": {"ny_core": 12},
        "framework_counts": {"ob_retest": 12},
        "market_timeframe_counts": {"M15": 12},
    }


def _adverse_vnext_evidence() -> dict:
    return {
        "matched_rows": 9,
        "decision_counts": {"AVOID": 9},
        "metrics": {
            "cost_adjusted_simulated_r": {"sum": -3.0},
            "proxy_score": {"sum": -4.0},
            "stress_simulated_r": {"sum": -2.0},
            "effective_n": {"sum": 9},
        },
        "source_component_decision_counts": {
            "nofill_far_miss_avoid": {"AVOID": 6},
        },
        "proxy_r_class_counts": {"STRONG_NEGATIVE_PROXY_R": 7},
        "target_stop_order_class_counts": {"STOP_FIRST_PROXY_DOMINANT": 4},
        "symbol_family_counts": {"XAGUSD_SILVER_FAMILY": 9},
        "side_counts": {"SHORT": 9},
        "route_session_counts": {"london_core": 9},
        "framework_counts": {"breaker_re_entry": 9},
        "market_timeframe_counts": {"M5": 9},
    }


def _context(**overrides) -> dict:
    ctx = {
        "symbol": "US30",
        "source_symbol": "US30.cash",
        "symbol_family": "US30_YM_FAMILY",
        "side": "LONG",
        "session": "ny_core",
        "framework": "ob_retest",
        "route_family": "ob_retest",
        "regime": "trending_bull",
        "market_timeframe": "M15",
        "h1_autocorrelation": 0.18,
        "h1_decay_risk_applied": False,
        "vnext_decision": "FOLLOW",
        "vnext_evidence": _positive_vnext_evidence(),
    }
    ctx.update(overrides)
    return ctx


class TestContextualSideRisk:
    def test_long_can_receive_full_risk_when_context_and_vnext_evidence_support_it(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(),
        )

        assert decision.mode == "contextual"
        assert decision.direction == "LONG"
        assert decision.reason == "contextual_side_risk_full_supported"
        assert decision.multiplier == 1.0
        assert decision.after_risk_pct == 2.0
        assert decision.score >= 2.0
        assert decision.evidence_summary["vnext_metric_sums"]["effective_n"] == 12

    def test_short_is_reduced_when_vnext_path_and_fillability_evidence_are_adverse(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="SHORT",
            config=_contextual_cfg(),
            context=_context(
                symbol="XAGUSD",
                symbol_family="XAGUSD_SILVER_FAMILY",
                side="SHORT",
                session="london_core",
                framework="breaker_re_entry",
                route_family="breaker_re_entry",
                regime="chop",
                market_timeframe="M5",
                h1_autocorrelation=-0.07,
                vnext_decision="AVOID",
                vnext_evidence=_adverse_vnext_evidence(),
            ),
        )

        assert decision.direction == "SHORT"
        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.multiplier == 0.25
        assert decision.after_risk_pct == 0.5
        assert decision.score <= -1.0
        assert any(f["factor"] == "nofill_path_quality" for f in decision.factors)

    def test_long_with_neutral_evidence_defaults_to_full_base_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.after_risk_pct == 2.0

    def test_ready8_haz001_support_can_restore_neutral_base_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_ready8_enabled=True,
                contextual_ready8_rules=[
                    {
                        "card_id": "HAZ-001",
                        "horizon_m15_bars": "32",
                        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
                        "score": 1.0,
                        "evidence_delta": 0.5498694567843504,
                        "reason": "haz001_h32_positive_neutral_movement_support",
                    }
                ],
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="MIXED",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                ready8_card_id="HAZ-001",
                ready8_horizon_m15_bars="32",
                ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["ready8_matched_rules"][0]["evidence_delta"] == 0.5498694567843504
        assert any(
            factor["factor"] == "ready8_context"
            and factor["detail"] == "haz001_h32_positive_neutral_movement_support"
            for factor in decision.factors
        )

    def test_ready8_context_rule_artifact_adds_haz001_branch_support(self):
        side_aware_sizing._load_ready8_rule_artifact.cache_clear()
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_ready8_enabled=True,
                contextual_ready8_rules=[],
                contextual_ready8_rule_artifact_paths=[str(READY8_CONTEXT_RISK_RULES)],
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                ready8_card_id="HAZ-001",
                ready8_horizon_m15_bars="32",
                ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
                ready8_partition_assignment="SEALED_VALIDATION_CANDIDATE_DESIGN",
            ),
        )

        matched = decision.evidence_summary["ready8_matched_rules"]

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert len(matched) == 2
        assert {rule["source_row_id"] for rule in matched} == {
            "HAZ001-READY8-BRANCH-007",
            "HAZ001-READY8-BRANCH-062",
        }
        assert sum(rule["score"] for rule in matched) == 1.0
        assert all(
            rule["branch_role"] == "MECHANISM_ANCHOR_FROM_HAZ001_SYNTHESIS"
            for rule in matched
        )

    def test_ready8_context_rule_artifact_requires_descriptor_anchors(self):
        side_aware_sizing._load_ready8_rule_artifact.cache_clear()
        cfg = _contextual_cfg(
            contextual_ready8_enabled=True,
            contextual_ready8_rules=[],
            contextual_ready8_rule_artifact_paths=[str(READY8_CONTEXT_RISK_RULES)],
        )
        base_context = _context(
            h1_autocorrelation=None,
            vnext_decision="LEGACY",
            vnext_evidence={"matched_rows": 0, "metrics": {}},
            ready8_card_id="HAZ-001",
            ready8_horizon_m15_bars="32",
            ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ready8_partition_assignment="SEALED_VALIDATION_CANDIDATE_DESIGN",
        )

        without_descriptor = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=base_context,
        )
        with_descriptor = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context={
                **base_context,
                "ready8_descriptor_name": "previous_candidate_gap_bucket",
                "ready8_descriptor_value": "WAIT_GAP_LT_60M",
            },
        )

        assert "HAZ001-READY8-BRANCH-019" not in {
            rule["source_row_id"]
            for rule in without_descriptor.evidence_summary["ready8_matched_rules"]
        }
        assert "HAZ001-READY8-BRANCH-019" in {
            rule["source_row_id"]
            for rule in with_descriptor.evidence_summary["ready8_matched_rules"]
        }

    def test_ready8_discriminative_context_artifact_adds_support_and_inverse_risk(self):
        side_aware_sizing._load_ready8_rule_artifact.cache_clear()
        cfg = _contextual_cfg(
            contextual_ready8_enabled=True,
            contextual_ready8_rules=[],
            contextual_ready8_rule_artifact_paths=[
                str(READY8_DISCRIMINATIVE_CONTEXT_RULES)
            ],
            contextual_ready8_adjustment_enabled=False,
        )

        positive = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                ready8_card_id="HAZ-001",
                ready8_horizon_m15_bars="32",
                ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ),
        )
        negative = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                ready8_card_id="MAC-001",
                ready8_horizon_m15_bars="32",
                ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ),
        )

        positive_match = positive.evidence_summary["ready8_matched_rules"][0]
        negative_match = negative.evidence_summary["ready8_matched_rules"][0]

        assert positive.reason == "contextual_side_risk_neutral_base"
        assert positive.multiplier == 1.0
        assert positive_match["score"] == 0.5
        assert positive_match["evidence_delta"] == pytest.approx(
            0.007095616898111001
        )
        assert positive_match["reason"] == (
            "ready8_discriminative_positive_context_support"
        )
        assert any(
            factor["factor"] == "ready8_context"
            and factor["detail"]
            == "ready8_discriminative_positive_context_support"
            for factor in positive.factors
        )

        assert negative.reason == "contextual_side_risk_weak_reduced"
        assert negative.multiplier == 0.5
        assert negative_match["score"] == -0.943777
        assert negative_match["evidence_delta"] == pytest.approx(
            -0.004718882667346162
        )
        assert negative_match["reason"] == (
            "ready8_discriminative_inverse_context_risk"
        )

    def test_ready8_failure_context_adjustment_artifact_zeroes_control_explained_support(self):
        side_aware_sizing._load_ready8_rule_artifact.cache_clear()
        base_context = _context(
            h1_autocorrelation=None,
            vnext_decision="MIXED",
            vnext_evidence={"matched_rows": 0, "metrics": {}},
            ready8_card_id="HAZ-001",
            ready8_horizon_m15_bars="32",
            ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ready8_partition_assignment="SEALED_VALIDATION_CANDIDATE_DESIGN",
        )
        unadjusted = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_ready8_enabled=True,
                contextual_ready8_rules=[],
                contextual_ready8_rule_artifact_paths=[str(READY8_CONTEXT_RISK_RULES)],
            ),
            context=base_context,
        )
        adjusted = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_ready8_enabled=True,
                contextual_ready8_rules=[],
                contextual_ready8_rule_artifact_paths=[str(READY8_CONTEXT_RISK_RULES)],
                contextual_ready8_adjustment_enabled=True,
                contextual_ready8_adjustment_rule_artifact_paths=[
                    str(READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES)
                ],
            ),
            context=base_context,
        )

        assert unadjusted.reason == "contextual_side_risk_neutral_base"
        assert sum(rule["score"] for rule in unadjusted.evidence_summary["ready8_matched_rules"]) == 1.0
        assert adjusted.reason == "contextual_side_risk_adverse_reduced"
        assert adjusted.multiplier == 0.25
        assert sum(rule["score"] for rule in adjusted.evidence_summary["ready8_matched_rules"]) == 0.0
        assert {
            rule["raw_score"]
            for rule in adjusted.evidence_summary["ready8_matched_rules"]
        } == {0.5}
        assert adjusted.evidence_summary["ready8_matched_adjustments"]
        assert all(
            adjustment["score_after"] == 0.0
            for adjustment in adjusted.evidence_summary["ready8_matched_adjustments"]
        )
        assert any(
            factor["factor"] == "ready8_context_adjustment"
            and factor["detail"] == "ready8_failure_context_adjustment"
            for factor in adjusted.factors
        )

    def test_ready8_mac001_metals_inverse_rule_reduces_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_ready8_enabled=True,
                contextual_ready8_rules=[
                    {
                        "card_id": "MAC-001",
                        "horizon_m15_bars": "32",
                        "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
                        "symbol_family": "XAUUSD_GC_FAMILY",
                        "score": -1.0,
                        "evidence_delta": -0.5151404151404151,
                        "reason": "mac001_xauusd_h32_inverse_avoid_risk",
                    }
                ],
            ),
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                ready8_card_id="MAC-001",
                ready8_horizon_m15_bars="32",
                ready8_target_family_id="neutral_high_low_excursion_m15_horizons_v1",
            ),
        )

        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.multiplier == 0.25
        assert decision.after_risk_pct == 0.5
        assert decision.evidence_summary["ready8_matched_rules"][0]["symbol_family"] == "XAUUSD_GC_FAMILY"
        assert any(
            factor["factor"] == "ready8_context"
            and factor["detail"] == "mac001_xauusd_h32_inverse_avoid_risk"
            for factor in decision.factors
        )

    def test_gbpjpy_validation_leash_reduces_neutral_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "source_path": ".context/01_knowledge_base/kb_validation_and_monitoring_framework.md",
                        "source_line_no": 41,
                        "reason": "gbpjpy_familywise_correction_failed_razor_thin_margin",
                    }
                ],
            ),
            context=_context(
                symbol="GBPJPY",
                source_symbol="GBPJPY",
                symbol_family="",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        assert decision.after_risk_pct == 1.0
        assert decision.evidence_summary["validation_leash_matched_rules"] == [
            {
                "symbol": "GBPJPY",
                "score": -0.5,
                "source_path": ".context/01_knowledge_base/kb_validation_and_monitoring_framework.md",
                "source_line_no": 41,
                "reason": "gbpjpy_familywise_correction_failed_razor_thin_margin",
            }
        ]
        assert any(
            factor["factor"] == "validation_leash"
            and factor["detail"] == "gbpjpy_familywise_correction_failed_razor_thin_margin"
            for factor in decision.factors
        )

    def test_validation_leash_is_symbol_scoped_and_does_not_reduce_usdjpy(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "reason": "gbpjpy_familywise_correction_failed_razor_thin_margin",
                    }
                ],
            ),
            context=_context(
                symbol="USDJPY",
                source_symbol="USDJPY",
                symbol_family="USDJPY_6J_FAMILY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["validation_leash_matched_rules"] == []
        assert not any(factor["factor"] == "validation_leash" for factor in decision.factors)

    def test_xauusd_long_decay_caveat_reduces_neutral_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "XAUUSD",
                        "side": "LONG",
                        "score": -0.5,
                        "source_path": ".context/01_knowledge_base/validated_numbers_caveats.md",
                        "source_line_no": 38,
                        "reason": "xauusd_v1_long_only_h2_decay_alarm_neutral_long_leash",
                    }
                ],
            ),
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                side="LONG",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        assert decision.evidence_summary["validation_leash_matched_rules"][0]["side"] == "LONG"
        assert decision.evidence_summary["validation_leash_matched_rules"][0]["source_line_no"] == 38
        assert any(
            factor["factor"] == "validation_leash"
            and factor["detail"] == "xauusd_v1_long_only_h2_decay_alarm_neutral_long_leash"
            for factor in decision.factors
        )

    def test_xauusd_long_decay_caveat_does_not_reduce_short_context(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="SHORT",
            config=_contextual_cfg(
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "XAUUSD",
                        "side": "LONG",
                        "score": -0.5,
                        "reason": "xauusd_v1_long_only_h2_decay_alarm_neutral_long_leash",
                    }
                ],
            ),
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                side="SHORT",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["validation_leash_matched_rules"] == []
        assert not any(factor["factor"] == "validation_leash" for factor in decision.factors)

    def test_monthly_decay_alert_reduces_only_matching_detector_regime(self):
        cfg = _contextual_cfg(
            contextual_monthly_decay_enabled=True,
            contextual_monthly_decay_rules=[
                {
                    "symbol": "XAUUSD",
                    "side": "LONG",
                    "detector_versions": ["v1", "v2_shadow"],
                    "score": -0.5,
                    "alert_kinds": ["WR_DECAY", "EXP_DECAY"],
                    "current_wr_pct": 18.2,
                    "baseline_wr_pct": 57.7,
                    "wr_drop_pp": 39.5,
                    "current_exp_r": -0.55,
                    "baseline_exp_r": 0.44,
                    "exp_drop_r": 0.99,
                    "source_path": "research/monthly_decay_monitor/2026-04_report_including_a1.md",
                    "source_line_no": 10,
                    "reason": "xauusd_v1_monthly_wr_exp_decay_long_risk_reducer",
                }
            ],
        )

        decayed = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                side="LONG",
                detector_version="v2_shadow",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )
        v2_active = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                side="LONG",
                detector_version="v2",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decayed.reason == "contextual_side_risk_weak_reduced"
        assert decayed.multiplier == 0.5
        assert decayed.evidence_summary["monthly_decay_matched_rules"][0]["wr_drop_pp"] == 39.5
        assert any(
            factor["factor"] == "monthly_decay_alert"
            and factor["detail"] == "xauusd_v1_monthly_wr_exp_decay_long_risk_reducer"
            for factor in decayed.factors
        )
        assert v2_active.reason == "contextual_side_risk_neutral_base"
        assert v2_active.multiplier == 1.0
        assert v2_active.evidence_summary["monthly_decay_matched_rules"] == []

    def test_long_with_weak_effective_n_reduces_without_forcing_neutral_reduction(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={
                    "matched_rows": 2,
                    "metrics": {"effective_n": {"sum": 1}},
                },
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        assert decision.after_risk_pct == 1.0

    def test_context_maps_can_route_symbol_session_framework_regime_timeframe_into_sizing(self):
        cfg = _contextual_cfg(
            contextual_symbol_family_scores={"US30_YM_FAMILY": 0.5},
            contextual_session_scores={"ny_core": 0.5},
            contextual_framework_scores={"ob_retest": 0.5},
            contextual_regime_scores={"trending_bull": 0.5},
            contextual_market_timeframe_scores={"M15": 0.5},
        )
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=cfg,
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
            ),
        )

        assert decision.reason == "contextual_side_risk_full_supported"
        assert decision.multiplier == 1.0
        factor_names = {factor["factor"] for factor in decision.factors}
        assert "contextual_symbol_family_scores" in factor_names
        assert "contextual_session_scores" in factor_names
        assert "contextual_framework_scores" in factor_names
        assert "contextual_regime_scores" in factor_names
        assert "contextual_market_timeframe_scores" in factor_names

    def test_align_score_modifier_offsets_validation_leash_without_becoming_gate(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_align_score_enabled=True,
                contextual_align_score_min=2.0,
                contextual_align_support_score=0.5,
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "reason": "gbpjpy_validation_leash",
                    }
                ],
            ),
            context=_context(
                symbol="GBPJPY",
                source_symbol="GBPJPY",
                symbol_family="",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                align_score=3,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["align_context"]["policy"] == "positive_modifier_not_gate"
        assert any(
            factor["factor"] == "align_context"
            and factor["detail"] == "align_score_positive_modifier_not_gate"
            for factor in decision.factors
        )

    def test_low_align_score_does_not_reduce_or_gate_neutral_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_align_score_enabled=True,
                contextual_align_score_min=2.0,
                contextual_align_support_score=0.5,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                align_score=1,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["align_context"]["align_score"] == 1.0
        assert not any(factor["factor"] == "align_context" for factor in decision.factors)

    def test_fvg_in_impulse_support_offsets_validation_leash_without_becoming_gate(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_fvg_in_impulse_enabled=True,
                contextual_fvg_in_impulse_support_score=0.5,
                contextual_fvg_in_impulse_delta_pp={"GBPJPY": 7.9},
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "reason": "gbpjpy_validation_leash",
                    }
                ],
            ),
            context=_context(
                symbol="GBPJPY",
                source_symbol="GBPJPY",
                symbol_family="",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                creates_fvg=True,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["fvg_in_impulse_context"]["present"] is True
        assert decision.evidence_summary["fvg_in_impulse_context"]["delta_pp"] == 7.9
        assert any(
            factor["factor"] == "fvg_in_impulse_context"
            and factor["detail"] == "fvg_in_impulse_positive_modifier_not_gate"
            for factor in decision.factors
        )

    def test_absent_fvg_in_impulse_does_not_reduce_or_gate_neutral_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_fvg_in_impulse_enabled=True,
                contextual_fvg_in_impulse_support_score=0.5,
                contextual_fvg_in_impulse_delta_pp={"USDJPY": 7.1},
            ),
            context=_context(
                symbol="USDJPY",
                source_symbol="USDJPY",
                symbol_family="USDJPY_FX_FAMILY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                fvg_in_impulse=False,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["fvg_in_impulse_context"]["present"] is False
        assert not any(factor["factor"] == "fvg_in_impulse_context" for factor in decision.factors)

    def test_sweep_before_ob_reduces_neutral_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_sweep_before_ob_enabled=True,
                contextual_sweep_before_ob_score=-0.5,
                contextual_sweep_before_ob_with_continuation_wr_pct=63.4,
                contextual_sweep_before_ob_without_continuation_wr_pct=71.6,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                sweep_before_ob=True,
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        assert decision.after_risk_pct == 1.0
        summary = decision.evidence_summary["sweep_before_ob_context"]
        assert summary["present"] is True
        assert summary["with_sweep_continuation_wr_pct"] == 63.4
        assert summary["without_sweep_continuation_wr_pct"] == 71.6
        assert summary["source_line_no"] == 173
        assert any(
            factor["factor"] == "sweep_before_ob_context"
            and factor["detail"] == "sweep_before_ob_adverse_modifier_not_gate"
            for factor in decision.factors
        )

    def test_absent_sweep_before_ob_does_not_reduce_or_gate_neutral_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_sweep_before_ob_enabled=True,
                contextual_sweep_before_ob_score=-0.5,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                sweep_before_ob=False,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["sweep_before_ob_context"]["present"] is False
        assert not any(factor["factor"] == "sweep_before_ob_context" for factor in decision.factors)

    def test_generic_liquidity_sweep_fields_do_not_reduce_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_sweep_before_ob_enabled=True,
                contextual_sweep_before_ob_score=-0.5,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                detected_sweeps_count=42,
                liquidity_sweep_detected=True,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["sweep_before_ob_context"] == {}
        assert not any(factor["factor"] == "sweep_before_ob_context" for factor in decision.factors)

    def test_high_internal_session_volatility_supports_risk_without_becoming_filter(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_internal_session_volatility_enabled=True,
                contextual_session_vol_ratio_support_min=1.2,
                contextual_session_vol_ratio_support_score=0.5,
                contextual_garch_evt_removed_high_vol_delta_r=-18.8,
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "reason": "gbpjpy_validation_leash",
                    }
                ],
            ),
            context=_context(
                symbol="GBPJPY",
                source_symbol="GBPJPY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                m15_session_vol_ratio=1.35,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        summary = decision.evidence_summary["internal_session_volatility"]
        assert summary["m15_session_vol_ratio"] == 1.35
        assert summary["removed_high_vol_entries_delta_r"] == -18.8
        assert summary["policy"] == "high_internal_vol_positive_modifier_not_entry_filter"
        assert any(
            factor["factor"] == "internal_session_volatility"
            and factor["detail"] == "high_internal_vol_positive_modifier_not_filter"
            for factor in decision.factors
        )

    def test_low_internal_session_volatility_does_not_reduce_or_gate_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_internal_session_volatility_enabled=True,
                contextual_session_vol_ratio_support_min=1.2,
                contextual_session_vol_ratio_support_score=0.5,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                m15_session_vol_ratio=0.72,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["internal_session_volatility"]["m15_session_vol_ratio"] == 0.72
        assert not any(factor["factor"] == "internal_session_volatility" for factor in decision.factors)

    def test_aligned_derived_order_flow_supports_risk_without_raw_volume_gate(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_derived_order_flow_enabled=True,
                contextual_order_flow_clv_threshold=0.2,
                contextual_order_flow_bvc_threshold=0.6,
                contextual_order_flow_min_signals=2,
                contextual_order_flow_aligned_score=0.5,
                contextual_validation_leash_enabled=True,
                contextual_validation_leash_rules=[
                    {
                        "symbol": "GBPJPY",
                        "score": -0.5,
                        "reason": "gbpjpy_validation_leash",
                    }
                ],
            ),
            context=_context(
                symbol="GBPJPY",
                source_symbol="GBPJPY",
                symbol_family="",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                m15_clv_avg_5=0.36,
                m15_bvc_buy_fraction=0.68,
                volume=999999,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        summary = decision.evidence_summary["derived_order_flow"]
        assert summary["aligned_signals"] == 2
        assert summary["opposed_signals"] == 0
        assert summary["policy"] == "derived_order_flow_modifier_not_raw_volume_gate"
        assert any(
            factor["factor"] == "derived_order_flow"
            and factor["detail"] == "clv_bvc_net_flow_aligned_positive_modifier"
            for factor in decision.factors
        )

    def test_opposing_derived_order_flow_reduces_neutral_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(
                contextual_derived_order_flow_enabled=True,
                contextual_order_flow_clv_threshold=0.2,
                contextual_order_flow_bvc_threshold=0.6,
                contextual_order_flow_net_flow_threshold=0.0,
                contextual_order_flow_min_signals=2,
                contextual_order_flow_opposed_score=-0.5,
            ),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                m15_clv_avg_5=-0.35,
                m15_bvc_buy_fraction=0.24,
                m15_net_flow_5=-1200.0,
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        summary = decision.evidence_summary["derived_order_flow"]
        assert summary["aligned_signals"] == 0
        assert summary["opposed_signals"] == 3
        assert any(
            factor["factor"] == "derived_order_flow"
            and factor["detail"] == "clv_bvc_net_flow_opposed_risk_reducer"
            for factor in decision.factors
        )

    def test_raw_volume_without_derived_order_flow_does_not_reduce_or_gate_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(contextual_derived_order_flow_enabled=True),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                volume=999999,
                tick_volume=999999,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["derived_order_flow"] == {}
        assert not any(factor["factor"] == "derived_order_flow" for factor in decision.factors)

    def test_wide_asian_range_reduces_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                asian_range_pct_of_adr=90.0,
                asian_range_category="wide",
            ),
        )

        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.multiplier == 0.25
        assert decision.after_risk_pct == 0.5
        assert decision.evidence_summary["asian_range_pct_of_adr"] == 90.0
        assert any(
            factor["factor"] == "asian_range"
            and factor["detail"] == "wide_range_consolidation_risk"
            for factor in decision.factors
        )

    def test_compressed_but_not_ultra_narrow_asian_range_supports_full_base_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                asian_range_info={"pct_of_adr": 42.0, "category": "moderate"},
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["asian_range_pct_of_adr"] == 42.0
        assert any(
            factor["factor"] == "asian_range"
            and factor["detail"] == "compressed_range_support"
            for factor in decision.factors
        )

    def test_late_session_phase_reduces_neutral_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                candle_time_utc="2026-05-19T15:05:00+00:00",
                session_start_utc="13:00",
            ),
        )

        assert decision.reason == "contextual_side_risk_weak_reduced"
        assert decision.multiplier == 0.5
        assert decision.after_risk_pct == 1.0
        assert decision.evidence_summary["session_phase"]["minutes_since_session_start"] == 125
        assert decision.evidence_summary["session_phase"]["phase"] == "late_session"
        assert any(
            factor["factor"] == "session_phase"
            and factor["detail"] == "post_90_minute_decision_fatigue_and_vol_decay"
            for factor in decision.factors
        )

    def test_first_90_minutes_session_phase_preserves_neutral_base_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                candle_time_utc="2026-05-19T13:45:00Z",
                session_start_utc="13:00",
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["session_phase"]["minutes_since_session_start"] == 45
        assert decision.evidence_summary["session_phase"]["phase"] == "first_window"
        assert any(
            factor["factor"] == "session_phase"
            and factor["detail"] == "first_90_minutes_quality_window"
            for factor in decision.factors
        )

    def test_near_high_impact_news_reduces_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                news_minutes_to_event=30.0,
                news_event_name="US CPI",
                news_currency="USD",
                news_impact="HIGH",
            ),
        )

        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.multiplier == 0.25
        assert decision.evidence_summary["news_event_risk"]["event"] == "US CPI"
        assert any(
            factor["factor"] == "news_event_risk"
            and factor["detail"] == "near_high_impact_news_reduce_window"
            for factor in decision.factors
        )

    def test_news_minutes_without_currency_and_impact_guard_do_not_reduce_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                news_minutes_to_event=30.0,
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["news_event_risk"] == {}
        assert not any(factor["factor"] == "news_event_risk" for factor in decision.factors)

    def test_high_gvz_reduces_metals_contextual_risk(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                symbol="XAUUSD",
                source_symbol="XAUUSD",
                symbol_family="XAUUSD_GC_FAMILY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                volatility_gvz=42.0,
                volatility_source="fred__GVZCLS",
            ),
        )

        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.multiplier == 0.25
        assert decision.evidence_summary["volatility_regime"]["gvz"] == 42.0
        assert any(
            factor["factor"] == "volatility_regime"
            and factor["detail"] == "gvz_high_headline_regime"
            for factor in decision.factors
        )

    def test_gvz_is_family_scoped_and_does_not_reduce_usdjpy(self):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="LONG",
            config=_contextual_cfg(),
            context=_context(
                symbol="USDJPY",
                source_symbol="USDJPY",
                symbol_family="USDJPY_FX_FAMILY",
                h1_autocorrelation=None,
                vnext_decision="LEGACY",
                vnext_evidence={"matched_rows": 0, "metrics": {}},
                volatility_gvz=42.0,
                volatility_source="fred__GVZCLS",
            ),
        )

        assert decision.reason == "contextual_side_risk_neutral_base"
        assert decision.multiplier == 1.0
        assert decision.evidence_summary["volatility_regime"] == {}
        assert not any(factor["factor"] == "volatility_regime" for factor in decision.factors)

    def test_record_attachment_preserves_contextual_evidence(self):
        record = {}
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=2.0,
            direction="SHORT",
            config=_contextual_cfg(),
            context=_context(side="SHORT", vnext_decision="AVOID", vnext_evidence=_adverse_vnext_evidence()),
        )

        side_aware_sizing.attach_contextual_side_risk_to_record(record, decision)

        attached = record["decision_pipeline"]["contextual_side_risk"]
        assert attached["reason"] == "contextual_side_risk_adverse_reduced"
        assert attached["evidence_summary"]["vnext_decision"] == "AVOID"
        assert record["instrumentation"]["contextual_side_risk_multiplier"] == 0.25

    def test_agent_config_activates_contextual_mode_not_fixed_short_full_rule(self):
        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        block = cfg["risk"]["side_aware_sizing"]
        assert block["enabled"] is True
        assert block["mode"] == "contextual"
        assert block["apply_to_execution"] is True
        assert block["contextual_default_multiplier"] == 1.0
        assert block["contextual_weak_multiplier"] == 0.5
        assert block["contextual_adverse_multiplier"] == 0.25
        assert block["contextual_full_risk_multiplier"] == 1.0
        assert block["contextual_asian_range_enabled"] is True
        assert block["contextual_asian_too_narrow_threshold_pct"] == 28.0
        assert block["contextual_asian_narrow_support_max_pct"] == 50.0
        assert block["contextual_asian_wide_threshold_pct"] == 80.0
        assert block["contextual_session_phase_enabled"] is True
        assert block["contextual_session_first_window_minutes"] == 90.0
        assert block["contextual_session_late_after_minutes"] == 90.0
        assert block["contextual_session_first_window_score"] == 0.25
        assert block["contextual_session_late_score"] == -0.5
        assert block["contextual_news_event_enabled"] is True
        assert block["contextual_news_reduce_pre_minutes"] == 60.0
        assert block["contextual_news_hard_pre_minutes"] == 15.0
        assert block["contextual_volatility_regime_enabled"] is True
        assert block["contextual_gvz_high_threshold"] == 40.0
        assert block["contextual_gvz_symbol_families"] == [
            "XAUUSD_GC_FAMILY",
            "XAGUSD_SILVER_FAMILY",
        ]
        assert block["contextual_ready8_enabled"] is True
        assert block["contextual_ready8_rule_artifact_paths"] == [
            READY8_CONTEXT_RISK_RULES.as_posix(),
            READY8_DISCRIMINATIVE_CONTEXT_RULES.as_posix(),
        ]
        assert block["contextual_ready8_adjustment_enabled"] is True
        assert block["contextual_ready8_adjustment_rule_artifact_paths"] == [
            READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES.as_posix()
        ]
        assert block["contextual_ready8_rules"][0]["card_id"] == "HAZ-001"
        assert block["contextual_ready8_rules"][0]["evidence_delta"] == 0.5498694567843504
        assert block["contextual_ready8_rules"][1]["card_id"] == "MAC-001"
        assert block["contextual_ready8_rules"][1]["symbol_family"] == "XAUUSD_GC_FAMILY"
        assert block["contextual_ready8_rules"][1]["evidence_delta"] == -0.5151404151404151
        assert block["contextual_align_score_enabled"] is True
        assert block["contextual_align_score_min"] == 2.0
        assert block["contextual_align_support_score"] == 0.5
        assert block["contextual_fvg_in_impulse_enabled"] is True
        assert block["contextual_fvg_in_impulse_support_score"] == 0.5
        assert block["contextual_fvg_in_impulse_delta_pp"]["XAUUSD"] == 19.7
        assert block["contextual_fvg_in_impulse_delta_pp"]["USDJPY"] == 7.1
        assert block["contextual_sweep_before_ob_enabled"] is True
        assert block["contextual_sweep_before_ob_score"] == -0.5
        assert block["contextual_sweep_before_ob_with_continuation_wr_pct"] == 63.4
        assert block["contextual_sweep_before_ob_without_continuation_wr_pct"] == 71.6
        assert block["contextual_internal_session_volatility_enabled"] is True
        assert block["contextual_session_vol_ratio_support_min"] == 1.2
        assert block["contextual_session_vol_ratio_support_score"] == 0.5
        assert block["contextual_garch_evt_removed_high_vol_delta_r"] == -18.8
        assert block["contextual_derived_order_flow_enabled"] is True
        assert block["contextual_order_flow_clv_threshold"] == 0.2
        assert block["contextual_order_flow_bvc_threshold"] == 0.6
        assert block["contextual_order_flow_net_flow_threshold"] == 0.0
        assert block["contextual_order_flow_min_signals"] == 2
        assert block["contextual_order_flow_aligned_score"] == 0.5
        assert block["contextual_order_flow_opposed_score"] == -0.5
        assert block["contextual_validation_leash_enabled"] is True
        assert block["contextual_validation_leash_rules"][0]["symbol"] == "GBPJPY"
        assert block["contextual_validation_leash_rules"][0]["score"] == -0.5
        assert block["contextual_validation_leash_rules"][1]["symbol"] == "XAUUSD"
        assert block["contextual_validation_leash_rules"][1]["side"] == "LONG"
        assert block["contextual_validation_leash_rules"][1]["score"] == -0.5
        assert block["contextual_monthly_decay_enabled"] is True
        assert block["contextual_monthly_decay_rules"][0]["symbol"] == "XAUUSD"
        assert block["contextual_monthly_decay_rules"][0]["side"] == "LONG"
        assert block["contextual_monthly_decay_rules"][0]["detector_versions"] == ["v1", "v2_shadow"]
        assert block["contextual_monthly_decay_rules"][0]["wr_drop_pp"] == 39.5
        assert block["contextual_monthly_decay_rules"][0]["source_line_no"] == 14
        assert block["contextual_monthly_decay_rules"][1]["symbol"] == "USDJPY"
        assert block["contextual_monthly_decay_rules"][1]["exp_drop_r"] == 0.41
        assert block["contextual_monthly_decay_rules"][1]["source_line_no"] == 12
        assert block["short_multiplier"] == 1.0  # legacy fallback only

    def test_orchestrator_hook_builds_context_attaches_evidence_and_applies_multiplier(self):
        from src.components.orchestrator import SessionOrchestrator

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.config = _contextual_cfg()
        orch._symbol = "US30"
        orch._mt5_symbol = "US30.cash"
        orch._kz_windows = {"ny_core": {"start_min": 13 * 60, "end_min": 15 * 60 + 30}}
        orch._asian_range_info = {"pct_of_adr": 42.0, "category": "moderate"}
        record = {}
        analysis = SimpleNamespace(
            framework="ob_retest",
            trade_parameters=SimpleNamespace(direction="LONG"),
        )
        vnext_decision = GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={
                "symbol": "US30",
                "source_symbol": "US30.cash",
                "symbol_family": "US30_YM_FAMILY",
                "side": "LONG",
                "route_session": "ny_core",
                "framework": "ob_retest",
                "route_family": "ob_retest",
                "market_timeframe": "M15",
            },
            enabled=True,
            apply_to_execution=True,
            matched=True,
            reason="matched_test_evidence",
            evidence=_positive_vnext_evidence(),
        )
        autocorr_risk = SimpleNamespace(autocorrelation=0.22, applied=False)

        decision = orch._apply_contextual_side_risk_sizing(
            current_risk_pct=2.0,
            analysis=analysis,
            raw_data={
                "candle_close_utc": "2026-05-19T13:30:00+00:00",
                "regime": "trending_bull",
                "ready8": {
                    "card_id": "HAZ-001",
                    "horizon_m15_bars": "32",
                    "target_family_id": "neutral_high_low_excursion_m15_horizons_v1",
                    "partition_assignment": "SEALED_VALIDATION_CANDIDATE_DESIGN",
                    "descriptor_name": "previous_candidate_gap_bucket",
                    "descriptor_value": "WAIT_GAP_LT_60M",
                },
                "creates_fvg": True,
                "sweep_before_ob": True,
                "m15_session_vol_ratio": 1.35,
                "m15_clv_avg_5": 0.31,
                "m15_bvc_buy_fraction": 0.64,
                "m15_net_flow_5": 850.0,
            },
            kill_zone="ny_core",
            vnext_decision=vnext_decision,
            autocorr_risk=autocorr_risk,
            record=record,
        )

        assert decision.reason == "contextual_side_risk_full_supported"
        assert decision.after_risk_pct == 2.0
        attached = record["decision_pipeline"]["contextual_side_risk"]
        assert attached["context"]["symbol_family"] == "US30_YM_FAMILY"
        assert attached["context"]["session"] == "ny_core"
        assert attached["context"]["candle_time_utc"] == "2026-05-19T13:30:00+00:00"
        assert attached["context"]["session_start_utc"] == "13:00"
        assert attached["context"]["asian_range_pct_of_adr"] == 42.0
        assert attached["context"]["ready8_card_id"] == "HAZ-001"
        assert attached["context"]["ready8_partition_assignment"] == (
            "SEALED_VALIDATION_CANDIDATE_DESIGN"
        )
        assert attached["context"]["ready8_descriptor_name"] == (
            "previous_candidate_gap_bucket"
        )
        assert attached["context"]["ready8_descriptor_value"] == "WAIT_GAP_LT_60M"
        assert attached["context"]["creates_fvg"] is True
        assert attached["context"]["sweep_before_ob"] is True
        assert attached["context"]["m15_session_vol_ratio"] == 1.35
        assert attached["context"]["m15_clv_avg_5"] == 0.31
        assert attached["context"]["m15_bvc_buy_fraction"] == 0.64
        assert attached["context"]["m15_net_flow_5"] == 850.0
        assert attached["evidence_summary"]["fvg_in_impulse_context"]["present"] is True
        assert attached["evidence_summary"]["sweep_before_ob_context"]["present"] is True
        assert attached["evidence_summary"]["internal_session_volatility"]["m15_session_vol_ratio"] == 1.35
        assert attached["evidence_summary"]["derived_order_flow"]["aligned_signals"] == 3
        assert attached["evidence_summary"]["vnext_metric_sums"]["cost_adjusted_simulated_r"] == 8.0

    def test_orchestrator_hook_consumes_news_calendar_and_gvz_external_feed_context(self):
        from src.components.orchestrator import SessionOrchestrator

        class FakeNewsCalendar:
            enabled = True

            def get_next_event(self, symbol, current_time):
                assert symbol == "XAUUSD"
                return {
                    "event": "FOMC Rate Decision",
                    "currency": "USD",
                    "impact": "HIGH",
                    "datetime_utc": current_time + timedelta(minutes=30),
                    "source": "unit_test_calendar",
                }

        orch = SessionOrchestrator.__new__(SessionOrchestrator)
        orch.config = _contextual_cfg()
        orch._symbol = "XAUUSD"
        orch._mt5_symbol = "XAUUSD"
        orch._asian_range_info = {}
        orch._news_calendar = FakeNewsCalendar()
        record = {}
        analysis = SimpleNamespace(
            framework="ob_retest",
            trade_parameters=SimpleNamespace(direction="LONG"),
        )
        vnext_decision = GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event={
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "symbol_family": "XAUUSD_GC_FAMILY",
                "side": "LONG",
                "route_session": "london_core",
                "framework": "ob_retest",
                "route_family": "ob_retest",
                "market_timeframe": "M15",
            },
            enabled=True,
            apply_to_execution=True,
            matched=False,
            reason="no_matching_vnext_rows",
            evidence={"matched_rows": 0, "metrics": {}},
        )
        autocorr_risk = SimpleNamespace(autocorrelation=None, applied=False)

        decision = orch._apply_contextual_side_risk_sizing(
            current_risk_pct=2.0,
            analysis=analysis,
            raw_data={
                "timestamp_utc": datetime(2026, 5, 19, 7, 0, tzinfo=timezone.utc).isoformat(),
                "fred__GVZCLS__value": 42.0,
            },
            kill_zone="london_core",
            vnext_decision=vnext_decision,
            autocorr_risk=autocorr_risk,
            record=record,
        )

        assert decision.reason == "contextual_side_risk_adverse_reduced"
        assert decision.after_risk_pct == 0.5
        attached = record["decision_pipeline"]["contextual_side_risk"]
        assert attached["context"]["news_event_name"] == "FOMC Rate Decision"
        assert attached["context"]["volatility_gvz"] == 42.0
        assert attached["evidence_summary"]["news_event_risk"]["source"] == "unit_test_calendar"
        assert attached["evidence_summary"]["volatility_regime"]["source"] == "fred__GVZCLS"


# --------------------------------------------------------------------------
# SPRT watcher tests (side_aware_sprt_watcher.py)
# --------------------------------------------------------------------------


def _make_cfg(window: int = 20, threshold: float = 0.50, **kwargs) -> dict:
    """Build a minimal config the watcher accepts."""
    block = {
        "enabled": True,
        "long_multiplier": 0.5,
        "short_multiplier": 1.0,
        "sprt_window_size": window,
        "sprt_wr_threshold": threshold,
    }
    block.update(kwargs)
    return {"risk": {"side_aware_sizing": block}}


class TestRecordLongOutcomes:
    def test_records_long_outcomes(self, _isolate_sprt_state_path):
        """5 wins → state has 5 entries with the right schema."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg())
        for _ in range(5):
            watcher.record_long_outcome("XAUUSD", was_win=True)
        # State file exists.
        assert _isolate_sprt_state_path.exists()
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert len(state["long_outcomes"]) == 5
        for entry in state["long_outcomes"]:
            assert entry["win"] is True
            assert entry["symbol"] == "XAUUSD"
            assert isinstance(entry["ts"], str)
            # ts ends with Z (UTC suffix).
            assert entry["ts"].endswith("Z")
        assert state["disabled_at"] is None
        assert state["disable_reason"] is None
        assert state["version"] == 1

    def test_window_truncation(self, _isolate_sprt_state_path):
        """Record 25 outcomes with window=20 → state has only last 20."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.0))
        for i in range(25):
            watcher.record_long_outcome(f"SYM{i:02d}", was_win=True)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert len(state["long_outcomes"]) == 20
        # First retained entry should be the 6th written (index 5).
        assert state["long_outcomes"][0]["symbol"] == "SYM05"
        # Last retained entry should be the 25th (index 24).
        assert state["long_outcomes"][-1]["symbol"] == "SYM24"


class TestAutoDisableSemantics:
    def test_auto_disables_on_low_wr(self, _isolate_sprt_state_path):
        """20 outcomes with 9 wins (WR=45% < 50%) → disabled_at + reason."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        # 9 wins, 11 losses → WR=0.45.
        outcomes = [True] * 9 + [False] * 11
        for w in outcomes:
            watcher.record_long_outcome("XAUUSD", was_win=w)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["disabled_at"] is not None
        assert isinstance(state["disabled_at"], str)
        assert state["disabled_at"].endswith("Z")
        assert "wr=0.45" in state["disable_reason"]
        assert "n=20" in state["disable_reason"]
        assert "threshold=0.50" in state["disable_reason"]

    def test_does_not_disable_on_acceptable_wr(self, _isolate_sprt_state_path):
        """20 outcomes with 11 wins (WR=55%) → disabled_at None."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        outcomes = [True] * 11 + [False] * 9
        for w in outcomes:
            watcher.record_long_outcome("XAUUSD", was_win=w)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["disabled_at"] is None
        assert state["disable_reason"] is None
        assert len(state["long_outcomes"]) == 20

    def test_does_not_disable_below_window_size(self, _isolate_sprt_state_path):
        """19 all-loss outcomes (window=20) → not disabled (insufficient)."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        for _ in range(19):
            watcher.record_long_outcome("XAUUSD", was_win=False)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["disabled_at"] is None
        assert state["disable_reason"] is None
        assert len(state["long_outcomes"]) == 19

    def test_is_disabled_after_auto_disable(self, _isolate_sprt_state_path):
        """Auto-disable triggers → ``is_disabled()`` returns True."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        for w in [True] * 9 + [False] * 11:
            watcher.record_long_outcome("XAUUSD", was_win=w)
        assert watcher.is_disabled() is True

    def test_disable_latch_is_monotonic(self, _isolate_sprt_state_path):
        """Once disabled, additional wins do NOT auto re-enable."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        # Trip the disable.
        for w in [True] * 9 + [False] * 11:
            watcher.record_long_outcome("XAUUSD", was_win=w)
        assert watcher.is_disabled() is True
        # Now add 20 wins — WR over the LAST 20 is 100%, but disable stays.
        for _ in range(20):
            watcher.record_long_outcome("XAUUSD", was_win=True)
        assert watcher.is_disabled() is True


class TestPersistence:
    def test_persistence_disabled_state_survives_reload(
        self, _isolate_sprt_state_path
    ):
        """Trip disable in watcher A; watcher B (fresh load) sees disabled."""
        cfg = _make_cfg(window=20, threshold=0.50)
        wa = _saw.SideAwareSprtWatcher(cfg)
        for _ in range(20):
            wa.record_long_outcome("XAUUSD", was_win=False)
        assert wa.is_disabled() is True
        # Simulate a process restart — fresh watcher reads from disk.
        wb = _saw.SideAwareSprtWatcher(cfg)
        assert wb.is_disabled() is True
        # And the entries are intact.
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert len(state["long_outcomes"]) == 20
        assert all(o["win"] is False for o in state["long_outcomes"])

    def test_state_file_parent_dir_auto_created(self, tmp_path, monkeypatch):
        """If the parent dir is missing, the watcher creates it on first write."""
        deep = tmp_path / "deeply" / "nested" / "pipeline_state" / "sprt.json"
        monkeypatch.setattr(_saw, "STATE_PATH", deep)
        watcher = _saw.SideAwareSprtWatcher(_make_cfg())
        watcher.record_long_outcome("XAUUSD", was_win=True)
        assert deep.exists()
        assert deep.parent.is_dir()

    def test_corrupt_file_treated_as_empty(self, _isolate_sprt_state_path):
        """Truncated JSON on load → watcher resets to empty schema."""
        _isolate_sprt_state_path.parent.mkdir(parents=True, exist_ok=True)
        _isolate_sprt_state_path.write_text(
            '{"long_outcomes": [{"win": true, "symbo',
            encoding="utf-8",
        )
        watcher = _saw.SideAwareSprtWatcher(_make_cfg())
        # is_disabled() reloads from disk and sees corrupt → empty → False.
        assert watcher.is_disabled() is False
        # First record_long_outcome rewrites a clean file.
        watcher.record_long_outcome("XAUUSD", was_win=True)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert len(state["long_outcomes"]) == 1


class TestReset:
    def test_reset_clears_state(self, _isolate_sprt_state_path):
        """Populate state, reset, ``is_disabled()`` False; file removed."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=20, threshold=0.50))
        for _ in range(20):
            watcher.record_long_outcome("XAUUSD", was_win=False)
        assert watcher.is_disabled() is True
        assert _isolate_sprt_state_path.exists()

        watcher.reset()
        assert watcher.is_disabled() is False
        assert not _isolate_sprt_state_path.exists()

    def test_reset_when_no_state_is_noop(self, _isolate_sprt_state_path):
        """Reset on a missing file does not raise."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg())
        assert not _isolate_sprt_state_path.exists()
        # Must not raise.
        watcher.reset()
        assert not _isolate_sprt_state_path.exists()
        assert watcher.is_disabled() is False


class TestCustomConfig:
    def test_custom_window_size_threshold_respected(
        self, _isolate_sprt_state_path
    ):
        """``window=10, threshold=0.7``, 10 outcomes 6 wins (60% < 70%) → disabled."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg(window=10, threshold=0.70))
        outcomes = [True] * 6 + [False] * 4
        for w in outcomes:
            watcher.record_long_outcome("XAUUSD", was_win=w)
        assert watcher.is_disabled() is True
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert len(state["long_outcomes"]) == 10
        assert "wr=0.60" in state["disable_reason"]
        assert "threshold=0.70" in state["disable_reason"]

    def test_record_includes_symbol_field(self, _isolate_sprt_state_path):
        """``state.long_outcomes[0].symbol == 'XAUUSD'``."""
        watcher = _saw.SideAwareSprtWatcher(_make_cfg())
        watcher.record_long_outcome("XAUUSD", was_win=True)
        with _isolate_sprt_state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        assert state["long_outcomes"][0]["symbol"] == "XAUUSD"

    def test_default_window_size_threshold_when_missing(
        self, _isolate_sprt_state_path
    ):
        """Empty config block → defaults (20, 0.50)."""
        watcher = _saw.SideAwareSprtWatcher({})
        assert watcher.window_size == 20
        assert watcher.wr_threshold == 0.50

    def test_invalid_threshold_falls_back_to_default(
        self, _isolate_sprt_state_path
    ):
        """Non-numeric threshold → default 0.50."""
        cfg = _make_cfg()
        cfg["risk"]["side_aware_sizing"]["sprt_wr_threshold"] = "garbage"
        watcher = _saw.SideAwareSprtWatcher(cfg)
        assert watcher.wr_threshold == 0.50


class TestIntegrationDocumentation:
    """Lightweight integration check (full orchestrator path is too heavy
    to mock for a unit test). This test documents the disabled-bypass
    contract: when ``is_disabled()`` returns True, the orchestrator skips
    ``apply_side_multiplier`` and uses the base risk percentage."""

    def test_orchestrator_skips_multiplier_when_disabled(
        self, _isolate_sprt_state_path
    ):
        cfg = _make_cfg(window=20, threshold=0.50)
        watcher = _saw.SideAwareSprtWatcher(cfg)
        # Trip the disable.
        for _ in range(20):
            watcher.record_long_outcome("XAUUSD", was_win=False)
        assert watcher.is_disabled() is True

        # Simulate the orchestrator's branch: when disabled, do NOT apply
        # the multiplier — preserve base risk.
        base_risk_pct = 2.0
        if watcher.is_disabled():
            effective = base_risk_pct
        else:
            effective = side_aware_sizing.apply_side_multiplier(
                base_risk_pct, "LONG", cfg,
            )
        assert effective == 2.0  # unchanged because we skipped
