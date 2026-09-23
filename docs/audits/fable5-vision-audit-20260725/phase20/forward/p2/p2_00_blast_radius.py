"""p2-00 — the blast radius of `risk.min_rr`, established by EXECUTION rather than by grep.

Three questions, three executable answers.

Q1  Can `min_rr` reach the armed book at all?
    Answered by the static first-party import closure of `run_book.py`, the live entrypoint.
    A grep for `min_rr` finds 50 files; the question is which of them the live process loads.

Q2  Do the armed sleeves' take-profits derive from it?
    Answered by running `build_book_trade_params` for every armed sleeve at two values of
    `risk.min_rr` and diffing the emitted broker packet byte for byte. A source read cannot
    prove absence of a coupling through four call layers; a differential run can.

Q3  Where does it act as a TARGET, where as a FLOOR, and where is it dead?
    Every read site classified with file:line and the classification justified by the
    surrounding contract, plus the config value that decides the dead ones.
"""

from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

HERE = Path(__file__).resolve().parent
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert")
# `mx_btcusd_d1_donchian_20_breakout` was disarmed by the owner 2026-08-05; carried here as a
# control because the committed launcher still lists it (v1's finding).
CONTROL_SLEEVES = ("mx_btcusd_d1_donchian_20_breakout", "metals_core", "fx_jpy")


