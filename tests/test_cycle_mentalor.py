"""Mentalor cycle · node spine (Day of Days)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miwbs.cli import ensure_world
from miwbs.commands import dispatch
from miwbs import cycle as cycle_mod
from miwbs.format import plain


class MentalorCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "day.world.db"
        self.world = ensure_world(self.path, reseed=True, seed="mentalor")

    def test_seed_is_mentalor_day_of_days(self) -> None:
        self.assertTrue(cycle_mod.is_mentalor(self.world))
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.current_cycle, "ʞ")
        self.assertEqual(cycle_mod.current_face(st), "CYC ʞ")
        r = dispatch(self.world, "remember")
        text = plain(r.message)
        self.assertIn("OBSERVING:", text)
        self.assertIn("CYC ʞ", text)
        self.assertNotIn("you remember", text.lower())

    def test_self_and_echo_untyped(self) -> None:
        rows = self.world.conn.execute(
            "SELECT name, kind, code FROM vens"
        ).fetchall()
        by_name = {r["name"]: r for r in rows}
        # Whole VEN code is bare "0" / "1" — not OTH-001, not SELF-0001
        self.assertEqual(by_name["SELF"]["code"], "0")
        self.assertEqual((by_name["SELF"]["kind"] or "").strip(), "")
        self.assertEqual(by_name["ECHO"]["code"], "1")
        self.assertEqual((by_name["ECHO"]["kind"] or "").strip(), "")
        # First where — kind where, code WHR-…
        self.assertIn("HERE", by_name)
        self.assertEqual((by_name["HERE"]["kind"] or "").strip(), "where")
        self.assertTrue(
            str(by_name["HERE"]["code"] or "").startswith("WHR-"),
            msg=by_name["HERE"]["code"],
        )
        n_inst = self.world.conn.execute(
            "SELECT COUNT(*) AS c FROM instances"
        ).fetchone()["c"]
        self.assertEqual(n_inst, 3)

    def test_self_is_not_the_room(self) -> None:
        """SELF stands in the first where; rename here ≠ rename me."""
        loc = self.world.player_location()
        pid = self.world.player_id()
        self.assertIsNotNone(loc)
        self.assertIsNotNone(pid)
        self.assertNotEqual(loc.id, pid)
        self.assertEqual(loc.ven_kind, "where")
        # Room holds pressure title; SELF prime name stays SELF
        self.assertIn("pressure", (loc.name or "").lower())
        me = self.world.get_instance(pid)
        assert me is not None
        self.assertEqual(me.name, "SELF")
        dispatch(self.world, "rename me as Thinker")
        dispatch(self.world, "rename here as the void stage")
        me2 = self.world.get_instance(pid)
        loc2 = self.world.player_location()
        assert me2 is not None and loc2 is not None
        self.assertEqual(me2.name, "Thinker")
        self.assertEqual(loc2.name, "the void stage")
        self.assertNotEqual(me2.name, loc2.name)

    def test_migration_restores_bare_zero_point_codes(self) -> None:
        """OTH-00N rewrite of 0/1 is repaired on migrate."""
        from miwbs.db import migrate_schema

        self.world.conn.execute(
            "UPDATE vens SET code = ? WHERE upper(name) = ?",
            ("OTH-001", "SELF"),
        )
        self.world.conn.execute(
            "UPDATE vens SET code = ? WHERE upper(name) = ?",
            ("OTH-002", "ECHO"),
        )
        self.world.conn.commit()
        migrate_schema(self.world.conn)
        self.world.conn.commit()
        by_name = {
            r["name"]: r["code"]
            for r in self.world.conn.execute("SELECT name, code FROM vens")
        }
        self.assertEqual(by_name["SELF"], "0")
        self.assertEqual(by_name["ECHO"], "1")

    def test_consider_starts_echo_dialog(self) -> None:
        from miwbs.format import plain

        r = dispatch(self.world, "consider | soft pressure")
        self.assertIn("ECHO", plain(r.message))
        self.assertIsNotNone(self.world.active_dialog)
        self.assertEqual(self.world.active_dialog.partner_name, "ECHO")
        self.assertEqual(self.world.active_dialog.player_name, "SELF")
        # speak turns
        dispatch(self.world, "is there light?")
        dispatch(self.world, "only the sense of something")
        end = dispatch(self.world, "/fin")
        self.assertIsNone(self.world.active_dialog)
        self.assertIn("ended", plain(end.message).lower())

    def test_zero_point_only_where_taught(self) -> None:
        from miwbs import mentor
        from miwbs.format import plain

        allowed = mentor.allowed_kinds(self.world)
        self.assertEqual(allowed, frozenset({"where"}))  # no synonym spam
        self.assertNotIn("person", allowed)
        self.assertNotIn("place", allowed)  # place is alias of where, not a taught key
        r = dispatch(self.world, "create person Bob | a guy")
        self.assertIn("not taught", plain(r.message).lower())
        r2 = dispatch(self.world, "create concept Wonder | a sense of wonder")
        self.assertIn("not taught", plain(r2.message).lower())
        # where taught — create where or place (place folds to where/place)
        r_where = dispatch(self.world, "create where Quiet Nook | a corner")
        self.assertNotIn("not taught", plain(r_where.message).lower())
        r_place = dispatch(self.world, "create place Alcove | a place-like where")
        self.assertNotIn("not taught", plain(r_place.message).lower())
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
        self.assertEqual(cycle_mod.current_face(st), "CYC ʞ.1")
        # back to kras point, insert between will create under 0
        dispatch(self.world, "node prev")
        dispatch(self.world, "node next")  # on 1
        # order 0,1 — go to 1 then insert uses left=0
        dispatch(self.world, "node insert")
        st = cycle_mod.load_state(self.world)
        self.assertTrue(st.current_path.startswith("0."))
        self.assertIn(st.current_path, st.cycles["ʞ"].order)
        # first splice under kras origin shows path under ʞ
        self.assertTrue(
            cycle_mod.current_face(st).startswith("CYC ʞ.ʞ.")
            or cycle_mod.current_face(st).startswith("CYC ʞ.ʞ")
            or cycle_mod.current_face(st) == "CYC ʞ"
        )

    def test_node_plus_intercalates_not_skips(self) -> None:
        """+ after kras with 1 ahead → 0.1 between, never kras · 2 · 1."""
        dispatch(self.world, "node +")  # 0 → 1 at tail
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.cycles["ʞ"].order, ["0", "1"])
        dispatch(self.world, "node prev")  # mark on kras
        dispatch(self.world, "node +")  # intercalate under 0
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.current_path, "0.1")
        self.assertEqual(st.cycles["ʞ"].order, ["0", "0.1", "1"])
        self.assertEqual(cycle_mod.current_face(st), "CYC ʞ.ʞ.1")
        # tail + still grows 2 after 1, not mid-stream
        dispatch(self.world, "node next")  # 1
        dispatch(self.world, "node +")
        st = cycle_mod.load_state(self.world)
        self.assertEqual(st.current_path, "2")
        self.assertEqual(st.cycles["ʞ"].order, ["0", "0.1", "1", "2"])

    def test_node_stream_shorthands(self) -> None:
        from miwbs.format import plain

        r = dispatch(self.world, "n+")
        self.assertIn("CYC ʞ.1", plain(r.message))
        r2 = dispatch(self.world, "n<")
        # origin: just kras (nothing before 0)
        self.assertIn("CYC ʞ", plain(r2.message))
        self.assertNotIn("CYC ʞ.ʞ", plain(r2.message))
        r3 = dispatch(self.world, "n>")
        self.assertIn("CYC ʞ.1", plain(r3.message))
        r4 = dispatch(self.world, "/n+")
        self.assertIn("CYC ʞ.", plain(r4.message))

    def test_consider_note_lore(self) -> None:
        from miwbs.format import plain

        r = dispatch(self.world, "consider note SELF | pressure?")
        self.assertIn("note", plain(r.message).lower())
        r2 = dispatch(self.world, "consider note ECHO | coming through.")
        self.assertIn("ECHO", plain(r2.message))
        listed = dispatch(self.world, "consider note")
        self.assertIn("pressure?", plain(listed.message))


if __name__ == "__main__":
    unittest.main()
