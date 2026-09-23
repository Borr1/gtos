#!/usr/bin/env python3
"""Session CH: run the two lever measurements and recalibrate current-book silence.

The economic family is declared by ``ch_declare.py``.  This driver refuses to gate unless
the V25 declaration and protocol are present, never imports a broker client, and never reads
March-2026 OHLC.  Its archive seam decodes each timestamp first and drops the protected month
before indexing the row's price cells.  Candidate lookback and maximum label horizons receive
an additional interval guard, so rows either side of March cannot smuggle its path into a
result.

Stages are intentionally separate.  A failed stage cannot leave a half-written result or a
trial-ledger row, and the outcome stages can be scheduled one at a time while other replay
lanes occupy the machine::

    python3 .../ch_lever_measurements.py --stage p1
    python3 .../ch_lever_measurements.py --stage entry
    python3 .../ch_lever_measurements.py --stage quiet

Nothing here arms, sizes, promotes, or contacts either broker.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import csv
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import random
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.entry_hour import (  # noqa: E402
    deferral_reason,
    parse_entry_hour,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import cost_r, load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import (  # noqa: E402
    GenerationPort,
    InMemoryBarSource,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import TradeRecord  # noqa: E402
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    resolve_rule,
    utc_to_broker_naive,
)
from src.utils.config import apply_profile_overrides  # noqa: E402

PROTOCOL = HERE / "CH_MEASUREMENT_PROTOCOL_V1.json"
FAMILY = HERE / "CANDIDATE_FAMILY_V25.json"
P1_OUT = HERE / "CH_PROMOTION_MILESTONES_V1.json"
ENTRY_OUT = HERE / "CH_JPY_ENTRY_HOUR_GATE_V1.json"
QUIET_OUT = HERE / "CH_QUIET_BOOK_THRESHOLDS_V1.json"
OWNER_OUT = HERE.parent / "OWNER_REQUEST_MX_BTCUSD_P1_HIST.md"

ESTATE = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
    / "AQ_ESTATE_TRADES_V2.json.gz"
)
AU_EXIT = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
    / "AU_EXIT_WIRING_V1.json"
)
COSTS = (
    REPO
    / "research/operations/broker_truth_layer_2026_07_29"
    / "BROKER_TRUE_COSTS_V1_1.json"
)
BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
JPY = Path(
    "/Users/borr/GTOSActive/repo/data/mt5_research_exports/"
    "bridge_ftmo_jpy_m15_20260731"
)
BB_PATH = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
    / "bb_fill_truth.py"
)

FTMO_SERVER = "FTMO-Server3"
FN_SERVER = "redacted_account-Server 2"
MX_BTC = "mx_btcusd_d1_donchian_20_breakout"
MX_MEMBERS = {
    "ETHUSD": "mx_ethusd_d1_donchian_20_breakout",
    "AVAUSD": "mx_avausd_d1_donchian_20_breakout",
    "NZDJPY": "mx_nzdjpy_d1_donchian_20_breakout",
}
SUBMID = "sub_mid_dn_revert"
JPY_SYMBOLS = ("GBPJPY", "CHFJPY", "AUDJPY", "USDJPY", "EURJPY")
CURRENT = {
    "FTMO": ("crypto", "energy_agri", "sub_xvol_pullback", SUBMID, MX_BTC),
    "redacted_account": ("crypto", "energy_agri", "sub_xvol_pullback", SUBMID),
}
BANDS: tuple[str | None, ...] = (None, "low", "mid", "high")
REAL_BANDS = ("low", "mid", "high")
BLACKOUT = (dt.date(2026, 3, 1), dt.date(2026, 3, 31))
ARCHIVE_END = dt.date(2026, 7, 27)
MAX_D1 = 80
MAX_M15 = 1280
TF_D1 = 16408
TF_H4 = 16388
TF_M15 = 15
TF_CODE = {"M15": TF_M15, "H4": TF_H4, "D1": TF_D1}
RANDOM_SEEDS = tuple(20260731 + i for i in range(5))
_NP_FLOAT = re.compile(r"^(?:np\.)?float(?:16|32|64)?\((.*)\)$")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)


def _write(path: Path, body: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(body, indent=1, sort_keys=True, default=str) + "\n")
    print(f"wrote {_rel(path)}", flush=True)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _number(raw: Any) -> float:
    """Parse ordinary floats and the bridge export's literal ``np.float64(...)`` cells."""
    token = str(raw).strip()
    m = _NP_FLOAT.fullmatch(token)
    if m:
        token = m.group(1).strip()
    value = float(token)
    if not math.isfinite(value):
        raise ValueError(f"non-finite price {raw!r}")
    return value


def _in_blackout(day: dt.date) -> bool:
    return BLACKOUT[0] <= day <= BLACKOUT[1]


def interval_hits_blackout(a: dt.datetime | dt.date, b: dt.datetime | dt.date) -> bool:
    """Inclusive calendar intersection; inputs may be in either order."""
    ad = a.date() if isinstance(a, dt.datetime) else a
    bd = b.date() if isinstance(b, dt.datetime) else b
    lo, hi = sorted((ad, bd))
    return not (hi < BLACKOUT[0] or lo > BLACKOUT[1])


@dataclass(frozen=True)
class SafeSeries:
    symbol: str
    timeframe: int
    path: Path
    bars: tuple[Bar, ...]
    times: tuple[dt.datetime, ...]
    sha256: str
    rows_seen: int
    rows_blackout_dropped_before_ohlc: int
    server: str

    def evidence(self) -> dict[str, Any]:
        return {
            "file": str(self.path),
            "sha256": self.sha256,
            "rows_seen": self.rows_seen,
            "rows_usable": len(self.bars),
            "rows_blackout_dropped_before_ohlc": self.rows_blackout_dropped_before_ohlc,
            "server": self.server,
            "first_utc": self.times[0].isoformat() if self.times else None,
            "last_utc": self.times[-1].isoformat() if self.times else None,
        }


