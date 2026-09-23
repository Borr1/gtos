"""The paired substrate: one decision store, one bar archive, one resolver.

THE SUBSTRATE IS THE ESTATE'S OWN DECISIONS, NOT A RE-DERIVATION
----------------------------------------------------------------
`AQ_ESTATE_TRADES_V2.json.gz` holds 22,324 unique candidate decisions over 32 sleeves
(29 that generate), each carrying the four things a paired treatment needs and nothing a
treatment is allowed to change:

    (sleeve, symbol, timeframe, decision_bar_iso, direction, sl_distance_price, target_dist)

Everything downstream of that tuple is a *treatment*.  Everything in it is *held*.  That is
what makes a difference between two arms a statement about the treatment rather than about
two different books.

The published `r_gross` on each row is the estate's own label.  :mod:`controls` re-derives
it from the bars under the published contract and refuses to run if a single row disagrees
-- the same doctrine as `r1_estate_rewalk.py`, whose control this reuses.

CACHING
-------
Loading 123 CSV series (3.55 M bars) costs ~108 s.  The harness caches the parsed series to
a pickle under the scratch root so an iteration costs seconds.  The cache key includes the
archive path and every file's (size, mtime); a changed archive invalidates it rather than
silently serving stale bars.
"""

from __future__ import annotations

import datetime as dt
import glob
import gzip
import hashlib
import json
import os
import pickle
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

REPO = Path(__file__).resolve().parents[9]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, TF_M15  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402

#: The bar archive AA/AQ/Lane 8 all walked.  Outside the repo, read-only, never written.
BARS_ARCHIVE = os.environ.get("B8_BARS", "/Users/borr/GTOSActive/vps-bars-20260727")

#: The estate's decision store of record.
INTENTS = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
)

#: Lane r1's quote-corrected rows -- used only by the statistics-layer reproduction control.
R1_ROWS = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz"
)

CACHE_DIR = Path(os.environ.get("B8_CACHE", "/Users/borr/.claude/jobs/adb9e69b/tmp/b8_cache"))

TF_NAME: dict[int, str] = {TF_M15: "M15", TF_H4: "H4", TF_D1: "D1"}
TF_MINUTES: dict[int, int] = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}
NAME_TF: dict[str, int] = {v: k for k, v in TF_NAME.items()}

#: The research horizon every published estate number is measured under.
MAXBARS = 80


@dataclass(frozen=True)
class Intent:
    """One held decision.  No field here may be varied by a treatment."""

    sleeve: str
    symbol: str
    timeframe: int
    decision_bar_iso: str
    direction: int
    stop_dist: float
    target_dist: float | None
    decision_day: str
    entry_utc: str
    #: The estate's published label under its own contract.  Control input only.
    published_r_gross: float
    published_exit_reason: str

    @property
    def tf_name(self) -> str:
        return TF_NAME[self.timeframe]

    @property
    def key(self) -> tuple[str, str, int, str]:
        """The pairing key.  Two arms agree on this or they are not paired."""
        return (self.sleeve, self.symbol, self.timeframe, self.decision_bar_iso)


@dataclass
class Series:
    """One symbol/timeframe bar series, plus an open-time index."""

    bars: list[Bar]
    times: list[dt.datetime]
    index: dict[dt.datetime, int]


def _archive_fingerprint(archive: str) -> str:
    h = hashlib.sha256()
    for p in sorted(glob.glob(f"{archive}/FTMO_*.csv.gz")):
        st = os.stat(p)
        h.update(os.path.basename(p).encode())
        h.update(str(st.st_size).encode())
        h.update(str(int(st.st_mtime)).encode())
    return h.hexdigest()[:16]


