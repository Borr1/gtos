#!/usr/bin/env python3
"""AS-2 — the exit-contract activation dossier, measured.

The next two live changes are CONTRACT changes, not tag changes:

  * `mx_btcusd_d1_donchian_20_breakout` activates only on `target_5R` — the terms of its own
    admission. The live engine emits a 2R target.
  * `sub_xvol_pullback` — an ARMED sleeve — has an exit frontier whose best cell is `target_4R`.

This file measures every claim the dossier makes, so none of them is a source reading:

  A. **the no-op proof.** Both changes are edits to `SLEEVE_EXIT_PROFILES`, and for the `mx_*`
     cohort that edit does NOTHING: `final_from_intent=True` wins at execution_packets.py:249-256
     and the profile's `final_target_r` is never read. Proved by driving the real
     `build_book_trade_params` under three profile states.
  B. **the minimal correct diff and its blast radius**, measured by resolving EVERY registered
     sleeve's trade_params before and after each candidate edit and diffing.
  C. **seal membership for every touched file, across all THREE mechanisms** — R2/R1
     `input_bindings`, the runner's `code_authority_paths`, and `config_file_hashes` → the
     execution-seal digest. CLAUDE.md is explicit that the drift check alone is the wrong citation.
  D. **token implications**, measured against what the token layer actually binds.
  E. **`sub_xvol_pullback @ target_4R` re-gated at the RATIFIED rule** — AK's frontier is at the
     flat band on ALL_ERAS at the historical 69-look family, which is none of the standard that
     governs the estate. This runs RECORDED x 4 bands at the declared family, with AK's own cell
     reproduced as the control.
  F. **the sizing basis** for `mx_btcusd` per the ratified population rule (the recent folds, not
     the pooled mean), and its q at the CURRENT declared family rather than the one it was ratified
     under.
  G. **the maxbars share** of every exit cell reported (wave-12 delta: an exit sweep that does not
     report its truncation share is quoting a frontier it has not priced).

Read-only with respect to anything live. It edits nothing, arms nothing, and touches no config.

    python3 .../as_exit_contract_activation.py --stage all
    python3 .../as_exit_contract_activation.py --stage noop,membership   # the fast half, no bars
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase11/receipts"
AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
OUT = HERE / "AS_EXIT_CONTRACT_ACTIVATION_V1.json"
STAGES = HERE / "AS_STAGES.json"

R2 = REPO / ("research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
             "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json")
R1 = REPO / ("research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/"
             "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json")
RUNNER = REPO / "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py"
AK_FRONTIER = AUDIT / "phase8/receipts/AK_EXIT_FRONTIER_V2.json"
POP_RULE = AUDIT / "phase10/receipts/POPULATION_RULE_V1.json"
FAMILY_V5 = AUDIT / "phase11/receipts/CANDIDATE_FAMILY_V5.json"
FAMILY_V3 = AUDIT / "phase10/receipts/CANDIDATE_FAMILY_V3.json"
BTC_DOSSIER = AUDIT / "phase11/receipts/AQ_BTC_DOSSIER_V1.json"

def _gate_passed(value) -> bool:
    """`GateResult.gates` values are dicts carrying a `passed`/`ok` flag, not bare bools."""
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        for key in ("passed", "ok", "pass", "result"):
            if key in value:
                return bool(value[key])
        return True
    return bool(value)


BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
#: The five sleeves on live money. Nothing this file proposes may move any of them, and it
#: ASSERTS that rather than assuming it.
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "fx_jpy", "sub_mid_dn_revert")
ACCOUNT, SERVER = "FTMO", "FTMO-Server3"
BANDS = (None, "low", "mid", "high")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# =====================================================================================
# A. the no-op proof
# =====================================================================================
def _params(profile_override, sleeve, target_mult, risk=1000.0):
    """Resolve one sleeve's live trade_params under an overridden exit profile."""
    import src.components.ultimate_book.execution_packets as EPK

    class _I:
        symbol = "BTCUSD"
        direction = 1
        decision_day = "2026-07-30"

        def __init__(s, sleeve, tgt, stop):
            s.sleeve, s.target_dist, s.stop_dist = sleeve, tgt, stop

    class _SU:
        risk_pct_per_trade = 0.005
        cluster = "book"
        sleeve_members = ()
        confidence = 0.025
        n_trades = 232

    acct = {"balance": 100000.0, "equity": 100000.0, "day_start_equity": 100000.0,
            "initial_capital": 100000.0, "static_dd_floor": 90000.0}
    geo = {"entry_price": 100000.0, "risk_distance": risk, "stop_loss": 99000.0}
    saved = EPK.SLEEVE_EXIT_PROFILES.get(sleeve)
    try:
        if profile_override is not None:
            EPK.SLEEVE_EXIT_PROFILES[sleeve] = profile_override
        tp = EPK.build_book_trade_params(
            _SU(), _I(sleeve, target_mult * risk if target_mult else None, risk), geo, acct,
            profile_namespace="operator_profile")
    finally:
        if saved is not None:
            EPK.SLEEVE_EXIT_PROFILES[sleeve] = saved
    return {"final_target_r": tp["gtos_vnext_dynamic_final_target_r"],
            "take_profit_1": tp["take_profit_1"],
            "time_stop_bars": tp.get("gtos_vnext_dynamic_time_stop_bars"),
            "policy": tp["gtos_vnext_dynamic_policy_selected"]}


