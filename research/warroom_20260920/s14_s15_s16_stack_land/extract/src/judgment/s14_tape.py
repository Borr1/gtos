"""Challenge 0 historical tape helpers for S14 prove (no live bars).

Rows are gold_state.v0-shaped with **bucket source fields only** — no raw
OHLCV arrays, no ticks, no broker_net / profit / R / MFE / MAE. Identity
nouns come from the Challenge replay family (login 0).
"""

from __future__ import annotations

from typing import Any

CHALLENGE_LOGIN = "0"


def _probs(choice: str, p: float) -> dict[str, float]:
    rest = (1.0 - p) / 4.0
    out = {k: rest for k in ("trend_up", "trend_down", "range", "chop", "unclear")}
    out[choice] = p
    return out


def _answers(choice: str, conf: float, change: float, viable: float) -> dict[str, Any]:
    return {
        "regime_type": {
            "choice": choice,
            "confidence": conf,
            "probabilities": _probs(choice, conf),
        },
        "regime_change_likely": {"noul": change},
        "strategy_viable": {"noul": viable},
    }


def gold_state(
    *,
    sleeve: str,
    symbol: str,
    side: str,
    candidate_id: str,
    close_ret_1: float,
    close_ret_5bar: float,
    vol_ratio: float,
    htf_slope_norm: float,
    mom_20_atr: float,
    atr14: float = 1.2,
    atr50: float = 1.0,
    sma_frac: float = 0.02,
    session: str = "london",
    sufficient: bool = True,
    occupancy: dict[str, Any] | None = None,
    missing: list[str] | None = None,
    spine_empty: bool = True,
    events: list[Any] | None = None,
) -> dict[str, Any]:
    occ = occupancy or {
        "already_placed_today": False,
        "corr_hold_named": False,
        "same_sleeve_reentry": False,
        "new_named_fire": False,
        "minutes_since_flat": 120,
    }
    return {
        "schema": "gtos.judgment.gold_state.v0",
        "as_of_clock": "as_of_open_study",
        "identity": {
            "candidate_id": candidate_id,
            "symbol": symbol,
            "side": side,
            "sleeve": sleeve,
            "origin_organism": "historical_lab",
            "family_class": "study",
        },
        "clock": {"is_friday": False, "rule": "new_york_plus_7", "as_of_utc": "2026-09-09T09:00:00Z"},
        "sessions": {"named": session, "source": "unassembled"},
        "timeframes": {
            "m15": {"tf": "M15", "close_ret_1": close_ret_1, "bars_available": 64},
            "h4": {"tf": "H4", "close_ret_5bar": close_ret_5bar, "bars_available": 40},
            "d1": {"tf": "D1", "bars_available": 20},
        },
        "sleeve_features": {
            "vol_ratio": vol_ratio,
            "htf_slope_norm": htf_slope_norm,
            "mom_20_atr": mom_20_atr,
            "price_vs_sma_frac": sma_frac,
        },
        "geometry": {"atr14": atr14, "atr50": atr50, "compression_ratio_prior_bar": vol_ratio},
        "levels": {"prior_day_high": None, "prior_day_low": None, "source": "unassembled"},
        "news": {
            "spine_empty": spine_empty,
            "source": "unassembled",
            "events": [] if events is None else events,
        },
        "occupancy": occ,
        "completeness": {
            "state_sufficient_for_live": sufficient,
            "missing_fields": missing or [],
        },
    }


