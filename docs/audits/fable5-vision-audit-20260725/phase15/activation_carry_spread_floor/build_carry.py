"""Build the CE spread-geometry-floor activation carry (Session CE, B2300-B2349).

Run from the repo root:

    python3 docs/audits/fable5-vision-audit-20260725/phase15/activation_carry_spread_floor/build_carry.py

WHAT THIS PRODUCES, AND WHY IT IS NOT "COPY MAINLINE"
-----------------------------------------------------
The live host does not run mainline. It runs the VPS lineage `redacted_host` plus three carries
that have landed on it (Session S's packet carry, Session AC's activation carry, Session AZ's
mx_btcusd carry). Its `book_engine.py` is the LINEAGE file -- 36,498 bytes against mainline's
58,727 -- and its `book_owner.py` is Session AZ's after-bytes, 226,002 against mainline's
254,834. Copying either whole would drag waves 5-14 onto a funded machine whose import closure
has never been checked for them. Session AZ made exactly this argument for `book_owner.py`;
this build makes it for `book_engine.py` as well, and for the same measured reason.

So each carried file is one of two kinds, stated per file in the manifest:

  * `mainline byte-identical` -- a NEW file with a satisfied import closure. Only
    `spread_geometry.py` qualifies: it imports `typing` and nothing else, so its closure is
    satisfied by any Python the host can start.
  * `host file + N anchored edits` -- the host's own bytes with the floor's hunks applied at
    anchors that are asserted to appear EXACTLY ONCE. An anchor that matches zero or twice
    aborts the build rather than producing a payload nobody can check.

THE ANCHORS ARE VERIFIED AGAINST THE HOST'S OWN BYTES, NOT AGAINST MAINLINE'S
-----------------------------------------------------------------------------
`book_engine.py`'s before-bytes come from `git show redacted_host:...`, and its generation loop is
BYTE-IDENTICAL to mainline's in the anchor region -- which is what makes a three-hunk anchored
edit honest rather than optimistic. `book_owner.py` and `run_book.py` come from Session AZ's
own payload files, which are the bytes that ceremony wrote to the host on 2026-07-31
(`phase13/receipts/MX_ACTIVATION_20260731.md`).

`run_book.py` is variant-selected exactly as AZ's was: the Stage-0 carry recorded LINE COUNTS
and no sha256, so no artifact pins the host's bytes. AZ's ceremony RESOLVED that -- the host
was recognised as variant `96ac1b566dc8` (Session I safety spine) and is now at that variant's
after-bytes. This carry therefore has ONE expected before-state for `run_book.py` and it is
pinned by a receipt for the first time in this programme.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
AZ = ROOT / "docs/audits/fable5-vision-audit-20260725/phase13/activation_carry_mx/files"
AC = ROOT / "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/files"
FILES = HERE / "files"
DIFFS = HERE / "diffs"

VPS_BASE_COMMIT = "redacted_host87668c5d503b52925d10be7dfb66540"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def anchored(src: str, old: str, new: str, *, what: str) -> str:
    """Replace `old` with `new`, asserting `old` occurs EXACTLY ONCE.

    Zero matches means the host is not in the state this build assumes. Two means the edit
    would land in a place nobody looked at. Both abort: a payload built on a guessed anchor is
    worse than no payload, because the sha256 in the manifest makes it look checked.
    """
    n = src.count(old)
    if n != 1:
        raise SystemExit(
            f"ABORT: anchor for {what!r} matched {n} times, expected exactly 1.\n"
            f"--- anchor ---\n{old}\n--------------")
    return src.replace(old, new, 1)


def git_show(rev: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT,
                          check=True, capture_output=True).stdout


# ======================================================================================
# 1. src/components/ultimate_book/spread_geometry.py  -- NEW, mainline byte-identical
# ======================================================================================

SPREAD_GEOMETRY = (ROOT / "src/components/ultimate_book/spread_geometry.py").read_bytes()


# ======================================================================================
# 2. src/components/ultimate_book/book_engine.py  -- lineage + 3 anchored edits
# ======================================================================================

# NOT the lineage's bytes, and this correction is the first thing this build got wrong.
# `book_engine.py` LOOKS like a path no ceremony has written -- Session AZ's manifest does not
# mention it and Session S's does not carry it -- but Session AC's activation carry has it as
# copy_order 3, and that carry landed on the host on 2026-07-29 12:37-12:39Z (8 of 9 files at
# after-hashes; `phase8/receipts/VPS_CEREMONY_COMPLETED.md`). The host is therefore at AC's
# after-bytes, 37,838 bytes and sha256 b6a9ef7d..., not the lineage's 36,498 / 187f35a4....
# Building against the lineage would have produced a manifest whose `sha256_before_expected`
# fails preflight on a funded machine -- which is the good outcome; the bad one is a verifier
# that reads "not carried yet" and an operator who copies anyway.
ENGINE_BEFORE = (AC / "book_engine.py").read_bytes()
_LINEAGE_ENGINE = git_show(VPS_BASE_COMMIT, "src/components/ultimate_book/book_engine.py")
assert sha(ENGINE_BEFORE) == \
    "b6a9ef7d98d20629260c3aaf8db9bbbba72dae36ec70ad5088c9b3482cd7b68a", \
    "AC's book_engine payload is not at the sha256 its own manifest records"

ENGINE_SIG_OLD = """    def __init__(self, config: dict, mt5, repo_root: str, namespace: str = "ftmo_primary",
                 account: str = "A", bar_count: int = 260, broker_symbol=None):
        self.config = config or {}
        self._mt5 = mt5
