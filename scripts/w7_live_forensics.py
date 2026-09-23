#!/usr/bin/env python3
"""Build the W7 live-divergence row set from broker truth, and attribute the drawdown window.

Gate G1b, Phase 1 item 2. Emits the artifact described by
`docs/audits/fable5-vision-audit-20260725/LIVE_DIVERGENCE_ROW_SCHEMA.md`.

WHY BROKER TRUTH IS PRIMARY, and not the GTOS ledgers
-----------------------------------------------------
The three GTOS-side execution ledgers died on 2026-07-02 (finding V3) and
`broker_order_lifecycle_capture_v4.jsonl` is request-side only, with `order_result` absent on all
594 rows (finding V2). So the only complete per-trade record of the W7 live window is the broker's
own deal + order history, exported from the VPS on 2026-07-26 to `09_mt5_api/`.

The load-bearing discovery this tool rests on: **the broker deal `comment` carries the sleeve tag**
(`W7:<sleeve>`), because the live book stamps it on the order request. So sleeve attribution -- Gate
G1b's axis (a) -- survives in broker truth and does not depend on the dead ledgers at all.

TIME BASE
---------
MT5 `history_deals_get().time` is BROKER SERVER WALL CLOCK expressed as a Unix epoch, not UTC
(finding F7). Converted with `src.utils.broker_clock.broker_epoch_to_utc`, which fails closed on an
unregistered server. Both accounts resolve to `new_york_plus_7`.

MONEY-PER-PRICE-UNIT
--------------------
R needs `risk_at_entry_usd = |entry - sl| * volume * usd_per_price_unit_per_lot`. Rather than trust a
symbol spec captured 2026-07-26 for trades placed in June, this tool SOLVES for the factor from the
position's own realized P&L:

    profit = (exit - entry) * dir * volume * usd_per_price_unit_per_lot

so `usd_per_price_unit_per_lot = profit / ((exit - entry) * dir * volume)`. That is self-calibrating,
uses only broker truth, and is exact at the position's own fill prices and FX rate. It degrades to the
symbol spec's `trade_tick_value / trade_tick_size` when the position closed flat (denominator ~0), and
to `null` when neither is available. `r_money_basis` records which was used on every row.

Run:  python3 scripts/w7_live_forensics.py [--export-root PATH] [--out-dir PATH]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    offset_seconds_at_utc,
    resolve_rule,
)

SCHEMA_VERSION = "gtos.live_divergence_row.v1"

DEFAULT_EXPORT_ROOT = Path("/Users/borr/GTOSActive/vps-export-20260725/extracted")
DEFAULT_TICK_ROOT = Path("/Users/borr/GTOSActive/vps-ticks-20260726")
DEFAULT_OUT = REPO / "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics"

# --------------------------------------------------------------------------------------------------
# Accounts
# --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class AccountSpec:
    key: str
    login: int
    server: str
    deals_file: str
    orders_file: str
    specs_file: str
    account_file: str
    initial_balance: float
    final_balance: float
    # Which calendar the FIRM resets its daily-loss window on. Different question from the MT5 server
    # clock -- see broker_clock.DAILY_RESET_RULES and B56/B58.
    daily_reset_rule: str | None
    tick_dir: str
    tick_prefix: str


ACCOUNTS: tuple[AccountSpec, ...] = (
    AccountSpec(
        "ftmo", 531325516, "FTMO-Server3",
        "ftmo_history_deals_get.jsonl", "ftmo_history_orders_get.jsonl",
        "ftmo_symbol_specs_traded.json", "ftmo_account_info.json",
        100000.0, 107879.56, "CE(S)T", "ftmo", "FTMO",
    ),
    AccountSpec(
        "redacted_account", 0, "redacted_account-Server 2",
        "redacted_account_history_deals_get.jsonl", "redacted_account_history_orders_get.jsonl",
        "redacted_account_symbol_specs_traded.json", "redacted_account_account_info.json",
        100000.0, 96229.28, None, "redacted_account", "redacted_account",
    ),
)

# --------------------------------------------------------------------------------------------------
# Sleeve books, read from the live surfaces rather than restated
# --------------------------------------------------------------------------------------------------


def load_books() -> dict[str, Any]:
    """Resolve the three live books from the code they are actually defined in.

    core-8   -> admission.SLEEVE_REGISTRY (config `ultimate_book_include_clean3: false`)
    9 cand.  -> agent_config.yaml `ultimate_book_candidate_book_sleeves`
    12 m.exp -> candidate_registry.MARKET_EXPANSION_CONDITIONED_POLICIES[<live policy>]
    """
    from src.components.ultimate_book import admission
    from src.components.ultimate_book.sleeves import candidate_registry as cr

    core8 = {
        name: {
            "confidence": spec.confidence,
            "asset_class": spec.asset_class,
            "status": spec.status,
            "symbols": list(spec.symbols),
        }
        for name, spec in admission.SLEEVE_REGISTRY.items()
    }

    cfg_text = (REPO / "config/agent_config.yaml").read_text()
    candidate_live = _yaml_string_list(cfg_text, "ultimate_book_candidate_book_sleeves")
    policy = _yaml_scalar(cfg_text, "ultimate_book_market_expansion_policy")
    mx_live = sorted(cr.MARKET_EXPANSION_CONDITIONED_POLICIES.get(policy, ()) or ())

    # The full 29-sleeve live registry, exactly as the live bridge assembles it. This is what gives
    # EVERY sleeve -- core, candidate and market-expansion -- its confidence and its asset_class.
    # asset_class is the correlated-risk-unit key, so a registry that only resolves core-8 (as an
    # earlier revision of this script did) leaves ~43% of the book with cluster "unknown", and the
    # cluster is the one axis that actually feeds sizing.
    effective = admission.effective_registry(
        include_clean3=False,
        include_candidate_book=True,
        candidate_book_sleeves=candidate_live,
        include_market_expansion_book=True,
        market_expansion_sleeves=mx_live,
    )
    sleeve_meta = {
        name: {"confidence": s.confidence, "asset_class": s.asset_class, "status": s.status,
               "symbols": list(s.symbols)}
        for name, s in effective.items()
    }

    return {
        "core8": core8,
        "candidate_live": candidate_live,
        "sleeve_meta": sleeve_meta,
        "market_expansion_policy": policy,
        "market_expansion_live": mx_live,
        "clean3": sorted(getattr(admission, "CLEAN3_REGISTRY", {}) or {}),
        "include_clean3": _yaml_scalar(cfg_text, "ultimate_book_include_clean3"),
        "profile": _yaml_scalar(cfg_text, "ultimate_book_profile"),
        "derisk_mode": _yaml_scalar(cfg_text, "ultimate_book_derisk_mode"),
        "allocation_profiles": {
            n: {"risk_per_unit_A": p.risk_per_unit_A, "note": p.note}
            for n, p in admission.ALLOCATION_PROFILES.items()
            if n.startswith("clean3_w7")
        },
    }


def _yaml_scalar(text: str, key: str) -> str | None:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(key + ":"):
            v = s[len(key) + 1:].split("#", 1)[0].strip().strip('"').strip("'")
            return v or None
    return None


def _yaml_string_list(text: str, key: str) -> list[str]:
    out: list[str] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(key + ":"):
            for nxt in lines[i + 1:]:
                st = nxt.strip()
                if st.startswith("- "):
                    out.append(st[2:].split("#", 1)[0].strip().strip('"').strip("'"))
                elif st and not st.startswith("#"):
                    break
            break
    return out


# Non-sleeve comments the runtime and the operator emit. Kept explicit so an unknown comment is
# reported as `unattributed` rather than silently absorbed into a family.
MANUAL_COMMENT_PREFIXES = ("owner_flatten", "GTOS_EMERGENCY", "safety_trade")
SMOKE_COMMENT_PREFIXES = ("FN_SMOKE", "smoke_force_clos", "fn_smoke")
PRE_W7_COMMENT_PREFIXES = ("GoldAgent",)
# Exit-side comments; never appear on an opening deal but listed so misclassification is visible.
EXIT_COMMENT_PREFIXES = ("TP1_", "close_vnext", "[sl ", "[tp ", "so:", "#")

MT5_COMMENT_LIMIT = 16  # measured: every stored comment is <= 16 chars; W7: + 13 of the sleeve name


# --------------------------------------------------------------------------------------------------
# Symbol canonicalisation
# --------------------------------------------------------------------------------------------------

# Broker symbol -> GTOS canonical name. Built from the two brokers' own traded-symbol sets. The two
# brokers use different strings for the same instrument, which is why axis (d) needs this map at all.
BROKER_TO_CANONICAL = {
    # FTMO
    "US100.cash": "NAS100", "US30.cash": "US30_cash", "US500.cash": "SPX500",
    "UK100.cash": "UK100", "GER40.cash": "GER40", "JP225.cash": "JP225",
    "AUS200.cash": "AUS200_cash", "EU50.cash": "EU50_cash", "FRA40.cash": "FRA40_cash",
    "USOIL.cash": "USOIL_cash", "UKOIL.cash": "UKOIL_cash",
    # redacted_account
    "NDX100": "NAS100", "US30": "US30_cash", "SPX500": "SPX500",
    "UK100": "UK100", "GER30": "GER40", "JP225": "JP225",
    "USOUSD": "USOIL_cash", "UKOUSD": "UKOIL_cash",
    # shared / identical
    "XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD", "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
    "AVAUSD": "AVAUSD", "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "AUDUSD": "AUDUSD",
    "NZDUSD": "NZDUSD", "USDCAD": "USDCAD", "USDJPY": "USDJPY", "GBPJPY": "GBPJPY",
    "EURJPY": "EURJPY", "AUDJPY": "AUDJPY", "NZDJPY": "NZDJPY", "CHFJPY": "CHFJPY",
    "CADJPY": "CADJPY", "EURGBP": "EURGBP",
}

# MT5 ENUM_DEAL_REASON, in the SDK's own order. Getting this wrong silently relabels every
# EA-driven close as a browser close: DEAL_REASON_EXPERT is 3, not 1.
DEAL_REASON = {0: "client", 1: "mobile", 2: "web", 3: "expert", 4: "sl", 5: "tp", 6: "so",
               7: "rollover", 8: "vmargin", 9: "split"}


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file. The VPS wrote these from Windows, so they carry a UTF-8 BOM."""
    with io.open(path, encoding="utf-8-sig") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def read_json(path: Path) -> Any:
    with io.open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------------------------------
