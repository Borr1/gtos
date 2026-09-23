#!/usr/bin/env python3
"""Receipt-only B0 router for the HDF-admitted fixed breaker.

The router authenticates final receipt bytes and observes the already-billed
disposition.  It never opens an economic row, re-runs a null, or constructs a
new candidate family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "gtos.wave20.b0-breaker-route.v1"
HDF_SCHEMA = "gtos-session-hdf-exit-capture-science-falsifier2-complete-v1"
FAMILY_SCHEMA = "gtos.walkforward.candidate_family.v1"
FIXED_MEMBER = "cq_current_breaker_re_entry_inverted_5d_stop_0p25d"
FAMILY_NAME = "CANDIDATE_BOOK_V1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class BreakerRouteRefusal(ValueError):
    """B0 authority did not bind exactly."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_file(repo_root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(repo_root.resolve()):
        raise BreakerRouteRefusal("repo_path_escape_refused")
    if not resolved.is_file():
        raise BreakerRouteRefusal(f"required_file_absent:{resolved}")
    return resolved


def _read_json(repo_root: Path, path: Path) -> tuple[dict[str, Any], bytes]:
    target = _repo_file(repo_root, path)
    data = target.read_bytes()
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise BreakerRouteRefusal(f"json_object_required:{target}")
    return payload, data


