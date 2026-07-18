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

    def test_only_self_untyped_code_zero(self) -> None:
        rows = self.world.conn.execute(
            "SELECT name, kind, code FROM vens"
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "SELF")
        self.assertEqual((rows[0]["kind"] or "").strip(), "")
        self.assertEqual(rows[0]["code"], "0")
        n_inst = self.world.conn.execute(
            "SELECT COUNT(*) AS c FROM instances"
        ).fetchone()["c"]
        self.assertEqual(n_inst, 1)

    def test_zero_point_no_types_until_taught(self) -> None:
        from miwbs import mentor
        from miwbs.format import plain

        self.assertEqual(mentor.allowed_kinds(self.world), frozenset())
        r = dispatch(self.world, "create person Bob | a guy")
        self.assertIn("not taught", plain(r.message).lower())
        r2 = dispatch(self.world, "create concept Wonder | a sense of wonder")
        self.assertIn("not taught", plain(r2.message).lower())
        # teach concept, then create works
        ws = mentor.workshop_for(self.world)
        ws.mint_type("concept", "the sense of Concept")
        r3 = dispatch(self.world, "create concept Concept | the concept of Concept")
        self.assertNotIn("not taught", plain(r3.message).lower())
        self.assertIn("concept", plain(r3.message).lower())

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