# Position reconstruction
# --------------------------------------------------------------------------------------------------


def derive_w7_window(deals_by_account: dict[str, list[dict]], rules: dict) -> tuple[str, str]:
    """First and last `W7:`-commented entry day, DERIVED from the data across both accounts.

    An earlier revision hardcoded "2026-06-15"/"2026-07-02" under a comment claiming they were
    established from the data. They were, once, by hand -- which means a refreshed export would age
    them out silently. Derived here so it cannot.
    """
    days: list[str] = []
    for key, deals in deals_by_account.items():
        rule = rules[key]
        for d in deals:
            if d.get("entry") == 0 and d.get("symbol") and str(d.get("comment", "")).startswith("W7:"):
                days.append(broker_epoch_to_utc(d["time"], rule).date().isoformat())
    if not days:
        raise RuntimeError(
            "no W7:-commented entry deals found in either account. The comment tag is the ONLY "
            "discriminator between the W7 book and the pre-W7 fleet (both share magic 20260401), so "
            "an empty result here means the probe is broken, not that the book never traded."
        )
    return min(days), max(days)


def classify_comment(comment: str, books: dict, entry_day_utc: str | None = None,
                     *, window: tuple[str, str], magic: int = 0,
                     open_reason: str | None = None) -> dict[str, Any]:
    """Resolve an opening deal's comment to a sleeve id, family and stack era."""
    c = (comment or "").strip()
    out = {
        "comment_raw": comment or "",
        "sleeve_tag": None,
        "sleeve_id": None,
        "sleeve_resolution": "unresolved",
        "sleeve_candidates": [],
        "sleeve_family": "unattributed",
        "stack_era": "unknown",
        "sleeve_confidence": None,
        "sleeve_status": None,
        "sleeve_cluster": None,
    }
    first, last = window
    if not c:
        # An empty comment is NOT the W7 book: `execution.py:3430-3444` always stamps `W7:<sleeve>`,
        # falling back to the literal `W7:UNTAGGED` (of which there are zero in the data). So an
        # untagged position came from a different code path entirely.
        #
        # WHICH path is decidable, and it is not the broad selector. All three untagged positions in
        # this export carry `magic == 0` -- never 20260401, which every engine-placed order sets
        # (`src/mt5/mt5_interface.py:58`) -- AND an opening deal `reason == 1` (DEAL_REASON_MOBILE).
        # They were placed from the MT5 phone app by hand. Empty-comment and mobile-open are a 1:1
        # correspondence across both accounts, so this is not an inference from one field.
        out["sleeve_family"] = "unattributed"
        out["sleeve_resolution"] = "empty_comment"
        if magic == 0 and open_reason == "mobile":
            out["stack_era"] = "manual_mobile"
        elif entry_day_utc is None:
            out["stack_era"] = "unknown"
        elif entry_day_utc < first:
            out["stack_era"] = "pre_w7_untagged"
        elif entry_day_utc > last:
            out["stack_era"] = "post_w7_broad"
        else:
            # Inside the window, untagged, but NOT hand-placed -- that would be a real attribution
            # gap. Named rather than hidden. Zero rows land here in this export.
            out["stack_era"] = "w7_window_untagged"
        return out
    if c.startswith(PRE_W7_COMMENT_PREFIXES):
        out.update(sleeve_family="pre_w7_fleet", stack_era="pre_w7_fleet",
                   sleeve_resolution="era_comment")
        return out
    if c.startswith(SMOKE_COMMENT_PREFIXES):
        out.update(sleeve_family="smoke", stack_era="smoke", sleeve_resolution="era_comment")
        return out
    if c.startswith(MANUAL_COMMENT_PREFIXES):
        out.update(sleeve_family="manual", stack_era="manual", sleeve_resolution="era_comment")
        return out
    if not c.startswith("W7:"):
        out["sleeve_resolution"] = "not_a_sleeve_comment"
        return out

    tag = c[3:]
    out["sleeve_tag"] = tag
    out["stack_era"] = "w7_book"

    pools = [
        ("core8", list(books["core8"])),
        ("candidate", list(books["candidate_live"])),
        ("market_expansion", list(books["market_expansion_live"])),
        ("clean3_not_deployed", list(books["clean3"])),
    ]
    # Exact match wins outright.
    for family, names in pools:
        if tag in names:
            out.update(sleeve_id=tag, sleeve_family=family, sleeve_resolution="exact")
            return _attach_sleeve_meta(out, books)
    # Otherwise the 16-char MT5 truncation means the tag is a prefix of the real name.
    hits = [(family, n) for family, names in pools for n in names if n.startswith(tag)]
    if len(hits) == 1:
        fam, name = hits[0]
        out.update(sleeve_id=name, sleeve_family=fam, sleeve_resolution="prefix_unique")
        return _attach_sleeve_meta(out, books)
    if len(hits) > 1:
        out.update(sleeve_resolution="prefix_ambiguous",
                   sleeve_candidates=sorted(n for _, n in hits),
                   sleeve_family="unattributed")
        return out
    out["sleeve_resolution"] = "unresolved"
    return out


