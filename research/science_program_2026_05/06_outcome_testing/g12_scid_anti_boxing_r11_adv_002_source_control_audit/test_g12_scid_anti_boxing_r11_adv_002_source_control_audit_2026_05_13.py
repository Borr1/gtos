"""Focused tests for the G12 ADV-002 source-control audit package."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT"
DATE_TAG = "2026-05-13"
TERMINAL_DECISION = "ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY"


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROUTE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


builder = load_module("build_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py", "g12_adv002_builder")
verifier = load_module("verify_g12_scid_anti_boxing_r11_adv_002_source_control_audit_2026_05_13.py", "g12_adv002_verifier")


def artifact(stem: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"


def test_decision_accepts_source_control_only() -> None:
    decision = json.loads(artifact("DECISION_LEDGER").read_text(encoding="utf-8"))
    assert decision["terminal_decision"] == TERMINAL_DECISION
    assert decision["terminal_blockers"] == []
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation"] is False
    assert decision["accepted_results_or_performance"] is False
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_repair_ledger_closes_manifest_hash_issue() -> None:
    repair = json.loads(artifact("REPAIR_LEDGER").read_text(encoding="utf-8"))
    assert repair["post_repair_manifest_mismatch_count"] == 0
    assert repair["post_repair_target_verifier_ok"] is True
    assert repair["post_repair_target_focused_tests_ok"] is True
    assert {row["status"] for row in repair["repairs"]} == {"CLOSED"}


def test_exact_requirement_rows_are_specific() -> None:
    requirements = json.loads(artifact("EXACT_REQUIREMENT_ROWS").read_text(encoding="utf-8"))
    ids = {row["requirement_row_id"] for row in requirements["rows"]}
    assert ids == {
        "ADV002-REQ-CANDIDATE-ID",
        "ADV002-REQ-DUPLICATE-KEY",
        "ADV002-REQ-SOURCE-HASH",
        "ADV002-REQ-GROUP-MEMBERSHIP",
        "ADV002-REQ-COLLISION-POLICY",
        "ADV002-REQ-ASOF-NOLEAK",
        "ADV002-REQ-CAPTURE-ROWS",
    }
    assert requirements["vague_blockers"] == []
    for row in requirements["rows"]:
        assert row["future_fail_closed_if_missing"]


def test_output_manifest_hashes_match_non_self_artifacts() -> None:
    verifier.verify(mark_focused_tests_ok=False)
    manifest_path = artifact("OUTPUT_MANIFEST")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repo_root = ROUTE_DIR.parents[3]
    mismatches = []
    for row in manifest["artifacts"]:
        path = repo_root / row["path"]
        if path.resolve() in {manifest_path.resolve(), manifest_path.with_suffix(".md").resolve()}:
            assert row["sha256"] is None
            assert "self-referential" in row["self_hash_policy"]
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if row["sha256"] != actual:
            mismatches.append((row["path"], row["sha256"], actual))
    assert mismatches == []


def test_verifier_accepts_generated_audit_package() -> None:
    result = verifier.verify(mark_focused_tests_ok=False)
    assert result["ok"], result["failures"]
    assert result["terminal_decision"] == TERMINAL_DECISION
    assert result["can_mark_goal_complete"] is True
