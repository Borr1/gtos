import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "analyze_orderflow_mbo_nas100_features.py"
    spec = importlib.util.spec_from_file_location("analyze_orderflow_mbo_nas100_features", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_order_book_updates_best_prices_and_depth():
    mod = _load_module()
    book = mod.OrderBook("NQ.v.0")

    add_bid = book.apply_row(SimpleNamespace(action="A", side="B", price=100.0, size=2, order_id=1), capture_effects=True)
    book.apply_row(SimpleNamespace(action="A", side="A", price=100.25, size=3, order_id=2), capture_effects=True)

    assert add_bid[0]["near10"] is False
    assert book.best_bid() == 100.0
    assert book.best_ask() == 100.25
    snap = book.snapshot()
    assert snap["total_depth10"] == 5.0
    assert round(snap["depth10_imbalance"], 4) == -0.2

    remove_bid = book.apply_row(SimpleNamespace(action="C", side="N", price=float("nan"), size=1, order_id=1), capture_effects=True)

    assert remove_bid[0]["near10"] is True
    assert book.snapshot()["total_depth10"] == 4.0
    book.apply_row(SimpleNamespace(action="R", side="N", price=float("nan"), size=0, order_id=0), capture_effects=True)
    assert book.snapshot()["total_depth10"] == 0.0
    assert book.clear_count == 1


def test_finalize_window_uses_predeclared_pull_features():
    mod = _load_module()
    acc = mod.WindowAccumulator()
    acc.add_sample({"total_depth20": 100.0, "depth20_imbalance": 0.1, "wall_concentration20": 0.2})
    acc.add_sample({"total_depth20": 80.0, "depth20_imbalance": -0.1, "wall_concentration20": 0.4})
    acc.add_action("B", "add", 10.0, True)
    acc.add_action("B", "remove", 30.0, True)

    row = mod.finalize_window("event15", acc, tick=0.25, thin_threshold=90.0)

    assert row["event15_sample_count"] == 2
    assert row["event15_median_total_depth20"] == 90.0
    assert row["event15_thin_depth20_rate"] == 0.5
    assert row["event15_near10_net_liquidity"] == -20.0
    assert row["event15_near10_bid_pull_pressure"] == 0.75