"""
ENGINE_SIG_NEW = '''    def __init__(self, config: dict, mt5, repo_root: str, namespace: str = "ftmo_primary",
                 account: str = "A", bar_count: int = 260, broker_symbol=None,
                 spread_geometry_floor=None):
        self.config = config or {}
        self._mt5 = mt5
        # THE GENERATION-SIDE SPREAD-GEOMETRY FLOOR (Session AY, B1810; carried by Session CE,
        # B2300). DEFAULT EMPTY -> not one tick of behaviour changes on this host.
        #
        # A stop narrower than a few multiples of the round-trip spread should never be
        # PROPOSED. This book already refuses to PLACE one -- twice, at the send layer
        # (`broker_net_cost_engine.pretrade_cost_refusal_reasons` and
        # `book_owner._spread_cost_screen`, both at `selected_cell_pretrade_max_spread_r`) --
        # and it fires: 198 legs refused on the two cost paths in this host's own launcher log
        # over 5,237 cycles, at observed spread_r up to 16.543.
        #
        # But between generation and send the doomed intent has ALREADY BEEN COUNTED.
        # `_running_conviction_override` below builds the day's distinct-firing-sleeve count
        # from INTENTS, after `precount_intent_filter`'s drop rules -- and the cost screen is
        # not one of them and cannot be, because it needs a tick and runs later.
        # `admission.py` then takes `na = max(na, override)`, monotone upward. So a sleeve
        # whose every leg the cost gate will refuse still raises the day's Kelly-lite
        # multiplier for every sleeve that DOES place: measured on this host's own export at
        # 16 contaminated account-days, 3 of which moved the multiplier, worst +25.227 % on
        # every unit that day (`AY_LIVE_SCREEN_EVIDENCE_V1.json`).
        #
        # Refusing at generation closes that by construction. Turning it ON for a sleeve is an
        # owner decision: it CHANGES WHICH TRADES AN ARMED BOOK PROPOSES.
        self._spread_geometry_floor = dict(spread_geometry_floor or {})
'''

ENGINE_LOOP_OLD = """                if intent is None:
                    continue
                intents.append(intent)
