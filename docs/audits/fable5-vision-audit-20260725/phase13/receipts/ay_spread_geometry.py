#!/usr/bin/env python3
"""Session AY — the spread-geometry repair (B1800-B1849).

    python3 docs/audits/fable5-vision-audit-20260725/phase13/receipts/ay_spread_geometry.py \
        --stage declare   # AY-0: the protocol + the family ratchet, BEFORE any outcome is read
    ... --stage live      # AY-2a: what the LIVE book already does about this, measured on its own logs
    ... --stage census    # AY-1a: the estate against the LIVE config's own limits, per sleeve
    ... --stage gate      # AY-1b: 27 arms x 4 bands at the ratified rule
    ... --stage verdict   # AY-1c: the per-sleeve REPAIR / NEUTRAL / HARMFUL table
    ... --stage all

THE FINDING THAT REFRAMES THE COMMISSION, AND IT IS IN THE LIVE CODE
--------------------------------------------------------------------
AW measured that 33.7 % of the estate's priced archive trades exceed a `spread_r <= 0.10`
limit it recovered from the SEALED B7.5 contract by reading the January ledger's own block
reason, and proposed applying that limit as a per-sleeve repair.

**The limit is not a proposal. It is the live W7 book's own pre-trade contract, running on
both funded accounts today, at the same two numbers.**

    config/agent_config.yaml:715   selected_cell_pretrade_max_spread_r: 0.10
    config/agent_config.yaml:716   selected_cell_pretrade_max_total_cost_r: 0.15
    config/agent_config.yaml:724   selected_cell_pretrade_max_spread_r_by_sleeve: {fx_jpy: 0.35, fx_jpy_ny: 0.35}

enforced twice on every W7 placement:

  * `broker_net_cost_engine.pretrade_cost_refusal_reasons:718-727` — the AUTHORITATIVE gate,
    reached because `execution_packets.build_book_trade_params` stamps
    `gtos_vnext_production_execution_path: True` (`:348`, `:538`), which is exactly the
    predicate `execution._is_vnext_production_execution_path:1902-1913` tests before
    `_vnext_pretrade_cost_model` builds the packet. A refusal returns `None` from
    `open_trade` (`execution.py:3438-3443`).
  * `book_owner._spread_cost_screen:4232-4270` — a deterministic PRE-SEND mirror of it, so
    the book declines cleanly instead of attempting a futile order.

It fires. In the read-only 2026-07-25 VPS export's own launcher log, **136 legs were refused
with `cost_screen_spread_r`** and 62 more with `pretrade_cost` — including `asia_pdl_fade` at
`spread_r` 0.398, 0.421, 0.920 and **1.306**, the sleeve AW's filter improves most.

So the arm AW called "the repair" is the LIVE CONTRACT, and the arm it called "control" — the
unfiltered archive — is the FICTION. Every published R/day for every estate sleeve is
measured on a population the live book would partly refuse. That is the same class of defect
AQ found in the `mx_*` time stop, on a different axis, and it is what this stage measures.

WHAT IS THEREFORE STILL WORTH BUILDING, AND WHY IT IS NOT A DUPLICATE
----------------------------------------------------------------------
The live floor sits at the SEND layer. Between generation and send, a doomed intent has
already: (a) been counted by `RunningConvictionLedger` as a distinct firing sleeve for the
day, which `admission.py:1188` takes as `na = max(na, override)` — **monotone upward** — and
which under the live half-Kelly bins moves the multiplier 0.991 -> 1.241 at the 3->4 edge,
**+25.2 % on every other unit that day**; (b) consumed a sizing slot; (c) emitted an operator
card. `book_engine._running_conviction_override:865-915` applies `precount_intent_filter`'s
five drop rules before counting and the cost screen is **not one of them** — the same shape
as the D3 defect its own docstring records being fixed in 2026-07-27, on a different filter.

`--stage live` measures that contamination on the export. The generation-side floor
(`--spread-geometry-floor`, `book_engine.py`) is the fix, and it is default-OFF.

THE CUT RULE IS THE LIVE CONFIG'S, WHICH IS WHY THIS IS NOT A FITTED THRESHOLD
------------------------------------------------------------------------------
Every threshold in `ARMS` is read from `config/agent_config.yaml` at run time, not typed
here. The per-sleeve `fx_jpy: 0.35` override is honoured because the live book honours it.
A number nobody in this session chose cannot have been chosen to produce an answer, and the
declaration records the file, the line and the sha256 of the block it came from.

The LADDER (`k in {0.05, 0.15, 0.20}`) is declared as SENSITIVITY, not as a search: it asks
whether the live constant is a lucky number, and its cells are billed like any other look but
never reported as a sleeve's verdict. The verdict rule uses the live limit alone.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import gzip
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
for _phase in ("phase7", "phase8", "phase9", "phase10", "phase11", "phase12"):
    sys.path.insert(0, str(REPO / f"docs/audits/fable5-vision-audit-20260725/{_phase}/receipts"))

import yaml  # noqa: E402

import ad_exit_sweep as AD  # noqa: E402

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase13/receipts"
PHASE12 = REPO / "docs/audits/fable5-vision-audit-20260725/phase12/receipts"
ESTATE = (REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
          / "AQ_ESTATE_TRADES_V2.json.gz")
FAMILY_V9 = PHASE12 / "CANDIDATE_FAMILY_V9.json"
FAMILY_V10 = HERE / "CANDIDATE_FAMILY_V10.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
LIVE_CONFIG = REPO / "config/agent_config.yaml"
VPS_LAUNCHER_LOG = Path(
    "/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/"
    "ultimate_book_launcher.jsonl.gz"
)

PROTOCOL_OUT = HERE / "AY_SPREAD_GEOMETRY_PROTOCOL_V1.json"
LIVE_OUT = HERE / "AY_LIVE_SCREEN_EVIDENCE_V1.json"
CENSUS_OUT = HERE / "AY_LIVE_CONTRACT_CENSUS_V1.json"
GATE_OUT = HERE / "AY_SLEEVE_GATE_V1.json"
VERDICT_OUT = HERE / "AY_SLEEVE_VERDICT_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BANDS = (None, "low", "mid", "high")
REAL_BANDS = ("low", "mid", "high")
POPULATION = "RECORDED"
OPTION = "B_balanced"
FAMILY_ID = "B7_5_SEPARABILITY_MINE_V1"

ARMED_FOUR = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
RECENTLY_PULLED = ("fx_jpy",)

#: The per-sleeve null. AW ran five seeds; five is enough for a mean but not for the
#: "did the filter beat EVERY random draw" statement the verdict rule needs, whose finest
#: resolution is 1/(N+1). Twenty seeds put that floor at 0.0476, below the 0.05 a reader
#: expects, and cost ~20 s of the ~2 min the whole gate stage takes.
N_RANDOM_SEEDS = 20

#: SENSITIVITY ladder, declared as such (see the module docstring). Never a verdict.
LADDER_SPREAD_R = (0.05, 0.15, 0.20)


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    payload = dict(payload)
    payload["self_sha256"] = _sha({k: v for k, v in payload.items() if k != "self_sha256"})
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO)}  ({path.stat().st_size:,} bytes)")


# =====================================================================================
# THE LIVE CONTRACT, read from the live config rather than typed


def live_cost_contract() -> dict:
    """Read the live pre-trade cost limits out of `config/agent_config.yaml`.

    READ, never written: this file is R2-bound (H1) and its bytes are hashed into BOTH
    live activation tokens' config digests. The five keys are returned with the file's own
    line numbers and a sha256 over the resolved block, so a later reader can tell whether
    the contract this session measured is the contract that was running.
    """
    text = LIVE_CONFIG.read_text(encoding="utf-8")
    cfg = yaml.safe_load(text) or {}
    rt = cfg.get("gtos_vnext_runtime", {}) or {}
    keys = (
        "selected_cell_pretrade_cost_model_required",
        "selected_cell_pretrade_max_spread_r",
        "selected_cell_pretrade_max_total_cost_r",
        "selected_cell_pretrade_max_spread_r_by_sleeve",
        "selected_cell_pretrade_max_total_cost_r_by_sleeve",
        "selected_cell_default_expected_slippage_r",
    )
    resolved = {k: rt.get(k) for k in keys}
    lines = {}
    for n, line in enumerate(text.splitlines(), 1):
        for k in keys:
            if line.strip().startswith(k + ":"):
                lines.setdefault(k, n)
    return {
        "source": str(LIVE_CONFIG.relative_to(REPO)),
        "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "resolved": resolved,
        "config_lines": lines,
        "block_sha256": _sha(resolved),
        "enforced_at": [
            "src/components/broker_net_cost_engine.py:718-727 (spread_r)",
            "src/components/broker_net_cost_engine.py:774-776 (total_cost_r)",
            "src/components/ultimate_book/book_owner.py:4232-4270 (pre-send mirror)",
        ],
        "reached_because": (
            "execution_packets.build_book_trade_params stamps "
            "gtos_vnext_production_execution_path=True (:348, :538), the predicate "
            "execution._is_vnext_production_execution_path:1902-1913 tests before building "
            "the packet; a refusal returns None from open_trade (execution.py:3438-3443)."
        ),
    }


def sleeve_spread_limit(contract: dict, sleeve: str) -> float:
    r = contract["resolved"]
    by = r.get("selected_cell_pretrade_max_spread_r_by_sleeve") or {}
    if sleeve in by:
        return float(by[sleeve])
    return float(r.get("selected_cell_pretrade_max_spread_r") or 0.10)


def sleeve_total_limit(contract: dict, sleeve: str) -> float | None:
    r = contract["resolved"]
    by = r.get("selected_cell_pretrade_max_total_cost_r_by_sleeve") or {}
    if sleeve in by:
        return float(by[sleeve])
    v = r.get("selected_cell_pretrade_max_total_cost_r")
    return None if v is None else float(v)


# =====================================================================================
# ARMS


def build_arms(contract: dict) -> dict:
    """`{arm_name: (kind, param)}`. `kind` decides how `stage_gate` filters.

    `live_spread_contract` IS THE HYPOTHESIS OF RECORD, and it is a PER-SLEEVE rule because
    the live gate is one: `fx_jpy`/`fx_jpy_ny` run 0.35 on an owner-approved 2026-06-16
    trial and every other sleeve runs 0.10. Collapsing that to one global constant would
    measure a contract nobody runs.

    WHY THE SPREAD LIMIT CARRIES THE VERDICT AND THE TOTAL LIMIT DOES NOT
    ---------------------------------------------------------------------
    The spread half is reconstructible EXACTLY: the live gate computes
    `(ask - bid) / sl_distance` and `panel.price_trades` reports `spread_price / sl` — the
    same quantity, from a modelled era-banded spread instead of a live tick.

    The TOTAL half is not, and it took TWO corrections to get right — the first of which
    would have condemned an armed sleeve. The live gate's total is
    `spread_r + expected_slippage_r + swap_cost_r` with **no commission**
    (`broker_net_cost_engine:577-583` sums exactly three terms), where:

      * `expected_slippage_r` is a **flat constant**, `selected_cell_default_expected_slippage_r`
        = 0.02, because nothing in the tree writes the trade_params key that would override it;
      * `swap_cost_r` is `daily_drag * min(horizon_days, cap=1.0)`, off the sleeve's CONTRACT
        horizon rather than any realised hold, and **ten of the 34 declared sleeves have a
        horizon under one day** (down to 0.1667 d).

    Correction 1: the arm first charged the RESEARCH total (commission + realised-hold swap),
    which read `crypto` — armed — as HARMFUL at −0.7247 R/day where the live arithmetic reads
    NEUTRAL at +0.0664. Correction 2, after an adversarial pass: the fix for (1) charged a
    per-symbol MEASURED slippage (up to 2.05x the live flat 0.02) and a FULL night of swap,
    and this docstring claimed the result was a SUBSET of the live refusal set. **It was
    neither a subset nor a superset — a mixture**: 15,808 of 86,387 priced rows over-charged,
    703 outright flips, 11 of them on `sub_mid_dn_revert`, an ARMED sleeve.

    `live_total_recon` now computes the live gate's own arithmetic (see `_live_total_recon`).
    It is still published beside the verdict and never as it, because the spread half needs
    no reconstruction at all and this one does.
    """
    arms: dict[str, tuple] = {
        "control": ("none", None),
        # the hypothesis of record — exact
        "live_spread_contract": ("live_spread", None),
        # the total half, reconstructed as a subset of the live refusal set
        "live_total_recon": ("live_total", None),
        # both together
        "live_both_recon": ("live_both", None),
        # controls, matched to `live_spread_contract`'s per-sleeve drop count
        "inverse_cheapest_matched": ("inverse", None),
    }
    for i in range(N_RANDOM_SEEDS):
        arms[f"random_matched_s{i}"] = ("random", i)
    for k in LADDER_SPREAD_R:
        arms[f"ladder_spread_r_le_{k:g}".replace(".", "p")] = ("spread_r", k)
    return arms


# =====================================================================================
# AY-0 — the declaration


def stage_declare(contract: dict) -> dict:
    arms = build_arms(contract)
    cells = {
        "arms": {k: {"kind": v[0], "param": v[1]} for k, v in arms.items()},
        "bands": [b or "flat_37_day_snapshot" for b in BANDS],
        "population": POPULATION,
        "option": OPTION,
        "family_id": FAMILY_ID,
        "live_contract_block_sha256": contract["block_sha256"],
    }
    return {
        "schema": "gtos.ay.spread_geometry_protocol.v1",
        "declared_at": "2026-07-30",
        "session": "AY (B1800-B1849)",
        "cells_sha256": _sha(cells),
        "cells": cells,
        "live_cost_contract": contract,
        "what_is_being_tested": (
            "Not 'does a cost filter help' -- a cost filter mechanically raises post-cost "
            "mean R and that arithmetic needs no measurement. What is tested is whether the "
            "LIVE pre-trade cost contract, which both funded books already enforce, changes "
            "each sleeve's judged economics BEYOND what dropping the same number of trades "
            "at random does. The filtered arm is the live population; the unfiltered arm is "
            "the fiction every published estate figure is measured on."
        ),
        "cut_rule": {
            "rule": "the LIVE config's own per-sleeve limits, read at run time",
            "why_not_fitted": (
                "The constants are not chosen in this session and not chosen from this "
                "session's data. 0.10/0.15 are in agent_config.yaml and in the sealed "
                "2026-07-16 B7.5 contract; the fx_jpy 0.35/0.45 overrides carry a dated "
                "owner approval (2026-06-16) in the config's own comment. The declaration "
                "pins their sha256 so a later edit is visible."
            ),
            "sensitivity_ladder": list(LADDER_SPREAD_R),
            "ladder_status": (
                "SENSITIVITY ONLY -- billed as looks, never reported as a sleeve's verdict. "
                "It asks whether the live constant is a lucky number, which is a different "
                "question from 'which k is best' and is the only one a pre-registered "
                "threshold can honestly be asked."
            ),
        },
        "controls": {
            "inverse_cheapest_matched": (
                "drops the same COUNT per sleeve, cheapest first. The sharp control: if "
                "dropping the dearest helps and dropping the cheapest hurts, the cost axis "
                "carries information about the TRADE, not just about the bill."
            ),
            "random_matched": (
                f"{N_RANDOM_SEEDS} seeds, same count per sleeve, chosen at random. Gives a "
                f"per-sleeve NULL DISTRIBUTION, not just a mean; the verdict rule reads its "
                f"maximum, whose resolution floor is 1/{N_RANDOM_SEEDS + 1} = "
                f"{1 / (N_RANDOM_SEEDS + 1):.4f}."
            ),
        },
        "verdict_rule": {
            "carried_by": (
                "`live_spread_contract` — the EXACTLY reconstructible half of the live gate. "
                "`live_total_recon` and `live_both_recon` are published on every row and "
                "never decide one; see build_arms for why."
            ),
            "NO_OP": (
                "the live spread limit drops 0 of the sleeve's priced trades at every real "
                "band. The identity-filter check (wave-10 §2): a gate on a coordinate the "
                "sleeve already pins is a no-op that reads as a result."
            ),
            "REPAIR": (
                "at >= 2 of the 3 real bands: delta > 0 AND delta > max(delta over all "
                f"{N_RANDOM_SEEDS} random seeds) AND delta_inverse < 0. All three clauses, "
                "because each kills a different wrong explanation: sign, sample size, and "
                "'any drop would have done'. A sleeve whose inverse control is itself "
                "NOT_EVALUABLE fails the third clause and is published with "
                "`inverse_evaluable: false` so the reason is legible."
            ),
            "HARMFUL": (
                "at >= 2 of the 3 real bands: delta < 0 AND delta < min(delta over all "
                "random seeds). A rule that is already live and harmful is a repair queue "
                "row pointing the other way."
            ),
            "NEUTRAL": "everything else, including 'suggestive but inside the random envelope'.",
            "declared_before": "any outcome of any arm was read",
        },
        "reporting_deltas": {
            "maxbars_share": "published per sleeve per arm (wave-12 delta, binding)",
            "chronological_folds": "published per sleeve (wave-11 §1, binding)",
            "band_column": "published alongside; admissions phrased as 'N of 3 bands'",
        },
    }


def stage_family_v10(contract: dict) -> dict:
    """V10 = V9 plus one member per AY arm. Controls are looks; the ratchet bills them."""
    v9 = json.loads(FAMILY_V9.read_text())
    families = json.loads(json.dumps(v9["families"]))
    mine = families[FAMILY_ID]
    have = {m["name"] for m in mine["members"]}
    added = []
    for arm, (kind, _p) in build_arms(contract).items():
        name = f"ay1_estate::{arm}"
        if name in have:
            continue
        added.append({
            "name": name,
            "source": "AY_SLEEVE_GATE_V1.json:runs",
            "basis": (
                "AY-1 arm over the estate archive at the ratified rule (RECORDED / "
                "B_balanced / four bands). `live_contract` is the hypothesis of record and "
                "reads its thresholds from config/agent_config.yaml; `inverse_cheapest` and "
                f"the {N_RANDOM_SEEDS} `random_matched` seeds are its controls; the three "
                "`ladder_*` cells are declared sensitivity. A control is a look like any "
                "other and is billed like one."
            ),
            "declared_at": "2026-07-30",
            "status": "declared",
            "look_taken": True,
        })
    mine["members"] = list(mine["members"]) + added
    mine["high_water_size"] = len(mine["members"])
    mine["high_water_looks"] = sum(1 for m in mine["members"] if m["look_taken"])
    mine["history"] = list(mine["history"]) + [{
        "at": "2026-07-30",
        "by": "Session AY (B1800-B1849)",
        "what": (
            "AY-1's per-sleeve arms declared. The axis is AW's, so the bill carries AW's "
            "486 as well as these. Note what is NOT billed as a discovery: the THRESHOLD, "
            "which is read from the live config and was set months before either session. "
            "The first run of this stage declared three arms — `live_contract`, "
            "`live_spread_only`, `live_total_only` — whose total term charged the RESEARCH "
            "total (commission + realised-hold swap) rather than the live gate's "
            "one-day-capped, commission-free total. Those looks were taken and are NOT "
            "removed; the corrected arms are declared alongside them and the bill rises. "
            "That is the ratchet doing its job: a specification bug is still a look."
        ),
        "members_added": [m["name"] for m in added],
    }]
    out = dict(v9)
    out["families"] = families
    out["supersedes"] = str(FAMILY_V9.relative_to(REPO))
    out["superseded_because"] = "AY-1's per-sleeve arms and their controls are further looks."
    out["generated_by"] = "ay_spread_geometry.py --stage declare"
    out.pop("self_sha256", None)
    return out


# =====================================================================================
# AY-2a — what the LIVE book already does, measured on its own logs


def stage_live(contract: dict) -> dict:
    """Read the VPS export's launcher log. Nothing here touches the host."""
    if not VPS_LAUNCHER_LOG.is_file():
        return {
            "schema": "gtos.ay.live_screen_evidence.v1",
            "status": "ABSENT",
            "path": str(VPS_LAUNCHER_LOG),
            "note": (
                "The read-only 2026-07-25 VPS export is not on this machine. The live "
                "contract itself is still established from source (see live_cost_contract); "
                "what is missing is the FIRING evidence."
            ),
        }
    cycles = 0
    reasons: collections.Counter = collections.Counter()
    screened: list[dict] = []
    # (namespace, day) -> {"sized": set, "screened": set, "placed": set, "na": set}
    by_day: dict[tuple, dict] = collections.defaultdict(
        lambda: {"sized": set(), "screened": set(), "placed": set(), "na": set()}
    )
    with gzip.open(VPS_LAUNCHER_LOG, "rt") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("action") != "cycle":
                continue
            cycles += 1
            ns = row.get("namespace")
            day = str(row.get("ts") or "")[:10]
            acc = by_day[(ns, day)]
            bridge = row.get("bridge") or {}
            for unit in (bridge.get("realized_units") or []):
                for s in (unit.get("sleeve_members") or ()):
                    acc["sized"].add(s)
                for o in (unit.get("overlays_applied") or ()):
                    if isinstance(o, str) and o.startswith("kelly_lite_na"):
                        acc["na"].add(o)
            for p in (row.get("placed") or []):
                s = p.get("sleeve") if isinstance(p, dict) else None
                if s:
                    acc["placed"].add(s)
            for sk in (row.get("skipped") or []):
                reason = str(sk.get("reason", ""))
                reasons[reason.split(":")[0]] += 1
                if reason.startswith("cost_screen_spread_r") or reason.startswith("pretrade_cost"):
                    sleeve = sk.get("sleeve")
                    if sleeve:
                        acc["screened"].add(sleeve)
                    screened.append({
                        "ns": ns, "day": day, "sleeve": sleeve,
                        "symbol": sk.get("symbol"), "reason": reason,
                    })

    # parse the observed spread_r out of the screen's own message
    obs = []
    for row in screened:
        r = row["reason"]
        if r.startswith("cost_screen_spread_r:"):
            try:
                head = r.split(":", 1)[1].split(" ")[0]
                got, lim = head.split(">")
                obs.append({**row, "spread_r": float(got), "limit": float(lim)})
            except Exception:
                pass
    by_sleeve: dict[str, dict] = {}
    for o in obs:
        d = by_sleeve.setdefault(o["sleeve"], {"n": 0, "max_spread_r": 0.0, "symbols": set()})
        d["n"] += 1
        d["max_spread_r"] = max(d["max_spread_r"], o["spread_r"])
        d["symbols"].add(o["symbol"])

    # THE CONVICTION CONTAMINATION. A sleeve whose every leg that day was cost-screened
    # still entered the day's firing union, because `_running_conviction_override` counts
    # INTENTS and the screen runs later, in book_owner, at send time.
    bins = ((1, 1, 0.748), (2, 3, 0.991), (4, 99, 1.241))

    def mult(n: int) -> float:
        for lo, hi, m in bins:
            if lo <= n <= hi:
                return m
        return 1.0

    contam = []
    for (ns, day), acc in sorted(by_day.items()):
        fired = acc["sized"] | acc["screened"]
        only_screened = {s for s in acc["screened"] if s not in acc["sized"]}
        # A sleeve that was sized on one leg and screened on another genuinely fired.
        doomed = {s for s in acc["screened"] if s not in acc["placed"]}
        n_actual, n_clean = len(fired), len(fired - doomed)
        if not fired or n_actual == n_clean:
            continue
        contam.append({
            "namespace": ns, "day": day,
            "n_firing_counted": n_actual,
            "n_firing_if_screened_excluded": n_clean,
            "kelly_multiplier_counted": mult(n_actual),
            "kelly_multiplier_clean": mult(n_clean),
            "size_inflation_pct": round(100.0 * (mult(n_actual) / mult(n_clean) - 1.0), 4),
            "sleeves_never_placed_but_counted": sorted(doomed),
            "sleeves_only_ever_screened": sorted(only_screened),
        })
    moved = [c for c in contam if c["size_inflation_pct"] > 0]
    return {
        "schema": "gtos.ay.live_screen_evidence.v1",
        "status": "MEASURED",
        "source": str(VPS_LAUNCHER_LOG),
        "source_note": (
            "The read-only 2026-07-25 VPS export, which predates both arming ceremonies. "
            "It measures the screen's behaviour on the SHADOW book, whose generation and "
            "cost gate are the same code the armed book runs (the gates decide broker "
            "authority, not generation)."
        ),
        "live_cost_contract": contract,
        "cycles": cycles,
        "skip_reasons": dict(reasons.most_common()),
        "n_cost_screen_or_pretrade_cost_skips": len(screened),
        "n_with_parsed_spread_r": len(obs),
        "observed_spread_r": {
            "max": round(max((o["spread_r"] for o in obs), default=0.0), 4),
            "median": round(statistics.median([o["spread_r"] for o in obs]), 4) if obs else None,
            "by_sleeve": {
                s: {"n": d["n"], "max_spread_r": round(d["max_spread_r"], 4),
                    "symbols": sorted(d["symbols"])}
                for s, d in sorted(by_sleeve.items(), key=lambda kv: -kv[1]["n"])
            },
        },
        "conviction_contamination": {
            "what": (
                "book_engine._running_conviction_override:865-915 counts a day's distinct "
                "firing sleeves from INTENTS, after precount_intent_filter's five drop "
                "rules. The pre-trade cost screen is not one of them and runs later, in "
                "book_owner at send time. admission.py:1188 takes na = max(na, override), "
                "monotone upward, so a sleeve that never placed a single leg can still "
                "raise the day's Kelly-lite multiplier for every sleeve that did."
            ),
            "live_flags_required": {
                "ultimate_book_kelly_lite": True, "ultimate_book_kelly_running_count": True,
                "note": "both are true on the live host (CLAUDE.md §4; bridge payload confirms)",
            },
            "bins": [list(b) for b in bins],
            "n_account_days_with_a_doomed_sleeve_counted": len(contam),
            "n_account_days_where_it_moved_the_multiplier": len(moved),
            "max_size_inflation_pct": round(
                max((c["size_inflation_pct"] for c in contam), default=0.0), 4),
            "days": contam,
        },
    }


