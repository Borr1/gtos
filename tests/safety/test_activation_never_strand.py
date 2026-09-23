"""The never-strand invariant, exercised the way the real broker actually fails.

`test_activation_token.py` already asserts that a broker read failure cannot
block a flatten — but it simulates that failure with a fake whose
``positions_get`` **raises**. ``MetaTrader5.positions_get`` does not raise. It
returns ``None``. ``RealMT5.get_positions`` turned that ``None`` into ``[]``
(`src/mt5/mt5_real.py:321-322`), the gate read the empty list as "the position
is gone", and a close therefore classified as **new exposure** and was refused
with no token present.

So the 36 tests in that file all passed while the invariant they exist to
protect was broken through the only adapter that ever talks to a real account.
That is the failure mode this file covers: not a missing check, but a correct
check fed by a lossy reader.

Every test here drives ``RealMT5.order_send`` and asserts on **whether the
broker was reached**. The three that matter most:

* ``test_a_close_survives_a_positions_get_that_returns_none`` — the hole.
* ``test_a_new_entry_is_still_refused_when_the_position_read_fails`` — the
  other side. A repair that let *everything* through under a failed read would
  pass the first test and destroy the mechanism.
* ``test_an_unmarked_provider_returning_empty_is_treated_as_unverified`` — the
  invariant is structural, not a convention. A future provider that forgets to
  raise still fails toward letting the position be closed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mt5.mt5_interface import MAGIC_NUMBER, TRADE_ACTION_DEAL, TRADE_ACTION_SLTP
from src.mt5.mt5_real import RealMT5
from src.safety import activation_token as at

TICKET = 555
CLOSE_LONG = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1,
              "volume": 0.10, "position": TICKET}
TIGHTEN_STOP = {"action": TRADE_ACTION_SLTP, "symbol": "XAUUSD",
                "position": TICKET, "sl": 1940.0}
NEW_ENTRY = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0,
             "volume": 0.10, "sl": 1900.0, "tp": 2000.0}


class _FakePosition:
    def __init__(self, ticket=TICKET, symbol="XAUUSD", type=0, volume=0.10,
                 sl=1900.0, magic=MAGIC_NUMBER):
        self.ticket = ticket
        self.symbol = symbol
        self.type = type
        self.volume = volume
        self.price_open = 1950.0
        self.sl = sl
        self.tp = 2000.0
        self.profit = 0.0
        self.magic = magic
        self.comment = ""
        self.time = 1_750_000_000


class _FakeResult:
    retcode = 10009
    order = 12345
    volume = 0.10
    price = 1950.0
    comment = "done"
    deal = 999
    request_id = 1
    retcode_external = None


class _FakeMT5Module:
    """A MetaTrader5 stand-in that fails the way the real one does.

    ``positions_mode``:
      ``"ok"``      -> returns the positions
      ``"none"``    -> returns ``None``, which is how the real module reports a
                       failed read. This is the case the pre-existing fakes
                       never modelled.
      ``"raise"``   -> raises, which the real module does not do
    """

    def __init__(self, positions=None, positions_mode="ok", login=310_000):
        self.sent: list[dict] = []
        self._positions = [_FakePosition()] if positions is None else positions
        self._mode = positions_mode
        self._login = login
        self.positions_get_calls: list[dict] = []

    def order_send(self, request):
        self.sent.append(dict(request))
        return _FakeResult()

    def positions_get(self, symbol=None):
        self.positions_get_calls.append({"symbol": symbol})
        if self._mode == "raise":
            raise RuntimeError("broker read failed")
        if self._mode == "none":
            return None
        return list(self._positions)

    def account_info(self):
        return type("_Acct", (), {"login": self._login})()


def _adapter(module: _FakeMT5Module) -> RealMT5:
    adapter = RealMT5.__new__(RealMT5)          # no terminal, no connect
    adapter._mt5 = module
    adapter._connected = True
    adapter._broker_offset_detected = True
    adapter._broker_offset_seconds = 0
    adapter.set_activation_context()
    return adapter


@pytest.fixture()
def token_dir(tmp_path, monkeypatch):
    """An empty activation directory: no token exists for any account."""

    directory = tmp_path / "activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(directory))
    return directory


# --------------------------------------------------------------------------
# The hole: a live position that cannot be closed
# --------------------------------------------------------------------------


def test_a_close_survives_a_positions_get_that_returns_none(token_dir):
    """THE test. A transient broker read failure must not refuse a flatten.

    Against the pre-fix code this fails with `activation_token_absent`: the
    masked `[]` made the close look like a deal against a position that no
    longer exists.
    """

    module = _FakeMT5Module(positions_mode="none")

    _adapter(module).order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1, (
        "a close was refused because the broker position read failed — the "
        "activation token has become able to strand real money in a position"
    )


def test_a_stop_tighten_survives_a_positions_get_that_returns_none(token_dir):
    """Tightening a stop is risk-reducing and must survive the same failure."""

    module = _FakeMT5Module(positions_mode="none")

    _adapter(module).order_send(dict(TIGHTEN_STOP))

    assert len(module.sent) == 1


def test_a_close_survives_a_position_carrying_a_foreign_magic(token_dir):
    """`get_positions` magic-filters, so a position adopted from an earlier
    deployment — or opened by hand — was invisible to the gate and could not be
    closed. The gate asks "does this ticket exist", not "does this book own
    it"."""

    module = _FakeMT5Module(
        positions=[_FakePosition(magic=MAGIC_NUMBER + 1)], positions_mode="ok",
    )

    _adapter(module).order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1


