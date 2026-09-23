"""The authority-gate tripwire, and the monitor that carries it.

Two things are asserted here and they are different in kind.

**The monitor runs at all.** `.tools/monitor_books.py` is the only process in the
system that sends an alert anywhere a human sees it, and at HEAD it was dead:
B58 widened `ACCOUNTS` to 5-tuples and updated five of the six unpack sites. The
sixth sat in the daemon's `while True` body, outside any `try`, *before* the
`send()` loop — so it raised `ValueError: too many values to unpack (expected 4,
got 5)` on cycle 0, having sent nothing, while `write_monitor_heartbeat("running")`
had already fired so the supervisor saw a healthy process and respawned it into
the same crash every 30 s. `tests/test_monitor_books_guard.py` covers the
single-instance logic only and could not have caught it.

**The tripwire itself.** Nothing watched the live-authority booleans. The
2026-07-26 VPS inspection found no flag file, no terminal block and no scheduler
stop — so the whole brake was config, and a flip of that config would have been
detected by nothing at all.

The tests import `.tools/monitor_books.py` by path with the `MetaTrader5` import
stubbed, because the module is on the never-execute list and imports the real
broker package at line 24.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MONITOR_PATH = REPO_ROOT / ".tools" / "monitor_books.py"


@pytest.fixture(scope="module")
def monitor():
    """Import the monitor with the broker package stubbed. Never connects."""

    stub = types.ModuleType("MetaTrader5")
    for name in ("initialize", "shutdown", "account_info", "positions_get",
                 "history_deals_get", "symbol_info", "last_error"):
        setattr(stub, name, lambda *a, **k: None)
    saved = sys.modules.get("MetaTrader5")
    sys.modules["MetaTrader5"] = stub
    try:
        spec = importlib.util.spec_from_file_location("_monitor_books_under_test", MONITOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        if saved is None:
            sys.modules.pop("MetaTrader5", None)
        else:
            sys.modules["MetaTrader5"] = saved


# --------------------------------------------------------------------------
# The monitor has to survive its own cycle
# --------------------------------------------------------------------------


def test_every_accounts_unpack_matches_the_accounts_tuple_arity(monitor):
    """The regression that silenced the daemon was an arity mismatch in one of
    six unpack sites. Assert the property, not the one line: any future widening
    of ACCOUNTS that misses a site fails here instead of at 3 a.m. on the VPS."""

    import ast

    arities = {len(row) for row in monitor.ACCOUNTS}
    assert len(arities) == 1, "ACCOUNTS rows are not all the same width"
    arity = arities.pop()

    tree = ast.parse(MONITOR_PATH.read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        # `for (a, b, c) in ACCOUNTS:` and `for (a, b, c), m in zip(ACCOUNTS, ...)`
        if not isinstance(node, (ast.For, ast.comprehension)):
            continue
        target = node.target
        if isinstance(target, ast.Tuple) and len(target.elts) == 2:
            inner = target.elts[0]
            if isinstance(inner, ast.Tuple):
                target = inner
        if not isinstance(target, ast.Tuple):
            continue
        if "ACCOUNTS" not in ast.dump(node.iter):
            continue
        if len(target.elts) != arity:
            offenders.append((getattr(node, "lineno", "?"), len(target.elts)))

    assert not offenders, (
        f"ACCOUNTS rows are {arity}-tuples but these unpacks are not: {offenders}. "
        f"An unpack in the daemon loop that is outside a try kills every alert."
    )


def test_a_monitor_cycle_reaches_its_alert_send(monitor, monkeypatch, tmp_path):
    """Behavioural: drive one non-daemon cycle with the broker stubbed and assert
    it gets as far as sending. Against the pre-fix code this raises ValueError
    before a single `send()`."""

    sent = []
    monkeypatch.setattr(monitor, "snap", lambda *a, **k: {})
    monkeypatch.setattr(monitor, "live_namespaces", lambda: set())
    monkeypatch.setattr(monitor, "edge_reconcile_all", lambda: [])
    monkeypatch.setattr(monitor, "disk_space_alert", lambda *a, **k: [])
    monkeypatch.setattr(monitor, "gate_tripwire", lambda: [])
    monkeypatch.setattr(monitor, "send", lambda msg: sent.append(msg))
    monkeypatch.setattr(sys, "argv", ["monitor_books.py"])

    monitor.main()

    assert any("RISK BLIND" in m for m in sent), (
        f"the cycle did not reach its alert send; got {sent!r}"
    )


# --------------------------------------------------------------------------
# The tripwire
# --------------------------------------------------------------------------


def _heartbeat(tmp_repo, namespace, **fields):
    path = tmp_repo / "pipeline_state" / "ultimate_book" / namespace / "heartbeat.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), "pid": 1,
              "namespace": namespace, "healthy": True}
    record.update(fields)
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


SHADOW_GATES = {
    "ultimate_book_enabled": True,
    "ultimate_book_apply_to_execution": True,
    "ultimate_book_live_activation_allowed": False,
    "ultimate_book_live_broker_authority": False,
}


@pytest.fixture()
def isolated(monitor, monkeypatch, tmp_path):
    """Point the tripwire at a temp tree with one account, so the tests are about
    the detector rather than about this machine's config."""

    monkeypatch.setattr(monitor, "REPO_ROOT", str(tmp_path))
    monkeypatch.setattr(monitor, "ACCOUNTS", [
        ("FTMO", r"C:\MT5\FTMO\terminal64.exe", 531325516, "operator_profile", "Europe/Prague"),
    ])
    monkeypatch.setattr(monitor, "_resolved_gates_from_disk",
                        lambda profile=None: (dict(SHADOW_GATES), None))
    return tmp_path


