"""BookLauncher safety logic: bar-close gating (no cycle without a new closed bar), and the
kill-switch / halt flag forcing run_cycle(place=False) (observe-only) even when a bar advanced."""
from datetime import datetime, timezone, timedelta

from src.components.ultimate_book.launcher import BookLauncher


class _FakeMT5:
    """get_candles returns 3 candles ending at self.head; the latest CLOSED bar (forming dropped) is
    head - 4h. Advancing self.head simulates a new H4 bar closing."""
    def __init__(self):
        self.head = datetime(2026, 6, 15, 8, 0, tzinfo=timezone.utc)
    def get_candles(self, symbol, tf, count):
        out = []
        for k in (2, 1, 0):
            t = self.head - timedelta(hours=4 * k)
            out.append({"time": t.isoformat(), "open": 100.0, "high": 101.0, "low": 99.0,
                        "close": 100.5, "volume": 100.0})
        return out


class _FakeOwner:
    def __init__(self):
        self.calls = []
        self.manage_calls = 0
        self.base_config = {}
    def run_cycle(self, *, now_utc=None, tags=None, place=True):
        self.calls.append({"tags": tags, "place": place})
        return {"ok": True, "reason": "x", "n_intents": 0, "runtime_effect_now": place,
                "placed": [], "shadow": 0, "skipped": []}
    def manage_open_positions(self, *, now_utc=None):
        self.manage_calls += 1
        return {"managed": [], "adopted": [], "closed": [], "errors": []}


def _launcher(tmp_path, owner, mt5):
    return BookLauncher(owner, mt5, lambda s: s, repo_root=str(tmp_path), tags=("crypto",),
                        poll_seconds=0.01)


