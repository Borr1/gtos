"""``authorize_broker_mutation`` says "Never raises". It raised. (B321)

Found by running D-3 sub-case (d) — ``GTOS_ACTIVATION_TOKEN_DIR`` pointing under
a home that cannot be resolved. The guard at ``token_dir_is_inside_repo`` catches
``RuntimeError`` correctly; the **denial branch it then takes** re-computed
``token_dir(directory)`` outside that guard, so the exception escaped from the
one function whose whole contract is to return a decision.

Why it is not exotic. ``Path.expanduser()`` raises ``RuntimeError('Could not
determine home directory.')`` whenever ``~`` cannot be resolved, and the module's
own **default** token directory is ``~/.gtos/activation``. A Windows scheduled
task running as ``SYSTEM`` or a service account with no ``USERPROFILE`` is D-6's
scenario, and it lands here.

Two things are asserted, and they are different in kind:

* the escape is **only** on the exposure-increasing path — a close returns before
  any of this, so the never-strand invariant was never at risk. That is worth
  pinning, because it is the reason this was a robustness defect rather than the
  one defect that costs money.
* the operator's read-only ``describe_activation_state`` must survive it too. It
  crashed on the same call, which is the same shape as B103/J1: a status command
  that dies on the state it exists to explain.
"""

from __future__ import annotations

import pytest

from src.safety import activation_token as at

TRADE_ACTION_DEAL = 1
TICKET = 981_233
DIGEST = at.account_digest(531_325_516)

CLOSE = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1,
         "volume": 0.10, "position": TICKET}
ENTRY = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0,
         "volume": 0.10, "sl": 1900.0, "tp": 2000.0}

# Two ways to make `~` unresolvable, because they fail in different places:
# an explicit unknown user, and the module's own default with no home at all.
UNRESOLVABLE = "~nosuchuser_gtos_b321/activation"


@pytest.fixture()
def no_home(monkeypatch):
    """The Windows-service-account shape: `~` cannot be expanded."""

    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, UNRESOLVABLE)
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)
    return UNRESOLVABLE


def test_token_dir_really_is_unresolvable(no_home):
    """The fixture must actually reproduce the condition, or the rest is vacuous."""

    with pytest.raises(RuntimeError):
        at.token_dir()


def test_an_entry_is_denied_not_crashed(no_home):
    decision = at.authorize_broker_mutation(
        dict(ENTRY), account_login_sha256=DIGEST, audit=False)

    assert decision.allowed is False
    assert decision.risk_direction == "increasing"
    # The path could not be resolved, so it cannot be proved to sit outside the
    # repository; `token_dir_is_inside_repo` fails closed and says so.
    assert decision.reason == "activation_token_dir_inside_repository"


def test_the_denial_still_tells_the_operator_which_path_was_tried(no_home):
    """A denial naming no path sends an operator hunting for a directory that
    does not exist. The unresolvable marker carries the raw value instead."""

    decision = at.authorize_broker_mutation(
        dict(ENTRY), account_login_sha256=DIGEST, audit=False)

    assert decision.token_path
    assert "unresolvable" in decision.token_path
    assert UNRESOLVABLE in decision.token_path


def test_a_close_is_untouched_by_any_of_it(no_home):
    """The invariant that outranks the defect. A close never reaches the token
    directory at all, so an unresolvable one cannot strand a position."""

    decision = at.authorize_broker_mutation(
        dict(CLOSE), account_login_sha256=DIGEST, audit=False)

    assert decision.allowed is True
    assert decision.risk_direction == "reducing"


def test_describe_activation_state_does_not_crash(no_home):
    state = at.describe_activation_state(DIGEST)

    assert state["token_dir_exists"] is False
    assert "unresolvable" in state["token_dir"]
    assert state["tokens"] == []


def test_token_dir_display_never_raises_and_round_trips_a_good_path(tmp_path, monkeypatch):
    """The helper must not become a stringifier that hides real paths."""

    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(tmp_path))
    assert at.token_dir_display() == str(tmp_path)

    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, UNRESOLVABLE)
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)
    rendered = at.token_dir_display()
    assert rendered.startswith("<unresolvable:")
    assert "RuntimeError" in rendered
