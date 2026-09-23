"""`scripts/mt5_preflight.py` was the last raw `mt5.order_send` with no halt check
and no activation token, on a host with two funded accounts and `trade_allowed`
true — and it is **byte-identical on the VPS lineage**, so it is there too.

It is not gated, it is de-fanged: Test 5 now uses `mt5.order_check`, which
submits the identical request to the broker's server for validation and returns
the same retcode — including 10030, unsupported filling mode, which is the one
answer the test exists to produce — without creating an order, a ticket, or
broker history. Gating it with a token would have been worse, because this script
has to run *before* a token exists.

The first two tests are behavioural: the script is driven as a subprocess and
asserted on what it does. The third is a census, because "this file contains no
broker mutation" is a statement about the file's shape.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "scripts" / "mt5_preflight.py"


def _run(args, env_extra=None):
    """Run the script. It refuses BEFORE `import MetaTrader5`, so these calls
    never need a broker and never reach one."""

    env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp"}
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(PREFLIGHT), *args],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60, env=env,
    )


def test_the_arming_flag_refuses_instead_of_silently_changing_meaning():
    """An operator running an old runbook line must not be left believing an
    order was placed. Silence would be the dangerous outcome here."""

    proc = _run(["--test-order"])

    assert proc.returncode == 2, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    assert "REFUSING TO RUN" in proc.stdout
    assert "order_check" in proc.stdout
    assert "MT5 PRE-FLIGHT CHECK" not in proc.stdout, (
        "the script started its checks anyway; the refusal must come first"
    )


def test_a_stale_environment_variable_also_refuses():
    """`GTOS_MT5_PREFLIGHT_TEST_ORDER=1` left in a VPS environment is evidence of
    an expectation that no longer holds, so it must not be quietly ignored."""

    for value in ("1", "true", "YES"):
        proc = _run([], env_extra={"GTOS_MT5_PREFLIGHT_TEST_ORDER": value})
        assert proc.returncode == 2, f"value={value!r} did not refuse"
        assert "REFUSING TO RUN" in proc.stdout


def test_the_preflight_no_longer_mutates_broker_state():
    """A census. `order_send` places an order; `order_check` validates one. This
    file must contain no call to the first."""

    tree = ast.parse(PREFLIGHT.read_text(encoding="utf-8"))
    calls = [
        f"{PREFLIGHT.name}:{node.lineno} {node.func.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"order_send", "positions_modify"}
    ]

    assert not calls, f"a broker mutation returned to the preflight: {calls}"


def test_the_capability_check_still_exists_and_uses_order_check():
    """De-fanged, not deleted. The filling-mode answer is the reason Test 5
    exists — the 18-of-19 symbol-spec divergence between the two brokers makes it
    more relevant now, not less."""

    tree = ast.parse(PREFLIGHT.read_text(encoding="utf-8"))
    checks = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "order_check"
    ]

    assert checks, "Test 5 lost its capability check entirely"
    source = PREFLIGHT.read_text(encoding="utf-8")
    assert "10030" in source, "the unsupported-filling-mode answer is no longer reported"


def test_the_config_path_resolves_against_the_repo_not_the_cwd():
    """It used to open `config/agent_config.yaml` relative to the CWD, so an
    operator standing anywhere but the repo root got a FileNotFoundError on a
    check that had nothing to do with where they were standing."""

    source = PREFLIGHT.read_text(encoding="utf-8")

    assert "open('config/agent_config.yaml')" not in source
    assert "_CONFIG_PATH" in source


@pytest.mark.parametrize("path", [
    "scripts/mt5_preflight.py",
])
def test_the_vps_still_carries_the_old_version(path):
    """Recorded, not asserted as a failure: the ungated file is byte-identical on
    the VPS lineage commit, i.e. it is on the credentialed host right now. This
    test documents the fact and will start failing once the VPS lineage moves —
    at which point the runbook's claim needs re-checking, which is the point."""

    proc = subprocess.run(
        ["git", "show", f"redacted_host:{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        pytest.skip("VPS lineage commit not present in this clone")

    assert "order_send" in proc.stdout, (
        "the VPS lineage copy no longer contains order_send — the runbook's "
        "description of what is on that host is now stale and must be re-derived"
    )
