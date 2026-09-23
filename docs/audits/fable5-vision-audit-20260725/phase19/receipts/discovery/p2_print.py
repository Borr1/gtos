import json
import sys

S = json.load(open(sys.argv[1]))
I = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}


def r(x, n=5):
    return None if x is None else round(float(x), n)


def line(*a):
    print(" | ".join(str(x) for x in a))


print("=" * 78)
print("COVERAGE")
for w, v in S["windows"].items():
    print(w, json.dumps(v["coverage"]))

for key in ("H1_signal_is_zero", "H2_structural_distance_extreme", "H3_exit_swap",
            "H4_fill_contract_repair", "H6_direction_vs_mirror"):
    print("=" * 78)
    print(key, "  SEALED VERDICT:", S[key].get("VERDICT"))
    s, i = S[key], I.get(key, {})
    flat = {k: v for k, v in s.items() if not isinstance(v, (dict, list))}
    print(" sealed:", {k: r(v) if isinstance(v, (int, float)) else v
                       for k, v in flat.items()})
    if i:
        fi = {k: v for k, v in i.items() if not isinstance(v, (dict, list))}
        print(" insamp:", {k: r(v) if isinstance(v, (int, float)) else v
                           for k, v in fi.items()})
    for sub in ("bootstrap", "bootstrap_gross", "bootstrap_net"):
        if sub in s:
            b = s[sub]
            print(f" {sub}: mean {r(b['mean'])} CI95 [{r(b['ci_lo'])},{r(b['ci_hi'])}]"
                  f" p<=0 {b.get('p_le_0')} n {b['n']} blocks {b['n_blocks']}")
    for sub in ("per_window", "per_window_gross", "per_window_net", "per_window_n"):
        if sub in s:
            print(f" {sub}: ", {k: r(v) for k, v in s[sub].items()})
            if sub in i:
                print(f"   insample {sub}: ", {k: r(v) for k, v in i[sub].items()})
    if key == "H1_signal_is_zero":
        for sub in ("secondary_f1_contract_clean", "secondary_whole_roster_corrected",
                    "secondary_per_emission_corrected_clean"):
            print(f" {sub}:", {k: r(v) for k, v in s[sub].items()
                               if isinstance(v, (int, float))})
    if key == "H2_structural_distance_extreme":
        print(" ALL FAMILIES (sealed):")
        for f, e in s["all_families"].items():
            print("   %-36s n %7d gross %+8.5f cost %7.5f net %+8.5f wr %.4f  pw %s"
                  % (f, e["n_fills"], e["gross"], e["cost"], e["net"], e["win_rate"],
                     {k: r(v, 4) for k, v in e["per_window_gross"].items()}))
        if i.get("all_families"):
            print(" ALL FAMILIES (in-sample 4 open windows):")
            for f, e in i["all_families"].items():
                print("   %-36s n %7d gross %+8.5f net %+8.5f"
                      % (f, e["n_fills"], e["gross"], e["net"]))
    if key == "H4_fill_contract_repair":
        v = s["variant_b_vs_d5_one_sided_estate_baseline"]
        print(" H4-b:", {k: r(x) if isinstance(x, (int, float)) else x
                         for k, x in v.items() if not isinstance(x, dict)})
        b = v["bootstrap"]
        print("   boot mean %s CI95 [%s,%s]" % (r(b["mean"]), r(b["ci_lo"]), r(b["ci_hi"])))
        print("   per_window", {k: r(x) for k, x in v["per_window"].items()})
        if i:
            iv = i["variant_b_vs_d5_one_sided_estate_baseline"]
            print("   insample delta", r(iv["delta_net"]), "windows+", iv["windows_positive"])

h5 = S.get("H5_forming_bar_candidate") or {}
if h5:
    print("=" * 78)
    print("H5  SEALED")
    a = h5["a_paired"]
    print(" H5a", a["VERDICT"], {k: r(v) for k, v in a.items()
                                 if isinstance(v, (int, float))})
    print("  boot", {k: r(v) for k, v in a["bootstrap"].items()})
    print("  per_window", {k: r(v) for k, v in a["per_window"].items()})
    b = h5["b_implementable"]
    print(" H5b CANDIDATE:", b["CANDIDATE"], "windows partial>close:",
          b["windows_partial_beats_close"])
    for k in ("close_book", "partial_book", "phantom_leg"):
        print("  ", k, {kk: r(vv) for kk, vv in b[k].items()
                        if isinstance(vv, (int, float))})
    print("  per_window", json.dumps(b["per_window"], default=lambda x: round(x, 5)))
    if I.get("H5_forming_bar_candidate"):
        ia = I["H5_forming_bar_candidate"]
        print(" INSAMPLE H5a", r(ia["a_paired"]["delta_net"]),
              ia["a_paired"]["VERDICT"], "| H5b",
              ia["b_implementable"]["CANDIDATE"],
              r(ia["b_implementable"]["partial_book"]["net"]),
              "vs close", r(ia["b_implementable"]["close_book"]["net"]))