"""
ENGINE_LOOP_NEW = """                if intent is None:
                    continue
                # THE SPREAD-GEOMETRY FLOOR (default-OFF; see __init__). Applied here, after
                # the generator has proposed a stop and before the intent exists as far as
                # anything downstream is concerned -- which is the whole point: an intent
                # refused here never reaches `_running_conviction_override`, so it cannot
                # raise the day's Kelly-lite multiplier for the sleeves that do place.
                refusal = self._spread_geometry_refusal(intent, spec, symbol, generation)
                if refusal is not None:
                    generation_skips.append(refusal)
                    continue
                intents.append(intent)
"""

ENGINE_METHOD_ANCHOR = "    # ---------------- equity / open-risk ----------------\n"
ENGINE_METHOD_NEW = '''    def _spread_geometry_refusal(self, intent, spec, symbol, generation) -> Optional[dict]:
        """The generation-side spread-geometry floor for ONE intent. None => keep it.

        Returns a `generation_skips` row on refusal, so the decision is visible in the same
        place every other generation skip is rather than in a log line nobody greps.

        FAIL-CLOSED, INCLUDING ON THIS METHOD'S OWN BUGS. An exception here would otherwise
        propagate to `evaluate`'s catch-all and stand the whole book down for the tick, so
        it is caught -- and caught as a REFUSAL of this one intent, not as a pass. That
        matches the authoritative gate (`missing_current_quote_spread_or_sl_distance` is a
        refusal reason, not a warning), and it fails in the direction that costs one trade
        rather than the direction that takes the pathological one. The skip row names the
        exception so a persistent internal fault reads as a fault, not as a quiet sleeve.
        """
        if not self._spread_geometry_floor:
            return None
        try:
            from .spread_geometry import evaluate_intent, resolve_floor_limit
            limit = resolve_floor_limit(self.config, spec.tag, self._spread_geometry_floor)
            if limit is None:
                return None
            tick = None
            try:
                tick = self._mt5.get_tick(self._broker_symbol(symbol))
            except Exception:   # noqa: BLE001 -- an unreadable quote is a REFUSAL, below
                tick = None
            reason, obs = evaluate_intent(intent, tick, limit)
            counts = generation.setdefault("spread_geometry_floor", {
                "evaluated": 0, "refused": 0, "sleeves": []})
            counts["evaluated"] += 1
            if reason is None:
                return None
            counts["refused"] += 1
            if spec.tag not in counts["sleeves"]:
                counts["sleeves"].append(spec.tag)
            return {"symbol": symbol, "sleeve": spec.tag, "cluster": spec.cluster,
                    "timeframe": spec.timeframe, "reason": reason,
                    "spread_geometry": {k: v for k, v in obs.items() if v is not None}}
        except Exception as exc:   # noqa: BLE001 -- never break the cycle; never fail open
            return {"symbol": symbol, "sleeve": getattr(spec, "tag", None),
                    "reason": f"spread_geometry_floor_error:{type(exc).__name__}:{exc}"}

    # ---------------- equity / open-risk ----------------
'''


def build_engine() -> bytes:
    src = ENGINE_BEFORE.decode("utf-8")
    src = anchored(src, ENGINE_SIG_OLD, ENGINE_SIG_NEW, what="book_engine.__init__ signature")
    src = anchored(src, ENGINE_LOOP_OLD, ENGINE_LOOP_NEW, what="book_engine generation loop")
    src = anchored(src, ENGINE_METHOD_ANCHOR, ENGINE_METHOD_NEW,
                   what="book_engine _spread_geometry_refusal insertion point")
    return src.encode("utf-8")


# ======================================================================================
# 3. src/components/ultimate_book/book_owner.py  -- AZ's after-bytes + 3 anchored edits
# ======================================================================================

OWNER_BEFORE = (AZ / "book_owner.py").read_bytes()

OWNER_SIG_OLD = """                 frontier_exits: tuple = ()):
"""
OWNER_SIG_NEW = """                 frontier_exits: tuple = (), spread_geometry_floor=None):
"""

OWNER_FIELD_OLD = """        self.base_config = base_config or {}
        self._frontier_exits = tuple(frontier_exits or ())
        self._mt5 = mt5