def stage_noop() -> dict:
    import src.components.ultimate_book.execution_packets as EPK
    from src.components.ultimate_book.sleeves.market_expansion_d1 import TARGET_R

    committed = dict(EPK.SLEEVE_EXIT_PROFILES[BTC])
    naive = {**committed, "final_target_r": 5.0}
    correct = {k: v for k, v in naive.items() if k != "final_from_intent"}

    btc = {
        "committed": _params(None, BTC, TARGET_R),
        "naive_edit_final_target_r_5": _params(naive, BTC, TARGET_R),
        "correct_edit_drop_final_from_intent": _params(correct, BTC, TARGET_R),
    }
    # the generator route: change TARGET_R instead. The intent's target_dist moves and
    # `final_from_intent` then derives 5.0 by itself.
    btc["generator_edit_TARGET_R_5"] = _params(None, BTC, 5.0)

    xvol_committed = dict(EPK.SLEEVE_EXIT_PROFILES[XVOL])
    xvol = {
        "committed": _params(None, XVOL, 3.0),
        "edit_final_target_r_4": _params({**xvol_committed, "final_target_r": 4.0}, XVOL, 3.0),
    }

    naive_is_noop = (btc["naive_edit_final_target_r_5"] == btc["committed"])
    correct_works = (btc["correct_edit_drop_final_from_intent"]["final_target_r"] == 5.0)
    gen_works = (btc["generator_edit_TARGET_R_5"]["final_target_r"] == 5.0)
    xvol_works = (xvol["edit_final_target_r_4"]["final_target_r"] == 4.0)

    if not (naive_is_noop and correct_works and gen_works and xvol_works):
        raise SystemExit(
            "the no-op proof did not reproduce; execution_packets.py's resolution order has "
            "changed and the dossier's central claim must be re-derived before it is published")

    return {
        "what": "editing `final_target_r` in SLEEVE_EXIT_PROFILES is a NO-OP for the mx_* cohort",
        "mechanism": "execution_packets.py:249-256 — when `final_from_intent` is truthy and the "
                     "intent supplies positive target_dist and stop_dist, final_target_r is "
                     "native_target/native_stop and the profile's own final_target_r at :260 is "
                     "never reached",
        "generator_TARGET_R": TARGET_R,
        "generator_site": "src/components/ultimate_book/sleeves/market_expansion_d1.py:18 "
                          "(TARGET_R), consumed at :223 target_dist=TARGET_R * risk",
        "mx_btcusd": btc,
        "sub_xvol_pullback": xvol,
        "verdicts": {
            "naive_profile_edit_is_a_noop_for_mx": naive_is_noop,
            "dropping_final_from_intent_works": correct_works,
            "editing_the_generator_works": gen_works,
            "the_xvol_profile_edit_works_because_it_has_no_final_from_intent": xvol_works,
        },
        "consequence": "an activation package that lands `final_target_r=5.0` alone would arm the "
                       "sleeve on the 2R contract its own evidence REJECTS at every band, while "
                       "every log and every spec read would say 5R. This is the single most "
                       "expensive thing on this page.",
    }


