"""p2-60 — the inertness proof: MY change against the parent, on the whole population.

Loads TWO copies of `broader_origin_generators` by path and runs both over the full 24-symbol,
12-month true-UTC M15 tape:

    BEFORE   the module at the parent commit
    AFTER    the parent commit plus the target-policy change and nothing else

Both are read from explicit files rather than from `src/`, because this branch is shared with
concurrent lanes whose own uncommitted edits to the same module would otherwise be attributed
to this one. (They were, on the first run: BTCUSD and ETHUSD showed 371 differing
`route_session` values apiece, which is the concurrent session-naming repair -- those two
symbols are the ones whose `SESSION_WINDOWS` carry the `off_configured_session` sentinel as a
24-hour window. Isolating the modules by path removes the ambiguity instead of arguing about it.)

Three arms, and the third is the one that states the repair:

  A  AFTER, policy OFF, at the shipped dial      must equal BEFORE on every field, every row
  B  AFTER, policy ON,  at the shipped dial      how many take-profits move if the key is set
  C  BEFORE vs BEFORE-at-a-lower-risk-dial       how many EXIT contracts the legacy resolver
                                                 moves when the RISK dial moves. That number is
                                                 the defect, and under the declared policy it
                                                 is zero.

Usage:  python3 p2_60_inertness.py <before.py> <after.py>
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from p2_10_regen import POI_FAMILIES, SYMS, TARGET_RR, load  # noqa: E402

LOW_DIAL = 0.5  # a risk dial below every declared target -- the case the repair exists for


def load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def emit(mod, sym, bars_raw, cfg):
    t, o, h, lo, c, v = bars_raw
    times = [datetime.fromisoformat(x).astimezone(timezone.utc) for x in t]
    bars = tuple(mod.Bar(time=times[i], open=float(o[i]), high=float(h[i]),
                         low=float(lo[i]), close=float(c[i]), volume=float(v[i]))
                 for i in range(len(c)))
    series = mod.BarSeries(symbol=sym, timeframe="M15", bars=bars,
                           source_path_feature_status="complete",
                           session_windows=mod.SESSION_WINDOWS.get(
                               mod._canonical_symbol(sym), ()))
    rr = mod._target_rr(cfg)
    rows = []
    for i in range(51, len(bars)):
        for cd in mod._generate_single_symbol_candidates(
            series=series, index=i, target_rr=rr, kill_zone="none",
            enable_mined_families=True, enable_microstructure=False,
        ):
            if cd.origin_family in POI_FAMILIES:
                continue
            rows.append((cd.origin_family, cd.direction, round(cd.entry_price, 12),
                         round(cd.stop_loss, 12), round(cd.take_profit_1, 12),
                         cd.route_session, cd.risk_reward_ratio))
    return rows


def main():
    before_p = sys.argv[1] if len(sys.argv) > 1 else "/tmp/head_gen.py"
    after_p = sys.argv[2] if len(sys.argv) > 2 else "/tmp/p2_only.py"
    B = load_module(before_p, "p2_before_gen")
    A = load_module(after_p, "p2_after_gen")
    key = A.TARGET_POLICY_ENABLE_KEY

    cfg_ship = {"risk": {"min_rr": TARGET_RR}}
    cfg_ship_on = {"risk": {"min_rr": TARGET_RR}, "gtos_vnext_runtime": {key: True}}
    cfg_low = {"risk": {"min_rr": LOW_DIAL}}
    cfg_low_on = {"risk": {"min_rr": LOW_DIAL}, "gtos_vnext_runtime": {key: True}}

    res = {"schema": "gtos.p2.inertness.v2", "before": before_p, "after": after_p,
           "shipped_dial_min_rr": TARGET_RR, "low_dial_min_rr": LOW_DIAL, "symbols": {}}
    tot = dict(n=0, A_mismatch=0, B_moved=0, C_legacy_moved_by_dial=0, D_policy_moved_by_dial=0)
    t0 = time.time()
    for sym in SYMS:
        raw = load(sym)
        if raw is None:
            continue
        b_ship = emit(B, sym, raw, cfg_ship)
        a_ship = emit(A, sym, raw, cfg_ship)
        a_ship_on = emit(A, sym, raw, cfg_ship_on)
        b_low = emit(B, sym, raw, cfg_low)
        a_low_on = emit(A, sym, raw, cfg_low_on)

        n = len(b_ship)
        A_mis = (abs(n - len(a_ship)) if n != len(a_ship)
                 else sum(1 for x, y in zip(b_ship, a_ship) if x != y))
        B_mov = sum(1 for x, y in zip(a_ship, a_ship_on) if x[4] != y[4])
        C_mov = sum(1 for x, y in zip(b_ship, b_low) if x[4] != y[4])
        D_mov = sum(1 for x, y in zip(a_ship_on, a_low_on) if x[4] != y[4])

        res["symbols"][sym] = {"n": n, "A_off_vs_parent_mismatch": A_mis,
                               "B_policy_on_moves_at_shipped_dial": B_mov,
                               "C_legacy_exits_moved_by_risk_dial": C_mov,
                               "D_declared_exits_moved_by_risk_dial": D_mov}
        tot["n"] += n
        tot["A_mismatch"] += A_mis
        tot["B_moved"] += B_mov
        tot["C_legacy_moved_by_dial"] += C_mov
        tot["D_policy_moved_by_dial"] += D_mov
        print(f"{sym:12s} n={n:6d}  A={A_mis:5d}  B={B_mov:6d}  C={C_mov:6d}  D={D_mov:5d}"
              f"  ({time.time()-t0:.0f}s)", file=sys.stderr)

    res["totals"] = tot
    res["verdict"] = {
        "A_default_path_byte_identical_to_parent": tot["A_mismatch"] == 0,
        "B_take_profits_that_move_if_the_key_is_set_at_the_shipped_dial": tot["B_moved"],
        "C_exit_contracts_the_LEGACY_resolver_moves_when_the_RISK_dial_moves":
            tot["C_legacy_moved_by_dial"],
        "D_exit_contracts_the_DECLARED_policy_moves_when_the_RISK_dial_moves":
            tot["D_policy_moved_by_dial"],
        "reading": (
            "C is the defect, stated as a count on the whole population: that many take-profits "
            "changed because someone moved a RISK dial. D is the same population under the "
            "declared policy. B is zero at the shipped dial because every declared target (1.5) "
            "is floored up to min_rr (2.0) -- the floor doing exactly its documented job."
        ),
    }
    out = HERE / "P2_INERTNESS_V2.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res["verdict"], indent=1))
    print("WROTE", out)


if __name__ == "__main__":
    main()
