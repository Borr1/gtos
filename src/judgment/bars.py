"""CSV bar loaders for gold_state. Clock: broker wall → UTC via NEW_YORK_PLUS_7."""

from __future__ import annotations

import csv
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from src.components.ultimate_book.primitives import Bar, atr14
from src.utils.broker_clock import NEW_YORK_PLUS_7, broker_naive_to_utc

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StampedBar:
    broker_naive: datetime
    utc: datetime
    bar: Bar
    source_path: str


def _parse_broker_time(raw: str) -> datetime:
    text = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable bar time: {raw!r}")


def _parse_iso_utc(raw: str) -> datetime:
    text = (raw or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_native_d1_npz(path: Path, *, limit: int | None = None) -> list[StampedBar]:
    """D1 OHLC from a period-16408 native bar archive. Not a tick file."""
    import numpy as np

    if path.is_relative_to(REPO_ROOT):
        rel = path.relative_to(REPO_ROOT).as_posix()
    else:
        rel = Path(path).as_posix()
    archive = np.load(path)
    broker = archive["broker_time"]
    out: list[StampedBar] = []
    n = len(broker) if limit is None else min(len(broker), limit)
    for i in range(n):
        naive = datetime.fromtimestamp(int(broker[i]), timezone.utc).replace(tzinfo=None)
        out.append(
            StampedBar(
                broker_naive=naive,
                utc=broker_naive_to_utc(naive, NEW_YORK_PLUS_7),
                bar=Bar(
                    o=float(archive["o"][i]),
                    h=float(archive["h"][i]),
                    l=float(archive["l"][i]),
                    c=float(archive["c"][i]),
                    v=float(archive["v"][i]),
                ),
                source_path=rel,
            )
        )
    return out


def load_ohlc_csv(path: Path, *, limit: int | None = None) -> list[StampedBar]:
    if not path.is_file():
        return []
    if path.suffix.lower() == ".npz":
        return _load_native_d1_npz(path, limit=limit)
    if path.is_relative_to(REPO_ROOT):
        rel = path.relative_to(REPO_ROOT).as_posix()
    else:
        rel = Path(path).as_posix()
    out: list[StampedBar] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            if row.get("time_utc"):
                # Challenge-true FTMO export: time_utc already corrected (−3h).
                # Do not run NY+7 on it.
                utc = _parse_iso_utc(row["time_utc"])
                labeled = (row.get("time_server_labeled") or "").strip()
                if labeled:
                    naive = _parse_iso_utc(labeled).replace(tzinfo=None)
                else:
                    naive = utc.replace(tzinfo=None) + timedelta(hours=3)
            else:
                naive = _parse_broker_time(row["time"])
                utc = broker_naive_to_utc(naive, NEW_YORK_PLUS_7)
            out.append(
                StampedBar(
                    broker_naive=naive,
                    utc=utc,
                    bar=Bar(
                        o=float(row["open"]),
                        h=float(row["high"]),
                        l=float(row["low"]),
                        c=float(row["close"]),
                        v=float(row.get("volume") or row.get("tick_volume") or 0.0),
                    ),
                    source_path=rel,
                )
            )
    return out


def last_closed_at_or_before(rows: list[StampedBar], as_of_utc: datetime) -> int | None:
    if not rows:
        return None
    as_of = as_of_utc.astimezone(timezone.utc)
    lo, hi, found = 0, len(rows) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if rows[mid].utc <= as_of:
            found = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return found


_MAX_LAG = {
    "M1": timedelta(hours=4),
    "M5": timedelta(hours=6),
    "M15": timedelta(hours=12),
    "H1": timedelta(hours=24),
    "H4": timedelta(hours=36),
    "D1": timedelta(days=5),
}


def tf_snap(rows: list[StampedBar], as_of_utc: datetime, tf: str, *, lookback: int = 20) -> dict | None:
    idx = last_closed_at_or_before(rows, as_of_utc)
    if idx is None:
        return None
    as_of = as_of_utc.astimezone(timezone.utc)
    lag = as_of - rows[idx].utc
    max_lag = _MAX_LAG.get(tf, timedelta(hours=12))
    if lag > max_lag:
        return None  # stale tape is missing state, not last April close wearing a September hat
    bars = [r.bar for r in rows[: idx + 1]]
    last = rows[idx]
    atr = atr14(bars, idx) if idx >= 14 else None
    close_vs = None
    if atr and atr > 0 and idx >= lookback:
        close_vs = (bars[idx].c - bars[idx - lookback].c) / atr
    trend = None
    if close_vs is not None:
        from .state_choices import LEGACY, trend_choice

        chosen = trend_choice(close_vs)
        if chosen is not LEGACY:
            trend = chosen
        elif close_vs > 1.0:
            trend = 1
        elif close_vs < -1.0:
            trend = -1
        else:
            trend = 0
    return {
        "tf": tf,
        "last_close": last.bar.c,
        "last_range": last.bar.h - last.bar.l,
        "atr14": atr if atr and atr > 0 else None,
        "close_vs_close_n_atr": close_vs,
        "trend": trend,
        "bars_available": idx + 1,
        "source_path": last.source_path,
        "last_utc": last.utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_broker": last.broker_naive.strftime("%Y-%m-%d %H:%M:%S"),
    }


def prior_day_levels(d1: list[StampedBar], as_of_utc: datetime) -> tuple[float | None, float | None]:
    idx = last_closed_at_or_before(d1, as_of_utc)
    if idx is None or idx < 1:
        return None, None
    as_of = as_of_utc.astimezone(timezone.utc)
    if as_of - d1[idx].utc > timedelta(days=5):
        return None, None
    prev = d1[idx - 1].bar
    return prev.h, prev.l


CHALLENGE_BAR_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917"
)
CHALLENGE_BAR_MULTI_DIR = CHALLENGE_BAR_DIR / "multi"
NATIVE_D1_DIR = REPO_ROOT / "judgment" / "astra" / "lab" / "native_bars_normalized001"