def _attach_sleeve_meta(row: dict, books: dict) -> dict:
    """Attach confidence / cluster / status from the FULL 29-sleeve live registry.

    Every family, not just core-8. `sleeve_confidence` is the multiplier the sizer applies
    (`admission.py:1192`: ``unit_risk = base_risk_per_unit * conf * derisk_mult``), so without it the
    dial comparison in `unit_risk_analysis` is against the wrong number, and `sleeve_cluster` is the
    correlated-risk-unit key the one-unit-per-cluster-per-day envelope is defined on.
    """
    spec = books["sleeve_meta"].get(row["sleeve_id"]) or {}
    row["sleeve_confidence"] = spec.get("confidence")
    row["sleeve_status"] = spec.get("status")
    row["sleeve_cluster"] = spec.get("asset_class")
    return row


def build_rows(acct: AccountSpec, export_root: Path, books: dict,
               window: tuple[str, str]) -> tuple[list[dict], dict]:
    api = export_root / "09_mt5_api"
    deals = read_jsonl(api / acct.deals_file)
    orders = read_jsonl(api / acct.orders_file)
    specs = read_json(api / acct.specs_file)
    rule = resolve_rule(acct.server)

    order_by_ticket = {o["ticket"]: o for o in orders}
    order_by_position = {}
    for o in orders:
        # The opening order of a position has ticket == position_id in MT5's model.
        if o.get("position_id") and o["ticket"] == o["position_id"]:
            order_by_position[o["position_id"]] = o

    # Split on DEAL TYPE, not on symbol truthiness. DEAL_TYPE_BUY=0 / SELL=1 are the only trade
    # deals; everything else (BALANCE=2, CREDIT=3, CHARGE=4, CORRECTION=5, BONUS=6, COMMISSION=7..10,
    # INTEREST=11, DIVIDEND=15..16, TAX=17) is an account operation. redacted_account's opening deposit is
    # type 4, not type 2 (finding V5), so a type-2-only filter is also wrong. Symbol truthiness
    # happens to coincide on this export, but a commission or dividend row CARRYING a symbol would be
    # silently ingested into the position model and corrupt the reconciliation that is this
    # artifact's correctness proof.
    trade_deals = [d for d in deals if d.get("type") in (0, 1)]
    balance_ops = [d for d in deals if d.get("type") not in (0, 1)]
    stray = [d for d in balance_ops if d.get("symbol")]

    by_pos: dict[int, list[dict]] = defaultdict(list)
    for d in trade_deals:
        by_pos[d["position_id"]].append(d)

    rows: list[dict] = []
    diagnostics = {
        "positions_without_entry_deal": [],
        "positions_without_exit_deal": [],
        "volume_mismatch": [],
    }

    for pos_id, ds in by_pos.items():
        ds.sort(key=lambda r: (r["time_msc"], r["ticket"]))
        opens = [d for d in ds if d["entry"] == 0]
        closes = [d for d in ds if d["entry"] in (1, 3)]  # 1=OUT, 3=OUT_BY
        inouts = [d for d in ds if d["entry"] == 2]       # reversal; none observed, handled anyway
        if not opens:
            diagnostics["positions_without_entry_deal"].append(pos_id)
            opens = ds[:1]
        entry = opens[0]
        sym = entry["symbol"]
        spec = specs.get(sym, {})

        entry_day = broker_epoch_to_utc(entry["time"], rule).date().isoformat()
        open_reason = DEAL_REASON.get(entry.get("reason"))
        cls = classify_comment(entry.get("comment", ""), books, entry_day,
                               window=window, magic=entry.get("magic", 0),
                               open_reason=open_reason)

        vol_open = sum(d["volume"] for d in opens) + sum(d["volume"] for d in inouts)
        vol_closed = sum(d["volume"] for d in closes)
        if closes and abs(vol_closed - vol_open) > 1e-9:
            diagnostics["volume_mismatch"].append(
                {"position_id": pos_id, "opened": vol_open, "closed": vol_closed})
        if not closes:
            diagnostics["positions_without_exit_deal"].append(pos_id)

        direction = 1 if entry["type"] == 0 else -1  # 0=buy
        side = "long" if direction == 1 else "short"

        gross = sum(d["profit"] for d in ds)
        comm = sum(d["commission"] for d in ds)
        swap = sum(d["swap"] for d in ds)
        fee = sum(d["fee"] for d in ds)
        realized_net = gross + comm + swap + fee

        exit_vwap = None
        if closes and vol_closed > 0:
            exit_vwap = sum(d["price"] * d["volume"] for d in closes) / vol_closed

        # ---- money-per-price-unit, solved from the position's own realized P&L -------------------
        upu, upu_basis = _usd_per_price_unit(entry, closes, direction, spec)

        # ---- risk and R --------------------------------------------------------------------------
        o = order_by_position.get(pos_id) or order_by_ticket.get(entry.get("order") or -1)
        # MT5 writes 0.0 for "no stop set", so 0.0 genuinely means absent here and `or None` is
        # correct for sl/tp. Everything downstream uses `is not None`, so a legitimately zero risk or
        # R can never be silently relabelled `unavailable` -- which an earlier revision did.
        sl = (o or {}).get("sl") or None
        tp = (o or {}).get("tp") or None
        risk_dist = abs(entry["price"] - sl) if sl is not None else None
        risk_usd = None
        if risk_dist is not None and upu is not None and risk_dist > 0 and vol_open > 0:
            risk_usd = risk_dist * vol_open * upu
        r_basis = "broker_order_sl" if risk_usd is not None else "unavailable"
        realized_r = (realized_net / risk_usd) if risk_usd else None
        # Gross R excludes commission/swap/fee. Reporting both stops "worse than -1 R" being read as
        # stop slippage when it is mostly commission.
        gross_r = (gross / risk_usd) if risk_usd else None
        cost_r = ((comm + swap + fee) / risk_usd) if risk_usd else None

        # ---- time --------------------------------------------------------------------------------
        e_utc = broker_epoch_to_utc(entry["time"], rule)
        e_brk = e_utc + timedelta(seconds=offset_seconds_at_utc(e_utc, rule))
        if closes:
            x_utc = broker_epoch_to_utc(closes[-1]["time"], rule)
            x_brk = x_utc + timedelta(seconds=offset_seconds_at_utc(x_utc, rule))
        else:
            x_utc = x_brk = None

        row = {
            "schema_version": SCHEMA_VERSION,
            "account": acct.key,
            "account_login": acct.login,
            "broker_server": acct.server,
            "position_id": pos_id,
            "entry_deal_ticket": entry["ticket"],
            "exit_deal_tickets": [d["ticket"] for d in closes],
            "entry_order_ticket": (o or {}).get("ticket"),
            "magic": entry.get("magic", 0),

            **{k: cls[k] for k in (
                "comment_raw", "sleeve_tag", "sleeve_id", "sleeve_resolution", "sleeve_candidates",
                "sleeve_family", "stack_era", "sleeve_confidence", "sleeve_status", "sleeve_cluster")},

            "broker_symbol": sym,
            "canonical_symbol": BROKER_TO_CANONICAL.get(sym),
            "symbol_map_status": "mapped" if sym in BROKER_TO_CANONICAL else "unmapped",
            "side": side,
            "volume": round(vol_open, 6),
            "volume_closed": round(vol_closed, 6),
            "trade_contract_size": spec.get("trade_contract_size"),

            "entry_time_broker": e_brk.replace(tzinfo=None).isoformat(),
            "entry_time_utc": e_utc.isoformat(),
            "exit_time_broker": x_brk.replace(tzinfo=None).isoformat() if x_brk else None,
            "exit_time_utc": x_utc.isoformat() if x_utc else None,
            "holding_seconds": int((x_utc - e_utc).total_seconds()) if x_utc else None,
            "day_key_utc": e_utc.date().isoformat(),
            "day_key_broker_server": e_brk.date().isoformat(),
            "day_key_ftmo_reset": _reset_day_key(e_utc, acct.daily_reset_rule),
            "broker_clock_offset_hours": offset_seconds_at_utc(e_utc, rule) / 3600.0,
            "broker_clock_rule": rule.name,

            "entry_price": entry["price"],
            "exit_price_vwap": exit_vwap,
            "gross_profit": round(gross, 6),
            "commission": round(comm, 6),
            "swap": round(swap, 6),
            "fee": round(fee, 6),
            "realized_net": round(realized_net, 6),
            "pct_of_initial_balance": realized_net / acct.initial_balance,

            "sl_price": sl,
            "tp_price": tp,
            "risk_distance_price": risk_dist,
            "usd_per_price_unit_per_lot": upu,
            "r_money_basis": upu_basis,
            "risk_at_entry_usd": round(risk_usd, 6) if risk_usd else None,
            "risk_pct_of_balance": (risk_usd / acct.initial_balance) if risk_usd else None,
            "realized_r": round(realized_r, 6) if realized_r is not None else None,
            "gross_r": round(gross_r, 6) if gross_r is not None else None,
            "cost_r": round(cost_r, 6) if cost_r is not None else None,
            "r_basis": r_basis,

            "open_reason": open_reason,
            "close_reason": DEAL_REASON.get(closes[-1]["reason"]) if closes else None,
            "close_reasons_all": sorted({DEAL_REASON.get(d["reason"]) for d in closes}),
            "hand_closed": any(DEAL_REASON.get(d["reason"]) in ("mobile", "web", "client")
                               for d in closes),
            "n_close_deals": len(closes),
            "partial_close": len(closes) > 1,
        }
        row["in_w7_denominator"] = row["stack_era"] == "w7_book"
        row["denominator_exclusion_reason"] = (
            None if row["in_w7_denominator"] else f"stack_era={row['stack_era']}")
        rows.append(row)

    rows.sort(key=lambda r: (r["entry_time_utc"], r["position_id"]))

    recon = {
        "initial_balance_deal": sum(d["profit"] for d in balance_ops),
        "balance_ops": [
            {"comment": d["comment"], "type": d["type"], "profit": d["profit"],
             "time_utc": broker_epoch_to_utc(d["time"], rule).isoformat()}
            for d in balance_ops
        ],
        "sum_realized_net_all_rows": round(sum(r["realized_net"] for r in rows), 6),
        "balance_ops_carrying_a_symbol": [
            {"ticket": d["ticket"], "type": d["type"], "symbol": d["symbol"],
             "comment": d.get("comment"), "profit": d["profit"]} for d in stray
        ],
        "n_deals_total": len(deals),
        "n_deals_trade": len(trade_deals),
        "n_positions": len(rows),
        "diagnostics": diagnostics,
    }
    recon["reconstructed_balance"] = round(
        recon["initial_balance_deal"] + recon["sum_realized_net_all_rows"], 6)
    recon["broker_reported_balance"] = acct.final_balance
    recon["residual"] = round(recon["reconstructed_balance"] - acct.final_balance, 6)
    return rows, recon


