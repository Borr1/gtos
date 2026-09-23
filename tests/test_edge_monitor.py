import json

from src.components.edge_monitor import EdgeMonitor, make_gtos_monitor


def test_load_state_repairs_corrupt_bocpd_vectors(tmp_path):
    state_path = tmp_path / "edge_monitor_state.json"

    monitor = make_gtos_monitor("primary")
    for outcome in [True, True, False, True]:
        monitor.update(outcome)
    monitor.save_state(str(state_path))

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["bocpd_run_wins"].extend([99.0, 100.0])
    state_path.write_text(json.dumps(state), encoding="utf-8")

    repaired = EdgeMonitor.load_state(str(state_path))

    assert repaired.n_trades == 4
    assert repaired._bocpd.n_obs == 4
    assert len(repaired._bocpd._log_joint) == len(repaired._bocpd._run_wins)
    assert len(repaired._bocpd._log_joint) == len(repaired._bocpd._run_n)

    result = repaired.update(False)

    assert result["n_trades"] == 5
    assert len(repaired._bocpd._log_joint) == len(repaired._bocpd._run_wins)
    assert len(repaired._bocpd._log_joint) == len(repaired._bocpd._run_n)


def test_load_state_keeps_valid_bocpd_vectors(tmp_path):
    state_path = tmp_path / "edge_monitor_state.json"

    monitor = make_gtos_monitor("primary")
    for outcome in [True, False, True]:
        monitor.update(outcome)
    monitor.save_state(str(state_path))

    loaded = EdgeMonitor.load_state(str(state_path))

    assert loaded.n_trades == 3
    assert loaded._bocpd.n_obs == 3
    assert len(loaded._bocpd._log_joint) == 4
    assert len(loaded._bocpd._run_wins) == 4
    assert len(loaded._bocpd._run_n) == 4