# redacted_account 2026-09-17 drop. XAU parent; peers + these under challenge_shadow_bars/multi/.
# File stems: US30_cash / UK100_cash. time_utc already −3h. No D1 for non-XAU.
# USDJPY is peer-of-XAU (PRIORITY). Pull Challenge-true M15+H4 beside multi/.
# Never invent DXY / yields / OB. April data/historical is never Challenge tape.
MULTI_SYMBOL_PRIORITY = ("USDJPY", "EURUSD", "GBPUSD", "BTCUSD", "EURGBP", "US30", "UK100", "ETHUSD")
MULTI_SYMBOL_OPTIONAL = ()
XAU_PEER_SYMBOLS = ("USDJPY",)
_FILE_STEM = {"US30": "US30_cash", "UK100": "UK100_cash"}
_STEM_TO_SYMBOL = {"US30_cash": "US30", "UK100_cash": "UK100", "US30.cash": "US30", "UK100.cash": "UK100"}
_BOX_MULTI = Path("/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi")
_TF_KEYS = frozenset({"m15", "h4", "d1"})
_TF_SUFFIX = {"m15": "M15", "h4": "H4", "d1": "D1"}


def normalize_symbol(symbol: str | None) -> str:
    raw = (symbol or "XAUUSD").strip().upper().replace("/", "").replace(".", "_")
    aliases = {"XAU": "XAUUSD", "GOLD": "XAUUSD", "US30_CASH": "US30", "UK100_CASH": "UK100"}
    return aliases.get(raw, raw)


def file_stem_for(symbol: str | None) -> str:
    """On-disk stem. US30.cash / UK100.cash land as US30_cash / UK100_cash."""
    return _FILE_STEM.get(normalize_symbol(symbol), normalize_symbol(symbol))


def symbol_from_stem(stem: str) -> str:
    return _STEM_TO_SYMBOL.get(stem, stem)


def _candidate_stems(symbol: str) -> list[str]:
    sym = normalize_symbol(symbol)
    stems = [file_stem_for(sym), sym]
    if sym == "US30":
        stems.extend(["US30_cash", "US30.cash", "US30"])
    elif sym == "UK100":
        stems.extend(["UK100_cash", "UK100.cash", "UK100"])
    out: list[str] = []
    seen: set[str] = set()
    for stem in stems:
        if stem not in seen:
            seen.add(stem)
            out.append(stem)
    return out


def challenge_search_dirs() -> list[Path]:
    """Known Challenge-true locations. April data/historical is never a member."""
    dirs: list[Path] = []
    extra = (os.environ.get("GTOS_CHALLENGE_BAR_MULTI") or "").strip()
    if extra:
        dirs.append(Path(extra))
    dirs.extend(
        [
            CHALLENGE_BAR_DIR,
            CHALLENGE_BAR_MULTI_DIR,
            REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_bars" / "multi",
            REPO_ROOT
            / "pipeline_state"
            / "ultimate_book"
            / "operator"
            / "judgment"
            / "state"
            / "_fable_bar_pull_20260917"
            / "multi",
            _BOX_MULTI,
            Path("/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars"),
        ]
    )
    seen: set[str] = set()
    out: list[Path] = []
    for path in dirs:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _default_missing_path(symbol: str, tf_suffix: str) -> Path:
    stem = file_stem_for(symbol)
    if normalize_symbol(symbol) == "XAUUSD":
        return CHALLENGE_BAR_DIR / f"{stem}_{tf_suffix}.csv"
    return CHALLENGE_BAR_MULTI_DIR / f"{stem}_{tf_suffix}.csv"


