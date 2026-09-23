"""Rewrite operator armed_sleeves to live 31 + 3 dsp. Leave redacted_account alone."""
from __future__ import annotations

import json
from pathlib import Path

P = Path(r"host-local\redacted_host\repo\config\live_armed_set.json")
SLEEVES = [
    "asia_pdl_fade",
    "asian_fade",
    "crypto",
    "dsp_climax_flush_to_96low_then_snap",
    "dsp_expanding_up_staircase",
    "dsp_london_two_up_into_20high_reverses",
    "energy_agri",
    "idxrev",
    "kz_london_crypto_low",
    "liq_asia_up_low_metal",
    "metal_session_reversion",
    "metals_core",
    "metals_ob_micro",
    "metals_softband",
    "mx_avausd_d1_donchian_20_breakout",
    "mx_btcusd_d1_donchian_20_breakout",
    "mx_cadjpy_d1_volume_surge_reversal",
    "mx_ethusd_d1_donchian_20_breakout",
    "mx_eu50_cash_d1_volume_surge_reversal",
    "mx_fra40_cash_d1_volume_surge_reversal",
    "mx_ger40_cash_d1_volume_surge_reversal",
    "mx_jp225_cash_d1_volume_surge_reversal",
    "mx_nzdjpy_d1_donchian_20_breakout",
    "mx_us100_cash_d1_atr_mean_reversion",
    "mx_us30_cash_d1_volume_surge_reversal",
    "mx_us500_cash_d1_atr_mean_reversion",
    "orb_crypto_london",
    "sub_mid_dn_revert",
    "sub_xvol_pullback",
    "vol_compression",
    "vp_euidx_pocgrav",
    "vss_fxcross_london_up_low",
    "asian_fade_widen",
    "orb_crypto_london_widen",
]

data = json.loads(P.read_text(encoding="utf-8"))
row = data["accounts"]["operator"]
row["minimal_size_usd"] = "75"
row["armed_sleeves"] = SLEEVES
P.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("armed", len(SLEEVES), "dsp", sum(1 for s in SLEEVES if s.startswith("dsp_")))