def test_no_cycle_without_new_bar(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    r1 = lc.tick()                              # first bar -> cycle
    assert r1["action"] == "cycle" and len(owner.calls) == 1
    r2 = lc.tick()                              # same bar -> no cycle
    assert r2["action"] == "no_new_bar" and len(owner.calls) == 1


def test_launcher_timeframes_include_active_candidate_book(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    owner.base_config = {
        "gtos_vnext_runtime": {
            "ultimate_book_include_candidate_book": True,
            "ultimate_book_candidate_book_sleeves": [
                "vol_compression",
                "asia_pdl_fade",
                "ny_crypto_momentum",
            ],
        }
    }
    lc = BookLauncher(owner, mt5, lambda s: s, repo_root=str(tmp_path), tags=None, poll_seconds=0.01)
    assert 16408 in lc._tf_tags      # D1 candidate vol_compression
    assert 15 in lc._tf_tags         # M15 candidate sleeves
    assert "vol_compression" in lc._tf_tags[16408]
    assert "asia_pdl_fade" in lc._tf_tags[15]
    assert "ny_crypto_momentum" in lc._tf_tags[15]


def test_launcher_cycle_log_carries_bridge_telemetry(tmp_path):
    import json

    class _TelemetryOwner(_FakeOwner):
        def run_cycle(self, *, now_utc=None, tags=None, place=True):
            self.calls.append({"tags": tags, "place": place})
            return {
                "ok": True,
                "reason": "admitted_book_authority",
                "n_intents": 1,
                "runtime_effect_now": True,
                "placed": [],
                "shadow": 0,
                "skipped": [],
                "runtime_learning": {
                    "enabled": True,
                    "log_path": "shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
                    "schema": "ultimate_book_runtime_learning_packet_v1",
                    "packets": 2,
                },
                "bridge": {
                    "runtime_effect_now": True,
                    "candidate_use_allowed_now": True,
                    "decision_status": "admitted_book_authority",
                    "include_candidate_book": True,
                    "candidate_book_sleeves": ["ny_crypto_momentum"],
                    "realized_units": [{"sleeve_members": ["ny_crypto_momentum"], "sized": True}],
                    "would_units": [{"sleeve_members": ["ny_crypto_momentum"], "sized": True}],
                },
            }

    owner, mt5 = _TelemetryOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    rec = lc.tick()
    assert rec["action"] == "cycle"
    log_path = tmp_path / "shadow_logs" / "ultimate_book_launcher.jsonl"
    row = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert row["runtime_effect_now"] is True
    assert row["bridge"]["include_candidate_book"] is True
    assert row["bridge"]["candidate_book_sleeves"] == ["ny_crypto_momentum"]
    assert row["bridge"]["realized_units"][0]["sleeve_members"] == ["ny_crypto_momentum"]
    assert row["runtime_learning"]["schema"] == "ultimate_book_runtime_learning_packet_v1"
    assert row["runtime_learning"]["packets"] == 2


def test_h4_fires_on_btc_when_xau_frozen(tmp_path):
    """crypto-weekend-underfire: the H4 cycle advances when BTCUSD (24/7) advances even while XAUUSD is
    frozen (weekend), so the crypto sleeve still generates weekend signals."""
    class _PerSymMT5:
        def __init__(self):
            self.xau_head = datetime(2026, 6, 13, 20, 0, tzinfo=timezone.utc)   # Fri last H4 (frozen)
            self.btc_head = datetime(2026, 6, 13, 20, 0, tzinfo=timezone.utc)
        def get_candles(self, symbol, tf, count):
            head = self.btc_head if "BTC" in symbol else self.xau_head
            return [{"time": (head - timedelta(hours=4 * k)).isoformat(), "open": 100.0, "high": 101.0,
                     "low": 99.0, "close": 100.5, "volume": 100.0} for k in (2, 1, 0)]
    owner, mt5 = _FakeOwner(), _PerSymMT5()
    lc = _launcher(tmp_path, owner, mt5)
    assert lc.tick()["action"] == "cycle" and len(owner.calls) == 1
    assert lc.tick()["action"] == "no_new_bar"
    mt5.btc_head += timedelta(hours=4)                 # BTC prints a weekend H4 bar; XAUUSD stays frozen
    r = lc.tick()
    assert r["action"] == "cycle" and len(owner.calls) == 2   # H4 advanced via BTC alone


def test_d1_fires_on_btc_when_xau_frozen_for_market_expansion(tmp_path):
    class _PerSymD1MT5:
        def __init__(self):
            self.xau_head = datetime(2026, 6, 13, 0, 0, tzinfo=timezone.utc)
            self.btc_head = datetime(2026, 6, 13, 0, 0, tzinfo=timezone.utc)
        def get_candles(self, symbol, tf, count):
            if tf != 16408:
                raise RuntimeError("this fixture is D1-only")
            head = self.btc_head if "BTC" in symbol else self.xau_head
            return [{"time": (head - timedelta(days=k)).isoformat(), "open": 100.0, "high": 101.0,
                     "low": 99.0, "close": 100.5, "volume": 100.0} for k in (2, 1, 0)]

    owner, mt5 = _FakeOwner(), _PerSymD1MT5()
    owner.base_config = {
        "gtos_vnext_runtime": {
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_policy": "positive_weighted12_after_swap",
            "ultimate_book_market_expansion_sleeves": [],
        }
    }
    lc = BookLauncher(owner, mt5, lambda s: s, repo_root=str(tmp_path), tags=None, poll_seconds=0.01)
    lc._tf_tags = {16408: lc._tf_tags[16408]}
    lc._last_bar_by_tf = {16408: None}
    assert lc.tick()["action"] == "cycle" and len(owner.calls) == 1
    assert lc.tick()["action"] == "no_new_bar"
    mt5.btc_head += timedelta(days=1)
    r = lc.tick()
    assert r["action"] == "cycle" and len(owner.calls) == 2


def test_transient_failure_does_not_consume_bar(tmp_path):
    """bar-consumed-on-transient-failure: a cycle that did not evaluate (broker hiccup -> bar_consumable
    False) must NOT consume the bar, so the next tick RETRIES that same bar instead of skipping its signal."""
    class _TransientOwner(_FakeOwner):
        def run_cycle(self, *, now_utc=None, tags=None, place=True):
            self.calls.append({"tags": tags, "place": place})
            return {"ok": False, "reason": "equity_unavailable", "n_intents": 0,
                    "runtime_effect_now": False, "placed": [], "shadow": 0, "skipped": [],
                    "bar_consumable": False}
    owner, mt5 = _TransientOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    r1 = lc.tick()
    assert r1["action"] == "cycle" and len(owner.calls) == 1
    r2 = lc.tick()                                   # SAME bar, not consumed -> cycle RE-RUNS (retry)
    assert r2["action"] == "cycle" and len(owner.calls) == 2


def test_management_runs_every_tick_even_without_new_bar(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    lc.tick()                                   # first tick (bar advances)
    r2 = lc.tick()                              # no new bar -> no cycle...
    assert r2["action"] == "no_new_bar"
    assert owner.manage_calls == 2              # ...but management STILL ran every tick


def test_new_bar_triggers_cycle(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    lc.tick()
    mt5.head += timedelta(hours=4)              # a new H4 bar closed
    r = lc.tick()
    assert r["action"] == "cycle" and len(owner.calls) == 2
    assert owner.calls[-1]["place"] is True


def test_kill_switch_forces_observe_only(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pipeline_state" / "ULTIMATE_BOOK_KILL.flag").write_text("stop")
    r = lc.tick()
    assert r["action"] == "cycle" and r["killed"] is True
    assert owner.calls[-1]["place"] is False    # kill-switch -> NEVER place


def test_halt_flag_forces_observe_only(tmp_path):
    owner, mt5 = _FakeOwner(), _FakeMT5()
    lc = _launcher(tmp_path, owner, mt5)
    (tmp_path / "pipeline_state").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pipeline_state" / "RESEARCH_RUNTIME_HALT.flag").write_text("halt")
    r = lc.tick()
    assert r["halted"] is True and owner.calls[-1]["place"] is False


def test_tick_never_raises_on_owner_error(tmp_path):
    class Boom:
        def run_cycle(self, **k): raise RuntimeError("cycle blew up")
    lc = _launcher(tmp_path, Boom(), _FakeMT5())
    r = lc.tick()                               # must not raise
    assert r["action"] == "error"


def test_tick_writes_namespaced_heartbeat(tmp_path):
    """F1: each tick stamps a per-namespace heartbeat so the monitor can detect a HUNG (PID alive, not
    ticking) worker, distinct from a DEAD one."""
    import json
    owner, mt5 = _FakeOwner(), _FakeMT5()
    owner._namespace = "ftmo_test"             # launcher reads owner._namespace at construction
    lc = _launcher(tmp_path, owner, mt5)
    lc.tick()
    hb = tmp_path / "pipeline_state" / "ultimate_book" / "ftmo_test" / "heartbeat.json"
    assert hb.exists()
    rec = json.loads(hb.read_text())
    assert rec["namespace"] == "ftmo_test" and "ts" in rec and "pid" in rec
    assert rec.get("healthy") is True   # COMP-4: heartbeat carries connection health for the monitor


def test_book_profile_nominal_for_notifier():
    """F2: the notifier now derives $/R from the active book profile nominal (1.25%), not the legacy
    per-symbol risk_per_trade_pct (2.0%) the book does not size with."""
    from src.components.ultimate_book.admission import ALLOCATION_PROFILES
    prof = ALLOCATION_PROFILES["clean3_w7_measured_nom1p25"]
    assert round(prof.risk_per_unit_A * 100.0, 4) == 1.25
    assert round(ALLOCATION_PROFILES["clean3_w7_ceiling_nom2p00"].risk_per_unit_A * 100.0, 4) == 2.00


def test_no_reconnect_spam_on_persistent_outage(tmp_path):
    """A persistent MT5 outage must alert ONCE (not every tick) and never falsely say 'reconnected'."""
    notifies = []

    class _DownMT5(_FakeMT5):
        def __init__(self):
            super().__init__()
            self._conn = False
            self._connect_succeeds = False
        def is_connected(self):
            return self._conn
        def connect(self):
            if self._connect_succeeds:
                self._conn = True   # reconnect succeeds only once flagged
            return self._conn
    owner, mt5 = _FakeOwner(), _DownMT5()
    lc = _launcher(tmp_path, owner, mt5)
    lc._notify = lambda m: notifies.append(m)
    for _ in range(3):
        lc.tick()
    assert sum("DISCONNECTED" in n for n in notifies) == 1     # alerted once on the persistent outage
    assert sum("reconnected" in n for n in notifies) == 0      # never falsely 'reconnected'

    mt5._connect_succeeds = True   # link comes back; next tick's connect() succeeds
    lc.tick()
    assert sum("reconnected" in n for n in notifies) == 1      # a single real reconnect notice


def test_broker_link_down_alerts_even_when_terminal_up(tmp_path):
    """MACRO-RES-02: the terminal PROCESS is up (is_connected True) but the BROKER/trade-server LINK is
    down -> the book is trade-blind and must alert (once) + attempt reconnect, not silently judge healthy.
    On link recovery it confirms ONCE."""
    notifies = []

    class _LinkDownMT5(_FakeMT5):
        def __init__(self):
            super().__init__()
            self._link = False
        def is_connected(self):
            return True                 # terminal process up...
        def connect(self):
            return True
        def broker_link_connected(self):
            return self._link           # ...but the broker/trade-server link is down

    owner, mt5 = _FakeOwner(), _LinkDownMT5()
    lc = _launcher(tmp_path, owner, mt5)
    lc._notify = lambda m: notifies.append(m)
    for _ in range(3):
        lc.tick()
    assert sum("DISCONNECTED" in n for n in notifies) == 1     # broker-link outage alerted once
    assert sum("reconnected" in n for n in notifies) == 0
    mt5._link = True                   # broker link restored (on its own, terminal never went down)
    lc.tick()
    assert sum("reconnected" in n for n in notifies) == 1      # single recovery confirmation
