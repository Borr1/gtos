from __future__ import annotations

import copy
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

import build_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2 as build
import verify_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2 as verify


def test_generated_artifact_bundle_passes_lane18_verifier():
    bundle = build.build_artifacts(write=False)

    result = verify.verify_artifact_bundle(bundle)

    assert result["ok"], result["issues"]


def test_verifier_fails_when_projected_pnl_dominates_broker_truth():
    row = {
        "broker_real_or_proxy_state": "BROKER_REAL",
        "cost_source_reason": "account history deal source",
        "projection_as_broker_truth_allowed": False,
        "projected_pnl": 100.0,
    }

    issues = verify.validate_cost_rows([row])

    assert "cost_row_1_projected_pnl_dominates_broker_truth" in issues


def test_verifier_fails_when_ticket_bound_contract_lacks_ticket_identity():
    contract = build.build_universal_contract("2026-06-01T00:00:00Z")
    bad = copy.deepcopy(contract)
    bad["event_contracts"]["partial_close"]["required_fields"] = [
        "volume",
        "close_price",
        "cost_source_reason",
    ]

    issues = verify.validate_universal_contract(bad)

    assert "ticket_bound_event_missing_identity_field:partial_close" in issues


def test_verifier_fails_when_false_close_classification_is_unmanaged():
    contract = build.build_universal_contract("2026-06-01T00:00:00Z")
    bad = copy.deepcopy(contract)
    bad["false_local_close_required_classifications"] = []

    issues = verify.validate_universal_contract(bad)

    assert "false_local_close_broker_contradiction_classification_missing" in issues


def test_verifier_fails_when_cost_source_reason_is_missing():
    row = {
        "broker_real_or_proxy_state": "SOURCE_GAP",
        "projection_as_broker_truth_allowed": False,
    }

    issues = verify.validate_cost_rows([row])

    assert "cost_row_1_missing_cost_source_reason" in issues


def test_verifier_fails_on_broker_real_proxy_label_confusion():
    row = {
        "broker_real_or_proxy_state": "BROKER_REAL",
        "source_row_type": "symbol_spread_snapshot_cost_proxy",
        "cost_source_reason": "proxy projection reused as broker truth",
        "projection_as_broker_truth_allowed": False,
    }

    issues = verify.validate_cost_rows([row])

    assert "cost_row_1_broker_real_proxy_label_confusion" in issues


def test_verifier_fails_on_generic_summary_source_gap():
    row = {
        "source_gap_id": "gap1",
        "symbol": "XAUUSD",
        "lifecycle_surface": "cost",
        "source_surface": "cost",
        "field": "generic_cost_gap",
        "missing_source_class": "GENERIC",
        "source_state": "generic missing cost",
        "recoverability": "unknown",
        "required_action": "fix later",
        "proof_required": "proof",
        "proxy_policy": "explicit_proxy_only_never_broker_truth",
        "source_refs": ["source.jsonl:1"],
    }

    issues = verify.validate_source_gap_rows([row])

    assert any("generic_cost_gap_not_allowed" in issue for issue in issues)