def _usd_per_price_unit(entry: dict, closes: list[dict], direction: int,
                        spec: dict) -> tuple[float | None, str]:
    """Solve USD-per-price-unit-per-lot from realized P&L; fall back to the symbol spec."""
    num = 0.0
    den = 0.0
    for d in closes:
        dp = (d["price"] - entry["price"]) * direction
        if abs(dp) < 1e-12 or d["volume"] <= 0:
            continue
        f = d["profit"] / (dp * d["volume"])
        if f > 0 and math.isfinite(f):
            num += f * d["volume"]
            den += d["volume"]
    if den > 0:
        return round(num / den, 8), "solved_from_realized_pnl"
    tv, ts = spec.get("trade_tick_value"), spec.get("trade_tick_size")
    if tv and ts:
        return round(tv / ts, 8), "symbol_spec_tick_value"
    return None, "unavailable"


def _reset_day_key(instant_utc: datetime, rule_name: str | None) -> str | None:
    """Day key under the FIRM's daily-loss reset calendar. None when the firm resets at server time."""
    if not rule_name:
        return None
    from src.utils.broker_clock import daily_reset_offset_hours
    off = daily_reset_offset_hours(instant_utc, rule_name)
    if off is None:
        return None
    return (instant_utc + timedelta(hours=off)).date().isoformat()


# --------------------------------------------------------------------------------------------------
# Era windows and the denominator
# --------------------------------------------------------------------------------------------------


def era_windows(rows: list[dict], acct: AccountSpec) -> dict:
    """Establish each era's window and the balance at its boundaries.

    The equity curve is ordered by EXIT time, because realized money lands when a position closes.
    An era's realized result is the sum of its own positions' `realized_net` -- which is exactly the
    change in balance attributable to that era, and is independent of any date guess.
    """
    # Enumerate the eras PRESENT, never a hardcoded list. A hardcoded list silently dropped the two
    # untagged FTMO positions worth +13,166.69 from this summary, which is exactly the kind of
    # quiet omission this receipt is supposed to make impossible.
    out: dict[str, Any] = {}
    for era in sorted({r["stack_era"] for r in rows}):
        sub = [r for r in rows if r["stack_era"] == era]
        if not sub:
            continue
        net = sum(r["realized_net"] for r in sub)
        out[era] = {
            "n_positions": len(sub),
            "first_entry_utc": min(r["entry_time_utc"] for r in sub),
            "last_entry_utc": max(r["entry_time_utc"] for r in sub),
            "last_exit_utc": max((r["exit_time_utc"] for r in sub if r["exit_time_utc"]),
                                 default=None),
            "realized_net": round(net, 2),
            "pct_of_initial_balance": round(100.0 * net / acct.initial_balance, 4),
            "trading_days_utc": len({r["day_key_utc"] for r in sub}),
        }
    # Prove the eras partition every row and every dollar.
    out["_partition_check"] = {
        "n_positions_total": len(rows),
        "n_positions_in_eras": sum(v["n_positions"] for k, v in out.items()
                                   if not k.startswith("_")),
        "sum_realized_net_in_eras": round(sum(v["realized_net"] for k, v in out.items()
                                              if not k.startswith("_")), 2),
        "sum_realized_net_all_rows": round(sum(r["realized_net"] for r in rows), 2),
        "initial_balance_plus_eras": round(
            acct.initial_balance + sum(v["realized_net"] for k, v in out.items()
                                       if not k.startswith("_")), 2),
        "broker_reported_balance": acct.final_balance,
    }
    out["_partition_check"]["residual"] = round(
        out["_partition_check"]["initial_balance_plus_eras"] - acct.final_balance, 2)
    return out


