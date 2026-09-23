"""KB6_stress_lib.py — shared reconstruction of the clean_3 deploy book day x sleeve matrix.

Rebuilds EXACTLY the same M (days x sleeves) matrix that INTEG_w5_clean3_deploy.py builds,
plus per-sleeve daily contributions, so the stress-hardening track (KB6) can test mitigations
on the real deployed book using the LOCKED W2 MC engine (block-bootstrap whole days, BLOCK=5,
N=20000, TARGET 8%/DAILY 5%/MAXDD 10%). Leak-free: every sleeve stream is the cached, already
forward-holdout-validated series; the regime/overlay features below use ONLY days < t.
"""
import sys, collections, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

mc_series = W2.mc_series
TARGET, MAXDD, DAILY, BLOCK, PATHCAP, N = I.TARGET, I.MAXDD, I.DAILY, I.BLOCK, I.PATHCAP, I.N

CLEAN3 = {'sub_xvol_pullback': 0.45, 'vp_euidx_pocgrav': 0.30, 'sub_mid_dn_revert': 0.20}


def candidate_daily(rows):
    by = collections.defaultdict(list)
    for r in rows:
        by[r['date']].append(r['R'])
    return {d: sum(v) / len(v) for d, v in by.items()}


def build_clean3():
    """Returns dict with all_days, sleeves, M (days x sleeves conf-wtd unit-R), comb, fwd_mask,
    vol_scale (book/clean3), book_series, per-day breadth (#nonzero sleeves)."""
    streams_w3 = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl: {} for sl in book_sleeves}
    for di, day in enumerate(days_w3):
        for si, sl in enumerate(book_sleeves):
            daily_sleeve[sl][day] = M_w3[di][si]
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3)
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])

    new_streams = pickle.load(open(HERE / 'INTEG_W5_new_streams_cache.pkl', 'rb'))
    cand = {nm: candidate_daily(new_streams[nm]) for nm in CLEAN3}
    nd = {nm: {d: v * cf for d, v in cand[nm].items()} for nm, cf in CLEAN3.items()}

    sleeves = list(book_sleeves) + list(CLEAN3.keys())
    all_days = sorted(book_days | set().union(*[set(cand[n]) for n in CLEAN3]))
    fwd_mask = [d.year >= 2025 for d in all_days]
    M = []
    for day in all_days:
        M.append([daily_sleeve[sl].get(day, 0.0) for sl in book_sleeves]
                 + [nd[nm].get(day, 0.0) for nm in CLEAN3])
    comb = [sum(r) for r in M]
    sd = statistics.pstdev(comb)
    vs = sd_book / sd if sd > 0 else 1.0
    book_series = [comb_book.get(d, 0.0) for d in all_days]
    # breadth = number of nonzero sleeves firing that day
    breadth = [sum(1 for x in row if x != 0.0) for row in M]
    return dict(all_days=all_days, sleeves=sleeves, M=M, comb=comb, fwd_mask=fwd_mask,
                vol_scale=vs, book_series=book_series, breadth=breadth,
                book_sleeves=book_sleeves, new_sleeves=list(CLEAN3.keys()))


def stress(series):
    return [(v * 1.5 if v < 0 else v) for v in series]


def grid_pass(series, scale=1.0, stressed=False, risks=(0.005, 0.0075, 0.01, 0.015, 0.02), seed_base=None):
    s = stress(series) if stressed else series
    if seed_base is None:
        seed_base = 999 if stressed else 1
    return {f"{r*100:.2f}%": mc_series(s, r * scale, seed_base=seed_base)['p_pass'] for r in risks}
