#!/usr/bin/env python3
"""Build ``FIRM_RULES_V1.json`` -- prop-firm rules from each firm's own pages, and a
mechanical check of the live config against them.

Stage 1.1 (Session J). Firm rules live in the broker-truth layer because they are the
same class of fact as costs and have been asserted from memory before.

This does not merely restate the rules: it **reads the live config and reports every
place the config disagrees with the firm's own page**. A rules document that cannot
contradict the running system is decoration.

Sourcing
--------
Rules below are keyed to one of three provenance kinds:

- ``captured_page``   -- raw HTML captured in-tree with a sha256, the way B56 established
                         the reset clocks. Strongest.
- ``fetched_page``    -- retrieved from the firm's own URL on the stated date by this
                         session, recorded as an extraction with the verbatim phrase.
                         Weaker than ``captured_page``: no byte-preserved artifact. The
                         follow-up is a byte-preserving re-capture.
- ``secondary_audit`` -- `.context/05_operations/redacted_account_terms_audit_2026-04-20.md`,
                         which carries its own per-term confidence column.

Usage
-----
    python3 scripts/build_firm_rules.py -o <out.json>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SCHEMA = "gtos.broker_truth.firm_rules.v1"
VERSION = "1.0.0"
FETCHED_ON = "2026-07-27"

FTMO = {
    "firm": "FTMO",
    "legal_entity": "FTMO Global Markets Ltd",
    "account_login": 531325516,
    "server": "FTMO-Server3",
    "product": "$100k FTMO Challenge 2-Step",
    "initial_balance_usd": 100000.0,
    "rules": {
        "max_daily_loss_pct": {
            "value": 5.0,
            "denominator": "Initial Simulated Capital (a FIXED cash amount)",
            "reset": "00:00 CE(S)T",
            "measured_on": "equity (balance + open P/L +/- swaps - commissions)",
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_"
            "2026_06_02/raw_official_sources/ftmo_trading_objectives.html "
            "(OFFICIAL_FTMO_SOURCE_INDEX.json:ftmo_trading_objectives, fetched "
            "2026-06-01T18:01:50Z, HTTP 200, 286133 bytes)",
            "verbatim": "recalculated daily at 00:00 CE(S)T as the difference between: the "
            "account balance recorded at 00:00 CE(S)T of the current day and the Maximum "
            "Daily Loss Amount, which is 5% of the Initial Simulated Capital",
        },
        "max_overall_loss_pct": {
            "value": 10.0,
            "kind": "static (not trailing) for 2-Step",
            "floor_usd": 90000.0,
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "as above -- 'establishes a static limit'",
        },
        "profit_target_pct": {
            "phase1": 10.0,
            "phase2": 5.0,
            "funded": None,
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "as above (2-Step section)",
        },
        "minimum_trading_days": {
            "value": 4,
            "window": "00:00:00 to 23:59:59 CE(S)T",
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "as above",
        },
        "consistency_rule": {
            "value": None,
            "note": "The Best Day Rule (best day <= 50% of Positive Days' Profit) applies to "
            "1-Step / FTMO Account (1-Step) ONLY and explicitly not to 2-Step. The live "
            "account is 2-Step, so it carries no consistency rule. This closes the "
            "'zero consistency enforcement' half of ULTIMATE_SYSTEM_REDTEAM_V1 GAP 7 by "
            "citation rather than by work.",
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "as above",
        },
        "payout": {
            "profit_split_pct": 80.0,
            "profit_split_upgraded_pct": 90.0,
            "upgrade_conditions": [
                "Minimum of 4 months as an FTMO Trader",
                "At least 10% of the initial (or scaled) capital in total net simulated profit",
                "At least 2 processed rewards",
                "Positive account balance at the time of scale-up",
            ],
            "scaling": "account size +25% every 4 months, up to $2,000,000",
            "first_claim": "the 14th or any following day after the first placed trade",
            "preconditions": "all open positions and pending orders must be closed",
            "minimum_usd": {"bank_wire": 20.0, "crypto": 50.0},
            "method_caps_usd": {"visa_mastercard": 20000.0, "skrill": 3000.0},
            "processing": "notified within 1-2 business days; reward typically sent within "
            "1-2 business days after invoice approval",
            "coverage": "MEASURED",
            "provenance_kind": "fetched_page",
            "provenance": f"https://ftmo.com/en/faq/how-do-i-withdraw-my-profits/ and "
            f"https://ftmo.com/en/reward-growth-and-scaling-plan/, fetched {FETCHED_ON}. "
            "Extraction, not a byte-preserved capture -- see module docstring.",
            "verbatim": "FTMO Challenge: 2-Step provides 80% of profits (increases to 90% "
            "under certain conditions)",
        },
    },
}

redacted_account = {
    "firm": "redacted_account",
    "legal_entity": "redacted_account Ltd",
    "account_login": 0,
    "server": "redacted_account-Server 2",
    "product": "redacted_account Stellar 2-Step $100K (CFD, MT5)",
    "initial_balance_usd": 100000.0,
    "rules": {
        "max_daily_loss_pct": {
            "value": 5.0,
            "denominator": "Initial Balance (a FIXED cash amount), PLUS today's realized profit",
            "reset": "00:00 server time",
            "measured_on": "closed results for the day + open position results; swap, "
            "commissions and fees included",
            "coverage": "MEASURED",
            "provenance_kind": "captured_page",
            "provenance": "research/science_program_2026_05/01_domain_syntheses/raw/"
            "G10_execution_risk_sources_2026-05-06/redacted_account_daily_loss_limit.html "
            "(help.redacted_account.com article 8019811, fetched 2026-05-06T08:04:58Z, 97062 bytes)",
            "verbatim": "if you start a new day with $110,000 and lose $5,000 during the day, "
            "your equity will be $105,000. However, since your daily loss limit is calculated "
            "based on the initial balance ($100,000 x 5% = $5,000), losing $5,000 breaches the "
            "limit for that day. This will result in your account being paused, even though "
            "your equity has not dropped to $95,000.",
        },
        "max_overall_loss_pct": {
            "value": 10.0,
            "coverage": "TRANSFERRED",
            "transferred_from": "agent_config.yaml:3141 / execution_packets.py:129-131, which "
            "assert the FTMO and redacted_account 100k challenge limits are identical",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md",
        },
        "profit_target_pct": {
            "phase1": 8.0,
            "phase2": 5.0,
            "coverage": "TRANSFERRED",
            "provenance_kind": "secondary_audit",
            "transferred_from": "config/agent_config.yaml:3142 + redacted_account.yaml:14",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md",
        },
        "minimum_trading_days": {
            "value": 5,
            "note": "per phase, >=1 trade/day. DIFFERS from FTMO's 4, and only FTMO's is "
            "configured anywhere.",
            "coverage": "MEASURED",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:35",
        },
        "consistency_rule": {
            "value": None,
            "note": "none for CFD accounts (the 40% rule is Futures-only)",
            "coverage": "MEASURED",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:37",
        },
        "news_window": {
            "note": "+/-5 min around listed high-impact news: only 40% of profit counts, "
            "100% of losses apply; a partial close inside the window taints the whole trade. "
            "NOT MODELLED ANYWHERE IN THE REPO.",
            "coverage": "MEASURED",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:39",
        },
        "weekend_holding": {
            "note": "allowed in Challenge, PROHIBITED on the funded account. Requires a "
            "post-pass config change that does not exist.",
            "coverage": "MEASURED",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:38",
        },
        "leverage": {
            "note": "XAUUSD and indices 1:30 in challenge -> 1:5 funded; FX 1:100 throughout. "
            "The post-pass step-down is unmodelled and is the highest-impact unmodelled item.",
            "coverage": "TRANSFERRED",
            "transferred_from": "secondary sources; the primary help-center page was not "
            "fetchable at audit time",
            "provenance_kind": "secondary_audit",
            "provenance": ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:43-45",
        },
        "payout": {
            "profit_split_pct": 80.0,
            "profit_split_upgraded_pct": 90.0,
            "profit_split_max_pct": 95.0,
            "upgrade_conditions": ["Scale-Up plan", "up to 95% with add-ons"],
            "first_claim": "after 21 days from receiving the funded account",
            "cycle": "bi-weekly (14 days) thereafter",
            "minimum_usd": 250.0,
            "minimum_accumulated_before_first_request_usd": 500.0,
            "maximum_per_request_usd": 4999.0,
            "processing": "within 24 h",
            "coverage": "MEASURED",
            "provenance_kind": "fetched_page",
            "provenance": f"https://help.redacted_account.com/en/articles/8020768 (Reward Share "
            f"Rules), fetched {FETCHED_ON}; cycle/minimum/maximum from "
            ".context/05_operations/redacted_account_terms_audit_2026-04-20.md:42,48 "
            "(secondary_audit). Extraction, not a byte-preserved capture.",
            "verbatim": "traders initially receive an 80% Reward Share ... Traders can "
            "increase their Reward Share up to 95% with add-ons",
        },
    },
}


def _load_yaml(rel: str) -> dict:
    path = REPO / rel
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def _dig(doc: dict, *keys):
    cur = doc
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def config_divergences() -> list[dict]:
    """Every place the running config disagrees with a firm's own page.

    Computed, not asserted: each entry names the config site, the firm-page value, and
    the direction of the error.
    """
    out: list[dict] = []
    agent = _load_yaml("config/agent_config.yaml")
    ftmo_profile = _load_yaml("config/profiles/operator_profile.yaml")
    fn_profile = _load_yaml("config/profiles/redacted_account.yaml")
    runtime = agent.get("gtos_vnext_runtime") or {}

    # 1. The daily-loss denominator.
    out.append(
        {
            "id": "FR1",
            "severity": "high",
            "title": "Daily-loss allowance is computed as a percentage of the day-start "
            "anchor; both firms define it as a fixed cash amount = 5% of INITIAL balance",
            "code_sites": [
                "src/components/ultimate_book/governor_state.py:271 "
                "(realized_today_pct = (equity - anchor) / anchor)",
                "src/components/prop_firm_headroom_v4.py:260-262",
            ],
            "firm_rule": "FTMO: balance at 00:00 CE(S)T minus 5% of Initial Simulated "
            "Capital. redacted_account: initial balance x 5%, plus today's realized profit.",
            "direction": "LOOSE IN PROFIT -- the two agree only while anchor == initial. "
            "On redacted_account's own worked example (day start $110,000) the firm breaches at "
            "-$5,000 while 5%-of-anchor permits -$5,500.",
            "why_it_matters": "This is structurally the same class of error B56 fixed for "
            "the reset clock: a rule read from a firm page, then implemented against a "
            "different denominator. It has not bitten because the accounts have not been "
            "in profit at a day start by enough to matter.",
            "not_in_scope": "The OVERALL max-DD basis is correct and deliberately so -- "
            "governor_state.py:280-282 pins max_dd_reference_equity to the static initial "
            "floor and comments that it 'does NOT trail up with profit'. Only the DAILY "
            "denominator is anchor-relative.",
            "verified_at_source": "governor_state.py:271 and prop_firm_headroom_v4.py:262 "
            "read directly on 2026-07-27",
        }
    )

    # 2. FTMO profit target constant.
    out.append(
        {
            "id": "FR2",
            "severity": "medium",
            "title": "FTMO_TARGET hardcoded at 0.08 contradicts the captured FTMO page",
            "code_sites": ["src/components/ultimate_book/admission.py:52-54"],
            "config_value": 0.08,
            "firm_rule": "2-Step: 10% phase 1, 5% phase 2",
            "profile_value": {
                "phase1": _dig(ftmo_profile, "gtos_vnext_runtime", "prop_safe_selector_phase1_target_pct")
                or _dig(ftmo_profile, "ftmo_rules", "profit_target_phase1_pct"),
                "phase2": _dig(ftmo_profile, "gtos_vnext_runtime", "prop_safe_selector_phase2_target_pct")
                or _dig(ftmo_profile, "ftmo_rules", "profit_target_phase2_pct"),
            },
            "direction": "Ambiguous, and stated as such. The constant's own comment calls it "
            "'the owner objective' and cites INTEG_portfolio_build.py -- a research script, "
            "not a firm page -- so 8% may be a deliberate internal target set below FTMO's "
            "10%. The defect is naming, not necessarily arithmetic: it is called FTMO_TARGET "
            "under a header reading 'FTMO CONSTANTS', beside FTMO_MAXDD and FTMO_DAILY, "
            "which ARE the firm's numbers. A reader will take all three as firm rules.",
            "verified_at_source": "admission.py:44-54 read directly on 2026-07-27",
            "owner_question": "Is 0.08 a deliberate internal target, or a stale transcription "
            "of the firm's target? If deliberate, rename it to INTERNAL_TARGET.",
        }
    )

    # 3. The base default is the wrong firm's number.
    base_phase1 = runtime.get("prop_safe_selector_phase1_target_pct")
    if base_phase1 is not None and abs(float(base_phase1) - 8.0) < 1e-9:
        out.append(
            {
                "id": "FR3",
                "severity": "low",
                "title": "agent_config base phase-1 target is redacted_account's 8.0, not FTMO's 10.0",
                "code_sites": ["config/agent_config.yaml prop_safe_selector_phase1_target_pct"],
                "config_value": base_phase1,
                "direction": "Both FTMO profiles override it, so it works; but a new FTMO "
                "profile that forgets to override inherits the wrong firm's target.",
            }
        )

    # 4. Minimum trading days: only one firm's is configured.
    fn_min_days = _dig(fn_profile, "redacted_account_rules", "minimum_trading_days")
    out.append(
        {
            "id": "FR4",
            "severity": "medium",
            "title": "redacted_account's 5 minimum trading days is configured nowhere",
            "code_sites": ["config/profiles/redacted_account.yaml (no redacted_account_rules block exists)"],
            "config_value": fn_min_days,
            "firm_rule": "redacted_account 5 per phase; FTMO 4",
            "direction": "The only minimum_trading_days key in any config is FTMO's 4, on "
            "the FTMO profile. redacted_account's stricter 5 is unrepresented.",
        }
    )

    # 5. The stale reset comment.
    out.append(
        {
            "id": "FR5",
            "severity": "low",
            "title": "Stale 'server = UTC+3, daily window resets 21:00 UTC' prose survives "
            "in config and handoff docs after B56 refuted it for FTMO",
            "code_sites": [
                "config/agent_config.yaml (governor_daily_reset_offset_hours comment)",
                "LIVE_HANDOFF.md:104",
                ".context/00_core/live_system_of_record.md:141-146",
            ],
            "firm_rule": "FTMO resets 00:00 CE(S)T (Europe/Prague); redacted_account at server "
            "midnight. Different calendars, ~4 weeks a year apart.",
            "direction": "Documentation only -- the live path reads "
            "prop_safe_selector_daily_reset_timezone, which is correct. But the prose is "
            "what a future session will read first.",
        }
    )

    # 6. The unsourced profit-split claim.
    out.append(
        {
            "id": "FR6",
            "severity": "medium",
            "title": "The repo's only profit-split numbers are unsourced and wrong",
            "code_sites": [".context/02_session_handoffs/19_apr17_priority1_deployment_handoff.md:160"],
            "config_value": "95% redacted_account vs 90% FTMO",
            "firm_rule": "Both live products start at 80%. FTMO 2-Step 80% -> 90% via "
            "Scaling Plan; redacted_account Stellar 2-Step 80% -> 90% via Scale-Up, 95% only "
            "with paid add-ons.",
            "direction": "Optimistic by 10-15 percentage points on both firms. Any "
            "days-to-payout or scaling arithmetic built on it overstates net income. "
            "KB3_regime_scaling.py's profit_split=0.8 assumption is, by contrast, correct.",
        }
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    doc = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/build_firm_rules.py",
        "provenance_kinds": {
            "captured_page": "raw HTML in-tree with sha256 -- strongest",
            "fetched_page": "retrieved from the firm's URL on the stated date; extraction, "
            "not byte-preserved",
            "secondary_audit": "an in-repo audit of the firm's terms, with its own "
            "confidence column",
        },
        "daily_reset_clocks": {
            "note": "A firm's reset rule and its MT5 server clock are different things, and "
            "this programme conflated them once already (B56). Kept in separate registries "
            "by src/utils/broker_clock.py:309-315.",
            "FTMO": {
                "reset": "00:00 CE(S)T (Europe/Prague)",
                "coverage": "MEASURED",
                "provenance": "FTMO's own captured page + config/profiles/"
                "operator_profile.yaml:87 (prop_safe_selector_daily_reset_timezone); "
                "EU calendar arithmetic verified against zoneinfo on every day of 2026, "
                "0 mismatches (B56)",
            },
            "redacted_account": {
                "reset": "00:00 server time",
                "coverage": "MEASURED",
                "provenance": "help.redacted_account.com article 8019811, captured 2026-05-06; "
                "the redacted_account profile deliberately declares no rule, pinned by "
                "tests/ultimate_book/test_daily_reset_rule.py:193-197",
            },
            "server_clock_both": {
                "rule": "America/New_York + 7 h (UTC+2 EST / UTC+3 EDT)",
                "coverage": "MEASURED",
                "provenance": "src/utils/broker_clock.py:250-287 -- 81 weekly session "
                "boundaries per broker, all transitions on US dates",
            },
            "known_gap": "The reset INSTANTS have never been observed on either live "
            "account. The rules are read from firm pages and the calendars are measured, "
            "but no day-boundary snapshot exists (IMPLEMENTATION_STATE.md:1734-1736, ask "
            "written and unsent).",
        },
        "firms": {"FTMO": FTMO, "redacted_account": redacted_account},
        "config_divergences": config_divergences(),
        "absent": [
            "FTMO payout eligibility beyond the 14-day first-claim rule (KYC, days on the "
            "funded account) -- not on any fetched page",
            "redacted_account help-center article 8394309, cited in 4 places as the reset source, "
            "is captured nowhere; the captured article is 8019811",
            "Any news-blackout gate in code (news_calendar.py exists and is unwired)",
            "Any weekend-flatten policy for redacted_account's funded phase",
            "redacted_account post-pass leverage step-down (1:30 -> 1:5) in any config",
            "Byte-preserved raw HTML for the two payout pages fetched 2026-07-27",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(f"wrote {args.out}")
    print(f"  config divergences: {len(doc['config_divergences'])}")
    for d in doc["config_divergences"]:
        print(f"    [{d['severity']:>6}] {d['id']}: {d['title'][:88]}")
    print(f"  named absences: {len(doc['absent'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