def daily_curve(rows: list[dict], day_key: str) -> list[dict]:
    """Realized P&L per day, keyed by the CLOSE day (money lands at close)."""
    per = defaultdict(lambda: {"realized_net": 0.0, "n_closed": 0})
    for r in rows:
        if not r["exit_time_utc"]:
            continue
        x = datetime.fromisoformat(r["exit_time_utc"])
        if day_key == "day_key_utc":
            k = x.date().isoformat()
        elif day_key == "day_key_broker_server":
            # Resolve the offset at the EXIT instant, not the entry's. Nothing in this window spans a
            # DST transition, so this moves no row today -- but a March/November window would.
            rule = resolve_rule(r["broker_server"])
            k = (x + timedelta(seconds=offset_seconds_at_utc(x, rule))).date().isoformat()
        else:
            k = r[day_key] or x.date().isoformat()
        per[k]["realized_net"] += r["realized_net"]
        per[k]["n_closed"] += 1
    return [{"day": k, "realized_net": round(v["realized_net"], 2), "n_closed": v["n_closed"]}
            for k, v in sorted(per.items())]


# --------------------------------------------------------------------------------------------------
# Attribution
# --------------------------------------------------------------------------------------------------


def attribute(rows: list[dict], acct: AccountSpec, books: dict) -> dict:
    w7 = [r for r in rows if r["in_w7_denominator"]]
    total = sum(r["realized_net"] for r in w7)

    def group(keyfn) -> list[dict]:
        g = defaultdict(list)
        for r in w7:
            g[keyfn(r)].append(r)
        out = []
        gross_losses = sum(x["realized_net"] for x in w7 if x["realized_net"] < 0)
        for k, sub in g.items():
            net = sum(x["realized_net"] for x in sub)
            rs = [x["realized_r"] for x in sub if x["realized_r"] is not None]
            grs = [x["gross_r"] for x in sub if x["gross_r"] is not None]
            crs = [x["cost_r"] for x in sub if x["cost_r"] is not None]
            wins = [x for x in sub if x["realized_net"] > 0]
            sub_loss = sum(x["realized_net"] for x in sub if x["realized_net"] < 0)
            out.append({
                "key": k,
                "n": len(sub),
                "realized_net": round(net, 2),
                "pct_of_initial": round(100.0 * net / acct.initial_balance, 4),
                # Two bases, because they differ a lot and the net one is fragile: a component's
                # share of a NET total can be inflated by another component's winners. redacted_account's
                # candidate book is 90.4% of the net loss but 73.4% of gross losses.
                "share_of_net_window_loss": (round(net / total, 4) if total else None),
                "share_of_gross_losses": (round(sub_loss / gross_losses, 4)
                                          if gross_losses else None),
                "mean_r": round(statistics.fmean(rs), 4) if rs else None,
                "mean_gross_r": round(statistics.fmean(grs), 4) if grs else None,
                "mean_cost_r": round(statistics.fmean(crs), 4) if crs else None,
                "sum_r": round(sum(rs), 4) if rs else None,
                "n_with_r": len(rs),
                "win_rate": round(len(wins) / len(sub), 4),
                "commission": round(sum(x["commission"] for x in sub), 2),
                "swap": round(sum(x["swap"] for x in sub), 2),
                "n_hand_closed": sum(1 for x in sub if x["hand_closed"]),
                "hand_closed_net": round(sum(x["realized_net"] for x in sub if x["hand_closed"]), 2),
            })
        return sorted(out, key=lambda d: d["realized_net"])

    risks = [r["risk_pct_of_balance"] for r in w7 if r["risk_pct_of_balance"] is not None]
    return {
        "w7_n_positions": len(w7),
        "w7_realized_net": round(total, 2),
        "w7_pct_of_initial": round(100.0 * total / acct.initial_balance, 4),
        "by_sleeve_family": group(lambda r: r["sleeve_family"]),
        "by_sleeve": group(lambda r: r["sleeve_id"] or f"UNRESOLVED:{r['sleeve_tag']}"),
        "by_symbol": group(lambda r: r["canonical_symbol"] or r["broker_symbol"]),
        "by_cluster": group(lambda r: r["sleeve_cluster"] or "unknown"),
        "by_side": group(lambda r: r["side"]),
        "by_close_reason": group(lambda r: r["close_reason"] or "open"),
        "realized_dial": {
            "n_with_risk": len(risks),
            "n_without_risk": len(w7) - len(risks),
            "mean_risk_pct": round(100.0 * statistics.fmean(risks), 4) if risks else None,
            "median_risk_pct": round(100.0 * statistics.median(risks), 4) if risks else None,
            "p90_risk_pct": (round(100.0 * sorted(risks)[int(0.9 * (len(risks) - 1))], 4)
                             if risks else None),
            "max_risk_pct": round(100.0 * max(risks), 4) if risks else None,
            # Deliberately NOT printed next to a per-trade figure as if comparable. The 2.00% is
            # base_risk_per_unit; the per-trade design target is base * conf / n. See unit_risk.
            "base_risk_per_unit_pct": 100.0 * (books["allocation_profiles"]
                                               .get(books["profile"], {})
                                               .get("risk_per_unit_A", float("nan"))),
            "compare_against": "unit_risk.designed_vs_observed_units, not base_risk_per_unit_pct",
        },
        "hand_intervention": {
            "n_hand_closed": sum(1 for r in w7 if r["hand_closed"]),
            "hand_closed_net": round(sum(r["realized_net"] for r in w7 if r["hand_closed"]), 2),
            "positions": [
                {"position_id": r["position_id"], "sleeve_id": r["sleeve_id"],
                 "broker_symbol": r["broker_symbol"], "realized_net": r["realized_net"],
                 "close_reasons": r["close_reasons_all"]}
                for r in w7 if r["hand_closed"]
            ],
            "note": (
                "A hand-closed W7 position's result is a human decision, not the sleeve's. Any "
                "'sleeve X returned +R' statement must flag these."
            ),
        },
        "costs": {
            "commission": round(sum(r["commission"] for r in w7), 2),
            "swap": round(sum(r["swap"] for r in w7), 2),
            "fee": round(sum(r["fee"] for r in w7), 2),
            "gross_profit": round(sum(r["gross_profit"] for r in w7), 2),
            "cost_pct_of_initial": round(
                100.0 * sum(r["commission"] + r["swap"] + r["fee"] for r in w7)
                / acct.initial_balance, 4),
        },
    }


