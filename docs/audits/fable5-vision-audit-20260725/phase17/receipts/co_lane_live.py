#!/usr/bin/env python3
"""Session CO: current-contract learner vector and live-surface economic A/B.

This is offline research tooling. It has no broker import, no order path, and no VPS path.
The raw estate contains rows on surfaces CO is forbidden to consume. The reader therefore
extracts each row's dates from its raw JSON text, classifies the complete label span, and
only then calls ``json.loads``. A refused row's outcome fields are never decoded.

Run from the repository root:

    python3 docs/audits/fable5-vision-audit-20260725/phase17/receipts/co_lane_live.py
"""
from __future__ import annotations

import collections
import csv
import dataclasses
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.learning_actuator import (  # noqa: E402
    SleeveEvidence,
    recommend,
)
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.trainer_partitions import lane_disposition_for_day  # noqa: E402
from src.research_infra.training_lane import IterationLedger  # noqa: E402
from src.research_infra.training_lane.append_only import read_rows  # noqa: E402
from src.research_infra.training_lane.iteration_ledger import (  # noqa: E402
    DEFAULT_ITERATION_LEDGER,
)
from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_stats,
    replay_book,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import (  # noqa: E402
    PricedTrade,
    TradeRecord,
    price_trades,
)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
    resolve_rule,
)


HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "CO_LANE_PROTOCOL_V1.json"
OUT = HERE / "CO_CURRENT_VECTOR_V1.json"
AA_SPLITS = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase6/receipts/"
    "AA_SLEEVE_SPLITS_V1.json"
)
ESTATE = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
    "AQ_ESTATE_TRADES_V2.json.gz"
)
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
CONFIG = REPO / "config/agent_config.yaml"
FTMO_PROFILE = REPO / "config/profiles/operator_profile.yaml"
FN_PROFILE = REPO / "config/profiles/redacted_account.yaml"
BTC_D1 = Path("/Users/borr/GTOSActive/vps-bars-20260727/FTMO_BTCUSD_D1.csv.gz")
CALIBRATION = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
    "LIVE_EVIDENCE_CALIBRATION_V2.json"
)
STOP_CONDITIONS = REPO / (
    "docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
    "FIVE_SLEEVE_STOP_CONDITIONS_V1.json"
)

ACCOUNTS = {
    "FTMO": (
        "crypto",
        "energy_agri",
        "sub_xvol_pullback",
        "sub_mid_dn_revert",
        "mx_btcusd_d1_donchian_20_breakout",
    ),
    "redacted_account": (
        "crypto",
        "energy_agri",
        "sub_xvol_pullback",
        "sub_mid_dn_revert",
    ),
}
REPAIR_SLEEVES = frozenset(("sub_xvol_pullback", "sub_mid_dn_revert"))
MX = "mx_btcusd_d1_donchian_20_breakout"
BAND_MIN = 0.50
BAND_MAX = 1.15
N_MC = 50_000
RUN_ID = "CO_CURRENT_20260801"
LOOK_REVISION = "correction2"
ENGINE_VERSION = "co-current-contract-lane-v1"

_DAY_RE = re.compile(r'"(?:bar_)?decision_day"\s*:\s*"(\d{4}-\d{2}-\d{2})"')
_ENTRY_RE = re.compile(r'"entry_utc"\s*:\s*"([^"\\]+)"')
_EXIT_RE = re.compile(r'"exit_utc"\s*:\s*"([^"\\]+)"')


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    doc = dict(payload)
    doc["self_sha256"] = _sha_payload({k: v for k, v in doc.items() if k != "self_sha256"})
    path.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {_rel(path)} ({path.stat().st_size:,} bytes)")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AD = _load_module(
    "co_ad_exit_sweep",
    REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/ad_exit_sweep.py",
)
Q = _load_module("co_mc_firm_rules", REPO / "scripts/mc_firm_rules.py")


def _skip_ws(text: str, pos: int) -> int:
    while pos < len(text) and (text[pos].isspace() or text[pos] == ","):
        pos += 1
    return pos


def _raw_object(text: str, pos: int) -> tuple[str, int]:
    """Return one raw JSON object without decoding any of its values."""
    if text[pos] != "{":
        raise ValueError(f"expected object at byte {pos}")
    start = pos
    depth = 0
    in_string = False
    escaped = False
    while pos < len(text):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : pos + 1], pos + 1
        pos += 1
    raise ValueError("unterminated JSON object")


def _raw_array(text: str, pos: int) -> tuple[str, int]:
    """Return one raw JSON array without decoding any of its values."""
    if text[pos] != "[":
        raise ValueError(f"expected array at byte {pos}")
    start = pos
    depth = 0
    in_string = False
    escaped = False
    while pos < len(text):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    return text[start : pos + 1], pos + 1
        pos += 1
    raise ValueError("unterminated JSON array")


def _as_date(value: str) -> dt.date:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _calendar_days(lo: dt.date, hi: dt.date) -> Iterable[dt.date]:
    cur = lo
    while cur <= hi:
        yield cur
        cur += dt.timedelta(days=1)