# =====================================================================================
# pricing


def load_estate() -> dict:
    doc = json.loads(gzip.open(ESTATE, "rt").read())
    return {s: rows for s, rows in doc["trades"].items() if rows}


#: The live gate's slippage term is a FLAT CONSTANT, not a per-symbol measurement.
#: `broker_net_cost_engine:544-548` reads `gtos_vnext_expected_slippage_r` from trade_params
#: and falls back to `selected_cell_default_expected_slippage_r`; **nothing in the tree writes
#: that trade_params key on a live order** (the only writer is the replay loop), so the
#: fallback IS the live behaviour. Read from config at run time, never typed.
def live_slippage_r(contract: dict) -> float:
    v = contract["resolved"].get("selected_cell_default_expected_slippage_r")
    return 0.0 if v is None else float(v)


#: The live gate's swap term is `daily_drag * min(horizon_days, cap)`, where `horizon_days`
#: comes from the sleeve's own `time_stop_bars` at `selected_cell_swap_cost_minutes_per_bar`
#: (15) and `cap` is `selected_cell_swap_cost_horizon_days_cap` (1.0). **Ten of the 34
#: declared sleeves have a horizon UNDER one day** — `liq_asia_up_low_metal` 0.1667 d,
#: `ny_crypto_momentum` 0.2083, `metal_session_reversion` 0.25, `asia_pdl_fade` and
#: `kz_london_crypto_low` 0.3333, four at 0.5, `orb_crypto_london` 0.8333 — so charging them
#: a full night, as the first version of this file did, over-charges them by up to 6x.
LIVE_SWAP_MINUTES_PER_BAR = 15.0
LIVE_SWAP_HORIZON_CAP_DAYS = 1.0