def historical_tape_rows() -> list[dict[str, Any]]:
    """≥24 Challenge-true identity rows for offline prove. No live bars."""

    rows: list[dict[str, Any]] = []

    def add(
        tape_id: str,
        sleeve: str,
        symbol: str,
        side: str,
        ticket: str,
        *,
        choice: str,
        conf: float,
        change: float,
        viable: float,
        ret1: float,
        ret5: float,
        vol: float,
        slope: float,
        mom: float,
        sma: float = 0.02,
        session: str = "london",
        occupancy: dict[str, Any] | None = None,
        sufficient: bool = True,
        missing: list[str] | None = None,
        note: str = "",
    ) -> None:
        cid = f"challenge:{CHALLENGE_LOGIN}:{ticket}:{sleeve}:{side}"
        rows.append(
            {
                "tape_id": tape_id,
                "login": CHALLENGE_LOGIN,
                "ns": "operator",
                "magic": 0,
                "note": note,
                "gold_state": gold_state(
                    sleeve=sleeve,
                    symbol=symbol,
                    side=side,
                    candidate_id=cid,
                    close_ret_1=ret1,
                    close_ret_5bar=ret5,
                    vol_ratio=vol,
                    htf_slope_norm=slope,
                    mom_20_atr=mom,
                    sma_frac=sma,
                    session=session,
                    sufficient=sufficient,
                    occupancy=occupancy,
                    missing=missing,
                ),
                "system_one_answers": _answers(choice, conf, change, viable),
            }
        )

    # Directional metals — high conf trend → admit_ok_label under research bars.
    # off_hours is G6 leave-alone so size_factor stays 1.0 (london would snap to 0.5).
    for i, ticket in enumerate(("291072108", "291096187", "s14m01", "s14m02", "s14m03")):
        add(
            f"admit-{i+1:02d}",
            "metals_core",
            "XAUUSD",
            "short" if i % 2 else "long",
            ticket,
            choice="trend_down" if i % 2 else "trend_up",
            conf=0.88,
            change=0.22,
            viable=0.72,
            ret1=0.012 if i % 2 == 0 else -0.013,
            ret5=0.03 if i % 2 == 0 else -0.028,
            vol=1.05,
            slope=0.8 if i % 2 == 0 else -0.8,
            mom=0.6 if i % 2 == 0 else -0.5,
            session="off_hours",
            note="research_admit_ok_label",
        )

    # KEEP spring — high conf, G7 no boost (size stays 1.0, never >1)
    for i, ticket in enumerate(("s14k01", "s14k02", "s14k03")):
        add(
            f"keep-{i+1:02d}",
            "dsp_spring_close",
            "XAUUSD",
            "long",
            ticket,
            choice="trend_up",
            conf=0.90,
            change=0.18,
            viable=0.80,
            ret1=0.009,
            ret5=0.022,
            vol=0.95,
            slope=0.7,
            mom=0.5,
            note="keep_no_boost",
        )

    # extra directional crypto/energy so n_decidable ≥ 20 with favored lists
    add(
        "admit-06",
        "crypto",
        "BTCUSD",
        "long",
        "s14c01",
        choice="trend_up",
        conf=0.86,
        change=0.21,
        viable=0.70,
        ret1=0.011,
        ret5=0.027,
        vol=1.15,
        slope=0.75,
        mom=0.55,
        session="off_hours",
        note="research_admit_ok_label",
    )
    add(
        "admit-07",
        "energy_agri",
        "XAUUSD",
        "short",
        "s14e01",
        choice="trend_down",
        conf=0.87,
        change=0.19,
        viable=0.74,
        ret1=-0.012,
        ret5=-0.03,
        vol=1.08,
        slope=-0.65,
        mom=-0.45,
        session="off_hours",
        note="research_admit_ok_label",
    )
    # G6 London cut: same metals_core high-conf as admit-01, but size snaps 1.0 → 0.5
    add(
        "g6-london-snap",
        "metals_core",
        "XAUUSD",
        "long",
        "s14g6",
        choice="trend_up",
        conf=0.88,
        change=0.22,
        viable=0.72,
        ret1=0.012,
        ret5=0.03,
        vol=1.05,
        slope=0.8,
        mom=0.6,
        session="london",
        note="g6_session_cut_snaps_to_half_size",
    )
    add(
        "half-00",
        "sub_xvol_pullback",
        "XAUUSD",
        "long",
        "s14x01",
        choice="range",
        conf=0.58,
        change=0.28,
        viable=0.61,
        ret1=0.002,
        ret5=-0.001,
        vol=0.65,
        slope=0.02,
        mom=-0.03,
        sma=0.0,
        note="half_size_tilt_candidate",
    )

    # vss range — MED conf → half_size under research bars
    for i, ticket in enumerate(("291087142", "s14v01", "s14v02", "s14v03")):
        add(
            f"half-{i+1:02d}",
            "vss_fxcross_london_up_low",
            "EURGBP",
            "sell",
            ticket,
            choice="range",
            conf=0.62,
            change=0.30,
            viable=0.66,
            ret1=0.001,
            ret5=-0.002,
            vol=0.85,
            slope=0.05,
            mom=-0.04,
            sma=0.0,
            note="half_size_tilt_candidate",
        )

    # stand_down: low viable / chop / change
    add(
        "down-01",
        "metals_core",
        "XAUUSD",
        "long",
        "s14d01",
        choice="chop",
        conf=0.70,
        change=0.25,
        viable=0.20,
        ret1=0.03,
        ret5=-0.04,
        vol=2.4,
        slope=0.1,
        mom=-0.2,
        note="viable_below_floor",
    )
    add(
        "down-02",
        "metals_core",
        "XAUUSD",
        "short",
        "s14d02",
        choice="trend_up",
        conf=0.80,
        change=0.78,
        viable=0.70,
        ret1=0.006,
        ret5=0.01,
        vol=1.6,
        slope=0.2,
        mom=0.1,
        note="regime_change_ceiling",
    )
    add(
        "down-03",
        "crypto",
        "BTCUSD",
        "long",
        "s14d03",
        choice="range",
        conf=0.77,
        change=0.20,
        viable=0.65,
        ret1=0.0,
        ret5=0.001,
        vol=1.1,
        slope=0.0,
        mom=0.0,
        note="regime_not_favored",
    )
    add(
        "down-04",
        "energy_agri",
        "XAUUSD",
        "long",
        "s14d04",
        choice="chop",
        conf=0.55,
        change=0.40,
        viable=0.55,
        ret1=-0.025,
        ret5=0.03,
        vol=2.2,
        slope=-0.1,
        mom=0.3,
        note="chop_not_favored",
    )

    # Hard-offs — even if answers say trend_up / high conf / viable
    add(
        "hoff-xa",
        "xa_huge_20_extreme",
        "EURUSD",
        "buy",
        "291076386",
        choice="trend_up",
        conf=0.92,
        change=0.10,
        viable=0.90,
        ret1=0.008,
        ret5=0.02,
        vol=1.0,
        slope=0.6,
        mom=0.4,
        note="xa_huge_hard_off",
    )
    add(
        "hoff-idx",
        "idxrev",
        "UK100.cash",
        "sell",
        "s14idx",
        choice="trend_down",
        conf=0.91,
        change=0.12,
        viable=0.88,
        ret1=-0.01,
        ret5=-0.025,
        vol=1.1,
        slope=-0.7,
        mom=-0.4,
        note="index_idxrev_hard_off",
    )
    add(
        "hoff-orb",
        "orb_crypto_london",
        "ETHUSD",
        "buy",
        "s14orb",
        choice="trend_up",
        conf=0.89,
        change=0.15,
        viable=0.84,
        ret1=0.015,
        ret5=0.04,
        vol=1.4,
        slope=0.9,
        mom=0.7,
        note="orb_crypto_hard_off",
    )
    add(
        "hoff-us30",
        "dsp_walked_hi",
        "US30.cash",
        "buy",
        "291113462",
        choice="trend_up",
        conf=0.86,
        change=0.20,
        viable=0.70,
        ret1=0.007,
        ret5=0.018,
        vol=1.2,
        slope=0.5,
        mom=0.3,
        note="us30_symbol_hard_off",
    )
    add(
        "hoff-bleed",
        "dsp_bleed_acc",
        "XAUUSD",
        "short",
        "s14bl",
        choice="trend_down",
        conf=0.87,
        change=0.11,
        viable=0.75,
        ret1=-0.009,
        ret5=-0.02,
        vol=1.0,
        slope=-0.6,
        mom=-0.4,
        note="bleed_hard_off",
    )

    # G8 reentry
    add(
        "g8-01",
        "metals_core",
        "XAUUSD",
        "long",
        "s14g8",
        choice="trend_up",
        conf=0.90,
        change=0.15,
        viable=0.80,
        ret1=0.01,
        ret5=0.02,
        vol=1.0,
        slope=0.7,
        mom=0.5,
        occupancy={
            "already_placed_today": True,
            "same_sleeve_reentry": True,
            "new_named_fire": False,
            "minutes_since_flat": 4,
            "corr_hold_named": False,
        },
        note="g8_block_reentry",
    )

    # incomplete — not decidable
    add(
        "inc-01",
        "metals_core",
        "XAUUSD",
        "long",
        "s14inc",
        choice="trend_up",
        conf=0.90,
        change=0.10,
        viable=0.80,
        ret1=0.01,
        ret5=0.02,
        vol=1.0,
        slope=0.5,
        mom=0.4,
        sufficient=False,
        missing=["timeframes", "sleeve_features"],
        note="incomplete_not_decidable",
    )

    # missing favored sleeve
    add(
        "fav-miss",
        "unknown_sleeve",
        "XAUUSD",
        "long",
        "s14nf",
        choice="trend_up",
        conf=0.90,
        change=0.10,
        viable=0.80,
        ret1=0.01,
        ret5=0.02,
        vol=1.0,
        slope=0.5,
        mom=0.4,
        note="favored_missing_fail_closed",
    )

    # cache-duplicate of admit-01 (same buckets/identity sleeve+symbol+side+features)
    rows.append(
        {
            "tape_id": "cache-dup-admit-01",
            "login": CHALLENGE_LOGIN,
            "ns": "operator",
            "magic": 0,
            "note": "identical_bucket_state_cache_hit",
            "gold_state": rows[0]["gold_state"],
            "system_one_answers": rows[0]["system_one_answers"],
        }
    )
    return rows
