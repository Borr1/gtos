#!/usr/bin/env python3
"""l8_ladder_build — per-candidate first-touch bar index for a dense target/stop ladder.

Emits l8_LADDER.jsonl.gz: {cid, dt, fill_bar, tfav[], tadv[], r_end, n_bars}
tfav[j] = 1-based bar at which +TGT[j] R was first touched AT OR AFTER the entry fill
          (-1 = never). tadv[k] = same for stop level STP[k].
r_end   = close-R of the last bar (mark at the 2h wall), only meaningful if filled.
Requiring the fill is the honest contract (w0_RESULT.md W0-F2).
"""
import gzip, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws

TGT = [0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0]
STP = [-0.25, -0.4, -0.5, -0.75, -1.0, -1.25, -1.5, -2.0]
OUT = os.path.join(HERE, "l8_LADDER.jsonl.gz")


def main():
    n = 0
    with gzip.open(OUT, "wt") as out:
        for rp in w0_ws.iter_rpaths():
            fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
            nb = len(fav)
            start = None
            for i in range(nb):
                if adv[i] <= 1e-12:
                    start = i
                    break
            tf = [-1] * len(TGT)
            ta = [-1] * len(STP)
            if start is not None:
                jf = 0
                ja = 0
                for i in range(start, nb):
                    f = fav[i]
                    a = adv[i]
                    while jf < len(TGT) and f >= TGT[jf] - 1e-12:
                        tf[jf] = i + 1
                        jf += 1
                    while ja < len(STP) and a <= STP[ja] + 1e-12:
                        ta[ja] = i + 1
                        ja += 1
                    if jf >= len(TGT) and ja >= len(STP):
                        break
            out.write(json.dumps({
                "cid": rp["candidate_id"], "dt": rp["decision_time_utc"],
                "fill_bar": (start + 1) if start is not None else -1,
                "tfav": tf, "tadv": ta,
                "r_end": round(cls[nb - 1], 6), "n_bars": nb,
            }, separators=(",", ":")) + "\n")
            n += 1
    print("wrote", n, "->", OUT)
    print("TGT", TGT)
    print("STP", STP)


if __name__ == "__main__":
    main()