def unit_risk_analysis(rows: list[dict], acct: AccountSpec) -> dict:
    """Aggregate per-trade risk into per-UNIT risk, which is what the dial actually governs.

    `clean3_w7_ceiling_nom2p00` sets `risk_per_unit = 0.020`. A "unit" is one (sleeve, decision-day)
    correlated risk unit, which the validated model SPLITS across the symbols that fired that day
    (`agent_config.yaml:1355-1368`: "validation ... collapses same-day same-cluster fires into ONE
    unit SPLIT across the symbols -> it DOES trade both, at reduced size"). So comparing a single
    trade's risk to 2.0% understates the dial by the split factor; the honest comparison is
    Σ risk over a (sleeve, day) against 2.0%, and Σ risk over a (cluster, day) against the
    one-unit-per-cluster-per-day envelope the 2.0% dial was certified on.
    """
    w7 = [r for r in rows if r["in_w7_denominator"] and r["risk_pct_of_balance"] is not None]

    def agg(keyfn) -> list[dict]:
        g = defaultdict(list)
        for r in w7:
            g[keyfn(r)].append(r)
        out = []
        for k, sub in g.items():
            tot = sum(x["risk_pct_of_balance"] for x in sub)
            out.append({
                "key": list(k) if isinstance(k, tuple) else k,
                "n_trades": len(sub),
                "risk_pct": round(100.0 * tot, 4),
                "realized_net": round(sum(x["realized_net"] for x in sub), 2),
            })
        return sorted(out, key=lambda d: -d["risk_pct"])

    per_sleeve_day = agg(lambda r: (r["sleeve_id"] or r["sleeve_tag"] or "?", r["day_key_utc"]))
    per_cluster_day = agg(lambda r: (r["sleeve_cluster"] or "unknown", r["day_key_utc"]))
    per_day = agg(lambda r: r["day_key_utc"])

    def stats(items: list[dict], field: str = "risk_pct") -> dict:
        vals = [i[field] for i in items]
        if not vals:
            return {}
        return {
            "n": len(vals),
            "mean_pct": round(statistics.fmean(vals), 4),
            "median_pct": round(statistics.median(vals), 4),
            "max_pct": round(max(vals), 4),
            "p90_pct": round(sorted(vals)[int(0.9 * (len(vals) - 1))], 4),
        }

    # THE CORRECT DIAL COMPARISON. `admission.py:1192-1193` is
    #   unit_risk = base_risk_per_unit * conf * derisk_mult ;  per_trade = unit_risk / n
    # and the docstring at :1038-1040 states the invariant: "the correlated unit's worst-case
    # simultaneous stop = base_risk_per_unit * conf".
    #
    # So 2.00% is NOT the risk any unit expresses -- it is the base a CONFIDENCE-1.00 sleeve would
    # express. Comparing a per-trade figure to 2.00% compares incommensurable quantities, and an
    # earlier revision of this script did exactly that and reported a nonexistent "10-15x under-sizing
    # defect". The comparator is `base * conf` per unit, and `base * conf / n` per trade.
    base = 0.020
    designed = []
    for (sleeve, day), sub in _group(w7, lambda r: (r["sleeve_id"] or r["sleeve_tag"] or "?",
                                                    r["day_key_utc"])).items():
        conf = next((r["sleeve_confidence"] for r in sub if r["sleeve_confidence"] is not None), None)
        if conf is None:
            continue
        obs = sum(r["risk_pct_of_balance"] for r in sub)
        des = base * conf
        designed.append({
            "sleeve": sleeve, "day": day, "n_trades": len(sub), "confidence": conf,
            "designed_unit_risk_pct": round(100.0 * des, 4),
            "observed_unit_risk_pct": round(100.0 * obs, 4),
            "observed_over_designed": round(obs / des, 4) if des else None,
            "designed_per_trade_pct": round(100.0 * des / len(sub), 4),
            "realized_net": round(sum(r["realized_net"] for r in sub), 2),
        })
    ratios = [d["observed_over_designed"] for d in designed if d["observed_over_designed"]]
    return {
        "dial_note": (
            "base_risk_per_unit for clean3_w7_ceiling_nom2p00 is 0.020, but a unit's worst-case "
            "simultaneous stop is base * sleeve_confidence (admission.py:1049-1051, :1192-1193). The "
            "2.00% figure is only reachable by a confidence-1.00 sleeve -- metals_core -- which "
            "placed nothing in this window. Compare observed_unit_risk_pct against "
            "designed_unit_risk_pct, NOT against 2.00%."
        ),
        "base_risk_per_unit_pct": 100.0 * base,
        "configured_gross_open_cap_pct": 4.0,
        "max_confidence_that_traded": max((r["sleeve_confidence"] for r in w7
                                           if r["sleeve_confidence"] is not None), default=None),
        "per_trade": stats([{"risk_pct": 100.0 * r["risk_pct_of_balance"]} for r in w7]),
        "per_sleeve_day": stats(per_sleeve_day),
        "per_cluster_day": stats(per_cluster_day),
        "per_day_total": stats(per_day),
        "observed_over_designed_unit_risk": {
            "n_units": len(ratios),
            "mean": round(statistics.fmean(ratios), 4) if ratios else None,
            "median": round(statistics.median(ratios), 4) if ratios else None,
            "min": round(min(ratios), 4) if ratios else None,
            "max": round(max(ratios), 4) if ratios else None,
            "n_units_over_designed": sum(1 for r in ratios if r > 1.0),
            "interpretation": (
                "<1 means the de-risk overlays shrank the unit below its design. >1 means kelly_lite "
                "sized it up on a high-breadth day."
            ),
        },
        "designed_vs_observed_units": sorted(designed, key=lambda d: -d["observed_unit_risk_pct"]),
        "per_day_total_series": sorted(per_day, key=lambda d: d["key"]),
        "n_units_at_or_over_base_2pct": sum(1 for d in per_sleeve_day if d["risk_pct"] >= 2.0),
        "n_days_at_or_over_gross_cap": sum(1 for d in per_day if d["risk_pct"] >= 4.0),
    }


def _group(rows: list[dict], keyfn) -> dict:
    g: dict = defaultdict(list)
    for r in rows:
        g[keyfn(r)].append(r)
    return g


