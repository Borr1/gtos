"""Focused tests for the ADV-002 duplicate-key collision source-control route."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROUTE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = load_module("build_scid_anti_boxing_r11_adv_002_2026_05_13.py", "adv002_builder")
verifier = load_module("verify_scid_anti_boxing_r11_adv_002_2026_05_13.py", "adv002_verifier")


def test_adv002_input_row_preserves_safe_flags() -> None:
    inventory = builder.load_json(builder.INPUTS["route_family_inventory"])
    row = builder.extract_adv_row(inventory)
    assert row["route_family_id"] == "ADV-002"
    assert row["science_domain"] == "adversarial_baselines_placebos"
    assert row["may_open_outcomes_or_results_in_this_route"] is False
    assert row["opens_broker_account_order_history_deal_position_evidence"] is False
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_duplicate_policy_covers_collision_classes_without_results() -> None:
    policy = builder.build_duplicate_policy()
    classes = {row["class"] for row in policy["collision_classes"]}
    assert "cross_card_duplicate" in classes
    assert "session_symbol_timeframe_collision" in classes
    assert "hash_eol_equivalent_text_duplicate" in classes
    assert policy["may_open_outcomes_or_results_in_this_route"] is False
    assert "outcomes" in policy["canonical_row_hierarchy"][-1]


def test_source_contracts_cover_required_source_requirements() -> None:
    searched = {
        "aggregate_term_hits": {
            "candidate_id": 1,
            "duplicate_key": 1,
            "source_hash": 1,
            "group_membership_version": 1,
            "collision_policy": 1,
        }
    }
    inventory = builder.load_json(builder.INPUTS["route_family_inventory"])
    row = builder.extract_adv_row(inventory)
    contracts = builder.build_source_contract_ledger(row, searched)
    requirements = {item["requirement"] for item in contracts["contracts"]}
    assert {"candidate id", "duplicate key", "source hash", "group membership version", "collision policy"} <= requirements
    group_contract = next(item for item in contracts["contracts"] if item["requirement"] == "group membership version")
    assert group_contract["status"] == "PARTIAL_LOCAL_EVIDENCE_EXACT_FIELD_BLOCKER"


def test_verifier_accepts_generated_artifacts_after_closeout() -> None:
    result = verifier.verify(mark_focused_tests_ok=False)
    assert result["ok"], result["failures"]
    assert result["can_mark_goal_complete"] is True


def test_output_manifest_hashes_match_non_self_artifacts() -> None:
    verifier.verify(mark_focused_tests_ok=False)
    manifest_path = ROUTE_DIR / "SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repo_root = ROUTE_DIR.parents[3]

    mismatches = []
    for row in manifest["files"]:
        path = repo_root / row["path"]
        if path.resolve() == manifest_path.resolve():
            assert row["sha256"] is None
            assert "self-referential" in row["self_hash_policy"]
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if row["sha256"] != actual:
            mismatches.append((row["path"], row["sha256"], actual))
    assert mismatches == []
