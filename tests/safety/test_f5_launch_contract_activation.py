"""F5 argv authorization: exact contract in, no accidental full-size route.

These tests never import MetaTrader5 or connect to a broker. They drive the same
signed activation decision used by ``RealMT5.order_send`` against temporary
token/config files.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.mt5.mt5_interface import (
    MAGIC_F5_MINIMAL,
    MAGIC_NUMBER,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_REMOVE,
)
from src.safety import activation_token as at


REPO_ROOT = Path(__file__).resolve().parents[2]
F5_NAMESPACE = "operator"
OTHER_F5_NAMESPACE = "redacted_account_f5_minimal"
ACCOUNT_DIGEST = "a" * 64
ENTRY = {
    "action": TRADE_ACTION_DEAL,
    "symbol": "XAUUSD",
    "type": 0,
    "volume": 0.01,
    "sl": 1900.0,
    "tp": 2000.0,
}
F5_TAGS = tuple(
    json.loads((REPO_ROOT / "config/live_armed_set.json").read_text(encoding="utf-8"))
    ["accounts"][F5_NAMESPACE]["armed_sleeves"]
)


def _config_tree(tmp_path: Path) -> Path:
    config = tmp_path / "agent_config.yaml"
    config.write_text("risk: 2.0\n", encoding="utf-8")
    profiles = tmp_path / "config/profiles"
    profiles.mkdir(parents=True)
    (profiles / "p.yaml").write_text("overlay: same\n", encoding="utf-8")
    (profiles / "p2.yaml").write_text("overlay: same\n", encoding="utf-8")
    return config


def _contract(**overrides):
    values = {
        "f5_enabled": True,
        "target_risk_usd": 10,
        "notional_initial_usd": 100_000,
        "tags": F5_TAGS,
        "namespace": F5_NAMESPACE,
        "magic": MAGIC_F5_MINIMAL,
        "profile": "p",
        "q1_mode": "off",
        "q1_selection": None,
        "q2_enabled": False,
    }
    values.update(overrides)
    return at.normalized_f5_launch_contract(**values)


def _digest(config: Path, contract: dict, *, profile: str = "p") -> str:
    value = at.config_digest_for(
        config,
        profile,
        repo_root=config.parent,
        launch_contract=contract,
    )
    assert value is not None
    return value


def _mint(token_dir: Path, *, namespace: str, config_digest: str | None) -> None:
    now = datetime.now(timezone.utc)
    at.write_token(
        at.build_token(
            account_login_sha256=ACCOUNT_DIGEST,
            expires_utc=now + timedelta(hours=1),
            namespace=namespace,
            config_digest_sha256=config_digest,
            issued_by="test",
            now=now,
        ),
        directory=token_dir,
    )


def _authorize(
    token_dir: Path,
    *,
    namespace: str,
    config_digest: str,
):
    return at.authorize_broker_mutation(
        dict(ENTRY),
        account_login_sha256=ACCOUNT_DIGEST,
        namespace=namespace,
        config_digest_sha256=config_digest,
        require_namespace_binding=True,
        require_config_digest_binding=True,
        directory=token_dir,
        audit=False,
    )


def test_exact_f5_launch_contract_authorizes_new_exposure(tmp_path):
    config = _config_tree(tmp_path)
    expected = _contract()
    expected_digest = _digest(config, expected)
    token_dir = tmp_path / "token"
    _mint(token_dir, namespace=F5_NAMESPACE, config_digest=expected_digest)

    decision = _authorize(
        token_dir,
        namespace=F5_NAMESPACE,
        config_digest=expected_digest,
    )

    assert decision.allowed is True
    assert decision.reason == "activation_token_valid"


@pytest.mark.parametrize(
    "label,expected_overrides,actual_overrides",
    [
        ("cash target", {}, {"target_risk_usd": 11}),
        ("notional base", {}, {"notional_initial_usd": 90_000}),
        ("selected tags", {}, {"tags": F5_TAGS[:-1]}),
        (
            "Q1 shadow to apply",
            {"q1_mode": "shadow", "q1_selection": "crypto"},
            {"q1_mode": "apply", "q1_selection": "crypto"},
        ),
        ("Q2 observation presence", {}, {"q2_enabled": True}),
    ],
)
def test_f5_token_refuses_target_tag_q1_and_q2_drift(
    tmp_path,
    label,
    expected_overrides,
    actual_overrides,
):
    config = _config_tree(tmp_path)
    expected = _contract(**expected_overrides)
    token_dir = tmp_path / "token"
    _mint(token_dir, namespace=F5_NAMESPACE, config_digest=_digest(config, expected))
    actual_values = dict(expected_overrides)
    actual_values.update(actual_overrides)
    actual = _contract(**actual_values)

    decision = _authorize(
        token_dir,
        namespace=F5_NAMESPACE,
        config_digest=_digest(config, actual),
    )

    assert decision.allowed is False, label
    assert decision.reason == "activation_token_config_digest_mismatch", label


def test_f5_token_refuses_namespace_drift(tmp_path):
    config = _config_tree(tmp_path)
    expected = _contract()
    token_dir = tmp_path / "token"
    _mint(token_dir, namespace=F5_NAMESPACE, config_digest=_digest(config, expected))
    actual = _contract(namespace=OTHER_F5_NAMESPACE)

    decision = _authorize(
        token_dir,
        namespace=OTHER_F5_NAMESPACE,
        config_digest=_digest(config, actual),
    )

    assert decision.allowed is False
    assert decision.reason == "activation_token_namespace_mismatch"


def test_f5_token_refuses_profile_drift_even_when_profile_bytes_match(tmp_path):
    config = _config_tree(tmp_path)
    expected = _contract(profile="p")
    token_dir = tmp_path / "token"
    _mint(token_dir, namespace=F5_NAMESPACE, config_digest=_digest(config, expected))
    actual = _contract(profile="p2")

    decision = _authorize(
        token_dir,
        namespace=F5_NAMESPACE,
        config_digest=_digest(config, actual, profile="p2"),
    )

    assert decision.allowed is False
    assert decision.reason == "activation_token_config_digest_mismatch"


def test_f5_magic_drift_is_refused_while_normalizing_the_startup_contract():
    with pytest.raises(ValueError, match="requires broker magic"):
        _contract(magic=MAGIC_NUMBER)


def test_missing_f5_flag_cannot_start_the_f5_identity_at_full_size():
    with pytest.raises(ValueError, match="accidental full-size route"):
        at.normalized_f5_launch_contract(
            f5_enabled=False,
            target_risk_usd=0,
            notional_initial_usd=100_000,
            tags=F5_TAGS,
            namespace=F5_NAMESPACE,
            magic=MAGIC_F5_MINIMAL,
            profile="p",
        )


def test_run_book_missing_f5_flag_exits_before_any_broker_connection(tmp_path):
    """Exercise the launcher seam, not only the normalizer in isolation."""

    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env.pop("GTOS_ACTIVATION_TOKEN_DIR", None)
    env.pop("GTOS_MT5_TERMINAL_PATH", None)
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "run_book.py"),
            "--config",
            str(REPO_ROOT / "config/agent_config.yaml"),
            "--profile",
            "operator_profile",
            "--namespace",
            F5_NAMESPACE,
            "--once",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    # This repository is also the live F5 worktree.  During an in-place deployment the
    # protected worker legitimately owns the global namespace mutex, which is an even earlier
    # fail-closed boundary than argv normalization.  Preserve the subprocess assertion for CI
    # and stopped-worker verification, but do not stop the live worker merely to let this test
    # reach the next pre-connect guard; the pure normalizer test above covers that contract.
    if proc.returncode == 4 and "single-instance mutex" in proc.stderr:
        assert "MT5 connect failed" not in proc.stderr
        pytest.skip("live F5 worker owns the namespace mutex")

    assert proc.returncode == 6
    assert "accidental full-size route" in proc.stderr
    assert "MT5 connect failed" not in proc.stderr


def test_f5_requires_the_token_to_declare_namespace_and_config_bindings(tmp_path):
    config = _config_tree(tmp_path)
    expected_digest = _digest(config, _contract())

    namespace_free = tmp_path / "namespace-free"
    _mint(namespace_free, namespace="", config_digest=expected_digest)
    decision = _authorize(
        namespace_free,
        namespace=F5_NAMESPACE,
        config_digest=expected_digest,
    )
    assert decision.allowed is False
    assert decision.reason == "activation_token_namespace_binding_required"

    config_free = tmp_path / "config-free"
    _mint(config_free, namespace=F5_NAMESPACE, config_digest=None)
    decision = _authorize(
        config_free,
        namespace=F5_NAMESPACE,
        config_digest=expected_digest,
    )
    assert decision.allowed is False
    assert decision.reason == "activation_token_config_digest_binding_required"


def test_required_f5_bindings_never_block_a_risk_reducing_cancel(tmp_path):
    decision = at.authorize_broker_mutation(
        {"action": TRADE_ACTION_REMOVE, "order": 12345},
        account_login_sha256=None,
        namespace=F5_NAMESPACE,
        config_digest_sha256=None,
        require_namespace_binding=True,
        require_config_digest_binding=True,
        directory=tmp_path / "no-token",
        audit=False,
    )

    assert decision.allowed is True
    assert decision.risk_direction == "reducing"


def test_non_f5_config_digest_is_legacy_compatible(tmp_path):
    config = _config_tree(tmp_path)
    profile = tmp_path / "config/profiles/p.yaml"
    expected_parts = [
        f"{config.name}:{hashlib.sha256(config.read_bytes()).hexdigest()}",
        f"{profile.name}:{hashlib.sha256(profile.read_bytes()).hexdigest()}",
    ]
    legacy = hashlib.sha256("|".join(expected_parts).encode("utf-8")).hexdigest()

    assert at.config_digest_for(config, "p", repo_root=tmp_path) == legacy


def test_semantically_identical_tags_have_one_contract_and_q2_stays_observation_only():
    canonical = _contract(q2_enabled=True)
    reordered = _contract(tags=tuple(reversed(F5_TAGS)) + (F5_TAGS[0],), q2_enabled=True)

    assert reordered == canonical
    assert canonical["q2"] == {"enabled": True, "effect": "observation_only"}
    # Was a hardcoded 32 (rotted at the 62-tag surface): the invariant is that
    # normalization keeps exactly the declared set, whatever the ladder day's surface.
    assert len(canonical["selected_tags"]) == len(set(F5_TAGS))