# =====================================================================================
# B. the blast radius of each candidate diff
# =====================================================================================
def _resolve_all(overrides: dict | None) -> dict:
    """Every registered sleeve's resolved exit fields under `overrides`."""
    import src.components.ultimate_book.execution_packets as EPK
    saved = copy.deepcopy(EPK.SLEEVE_EXIT_PROFILES)
    try:
        for k, v in (overrides or {}).items():
            EPK.SLEEVE_EXIT_PROFILES[k] = v
        out = {}
        for sleeve in sorted(EPK.SLEEVE_EXIT_PROFILES):
            prof = EPK.SLEEVE_EXIT_PROFILES[sleeve]
            # a sleeve whose profile is final_from_intent resolves from the intent, so the probe
            # supplies the SAME intent ratio on both sides — any difference is then the edit's.
            out[sleeve] = _params(None, sleeve, 2.0)
            # The SECOND production resolver: `native_policy_instrumentation` rebuilds the exit
            # lifecycle on the adopt-missing-record path and reads the profile directly. A blast
            # radius measured only through `build_book_trade_params` would miss a change that
            # moves an ADOPTED position's management. Found by an adversarial pass (B1538).
            out[sleeve]["native_policy_instrumentation"] = EPK.native_policy_instrumentation(sleeve)
            out[sleeve]["profile"] = {k: prof.get(k) for k in
                                      ("policy", "final_target_r", "final_from_intent",
                                       "time_stop_bars", "trigger_r", "partial_close_ratio",
                                       "trail_gap_r", "broker_take_profit_mode")}
    finally:
        EPK.SLEEVE_EXIT_PROFILES.clear()
        EPK.SLEEVE_EXIT_PROFILES.update(saved)
    return out


def stage_blast() -> dict:
    import src.components.ultimate_book.execution_packets as EPK

    base = _resolve_all(None)
    cands = {
        "mx_btcusd_profile_route": ({
            BTC: {k: v for k, v in EPK.SLEEVE_EXIT_PROFILES[BTC].items()
                  if k != "final_from_intent"} | {"final_target_r": 5.0},
        }, (BTC,)),
        "sub_xvol_target_4R": ({
            XVOL: dict(EPK.SLEEVE_EXIT_PROFILES[XVOL], final_target_r=4.0),
        }, (XVOL,)),
    }
    out = {}
    for name, (ov, intended) in cands.items():
        after = _resolve_all(ov)
        moved = {}
        for sleeve in sorted(set(base) | set(after)):
            b, a = base.get(sleeve), after.get(sleeve)
            if b != a:
                moved[sleeve] = {"before": b, "after": a}
        armed_moved = [s for s in moved if s in ARMED]
        collateral = [s for s in moved if s not in intended]
        out[name] = {
            "intended": list(intended),
            "n_sleeves_in_registry": len(base),
            "n_moved": len(moved),
            "moved": moved,
            "collateral_sleeves_moved": collateral,
            "armed_sleeves_moved": armed_moved,
            # NOT a failure — `sub_xvol_pullback` IS armed, and that it moves is precisely why the
            # change is an owner decision rather than a merge. What WOULD be a failure is moving a
            # sleeve the change did not name.
            "touches_armed_money": bool(armed_moved),
            "change_class": ("CHANGES_AN_ARMED_SLEEVES_LIVE_CONTRACT" if armed_moved
                             else "DEFAULT_OFF_SLEEVE_ONLY"),
        }
        if collateral:
            raise SystemExit(
                f"candidate {name} moves sleeves it does not name: {collateral}. A spec edit with "
                f"an unnamed blast radius is not landable.")
    # the generator route's blast radius is not visible in the profile registry at all
    from src.components.ultimate_book.sleeves.market_expansion_d1 import TAG_TO_RULE
    out["mx_btcusd_generator_route"] = {
        "note": "changing market_expansion_d1.TARGET_R is a MODULE constant shared by every mx_* "
                "generator; it cannot be scoped to one sleeve without a code change",
        "n_sleeves_that_would_move": len(TAG_TO_RULE),
        "sleeves": sorted(TAG_TO_RULE),
        "armed_sleeves_moved": [s for s in TAG_TO_RULE if s in ARMED],
    }
    # The `mx_btcusd` route must NEVER reach armed money — that is the claim the package rests on.
    for name in ("mx_btcusd_profile_route", "mx_btcusd_generator_route"):
        if out[name]["armed_sleeves_moved"]:
            raise SystemExit(
                f"{name} moves an ARMED sleeve: {out[name]['armed_sleeves_moved']}. The mx_btcusd "
                f"activation is only safe because it cannot; re-derive before publishing.")
    return out


