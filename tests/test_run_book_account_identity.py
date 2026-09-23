"""Account-identity startup gate for the live W7 book — guards run_book.py's wiring of
src.utils.broker_profile.assert_mt5_account_matches_profile (finding MACRO-A4).

Two protections:
 1) the two LIVE profiles actually carry a broker_profile.expected_account contract bound to the KNOWN
    live login, so the gate ENGAGES (a config regression dropping the contract would silently disable
    wrong-account protection and is exactly how a book ends up trading the wrong real-money account);
 2) the gate PASSES for the expected login and REFUSES (RuntimeError) on any login mismatch.
"""
import os

import pytest
import yaml

from src.utils.broker_profile import (
    assert_mt5_account_matches_profile,
    expected_account_contract,
    sha256_text,
)
from src.utils.config import apply_profile_overrides

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the two live books and their real (operational, non-secret) MT5 login numbers
LIVE = {"operator_profile": 531325516, "redacted_account": 0}


def _merged(profile):
    with open(os.path.join(REPO, "config", "agent_config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return apply_profile_overrides(cfg, profile)


class _Raw:
    def __init__(self, account, terminal):
        self._a, self._t = account, terminal

    def account_info(self):
        return self._a

    def terminal_info(self):
        return self._t


class _Wrapper:
    def __init__(self, raw):
        self._mt5 = raw


def _wrapper(contract, login):
    account = {"login": login, "server": contract.get("server"),
               "company": contract.get("company"), "currency": contract.get("currency")}
    terminal = {"path": contract.get("terminal_path"), "data_path": contract.get("terminal_data_path")}
    return _Wrapper(_Raw(account, terminal))


@pytest.mark.parametrize("profile,login", list(LIVE.items()))
def test_live_profile_carries_contract_bound_to_known_login(profile, login):
    c = expected_account_contract(_merged(profile))
    assert c.get("login_sha256"), f"{profile} missing broker_profile.expected_account.login_sha256"
    # the committed hash must bind the KNOWN live login (else the gate would protect the wrong account)
    assert c["login_sha256"] == sha256_text(login)


@pytest.mark.parametrize("profile,login", list(LIVE.items()))
def test_gate_passes_on_matching_account(profile, login):
    merged = _merged(profile)
    res = assert_mt5_account_matches_profile(_wrapper(expected_account_contract(merged), login), merged)
    assert res["checked"] is True and res["status"] == "passed"
    assert "login_sha256" in res["fields_checked"]


@pytest.mark.parametrize("profile,login", list(LIVE.items()))
def test_gate_refuses_on_wrong_login(profile, login):
    merged = _merged(profile)
    with pytest.raises(RuntimeError):
        assert_mt5_account_matches_profile(_wrapper(expected_account_contract(merged), login + 1), merged)


def test_gate_refuses_on_wrong_server():
    merged = _merged("operator_profile")
    c = dict(expected_account_contract(merged))
    w = _wrapper(c, LIVE["operator_profile"])
    w._mt5._a["server"] = "SomeOther-Server"
    with pytest.raises(RuntimeError):
        assert_mt5_account_matches_profile(w, merged)


def test_no_contract_is_not_configured_not_a_refusal():
    # a profile WITHOUT a contract returns checked=False (default-off), it does not raise
    res = assert_mt5_account_matches_profile(_Wrapper(_Raw({}, {})), {})
    assert res["checked"] is False and res["status"] == "not_configured"
