"""OD-2: the executing closure and the verification tooling are now separable.

The R1 post-acceleration contract binds 44 paths by SHA-256, including two
verifiers that never run during a replay. Fixing a bug in one of them therefore
cost a campaign re-run (~16.5 h per window) — E7's finding, and the reason the
owner approved OD-2.

Every test below drives the **real** enforcement entrypoint,
`replay_acceleration_attempt5_typed_sparse_runner.selection_sizing_factorial_binding_from_args`,
which is what an arm launch calls. Nothing here launches a replay or touches a
broker.

The load-bearing test is `test_a_verifier_fix_breaks_r1_and_not_r2`: it is the
entire justification for the split, stated as a measurement.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE = (
    REPO_ROOT
    / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
)
R1_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json"
R2_PATH = ROUTE / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
SPLIT_VERIFIER = REPO_ROOT / "src/research_infra/b7_5_post_acceleration_semantic_verifier.py"

# The contract resolver searches this root as a fallback, and the two
# package-authority JSONL ledgers only match there (B2/B3).
RUNTIME_EVIDENCE_ROOT = "/Users/borr/GTOSActive/repo"

#: R2-bound paths whose sealed bytes have been deliberately superseded, with the authority for
#: each. The seal is broken FORWARD by owner decision -- it is not an accident and it is not a
#: defect -- but "authorized" has to mean *named*, or a genuinely unrecorded edit slips into a
#: test everyone already knows is red. Anything drifted and absent from this mapping fails
#: `test_the_working_tree_break_is_complete_and_every_drifted_path_is_named`.
AUTHORIZED_FORWARD_BREAKS = {
    "src/components/broker_net_cost_engine.py":
        "CN, the broker-true commission default. CLAUDE.md §4: 'CN's broker_net_cost_engine.py "
        "edit is the authorized forward R2 seal break (owner word, recorded): any future "
        "sealed replay regenerates its decision contract first.' Extended since by the "
        "2026-08-12 cost model (realized rollover crossings, slippage by barrier).",
    "config/agent_config.yaml":
        "live arming and the ultimate_book gates. Owner decisions OD-AI-2/OD-AI-3 and the "
        "F5 landing; the live host's own config, not this repository's, is what arms a book.",
    "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py":
        "wave-21 replay engine work, on the parked campaign's own runner.",
    "src/research_infra/replay_compact_event_sink.py":
        "wave-21 replay engine work.",
    "src/research_infra/v4_timewarp_simulated_live_research_loop.py":
        "wave-21 replay engine work.",
    "src/research/moonshot_scheduler_v4_best_trade_allocator.py":
        "wave-21 scheduler work (d90da611b), plus the 2026-08-12 live-isolation repair that "
        "defers the broad-origin import out of the live entrypoint's module graph.",
    "research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
    "/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl":
        "CLAUDE.md §3 (B905): the contract's expected bytes match no committed object in any "
        "tree -- only the uncommitted working copy in MAIN_REPO_ROOT. Standing hazard, "
        "recorded; do not clean or re-checkout that path.",
}

pytestmark = pytest.mark.skipif(
    not R2_PATH.is_file(), reason="R2 verification-split contract not present"
)


def _contract(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bound_rows(contract_path: Path) -> dict[str, str]:
    return {
        row["path"]: row["sha256"]
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in _contract(contract_path)["input_bindings"][group]
    }


def drifted_bound_paths(contract_path: Path) -> list[str]:
    """Bound paths whose sealed bytes are at NEITHER binding root the runner searches.

    Mirrors `resolve_exact_bound_input`
    (`replay_acceleration_attempt5_typed_sparse_runner.py:1053-1075`), which returns on the
    first root whose content HASHES to the contract's value -- so a path that matches at the
    main repo is not drifted however the worktree's copy reads.
    """
    import hashlib

    roots = [REPO_ROOT, Path(RUNTIME_EVIDENCE_ROOT)]
    out = []
    for relative, sha in _bound_rows(contract_path).items():
        for root in roots:
            candidate = root / relative
            if candidate.is_file() and hashlib.sha256(
                candidate.read_bytes()
            ).hexdigest() == sha:
                break
        else:
            out.append(relative)
    return sorted(out)


@pytest.fixture(scope="session")
def sealed_binding_root(tmp_path_factory):
    """A binding root carrying the SEALED bytes of every path that has since drifted.

    Six R2-bound paths are drifted at `origin/main` itself -- the forward cost work the owner
    authorized (CLAUDE.md §4: "CN's `broker_net_cost_engine.py` edit is the authorized forward
    R2 seal break") plus the wave-21 replay-engine changes. So the enforcement path refuses,
    correctly, and the four binding tests below could not run at all.

    Restoring the sealed bytes is what `test_r1_binds_again_the_moment_the_sealed_bytes_are_restored`
    already does for two verifier files, by finding the blob in history that hashes to the
    contract's value. This generalises that to every drifted path and puts the result in a
    TEMP tree instead of writing into `src/`: the runner searches
    `[worktree, runtime_evidence_root, MAIN_REPO_ROOT]` and returns on the first HASH MATCH, so
    handing it this directory as `runtime_evidence_root` binds the sealed bytes while the
    working tree keeps the authorized break. Nothing in the repository is mutated.
    """
    import hashlib
    import subprocess

    # R2's drifted set ONLY, deliberately. R1 additionally binds the two verifiers P1 fixed,
    # and restoring THOSE would defeat `test_a_verifier_fix_breaks_r1_and_not_r2`, whose whole
    # measurement is that R1 fails closed on them while R2 does not.
    root = tmp_path_factory.mktemp("sealed_binding_root")
    rows = _bound_rows(R2_PATH)
    wanted = {relative: rows[relative] for relative in drifted_bound_paths(R2_PATH)}

    unrecoverable = []
    for relative, sha in sorted(wanted.items()):
        commits = subprocess.run(
            ["git", "log", "--format=%H", "-n", "80", "--all", "--", relative],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.split()
        found = None
        for commit in commits:
            blob = subprocess.run(
                ["git", "cat-file", "-p", f"{commit}:{relative}"],
                cwd=REPO_ROOT, capture_output=True,
            )
            if blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == sha:
                found = blob.stdout
                break
        if found is None:
            unrecoverable.append(relative)
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(found)
    return {"root": root, "restored": sorted(set(wanted) - set(unrecoverable)),
            "unrecoverable": unrecoverable}


def _bind(contract_path: Path, arm: dict, evidence_root: str | None = None) -> dict:
    """Run the live enforcement path.

    Imported normally, NOT re-imported. An earlier version deleted the module
    from `sys.modules` first, to defeat a file-SHA cache that turned out not to
    need defeating -- `file_sha256_cached` keys on (path, mtime_ns, size), so a
    modified file already misses. The deletion created a second module object,
    and `multiprocessing` later refused to pickle a function from it
    ("it's not the same object as ..."), breaking three replay tests that ran
    afterwards. Caught by the full-suite failure-set diff.
    """

    runner = importlib.import_module(
        "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    )
    args = argparse.Namespace(
        decision_contract=str(contract_path),
        arm_id=arm["arm_id"],
        expected_arm_fingerprint_sha256=arm["arm_fingerprint_sha256"],
        runtime_evidence_root=evidence_root or RUNTIME_EVIDENCE_ROOT,
    )
    return runner.selection_sizing_factorial_binding_from_args(args)


def _sealed(fixture) -> str:
    """The sealed binding root, or a skip naming exactly what could not be recovered."""
    if fixture["unrecoverable"]:
        pytest.skip(
            "sealed bytes not reachable from this history graft for: "
            + ", ".join(fixture["unrecoverable"])
        )
    return str(fixture["root"])


@pytest.mark.parametrize("arm_index", range(4))
def test_r2_binds_through_the_real_enforcement_path(arm_index, sealed_binding_root):
    """A contract the runner rejects is worthless however elegant its data.

    Bound against the SEALED bytes (see `sealed_binding_root`), because the working tree
    carries the owner-authorized forward break and would refuse -- which is the enforcement
    path working, and is asserted separately in
    `test_the_working_tree_break_is_complete_and_every_drifted_path_is_named`.
    """

    contract = _contract(R2_PATH)
    assert _bind(R2_PATH, contract["factorial_contract"]["arms"][arm_index],
                 _sealed(sealed_binding_root)) is not None


def test_the_working_tree_break_is_complete_and_every_drifted_path_is_named():
    """The other half: the enforcement path REFUSES this tree, and refuses for known paths.

    Six R2-bound paths are drifted at `origin/main`, not merely in this worktree. That is the
    authorized forward break (CLAUDE.md §4) plus the wave-21 replay-engine work, and it is why
    the parked campaign's resume option is dead. The property worth guarding is not "nothing
    drifted" -- something deliberately did -- but that the drift is ENUMERATED, so a new
    unrecorded edit to a bound path is loud instead of being absorbed into a known-red test.
    """

    drifted = set(drifted_bound_paths(R2_PATH))
    unrecorded = sorted(drifted - set(AUTHORIZED_FORWARD_BREAKS))
    assert not unrecorded, (
        "an edit landed on an R2-bound path with no recorded authority: "
        + ", ".join(unrecorded)
        + "\nAdd it to AUTHORIZED_FORWARD_BREAKS with WHO authorized it and WHY, or restore "
          "the sealed bytes. This is the check that stops an unrecorded seal break hiding "
          "inside a known-red test."
    )
    # ...and the runner's behaviour matches the measurement, in both directions. The SET is
    # deliberately not pinned: CLAUDE.md §3 records that it is a property of the working
    # tree's own state (which paths resolve at which binding root, LFS hydration included) and
    # is therefore not portable between worktrees. What IS portable is the implication.
    arm = _contract(R2_PATH)["factorial_contract"]["arms"][0]
    if drifted:
        with pytest.raises(ValueError, match="input_drift"):
            _bind(R2_PATH, arm)
    else:
        assert _bind(R2_PATH, arm) is not None, (
            "no bound path is drifted, so the runner must bind this tree directly")


def test_a_verifier_fix_breaks_r1_and_not_r2(sealed_binding_root):
    """THE test. This is what OD-2 buys, measured rather than asserted.

    P1 has landed, so this is now the *standing* state rather than a simulation:
    the R-P1 fix is in `b7_5_post_acceleration_semantic_verifier.py`, R1 fails
    closed on it, and R2 binds. Both halves matter — R2 binding proves the split
    works, R1 failing proves the binding was real in the first place.
    """

    r1_arm = _contract(R1_PATH)["factorial_contract"]["arms"][0]
    r2_arm = _contract(R2_PATH)["factorial_contract"]["arms"][0]
    # Both sides bind against the same sealed root, so the ONLY difference between them is
    # the split itself: R1 still binds the two verifiers P1 fixed, R2 moved them to
    # `verification_tooling`, which the enforcement loop does not read. Without this the
    # comparison would be contaminated by the six unrelated forward breaks in the tree and
    # would "pass" for the wrong reason.
    root = _sealed(sealed_binding_root)

    with pytest.raises(ValueError, match="input_drift"):
        _bind(R1_PATH, r1_arm, root)
    assert _bind(R2_PATH, r2_arm, root) is not None, (
        "R2 rejects the fixed verifier — the split did not take effect"
    )


def test_r1_binds_again_the_moment_the_sealed_bytes_are_restored(sealed_binding_root):
    """R1 is superseded, not broken. Re-running a January arm under R1 costs one
    `git checkout` of the two verifier files and nothing else, and this measures
    that rather than asserting it."""

    r1_arm = _contract(R1_PATH)["factorial_contract"]["arms"][0]
    bound = {
        row["path"]: row["sha256"]
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in _contract(R1_PATH)["input_bindings"][group]
    }
    targets = [
        REPO_ROOT / "src/research_infra/b7_5_post_acceleration_semantic_verifier.py",
        REPO_ROOT / "src/research_infra/replay_acceleration_task2_semantic_acceptance.py",
    ]
    saved = {path: path.read_bytes() for path in targets}
    import subprocess

    try:
        for path in targets:
            rel = str(path.relative_to(REPO_ROOT))
            blob = subprocess.run(
                ["git", "log", "--format=%H", "-n", "40", "--", rel],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )
            assert blob.returncode == 0
            # The sealed bytes are whatever hashes to the contract's value; find
            # them in history rather than hardcoding a commit.
            found = None
            for commit in blob.stdout.split():
                content = subprocess.run(
                    ["git", "cat-file", "-p", f"{commit}:{rel}"],
                    cwd=REPO_ROOT, capture_output=True,
                )
                import hashlib
                if hashlib.sha256(content.stdout).hexdigest() == bound[rel]:
                    found = content.stdout
                    break
            if found is None:
                pytest.skip(f"sealed bytes for {rel} not reachable from this history graft")
            path.write_bytes(found)
        # The two verifiers are restored in place, above. The six paths the authorized forward
        # break moved -- which R1 binds too -- come from the sealed temp root, so this still
        # measures exactly what it claims: R1 binds again once ITS sealed verifier bytes are back.
        assert _bind(R1_PATH, r1_arm, _sealed(sealed_binding_root)) is not None
    finally:
        for path, content in saved.items():
            path.write_bytes(content)


def test_the_split_moved_exactly_the_never_executing_verifiers():
    bindings = _contract(R2_PATH)["input_bindings"]
    moved = {row["path"] for row in bindings["verification_tooling"]}
    assert moved == {
        "src/research_infra/b7_5_post_acceleration_semantic_verifier.py",
        "src/research_infra/replay_acceleration_task2_semantic_acceptance.py",
    }
    bound = {row["path"] for row in bindings["common_behavior_inputs"]}
    assert not (moved & bound), "a verifier is in both groups; it is still enforced"
    assert bindings["verification_tooling_enforced"] is False


FREED_VERIFIERS = (
    "b7_5_post_acceleration_semantic_verifier",
    "replay_acceleration_task2_semantic_acceptance",
)

#: What an arm launch actually runs. If either of these can reach a freed
#: verifier by any chain of imports, the OD-2 split is a behaviour hole.
SEALED_ARM_ENTRYPOINTS = (
    "b7_5_post_acceleration_runner",
    "replay_acceleration_attempt5_typed_sparse_runner",
)


def _import_graph():
    """module stem -> stems it imports, parsed rather than grepped.

    Keyed on bare stems, which over-approximates if two modules ever share one:
    a collision produces a spurious edge, so the census errs toward reporting a
    hole that is not there rather than missing one that is. For a guard, that is
    the safe direction.
    """

    import ast
    import collections

    edges = collections.defaultdict(set)
    for base in ("src", "scripts"):
        for path in (REPO_ROOT / base).rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = [module] + [
                        f"{module}.{alias.name}" for alias in node.names
                    ]
                else:
                    continue
                for name in names:
                    edges[path.stem].update(
                        part for part in name.split(".") if part
                    )
    return edges


def test_the_import_census_sees_parenthesised_imports():
    """Guard on the guard.

    The census below replaced a `rg '^\\s*(import|from)\\b.*\\bMODULE\\b'`
    scan. Every importer in this repo writes
    `from src.research_infra import (\\n    module_name,\\n)`, so the module
    name never shared a line with the `from` and that regex matched **nothing**
    — it passed vacuously while eight modules did in fact import a freed
    verifier. This test fails if the census ever stops seeing them.
    """

    edges = _import_graph()
    importers = {
        stem for stem, deps in edges.items() if deps & set(FREED_VERIFIERS)
    }
    assert (
        "replay_acceleration_task3_exact_cache_acceptance" in importers
    ), "the census can no longer see a known parenthesised importer"
    assert len(importers) >= 5, f"census found implausibly few importers: {importers}"


def test_the_freed_verifiers_are_genuinely_unreachable_from_the_arm_path():
    """The split is only safe if these files never execute during a replay.

    Stated as the property that actually matters: no chain of imports leads from
    a sealed arm entrypoint to a freed verifier. That is stronger than an
    allowlist of direct importers, because an allowlisted importer that is
    itself on the arm path would still be a hole — and it cannot be evaded by
    import style.
    """

    edges = _import_graph()
    reaches = set(FREED_VERIFIERS)
    changed = True
    while changed:
        changed = False
        for stem, deps in edges.items():
            if stem not in reaches and (deps & reaches):
                reaches.add(stem)
                changed = True

    on_the_arm_path = sorted(set(SEALED_ARM_ENTRYPOINTS) & reaches)
    assert not on_the_arm_path, (
        f"a sealed arm entrypoint can reach a freed verifier: {on_the_arm_path}. "
        "The OD-2 split has become a behaviour hole and the contract must be "
        "regenerated with those verifiers bound again."
    )

    # Everything that does reach them must be verification tooling. This is a
    # readability check on the closure, not the safety property above.
    family = {
        "replay_acceleration_task2_closure_gate",
        "replay_acceleration_task3_exact_cache_acceptance",
        "replay_acceleration_task4_shared_preparation_acceptance",
        "replay_acceleration_task5_compact_sink_acceptance",
        "replay_acceleration_task6_prepared_pack_acceptance",
        "replay_acceleration_task8_profile_runner",
        "replay_acceleration_task9_final_validation",
        "replay_differential_harness",
        # Session H (B90-B99). Both are verification tooling: packet_validation
        # compares SleeveBookPolicy's decisions against the live book's recorded
        # ones and validate_sleeve_book_policy is its runner. Neither is on the arm
        # path -- the assertion above covers that -- and each reaches task2 only
        # through replay_differential_harness's difference engine.
        #
        # NOTE for whoever owns this test: the census keys edges by `path.stem`,
        # so a new module whose BASENAME collides with any dotted import component
        # drags unrelated modules into the closure. This module was first written
        # as `validation.py` and pulled in 13 false reachers, because eight
        # pre-existing modules import `src.utils.validation` /
        # `src.security.validation`. It was renamed rather than allowlisted. The
        # real fix is to key the census by dotted path instead of stem; that is
        # strictly strengthening but it belongs to this test's own lane, so it is
        # recorded here rather than done here.
        "packet_validation",
        "validate_sleeve_book_policy",
    }
    unexpected = sorted(reaches - set(FREED_VERIFIERS) - family)
    assert not unexpected, (
        f"new modules reach a freed verifier: {unexpected}. Each is off the arm "
        "path per the assertion above, but confirm it is verification tooling "
        "and add it here deliberately."
    )


def test_r2_preserves_everything_the_split_must_not_change():
    r1, r2 = _contract(R1_PATH), _contract(R2_PATH)

    # The runner pins all three against hardcoded constants in an executing file.
    assert r2["schema"] == r1["schema"]
    assert r2["status"] == r1["status"]
    assert r2["predecessor_contract_binding"] == r1["predecessor_contract_binding"]

    # Package authority is untouched; only the behaviour group changed.
    assert (
        r2["input_bindings"]["package_authority_input_digest_sha256"]
        == r1["input_bindings"]["package_authority_input_digest_sha256"]
    )
    assert (
        r2["input_bindings"]["common_execution_input_digest_sha256"]
        != r1["input_bindings"]["common_execution_input_digest_sha256"]
    )
    # A new generation must have new fingerprints, or arms would pool across
    # contracts that bind different code.
    assert {row["arm_fingerprint_sha256"] for row in r2["factorial_contract"]["arms"]}.isdisjoint(
        {row["arm_fingerprint_sha256"] for row in r1["factorial_contract"]["arms"]}
    )


def test_r1_the_artifact_is_untouched():
    """OD-2 is forward-only: the R1 contract file and its builder are January's
    record and neither may be rewritten.

    Note what this does NOT assert. Once P1 landed, `--mode decision --check`
    correctly FAILS, because two of R1's bound inputs changed on disk. That is
    the intended cost, not a broken artifact — see
    `test_r1_binds_again_the_moment_the_sealed_bytes_are_restored`. What must
    stay true is that R1's own bytes, and the bytes of the builder that produced
    them, are exactly what January was sealed with.
    """

    import hashlib

    assert _contract(R1_PATH)["self_hash"]["sha256"] == (
        "9faa7d4c2d0cd669b7fac0c1e42b38a8e9a566b7eadf22f1ab28a1d09df20073"
    )
    bound = {
        row["path"]: row["sha256"]
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in _contract(R1_PATH)["input_bindings"][group]
    }
    builder = "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/build_b7_5_post_acceleration_contracts.py"
    assert hashlib.sha256((REPO_ROOT / builder).read_bytes()).hexdigest() == bound[builder], (
        "the R1 builder was edited; R1 can no longer be regenerated from its own authority"
    )


def test_r2_no_longer_rebuilds_and_the_break_is_exactly_the_authorized_one():
    """Until 2026-08-01 this test was `test_r2_rebuilds_deterministically` and asserted
    `--check` returncode 0. Session CN (B2750+) then landed the owner-authorized forward
    seal break: `src/components/broker_net_cost_engine.py` — an R2 `common_behavior_inputs`
    member — now charges broker-true commission as the default fourth cost term on the LIVE
    path. The sealed history is untouched (R2's own bytes, the execution-seal file/root and
    all four shared per-arm digests are byte-identical; CN's result §5 pins each hash), but
    the CONTRACT is now honestly stale: a forward sealed replay must regenerate its decision
    authority and rerun affected windows before trusting R2 again.

    Same shape as R1 after P1 (see `test_r1_is_the_january_contract_of_record...` above):
    the correct assertion is not that the check passes, but that it fails FOR EXACTLY the
    authorized reason and no other. Anything beyond the CN engine break failing here is a
    real, unauthorized drift and must stay loud.
    """
    import hashlib
    import subprocess

    proc = subprocess.run(
        [sys.executable,
         str(ROUTE / "build_b7_5_post_acceleration_contract_r2_verification_split.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode != 0, (
        "R2 --check PASSED, which would mean the decision contract was regenerated. "
        "Regeneration is replay-authority work (rerun affected windows first); if that "
        "was done deliberately, restore this test to its pre-CN returncode-0 form."
    )
    assert "decision_contract_stale_or_input_drifted" in (proc.stdout + proc.stderr)

    engine = "src/components/broker_net_cost_engine.py"
    bound = {
        row["path"]: row["sha256"]
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in _contract(R2_PATH)["input_bindings"][group]
    }
    # The contract still expects the sealed pre-CN engine: R2 itself was not rewritten.
    assert bound[engine] == (
        "eb4ec5173ce28d4b2f6631fbe2e912a1dc5e20d392cd2a2517627d2cc2ab40d0"
    ), "R2's own binding for the engine moved — the contract bytes were rewritten"
    # And the working tree does NOT carry the sealed bytes: the break is real.
    #
    # This pinned CN's exact after-bytes
    # (`f599f25f17008667442f926805a3738914d44e03aa0e29b75a293fdcffeb36ed`), which made every
    # subsequent AUTHORIZED cost commit report itself as "an unrecorded edit". Three have
    # landed since -- `072f4b6d6`, `ef8533e1c`, `3da95f915` -- all of them forward cost work
    # under the same owner decision that authorized CN. Pinning one revision of a file that is
    # expected to keep moving turns the record into a tripwire on its own authorization.
    #
    # The check that survives, and that still catches the thing this was for, lives in
    # `test_the_working_tree_break_is_complete_and_every_drifted_path_is_named`: EVERY drifted
    # bound path must be named in `AUTHORIZED_FORWARD_BREAKS`. Here we assert only the local
    # fact this test needs -- the engine is off its sealed bytes, so the `--check` failure
    # above is explained by a break that is present rather than by something else.
    actual = hashlib.sha256((REPO_ROOT / engine).read_bytes()).hexdigest()
    assert actual != bound[engine], (
        "broker_net_cost_engine.py is back at its SEALED bytes, so CN's authorized break has "
        "been reverted. If that was deliberate, restore this test to its pre-CN form."
    )
    assert engine in AUTHORIZED_FORWARD_BREAKS


def test_the_deferred_verifiers_are_named_with_their_reason():
    """Seven never-executing verifiers stay bound because `code_authority_paths`
    binds them a second time from inside an executing file. Silence about that
    would read as "the split freed everything"."""

    deferred = _contract(R2_PATH)["input_bindings"]["verification_tooling_deferred"]
    assert len(deferred["paths"]) == 7
    assert "code_authority_paths" in deferred["reason"]
    bound = {row["path"] for row in _contract(R2_PATH)["input_bindings"]["common_behavior_inputs"]}
    assert set(deferred["paths"]) <= bound