def _iterable_span(raw: str) -> tuple[bool, list[str], str]:
    """Classify the label span before its outcome fields are decoded."""
    dm = _DAY_RE.search(raw)
    em = _ENTRY_RE.search(raw)
    xm = _EXIT_RE.search(raw)
    if not (dm and em and xm):
        return False, [], "missing_predecode_date"
    try:
        decision = dt.date.fromisoformat(dm.group(1))
        entry = _as_date(em.group(1))
        exit_ = _as_date(xm.group(1))
    except ValueError:
        return False, [], "invalid_predecode_date"
    if exit_ < entry:
        return False, [], "reversed_label_span"
    consumed = list(_calendar_days(min(decision, entry), max(decision, exit_)))
    for day in consumed:
        disposition = lane_disposition_for_day(day)
        if not disposition.may_iterate:
            surface = disposition.surface.surface or "GAP"
            return False, [], f"refused_{surface}"
    return True, [d.isoformat() for d in consumed], "safe"


def load_aa_fold_membership(wanted: Sequence[str]) -> dict[str, dict[str, set[dt.date]]]:
    """Read only AA's fold-day arrays; never decode its outcome-bearing sleeve objects.

    The AA artifact co-locates fold membership with ``daily_net_r`` and blackout aggregates.
    Loading the whole document would expose forbidden outcomes merely to recover a calendar.
    This reader isolates the raw sleeve object, isolates its raw ``folds`` array, rejects any
    outcome key in that array, and only then decodes the calendar-only fold records.
    """
    text = AA_SPLITS.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    marker = re.search(r'"sleeves"\s*:\s*\{', text)
    if marker is None:
        raise ValueError("AA split artifact has no sleeves object")
    pos = marker.end()
    wanted_set = set(wanted)
    folds_by_sleeve: dict[str, list[dict[str, Any]]] = {}
    while True:
        pos = _skip_ws(text, pos)
        if text[pos] == "}":
            break
        sleeve, pos = decoder.raw_decode(text, pos)
        pos = _skip_ws(text, pos)
        if text[pos] != ":":
            raise ValueError(f"missing colon after AA sleeve {sleeve!r}")
        pos = _skip_ws(text, pos + 1)
        raw_sleeve, pos = _raw_object(text, pos)
        if sleeve not in wanted_set:
            continue
        fold_marker = re.search(r'"folds"\s*:\s*\[', raw_sleeve)
        if fold_marker is None:
            folds_by_sleeve[sleeve] = []
            continue
        raw_folds, _ = _raw_array(raw_sleeve, fold_marker.end() - 1)
        forbidden = ("daily_net_r", "daily_cost_components", "blackout_r_gross")
        if any(f'"{key}"' in raw_folds for key in forbidden):
            raise ValueError(f"outcome field leaked into AA fold-only span for {sleeve}")
        parsed = json.loads(raw_folds)
        if not isinstance(parsed, list):
            raise ValueError(f"AA folds for {sleeve} are not a list")
        folds_by_sleeve[sleeve] = parsed

    missing = wanted_set - set(folds_by_sleeve)
    if missing:
        raise ValueError(f"AA fold membership missing sleeves: {sorted(missing)}")

    result: dict[str, dict[str, set[dt.date]]] = {}
    for sleeve, folds in folds_by_sleeve.items():
        if len(folds) < 2:
            result[sleeve] = {"train": set(), "oos": set(), "sealed": set()}
            continue
        raw_sets = {
            "train": set(folds[0].get("train_days") or ()),
            "oos": {
                str(day)
                for fold in folds[:-1]
                for day in (fold.get("test_days") or ())
            },
            "sealed": set(folds[-1].get("test_days") or ()),
        }
        memberships: dict[str, set[dt.date]] = {}
        for split, values in raw_sets.items():
            parsed_days = {dt.date.fromisoformat(str(value)) for value in values}
            # The source calendar spans the reserved TEST band. Membership is harmless
            # metadata, but CO's fitting population is its TRAIN/VAL intersection only.
            memberships[split] = {
                day for day in parsed_days if lane_disposition_for_day(day).may_iterate
            }
        overlap = (
            (memberships["train"] & memberships["oos"])
            | (memberships["train"] & memberships["sealed"])
            | (memberships["oos"] & memberships["sealed"])
        )
        if overlap:
            raise ValueError(f"AA fold membership overlaps for {sleeve}")
        result[sleeve] = memberships
    return result


def load_safe_estate(wanted: Sequence[str]) -> tuple[dict[str, list[dict]], dict[str, Any]]:
    """Decode only rows whose complete recorded label span is on TRAIN/VAL."""
    text = gzip.open(ESTATE, "rt", encoding="utf-8").read()
    decoder = json.JSONDecoder()
    pos = text.index("{", text.index('"trades"')) + 1
    wanted_set = set(wanted)
    rows: dict[str, list[dict]] = {s: [] for s in wanted}
    telemetry: dict[str, Any] = {
        s: {"raw_rows": 0, "decoded_safe_rows": 0, "safe_consumed_days": set(), "refused": {}}
        for s in wanted
    }
    while True:
        pos = _skip_ws(text, pos)
        if text[pos] == "}":
            break
        sleeve, pos = decoder.raw_decode(text, pos)
        pos = _skip_ws(text, pos)
        if text[pos] != ":":
            raise ValueError(f"missing colon after sleeve {sleeve!r}")
        pos = _skip_ws(text, pos + 1)
        if text[pos] != "[":
            raise ValueError(f"sleeve {sleeve!r} is not an array")
        pos += 1
        while True:
            pos = _skip_ws(text, pos)
            if text[pos] == "]":
                pos += 1
                break
            raw, pos = _raw_object(text, pos)
            if sleeve not in wanted_set:
                continue
            tel = telemetry[sleeve]
            tel["raw_rows"] += 1
            safe, days, reason = _iterable_span(raw)
            if not safe:
                tel["refused"][reason] = tel["refused"].get(reason, 0) + 1
                continue
            row = json.loads(raw)
            rows[sleeve].append(row)
            tel["decoded_safe_rows"] += 1
            tel["safe_consumed_days"].update(days)
    for sleeve, tel in telemetry.items():
        days = sorted(tel["safe_consumed_days"])
        tel["safe_consumed_days"] = {
            "n": len(days),
            "first": days[0] if days else None,
            "last": days[-1] if days else None,
            "days": days,
        }
        tel["refused"] = dict(sorted(tel["refused"].items()))
    return rows, telemetry


