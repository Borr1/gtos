#!/usr/bin/env python3
"""Lane FB verification walker (FA-continuation Phase A2).

Recomputes Session FB's grid claims FROM RAW INPUTS:
  - January pool  CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz          (27,658 rows)
  - Ordered path  CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1    (streamed line-by-line)
  - Tick sources  wave16 lane registry (4 symbols, sha256-verified)

Mirrors GRID_PROTOCOL.json exactly (D = |entry-stop_loss|; 120-min horizon;
LONG exits bid / SHORT exits ask on ticks; conservative same-M1-bar stop;
gross = target_d/stop_d | -1 | terminal_signed_d/stop_d; net = gross - cost_r/stop_d;
TRAIN = first 13 UTC dates, HOLDOUT = last 8).

Sol receipts are treated as CLAIMS; the pool/sidecar/ticks are the EVIDENCE.
January only: any 2026-02/2026-03 timestamp in the walked surface aborts.
Writes A2_FB_RECOMPUTE_RESULT.json next to itself. Read-only everywhere else.
"""

from __future__ import annotations

import bisect
import datetime as dt
import gzip
import hashlib
import json
import math
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent
RESULT = OUT_DIR / "A2_FB_RECOMPUTE_RESULT.json"

POOL = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/docs/audits/"
    "fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
SIDECAR = Path(
    "/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801/docs/audits/"
    "fable5-vision-audit-20260725/phase18/receipts/pools/"
    "CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
)
TICK_ROOT = Path(
    "/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/ticks/202601"
)
GRID_DIR = Path(
    "/Users/borr/GTOSActive/worktrees/wave19-sol-grid-20260801/research/operations/"
    "wave19_sol_repair_2026_08_01/grid"
)

EXPECTED_POOL_SHA = "ee920fb0e28713f28cf85322d6b6494beef07c27235db9e6ba59dd6e5097fc8f"
EXPECTED_SIDECAR_SHA = "ffa2a2151e79ab81202fab07706f859579e453e0b00784c1e69b381903e9ba61"
EXPECTED_TICK_SHA = {
    "EURUSD": "da4bfe6ddb6380ca3ee86999777c26534a483047b1f6396a87c2c34857a49cd5",
    "USDJPY": "e0338100e5883194b618e7f3ae99605a7d8c3e74c21985c6e5a5b9e082d7dfec",
    "XAGUSD": "ae6133d5f3eb967ed0092cd61d016047d9a635f3aaf401be610c4dd7c1e132ba",
    "XAUUSD": "76cfaed693a6912e4394bbe666e56cd4c2ff26d1ed23b7bac0634dd938f829ce",
}

TOL = 1e-9
INF = np.iinfo(np.int32).max
TARGETS = np.asarray([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0], dtype=np.float64)
STOPS = np.asarray([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0], dtype=np.float64)
HORIZON_MIN = 120
FAMILY_MIN = 500
DIRECTION_MIN = 300
SEED = 20260801
DRAWS = 999

t0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - t0:8.1f}s] {msg}", flush=True)


