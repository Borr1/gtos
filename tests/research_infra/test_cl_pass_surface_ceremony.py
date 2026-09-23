"""Behavioural gates for Session CL's zero-mutation ceremony package."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / "docs/audits/fable5-vision-audit-20260725/phase17/activation_pass_surface/verify_pass_surface.py"
)
SPEC = importlib.util.spec_from_file_location("cl_pass_surface_ceremony", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


FTMO_TAGS = "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout"
FN_TAGS = "crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert"
FLOOR = "sub_mid_dn_revert,sub_xvol_pullback"


def _file(path: str, sha: str) -> dict:
    return {"path": path, "present": True, "sha256": sha, "bytes": 10}


def valid_capture() -> dict:
    ftmo_cmd = (
        f"python.exe run_book.py --namespace operator_profile --tags {FTMO_TAGS} "
        "--frontier-exits mx_btcusd_d1_donchian_20_breakout "
        f"--spread-geometry-floor {FLOOR}"
    )
    fn_cmd = (
        f"python.exe run_book.py --namespace redacted_account_live_bee34003 --tags {FN_TAGS} "
        f"--spread-geometry-floor {FLOOR}"
    )
    return {
        "schema": "gtos.phase17.cl.host_pass_surface_capture.v1",
        "captured_at_utc": "2026-08-01T00:00:00Z",
        "git_branch": "vps/ultimate-conditioned-expansion-minimal-2026-06-18",
        "git_head": "267cccc94abcdef",
        "files": {
            "supervisor": _file("scripts/run_book_supervisor.ps1", "63079cec" + "0" * 56),
            "agent_config": _file("config/agent_config.yaml", "a" * 64),
            "redacted_account_profile": _file("config/profiles/redacted_account.yaml", "b" * 64),
            "run_book": _file("run_book.py", "c" * 64),
        },
        "supervisor_books_block": "$books = @(...)\n",
        "supervisor_books_block_sha256": "d" * 64,
        "supervisor_book_hashtable_keys": ["frontier", "kill", "log", "ns", "profile", "tags", "term"],
        "books": {
            "operator_profile": [
                {"pid": 10, "creation_date": "2026-08-01T00:00:00Z", "command_line": ftmo_cmd}
            ],
            "redacted_account_live_bee34003": [
                {"pid": 11, "creation_date": "2026-08-01T00:00:01Z", "command_line": fn_cmd}
            ],
        },
        "firing_ledgers": {
            "operator_profile": _file("ftmo/firing_sleeves.json", "e" * 64),
            "redacted_account_live_bee34003": _file("fn/firing_sleeves.json", "f" * 64),
        },
        "log_proofs": {
            "operator_profile": [
                "BookLauncher starting: tfs=[16388, 16408] poll=60s",
                "FRONTIER EXIT CONTRACT IS ON for mx_btcusd_d1_donchian_20_breakout: target_5R (broker TP 5.0R)",
                "SPREAD-GEOMETRY FLOOR IS ON for sub_mid_dn_revert at spread_r <= 0.1000",
                "SPREAD-GEOMETRY FLOOR IS ON for sub_xvol_pullback at spread_r <= 0.1000",
            ],
            "redacted_account_live_bee34003": [
                "BookLauncher starting: tfs=[16388] poll=60s",
                "SPREAD-GEOMETRY FLOOR IS ON for sub_mid_dn_revert at spread_r <= 0.1000",
                "SPREAD-GEOMETRY FLOOR IS ON for sub_xvol_pullback at spread_r <= 0.1000",
            ],
        },
    }


def test_real_package_is_hash_sealed_and_empty() -> None:
    """The package's own properties: empty, copies nothing, every file at its sealed hash.

    The restricted-config guard is asserted separately below. It is a PRECONDITION the
    ceremony checked before executing on 2026-08-01 -- "nothing has edited a restricted
    config in this worktree" -- and every live arming decision since legitimately edits
    `config/agent_config.yaml`. Leaving it inside `check_package` meant one authorized
    config byte took the ceremony's package proof down with it.
    """
    MOD.check_package(restricted_config_guard=False)


def test_the_restricted_config_guard_is_declared_and_its_drift_is_named() -> None:
    """The guard still runs; what changed is that its result is reported, not conflated.

    Both guarded paths must exist (`restricted_config_drift` refuses a missing one), and any
    that has moved must be one the record explains. `config/agent_config.yaml` is the live
    arming surface: OD-AI-2/OD-AI-3 and the 2026-08-12 F5 landing all edit it, and
    CLAUDE.md §4 records that it is the host's own config -- not this repository's -- that
    arms a book. `config/profiles/redacted_account.yaml` is the redacted_account profile and is inside
    the activation-token digest, so a change there is a re-mint event and must be visible.
    """
    manifest = MOD.load(MOD.MANIFEST)
    guarded = set(manifest["restricted_config_worktree_guard"])
    assert guarded == {"config/agent_config.yaml", "config/profiles/redacted_account.yaml"}

    explained = {
        "config/agent_config.yaml":
            "the live arming surface; OD-AI-* and the F5 landing edit it by owner decision",
    }
    drifted = MOD.restricted_config_drift()
    unexplained = sorted(set(drifted) - set(explained))
    assert not unexplained, (
        "a restricted config moved with no recorded reason: " + ", ".join(unexplained)
        + "\nThis is the guard doing its job — name the decision or restore the bytes."
    )


def test_valid_host_capture_proves_exact_current_set() -> None:
    MOD.validate_host(valid_capture())


@pytest.mark.parametrize("bad_tags", ["", "not_a_real_sleeve"])
def test_empty_fail_open_and_all_typo_tags_are_refused(bad_tags: str) -> None:
    capture = valid_capture()
    command = capture["books"]["operator_profile"][0]["command_line"]
    capture["books"]["operator_profile"][0]["command_line"] = command.replace(FTMO_TAGS, bad_tags)
    with pytest.raises(MOD.Refusal, match="tags"):
        MOD.validate_host(capture)


def test_nonempty_approval_cannot_be_relabelled_as_no_op() -> None:
    approved = MOD.load(MOD.APPROVED)
    approved["approved_direct_additions"]["FTMO"] = ["fx_jpy"]
    with pytest.raises(MOD.Refusal, match="direct approval"):
        MOD.validate_approved(approved)


def test_postflight_refuses_any_supervisor_process_or_ledger_change() -> None:
    before = valid_capture()
    after = copy.deepcopy(before)
    after["books"]["operator_profile"][0]["pid"] = 99
    with pytest.raises(MOD.Refusal, match="pre/post host state changed"):
        MOD.validate_postflight(before, after)