def live_horizon_days(sleeve: str) -> float:
    from src.components.ultimate_book.execution_packets import (
        DEFAULT_EXIT_PROFILE, SLEEVE_EXIT_PROFILES,
    )
    prof = SLEEVE_EXIT_PROFILES.get(sleeve) or DEFAULT_EXIT_PROFILE
    bars = prof.get("time_stop_bars") or DEFAULT_EXIT_PROFILE["time_stop_bars"]
    return min(float(bars) * LIVE_SWAP_MINUTES_PER_BAR / 1440.0, LIVE_SWAP_HORIZON_CAP_DAYS)


def _live_total_recon(comp: dict, daily_drag_r, sleeve: str, slip: float) -> float | None:
    """`spread_r + the live slippage constant + daily_drag * min(horizon, 1 day)`.

    THE LIVE GATE'S OWN ARITHMETIC, not an approximation of it — corrected after an
    adversarial pass refuted the first version. That version charged `slippage_r` (a
    per-symbol MEASURED value, up to 2.05x the live flat 0.02) and a FULL night of swap, and
    claimed the result was a subset of the live refusal set. It was neither a subset nor a
    superset: 15,808 of 86,387 priced rows were over-charged and 703 flipped outright,
    including 11 on `sub_mid_dn_revert` — an ARMED sleeve. The one thing that version had
    right is that the live total carries **no commission** (`broker_net_cost_engine:577-583`
    sums exactly three terms), and that is still true here.

    `daily_drag_r` is `swap_r / nights` measured on a long-hold probe (see `priced_by_band`),
    which is exact for any nights > 0 because `cost_r` computes `swap_r = drag * nights / sl`.
    None when the probe could not price the trade — published as None, never as zero.
    """
    if not comp or daily_drag_r is None:
        return None
    return (float(comp.get("spread_r") or 0.0)
            + float(slip)
            + float(daily_drag_r) * live_horizon_days(sleeve))


