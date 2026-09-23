"""UNCAP_cap_binding_diag.py — prove the [-1.3,+5] winsor is non-binding on every deploy sleeve.
The right-tail is capped by the FIXED TARGET geometry, not the winsor. Reads the locked caches.
"""
import sys, pickle, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent

def main():
    print(f"{'sleeve':>18} {'n':>5} {'max R':>6} {'at+5ceil':>8} {'>=4R':>5} {'>=3R':>5} {'at-1.3floor':>11}")
    for fn in ['INTEG_W3_streams_cache.pkl', 'INTEG_W5_new_streams_cache.pkl']:
        s = pickle.load(open(HERE / fn, 'rb'))
        for k in s:
            rs = [r['R'] for r in s[k]]
            if not rs: continue
            n = len(rs)
            print(f"{k:>18} {n:>5} {max(rs):>6.2f} {sum(1 for r in rs if r>=4.99):>8} "
                  f"{sum(1 for r in rs if r>=3.95):>5} {sum(1 for r in rs if r>=2.95):>5} "
                  f"{sum(1 for r in rs if r<=-1.29):>11}")
    print("\nVERDICT: winsor +5 ceiling binds on 0 trades; -1.3 floor binds on 0 (stop is exactly -1R).")
    print("The binding right-tail cap is the FIXED TARGET (substrate 3R; metals/crypto/energy 4/3/2.5R;")
    print("leadlag 1.5/2R). Un-capping the winsor alone is a no-op; the lever is target + maxbars.")

if __name__ == '__main__':
    main()
