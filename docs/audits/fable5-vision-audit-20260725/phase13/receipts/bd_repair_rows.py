"""Session BD's repair-queue rows. Append-only; union-merged at the train."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave13-live-debt-sweep-20260730")
Q = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/REPAIR_QUEUE_APPEND.jsonl"
NOW = datetime.now(timezone.utc).isoformat()

ROWS = [
    {
        "session": "BD", "sleeve": None, "is_primary": True,
        "component": "src/components/ultimate_book/book_owner.py :: _runtime_learning_admission_members",
        "verdict": "OPEN",
        "gate": "packet joinability",
        "margin": "303 of 985 unit rows (30.8 %)",
        "action": (
            "**303 of 985 `unit_admitted`/`unit_shadow` rows in the 99,112-packet live export carry "
            "NO member roster at all** (`admission_unit_member_count: 0`), so no join key is "
            "recoverable for them by ANY rule -- OD-P2's agreement rule included. The cause is "
            "upstream of the emitter: `_runtime_learning_admission_members` returns `[]` when the "
            "unit's `sleeve_members` is empty OR when `skip_context` has no matching entry for any "
            "member. Which of the two dominates is unmeasured. This is 30.8 % of the unit stream and "
            "it is the residual after OD-P2, not something OD-P2 introduced."
        ),
        "prescription": (
            "Measure the split first (empty `sleeve_members` vs `skip_context` miss) on the same "
            "export; they have different repairs and only one of them is in the emitter."
        ),
        "evidence": {
            "artifact": "measured over vps-export-20260725 ultimate_book_runtime_learning_packets.jsonl.gz",
            "unit_rows": 985, "rows_with_no_members": 303,
            "member_count_histogram": {"0": 303, "1": 405, "2": 250, "3": 18, "4": 4, "5": 4, "6": 1},
        },
    },
    {
        "session": "BD", "sleeve": None, "is_primary": True,
        "component": "src/components/execution.py :: _trading_m15_bars_since",
        "verdict": "FILED",
        "gate": "time-stop reachability",
        "margin": "56 bars of headroom (0.72 %)",
        "action": (
            "AQ §6a's exposure is now DETECTED (`coverage_status`, `count_is_lower_bound`, "
            "`time_stop_unreachable`) and the BEHAVIOUR half is deliberately unbuilt behind "
            "`ultimate_book_time_stop_wallclock_on_truncated_window` (default OFF). What remains "
            "open is the owner decision AQ named: on a truncated window the choice is an INERT "
            "backstop (today) or an EARLY one (wall-clock over-counts -- index CFDs ~3x, fx over "
            "weekends). Both are wrong; which is less wrong is per-sleeve. Also open: the F15 "
            "measurement is 7,800 available against an `mx_*` request of 7,744, which is **56 bars "
            "of headroom on a terminal `Max bars in chart` setting** that a future session can "
            "change without knowing this code exists."
        ),
        "prescription": (
            "Re-run the F15 `copy_rates` probe as a PRECONDITION of arming any `mx_*` sleeve, not "
            "once. The diagnostic now emits `time_stop_unreachable` per tick, so the live book can "
            "answer it continuously instead of by ceremony."
        ),
        "evidence": {
            "budget_m15_bars": 7680, "bars_requested": 7744, "f15_measured_available": 7800,
            "headroom_bars": 56, "headroom_frac": 0.00723,
            "armed_sleeves_exposed": 0, "armed_budget_m15_bars": 1280, "armed_requested": 1344,
        },
    },
    {
        "session": "BD", "sleeve": "energy_agri", "is_primary": True,
        "component": "SLEEVE_EXIT_PROFILES['energy_agri'] :: partial_be_runner",
        "verdict": "REJECT",
        "gate": "significance",
        "margin": "p 0.206 vs alpha 0.10",
        "action": (
            "The scale-out on an ARMED sleeve costs **+0.2302 R/day** against a plain exit, gated at "
            "the ratified rule (RECORDED, B_balanced alpha 0.10, family V5, four bands) -- a third "
            "instrument agreeing with AD §6.2 (-0.308 R/day, n=67) and AU §2 (+0.2302 restamp "
            "error), and reproducing AU to four decimals. **Both arms REJECT at all four bands** "
            "(p 0.321 -> 0.206), n=64, and the chronological folds decay under BOTH contracts with "
            "the most recent negative either way. The control holds: across the four "
            "`partial_be_runner` sleeves the sign runs BOTH ways (metals_core -0.0777, "
            "metals_ob_micro -0.0399 favour the scale-out)."
        ),
        "prescription": (
            "Wired as `FRONTIER_EXIT_OVERRIDES['energy_agri']` cell `plain_exit_no_partial`, default "
            "OFF, ceremony selects by name. **Do not arm on this evidence.** Re-visit on sample: "
            "n=64 is the binding constraint, not the effect size."
        ),
        "evidence": {
            "artifact": "docs/audits/fable5-vision-audit-20260725/phase13/receipts/BD_PARTIAL_EXIT_V1.json",
            "delta_r_per_day_all_bands": 0.230213,
            "live_mean_r_per_day_mid": 0.17629131694575584,
            "plain_mean_r_per_day_mid": 0.40650392440734884,
            "p_raw_live": 0.32126787321267875, "p_raw_plain": 0.20607939206079393,
            "n_trades": 64, "maxbars_share_both_arms": 0.0,
            "fold_means_live": [0.533, 0.282, -0.287], "fold_means_plain": [0.933, 0.351, -0.064],
            "control_sign_runs_both_ways": True,
            "delta_identical_at_every_band_because": (
                "a cost band shifts both arms equally, so 'at every band' is structural rather than "
                "four independent confirmations -- applies to AU §2's phrasing too"
            ),
        },
    },
    {
        "session": "BD", "sleeve": None, "is_primary": False,
        "component": "docs/audits/fable5-vision-audit-20260725/phase3/PACKET_EMITTER_CARRY.md §6.1 / IMPLEMENTATION_STATE B213",
        "verdict": "CORRECTED",
        "gate": None, "margin": "6.21x bytes",
        "action": (
            "OD-P3 was filed as *'a small change to that allowlist'*. Measured: adding "
            "`gtos_vnext_pretrade_cost_model` to the flat key list emits the whole 42-key model at "
            "**2,764 bytes against 445** derived (217.5 MB vs 35.0 MB per 37-day window), and it "
            "does NOT fail loudly -- `_clean_mapping` redacts `profile.server` to "
            "`server_hash_sha256` before the forbidden-key scan runs, so it passes validation and "
            "ships a hash of the broker server name in every packet as noise. My own first draft "
            "asserted the opposite (that it would be quarantined) and was wrong."
        ),
        "prescription": (
            "Built as a derivation of scalars instead. And the part worth more than the wiring: "
            "`total_cost_r` charges NO commission (F38's shape, surviving in the pretrade model "
            "after being repaired in the realized one) while the realized side does, so "
            "`modelled_vs_realized_comparable` is published per row with the exclusion named."
        ),
        "evidence": {
            "packets_carrying_any_modelled_cost_before": 0, "corpus_packets": 99112,
            "naive_bytes": 2764, "derived_bytes": 445, "ratio": 6.21,
        },
    },
    {
        "session": "BD", "sleeve": None, "is_primary": False,
        "component": "docs/audits/fable5-vision-audit-20260725/phase3/PACKET_EMITTER_CARRY.md §7 OD-P1",
        "verdict": "CORRECTED",
        "gate": None, "margin": "2.4x, and 2.35 pp",
        "action": (
            "OD-P1's 76.05 % is reproducible (76.79 % of stream here, within 0.7 pp) but its STATE "
            "CONTRACT was never written down, and the change is irreversible for the window in "
            "which it runs. The same stream compresses **0.94 % / 40.14 % / 96.72 %** of "
            "`position_managed` under three contracts. The obvious implementation -- a top-level "
            "`*_checked_at_utc` exclusion list -- is the middle line: **it under-delivers by 2.4x "
            "while looking deployed**, because `policy_clock_diagnostic` embeds its own "
            "`checked_at_utc` one level down (59.7 % of rows, 100 % churn). Separately, 76.05 % is "
            "the NO-heartbeat figure; with the 15-minute heartbeat P recommends in the same "
            "paragraph it is **73.70 %** (the heartbeat costs 3,069 packets, 2.35 pp)."
        ),
        "prescription": (
            "Contract declared and named (`position_managed_emit_on_change_v1_recursive_checked_at`), "
            "default OFF, and every emitted packet now carries the run length it stands for so the "
            "irreversible loss is at least COUNTABLE."
        ),
        "evidence": {
            "drop_pct_position_managed": {"none": 0.94, "toplevel": 40.14, "recursive": 96.72},
            "drop_pct_stream_no_heartbeat": 76.79, "drop_pct_stream_900s_heartbeat": 73.70,
            "heartbeat_packets_at_900s": 3069,
            "churn_is_bimodal": "4 fields at 100 %, 2 at 4.86 %, 98 at <= 0.46 %",
        },
    },
    {
        "session": "BD", "sleeve": None, "is_primary": False,
        "component": "src/costs/model.py :: _load_cached",
        "verdict": "CLOSED",
        "gate": None, "margin": "3 sessions",
        "action": (
            "The cost artifact is COMMITTED, and its absence message said *'Build it with "
            "`build_broker_true_costs.py`'* unconditionally -- sending three sessions in a row "
            "(AR B1473, AS handoff 6, BD) to re-run a broker-truth capture when the answer was one "
            "`git sparse-checkout add`, each after a ~25 s substrate build. AS filed the fix as "
            "'one line in the profile'; that line DID land in `scripts/gtos_hydrate_test_data.py` "
            "(Session AU). The MESSAGE never did, and the message is what a session reads at the "
            "moment it is stuck."
        ),
        "prescription": (
            "The two cases are now distinguished with `git ls-files` and each says the true thing. "
            "General form: when a fix lands in a tool nobody is required to run, check whether the "
            "ERROR PATH still points the wrong way."
        ),
        "evidence": {"sessions_that_hit_it": ["AR B1473", "AS handoff 6", "BD"]},
    },
]


def main() -> int:
    with Q.open("a", encoding="utf-8") as fh:
        for r in ROWS:
            fh.write(json.dumps({**r, "appended_utc": NOW}, sort_keys=True) + "\n")
    total = sum(1 for line in Q.open(encoding="utf-8") if line.strip())
    print(f"appended {len(ROWS)} rows ({sum(1 for r in ROWS if r['is_primary'])} primary); "
          f"queue now {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
