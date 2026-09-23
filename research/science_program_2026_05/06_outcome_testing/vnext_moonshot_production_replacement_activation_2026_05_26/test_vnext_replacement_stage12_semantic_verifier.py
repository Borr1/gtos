from __future__ import annotations

import json
import subprocess
import sys
import hashlib
from pathlib import Path

import pytest
import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"


def _read_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def _assert_selector_truth_matches_artifacts(result: dict, selector_summary: dict) -> None:
    selector = result["stage13_full_moonshot_production_selector"]
    metrics = selector_summary["combined_production_selector_metrics"]
    assert selector["combined_selected_rows"] == selector_summary["combined_selected_rows"]
    assert selector["old_three_selected_rows"] == selector_summary["old_three_selected_rows"]
    assert (
        selector["broader_origin_selected_rows"]
        == selector_summary["broader_origin_selected_rows"]
    )
    assert selector["total_r"] == metrics["total_r"]
    assert selector["expectancy_r"] == metrics["expectancy_r"]
    assert selector["profit_factor"] == metrics["profit_factor"]
    assert selector["win_rate"] == metrics["win_rate"]


def _load_stage12_verifier_module():
    import importlib.util

    verifier_path = ROUTE_DIR / "verify_vnext_replacement_stage12_semantic_red_team.py"
    spec = importlib.util.spec_from_file_location("stage12_semantic_verifier", verifier_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_route_module(filename: str, module_name: str):
    import importlib.util

    module_path = ROUTE_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stage12_passes_after_repaired_activation_slice() -> None:
    result = _read_json(f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json")
    selector_summary = _read_json(
        f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
    )
    assert result["status"] == "passed"
    assert result["activation_gate_passed"] is True
    assert result["production_activation_overlay_applied"] is True
    assert (
        result["allowed_final_status_recommendation"]
        == "production_activation_config_overlay_applied_after_semantic_gates"
    )
    assert result["blocking_checks"] == []
    assert result["stage13_activation_repair"]["selected_rows"] > 5000
    assert result["stage13_activation_repair"]["expectancy_r"] > 0
    _assert_selector_truth_matches_artifacts(result, selector_summary)
    assert (
        result["stage13_full_moonshot_production_selector"]["broader_origin_selected_rows"]
        > result["stage13_full_moonshot_production_selector"]["old_three_selected_rows"]
    )
    assert (
        result["same_evidence_class_repair_pursuit"]["delta_scan"]["candidate_rows"]
        == 253234
    )


def test_stage12_rejects_stale_selector_count_drift() -> None:
    result = _read_json(f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json")
    selector_summary = _read_json(
        f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
    )
    drifted = json.loads(json.dumps(result))
    drifted["stage13_full_moonshot_production_selector"][
        "combined_selected_rows"
    ] = selector_summary["combined_selected_rows"] + 1
    with pytest.raises(AssertionError):
        _assert_selector_truth_matches_artifacts(drifted, selector_summary)


def test_stage12_semantic_verifier_failure_exit_is_nonzero() -> None:
    module = _load_stage12_verifier_module()
    assert module._activation_exit_code(True) == 0
    assert module._activation_exit_code(False) != 0


def test_stage12_main_returns_nonzero_for_blocking_check_without_writes(monkeypatch) -> None:
    module = _load_stage12_verifier_module()
    delta_scan = module.DeltaScan()
    delta_scan.candidate_rows = 253234
    delta_scan.aggregate_rows = 1
    monkeypatch.setattr(module, "_scan_delta_ledger", lambda: delta_scan)
    monkeypatch.setattr(
        module,
        "_semantic_checks",
        lambda *args, **kwargs: [
            {
                "failure_class": "forced_negative_fixture",
                "status": "failed_activation_blocker",
            }
        ],
    )
    assert module.main(check_mode=True) == 1


def test_stage12_check_mode_does_not_mutate_route_artifacts() -> None:
    verifier_path = ROUTE_DIR / "verify_vnext_replacement_stage12_semantic_red_team.py"
    write_targets = [
        ROUTE_DIR / f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json",
        ROUTE_DIR / f"VNEXT_REPLACEMENT_SATURATION_SELF_RED_TEAM_{DATE}.md",
        ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json",
        ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json",
        ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl",
    ]
    before = {path: _sha256(path) for path in write_targets}
    completed = subprocess.run(
        [sys.executable, str(verifier_path), "--check"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout[-1000:]
    after = {path: _sha256(path) for path in write_targets}
    assert after == before


def test_output_manifest_verifier_detects_hash_drift(tmp_path) -> None:
    module = _load_route_module(
        "verify_vnext_replacement_output_manifest.py",
        "vnext_output_manifest_verifier",
    )
    artifact = tmp_path / "artifact.json"
    artifact.write_text('{"ok": true}\n', encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "outputs": [
            {
                "path": artifact.name,
                "sha256": "stale",
                "size_bytes": artifact.stat().st_size,
            }
        ]
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    issues = module._verify_entries(
        manifest, manifest_path=manifest_path, route_dir=tmp_path
    )
    assert any(issue["issue"] == "sha256_mismatch" for issue in issues)


def test_route_state_integrity_detects_stale_head_and_completion_contradiction() -> None:
    module = _load_route_module(
        "verify_vnext_replacement_route_state_integrity.py",
        "vnext_route_state_integrity",
    )
    state = {
        "completion_gate_status": {"route_complete": False},
        "current_head": "old",
        "route_complete": True,
        "scoped_commit_proof": {"production_package_commit_sha": "abc123"},
    }
    manifest = {"current_head": "old"}
    issues = module._state_issues(
        state,
        manifest,
        "new head",
        commit_exists=lambda commit: commit == "abc123",
    )
    issue_names = {issue["issue"] for issue in issues}
    assert "state_current_head_stale" in issue_names
    assert "manifest_current_head_stale" in issue_names
    assert "route_complete_internal_contradiction" in issue_names


def test_stage12_behavioral_diff_requires_more_than_config_flags() -> None:
    result = _read_json(f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json")
    diff = result["activation_overlay_behavioral_diff"]
    assert diff["routing_effect_configured"] is True
    assert diff["execution_policy_effect_configured"] is True
    assert diff["prop_governor_effect_configured"] is True
    assert diff["monitoring_output_configured"] is True
    assert diff["replay_decision_effect_proven_positive"] is True
    assert diff["full_moonshot_selector_verified_positive"] is True
    assert diff["production_activation_overlay_applied_in_repo_config"] is True
    assert diff["pass"] is True


def test_stage12_overlay_is_applied_in_config_and_rollback_restores_flags() -> None:
    overlay = yaml.safe_load(
        (ROUTE_DIR / f"VNEXT_REPLACEMENT_CONFIG_OVERLAY_DIFF_{DATE}.yaml").read_text(
            encoding="utf-8"
        )
    )
    config = yaml.safe_load(Path("config/agent_config.yaml").read_text(encoding="utf-8"))
    runtime = config["gtos_vnext_runtime"]
    assert runtime["apply_to_execution"] is True
    assert runtime["moonshot_dynamic_execution_router_apply_to_execution"] is True
    assert runtime["moonshot_dynamic_execution_router_repaired_overlay_selector"] == (
        "full_moonshot_old_three_plus_broader_origin_positive_native_be_after_trigger"
    )
    prod = overlay["semantic_gated_production_activation_overlay_candidate"]["config"][
        "gtos_vnext_runtime"
    ]
    rollback = overlay["rollback_overlay"]["config"]["gtos_vnext_runtime"]
    assert prod["apply_to_execution"] is True
    assert prod["moonshot_dynamic_execution_router_apply_to_execution"] is True
    assert rollback["apply_to_execution"] is False
    assert rollback["moonshot_dynamic_execution_router_apply_to_execution"] is False
    assert rollback["prop_safe_selector_apply_to_execution"] is False
    assert rollback["replacement_ml_apply_to_execution"] is False


def test_stage12_self_red_team_covers_all_prompt_failure_classes() -> None:
    module = _load_stage12_verifier_module()
    result = _read_json(f"VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json")
    red_team = (
        ROUTE_DIR / f"VNEXT_REPLACEMENT_SATURATION_SELF_RED_TEAM_{DATE}.md"
    ).read_text(encoding="utf-8")
    result_failure_classes = {
        check["failure_class"] for check in result["semantic_gate_results"]
    }
    for check in result["semantic_gate_results"]:
        assert check["failure_class"] in red_team
    for required_failure_class in module.REQUIRED_FAILURE_CLASSES:
        assert required_failure_class in result_failure_classes
    assert len(result["semantic_gate_results"]) >= len(module.REQUIRED_FAILURE_CLASSES)