def drawdown_analysis(rows: list[dict], acct: AccountSpec) -> dict:
    """Realized daily P&L and running drawdown for the W7 era, on each account's OWN reset calendar.

    The governor's walls are: soft daily stop -3%, hard daily -5% (the prop-fatal one), max-DD -10%
    from the STATIC initial balance. CYCLE62's CORE8_DEPLOYED+smooth cell claims worst_day -4.695%
    and daily_breach_pct 0.0. This measures the realized equivalents.
    """
    w7 = [r for r in rows if r["in_w7_denominator"] and r["exit_time_utc"]]
    reset_rule = acct.daily_reset_rule

    def day_of(r: dict) -> str:
        x = datetime.fromisoformat(r["exit_time_utc"])
        if reset_rule:
            from src.utils.broker_clock import daily_reset_offset_hours
            off = daily_reset_offset_hours(x, reset_rule)
            return (x + timedelta(hours=off or 0.0)).date().isoformat()
        # redacted_account: 00:00 server time
        return (x + timedelta(hours=r["broker_clock_offset_hours"])).date().isoformat()

    per = defaultdict(float)
    for r in w7:
        per[day_of(r)] += r["realized_net"]

    # Equity at the start of the W7 era = initial balance + everything realized before it.
    pre = sum(r["realized_net"] for r in rows
              if not r["in_w7_denominator"] and r["exit_time_utc"]
              and r["exit_time_utc"] < min(x["entry_time_utc"] for x in w7))
    start_equity = acct.initial_balance + pre

    eq = start_equity
    peak = start_equity
    series = []
    worst_day_pct = 0.0
    worst_dd_from_start = 0.0
    worst_dd_from_peak = 0.0
    for day in sorted(per):
        pnl = per[day]
        day_pct = 100.0 * pnl / eq          # daily loss is vs the day's OPENING equity
        eq += pnl
        peak = max(peak, eq)
        dd_start = 100.0 * (eq - acct.initial_balance) / acct.initial_balance
        dd_peak = 100.0 * (eq - peak) / peak
        worst_day_pct = min(worst_day_pct, day_pct)
        worst_dd_from_start = min(worst_dd_from_start, dd_start)
        worst_dd_from_peak = min(worst_dd_from_peak, dd_peak)
        series.append({
            "day": day, "realized_net": round(pnl, 2), "day_pct_of_open_equity": round(day_pct, 4),
            "equity_close": round(eq, 2), "pct_from_initial_balance": round(dd_start, 4),
            "pct_from_peak": round(dd_peak, 4),
        })

    # The TRUE peak-to-trough on the account, deal by deal, over ALL eras. This is the number a prop
    # max-drawdown rule bites on, and it is deeper than any era sum: the daily W7-only series above
    # excludes pre-W7 positions that happened to CLOSE inside the window, so it is a synthetic
    # "W7-only" curve, not the account's.
    all_closes = sorted(
        ((r["exit_time_utc"], r["realized_net"]) for r in rows if r["exit_time_utc"]),
        key=lambda t: t[0])
    bal = acct.initial_balance
    acct_peak = bal
    trough = bal
    trough_at = None
    worst_from_peak = 0.0
    for ts, pnl in all_closes:
        bal += pnl
        acct_peak = max(acct_peak, bal)
        if bal < trough:
            trough, trough_at = bal, ts
        worst_from_peak = min(worst_from_peak, 100.0 * (bal - acct_peak) / acct_peak)

    return {
        "account_true_drawdown": {
            "note": (
                "Deal-ordered over EVERY era, which is what a prop max-DD rule measures. Deeper than "
                "the era sums and deeper than the W7-only series below."
            ),
            "peak_balance": round(acct_peak, 2),
            "trough_balance": round(trough, 2),
            "trough_at_utc": trough_at,
            "trough_pct_from_initial_balance": round(
                100.0 * (trough - acct.initial_balance) / acct.initial_balance, 4),
            "worst_pct_from_running_peak": round(worst_from_peak, 4),
        },
        "day_boundary": reset_rule or "server_midnight",
        "day_boundary_note": (
            "FTMO's daily-loss window resets 00:00 CE(S)T; redacted_account's at 00:00 server time. "
            "These are DIFFERENT clocks and the governor hardcodes neither correctly -- see "
            "agent_config.yaml governor_daily_reset_offset_hours: 3.0."
        ),
        "w7_start_equity": round(start_equity, 2),
        "w7_end_equity": round(eq, 2),
        "n_days": len(series),
        "worst_day_pct_of_open_equity": round(worst_day_pct, 4),
        "worst_drawdown_pct_from_initial_balance": round(worst_dd_from_start, 4),
        "worst_drawdown_pct_from_peak": round(worst_dd_from_peak, 4),
        "governor_soft_daily_stop_pct": -3.0,
        "governor_hard_daily_pct": -5.0,
        "cycle62_claimed_worst_day_pct": -4.695,
        "days_breaching_soft_stop": [s["day"] for s in series
                                     if s["day_pct_of_open_equity"] <= -3.0],
        "days_breaching_hard_daily": [s["day"] for s in series
                                      if s["day_pct_of_open_equity"] <= -5.0],
        "series": series,
    }


def cross_broker_pairing(all_rows: list[dict]) -> dict:
    """Axis (d): the SAME signal on both accounts, paired, so the asymmetry is isolated.

    A pair is (sleeve_id, canonical_symbol, side, day_key_utc) present on both accounts. That is the
    tightest identity available -- the two book workers are independent processes running the same
    book, so a signal that fired on one should fire on the other.
    """
    w7 = [r for r in all_rows if r["in_w7_denominator"]]
    key = lambda r: (r["sleeve_id"] or r["sleeve_tag"], r["canonical_symbol"], r["side"],
                     r["day_key_utc"])
    by_acct: dict[str, dict] = {"ftmo": {}, "redacted_account": {}}
    for r in w7:
        by_acct[r["account"]].setdefault(key(r), []).append(r)

    common = sorted(set(by_acct["ftmo"]) & set(by_acct["redacted_account"]))
    only_f = sorted(set(by_acct["ftmo"]) - set(by_acct["redacted_account"]))
    only_n = sorted(set(by_acct["redacted_account"]) - set(by_acct["ftmo"]))

    pairs = []
    for k in common:
        f = by_acct["ftmo"][k]
        n = by_acct["redacted_account"][k]
        fn_net = sum(x["realized_net"] for x in n)
        ft_net = sum(x["realized_net"] for x in f)
        f_risk = sum(x["risk_at_entry_usd"] or 0.0 for x in f)
        n_risk = sum(x["risk_at_entry_usd"] or 0.0 for x in n)
        f_r = [x["realized_r"] for x in f if x["realized_r"] is not None]
        n_r = [x["realized_r"] for x in n if x["realized_r"] is not None]
        pairs.append({
            "sleeve": k[0], "symbol": k[1], "side": k[2], "day": k[3],
            "ftmo_net": round(ft_net, 2), "fn_net": round(fn_net, 2),
            "net_delta_fn_minus_ftmo": round(fn_net - ft_net, 2),
            "ftmo_risk_usd": round(f_risk, 2), "fn_risk_usd": round(n_risk, 2),
            "risk_ratio_fn_over_ftmo": round(n_risk / f_risk, 4) if f_risk else None,
            "ftmo_mean_r": round(statistics.fmean(f_r), 4) if f_r else None,
            "fn_mean_r": round(statistics.fmean(n_r), 4) if n_r else None,
            "ftmo_vol": round(sum(x["volume"] for x in f), 4),
            "fn_vol": round(sum(x["volume"] for x in n), 4),
            "ftmo_entry": f[0]["entry_price"], "fn_entry": n[0]["entry_price"],
            "ftmo_contract_size": f[0]["trade_contract_size"],
            "fn_contract_size": n[0]["trade_contract_size"],
            "contract_size_equal": (f[0]["trade_contract_size"] == n[0]["trade_contract_size"]),
        })
    pairs.sort(key=lambda p: p["net_delta_fn_minus_ftmo"])

    ratios = [p["risk_ratio_fn_over_ftmo"] for p in pairs if p["risk_ratio_fn_over_ftmo"]]
    paired_ft = sum(p["ftmo_net"] for p in pairs)
    paired_fn = sum(p["fn_net"] for p in pairs)
    return {
        "n_paired_signals": len(pairs),
        "n_ftmo_only": len(only_f),
        "n_redacted_account_only": len(only_n),
        "paired_ftmo_net": round(paired_ft, 2),
        "paired_fn_net": round(paired_fn, 2),
        "paired_delta_fn_minus_ftmo": round(paired_fn - paired_ft, 2),
        "unpaired_ftmo_net": round(
            sum(r["realized_net"] for k in only_f for r in by_acct["ftmo"][k]), 2),
        "unpaired_fn_net": round(
            sum(r["realized_net"] for k in only_n for r in by_acct["redacted_account"][k]), 2),
        "risk_ratio_fn_over_ftmo": {
            "n": len(ratios),
            "mean": round(statistics.fmean(ratios), 4) if ratios else None,
            "median": round(statistics.median(ratios), 4) if ratios else None,
        },
        "n_pairs_with_unequal_contract_size": sum(1 for p in pairs
                                                  if p["contract_size_equal"] is False),
        "ftmo_only_signals": [list(k) for k in only_f],
        "redacted_account_only_signals": [list(k) for k in only_n],
        "pairs": pairs,
    }


