"""Unit tests for substrate.py — lock in the leak-free guarantee + map contract.
Run: python3 -m pytest test_substrate.py -q   (or just python3 test_substrate.py)
"""
import sys, math, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import substrate as sub
from geometry_lib import Bar


# --------------------------------------------------------------------------- #
# LEAK-FREE: the state at bar i must be identical whether or not FUTURE bars
# exist. This is the single most important invariant of the whole substrate.
# --------------------------------------------------------------------------- #
def _synth(n, seed=1):
    random.seed(seed)
    bars = []
    px = 100.0
    for _ in range(n):
        px *= (1 + random.gauss(0, 0.01))
        hi = px * (1 + abs(random.gauss(0, 0.004)))
        lo = px * (1 - abs(random.gauss(0, 0.004)))
        o = lo + (hi - lo) * random.random()
        c = lo + (hi - lo) * random.random()
        bars.append(Bar(o, hi, lo, c, 1.0))
    return bars


def test_state_is_leak_free(monkeypatch=None):
    """States computed on a TRUNCATED series (bars[:i+1]) must equal states
    computed on the FULL series at the same i. If any feature peeked at future
    bars this fails."""
    from datetime import datetime, timedelta
    bars = _synth(900)
    times = [datetime(2020, 1, 1) + timedelta(hours=4 * k) for k in range(len(bars))]

    # patch w1.load to serve our synthetic series
    import wave1_structure_setups_ict as w1
    orig = w1.load
    def fake_load(sym):
        cut = SUB_CUT[0]
        return times[:cut], bars[:cut]
    SUB_CUT = [len(bars)]
    w1.load = fake_load
    # min length build_states accepts (state-window guard incl. MAXBARS buffer)
    minlen = sub.WARMUP + sub.MAXBARS + 6
    try:
        # full series
        _, _, _, full = sub.build_states("FAKE")
        # truncated at i+1 for several test indices; keep truncated length valid
        for i in (minlen - 1, sub.WARMUP + 120, 500, 800):
            SUB_CUT[0] = i + 1
            assert i + 1 >= minlen, "test index below build_states guard"
            res = sub.build_states("FAKE")
            assert res is not None, f"truncated build failed at {i}"
            _, _, _, trunc = res
            st_full = full[i]; st_trunc = trunc[i]
            assert st_full is not None and st_trunc is not None
            for k in st_full:
                a, b = st_full[k], st_trunc[k]
                assert abs(a - b) < 1e-9 if isinstance(a, float) else a == b, \
                    f"LEAK at i={i} feature={k}: full={a} trunc={b}"
    finally:
        w1.load = orig


# --------------------------------------------------------------------------- #
# discretization is total + ordered
# --------------------------------------------------------------------------- #
def test_buckets_total():
    assert sub._bucket_vr(0.5) == "lo" and sub._bucket_vr(2.0) == "xhi"
    assert sub._bucket_slope(5) == "up" and sub._bucket_slope(-5) == "dn" and sub._bucket_slope(0) == "flat"
    assert sub._bucket_persist(0.5) == "trend" and sub._bucket_persist(-0.5) == "revert" and sub._bucket_persist(0) == "rand"
    assert sub._bucket_session(0) == "asia" and sub._bucket_session(10) == "london" and sub._bucket_session(20) == "ny"


def test_cell_coords_all_dims():
    st = {"vr": 1.2, "vol_pct": 0.5, "slope20": 2, "slope50": 2, "slope100": 2,
          "htf": 1, "mtf_align": 1, "rng_pos": 0.9, "compression": 0.5,
          "ac60": 0.2, "dist_hi": 1, "dist_lo": 1, "ma_dist": 0, "hour": 10, "dow": 2}
    co = sub.cell_coords(st)
    assert set(co) == set(sub.CELL_DIMS)
    assert co["persist"] == "trend" and co["comp"] == "coil" and co["session"] == "london"


def test_cell_key_depth_and_stability():
    co = {d: "x" for d in sub.CELL_DIMS}
    k_full = sub.cell_key(co, (1.0, 2.0), +1, sub.CELL_DIMS)
    k_shallow = sub.cell_key(co, (1.0, 2.0), +1, ("vol",))
    assert "depth7" in k_full and "depth1" in k_shallow
    # stable / deterministic
    assert k_full == sub.cell_key(co, (1.0, 2.0), +1, sub.CELL_DIMS)
    # direction & geometry change the key
    assert sub.cell_key(co, (1.0, 2.0), -1, sub.CELL_DIMS) != k_full
    assert sub.cell_key(co, (0.75, 2.0), +1, sub.CELL_DIMS) != k_full