"""
OWNER_FIELD_NEW = """        # `spread_geometry_floor` is the second of the same shape, reached from `run_book.py
        # --spread-geometry-floor` (Session AY, B1810; carried by Session CE, B2300). It is a
        # PER-SLEEVE MAP rather than a boolean because AY-1 measured the repair sleeve by
        # sleeve at the ratified rule and it is a REPAIR on two of the armed sleeves
        # (`sub_mid_dn_revert` +0.426 R/day, `sub_xvol_pullback` +0.264), NEUTRAL on the other
        # two (`crypto`, `energy_agri` -- inside the random-drop envelope at every band) and a
        # NO-OP on seven of the estate. One boolean would force the two NEUTRAL sleeves to be
        # armed with the two REPAIRs. It reaches GENERATION only -- the send-layer gate it
        # mirrors already exists on this host and is untouched. It is a constructor argument
        # and NOT a config key for the same reason `frontier_exits` is: both
        # `config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are hashed into a
        # live activation token's config digest. Default {} == byte-identical to what this
        # host runs today.
        self.base_config = base_config or {}
        self._frontier_exits = tuple(frontier_exits or ())
        self._spread_geometry_floor = dict(spread_geometry_floor or {})
        self._mt5 = mt5
"""

OWNER_ENGINE_OLD = """        self.engine = UltimateBookLiveEngine(rt, mt5, repo_root, namespace=namespace,
                                             broker_symbol=self._broker_symbol)
"""
OWNER_ENGINE_NEW = """        self.engine = UltimateBookLiveEngine(rt, mt5, repo_root, namespace=namespace,
                                             broker_symbol=self._broker_symbol,
                                             spread_geometry_floor=self._spread_geometry_floor)
"""


def build_owner() -> bytes:
    src = OWNER_BEFORE.decode("utf-8")
    src = anchored(src, OWNER_SIG_OLD, OWNER_SIG_NEW, what="book_owner.__init__ signature")
    src = anchored(src, OWNER_FIELD_OLD, OWNER_FIELD_NEW, what="book_owner field assignment")
    src = anchored(src, OWNER_ENGINE_OLD, OWNER_ENGINE_NEW, what="book_owner engine construction")
    return src.encode("utf-8")


# ======================================================================================
# 4. run_book.py  -- AZ's variant-96ac after-bytes + 3 anchored edits
# ======================================================================================

RUN_BOOK_BEFORE = (AZ / "run_book.variant_96ac1b566dc8.py").read_bytes()

RB_ARG_ANCHOR = """    args = p.parse_args()
"""
RB_ARG_NEW = '''    p.add_argument("--spread-geometry-floor", default=None,
                   help="Comma-separated sleeves to run with the GENERATION-side "
                        "spread-geometry floor on, optionally with a per-sleeve spread_r "
                        "limit (`sub_mid_dn_revert` or `sub_mid_dn_revert:0.075`). Session AY, "
                        "B1810. A sleeve named WITHOUT a limit inherits the limit the send "
                        "gate will apply to it (`selected_cell_pretrade_max_spread_r`, with "
                        "the per-sleeve override), so the two layers cannot drift apart and an "
                        "owner config edit moves both at once. This book ALREADY refuses these "
                        "trades at the send layer; the floor refuses them EARLIER, which is "
                        "worth something for a reason that is about the OTHER sleeves: an "
                        "intent that reaches the intent list has already been counted by "
                        "`_running_conviction_override`, and `na = max(na, override)` is "
                        "monotone upward, so a sleeve whose every leg the cost gate refuses "
                        "still raises the day's Kelly-lite multiplier for every sleeve that "
                        "does place -- measured on this host's own export at 16 contaminated "
                        "account-days, 3 of which moved the multiplier, worst +25.227 %%. "
                        "REPAIR at the ratified rule on `sub_mid_dn_revert` (+0.426 R/day at "
                        "mid, 46.9 %% of its trades over the limit) and `sub_xvol_pullback` "
                        "(+0.264, on 6 dropped trades of 85); NEUTRAL on `crypto` and "
                        "`energy_agri`, which is why this is a per-sleeve map and not a "
                        "boolean. FAIL-CLOSED: an opted-in sleeve whose quote cannot be read "
                        "proposes nothing that tick, matching the authoritative gate's own "
                        "`missing_current_quote_spread_or_sl_distance`. Empty by default. An "
                        "empty string is REFUSED rather than read as 'all' (the --tags "
                        "fail-open, B359) and an unknown sleeve name is REFUSED rather than "
                        "dropped. Set here rather than in agent_config.yaml or "
                        "profiles/redacted_account.yaml because BOTH are hashed into a live "
                        "activation token's config digest.")
    args = p.parse_args()
'''

RB_PARSE_OLD = """    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace,
                              frontier_exits=frontier_exits)
