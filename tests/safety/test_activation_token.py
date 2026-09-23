"""The activation token: presence-of-authorization at the broker choke point.

These tests are behavioural. They drive `RealMT5.order_send` against a fake MT5
module and assert on **whether the broker was reached**, not on log strings or
source text. The one exception is `test_the_mutating_surface_has_not_widened`,
which is deliberately a source census because the invariant it protects — "no
new place in `src/` mutates the broker outside the adapter" — is a statement
about the shape of the codebase and cannot be observed any other way.

The load-bearing test in this file is
`test_an_expired_token_still_lets_the_account_be_flattened`. If that ever fails,
this mechanism has become able to trap real money in an open position, which is
the one thing it must never do.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.mt5.mt5_interface import (
    MAGIC_NUMBER,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_MODIFY,
    TRADE_ACTION_PENDING,
    TRADE_ACTION_REMOVE,
    TRADE_ACTION_SLTP,
)
from src.mt5.mt5_real import RealMT5
from src.safety import activation_token as at

REPO_ROOT = Path(__file__).resolve().parents[2]
# ROOT-CAUSE UPDATE 2026-08-25: the FTMO account SWITCHED on 2026-08-21 (retired account
# -> Verification 0). The profile FILE NAME keeps its historical prefix (310fcf06
# was the OLD login sha; the file is R2-seal-bound, H1 — renaming would break the seal),
# but the binding that matters is expected_account.login_sha256, which moved with the
# account. This constant is the LIVE account's sha; the old value lives in git history.
FTMO_LOGIN_SHA = "0000000000000000000000000000000000000000000000000000000000000000"


# --------------------------------------------------------------------------
# Fakes — no MetaTrader5, no network, no broker.
# --------------------------------------------------------------------------


class _FakePosition:
    def __init__(self, ticket=555, symbol="XAUUSD", type=0, volume=0.10, sl=1900.0):
        self.ticket = ticket
        self.symbol = symbol
        self.type = type
        self.volume = volume
        self.price_open = 1950.0
        self.sl = sl
        self.tp = 2000.0
        self.profit = 0.0
        self.magic = MAGIC_NUMBER
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


class _FakeAccount:
    def __init__(self, login=310_000):
        self.login = login


class _FakeMT5Module:
    """Records every order_send it is asked to perform."""

    def __init__(self, positions=None, login=310_000, positions_raise=False):
        self.sent: list[dict] = []
        self._positions = positions if positions is not None else [_FakePosition()]
        self._login = login
        self._positions_raise = positions_raise

    def order_send(self, request):
        self.sent.append(dict(request))
        return _FakeResult()

    def positions_get(self, symbol=None):
        if self._positions_raise:
            raise RuntimeError("broker read failed")
        return list(self._positions)

    def account_info(self):
        return _FakeAccount(self._login)


def _adapter(
    module: _FakeMT5Module,
    *,
    namespace=None,
    config_digest=None,
    require_namespace_binding=False,
    require_config_digest_binding=False,
) -> RealMT5:
    adapter = RealMT5.__new__(RealMT5)          # bypass __init__: no terminal, no connect
    adapter._mt5 = module
    adapter._connected = True
    adapter._broker_offset_detected = True      # skip the lazy get_tick warm-up
    adapter._broker_offset_seconds = 0
    adapter.set_activation_context(
        namespace=namespace,
        config_digest_sha256=config_digest,
        require_namespace_binding=require_namespace_binding,
        require_config_digest_binding=require_config_digest_binding,
    )
    return adapter


@pytest.fixture()
def token_dir(tmp_path, monkeypatch):
    """A per-test activation directory. Never `pipeline_state/` — see F30."""

    directory = tmp_path / "activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(directory))
    return directory


def _mint(directory: Path, *, hours=4.0, namespace=None, config_digest=None,
          account=FTMO_LOGIN_SHA, now=None) -> Path:
    now = now or datetime.now(timezone.utc)
    token = at.build_token(
        account_login_sha256=account,
        expires_utc=now + timedelta(hours=hours),
        namespace=namespace,
        config_digest_sha256=config_digest,
        issued_by="test",
        now=now,
    )
    return at.write_token(token, directory=directory)


# The digest of the fake account login the adapter reports.
LIVE_ACCOUNT_SHA = at.account_digest(310_000)

BUY_ENTRY = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0, "volume": 0.10,
             "sl": 1900.0, "tp": 2000.0}
CLOSE_LONG = {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1, "volume": 0.10,
              "position": 555}


# --------------------------------------------------------------------------
# Fail-closed by construction
# --------------------------------------------------------------------------


def test_no_token_refuses_a_new_entry_and_never_reaches_the_broker(token_dir):
    module = _FakeMT5Module()
    adapter = _adapter(module)

    with pytest.raises(at.ActivationTokenError) as excinfo:
        adapter.order_send(dict(BUY_ENTRY))

    assert module.sent == [], "the broker was reached despite no activation token"
    assert excinfo.value.decision.reason == "activation_token_absent"
    assert excinfo.value.decision.risk_direction == "increasing"


def test_a_fresh_clone_is_the_safe_state(tmp_path, monkeypatch):
    """No token directory at all — the state of any machine that just cloned."""

    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(tmp_path / "never-created"))
    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(BUY_ENTRY))
    assert module.sent == []


def test_a_valid_token_lets_a_new_entry_through(token_dir):
    _mint(token_dir, account=LIVE_ACCOUNT_SHA)
    module = _FakeMT5Module()
    adapter = _adapter(module)

    result = adapter.order_send(dict(BUY_ENTRY))

    assert result.retcode == 10009
    assert len(module.sent) == 1


def test_an_expired_token_refuses_new_exposure(token_dir):
    past = datetime.now(timezone.utc) - timedelta(hours=8)
    _mint(token_dir, hours=4.0, account=LIVE_ACCOUNT_SHA, now=past)
    module = _FakeMT5Module()

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(BUY_ENTRY))

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_expired"


def test_a_token_for_another_account_is_refused(token_dir):
    _mint(token_dir, account=FTMO_LOGIN_SHA)          # not the connected account
    module = _FakeMT5Module()

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(BUY_ENTRY))

    assert module.sent == []
    # The token filename is keyed by account digest, so a token minted for a
    # different account is not even found for this one.
    assert excinfo.value.decision.reason == "activation_token_absent"


def test_a_hand_edited_token_is_refused(token_dir):
    path = _mint(token_dir, hours=1.0, account=LIVE_ACCOUNT_SHA)
    token = json.loads(path.read_text())
    token["expires_utc"] = (datetime.now(timezone.utc) + timedelta(days=3650)).isoformat()
    path.write_text(json.dumps(token))

    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(BUY_ENTRY))

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_signature_invalid"


@pytest.mark.parametrize("field", list(at._SIGNED_FIELDS))
def test_every_signed_field_is_actually_covered_by_the_signature(token_dir, field):
    """A field listed as signed but omitted from the payload would be editable
    without detection. This proves each one moves the signature."""

    token = at.build_token(
        account_login_sha256=LIVE_ACCOUNT_SHA,
        expires_utc=datetime.now(timezone.utc) + timedelta(hours=2),
        namespace="ns", config_digest_sha256="deadbeef", issued_by="a", note="b",
    )
    key = at.ensure_signing_key(token_dir)
    original = at.sign_token(token, key)

    mutated = dict(token)
    mutated[field] = "MUTATED"
    assert at.sign_token(mutated, key) != original, f"{field} is not covered by the signature"


def test_a_missing_signing_key_refuses_rather_than_passes(token_dir):
    _mint(token_dir, account=LIVE_ACCOUNT_SHA)
    at.signing_key_path(token_dir).unlink()

    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(BUY_ENTRY))

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_signing_key_absent"


def test_an_unknown_action_is_refused(token_dir):
    """Fail closed on anything the classifier does not recognise."""

    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send({"action": 4242, "symbol": "XAUUSD"})

    assert module.sent == []
    assert excinfo.value.decision.risk_direction == "unknown"


# --------------------------------------------------------------------------
# The non-negotiable: the token can never trap the account
# --------------------------------------------------------------------------


def test_an_expired_token_still_lets_the_account_be_flattened(token_dir):
    """THE load-bearing test. If this fails, an expired token can strand real
    money in an open position."""

    past = datetime.now(timezone.utc) - timedelta(days=2)
    _mint(token_dir, hours=1.0, account=LIVE_ACCOUNT_SHA, now=past)
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])
    adapter = _adapter(module)

    result = adapter.order_send(dict(CLOSE_LONG))

    assert result.retcode == 10009
    assert len(module.sent) == 1, "a flatten was blocked by an expired activation token"


def test_no_token_at_all_still_lets_the_account_be_flattened(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])
    adapter = _adapter(module)

    adapter.order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1


def test_a_partial_close_is_risk_reducing(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=1.00)])
    request = dict(CLOSE_LONG, volume=0.25)

    _adapter(module).order_send(request)

    assert len(module.sent) == 1


def test_cancelling_a_pending_order_needs_no_token(token_dir):
    module = _FakeMT5Module()
    _adapter(module).order_send({"action": TRADE_ACTION_REMOVE, "order": 9001})
    assert len(module.sent) == 1


def test_tightening_a_stop_needs_no_token(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, sl=1900.0)])
    _adapter(module).order_send(
        {"action": TRADE_ACTION_SLTP, "symbol": "XAUUSD", "position": 555, "sl": 1940.0}
    )
    assert len(module.sent) == 1


def test_widening_a_stop_needs_a_token(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, sl=1900.0)])
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(
            {"action": TRADE_ACTION_SLTP, "symbol": "XAUUSD", "position": 555, "sl": 1850.0}
        )
    assert module.sent == []


def test_removing_a_stop_entirely_needs_a_token(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, sl=1900.0)])
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(
            {"action": TRADE_ACTION_SLTP, "symbol": "XAUUSD", "position": 555, "sl": 0.0}
        )
    assert module.sent == []


def test_a_close_still_passes_when_the_position_read_fails(token_dir):
    """Deliberate asymmetry: if the broker cannot be read, a DEAL naming an
    existing ticket is treated as reducing. Refusing it would let a broker
    outage block a flatten."""

    module = _FakeMT5Module(positions_raise=True)
    _adapter(module).order_send(dict(CLOSE_LONG))
    assert len(module.sent) == 1


def test_a_same_direction_deal_on_a_position_is_not_a_close(token_dir):
    """Opposing type is one of the five conditions; without it this is an add."""

    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(CLOSE_LONG, type=0))
    assert module.sent == []


def test_closing_more_than_the_position_holds_is_not_a_close(token_dir):
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(CLOSE_LONG, volume=0.50))
    assert module.sent == []


def test_a_pending_placement_needs_a_token(token_dir):
    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send({"action": TRADE_ACTION_PENDING, "symbol": "XAUUSD",
                                     "type": 2, "volume": 0.1, "price": 1940.0})
    assert module.sent == []


def test_modifying_a_working_order_needs_a_token(token_dir):
    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send({"action": TRADE_ACTION_MODIFY, "order": 9001, "price": 1930.0})
    assert module.sent == []


# --------------------------------------------------------------------------
# Bindings
# --------------------------------------------------------------------------


def test_a_namespace_bound_token_refuses_a_process_that_cannot_name_its_namespace(token_dir):
    """A binding the process cannot answer is a denial, not a pass."""

    _mint(token_dir, account=LIVE_ACCOUNT_SHA, namespace="operator_profile")
    module = _FakeMT5Module()

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module).order_send(dict(BUY_ENTRY))     # no namespace declared

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_namespace_unsatisfied"


def test_a_namespace_bound_token_refuses_the_wrong_namespace(token_dir):
    _mint(token_dir, account=LIVE_ACCOUNT_SHA, namespace="operator_profile")
    module = _FakeMT5Module()

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module, namespace="redacted_account_live_bee34003").order_send(dict(BUY_ENTRY))

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_namespace_mismatch"


def test_a_namespace_bound_token_accepts_its_own_namespace(token_dir):
    _mint(token_dir, account=LIVE_ACCOUNT_SHA, namespace="operator_profile")
    module = _FakeMT5Module()

    _adapter(module, namespace="operator_profile").order_send(dict(BUY_ENTRY))

    assert len(module.sent) == 1


def test_editing_the_config_revokes_a_config_bound_token(token_dir):
    _mint(token_dir, account=LIVE_ACCOUNT_SHA, config_digest="digest-at-mint-time")
    module = _FakeMT5Module()

    with pytest.raises(at.ActivationTokenError) as excinfo:
        _adapter(module, config_digest="digest-after-an-edit").order_send(dict(BUY_ENTRY))

    assert module.sent == []
    assert excinfo.value.decision.reason == "activation_token_config_digest_mismatch"


def test_real_adapter_enforces_required_f5_bindings_but_still_allows_a_close(token_dir):
    """The required-binding flags must reach the actual order-send choke point."""

    _mint(token_dir, account=LIVE_ACCOUNT_SHA)  # deliberately namespace/config-unbound
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])
    adapter = _adapter(
        module,
        namespace="operator",
        config_digest="f5-composite-digest",
        require_namespace_binding=True,
        require_config_digest_binding=True,
    )

    with pytest.raises(at.ActivationTokenError) as excinfo:
        adapter.order_send(dict(BUY_ENTRY))
    assert excinfo.value.decision.reason == "activation_token_namespace_binding_required"
    assert module.sent == []

    adapter.order_send(dict(CLOSE_LONG))
    assert len(module.sent) == 1, "F5 binding enforcement blocked a risk-reducing close"


def test_the_config_digest_tracks_the_real_config_bytes(tmp_path):
    config = tmp_path / "agent_config.yaml"
    config.write_text("risk: 2.0\n")
    profiles = tmp_path / "config" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "p.yaml").write_text("overlay: 1\n")

    before = at.config_digest_for(config, "p", repo_root=tmp_path)
    assert before is not None
    config.write_text("risk: 3.0\n")           # the owner's dial moved
    after = at.config_digest_for(config, "p", repo_root=tmp_path)

    assert before != after
    assert at.config_digest_for(tmp_path / "missing.yaml", "p", repo_root=tmp_path) is None


def test_the_account_digest_matches_the_profile_contract_convention():
    """The token binds the same digest the profile already asserts on, so the
    two identity checks cannot disagree about what account they mean."""

    import yaml
    profile = yaml.safe_load(
        (REPO_ROOT / "config" / "profiles" / "operator_profile.yaml").read_text(encoding="utf-8-sig")
    )
    contract = profile["broker_profile"]["expected_account"]["login_sha256"]
    assert contract == FTMO_LOGIN_SHA
    # Same function the identity assert uses, reached through the token module.
    from src.utils.broker_profile import sha256_text
    assert at.account_digest("x") == sha256_text("x")


# --------------------------------------------------------------------------
# Lifetime, location, audit
# --------------------------------------------------------------------------


def test_a_token_cannot_be_minted_to_outlive_the_cap():
    with pytest.raises(ValueError, match="exceeds"):
        at.build_token(
            account_login_sha256=LIVE_ACCOUNT_SHA,
            expires_utc=datetime.now(timezone.utc) + timedelta(hours=at.MAX_TOKEN_LIFETIME_HOURS + 1),
        )


def test_a_token_cannot_be_minted_already_expired():
    with pytest.raises(ValueError, match="future"):
        at.build_token(
            account_login_sha256=LIVE_ACCOUNT_SHA,
            expires_utc=datetime.now(timezone.utc) - timedelta(minutes=1),
        )


def test_tokens_do_not_live_in_the_repository(monkeypatch):
    """F30: the suite writes into `pipeline_state/` and conftest guards that
    tree, so a token there would be both fragile and one `git add -A` from
    being committed."""

    monkeypatch.delenv(at.TOKEN_DIR_ENV_VAR, raising=False)
    resolved = at.token_dir().resolve()
    assert not str(resolved).startswith(str(REPO_ROOT)), resolved
    assert "pipeline_state" not in str(resolved)


def test_every_decision_is_audited_outside_the_repository(token_dir):
    module = _FakeMT5Module()
    with pytest.raises(at.ActivationTokenError):
        _adapter(module).order_send(dict(BUY_ENTRY))

    rows = [json.loads(line) for line in
            at.audit_log_path(token_dir).read_text().splitlines() if line.strip()]
    assert rows and rows[-1]["allowed"] is False
    assert rows[-1]["reason"] == "activation_token_absent"
    assert rows[-1]["request_summary"]["symbol"] == "XAUUSD"
    assert not str(at.audit_log_path(token_dir)).startswith(str(REPO_ROOT / "pipeline_state"))


def test_an_unwritable_audit_directory_cannot_block_a_flatten(token_dir, monkeypatch):
    """The audit trail is best-effort by design: it must never become the
    reason a position cannot be closed."""

    monkeypatch.setattr(at, "audit_log_path", lambda *a, **k: Path("/proc/definitely/not/writable.jsonl"))
    module = _FakeMT5Module(positions=[_FakePosition(ticket=555, type=0, volume=0.10)])

    _adapter(module).order_send(dict(CLOSE_LONG))

    assert len(module.sent) == 1


# --------------------------------------------------------------------------
# The mutating surface
# --------------------------------------------------------------------------


# Every file in the repository that calls `order_send` on something and is NOT
# `RealMT5.order_send` (where the activation check lives). Each carries the
# reason it is allowed to. An entry here is a decision, not a rubber stamp.
#
# Scope note, because the previous version of this census got it wrong: it
# searched `src/` only. `scripts/`, `.tools/` and the repo root were outside its
# search path **by construction**, which is precisely where every ungated
# broker-mutating script lives — so the guardrail could not see the thing it
# existed to catch.
_DECLARED_MUTATION_SITES = {
    # -- the choke point and its immediate family --
    "src/mt5/mt5_real.py":
        "IS the adapter; the activation check lives here",
    "src/components/execution.py":
        "routes through self.mt5 -> the adapter",

    # -- raw-module callers deliberately NOT token-gated, each a flatten --
    # The never-strand rule cuts the other way for these: they are the code that
    # gets a real position OFF a real account. A guard that can refuse is a
    # guard that can strand.
    "src/safety/heartbeat_monitor.py":
        "raw module; halt-checked. Its only mutation is a flatten (risk-reducing by policy), "
        "and it runs unattended, so a token that lapsed overnight must not block it",
    "scripts/fn_smoke_trade.py":
        "entry is guarded via authorize_raw_broker_request; _force_close_position is a "
        "deliberate exemption (see its docstring) — the halt inside that guard would be "
        "able to strand a filled smoke trade",
    "scripts/flatten_all_positions.py":
        "owner emergency flatten. Every request is risk-reducing, so the token would pass "
        "them anyway; gating it would only add a way for the flatten to fail",
    "scripts/emergency_close_and_stop_redacted_account.py":
        "owner emergency close + pending-cancel. Same argument as flatten_all_positions.py",

    # -- not a mutating site at all; declared so the census stays exhaustive --
    "scripts/token_chaos_drills.py":
        "the chaos-drill harness. Its `.order_send(` call IS a call to "
        "`RealMT5.order_send` — the choke point — driven against a fake module that "
        "the harness constructs itself; it never imports MetaTrader5 and never calls "
        "connect(). Declared rather than glob-excluded, because excluding a path "
        "pattern would blind the census to anything else added under scripts/",

    # -- committed EVIDENCE under docs/, declared for the same reason --
    # A `-g '!docs/**'` would have been one line and is refused deliberately: docs/ holds
    # the activation-carry staging tree, i.e. bytes that are intended to reach the VPS, so
    # it is the last place that should become invisible to a mutation census.
    "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/files/execution.py":
        "the carry copy of src/components/execution.py, staged for the VPS. Same four "
        "`self.mt5.order_send(request)` sites as the declared original, routed through the "
        "adapter where the activation check lives; it is a frozen artifact of what was "
        "carried, not a second execution surface",
    "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority"
    "/swarm2/breakthrough/b8_paired_shadow/controls.py":
        "a control that asserts ShadowReadOnlyMT5Adapter REFUSES a mutation: it calls "
        "`ad.order_send({'action': 1})` against a `_Fake()` module the file constructs "
        "itself and passes only if that raises. Same argument as token_chaos_drills.py",
}


def test_the_mutating_surface_has_not_widened():
    """A census, not a behaviour test — and deliberately so.

    Anything that mutates broker state must either route through
    `RealMT5.order_send`, where the activation check lives, or appear in
    `_DECLARED_MUTATION_SITES` with the argument for why not.

    Two properties are asserted, and the second is the one that rots:
      1. no NEW mutating file appeared outside the declared set;
      2. every declared exemption still actually mutates. A stale exemption is
         how a real one hides — it makes the list look considered while nothing
         checks that its entries mean anything.

    `execution.py:6699` passes `order_send` as a bare attribute to
    `executor.submit`, so a census keyed on a Call node misses it entirely (C2)
    — which is why the check lives inside the callee rather than at call sites.
    """

    import subprocess

    # The whole repository, not `src/`. The excluded prefixes keep the vendored replay
    # and go-live packages out; those drive simulated brokers.
    #
    # This used to shell out to `rg`. `rg` is not an executable on every machine that runs
    # this suite -- on the research laptop it is a shell function, so `subprocess.run`
    # raised `FileNotFoundError` and THE CENSUS NEVER RAN. That is the worst failure mode
    # available to a safety check: it reads as one red line while asserting nothing at all.
    # `git ls-files` gives the same corpus (tracked, .gitignore-respecting) with no
    # external binary, and the two assertions below are unchanged.
    excluded = ("tests/", "research/", "src/research_infra/")
    tracked = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()

    hits: list[str] = []
    for relative in tracked:
        if relative.startswith(excluded):
            continue
        path = REPO_ROOT / relative
        if not path.is_file():  # tracked but not materialised in a sparse worktree
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1
        ):
            if ".order_send(" in line:
                hits.append(f"{relative}:{number}:{line.strip()}")

    assert hits, (
        "the census found no `.order_send(` anywhere -- it is scanning the wrong corpus, "
        "and an empty scan asserts nothing. Check the `git ls-files` call above."
    )

    seen, offenders = set(), []
    for line in hits:
        path = line.split(":", 1)[0].lstrip("./")
        if path in _DECLARED_MUTATION_SITES:
            seen.add(path)
            continue
        offenders.append(line)

    assert not offenders, (
        "a new broker-mutating site appeared outside the activation choke point:\n"
        + "\n".join(offenders)
        + "\nEither route it through RealMT5.order_send, or add it to "
          "_DECLARED_MUTATION_SITES with the argument for why it is exempt."
    )

    stale = sorted(set(_DECLARED_MUTATION_SITES) - seen)
    assert not stale, (
        f"these files are declared as broker-mutating but no longer call order_send: {stale}. "
        f"Remove them — a stale exemption makes the list look reviewed while it is not."
    )


def test_every_guarded_raw_script_guards_every_mutating_function():
    """The previous guard test could not see this class of hole at all.

    `test_raw_broker_script_guards.py` filters to functions that *already*
    contain `authorize_raw_broker_request` and then checks ordering within them
    — so a raw `order_send` in a sibling function is structurally invisible, and
    one was (`fn_smoke_trade._force_close_position`). This asserts the whole
    file instead: every function that mutates is either guarded or named here
    with its reason.
    """

    import ast

    exempt = {
        ("scripts/fn_smoke_trade.py", "_force_close_position"):
            "a flatten; the halt inside the guard could strand a filled smoke trade",
    }

    findings = []
    for relative in ("scripts/fn_smoke_trade.py",):
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.dump(node)
            if "attr='order_send'" not in body and 'attr="order_send"' not in body:
                continue
            if "authorize_raw_broker_request" in body:
                continue
            if (relative, node.name) in exempt:
                continue
            findings.append(f"{relative}::{node.name} mutates the broker with no guard")

    assert not findings, "\n".join(findings) + (
        "\nGuard it, or add it to `exempt` above with the argument for why not."
    )


def test_the_five_condition_classifier_has_one_definition():
    """`execution.py` and the activation gate must agree about what "reducing"
    means; two copies that drift apart is a live-risk defect."""

    import inspect
    from src.components import execution

    source = inspect.getsource(execution.ExecutionEngine._request_reduces_existing_position)
    assert "deal_reduces_existing_position" in source


@pytest.mark.parametrize(
    "request_dict,positions,expected",
    [
        ({"action": TRADE_ACTION_DEAL, "position": 555, "type": 1, "volume": 0.1},
         [_FakePosition(ticket=555, type=0, volume=0.1)], True),
        ({"action": TRADE_ACTION_DEAL, "position": 555, "type": 0, "volume": 0.1},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # same direction
        ({"action": TRADE_ACTION_DEAL, "position": 555, "type": 1, "volume": 0.2},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # oversized
        ({"action": TRADE_ACTION_DEAL, "position": 0, "type": 1, "volume": 0.1},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # no ticket
        ({"action": TRADE_ACTION_DEAL, "position": 555, "type": 1, "volume": 0.0},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # no volume
        ({"action": TRADE_ACTION_SLTP, "position": 555, "type": 1, "volume": 0.1},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # wrong action
        ({"action": TRADE_ACTION_DEAL, "position": 999, "type": 1, "volume": 0.1},
         [_FakePosition(ticket=555, type=0, volume=0.1)], False),        # unknown ticket
    ],
)
def test_all_five_conditions_are_enforced(request_dict, positions, expected):
    assert at.deal_reduces_existing_position(request_dict, positions) is expected


def test_a_structurally_impossible_close_costs_no_broker_round_trip():
    """The pre-check exists so a new entry (the common case) does not pay an
    extra `positions_get` on every order."""

    calls = []

    def provider(symbol):
        calls.append(symbol)
        return []

    at.classify_request(dict(BUY_ENTRY), provider)
    assert calls == []