def safe_btc_d1() -> tuple[dict, dict, list[int], dict[str, int]]:
    """Load BTC D1 bars without decoding OHLC on a forbidden date.

    ``segment[i]`` changes after every refused band. A 5R candidate is accepted only when
    its complete 80-bar structural horizon remains inside one safe segment.
    """
    rule = resolve_rule("FTMO-Server3")
    bars: list[Bar] = []
    times: list[dt.datetime] = []
    segments: list[int] = []
    segment = 0
    in_refused = False
    tel = collections.Counter()
    with gzip.open(BTC_D1, "rt", encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh):
            raw_time = (rec.get("time") or "").strip()
            try:
                stamp = broker_epoch_to_utc(float(raw_time), rule)
            except (TypeError, ValueError, OSError, OverflowError):
                tel["unparseable_time"] += 1
                continue
            disposition = lane_disposition_for_day(stamp.date())
            if not disposition.may_iterate:
                tel[f"skipped_{disposition.surface.surface or 'GAP'}"] += 1
                in_refused = True
                continue
            if in_refused:
                segment += 1
                in_refused = False
            try:
                bar = Bar(
                    float(rec["open"]),
                    float(rec["high"]),
                    float(rec["low"]),
                    float(rec["close"]),
                    float(rec.get("tick_volume") or rec.get("volume") or 0.0),
                )
            except (KeyError, TypeError, ValueError):
                tel["unparseable_safe_ohlc"] += 1
                continue
            bars.append(bar)
            times.append(stamp)
            segments.append(segment)
            tel["safe_rows"] += 1
    key = ("BTCUSD", AD.TF_D1)
    return {key: (bars, times)}, {key: {t: i for i, t in enumerate(times)}}, segments, dict(tel)


def target5_rows(rows: Sequence[dict], costs: Any) -> tuple[list[dict], dict[str, Any]]:
    series, index, segments, bar_tel = safe_btc_d1()
    key = ("BTCUSD", AD.TF_D1)
    idx = index[key]
    eligible: list[dict] = []
    refused = collections.Counter()
    for row in rows:
        try:
            i = idx[dt.datetime.fromisoformat(str(row["decision_bar_iso"]))]
        except (KeyError, ValueError):
            refused["decision_bar_not_in_safe_series"] += 1
            continue
        end = i + int(AD.MAXBARS)
        if end >= len(segments):
            refused["structural_horizon_beyond_safe_series"] += 1
            continue
        if segments[i] != segments[end]:
            refused["structural_horizon_crosses_forbidden_segment"] += 1
            continue
        eligible.append(row)
    variant = AD.Variant(
        name="target_5R",
        family="target",
        target_mode="fixed_r",
        target_r=5.0,
        note="current FTMO frontier exit; 80 D1 bar repaired structural horizon",
    )
    out, sim_tel = AD.resimulate(
        eligible,
        variant,
        series,
        index,
        costs,
        "FTMO",
        resolve_rule("FTMO-Server3"),
    )
    return out, {
        "input_safe_rows": len(rows),
        "horizon_safe_rows": len(eligible),
        "resimulated_rows": len(out),
        "refused": dict(sorted(refused.items())),
        "bar_reader": bar_tel,
        "simulation": sim_tel,
    }


def _runtime_contract() -> tuple[dict, dict]:
    text = CONFIG.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text) or {}
    runtime = dict(cfg.get("gtos_vnext_runtime") or {})
    return runtime, {
        "source": _rel(CONFIG),
        "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "global_spread_r": runtime.get("selected_cell_pretrade_max_spread_r"),
        "by_sleeve": runtime.get("selected_cell_pretrade_max_spread_r_by_sleeve") or {},
    }


def _spread_limit(contract: Mapping[str, Any], sleeve: str) -> float:
    by = contract.get("by_sleeve") or {}
    if sleeve in by:
        return float(by[sleeve])
    return float(contract.get("global_spread_r") or 0.10)


def _profile_resolver(path: Path):
    return build_broker_symbol_resolver(yaml.safe_load(path.read_text()) or {})


def _trade_record(row: Mapping[str, Any], resolver) -> TradeRecord:
    canonical = str(row.get("symbol_canonical") or row["symbol"])
    return TradeRecord(
        sleeve=str(row["sleeve"]),
        symbol=resolver(canonical),
        entry_utc=dt.datetime.fromisoformat(str(row["entry_utc"])),
        exit_utc=dt.datetime.fromisoformat(str(row["exit_utc"])),
        direction=int(row["direction"]),
        sl_distance_price=float(row["sl_distance_price"]),
        entry_price=float(row["entry_price"]),
        r_gross=float(row["r_gross"]),
        features={
            "symbol_canonical": canonical,
            "decision_day": str(row.get("decision_day") or row.get("bar_decision_day")),
            "bar_decision_day": str(row.get("bar_decision_day") or row.get("decision_day")),
            "decision_bar_iso": row.get("decision_bar_iso"),
            "timeframe": row.get("timeframe"),
            "hold_hours": row.get("hold_hours"),
            "exit_policy": row.get("exit_policy"),
        },
    )


