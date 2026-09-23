"""The three broker-capable scripts that do not go through `RealMT5.order_send`.

`fn_smoke_trade.py` drives the raw `MetaTrader5` module (F19) and
`dual_broker_execution_follower.py` **re-transmits historical intents to a live
broker account** with no halt check of its own (H6). Neither can be imported
here — the first hits `import MetaTrader5` at module scope, and both are on the
never-execute list — so the wiring tests below are **AST structural** rather than
string greps: they assert that the guard call dominates the mutation inside the
same function, which is the property that matters and which a substring search
cannot establish.

The composed guard itself is tested behaviourally, with no broker.
"""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.mt5.mt5_interface import TRADE_ACTION_DEAL
from src.safety import activation_token as at
from src.safety.runtime_halt import RuntimeHaltError

REPO_ROOT = Path(__file__).resolve().parents[2]


def _functions_containing(tree: ast.AST, attr_chain: str) -> list[ast.FunctionDef]:
    """Every function whose body calls e.g. `mt5.order_send(...)`."""

    owner, name = attr_chain.split(".")
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == name
                and isinstance(inner.func.value, ast.Name)
                and inner.func.value.id == owner
            ):
                found.append(node)
                break
    return found


def _first_lineno_of_call(node: ast.AST, func_name: str) -> int | None:
    best = None
    for inner in ast.walk(node):
        if isinstance(inner, ast.Call):
            target = inner.func
            named = getattr(target, "id", None) or getattr(target, "attr", None)
            if named == func_name:
                best = inner.lineno if best is None else min(best, inner.lineno)
    return best


def _tree(rel: str) -> ast.AST:
    return ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8-sig"))


# --------------------------------------------------------------------------
# fn_smoke_trade.py — gated, not deleted
# --------------------------------------------------------------------------


def test_fn_smoke_trade_authorizes_before_it_opens_a_position():
    tree = _tree("scripts/fn_smoke_trade.py")
    entry_functions = [
        fn for fn in _functions_containing(tree, "mt5.order_send")
        if _first_lineno_of_call(fn, "authorize_raw_broker_request") is not None
    ]
    assert entry_functions, (
        "no function in fn_smoke_trade.py calls authorize_raw_broker_request before "
        "mt5.order_send — the script drives the raw MetaTrader5 module and would bypass "
        "both the halt and the activation token"
    )
    for fn in entry_functions:
        guard = _first_lineno_of_call(fn, "authorize_raw_broker_request")
        send = min(
            inner.lineno
            for inner in ast.walk(fn)
            if isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr == "order_send"
        )
        assert guard < send, f"{fn.name}: the guard runs after the order, not before"


def test_fn_smoke_trade_still_exists_with_its_tests():
    """F19 said "delete or gate it". Gated: it carries genuine behavioural tests
    and a live smoke trade is a real canary-day need, so fencing it off would
    have thrown away working coverage to avoid writing six lines."""

    assert (REPO_ROOT / "scripts/fn_smoke_trade.py").is_file()
    assert list(REPO_ROOT.glob("tests/**/test_fn_smoke_trade*.py")), (
        "fn_smoke_trade's tests vanished; if the script is being retired it goes "
        "as a reviewed tests+code pair (F23), not tests first"
    )


# --------------------------------------------------------------------------
# dual_broker_execution_follower.py — the re-transmission path
# --------------------------------------------------------------------------


def test_the_follower_checks_the_halt_before_opening_a_trade():
    tree = _tree("scripts/dual_broker_execution_follower.py")
    openers = [
        fn for fn in ast.walk(tree)
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _first_lineno_of_call(fn, "open_trade") is not None
    ]
    guarded = [fn for fn in openers if _first_lineno_of_call(fn, "enforce_runtime_not_halted")]
    assert guarded, (
        "dual_broker_execution_follower.py opens trades with no halt check of its own. "
        "engine.open_trade has one, but it is config-armed and both of its defaults are "
        "False (runtime_halt.py:91 and :247)."
    )
    for fn in guarded:
        assert _first_lineno_of_call(fn, "enforce_runtime_not_halted") < _first_lineno_of_call(
            fn, "open_trade"
        ), f"{fn.name}: the halt check runs after the order"