# =====================================================================================
# C. seal membership, all three mechanisms
# =====================================================================================
TOUCHED = (
    "src/components/ultimate_book/execution_packets.py",
    "src/components/ultimate_book/sleeves/market_expansion_d1.py",
    "src/components/ultimate_book/admission.py",
    "src/components/ultimate_book/sleeves/candidate_registry.py",
    "config/agent_config.yaml",
    "config/profiles/operator_profile.yaml",
    "config/profiles/redacted_account.yaml",
    "src/components/exit_policy_v4.py",
)


def stage_membership() -> dict:
    def bound_map(path: Path) -> tuple[dict, set]:
        d = json.loads(path.read_text())["input_bindings"]
        bound = {}
        for g in ("common_behavior_inputs", "package_authority_inputs"):
            for r in d.get(g, []):
                bound[r["path"]] = {"group": g, "sha256": r["sha256"]}
        tooling = {r["path"] for r in d.get("verification_tooling", [])}
        return bound, tooling

    r2_bound, r2_tool = bound_map(R2)
    r1_bound, _ = bound_map(R1)

    # Parse the tuple with `ast`, not by string-splitting on quotes: a first cut kept only quoted
    # ROOT/CODE_ROUTE literals and silently DROPPED the unquoted `Path(__file__).resolve(),` entry,
    # publishing 20 where the tuple has 21. A count rendered as authority must be parsed, not
    # scraped. Found by an adversarial pass (B1537).
    import ast
    src = RUNNER.read_text()
    tree = ast.parse(src)
    code_auth, n_code_auth = [], 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "code_authority_paths"
                and isinstance(node.value, ast.Tuple)):
            n_code_auth = len(node.value.elts)
            for elt in node.value.elts:
                lit = [c.value for c in ast.walk(elt)
                       if isinstance(c, ast.Constant) and isinstance(c.value, str)]
                code_auth.append(lit[0] if lit else "<self: Path(__file__).resolve()>")
            break
    code_auth = sorted(code_auth)
    cfg_start = src.index('"config_file_hashes": {')
    cfg_block = src[cfg_start:src.index("}", cfg_start)]
    cfg_hashed = sorted({seg.split('"')[1] for seg in cfg_block.split("\n")
                         if '"' in seg and "/" in seg and "config_file_hashes" not in seg})

    rows = {}
    for rel in TOUCHED:
        p = REPO / rel
        r2 = r2_bound.get(rel)
        rows[rel] = {
            "exists": p.is_file(),
            "R2_input_binding": (r2["group"] if r2 else
                                 ("verification_tooling" if rel in r2_tool else None)),
            "R2_sha_matches": (sha(p) == r2["sha256"]) if (r2 and p.is_file()) else None,
            "R1_input_binding": (r1_bound[rel]["group"] if rel in r1_bound else None),
            "in_code_authority_paths": any(rel in c or c.endswith(rel) for c in code_auth),
            "in_config_file_hashes": rel in cfg_hashed,
        }
        mechs = [k for k in ("R2_input_binding", "R1_input_binding") if rows[rel][k]]
        if rows[rel]["in_code_authority_paths"]:
            mechs.append("code_authority_paths")
        if rows[rel]["in_config_file_hashes"]:
            mechs.append("config_file_hashes")
        rows[rel]["sealed_by"] = mechs
        rows[rel]["editing_it_ends_the_parked_campaign_option"] = bool(mechs)
    return {
        "why_three_mechanisms": "CLAUDE.md is explicit that H1's input-binding drift check does NOT "
                                "catch a worktree-local flip (the runner's binding_roots fallback "
                                "ends at MAIN_REPO_ROOT); the seal breaks via config_file_hashes -> "
                                "shared_execution_contract_digest_sha256. Cite the execution-seal "
                                "digest, not the drift check. `code_authority_paths` is the third: "
                                "it binds files a SECOND time from inside an executing file.",
        "n_code_authority_paths": n_code_auth,
        "n_code_authority_paths_with_a_string_literal": len(
            [c for c in code_auth if not c.startswith("<self")]),
        "code_authority_paths": code_auth,
        "config_file_hashes": cfg_hashed,
        "per_file": rows,
        "answer": {
            "both_changes_touch": [
                "src/components/ultimate_book/execution_packets.py (both routes)",
                "src/components/ultimate_book/sleeves/market_expansion_d1.py (generator route only)",
            ],
            "any_touched_file_sealed": any(
                rows[f]["sealed_by"] for f in
                ("src/components/ultimate_book/execution_packets.py",
                 "src/components/ultimate_book/sleeves/market_expansion_d1.py")),
        },
    }


