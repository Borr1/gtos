"""`_account_label` must never render an F5 ($10 experiment) card as an armed-book card.

The defect this pins, measured on the live VPS 2026-08-12: the minimal-size experiment runs
under namespace `operator`, `"operator".startswith("ftmo")` is True, so every
operator card it emitted read `[FTMO]` — identical to a real-money fill, in the same Telegram
chat, with risk quoted as a percent of a notional $100,000 ledger so the numbers matched too.

Behavioural, not source-string: each case builds an object with the real method bound to it
and asserts on the string a Telegram card would actually carry.
"""
from __future__ import annotations

import pytest

from types import SimpleNamespace

from src.components.ultimate_book.book_owner import UltimateBookOwner


class _Stub:
    """Minimal stand-in carrying only what `_account_label` reads."""

    _account_label = UltimateBookOwner._account_label

    def __init__(self, namespace, f5_ledger=None):
        self._namespace = namespace
        self._f5_ledger = f5_ledger
        # Real construction invariant (book_owner.py:299): the ledger exists iff the
        # MinimalSizeConfig is enabled — the label renders the rung from that config
        # since 2026-08-25 (the $75 literal lied at every ladder step).
        self._f5_cfg = (SimpleNamespace(target_risk_usd=250.0)
                        if f5_ledger is not None else None)


@pytest.fixture(autouse=True)
def _no_env_override(monkeypatch):
    monkeypatch.delenv("GTOS_ALERT_LABEL", raising=False)


# --- the armed book must be byte-identical to pre-fix behaviour ---------------------
@pytest.mark.parametrize("namespace,expected", [
    ("operator_profile", "FTMO"),
    ("ftmo_primary", "FTMO"),
    ("redacted_account_live_bee34003", "redacted_account"),
    ("redacted_account", "redacted_account"),
    ("something_else", "something_else"),
    ("", "book"),
])
def test_armed_labels_unchanged(namespace, expected):
    assert _Stub(namespace, f5_ledger=None)._account_label() == expected


# --- the F5 worker must be unmistakable ---------------------------------------------
def test_f5_namespace_alone_is_not_enough_to_be_safe():
    """The namespace prefix genuinely collides — this is why the ledger keys the branch."""
    assert "operator".startswith("ftmo")


def test_f5_worker_is_labelled_as_a_test():
    """ROOT-CAUSE REWRITE 2026-08-25 (stale expectation): the original pinned "$10",
    the 2026-08-12 unit. The F5 unit is an owner LADDER now — $75 under
    OWNER-GRANT-20260825 OD-J7 (docs/audits/fable-20260825/OWNER-GRANT-20260825.md),
    stepped again by charter commit eb30257fa — so the protection pinned here is the
    invariant, not the rung: the card must be unmistakable as an F5 TEST, never render
    as the armed book, and must still SHOW a dollar unit."""
    import re

    label = _Stub("operator", f5_ledger=object())._account_label()
    assert label != "FTMO"
    assert "F5" in label and "TEST" in label
    assert re.search(r"\$\d+", label), "the card must carry the fixed dollar unit"


def test_f5_label_survives_on_any_namespace():
    """A ledger is attached iff --f5-minimal-size-usd was passed, whatever the namespace."""
    for ns in ("operator", "redacted_account_f5", "anything"):
        assert "F5" in _Stub(ns, f5_ledger=object())._account_label()


def test_env_override_replaces_label_and_defaults_off(monkeypatch):
    monkeypatch.setenv("GTOS_ALERT_LABEL", "SANDBOX")
    assert _Stub("operator_profile")._account_label() == "SANDBOX"
    monkeypatch.setenv("GTOS_ALERT_LABEL", "   ")   # blank => no override
    assert _Stub("operator_profile")._account_label() == "FTMO"
