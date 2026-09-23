"""Bars in, frames out — through the sanctioned timebase seam, never around it.

The VPS bar archive's `time` column is **broker server wall clock**, not UTC, and every
file says so in a `.timebase.json` sidecar. Reading it as UTC is finding F7. So this
module never parses a bar file itself: it hands the paths to
`replay_policy.generation.CsvBarSource`, which refuses a file with no sidecar and converts
through `src/utils/broker_clock.py`.

Symbols cross the canonical -> broker boundary via
`symbol_map.build_broker_symbol_resolver(profile)` — the same crossing `book_engine.py:461`
makes, and the one whose bypass (a raw `mt5.symbol_info` on canonical names) reported two
live sleeves untradeable when both are at full surface.
"""

from __future__ import annotations

import datetime as dt
import glob
import os
from pathlib import Path
from typing import Any, Iterable, Optional

from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15
from src.components.ultimate_book.primitives import Bar
from src.research_infra.regime_spine.state import BarFrame, build_frame

__all__ = ["ARCHIVE", "TF_NAME", "load_series", "frames_for", "archive_index"]

#: The VPS `copy_rates_range` pull. Read-only; nothing here writes to it.
ARCHIVE = "/Users/borr/GTOSActive/vps-bars-20260727"

TF_NAME = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
NAME_TF = {v: k for k, v in TF_NAME.items()}


def _resolver(profile_path: Optional[str] = None):
    import yaml

    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver

    repo = Path(__file__).resolve().parents[3]
    p = profile_path or (repo / "config/profiles/operator_profile.yaml")
    prof = yaml.safe_load(open(p)) or {}
    return build_broker_symbol_resolver(prof)


def archive_index(archive: str = ARCHIVE, broker: str = "FTMO") -> dict[tuple[str, int], str]:
    """`{(canonical_symbol, timeframe): path}` for every file in the archive.

    The archive's filenames carry the **canonical** GTOS name, not the broker one
    (`BARS_MANIFEST.json`: *"Files are keyed on the CANONICAL GTOS name; each sidecar
    carries broker_symbol with the real one"*). Keying this index on the broker name
    instead silently loses every dotted instrument — `USOIL_cash`, `US30_cash`, the whole
    index and energy surface — which is 12 of the armed four's 20 symbols. Measured, not
    assumed: the first run of this module returned 8 frames instead of 20.
    """
    out: dict[tuple[str, int], str] = {}
    for p in sorted(glob.glob(f"{archive}/{broker}_*.csv.gz")):
        stem = os.path.basename(p)[len(broker) + 1:-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = NAME_TF.get(tfs)
        if tf is None:
            continue
        out[(sym, tf)] = p
    return out


def load_series(symbols: Iterable[str], timeframe: int, *,
                archive: str = ARCHIVE,
                profile_path: Optional[str] = None,
                ) -> dict[str, tuple[list[Bar], list[dt.datetime], str]]:
    """Load canonical `symbols` at `timeframe`. Returns `{canonical: (bars, times, broker)}`.

    A symbol with no archive file is simply absent from the result — that absence is the
    (a) cause this session exists to separate from the (b) and (c) ones, so it is returned
    as data rather than raised.
    """
    from src.research_infra.replay_policy.generation import CsvBarSource

    res = _resolver(profile_path)
    idx = archive_index(archive)
    files = {}
    for s in symbols:
        key = (s, int(timeframe))
        if key in idx:
            files[key] = idx[key]
    if not files:
        return {}
    src = CsvBarSource(files, label=f"regime_spine:{os.path.basename(archive)}")
    out: dict[str, tuple[list[Bar], list[dt.datetime], str]] = {}
    for (canon, tf), _path in files.items():
        rows = src._load((canon, tf))
        if not rows:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        out[canon] = (bars, times, res(canon))
    return out


def frames_for(symbols: Iterable[str], timeframe: int, *,
               archive: str = ARCHIVE,
               profile_path: Optional[str] = None,
               cache: Optional[dict] = None,
               ) -> dict[str, BarFrame]:
    """`{canonical_symbol: BarFrame}`, memoised through `cache` when one is supplied."""
    want = list(dict.fromkeys(symbols))
    out: dict[str, BarFrame] = {}
    todo = []
    for s in want:
        key = (s, int(timeframe))
        if cache is not None and key in cache:
            out[s] = cache[key]
        else:
            todo.append(s)
    if todo:
        for canon, (bars, times, bsym) in load_series(
                todo, timeframe, archive=archive, profile_path=profile_path).items():
            fr = build_frame(bsym, timeframe, bars, times)
            out[canon] = fr
            if cache is not None:
                cache[(canon, int(timeframe))] = fr
    return out


def surface_availability(symbols: Iterable[str], timeframe: int, *,
                         warmup_bars: int, archive: str = ARCHIVE,
                         profile_path: Optional[str] = None) -> dict[str, Any]:
    """When each symbol's series starts, and when it first clears the warmup floor.

    This is cause (a) made explicit and quantitative: a sleeve cannot fire on a symbol
    before this date, so any economics attributed to it before then is measuring the
    sleeve's absence, not its edge.
    """
    rows = {}
    got = load_series(symbols, timeframe, archive=archive, profile_path=profile_path)
    for s in symbols:
        if s not in got:
            rows[s] = {"in_archive": False}
            continue
        bars, times, bsym = got[s]
        i0 = warmup_bars - 1
        rows[s] = {
            "in_archive": True,
            "broker_symbol": bsym,
            "n_bars": len(bars),
            "first_bar_utc": times[0].isoformat(),
            "last_bar_utc": times[-1].isoformat(),
            "first_evaluable_utc": (times[i0].isoformat() if i0 < len(times) else None),
        }
    return rows