def test_a_clean_shadow_state_is_quiet(monitor, isolated):
    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES),
               runtime_effect_now=False)
    assert monitor.gate_tripwire() == []


def test_an_edited_config_is_detected_before_any_restart(monitor, isolated, monkeypatch):
    """The early signal. A flip only takes effect on restart, so seeing it in the
    file is worth more than seeing it in a process."""

    flipped = dict(SHADOW_GATES, ultimate_book_live_activation_allowed=True)
    monkeypatch.setattr(monitor, "_resolved_gates_from_disk", lambda profile=None: (flipped, None))
    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES), runtime_effect_now=False)

    alerts = monitor.gate_tripwire()

    assert any("AUTHORITY GATE CHANGED ON DISK" in a for a in alerts)
    assert any("live_activation_allowed" in a for a in alerts)


def test_a_running_book_with_live_authority_is_detected(monitor, isolated):
    _heartbeat(isolated, "operator_profile",
               gates=dict(SHADOW_GATES, ultimate_book_live_broker_authority=True),
               runtime_effect_now=True)

    alerts = monitor.gate_tripwire()

    assert any("RUNNING BOOK IS AUTHORISED" in a for a in alerts)
    assert any("LIVE ORDER AUTHORITY ACTIVE" in a for a in alerts)


def test_a_gate_key_that_should_not_exist_is_detected(monitor, isolated, monkeypatch):
    """`ultimate_book_live_broker_authority` appears in no committed config; it
    resolves False from a code default. Its APPEARANCE as true is the flip."""

    monkeypatch.setattr(
        monitor, "_resolved_gates_from_disk",
        lambda profile=None: (dict(SHADOW_GATES, ultimate_book_live_broker_authority=True), None),
    )
    assert any("live_broker_authority" in a for a in monitor.gate_tripwire())


def test_an_unreadable_config_is_never_reported_as_all_clear(monitor, isolated, monkeypatch):
    monkeypatch.setattr(monitor, "_resolved_gates_from_disk",
                        lambda profile=None: (None, "OSError('boom')"))
    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES))

    alerts = monitor.gate_tripwire()

    assert any("GATE STATE UNVERIFIABLE" in a for a in alerts)


def test_a_book_that_publishes_no_gate_state_is_never_all_clear(monitor, isolated):
    """A worker on a pre-tripwire build looks identical to a healthy one."""

    _heartbeat(isolated, "operator_profile")

    assert any("GATE STATE UNVERIFIABLE" in a for a in monitor.gate_tripwire())


def test_a_stale_heartbeat_is_left_to_the_hang_detector(monitor, isolated):
    """book_hung already owns staleness; double-alerting trains the operator to
    ignore the channel."""

    old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)).isoformat()
    _heartbeat(isolated, "operator_profile", ts=old)

    assert monitor.gate_tripwire() == []


def test_a_book_that_has_never_started_is_left_to_the_down_detector(monitor, isolated):
    assert monitor.gate_tripwire() == []


# --------------------------------------------------------------------------
# Hole 2 — the un-digested derisk override, made observable
# --------------------------------------------------------------------------


