from __future__ import annotations

import json

from research.operations.vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02 import (
    build_vnext_ftmo_local_profile_and_vps_dual_prod_prep as builder,
)
from research.operations.vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02.verify_vnext_ftmo_local_profile_and_vps_dual_prod_prep import (
    verify_route,
)
from scripts.verify_broker_profile import VNEXT_24_SYMBOLS


def test_ftmo_alias_resolution_prefers_cash_aliases():
    inventory_names = {
        "AUDJPY",
        "AUDUSD",
        "BTCUSD",
        "CHFJPY",
        "ETHUSD",
        "EURGBP",
        "EURJPY",
        "EURUSD",
        "GBPJPY",
        "GBPUSD",
        "GER40.cash",
        "JP225.cash",
        "US100.cash",
        "NZDUSD",
        "US500.cash",
        "UK100.cash",
        "UKOIL.cash",
        "US30.cash",
        "USDCAD",
        "USDCHF",
        "USDJPY",
        "USOIL.cash",
        "XAGUSD",
        "XAUUSD",
    }
    rows = builder.resolve_aliases([{"name": name} for name in inventory_names])
    by_symbol = {row["symbol"]: row for row in rows}

    assert len(rows) == len(VNEXT_24_SYMBOLS)
    assert all(row["alias_status"] == "resolved" for row in rows)
    assert by_symbol["NAS100"]["mt5_symbol"] == "US100.cash"
    assert by_symbol["SPX500"]["mt5_symbol"] == "US500.cash"
    assert by_symbol["UKOIL_cash"]["mt5_symbol"] == "UKOIL.cash"
    assert by_symbol["USOIL_cash"]["mt5_symbol"] == "USOIL.cash"


def test_route_verifier_reports_unresolved_active_aliases(tmp_path):
    route_dir = tmp_path / "route"
    route_dir.mkdir()
    rows = [
        {
            "schema_version": "ftmo_alias_resolution_v1",
            "symbol": symbol,
            "mt5_symbol": None if symbol == "NAS100" else symbol,
            "alias_status": "unsupported" if symbol == "NAS100" else "resolved",
        }
        for symbol in VNEXT_24_SYMBOLS
    ]
    (route_dir / "VNEXT_FTMO_ALIAS_RESOLUTION_LEDGER.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = verify_route(route_dir, tmp_path, write_result=False)

    assert result["ok"] is False
    assert any(issue["code"] == "unresolved_active_aliases" for issue in result["issues"])
