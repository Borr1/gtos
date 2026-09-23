"""What three adversarial passes over the activation token actually broke.

`test_activation_token.py` asserts the mechanism does what it was designed to
do. This file asserts it survives being attacked, and every test here
corresponds to a concrete way it did not. The two that matter most:

* ``test_the_token_directory_may_not_live_inside_the_repository`` — the token's
  own claim is that authorization "travels with the machine that is allowed to
  trade, not with the code". It did not. `run_book.py` reads `.env` with
  `override=True` *before* importing the safety module, `token_dir()` reads the
  environment at call time, and `ensure_signing_key` mints a fresh key wherever
  it is pointed. One line in an untracked in-repo file was a self-issued
  authorization for a funded account whose digest is published in-tree.

* ``test_a_deal_on_one_symbol_quoting_another_symbols_ticket_is_not_a_close``
  (in the never-strand file) — a token-free new position.

Everything else here is a narrower version of the same lesson: the gate's
strength was never the token check, it was the classification feeding it.
"""

from __future__ import annotations

import functools
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.mt5.mt5_interface import (
    TRADE_ACTION_DEAL,
    TRADE_ACTION_PENDING,
    TRADE_ACTION_SLTP,
)
from src.safety import activation_token as at

TICKET = 555
FLAT_ACCOUNT_BUY = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0,
                    "volume": 50.0, "position": 1, "price": 2000.0}
CLOSE_LONG = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1,
              "volume": 0.10, "position": TICKET}


class _Pos:
    def __init__(self, **kw):
        self.ticket = kw.get("ticket", TICKET)
        self.symbol = kw.get("symbol", "XAUUSD")
        self.type = kw.get("type", 0)
        self.volume = kw.get("volume", 0.10)
        self.sl = kw.get("sl", 1900.0)
        self.tp = kw.get("tp", 2000.0)


@pytest.fixture()
def token_dir(tmp_path, monkeypatch):
    directory = tmp_path / "activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(directory))
    return directory


def _unreadable_broker(symbol):
    raise at.PositionsUnavailable("broker read failed")


@at.strict_positions_provider
def _flat_account(symbol):
    return []


@at.strict_positions_provider
def _one_long(symbol):
    return [_Pos()]


# --------------------------------------------------------------------------
# B103 — the authorization root must be machine state, not repository state
# --------------------------------------------------------------------------


def test_the_token_directory_may_not_live_inside_the_repository(tmp_path, monkeypatch):
    """A token minted into a directory inside the working tree is refused, even
    though it is perfectly valid — because reaching it only required write
    access to the repo, not to the machine's activation directory."""

    inside = at.repo_root_for_activation() / "pipeline_state" / "_attack_activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(inside))

    assert at.token_dir_is_inside_repo() is True

    decision = at.authorize_broker_mutation(
        {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0, "volume": 0.10},
        account_login_sha256="deadbeef", audit=False,
    )

    assert not decision.allowed
    assert decision.reason == "activation_token_dir_inside_repository"


def test_a_repo_internal_token_directory_still_cannot_block_a_close(tmp_path, monkeypatch):
    """The repo-internal check must sit AFTER the risk-reducing return, or the
    fix for one hole becomes a strand."""

    inside = at.repo_root_for_activation() / "pipeline_state" / "_attack_activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(inside))

    decision = at.authorize_broker_mutation(
        dict(CLOSE_LONG), account_login_sha256="deadbeef",
        positions_provider=_one_long, audit=False,
    )

    assert decision.allowed
    assert decision.reason == "risk_reducing_position_close"


def test_a_directory_outside_the_repository_is_accepted(token_dir):
    assert at.token_dir_is_inside_repo() is False


def test_run_book_refuses_a_dotenv_override_of_the_activation_directory():
    """`run_book.py` must restore the machine's value after `load_dotenv`.

    Asserted on the mechanism rather than by importing `run_book` (which
    connects to a broker). The three things that must all be true are: the
    snapshot is taken before `load_dotenv`, the value is restored after, and the
    refusal is announced.
    """

    source = (at.repo_root_for_activation() / "run_book.py").read_text(encoding="utf-8")
    lines = source.splitlines()

    def _line_of(prefix):
        # Anchor on the STATEMENT, not on a mention of it in a comment — the
        # first draft of this test matched its own explanatory comment and
        # passed for the wrong reason.
        for index, line in enumerate(lines):
            if line.strip().startswith(prefix):
                return index
        raise AssertionError(f"run_book.py has no statement starting {prefix!r}")

    snapshot = _line_of("_activation_dir_from_machine = os.environ.get")
    dotenv = _line_of("load_dotenv(override=True)")
    restore = _line_of("os.environ[_ACTIVATION_DIR_ENV] = _activation_dir_from_machine")

    assert snapshot < dotenv < restore, (
        "the machine's activation directory must be captured BEFORE .env is read "
        "and restored after, or one untracked line relocates the authorization root"
    )
    assert "REFUSING the .env override" in source