#: Long enough that `rollover_nights` charges at least one night from ANY entry weekday, so
#: `swap_r / nights` recovers the per-night drag exactly. The value of the divisor does not
#: matter (`swap_r = drag * nights / sl` makes the ratio drag/sl for every nights > 0); what
#: matters is that it is never zero, which a 24 h probe is not guaranteed to avoid.
_SWAP_PROBE_HOURS = 192.0


def priced_by_band(recs: dict, costs, band, contract: dict) -> dict:
    """`{sleeve: [(TradeRecord, spread_r, live_total_r, status, research_total_r, nights)]}`.

    Gate-native pricing (`panel.price_trades`, the one cost authority), run TWICE: once as
    the trade actually ran, and once on a clone held `_SWAP_PROBE_HOURS` so the per-night
    swap drag can be recovered for every trade — including the ones whose realised hold
    crossed no rollover at all, which the first version of this file could only charge as
    zero. The third slot is the LIVE gate's total; the research total that
    `PricedTrade.cost_r` reports is kept in the fifth so the difference stays visible rather
    than being silently replaced.
    """
    o = OPTIONS[OPTION]
    spec = o.with_(spec_id=f"{o.spec_id}_ay_price", spread_band=band)
    slip = live_slippage_r(contract)
    out: dict[str, list] = collections.defaultdict(list)
    for sleeve, trades in recs.items():
        priced, _ = price_trades(trades, spec, costs=costs)
        probe_recs = [
            dataclasses.replace(t, exit_utc=t.entry_utc + dt.timedelta(hours=_SWAP_PROBE_HOURS))
            for t in trades
        ]
        probed, _ = price_trades(probe_recs, spec, costs=costs)
        for p, q in zip(priced, probed):
            comp = p.components or {}
            qc = q.components or {}
            nights = float(q.swap_nights) if q.swap_nights else 0.0
            drag = (float(qc.get("swap_r") or 0.0) / nights) if nights > 0 else None
            out[sleeve].append((
                p.trade, comp.get("spread_r"),
                _live_total_recon(comp, drag, sleeve, slip), p.status,
                p.cost_r, p.swap_nights,
            ))
    return out