def test_the_gate_reads_the_whole_account_not_one_symbol(token_dir):
    """The provider used to be called with the request's symbol, so a
    magic-filtered or symbol-scoped view could hide a position from a close."""

    module = _FakeMT5Module(positions=[_FakePosition()])

    _adapter(module).order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1
    assert module.positions_get_calls == [{"symbol": None}], (
        "the activation gate must read the whole account, not one symbol"
    )


def test_a_deal_on_one_symbol_quoting_another_symbols_ticket_is_not_a_close(token_dir):
    """The cost of reading the whole account, and the reason the classifier has
    to check the symbol itself.

    `_matching_position` keys on ticket alone. Once the provider stopped
    filtering by symbol, a DEAL that OPENS a EURUSD short while quoting an open
    XAUUSD long's ticket matched that position, passed the five conditions, and
    was allowed with no token — a token-free new position. The symbol-scoped
    read had been hiding it.

    This test is the reason the whole-account read is safe. If it ever goes
    green-by-deletion, the read must go back to being symbol-scoped.
    """

    module = _FakeMT5Module(positions=[_FakePosition(symbol="XAUUSD", type=0, volume=1.00)])
    opens_a_eurusd_short = {"action": TRADE_ACTION_DEAL, "symbol": "EURUSD",
                            "type": 1, "volume": 1.00, "position": TICKET}

    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(opens_a_eurusd_short)

    assert module.sent == [], "a DEAL on a different symbol was certified as a close"


def test_a_close_whose_position_carries_no_symbol_is_still_a_close(token_dir):
    """The symbol condition applies only when both sides declare one. A position
    record that does not expose `symbol` must not become uncloseable."""

    class _NoSymbol:
        ticket, type, volume, sl, tp, magic = TICKET, 0, 0.10, 1900.0, 2000.0, MAGIC_NUMBER
        price_open, profit, comment, time = 1950.0, 0.0, "", 1_750_000_000

    module = _FakeMT5Module(positions=[_NoSymbol()])

    _adapter(module).order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1


def test_the_designed_failsafe_branch_is_reachable_through_the_real_adapter(token_dir):
    """`risk_reducing_position_close_unverified` existed but was dead code
    through `RealMT5`, because the branch fires only when the provider raises
    and the real adapter never raised."""

    module = _FakeMT5Module(positions_mode="none")
    adapter = _adapter(module)

    decision = at.authorize_broker_mutation(
        dict(CLOSE_LONG),
        account_login_sha256=adapter.account_login_sha256(),
        positions_provider=adapter.positions_for_activation,
        audit=False,
    )

    assert decision.allowed
    assert decision.reason == "risk_reducing_position_close_unverified"
    assert decision.positions_verified is False


# --------------------------------------------------------------------------
# The other side: the repair must not open the gate
# --------------------------------------------------------------------------


def test_a_new_entry_is_still_refused_when_the_position_read_fails(token_dir):
    """A repair that let everything through under a failed read would pass every
    test above and destroy the mechanism. A new entry carries no position
    ticket, so it never consults the broker and is never exempt."""

    module = _FakeMT5Module(positions_mode="none")

    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(NEW_ENTRY))

    assert module.sent == []


def test_a_same_direction_deal_is_still_refused_when_the_position_is_visible(token_dir):
    """Adding to a position is not a close, and a verified read still says so."""

    module = _FakeMT5Module(positions=[_FakePosition(type=0, volume=0.10)])

    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(CLOSE_LONG, type=0))

    assert module.sent == []