# --------------------------------------------------------------------------
# B102/F-2 — the unverified escape hatch has to be bounded
# --------------------------------------------------------------------------


def test_an_unreadable_broker_does_not_authorize_a_pending_order():
    """The escape hatch exists for closes. A pending placement is never one."""

    direction, reason, _ = at.classify_request(
        {"action": TRADE_ACTION_PENDING, "symbol": "XAUUSD", "type": 2,
         "volume": 1.0, "price": 1900.0, "position": 1},
        _unreadable_broker,
    )
    assert direction == "increasing"


def test_an_unreadable_broker_does_not_authorize_a_deal_with_a_pending_order_type():
    """`type` 2-7 are pending types. A close is always a market DEAL."""

    direction, _reason, _ = at.classify_request(
        dict(FLAT_ACCOUNT_BUY, type=4), _unreadable_broker,
    )
    assert direction == "increasing"


def test_an_unreadable_broker_does_not_authorize_a_deal_carrying_opening_geometry():
    """No close-request producer in this repo carries `sl` or `tp`; the entry
    path carries both. A "close" that brings its own stop and target is an
    opening wearing a position ticket."""

    direction, _reason, _ = at.classify_request(
        dict(FLAT_ACCOUNT_BUY, sl=1900.0, tp=2100.0), _unreadable_broker,
    )
    assert direction == "increasing"


def test_a_deal_with_no_order_type_at_all_is_not_a_close():
    request = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "volume": 50.0, "position": 1}
    direction, _reason, _ = at.classify_request(request, _unreadable_broker)
    assert direction == "increasing"


# --------------------------------------------------------------------------
# B102/F-3, F-4 — the authority of the reader, not the shape of its answer
# --------------------------------------------------------------------------


def test_the_strictness_promise_survives_a_wrapper():
    """The marker is a function attribute, so `partial`/decorator wrapping drops
    it — and dropping it is fail-open on the exposure side."""

    assert at.provider_is_authoritative(_flat_account) is True
    assert at.provider_is_authoritative(functools.partial(_flat_account)) is True

    @functools.wraps(_flat_account)
    def wrapped(symbol):
        return _flat_account(symbol)

    assert at.provider_is_authoritative(wrapped) is True
    assert at.provider_is_authoritative(lambda symbol: []) is False


def test_a_wrapped_strict_provider_still_refuses_a_bogus_close():
    direction, _reason, verified = at.classify_request(
        FLAT_ACCOUNT_BUY, functools.partial(_flat_account),
    )
    assert direction == "increasing"
    assert verified is True


def test_a_partial_view_from_an_unmarked_provider_cannot_prove_absence():
    """An unmarked provider returning three positions is no more trustworthy
    about a fourth one's absence than one returning none."""

    direction, reason, verified = at.classify_request(
        dict(CLOSE_LONG, position=999),
        lambda symbol: [_Pos(ticket=1), _Pos(ticket=2)],
    )
    assert direction == "reducing"
    assert reason == "risk_reducing_position_close_unverified"
    assert verified is False


def test_a_container_that_cannot_be_sized_is_not_an_answer():
    """`if positions:` invokes truthiness, and a container whose `__bool__`
    raises (a numpy array is the realistic one) was swallowed into "unverified"
    silently. It still must not be read as an authoritative answer."""

    class _Ambiguous(list):
        def __bool__(self):
            raise ValueError("truth value is ambiguous")

        def __len__(self):
            raise ValueError("ambiguous")

    @at.strict_positions_provider
    def provider(symbol):
        return _Ambiguous([_Pos()])

    direction, reason, verified = at.classify_request(dict(CLOSE_LONG), provider)
    assert verified is False
    assert direction == "reducing"


# --------------------------------------------------------------------------
# B102/F-7, F-8, F-9 — arithmetic that decided the wrong way
# --------------------------------------------------------------------------


def test_a_short_whose_stop_is_widened_is_not_tightened_when_the_side_is_unknown():
    """`pos_type` defaulted to 0 (LONG), so a SHORT with no readable side had a
    stop moved *up* — away from entry — read as a tighten and pass token-free.
    The same field defaults to -1 (fail closed) on the DEAL path."""

    position_without_a_side = {"ticket": TICKET, "sl": 2100.0, "volume": 1.0}
    assert at.sltp_reduces_or_preserves_risk(
        {"action": TRADE_ACTION_SLTP, "position": TICKET, "sl": 2200.0},
        position_without_a_side,
    ) is False