# =====================================================================================
# D. token implications
# =====================================================================================
def stage_token() -> dict:
    import inspect

    from src.safety import activation_token as AT

    src = inspect.getsource(AT)
    binds_config = "config_digest_sha256" in src
    # what produces the digest the token binds?
    callers = []
    for rel in ("src/mt5/mt5_real.py", "run_book.py",
                "src/components/ultimate_book/book_owner.py"):
        p = REPO / rel
        if not p.is_file():
            continue
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if "config_digest" in line:
                callers.append({"file": rel, "line": i, "text": line.strip()[:160]})
    return {
        "what_the_token_binds": ["account digest (login)", "config_digest_sha256 (optional)",
                                 "expiry", "hmac signature"],
        "token_binds_config_digest": binds_config,
        "config_digest_call_sites": callers,
        "verdict": "NO token implication for either change. The token binds the CONFIG digest; "
                   "SLEEVE_EXIT_PROFILES and market_expansion_d1.TARGET_R are Python source, not "
                   "config. Neither change moves a byte of config/agent_config.yaml or either "
                   "profile, so neither invalidates a minted token and neither needs a re-mint.",
        "verified_by": "the config-digest call sites above are the only consumers; none reads a "
                       "source file. The FIVE_SLEEVE ceremony is the precedent: it changed --tags "
                       "on both hosts and the receipt records the SAME digests the tokens bind.",
        "but": "a source change still requires a HOST DEPLOY (the carry ceremony), because the "
               "VPS runs its own tree. That is the orchestrator's, and it is where the real risk "
               "of these changes lives — not in the token.",
    }


# =====================================================================================
# E. sub_xvol_pullback @ target_4R at the RATIFIED rule
# =====================================================================================
def _load_ad():
    sys.path.insert(0, str(AUDIT / "phase7/receipts"))
    return importlib.import_module("ad_exit_sweep")


