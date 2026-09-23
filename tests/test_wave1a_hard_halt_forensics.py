from src.research_infra.wave1a_hard_halt_forensics import (
    broker_stats,
    canonical_symbol,
    classify_failure_tags,
    compute_exact_or_proxy_r,
)


def test_canonical_symbol_aliases_broker_names():
    assert canonical_symbol("NAS100") == "NDX100"
    assert canonical_symbol("GER40") == "GER30"
    assert canonical_symbol("XAUUSD") == "XAUUSD"


def test_broker_stats_computes_cash_denominator():
    trades = [
        {"net_pnl": 100.0},
        {"net_pnl": -50.0},
        {"net_pnl": -25.0},
    ]
    stats = broker_stats(trades)
    assert stats["trade_count"] == 3
    assert stats["net_pnl_broker_real_cash"] == 25.0
    assert stats["wins"] == 1
    assert stats["losses"] == 2
    assert stats["win_rate"] == 0.333333


def test_exact_r_prefers_trade_record_exit_actual_r():
    trade = {"net_pnl": -250.0}
    record = {"execution": {"cash_risk_amount": 500.0}, "exit": {"actual_r": -0.75}}
    fields = compute_exact_or_proxy_r(trade, record)
    assert fields["exact_r"] == -0.75
    assert fields["proxy_r"] is None
    assert fields["exact_r_status"] == "source_bound_trade_record_exit_actual_r"


def test_proxy_r_when_exact_geometry_missing():
    fields = compute_exact_or_proxy_r({"net_pnl": -125.0}, None)
    assert fields["exact_r"] is None
    assert fields["proxy_r"] == -0.5
    assert fields["proxy_r_status"] == "broker_cash_pnl_div_default_0_25pct_proxy_risk_250usd"


def test_failure_tags_capture_cost_cluster_and_micro_ev():
    tags = classify_failure_tags(
        symbol="NAS100",
        net_pnl=-300.0,
        exit_reasons=["sl"],
        exit_comments=["[sl 123]"],
        swap=-100.0,
        selected_expectancy=0.03,
        selected_rows=21,
        cluster_size=3,
    )
    assert "dominant_damage_symbol" in tags
    assert "high_swap_drag" in tags
    assert "micro_positive_ev_floor" in tags
    assert "small_selected_cell_denominator" in tags
    assert "clustered_entry" in tags

