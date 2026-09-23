"""Every file the F5 carry touches must be outside the R2 seal AND outside both live
activation-token digests.

WHY THIS FILE EXISTS, and it is not hypothetical: during the F5 landing this session edited a
COMMENT in ``config/profiles/redacted_account.yaml``. That file is free of the R2 decision contract --
which is what the commission said, and it is true -- so the edit looked safe. It is not.
``activation_token.config_digest_for`` hashes ``config/agent_config.yaml`` **plus the active
profile file's BYTES**, and ``run_book.py`` binds that digest for the running worker. The
redacted_account book launches with ``--profile redacted_account``, so a one-byte comment change to that
file invalidates the redacted_account activation token the moment the file reaches the host -- and
``RealMT5.order_send`` then refuses every exposure-increasing request on an account trading
real money, until someone notices and re-mints.

The edit was reverted. This test is what makes the next one impossible to land quietly.

The two checks are deliberately different in kind:

* the R2 seal is a property of a JSON contract, checked by path membership;
* the token digest is a property of ``config_digest_for``'s own behaviour, checked by
  MEASURING the digest before and after a byte-level perturbation of each carried file --
  because a path list can go stale while the function cannot.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.safety.activation_token import config_digest_for

REPO = Path(__file__).resolve().parents[2]

R2_CONTRACT = (REPO / "research/operations"
               / "final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
               / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json")

#: The live profiles the two ARMED workers launch with (`run_book_supervisor.ps1`).
LIVE_PROFILES = ("operator_profile", "redacted_account")

#: Exactly what the F5 ceremony carries to the host. Adding a row here is a claim that the
#: file is safe to carry, and the two tests below are what check that claim.
F5_CARRY = (
    "src/components/ultimate_book/minimal_size.py",
    "src/mt5/mt5_interface.py",
    "src/mt5/mt5_real.py",
    "src/components/execution.py",
    "src/components/ultimate_book/book_engine.py",
    "src/components/ultimate_book/book_owner.py",
    "src/safety/armed_set.py",
    "run_book.py",
    "scripts/f5_status.py",
    "config/live_armed_set.json",
    "scripts/run_book_supervisor.ps1",
)


def _r2_bound_paths() -> set[str]:
    contract = json.loads(R2_CONTRACT.read_text(encoding="utf-8"))
    bound: set[str] = set()
    for group, rows in contract["input_bindings"].items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            bound.add(row["path"] if isinstance(row, dict) else row)
    return bound


def test_the_carry_list_is_real() -> None:
    """A carry list naming a file that does not exist would pass every check below by
    vacuity."""
    for rel in F5_CARRY:
        assert (REPO / rel).is_file(), rel


def test_no_carried_file_is_bound_by_the_r2_decision_contract() -> None:
    """H1: editing a bound file makes the next sealed replay fail closed with
    ``selection_sizing_decision_contract_input_drift``, and landing the change costs a
    contract regeneration plus ~16.5 h per affected window."""
    bound = _r2_bound_paths()
    offenders = [rel for rel in F5_CARRY if rel in bound]
    assert offenders == [], (
        f"F5 carries R2-bound file(s) {offenders}: the next sealed replay would fail closed "
        f"and landing it costs a re-seal plus ~16.5 h per window")

    # The guard is only meaningful if the contract really does bind SOMETHING we could have
    # hit. Both of these are one directory away from files the package edits.
    assert "config/agent_config.yaml" in bound
    assert "config/profiles/operator_profile.yaml" in bound


@pytest.mark.parametrize("profile", LIVE_PROFILES)
def test_no_carried_file_enters_a_live_activation_token_digest(profile: str, tmp_path) -> None:
    """MEASURED, not asserted from a path list.

    Perturb each carried file by one byte and check the digest does not move. A file whose
    bytes reach the digest would invalidate that account's activation token on carry, and
    ``RealMT5.order_send`` refuses every exposure-increasing request without a valid token --
    so the armed book stops opening positions on a funded account until a human re-mints.
    """
    baseline = config_digest_for(REPO / "config/agent_config.yaml", profile, repo_root=REPO)
    assert baseline, "cannot compute the digest -- the check would be vacuous"

    for rel in F5_CARRY:
        path = REPO / rel
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# f5 digest probe\n")
            perturbed = config_digest_for(REPO / "config/agent_config.yaml", profile,
                                          repo_root=REPO)
        finally:
            path.write_bytes(original)
        assert path.read_bytes() == original, f"probe failed to restore {rel}"
        assert perturbed == baseline, (
            f"{rel} enters the {profile} activation-token digest: carrying it would refuse "
            f"every exposure-increasing order on that account until a re-mint")

    assert config_digest_for(REPO / "config/agent_config.yaml", profile,
                             repo_root=REPO) == baseline


@pytest.mark.parametrize("profile", LIVE_PROFILES)
def test_the_digest_probe_can_actually_fail(profile: str) -> None:
    """The converse, on the SAME mechanism: the two files that DO enter the digest must move
    it. Without this the test above would pass against a `config_digest_for` that returned a
    constant."""
    base = REPO / "config/agent_config.yaml"
    from src.safety.activation_token import profile_path_for

    baseline = config_digest_for(base, profile, repo_root=REPO)
    for path in (base, profile_path_for(profile, repo_root=REPO)):
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# f5 digest probe\n")
            moved = config_digest_for(base, profile, repo_root=REPO)
        finally:
            path.write_bytes(original)
        assert path.read_bytes() == original
        assert moved != baseline, f"{path.name} does NOT move the digest -- probe is broken"


def test_the_redacted_account_profile_is_byte_identical_to_head() -> None:
    """The specific file this session edited and reverted. Its stale FOLLOWER header is a
    real documentation defect -- the operative block 1,000 lines lower says
    `role: primary_full_runtime` with five `copy_primary_*: forbidden` constraints -- and it
    is NOT fixed here, because fixing a comment in it costs a redacted_account token re-mint. It is
    queued for the next scheduled re-mint alongside `post_event_block_minutes: 2 -> 5`.

    Pinned against git rather than a hardcoded hash so it tracks a legitimate future edit."""
    import subprocess

    path = REPO / "config/profiles/redacted_account.yaml"
    head = subprocess.run(["git", "show", "HEAD:config/profiles/redacted_account.yaml"],
                          cwd=REPO, capture_output=True, check=False)
    if head.returncode != 0:
        pytest.skip("git object unavailable")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == \
        hashlib.sha256(head.stdout).hexdigest(), (
            "config/profiles/redacted_account.yaml differs from HEAD. It is inside the redacted_account "
            "activation-token digest: carrying it refuses every exposure-increasing order on "
            "that funded account until the token is re-minted. Bundle the edit with a re-mint.")