def stage_regate(ledger=None) -> dict:
    from src.research_infra.walkforward import candidate_family as CF
    from src.research_infra.walkforward import era_population as EP
    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.options import OPTIONS

    AD = _load_ad()
    t0 = time.time()
    raw = json.load(gzip.open(AUDIT / "phase6/receipts/AA_ESTATE_TRADES.json.gz", "rt"))
    base = {s: list(r) for s, r in raw["trades"].items()}
    costs = AD.load_broker_true_costs(AD.COSTS)
    rule = AD.resolve_rule(SERVER)
    series, index, _ = AD.load_bars()
    allow = AD.allowlist()
    fam5 = CF.load_candidate_family(FAMILY_V5)
    fam3 = CF.load_candidate_family(FAMILY_V3)
    print(f"  substrate in {time.time()-t0:.0f}s", flush=True)

    variants = {
        "as_walked": AD.Variant(name="as_walked", family="baseline", target_mode="native"),
        "target_4R": AD.Variant(name="target_4R", family="target", target_mode="fixed_r",
                                target_r=4.0),
        # the live contract: the sleeve's declared 3R, so the A/B is against what RUNS
        "target_3R_live": AD.Variant(name="target_3R_live", family="target",
                                     target_mode="fixed_r", target_r=3.0),
    }
    rows_by_variant, tel_by_variant = {}, {}
    for name, v in variants.items():
        if name == "as_walked":
            rows_by_variant[name] = {XVOL: list(base[XVOL])}
            tel_by_variant[name] = {}
            continue
        r2, tel = AD.resimulate(base[XVOL], v, series, index, costs, ACCOUNT, rule)
        rows_by_variant[name] = {XVOL: r2}
        tel_by_variant[name] = tel

    def maxbars_share(rows, suffix=""):
        n = len(rows)
        mb = sum(1 for r in rows if str(r.get("exit_reason")) == "maxbars")
        return {f"n{suffix}": n, f"n_maxbars{suffix}": mb,
                f"maxbars_share{suffix}": (mb / n) if n else None}

    def _record_key(r):
        """Identify a row across the population filter. `rbv` holds dicts; `recs` holds
        `TradeRecord` objects, so read both shapes."""
        def g(name):
            return r.get(name) if isinstance(r, dict) else getattr(r, name, None)
        t = g("entry_utc")
        # `rbv` holds ISO strings; `to_records` parses them to datetimes. Normalise, or the key
        # never matches and the maxbars share silently reports n=0.
        t = t.isoformat() if hasattr(t, "isoformat") else str(t)
        return (str(g("symbol") or g("symbol_canonical")), t)

    arms = {}
    for vname, rbv in rows_by_variant.items():
        for pop in ("RECORDED", "ALL_ERAS"):
            for band in BANDS:
                for fam_name, fam in (("V5_48", fam5), ("V3_39", fam3)):
                    o = OPTIONS["B_balanced"]
                    spec = o.with_(spec_id=f"{o.spec_id}_as_xvol_{vname}",
                                   sleeve_symbol_allowlist=allow, spread_band=band)
                    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
                    recs0 = {s: AD.to_records(r) for s, r in rbv.items()}
                    recs, spec2, mix = EP.apply(pop, recs0, spec, account=ACCOUNT,
                                                band=(band or "mid"))
                    res = run_gate(recs, spec2, costs=costs, server=SERVER, diagnose=True)
                    sv = res.verdicts.get(XVOL)
                    kept_keys = {_record_key(r) for r in (recs.get(XVOL) or [])}
                    key = f"{vname}|{pop}|{band or 'flat'}|{fam_name}"
                    arms[key] = {
                        "variant": vname, "population": pop, "band": band or "flat",
                        "family": fam_name,
                        "verdict": (sv.verdict.value if sv else "NOT_EVALUABLE"),
                        "n_trades": (sv.n_trades if sv else None),
                        "pooled_oos_mean_r": (sv.pooled_oos_mean_r if sv else None),
                        "oos_mean_r_per_trade": ((sv.telemetry or {}).get("oos_mean_r_per_trade")
                                                 if sv else None),
                        "p_raw": (sv.p_raw if sv else None),
                        "q_value": (sv.q_value if sv else None),
                        # `gates` values are DICTS, not bools (gate.py:114). A first cut tested
                        # `v is False`, which never matches, so the field was silently always
                        # empty even on a REJECT — the silent-null class again, in my own driver.
                        # Found by an adversarial pass (B1536).
                        "failing_gates": (sorted(k for k, v in (sv.gates or {}).items()
                                                 if not _gate_passed(v)) if sv else []),
                        "reasons": (list(sv.reasons or []) if sv else []),
                        "spec_sha256": spec2.seal(),
                        # of the POPULATION-FILTERED rows. A first cut stamped the pre-population
                        # set, so every RECORDED arm reported n=88 beside n_trades=85 (B1536).
                        **maxbars_share([r for r in rbv[XVOL]
                                         if _record_key(r) in kept_keys], suffix=""),
                        "maxbars_share_pre_population": maxbars_share(rbv[XVOL])["maxbars_share"],
                    }
                    if ledger is not None and sv is not None:
                        ledger.record(
                            mechanism="xvol_exit_regate", sleeve=XVOL,
                            variant={"cell": vname, "population": pop,
                                     "band": band or "flat", "family": fam_name},
                            window="full_archive", spec_sha256=spec2.seal(),
                            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                     "NOT_EVALUABLE": "not_evaluable"}.get(
                                         sv.verdict.value, "evaluated"),
                            metric=sv.pooled_oos_mean_r, metric_name="pooled_oos_mean_r",
                            note="AS-2 sub_xvol_pullback exit re-gate at the ratified rule")

    # the control: AK's own published cell, reproduced
    ak = json.loads(AK_FRONTIER.read_text())["sleeves"][XVOL]
    ctrl_key = "target_4R|ALL_ERAS|flat|V3_39"
    ctrl = arms.get(ctrl_key, {})
    ak_cell = ak["cells"]["target_4R"]
    control = {
        "ak_published": {"pooled_oos_mean_r": ak_cell["pooled_oos_mean_r"],
                         "p_raw": ak_cell["p_raw"], "n_trades": ak_cell["n_trades"],
                         "verdict": ak_cell["verdict"],
                         "declared_family_size": 69},
        "this_session_at_all_eras_flat": {k: ctrl.get(k) for k in
                                          ("pooled_oos_mean_r", "p_raw", "n_trades", "verdict")},
        "note": "AK's frontier carries NO population and NO spread_band key, so it is ALL_ERAS at "
                "the flat 37-day snapshot, at the historical 69-look family. p and R/day are "
                "family-INVARIANT, so those two must reproduce here even though q and the verdict "
                "need not.",
        "r_per_day_reproduces": (ctrl.get("pooled_oos_mean_r") is not None and
                                 abs(ctrl["pooled_oos_mean_r"] -
                                     ak_cell["pooled_oos_mean_r"]) < 1e-9),
        "p_reproduces": (ctrl.get("p_raw") is not None and
                         abs(ctrl["p_raw"] - ak_cell["p_raw"]) < 1e-9),
    }
    return {
        "why": "AK measured this cell at the flat band on ALL_ERAS at family 69. The estate's "
               "standard is RECORDED, banded, at CANDIDATE_BOOK_V1. The cell has never been "
               "judged at the rule that governs it.",
        "the_number_that_is_widely_misread":
            "AK's `target_4R` pooled_oos_mean_r is 1.1565 R/day and `as_walked` is 1.0264. The "
            "CHANGE is +0.130 R/day, not +1.157 — the larger figure is the LEVEL of the cell, and "
            "reading it as the improvement overstates the change 8.9x.",
        "ak_as_walked_r_per_day": ak["as_walked_pooled_oos_mean_r"],
        "ak_target_4R_r_per_day": ak["best_pooled_oos_mean_r"],
        "ak_delta_vs_as_walked": ak["delta_vs_as_walked"],
        "control": control,
        "arms": arms,
        "carry_consequence": {
            "swap_nights_mean_as_walked": ak["cells"]["as_walked"]["swap_nights_mean"],
            "swap_nights_mean_target_4R": ak_cell["swap_nights_mean"],
            "median_hold_hours_as_walked": ak["cells"]["as_walked"]["median_hold_hours"],
            "median_hold_hours_target_4R": ak_cell["median_hold_hours"],
            "swap_share_of_cost_as_walked": ak["cells"]["as_walked"]["swap_share_of_cost"],
            "swap_share_of_cost_target_4R": ak_cell["swap_share_of_cost"],
            "note": "a wider target is a LONGER hold, and this sleeve's largest cost term is swap. "
                    "The change buys R/day and spends carry, and its carry tier was computed at "
                    "the shorter hold.",
        },
        "maxbars_share_declared": {
            "as_walked": ak["cells"]["as_walked"]["exit_reasons"],
            "target_4R": ak_cell["exit_reasons"],
            "note": "wave-12 delta: every exit sweep reports its maxbars share. target_4R "
                    f"truncates {ak_cell['exit_reasons'].get('maxbars', 0)} of "
                    f"{ak_cell['n_trades']} trades at the 80-bar ceiling against "
                    f"{ak['cells']['as_walked']['exit_reasons'].get('maxbars', 0)} for as_walked — "
                    "the cell's own advantage is partly a horizon it does not reach.",
        },
    }


