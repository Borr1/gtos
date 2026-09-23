"""The mint ceremony's two ways to go wrong quietly.

Both were found by an adversarial pass over the token lifecycle (B103) and both
are operator-facing rather than code-facing, which is exactly why they matter:
the runbook in `phase3/STAGE0_VPS_RUNBOOK.md` is executed by a human on a live
funded host, and a CLI that succeeds while doing something other than what was
meant is the failure mode that runbook cannot defend against.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "scripts" / "gtos_activation_token.py"
LIVE_PROFILE = "operator_profile"
F5_NAMESPACE = "operator"
F5_TAGS = ",".join(
    json.loads((REPO_ROOT / "config/live_armed_set.json").read_text(encoding="utf-8"))
    ["accounts"][F5_NAMESPACE]["armed_sleeves"]
)


def _run(args, token_dir, expect_rc=None):
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": str(token_dir),
             "GTOS_ACTIVATION_TOKEN_DIR": str(token_dir)},
    )
    if expect_rc is not None:
        assert proc.returncode == expect_rc, (
            f"rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


@pytest.fixture()
def token_dir(tmp_path):
    return tmp_path / "activation"


def test_minting_without_a_namespace_warns(token_dir):
    """The unbound-CONFIG case already warned; the unbound-NAMESPACE case did
    not, and it is the wider hole. `verify_token` enforces a namespace only when
    the token declares one, so a namespace-less token authorizes every process
    on that account — including the dual-broker follower."""

    proc = _run(["mint", "--profile", LIVE_PROFILE, "--expires-in-hours", "1",
                 "--issued-by", "test"], token_dir, expect_rc=0)

    assert json.loads(proc.stdout)["namespace"] is None
    assert "binds NO namespace" in proc.stderr
    assert "authorizes ANY process" in proc.stderr


def test_minting_with_a_namespace_does_not_warn(token_dir):
    proc = _run(["mint", "--profile", LIVE_PROFILE, "--namespace", LIVE_PROFILE,
                 "--expires-in-hours", "1", "--issued-by", "test"], token_dir, expect_rc=0)

    assert json.loads(proc.stdout)["namespace"] == LIVE_PROFILE
    assert "binds NO namespace" not in proc.stderr


def test_a_second_mint_refuses_rather_than_silently_replacing(token_dir, tmp_path):
    """One token per ACCOUNT. ROOT-CAUSE UPDATE 2026-08-25: this used `--profile ftmo`
    as the colliding second profile because both FTMO profiles shared one login_sha256.
    The account switched 2026-08-21 (retired -> Verification 0) and `ftmo.yaml`
    is R2-seal-bound at the OLD account, so the two now legitimately differ. The guard's
    subject is unchanged — a DIFFERENT profile naming the SAME account must refuse, not
    silently replace — so the collision is reproduced with a temp profile carrying the
    live login_sha256."""

    _run(["mint", "--profile", LIVE_PROFILE, "--namespace", LIVE_PROFILE,
          "--expires-in-hours", "4", "--issued-by", "first"], token_dir, expect_rc=0)
    before = (token_dir / f"{_digest()}.token.json").read_text(encoding="utf-8")

    import yaml
    live = yaml.safe_load((REPO_ROOT / "config" / "profiles" / f"{LIVE_PROFILE}.yaml"
                           ).read_text(encoding="utf-8-sig"))
    sha = live["broker_profile"]["expected_account"]["login_sha256"]
    twin = tmp_path / "ftmo_twin.yaml"
    twin.write_text(
        "broker_profile:\n  expected_account:\n    login_sha256: %s\n" % sha,
        encoding="utf-8",
    )
    proc = _run(["mint", "--profile", str(twin), "--expires-in-hours", "1",
                 "--issued-by", "second"], token_dir)

    assert proc.returncode != 0
    assert "a token already exists" in proc.stderr
    assert (token_dir / f"{_digest()}.token.json").read_text(encoding="utf-8") == before, (
        "the refused mint still overwrote the token"
    )


def test_force_replaces_deliberately(token_dir):
    _run(["mint", "--profile", LIVE_PROFILE, "--namespace", LIVE_PROFILE,
          "--expires-in-hours", "4", "--issued-by", "first"], token_dir, expect_rc=0)

    proc = _run(["mint", "--profile", LIVE_PROFILE, "--namespace", LIVE_PROFILE,
                 "--expires-in-hours", "1", "--issued-by", "second", "--force"],
                token_dir, expect_rc=0)

    assert json.loads(proc.stdout)["lifetime_hours"] == 1.0


def test_f5_mint_and_verify_bind_the_exact_launcher_contract(token_dir):
    common = [
        "--profile", LIVE_PROFILE,
        "--namespace", F5_NAMESPACE,
        "--f5-minimal-size-usd", "10",
        "--f5-notional-initial-usd", "100000",
        "--tags", F5_TAGS,
    ]
    minted = _run(
        ["mint", *common, "--expires-in-hours", "1", "--issued-by", "test"],
        token_dir,
        expect_rc=0,
    )
    payload = json.loads(minted.stdout)
    assert payload["launch_contract"]["f5"]["enabled"] is True
    # The true invariant: normalization preserves the whole declared surface (was a
    # hardcoded 32 that rotted at the 2026-08-25 62-tag judge-era surface).
    assert len(payload["launch_contract"]["selected_tags"]) == len(F5_TAGS.split(","))
    assert payload["launch_contract_digest_sha256"]

    _run(["verify", *common], token_dir, expect_rc=0)
    drifted = _run(
        ["verify", *["11" if value == "10" else value for value in common]],
        token_dir,
        expect_rc=1,
    )
    assert json.loads(drifted.stdout)["reason"] == "activation_token_config_digest_mismatch"


def test_f5_mint_refuses_an_unbound_token(token_dir):
    proc = _run(
        [
            "mint",
            "--profile", LIVE_PROFILE,
            "--namespace", F5_NAMESPACE,
            "--f5-minimal-size-usd", "10",
            "--tags", F5_TAGS,
            "--no-bind-config",
            "--expires-in-hours", "1",
        ],
        token_dir,
    )

    assert proc.returncode != 0
    assert "must bind config plus its normalized launch contract" in proc.stderr


def test_f5_namespace_mint_refuses_a_missing_size_flag(token_dir):
    proc = _run(
        [
            "mint",
            "--profile", LIVE_PROFILE,
            "--namespace", F5_NAMESPACE,
            "--expires-in-hours", "1",
        ],
        token_dir,
    )

    assert proc.returncode != 0
    assert "accidental full-size route" in proc.stderr


def test_the_two_ftmo_profiles_pin_their_own_accounts():
    """ROOT-CAUSE REWRITE 2026-08-25 (was test_the_two_ftmo_profiles_really_do_share_
    an_account_digest): the shared-digest world ended with the 2026-08-21 account switch.
    `ftmo.yaml` is the sealed replay profile (R2-bound, H1 — its bytes must not move) and
    stays pinned at the RETIRED account; `operator_profile.yaml` moved with the live
    account (Verification 0). Each side now gets its own explicit pin so drift on
    EITHER file fails loudly — including any well-meant edit to the sealed one."""

    import yaml

    def _sha(name):
        data = yaml.safe_load((REPO_ROOT / "config" / "profiles" / f"{name}.yaml"
                               ).read_text(encoding="utf-8-sig"))
        return ((data.get("broker_profile") or {}).get("expected_account") or {}
                ).get("login_sha256")

    assert _sha(LIVE_PROFILE) == (
        "0000000000000000000000000000000000000000000000000000000000000000"
    ), "the live profile no longer names the Verification account"
    assert _sha("ftmo") == (
        "0000000000000000000000000000000000000000000000000000000000000000"
    ), "the SEALED replay profile moved — that is an R2 seal break (H1), investigate"


def _digest():
    import yaml

    data = yaml.safe_load(
        (REPO_ROOT / "config" / "profiles" / f"{LIVE_PROFILE}.yaml").read_text())
    return data["broker_profile"]["expected_account"]["login_sha256"]
