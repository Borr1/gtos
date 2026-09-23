#!/usr/bin/env python3
"""Session CI: regenerate ``vp_euidx_pocgrav`` over the provenance-spliced M1 view.

Pure offline research path.  H4 decisions and labels come from the existing read-only FTMO bar
archive.  Prior-day M1 volume profiles come from CI's hybrid view: provenance-declared Dukascopy
BID candles before the first broker M1 stamp and broker bars thereafter.  The live generation port,
the CA exit contract, and the CA winsorisation path are reused unchanged.

March 2026 is protected twice: the hybrid M1 input contains no March rows, and this driver skips
March decision clocks plus every pre-March candidate whose full 80-H4-bar label horizon could
reach March.  The latter check happens before ``replay()``; no March outcome is read and discarded.
"""

from __future__ import annotations

import collections
import datetime as dt
import gzip
import json
import statistics
import sys
import time
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_H4  # noqa: E402
from src.components.ultimate_book.book_engine import (  # noqa: E402
    _candidate_book_sleeves,
    _market_expansion_sleeves,
)
from src.components.ultimate_book.execution_packets import (  # noqa: E402
    DEFAULT_EXIT_PROFILE,
    SLEEVE_EXIT_PROFILES,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource, GenerationPort  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.fidelity import fidelity_for  # noqa: E402


HERE = Path(__file__).resolve().parent
ARCHIVE = Path("/Users/borr/GTOSActive/vps-bars-20260727")
DATA_ROOT = REPO / "data/mt5_research_exports/thirdparty_m1_ger40_uk100_20260731"
SPLICE_RECEIPT = HERE / "CI_THIRD_PARTY_SPLICE_V1.json"
OUT = HERE / "CI_VP_TRADES_V1.json.gz"
SUMMARY_OUT = HERE / "CI_VP_GENERATION_V1.json"
CA_TRADES = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase14/receipts/"
      "CA_REVIVAL_TRADES_VP_V1.json.gz"
)

SLEEVE = "vp_euidx_pocgrav"
SYMBOLS = ("GER40", "UK100")
MAXBARS = 80
LIVE_STOP_OWN_BARS = 60
H4_MINUTES = 240
PROTECTED_START = dt.date(2026, 3, 1)
PROTECTED_END = dt.date(2026, 3, 31)


def _is_protected(value: dt.datetime | dt.date) -> bool:
    day = value.date() if isinstance(value, dt.datetime) else value
    return PROTECTED_START <= day <= PROTECTED_END


def _label_horizon_touches_protected(entry: dt.datetime, horizon: dt.datetime) -> bool:
    """True when a forward label walk could consume any protected March outcome."""
    return entry.date() <= PROTECTED_END and horizon.date() >= PROTECTED_START


def _build() -> tuple[dict, object, CsvBarSource, GenerationPort, dict]:
    splice = json.loads(SPLICE_RECEIPT.read_text())
    profile = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolver = build_broker_symbol_resolver(profile)
    files = {
        (resolver("GER40"), TF_H4): ARCHIVE / "FTMO_GER40_H4.csv.gz",
        (resolver("UK100"), TF_H4): ARCHIVE / "FTMO_UK100_H4.csv.gz",
        (resolver("GER40"), 1): DATA_ROOT / splice["gate_view"]["GER40"]["path"],
        (resolver("UK100"), 1): DATA_ROOT / splice["gate_view"]["UK100"]["path"],
    }
    for path in files.values():
        if not Path(path).is_file():
            raise SystemExit(f"required bar file missing: {path}")
    base = yaml.safe_load(open(REPO / "config/agent_config.yaml"))
    cfg = dict(base.get("gtos_vnext_runtime") or {})
    cfg["ultimate_book_include_clean3"] = True
    source = CsvBarSource(files, label="ci_vp_provenance_splice")
    port = GenerationPort(
        cfg,
        source,
        namespace="ci_vp_thirdparty_m1",
        broker_symbol=resolver,
    )
    return cfg, resolver, source, port, splice