def test_an_oversized_close_is_still_refused_when_the_position_is_visible(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(type=0, volume=0.10)])

    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(CLOSE_LONG, volume=0.50))

    assert module.sent == []


def test_a_widened_stop_is_still_refused_when_the_position_is_visible(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(type=0, sl=1900.0)])

    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(TIGHTEN_STOP, sl=1850.0))

    assert module.sent == []


# --------------------------------------------------------------------------
# The invariant is structural, not a convention
# --------------------------------------------------------------------------


def test_the_activation_provider_raises_rather_than_masking_a_failed_read():
    """The adapter-level contract, asserted directly."""

    adapter = _adapter(_FakeMT5Module(positions_mode="none"))

    with pytest.raises(at.PositionsUnavailable):
        adapter.positions_for_activation("XAUUSD")


def test_get_positions_still_masks_and_is_therefore_not_the_gates_reader():
    """`get_positions` keeps its documented `[]`-on-failure behaviour for its
    own callers. This test pins *why* a second reader exists: if someone later
    "simplifies" the gate back onto `get_positions`, the strand returns."""

    adapter = _adapter(_FakeMT5Module(positions_mode="none"))

    assert adapter.get_positions("XAUUSD") == []
    assert not getattr(adapter.get_positions, "gtos_strict_positions_provider", False)
    assert getattr(adapter.positions_for_activation, "gtos_strict_positions_provider", False)


def test_an_unmarked_provider_returning_empty_is_treated_as_unverified():
    """The backstop. A provider that has not promised to raise on a failed read
    cannot be trusted to mean "no positions" when it returns none — so a close
    is still allowed. This is what makes the invariant survive a future edit to
    the adapter."""

    direction, reason, verified = at.classify_request(dict(CLOSE_LONG), lambda symbol: [])

    assert direction == "reducing"
    assert reason == "risk_reducing_position_close_unverified"
    assert verified is False


def test_a_marked_provider_returning_empty_is_evidence_of_absence():
    """And the other half — otherwise the backstop would be a blanket allow.
    A provider that *can* report unavailability and returns empty anyway is
    telling the truth: the position is not there, so this is not a close."""

    @at.strict_positions_provider
    def provider(symbol):
        return []

    direction, reason, verified = at.classify_request(dict(CLOSE_LONG), provider)

    assert direction == "increasing"
    assert reason == "exposure_increasing_deal_on_position"
    assert verified is True


def test_the_raw_module_guard_does_not_mask_a_failed_position_read(token_dir, monkeypatch):
    """`authorize_raw_broker_request` had the identical bug in its own inline
    provider (`positions_get(symbol=symbol) or ()`). It covers
    `fn_smoke_trade.py` and `dual_broker_execution_follower.py`, so the same
    strand was reachable from the scripts that drive the raw module."""

    # `authorize_raw_broker_request` imports the halt guard lazily from
    # `runtime_halt`, so the patch has to land on that module, not on this one.
    # The halt is a separate mechanism with its own tests; this test is about
    # the token's position read. (This worktree carries live halt flags in
    # `pipeline_state/`, so an unpatched call would raise RuntimeHaltError.)
    from src.safety import runtime_halt

    monkeypatch.setattr(
        runtime_halt, "enforce_runtime_not_halted", lambda **kwargs: None,
    )
    module = _FakeMT5Module(positions_mode="none")

    decision = at.authorize_raw_broker_request(
        dict(CLOSE_LONG), mt5_module=module, config={},
    )

    assert decision.allowed
    assert decision.reason == "risk_reducing_position_close_unverified"


# --------------------------------------------------------------------------
# Diagnosability — an operator at 2 a.m. must see the real cause
# --------------------------------------------------------------------------


def test_a_refusal_records_the_classification_that_caused_it(token_dir):
    """On a denial the surfaced reason is the *token* status, which sends an
    operator to the token directory. The classification that got the request
    there — and whether it rested on a real broker read — must be in the audit
    row too, or the actual cause is unrecoverable after the fact."""

    module = _FakeMT5Module(positions=[_FakePosition(type=0, volume=0.10)])

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(CLOSE_LONG, type=0))

    decision = excinfo.value.decision
    assert decision.reason == "activation_token_absent"
    assert decision.classification == "exposure_increasing_deal_on_position"
    assert decision.positions_verified is True
    assert "exposure_increasing_deal_on_position" in str(excinfo.value)

    rows = [
        json.loads(line)
        for line in Path(at.audit_log_path()).read_text(encoding="utf-8").splitlines()
    ]
    assert rows[-1]["classification"] == "exposure_increasing_deal_on_position"
    assert rows[-1]["positions_verified"] is True