def test_an_env_override_of_the_derisk_mode_is_detected(monitor, isolated):
    """`GTOS_UB_DERISK_MODE` wins over YAML (book_engine.py:580) while the
    activation token's config digest hashes only the config FILES — so this is
    the one way to make the live derisk shape disagree with the config a token
    certifies, and it left no trace."""

    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES),
               runtime_effect_now=False, derisk_mode_yaml="smooth",
               derisk_mode_effective="band", profile="clean3_w7_ceiling_nom2p00")

    alerts = monitor.gate_tripwire()

    assert any("DERISK MODE OVERRIDDEN" in a for a in alerts)


def test_a_silently_flat_book_at_the_live_dial_is_detected(monitor, isolated):
    """At the live 2.0% dial `admit_and_size` fails closed on any non-smooth
    shape (admission.py:1407). The book keeps ticking, keeps reporting healthy,
    and admits nothing. That is the failure this alert exists for."""

    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES),
               runtime_effect_now=False, derisk_mode_yaml="band",
               derisk_mode_effective="band", profile="clean3_w7_ceiling_nom2p00")

    alerts = monitor.gate_tripwire()

    assert any("SILENTLY FLAT" in a for a in alerts)


def test_a_sub_two_percent_dial_does_not_raise_the_flat_alarm(monitor, isolated):
    """The interlock is not armed below 2.0%, so band there is a shape change,
    not a stop. Alerting on it would be a false positive."""

    _heartbeat(isolated, "operator_profile", gates=dict(SHADOW_GATES),
               runtime_effect_now=False, derisk_mode_yaml="band",
               derisk_mode_effective="band", profile="clean3_w7_measured_nom1p25")

    assert not any("SILENTLY FLAT" in a for a in monitor.gate_tripwire())


def test_the_live_dial_is_the_one_the_interlock_arms_on(monitor):
    """Pins the fact the two alerts above depend on."""

    assert monitor._dial_requires_smooth("clean3_w7_ceiling_nom2p00") is True
    assert monitor._dial_requires_smooth("clean3_w7_measured_nom1p25") is False
    assert monitor._dial_requires_smooth("a_dial_that_does_not_exist") is False


# --------------------------------------------------------------------------
# The producer side
# --------------------------------------------------------------------------


def test_the_launcher_publishes_the_state_the_tripwire_reads():
    """The consumer above is worthless if the producer stops emitting. Assert the
    contract from the launcher's side, without a broker."""

    from src.components.ultimate_book.launcher import BookLauncher

    class _Owner:
        base_config = {"gtos_vnext_runtime": {
            "ultimate_book_enabled": True,
            "ultimate_book_apply_to_execution": True,
            "ultimate_book_live_activation_allowed": False,
            "ultimate_book_profile": "clean3_w7_ceiling_nom2p00",
            "ultimate_book_derisk_mode": "smooth",
        }}

        def _runtime_learning_bridge_context(self, decision=None):
            rt = self.base_config["gtos_vnext_runtime"]
            return {
                "enabled": rt["ultimate_book_enabled"],
                "apply_to_execution": rt["ultimate_book_apply_to_execution"],
                "live_activation_allowed_by_config": rt["ultimate_book_live_activation_allowed"],
                "live_broker_authority": False,
                "runtime_effect_now": False,
                "profile": rt["ultimate_book_profile"],
            }

    launcher = BookLauncher.__new__(BookLauncher)
    launcher.owner = _Owner()

    state = launcher._authority_state()

    assert set(state["gates"]) == set(SHADOW_GATES)
    assert state["runtime_effect_now"] is False
    assert state["profile"] == "clean3_w7_ceiling_nom2p00"
    assert state["derisk_mode_effective"] in {"smooth", "band"}
    assert "GTOS_ACTIVATION_TOKEN_DIR" in state["env"]


def test_the_authority_state_never_raises_into_the_tick():
    """It is called from `_write_heartbeat`, which runs before any broker call at
    the top of every tick. A book must not die because its telemetry did."""

    from src.components.ultimate_book.launcher import BookLauncher

    class _Hostile:
        base_config = None

        def _runtime_learning_bridge_context(self, decision=None):
            raise RuntimeError("bridge exploded")

    launcher = BookLauncher.__new__(BookLauncher)
    launcher.owner = _Hostile()

    state = launcher._authority_state()

    assert "gates" not in state          # unavailable, and the monitor alerts on that
    assert "env" in state