def _live_contract() -> dict:
    profile = SLEEVE_EXIT_PROFILES.get(SLEEVE, DEFAULT_EXIT_PROFILE)
    return {
        **profile,
        "time_stop_bars_m15": profile.get("time_stop_bars"),
        "time_stop_own_h4_bars": LIVE_STOP_OWN_BARS,
        "primary_research_maxbars": MAXBARS,
    }


def generate() -> dict:
    t0 = time.time()
    cfg, resolver, source, port, splice = _build()
    specs = {
        spec.tag: spec
        for spec in active_specs(
            None,
            include_candidate_book=bool(cfg.get("ultimate_book_include_candidate_book", False)),
            candidate_book_sleeves=_candidate_book_sleeves(cfg) or None,
            include_market_expansion_book=bool(
                cfg.get("ultimate_book_include_market_expansion_book", False)
            ),
            market_expansion_sleeves=_market_expansion_sleeves(cfg) or None,
        )
    }
    spec = specs.get(SLEEVE)
    if spec is None or spec.timeframe != TF_H4 or tuple(spec.on_surface) != SYMBOLS:
        raise SystemExit(
            f"registry drift for {SLEEVE}: "
            f"{None if spec is None else (spec.timeframe, tuple(spec.on_surface))}"
        )

    series: dict[str, tuple[list[Bar], list[dt.datetime]]] = {}
    index: dict[str, dict[dt.datetime, int]] = {}
    for canonical in SYMBOLS:
        symbol = resolver(canonical)
        rows = source._load((symbol, TF_H4))
        bars = [Bar(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0))
                for r in rows]
        times = [dt.datetime.fromisoformat(r["time"]) for r in rows]
        series[symbol] = (bars, times)
        index[symbol] = {stamp: i for i, stamp in enumerate(times)}

    # The earliest M1 row is an availability boundary, not an outcome-selected cut.
    earliest_m1 = min(
        dt.datetime.fromisoformat(source._load((resolver(canonical), 1))[0]["time"])
        for canonical in SYMBOLS
    )
    stamps = sorted(
        {
            stamp
            for _symbol, (_bars, times) in series.items()
            for stamp in times
            if stamp >= earliest_m1
        }
    )
    grid_all = [stamp + dt.timedelta(minutes=H4_MINUTES) for stamp in stamps]
    grid = [stamp for stamp in grid_all if not _is_protected(stamp)]
    print(
        f"CI vp grid: {len(grid):,} closes ({len(grid_all) - len(grid):,} March closes "
        f"excluded before generation), {grid[0].date()}..{grid[-1].date()}",
        flush=True,
    )

    candidates = []
    seen: set[tuple] = set()
    duplicates = 0
    evaluations = 0
    for n, close in enumerate(grid, 1):
        result = port.generate(close, tags=(SLEEVE,))
        evaluations += len(result.evaluations)
        for candidate in result.candidates:
            key = (candidate.sleeve, candidate.symbol, candidate.decision_bar_iso)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            candidates.append(candidate)
        if n % 2_500 == 0:
            print(f"  generation {n:,}/{len(grid):,} candidates={len(candidates):,}", flush=True)

    rows = []
    skips: collections.Counter = collections.Counter()
    join_by_symbol = {
        canonical: dt.datetime.fromisoformat(splice["gate_view"][canonical]["join_utc"])
        for canonical in SYMBOLS
    }
    for candidate in candidates:
        symbol = resolver(candidate.symbol)
        bars, times = series[symbol]
        i = index[symbol].get(dt.datetime.fromisoformat(candidate.decision_bar_iso))
        if i is None or i + 2 >= len(bars):
            skips["bar_not_found_or_no_room"] += 1
            continue
        entry_utc = times[i] + dt.timedelta(minutes=H4_MINUTES)
        if _is_protected(entry_utc):
            raise AssertionError("March decision escaped the pre-generation exclusion")
        # Refuse before replay so no H4 outcome inside March can be read and later filtered.
        horizon_i = min(i + MAXBARS, len(times) - 1)
        horizon_utc = times[horizon_i] + dt.timedelta(minutes=H4_MINUTES)
        if _label_horizon_touches_protected(entry_utc, horizon_utc):
            skips["pre_march_candidate_full_label_horizon_touches_protected_month"] += 1
            continue

        plain = replay(
            bars,
            i,
            candidate.direction,
            stop_dist=candidate.stop_dist,
            policy=ExitPolicy(target_dist=candidate.target_dist, maxbars=MAXBARS, label="plain"),
        )
        live = replay(
            bars,
            i,
            candidate.direction,
            stop_dist=candidate.stop_dist,
            policy=ExitPolicy(
                target_dist=candidate.target_dist,
                maxbars=LIVE_STOP_OWN_BARS,
                label="live_time_stop",
            ),
        )
        exit_utc = times[plain.exit_index] + dt.timedelta(minutes=H4_MINUTES)
        live_exit_utc = times[live.exit_index] + dt.timedelta(minutes=H4_MINUTES)
        if _is_protected(exit_utc) or _is_protected(live_exit_utc):
            raise AssertionError("March outcome escaped the pre-replay horizon exclusion")

        canonical = candidate.symbol
        # The sleeve builds a profile from the prior completed UTC day.  At the join-day edge
        # the profile is still third-party; from the day after the broker's first date it is FTMO.
        profile_day = (dt.datetime.fromisoformat(candidate.decision_bar_iso).date()
                       - dt.timedelta(days=1))
        join_day = join_by_symbol[canonical].date()
        aux_provenance = "Dukascopy_thirdparty" if profile_day < join_day else "FTMO_broker"
        rows.append(
            {
                "sleeve": candidate.sleeve,
                "symbol": symbol,
                "symbol_canonical": canonical,
                "entry_utc": entry_utc.isoformat(),
                "exit_utc": exit_utc.isoformat(),
                "direction": int(candidate.direction),
                "sl_distance_price": float(candidate.stop_dist),
                "entry_price": float(bars[i].c),
                "r_gross": float(winsorize_R(plain.r_gross)),
                "r_gross_plain": float(winsorize_R(plain.r_gross)),
                "r_gross_live_stop": float(winsorize_R(live.r_gross)),
                "live_stop_own_bars": LIVE_STOP_OWN_BARS,
                "exit_policy": plain.detail.get("policy", "plain"),
                "exit_reason": plain.exit_reason,
                "exit_reason_live_stop": live.exit_reason,
                "mfe_r": round(plain.mfe_r, 6),
                "mae_r": round(plain.mae_r, 6),
                "bars_to_mfe": int(plain.bars_to_mfe),
                "timeframe": int(TF_H4),
                "decision_bar_iso": candidate.decision_bar_iso,
                "decision_day": candidate.decision_day,
                "bar_decision_day": (candidate.features or {}).get("bar_decision_day"),
                "target_dist": (
                    float(candidate.target_dist) if candidate.target_dist is not None else None
                ),
                "intra_size": float(candidate.intra_size or 1.0),
                "vp_loc": candidate.vp_loc,
                "decision_hour": candidate.decision_hour,
                "exit_bar_offset": int(plain.exit_index - i),
                "hold_hours": round((plain.exit_index - i) * H4_MINUTES / 60.0, 4),
                "features": {
                    k: v for k, v in (candidate.features or {}).items() if k != "last_close"
                },
                "m1_profile_day_utc": profile_day.isoformat(),
                "m1_aux_provenance": aux_provenance,
                "thirdparty_caveat": (
                    "Dukascopy Bank BID index-CFD M1, not FTMO bars; costs are FTMO-priced. "
                    "See CI_THIRD_PARTY_OVERLAP_V1.json."
                ),
            }
        )

    old = json.loads(gzip.open(CA_TRADES, "rt"))["trades"][SLEEVE]
    old_key = {(r["symbol"], r["decision_bar_iso"]): round(float(r["r_gross"]), 9) for r in old}
    new_key = {(r["symbol"], r["decision_bar_iso"]): round(float(r["r_gross"]), 9) for r in rows}
    shared = sorted(set(old_key) & set(new_key))
    mismatched = [key for key in shared if old_key[key] != new_key[key]]
    control = {
        "ca_rows": len(old_key),
        "ci_rows": len(new_key),
        "shared_rows": len(shared),
        "ca_rows_missing_from_ci": len(set(old_key) - set(new_key)),
        "shared_r_gross_mismatches": len(mismatched),
        "pass": len(shared) == len(old_key) and not mismatched,
        "reading": (
            "Every CA post-join trade survives with identical decision key and r_gross; the "
            "pre-join population is the only new evidence."
        ),
    }
    if not control["pass"]:
        raise SystemExit(f"CA reproduction control failed: {control}")

    payload = {
        "schema": "gtos.wave15.ci.vp_trades.v1",
        "session": "CI",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "sleeve": SLEEVE,
        "h4_source": str(ARCHIVE),
        "m1_source": str(DATA_ROOT / "gate"),
        "m1_splice_receipt": str(SPLICE_RECEIPT.relative_to(REPO)),
        "population": "full declared on_surface (GER40 and UK100; no member filtered)",
        "maxbars": MAXBARS,
        "live_time_stop_own_bars": LIVE_STOP_OWN_BARS,
        "exit_contract": _live_contract(),
        "fidelity": {
            "class": fidelity_for(SLEEVE).cls.value,
            "live_recall": fidelity_for(SLEEVE).live_recall,
            "scoreable_at_0_50": fidelity_for(SLEEVE).scoreable(0.50),
        },
        "generation_grid": {
            "n_closes_before_blackout": len(grid_all),
            "n_closes_after_blackout": len(grid),
            "first": grid[0].isoformat(),
            "last": grid[-1].isoformat(),
            "march_closes_excluded_before_generation": len(grid_all) - len(grid),
            "evaluations": evaluations,
        },
        "n_candidates_unique": len(candidates),
        "n_duplicates_dropped": duplicates,
        "n_trades": len(rows),
        "n_by_symbol": dict(
            sorted(collections.Counter(r["symbol"] for r in rows).items())
        ),
        "n_by_m1_aux_provenance": dict(
            sorted(collections.Counter(r["m1_aux_provenance"] for r in rows).items())
        ),
        "gross": {
            "sum_r": round(sum(r["r_gross"] for r in rows), 6),
            "mean_r_per_trade": round(statistics.fmean(r["r_gross"] for r in rows), 6),
        },
        "skips": dict(skips),
        "march_protection": {
            "outcome_read": False,
            "input_rows_in_gate_view": 0,
            "decision_closes_excluded_before_generation": len(grid_all) - len(grid),
            "candidate_horizons_refused_before_replay": skips[
                "pre_march_candidate_full_label_horizon_touches_protected_month"
            ],
        },
        "ca_post_join_reproduction_control": control,
        "seconds_total": round(time.time() - t0, 3),
        "trades": {SLEEVE: rows},
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    with OUT.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:
            fh.write(encoded)
    summary = {k: v for k, v in payload.items() if k != "trades"}
    summary["trades_artifact"] = str(OUT.relative_to(REPO))
    summary["trades_artifact_sha256"] = __import__("hashlib").sha256(OUT.read_bytes()).hexdigest()
    SUMMARY_OUT.write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
    print(
        f"wrote {OUT.relative_to(REPO)} n={len(rows):,} "
        f"meanR={payload['gross']['mean_r_per_trade']:+.4f} control={control['pass']}",
        flush=True,
    )
    return payload


if __name__ == "__main__":
    generate()