def _manifest_expectation(path: Path) -> tuple[str | None, int | None]:
    """Expected hash/count from the archive's own manifest, never from the file itself."""
    if path.parent == JPY:
        doc = json.loads((JPY / "EXPORT_MANIFEST.json").read_text())
        rec = (doc.get("files") or {}).get(path.name.split("_", 1)[0]) or {}
        return rec.get("sha256"), rec.get("rows")
    for name in ("BARS_MANIFEST.json", "BARS_TOPUP_MANIFEST.json", "BARS_TOPUP_M15_MANIFEST.json"):
        p = BARS / name
        if not p.is_file():
            continue
        for rec in json.loads(p.read_text()).get("files") or []:
            if rec.get("file") == path.name:
                return rec.get("sha256"), rec.get("rows")
    return None, None


def load_safe_series(path: Path, *, symbol: str, timeframe: int, server: str) -> SafeSeries:
    """Hash-check and load bars while making March price cells structurally unreachable.

    Time is decoded before ``open/high/low/close`` is indexed.  A malformed price token in a
    protected row is therefore ignored, while the same token outside March fails the run.
    This behavior is pinned by Session CH's tests.
    """
    if not path.is_file():
        raise FileNotFoundError(path)
    side = Path(str(path) + ".timebase.json")
    if not side.is_file():
        raise ValueError(f"{path}: no sanctioned timebase sidecar")
    meta = json.loads(side.read_text())
    declared_server = meta.get("broker") or meta.get("broker_clock_server")
    if declared_server != server:
        raise ValueError(f"{side}: declares {declared_server!r}, expected {server!r}")
    declares = meta.get("declares")
    if declares is not None and declares != path.name:
        raise ValueError(f"{side}: declares {declares!r}, not {path.name!r}")
    basis = meta.get("timebase") or meta.get("time_column_basis")
    if basis not in ("broker_server_wall_clock", "broker_server_local"):
        raise ValueError(f"{side}: unsupported basis {basis!r}")
    expected_sha, expected_rows = _manifest_expectation(path)
    actual_sha = _sha(path)
    if expected_sha and actual_sha != expected_sha:
        raise ValueError(f"{path}: sha256 {actual_sha} != manifest {expected_sha}")

    rule = resolve_rule(server)
    opener = gzip.open if path.name.endswith(".gz") else open
    bars: list[Bar] = []
    times: list[dt.datetime] = []
    seen = skipped = 0
    with opener(path, "rt", newline="") as fh:
        for rec in csv.DictReader(fh):
            seen += 1
            raw_time = str(rec.get("time") or "").strip()
            epoch = float(raw_time)
            # Raw MT5 epochs decode-as-UTC to BROKER WALL.  Check both labels so a DST-edge
            # row cannot enter through disagreement about which calendar named the date.
            broker_wall = dt.datetime.fromtimestamp(epoch, tz=dt.timezone.utc).replace(tzinfo=None)
            stamp = broker_epoch_to_utc(epoch, rule)
            if _in_blackout(broker_wall.date()) or _in_blackout(stamp.date()):
                skipped += 1
                continue  # DO NOT INDEX A SINGLE OHLC CELL ABOVE THIS LINE.
            bars.append(Bar(
                _number(rec["open"]), _number(rec["high"]),
                _number(rec["low"]), _number(rec["close"]),
                _number(rec.get("tick_volume") or rec.get("volume") or 0),
            ))
            times.append(stamp)
    if expected_rows is not None and seen != int(expected_rows):
        raise ValueError(f"{path}: read {seen} rows, manifest declares {expected_rows}")
    if not bars or len(bars) != len(times):
        raise ValueError(f"{path}: no usable safe series")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError(f"{path}: timestamps are not strictly increasing after correction")
    return SafeSeries(symbol, timeframe, path, tuple(bars), tuple(times), actual_sha,
                      seen, skipped, server)


def _index(series: SafeSeries) -> dict[dt.datetime, int]:
    return {t: i for i, t in enumerate(series.times)}


