from __future__ import annotations

import json
from pathlib import Path

from scripts import analyze_lane6_asset_risk_edge_triage as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_root(root: Path) -> None:
    _write_json(
        root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_per_cohort_results.json",
        {
            "metadata": {"cohort_size": 2338},
            "primary_full_cohort": {
                "backtest": {"delta": {"mean_r": -0.004960547358764833}},
                "dsr_paired_delta": {"dsr_p": 0.9999646857030353},
            },
        },
    )
    _write_text(
        root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "h_pm01_vol_conditional_sizing.md",
        "realized_vol_rank = percentile rank\n",
    )
    _write_text(
        root / "research" / "ml_program" / "phase_2" / "position_mgmt" / "_compute_h_pm03.py",
        "def f(vol_rank): return vol_rank\n",
    )
    _write_text(
        root / "scripts" / "research" / "na8_babu_decomposition.py",
        "realized_vol_rank\n",
    )
    _write_text(
        root / "research" / "ml_program" / "feature_catalogs" / "volatility.md",
        "Realized vol + transitions\n`h1_realized_vol_20`\n`h1_atr_14_pct_w100`\n",
    )
    _write_text(
        root / "research" / "ml_program" / "feature_catalogs" / "regime.md",
        "\n".join(
            [
                "regime_consecutive_h4_bars",
                "regime_h4_bars_since_last_flip",
                "regime_changed_in_last_1",
                "regime_changed_in_last_5",
                "regime_changed_in_last_10",
                "regime_changed_in_last_20",
                "regime_changed_in_last_50",
                "regime_v2_score_change_1",
                "regime_v2_score_change_5",
                "regime_v2_score_change_20",
            ]
        ),
    )
    _write_text(root / "research" / "ml_program" / "scripts" / "features" / "regime.py", "")
    _write_text(
        root / "shadow_logs" / "regime_classifications.jsonl",
        '{"symbol":"XAUUSD","regime":"trending_bull"}\n',
    )
    _write_json(
        root / "research" / "ml_program" / "audit" / "LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.json",
        {
            "evidence": {
                "k54_v3": {
                    "w_unit_ablation": {
                        "v3_features_minus_arch_a_auc": 0.003457028435499998,
                        "on_minus_off_auc": -0.053973164278853014,
                        "arch_a_auc": 0.5604983423919125,
                        "feature_cols_count": {"v3": 1240},
                    }
                }
            }
        },
    )
    _write_text(
        root / "research" / "ml_program" / "models" / "k54_v3" / "train_k54_v3.py",
        "kw__k7_osler_stopcluster_proxy\n",
    )
    _write_text(root / "research" / "ml_program" / "models" / "k54_v3" / "top_features.json", "{}")
    _write_json(
        root / "research" / "ml_program" / "audit" / "LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json",
        {
            "inventories": {
                "ticks": {
                    "max_symbol_days": 5,
                    "symbols_with_ticks": 7,
                    "tick_features_helper_exists": True,
                }
            }
        },
    )
    _write_text(root / "data" / "external" / "normalized" / "fred" / "VIXCLS_observations_x.jsonl", "{}\n")
    _write_text(root / "data" / "external" / "normalized" / "fred" / "GVZCLS_observations_x.jsonl", "{}\n")
    _write_text(
        root / "data" / "external" / "normalized" / "wgc" / "gold_demand_trends_x.jsonl",
        "{}\n",
    )
    _write_text(
        root / "data" / "historical_2026" / "XAUUSD_D1.csv",
        "time,open,high,low,close,volume\n2026-01-02,1,2,1,2,1\n",
    )
    _write_text(
        root / "research" / "academic_pipeline" / "results" / "Q-crowding_retail.md",
        "CFTC COT speculator positioning | MISSING\nIG / OANDA client-sentiment | MISSING\n",
    )
    _write_json(
        root / "knowledge_base" / "trade_records" / "XAUUSD" / "sample.json",
        {
            "metadata": {"symbol": "XAUUSD"},
            "trade_parameters": {"stop_loss": 214.002, "take_profit_1": 215.0},
            "execution": None,
        },
    )


def test_lane6_asset_risk_edge_triage_classifies_first_cluster(tmp_path):
    _seed_root(tmp_path)

    payload = mod.build_payload(tmp_path)
    by_id = payload["task_classifications"]

    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert by_id["V-1"]["status"] == "DONE"
    assert by_id["V-2"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["V-3"]["status"] == "DONE"
    assert by_id["A-8"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["C-2"]["status"] == "BLOCKED_WITH_REASON"
    assert by_id["E-1"]["status"] == "REJECTED_FAILED"
    assert by_id["E-2"]["status"] == "DEFERRED_WITH_TRIGGER"
    assert by_id["E-4"]["status"] == "BLOCKED_WITH_REASON"
    assert payload["status_counts"] == {
        "BLOCKED_WITH_REASON": 4,
        "DEFERRED_WITH_TRIGGER": 1,
        "DONE": 2,
        "REJECTED_FAILED": 1,
    }


def test_lane6_asset_risk_edge_evidence_extracts_sources_and_feature_state(tmp_path):
    _seed_root(tmp_path)

    evidence = mod.build_evidence(tmp_path)

    assert evidence["vol_features"]["hpm01_has_realized_vol_rank"] is True
    assert evidence["regime_features"]["feature_count_present"] == 10
    assert evidence["external_feeds"]["has_real_gold_deflator"] is False
    assert evidence["external_feeds"]["vol_terms_present"]["VRP"] is False
    assert evidence["k54_osler"]["k7_proxy_in_train_code"] is True
    assert evidence["production_trade_levels"]["records_with_trade_parameters"] == 1