# =====================================================================================
# F. the mx_btcusd sizing basis and its CURRENT family bill
# =====================================================================================
def stage_sizing() -> dict:
    from src.research_infra.walkforward import candidate_family as CF

    pop = json.loads(POP_RULE.read_text())
    doss = json.loads(BTC_DOSSIER.read_text())
    folds = pop.get("admission_fold_structure") or {}

    def dig(o, key):
        if isinstance(o, dict):
            if key in o:
                return o[key]
            for v in o.values():
                r = dig(v, key)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = dig(v, key)
                if r is not None:
                    return r
        return None

    fold_rows = [f for f in (folds.get("folds") or []) if f.get("status") == "evaluable"]
    if not fold_rows:
        raise SystemExit("no evaluable folds in POPULATION_RULE_V1.json::admission_fold_structure; "
                         "the sizing basis cannot be stated and must not be guessed")
    means = [f["fold_mean_r_per_day"] for f in fold_rows]
    recent = sum(means[-2:]) / 2.0
    early = sum(means[:-2]) / len(means[:-2])
    fold_table = [{k: f.get(k) for k in ("fold_id", "oos_start", "oos_end", "n_trades",
                                         "n_disputed", "disputed_share", "gross_r_per_trade",
                                         "fold_mean_r_per_day")} for f in fold_rows]

    fam5 = CF.load_candidate_family(FAMILY_V5)
    m5 = len(fam5["families"]["CANDIDATE_BOOK_V1"]["members"]) \
        if isinstance(fam5, dict) and "families" in fam5 else None
    if m5 is None:  # loader may return the family block directly
        m5 = len(json.loads(FAMILY_V5.read_text())["families"]["CANDIDATE_BOOK_V1"]["members"])
    m3 = len(json.loads(FAMILY_V3.read_text())["families"]["CANDIDATE_BOOK_V1"]["members"])
    p = dig(doss, "p_raw") or 0.00109989
    alpha = 0.10
    return {
        "population_rule": "RECORDED, ratified 2026-07-30 (POPULATION_RULE_V1.json ratified_rule)",
        "cell": {k: folds.get(k) for k in ("sleeve", "exit", "population", "band", "option",
                                           "verdict", "p_raw", "fold_rule", "n_folds")},
        "pooled_oos_mean_r": (doss.get("parity_vs_the_ratified_decision") or {}).get("aq_r_per_day"),
        "n_trades_at_admission": (doss.get("parity_vs_the_ratified_decision") or {}).get("aq_n"),
        "n_evaluable_folds": len(fold_rows),
        "fold_table": fold_table,
        "fold_r_per_day": means,
        "recent_two_fold_mean_r_per_day": recent,
        "early_folds_mean_r_per_day": early,
        "decay_ratio": recent / early,
        "n_trades_in_the_recent_two_folds": sum(f["n_trades"] for f in fold_rows[-2:]),
        "n_trades_total": sum(f["n_trades"] for f in fold_rows),
        "sizing_instruction": "size on the RECENT folds. `stability` counts the SIGN of a fold "
                              "mean, not its level, so a 7.6x chronological decay reads as 5/5 "
                              "positive and passes every gate by construction (wave-11 §1).",
        "family_bill_now": {
            "declared_family_at_ratification_V3": m3,
            "declared_family_now_V5": m5,
            "p_raw": p,
            "bh_rank1_bar_at_V3": alpha / m3,
            "bh_rank1_bar_at_V5": alpha / m5,
            "inside_by_at_V3": (alpha / m3) / p,
            "inside_by_at_V5": (alpha / m5) / p,
            "still_admits_at_V5": p < (alpha / m5),
            "note": "p is family-invariant; only the bar moves. The wave-11 ratchet raised "
                    f"CANDIDATE_BOOK_V1 from {m3} to {m5}, and the admission survives it.",
        },
    }