def _intent_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Copy pre-outcome intent fields; never iterate/copy the source mapping wholesale."""
    return {
        "sleeve": row["sleeve"],
        "symbol": row["symbol"],
        "symbol_canonical": row.get("symbol_canonical") or row["symbol"],
        "direction": int(row["direction"]),
        "sl_distance_price": float(row["sl_distance_price"]),
        "target_dist": (float(row["target_dist"]) if row.get("target_dist") is not None else None),
        "decision_bar_iso": row["decision_bar_iso"],
        "decision_day": row["decision_day"],
        "entry_utc": row["entry_utc"],
        "timeframe": int(row["timeframe"]),
    }


def _to_record(row: Mapping[str, Any]) -> TradeRecord:
    return TradeRecord(
        sleeve=str(row["sleeve"]), symbol=str(row["symbol"]),
        entry_utc=dt.datetime.fromisoformat(str(row["entry_utc"])),
        exit_utc=dt.datetime.fromisoformat(str(row["exit_utc"])),
        direction=int(row["direction"]),
        sl_distance_price=float(row["sl_distance_price"]),
        entry_price=float(row["entry_price"]), r_gross=float(row["r_gross"]),
        features={
            "row_id": row.get("row_id"), "member": row.get("member"),
            "symbol_canonical": row.get("symbol_canonical"),
            "decision_day": row.get("decision_day"),
            "decision_bar_iso": row.get("decision_bar_iso"),
            "timeframe": row.get("timeframe"), "arm": row.get("arm"),
            "exit_reason": row.get("exit_reason"),
            "mfe_r": row.get("mfe_r"), "mae_r": row.get("mae_r"),
        },
    )


def _verdict(sv) -> dict[str, Any]:
    folds = [dict(f) for f in (sv.folds or [])]
    recent = [float(f["test_mean_r"]) for f in folds
              if f.get("status") == "evaluable" and f.get("test_mean_r") is not None][-2:]
    return {
        "verdict": sv.verdict.value,
        "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": (sv.gates.get("expectancy") or {}).get("oos_mean_r_per_trade"),
        "p_raw": sv.p_raw,
        "q_value": sv.q_value,
        "coverage": sv.coverage,
        "failing_gates": [k for k, v in sv.gates.items() if not v.get("pass")],
        "folds": folds,
        "recent_two_fold_means": recent,
        "recent_two_fold_mean": statistics.fmean(recent) if len(recent) == 2 else None,
        "reasons": list(sv.reasons),
    }


def _run_one_gate(
    records: Sequence[TradeRecord], *, sleeve: str, account: str, server: str,
    family_id: str, band: str | None, arm: str,
) -> tuple[dict[str, Any], Any]:
    family = CF.load_candidate_family(FAMILY)
    allow = {sleeve: tuple(sorted({r.symbol for r in records}))}
    base = OPTIONS["B_balanced"].with_(
        spec_id=f"wf_gate_B_ch_{arm}_{band or 'flat'}",
        account=account, spread_band=band, sleeve_symbol_allowlist=allow,
    )
    spec = CF.with_declared_family(base, family_id, loaded=family)
    pop, spec, mix = EP.apply(
        "RECORDED", {sleeve: list(records)}, spec, account=account, band=band or "mid"
    )
    result = run_gate(pop, spec, costs=load_broker_true_costs(COSTS),
                      server=server, diagnose=True)
    sv = result.verdicts[sleeve]
    return {
        "band": band or "flat_37_day_snapshot_control",
        "band_is_control": band is None,
        "population": "RECORDED",
        "population_mix": mix,
        "option": "B_balanced",
        "family": family_id,
        "declared_family_size": spec.declared_family_size,
        "declared_family_id": spec.declared_family_id,
        "spec_sha256": spec.seal(),
        **_verdict(sv),
    }, result


def _gate_bands(rows: Sequence[dict[str, Any]], *, sleeve: str, account: str,
                server: str, family_id: str, arm: str) -> tuple[dict[str, Any], dict[str, Any]]:
    records = [_to_record(r) for r in rows]
    summaries, raw = {}, {}
    for band in BANDS:
        label = band or "flat"
        summaries[label], raw[label] = _run_one_gate(
            records, sleeve=sleeve, account=account, server=server,
            family_id=family_id, band=band, arm=arm,
        )
        print(f"  gate {arm:38s} {label:4s}: {summaries[label]['verdict']} "
              f"R/day={summaries[label]['pooled_oos_mean_r']}", flush=True)
    return summaries, raw


def _replay_intent(intent: Mapping[str, Any], series: SafeSeries, i: int, *, target_r: float,
                   maxbars: int, row_id: str, arm: str = "target_5R") -> dict[str, Any]:
    stop = float(intent["sl_distance_price"])
    pol = ExitPolicy(target_dist=target_r * stop, maxbars=maxbars, label=arm)
    pr = replay(series.bars, i, int(intent["direction"]), stop_dist=stop, policy=pol)
    step = dt.timedelta(days=1) if series.timeframe == TF_D1 else dt.timedelta(minutes=15)
    return {
        **dict(intent), "row_id": row_id, "member": str(intent["sleeve"]), "arm": arm,
        "entry_utc": (series.times[i] + step).isoformat(),
        "entry_price": float(series.bars[i].c),
        "exit_utc": (series.times[pr.exit_index] + step).isoformat(),
        "target_dist": target_r * stop,
        "r_gross": float(winsorize_R(pr.r_gross)),
        "exit_reason": pr.exit_reason,
        "mfe_r": pr.mfe_r, "mae_r": pr.mae_r,
    }


def _safe_d1_intents(sleeve: str, symbol: str, series: SafeSeries,
                     source_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict], dict]:
    idx = _index(series)
    out: list[dict] = []
    drops = collections.Counter()
    for n, source in enumerate(source_rows):
        intent = _intent_projection(source)
        t = dt.datetime.fromisoformat(intent["decision_bar_iso"])
        i = idx.get(t)
        if i is None:
            drops["decision_bar_absent"] += 1
            continue
        if i < 19 or i + MAX_D1 >= len(series.bars):
            drops["insufficient_20bar_lookback_or_80bar_forward"] += 1
            continue
        if interval_hits_blackout(series.times[i - 19], series.times[i + MAX_D1]):
            drops["max_path_or_generator_lookback_intersects_march"] += 1
            continue
        out.append(_replay_intent(intent, series, i, target_r=5.0, maxbars=MAX_D1,
                                  row_id=f"{sleeve}:{n}"))
    return out, dict(drops)


def _generate_fn_btc(series: SafeSeries) -> tuple[list[dict], dict]:
    """Port the live mx generator over the redacted_account capture, then label target_5R."""
    base_cfg = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    merged = apply_profile_overrides(base_cfg, "redacted_account")
    runtime = dict(merged.get("gtos_vnext_runtime") or {})
    runtime.update({
        "ultimate_book_include_market_expansion_book": True,
        "ultimate_book_market_expansion_policy": "explicit_allowlist",
        "ultimate_book_market_expansion_sleeves": [MX_BTC],
    })
    source = InMemoryBarSource(label="CH redacted_account BTC D1 March-sanitized")
    source.add("BTCUSD", TF_D1, [
        {"time": t.isoformat(), "open": b.o, "high": b.h, "low": b.l, "close": b.c,
         "volume": b.v}
        for t, b in zip(series.times, series.bars)
    ])
    resolver = build_broker_symbol_resolver(merged)
    port = GenerationPort(runtime, source, namespace="ch_fn_btc", account="redacted_account",
                          broker_symbol=resolver)
    if MX_BTC not in port.active_sleeve_names():
        raise RuntimeError(f"{MX_BTC} is not active in the in-memory replay configuration")
    rows: list[dict] = []
    seen: set[str] = set()
    drops = collections.Counter()
    # Generation at row i+1's open sees i as the most recent closed D1 bar.
    for i in range(19, len(series.bars) - MAX_D1 - 1):
        if interval_hits_blackout(series.times[i - 19], series.times[i + MAX_D1]):
            drops["max_path_or_generator_lookback_intersects_march"] += 1
            continue
        now = series.times[i + 1]
        got = port.generate(now, tags=[MX_BTC])
        for cand in got.candidates:
            if cand.sleeve != MX_BTC or not cand.decision_bar_iso:
                continue
            key = str(cand.decision_bar_iso)
            if key in seen:
                continue
            seen.add(key)
            j = bisect.bisect_left(series.times, dt.datetime.fromisoformat(key))
            if j >= len(series.times) or series.times[j] != dt.datetime.fromisoformat(key):
                drops["generated_decision_bar_absent"] += 1
                continue
            intent = {
                "sleeve": MX_BTC, "symbol": cand.symbol,
                "symbol_canonical": "BTCUSD", "direction": cand.direction,
                "sl_distance_price": cand.stop_dist, "target_dist": cand.target_dist,
                "decision_bar_iso": key, "decision_day": cand.decision_day,
                "entry_utc": (series.times[j] + dt.timedelta(days=1)).isoformat(),
                "timeframe": TF_D1,
            }
            rows.append(_replay_intent(intent, series, j, target_r=5.0, maxbars=MAX_D1,
                                       row_id=f"{MX_BTC}:fn:{key}"))
    return rows, {
        "drops": dict(drops), "n_unique_candidates": len(rows),
        "generation_port": port.describe(),
        "runtime_overrides_in_memory_only": {
            "ultimate_book_include_market_expansion_book": True,
            "ultimate_book_market_expansion_policy": "explicit_allowlist",
            "ultimate_book_market_expansion_sleeves": [MX_BTC],
        },
    }


def _band_passes(gates: Mapping[str, Mapping[str, Any]]) -> int:
    return sum(gates[b].get("verdict") == "ADMIT" for b in REAL_BANDS)


def stage_p1(*, ledger: bool = True) -> dict[str, Any]:
    proto = json.loads(PROTOCOL.read_text())
    if proto.get("multiplicity", {}).get("p1_hist") != 4 or not FAMILY.is_file():
        raise RuntimeError("P1 declaration chain is absent or not the declared four-look family")
    estate = json.loads(gzip.open(ESTATE, "rt").read())
    truth = load_broker_true_costs(COSTS)
    del truth  # load is itself the fail-closed artifact check; gates load the same bytes.
    evidence: dict[str, Any] = {}
    results: dict[str, Any] = {}

    fn_series = load_safe_series(BARS / "redacted_account_BTCUSD_D1.csv.gz", symbol="BTCUSD",
                                 timeframe=TF_D1, server=FN_SERVER)
    fn_rows, fn_meta = _generate_fn_btc(fn_series)
    evidence[MX_BTC] = fn_series.evidence()
    fn_gates, _ = _gate_bands(fn_rows, sleeve=MX_BTC, account="redacted_account",
                              server=FN_SERVER, family_id="CANDIDATE_BOOK_V1",
                              arm="p1_m1_fn_btc_target5")
    results[MX_BTC] = {"rows": len(fn_rows), "generation": fn_meta, "bands": fn_gates}

    for symbol, sleeve in MX_MEMBERS.items():
        series = load_safe_series(BARS / f"FTMO_{symbol}_D1.csv.gz", symbol=symbol,
                                  timeframe=TF_D1, server=FTMO_SERVER)
        rows, drops = _safe_d1_intents(sleeve, symbol, series, estate["trades"][sleeve])
        gates, _ = _gate_bands(rows, sleeve=sleeve, account="FTMO", server=FTMO_SERVER,
                               family_id="CANDIDATE_BOOK_V1", arm=f"p1_m2_{symbol}_target5")
        evidence[sleeve] = series.evidence()
        results[sleeve] = {"rows": len(rows), "drops": drops, "bands": gates}

    m1 = results[MX_BTC]["bands"]
    m1_pass = (_band_passes(m1) >= 2 and (m1["mid"].get("pooled_oos_mean_r") or 0) > 0
               and (m1["mid"].get("recent_two_fold_mean") or 0) > 0)
    ava = MX_MEMBERS["AVAUSD"]
    m2_ne = any(results[ava]["bands"][b]["verdict"] == "NOT_EVALUABLE"
                for b in REAL_BANDS)
    each_positive = all((results[s]["bands"]["mid"].get("pooled_oos_mean_r") or 0) > 0
                        for s in MX_MEMBERS.values())
    each_admits = all(_band_passes(results[s]["bands"]) >= 2 for s in MX_MEMBERS.values())
    m2_state = "UNREACHABLE" if m2_ne else ("PASS" if each_positive and each_admits else "FAIL")

    au = json.loads(AU_EXIT.read_text())
    identity = au["identity"][MX_BTC]
    p = identity["frontier_is_the_research_cell"]
    from src.components.ultimate_book.execution_packets import (  # noqa: PLC0415
        SLEEVE_EXIT_PROFILES,
        time_stop_m15,
    )
    prof = SLEEVE_EXIT_PROFILES[MX_BTC]
    m3_pass = (p["n_shared"] == 318 and p["n_mismatched"] == 0 and p["identical"] is True
               and prof["time_stop_bars"] == time_stop_m15(80, "D1") == 7680)
    recent = {s: results[s]["bands"]["mid"].get("recent_two_fold_mean")
              for s in (MX_BTC, *MX_MEMBERS.values())}
    m4_pass = all(v is not None and v > 0 for v in recent.values())
    all_pass = m1_pass and m2_state == "PASS" and m3_pass and m4_pass
    milestones = {
        "M1_cross_broker": {"state": "PASS" if m1_pass else "FAIL",
                            "admit_bands": _band_passes(m1),
                            "mid_sign": m1["mid"].get("pooled_oos_mean_r"),
                            "recent_two_fold_mean": m1["mid"].get("recent_two_fold_mean")},
        "M2_cross_instrument_mechanism": {
            "state": m2_state, "strict_form_used": True,
            "all_three_mid_positive": each_positive, "all_three_admit_at_least_2_of_3": each_admits,
            "admit_bands": {s: _band_passes(results[s]["bands"]) for s in MX_MEMBERS.values()},
            "AVA_not_evaluable_makes_milestone_unreachable": m2_ne,
        },
        "M3_repair_interaction_persists": {"state": "PASS" if m3_pass else "FAIL",
                                            "au_identity": p, "live_time_stop_bars": prof["time_stop_bars"]},
        "M4_recent_regime": {"state": "PASS" if m4_pass else "FAIL",
                              "recent_two_fold_mean_by_member": recent},
    }
    doc = {
        "schema": "gtos.phase15.ch.p1_hist.v1", "session": "CH", "arms_nothing": True,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol": _rel(PROTOCOL), "protocol_sha256": _sha(PROTOCOL),
        "candidate_family": _rel(FAMILY), "candidate_family_sha256": _sha(FAMILY),
        "march_2026": {"status": "OUTCOME_UNREAD", "reader_order": "timestamp_before_ohlc",
                       "source_rows_dropped": sum(x["rows_blackout_dropped_before_ohlc"]
                                                  for x in evidence.values())},
        "milestones": milestones, "all_historical_milestones_pass": all_pass,
        "false_promotion_arithmetic": {
            "strict_form": "analytic estimate approximately 0.05 if M2 is reachable and passes",
            "loose_form": "analytic bound 0.13..0.35; not substituted by Session CH",
            "status": ("STRICT_FORM_PASSED_APPROX_0p05" if all_pass else
                       ("STRICT_FORM_UNREACHABLE" if m2_state == "UNREACHABLE" else
                        "NO_PROMOTION_ARITHMETIC_TRIGGERED")),
            "not_a_bootstrap_measurement": True,
        },
        "owner_request": ("WRITE_OWNER_PAGE" if all_pass else "NONE"),
        "live_veto": "UNRESOLVED_BY_THIS_OFFLINE_SESSION",
        "evidence": evidence, "members": results,
    }
    _write(P1_OUT, doc)
    if ledger:
        led = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="CH", run_id="CH_P1_HIST_V1")
        for sleeve, item in results.items():
            mid = item["bands"]["mid"]
            led.record(mechanism="p1_hist", sleeve=sleeve,
                       variant={"target_r": 5, "bands": list(REAL_BANDS), "population": "RECORDED"},
                       window="historical archive excluding March path shoulders",
                       outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                "NOT_EVALUABLE": "not_evaluable"}.get(mid["verdict"], "evaluated"),
                       metric=mid.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
                       spec_sha256=mid["spec_sha256"], note="Session CH P1-HIST declared look")
    if all_pass:
        OWNER_OUT.write_text(
            "# Owner request — mx_btcusd P1-HIST weight step\n\n"
            "All four historical milestones in `receipts/CH_PROMOTION_MILESTONES_V1.json` passed. "
            "This requests Borhen's ceremony to consider moving the sleeve from the 0.025 class "
            "toward the 0.05 incubation ceiling. Nothing in Session CH armed, reweighted, or "
            "resolved the required live veto.\n"
        )
    return doc


def _entry_pair(intent: Mapping[str, Any], series: SafeSeries, idx: Mapping[dt.datetime, int],
                row_id: str) -> tuple[dict, dict] | None:
    entry = dt.datetime.fromisoformat(str(intent["entry_utc"]))
    j0 = idx.get(entry - dt.timedelta(minutes=15))
    j1 = idx.get(entry + dt.timedelta(minutes=45))
    if j0 is None or j1 is None or j0 + MAX_M15 >= len(series.bars) or j1 + MAX_M15 >= len(series.bars):
        return None
    decision = dt.datetime.fromisoformat(str(intent["decision_bar_iso"]))
    # 260 H4 bars is the generator's conservative live warmup; +1280 M15 is the exit ceiling.
    # The stored intent's 260 H4-bar warmup spans weekends, so 60 calendar days is the
    # conservative pre-decision shoulder. The forward endpoint is the ACTUAL 1,280th
    # printed M15 bar; 1,280 * 15 wall-clock minutes would undercount weekends.
    forward_end = series.times[j1 + MAX_M15] + dt.timedelta(minutes=15)
    if interval_hits_blackout(decision - dt.timedelta(days=60), forward_end):
        return None
    out = []
    for label, j in (("original", j0), ("shifted", j1)):
        stop = float(intent["sl_distance_price"])
        target = intent.get("target_dist")
        pr = replay(series.bars, j, int(intent["direction"]), stop_dist=stop,
                    policy=ExitPolicy(target_dist=float(target) if target else None,
                                      maxbars=MAX_M15, label=label))
        out.append({
            **dict(intent), "row_id": row_id, "member": str(intent["symbol_canonical"]),
            "entry_utc": (series.times[j] + dt.timedelta(minutes=15)).isoformat(),
            "entry_price": series.bars[j].c,
            "exit_utc": (series.times[pr.exit_index] + dt.timedelta(minutes=15)).isoformat(),
            "r_gross": float(winsorize_R(pr.r_gross)), "exit_reason": pr.exit_reason,
            "mfe_r": pr.mfe_r, "mae_r": pr.mae_r,
        })
    return out[0], out[1]


def _paired_summary(raw: Mapping[str, Any], base_raw: Mapping[str, Any], *,
                    affected_ids: set[str] | None = None) -> dict[str, Any]:
    def priced(result) -> dict[str, Any]:
        out = {}
        for p in result.priced_by_sleeve.get(SUBMID, []):
            if p.status == "priced" and p.r_net is not None:
                out[p.trade.features["row_id"]] = p
        return out
    a, b = priced(raw), priced(base_raw)
    keys = sorted(set(a) & set(b))
    diffs: dict[str, tuple[str, tuple[float, float, float]]] = {}
    for k in keys:
        ap, bp = a[k], b[k]
        member = str(ap.trade.features["member"])
        diffs[k] = (member, (ap.trade.r_gross - bp.trade.r_gross,
                             float(bp.cost_r) - float(ap.cost_r),
                             float(ap.r_net) - float(bp.r_net)))

    def one(vals: Sequence[tuple[float, float, float]]) -> dict:
        return {"n": len(vals),
                "gross_delta_r_per_trade": statistics.fmean(v[0] for v in vals) if vals else None,
                "cost_saved_r_per_trade": statistics.fmean(v[1] for v in vals) if vals else None,
                "net_delta_r_per_trade": statistics.fmean(v[2] for v in vals) if vals else None}
    def pack(selected: Iterable[str]) -> dict[str, Any]:
        by_member: dict[str, list[tuple[float, float, float]]] = collections.defaultdict(list)
        for row_id in selected:
            member, values = diffs[row_id]
            by_member[member].append(values)
        return {"pooled": one([v for vals in by_member.values() for v in vals]),
                "per_member": {m: one(v) for m, v in sorted(by_member.items())}}

    result = pack(keys)
    result["denominator"] = "all gate-priced rows in the matched RECORDED JPY population"
    affected = [k for k in keys if affected_ids is not None and k in affected_ids]
    result["affected_only"] = {
        **pack(affected),
        "denominator": "gate-priced rows shifted by this arm",
    }
    return result


def stage_entry(*, ledger: bool = True) -> dict[str, Any]:
    proto = json.loads(PROTOCOL.read_text())
    arms = list(proto["entry_hour"]["looks"])
    if len(arms) != 8 or not FAMILY.is_file():
        raise RuntimeError("entry-hour declaration chain is absent or not the declared eight looks")
    estate = json.loads(gzip.open(ESTATE, "rt").read())
    costs = load_broker_true_costs(COSTS)
    series = {s: load_safe_series(JPY / f"{s}_M15.csv", symbol=s, timeframe=TF_M15,
                                  server=FTMO_SERVER) for s in JPY_SYMBOLS}
    indices = {s: _index(x) for s, x in series.items()}
    selection = parse_entry_hour(SUBMID, known_sleeves={SUBMID},
                                 timeframe_of={SUBMID: TF_H4})
    pairs: dict[str, tuple[dict, dict]] = {}
    drops = collections.Counter()
    semantics_checked = 0
    for n, source in enumerate(estate["trades"][SUBMID]):
        intent = _intent_projection(source)
        sym = str(intent["symbol_canonical"])
        if sym not in series:
            continue
        pair = _entry_pair(intent, series[sym], indices[sym], f"{sym}:{n}")
        if pair is None:
            drops["not_matched_or_march_path_guard"] += 1
            continue
        original, shifted = pair
        entry = dt.datetime.fromisoformat(original["entry_utc"])
        local = utc_to_broker_naive(entry, resolve_rule(FTMO_SERVER))
        original["broker_entry_hour"] = shifted["broker_entry_hour"] = local.hour
        if local.hour == 0:
            reason = deferral_reason(SUBMID, local, local, selection)
            emitted = deferral_reason(SUBMID, local, local + dt.timedelta(hours=1), selection)
            if reason is None or emitted is not None:
                raise RuntimeError("the replay's h00 shift does not match entry_hour.deferral_reason")
            semantics_checked += 1
        pairs[original["row_id"]] = (original, shifted)
    if not pairs or semantics_checked == 0:
        raise RuntimeError("no matched entry rows or no implemented hour-00 rows")

    all_ids = sorted(pairs)
    by_member = collections.defaultdict(list)
    actual = collections.defaultdict(list)
    entry_spread: dict[str, float] = {}
    for row_id, (orig, _shift) in pairs.items():
        member = str(orig["member"])
        by_member[member].append(row_id)
        if int(orig["broker_entry_hour"]) == 0:
            actual[member].append(row_id)
        b = cost_r(orig["symbol"], "FTMO", 0.0,
                   sl_distance_price=orig["sl_distance_price"],
                   entry_price=orig["entry_price"],
                   side="LONG" if orig["direction"] > 0 else "SHORT",
                   entry_utc=dt.datetime.fromisoformat(orig["entry_utc"]),
                   spread_band="mid", costs=costs)
        entry_spread[row_id] = float(b.spread_r.value)

    shifted_by_arm: dict[str, set[str]] = {"h00_control": set(),
                                           "h01_ratified": {x for v in actual.values() for x in v}}
    inverse: set[str] = set()
    for member, ids in by_member.items():
        inverse.update(sorted(ids, key=lambda x: (entry_spread[x], x))[:len(actual[member])])
    shifted_by_arm["inverse_cheapest_shift_matched"] = inverse
    for k, seed in enumerate(RANDOM_SEEDS):
        rng = random.Random(seed)
        chosen: set[str] = set()
        for member, ids in sorted(by_member.items()):
            chosen.update(rng.sample(sorted(ids), len(actual[member])))
        shifted_by_arm[f"random_shift_matched_s{k}"] = chosen

    gate_summary: dict[str, Any] = {}
    gate_raw: dict[str, Any] = {}
    for arm in arms:
        rs = []
        for row_id in all_ids:
            row = dict(pairs[row_id][1 if row_id in shifted_by_arm[arm] else 0])
            row["arm"] = arm
            rs.append(row)
        gate_summary[arm], gate_raw[arm] = _gate_bands(
            rs, sleeve=SUBMID, account="FTMO", server=FTMO_SERVER,
            family_id="B7_5_SEPARABILITY_MINE_V1", arm=f"entry_{arm}",
        )

    paired: dict[str, Any] = {}
    for arm in arms:
        paired[arm] = {}
        for band in ("flat", *REAL_BANDS):
            paired[arm][band] = _paired_summary(gate_raw[arm][band],
                                                gate_raw["h00_control"][band],
                                                affected_ids=shifted_by_arm[arm])
    h01 = paired["h01_ratified"]
    positive_bands = sum((h01[b]["pooled"].get("net_delta_r_per_trade") or 0) > 0
                         for b in REAL_BANDS)
    mid_delta = h01["mid"]["pooled"].get("net_delta_r_per_trade")
    control_mid = [paired[a]["mid"]["pooled"].get("net_delta_r_per_trade")
                   for a in arms if a not in ("h00_control", "h01_ratified")]
    member_mid = h01["mid"]["per_member"]
    n_member_positive = sum((v.get("net_delta_r_per_trade") or 0) > 0 for v in member_mid.values())
    none_bad = all((v.get("net_delta_r_per_trade") is not None
                    and v["net_delta_r_per_trade"] > -0.10) for v in member_mid.values())
    recent = gate_summary["h01_ratified"]["mid"].get("recent_two_fold_mean")
    beats_all_controls = (mid_delta is not None
                          and all(x is not None and mid_delta > x for x in control_mid))
    recent_positive = recent is not None and recent > 0
    member_rule = n_member_positive >= 4 and none_bad
    economic_rule = positive_bands >= 2 and beats_all_controls and recent_positive and member_rule
    failures = []
    if positive_bands < 2:
        failures.append("positive_net_delta_in_fewer_than_2_of_3_real_bands")
    if not beats_all_controls:
        failures.append("h01_mid_did_not_beat_inverse_and_every_random_control")
    if not recent_positive:
        failures.append("recent_two_fold_mean_not_positive")
    if not member_rule:
        failures.append("fewer_than_4_members_positive_or_member_at_or_below_minus_0p10")

    h01_mid_affected = h01["mid"]["affected_only"]["per_member"]
    h01_mid_all = h01["mid"]["per_member"]
    member_table = {}
    for member in JPY_SYMBOLS:
        changed = h01_mid_affected.get(member) or {}
        all_rows = h01_mid_all.get(member) or {}
        member_table[member] = {
            "matched_rows": len(by_member[member]),
            "hour_00_rows": len(actual[member]),
            "recorded_priced_rows": int(all_rows.get("n") or 0),
            "recorded_priced_hour_00_rows": int(changed.get("n") or 0),
            "gross_delta_r_per_affected_trade": changed.get("gross_delta_r_per_trade"),
            "cost_saved_r_per_affected_trade": changed.get("cost_saved_r_per_trade"),
            "net_delta_r_per_affected_trade": changed.get("net_delta_r_per_trade"),
            "evidence_state": ("MEASURED" if changed.get("n") else
                               "NO_RECORDED_PRICED_HOUR_00_ROW"),
        }
    # The live selector is whole-sleeve. JPY evidence cannot silently authorize metals,
    # oils, indices or BTC entries at reopen, so the current CLI remains off absent transfer.
    recommendation = "DO-NOT-ARM"
    reason = (("declared economic rule failed: " + ", ".join(failures)) if not economic_rule else
              "JPY economic rule passed, but whole-sleeve metals-at-reopen transfer is unmeasured")
    doc = {
        "schema": "gtos.phase15.ch.jpy_entry_hour_gate.v1", "session": "CH",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "arms_nothing": True, "recommendation": recommendation, "recommendation_reason": reason,
        "economic_rule_passed_on_jpy_surface": economic_rule,
        "current_cli_scope": "whole sub_mid_dn_revert sleeve",
        "metals_at_reopen": {"in_jpy_measurement": False, "in_arming_decision_scope": True,
                              "transfer_status": "UNMEASURED"},
        "protocol": _rel(PROTOCOL), "protocol_sha256": _sha(PROTOCOL),
        "candidate_family": _rel(FAMILY), "candidate_family_sha256": _sha(FAMILY),
        "march_2026": {"status": "OUTCOME_UNREAD", "reader_order": "timestamp_before_ohlc",
                       "source_rows_dropped": sum(x.rows_blackout_dropped_before_ohlc
                                                  for x in series.values())},
        "input": {s: x.evidence() for s, x in sorted(series.items())},
        "population": {"n_matched": len(pairs), "n_by_member": {m: len(v) for m, v in by_member.items()},
                       "n_h00_by_member": {m: len(actual[m]) for m in JPY_SYMBOLS},
                       "drops": dict(drops), "implemented_semantics_checked": semantics_checked},
        "per_member_h01_mid": member_table,
        "controls": {a: {"n_shifted": len(shifted_by_arm[a])} for a in arms},
        "bands": gate_summary, "paired_economics_vs_h00": paired,
        "arm_rule_inputs": {"positive_real_bands": positive_bands, "h01_mid_delta": mid_delta,
                            "control_mid_deltas": control_mid,
                            "control_mid_delta_by_arm": {
                                a: paired[a]["mid"]["pooled"].get("net_delta_r_per_trade")
                                for a in arms if a not in ("h00_control", "h01_ratified")
                            },
                            "h01_beats_inverse_and_every_random_control": beats_all_controls,
                            "recent_two_fold_mean": recent,
                            "positive_members_mid": n_member_positive,
                            "members_with_mid_evidence": sorted(member_mid),
                            "members_without_mid_evidence": sorted(set(JPY_SYMBOLS) - set(member_mid)),
                            "no_member_at_or_below_minus_0p10": none_bad,
                            "failed_conditions": failures},
    }
    _write(ENTRY_OUT, doc)
    if ledger:
        led = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="CH", run_id="CH_ENTRY_HOUR_V1")
        for arm in arms:
            mid = gate_summary[arm]["mid"]
            led.record(mechanism="sub_mid_jpy_entry_hour", sleeve=SUBMID,
                       variant={"arm": arm, "matched_population": len(pairs),
                                "bands": list(REAL_BANDS), "population": "RECORDED"},
                       window="fresh FTMO JPY M15 excluding March path shoulders",
                       outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                "NOT_EVALUABLE": "not_evaluable"}.get(mid["verdict"], "evaluated"),
                       metric=mid.get("pooled_oos_mean_r"), metric_name="pooled_oos_mean_r",
                       spec_sha256=mid["spec_sha256"], note="Session CH declared entry-hour look")
    return doc


def _safe_fill_projection(rows: Iterable[Mapping[str, Any]], *, timeframe: int,
                          maxbars: int = 80, lookback: int = 260) -> tuple[list[dict], int]:
    """Project cadence keys, reading ``exit_utc`` only after the March path guard passes."""
    minutes = {TF_M15: 15, TF_H4: 240, TF_D1: 1440}[timeframe]
    out, censored = [], 0
    for row in rows:
        entry = dt.datetime.fromisoformat(str(row["entry_utc"]))
        decision = dt.datetime.fromisoformat(str(row["decision_bar_iso"]))
        if interval_hits_blackout(decision - dt.timedelta(minutes=lookback * minutes),
                                  entry + dt.timedelta(minutes=maxbars * minutes)):
            censored += 1
            continue
        out.append({"sleeve": row["sleeve"], "symbol": row["symbol"],
                    "entry_utc": row["entry_utc"], "exit_utc": row["exit_utc"],
                    "decision_day": row["decision_day"]})
    return out, censored


def calibrate_silence(book_days: Sequence[dt.date], *, start: dt.date, end: dt.date,
                      censored: Sequence[tuple[dt.date, dt.date]], seed: int,
                      n_fills: int | None = None) -> dict:
    """BB's moving-block calibration on a session index with protected spans removed."""
    def allowed(day: dt.date) -> bool:
        return day.weekday() < 5 and not any(a <= day <= b for a, b in censored)
    sessions = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)
                if allowed(start + dt.timedelta(days=i))]
    index = {d: i for i, d in enumerate(sessions)}
    idx = sorted({index[d] for d in book_days if d in index})
    if len(idx) < 3:
        raise RuntimeError("too few uncensored book days for a quiet threshold")
    gaps = [b - a for a, b in zip(idx, idx[1:])]
    series = [1 if i in set(idx) else 0 for i in range(len(sessions))]
    rng = random.Random(seed)
    block = 21
    quantiles = {}
    for p in (0.95, 0.99):
        qs = []
        for _ in range(2000):
            sample: list[int] = []
            while len(sample) < len(series):
                hi = max(1, len(series) - block + 1)
                st = rng.randrange(hi)
                sample.extend(series[st:st + block])
            ii = [i for i, v in enumerate(sample[:len(series)]) if v]
            gg = sorted([b - a for a, b in zip(ii, ii[1:])] or [len(series)])
            qs.append(gg[min(len(gg) - 1, max(0, math.ceil(p * len(gg)) - 1))])
        qs.sort()
        quantiles[str(p)] = {"median": qs[len(qs) // 2], "p05": qs[int(.05 * len(qs))],
                             "p95": qs[int(.95 * len(qs))]}

    def false_per_year(k: int) -> float:
        years = len(sessions) / 252
        return round(sum(g > k for g in gaps) / years, 3) if years else 0.0
    warn, alert = quantiles["0.95"]["median"], quantiles["0.99"]["median"]
    return {
        "window": f"{start.isoformat()}..{end.isoformat()}",
        "weekday_sessions_uncensored": len(sessions), "book_days": len(idx),
        "book_day_density": round(len(idx) / len(sessions), 6),
        "expected_fills_per_week": round((n_fills if n_fills is not None else len(idx))
                                         / len(sessions) * 5, 4),
        "warn_after_silent_weekday_sessions": int(warn),
        "alert_after_silent_weekday_sessions": int(alert),
        "alarm_false_trip_probability": {"warn": 0.05, "alert": 0.01},
        "expected_false_alarms_per_year": {"warn": false_per_year(warn),
                                            "alert": false_per_year(alert)},
        "block_bootstrap": quantiles, "block_sessions": block, "draws": 2000,
        "protected_session_spans_compressed": [[a.isoformat(), b.isoformat()] for a, b in censored],
    }


def stage_quiet() -> dict[str, Any]:
    BB = _load_module("ch_bb_fill_truth", BB_PATH)
    estate = json.loads(gzip.open(ESTATE, "rt").read())
    projected: dict[str, list[dict]] = {}
    censored_rows = collections.Counter()
    for sleeve in set(CURRENT["redacted_account"]):
        tf = TF_CODE[str(estate["timeframe_by_sleeve"][sleeve])]
        rows, n = _safe_fill_projection(estate["trades"][sleeve], timeframe=tf)
        projected[sleeve] = rows
        censored_rows[sleeve] = n
    btc = load_safe_series(BARS / "FTMO_BTCUSD_D1.csv.gz", symbol="BTCUSD",
                           timeframe=TF_D1, server=FTMO_SERVER)
    mx_rows, mx_drops = _safe_d1_intents(MX_BTC, "BTCUSD", btc, estate["trades"][MX_BTC])
    projected[MX_BTC] = [{"sleeve": r["sleeve"], "symbol": r["symbol"],
                          "entry_utc": r["entry_utc"], "exit_utc": r["exit_utc"],
                          "decision_day": r["decision_day"]} for r in mx_rows]

    book_level = {}
    account_detail = {}
    coverage = BB.bar_coverage()
    timeframe_of = dict(estate["timeframe_by_sleeve"])
    timeframe_of[MX_BTC] = "D1"
    # The widest input+label censor is the D1 20-bar lookback and 80-bar forward shoulder.
    protected = [(dt.date(2026, 1, 15), dt.date(2026, 6, 30))]
    for n, (account, sleeves) in enumerate(CURRENT.items()):
        proj = [r for s in sleeves for r in projected[s]]
        occ = BB.occupancy(proj, sleeves)
        filled = set(occ["filled_keys"])
        cadence = BB.cadence(proj, sleeves, coverage, filled, timeframe_of)
        filled_days = sorted({dt.date.fromisoformat(r["decision_day"]) for r in proj
                              if f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}" in filled})
        # BB's own denominator: the last symbol/timeframe bar surface to become available,
        # never the first/last favourable trade. This is the difference between a fill prior
        # and dilution by years when only a subset of the book could have fired.
        full = cadence["book"]["live_equivalent"] or {}
        if not full.get("FULL_SURFACE_from"):
            raise RuntimeError(f"BB cadence found no full-surface start for {account}")
        start = dt.date.fromisoformat(full["FULL_SURFACE_from"])
        n_fills = sum(1 for r in proj
                      if f"{r['sleeve']}|{r['symbol']}|{r['entry_utc']}" in filled
                      and dt.date.fromisoformat(r["decision_day"]) >= start
                      and not any(a <= dt.date.fromisoformat(r["decision_day"]) <= b
                                  for a, b in protected))
        cal = calibrate_silence(filled_days, start=start, end=ARCHIVE_END,
                                censored=protected, seed=20260731 + n, n_fills=n_fills)
        book_level[account] = {
            "armed_set": list(sleeves), "expected_fills_per_week": cal["expected_fills_per_week"],
            "warn_after_silent_weekday_sessions": cal["warn_after_silent_weekday_sessions"],
            "alert_after_silent_weekday_sessions": cal["alert_after_silent_weekday_sessions"],
            "alarm_false_trip_probability": cal["alarm_false_trip_probability"],
            "expected_false_alarms_per_year": cal["expected_false_alarms_per_year"],
            "measured_window": cal["window"], "book_day_density": cal["book_day_density"],
        }
        account_detail[account] = {"occupancy": occ, "cadence": cadence,
                                   "calibration": cal}
    doc = {
        "schema": "gtos.live.quiet_basis.v1", "session": "CH",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provenance": "Session CH current-account-set occupancy plus BB moving-block cadence",
        "arms_nothing": True, "book_level": book_level, "per_account_sleeve": {},
        "account_detail": account_detail,
        "march_2026": {"status": "OUTCOME_UNREAD", "reader_order": "guard before exit_utc/OHLC",
                       "protected_session_spans_compressed": protected},
        "source": {"estate": _rel(ESTATE), "ftmo_btc_target5": btc.evidence(),
                   "mx_drops": mx_drops, "stored_rows_censored_before_exit_read": dict(censored_rows)},
    }
    _write(QUIET_OUT, doc)
    return doc


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stage", choices=("p1", "entry", "quiet"), required=True)
    ap.add_argument("--no-ledger", action="store_true", help="tests/development only")
    ns = ap.parse_args(argv)
    if ns.stage == "p1":
        stage_p1(ledger=not ns.no_ledger)
    elif ns.stage == "entry":
        stage_entry(ledger=not ns.no_ledger)
    else:
        stage_quiet()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
