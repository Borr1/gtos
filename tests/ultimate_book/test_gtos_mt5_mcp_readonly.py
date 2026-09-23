"""Behavioural tests for the read-only MT5 MCP contract prototype.

The property under test is a NEGATIVE one and it is the whole point of the design: this server must
be structurally incapable of moving broker state, not merely configured not to. A prompt-injected
agent, a mis-set permission and a buggy caller all fail closed against a missing mechanism and none
of them fail closed against a policy.

Context these tests encode (design doc §4): `RealMT5.order_send` is GTOS's activation choke point
and it runs INSIDE the GTOS Python process (`src/mt5/mt5_real.py:475-497`). Any MCP server that can
place an order — the terminal's own native one on build 6060+, or a third-party Python one importing
`MetaTrader5` — is a second order path that the activation token cannot see.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
# `scripts/` is never added to sys.path. `scripts/research/` is a REGULAR package and the repo
# root's `research/` is a NAMESPACE one, so it would win regardless of position and break
# `research.operations` for every test that ran afterwards in the same process.

_SPEC = importlib.util.spec_from_file_location(
    "gtos_mt5_mcp_readonly", REPO / "scripts" / "gtos_mt5_mcp_readonly.py")
mcp = importlib.util.module_from_spec(_SPEC)
sys.modules["gtos_mt5_mcp_readonly"] = mcp
_SPEC.loader.exec_module(mcp)

cc = mcp.cc  # the command center, loaded by path by the module under test  # noqa: E402


# ---------------------------------------------------------------------------
# the refusal layer
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(mcp.MUTATING_TOOLS))
def test_every_mutating_tool_is_refused(name):
    with pytest.raises(mcp.MutatingToolRefused) as exc:
        mcp.call_tool(name, cc.Export(None), symbol="XAUUSD", volume=0.01)
    msg = str(exc.value)
    assert "REFUSED" in msg
    assert "read-only by construction" in msg
    assert "activation token" in msg, "the refusal must name the brake it is protecting"


def test_a_refused_tool_is_never_also_implemented():
    """A name cannot be both refused and dispatchable — that would make the order ambiguous."""
    assert not (set(mcp.MUTATING_TOOLS) & set(mcp.TOOLS))


def test_refusal_is_distinct_from_unknown_tool():
    """`create_order` must not read as a typo the caller should retry under another spelling."""
    with pytest.raises(mcp.MutatingToolRefused):
        mcp.call_tool("create_order", cc.Export(None))
    with pytest.raises(mcp.UnknownTool):
        mcp.call_tool("get_the_moon", cc.Export(None))


def test_refusal_precedes_argument_validation():
    """A mutating call is refused even when it is malformed — the check is first, not last."""
    with pytest.raises(mcp.MutatingToolRefused):
        mcp.call_tool("close_position", cc.Export(None), nonsense_kwarg=1)


def test_manifest_publishes_the_refusals():
    d = mcp.describe()
    refused = {r["name"] for r in d["refused_by_design"]}
    assert refused == set(mcp.MUTATING_TOOLS)
    assert "no order-sending code" in d["guarantee"]
    assert {t["name"] for t in d["tools"]} == set(mcp.TOOLS)


# ---------------------------------------------------------------------------
# the structural guarantee
# ---------------------------------------------------------------------------
def test_module_contains_no_broker_mutation_code():
    """Grep-shaped on purpose: here the ABSENCE of a construct IS the property being asserted.

    (Elsewhere in this estate a source-substring test would be the wrong tool — it passes against a
    wrong implementation. It is the right tool for "this file must not contain X".)
    """
    src = (REPO / "scripts" / "gtos_mt5_mcp_readonly.py").read_text()
    body = src.split('"""', 2)[-1]          # skip the module docstring, which discusses these names
    for forbidden in ("import MetaTrader5", "mt5.order_send(", "_mt5.order_send(",
                      "order_send(request", "positions_get()", "symbol_info_tick("):
        assert forbidden not in body, f"{forbidden!r} must never appear in a read-only server"