def peak_gb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024**3)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_utc(value) -> dt.datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise RuntimeError(f"naive_timestamp:{value}")
    return parsed.astimezone(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat()


def epoch_us(value: dt.datetime) -> int:
    return int(round(value.timestamp() * 1_000_000))


def require_january(text: str, ctx: str) -> None:
    if not text.startswith("2026-01"):
        raise RuntimeError(f"non_january_surface:{ctx}:{text}")


def normalize_side(row) -> str:
    seen = []
    for field in ("side", "direction"):
        value = str(row.get(field) or "").strip().upper()
        if value:
            seen.append(value)
    if not seen or any(v not in {"LONG", "SHORT"} for v in seen):
        raise RuntimeError(f"side_invalid:{seen}")
    if len(set(seen)) != 1:
        raise RuntimeError(f"side_direction_disagree:{seen}")
    return seen[0]


# ---------------------------------------------------------------- 1. pool
log("hash-checking pool")
pool_sha = sha256_file(POOL)
if pool_sha != EXPECTED_POOL_SHA:
    raise RuntimeError(f"pool_sha_drift:{pool_sha}")

log("loading pool")
pool_rows: list[dict] = []
with gzip.open(POOL, "rt", encoding="utf-8") as handle:
    for line in handle:
        if line.strip():
            pool_rows.append(json.loads(line))
N = len(pool_rows)
log(f"pool rows: {N}")

entry_arr = np.asarray([float(r["entry_price"]) for r in pool_rows])
stoploss_arr = np.asarray([float(r["stop_loss"]) for r in pool_rows])
cost_arr = np.asarray([float(r["cost_r"]) for r in pool_rows])
netproxy_arr = np.asarray([float(r["opportunity_net_proxy_r"]) for r in pool_rows])
commission_arr = np.asarray([float(r.get("commission_r") or 0.0) for r in pool_rows])
family_list = [str(r.get("origin_family") or "") for r in pool_rows]
side_list = [normalize_side(r) for r in pool_rows]
symbol_list = [str(r["symbol"]) for r in pool_rows]
day_list = [str(r["decision_time_utc"])[:10] for r in pool_rows]
decision_dt = [parse_utc(r["decision_time_utc"]) for r in pool_rows]
composite_keys = [
    (str(r["candidate_id"]), iso(decision_dt[i]), symbol_list[i], side_list[i])
    for i, r in enumerate(pool_rows)
]
for i, r in enumerate(pool_rows):
    require_january(str(r["decision_time_utc"]), f"pool_row_{i}")
if len(set(composite_keys)) != N:
    raise RuntimeError("pool_composite_key_not_unique")
if any(f == "" for f in family_list):
    raise RuntimeError("origin_family_missing")
base_d = np.abs(entry_arr - stoploss_arr)
if np.any(base_d <= 0):
    raise RuntimeError("zero_stop_distance_row")

days_arr = np.asarray(day_list, dtype="U10")
unique_days = sorted(set(day_list))
if len(unique_days) != 21:
    raise RuntimeError(f"trading_day_count:{len(unique_days)}!=21")
train_dates, holdout_dates = unique_days[:13], unique_days[13:]
masks = {
    "TRAIN": np.isin(days_arr, np.asarray(train_dates, dtype="U10")),
    "HOLDOUT": np.isin(days_arr, np.asarray(holdout_dates, dtype="U10")),
    "FULL": np.ones(N, dtype=bool),
}

# FB3 totals from the raw pool
fb3 = {
    "rows": N,
    "net_sum_r": float(np.sum(netproxy_arr)),
    "cost_sum_r": float(np.sum(cost_arr)),
    "gross_sum_r": float(np.sum(netproxy_arr + cost_arr)),
    "train_dates": train_dates,
    "holdout_dates": holdout_dates,
}
log(f"FB3 recompute: net={fb3['net_sum_r']:.7f} cost={fb3['cost_sum_r']:.7f} gross={fb3['gross_sum_r']:.7f}")

# populations (Sol's build_populations mirrored)
families_np = np.asarray(family_list, dtype="U96")
directions_np = np.asarray(side_list, dtype="U5")
populations: list[dict] = []
for family in sorted(set(family_list)):
    fmask = families_np == family
    populations.append(
        {
            "population_id": f"family:{family}",
            "kind": "family",
            "family": family,
            "direction": None,
            "mask": fmask,
            "n": int(fmask.sum()),
            "minimum_n": FAMILY_MIN,
            "eligible": bool(fmask.sum() >= FAMILY_MIN),
        }
    )
    for direction in ("LONG", "SHORT"):
        cmask = np.logical_and(fmask, directions_np == direction)
        if not cmask.any():
            continue
        populations.append(
            {
                "population_id": f"family_direction:{family}|{direction}",
                "kind": "family_direction",
                "family": family,
                "direction": direction,
                "mask": cmask,
                "n": int(cmask.sum()),
                "minimum_n": DIRECTION_MIN,
                "eligible": bool(cmask.sum() >= DIRECTION_MIN),
            }
        )
eligible_pops = [p for p in populations if p["eligible"]]
log(f"populations: {len(populations)} total, {len(eligible_pops)} eligible")

# ---------------------------------------------------------------- 2. sidecar walk
log("hash-checking sidecar")
sidecar_sha = sha256_file(SIDECAR)
if sidecar_sha != EXPECTED_SIDECAR_SHA:
    raise RuntimeError(f"sidecar_sha_drift:{sidecar_sha}")

summaries = {
    o: {
        "tgt": np.full((N, len(TARGETS)), INF, dtype=np.int32),
        "stp": np.full((N, len(STOPS)), INF, dtype=np.int32),
        "term": np.full(N, np.nan, dtype=np.float64),
        "mode": np.full(N, "", dtype="U16"),
    }
    for o in ("as_declared", "inverted")
}

log("streaming sidecar (M1 conservative walk)")
observation_rows_total = 0
with gzip.open(SIDECAR, "rt", encoding="utf-8") as handle:
    index = -1
    for line in handle:
        if not line.strip():
            continue
        index += 1
        row = json.loads(line)
        if row.get("arm_id") != "S0R0":
            raise RuntimeError(f"sidecar_arm:{index}")
        key = (
            str(row.get("candidate_id") or ""),
            str(row.get("decision_time_utc") or ""),
            str(row.get("symbol") or ""),
            normalize_side(row),
        )
        if index >= N or key != composite_keys[index]:
            raise RuntimeError(f"sidecar_key_mismatch:{index}:{key}")
        decision = decision_dt[index]
        horizon = parse_utc(row.get("horizon_end_utc"))
        if horizon != decision + dt.timedelta(minutes=HORIZON_MIN):
            raise RuntimeError(f"sidecar_horizon:{index}")
        obs = row["ordered_path_observations"]
        if not obs:
            raise RuntimeError(f"sidecar_obs_empty:{index}")
        previous = None
        for ob in obs:
            ts = parse_utc(ob["time_utc"])
            require_january(str(ob["time_utc"]), f"obs_{index}")
            if ts <= decision or ts > horizon:
                raise RuntimeError(f"sidecar_obs_window:{index}")
            if previous is not None and ts <= previous:
                raise RuntimeError(f"sidecar_obs_order:{index}")
            previous = ts
        observation_rows_total += len(obs)
        entry = entry_arr[index]
        d = base_d[index]
        high = np.fromiter((float(o_["high"]) for o_ in obs), dtype=np.float64)
        low = np.fromiter((float(o_["low"]) for o_ in obs), dtype=np.float64)
        close = float(obs[-1]["close"])
        # shared building blocks: A = long-favorable run, B = long-adverse run
        run_a = np.maximum.accumulate((high - entry) / d)
        run_b = np.maximum.accumulate((entry - low) / d)
        t_long = (close - entry) / d
        declared = side_list[index]
        for orientation in ("as_declared", "inverted"):
            side = declared if orientation == "as_declared" else ("SHORT" if declared == "LONG" else "LONG")
            if side == "LONG":
                fav, adv, term = run_a, run_b, t_long
            else:
                fav, adv, term = run_b, run_a, -t_long
            n_obs = len(obs)
            ti = np.searchsorted(fav, TARGETS - TOL, side="left")
            si = np.searchsorted(adv, STOPS - TOL, side="left")
            s = summaries[orientation]
            s["tgt"][index] = np.where(ti >= n_obs, INF, ti).astype(np.int32)
            s["stp"][index] = np.where(si >= n_obs, INF, si).astype(np.int32)
            s["term"][index] = term
            s["mode"][index] = "M1_CONSERVATIVE"
        if index % 5000 == 4999:
            log(f"  sidecar row {index + 1}/{N} peak={peak_gb():.2f}GB")
    if index + 1 != N:
        raise RuntimeError(f"sidecar_row_count:{index + 1}!={N}")
log(f"sidecar done: {observation_rows_total} observation rows")

# ---------------------------------------------------------------- 3. tick override
tick_report = {}
symbol_np = np.asarray(symbol_list, dtype="U24")
for symbol in sorted(EXPECTED_TICK_SHA):
    path = TICK_ROOT / symbol / "microstructure_ticks.jsonl"
    digest = sha256_file(path)
    if digest != EXPECTED_TICK_SHA[symbol]:
        raise RuntimeError(f"tick_sha_drift:{symbol}:{digest}")
    log(f"loading ticks {symbol}")
    count = 0
    with path.open("rb") as handle:
        for _ in handle:
            count += 1
    times = np.empty(count, dtype=np.int64)
    bid = np.empty(count, dtype=np.float64)
    ask = np.empty(count, dtype=np.float64)
    pos = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            times[pos] = int(row["time_msc"]) * 1000
            bid[pos] = float(row["bid"])
            ask[pos] = float(row["ask"])
            pos += 1
    times, bid, ask = times[:pos], bid[:pos], ask[:pos]
    if np.any(times[1:] < times[:-1]):
        raise RuntimeError(f"tick_order:{symbol}")
    overridden = fallback = 0
    for index in np.flatnonzero(symbol_np == symbol):
        decision = decision_dt[index]
        horizon = decision + dt.timedelta(minutes=HORIZON_MIN)
        start = int(np.searchsorted(times, epoch_us(decision), side="right"))
        end = int(np.searchsorted(times, epoch_us(horizon), side="right"))
        if start >= end:
            fallback += 1
            continue
        entry = entry_arr[index]
        d = base_d[index]
        declared = side_list[index]
        for orientation in ("as_declared", "inverted"):
            side = declared if orientation == "as_declared" else ("SHORT" if declared == "LONG" else "LONG")
            if side == "LONG":
                signed = (bid[start:end] - entry) / d
            else:
                signed = (entry - ask[start:end]) / d
            fav = np.maximum.accumulate(signed)
            adv = np.maximum.accumulate(-signed)
            n_obs = end - start
            ti = np.searchsorted(fav, TARGETS - TOL, side="left")
            si = np.searchsorted(adv, STOPS - TOL, side="left")
            s = summaries[orientation]
            s["tgt"][index] = np.where(ti >= n_obs, INF, ti).astype(np.int32)
            s["stp"][index] = np.where(si >= n_obs, INF, si).astype(np.int32)
            s["term"][index] = float(signed[-1])
            s["mode"][index] = "ORDERED_TICK"
        overridden += 1
    tick_report[symbol] = {
        "pool_rows": int((symbol_np == symbol).sum()),
        "ordered_tick_rows": overridden,
        "m1_fallback_rows": fallback,
        "source_rows": int(pos),
        "sha256": digest,
    }
    del times, bid, ask
    log(f"  {symbol}: {tick_report[symbol]} peak={peak_gb():.2f}GB")

mode_counts = {
    o: {m: int((summaries[o]["mode"] == m).sum()) for m in ("ORDERED_TICK", "M1_CONSERVATIVE")}
    for o in summaries
}
log(f"source modes: {mode_counts}")

# ---------------------------------------------------------------- 4. cells + comparison
log("loading GRID_FULL_RESULTS.json for comparison")
grid = json.loads((GRID_DIR / "GRID_FULL_RESULTS.json").read_text())
classification = json.loads((GRID_DIR / "FAMILY_CLASSIFICATION.json").read_text())
breaker = json.loads((GRID_DIR / "BREAKER_REDERIVATION.json").read_text())

split_pop_idx: dict[tuple[str, str], np.ndarray] = {}
for population in eligible_pops:
    for split, smask in masks.items():
        split_pop_idx[(population["population_id"], split)] = np.flatnonzero(
            np.logical_and(smask, population["mask"])
        )
full_split_idx = {split: np.flatnonzero(mask) for split, mask in masks.items()}


def cell_arrays(orientation: str, tpos: int, spos: int, target_d: float, stop_d: float):
    s = summaries[orientation]
    ti = s["tgt"][:, tpos]
    si = s["stp"][:, spos]
    target_hit = ti < si
    stop_hit = si < ti
    ambiguous = np.logical_and(ti == si, ti != INF)
    horizon = np.logical_and(ti == INF, si == INF)
    if not np.all(target_hit | stop_hit | ambiguous | horizon):
        raise RuntimeError("outcome_partition_invalid")
    gross = np.where(
        target_hit,
        target_d / stop_d,
        np.where(np.logical_or(stop_hit, ambiguous), -1.0, s["term"] / stop_d),
    )
    net = gross - cost_arr / stop_d
    return gross, net, target_hit, stop_hit, ambiguous, horizon


def split_metrics(gross, net, target_hit, stop_hit, ambiguous, horizon, idx):
    if not len(idx):
        return {"n": 0}
    return {
        "n": int(len(idx)),
        "mean_gross_r": float(np.mean(gross[idx])),
        "mean_net_r": float(np.mean(net[idx])),
        "ambiguous_rows": int(ambiguous[idx].sum()),
        "outcomes": {
            "TARGET": int(target_hit[idx].sum()),
            "STOP": int(stop_hit[idx].sum()),
            "AMBIGUOUS": int(ambiguous[idx].sum()),
            "HORIZON": int(horizon[idx].sum()),
        },
    }


tpos_of = {float(t): i for i, t in enumerate(TARGETS)}
spos_of = {float(s): i for i, s in enumerate(STOPS)}

deviation_max = 0.0
deviation_max_where = None
n_mismatches = []
value_compared = 0
verdict_mismatches = []
train_net_table: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
my_cells: dict[str, dict] = {}

log("evaluating 198 cells and comparing against receipt")
for cell in grid["cells"]:
    cell_id = cell["cell_id"]
    orientation = cell["orientation"]
    target_d = float(cell["target_distance_D"])
    stop_d = float(cell["stop_distance_D"])
    gross, net, th, sh, am, hz = cell_arrays(orientation, tpos_of[target_d], spos_of[stop_d], target_d, stop_d)
    mine_cell = {"full_pool": {}, "populations": {}}
    for split, idx in full_split_idx.items():
        mine = split_metrics(gross, net, th, sh, am, hz, idx)
        theirs = cell["full_pool"]["splits"][split]
        for key in ("mean_gross_r", "mean_net_r"):
            dev = abs(mine[key] - float(theirs[key]))
            value_compared += 1
            if dev > deviation_max:
                deviation_max, deviation_max_where = dev, f"{cell_id}|full_pool|{split}|{key}"
        if mine["n"] != int(theirs["n"]):
            n_mismatches.append(f"{cell_id}|full_pool|{split}")
        mine_cell["full_pool"][split] = mine
    for population in eligible_pops:
        pid = population["population_id"]
        theirs_pop = cell["populations"][pid]
        mine_splits = {}
        for split in ("TRAIN", "HOLDOUT", "FULL"):
            idx = split_pop_idx[(pid, split)]
            mine = split_metrics(gross, net, th, sh, am, hz, idx)
            theirs = theirs_pop["splits"][split]
            for key in ("mean_gross_r", "mean_net_r"):
                dev = abs(mine[key] - float(theirs[key]))
                value_compared += 1
                if dev > deviation_max:
                    deviation_max, deviation_max_where = dev, f"{cell_id}|{pid}|{split}|{key}"
            if mine["n"] != int(theirs["n"]) or mine["ambiguous_rows"] != int(theirs["ambiguous_rows"]):
                n_mismatches.append(f"{cell_id}|{pid}|{split}")
            rec_out = {k: int(v) for k, v in theirs["outcomes"].items()}
            mine_out = {k: v for k, v in mine["outcomes"].items() if v}
            if rec_out != mine_out:
                n_mismatches.append(f"{cell_id}|{pid}|{split}|outcomes")
            mine_splits[split] = mine
        train_net_table[pid][orientation][cell_id] = (
            mine_splits["TRAIN"]["mean_net_r"],
            target_d,
            stop_d,
        )
        # verdict recompute
        tr, ho = mine_splits["TRAIN"], mine_splits["HOLDOUT"]
        if tr["n"] == 0 or ho["n"] == 0:
            verdict = "NOT_EVALUABLE_EMPTY_CHRONOLOGICAL_SPLIT"
        else:
            tn, hn, tg, hg = tr["mean_net_r"], ho["mean_net_r"], tr["mean_gross_r"], ho["mean_gross_r"]
            if tn > 0 and hn > 0:
                verdict = "PERSISTENT_NET_POSITIVE"
            elif tn > 0 and hn <= 0:
                verdict = "TRAIN_ONLY_NET_POSITIVE"
            elif tn <= 0 and hn > 0:
                verdict = "HOLDOUT_ONLY_NET_POSITIVE"
            elif tg > 0 and hg > 0:
                verdict = "PERSISTENT_GROSS_POSITIVE_COST_VETOED"
            else:
                verdict = "NET_NEGATIVE_BOTH_SPLITS"
        if verdict != theirs_pop["verdict"]:
            verdict_mismatches.append(f"{cell_id}|{pid}: mine={verdict} theirs={theirs_pop['verdict']}")
        mine_cell["populations"][pid] = {"verdict": verdict, "splits": mine_splits}
    my_cells[cell_id] = mine_cell
log(
    f"cell sweep done: {value_compared} float values compared, max|dev|={deviation_max:.3e} at {deviation_max_where}; "
    f"n/outcome mismatches={len(n_mismatches)}; verdict mismatches={len(verdict_mismatches)}"
)

# ---------------------------------------------------------------- 5. leaders + classification
def rank_key(item):
    cell_id, (train_net, target_d, stop_d) = item
    return (-train_net, target_d, stop_d, cell_id)


my_leaders: dict[str, dict[str, dict]] = {}
for population in eligible_pops:
    pid = population["population_id"]
    my_leaders[pid] = {}
    for orientation in ("as_declared", "inverted"):
        ranked = sorted(train_net_table[pid][orientation].items(), key=rank_key)
        cell_id, (train_net, target_d, stop_d) = ranked[0]
        my_leaders[pid][orientation] = {
            "cell_id": cell_id,
            "target_distance_D": target_d,
            "stop_distance_D": stop_d,
            "splits": my_cells[cell_id]["populations"][pid]["splits"],
        }

leader_mismatches = []
their_leaders_by_pid = {p["population_id"]: p for p in classification["population_classifications"]}
for pid, by_orientation in my_leaders.items():
    theirs = their_leaders_by_pid[pid].get("orientation_leaders") or {}
    for orientation, mine in by_orientation.items():
        if theirs.get(orientation, {}).get("cell_id") != mine["cell_id"]:
            leader_mismatches.append(
                f"{pid}|{orientation}: mine={mine['cell_id']} theirs={theirs.get(orientation, {}).get('cell_id')}"
            )


def classify(declared, inverted):
    def pnet(leader):
        s = leader["splits"]
        return s["TRAIN"]["mean_net_r"] > 0 and s["HOLDOUT"]["mean_net_r"] > 0

    def pgross(leader):
        s = leader["splits"]
        return s["TRAIN"]["mean_gross_r"] > 0 and s["HOLDOUT"]["mean_gross_r"] > 0

    if pnet(declared):
        return "PERSISTENT_AS_DECLARED_REPAIR"
    if pnet(inverted):
        return "ANTI_PREDICTIVE_INVERTIBLE"
    if pgross(declared) or pgross(inverted):
        return "GROSS_POSITIVE_COST_KILLED"
    values = [
        leader["splits"][split]["mean_gross_r"]
        for leader in (declared, inverted)
        for split in ("TRAIN", "HOLDOUT")
    ]
    if all(v <= 0 for v in values):
        return "DEAD_UNDER_BOTH_ORIENTATIONS"
    return "NOISE"


classification_mismatches = []
my_classifications = {}
for population in populations:
    pid = population["population_id"]
    if not population["eligible"]:
        mine = "NOT_EVALUABLE_BELOW_PREREGISTERED_DENOMINATOR"
    else:
        mine = classify(my_leaders[pid]["as_declared"], my_leaders[pid]["inverted"])
    my_classifications[pid] = mine
    theirs = their_leaders_by_pid[pid]["classification"]
    if mine != theirs:
        classification_mismatches.append(f"{pid}: mine={mine} theirs={theirs}")

family_gpck = sorted(
    p["population_id"]
    for p in populations
    if p["kind"] == "family" and my_classifications[p["population_id"]] == "GROSS_POSITIVE_COST_KILLED"
)
log(f"family-level GROSS_POSITIVE_COST_KILLED (mine): {len(family_gpck)} -> {family_gpck}")

# FB5 detail: the 7 families' leader gross/net splits from MY recompute
fb5_detail = {}
for pid in family_gpck:
    detail = {}
    for orientation, leader in my_leaders[pid].items():
        s = leader["splits"]
        detail[orientation] = {
            "cell_id": leader["cell_id"],
            "TRAIN": {"n": s["TRAIN"]["n"], "mean_gross_r": s["TRAIN"]["mean_gross_r"], "mean_net_r": s["TRAIN"]["mean_net_r"]},
            "HOLDOUT": {"n": s["HOLDOUT"]["n"], "mean_gross_r": s["HOLDOUT"]["mean_gross_r"], "mean_net_r": s["HOLDOUT"]["mean_net_r"]},
            "FULL": {"n": s["FULL"]["n"], "mean_gross_r": s["FULL"]["mean_gross_r"], "mean_net_r": s["FULL"]["mean_net_r"]},
        }
    fb5_detail[pid] = detail

# ---------------------------------------------------------------- 6. max-T
log("max-T control: building candidates")
population_by_id = {p["population_id"]: p for p in populations}
candidates = []
for pid, by_orientation in my_leaders.items():
    population = population_by_id[pid]
    is_breaker = population["family"] == "current_breaker_re_entry"
    for orientation in ("as_declared", "inverted"):
        leader = by_orientation[orientation]
        train_positive = leader["splits"]["TRAIN"]["mean_net_r"] > 0
        if is_breaker or train_positive:
            target_d = leader["target_distance_D"]
            stop_d = leader["stop_distance_D"]
            gross, net, *_ = cell_arrays(
                orientation, tpos_of[target_d], spos_of[stop_d], target_d, stop_d
            )
            train_mask = masks["TRAIN"]
            pop_train = np.logical_and(train_mask, population["mask"])
            baseline = float(np.mean(net[train_mask]))
            observed_mean = float(np.mean(net[pop_train]))
            candidates.append(
                {
                    "leader_id": f"{pid}|{orientation}",
                    "population_id": pid,
                    "cell_id": leader["cell_id"],
                    "orientation": orientation,
                    "vector": net,
                    "baseline_train_mean_net_r": baseline,
                    "observed_population_train_mean_net_r": observed_mean,
                    "observed_train_lift_r": observed_mean - baseline,
                    "population_train_n": int(pop_train.sum()),
                }
            )
log(f"max-T candidates: {len(candidates)} -> {[c['leader_id'] for c in candidates]}")

joint_labels = np.asarray(
    [f"{family_list[i]}|{side_list[i]}" for i in range(N)], dtype="U110"
)
levels = sorted(set(joint_labels.tolist()))
level_to_code = {level: pos for pos, level in enumerate(levels)}
codes = np.asarray([level_to_code[l] for l in joint_labels], dtype=np.int32)
family_codes = {}
for population in populations:
    family = population["family"]
    if family not in family_codes:
        family_codes[family] = np.asarray(
            [level_to_code[l] for l in levels if l.startswith(f"{family}|")], dtype=np.int32
        )
candidate_groups = defaultdict(list)
for candidate in candidates:
    candidate_groups[candidate["population_id"]].append(candidate)

train_indices_by_day = [
    np.flatnonzero(np.logical_and(masks["TRAIN"], days_arr == day))
    for day in sorted(set(days_arr[masks["TRAIN"]].tolist()))
]
rng = np.random.default_rng(SEED)
null_max = np.empty(DRAWS, dtype=np.float64)
log("max-T control: running 999 draws")
for draw in range(DRAWS):
    shuffled = codes.copy()
    for indices in train_indices_by_day:
        shuffled[indices] = rng.permutation(codes[indices])
    draw_max = -math.inf
    for pid, group in candidate_groups.items():
        population = population_by_id[pid]
        if population["kind"] == "family":
            permuted = np.isin(shuffled, family_codes[population["family"]])
        else:
            level = f"{population['family']}|{population['direction']}"
            permuted = shuffled == level_to_code[level]
        permuted_train = np.logical_and(masks["TRAIN"], permuted)
        if not permuted_train.any():
            raise RuntimeError(f"empty_permuted_population:{pid}")
        for candidate in group:
            lift = float(np.mean(candidate["vector"][permuted_train]) - candidate["baseline_train_mean_net_r"])
            draw_max = max(draw_max, lift)
    null_max[draw] = draw_max
    if draw % 200 == 199:
        log(f"  draw {draw + 1}/999")

max_t_mine = []
for candidate in candidates:
    observed = candidate["observed_train_lift_r"]
    p_value = float((1 + np.count_nonzero(null_max >= observed)) / (DRAWS + 1))
    max_t_mine.append(
        {k: v for k, v in candidate.items() if k != "vector"}
        | {"familywise_maxT_p": p_value, "familywise_significant": p_value <= 0.05}
    )
null_mine = {
    "mean": float(np.mean(null_max)),
    "sd": float(np.std(null_max, ddof=1)),
    "q95": float(np.quantile(null_max, 0.95)),
    "min": float(np.min(null_max)),
    "max": float(np.max(null_max)),
}
log(f"null (mine): {null_mine}")

# compare with receipt
their_maxt = breaker["fixed_leader_within_day_max_T"]
maxt_compare = []
theirs_by_leader = {c["leader_id"]: c for c in their_maxt["candidate_leaders"]}
for mine in max_t_mine:
    theirs = theirs_by_leader.get(mine["leader_id"])
    if theirs is None:
        maxt_compare.append({"leader_id": mine["leader_id"], "status": "MISSING_IN_RECEIPT"})
        continue
    maxt_compare.append(
        {
            "leader_id": mine["leader_id"],
            "cell_match": mine["cell_id"] == theirs["cell_id"],
            "lift_mine": mine["observed_train_lift_r"],
            "lift_theirs": theirs["observed_train_lift_r"],
            "lift_absdev": abs(mine["observed_train_lift_r"] - theirs["observed_train_lift_r"]),
            "p_mine": mine["familywise_maxT_p"],
            "p_theirs": theirs["familywise_maxT_p"],
            "p_match": abs(mine["familywise_maxT_p"] - theirs["familywise_maxT_p"]) < 1e-12,
        }
    )
extra_in_receipt = sorted(set(theirs_by_leader) - {m["leader_id"] for m in max_t_mine})

# max-T arithmetic check purely from the receipt cell table
receipt_arithmetic = []
cells_by_id = {c["cell_id"]: c for c in grid["cells"]}
for theirs in their_maxt["candidate_leaders"]:
    cell = cells_by_id[theirs["cell_id"]]
    baseline_from_cells = cell["full_pool"]["splits"]["TRAIN"]["mean_net_r"]
    pop_from_cells = cell["populations"][theirs["population_id"]]["splits"]["TRAIN"]["mean_net_r"]
    receipt_arithmetic.append(
        {
            "leader_id": theirs["leader_id"],
            "baseline_matches_cell_table": abs(baseline_from_cells - theirs["baseline_train_mean_net_r"]) < 1e-12,
            "pop_mean_matches_cell_table": abs(pop_from_cells - theirs["observed_population_train_mean_net_r"]) < 1e-12,
            "lift_equals_difference": abs(
                (pop_from_cells - baseline_from_cells) - theirs["observed_train_lift_r"]
            ) < 1e-12,
        }
    )

# ---------------------------------------------------------------- 7. FB1/FB2 extraction
fb1_mine = my_cells["inverted|target_5D|stop_0.25D"]["populations"]["family:current_breaker_re_entry"]
fb2_mine = my_cells["as_declared|target_1.5D|stop_0.25D"]["populations"]["family:current_ob_retest"]

result = {
    "schema": "gtos.a2_verify.lane_fb.recompute.v1",
    "generated_at_utc": dt.datetime.now(tz=dt.timezone.utc).isoformat(),
    "numpy_version": np.__version__,
    "python_version": sys.version.split()[0],
    "peak_rss_gb": peak_gb(),
    "inputs": {
        "pool_sha256": pool_sha,
        "sidecar_sha256": sidecar_sha,
        "tick_sha256": EXPECTED_TICK_SHA,
        "observation_rows_walked": observation_rows_total,
    },
    "fb3_pool_totals": fb3,
    "tick_override": tick_report,
    "source_mode_counts": mode_counts,
    "cell_sweep": {
        "float_values_compared": value_compared,
        "max_abs_deviation": deviation_max,
        "max_abs_deviation_at": deviation_max_where,
        "n_or_outcome_mismatches": n_mismatches[:50],
        "n_or_outcome_mismatch_count": len(n_mismatches),
        "verdict_mismatches": verdict_mismatches[:50],
        "verdict_mismatch_count": len(verdict_mismatches),
    },
    "fb1_mine": fb1_mine,
    "fb2_mine": fb2_mine,
    "leader_mismatches": leader_mismatches,
    "classification_mismatches": classification_mismatches,
    "my_family_gross_positive_cost_killed": family_gpck,
    "fb5_leader_detail": fb5_detail,
    "max_t": {
        "candidates_mine": [
            {k: v for k, v in c.items() if k != "vector"} for c in candidates
        ],
        "null_mine": null_mine,
        "null_theirs": their_maxt["null"],
        "comparison": maxt_compare,
        "extra_in_receipt": extra_in_receipt,
        "receipt_internal_arithmetic": receipt_arithmetic,
        "p_mine_by_leader": {m["leader_id"]: m["familywise_maxT_p"] for m in max_t_mine},
    },
}
RESULT.write_text(json.dumps(result, indent=1))
log(f"result written to {RESULT}")
log(f"peak RSS: {peak_gb():.2f} GB")