def power_arithmetic(all_rows: list[dict]) -> dict:
    """Is the observed W7 result distinguishable from the validated model at this sample size?

    CYCLE62's own per-unit daily R distribution for the deployed book is
    `series.core8 = {n: 1679, mean: 0.08151, std: 0.65754}` at `eff_pct 1.729`. That is the
    distribution the 2.0% dial was certified on. The test: given the number of live trading days
    observed, how far is the realized account return from that model's expectation, in sigmas?

    Stated as arithmetic, not as a verdict. A p-value at n=14 is a weak instrument and the receipt
    says so.
    """
    cyc_mean_r = 0.08151      # per unit-day, CYCLE62 series.core8.mean
    cyc_std_r = 0.65754       # per unit-day
    eff_pct = 1.729           # CYCLE62 CORE8_DEPLOYED eff_pct (post half-Kelly)

    out = {
        "source": "CYCLE62_CORE8_REVALIDATION.json (origin/live-handoff-2026-06-15@98da29d2a)",
        "model_mean_r_per_unit_day": cyc_mean_r,
        "model_std_r_per_unit_day": cyc_std_r,
        "model_eff_pct_per_unit": eff_pct,
        "caveat": (
            "The model's unit is a per-unit DAY at eff 1.729% of balance. The live book deployed far "
            "less risk than that per day (see unit_risk), so this comparison is an UPPER bound on "
            "the model's expected return and therefore a LOWER bound on the shortfall. Reported "
            "both ways below."
        ),
        "accounts": {},
    }
    for acct in ACCOUNTS:
        rows = [r for r in all_rows if r["account"] == acct.key and r["in_w7_denominator"]]
        if not rows:
            continue
        days = sorted({r["day_key_utc"] for r in rows})
        n = len(days)
        net_pct = 100.0 * sum(r["realized_net"] for r in rows) / acct.initial_balance

        # (i) model at its own certified risk: one unit-day per trading day
        exp_pct = n * cyc_mean_r * eff_pct
        sd_pct = math.sqrt(n) * cyc_std_r * eff_pct
        z_model = (net_pct - exp_pct) / sd_pct if sd_pct else None

        # (ii) model rescaled to the risk the book ACTUALLY deployed per day
        risks = [r["risk_pct_of_balance"] for r in rows if r["risk_pct_of_balance"] is not None]
        per_day_risk = defaultdict(float)
        for r in rows:
            if r["risk_pct_of_balance"] is not None:
                per_day_risk[r["day_key_utc"]] += r["risk_pct_of_balance"]
        mean_day_risk_pct = 100.0 * statistics.fmean(per_day_risk.values()) if per_day_risk else 0.0
        scale = mean_day_risk_pct / eff_pct if eff_pct else 0.0
        exp_pct_scaled = exp_pct * scale
        sd_pct_scaled = sd_pct * scale
        z_scaled = (net_pct - exp_pct_scaled) / sd_pct_scaled if sd_pct_scaled else None

        # realized per-trade R vs the model's per-unit-day R (different units; reported, not tested)
        rs = [r["realized_r"] for r in rows if r["realized_r"] is not None]

        out["accounts"][acct.key] = {
            "n_trading_days": n,
            "realized_pct_of_initial": round(net_pct, 4),
            "mean_deployed_risk_per_day_pct": round(mean_day_risk_pct, 4),
            "deployed_vs_certified_risk_ratio": round(scale, 4),
            "model_at_certified_risk": {
                "expected_pct": round(exp_pct, 4),
                "sd_pct": round(sd_pct, 4),
                "z": round(z_model, 3) if z_model is not None else None,
                "one_sided_p": round(_norm_cdf(z_model), 5) if z_model is not None else None,
            },
            "model_rescaled_to_deployed_risk": {
                "expected_pct": round(exp_pct_scaled, 4),
                "sd_pct": round(sd_pct_scaled, 4),
                "z": round(z_scaled, 3) if z_scaled is not None else None,
                "one_sided_p": round(_norm_cdf(z_scaled), 5) if z_scaled is not None else None,
            },
            "realized_mean_r_per_trade": round(statistics.fmean(rs), 4) if rs else None,
            "realized_sum_r": round(sum(rs), 4) if rs else None,
            "n_trades_with_r": len(rs),
            "days_to_target_median_model": {"redacted_account": 64, "ftmo": 110},
        }
    return out


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# --------------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export-root", type=Path, default=DEFAULT_EXPORT_ROOT)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    books = load_books()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Derive the W7 window from the data before building any row, so the era classifier never leans
    # on a hardcoded date.
    api = args.export_root / "09_mt5_api"
    deals_by_account = {a.key: read_jsonl(api / a.deals_file) for a in ACCOUNTS}
    rules_by_account = {a.key: resolve_rule(a.server) for a in ACCOUNTS}
    window = derive_w7_window(deals_by_account, rules_by_account)

    all_rows: list[dict] = []
    manifest: dict[str, Any] = {
        "schema": "gtos.w7_live_forensics.manifest.v1",
        "row_schema_version": SCHEMA_VERSION,
        "generated_by": "scripts/w7_live_forensics.py",
        "source_export": str(args.export_root),
        "w7_window_derived": {"first_entry_day_utc": window[0], "last_entry_day_utc": window[1]},
        "source_note": (
            "Broker truth is primary: 09_mt5_api/{ftmo,redacted_account}_history_{deals,orders}_get.jsonl. "
            "The GTOS execution ledgers died 2026-07-02 (V3) and never captured a fill (V2)."
        ),
        "live_books": {
            "profile": books["profile"],
            "derisk_mode": books["derisk_mode"],
            "include_clean3": books["include_clean3"],
            "core8": sorted(books["core8"]),
            "candidate_live": books["candidate_live"],
            "market_expansion_policy": books["market_expansion_policy"],
            "market_expansion_live": books["market_expansion_live"],
            "total_live_sleeves": (len(books["core8"]) + len(books["candidate_live"])
                                  + len(books["market_expansion_live"])),
        },
        "accounts": {},
    }

    for acct in ACCOUNTS:
        rows, recon = build_rows(acct, args.export_root, books, window)
        all_rows.extend(rows)
        manifest["accounts"][acct.key] = {
            "login": acct.login,
            "server": acct.server,
            "daily_reset_rule": acct.daily_reset_rule or "server_midnight",
            "reconciliation": recon,
            "eras": era_windows(rows, acct),
            "attribution": attribute(rows, acct, books),
            "daily_realized_by_close_day_utc": daily_curve(
                [r for r in rows if r["in_w7_denominator"]], "day_key_utc"),
            "sleeve_resolution_counts": dict(Counter(r["sleeve_resolution"] for r in rows)),
            "unmapped_symbols": sorted({r["broker_symbol"] for r in rows
                                        if r["symbol_map_status"] == "unmapped"}),
            "unit_risk": unit_risk_analysis(rows, acct),
            "drawdown": drawdown_analysis(rows, acct),
        }

    manifest["cross_broker_pairing"] = cross_broker_pairing(all_rows)
    manifest["power_arithmetic"] = power_arithmetic(all_rows)

    rows_path = args.out_dir / "LIVE_TRADE_ROWS.jsonl"
    with io.open(rows_path, "w", encoding="utf-8") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")

    manifest["n_rows_total"] = len(all_rows)
    manifest["n_rows_w7"] = sum(1 for r in all_rows if r["in_w7_denominator"])
    man_path = args.out_dir / "LIVE_TRADE_ROWS_MANIFEST.json"
    with io.open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")

    print(f"wrote {rows_path} ({len(all_rows)} rows, {manifest['n_rows_w7']} W7)")
    print(f"wrote {man_path}")
    for k, a in manifest["accounts"].items():
        r = a["reconciliation"]
        print(f"  {k}: reconstructed {r['reconstructed_balance']} vs broker "
              f"{r['broker_reported_balance']} -> residual {r['residual']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