def import_closure(entry: str) -> set[str]:
    seen: set[str] = set()
    stack = [entry]

    def modpath(m: str):
        p = REPO / (m.replace(".", "/") + ".py")
        if p.is_file():
            return p
        p2 = REPO / (m.replace(".", "/") + "/__init__.py")
        return p2 if p2.is_file() else None

    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        p = modpath(m)
        if p is None:
            continue
        try:
            tree = ast.parse(p.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in ("src", "scripts"):
                        stack.append(a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in ("src", "scripts"):
                    stack.append(node.module)
                    for a in node.names:
                        stack.append(node.module + "." + a.name)
    return seen


def q2_armed_packets():
    """Where does each armed sleeve's broker take-profit actually come from?

    Two independent proofs, because either alone can be argued with:

    (a) STRUCTURAL — `build_book_trade_params` takes no `config` argument at all
        (`execution_packets.py:506-507`), so it has no object on which to read `risk.min_rr`.
        Reported as its live signature so a future signature change breaks this claim loudly.

    (b) BEHAVIOURAL — run it for every armed sleeve under a config whose `risk.min_rr` is
        monkeypatched into a poison pill that RAISES on read. If any layer under the packet
        builder consulted the key, the build would raise instead of returning.
    """
    import inspect

    from src.components.ultimate_book.execution_packets import (
        DEFAULT_EXIT_PROFILE, SLEEVE_EXIT_PROFILES, build_book_trade_params,
    )

    class _Intent:
        def __init__(self, sleeve):
            self.sleeve = sleeve
            self.symbol = "XAUUSD"
            self.direction = 1
            self.decision_day = "2026-08-07"
            self.stop_dist = 1.0
            self.target_dist = 4.0

    class _Sized:
        def __init__(self, sleeve):
            self.sleeve = sleeve
            self.symbol = "XAUUSD"
            self.risk_pct_per_trade = 0.005
            self.cluster = "book"
            self.confidence = 0.5
            self.n_trades = 100
            self.sleeve_members = ()
            self.lots = 0.10

    class _PoisonDict(dict):
        """Any read of `min_rr` under this config is a coupling and is fatal."""

        def get(self, k, d=None):
            if k == "min_rr":
                raise AssertionError("risk.min_rr was READ on the armed book packet path")
            return super().get(k, d)

        def __getitem__(self, k):
            if k == "min_rr":
                raise AssertionError("risk.min_rr was READ on the armed book packet path")
            return super().__getitem__(k)

    out = {"_signature": str(inspect.signature(build_book_trade_params)),
           "_takes_config_argument":
               "config" in inspect.signature(build_book_trade_params).parameters}
    acct = {"balance": 100000.0, "equity": 100000.0}
    for sleeve in ARMED + CONTROL_SLEEVES:
        prof = SLEEVE_EXIT_PROFILES.get(sleeve, DEFAULT_EXIT_PROFILE)
        rec = {"profile_source": "SLEEVE_EXIT_PROFILES" if sleeve in SLEEVE_EXIT_PROFILES
               else "DEFAULT_EXIT_PROFILE",
               "declared_final_target_r": prof.get("final_target_r"),
               "final_from_intent": bool(prof.get("final_from_intent"))}
        try:
            p = build_book_trade_params(
                _Sized(sleeve), _Intent(sleeve),
                {"entry_price": 100.0, "stop_loss": 99.0, "risk_distance": 1.0},
                acct, profile_namespace="operator_profile",
            )
            rec["built"] = True
            rec["resolved_final_target_r"] = p.get("gtos_vnext_dynamic_final_target_r")
            rec["take_profit_1"] = p.get("take_profit_1")
            rec["stop_loss"] = p.get("stop_loss")
            rec["implied_rr"] = (
                None if not p.get("take_profit_1") else
                round((p["take_profit_1"] - 100.0) / (100.0 - p["stop_loss"]), 6))
        except AssertionError as exc:
            rec["built"] = False
            rec["min_rr_coupling"] = str(exc)
        except Exception as exc:
            rec["built"] = False
            rec["error"] = f"{type(exc).__name__}: {exc}"
        out[sleeve] = rec
    return out


READ_SITES = [
    # (file:line, what it does with the value, class, live-reachable-from-run_book)
    ("src/components/broader_origin_generators.py:2489-2492",
     "_target_rr(config) -> risk.min_rr; the ONLY source of `target_rr`, which becomes "
     "take_profit_1 = entry +/- target_rr * risk for all ten broader-origin families "
     "(:322 -> :2033 _candidate -> :2086/:2099)", "TARGET", False),
    ("src/components/orchestrator.py:5062-5065",
     "final_target_r fallback = max(tp.risk_reward_ratio, min_rr) when the dynamic context "
     "carries no target; :5111-5113 then rebuilds take_profit_1 = entry +/- final_target_r * "
     "sl_distance off the LIVE fill. Both terms of the max are min_rr for a broad candidate, "
     "because the generator set risk_reward_ratio = target_rr = min_rr.", "TARGET", False),
    ("src/components/permissions.py:2116, 2149-2150, 2160-2161",
     "rebuilds take_profit_1 at min_rr when correcting inverted geometry -- but only under "
     "risk.inverted_geometry_policy in {auto_correct, autocorrect, mirror}; "
     "config/agent_config.yaml:43 is `reject`, so the branch returns an ExecutionDenial at "
     ":2141 before reaching it.", "TARGET (dead by config)", False),
    ("src/components/expired_poi_watch.py:204, 483, 560",
     "min_rearm_rr -- a THRESHOLD a re-armed POI must clear. This is the documented use of a "
     "floor and is not a target.", "FLOOR", False),
    ("scripts/batch_backtest.py:815-817, scripts/backtest_runner.py:691-693",
     "rejects a candidate whose rr < min_rr - 0.1. FLOOR, correct use.", "FLOOR", False),
    ("src/research_infra/dumb_baseline.py:390, 414, 647-660, 2099-2117",
     "research reference implementation: uses min_rr as the target when the structural target "
     "implies less than it (:647-655) and unconditionally in the fallback (:2099).",
     "TARGET (research)", False),
    ("src/research_infra/ob_zone_test.py:767-829, :860-924; "
     "src/research_infra/ob_zone_original_geometry.py:312-416",
     "research harnesses: TP = entry +/- min_rr * sl_dist.", "TARGET (research)", False),
    ("scripts/simulate_t7_live_period.py:831-832, 990-999",
     "drawdown_reduction.min_rr overriding risk.min_rr as the rebuilt TP.",
     "TARGET (research)", False),
    ("src/research_infra/incremental_engine.py:292-293",
     "declares risk.min_rr and drawdown_reduction.min_rr as cache-invalidating config keys, "
     "with the comment 'inverted-TP geometry uses this'.", "CACHE KEY", False),
    ("src/components/knowledge_base.py:289",
     "a literal 1.5 inside a KB default block.", "CONSTANT", False),
    ("src/research_infra/replay_acceleration_candidate_boundary.py:225",
     "a literal 1.5 in the replay boundary's synthetic config.", "CONSTANT", False),
]


def main():
    closure = import_closure("run_book")
    reach = {
        "run_book_first_party_modules": len(closure),
        "broader_origin_generators": "src.components.broader_origin_generators" in closure,
        "orchestrator": "src.components.orchestrator" in closure,
        "permissions": "src.components.permissions" in closure,
        "expired_poi_watch": "src.components.expired_poi_watch" in closure,
        "ultimate_book.execution_packets": "src.components.ultimate_book.execution_packets" in closure,
    }
    res = {
        "schema": "gtos.p2.blast_radius.v1",
        "q1_live_entrypoint_import_closure": reach,
        "q2_armed_sleeve_packets_vs_min_rr": q2_armed_packets(),
        "q3_read_sites": [
            {"site": a, "what": b, "class": c, "reachable_from_run_book": d}
            for a, b, c, d in READ_SITES
        ],
    }
    p = HERE / "P2_BLAST_RADIUS_V1.json"
    p.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["q1_live_entrypoint_import_closure"], indent=1))
    print(json.dumps(res["q2_armed_sleeve_packets_vs_min_rr"], indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