def load_series(archive: str = BARS_ARCHIVE, *, verbose: bool = True) -> dict[tuple[str, int], Series]:
    """Every FTMO series in the archive, keyed by (canonical symbol, timeframe).

    The broker-wall-clock -> true-UTC conversion is `CsvBarSource`'s, i.e. the same seam
    `generation.py:162` uses.  Reading those stamps as raw UTC is finding F7 and is exactly
    what this must not do.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"series_{_archive_fingerprint(archive)}.pkl"
    if cache.is_file():
        with cache.open("rb") as fh:
            return pickle.load(fh)

    t0 = time.time()
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    files: dict[tuple[str, int], str] = {}
    for p in glob.glob(f"{archive}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = NAME_TF.get(tfs)
        if tf is None:
            continue
        files[(resolve(sym), tf)] = p

    src = CsvBarSource(files, label=f"b8-{os.path.basename(archive)}-FTMO")
    out: dict[tuple[str, int], Series] = {}
    for key in files:
        rows = src._load(key)
        if not rows:
            continue
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0)) for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        out[key] = Series(bars, times, {ts: i for i, ts in enumerate(times)})
    with cache.open("wb") as fh:
        pickle.dump(out, fh, protocol=pickle.HIGHEST_PROTOCOL)
    if verbose:
        print(f"[substrate] loaded {len(out)} series in {time.time() - t0:.0f}s -> {cache}")
    return out


def load_intents(path: Path = INTENTS) -> tuple[list[Intent], dict[str, Any]]:
    """Every held decision in the estate store, plus the store's own metadata."""
    doc = json.load(gzip.open(path))
    intents: list[Intent] = []
    for sleeve, rows in sorted(doc["trades"].items()):
        for r in rows:
            td = r.get("target_dist")
            intents.append(
                Intent(
                    sleeve=sleeve,
                    symbol=r["symbol"],
                    timeframe=int(r["timeframe"]),
                    decision_bar_iso=r["decision_bar_iso"],
                    direction=int(r["direction"]),
                    stop_dist=float(r["sl_distance_price"]),
                    target_dist=(float(td) if td else None),
                    decision_day=r["decision_day"],
                    entry_utc=r["entry_utc"],
                    published_r_gross=float(r["r_gross"]),
                    published_exit_reason=str(r["exit_reason"]),
                )
            )
    meta = {k: v for k, v in doc.items() if k != "trades"}
    return intents, meta


@dataclass
class Substrate:
    """Decisions + bars + the resolver that binds one to the other."""

    intents: list[Intent]
    series: dict[tuple[str, int], Series]
    meta: dict[str, Any]
    archive: str = BARS_ARCHIVE

    @classmethod
    def load(cls, *, archive: str = BARS_ARCHIVE, verbose: bool = True) -> "Substrate":
        intents, meta = load_intents()
        series = load_series(archive, verbose=verbose)
        return cls(intents=intents, series=series, meta=meta, archive=archive)

    # -- resolution ---------------------------------------------------------------
    def resolve(self, it: Intent) -> tuple[Series, int] | None:
        """(series, decision-bar index) on the intent's OWN grid, or None."""
        s = self.series.get((it.symbol, it.timeframe))
        if s is None:
            return None
        i = s.index.get(dt.datetime.fromisoformat(it.decision_bar_iso))
        if i is None or i + 2 >= len(s.bars):
            return None
        return s, i

    def resolve_on(self, it: Intent, timeframe: int) -> tuple[Series, int] | None:
        """The same decision projected onto ANOTHER grid, at the first bar that OPENS at
        or after the intent's own entry instant.

        This is the cross-grid seam the entry-timing question needs, and it is deliberately
        the only one: an arm may re-anchor a fill in time, never re-derive the signal.
        """
        s = self.series.get((it.symbol, timeframe))
        if s is None:
            return None
        entry = dt.datetime.fromisoformat(it.entry_utc)
        lo, hi = 0, len(s.times)
        while lo < hi:  # first index with times[k] >= entry
            mid = (lo + hi) // 2
            if s.times[mid] < entry:
                lo = mid + 1
            else:
                hi = mid
        if lo >= len(s.times) - 2:
            return None
        return s, lo

    def entry_instant(self, it: Intent) -> dt.datetime:
        return dt.datetime.fromisoformat(it.entry_utc)

    def by_sleeve(self, *sleeves: str) -> list[Intent]:
        want = set(sleeves)
        return [i for i in self.intents if i.sleeve in want]

    def forward(self, intents: Sequence[Intent] | None = None, year: int = 2025) -> list[Intent]:
        src = self.intents if intents is None else intents
        return [i for i in src if i.entry_utc[:4] >= str(year)]

    def __iter__(self) -> Iterator[Intent]:
        return iter(self.intents)
