"""run_book.py's environment-authority contract, pinned at the LIVE lineage's design.

REWRITTEN 2026-08-25 (root cause: STALE EXPECTATION). The two original tests asserted a
`_UNDIGESTED_BEHAVIOR_ENV` strip loop that exists in NO commit reachable from this
repository (`git log --all -S _UNDIGESTED_BEHAVIOR_ENV` returns nothing): they arrived
with the f5-live truth snapshot (`68bad3751`, committed under
docs/audits/fable-20260825/OWNER-GRANT-20260825.md; shipped at `79c8ecb75`,
CEREMONY-RECEIPT-20260825.md) already red, pinning a mechanism the live surface never
carried. The live design is WATCH, not STRIP:

  * behavior env (GTOS_PROFILE / GTOS_MT5_TERMINAL_PATH / GTOS_UB_DERISK_MODE) stays a
    documented input channel (run_book.py --terminal-path fallback; config.PROFILE_ENV_VAR;
    launcher derisk resolution) and is published, together with the token dir, into every
    heartbeat BEFORE any broker call — `BookLauncher.WATCHED_ACTIVATION_ENV` +
    `_authority_state()` (src/components/ultimate_book/launcher.py) — because these
    variables change live behaviour without invalidating an activation token, and
    recording what the running worker resolved is what makes drift observable at all;
  * GTOS_ACTIVATION_TOKEN_DIR is MACHINE-OWNED: run_book.py snapshots the machine value
    BEFORE `load_dotenv(override=True)` and refuses a `.env` relocation of the
    authorization root (run_book.py prologue, B103) — the exact protection the second
    original test was about, kept here at the true mechanism.

Both protections the original file provided survive, at the true values, and both are now
behavioural (the refusal logic is EXECUTED, not grepped).
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

BEHAVIOR_ENV = ("GTOS_PROFILE", "GTOS_MT5_TERMINAL_PATH", "GTOS_UB_DERISK_MODE")
TOKEN_DIR_ENV = "GTOS_ACTIVATION_TOKEN_DIR"


def _run_book_prologue() -> str:
    """Everything run_book.py executes before its first `src.*` import: the dotenv load
    and the machine-owned token-dir defence. The slice boundary is the first runtime
    import, which is also where the original tests drew it."""
    source = (REPO / "run_book.py").read_text(encoding="utf-8")
    return source[: source.index("from src.security import install_runtime_monitoring")]


def _exec_prologue(monkeypatch, dotenv_sets: dict[str, str]) -> None:
    """Execute run_book.py's real prologue bytes with `dotenv.load_dotenv` replaced by a
    stub that applies `dotenv_sets` — i.e. simulate exactly what an untracked repo `.env`
    could do, without touching the filesystem or the heavy runtime imports."""
    fake = types.ModuleType("dotenv")

    def load_dotenv(*args, **kwargs):
        for key, value in dotenv_sets.items():
            # Via monkeypatch, NEVER os.environ directly: a bare write after
            # `delenv(raising=False)` on an absent key had no restore record and
            # leaked "smooth-from-dotenv" process-wide, failing an unrelated
            # tripwire test suites later (isolation defect, root-caused 2026-08-25).
            monkeypatch.setenv(key, value)
        return True

    fake.load_dotenv = load_dotenv
    monkeypatch.setitem(sys.modules, "dotenv", fake)
    exec(compile(_run_book_prologue(), "run_book.py<prologue>", "exec"), {"__name__": "rb"})


def test_watched_env_covers_the_behavior_vars_and_reaches_the_heartbeat(monkeypatch, tmp_path):
    """The behavior variables are not stripped — they are WATCHED. Every one of them, plus
    the token dir, must be in `WATCHED_ACTIVATION_ENV`, and the values the running worker
    resolved must land in the on-disk heartbeat an out-of-process monitor reads."""
    from src.components.ultimate_book.launcher import BookLauncher

    for name in BEHAVIOR_ENV + (TOKEN_DIR_ENV,):
        assert name in BookLauncher.WATCHED_ACTIVATION_ENV, (
            f"{name} left the watched set: it changes live behaviour without invalidating "
            f"an activation token, so a monitor could no longer see it drift"
        )

    sentinel = {name: f"sentinel-{i}" for i, name in enumerate(BEHAVIOR_ENV)}
    for name, value in sentinel.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv(TOKEN_DIR_ENV, raising=False)

    stub = types.SimpleNamespace(
        WATCHED_ACTIVATION_ENV=BookLauncher.WATCHED_ACTIVATION_ENV,
        owner=types.SimpleNamespace(base_config={}),
        _repo=tmp_path,
        _namespace="envtest",
        _last_link_healthy=True,
    )
    stub._authority_state = lambda: BookLauncher._authority_state(stub)
    state = stub._authority_state()
    assert state["env"] == {**sentinel, TOKEN_DIR_ENV: None}

    # and the same block reaches the heartbeat file, written before any broker call
    from datetime import datetime, timezone
    import json

    BookLauncher._write_heartbeat(stub, datetime.now(timezone.utc))
    hb = json.loads(
        (tmp_path / "pipeline_state" / "ultimate_book" / "envtest" / "heartbeat.json")
        .read_text(encoding="utf-8")
    )
    assert hb["env"] == {**sentinel, TOKEN_DIR_ENV: None}


def test_activation_token_directory_remains_machine_owned_not_env_overridable(
        monkeypatch, capsys):
    """A repo `.env` must NOT be able to relocate the authorization root: the token layer
    would mint a fresh signing key wherever it is pointed, so relocation is a self-issued
    authorization, not a broken config. run_book.py's own prologue must restore the
    machine value and say so on stderr. Executed, not grepped."""
    monkeypatch.setenv(TOKEN_DIR_ENV, "/machine/owned/dir")
    _exec_prologue(monkeypatch, {TOKEN_DIR_ENV: "/evil/from-dotenv"})
    assert os.environ[TOKEN_DIR_ENV] == "/machine/owned/dir"
    err = capsys.readouterr().err
    assert "REFUSING" in err and TOKEN_DIR_ENV in err


def test_a_dotenv_token_dir_with_no_machine_value_is_removed_not_adopted(monkeypatch, capsys):
    """The unset-machine case: `.env` supplying the ONLY value is still a relocation of the
    authorization root and must be popped, so the token layer falls back to its default
    (`~/.gtos/activation`) rather than to a repo-controlled path."""
    monkeypatch.delenv(TOKEN_DIR_ENV, raising=False)
    _exec_prologue(monkeypatch, {TOKEN_DIR_ENV: "/evil/from-dotenv"})
    assert TOKEN_DIR_ENV not in os.environ
    assert "REFUSING" in capsys.readouterr().err


def test_behavior_env_is_watched_not_stripped_by_the_prologue(monkeypatch, capsys):
    """The inverse pin, so the strip design cannot come back silently: the prologue's
    defence is SCOPED to the token dir. Machine-set behavior env survives, and a `.env`
    value for a behavior variable is accepted (it is watched into the heartbeat by the
    launcher, which the first test pins) — not popped, not reverted, and not refused."""
    monkeypatch.setenv("GTOS_PROFILE", "machine-profile")
    monkeypatch.delenv("GTOS_UB_DERISK_MODE", raising=False)
    monkeypatch.setenv(TOKEN_DIR_ENV, "/machine/owned/dir")
    _exec_prologue(monkeypatch, {"GTOS_UB_DERISK_MODE": "smooth-from-dotenv"})
    assert os.environ["GTOS_PROFILE"] == "machine-profile"
    assert os.environ["GTOS_UB_DERISK_MODE"] == "smooth-from-dotenv"
    assert os.environ[TOKEN_DIR_ENV] == "/machine/owned/dir"
    assert "REFUSING" not in capsys.readouterr().err
