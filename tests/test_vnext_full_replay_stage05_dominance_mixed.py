from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/science_program_2026_05/06_outcome_testing/"
    / "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    / "build_vnext_full_replay_stage05_dominance_mixed_2026_05_24.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("stage05_dominance_mixed", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_counterfactual_removing_dominant_family_changes_decision():
    m = load_module()
    row = {
        "evidence_family": "family_a",
        "source_component": "component_a",
        "action_class": "avoid_filter",
        "decision": "AVOID",
        "event_scope": {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "side": "SHORT",
            "market_timeframe": "M15",
            "route_session": "london",
        },
        "metrics": {"proxy_score": {"sum": -3}},
    }
    trace = {
        "candidate_id": "cand_1",
        "runtime_trace_id": "trace_1",
        "runtime_event_cache_id": "cache_1",
        "runtime_mode": "hypothetical_activated_vnext",
        "runtime_input_event": {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "side": "SHORT",
            "market_timeframe": "M15",
            "route_session": "london",
        },
        "route_decision": {"decision": "AVOID"},
    }
    cache = {"route_decision": {"evidence": {"rows": [row]}}}

    variants, dominance, _details = m.counterfactuals_for_surface("route_decision", trace, cache)

    assert dominance["dominant_evidence_family"] == "family_a"
    assert variants["all_evidence"]["decision"] == "AVOID"
    assert variants["dominant_family_removed"]["decision"] == "LEGACY"
    assert variants["dominant_family_removed"]["changed_decision"] is True


def test_evidence_row_classification_separates_broad_stale_and_source_bound():
    m = load_module()
    event = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "side": "LONG",
        "market_timeframe": "M15",
        "route_session": "london",
    }
    source_bound = {
        "evidence_family": "current_replay",
        "event_scope": {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "side": "LONG",
            "market_timeframe": "M15",
            "route_session": "london_core",
        },
    }
    stale = {
        "evidence_family": "legacy_v2_v3_paper_live_friction",
        "event_scope": source_bound["event_scope"],
    }
    broad = {"evidence_family": "all_sessions_context", "event_scope": {}}

    assert m.classify_evidence_row(source_bound, event)["current_source_bound"] is True
    assert m.classify_evidence_row(stale, event)["stale_legacy"] is True
    assert m.classify_evidence_row(broad, event)["broad_unanchored"] is True


def test_mixed_resolution_source_required_becomes_guard():
    m = load_module()
    stats = {
        "baseline_decision_counts": {"MIXED": 10},
        "classification_counts": {"UNKNOWN": 10},
        "best_r_sum": 5.0,
        "best_r_count": 10,
        "source_required_rows": 3,
        "broad_unanchored_rows": 0,
        "stale_legacy_rows": 0,
        "variant_change_count": 0,
    }

    resolution, rationale = m.classify_mixed_resolution(stats)

    assert resolution == "source_required_and_guarded"
    assert "source-acquisition guard" in rationale
