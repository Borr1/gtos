#!/usr/bin/env python3
"""OD-2: split the executing closure from the verification tooling, forward-only.

What this changes and why
-------------------------
The R1 post-acceleration contract binds 44 paths by SHA-256, and the enforcement
loop (`replay_acceleration_attempt5_typed_sparse_runner.py:1078-1091`) refuses to
run an arm if any of them has drifted. Two of those 44 are **verification
tooling that never executes during a replay** — nothing in the arm path imports
them, and their only importers are each other and their tests:

  * `src/research_infra/b7_5_post_acceleration_semantic_verifier.py`
  * `src/research_infra/replay_acceleration_task2_semantic_acceptance.py`

Binding them means a bug fix in a *verifier* costs a campaign re-run — which is
E7's finding and the reason OD-2 was approved. This builder emits an R2
generation in which those two move to a sibling `verification_tooling` group:
**recorded with their hashes for provenance, not enforced**.

Why this needs no change to any executing file
----------------------------------------------
The enforcement loop iterates two *literal* group names,
`("common_behavior_inputs", "package_authority_inputs")`. A third sibling key is
invisible to it. So the split is implemented purely as contract data: the runner,
the engine and every `code_authority_paths` entry stay byte-identical, which is
what OD-2 requires so windows remain poolable.

Forward-only, and what "forward-only" costs
-------------------------------------------
The R1 contract file is **not** touched, and neither is its builder (which is one
of its own bound inputs — editing it would drift the generation that January was
sealed under). January therefore stays accepted and re-verifiable exactly as it
is. April/May/March and every learned-arm campaign run under R2 via
`--decision-contract`, which is already a required CLI argument of the arm runner
(`b7_5_post_acceleration_runner.py:2301`), so nothing needs rewiring.

The honest scope of the split
-----------------------------
It frees **2 of 44**, not the 9 the audits imply. The other never-executing
verifiers are bound a second time by `code_authority_paths`
(`attempt5:1405-1431`) — seven of them — and freeing those would require editing
`replay_acceleration_attempt5_typed_sparse_runner.py`, an executing file on the
sealed path. That is exactly the byte-identity OD-2 forbids breaking, so they
stay bound here and are listed in `verification_tooling_deferred` with the reason.
They come free in Phase 2, when the runner is replaced rather than edited.

Two further inputs are contract-only with zero importers but are **not** moved,
because "unimported" is not the same as "not authority":
`build_b7_5_post_acceleration_contracts.py` is the R1 construction authority, and
`replay_acceleration_task9_final_validation.py` is the acceptance evidence the
contract's own `acceleration_acceptance_binding` rests on.

Usage
-----
    python3 .../build_b7_5_post_acceleration_contract_r2_verification_split.py
    python3 .../build_b7_5_post_acceleration_contract_r2_verification_split.py --check
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 import (  # noqa: E402,E501
    build_b7_5_post_acceleration_contracts as r1,
)
from research.operations.final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16 import (  # noqa: E402,E501
    build_b7_5_selection_sizing_decision_contract as sealed,
)

# Schema AND status must stay R1's literals, and so must the whole
# `predecessor_contract_binding` block. `attempt5:929-990` compares all three
# against hardcoded constants and raises
# `selection_sizing_decision_contract_invalid` /
# `..._predecessor_binding_invalid` on any difference — and those constants live
# in an executing file that OD-2 forbids editing. So the generation is recorded
# in `contract_generation`, a key the enforcement path never reads.
R2_SCHEMA = r1.DECISION_SCHEMA
R2_STATUS = r1.DECISION_STATUS
R2_OUTPUT_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"

R1_RELATIVE_PATH = str(r1.DECISION_OUTPUT_PATH.relative_to(ROOT))
R2_BUILDER_RELATIVE_PATH = str(Path(__file__).resolve().relative_to(ROOT))

#: The inputs that move out of the enforced closure. Each is verification tooling
#: with **zero importers on the arm path** — verified with an import census, not
#: assumed. Adding to this list without re-running that census would silently
#: unbind behaviour.
VERIFICATION_TOOLING_INPUT_IDS = (
    "post_acceleration_semantic_verifier",
    "task2_semantic_acceptance",
)

#: Never-executing verifiers that stay bound because `code_authority_paths`
#: binds them a second time and that list lives inside an executing file.
VERIFICATION_TOOLING_DEFERRED = (
    "src/research_infra/replay_acceleration_integrated_source_verifier.py",
    "src/research_infra/replay_acceleration_real_gate.py",
    "src/research_infra/replay_semantic_diagnostic.py",
    "src/research_infra/replay_acceleration_real_parity_verifier.py",
    "src/research_infra/replay_acceleration_streaming_archive_verifier.py",
    "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py",
    "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py",
)


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise r1.PostAccelerationContractError(code)


def build_r2_contract() -> dict[str, Any]:
    """R2 = R1 with the verification tooling moved out of the enforced closure.

    Deliberately a *transform of R1's own payload* rather than a re-derivation:
    every field R2 does not explicitly change is R1's, byte for byte, so the
    diff between the two generations is exactly the split and nothing else.
    """

    base = r1.build_decision_contract()
    _require(r1.verify_self_hash(base), "r1_self_hash_invalid")

    protocol, _protocol_sha = sealed.read_and_validate_protocol(ROOT)
    payload = copy.deepcopy(base)
    bindings = payload["input_bindings"]

    common_rows = list(bindings["common_behavior_inputs"])
    moved = [row for row in common_rows if row["input_id"] in VERIFICATION_TOOLING_INPUT_IDS]
    _require(
        len(moved) == len(VERIFICATION_TOOLING_INPUT_IDS),
        "verification_tooling_input_missing_from_r1",
    )
    _require(
        all(row["kind"] == "verification_code" for row in moved),
        "verification_tooling_kind_unexpected",
    )
    retained = [row for row in common_rows if row["input_id"] not in VERIFICATION_TOOLING_INPUT_IDS]

    # The builder that produced THIS generation is itself construction authority
    # and must be bound, exactly as R1 binds its own builder.
    retained.extend(r1.hash_inputs((
        r1.InputSpec("post_acceleration_r2_builder", "behavior_code", R2_BUILDER_RELATIVE_PATH),
    )))
    retained.sort(key=lambda row: row["input_id"])

    common_digest = r1.stable_sha256(retained)
    package_digest = bindings["package_authority_input_digest_sha256"]
    common_projection = {
        "common_behavior_input_digest_sha256": common_digest,
        "package_authority_input_digest_sha256": package_digest,
    }
    common_execution_digest = r1.stable_sha256(common_projection)

    verification_rows = sorted(moved, key=lambda row: row["input_id"])
    bindings.update({
        "common_behavior_inputs": retained,
        "common_behavior_input_digest_sha256": common_digest,
        "common_execution_input_projection": common_projection,
        "common_execution_input_digest_sha256": common_execution_digest,
        # Recorded, versioned, and deliberately NOT part of any enforced digest:
        # this is the whole point of the split. The enforcement loop iterates two
        # literal group names and never sees this key.
        "verification_tooling": verification_rows,
        "verification_tooling_digest_sha256": r1.stable_sha256(verification_rows),
        "verification_tooling_enforced": False,
        "verification_tooling_excluded_from_arm_fingerprint": True,
        "verification_tooling_deferred": {
            "paths": list(VERIFICATION_TOOLING_DEFERRED),
            "reason": (
                "bound a second time by code_authority_paths inside "
                "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py; "
                "freeing them requires editing an executing file, which OD-2 forbids"
            ),
        },
    })

    # The arm fingerprints move with the execution digest — that is what makes R2
    # a genuinely new generation rather than a relabelled R1.
    arms = [
        sealed.arm_fingerprint(
            protocol,
            arm,
            common_execution_input_digest_sha256=common_execution_digest,
        )
        for arm in protocol["arms"]
    ]
    _require(len({row["arm_fingerprint_sha256"] for row in arms}) == 4, "arm_fingerprints_not_unique")
    _require(
        {row["arm_fingerprint_sha256"] for row in arms}
        != {row["arm_fingerprint_sha256"] for row in base["factorial_contract"]["arms"]},
        "r2_arm_fingerprints_unchanged",
    )
    payload["factorial_contract"]["arms"] = arms

    payload["schema"] = R2_SCHEMA
    payload["status"] = R2_STATUS
    # `predecessor_contract_binding` stays R1's, byte for byte: the enforcement
    # path pins it to the pre-acceleration contract by hardcoded SHA. The R1->R2
    # lineage is recorded here instead, where nothing enforces it.
    payload["contract_generation"] = {
        "generation": "r2_verification_split",
        "owner_decision": "OD-2",
        "forward_only": True,
        "supersedes": {
            "path": R1_RELATIVE_PATH,
            "file_sha256": r1.file_sha256(r1.DECISION_OUTPUT_PATH),
            "self_hash_sha256": base["self_hash"]["sha256"],
        },
        "january_remains_accepted_under": R1_RELATIVE_PATH,
        "executing_files_unchanged": True,
        "code_authority_root_unchanged": True,
        "enforcement_loop_unchanged": True,
        "enforcement_group_names": ["common_behavior_inputs", "package_authority_inputs"],
        "schema_and_status_deliberately_identical_to_r1": (
            "attempt5:929-990 pins schema, status and predecessor_contract_binding "
            "to hardcoded constants inside an executing file"
        ),
    }

    payload["self_hash"] = {
        "algorithm": "sha256",
        "canonicalization": r1.CANONICALIZATION,
        "excluded_path": "self_hash.sha256",
    }
    payload["self_hash"]["sha256"] = r1.canonical_self_hash(payload)
    _require(r1.verify_self_hash(payload), "r2_self_hash_failed")

    # Invariants the split exists to preserve.
    _require(
        payload["input_bindings"]["package_authority_input_digest_sha256"]
        == base["input_bindings"]["package_authority_input_digest_sha256"],
        "package_authority_digest_changed",
    )
    _require(
        len(payload["input_bindings"]["common_behavior_inputs"])
        == len(base["input_bindings"]["common_behavior_inputs"]) - len(moved) + 1,
        "common_behavior_input_count_unexpected",
    )
    return payload


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=R2_OUTPUT_PATH)
    parser.add_argument("--check", action="store_true",
                        help="verify the committed R2 contract still rebuilds identically")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_r2_contract()
    if args.check:
        r1.check_existing(args.output, payload)
    else:
        r1.atomic_write_json(args.output, payload)
    import json
    print(json.dumps({
        "status": "VALID_R2_VERIFICATION_SPLIT" if args.check else payload["status"],
        "output": str(args.output),
        "self_hash_sha256": payload["self_hash"]["sha256"],
        "common_execution_input_digest_sha256":
            payload["input_bindings"]["common_execution_input_digest_sha256"],
        "bound_paths": (
            len(payload["input_bindings"]["common_behavior_inputs"])
            + len(payload["input_bindings"]["package_authority_inputs"])
        ),
        "verification_tooling_unbound": [
            row["path"] for row in payload["input_bindings"]["verification_tooling"]
        ],
        "arm_fingerprints": {
            row["arm_id"]: row["arm_fingerprint_sha256"]
            for row in payload["factorial_contract"]["arms"]
        },
        "replay_launched": False,
        "outcomes_evaluated": False,
        "broker_live_authority": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
