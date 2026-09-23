"""Known-answer and refusal tests for Session HK's metadata-only tools.

Set ``HK_REPO_ROOT`` to run these exact test bytes against another immutable
repository node.  The tests do not import runtime, config, broker, or MT5 code.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest


REPO = Path(os.environ.get("HK_REPO_ROOT", Path(__file__).resolve().parents[2])).resolve()
TEST_SOURCE_REPO = Path(__file__).resolve().parents[2]
RECEIPTS = REPO / "docs/audits/fable5-vision-audit-20260725/phase20/receipts"


def _tool_path(name: str) -> Path:
    """Resolve a relocated tool against the SELECTED repo's layout.

    At HEAD the tools live in src/research_infra/ (A0 relocation); older nodes
    reachable via HK_REPO_ROOT carry them under docs/.../receipts/.
    """
    for candidate in (REPO / "src/research_infra" / name, RECEIPTS / name):
        if candidate.is_file():
            return candidate
    return REPO / "src/research_infra" / name


S0_PATH = _tool_path("wave20_source_inventory.py")
B0_PATH = _tool_path("verify_wave20_breaker_branch.py")


def _load(path: Path, name: str):
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S0 = _load(S0_PATH, "session_hk_source_inventory")
B0 = _load(B0_PATH, "session_hk_breaker_router")
PARENT = "1" * 40


def _require(module):
    assert module is not None, "Session HK implementation is absent at HK_REPO_ROOT"
    return module


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minimal_plan(path: Path, artifact_path: str, digest: str) -> Path:
    nodes = [
        {
            "id": node,
            "prerequisite_artifacts": [{"path": artifact_path, "sha256": digest}],
        }
        for node in ("O1", "B1", "C0", "N1", "F1", "K1", "P1")
    ]
    path.write_text(json.dumps({"dag": {"nodes": nodes}}), encoding="utf-8")
    return path


def _synthetic_b0(tmp_path: Path, *, mutate_hdf=None, mutate_plan=None):
    hdf = json.loads((RECEIPTS / "SESSION_HDF_COMPLETE.json").read_text(encoding="utf-8"))
    family = json.loads(
        (
            REPO
            / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/"
            "CANDIDATE_FAMILY_V27.json"
        ).read_text(encoding="utf-8")
    )
    if mutate_hdf:
        mutate_hdf(hdf)
    hdf_path = tmp_path / "SESSION_HDF_COMPLETE.json"
    family_path = tmp_path / "CANDIDATE_FAMILY_V27.json"
    hdf_path.write_text(json.dumps(hdf), encoding="utf-8")
    family_path.write_text(json.dumps(family), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=HK Test",
            "-c",
            "user.email=redacted@example.com",
            "add",
            hdf_path.name,
            family_path.name,
        ],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=HK Test",
            "-c",
            "user.email=redacted@example.com",
            "commit",
            "-q",
            "-m",
            "synthetic authority",
        ],
        cwd=tmp_path,
        check=True,
    )
    authority_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    b0 = {
        "id": "B0",
        "prerequisite_artifacts": [
            {
                "path": authority_commit + ":SESSION_HDF_COMPLETE.json",
                "sha256": _digest(hdf_path),
            },
            {"path": "CANDIDATE_FAMILY_V27.json", "sha256": _digest(family_path)},
        ],
        "family_denominator": {
            "family": "CANDIDATE_BOOK_V1_V27",
            "member": "cq_current_breaker_re_entry_inverted_5d_stop_0p25d",
            "all_declared": 59,
            "looks_taken": 57,
            "other_p_values": "58 padded at 1.0",
            "alpha": 0.1,
            "gate_option": "B_balanced",
            "population": "RECORDED",
        },
    }
    plan = {"dag": {"nodes": [b0]}}
    if mutate_plan:
        mutate_plan(plan)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return hdf_path, plan_path


def test_implementation_imports_are_bound_to_selected_repository():
    for module in (_require(S0), _require(B0)):
        assert Path(module.__file__).resolve().is_relative_to(REPO)
    assert TEST_SOURCE_REPO == Path(__file__).resolve().parents[2]


def test_s0_known_answer_reports_every_declared_entry_without_pool(tmp_path):
    module = _require(S0)
    artifact = tmp_path / "authority.json"
    artifact.write_text(
        json.dumps({"schema": "known.answer.v1", "window": ["2026-01-01", "2026-01-30"]}),
        encoding="utf-8",
    )
    plan = _minimal_plan(tmp_path / "plan.json", "authority.json", _digest(artifact))
    receipt = module.build_inventory(
        plan_path=plan,
        repo_root=tmp_path,
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["status"] == "SOURCE_INVENTORY_BOUND"
    assert receipt["denominator"] == {
        "nodes": ["O1", "B1", "C0", "N1", "F1", "K1", "P1"],
        "declared_entries": 7,
        "reported_entries": 7,
        "silent_omissions": 0,
    }
    assert receipt["counts"] == {"present": 7, "absent": 0, "conflicting": 0, "forbidden": 0}
    assert receipt["boundaries"]["candidate_pool_created"] is False
    assert receipt["boundaries"]["economic_aggregations"] == 0


@pytest.mark.parametrize(
    ("path", "role", "reason"),
    [
        ("captures/2026-03-01/outcomes.json", "metadata_only", "march_path_refused"),
        ("captures/live_forward/outcomes.json", "metadata_only", "live_forward_path_refused"),
        ("captures/2026-02/economics.json", "economics", "february_economics_refused"),
    ],
)
def test_s0_refuses_forbidden_paths_before_touch(path, role, reason):
    module = _require(S0)
    assert module.path_policy(path, role=role).startswith(reason)


def test_s0_allows_february_attribution_metadata_only():
    module = _require(S0)
    assert module.path_policy("captures/2026-02/attribution.json", role="attribution_only") is None


def test_s0_refuses_outcome_metadata_key_requests():
    module = _require(S0)
    with pytest.raises(module.InventoryRefusal, match="outcome_metadata_key_refused"):
        module.validate_metadata_keys(("schema", "net_r"))


def test_s0_hash_conflict_is_explicit_and_not_rejection(tmp_path):
    module = _require(S0)
    artifact = tmp_path / "authority.json"
    artifact.write_text('{"schema":"known.answer.v1"}', encoding="utf-8")
    plan = _minimal_plan(tmp_path / "plan.json", "authority.json", "0" * 64)
    receipt = module.build_inventory(
        plan_path=plan,
        repo_root=tmp_path,
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["status"] == "SOURCE_AUTHORITY_CONFLICT_STOP"
    assert receipt["counts"]["conflicting"] == 7
    assert all(row["absence_is_rejection"] is False for row in receipt["entries"])


def test_s0_accepts_only_exact_g0_hash_supersession(tmp_path):
    module = _require(S0)
    artifact = tmp_path / "authority.json"
    artifact.write_text('{"schema":"known.answer.v2"}', encoding="utf-8")
    frozen_sha = "0" * 64
    integrated_sha = _digest(artifact)
    plan = _minimal_plan(tmp_path / "plan.json", "authority.json", frozen_sha)
    receipt = module.build_inventory(
        plan_path=plan,
        repo_root=tmp_path,
        authority_supersessions={
            "authority.json": {
                "path": "authority.json",
                "frozen_preregistration_sha256": frozen_sha,
                "integrated_source_sha256": integrated_sha,
                "authority": "synthetic_exact_g0_binding",
            }
        },
        g0_binding={"path": "g0.json", "sha256": "2" * 64, "status": "PASS"},
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["status"] == "SOURCE_INVENTORY_BOUND"
    assert receipt["counts"]["present"] == 7
    assert all(
        row["reason"] == "sha256_superseded_by_exact_g0_integrated_source"
        for row in receipt["entries"]
    )


def test_s0_missing_placeholder_names_exact_prerequisite(tmp_path):
    module = _require(S0)
    plan = _minimal_plan(tmp_path / "plan.json", "SURVIVOR_GATE_RECEIPT", "RESOLVE_AFTER_SURVIVOR")
    receipt = module.build_inventory(
        plan_path=plan,
        repo_root=tmp_path,
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["status"] == "SOURCE_ABSENT_WITH_EXACT_CAPTURE_PREREQUISITE"
    assert receipt["counts"]["absent"] == 7
    assert {row["exact_capture_prerequisite"] for row in receipt["entries"]} == {
        "resolve_placeholder:SURVIVOR_GATE_RECEIPT"
    }


def test_b0_exact_published_receipts_advance_fixed_member_unchanged():
    module = _require(B0)
    receipt = module.route_breaker(
        hdf_path=RECEIPTS / "SESSION_HDF_COMPLETE.json",
        prereg_path=RECEIPTS / "WAVE20_SCIENCE_PREREGISTRATION.json",
        repo_root=REPO,
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["status"] == "HDF_VALIDATED_ADMIT_OBSERVED_ADVANCE_UNCHANGED"
    assert receipt["candidate"]["member"] == "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
    assert receipt["candidate"]["changed_by_router"] is False
    assert receipt["route"]["B1"] == "SKIPPED_BY_PREREGISTERED_BRANCH"
    assert receipt["route"]["breadth_opened"] is False
    assert receipt["observed_prior_disposition"]["economics_recomputed"] is False


def test_b0_refuses_non_admit_hdf_even_when_bytes_are_rebound(tmp_path):
    module = _require(B0)

    def mutate_hdf(hdf):
        hdf["cs_disposition"]["hdc_hdf_capture_anchor"]["verdict"] = "REJECT"

    hdf_path, plan_path = _synthetic_b0(tmp_path, mutate_hdf=mutate_hdf)
    with pytest.raises(module.BreakerRouteRefusal, match="hdf_anchor_verdict_mismatch"):
        module.route_breaker(
            hdf_path=hdf_path,
            prereg_path=plan_path,
            repo_root=tmp_path,
            p1_adapter_exact_parent=PARENT,
        )


def test_b0_refuses_candidate_identity_change(tmp_path):
    module = _require(B0)

    def mutate_plan(plan):
        plan["dag"]["nodes"][0]["family_denominator"]["member"] = "different_candidate"

    hdf_path, plan_path = _synthetic_b0(tmp_path, mutate_plan=mutate_plan)
    with pytest.raises(module.BreakerRouteRefusal, match="fixed_member_mismatch"):
        module.route_breaker(
            hdf_path=hdf_path,
            prereg_path=plan_path,
            repo_root=tmp_path,
            p1_adapter_exact_parent=PARENT,
        )


def test_b0_refuses_hdf_hash_drift_before_routing(tmp_path):
    module = _require(B0)
    hdf_path, plan_path = _synthetic_b0(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["dag"]["nodes"][0]["prerequisite_artifacts"][0]["sha256"] = "0" * 64
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(module.BreakerRouteRefusal, match="final_hdf_completion_hash_mismatch"):
        module.route_breaker(
            hdf_path=hdf_path,
            prereg_path=plan_path,
            repo_root=tmp_path,
            p1_adapter_exact_parent=PARENT,
        )


def test_b0_refuses_unreadable_exact_hdf_git_object(tmp_path):
    module = _require(B0)
    hdf_path, plan_path = _synthetic_b0(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["dag"]["nodes"][0]["prerequisite_artifacts"][0]["path"] = (
        "f" * 40 + ":SESSION_HDF_COMPLETE.json"
    )
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(module.BreakerRouteRefusal, match="exact_git_object_unreadable"):
        module.route_breaker(
            hdf_path=hdf_path,
            prereg_path=plan_path,
            repo_root=tmp_path,
            p1_adapter_exact_parent=PARENT,
        )


def test_machine_receipts_carry_no_execution_or_activation_authority():
    module = _require(B0)
    receipt = module.route_breaker(
        hdf_path=RECEIPTS / "SESSION_HDF_COMPLETE.json",
        prereg_path=RECEIPTS / "WAVE20_SCIENCE_PREREGISTRATION.json",
        repo_root=REPO,
        p1_adapter_exact_parent=PARENT,
    )
    assert receipt["execution_authority"] is False
    assert receipt["activation_authority"] is False
    assert receipt["result_bearing_science_executed"] is False
    assert receipt["p1_adapter_exact_parent"] == PARENT