# --------------------------------------------------------------------------- #
# mine() + top_edges() contract on a tiny synthetic record set
# --------------------------------------------------------------------------- #
def test_mine_aggregates_multi_depth():
    co = {d: "a" for d in sub.CELL_DIMS}
    rows = []
    for y in (2022, 2023, 2024, 2025, 2026):
        for _ in range(30):
            rows.append({"sym": "S", "cls": "fx", "year": y, "coords": co,
                         "dir": +1, "gi": 0, "R": 0.3, "hit": True})
    cmap = sub.mine(rows, min_cell_n=10)
    # depth-0 and depth-7 cells must both exist for this geom/dir
    depths = {c["depth"] for c in cmap.values()}
    assert "depth0" in depths and "depth7" in depths
    # the full-depth cell aggregates all 150 rows
    full = [c for c in cmap.values() if c["depth"] == "depth7"]
    assert full and full[0]["n"] == 150
    assert full[0]["train"]["n"] == 90 and full[0]["fwd"]["n"] == 60
    assert abs(full[0]["fwd"]["mean_R"] - 0.3) < 1e-9
    assert abs(full[0]["fwd"]["odds"] - 1.0) < 1e-9


def test_top_edges_requires_forward_hold():
    co = {d: "a" for d in sub.CELL_DIMS}
    # a cell that is +EV in train but NEGATIVE forward must NOT pass
    rows = []
    for y in (2022, 2023, 2024):
        for _ in range(30):
            rows.append({"sym": "S", "cls": "fx", "year": y, "coords": co,
                         "dir": +1, "gi": 0, "R": 0.5, "hit": True})
    for y in (2025, 2026):
        for _ in range(30):
            rows.append({"sym": "S", "cls": "fx", "year": y, "coords": co,
                         "dir": +1, "gi": 0, "R": -0.5, "hit": False})
    cmap = sub.mine(rows, min_cell_n=10)
    edges = sub.top_edges(cmap, min_n_train=40, min_n_fwd=40)
    assert all(e["meanR_fwd"] >= 0.05 for e in edges)
    # train+ / fwd- must be excluded
    assert not any(e["meanR_train"] > 0 and e["meanR_fwd"] < 0 for e in edges)


def test_top_edges_passes_when_both_hold():
    co = {d: "a" for d in sub.CELL_DIMS}
    rows = []
    for y in (2022, 2023, 2024, 2025, 2026):
        for _ in range(30):
            rows.append({"sym": "S", "cls": "fx", "year": y, "coords": co,
                         "dir": +1, "gi": 0, "R": 0.4, "hit": True})
    cmap = sub.mine(rows, min_cell_n=10)
    edges = sub.top_edges(cmap, min_n_train=40, min_n_fwd=40)
    assert len(edges) >= 1
    e = max(edges, key=lambda x: x["n_train"])
    assert e["meanR_train"] >= 0.05 and e["meanR_fwd"] >= 0.05
    assert e["pos_fwd_years"] == e["total_fwd_years"]


def test_query_and_best_cell():
    co = {d: "a" for d in sub.CELL_DIMS}
    rows = []
    for y in (2023, 2024, 2025, 2026):
        for _ in range(30):
            rows.append({"sym": "S", "cls": "fx", "year": y, "coords": co,
                         "dir": +1, "gi": 2, "R": 0.2, "hit": False})
    cmap = sub.mine(rows, min_cell_n=10)
    # a live state with the same coords should resolve to the deepest cell w/ n_fwd
    state = {"vr": 0.5, "vol_pct": 0.5, "slope20": 0, "slope50": 0, "slope100": 0,
             "htf": 0, "mtf_align": 0, "rng_pos": 0.5, "compression": 1.0,
             "ac60": 0.0, "dist_hi": 1, "dist_lo": 1, "ma_dist": 0, "hour": 0, "dow": 0}
    # force coords to 'a' by monkeypatching cell_coords for this assertion
    orig = sub.cell_coords
    sub.cell_coords = lambda st: co
    try:
        dims, c = sub.best_cell(cmap, state, sub.GEOMS[2], +1, min_n_fwd=40)
        assert c is not None and c["fwd"]["n"] >= 40
        # deepest available should be depth-7 (full plan present)
        assert "depth7" in c["depth"]
    finally:
        sub.cell_coords = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} substrate tests passed")