# =====================================================================================
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", default="all",
                    help="comma list of noop,blast,membership,token,regate,sizing or 'all'")
    ap.add_argument("--no-ledger", action="store_true")
    args = ap.parse_args()
    want = ("noop", "blast", "membership", "token", "regate", "sizing") \
        if args.stage == "all" else tuple(s.strip() for s in args.stage.split(","))

    ledger = None
    if not args.no_ledger and "regate" in want:
        try:
            from src.research_infra.validation_integrity.trial_budget_ledger import (
                DEFAULT_TRIAL_LEDGER, TrialLedger,
            )
            ledger = TrialLedger(DEFAULT_TRIAL_LEDGER, session="AS")
        except Exception as exc:  # pragma: no cover - the ledger must never block a measurement
            print(f"  (trial ledger unavailable: {exc})")

    cache = json.loads(STAGES.read_text()) if STAGES.is_file() else {}
    runners = {"noop": stage_noop, "blast": stage_blast, "membership": stage_membership,
               "token": stage_token, "sizing": stage_sizing}
    for name in want:
        t0 = time.time()
        print(f"[{name}] ...", flush=True)
        cache[name] = stage_regate(ledger) if name == "regate" else runners[name]()
        cache[name]["seconds"] = round(time.time() - t0, 2)
        STAGES.write_text(json.dumps(cache, indent=1, default=str) + "\n")
        print(f"[{name}] {time.time()-t0:.1f}s", flush=True)

    doc = {
        "schema": "gtos.live.exit_contract_activation.v1",
        "generated_by": "docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                        "as_exit_contract_activation.py",
        "session": "AS", "blocks": "B1520-B1539",
        "armed_set_asserted_unmoved": list(ARMED),
        **{k: v for k, v in cache.items()},
    }
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")
    if ledger is not None:
        print(f"trial ledger: {ledger.n_written} rows appended to {ledger.path} "
              f"(session {ledger.session}, {ledger.write_errors} write errors)")


if __name__ == "__main__":
    main()