def _native_d1_stems(symbol: str) -> list[str]:
    raw = (symbol or "").strip()
    stems = [raw, raw.replace(".", "_"), * _candidate_stems(symbol)]
    out: list[str] = []
    seen: set[str] = set()
    for stem in stems:
        if stem and stem not in seen:
            seen.add(stem)
            out.append(stem)
    return out


def resolve_challenge_tf(symbol: str, tf: str) -> Path:
    """First existing series for this symbol/TF. Missing path is the landing slot, not April."""
    tf_key = tf.lower()
    suffix = _TF_SUFFIX.get(tf_key, tf.upper())
    for directory in challenge_search_dirs():
        for stem in _candidate_stems(symbol):
            path = directory / f"{stem}_{suffix}.csv"
            if path.is_file():
                return path
    if suffix == "D1":
        for stem in _native_d1_stems(symbol):
            path = NATIVE_D1_DIR / f"{stem}_16408.npz"
            if path.is_file():
                return path
    return _default_missing_path(symbol, suffix)


def challenge_symbol_paths(symbol: str = "XAUUSD") -> dict[str, Path]:
    """Challenge-true FTMO 0 tape paths. Missing files stay missing."""
    return {
        "m15": resolve_challenge_tf(symbol, "M15"),
        "h4": resolve_challenge_tf(symbol, "H4"),
        "d1": resolve_challenge_tf(symbol, "D1"),
    }


def challenge_tape_present(symbol: str) -> bool:
    path = resolve_challenge_tf(symbol, "M15")
    return path.is_file()


def challenge_gold_paths() -> dict[str, Path]:
    """XAU alias. Do not use April repo M15 here."""
    return challenge_symbol_paths("XAUUSD")


def landed_challenge_symbols() -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for directory in challenge_search_dirs():
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*_M15.csv")):
            stem = path.name[: -len("_M15.csv")]
            sym = normalize_symbol(symbol_from_stem(stem))
            if sym not in seen:
                seen.add(sym)
                found.append(sym)
    return found


# Challenge-true peer tape starts with the XAU drop (2026-09-17) and the
# 2026-09-18 FX pull (through ~03:00Z). April historical last-prints fail this.
CHALLENGE_PEER_MIN_LAST_UTC = datetime(2026, 9, 17, tzinfo=timezone.utc)


def admit_challenge_peer_csv(path: Path) -> dict:
    """Refuse April / broker-naive exports. Challenge peers carry time_utc = server−3h."""
    if not path.is_file():
        return {"ok": False, "reason": "missing", "path": str(path)}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if "time_utc" not in fields:
            return {
                "ok": False,
                "reason": "no_time_utc_column_april_or_broker_naive",
                "path": str(path),
            }
        first = last = None
        n = 0
        for row in reader:
            n += 1
            if first is None:
                first = row
            last = row
    if last is None:
        return {"ok": False, "reason": "empty", "path": str(path)}
    try:
        last_utc = _parse_iso_utc(str(last.get("time_utc") or ""))
    except (TypeError, ValueError):
        return {"ok": False, "reason": "unparseable_time_utc", "path": str(path)}
    if last_utc < CHALLENGE_PEER_MIN_LAST_UTC:
        return {
            "ok": False,
            "reason": "last_utc_before_challenge_era",
            "last_utc": last_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": str(path),
        }
    labeled = str(last.get("time_server_labeled") or "").strip()
    offset_ok = None
    if labeled:
        hours = (_parse_iso_utc(labeled) - last_utc).total_seconds() / 3600.0
        offset_ok = abs(hours - 3.0) < 0.15
        if not offset_ok:
            return {
                "ok": False,
                "reason": "server_offset_not_minus_3h",
                "offset_hours": round(hours, 4),
                "path": str(path),
            }
    first_utc = None
    if first and first.get("time_utc"):
        try:
            first_utc = _parse_iso_utc(str(first["time_utc"]))
        except (TypeError, ValueError):
            first_utc = None
    return {
        "ok": True,
        "n": n,
        "first_utc": first_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if first_utc else None,
        "last_utc": last_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offset_ok": offset_ok,
        "path": str(path),
    }