def test_the_follower_arms_the_halt_guard_rather_than_trusting_config():
    """`enabled_default=True` is the whole point — a follower launched with a
    config that never mentions `runtime_control` must still be braked."""

    source = (REPO_ROOT / "scripts/dual_broker_execution_follower.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "enforce_runtime_not_halted"
        ):
            defaults = [kw for kw in node.keywords if kw.arg == "enabled_default"]
            assert defaults, "the follower's halt check is config-armed and may never fire"
            assert getattr(defaults[0].value, "value", None) is True
            return
    pytest.fail("no enforce_runtime_not_halted call found")


def test_the_follower_no_longer_reads_a_failed_history_fetch_as_no_deals():
    """C6. `or []` collapsed "the broker fetch failed" into "there were no deals
    today", which reset the reconstructed day-start balance to the CURRENT
    already-drawn-down balance and re-opened the whole daily-loss budget."""

    source = (REPO_ROOT / "scripts/dual_broker_execution_follower.py").read_text(encoding="utf-8-sig")
    assert "get_history_deals(reset_start_utc, now_utc, broker_symbol) or []" not in source
    assert "history_deals_unreadable" in source


# --------------------------------------------------------------------------
# The composed guard, behaviourally
# --------------------------------------------------------------------------


class _RawModule:
    def __init__(self, login=310_000, positions=()):
        self.sent = []
        self._login = login
        self._positions = positions

    def account_info(self):
        return type("A", (), {"login": self._login})()

    def positions_get(self, symbol=None):
        return list(self._positions)


@pytest.fixture()
def token_dir(tmp_path, monkeypatch):
    directory = tmp_path / "activation"
    monkeypatch.setenv(at.TOKEN_DIR_ENV_VAR, str(directory))
    return directory


@pytest.fixture()
def unhalted(tmp_path):
    """A config whose halt root is an empty directory.

    `enforce_runtime_not_halted` resolves its flag paths against `Path.cwd()`
    when no `repo_root` is configured. These two tests are about the TOKEN, not
    the halt, and they passed no config — so on any checkout that actually
    carries the halt flags (this worktree does; `pipeline_state/` was restored
    from the sparse profile) the guard fired first, tried to append its audit row
    into `pipeline_state/`, and hit conftest's production-write guard. Both
    tests errored on infrastructure rather than on their assertion, which meant
    the raw-broker guard had no live coverage at all on a halted machine.
    """

    return {"runtime_control": {"repo_root": str(tmp_path / "clean_root")}}


def test_the_raw_guard_refuses_a_new_entry_without_a_token(token_dir, unhalted):
    with pytest.raises(at.ActivationTokenError):
        at.authorize_raw_broker_request(
            {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0, "volume": 0.1},
            mt5_module=_RawModule(),
            config=unhalted,
        )


def test_the_raw_guard_allows_a_close_without_a_token(token_dir, unhalted):
    position = type("P", (), {"ticket": 7, "symbol": "XAUUSD", "type": 0,
                              "volume": 0.1, "sl": 1.0})()
    decision = at.authorize_raw_broker_request(
        {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 1, "volume": 0.1, "position": 7},
        mt5_module=_RawModule(positions=(position,)),
        config=unhalted,
    )
    assert decision.allowed and decision.risk_direction == "reducing"


def test_the_raw_guard_blocks_everything_when_the_halt_is_active(token_dir, tmp_path):
    """The halt and the token deliberately differ: the halt is an intentional act
    by an operator who is present, so it blocks risk-reducing requests too --
    the same reading the owner decided for the book's broker-authority gate."""

    flag = tmp_path / "pipeline_state" / "GTOS_HARD_PRODUCTION_HALT.flag"
    flag.parent.mkdir(parents=True)
    flag.write_text("halted")
    config = {"runtime_control": {"enabled": True, "repo_root": str(tmp_path)}}

    at.write_token(
        at.build_token(
            account_login_sha256=at.account_digest(310_000),
            expires_utc=datetime.now(timezone.utc) + timedelta(hours=1),
        ),
        directory=token_dir,
    )
    with pytest.raises(RuntimeHaltError):
        at.authorize_raw_broker_request(
            {"action": TRADE_ACTION_DEAL, "symbol": "XAUUSD", "type": 0, "volume": 0.1},
            mt5_module=_RawModule(),
            config=config,
        )