def test_a_non_finite_position_volume_does_not_vacate_the_volume_bound():
    """`100.0 - nan` is `nan`, and `nan > 1e-9` is False, so the bound that keeps
    an oversized deal from counting as a close was simply skipped."""

    assert at.deal_reduces_existing_position(
        dict(CLOSE_LONG, volume=100.0),
        [_Pos(type=0, volume=float("nan"))],
    ) is False


def test_tightening_a_take_profit_on_a_stopless_position_needs_no_token():
    """MT5's SLTP writes both fields, so `_modify_tp` round-trips `sl` — which is
    0 on a position that has no stop. Treating that as "the stop was cleared"
    made a profit-lock tighten require a token."""

    assert at.sltp_reduces_or_preserves_risk(
        {"action": TRADE_ACTION_SLTP, "position": TICKET, "sl": 0.0, "tp": 2100.0},
        _Pos(type=0, sl=0.0),
    ) is True


def test_clearing_a_real_stop_still_needs_a_token():
    """The other half — otherwise the fix above is a blanket allow."""

    assert at.sltp_reduces_or_preserves_risk(
        {"action": TRADE_ACTION_SLTP, "position": TICKET, "sl": 0.0},
        _Pos(type=0, sl=1900.0),
    ) is False


# --------------------------------------------------------------------------
# B103 — "Never raises" was not true
# --------------------------------------------------------------------------


def test_a_non_ascii_signature_denies_rather_than_crashing(token_dir):
    """`hmac.compare_digest` raises TypeError on a non-ASCII str. The gate is
    documented as never raising, and callers catch only ActivationTokenError."""

    at.ensure_signing_key(token_dir)
    token = at.build_token(account_login_sha256="abc",
                           expires_utc=datetime.now(timezone.utc) + timedelta(hours=1))
    token["signature"] = "ünicode"

    ok, reason, _detail = at.verify_token(token, account_login_sha256="abc", directory=token_dir)

    assert ok is False
    assert reason == "activation_token_signature_invalid"


def test_a_token_file_with_non_utf8_bytes_denies_rather_than_crashing(token_dir):
    token_dir.mkdir(parents=True, exist_ok=True)
    at.token_path_for("abc", directory=token_dir).write_bytes(b"\xff\xfe not utf-8")

    token, status, _path = at.read_token("abc", directory=token_dir)

    assert token is None
    assert status == "activation_token_unreadable"


def test_a_corrupt_signing_key_does_not_brick_the_mint_path(token_dir):
    """A key file with non-UTF-8 bytes raised out of `ensure_signing_key`, so the
    operator could not re-authorize without deleting the file by hand."""

    token_dir.mkdir(parents=True, exist_ok=True)
    at.signing_key_path(token_dir).write_bytes(b"\xff\xfe\x00")

    assert at.load_signing_key(token_dir) is None
    key = at.ensure_signing_key(token_dir)
    assert key and len(key) >= 32


def test_the_operator_status_command_survives_a_malformed_token(token_dir):
    token_dir.mkdir(parents=True, exist_ok=True)
    at.token_path_for("abc", directory=token_dir).write_bytes(b"\xff\xfe not utf-8")

    state = at.describe_activation_state(directory=token_dir)

    assert state["tokens"] and state["tokens"][0]["status"] == "activation_token_unreadable"


# --------------------------------------------------------------------------
# B103 — the token store is shared by two live books
# --------------------------------------------------------------------------


def test_a_token_is_never_visible_half_written(token_dir):
    """Both books share one activation directory. An in-place truncate let a
    concurrent reader see a partial file and refuse a legitimate entry."""

    now = datetime.now(timezone.utc)
    path = at.write_token(
        at.build_token(account_login_sha256="abc", expires_utc=now + timedelta(hours=1)),
        directory=token_dir,
    )
    for _ in range(25):
        at.write_token(
            at.build_token(account_login_sha256="abc", expires_utc=now + timedelta(hours=2)),
            directory=token_dir,
        )
        token, status, _p = at.read_token("abc", directory=token_dir)
        assert status == "ok", "a reader saw a partially written token"
        assert token is not None

    assert not list(token_dir.glob("*.tmp*")), "a temp file was left behind"
    assert json.loads(path.read_text(encoding="utf-8"))["account_login_sha256"] == "abc"


def test_the_activation_directory_is_owner_only(token_dir):
    at.ensure_signing_key(token_dir)

    mode = at.token_dir(token_dir).stat().st_mode & 0o777

    assert mode == 0o700, f"activation directory is {oct(mode)}, expected 0o700"