def copy_multi_csvs_if_present(src: Path | None = None) -> dict:
    """Copy box/VPS multi CSVs into the lab landing dir. Never invent bars.

    April ``exports/multi_instrument`` / ``data/historical*`` fail admit
    (no ``time_utc``, last print in April). Chair-claimed VPS files that
    are not on this VM stay uncopied.
    """
    sources = []
    if src is not None:
        sources.append(Path(src))
    extra = (os.environ.get("GTOS_CHALLENGE_BAR_MULTI") or "").strip()
    if extra:
        sources.append(Path(extra))
    sources.extend(
        [
            _BOX_MULTI,
            REPO_ROOT
            / "pipeline_state"
            / "ultimate_book"
            / "operator"
            / "judgment"
            / "state"
            / "_fable_bar_pull_20260917"
            / "multi",
        ]
    )
    dest = CHALLENGE_BAR_MULTI_DIR
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    rejected: list[dict] = []
    used = None
    for directory in sources:
        if not directory.is_dir():
            continue
        csvs = sorted(directory.glob("*_M15.csv")) + sorted(directory.glob("*_H4.csv"))
        if not csvs:
            continue
        used = str(directory)
        for path in csvs:
            admit = admit_challenge_peer_csv(path)
            if not admit.get("ok"):
                rejected.append({"name": path.name, "reason": admit.get("reason")})
                continue
            target = dest / path.name
            if path.resolve() == target.resolve():
                continue
            shutil.copy2(path, target)
            copied.append(path.name)
        for extra_name in ("pull_meta.json", "README.md"):
            extra_path = directory / extra_name
            if extra_path.is_file() and copied:
                shutil.copy2(extra_path, dest / extra_name)
        break
    return {
        "src": used,
        "dest": str(dest.relative_to(REPO_ROOT)) if dest.is_relative_to(REPO_ROOT) else str(dest),
        "n_copied": len(copied),
        "copied": copied,
        "n_rejected": len(rejected),
        "rejected": rejected,
        "invented": False,
        "april_historical_used": False,
    }


def load_all_landed_challenge_books() -> dict[str, dict[str, list[StampedBar]]]:
    return {sym: load_challenge_books(symbol=sym) for sym in landed_challenge_symbols()}


def default_gold_paths() -> dict[str, Path]:
    """April 2026 historical pack for G-2W lab. Challenge scoring uses challenge_gold_paths."""
    h2026 = REPO_ROOT / "data" / "historical_2026"
    hist = REPO_ROOT / "data" / "historical"
    m15 = h2026 / "XAUUSD_M15.csv"
    if not m15.is_file():
        m15 = hist / "XAUUSD_M15.csv"
    h4 = h2026 / "XAUUSD_H4.csv"
    if not h4.is_file():
        h4 = hist / "XAUUSD_H4.csv"
    d1 = h2026 / "XAUUSD_D1.csv"
    if not d1.is_file():
        d1 = hist / "XAUUSD_D1.csv"
    return {"m15": m15, "h4": h4, "d1": d1}


def load_gold_books(paths: dict[str, Path] | None = None) -> dict[str, list[StampedBar]]:
    chosen = paths or default_gold_paths()
    return {tf: load_ohlc_csv(path) for tf, path in chosen.items()}


def load_challenge_books(symbol: str = "XAUUSD") -> dict[str, list[StampedBar]]:
    return load_gold_books(challenge_symbol_paths(symbol))


def _is_single_tf_cache(cache: dict) -> bool:
    if not cache:
        return True
    keys = {str(k).lower() for k in cache}
    if keys & _TF_KEYS:
        return True
    return False


def books_for_symbol(
    symbol: str,
    cache: dict | None = None,
) -> dict[str, list[StampedBar]] | None:
    """Return M15/H4/D1 for this symbol. Never substitute XAU for another pair."""
    sym = normalize_symbol(symbol)
    if cache is None:
        if not challenge_tape_present(sym):
            return None
        return load_challenge_books(symbol=sym)
    if _is_single_tf_cache(cache):
        if sym == "XAUUSD":
            return cache
        if not challenge_tape_present(sym):
            return None
        return load_challenge_books(symbol=sym)
    if sym in cache:
        return cache[sym]
    if not challenge_tape_present(sym):
        cache[sym] = None
        return None
    loaded = load_challenge_books(symbol=sym)
    cache[sym] = loaded
    return loaded
