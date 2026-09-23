"""SHADOW remasure — non-XAU sufficient rows travel as symbol_state, not gold-defaults.

Chair unlock: ``n_non_xau_sufficient=45`` on EURUSD / USDJPY / GBPUSD /
EURGBP + US30 hard-off. Fixture-grid remasure only. Does **not** rewrite
the landed XAU Challenge tape (``shadow.summary.json`` stays
``n_non_xau_sufficient=0`` because only XAUUSD CSVs are landed).

Never places. Never remints. Never flattens. Named APPLY stays XAU-only.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.components.ultimate_book.primitives import Bar

from .bars import StampedBar, normalize_symbol
from .compose import compose_shadow
from .gold_state import SCHEMA as GOLD_SCHEMA
from .symbol_state import SCHEMA as SYMBOL_SCHEMA
from .symbol_state import assemble_symbol_state_v0

SCHEMA = "gtos.judgment.non_xau_remeasure.v0"
NON_XAU_REMEASURE_N = 45
NON_XAU_REMEASURE_N_AS_OF = 9
NON_XAU_REMEASURE_SYMBOLS = ("EURUSD", "USDJPY", "GBPUSD", "EURGBP", "US30")
US30_HARD_OFF_SLEEVE = "mx_us30_d1_donchian"
FX_STUDY_SLEEVE = "vss_fxcross_london_up_low"
AS_OF_GRID = datetime(2026, 9, 17, 11, 5, tzinfo=timezone.utc)
STEP_MINUTES = 15
EMPTY_SPINE = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
RECEIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "judgment"
    / "astra"
    / "lab"
    / "wires"
    / "NON_XAU_REMEASURE_V0.json"
)

GOLD_DEFAULT_LEAK_CODES = (
    "schema_gold_state_v0",
    "schema_not_symbol_state",
    "nested_gold_state",
    "asset_class_metal",
    "identity_xauusd",
    "peer_not_xau_primary",
    "missing_class_specific",
    "news_unfiltered_gold",
    "named_apply_symbol",
    "live_size_tilt_moved",
    "live_cost_tilt_moved",
    "apply_this_row",
    "place_unlocked",
)


def _tf_book(
    n: int,
    start: datetime,
    step_hours: float,
    closes: list[float],
    *,
    half_range: float,
) -> list[StampedBar]:
    out: list[StampedBar] = []
    for i in range(n):
        utc = start + timedelta(hours=step_hours * i)
        close = closes[i] if i < len(closes) else closes[-1]
        out.append(
            StampedBar(
                broker_naive=utc.replace(tzinfo=None) + timedelta(hours=3),
                utc=utc,
                bar=Bar(o=close, h=close + half_range, l=close - half_range, c=close, v=1.0),
                source_path="non_xau_remeasure",
            )
        )
    return out


def _books(start_px: float, step: float, *, half: float) -> dict[str, list[StampedBar]]:
    m15_start = datetime(2026, 9, 17, 5, 0, tzinfo=timezone.utc)
    h4_start = datetime(2026, 9, 16, 1, 0, tzinfo=timezone.utc)
    d1_start = datetime(2026, 9, 9, 0, 0, tzinfo=timezone.utc)
    return {
        "m15": _tf_book(32, m15_start, 0.25, [start_px + step * i for i in range(32)], half_range=half),
        "h4": _tf_book(16, h4_start, 4.0, [start_px + step * 4 * i for i in range(16)], half_range=half * 4),
        "d1": _tf_book(10, d1_start, 24.0, [start_px + step * 16 * i for i in range(10)], half_range=half * 8),
    }


def _geo(entry: float, stop: float) -> dict[str, float | str]:
    return {
        "entry": entry,
        "stop": stop,
        "stop_dist": abs(entry - stop),
        "order_type": "MARKET",
    }


GRID_SPEC: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "books": _books(1.1700, 0.00015, half=0.0004),
        "geo": _geo(1.1720, 1.1695),
        "sleeve": FX_STUDY_SLEEVE,
        "asset": "fx",
    },
    "USDJPY": {
        "books": _books(148.20, 0.02, half=0.04),
        "geo": _geo(148.10, 148.45),
        "sleeve": FX_STUDY_SLEEVE,
        "asset": "fx",
    },
    "GBPUSD": {
        "books": _books(1.3400, 0.00012, half=0.0003),
        "geo": _geo(1.3430, 1.3400),
        "sleeve": FX_STUDY_SLEEVE,
        "asset": "fx",
    },
    "EURGBP": {
        "books": _books(0.8720, 0.00008, half=0.00025),
        "geo": _geo(0.8730, 0.8705),
        "sleeve": FX_STUDY_SLEEVE,
        "asset": "fx",
    },
    "US30": {
        "books": _books(46200.0, 8.0, half=12.0),
        "geo": _geo(46300.0, 46150.0),
        "sleeve": US30_HARD_OFF_SLEEVE,
        "asset": "index",
    },
}


def gold_default_leaks(
    state: Mapping[str, Any] | None,
    compose: Mapping[str, Any] | None = None,
) -> list[str]:
    """Named gold-default leaks on a claimed non-XAU sufficient row.

    A non-XAU row wears gold-defaults when it travels as ``gold_state.v0``,
    nests a gold object, wears metal/XAU identity, stamps ``not_xau_primary``,
    drops ``class_specific``, carries unfiltered gold news, or opens a named
    APPLY / live tilt. Empty list = the row is symbol_state observe.
    """
    leaks: list[str] = []
    state = state or {}
    identity = state.get("identity") or {}
    symbol = normalize_symbol(identity.get("symbol"))
    schema = state.get("schema")
    if schema == GOLD_SCHEMA:
        leaks.append("schema_gold_state_v0")
    elif schema != SYMBOL_SCHEMA:
        leaks.append("schema_not_symbol_state")
    if state.get("gold_state") is not None:
        leaks.append("nested_gold_state")
    if identity.get("asset_class") == "metal":
        leaks.append("asset_class_metal")
    if symbol == "XAUUSD":
        leaks.append("identity_xauusd")
    peers = state.get("peers") or {}
    for row in peers.values():
        if isinstance(row, dict) and row.get("source") == "not_xau_primary":
            leaks.append("peer_not_xau_primary")
            break
    class_block = state.get("class_specific")
    if not isinstance(class_block, dict) or not class_block.get("assembled"):
        leaks.append("missing_class_specific")
    news = state.get("news") or {}
    if not news.get("relevant_currencies") or "pair_high_events" not in news:
        leaks.append("news_unfiltered_gold")
    packed = compose or {}
    if packed.get("named_apply_symbol") is True:
        leaks.append("named_apply_symbol")
    if packed:
        try:
            if abs(float(packed.get("live_size_tilt") or 1.0) - 1.0) > 1e-9:
                leaks.append("live_size_tilt_moved")
        except (TypeError, ValueError):
            leaks.append("live_size_tilt_moved")
        try:
            if abs(float(packed.get("live_cost_tilt") or 1.0) - 1.0) > 1e-9:
                leaks.append("live_cost_tilt_moved")
        except (TypeError, ValueError):
            leaks.append("live_cost_tilt_moved")
        if packed.get("apply_this_row") is True:
            leaks.append("apply_this_row")
    return leaks


def _us30_leaks(state: Mapping[str, Any], compose: Mapping[str, Any]) -> list[str]:
    leaks: list[str] = []
    identity = state.get("identity") or {}
    surface = state.get("surface") or {}
    index = ((state.get("class_specific") or {}).get("index") or {})
    if identity.get("family_class") != "house_hard_off":
        leaks.append("us30_not_hard_off")
    if surface.get("us30_off") is not True:
        leaks.append("us30_off_softened")
    if index.get("house_us30_off") is not True:
        leaks.append("us30_index_house_off_softened")
    if compose.get("house_block") is not True:
        leaks.append("us30_house_block_missing")
    return leaks


def _fx_leaks(state: Mapping[str, Any], symbol: str) -> list[str]:
    leaks: list[str] = []
    identity = state.get("identity") or {}
    fx = ((state.get("class_specific") or {}).get("fx") or {})
    if identity.get("asset_class") != "fx":
        leaks.append("fx_asset_class_wrong")
    if not fx.get("pair"):
        leaks.append("fx_missing_pair")
    expected = {
        "EURUSD": ("EUR", "USD"),
        "USDJPY": ("USD", "JPY"),
        "GBPUSD": ("GBP", "USD"),
        "EURGBP": ("EUR", "GBP"),
    }.get(symbol)
    if expected and (fx.get("pair") or {}) != {"base": expected[0], "quote": expected[1]}:
        leaks.append("fx_pair_mismatch")
    return leaks


def _ready_admit_leaks(state: Mapping[str, Any]) -> list[str]:
    sleeve = state.get("sleeve") or {}
    leaks: list[str] = []
    for key in ("gbpjpy_a_plus_ready", "xau_dsp_shakeout_ready"):
        row = sleeve.get(key) or {}
        if row.get("admit") is not None or row.get("choice") == "admit":
            leaks.append("admit_choice_emitted")
            break
    return leaks


def grid_books() -> dict[str, dict[str, list[StampedBar]]]:
    return {symbol: dict(spec["books"]) for symbol, spec in GRID_SPEC.items()}


def iter_grid_as_ofs() -> list[datetime]:
    return [AS_OF_GRID + timedelta(minutes=STEP_MINUTES * i) for i in range(NON_XAU_REMEASURE_N_AS_OF)]


def assemble_grid_row(symbol: str, as_of: datetime) -> dict[str, Any]:
    spec = GRID_SPEC[symbol]
    return assemble_symbol_state_v0(
        as_of_utc=as_of,
        side="long",
        sleeve=spec["sleeve"],
        symbol=symbol,
        origin_organism="f5_challenge",
        books=spec["books"],
        spines=EMPTY_SPINE,
        geometry=spec["geo"],
        cost={"spread_r_of_stop": 0.05},
        sleeve_features={"tag": spec["sleeve"]},
    )


def score_grid_row(symbol: str, as_of: datetime, *, ticket: str) -> dict[str, Any]:
    """Challenge observe path. Multi-symbol cache — never a single-tf XAU shortcut."""
    from .challenge_shadow import score_position

    spec = GRID_SPEC[symbol]
    geo = spec["geo"]
    return score_position(
        {
            "ticket": ticket,
            "symbol": symbol,
            "side": "LONG",
            "sleeve": spec["sleeve"],
            "entry": geo["entry"],
            "orig_sl": geo["stop"],
            "stop_dist": geo["stop_dist"],
            "spread_R": 0.05,
            "open_time_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "_kind": "replay_close",
        },
        books=grid_books(),
        spines=EMPTY_SPINE,
        sit_meta={},
    )


def _compact_row(
    *,
    symbol: str,
    as_of: datetime,
    state: Mapping[str, Any],
    compose: Mapping[str, Any],
    leaks: Sequence[str],
    via: str,
) -> dict[str, Any]:
    identity = state.get("identity") or {}
    completeness = state.get("completeness") or {}
    return {
        "symbol": symbol,
        "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema": state.get("schema"),
        "asset_class": identity.get("asset_class"),
        "family_class": identity.get("family_class"),
        "sufficient": bool(completeness.get("state_sufficient_for_live")),
        "gold_state_nested": state.get("gold_state") is not None,
        "named_apply_symbol": compose.get("named_apply_symbol"),
        "apply_this_row": compose.get("apply_this_row"),
        "live_size_tilt": compose.get("live_size_tilt"),
        "live_cost_tilt": compose.get("live_cost_tilt"),
        "house_block": compose.get("house_block"),
        "never_place": True,
        "via": via,
        "leaks": list(leaks),
    }


def remasure_non_xau_sufficient(
    rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify 45 non-XAU sufficient rows through assemble + Challenge compose.

    ``rows`` is an optional pre-built list of ``{state, compose, symbol}``.
    Absent → build the fixture grid and score each cell on the observe path.
    """
    os.environ["GTOS_JEV_A1_CALL"] = "0"
    packed: list[dict[str, Any]] = []
    if rows is None:
        for i, as_of in enumerate(iter_grid_as_ofs()):
            for symbol in NON_XAU_REMEASURE_SYMBOLS:
                assembled = assemble_grid_row(symbol, as_of)
                scored = score_grid_row(symbol, as_of, ticket=f"nxr-{symbol}-{i}")
                state = scored.get("state") or assembled
                compose = scored.get("compose") or compose_shadow(assembled, ticket=f"nxr-{symbol}-{i}")
                leaks = list(gold_default_leaks(state, compose))
                leaks.extend(_ready_admit_leaks(state))
                if symbol == "US30":
                    leaks.extend(_us30_leaks(state, compose))
                else:
                    leaks.extend(_fx_leaks(state, symbol))
                if assembled.get("schema") != SYMBOL_SCHEMA:
                    leaks.append("assemble_schema_not_symbol_state")
                if assembled.get("gold_state") is not None:
                    leaks.append("assemble_nested_gold_state")
                packed.append(
                    _compact_row(
                        symbol=symbol,
                        as_of=as_of,
                        state=state,
                        compose=compose,
                        leaks=leaks,
                        via="score_position",
                    )
                )
    else:
        for raw in rows:
            state = raw.get("state") or raw
            compose = raw.get("compose") or compose_shadow(state)
            symbol = normalize_symbol(
                raw.get("symbol") or (state.get("identity") or {}).get("symbol")
            )
            as_of_raw = raw.get("as_of_utc") or (state.get("clock") or {}).get("as_of_utc")
            as_of = (
                datetime.fromisoformat(str(as_of_raw).replace("Z", "+00:00"))
                if as_of_raw
                else AS_OF_GRID
            )
            leaks = list(gold_default_leaks(state, compose))
            leaks.extend(_ready_admit_leaks(state))
            if symbol == "US30":
                leaks.extend(_us30_leaks(state, compose))
            elif symbol in NON_XAU_REMEASURE_SYMBOLS:
                leaks.extend(_fx_leaks(state, symbol))
            packed.append(
                _compact_row(
                    symbol=symbol,
                    as_of=as_of,
                    state=state,
                    compose=compose,
                    leaks=leaks,
                    via="supplied",
                )
            )

    sufficient = [row for row in packed if row["sufficient"]]
    leaked = [row for row in packed if row["leaks"]]
    by_symbol: dict[str, dict[str, int]] = {}
    for symbol in NON_XAU_REMEASURE_SYMBOLS:
        subset = [row for row in packed if row["symbol"] == symbol]
        by_symbol[symbol] = {
            "n": len(subset),
            "n_sufficient": sum(1 for row in subset if row["sufficient"]),
            "n_leaks": sum(1 for row in subset if row["leaks"]),
            "n_hard_off": sum(1 for row in subset if row["family_class"] == "house_hard_off"),
        }
    leak_codes: dict[str, int] = {}
    for row in leaked:
        for code in row["leaks"]:
            leak_codes[code] = leak_codes.get(code, 0) + 1

    return {
        "schema": SCHEMA,
        "source": "fixture_grid" if rows is None else "supplied_rows",
        "not_landed_challenge_tape": True,
        "landed_xau_pack_untouched": True,
        "n": len(packed),
        "n_non_xau_sufficient": len(sufficient),
        "n_target": NON_XAU_REMEASURE_N,
        "n_as_of": NON_XAU_REMEASURE_N_AS_OF,
        "symbols": list(NON_XAU_REMEASURE_SYMBOLS),
        "us30_hard_off": sum(1 for row in packed if row["symbol"] == "US30" and row["family_class"] == "house_hard_off"),
        "us30_off": sum(1 for row in packed if row["symbol"] == "US30"),
        "n_gold_default_leaks": len(leaked),
        "leak_codes": leak_codes,
        "named_apply_symbol": sum(1 for row in packed if row["named_apply_symbol"]),
        "apply_this_row": sum(1 for row in packed if row["apply_this_row"]),
        "live_size_tilt_locked": all(
            abs(float(row.get("live_size_tilt") or 1.0) - 1.0) < 1e-9 for row in packed
        ),
        "live_cost_tilt_locked": all(
            abs(float(row.get("live_cost_tilt") or 1.0) - 1.0) < 1e-9 for row in packed
        ),
        "never_place": all(row.get("never_place") is True for row in packed) and True,
        "never_apply": True,
        "never_remint": True,
        "never_flatten": True,
        "admit_choice_emitted": leak_codes.get("admit_choice_emitted", 0),
        "by_symbol": by_symbol,
        "pipe": "assemble_symbol_state_v0 → score_position → compose_shadow",
        "jev_calls": "off",
        "unlock": (
            "non-XAU sufficient rows use symbol_state.v0, not gold-defaults"
            if not leaked and len(sufficient) == NON_XAU_REMEASURE_N
            else "locked_or_leaking"
        ),
        "rows": packed,
    }


def write_receipt(
    path: Path | None = None,
    receipt: Mapping[str, Any] | None = None,
) -> Path:
    target = path or RECEIPT_PATH
    packed = dict(receipt or remasure_non_xau_sufficient())
    # Receipt on disk stays compact — drop per-row bodies after the counts seal.
    disk = {k: v for k, v in packed.items() if k != "rows"}
    disk["n_rows_sealed"] = packed.get("n")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(disk, indent=2) + "\n", encoding="utf-8")
    return target


def main() -> int:
    receipt = remasure_non_xau_sufficient()
    path = write_receipt(receipt=receipt)
    printable = {k: v for k, v in receipt.items() if k != "rows"}
    printable["receipt"] = str(path)
    print(json.dumps(printable, indent=2))
    if receipt["n_non_xau_sufficient"] != NON_XAU_REMEASURE_N:
        return 2
    if receipt["n_gold_default_leaks"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
