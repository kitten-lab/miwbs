"""Zero-point consider → crate + TPS chronicle."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miwbs import chronicle as ch
from miwbs.cli import ensure_world
from miwbs.commands import dispatch
from miwbs.format import plain


class ConsiderChronicleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(tempfile.mkdtemp()) / "zero.world.db"
        self.world = ensure_world(self.path, reseed=True, seed="mentalor")

    def test_seed_is_herenow_only(self) -> None:
        names = [
            r["name"]
            for r in self.world.conn.execute("SELECT name FROM vens")
        ]
        self.assertEqual(names, ["HERENOW"])
        self.assertEqual(ch.herenow_id(self.world), self.world.player_id())

    def test_consider_stores_crate_and_prints(self) -> None:
        r = dispatch(self.world, "consider I am somewhere.")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertIn("ECHO: I am somewhere.", text)
        self.assertIn("HISTORIES STORED:", text)
        self.assertIn("CRATE cUID:", text)
        self.assertIn("TPS tUID:", text)
        self.assertIn("EVENT_TIME:", text)
        self.assertIn("INGEST_TIME:", text)
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].body, "I am somewhere.")
        self.assertIsNone(crates[0].writer)
        self.assertEqual(crates[0].event_unix, crates[0].ingest_unix)

    def test_consider_event_unix_flag(self) -> None:
        r = dispatch(self.world, "consider I am somewhere -u -100000000")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertIn("u-100000000", text)
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].event_unix, -100000000)
        self.assertNotEqual(crates[0].event_unix, crates[0].ingest_unix)
        self.assertIn("tps-n100000000", crates[0].tps_uid)
        self.assertIn("EVENT_TIME:     u-100000000", text)

    def test_allowlist_blocks_look(self) -> None:
        r = dispatch(self.world, "look")
        self.assertIn("only consider", plain(r.message).lower())

    def test_title_and_detail_flags(self) -> None:
        r = dispatch(
            self.world,
            "consider the sky holds -t Opening -d a soft line",
        )
        self.assertTrue(r.ok, msg=r.message)
        c = ch.load_crates(self.world)[0]
        self.assertEqual(c.body, "the sky holds")
        self.assertEqual(c.title, "Opening")
        self.assertEqual(c.detail, "a soft line")


if __name__ == "__main__":
    unittest.main()
