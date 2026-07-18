"""Hidden mentor workshop (merged from ven-mentor) — empty bootstrap."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from miwbs.mentor_workshop import Workshop


class MentorWorkshopTests(unittest.TestCase):
    def test_empty_bootstrap_and_mint_type(self) -> None:
        tmp = Path(tempfile.mkdtemp()) / "w.json"
        ws = Workshop(tmp)
        self.assertEqual(ws.types, {})
        self.assertEqual(ws.properties, {})
        t = ws.mint_type("quai", "atomic residue")
        self.assertTrue(t.code.startswith("PVT-"))
        self.assertIn("quai", ws.types)
