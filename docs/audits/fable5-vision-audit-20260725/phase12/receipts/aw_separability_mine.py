#!/usr/bin/env python3
"""Session AW — the separability mine (B1750-B1799).

    python3 docs/audits/fable5-vision-audit-20260725/phase12/receipts/aw_separability_mine.py \
        --stage census     # feature census + alias detection + the cost charge model
    ... --stage declare    # SEAL the protocol and the family, BEFORE any outcome is read
    ... --stage mine       # the funnel: TRAIN -> HOLDOUT -> APRIL -> arm stability
    ... --stage model      # the separability CEILING: what a fitted model can do
    ... --stage all

THE QUESTION, AND WHY IT IS OPEN
--------------------------------
`JANUARY_BANK.md` §3, on the sealed January reference arm S0R0: the diagnostic pool carries
**+6,916.95 R over 8,006 positive rows against −31,400.82 R over 20,513 negative rows**, and
the campaign only ever tested whether the incumbent's **two pre-registered binary switches**
separate them. They did not, measurably (`selection` = −0.0491, inside the sealed ±0.1 band).
Whether ANY rule separates the pool is, in the bank's own words, *"open and unmeasured at any
useful resolution"*. Borhen, 2026-07-30: *"maybe there was something wrong, maybe if with some
fixes it becomes positive."* This measures it.

THE BAR, STATED BEFORE THE FIRST LOOK
--------------------------------------
The pool is **asymmetric**, and the "±38,317 R of separable opportunity" framing conceals it.
Winners average **+0.864 R**; losers average **−1.531 R**. A rule that SELECTS rows therefore
has to be right **63.9 %** of the time to break even, against a base rate of **28.1 %**. That
is a 2.28× precision lift, not a nudge, and it is the number every cell below is judged
against. It is computed by `b7_5_diagnostic_pool.pool_summary()` so it cannot drift.

WHAT IS CHARGED, AND WHY IT IS NOT THE LEDGER'S OWN COST
--------------------------------------------------------
The row's `opportunity_net_proxy_r` is already net of the replay's broker-calibrated cost
(`cost_r` = spread + slippage + swap, per row). Two known defects are charged ON TOP:

* **F31** — the replay's exit model grants exactly zero gap-through. Measured over the 212
  covered level-exit rows of the four sealed arms: **−0.038186 R/row**, adverse on 204 of
  212, and a LOWER bound (`GATE_G1A_RECEIPT.md` §4). Charged on level exits only.
* **F38** — `broker_net_cost_engine.py:577-583` sums spread + slippage + swap and charges
  **zero commission**. The census below confirms it in this window: `commission_r` is
  identically 0.0 on all 28,519 rows. Broker truth says that is right for some instruments
  and wrong for others (US500.cash is a MEASURED zero; XAUUSD is 0.140055 bp of notional),
  so the charge is per-instrument from `BROKER_TRUE_COSTS_V1.json`, never a constant.

`net_r_aw = opportunity_net_proxy_r + f31_level_charge − broker_true_commission_r`.
The raw column travels beside it everywhere so the two are always comparable.

THE MULTIPLICITY DISCIPLINE
---------------------------
`--stage declare` writes the cell list — every axis, every cut, by name — and its sha256,
into `AW_MINE_PROTOCOL_V1.json` and into a new `B7_5_SEPARABILITY_MINE_V1` family in
`CANDIDATE_FAMILY_V7.json`. `--stage mine` refuses to run if the protocol's re-derived cell
hash does not match the sealed one. The cut rules are derived from the TRAIN split only and
from feature distributions only — no outcome is read by `declare`, which is what makes the
declaration honest rather than decorative.

An axis that carries fewer than two distinct values tests no hypothesis and is declared
`look_taken=False` with the distinct-value count as its evidence — the same rule
`candidate_family.Member` already applies to a zero-trade sleeve. Exact aliases (same
partition of the rows under a different label, e.g. `origin_family` / `route_family` /
`framework`) are ONE member, not three: a repeated row *"would inflate the bill without a
look having been taken"*.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import (  # noqa: E402
    CostTruthError,
    _usd_per_price_unit_per_lot,
    commission_usd_per_lot,
    load_broker_true_costs,
)
from src.research_infra import b7_5_diagnostic_pool as DP  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
POOL = HERE / ".aw_diagnostic_pool_v1.jsonl.gz"
CENSUS_OUT = HERE / "AW_FEATURE_CENSUS_V1.json"
PROTOCOL_OUT = HERE / "AW_MINE_PROTOCOL_V1.json"
FAMILY_V6 = HERE / "CANDIDATE_FAMILY_V6.json"
FAMILY_V7 = HERE / "CANDIDATE_FAMILY_V7.json"
MAP_OUT = HERE / "AW_SEPARABILITY_MAP_V1.json"
GROSS_OUT = HERE / "AW_GROSS_VIEW_V1.json"
FAMILY_V8 = HERE / "CANDIDATE_FAMILY_V8.json"
MODEL_OUT = HERE / "AW_MODEL_CEILING_V1.json"
COSTS_V1 = REPO / "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"

PRIMARY_ARM = "S0R0"
STABILITY_ARMS = ("S1R0", "S0R1", "S1R1")
APRIL_ARM = "APR_S1R1_PARTIAL"

#: The split. Chronological, declared here and nowhere else. January's diagnostic pool spans
#: 21 trading days; the first 13 are TRAIN and the last 8 are HOLDOUT (61.9 % / 38.1 %).
#: Chronological rather than random because a random split over a single month leaks the
#: month's own regime into both sides, and every wave-11/12 standard is chronological.
N_TRAIN_DAYS = 13

#: Cut rules. One per kind, fixed before the data is seen.
MIN_CELL_TRAIN_ROWS = 200
MIN_CELL_HOLDOUT_ROWS = 100
MIN_CELL_APRIL_ROWS = 100
NUMERIC_CUT = "train_tertiles"          # q33 / q67 computed on TRAIN only
CATEGORICAL_CUT = "level_wise"          # one cell per level with >= MIN_CELL_TRAIN_ROWS
TOP_K_FOR_INTERACTIONS = 8              # crossed pairwise -> at most 28 interaction cells

#: Axes deliberately NOT screened, with the reason. Raw prices are not comparable across a
#: 24-symbol surface (XAUUSD ~ 2,600 against EURUSD ~ 1.09); they enter only through the
#: unitless derivations `stop_distance_frac` and `rr_ratio`.
EXCLUDED_AXES = {
    "entry_price": "raw price, not comparable across the 24-symbol surface",
    "stop_loss": "raw price, not comparable across the 24-symbol surface",
    "take_profit_1": "raw price, not comparable across the 24-symbol surface",
}

SCHEMA_PROTOCOL = "gtos.aw.separability_mine_protocol.v1"
SCHEMA_CENSUS = "gtos.aw.feature_census.v1"
SCHEMA_MAP = "gtos.aw.separability_map.v1"


# ---------------------------------------------------------------------------------------
# shared
# ---------------------------------------------------------------------------------------


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    payload = dict(payload)
    payload["self_sha256"] = _sha({k: v for k, v in payload.items() if k != "self_sha256"})
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)}  ({path.stat().st_size:,} bytes)")


def load_frame() -> pd.DataFrame:
    if not POOL.is_file():
        raise SystemExit(
            f"pool not built: {POOL}\n"
            "build it with:  python3 -c \"import sys;sys.path.insert(0,'.');"
            "from src.research_infra import b7_5_diagnostic_pool as DP;"
            f"DP.build_pool(list(DP.JANUARY_ARMS)+['{APRIL_ARM}'],out_path='{POOL}')\""
        )
    df = pd.DataFrame(DP.load_pool(POOL))
    df["trading_day"] = df["trading_day"].astype(str)
    return df


# ---------------------------------------------------------------------------------------
# the cost charge (F31 + F38)
# ---------------------------------------------------------------------------------------


def commission_charge(df: pd.DataFrame) -> tuple[pd.Series, dict]:
    """Broker-true round-turn commission in R, per row. F38's missing term.

    `commission_r = commission_usd_per_lot / (sl_distance_price * usd_per_price_unit_per_lot)`
    — `src/costs/model.py:16`. The commission is a property of the TRADE, not of the
    instrument, because the R denominator is the stop distance.
    """

    profile = yaml.safe_load((REPO / "config/profiles/operator_profile.yaml").read_text())
    resolve = build_broker_symbol_resolver(profile or {})
    costs = load_broker_true_costs(COSTS_V1)

    per_symbol: dict[str, dict] = {}
    for canonical in sorted(df["symbol"].dropna().unique()):
        broker = resolve(canonical)
        try:
            rec = costs.instrument("FTMO", broker)
        except CostTruthError as exc:
            per_symbol[canonical] = {"broker_symbol": broker, "error": str(exc)[:160]}
            continue
        per_symbol[canonical] = {
            "broker_symbol": broker,
            "kind": rec["commission"]["kind"],
            "coverage": rec["commission"]["coverage"],
            "usd_per_price_unit_per_lot": _usd_per_price_unit_per_lot(rec),
            "rec": rec,
        }

    values = np.zeros(len(df), dtype=float)
    unpriced = 0
    for i, (canonical, entry, stop) in enumerate(
        zip(df["symbol"].to_numpy(), df["entry_price"].to_numpy(), df["stop_loss"].to_numpy())
    ):
        meta = per_symbol.get(canonical)
        if meta is None or "rec" in meta is None or "error" in meta:
            unpriced += 1
            continue
        sl = abs(float(entry) - float(stop)) if (entry is not None and stop is not None) else 0.0
        if not sl:
            unpriced += 1
            continue
        usd, _ = commission_usd_per_lot(meta["rec"], float(entry))
        values[i] = usd / (sl * meta["usd_per_price_unit_per_lot"])

    summary = {
        "artifact": str(COSTS_V1.relative_to(REPO)),
        "account": "FTMO",
        "unpriced_rows": unpriced,
        "per_symbol": {
            k: {kk: vv for kk, vv in v.items() if kk != "rec"} for k, v in per_symbol.items()
        },
    }
    return pd.Series(values, index=df.index), summary


def charge(df: pd.DataFrame) -> pd.DataFrame:
    """Attach `commission_r_broker_true` and the primary outcome `net_r_aw`."""

    comm, meta = commission_charge(df)
    df = df.copy()
    df["commission_r_broker_true"] = comm
    df["net_r_aw"] = df["outcome_net_proxy_r_f31"].astype(float) - comm
    df.attrs["commission_meta"] = meta
    return df


# ---------------------------------------------------------------------------------------
# stage: census
# ---------------------------------------------------------------------------------------


def _partition_signature(series: pd.Series) -> str:
    """Hash the PARTITION a column induces, not its labels.

    `origin_family` and `framework` carry different strings (`current_fvg_fill` /
    `fvg_fill`) for the same 10 groups of rows. They test one hypothesis, so they are one
    member of the family. Relabelling by first-appearance order makes that visible.
    """

    order: dict = {}
    codes = []
    for value in series.tolist():
        if isinstance(value, float) and math.isnan(value):
            value = None
        if value not in order:
            order[value] = len(order)
        codes.append(order[value])
    return hashlib.sha256(
        np.asarray(codes, dtype=np.int32).tobytes() + str(len(order)).encode()
    ).hexdigest()


def stage_census(df: pd.DataFrame) -> dict:
    jan = df[df.arm_id == PRIMARY_ARM]
    axes = {}
    sig_groups: dict[str, list[str]] = {}
    for f in DP.FEATURE_FIELDS:
        s = jan[f.name]
        nuniq = int(s.nunique(dropna=True))
        entry = {
            "family": f.family,
            "kind": f.kind,
            "n_distinct": nuniq,
            "n_null": int(s.isna().sum()),
            "excluded": EXCLUDED_AXES.get(f.name),
            "partition_sha256": _partition_signature(s),
        }
        if f.kind in ("cat", "bool"):
            entry["levels"] = {
                str(k): int(v)
                for k, v in collections.Counter(s.dropna().astype(str)).most_common(40)
            }
        else:
            d = pd.to_numeric(s, errors="coerce").dropna()
            if len(d):
                entry["quantiles"] = {
                    q: float(d.quantile(v))
                    for q, v in (("min", 0.0), ("q33", 1 / 3), ("q50", 0.5),
                                 ("q67", 2 / 3), ("max", 1.0))
                }
        axes[f.name] = entry
        sig_groups.setdefault(entry["partition_sha256"], []).append(f.name)

    aliases = {names[0]: names[1:] for names in sig_groups.values() if len(names) > 1}
    degenerate = {n: a["n_distinct"] for n, a in axes.items() if a["n_distinct"] < 2}

    charged = charge(jan)
    return {
        "schema": SCHEMA_CENSUS,
        "primary_arm": PRIMARY_ARM,
        "rows": int(len(jan)),
        "trading_days": sorted(jan["trading_day"].unique().tolist()),
        "axes": axes,
        "alias_groups": aliases,
        "alias_note": (
            "Grouped by the PARTITION each column induces, not by value equality: "
            "origin_family / route_family / framework label the same 10 groups of rows "
            "differently. One partition == one hypothesis == one family member."
        ),
        "degenerate_axes": degenerate,
        "degenerate_note": (
            "Fewer than two distinct values -> no hypothesis is testable. Declared "
            "look_taken=False, the same rule candidate_family.Member applies to a "
            "zero-trade sleeve."
        ),
        "excluded_axes": EXCLUDED_AXES,
        "pool_summary_raw": DP.pool_summary(
            jan.to_dict("records"), outcome="outcome_net_proxy_r"
        ),
        "pool_summary_f31": DP.pool_summary(
            jan.to_dict("records"), outcome="outcome_net_proxy_r_f31"
        ),
        "pool_summary_aw": DP.pool_summary(charged.to_dict("records"), outcome="net_r_aw"),
        "f38_commission_is_identically_zero_in_the_ledger": bool(
            (jan["commission_r"].astype(float) == 0.0).all()
        ),
        "commission_charge": charged.attrs["commission_meta"],
        "f31_r_per_level_exit_row": DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW,
        "level_exit_share": float(jan["outcome_is_level_exit"].mean()),
    }


# ---------------------------------------------------------------------------------------
# stage: declare
# ---------------------------------------------------------------------------------------


def split_days(jan: pd.DataFrame) -> tuple[list[str], list[str]]:
    days = sorted(jan["trading_day"].unique().tolist())
    return days[:N_TRAIN_DAYS], days[N_TRAIN_DAYS:]


def enumerate_cells(jan: pd.DataFrame, census: dict) -> list[dict]:
    """The declared cell list. Reads FEATURES and the TRAIN split only — never an outcome."""

    train_days, _ = split_days(jan)
    train = jan[jan["trading_day"].isin(train_days)]
    # Alias collapsing applies to axes that TEST something. Every constant column induces
    # the same trivial one-group partition, so the signature groups all fifteen degenerate
    # axes together — collapsing those would delete the record that each was examined and
    # found constant, while saving nothing (a degenerate axis is `look_taken=False` and
    # bills nothing either way). So: collapse live axes, enumerate dead ones individually.
    degenerate = set(census["degenerate_axes"])
    aliases = {
        head: [n for n in extra if n not in degenerate]
        for head, extra in census["alias_groups"].items()
        if head not in degenerate
    }
    aliased_away = {n for extra in aliases.values() for n in extra}

    cells: list[dict] = []
    for f in DP.FEATURE_FIELDS:
        name = f.name
        axis = census["axes"][name]
        if name in EXCLUDED_AXES or name in aliased_away:
            continue
        alias_of = aliases.get(name, [])
        if axis["n_distinct"] < 2:
            cells.append({
                "cell_id": f"{name}::DEGENERATE",
                "axis": name, "axis_family": f.family, "cut": "none",
                "look_taken": False,
                "no_look_evidence": (
                    f"AW_FEATURE_CENSUS_V1.json:axes.{name}.n_distinct = "
                    f"{axis['n_distinct']} over {census['rows']} S0R0 rows — the axis is "
                    "constant, so no hypothesis is testable on it."
                ),
                "aliases": alias_of,
            })
            continue
        if f.kind in ("cat", "bool"):
            counts = collections.Counter(train[name].dropna().astype(str))
            for level, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                if n < MIN_CELL_TRAIN_ROWS:
                    continue
                cells.append({
                    "cell_id": f"{name}=={level}",
                    "axis": name, "axis_family": f.family, "cut": CATEGORICAL_CUT,
                    "level": level, "train_rows_at_declaration": int(n),
                    "look_taken": True, "aliases": alias_of,
                })
        else:
            d = pd.to_numeric(train[name], errors="coerce").dropna()
            lo, hi = float(d.quantile(1 / 3)), float(d.quantile(2 / 3))
            if not (lo < hi):
                cells.append({
                    "cell_id": f"{name}::DEGENERATE_TERTILES",
                    "axis": name, "axis_family": f.family, "cut": NUMERIC_CUT,
                    "look_taken": False,
                    "no_look_evidence": (
                        f"TRAIN q33 == q67 == {lo!r} for {name}: the tertile cut produces "
                        "no partition, so no hypothesis is testable under the declared cut."
                    ),
                    "aliases": alias_of,
                })
                continue
            for tag, bounds in (("T1", (None, lo)), ("T2", (lo, hi)), ("T3", (hi, None))):
                cells.append({
                    "cell_id": f"{name}::{tag}",
                    "axis": name, "axis_family": f.family, "cut": NUMERIC_CUT,
                    "tertile": tag, "lower": bounds[0], "upper": bounds[1],
                    "look_taken": True, "aliases": alias_of,
                })
    return cells


def stage_declare(df: pd.DataFrame, census: dict) -> dict:
    jan = df[df.arm_id == PRIMARY_ARM]
    train_days, holdout_days = split_days(jan)
    cells = enumerate_cells(jan, census)
    looks = [c for c in cells if c["look_taken"]]

    protocol = {
        "schema": SCHEMA_PROTOCOL,
        "session": "AW",
        "blocks": "B1750-B1799",
        "declared_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "declared_before_any_outcome_was_read": True,
        "question": (
            "JANUARY_BANK section 3: the January reference arm's diagnostic pool carries "
            "+6,916.95 R over 8,006 positive rows against -31,400.82 R over 20,513 "
            "negative rows. The campaign tested two binary switches. Does ANY declared "
            "rule separate the pool out of window?"
        ),
        "substrate": {
            "pool": "AW_DIAGNOSTIC_POOL_V1 (b7_5_diagnostic_pool, seal-verified)",
            "primary_arm": PRIMARY_ARM,
            "stability_arms": list(STABILITY_ARMS),
            "secondary_holdout_arm": APRIL_ARM,
            "march_is_never_read": True,
        },
        "split": {
            "rule": "chronological_first_13_of_21_january_trading_days",
            "why_not_random": (
                "a random split over one month puts the same regime on both sides; every "
                "wave-11/12 standard is chronological."
            ),
            "train_days": train_days,
            "holdout_days": holdout_days,
        },
        "outcome": {
            "primary": "net_r_aw",
            "formula": (
                "opportunity_net_proxy_r + f31_level_charge - broker_true_commission_r"
            ),
            "f31_r_per_level_exit_row": DP.F31_GAP_THROUGH_R_PER_LEVEL_EXIT_ROW,
            "f31_source": "GATE_G1A_RECEIPT.md:147-241; IMPLEMENTATION_STATE.md B33/B34",
            "f38_commission": str(COSTS_V1.relative_to(REPO)),
            "reported_alongside": ["outcome_net_proxy_r", "outcome_net_proxy_r_f31"],
        },
        "cut_rules": {
            "categorical": CATEGORICAL_CUT,
            "numeric": NUMERIC_CUT,
            "numeric_bounds_from": "TRAIN split only",
            "min_cell_train_rows": MIN_CELL_TRAIN_ROWS,
            "min_cell_holdout_rows": MIN_CELL_HOLDOUT_ROWS,
            "min_cell_april_rows": MIN_CELL_APRIL_ROWS,
            "top_k_for_interactions": TOP_K_FOR_INTERACTIONS,
        },
        "funnel": {
            "F1_train": f"train n >= {MIN_CELL_TRAIN_ROWS} AND train mean net_r_aw > 0",
            "F2_holdout": f"holdout n >= {MIN_CELL_HOLDOUT_ROWS} AND holdout mean > 0",
            "F3_holdout_stability": "holdout day-positive fraction >= 0.50",
            "F4_april": f"april n >= {MIN_CELL_APRIL_ROWS} AND april mean > 0",
            "F5_arm_stability": "full-window mean > 0 on ALL THREE other January arms",
            "survivors_go_to": "AW-3 archive walkforward gate at the ratified rule",
        },
        "inference": {
            "unit": "trading day (rows within a day are not independent)",
            "test": "exact day-blocked sign-flip permutation on per-day means, H0: mean = 0",
            "resolution_floor": "1 / 2**n_days, reported on every p (wave-10 section 2)",
            "multiplicity": "BH over the declared family; Bonferroni reported alongside",
        },
        "excluded_axes": EXCLUDED_AXES,
        "alias_groups": census["alias_groups"],
        "cells": cells,
        "cells_sha256": _sha(cells),
        "declared_family_size": len(cells),
        "declared_looks_taken": len(looks),
        "interaction_budget": TOP_K_FOR_INTERACTIONS * (TOP_K_FOR_INTERACTIONS - 1) // 2,
        "model_budget": 3,
        "total_declared_bill": (
            len(cells) + TOP_K_FOR_INTERACTIONS * (TOP_K_FOR_INTERACTIONS - 1) // 2 + 3
        ),
        "breakeven_precision": census["pool_summary_aw"]["breakeven_precision"],
        "base_rate": census["pool_summary_aw"]["base_rate"],
    }
    return protocol


def stage_family(protocol: dict) -> dict:
    """CANDIDATE_FAMILY_V7 = V6's three families, unchanged, plus the mine's own."""

    v6 = json.loads(FAMILY_V6.read_text())
    families = json.loads(json.dumps(v6["families"]))  # deep copy, byte-for-byte carried

    members = []
    for cell in protocol["cells"]:
        member = {
            "name": cell["cell_id"],
            "source": "AW_MINE_PROTOCOL_V1.json:cells",
            "basis": (
                f"{cell['axis_family']} axis {cell['axis']!r}, cut {cell['cut']!r} — a "
                "declared separability look over the sealed B7.5 January diagnostic pool"
            ),
            "declared_at": "2026-07-30",
            "status": "declared",
            "look_taken": bool(cell["look_taken"]),
        }
        if not cell["look_taken"]:
            member["no_look_evidence"] = cell["no_look_evidence"]
        members.append(member)
    for a, b in itertools.combinations(range(TOP_K_FOR_INTERACTIONS), 2):
        members.append({
            "name": f"interaction::rank{a + 1}_x_rank{b + 1}",
            "source": "AW_MINE_PROTOCOL_V1.json:cut_rules.top_k_for_interactions",
            "basis": (
                "pairwise cross of the two TRAIN-ranked univariate cells at these ranks; "
                "the SLOT is declared here, its occupant is decided by TRAIN order alone"
            ),
            "declared_at": "2026-07-30", "status": "declared", "look_taken": True,
        })
    for name, what in (
        ("model::l2_logistic", "regularised linear separability ceiling"),
        ("model::hgb_depth3", "shallow non-linear separability ceiling"),
        ("model::holdout_refit_control", "in-sample ceiling control, never a result"),
    ):
        members.append({
            "name": name, "source": "AW_MINE_PROTOCOL_V1.json:model_budget",
            "basis": what, "declared_at": "2026-07-30", "status": "declared",
            "look_taken": True,
        })

    families["B7_5_SEPARABILITY_MINE_V1"] = {
        "purpose": (
            "Every look Session AW takes at the sealed B7.5 January diagnostic pool while "
            "asking JANUARY_BANK section 3's open question. A rule mined here and then "
            "gated on the archive is a SELECTED hypothesis: its bill must include the "
            "selection, or the gate is being shown the winner of a contest it cannot see."
        ),
        "declaration_date": "2026-07-30",
        "high_water_size": len(members),
        "high_water_looks": sum(1 for m in members if m["look_taken"]),
        "members": members,
        "history": [{
            "at": "2026-07-30", "by": "Session AW (B1750-B1799)",
            "what": "family created; every member declared before any outcome was read",
            "members_added": [m["name"] for m in members],
        }],
        "note": (
            "Cells are enumerated mechanically by aw_separability_mine.py --stage declare "
            "from the FEATURE distributions of the TRAIN split. No outcome column is "
            "opened by that stage, and --stage mine refuses to run if the cell list's "
            "sha256 has moved."
        ),
        "provenance": "AW_MINE_PROTOCOL_V1.json",
    }

    return {
        "schema": v6["schema"],
        "declaration_date": "2026-07-30",
        "declared_by": "Session AW (B1750-B1799), Fable-5 wave 12",
        "generated_by": "aw_separability_mine.py --stage declare",
        "supersedes": str(FAMILY_V6.relative_to(REPO)),
        "superseded_because": (
            "V6 carries no family for the B7.5 diagnostic-pool separability question. AW "
            "declares one; V6's three families are carried forward byte-for-byte, so the "
            "succession is a strict superset and every V6-era q-value still reproduces."
        ),
        "families": families,
        "freeze_rule": v6["freeze_rule"],
        "aw_declaration_note": {
            "declared_before_any_gate_ran": True,
            "what_the_new_family_bills": (
                "The mine's own looks. AW-3 gates a surviving rule against "
                "max(estate family, mine family) as stated in the result doc — a rule "
                "selected out of N looks is corrected for N."
            ),
            "why_aliases_are_one_member": (
                "origin_family / route_family / framework induce the SAME partition of the "
                "28,519 rows under different labels. Three rows would be three looks on "
                "the record and one look in fact, which is the mirror image of the defect "
                "the ratchet closes."
            ),
        },
        "ratified_by": v6.get("ratified_by"),
        "ratified_utc": v6.get("ratified_utc"),
        "what_is_being_ratified": v6.get("what_is_being_ratified"),
        "rules_considered_and_rejected_as_families": v6.get(
            "rules_considered_and_rejected_as_families"
        ),
        "union_note": v6.get("union_note"),
        "the_historical_69_double_counts_and_here_is_the_measurement": v6.get(
            "the_historical_69_double_counts_and_here_is_the_measurement"
        ),
        "ao_declaration_note": v6.get("ao_declaration_note"),
        "aq_declaration_note": v6.get("aq_declaration_note"),
        "ar_declaration_note": v6.get("ar_declaration_note"),
        "av_declaration_note": v6.get("av_declaration_note"),
    }


# ---------------------------------------------------------------------------------------
# stage: mine
# ---------------------------------------------------------------------------------------


def sign_flip_p(day_means: np.ndarray, *, max_exact_days: int = 22) -> dict:
    """Exact day-blocked sign-flip permutation, H0: the cell's mean R is 0.

    Reports the resolution floor beside the p, because a p at or below `1/2**n_days`
    cannot distinguish itself from the floor (wave-10 section 2).
    """

    n = len(day_means)
    if n == 0:
        return {"p": None, "n_days": 0, "floor": None, "at_floor": None}
    observed = float(day_means.mean())
    floor = 1.0 / (2 ** n)
    if n <= max_exact_days:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=n)))
        stats = (signs * day_means).mean(axis=1)
        count = int((stats >= observed - 1e-15).sum())
        p = count / len(stats)
    else:
        rng = np.random.default_rng(20260730)
        draws = rng.choice((1.0, -1.0), size=(200_000, n))
        stats = (draws * day_means).mean(axis=1)
        p = float((stats >= observed - 1e-15).mean())
    return {
        "p": round(float(p), 8), "n_days": n, "floor": round(floor, 8),
        "at_floor": bool(p <= floor * 1.5), "observed_mean": round(observed, 6),
    }


def cell_mask(frame: pd.DataFrame, cell: dict) -> np.ndarray:
    axis = cell["axis"]
    if cell["cut"] == CATEGORICAL_CUT:
        return (frame[axis].astype("object").map(lambda v: str(v) if v is not None else None)
                == cell["level"]).to_numpy()
    values = pd.to_numeric(frame[axis], errors="coerce").to_numpy(dtype=float)
    lo, hi = cell.get("lower"), cell.get("upper")
    mask = ~np.isnan(values)
    if lo is not None:
        mask &= values > lo
    if hi is not None:
        mask &= values <= hi
    return mask


def describe(
    frame: pd.DataFrame,
    mask: np.ndarray,
    *,
    with_p: bool = False,
    outcome: str = "net_r_aw",
) -> dict:
    sub = frame[mask]
    n = int(len(sub))
    # Every key is always present, with None where it is undefined. An empty cell that
    # returns a SHORT dict makes every downstream reader carry a `.get` — and the one that
    # forgets raises on the rarest input, which is the wrong place to discover it.
    out = {
        "n": n, "mean_r": None, "mean_r_raw": None, "sum_r": None, "precision": None,
        "n_days": 0, "day_positive_frac": None, "share_of_rows": None,
    }
    if with_p:
        out["perm"] = {"p": None, "n_days": 0, "floor": None, "at_floor": None}
    if not n:
        return out
    r = sub[outcome].to_numpy(dtype=float)
    by_day = sub.groupby("trading_day")[outcome].mean()
    out.update({
        "mean_r": round(float(r.mean()), 6),
        "mean_r_raw": round(float(sub["outcome_net_proxy_r"].astype(float).mean()), 6),
        "sum_r": round(float(r.sum()), 4),
        "precision": round(float((r > 0).mean()), 6),
        "n_days": int(len(by_day)),
        "day_positive_frac": round(float((by_day > 0).mean()), 6),
        "share_of_rows": round(n / len(frame), 6),
    })
    if with_p:
        out["perm"] = sign_flip_p(by_day.to_numpy(dtype=float))
    return out


def stage_mine(df: pd.DataFrame, protocol: dict) -> dict:
    jan_all = charge(df[df.arm_id == PRIMARY_ARM])
    train_days = set(protocol["split"]["train_days"])
    holdout_days = set(protocol["split"]["holdout_days"])
    train = jan_all[jan_all["trading_day"].isin(train_days)]
    holdout = jan_all[jan_all["trading_day"].isin(holdout_days)]
    april = charge(df[df.arm_id == APRIL_ARM])
    stability = {a: charge(df[df.arm_id == a]) for a in STABILITY_ARMS}

    baseline = {
        "train": describe(train, np.ones(len(train), dtype=bool), with_p=True),
        "holdout": describe(holdout, np.ones(len(holdout), dtype=bool), with_p=True),
        "april": describe(april, np.ones(len(april), dtype=bool), with_p=True),
        "january_full": describe(jan_all, np.ones(len(jan_all), dtype=bool), with_p=True),
    }

    # Every split is measured for EVERY cell, not only for cells that reach it. The funnel
    # is then a LABEL on a complete row rather than a reason the rest of the row is absent
    # — the deliverable is the map of separability, and a map with holes where the answer
    # was bad is a highlight reel.
    results = []
    for cell in protocol["cells"]:
        if not cell["look_taken"]:
            results.append({**{k: cell[k] for k in ("cell_id", "axis", "axis_family", "cut")},
                            "look_taken": False, "stage_reached": "DEGENERATE"})
            continue
        tr = describe(train, cell_mask(train, cell), with_p=True)
        ho = describe(holdout, cell_mask(holdout, cell), with_p=True)
        ap = describe(april, cell_mask(april, cell), with_p=True)
        arms = {a: describe(f, cell_mask(f, cell)) for a, f in stability.items()}
        row = {
            "cell_id": cell["cell_id"], "axis": cell["axis"],
            "axis_family": cell["axis_family"], "cut": cell["cut"], "look_taken": True,
            "train": tr, "holdout": ho, "april": ap, "arm_stability": arms,
            "train_lift_vs_baseline": (
                None if tr["mean_r"] is None
                else round(tr["mean_r"] - baseline["train"]["mean_r"], 6)
            ),
            "holdout_lift_vs_baseline": (
                None if ho["mean_r"] is None
                else round(ho["mean_r"] - baseline["holdout"]["mean_r"], 6)
            ),
        }
        row["F1_train"] = bool(tr["n"] >= MIN_CELL_TRAIN_ROWS and (tr["mean_r"] or -1) > 0)
        row["F2_holdout"] = bool(
            ho["n"] >= MIN_CELL_HOLDOUT_ROWS and (ho["mean_r"] or -1) > 0
        )
        row["F3_holdout_stability"] = bool((ho["day_positive_frac"] or 0) >= 0.50)
        row["F4_april"] = bool(ap["n"] >= MIN_CELL_APRIL_ROWS and (ap["mean_r"] or -1) > 0)
        row["F5_arm_stability"] = bool(
            arms and all((v["mean_r"] or -1) > 0 for v in arms.values())
        )
        gates = ("F1_train", "F2_holdout", "F3_holdout_stability", "F4_april",
                 "F5_arm_stability")
        stage = "SURVIVOR"
        for gate in gates:
            if not row[gate]:
                stage = gate.split("_")[0]
                break
        row["stage_reached"] = stage
        results.append(row)

    survivors = [r for r in results if r.get("stage_reached") == "SURVIVOR"]
    funnel = collections.Counter(r.get("stage_reached") for r in results)

    # --- interactions: the declared top-K by TRAIN order alone, crossed pairwise --------
    # `AW_MINE_PROTOCOL_V1.json` declares the SLOT and says the occupant "is decided by
    # TRAIN order alone" — no sign filter. Ranking among F1 passers would have made the
    # whole interaction budget unreachable the moment F1 emptied, which is a different
    # rule from the one declared.
    ranked = sorted(
        (r for r in results if r.get("look_taken") and r["train"]["n"] >= MIN_CELL_TRAIN_ROWS),
        key=lambda r: (-(r["train"]["mean_r"] if r["train"]["mean_r"] is not None else -9e9),
                       r["cell_id"]),
    )[:TOP_K_FOR_INTERACTIONS]
    by_id = {c["cell_id"]: c for c in protocol["cells"]}
    interactions = []
    for a, b in itertools.combinations(ranked, 2):
        ca, cb = by_id[a["cell_id"]], by_id[b["cell_id"]]
        if ca["axis"] == cb["axis"]:
            interactions.append({
                "cell_id": f"{a['cell_id']} AND {b['cell_id']}",
                "same_axis_disjoint": True, "stage_reached": "DISJOINT"})
            continue
        tr = describe(train, cell_mask(train, ca) & cell_mask(train, cb), with_p=True)
        ho = describe(holdout, cell_mask(holdout, ca) & cell_mask(holdout, cb), with_p=True)
        ap = describe(april, cell_mask(april, ca) & cell_mask(april, cb), with_p=True)
        arms = {k: describe(f, cell_mask(f, ca) & cell_mask(f, cb))
                for k, f in stability.items()}
        item = {
            "cell_id": f"{a['cell_id']} AND {b['cell_id']}",
            "train": tr, "holdout": ho, "april": ap, "arm_stability": arms,
        }
        checks = (
            tr["n"] >= MIN_CELL_TRAIN_ROWS and (tr["mean_r"] or -1) > 0,
            ho["n"] >= MIN_CELL_HOLDOUT_ROWS and (ho["mean_r"] or -1) > 0,
            (ho["day_positive_frac"] or 0) >= 0.50,
            ap["n"] >= MIN_CELL_APRIL_ROWS and (ap["mean_r"] or -1) > 0,
            all((v["mean_r"] or -1) > 0 for v in arms.values()),
        )
        labels = ("F1", "F2", "F3", "F4", "F5")
        item["stage_reached"] = next(
            (lab for lab, ok in zip(labels, checks) if not ok), "SURVIVOR"
        )
        interactions.append(item)

    # --- does ANY axis carry information, even where no cell crosses zero? --------------
    # The funnel answers "is there a tradeable cell". This answers the weaker and more
    # useful question: do TRAIN cell means predict HOLDOUT cell means at all? A positive
    # rank correlation with no cell above zero would mean real-but-insufficient signal and
    # a different prescription (widen the pool) than an absent one (abandon the axis).
    def _spearman(xs, ys):
        if len(xs) < 4:
            return None
        rx = pd.Series(xs).rank().to_numpy()
        ry = pd.Series(ys).rank().to_numpy()
        if rx.std() == 0 or ry.std() == 0:
            return None
        return round(float(np.corrcoef(rx, ry)[0, 1]), 6)

    scored = [
        r for r in results
        if r.get("look_taken") and r["train"]["mean_r"] is not None
        and r["holdout"]["mean_r"] is not None
        and r["train"]["n"] >= MIN_CELL_TRAIN_ROWS
        and r["holdout"]["n"] >= MIN_CELL_HOLDOUT_ROWS
    ]
    persistence = {
        "n_cells": len(scored),
        "train_to_holdout_spearman": _spearman(
            [r["train"]["mean_r"] for r in scored], [r["holdout"]["mean_r"] for r in scored]
        ),
        "train_to_april_spearman": _spearman(
            [r["train"]["mean_r"] for r in scored],
            [r["april"]["mean_r"] if r["april"]["mean_r"] is not None else float("nan")
             for r in scored],
        ),
        "by_axis_family": {},
        "note": (
            "Spearman over cell MEANS, one point per cell. Positive == the TRAIN ordering "
            "of cells survives to the held-out days; near zero == the axis carries no "
            "transferable information at all, whatever its in-sample spread looks like."
        ),
    }
    for fam in sorted({r["axis_family"] for r in scored}):
        sub = [r for r in scored if r["axis_family"] == fam]
        persistence["by_axis_family"][fam] = {
            "n_cells": len(sub),
            "train_to_holdout_spearman": _spearman(
                [r["train"]["mean_r"] for r in sub], [r["holdout"]["mean_r"] for r in sub]
            ),
            "best_train_mean_r": round(max(r["train"]["mean_r"] for r in sub), 6),
            "best_holdout_mean_r": round(max(r["holdout"]["mean_r"] for r in sub), 6),
        }

    by_axis = {}
    for axis in sorted({r["axis"] for r in results if r.get("look_taken")}):
        sub = [r for r in results if r.get("axis") == axis and r.get("look_taken")
               and r["train"]["mean_r"] is not None]
        if not sub:
            continue
        means = [r["train"]["mean_r"] for r in sub]
        by_axis[axis] = {
            "n_cells": len(sub),
            "train_mean_r_min": round(min(means), 6),
            "train_mean_r_max": round(max(means), 6),
            "train_spread": round(max(means) - min(means), 6),
            "best_cell": max(sub, key=lambda r: r["train"]["mean_r"])["cell_id"],
            "best_cell_holdout_mean_r": max(
                sub, key=lambda r: r["train"]["mean_r"]
            )["holdout"]["mean_r"],
        }

    def _top(key, split):
        pool = [r for r in results if r.get("look_taken")
                and r[split]["mean_r"] is not None
                and r[split]["n"] >= (MIN_CELL_TRAIN_ROWS if split == "train"
                                      else MIN_CELL_HOLDOUT_ROWS)]
        pool.sort(key=lambda r: -r[split]["mean_r"])
        return [{
            "cell_id": r["cell_id"], "axis_family": r["axis_family"],
            "train": {k: r["train"][k] for k in ("n", "mean_r", "precision")},
            "holdout": {k: r["holdout"][k] for k in ("n", "mean_r", "precision",
                                                     "day_positive_frac")},
            "april": {k: r["april"][k] for k in ("n", "mean_r", "precision")},
            "stage_reached": r["stage_reached"],
        } for r in pool[:25]]

    return {
        "schema": SCHEMA_MAP,
        "protocol_sha256": protocol["self_sha256"],
        "cells_sha256_recomputed": _sha(protocol["cells"]),
        "baseline": baseline,
        "declared_family_size": protocol["total_declared_bill"],
        "breakeven_precision": protocol["breakeven_precision"],
        "funnel_counts": dict(funnel),
        "funnel_note": (
            "Every cell is measured on every split; the funnel label names the FIRST gate "
            "a cell fails, not the point where measurement stopped."
        ),
        "persistence": persistence,
        "by_axis": by_axis,
        "top_25_by_train_mean_r": _top("mean_r", "train"),
        "top_25_by_holdout_mean_r": _top("mean_r", "holdout"),
        "interaction_ranked_cells": [r["cell_id"] for r in ranked],
        "cells": results,
        "interactions": interactions,
        "survivors": [r["cell_id"] for r in survivors]
        + [i["cell_id"] for i in interactions if i.get("stage_reached") == "SURVIVOR"],
        "commission_charge": jan_all.attrs["commission_meta"],
    }


# ---------------------------------------------------------------------------------------
# stage: gross  (the PRE-COST decomposition, and a second bill for asking it)
# ---------------------------------------------------------------------------------------


def stage_gross(df: pd.DataFrame, protocol: dict) -> dict:
    """Does any declared cell have DIRECTIONAL edge before cost is charged?

    This is a different question from the one `--stage mine` asks, and asking it is a new
    look on every cell — so `--stage gross` re-declares all 212 into `CANDIDATE_FAMILY_V8`
    with a `history` entry, and the bill goes up. It is asked because the net funnel
    returned zero and the decomposition names two very different prescriptions:

      * gross positive, net negative  -> the mechanism works and the COST kills it. That
        is a cost repair (cheaper instrument, cheaper session, wider stop), and it is
        exactly the "maybe with some fixes it becomes positive" the owner asked about.
      * gross negative                -> there is no directional edge to rescue, and no
        cost repair can create one.
    """

    jan = charge(df[df.arm_id == PRIMARY_ARM])
    april = charge(df[df.arm_id == APRIL_ARM])
    train = jan[jan["trading_day"].isin(set(protocol["split"]["train_days"]))]
    holdout = jan[jan["trading_day"].isin(set(protocol["split"]["holdout_days"]))]

    g = jan["outcome_gross_r"].astype(float)
    cost = jan["cost_r"].astype(float)
    decomposition = {
        "rows": int(len(jan)),
        "mean_gross_r": round(float(g.mean()), 6),
        "share_gross_positive": round(float((g > 0).mean()), 6),
        "mean_replay_cost_r": round(float(-cost.mean()), 6),
        "mean_spread_r": round(float(-jan["spread_r"].astype(float).mean()), 6),
        "mean_swap_r": round(float(-jan["swap_cost_r"].astype(float).mean()), 6),
        "mean_f31_charge_r": round(float(
            (jan["outcome_net_proxy_r_f31"].astype(float)
             - jan["outcome_net_proxy_r"].astype(float)).mean()), 6),
        "mean_broker_true_commission_r": round(
            float(-jan["commission_r_broker_true"].astype(float).mean()), 6),
        "mean_net_r_aw": round(float(jan["net_r_aw"].astype(float).mean()), 6),
        "binary_population": {
            "note": "rows whose gross R is exactly -1 (stop) or +2 (target): the pure "
                    "2R-target/1R-stop bet, whose break-even hit rate is 1/3",
            "n_stop": int((g == -1.0).sum()),
            "n_target": int((g == 2.0).sum()),
            "hit_rate": round(float((g == 2.0).sum() / max(1, int(((g == -1.0) | (g == 2.0)).sum()))), 6),
            "breakeven_hit_rate": round(1 / 3, 6),
            "mean_gross_r": round(float(g[(g == -1.0) | (g == 2.0)].mean()), 6),
        },
        "cost_tail": {
            "note": "spread_r is spread_price / sl_distance_price, so a cost above 1 R "
                    "means the stop is narrower than the round-trip spread",
            "rows_cost_over_1r": int((cost > 1).sum()),
            "rows_cost_over_2r": int((cost > 2).sum()),
            "rows_cost_over_5r": int((cost > 5).sum()),
            "max_cost_r": round(float(cost.max()), 4),
            "net_r_in_cost_over_1r_rows": round(
                float(jan.loc[cost > 1, "net_r_aw"].astype(float).sum()), 2),
            "net_r_total": round(float(jan["net_r_aw"].astype(float).sum()), 2),
        },
    }

    results = []
    for cell in protocol["cells"]:
        if not cell["look_taken"]:
            continue
        tr = describe(train, cell_mask(train, cell), with_p=True, outcome="outcome_gross_r")
        ho = describe(holdout, cell_mask(holdout, cell), with_p=True,
                      outcome="outcome_gross_r")
        ap = describe(april, cell_mask(april, cell), with_p=True, outcome="outcome_gross_r")
        results.append({
            "cell_id": cell["cell_id"], "axis": cell["axis"],
            "axis_family": cell["axis_family"],
            "train": tr, "holdout": ho, "april": ap,
            "G1_train": bool(tr["n"] >= MIN_CELL_TRAIN_ROWS and (tr["mean_r"] or -1) > 0),
            "G2_holdout": bool(ho["n"] >= MIN_CELL_HOLDOUT_ROWS and (ho["mean_r"] or -1) > 0),
            "G3_april": bool(ap["n"] >= MIN_CELL_APRIL_ROWS and (ap["mean_r"] or -1) > 0),
        })
    for r in results:
        r["gross_survivor"] = bool(r["G1_train"] and r["G2_holdout"] and r["G3_april"])

    gross_survivors = [r for r in results if r["gross_survivor"]]
    ranked = sorted(results, key=lambda r: -(r["train"]["mean_r"] or -9e9))
    return {
        "schema": "gtos.aw.gross_view.v1",
        "protocol_sha256": protocol["self_sha256"],
        "decomposition": decomposition,
        "baseline": {
            "train": describe(train, np.ones(len(train), bool), with_p=True,
                              outcome="outcome_gross_r"),
            "holdout": describe(holdout, np.ones(len(holdout), bool), with_p=True,
                                outcome="outcome_gross_r"),
            "april": describe(april, np.ones(len(april), bool), with_p=True,
                              outcome="outcome_gross_r"),
        },
        "n_cells": len(results),
        "n_G1_train_positive": sum(1 for r in results if r["G1_train"]),
        "n_G2_holdout_positive": sum(1 for r in results if r["G2_holdout"]),
        "n_gross_survivors": len(gross_survivors),
        "gross_survivors": [r["cell_id"] for r in gross_survivors],
        "top_25_by_train_gross": [
            {"cell_id": r["cell_id"], "axis_family": r["axis_family"],
             "train": {k: r["train"][k] for k in ("n", "mean_r", "precision")},
             "holdout": {k: r["holdout"][k] for k in ("n", "mean_r", "precision")},
             "april": {k: r["april"][k] for k in ("n", "mean_r", "precision")},
             "gross_survivor": r["gross_survivor"]}
            for r in ranked[:25]
        ],
        "cells": results,
    }


def stage_family_v8(gross: dict) -> dict:
    """V8 = V7 plus one member per pre-cost look. Additions RAISE the bill, by design."""

    v7 = json.loads(FAMILY_V7.read_text())
    families = json.loads(json.dumps(v7["families"]))
    mine = families["B7_5_SEPARABILITY_MINE_V1"]
    added = []
    for cell in gross["cells"]:
        name = f"gross::{cell['cell_id']}"
        added.append({
            "name": name, "source": "AW_GROSS_VIEW_V1.json:cells",
            "basis": (
                "the same cell asked a DIFFERENT question — does it have directional edge "
                "BEFORE cost — after the net funnel returned zero survivors"
            ),
            "declared_at": "2026-07-30", "status": "declared", "look_taken": True,
        })
    mine["members"] = list(mine["members"]) + added
    mine["high_water_size"] = len(mine["members"])
    mine["high_water_looks"] = sum(1 for m in mine["members"] if m["look_taken"])
    mine["history"] = list(mine["history"]) + [{
        "at": "2026-07-30", "by": "Session AW (B1750-B1799)",
        "what": (
            "pre-cost view added after the net funnel returned 0 of 212. Asking whether a "
            "cell has directional edge before cost is a second hypothesis about the same "
            "rows, so it is a second look, and the bill rises accordingly. Declaring it "
            "here rather than re-writing the sealed V7 is the point: the net looks were "
            "taken and cannot be un-taken."
        ),
        "members_added": [m["name"] for m in added],
    }]
    out = dict(v7)
    out["families"] = families
    out["supersedes"] = str(FAMILY_V7.relative_to(REPO))
    out["superseded_because"] = (
        "Session AW's pre-cost decomposition is 212 further looks at the same rows. The "
        "ratchet requires them to be added, not absorbed."
    )
    out["generated_by"] = "aw_separability_mine.py --stage gross"
    out.pop("self_sha256", None)
    return out


# ---------------------------------------------------------------------------------------
# stage: model  (the separability CEILING)
# ---------------------------------------------------------------------------------------


def _design(frame: pd.DataFrame, cat_axes, num_axes, categories: dict | None = None):
    parts, names = [], []
    cats = {} if categories is None else categories
    for axis in num_axes:
        v = pd.to_numeric(frame[axis], errors="coerce").to_numpy(dtype=float)
        med = np.nanmedian(v) if np.isfinite(v).any() else 0.0
        v = np.where(np.isfinite(v), v, med)
        parts.append(v.reshape(-1, 1))
        names.append(axis)
    for axis in cat_axes:
        levels = cats.get(axis)
        if levels is None:
            levels = sorted({str(x) for x in frame[axis].dropna().tolist()})
            cats[axis] = levels
        col = frame[axis].astype("object").map(lambda x: str(x) if x is not None else "")
        for lv in levels:
            parts.append((col == lv).to_numpy(dtype=float).reshape(-1, 1))
            names.append(f"{axis}=={lv}")
    return np.hstack(parts) if parts else np.zeros((len(frame), 0)), names, cats


def stage_model(df: pd.DataFrame, protocol: dict) -> dict:
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    jan = charge(df[df.arm_id == PRIMARY_ARM])
    april = charge(df[df.arm_id == APRIL_ARM])
    train = jan[jan["trading_day"].isin(set(protocol["split"]["train_days"]))]
    holdout = jan[jan["trading_day"].isin(set(protocol["split"]["holdout_days"]))]

    used = {c["axis"] for c in protocol["cells"] if c["look_taken"]}
    num_axes = sorted(a for a in used
                      if next(f for f in DP.FEATURE_FIELDS if f.name == a).kind == "num")
    cat_axes = sorted(a for a in used if a not in num_axes)

    Xtr, names, cats = _design(train, cat_axes, num_axes)
    Xho, _, _ = _design(holdout, cat_axes, num_axes, categories=cats)
    Xap, _, _ = _design(april, cat_axes, num_axes, categories=cats)
    ytr = (train["net_r_aw"].to_numpy(dtype=float) > 0).astype(int)
    yho = (holdout["net_r_aw"].to_numpy(dtype=float) > 0).astype(int)
    yap = (april["net_r_aw"].to_numpy(dtype=float) > 0).astype(int)

    scaler = StandardScaler().fit(Xtr)
    out: dict = {"schema": "gtos.aw.model_ceiling.v1", "n_features": len(names),
                 "n_train": int(len(train)), "n_holdout": int(len(holdout)),
                 "n_april": int(len(april)), "models": {}}

    def evaluate(tag, score_ho, score_ap, score_tr):
        def block(frame, scores, y):
            if not len(frame):
                return None
            r = frame["net_r_aw"].to_numpy(dtype=float)
            order = np.argsort(-scores)
            res = {"auc": round(float(roc_auc_score(y, scores)), 6) if len(set(y)) > 1 else None}
            for q, label in ((0.10, "top_decile"), (0.20, "top_quintile"), (0.50, "top_half")):
                k = max(1, int(len(scores) * q))
                sel = order[:k]
                res[label] = {
                    "n": int(k), "mean_r": round(float(r[sel].mean()), 6),
                    "precision": round(float((r[sel] > 0).mean()), 6),
                    "sum_r": round(float(r[sel].sum()), 3),
                }
            return res
        out["models"][tag] = {
            "train_in_sample": block(train, score_tr, ytr),
            "holdout": block(holdout, score_ho, yho),
            "april": block(april, score_ap, yap),
        }

    lr = LogisticRegression(max_iter=2000, C=0.1).fit(scaler.transform(Xtr), ytr)
    evaluate("l2_logistic",
             lr.predict_proba(scaler.transform(Xho))[:, 1],
             lr.predict_proba(scaler.transform(Xap))[:, 1],
             lr.predict_proba(scaler.transform(Xtr))[:, 1])
    coefs = sorted(zip(names, lr.coef_[0].tolist()), key=lambda kv: -abs(kv[1]))[:25]
    out["models"]["l2_logistic"]["top_coefficients"] = [
        {"feature": n, "coef": round(v, 5)} for n, v in coefs
    ]

    hgb = HistGradientBoostingClassifier(
        max_depth=3, max_iter=200, learning_rate=0.05, random_state=20260730
    ).fit(Xtr, ytr)
    evaluate("hgb_depth3", hgb.predict_proba(Xho)[:, 1], hgb.predict_proba(Xap)[:, 1],
             hgb.predict_proba(Xtr)[:, 1])

    ctrl = HistGradientBoostingClassifier(
        max_depth=3, max_iter=200, learning_rate=0.05, random_state=20260730
    ).fit(Xho, yho)
    evaluate("holdout_refit_control", ctrl.predict_proba(Xho)[:, 1],
             ctrl.predict_proba(Xap)[:, 1], ctrl.predict_proba(Xtr)[:, 1])
    out["models"]["holdout_refit_control"]["what_this_is"] = (
        "fitted ON the holdout and scored on it. An in-sample CEILING, never a result — it "
        "is here so the reader can see how much of any honest number is fittable noise."
    )
    out["breakeven_precision"] = protocol["breakeven_precision"]
    out["base_rate"] = protocol["base_rate"]
    return out


# ---------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=("census", "declare", "mine", "gross", "model", "all"))
    args = ap.parse_args()
    df = load_frame()

    if args.stage in ("census", "all"):
        _write(CENSUS_OUT, stage_census(df))
    if args.stage in ("declare", "all"):
        census = json.loads(CENSUS_OUT.read_text())
        protocol = stage_declare(df, census)
        _write(PROTOCOL_OUT, protocol)
        _write(FAMILY_V7, stage_family(json.loads(PROTOCOL_OUT.read_text())))
    if args.stage in ("mine", "all"):
        protocol = json.loads(PROTOCOL_OUT.read_text())
        if _sha(protocol["cells"]) != protocol["cells_sha256"]:
            raise SystemExit(
                "cells_sha256 mismatch: the declared cell list has been edited since it "
                "was sealed. Refusing to mine against a moved bill."
            )
        _write(MAP_OUT, stage_mine(df, protocol))
    if args.stage in ("gross", "all"):
        protocol = json.loads(PROTOCOL_OUT.read_text())
        gross = stage_gross(df, protocol)
        _write(GROSS_OUT, gross)
        _write(FAMILY_V8, stage_family_v8(gross))
    if args.stage in ("model", "all"):
        protocol = json.loads(PROTOCOL_OUT.read_text())
        _write(MODEL_OUT, stage_model(df, protocol))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
