"""Book edge reconciler — the closed loop (SYNTH-1 / MACRO-EDGE-01): realized per-sleeve P&L folds into a
persisted expectancy and a sleeve whose trailing window turns net-losing over a minimum sample alarms."""
import tempfile

from src.components.ultimate_book.edge_reconciler import BookEdgeReconciler


def _deals(sleeve, profits, start_ticket=1, t0=1000):
    return [{"ticket": start_ticket + i, "sleeve": sleeve, "profit": p, "time": t0 + i}
            for i, p in enumerate(profits)]


def test_no_alarm_when_profitable():
    r = BookEdgeReconciler(tempfile.mkdtemp(), "ns", min_sample=5, window=10)
    assert r.ingest(_deals("idxrev", [10, -5, 20, 8, -3, 15])) == []     # net positive window
    assert r.summary()["idxrev"]["alarmed"] is False


def test_decay_alarm_when_window_net_losing():
    r = BookEdgeReconciler(tempfile.mkdtemp(), "ns", min_sample=5, window=10)
    alarms = r.ingest(_deals("idxrev", [-10, -5, -20, -8, -3, -15]))    # 6 trades, net negative
    assert any("idxrev" in a and "DECAY" in a for a in alarms)
    assert r.summary()["idxrev"]["alarmed"] is True


def test_idempotent_and_persistent():
    d = tempfile.mkdtemp()
    deals = _deals("idxrev", [-10, -5, -20, -8, -3, -15])
    r = BookEdgeReconciler(d, "ns", min_sample=5, window=10)
    r.ingest(deals)
    n1 = r.summary()["idxrev"]["n"]
    assert r.ingest(deals) == [] and r.summary()["idxrev"]["n"] == n1     # same tickets -> no double-count
    # a fresh reconciler (post-restart) reloads the cursor + state from disk
    assert BookEdgeReconciler(d, "ns").summary()["idxrev"]["n"] == n1


def test_rearm_on_recovery_then_realarm():
    r = BookEdgeReconciler(tempfile.mkdtemp(), "ns", min_sample=5, window=8)
    r.ingest(_deals("idxrev", [-10, -5, -20, -8, -3, -15], start_ticket=1, t0=1000))
    assert r.summary()["idxrev"]["alarmed"] is True
    r.ingest(_deals("idxrev", [30] * 8, start_ticket=100, t0=2000))      # window recovers positive
    assert r.summary()["idxrev"]["alarmed"] is False                      # re-armed
    assert any("DECAY" in a for a in r.ingest(_deals("idxrev", [-40] * 8, start_ticket=200, t0=3000)))


def test_per_sleeve_isolation():
    r = BookEdgeReconciler(tempfile.mkdtemp(), "ns", min_sample=5, window=10)
    alarms = r.ingest(_deals("metals_core", [-10] * 6, start_ticket=1)
                      + _deals("idxrev", [20] * 6, start_ticket=50))
    assert any("metals_core" in a for a in alarms) and not any("idxrev" in a for a in alarms)