def _maxbars_share(trades) -> float | None:
    n = len(trades)
    if not n:
        return None
    mb = sum(1 for t in trades if (t.features or {}).get("exit_reason") == "maxbars")
    return round(mb / n, 6)


# =====================================================================================
# AY-1a — the census, at the LIVE per-sleeve limits


def stage_census(recs: dict, costs, contract: dict) -> dict:
    per_band = {}
    for band in BANDS:
        rows = priced_by_band(recs, costs, band, contract)
        per_sleeve = {}
        tot = priced_n = over_sp = over_tot = over_either = 0
        for sleeve, items in sorted(rows.items()):
            sp_lim = sleeve_spread_limit(contract, sleeve)
            tot_lim = sleeve_total_limit(contract, sleeve)
            pr = [it for it in items if it[3] == "priced" and it[1] is not None]

            def over_sp_(it):
                return it[1] > sp_lim

            def over_tot_(it):
                return tot_lim is not None and it[2] is not None and it[2] > tot_lim

            osp = sum(1 for it in pr if over_sp_(it))
            otot = sum(1 for it in pr if over_tot_(it))
            oeith = sum(1 for it in pr if over_sp_(it) or over_tot_(it))
            r_over = [it[0].r_gross for it in pr if over_sp_(it)]
            r_keep = [it[0].r_gross for it in pr if not over_sp_(it)]
            # The reconstruction's own blind spot, published per sleeve: a trade whose
            # realised hold crossed no rollover gets ZERO swap here and up to one night at
            # the live gate. These are the rows on which this census under-refuses.
            n_zero_nights = sum(1 for it in pr if not it[5])
            n_total_unpriceable = sum(1 for it in pr if it[2] is None)
            per_sleeve[sleeve] = {
                "spread_r_limit": sp_lim,
                "total_cost_r_limit": tot_lim,
                "limit_is_sleeve_override": sleeve in (
                    contract["resolved"].get("selected_cell_pretrade_max_spread_r_by_sleeve") or {}),
                "n_trades": len(items), "n_priced": len(pr),
                "n_over_spread_limit": osp,
                "n_over_live_total_recon_limit": otot,
                "n_refused_by_live_contract": oeith,
                "frac_over_spread_limit": round(osp / len(pr), 6) if pr else None,
                "frac_refused_by_live_contract": round(oeith / len(pr), 6) if pr else None,
                "live_horizon_days": round(live_horizon_days(sleeve), 6),
                "n_realised_hold_crossed_no_rollover": n_zero_nights,
                "n_live_total_unreconstructible": n_total_unpriceable,
                "median_spread_r": (
                    round(float(sorted(it[1] for it in pr)[len(pr) // 2]), 6) if pr else None),
                "max_spread_r": round(max((it[1] for it in pr), default=0.0), 6) if pr else None,
                "mean_r_gross_over_spread_limit": (
                    round(statistics.fmean(r_over), 6) if r_over else None),
                "mean_r_gross_within_spread_limit": (
                    round(statistics.fmean(r_keep), 6) if r_keep else None),
                "armed": sleeve in ARMED_FOUR,
            }
            tot += len(items)
            priced_n += len(pr)
            over_sp += osp
            over_tot += otot
            over_either += oeith
        per_band[band or "flat_37_day_snapshot"] = {
            "n_trades": tot, "n_priced": priced_n,
            "n_over_spread_limit": over_sp,
            "n_over_live_total_recon_limit": over_tot,
            "n_refused_by_live_contract": over_either,
            "frac_over_spread_limit": round(over_sp / priced_n, 6) if priced_n else None,
            "frac_refused_by_live_contract": round(over_either / priced_n, 6) if priced_n else None,
            "by_sleeve": per_sleeve,
        }
    return {
        "schema": "gtos.ay.live_contract_census.v1",
        "what_this_measures": (
            "How much of the estate's own archive the LIVE pre-trade cost gate would refuse "
            "— per sleeve, at each sleeve's own live limit (fx_jpy/fx_jpy_ny run the "
            "owner-approved 0.35/0.45; everything else 0.10/0.15). AW published the same "
            "census against a single global 0.10, which understates the two JPY sleeves and "
            "is right about all the others."
        ),
        "total_limit_caveat": (
            "`n_over_live_total_recon_limit` uses `_live_total_recon` = spread_r + the LIVE "
            "flat slippage constant (selected_cell_default_expected_slippage_r = 0.02, which "
            "is the live behaviour because nothing writes the trade_params key that would "
            "override it) + daily_drag * min(the SLEEVE'S OWN contract horizon, 1.0 day). No "
            "commission, because the live total has none. An earlier version of this file "
            "charged per-symbol MEASURED slippage and a FULL night of swap and claimed the "
            "result was a subset of the live refusal set; an adversarial pass measured that "
            "it was neither a subset nor a superset but a MIXTURE (15,808 of 86,387 rows "
            "over-charged, 703 flips, 11 on the armed sub_mid_dn_revert), because ten of the "
            "34 declared sleeves have a contract horizon under one day. That claim is "
            "withdrawn and these columns are the corrected ones."
        ),
        "total_limit_residual_approximation": (
            "The per-night swap drag is recovered exactly, for every trade including those "
            "whose realised hold crossed no rollover, from a "
            f"{int(_SWAP_PROBE_HOURS)}-hour pricing probe (swap_r / nights is drag/sl for any "
            "nights > 0). What remains approximate is the SPREAD source: the live gate reads "
            "a tick at send time and this reads the era-banded model at entry, which is why "
            "all four bands are published."
        ),
        "estate": str(ESTATE.relative_to(REPO)),
        "costs": str(COSTS.relative_to(REPO)),
        "account": ACCOUNT, "server": SERVER,
        "live_cost_contract": contract,
        "armed_sleeves": list(ARMED_FOUR),
        "recently_pulled_sleeves": list(RECENTLY_PULLED),
        "by_band": per_band,
    }


# =====================================================================================
# AY-1b — the gate


def _refused_by(kind, param, spread_r, live_total_r, status, sp_lim, tot_lim) -> bool:
    # An UNPRICED trade cannot be shown to violate a cost limit, so it is kept and the
    # gate's own coverage policy handles it. Dropping it here would silently turn "we
    # could not price this" into "this is too expensive".
    if status != "priced" or spread_r is None:
        return False
    if kind in ("live_spread", "live_both") and spread_r > sp_lim:
        return True
    if (kind in ("live_total", "live_both") and tot_lim is not None
            and live_total_r is not None and live_total_r > tot_lim):
        return True
    if kind == "spread_r" and spread_r > float(param):
        return True
    return False


def _filter_rows(items, kind, param, contract, sleeve):
    """Return `(kept_trades, n_dropped)` for one arm on one sleeve."""
    sp_lim = sleeve_spread_limit(contract, sleeve)
    tot_lim = sleeve_total_limit(contract, sleeve)
    if kind == "none":
        return [it[0] for it in items], 0
    if kind in ("live_spread", "live_total", "live_both", "spread_r"):
        keep, dropped = [], 0
        for trade, spread_r, live_total_r, status, _res_total, _nights in items:
            if _refused_by(kind, param, spread_r, live_total_r, status, sp_lim, tot_lim):
                dropped += 1
                continue
            keep.append(trade)
        return keep, dropped
    # Controls: drop the SAME COUNT the HYPOTHESIS OF RECORD drops on this sleeve —
    # `live_spread_contract`, not the arm's own rule. A matched count that silently became
    # the arm's own count would make every control self-matching and the comparison
    # meaningless, so it is written out here rather than routed through `_refused_by(kind)`.
    priced = [it for it in items if it[3] == "priced" and it[1] is not None]
    n_drop = sum(1 for it in priced if it[1] > sp_lim)
    if kind == "inverse":
        order = sorted(range(len(priced)), key=lambda i: priced[i][1])
    else:
        rng = random.Random(20260730 + int(param) * 1_000_003 + len(priced))
        order = list(range(len(priced)))
        rng.shuffle(order)
    drop_ids = {id(priced[i][0]) for i in order[:n_drop]}
    keep = [it[0] for it in items if id(it[0]) not in drop_ids]
    return keep, n_drop


def stage_gate(recs: dict, costs, contract: dict, ledger: TrialLedger | None) -> dict:
    fam = CF.load_candidate_family(FAMILY_V10)
    allow = AD.allowlist()
    arms = build_arms(contract)
    results = {}
    for band in BANDS:
        rows = priced_by_band(recs, costs, band, contract)
        for arm, (kind, param) in arms.items():
            filtered, dropped, per_sleeve_dropped = {}, 0, {}
            for sleeve, items in rows.items():
                keep, nd = _filter_rows(items, kind, param, contract, sleeve)
                per_sleeve_dropped[sleeve] = nd
                dropped += nd
                if keep:
                    filtered[sleeve] = keep
            if not filtered:
                results[f"{arm}|{band or 'flat'}"] = {
                    "arm": arm, "band": band, "verdicts": {}, "note": "empty"}
                continue
            o = OPTIONS[OPTION]
            spec = o.with_(spec_id=f"{o.spec_id}_ay1_{arm}",
                           sleeve_symbol_allowlist=allow, spread_band=band)
            spec = CF.with_declared_family(spec, FAMILY_ID, loaded=fam)
            recs2, spec, mix = EP.apply(POPULATION, dict(filtered), spec,
                                        account=ACCOUNT, band=(band or "mid"))
            t0 = time.time()
            res = run_gate(recs2, spec, costs=costs, server=SERVER, diagnose=True)
            elapsed = round(time.time() - t0, 1)
            if (res.family.get("wipeout") or {}).get("wiped_out"):
                raise SystemExit(
                    f"whole-run wipeout on {arm}/{band}: {res.family['wipeout']} — "
                    "refusing to tabulate a wall of nulls as a result (AQ B1435)")
            # The 20 random controls are 72 % of this artifact's bytes and the verdict rule
            # reads four scalars from each. Their fold tables are dropped -- NOT the folds of
            # any hypothesis arm, and not any scalar the rule uses -- so a reader can still
            # reproduce every verdict from the file while it stays under the 5 MB threshold
            # `OVERENGINEERING_AND_DELETION_MAP.md` measures 280 inline blobs against.
            # Regenerating with this line removed restores them.
            slim = kind == "random"
            verdicts = {}
            for sleeve, sv in res.verdicts.items():
                verdicts[sleeve] = {
                    "verdict": sv.verdict.value, "n_trades": sv.n_trades,
                    "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                    "p_raw": sv.p_raw, "q": sv.q_value,
                    "folds_positive": sv.gates.get("stability", {}).get("positive_frac"),
                    "oos_mean_r_per_trade": (sv.telemetry or {}).get("oos_mean_r_per_trade"),
                    "n_dropped_by_arm": per_sleeve_dropped.get(sleeve, 0),
                    "maxbars_share": _maxbars_share(recs2.get(sleeve) or ()),
                    # THE CHRONOLOGICAL FOLD TABLE — wave-11 §1, binding on every
                    # admission-grade row. `test_mean_r` is the OOS mean of that fold
                    # (`gate.FoldSlice.as_dict`); the first draft of this file read a key
                    # named `oos_mean_r`, which does not exist, and published a column of
                    # nulls that looked like "no decay" rather than "not measured".
                    "folds": None if slim else [
                        {"fold_id": f.get("fold_id"), "oos_start": f.get("oos_start"),
                         "oos_end": f.get("oos_end"), "status": f.get("status"),
                         "n_test_days": f.get("n_test_days"),
                         "n_test_trades": f.get("n_test_trades"),
                         "test_mean_r": f.get("test_mean_r")}
                        for f in (sv.folds or [])],
                    # The fold CALENDAR survives slimming even when the fold table does not:
                    # an adversarial pass pointed out that the random arms' spans are exactly
                    # what shows the control calendars are asymmetric to the hypothesis arm's
                    # (§3.1), and dropping them would make that caveat unreproducible from
                    # the artifact it is published in.
                    "fold_span": [
                        (f.get("oos_start"), f.get("oos_end")) for f in (sv.folds or [])],
                    "folds_omitted_because": (
                        "random control arm; the fold table is dropped for size, the fold "
                        "SPANS and every scalar the verdict rule reads are kept"
                        if slim else None),
                    "reasons": list(sv.reasons)[:4],
                }
            key = f"{arm}|{band or 'flat'}"
            results[key] = {
                "arm": arm, "arm_kind": kind, "band": band or "flat_37_day_snapshot",
                "band_is_control": band is None,
                "population": POPULATION, "option": OPTION,
                "spec_sha256": spec.seal(),
                "declared_family_id": FAMILY_ID,
                "declared_family_size": spec.declared_family_size,
                "effective_family_size": res.family["multiplicity"]["effective_family_size"],
                "alpha": spec.alpha, "multiplicity": spec.multiplicity,
                "trades_dropped_by_arm": dropped,
                "population_mix": mix, "seconds": elapsed,
                "n_admit": sum(1 for v in verdicts.values() if v["verdict"] == "ADMIT"),
                "best_p_raw": min((v["p_raw"] for v in verdicts.values()
                                   if v["p_raw"] is not None), default=None),
                "verdicts": verdicts,
            }
            if ledger is not None:
                for sleeve, v in verdicts.items():
                    ledger.record(
                        mechanism="ay1_live_cost_contract", sleeve=sleeve,
                        variant={"arm": arm, "band": band or "flat", "population": POPULATION,
                                 "option": OPTION},
                        window="full_archive", spec_sha256=spec.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(v["verdict"], "evaluated"),
                        metric=v["pooled_oos_mean_r"], metric_name="pooled_oos_mean_r",
                        note="AY-1: the LIVE pre-trade cost contract applied to the estate archive")
            print(f"  {arm:28s} band={str(band):5s} dropped={dropped:6d} "
                  f"admits={results[key]['n_admit']} ({elapsed}s)")
    return {
        "schema": "gtos.ay.sleeve_gate.v1",
        "estate": str(ESTATE.relative_to(REPO)),
        "costs": str(COSTS.relative_to(REPO)),
        "family": str(FAMILY_V10.relative_to(REPO)),
        "family_id": FAMILY_ID,
        "protocol": str(PROTOCOL_OUT.relative_to(REPO)),
        "live_cost_contract": contract,
        "arms": {k: {"kind": v[0], "param": v[1]} for k, v in arms.items()},
        "n_random_seeds": N_RANDOM_SEEDS,
        "runs": results,
    }


# =====================================================================================
# AY-1c — the verdict table


def _recent_folds(folds, k: int = 2) -> float | None:
    """Mean OOS R over the k most recent EVALUABLE folds, or None if there are none.

    `None` rather than 0.0: a sleeve with no evaluable recent fold has no recent
    expectancy, and a zero there would read as "flat" to every downstream sizing
    conversation instead of "unmeasured".
    """
    if not folds:
        return None
    vals = [f["test_mean_r"] for f in folds
            if f.get("status") == "evaluable" and f.get("test_mean_r") is not None]
    if not vals:
        return None
    return round(statistics.fmean(vals[-k:]), 6)


def _ladder_deltas(runs: dict, gate: dict, sleeve: str) -> dict:
    """Ladder-arm deltas against the same control, at band `mid`. None where either side
    is missing — an absent number is published as absent, never as zero."""
    ctl = ((runs.get("control|mid") or {}).get("verdicts") or {}).get(sleeve) or {}
    base = ctl.get("pooled_oos_mean_r")
    out = {}
    for arm in (a for a in gate["arms"] if a.startswith("ladder_")):
        v = ((runs.get(f"{arm}|mid") or {}).get("verdicts") or {}).get(sleeve) or {}
        got = v.get("pooled_oos_mean_r")
        out[arm] = None if (base is None or got is None) else round(got - base, 6)
    return out


def stage_verdict(gate: dict, contract: dict) -> dict:
    runs = gate["runs"]
    sleeves = sorted({s for r in runs.values() for s in (r.get("verdicts") or {})})
    rand_arms = [f"random_matched_s{i}" for i in range(N_RANDOM_SEEDS)]
    out = {}
    for sleeve in sleeves:
        per_band = {}
        for band in REAL_BANDS:
            def get(arm, key="pooled_oos_mean_r"):
                r = runs.get(f"{arm}|{band}") or {}
                v = (r.get("verdicts") or {}).get(sleeve)
                return None if v is None else v.get(key)

            base = get("control")
            live = get("live_spread_contract")
            if base is None or live is None:
                per_band[band] = {"evaluable": False}
                continue
            d_live = live - base
            d_inv = (get("inverse_cheapest_matched") - base
                     if get("inverse_cheapest_matched") is not None else None)
            d_rand = [get(a) - base for a in rand_arms if get(a) is not None]
            n_rand = [get(a, "n_trades") for a in rand_arms if get(a, "n_trades") is not None]
            ctl = runs.get(f"control|{band}", {}).get("verdicts", {}).get(sleeve) or {}
            arm = runs.get(f"live_spread_contract|{band}", {}).get("verdicts", {}).get(sleeve) or {}
            tot = runs.get(f"live_total_recon|{band}", {}).get("verdicts", {}).get(sleeve) or {}
            both = runs.get(f"live_both_recon|{band}", {}).get("verdicts", {}).get(sleeve) or {}
            n_drop = arm.get("n_dropped_by_arm", 0)
            beats_all = bool(d_rand) and d_live > max(d_rand)
            below_all = bool(d_rand) and d_live < min(d_rand)
            per_band[band] = {
                "evaluable": True,
                "n_dropped_by_live_contract": n_drop,
                "control_pooled_oos_mean_r": base,
                "live_contract_pooled_oos_mean_r": live,
                "delta_live_contract": round(d_live, 6),
                # published beside the verdict, never as it — see build_arms
                "live_total_recon_pooled_oos_mean_r": tot.get("pooled_oos_mean_r"),
                "live_total_recon_n_dropped": tot.get("n_dropped_by_arm"),
                "live_both_recon_pooled_oos_mean_r": both.get("pooled_oos_mean_r"),
                "live_both_recon_n_dropped": both.get("n_dropped_by_arm"),
                "delta_inverse_cheapest": None if d_inv is None else round(d_inv, 6),
                "delta_random_mean": round(statistics.fmean(d_rand), 6) if d_rand else None,
                "delta_random_sd": (round(statistics.pstdev(d_rand), 6)
                                    if len(d_rand) > 1 else None),
                "delta_random_min": round(min(d_rand), 6) if d_rand else None,
                "delta_random_max": round(max(d_rand), 6) if d_rand else None,
                "n_random_beaten": sum(1 for d in d_rand if d_live > d),
                "n_random": len(d_rand),
                # 1/(N+1) when the arm beats every seed — the RESOLUTION FLOOR of a 20-seed
                # null, not a measured value, and the same number on all three bands because
                # the seeds are shared. Read `beats_every_random` as the statement; read this
                # as "the finest p 20 seeds can express".
                "empirical_p_vs_random": (
                    round((sum(1 for d in d_rand if d >= d_live) + 1) / (len(d_rand) + 1), 6)
                    if d_rand else None),
                "empirical_p_is_the_resolution_floor": bool(d_rand) and d_live > max(d_rand),
                # The controls are matched on the DROP COUNT before the population rule runs;
                # `EP.apply(RECORDED)` then runs per arm, so the SCORED n differs between the
                # arm and its controls. Published because "same sample size" is the natural
                # reading of a matched control and it is not what is matched.
                "n_trades_scored_control": ctl.get("n_trades"),
                "n_trades_scored_live_contract": arm.get("n_trades"),
                "n_trades_scored_random_mean": (
                    round(statistics.fmean(n_rand), 4) if n_rand else None),
                "n_trades_scored_inverse": (
                    runs.get(f"inverse_cheapest_matched|{band}", {}).get("verdicts", {})
                    .get(sleeve, {}).get("n_trades")),
                "beats_every_random": beats_all,
                "below_every_random": below_all,
                "inverse_is_negative": (d_inv is not None and d_inv < 0),
                # Published so "not a REPAIR" is legible: a sleeve whose inverse control
                # could not be evaluated fails the third clause for a reason that is about
                # the CONTROL, not about the sleeve.
                "inverse_evaluable": d_inv is not None,
                "control_verdict": ctl.get("verdict"),
                "live_contract_verdict": arm.get("verdict"),
                "control_p_raw": ctl.get("p_raw"),
                "live_contract_p_raw": arm.get("p_raw"),
                "control_n_trades": ctl.get("n_trades"),
                "live_contract_n_trades": arm.get("n_trades"),
                "maxbars_share_control": ctl.get("maxbars_share"),
                "maxbars_share_live_contract": arm.get("maxbars_share"),
                "folds_control": ctl.get("folds"),
                "folds_live_contract": arm.get("folds"),
                # THE FOLD TABLES ARE NOT ALWAYS COMPARABLE, and silently pairing them
                # would be a wrong claim in a table that looks right. `build_fold_calendar`
                # derives the boundaries from the SPAN of the data it is given, so an arm
                # that drops a sleeve's earliest trades moves every boundary — on
                # `sub_mid_dn_revert` by about four years. The POOLED comparison is still
                # valid (each arm is scored OOS on its own calendar); a fold-by-fold one is
                # not, and this flag says which of the two a reader is looking at.
                "fold_calendar_identical": (
                    [(f.get("oos_start"), f.get("oos_end")) for f in (ctl.get("folds") or [])]
                    == [(f.get("oos_start"), f.get("oos_end")) for f in (arm.get("folds") or [])]
                ),
                # AN measured a 7.6x chronological decay that every gate passes, so anything
                # that will be SIZED quotes the recent folds as its expectancy basis.
                "recent_two_folds_mean_r_control": _recent_folds(ctl.get("folds")),
                "recent_two_folds_mean_r_live_contract": _recent_folds(arm.get("folds")),
            }
        ok = [b for b in REAL_BANDS if per_band.get(b, {}).get("evaluable")]
        drops = [per_band[b]["n_dropped_by_live_contract"] for b in ok]
        n_repair = sum(1 for b in ok
                       if per_band[b]["delta_live_contract"] > 0
                       and per_band[b]["beats_every_random"]
                       and per_band[b]["inverse_is_negative"])
        n_harm = sum(1 for b in ok
                     if per_band[b]["delta_live_contract"] < 0
                     and per_band[b]["below_every_random"])
        if not ok:
            verdict = "NOT_EVALUABLE"
        elif drops and max(drops) == 0:
            verdict = "NO_OP"
        elif n_repair >= 2:
            verdict = "REPAIR"
        elif n_harm >= 2:
            verdict = "HARMFUL"
        else:
            verdict = "NEUTRAL"
        out[sleeve] = {
            "verdict": verdict,
            "armed": sleeve in ARMED_FOUR,
            "recently_pulled": sleeve in RECENTLY_PULLED,
            "spread_r_limit_live": sleeve_spread_limit(contract, sleeve),
            "total_cost_r_limit_live": sleeve_total_limit(contract, sleeve),
            "n_bands_repair": n_repair, "n_bands_harmful": n_harm,
            "n_bands_evaluable": len(ok),
            "by_band": per_band,
            # Sensitivity, at `mid` only and labelled as such: does the answer depend on the
            # live constant being exactly 0.10? Never part of the verdict.
            "ladder_delta_mid": _ladder_deltas(runs, gate, sleeve),
        }
    counts = collections.Counter(v["verdict"] for v in out.values())
    return {
        "schema": "gtos.ay.sleeve_verdict.v1",
        "protocol": str(PROTOCOL_OUT.relative_to(REPO)),
        "gate": str(GATE_OUT.relative_to(REPO)),
        "verdict_rule": (
            "REPAIR = at >= 2 of 3 real bands: delta > 0 AND delta > max(random) AND "
            "inverse < 0. HARMFUL = at >= 2 bands: delta < 0 AND delta < min(random). "
            "NO_OP = the live contract drops 0 priced trades at every band. Declared in "
            "AY_SPREAD_GEOMETRY_PROTOCOL_V1.json before any outcome was read."
        ),
        "counts": dict(counts),
        "armed_four": {s: out[s]["verdict"] for s in ARMED_FOUR if s in out},
        "by_sleeve": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=("declare", "live", "census", "gate", "verdict", "all"))
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()
    contract = live_cost_contract()
    print("live cost contract:", json.dumps(contract["resolved"], sort_keys=True))
    if args.stage in ("declare", "all"):
        _write(PROTOCOL_OUT, stage_declare(contract))
        _write(FAMILY_V10, stage_family_v10(contract))
    if args.stage in ("live", "all"):
        _write(LIVE_OUT, stage_live(contract))
    need_estate = args.stage in ("census", "gate", "all")
    if need_estate:
        costs = load_broker_true_costs(COSTS)
        raw = load_estate()
        recs = {s: AD.to_records(rows) for s, rows in raw.items()}
        print(f"estate: {len(recs)} sleeves, {sum(len(v) for v in recs.values()):,} trades")
        if args.stage in ("census", "all"):
            _write(CENSUS_OUT, stage_census(recs, costs, contract))
        if args.stage in ("gate", "all"):
            ledger = None if args.no_ledger else TrialLedger(DEFAULT_TRIAL_LEDGER, session="AY")
            _write(GATE_OUT, stage_gate(recs, costs, contract, ledger))
    if args.stage in ("verdict", "all"):
        gate = json.loads(GATE_OUT.read_text())
        _write(VERDICT_OUT, stage_verdict(gate, contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