def price_current_contract(
    rows: Sequence[Mapping[str, Any]],
    *,
    account: str,
    sleeve: str,
    costs: Any,
    contract: Mapping[str, Any],
) -> tuple[list[PricedTrade], dict[str, Any]]:
    resolver = _profile_resolver(FTMO_PROFILE if account == "FTMO" else FN_PROFILE)
    recs = [_trade_record(row, resolver) for row in rows]
    spec = OPTIONS["B_balanced"].with_(
        spec_id=f"co_{account.lower()}_{sleeve}_current_contract",
        account=account,
        spread_band="mid",
    )
    priced, coverage = price_trades(recs, spec, costs=costs)
    cov = coverage.get(sleeve)
    kept: list[PricedTrade] = []
    spread_dropped = 0
    limit = _spread_limit(contract, sleeve)
    for item in priced:
        if item.status != "priced" or item.r_net is None:
            continue
        if sleeve in REPAIR_SLEEVES:
            spread_r = (item.components or {}).get("spread_r")
            if spread_r is None or float(spread_r) > limit:
                spread_dropped += 1
                continue
        kept.append(item)
    return kept, {
        "n_input": len(recs),
        "n_priced_before_current_spread_floor": sum(
            1 for p in priced if p.status == "priced" and p.r_net is not None
        ),
        "n_current_contract": len(kept),
        "n_spread_floor_dropped": spread_dropped,
        "spread_r_limit": limit if sleeve in REPAIR_SLEEVES else None,
        "coverage": ({
            "n_total": cov.n_total,
            "n_priced": cov.n_priced,
            "n_unpriced": cov.n_unpriced,
            "coverage_frac": cov.coverage_frac,
            "measured_frac": cov.measured_frac,
            "unpriced_reasons": cov.unpriced_reasons,
        } if cov is not None else None),
        "spec": {
            "spec_id": spec.spec_id,
            "account": spec.account,
            "spread_band": spec.spread_band,
            "fold_rule": spec.fold_rule,
            "n_folds": spec.n_folds,
        },
    }


def _split_stats(
    priced: Sequence[PricedTrade], days: set[dt.date], *, day_key: str
) -> dict[str, Any]:
    rows = [p for p in priced if p.status == "priced" and p.r_net is not None
            and p.trade.day(day_key) in days]
    vals = [float(p.r_net) for p in rows if p.r_net is not None]
    actual_days = sorted({p.trade.day(day_key) for p in rows})
    return {
        "mean_r": math.fsum(vals) / len(vals) if vals else None,
        "net_r": math.fsum(vals) if vals else 0.0,
        "n_trades": len(vals),
        "n_days": len(actual_days),
        "first_day": actual_days[0].isoformat() if actual_days else None,
        "last_day": actual_days[-1].isoformat() if actual_days else None,
    }


def current_evidence(
    priced: Sequence[PricedTrade], *, account: str, sleeve: str,
    split_days: Mapping[str, set[dt.date]],
) -> tuple[SleeveEvidence, dict[str, Any]]:
    spec = OPTIONS["B_balanced"].with_(
        spec_id=f"co_{account.lower()}_{sleeve}_split",
        account=account,
        spread_band="mid",
    )
    stats = {
        name: _split_stats(priced, days, day_key=spec.day_key)
        for name, days in split_days.items()
    }
    ev = SleeveEvidence(
        sleeve=sleeve,
        train_meanR=stats["train"]["mean_r"],
        oos_meanR=stats["oos"]["mean_r"],
        sealed_meanR=stats["sealed"]["mean_r"],
        train_n=stats["train"]["n_trades"],
        oos_n=stats["oos"]["n_trades"],
        sealed_n=stats["sealed"]["n_trades"],
        train_days=stats["train"]["n_days"],
        oos_days=stats["oos"]["n_days"],
        sealed_days=stats["sealed"]["n_days"],
        status="current_armed_contract",
        evidence_basis=(
            f"cost_true:{_rel(COSTS)}:{account}:mid; safe TRAIN/VAL only; "
            + ("target_5R; " if sleeve == MX else "")
            + ("live_spread_floor; " if sleeve in REPAIR_SLEEVES else "")
            + "production fold builder"
        ),
    )
    detail = {
        "splits": stats,
        "fold_membership_source": _rel(AA_SPLITS),
        "fold_membership_source_sha256": _sha_file(AA_SPLITS),
        "fold_membership": {
            name: {
                "n_iterable_days": len(days),
                "first_day": min(days).isoformat() if days else None,
                "last_day": max(days).isoformat() if days else None,
            }
            for name, days in split_days.items()
        },
        "split_day_membership_sha256": {
            name: _sha_payload(sorted(d.isoformat() for d in days))
            for name, days in split_days.items()
        },
    }
    return ev, detail


def _book_trade(item: PricedTrade) -> BookTrade:
    trade = item.trade
    f = trade.features or {}
    return BookTrade(
        sleeve=trade.sleeve,
        symbol=trade.symbol,
        symbol_canonical=str(f.get("symbol_canonical") or trade.symbol),
        entry_utc=trade.entry_utc,
        exit_utc=trade.exit_utc,
        direction=trade.direction,
        stop_dist=trade.sl_distance_price,
        entry_price=trade.entry_price,
        r_net=float(item.r_net),
        decision_day=str(f.get("decision_day") or trade.entry_utc.date()),
        decision_bar_iso=(str(f.get("decision_bar_iso")) if f.get("decision_bar_iso") else None),
        timeframe=(int(f["timeframe"]) if f.get("timeframe") is not None else None),
        features={"exit_policy": f.get("exit_policy")},
    )