"""
RB_PARSE_NEW = """    # Same doctrine, same wave (Session AY, B1810): a floor the operator believes is running
    # and is not is worse than no floor, so an unparseable or unknown selection stops the
    # worker HERE rather than degrading silently at every tick.
    from src.components.ultimate_book.spread_geometry import (
        SpreadGeometryFloorError, parse_spread_geometry_floor,
    )
    # EVERY registered generator, not just `BUILT`. `BUILT` is the 11 core sleeves; the
    # candidate book adds 9 and market expansion 12, and AY-1's largest measured repair
    # (`asia_pdl_fade`, -0.902 -> +0.095 R/day at mid) is in CANDIDATE_BUILT. Validating
    # against `BUILT` alone would refuse the flag's best use as a typo.
    from src.components.ultimate_book.sleeves.registry import (
        BUILT as _BUILT_SLEEVES, CANDIDATE_BUILT as _CAND_SLEEVES,
        MARKET_EXPANSION_BUILT as _MX_SLEEVES,
    )
    _known_sleeves = set(_BUILT_SLEEVES) | set(_CAND_SLEEVES) | set(_MX_SLEEVES)
    try:
        spread_geometry_floor = parse_spread_geometry_floor(
            args.spread_geometry_floor, known_sleeves=_known_sleeves)
    except SpreadGeometryFloorError as exc:
        logging.error("--spread-geometry-floor refused: %s", exc)
        return 4
    owner = UltimateBookOwner(merged, mt5, ".", namespace=args.namespace,
                              frontier_exits=frontier_exits,
                              spread_geometry_floor=spread_geometry_floor)
"""

RB_BANNER_OLD = """                        describe_frontier_contract(_s))
    broker_symbol = build_broker_symbol_resolver(merged)
"""
RB_BANNER_NEW = """                        describe_frontier_contract(_s))
    if spread_geometry_floor:
        _rt_cfg = merged.get("gtos_vnext_runtime", merged)
        from src.components.ultimate_book.spread_geometry import resolve_floor_limit
        for _s in sorted(spread_geometry_floor):
            _lim = resolve_floor_limit(_rt_cfg, _s, spread_geometry_floor)
            logging.warning("SPREAD-GEOMETRY FLOOR IS ON for %s at spread_r <= %.4f (%s). "
                            "Intents whose live spread exceeds that fraction of their own stop "
                            "are refused AT GENERATION, so they never enter the day's running "
                            "conviction count. This changes WHICH TRADES this book proposes.",
                            _s, _lim,
                            "explicit" if spread_geometry_floor[_s] is not None
                            else "inherited from the send gate's own limit")
    broker_symbol = build_broker_symbol_resolver(merged)
