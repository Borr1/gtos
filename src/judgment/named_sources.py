"""Named on-disk sources for rates / DXY / funding research.

Does not fetch. Does not invent NEWS_PROTOCOL, FRED, or X endpoints.
A missing file stays missing. A present-but-wrong file stays rejected.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

DXY_ABSENT_REASON = "no_dxy_csv_on_this_clone"
DXY_REJECTED_REASON = "dxy_csv_present_but_not_ice_dxy"
YIELD_ABSENT_REASON = "no_named_yield_tape_on_this_clone"
FUNDING_ABSENT_REASON = "no_named_funding_stress_feed_on_this_clone"
SIERRA_ZN_CONTROL_THIN = "sierra_zn_control_present_but_thin_not_challenge_true"
SIERRA_VIX_CONTROL_THIN = "sierra_vxm_control_present_but_thin_not_funding"

# ICE Dollar Index lives near 100. This clone's data/DXY_D1.csv prints ~25.
ICE_DXY_LOW = 70.0
ICE_DXY_HIGH = 130.0

DEFAULT_DXY_PATH = REPO_ROOT / "data" / "DXY_D1.csv"
CHALLENGE_DIR = REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917"
CHALLENGE_MULTI = CHALLENGE_DIR / "multi"
HIST_2026 = REPO_ROOT / "data" / "historical_2026"
HIST = REPO_ROOT / "data" / "historical"
HIST_2223 = REPO_ROOT / "data" / "historical_2022_2023"
SIERRA_BOUNDED = (
    REPO_ROOT
    / "data"
    / "sierra_ohlcv_roots"
    / "sierra_first_wave_bounded_conversion_20260504"
)

USD_PROXY_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY")
RISK_PROXY_SYMBOLS = ("NAS100", "US30", "UK100")
CROSS_FX_SYMBOLS = ("EURGBP", "GBPJPY")
QUOTE_USD_INVERT = frozenset({"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"})
BASE_USD_DIRECT = frozenset({"USDJPY", "USDCHF", "USDCAD"})
YIELD_PRICE_INVERSE = frozenset({"ZN", "ZB", "ZF", "ZT"})

# Named files we will *look for*. Absence is a repair item, not an HTTP client.
YIELD_CANDIDATE_PATHS = (
    REPO_ROOT / "data" / "US10Y_D1.csv",
    REPO_ROOT / "data" / "TNX_D1.csv",
    REPO_ROOT / "data" / "DGS10.csv",
    REPO_ROOT / "data" / "DGS2.csv",
    HIST_2026 / "US10Y_D1.csv",
    HIST / "US10Y_D1.csv",
)
FUNDING_CANDIDATE_PATHS = (
    REPO_ROOT / "data" / "TED.csv",
    REPO_ROOT / "data" / "SOFR.csv",
    REPO_ROOT / "data" / "FRA_OIS.csv",
    REPO_ROOT / "data" / "VIXCLS.csv",
    REPO_ROOT / "data" / "fred" / "TED.csv",
    REPO_ROOT / "data" / "fred" / "SOFR.csv",
)
NEWS_SPINE_PATHS = (
    REPO_ROOT / "data" / "news_calendar.json",
    REPO_ROOT / "data" / "news" / "f5_high_calendar_host_20260916.json",
    REPO_ROOT / "data" / "news" / "high_spine_ff_thisweek_20260917.json",
    REPO_ROOT / "data" / "news" / "ff_thisweek_raw_20260917.json",
    REPO_ROOT / "data" / "news" / "news_calendar_f5_synced_from_spine.json",
)
HOST_EVENTS_PATH = CHALLENGE_DIR / "events_since_20260915.jsonl"
NEWS_PROTOCOL_CANDIDATES = (
    REPO_ROOT / "NEWS_PROTOCOL.md",
    REPO_ROOT / "judgment" / "NEWS_PROTOCOL.md",
    REPO_ROOT / ".context" / "00_core" / "NEWS_PROTOCOL.md",
)
DESK_BRIEF_CANDIDATES = (
    REPO_ROOT / "data" / "desk_briefs.json",
    REPO_ROOT / "judgment" / "astra" / "lab" / "desk_briefs.json",
)

_FILE_STEM = {"US30": "US30_cash", "UK100": "UK100_cash"}


def _rel(path: Path) -> str:
    if path.is_relative_to(REPO_ROOT):
        return str(path.relative_to(REPO_ROOT))
    return str(path)


def _exists(path: Path) -> bool:
    return path.is_file()


def _csv_preview(path: Path, *, max_rows: int = 4) -> dict[str, Any]:
    if not path.is_file():
        return {"present": False, "path": _rel(path), "n_rows": 0}
    n = 0
    first = last = header = None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            n += 1
            if first is None:
                first = row[0]
            last = row[0]
    return {
        "present": True,
        "path": _rel(path),
        "n_rows": n,
        "header0": None if not header else header[0],
        "first": first,
        "last": last,
        "preview_capped": n > max_rows,
    }


def file_stem_for(symbol: str) -> str:
    return _FILE_STEM.get(symbol, symbol)


def usd_return_for_pair(symbol: str, ret: float | None) -> float | None:
    """Map a pair return onto USD. + = USD stronger. None if pair is not a USD proxy."""
    if ret is None:
        return None
    sym = (symbol or "").strip().upper().replace("/", "").replace(".", "_")
    if sym.endswith("_CASH"):
        sym = sym[: -len("_CASH")]
    if sym in QUOTE_USD_INVERT:
        return -ret
    if sym in BASE_USD_DIRECT:
        return ret
    return None


def inspect_dxy_csv(path: Path | None = None) -> dict[str, Any]:
    """Quality gate for a named DXY file. Never rescale. Never invent ICE DXY."""
    dest = path if path is not None else DEFAULT_DXY_PATH
    if not dest.is_file():
        return {
            "file_present": False,
            "path": _rel(dest),
            "series": None,
            "usable_as_ice_dxy": False,
            "source": "unassembled",
            "reason": DXY_ABSENT_REASON,
            "last_close": None,
            "n_rows": 0,
            "first": None,
            "last": None,
            "ice_band": [ICE_DXY_LOW, ICE_DXY_HIGH],
            "challenge_true": False,
        }
    closes: list[float] = []
    first = last = None
    with dest.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stamp = (row.get("time") or row.get("time_utc") or "").strip()
            raw = row.get("close") or row.get("Close")
            if raw is None or raw == "":
                continue
            try:
                close = float(raw)
            except (TypeError, ValueError):
                continue
            closes.append(close)
            if first is None:
                first = stamp
            last = stamp
    last_close = closes[-1] if closes else None
    usable = bool(
        last_close is not None and ICE_DXY_LOW <= last_close <= ICE_DXY_HIGH
    )
    reason = None if usable else DXY_REJECTED_REASON
    return {
        "file_present": True,
        "path": _rel(dest),
        "series": None,
        "usable_as_ice_dxy": usable,
        "source": "named_dxy_csv" if usable else "unassembled",
        "reason": reason,
        "last_close": last_close,
        "n_rows": len(closes),
        "first": first,
        "last": last,
        "ice_band": [ICE_DXY_LOW, ICE_DXY_HIGH],
        "challenge_true": False,
        "note": (
            None
            if usable
            else "Prints outside ICE DXY band. Do not rescale. Do not treat as USD impulse."
        ),
    }


def _tf_row(directory: Path, symbol: str, tf: str) -> dict[str, Any]:
    stem = file_stem_for(symbol)
    path = directory / f"{stem}_{tf}.csv"
    preview = _csv_preview(path)
    preview["symbol"] = symbol
    preview["tf"] = tf
    return preview


def _symbol_tfs(directory: Path, symbol: str, tfs: tuple[str, ...] = ("D1", "H4", "M15")) -> dict[str, Any]:
    rows = {tf.lower(): _tf_row(directory, symbol, tf) for tf in tfs}
    present = [tf for tf, row in rows.items() if row["present"]]
    return {
        "symbol": symbol,
        "directory": _rel(directory) if directory.exists() else _rel(directory),
        "present_tfs": present,
        "any": bool(present),
        "tfs": rows,
    }


def named_source_inventory() -> dict[str, Any]:
    """Disk truth. Challenge-true vs lab vs absent. No network."""
    challenge_xau = {
        tf.lower(): _csv_preview(CHALLENGE_DIR / f"XAUUSD_{tf}.csv")
        for tf in ("M15", "H4", "D1")
    }
    challenge_multi = {
        symbol: _symbol_tfs(CHALLENGE_MULTI, symbol)
        for symbol in USD_PROXY_SYMBOLS + RISK_PROXY_SYMBOLS
    }
    challenge_cross_fx = {
        symbol: _symbol_tfs(CHALLENGE_MULTI, symbol)
        for symbol in CROSS_FX_SYMBOLS
    }
    multi_any_landed = any(
        row.get("any")
        for row in list(challenge_multi.values()) + list(challenge_cross_fx.values())
    )
    lab_2026 = {
        symbol: _symbol_tfs(HIST_2026, symbol)
        for symbol in USD_PROXY_SYMBOLS + RISK_PROXY_SYMBOLS + ("XAGUSD",)
    }
    sierra_zn = _csv_preview(SIERRA_BOUNDED / "ZN_CONTROL_D1.csv")
    sierra_zn["allowed_use"] = "rates_liquidity_control_only"
    sierra_zn["challenge_true"] = False
    sierra_zn["reason"] = SIERRA_ZN_CONTROL_THIN if sierra_zn["present"] else YIELD_ABSENT_REASON
    sierra_vix = _csv_preview(SIERRA_BOUNDED / "VIX_VXM_D1.csv")
    sierra_vix["allowed_use"] = "volatility_control_only"
    sierra_vix["challenge_true"] = False
    sierra_vix["reason"] = SIERRA_VIX_CONTROL_THIN if sierra_vix["present"] else FUNDING_ABSENT_REASON

    yield_hits = [_rel(p) for p in YIELD_CANDIDATE_PATHS if _exists(p)]
    funding_hits = [_rel(p) for p in FUNDING_CANDIDATE_PATHS if _exists(p)]
    news = [{ "path": _rel(p), "present": _exists(p)} for p in NEWS_SPINE_PATHS]
    protocol = [ _rel(p) for p in NEWS_PROTOCOL_CANDIDATES if _exists(p)]
    briefs = [ _rel(p) for p in DESK_BRIEF_CANDIDATES if _exists(p)]

    dxy = inspect_dxy_csv()
    return {
        "schema": "gtos.judgment.named_sources.v0",
        "never_invent_endpoints": True,
        "never_invent_news_protocol": True,
        "challenge_true": {
            "xau": challenge_xau,
            "multi_fx_index": challenge_multi,
            "cross_fx": challenge_cross_fx,
            "multi_dir_exists": CHALLENGE_MULTI.is_dir(),
            "multi_any_landed": multi_any_landed,
            "host_events": {
                "path": _rel(HOST_EVENTS_PATH),
                "present": _exists(HOST_EVENTS_PATH),
            },
            "news_spines": news,
        },
        "lab_only": {
            "historical_2026": lab_2026,
            "historical_has_gbpusd": _exists(HIST / "GBPUSD_D1.csv"),
            "historical_has_usdjpy": _exists(HIST / "USDJPY_D1.csv"),
            "historical_has_us30": _exists(HIST / "US30_cash_D1.csv"),
            "historical_2022_2023_nas100": _exists(HIST_2223 / "NAS100_D1.csv"),
            "note": (
                "April/2025-10..2026-04 broker CSVs. Not Challenge-true. "
                "Do not score a September Challenge as-of on these tapes."
            ),
        },
        "dxy": dxy,
        "rates": {
            "named_yield_csvs": yield_hits,
            "sierra_zn_control_d1": sierra_zn,
            "assembled_as_challenge_true": False,
        },
        "funding": {
            "named_funding_csvs": funding_hits,
            "sierra_vxm_control_d1": sierra_vix,
            "fred_cache_dir": {
                "path": "data/fred",
                "present": (REPO_ROOT / "data" / "fred").is_dir(),
            },
            "assembled_as_challenge_true": False,
        },
        "forbidden_absent": {
            "NEWS_PROTOCOL": protocol,
            "desk_briefs": briefs,
            "MAC_INGEST": False,
        },
        "repair_items": _repair_items(
            challenge_multi=challenge_multi,
            dxy=dxy,
            yield_hits=yield_hits,
            funding_hits=funding_hits,
            sierra_zn=sierra_zn,
            protocol=protocol,
        ),
    }


def _repair_items(
    *,
    challenge_multi: dict[str, Any],
    dxy: dict[str, Any],
    yield_hits: list[str],
    funding_hits: list[str],
    sierra_zn: dict[str, Any],
    protocol: list[str],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    missing_multi = [sym for sym, row in challenge_multi.items() if not row.get("any")]
    if missing_multi:
        items.append(
            {
                "id": "land_challenge_multi_fx_index",
                "blocked": ",".join(missing_multi),
                "repair": (
                    "Land Challenge-true EURUSD/GBPUSD/USDJPY/NAS100/US30/UK100 "
                    "M15+H4 into judgment/astra/lab/challenge_shadow_20260917/multi/. "
                    "Do not promote data/historical_2026 April files."
                ),
            }
        )
    if dxy.get("file_present") and not dxy.get("usable_as_ice_dxy"):
        items.append(
            {
                "id": "replace_mislabeled_dxy",
                "blocked": dxy.get("path") or "data/DXY_D1.csv",
                "repair": (
                    "Replace data/DXY_D1.csv with a named ICE DXY series in the "
                    f"{ICE_DXY_LOW}-{ICE_DXY_HIGH} band, or delete the ~25 print. "
                    "Do not invent a ×4 rescale."
                ),
            }
        )
    elif not dxy.get("file_present"):
        items.append(
            {
                "id": "ingest_ice_dxy",
                "blocked": "usd.dxy",
                "repair": "Ingest a named ICE DXY D1 CSV with clock + source path.",
            }
        )
    if not yield_hits:
        items.append(
            {
                "id": "ingest_named_yield",
                "blocked": "rates_impulse",
                "repair": (
                    "Ingest named US10Y / TNX / DGS10 with publication clock. "
                    "Sierra ZN_CONTROL_D1 is 3 April days, control_only — not enough."
                ),
            }
        )
    if sierra_zn.get("present") and int(sierra_zn.get("n_rows") or 0) < 20:
        items.append(
            {
                "id": "extend_sierra_zn_or_leave_control",
                "blocked": sierra_zn.get("path") or "ZN_CONTROL_D1",
                "repair": (
                    "Either extend ZN beyond the 2026-04-15..17 bounded conversion "
                    "and join the Challenge clock, or leave rates_impulse null. "
                    "Owner must promote control_only before it is a rates print."
                ),
            }
        )
    if not funding_hits:
        items.append(
            {
                "id": "ingest_funding_stress_feed",
                "blocked": "funding_stress",
                "repair": (
                    "Named TED / SOFR / FRA-OIS (publication-time metadata). "
                    "2026-05 research already blocked this: FRED VIX/yields were "
                    "partial and TED/funding was incomplete. VIX_VXM control is "
                    "not funding. Do not invent a FRED URL."
                ),
            }
        )
    if not protocol:
        items.append(
            {
                "id": "do_not_invent_news_protocol",
                "blocked": "NEWS_PROTOCOL",
                "repair": (
                    "Ingest the real Project NEWS_PROTOCOL file when it exists. "
                    "Until then fail-closed. Host events.jsonl is a writer tape."
                ),
            }
        )
    items.append(
        {
            "id": "no_raw_x_firehose",
            "blocked": "narrative / funding-AI prose",
            "repair": "Walter / desk_briefs only if the Mac Project emits them. Never raw X.",
        }
    )
    return items