def _week_metrics(series: Mapping[dt.date, float]) -> dict[str, Any]:
    weeks: dict[str, float] = {}
    for day, value in series.items():
        iso = day.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}"
        weeks[key] = weeks.get(key, 0.0) + float(value)
    worst_day = min(series.items(), key=lambda kv: kv[1]) if series else (None, 0.0)
    worst_week = min(weeks.items(), key=lambda kv: kv[1]) if weeks else (None, 0.0)
    return {
        "n_realized_days": len(series),
        "worst_day": worst_day[0].isoformat() if worst_day[0] else None,
        "worst_day_pct": float(worst_day[1]) * 100.0,
        "worst_iso_week": worst_week[0],
        "worst_iso_week_pct": float(worst_week[1]) * 100.0,
    }


def _firm_daily_series(result, account: str) -> dict[dt.date, float]:
    """Realized P&L on the firm's own daily-loss reset calendar."""
    out: dict[dt.date, float] = {}
    server_rule = resolve_rule(
        "FTMO-Server3" if account == "FTMO" else "redacted_account-Server 2"
    )
    for placed in result.placed:
        if "pnl" not in placed:
            continue
        exit_utc = placed["exit_utc"].astimezone(dt.timezone.utc)
        if account == "FTMO":
            offset_h = daily_reset_offset_hours(exit_utc, "europe_prague")
            if offset_h is None:
                raise RuntimeError("FTMO reset calendar unexpectedly unresolved")
        else:
            offset_h = offset_seconds_at_utc(exit_utc, server_rule) / 3600.0
        day = (exit_utc + dt.timedelta(hours=offset_h)).date()
        out[day] = out.get(day, 0.0) + placed["pnl"] / placed["balance_at_entry"]
    return dict(sorted(out.items()))


def _p2(account: str, values: Sequence[float], seed: int) -> dict[str, Any]:
    rule = next(r for r in Q.rule_sets(account)[0] if r.label == "P2_BOTH_PHASES")
    result = Q.mc(list(values), 1.0, rule, N_MC, seed_base=seed)
    p = float(result["p_pass"])
    return {
        "p_pass": p,
        "standard_error": math.sqrt(max(p * (1.0 - p), 0.0) / N_MC),
        "n_paths": N_MC,
        "seed_base": seed,
        "risk_encoding": "book_daily fractional return already includes production sizing; mc risk=1.0",
        "rules": rule.as_dict(),
        "raw": result,
    }


def _book_ab(
    *,
    account: str,
    trades: Sequence[BookTrade],
    weights: Mapping[str, float],
    runtime_base: Mapping[str, Any],
    label_suffix: str,
) -> dict[str, Any]:
    sleeves = ACCOUNTS[account]
    base_runtime = dict(runtime_base)
    base_runtime["ultimate_book_include_clean3"] = True
    base_runtime["ultimate_book_include_market_expansion_book"] = account == "FTMO"
    base_runtime["ultimate_book_market_expansion_policy"] = "explicit_allowlist"
    base_runtime["ultimate_book_market_expansion_sleeves"] = (
        [MX] if account == "FTMO" else []
    )
    base_runtime["ultimate_book_learning_rerate"] = {s: 1.0 for s in sleeves}
    applied_runtime = dict(base_runtime)
    applied_runtime["ultimate_book_learning_rerate"] = dict(weights)
    cfg_common = {
        "sleeves": tuple(sleeves),
        "starting_balance": 100_000.0,
        "floating": "none",
        # Production book_engine hard-wires allocation side A for both namespaces.
        "account_side": "A",
        "reset_rule": "europe_prague" if account == "FTMO" else None,
        "reset_offset_hours": 3.0,
        "broker_clock_server": "FTMO-Server3" if account == "FTMO" else "redacted_account-Server 2",
    }
    baseline = replay_book(
        trades,
        BookConfig(runtime=base_runtime, label=f"co_{account}_baseline_{label_suffix}", **cfg_common),
    )
    applied = replay_book(
        trades,
        BookConfig(runtime=applied_runtime, label=f"co_{account}_applied_{label_suffix}", **cfg_common),
    )
    b_daily = _firm_daily_series(baseline, account)
    a_daily = _firm_daily_series(applied, account)
    if not b_daily or not a_daily:
        raise RuntimeError(
            "CO book replay produced no realized days: "
            + json.dumps(
                {
                    "account": account,
                    "n_candidates": len(trades),
                    "baseline_stats": book_stats(baseline),
                    "baseline_rejections": baseline.rejections,
                    "applied_stats": book_stats(applied),
                    "applied_rejections": applied.rejections,
                },
                sort_keys=True,
                default=str,
            )
        )
    seed = 20260801 + (0 if account == "FTMO" else 1000)
    b_mc = _p2(account, list(b_daily.values()), seed)
    a_mc = _p2(account, list(a_daily.values()), seed)
    pooled_se = math.sqrt(b_mc["standard_error"] ** 2 + a_mc["standard_error"] ** 2)
    delta = a_mc["p_pass"] - b_mc["p_pass"]
    return {
        "account": account,
        "weights": dict(weights),
        "population": {
            "n_candidates": len(trades),
            "first_entry": min(t.entry_utc for t in trades).isoformat() if trades else None,
            "last_exit": max(t.exit_utc for t in trades).isoformat() if trades else None,
            "safe_label_spans_only": True,
            "daily_axis": (
                "Europe/Prague reset day" if account == "FTMO"
                else "redacted_account broker-server reset day (measured US-DST calendar)"
            ),
        },
        "baseline": {
            "stats": book_stats(baseline),
            "tail": _week_metrics(b_daily),
            "mc": b_mc,
        },
        "applied": {
            "stats": book_stats(applied),
            "tail": _week_metrics(a_daily),
            "mc": a_mc,
        },
        "delta": {
            "p_pass": delta,
            "pooled_standard_error": pooled_se,
            "two_se": 2.0 * pooled_se,
            "negative_beyond_noise": delta < -2.0 * pooled_se,
            "worst_day_pct": (
                _week_metrics(a_daily)["worst_day_pct"]
                - _week_metrics(b_daily)["worst_day_pct"]
            ),
            "worst_iso_week_pct": (
                _week_metrics(a_daily)["worst_iso_week_pct"]
                - _week_metrics(b_daily)["worst_iso_week_pct"]
            ),
        },
        "governor_seniority": {
            "baseline_cap_bound_cycles": baseline.diagnostics.get(
                "n_cycles_where_gross_cap_shed_a_unit"
            ),
            "applied_cap_bound_cycles": applied.diagnostics.get(
                "n_cycles_where_gross_cap_shed_a_unit"
            ),
            "baseline_rejections": baseline.rejections,
            "applied_rejections": applied.rejections,
        },
        "consumed_days": sorted({d.isoformat() for d in set(b_daily) | set(a_daily)}),
    }