"""


def build_run_book() -> bytes:
    src = RUN_BOOK_BEFORE.decode("utf-8")
    src = anchored(src, RB_ARG_ANCHOR, RB_ARG_NEW, what="run_book argparse insertion point")
    src = anchored(src, RB_PARSE_OLD, RB_PARSE_NEW, what="run_book parse + owner construction")
    src = anchored(src, RB_BANNER_OLD, RB_BANNER_NEW, what="run_book launch banner")
    return src.encode("utf-8")


# ======================================================================================
# emit
# ======================================================================================

def unified_diff(before: bytes, after: bytes, path: str) -> str:
    import difflib
    return "".join(difflib.unified_diff(
        before.decode("utf-8").splitlines(keepends=True),
        after.decode("utf-8").splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}", n=4))


def main() -> int:
    FILES.mkdir(parents=True, exist_ok=True)
    DIFFS.mkdir(parents=True, exist_ok=True)

    engine_after = build_engine()
    owner_after = build_owner()
    run_book_after = build_run_book()

    # A payload that does not COMPILE cannot be allowed to reach a funded host. This is a
    # syntax check only -- `verify_carry.py --check imports/behaviour` is what proves it runs.
    import py_compile
    import tempfile
    for name, blob in (("book_engine.py", engine_after), ("book_owner.py", owner_after),
                       ("run_book.py", run_book_after),
                       ("spread_geometry.py", SPREAD_GEOMETRY)):
        with tempfile.NamedTemporaryFile("wb", suffix=".py", delete=False) as fh:
            fh.write(blob)
            tmp = fh.name
        py_compile.compile(tmp, doraise=True)
        Path(tmp).unlink(missing_ok=True)
        print(f"  compiles: {name}")

    records = [
        {
            "copy_order": 1, "stage": "A",
            "repo_path": "src/components/ultimate_book/spread_geometry.py",
            "destination_on_vps": "src\\components\\ultimate_book\\spread_geometry.py",
            "payload_basename": "spread_geometry.py",
            "is_new_file_on_vps": True,
            "before": None, "after": SPREAD_GEOMETRY,
            "host_bytes_provenance": "ABSENT on the host -- a new module. `git show "
                                     "redacted_host:src/components/ultimate_book/spread_geometry.py` "
                                     "fails: the path does not exist in the lineage.",
            "source_kind": "mainline byte-identical",
            "note": "FIRST, and it is inert until something imports it. Its import closure is "
                    "`typing` and nothing else -- no MT5, no config read, no other project "
                    "module -- so it cannot fail to import on any interpreter that starts. "
                    "Carried byte-identical to mainline because there is nothing to reconcile: "
                    "no version of it has ever existed on this host.",
        },
        {
            "copy_order": 2, "stage": "A",
            "repo_path": "src/components/ultimate_book/book_engine.py",
            "destination_on_vps": "src\\components\\ultimate_book\\book_engine.py",
            "payload_basename": "book_engine.py",
            "is_new_file_on_vps": False,
            "before": ENGINE_BEFORE, "after": engine_after,
            "host_bytes_provenance": "Session AC's activation carry (copy_order 3), applied to "
                                     "the host 2026-07-29 12:37-12:39Z and verified at "
                                     "after-bytes by `verify_carry.py --check all` on "
                                     "2026-07-30 (phase8/receipts/VPS_CEREMONY_COMPLETED.md), "
                                     f"then committed on the host branch. NOT lineage "
                                     f"{VPS_BASE_COMMIT[:9]}, which is what this build assumed "
                                     "on its first pass and had wrong.",
            "source_kind": "host file + 3 anchored edits",
            "note": "SECOND. MAINLINE'S book_engine.py MUST NOT BE COPIED: it is 58,727 bytes "
                    "against this host's 37,838, and the diff carries waves 5-14 "
                    "(pre-gap bar recovery, the vol-level tilt, AB's regime spine) whose import "
                    "closure this host has never been checked for. The three anchored edits are "
                    "the whole of the floor's engine side: the kwarg + field, the one call in "
                    "the generation loop, and the method. INERT until book_owner.py passes the "
                    "kwarg, so landing it alone changes nothing.",
        },
        {
            "copy_order": 3, "stage": "A",
            "repo_path": "src/components/ultimate_book/book_owner.py",
            "destination_on_vps": "src\\components\\ultimate_book\\book_owner.py",
            "payload_basename": "book_owner.py",
            "is_new_file_on_vps": False,
            "before": OWNER_BEFORE, "after": owner_after,
            "host_bytes_provenance": "Session AZ's mx_btcusd carry, after-bytes written to the "
                                     "host 2026-07-31 ~01:26Z and recorded in the host's "
                                     "CARRIED_STATE.json (phase13/receipts/"
                                     "MX_ACTIVATION_20260731.md)",
            "source_kind": "host file + 3 anchored edits",
            "note": "THIRD, and the ordering is load-bearing: it passes "
                    "`spread_geometry_floor=` to UltimateBookLiveEngine, which the lineage "
                    "engine's signature does not accept -- a TypeError at STARTUP, on both "
                    "namespaces. MAINLINE'S book_owner.py MUST NOT BE COPIED for the reason "
                    "Session AZ measured (254,834 bytes against this host's 226,002).",
        },
        {
            "copy_order": 4, "stage": "A",
            "repo_path": "run_book.py",
            "destination_on_vps": "run_book.py",
            "payload_basename": "run_book.py",
            "is_new_file_on_vps": False,
            "before": RUN_BOOK_BEFORE, "after": run_book_after,
            "host_bytes_provenance": "Session AZ's mx_btcusd carry, variant `96ac1b566dc8` "
                                     "(Session I safety spine) RESOLVED at the 2026-07-31 "
                                     "ceremony and written at its after-bytes. This is the "
                                     "first carry in the programme whose run_book.py "
                                     "before-state is pinned by a receipt rather than inferred "
                                     "from line counts.",
            "source_kind": "host file + 3 anchored edits",
            "note": "LAST, and that ordering is the whole of the safety argument -- Session "
                    "AZ's, unchanged: run_book.py is the only carried file whose failure is a "
                    "MODULE-LOAD or STARTUP death on both namespaces, and every other file here "
                    "is inert until it exists. It imports `parse_spread_geometry_floor` from "
                    "spread_geometry (ImportError without file 1) and passes "
                    "`spread_geometry_floor=` to UltimateBookOwner (TypeError without file 3).",
        },
    ]

    files = []
    for rec in records:
        after = rec.pop("after")
        before = rec.pop("before")
        payload = FILES / rec["payload_basename"]
        payload.write_bytes(after)
        if before is not None:
            (DIFFS / (rec["repo_path"].replace("/", "_") + ".diff")).write_text(
                unified_diff(before, after, rec["repo_path"]), encoding="utf-8")
        rec2 = dict(rec)
        rec2["source_in_this_repo"] = (
            "docs/audits/fable5-vision-audit-20260725/phase15/"
            f"activation_carry_spread_floor/files/{rec['payload_basename']}")
        if before is not None:
            rec2["diff_in_this_repo"] = (
                "docs/audits/fable5-vision-audit-20260725/phase15/"
                "activation_carry_spread_floor/diffs/"
                + rec["repo_path"].replace("/", "_") + ".diff")
            rec2["sha256_before_expected"] = sha(before)
            rec2["bytes_before"] = len(before)
        else:
            rec2["sha256_before_expected"] = None
            rec2["bytes_before"] = 0
        rec2["sha256_after_carry"] = sha(after)
        rec2["bytes_after"] = len(after)
        rec2["crlf_present"] = b"\r\n" in after
        files.append(rec2)
        print(f"  {rec['copy_order']}. {rec['repo_path']}: "
              f"{rec2['bytes_before']} -> {rec2['bytes_after']} bytes")

    manifest = {
        "schema": "gtos.phase15.activation_carry_spread_floor_manifest.v1",
        "session": "CE",
        "blocks": "B2300-B2349",
        "built_by": "docs/audits/fable5-vision-audit-20260725/phase15/"
                    "activation_carry_spread_floor/build_carry.py",
        "purpose": (
            "Make Session AY's GENERATION-SIDE spread-geometry floor RUNNABLE on the live "
            "host. The package arms nothing: it carries the capability, and the activation is "
            "`--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback` on the supervisor "
            "line. Under OD-HISTORICAL-FIRST a measured, controls-clean improvement to an "
            "armed sleeve sleeping behind a default-off flag is a DEFECT STATE; AY measured "
            "REPAIR on two of the armed sleeves with a 20-seed random null and a negative "
            "inverse control, so this is the clearest case in the estate."),
        "vps_base_ref": "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18",
        "vps_base_commit": VPS_BASE_COMMIT,
        "host_repo_root": "C:\\Users\\MSI\\Documents\\ai-trading-agent",
        "host_interpreter": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.venv-gtos\\Scripts\\python.exe",
        "host_interpreter_version": "3.13.13",
        "host_branch_head_at_build_time": "d6c9c4b19 (the mx_btcusd activation, 2026-07-31 ~01:26Z)",
        "arms_nothing_by_itself": True,
        "composes_with": {
            "session_S_packet_carry": "docs/audits/fable5-vision-audit-20260725/phase4/packet_carry/MANIFEST.json",
            "session_AC_activation_carry": "docs/audits/fable5-vision-audit-20260725/phase5/activation_carry/MANIFEST.json",
            "session_AZ_mx_carry": "docs/audits/fable5-vision-audit-20260725/phase13/activation_carry_mx/MANIFEST.json",
            "rule": (
                "All three are ALREADY APPLIED on the host. This carry reads AZ's after-bytes "
                "as its OWN before-bytes for book_owner.py and run_book.py, shares no "
                "destination path with the S or AC carries that AZ did not already supersede, "
                "and adds two paths no carry has ever written "
                "(book_engine.py, spread_geometry.py)."),
            "supersedes": {
                "book_owner.py": {"az_after": sha(OWNER_BEFORE),
                                  "this_carry_after": sha(owner_after)},
                "run_book.py": {"az_after": sha(RUN_BOOK_BEFORE),
                                "this_carry_after": sha(run_book_after)},
            },
        },
        "not_carried": [
            {
                "repo_path": "config/agent_config.yaml",
                "reason": "Hashed into the live activation token's config digest (FTMO "
                          "ffe16657feaf, redacted_account e184a81d3b1b). One byte stops the armed "
                          "book placing until the token is re-minted. Nothing here needs it: "
                          "the floor's limit is READ from this file at run time via "
                          "`resolve_floor_limit`, which is exactly why the selection is a "
                          "launcher argument and the threshold is not.",
            },
            {
                "repo_path": "config/profiles/redacted_account.yaml",
                "reason": "Same, and the redacted_account account is out of scope for this "
                          "activation -- AY's REPAIR sleeves are `sub_mid_dn_revert` (not in "
                          "redacted_account's four tags) and `sub_xvol_pullback` (which is).",
            },
            {
                "repo_path": "src/components/ultimate_book/weekend_policy.py",
                "reason": "Session BA's weekend policy is a SEPARATE owner decision (CE-3) and "
                          "its own precondition is carrying `src/utils/broker_clock.py`, which "
                          "is ABSENT from this host. Carrying it here would put a module on a "
                          "funded machine ahead of the decision that needs it. The floor's "
                          "anchored edits are placed so a later weekend carry appends to the "
                          "same signatures without conflict -- verified in "
                          "`verify_carry.py --check behaviour`.",
            },
            {
                "repo_path": "src/components/ultimate_book/execution_packets.py",
                "reason": "Untouched by the floor. AZ carried it on 2026-07-31 and it is at "
                          "AZ's after-bytes; re-carrying an unchanged file only adds a way for "
                          "a ceremony to go wrong.",
            },
        ],
        "seal_exposure": {
            "R2_input_bindings": "none of the 4 carried paths is bound (43 bound paths checked "
                                 "at session start: 2 UNHYDRATED-LFS, 0 drifted)",
            "R1_input_bindings": "none",
            "code_authority_paths": "none",
            "config_file_hashes": "no config file is touched, so "
                                  "shared_execution_contract_digest_sha256 cannot move",
            "activation_tokens": "neither token's config digest can move -- the token binds "
                                 "config bytes and this carry writes only .py files",
            "checked_at": "session CE, against "
                          "src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py "
                          "and both contracts",
        },
        "files": files,
    }
    (HERE / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {HERE / 'MANIFEST.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
