"""Behavioral tests for Challenge manage Choices. No network. No order_send."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from src.judgment.manage_choices import (
    CRITERIA,
    MODEL,
    arm_pending_remove,
    clear_cache,
    decide,
    emit_manage,
)

LIVE_GOLD = 294215389


def _hop(winner: str, probs: dict[str, float] | None = None, **extra):
    def ask(state, *, question_id, instructions, criteria):
        del state, instructions
        assert question_id
        assert set(criteria) == set(CRITERIA)
        mass = probs if probs is not None else {winner: 0.61, "hold": 0.39}
        return {
            "decision_emitted": True,
            "choice": winner,
            "probability": mass[winner],
            "probabilities": mass,
            "probability_source": "probabilities",
            "order_send": False,
            **extra,
        }

    return ask


class ManageChoiceTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_cache()
        self.tmp = tempfile.TemporaryDirectory()
        self.record = Path(self.tmp.name) / "manage_choices.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        clear_cache()

    def test_highest_probability_authorizes_only_that_act(self) -> None:
        row = decide(
            "move_sl",
            ticket=111,
            symbol="XAUUSD",
            proposed=4335.0,
            reason="be",
            ask=_hop("move_sl", {"leave_orig": 0.1, "move_sl": 0.55, "move_tp": 0.05, "close": 0.1, "hold": 0.2}),
            use_cache=False,
            record_to=self.record,
        )
        self.assertTrue(row["send"])
        self.assertEqual(row["choice"], "move_sl")
        self.assertEqual(row["persist"], "0.00")
        self.assertFalse(row["agent_order_send"])
        self.assertTrue(row["friends_copy_result"])
        self.assertIn("move_sl", self.record.read_text(encoding="utf-8"))

    def test_other_winner_does_not_send_this_act(self) -> None:
        for act, winner in (
            ("move_sl", "hold"),
            ("move_sl", "leave_orig"),
            ("move_sl", "close"),
            ("move_sl", "move_tp"),
            ("move_tp", "move_sl"),
            ("close", "hold"),
            ("close", "leave_orig"),
            ("remove", "hold"),
            ("remove", "move_sl"),
        ):
            row = decide(act, ticket=222, ask=_hop(winner), use_cache=False, record=False)
            self.assertFalse(row["send"], msg=f"{act} winner {winner}")
            self.assertEqual(row["choice"], winner)

    def test_tie_is_not_a_decision(self) -> None:
        def ask(state, *, question_id, instructions, criteria):
            del state, question_id, instructions, criteria
            return {
                "decision_emitted": False,
                "choice": None,
                "probability": None,
                "probabilities": {"close": 0.5, "hold": 0.5},
                "error": "no_unique_highest",
                "order_send": False,
            }

        row = decide("close", ticket=333, ask=ask, use_cache=False, record=False)
        self.assertFalse(row["decision_emitted"])
        self.assertFalse(row["send"])
        self.assertNotIn("jev_absent", str(row))

    def test_live_gold_close_sends_when_close_wins(self) -> None:
        for act in ("close", "remove"):
            row = decide(
                act,
                ticket=LIVE_GOLD,
                symbol="XAUUSD",
                ask=_hop("close", {"close": 0.9, "hold": 0.1}),
                use_cache=False,
                record=False,
            )
            self.assertEqual(row["choice"], "close")
            self.assertTrue(row["decision_emitted"])
            self.assertTrue(row["send"])
            self.assertNotIn("gold_pin_blocked", row)
            self.assertEqual(row["model"], MODEL)

    def test_gold_sl_move_can_still_be_the_choice(self) -> None:
        row = decide(
            "move_sl",
            ticket=LIVE_GOLD,
            proposed=4332.0,
            ask=_hop("move_sl"),
            use_cache=False,
            record=False,
        )
        self.assertTrue(row["send"])

    def test_unreadable_ask_does_not_send(self) -> None:
        def ask(state, *, question_id, instructions, criteria):
            del state, question_id, instructions, criteria
            return {"decision_emitted": False, "error": "key_unreadable", "probabilities": {}}

        self.assertFalse(
            emit_manage("move_tp", ticket=9, namespace="operator", ask=ask, use_cache=False, record=False)
        )

    def test_other_namespace_does_not_ask(self) -> None:
        called = {"n": 0}

        def ask(state, *, question_id, instructions, criteria):
            del state, question_id, instructions, criteria
            called["n"] += 1
            return {}

        self.assertTrue(emit_manage("close", ticket=1, namespace="redacted_account", ask=ask, record=False))
        self.assertEqual(called["n"], 0)

    def test_remove_hook_sends_only_when_close_wins(self) -> None:
        sent = []

        class Mt5:
            def order_send(self, request, *args, **kwargs):
                sent.append(request)
                return type("R", (), {"retcode": 10009, "success": True})()

        mt5 = Mt5()
        self.assertTrue(
            arm_pending_remove(mt5, ask=_hop("close"), write_stamp=False, record=False)
        )
        result = mt5.order_send({"action": 8, "order": 55})
        self.assertEqual(result.retcode, 10009)
        self.assertEqual(sent, [{"action": 8, "order": 55}])
        self.assertFalse(arm_pending_remove(mt5, ask=_hop("hold"), write_stamp=False, record=False))

    def test_remove_hook_hold_blocks_and_gold_close_sends(self) -> None:
        sent = []

        class Mt5:
            def order_send(self, request, *args, **kwargs):
                sent.append(request)
                return type("R", (), {"retcode": 10009})()

        mt5 = Mt5()
        arm_pending_remove(mt5, ask=_hop("hold"), write_stamp=False, record=False)
        blocked = mt5.order_send({"action": 8, "order": 77})
        self.assertIsNone(blocked.retcode)
        self.assertFalse(blocked.success)
        deal = mt5.order_send({"action": 1, "order": 77})
        self.assertEqual(deal.retcode, 10009)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["action"], 1)

        clear_cache()
        gold = type("M", (), {})()
        sent.clear()

        def original(request, *args, **kwargs):
            sent.append(request)
            return type("R", (), {"retcode": 10009})()

        gold.order_send = original
        arm_pending_remove(gold, ask=_hop("close"), write_stamp=False, record=False)
        closed = gold.order_send({"action": 8, "order": LIVE_GOLD})
        self.assertEqual(closed.retcode, 10009)
        self.assertEqual(sent, [{"action": 8, "order": LIVE_GOLD}])

    def test_source_has_no_absent_mode_and_execution_gate_is_present(self) -> None:
        src = Path(__file__).resolve().parents[2] / "src" / "judgment" / "manage_choices.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("jev_absent", text)
        self.assertNotIn("missing_jev", text)
        self.assertNotIn("294215389", text)
        self.assertNotIn("gold_pin", text)
        self.assertNotIn("gold_ticket_do_not_close", text)
        self.assertIn(MODEL, text)
        self.assertEqual(MODEL, "jev-1.13.0")
        self.assertNotIn(".order_send(", text)
        execution = Path(__file__).resolve().parents[2] / "src" / "components" / "execution.py"
        hooked = execution.read_text(encoding="utf-8")
        self.assertIn("_challenge_manage_emit", hooked)
        ast.parse(hooked)


if __name__ == "__main__":
    unittest.main()