def _log_once(
    *,
    look_id: str,
    mechanism: str,
    sleeve: str,
    spec: Mapping[str, Any],
    days: Sequence[str],
    verdict: str,
    metric: float | None,
    metric_name: str,
    note: str,
    extra: Mapping[str, Any],
) -> bool:
    existing = {
        str(row.get("extra", {}).get("look_id"))
        for row in read_rows(DEFAULT_ITERATION_LEDGER)
        if row.get("session") == "CO" and isinstance(row.get("extra"), dict)
    }
    if look_id in existing:
        return False
    IterationLedger(
        DEFAULT_ITERATION_LEDGER,
        session="CO",
        run_id=RUN_ID,
    ).record(
        mechanism=mechanism,
        sleeve=sleeve,
        spec=dict(spec),
        days=days,
        engine_version=ENGINE_VERSION,
        verdict=verdict,
        metric=metric,
        metric_name=metric_name,
        note=note,
        receipt=_rel(OUT),
        extra={"look_id": look_id, **dict(extra)},
    )
    return True


def _veto_contract(vectors: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    cal = json.loads(CALIBRATION.read_text())
    stops = json.loads(STOP_CONDITIONS.read_text())
    out: dict[str, Any] = {}
    for account, sleeves in vectors.items():
        acc = {}
        for sleeve, row in sleeves.items():
            c = ((cal.get("accounts") or {}).get(account) or {}).get(sleeve) or {}
            stop_key = f"{account}::{sleeve}"
            s1a = (
                stops.get("conditions", {})
                .get("S1a_risk_floor", {})
                .get("per_sleeve_account", {})
                .get(stop_key)
            )
            acc[sleeve] = {
                "armed_multiplier": row["emitted_multiplier"],
                "neutral_reversal": (
                    "At n>=3 closed fills, live mean R <= 0 blocks every historical size-up "
                    "and emits 1.00 at the next decision-day boundary."
                ),
                "down_weight_first_passage": ({
                    "stop_outs_to_down_weight": c.get("stop_outs_to_down_weight"),
                    "claim": c.get("claim"),
                    "sd": c.get("sd"),
                    "c_down": c.get("c_down"),
                    "boundary_formula": "claim*n - c_down*sd*sqrt(n)",
                    "action": "emit 0.50 at the next decision-day boundary",
                } if c.get("calibrated") else {
                    "calibrated": False,
                    "action": "no inferred brake; use the pre-registered risk floor",
                }),
                "lane_kill": ({
                    "c_kill": c.get("c_kill"),
                    "stop_outs_to_kill": c.get("stop_outs_to_kill"),
                    "action": "hard gate only when the calibrated first-passage kill exists",
                } if c.get("c_kill") is not None else {
                    "calibrated": False,
                    "action": "the lane has no familywise hard-kill boundary for this sleeve",
                }),
                "pre_registered_account_risk_floor": s1a,
            }
        out[account] = acc
    return {
        "declared_before_arming": True,
        "live_forward_role": "VETO_ONLY; never fitting input",
        "evaluation_boundary": "next account decision-day only",
        "cost_requirement": (
            "A live record weaker than MEASURED may brake but may never support or raise a weight."
        ),
        "accounts": out,
        "calibration": _rel(CALIBRATION),
        "calibration_sha256": _sha_file(CALIBRATION),
        "stop_conditions": _rel(STOP_CONDITIONS),
        "stop_conditions_sha256": _sha_file(STOP_CONDITIONS),
    }


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text())
    if not protocol.get("declared_before_outcome_read"):
        raise RuntimeError("CO protocol is not predeclared")
    costs = load_broker_true_costs(COSTS)
    runtime, spread_contract = _runtime_contract()

    safe_rows, source_tel = load_safe_estate(sorted({s for v in ACCOUNTS.values() for s in v}))
    aa_membership = load_aa_fold_membership(
        sorted({s for v in ACCOUNTS.values() for s in v})
    )
    mx_rows, mx_tel = target5_rows(safe_rows[MX], costs)
    safe_rows[MX] = mx_rows

    vectors: dict[str, dict[str, Any]] = {}
    priced_by_account: dict[str, dict[str, list[PricedTrade]]] = {}
    looks_written: list[str] = []
    looks_skipped: list[str] = []

    for account, sleeves in ACCOUNTS.items():
        vectors[account] = {}
        priced_by_account[account] = {}
        for sleeve in sleeves:
            priced, pricing = price_current_contract(
                safe_rows[sleeve],
                account=account,
                sleeve=sleeve,
                costs=costs,
                contract=spread_contract,
            )
            priced_by_account[account][sleeve] = priced
            evidence, detail = current_evidence(
                priced,
                account=account,
                sleeve=sleeve,
                split_days=aa_membership[sleeve],
            )
            rec = recommend(evidence, enabled=True, owner_dial_cap=BAND_MAX)
            emitted = max(BAND_MIN, min(BAND_MAX, float(rec.conf_mult)))
            row = {
                "account": account,
                "sleeve": sleeve,
                "current_contract": (
                    "target_5R" if sleeve == MX else
                    "live_spread_floor" if sleeve in REPAIR_SLEEVES else
                    "as_walked_current_exit"
                ),
                "evidence_basis": evidence.evidence_basis,
                "splits": detail["splits"],
                "fold_membership_source": detail["fold_membership_source"],
                "fold_membership_source_sha256": detail["fold_membership_source_sha256"],
                "fold_membership": detail["fold_membership"],
                "split_day_membership_sha256": detail["split_day_membership_sha256"],
                "pricing": pricing,
                "learner": dataclasses.asdict(rec),
                "raw_recommended_multiplier": rec.conf_mult,
                "emitted_multiplier": emitted,
                "band": [BAND_MIN, BAND_MAX],
                "band_effect": (
                    "hard-gate recommendation converted to bounded 0.50 brake"
                    if rec.conf_mult < BAND_MIN else "none"
                ),
            }
            vectors[account][sleeve] = row
            look_id = f"{RUN_ID}:{LOOK_REVISION}:learner:{account}:{sleeve}"
            decoded_days = source_tel[sleeve]["safe_consumed_days"]["days"]
            written = _log_once(
                look_id=look_id,
                mechanism="current_contract_learning_rerate",
                sleeve=f"{account}::{sleeve}",
                spec={
                    "account": account,
                    "sleeve": sleeve,
                    "contract": row["current_contract"],
                    "band": [BAND_MIN, BAND_MAX],
                    "owner_dial_cap": BAND_MAX,
                    "cost_band": "mid",
                    "protocol_sha256": _sha_file(PROTOCOL),
                },
                days=decoded_days,
                verdict=(
                    "improved" if emitted > 1.0 else
                    "regressed" if emitted < 1.0 else
                    "no_change"
                ),
                metric=emitted,
                metric_name="bounded_current_contract_multiplier",
                note=(
                    f"{rec.verdict}; VAL is used once and is not a fresh holdout. "
                    "Complete label spans were classified before outcome decode; TEST and gaps refused."
                ),
                extra={
                    "recommendation_verdict": rec.verdict,
                    "raw_recommended_multiplier": rec.conf_mult,
                    "splits": detail["splits"],
                    "label_span_safe_before_decode": True,
                },
            )
            (looks_written if written else looks_skipped).append(look_id)
            print(
                f"{account:11s} {sleeve:38s} {rec.verdict:22s} "
                f"raw={rec.conf_mult:.3f} emitted={emitted:.3f} "
                f"priced={pricing['n_current_contract']} "
                f"unpriced={((pricing.get('coverage') or {}).get('unpriced_reasons') or {})}"
            )

    measured_vectors = {
        account: {s: float(row["emitted_multiplier"]) for s, row in rows.items()}
        for account, rows in vectors.items()
    }
    book_trades = {
        account: [
            _book_trade(p)
            for sleeve in ACCOUNTS[account]
            for p in priced_by_account[account][sleeve]
        ]
        for account in ACCOUNTS
    }
    probe_ab = {
        account: _book_ab(
            account=account,
            trades=book_trades[account],
            weights=measured_vectors[account],
            runtime_base=runtime,
            label_suffix="measured",
        )
        for account in ACCOUNTS
    }
    ceremony_vectors = {
        account: (
            {s: min(1.0, w) for s, w in measured_vectors[account].items()}
            if probe_ab[account]["delta"]["negative_beyond_noise"]
            else dict(measured_vectors[account])
        )
        for account in ACCOUNTS
    }
    applied_ab = {
        account: (
            _book_ab(
                account=account,
                trades=book_trades[account],
                weights=ceremony_vectors[account],
                runtime_base=runtime,
                label_suffix="ceremony",
            )
            if ceremony_vectors[account] != measured_vectors[account]
            else probe_ab[account]
        )
        for account in ACCOUNTS
    }

    for account in ACCOUNTS:
        ab = applied_ab[account]
        # correction1 reached this cell only after the pricing and registry defects were
        # repaired, so it is already the valid firm-rule look and remains idempotent.
        look_id = f"{RUN_ID}:correction1:firm_rules:{account}"
        written = _log_once(
            look_id=look_id,
            mechanism="current_contract_lane_book_ab",
            sleeve=f"{account}::CURRENT_ARMED_BOOK",
            spec={
                "account": account,
                "weights": ceremony_vectors[account],
                "n_mc": N_MC,
                "rule": "P2_BOTH_PHASES",
                "negative_beyond_noise_rule": "delta < -2 pooled MC SE",
                "protocol_sha256": _sha_file(PROTOCOL),
            },
            days=ab["consumed_days"],
            verdict=(
                "improved" if ab["delta"]["p_pass"] > 0 else
                "regressed" if ab["delta"]["p_pass"] < 0 else
                "no_change"
            ),
            metric=ab["delta"]["p_pass"],
            metric_name="P2_BOTH_PHASES_p_pass_delta",
            note=(
                "Fixed-vector production-sizer/governor replay. VAL is used once; no live TEST row "
                "or forbidden label span entered the population."
            ),
            extra={
                "p_pass_baseline": ab["baseline"]["mc"]["p_pass"],
                "p_pass_applied": ab["applied"]["mc"]["p_pass"],
                "negative_beyond_noise": ab["delta"]["negative_beyond_noise"],
                "full_measured_vector_suppressed": (
                    ceremony_vectors[account] != measured_vectors[account]
                ),
            },
        )
        (looks_written if written else looks_skipped).append(look_id)

    ledger_rows = read_rows(DEFAULT_ITERATION_LEDGER)
    co_rows = [r for r in ledger_rows if r.get("session") == "CO"]
    doc = {
        "schema": "gtos.phase17.co.current_vector.v1",
        "generated_at_utc": _utc_now(),
        "session": "CO",
        "blocks": "B2800-B2849",
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "protocol": _rel(PROTOCOL),
        "protocol_sha256": _sha_file(PROTOCOL),
        "surface_disclosure": (
            "VAL is the survivor book's used-once selection surface. These figures are a "
            "current-contract rerating, not a fresh holdout claim. TEST is veto-only."
        ),
        "forbidden_outcome_control": {
            "status": "PASS",
            "method": (
                "raw row decision/entry/exit dates classified before json.loads; complete label "
                "span must be TRAIN/VAL. BTC D1 timestamps classified before OHLC conversion; "
                "target_5R complete structural horizon must remain in one safe segment."
            ),
            "estate_reader": source_tel,
            "target5": mx_tel,
        },
        "inputs": {
            _rel(path): _sha_file(path)
            for path in (
                PROTOCOL, ESTATE, AA_SPLITS, COSTS, CONFIG, FTMO_PROFILE, FN_PROFILE, BTC_D1
            )
        },
        "spread_contract": spread_contract,
        "learner_band": {
            "min": BAND_MIN,
            "neutral": 1.0,
            "max": BAND_MAX,
            "theoretical_per_sleeve_relative_change_pct": [-50.0, 15.0],
            "hard_gate_outside_carrier": True,
        },
        "recommendations": vectors,
        "measured_vectors": measured_vectors,
        "probe_ab": probe_ab,
        "ceremony_vectors": ceremony_vectors,
        "applied_ab": applied_ab,
        "decision": {
            account: (
                "DOWN_ONLY_APPLIED_BECAUSE_FULL_VECTOR_NEGATIVE_BEYOND_NOISE"
                if ceremony_vectors[account] != measured_vectors[account]
                else "MEASURED_VECTOR_APPLIED"
            )
            for account in ACCOUNTS
        },
        "live_veto": _veto_contract(vectors),
        "iteration_ledger": {
            "path": _rel(Path(DEFAULT_ITERATION_LEDGER)),
            "sha256": _sha_file(Path(DEFAULT_ITERATION_LEDGER)),
            "predeclared_looks": 11,
            "logical_look_cells": 11,
            "append_rows_for_session": len(co_rows),
            "written_this_run": len(looks_written),
            "idempotently_skipped": len(looks_skipped),
            "session_co_rows_after": len(co_rows),
            "all_unbilled": all(r.get("billed") is False for r in co_rows),
            "looks_written": looks_written,
            "looks_skipped": looks_skipped,
            "correction_history": {
                "reason": (
                    "The first two preprocessing attempts produced zero priced rows: the first "
                    "also keyed AA membership on entry rather than decision day; both ran before "
                    "the sparse spread-model dependency was materialized. Append-only rows were "
                    "retained, are unbilled, and are superseded rather than rewritten."
                ),
                "superseded_learner_prefixes": [
                    f"{RUN_ID}:learner:",
                    f"{RUN_ID}:correction1:learner:",
                ],
                "effective_learner_prefix": f"{RUN_ID}:correction2:learner:",
                "effective_firm_rule_prefix": f"{RUN_ID}:correction1:firm_rules:",
                "additional_hypothesis_looks": 0,
                "family_ratchet_effect": "none",
            },
        },
        "runtime_boundary": {
            "weights_are_input_to_existing_pre_governor_learning_rerate_seam": True,
            "production_sizer_and_governor_used_in_ab": True,
            "breach_flatten_not_modified": True,
            "no_config_bytes_modified": True,
            "no_broker_or_vps_path_called": True,
        },
    }
    _write(OUT, doc)
    for account, ab in applied_ab.items():
        print(
            f"{account:11s} p_pass {ab['baseline']['mc']['p_pass']:.5f} -> "
            f"{ab['applied']['mc']['p_pass']:.5f} "
            f"delta={ab['delta']['p_pass']:+.5f} "
            f"two_se={ab['delta']['two_se']:.5f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
