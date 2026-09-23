"""The decision emitter: the full 29-sleeve estate as a read-only shadow book.

WHAT THIS IS
------------
Lane 4 rung 1 is *"run the full 29-sleeve estate as a read-only shadow book"*.  This is that
runner.  It drives the estate's OWN generation loop -- `replay_policy.generation
.GenerationPort`, which wraps `UltimateBookLiveEngine._generate_intents`, the same code path
`run_book.py` runs -- over a `BarSource`, at bar closes, and appends every candidate decision
to a JSONL in the exact schema :mod:`live_shadow` reads back.

**One runner, two bar sources, no code change between them:**

* offline / catch-up: `CsvBarSource` over `/Users/borr/GTOSActive/vps-bars-20260727` (or the
  host's own archive).  This is what the paired questions run on today.
* forward on the VPS: a `BarSource` backed by `ShadowReadOnlyMT5Adapter.copy_rates_from_pos`.
  The adapter's `order_send` raises; there is no mutation surface to reach.

WHY IT DRIVES THE ENGINE RATHER THAN CALLING GENERATORS DIRECTLY
------------------------------------------------------------------
Calling each sleeve's `generate()` by hand would reproduce the *rules* and not the *book*: the
include-flag registry (`book_engine.py:283-295`), the DF-1 active-sleeve filter, the warmup
and bar-count resolution, and the per-sleeve broker-symbol mapping all live in the engine.  A
decision stream that skipped them would be a different book from the one every estate number
describes, and the paired questions would silently be about that other book.

ZERO BROKER MUTATION
--------------------
`GenerationPort` is handed a `ReplayMT5` (offline) or the read-only shadow adapter (forward).
Neither exposes an order surface.  This module names no mutation call and imports no network
library; `controls.control_read_only` scans it with every other module in the package.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from .substrate import BARS_ARCHIVE, NAME_TF, REPO, TF_MINUTES, TF_NAME

#: The research config the estate's own artifact was generated under.  `include_clean3` is
#: flipped in the config DICT handed to the port, never on disk -- `agent_config.yaml` is
#: H1-bound AND its digest is bound by the live activation token
#: (`AQ_ESTATE_TRADES_V2.research_overrides`, and the same doctrine here).
RESEARCH_OVERRIDES: dict[str, Any] = {
    "ultimate_book_include_clean3": True,
    "ultimate_book_include_candidate_book": True,
    "ultimate_book_include_market_expansion_book": True,
}


def runtime_config(repo: Path = REPO, *, profile: str = "operator_profile",
                   overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """The merged `gtos_vnext_runtime` block, with the research overrides applied IN MEMORY."""
    import yaml

    base = yaml.safe_load(open(repo / "config/agent_config.yaml")) or {}
    prof = yaml.safe_load(open(repo / f"config/profiles/{profile}.yaml")) or {}
    cfg = dict((base.get("gtos_vnext_runtime") or {}))
    cfg.update(prof.get("gtos_vnext_runtime") or {})
    cfg.update(RESEARCH_OVERRIDES)
    cfg.update(overrides or {})
    # Belt and braces: a shadow emitter must never be able to reach broker authority even if
    # a config it read had it on. These three are the live gates (CLAUDE.md section 4).
    cfg["ultimate_book_live_broker_authority"] = False
    cfg["ultimate_book_live_activation_allowed"] = False
    cfg["ultimate_book_apply_to_execution"] = False
    return cfg


def csv_bar_source(archive: str = BARS_ARCHIVE, repo: Path = REPO,
                   profile: str = "operator_profile"):
    """A `CsvBarSource` over the bar archive, symbol-resolved exactly as the estate does."""
    import glob
    import os

    import yaml

    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    from src.research_infra.replay_policy.generation import CsvBarSource

    prof = yaml.safe_load(open(repo / f"config/profiles/{profile}.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)
    files: dict[tuple[str, int], str] = {}
    for p in glob.glob(f"{archive}/FTMO_*.csv.gz"):
        stem = os.path.basename(p)[len("FTMO_"):-len(".csv.gz")]
        sym, _, tfs = stem.rpartition("_")
        tf = NAME_TF.get(tfs)
        if tf is not None:
            files[(resolve(sym), tf)] = p
    return CsvBarSource(files, label=f"b8-emit-{os.path.basename(archive)}")


def _key(sleeve: str, symbol: str, timeframe: Any, decision_bar_iso: str) -> tuple:
    """The dedupe key, normalised so a reload and an in-loop emit agree on type."""
    tf = timeframe if isinstance(timeframe, int) else NAME_TF.get(str(timeframe), timeframe)
    return (str(sleeve), str(symbol), int(tf), str(decision_bar_iso))


def emit(bar_source, out_path: Path, *, start: dt.datetime, end: dt.datetime,
         timeframes: Sequence[int] = (), config: dict[str, Any] | None = None,
         namespace: str = "b8_paired_shadow", tags: Sequence[str] | None = None,
         verbose: bool = True) -> dict[str, Any]:
    """Walk bar closes in [start, end] and append every candidate decision to `out_path`.

    `tags=None` is deliberate and is the WHOLE POINT of rung 1: the live book runs a
    four-sleeve `--tags` subset, and this shadow runs the entire include-flag registry.  It is
    the one place in this estate where passing no tags is correct rather than fail-open, and it
    is safe here for exactly one reason -- there is no order surface behind it.
    """
    from src.research_infra.replay_policy.generation import GenerationPort, bar_closes

    cfg = config or runtime_config()
    port = GenerationPort(cfg, bar_source, namespace=namespace, account="SHADOW")
    active = sorted(port.active_sleeve_names())
    tfs = tuple(timeframes) or tuple(sorted({16388, 15, 1440}))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple] = set()
    if out_path.is_file():
        for line in out_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                # THE KEY MUST BE THE SAME TYPE ON BOTH SIDES. The file stores the timeframe
                # as a NAME ("H4") and the in-loop key is the engine's integer, so a naive
                # reload silently deduped nothing and a restarted emitter would re-append
                # every decision it had already written. Double-counted decisions inflate the
                # sequential monitor's information fraction, which is the entire basis of its
                # alpha spending -- a restart would have bought an unearned early stop.
                seen.add(_key(r["sleeve"], r["symbol"], r["timeframe"], r["decision_bar_iso"]))

    stats = {"cycles": 0, "candidates": 0, "appended": 0, "duplicates": 0,
             "active_sleeves": active, "n_active_sleeves": len(active),
             "timeframes": [TF_NAME.get(t, t) for t in tfs],
             "window": [start.isoformat(), end.isoformat()],
             "bar_source": dict(bar_source.describe()) if hasattr(bar_source, "describe") else {}}
    t0 = time.time()
    with out_path.open("a") as fh:
        for tf in tfs:
            for close_at in bar_closes(start, end, tf):
                res = port.generate(close_at, tags=tags)
                stats["cycles"] += 1
                for c in res.candidates:
                    stats["candidates"] += 1
                    key = _key(c.sleeve, c.symbol, int(c.timeframe), c.decision_bar_iso)
                    if key in seen:
                        stats["duplicates"] += 1
                        continue
                    seen.add(key)
                    # `entry_utc` is the DECISION BAR'S CLOSE, not the cycle instant that
                    # emitted it -- because that is the anchor the sanctioned labeller uses
                    # (`exits.replay` enters at `bars[i].c`) and the anchor the sealed store
                    # carries. A cycle at 00:00 can surface a bar that closed at 21:00; using
                    # the cycle instant would silently re-anchor every forward decision and
                    # break pairing against history. The gap is real and measured --
                    # `AQ_ESTATE_TRADES_V2.entry_convention_gap`, mean |R| 0.0315 -- so the
                    # cycle instant is kept alongside rather than discarded.
                    tf_int = int(c.timeframe)
                    bar_open = dt.datetime.fromisoformat(c.decision_bar_iso)
                    entry_at = bar_open + dt.timedelta(minutes=TF_MINUTES[tf_int])
                    row = {
                        "sleeve": c.sleeve, "symbol": c.symbol,
                        "timeframe": TF_NAME.get(tf_int, tf_int),
                        "decision_bar_iso": c.decision_bar_iso,
                        "direction": int(c.direction),
                        "sl_distance_price": float(c.stop_dist),
                        "target_dist": (float(c.target_dist) if c.target_dist else None),
                        "decision_day": c.decision_day,
                        "entry_utc": entry_at.isoformat(),
                        "surfaced_at_cycle_utc": close_at.isoformat(),
                        "surfacing_lag_minutes": round(
                            (close_at - entry_at).total_seconds() / 60.0, 1),
                        "emitted_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "broker_mutation": False,
                    }
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
                    stats["appended"] += 1
                if verbose and stats["cycles"] % 500 == 0:
                    print(f"  [emit] {TF_NAME.get(tf, tf)} {close_at.date()} "
                          f"cycles={stats['cycles']} appended={stats['appended']}", flush=True)
    stats["seconds"] = round(time.time() - t0, 1)
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Emit read-only estate decisions for B8.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", required=True, help="ISO date, inclusive")
    ap.add_argument("--end", required=True, help="ISO date, inclusive")
    ap.add_argument("--archive", default=BARS_ARCHIVE)
    ap.add_argument("--timeframes", default="H4",
                    help="comma-separated M15,H4,D1 (default H4 -- the cheapest useful grid)")
    args = ap.parse_args(argv)

    tfs = tuple(NAME_TF[t.strip()] for t in args.timeframes.split(",") if t.strip())
    start = dt.datetime.fromisoformat(args.start).replace(tzinfo=dt.timezone.utc)
    end = dt.datetime.fromisoformat(args.end).replace(tzinfo=dt.timezone.utc)
    stats = emit(csv_bar_source(args.archive), Path(args.out), start=start, end=end,
                 timeframes=tfs)
    print(json.dumps(stats, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