def _read_exact_git_blob(repo_root: Path, reference: str) -> bytes:
    if ":" not in reference:
        raise BreakerRouteRefusal("exact_git_object_required")
    commit, path = reference.split(":", 1)
    if not HEX40.fullmatch(commit) or not path:
        raise BreakerRouteRefusal("exact_git_object_invalid")
    proc = subprocess.run(
        ["git", "show", reference],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise BreakerRouteRefusal(
            "exact_git_object_unreadable:"
            + proc.stderr.decode("utf-8", errors="replace").strip()
        )
    return proc.stdout


def _b0_node(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    dag = plan.get("dag")
    nodes = dag.get("nodes") if isinstance(dag, Mapping) else None
    if not isinstance(nodes, list):
        raise BreakerRouteRefusal("preregistration_dag_nodes_missing")
    matches = [node for node in nodes if isinstance(node, Mapping) and node.get("id") == "B0"]
    if len(matches) != 1:
        raise BreakerRouteRefusal("exactly_one_b0_node_required")
    return matches[0]


def _expected_artifact(node: Mapping[str, Any], basename: str) -> Mapping[str, Any]:
    artifacts = node.get("prerequisite_artifacts")
    matches = [
        artifact
        for artifact in artifacts or []
        if isinstance(artifact, Mapping)
        and str(artifact.get("path") or "").split(":", 1)[-1].endswith(basename)
    ]
    if len(matches) != 1:
        raise BreakerRouteRefusal(f"exactly_one_preregistered_artifact_required:{basename}")
    return matches[0]


def _require_equal(label: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise BreakerRouteRefusal(
            f"{label}_mismatch:observed={observed!r}:expected={expected!r}"
        )


def route_breaker(
    *,
    hdf_path: Path,
    prereg_path: Path,
    repo_root: Path,
    p1_adapter_exact_parent: str,
) -> dict[str, Any]:
    if not HEX40.fullmatch(p1_adapter_exact_parent):
        raise BreakerRouteRefusal("p1_adapter_exact_parent_must_be_full_commit")
    prereg, prereg_bytes = _read_json(repo_root, prereg_path)
    hdf, hdf_bytes = _read_json(repo_root, hdf_path)
    b0 = _b0_node(prereg)
    hdf_artifact = _expected_artifact(b0, "SESSION_HDF_COMPLETE.json")
    family_artifact = _expected_artifact(b0, "CANDIDATE_FAMILY_V27.json")
    hdf_expected_sha = str(hdf_artifact.get("sha256") or "")
    hdf_observed_sha = sha256_bytes(hdf_bytes)
    if not HEX64.fullmatch(hdf_expected_sha) or hdf_observed_sha != hdf_expected_sha:
        raise BreakerRouteRefusal("final_hdf_completion_hash_mismatch")
    hdf_git_object = str(hdf_artifact.get("path") or "")
    hdf_git_bytes = _read_exact_git_blob(repo_root, hdf_git_object)
    if hdf_git_bytes != hdf_bytes or sha256_bytes(hdf_git_bytes) != hdf_expected_sha:
        raise BreakerRouteRefusal("final_hdf_exact_git_object_bytes_mismatch")

    family_path_text = str(family_artifact.get("path") or "")
    family_path = _repo_file(repo_root, repo_root / family_path_text)
    family, family_bytes = _read_json(repo_root, family_path)
    family_expected_sha = str(family_artifact.get("sha256") or "")
    family_observed_sha = sha256_bytes(family_bytes)
    if family_observed_sha != family_expected_sha:
        raise BreakerRouteRefusal("candidate_family_v27_hash_mismatch")

    _require_equal("hdf_schema", hdf.get("schema"), HDF_SCHEMA)
    _require_equal("hdf_status", hdf.get("status"), "SAFE_ONLY_WITH_HDF_COMMITS")
    _require_equal("family_schema", family.get("schema"), FAMILY_SCHEMA)
    disposition = hdf.get("cs_disposition")
    if not isinstance(disposition, Mapping):
        raise BreakerRouteRefusal("hdf_cs_disposition_missing")
    anchor = disposition.get("hdc_hdf_capture_anchor")
    if not isinstance(anchor, Mapping):
        raise BreakerRouteRefusal("hdf_capture_anchor_missing")
    _require_equal("hdf_anchor_verdict", anchor.get("verdict"), "ADMIT")
    _require_equal(
        "hdf_disposition_status",
        disposition.get("status"),
        "RATIFIED_GATE_ADMIT_DOSSIER_REQUIRED_NOT_ARMED",
    )
    _require_equal("hdf_candidate_queued", disposition.get("queued"), False)
    _require_equal("hdf_dossier_created", disposition.get("dossier_created"), False)
    _require_equal("hdf_activation_authority", disposition.get("activation_authority"), False)
    boundaries = hdf.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise BreakerRouteRefusal("hdf_boundaries_missing")
    for key in (
        "broad_replay_launched",
        "march_outcomes_read",
        "live_outcomes_read",
        "runtime_changed",
        "config_changed",
        "broker_contacted",
        "vps_contacted",
        "activation_token_read_or_written",
        "production_or_live_trading_changed",
        "candidate_queued",
        "activation_dossier_created",
        "promotion_or_arming",
        "activation_authority",
    ):
        _require_equal(f"hdf_boundary_{key}", boundaries.get(key), False)

    denominator = b0.get("family_denominator")
    if not isinstance(denominator, Mapping):
        raise BreakerRouteRefusal("b0_family_denominator_missing")
    _require_equal("fixed_member", denominator.get("member"), FIXED_MEMBER)
    _require_equal("family_name", denominator.get("family"), f"{FAMILY_NAME}_V27")
    _require_equal("all_declared", denominator.get("all_declared"), 59)
    _require_equal("looks_taken", denominator.get("looks_taken"), 57)
    _require_equal("other_p_values", denominator.get("other_p_values"), "58 padded at 1.0")
    _require_equal("alpha", denominator.get("alpha"), 0.1)
    _require_equal("gate_option", denominator.get("gate_option"), "B_balanced")
    _require_equal("population", denominator.get("population"), "RECORDED")

    family_block = (family.get("families") or {}).get(FAMILY_NAME)
    if not isinstance(family_block, Mapping):
        raise BreakerRouteRefusal("candidate_book_v1_family_missing")
    members = family_block.get("members")
    if not isinstance(members, list):
        raise BreakerRouteRefusal("candidate_book_v1_members_missing")
    selected = [
        member
        for member in members
        if isinstance(member, Mapping) and member.get("name") == FIXED_MEMBER
    ]
    if len(selected) != 1:
        raise BreakerRouteRefusal("fixed_breaker_member_identity_not_unique")
    _require_equal("fixed_breaker_look_taken", selected[0].get("look_taken"), True)
    member_bytes = json.dumps(
        selected[0], sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    _require_equal("family_high_water_size", family_block.get("high_water_size"), 59)
    _require_equal("family_high_water_looks", family_block.get("high_water_looks"), 57)
    _require_equal("family_member_count", len(members), 59)
    _require_equal(
        "family_look_count",
        sum(member.get("look_taken") is True for member in members if isinstance(member, Mapping)),
        57,
    )
    multiplicity = disposition.get("multiplicity")
    if not isinstance(multiplicity, Mapping):
        raise BreakerRouteRefusal("hdf_multiplicity_missing")
    _require_equal("hdf_family_size", multiplicity.get("family_size"), 59)
    _require_equal("hdf_looks_taken", multiplicity.get("looks_taken"), 57)
    _require_equal("hdf_padded_members", multiplicity.get("other_members_padded_at_p1"), 58)
    _require_equal("hdf_alpha", multiplicity.get("alpha"), 0.1)

    return {
        "schema": SCHEMA,
        "session": "HK",
        "node": "B0",
        "status": "HDF_VALIDATED_ADMIT_OBSERVED_ADVANCE_UNCHANGED",
        "execution_authority": False,
        "activation_authority": False,
        "result_bearing_science_executed": False,
        "p1_adapter_exact_parent": p1_adapter_exact_parent,
        "bindings": {
            "preregistration": {
                "path": str(prereg_path.resolve().relative_to(repo_root.resolve())),
                "sha256": sha256_bytes(prereg_bytes),
            },
            "final_hdf_completion": {
                "path": str(hdf_path.resolve().relative_to(repo_root.resolve())),
                "sha256": hdf_observed_sha,
                "preregistered_git_object": hdf_git_object,
                "exact_git_object_bytes_match": True,
                "hdf_implementation_head": hdf.get("hdf_implementation_head"),
            },
            "candidate_family_v27": {
                "path": family_path_text,
                "sha256": family_observed_sha,
            },
        },
        "observed_prior_disposition": {
            "status": disposition.get("status"),
            "anchor": dict(anchor),
            "multiplicity": dict(multiplicity),
            "economics_recomputed": False,
            "economic_rows_opened": 0,
        },
        "candidate": {
            "member": FIXED_MEMBER,
            "family": f"{FAMILY_NAME}_V27",
            "all_declared": 59,
            "looks_taken": 57,
            "other_p_values_padded_at_1": 58,
            "alpha": 0.1,
            "gate_option": "B_balanced",
            "population": "RECORDED",
            "family_member_record": dict(selected[0]),
            "family_member_record_canonical_sha256": sha256_bytes(member_bytes),
            "changed_by_router": False,
        },
        "route": {
            "next": "K1_APPLICABILITY",
            "then": "P1_IMPLEMENTATION_COMMISSION",
            "B1": "SKIPPED_BY_PREREGISTERED_BRANCH",
            "breadth_opened": False,
            "O1_opened": False,
            "C0_opened": False,
            "N1_opened": False,
            "FC2_opened": False,
        },
        "boundaries": {
            "receipt_only": True,
            "economic_recomputation": False,
            "candidate_pool_created": False,
            "candidate_queued": False,
            "dossier_created": False,
            "march_outcomes_read": False,
            "live_forward_outcomes_read": False,
            "february_economics_read": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hdf-complete", required=True, type=Path)
    parser.add_argument("--prereg", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--p1-parent", required=True)
    ns = parser.parse_args(argv)
    repo_root = Path.cwd().resolve()
    try:
        receipt = route_breaker(
            hdf_path=ns.hdf_complete,
            prereg_path=ns.prereg,
            repo_root=repo_root,
            p1_adapter_exact_parent=ns.p1_parent,
        )
    except (BreakerRouteRefusal, json.JSONDecodeError, OSError) as exc:
        parser.error(str(exc))
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{receipt['status']}: {ns.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
