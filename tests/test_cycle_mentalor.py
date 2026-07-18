"""Mentalor cycle · node spine (Day of Days)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miwbs.cli import ensure_world
from miwbs.commands import dispatch
from miwbs import cycle as cycle_mod


class MentalorCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "day.world.db"
        self.world = ensure_world(self.path, reseed=True, seed="mentalor")

    def test_seed_is_mentalor_day_of_days(self) -> None:
        self.assertTrue(cycle_mod.is_mentalor(self.world))
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.current_cycle, "ʞ")
        self.assertEqual(cycle_mod.current_face(st), "CYCʞ-0")
        r = dispatch(self.world, "remember")
        self.assertIn("you remember", r.message)
        self.assertIn("CYCʞ-0", r.message)

    def test_node_plus_and_splice_path(self) -> None:
        dispatch(self.world, "node +")
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.current_path, "1")
        self.assertEqual(cycle_mod.current_face(st), "CYCʞ-1")
        # back to 0, insert between will create under 0
        dispatch(self.world, "node prev")
        dispatch(self.world, "node next")  # on 1
        # order 0,1 — go to 1 then insert uses left=0
        dispatch(self.world, "node insert")
        st = cycle_mod.load_state(self.world)
        self.assertTrue(st.current_path.startswith("0."))
        self.assertIn(st.current_path, st.cycles["ʞ"].order)

    def test_consider_self_echo(self) -> None:
        r = dispatch(self.world, "consider SELF | pressure?")
        self.assertTrue(r.ok)
        self.assertIn("SELF", r.message)
        r2 = dispatch(self.world, "consider ECHO | coming through.")
        self.assertTrue(r2.ok)
        listed = dispatch(self.world, "consider")
        self.assertIn("pressure?", listed.message)
        self.assertIn("ECHO", listed.message)


if __name__ == "__main__":
    unittest.main()