def test_no_metatrader5_module_is_imported_by_loading_this_server():
    """Rewritten at the wave-13 train: the original asserted absence in THIS process's
    sys.modules, which tests the SUITE'S import history rather than this server -- several
    sibling tests legitimately install a MetaTrader5 stub, so the assertion failed on test
    ORDER. The property that matters: importing the server pulls no MetaTrader5. Asserted in
    a fresh interpreter, where nothing else has run."""
    import subprocess
    code = (
        "import sys, importlib.util; "
        f"spec = importlib.util.spec_from_file_location('gtos_mcp_probe', {str(_SPEC.origin)!r}); "
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
        "sys.exit(1 if 'MetaTrader5' in sys.modules else 0)"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, f"loading the server imported MetaTrader5:\n{r.stderr[-400:]}"


def test_every_exposed_tool_is_a_read():
    """Each tool must run against an EMPTY export without raising and without writing anything.

    A tool that needs to mutate to answer would fail here rather than at a terminal.
    """
    export = cc.Export(None)
    for name in mcp.TOOLS:
        kwargs = {}
        if name != "get_authority_state":
            kwargs["account"] = "FTMO"
        if name == "get_symbol_info":
            kwargs["symbol"] = "XAUUSD"
        out = mcp.call_tool(name, export, **kwargs)
        assert isinstance(out, dict)
        assert "available" in out


def test_unknown_account_is_rejected():
    with pytest.raises(ValueError):
        mcp.call_tool("get_account", cc.Export(None), account="SomeOtherFirm")


# ---------------------------------------------------------------------------
# behaviour against a synthetic export
# ---------------------------------------------------------------------------
@pytest.fixture()
def export(tmp_path):
    api = tmp_path / "09_mt5_api"
    api.mkdir(parents=True)
    (api / "ftmo_account_info.json").write_text(json.dumps(
        {"login": 1, "server": "FTMO-Server3", "balance": 100.0, "equity": 101.0,
         "currency": "USD", "name": "$100k FTMO Challenge 2-Step", "secret_field": "nope"}))
    (api / "ftmo_terminal_info.json").write_text(json.dumps(
        {"build": 5836, "connected": True, "trade_allowed": True, "mqid": True}))
    (api / "ftmo_positions_get.jsonl").write_text(json.dumps(
        {"ticket": 9, "symbol": "XAUUSD", "volume": 0.03, "sl": 1.0, "tp": 2.0,
         "magic": 777, "profit": 1.5}) + "\n")
    (api / "ftmo_symbol_specs_traded.json").write_text(json.dumps(
        {"XAUUSD": {"digits": 2, "trade_contract_size": 100}}))
    return cc.Export(tmp_path)


def test_get_account_projects_only_the_declared_fields(export):
    out = mcp.call_tool("get_account", export, account="FTMO")
    assert out["equity"] == 101.0 and out["login"] == 1
    assert "secret_field" not in out, "the tool must project a declared field set, not pass through"


def test_get_terminal_exposes_the_build(export):
    """`build` is on the surface deliberately: it is the field that says whether the host has taken
    the update that adds a terminal-side AI order path, and nothing else in the estate watches it."""
    out = mcp.call_tool("get_terminal", export, account="FTMO")
    assert out["build"] == 5836


def test_get_positions_reads_the_jsonl(export):
    out = mcp.call_tool("get_positions", export, account="FTMO")
    assert out["n"] == 1 and out["positions"][0]["ticket"] == 9


def test_get_symbol_info_handles_the_dict_keyed_shape(export):
    out = mcp.call_tool("get_symbol_info", export, account="FTMO", symbol="XAUUSD")
    assert out["available"] is True and out["spec"]["digits"] == 2


def test_get_symbol_info_missing_symbol_lists_what_it_knows(export):
    out = mcp.call_tool("get_symbol_info", export, account="FTMO", symbol="NOPE")
    assert out["available"] is False and out["known_symbols"] == ["XAUUSD"]


def test_history_deals_declares_the_broker_clock_semantics(export):
    out = mcp.call_tool("get_history_deals", export, account="FTMO")
    assert "broker-clock epoch" in out["time_field_semantics"], \
        "a deal time that a caller might read as UTC must say so at the point of delivery"


def test_authority_state_reports_the_single_record_trap(tmp_path):
    """The GTOS-specific tool must hand back the union AND what a single record would have claimed.

    An agent that re-derived the armed set from the raw log would walk into `launcher.py:328`.
    """
    logs = tmp_path / "05_shadow_logs"
    logs.mkdir(parents=True)
    (tmp_path / "09_mt5_api").mkdir(parents=True)
    rows = [
        {"action": "cycle", "namespace": "operator_profile", "ts": "2026-07-25T00:00:00+00:00",
         "tags": ["a", "b", "c"], "advanced_tf": [16388, 16408],
         "bridge": {"enabled": True, "apply_to_execution": False,
                    "live_activation_allowed_by_config": False, "live_broker_authority": False,
                    "profile": "p"}},
        {"action": "cycle", "namespace": "operator_profile", "ts": "2026-07-25T04:00:00+00:00",
         "tags": ["a"], "advanced_tf": [16388],
         "bridge": {"enabled": True, "apply_to_execution": False,
                    "live_activation_allowed_by_config": False, "live_broker_authority": False,
                    "profile": "p"}},
    ]
    (logs / "ultimate_book_launcher.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n")
    out = mcp.call_tool("get_authority_state", cc.Export(tmp_path))
    ftmo = out["per_account"]["FTMO"]
    assert ftmo["n_effective_sleeves"] == 3, "the union, not the last record"
    assert ftmo["last_single_record_would_have_said"] == 1
    assert ftmo["gates"]["live_broker_authority"] is False
    assert "PRE-DF-1" in ftmo["caveat"]


def test_cli_returns_2_on_a_refused_tool():
    import subprocess
    r = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "gtos_mt5_mcp_readonly.py"),
         "--call", "create_order"], capture_output=True, text=True)
    assert r.returncode == 2, "a refusal must be distinguishable from a usage error by exit code"
    assert "REFUSED" in r.stderr
