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
        self.assertIn("CRATE", text)
        self.assertIn("TPS", text)
        self.assertIn("EVENT", text)
        self.assertIn("INGEST", text)
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].body, "I am somewhere.")
        self.assertIsNone(crates[0].writer)
        self.assertEqual(crates[0].event_unix, crates[0].ingest_unix)

    def test_consider_event_unix_flag(self) -> None:
        r = dispatch(self.world, "consider I am somewhere -e -100000000")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertIn("u-100000000", text)
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].event_unix, -100000000)
        self.assertNotEqual(crates[0].event_unix, crates[0].ingest_unix)
        self.assertEqual(crates[0].tps_uid, "N100000000")
        self.assertIn("EVENT     u-100000000", text)

    def test_allowlist_blocks_look(self) -> None:
        r = dispatch(self.world, "look")
        self.assertIn("consider", plain(r.message).lower())
        self.assertIn("research", plain(r.message).lower())

    def test_body_via_d_flag(self) -> None:
        r = dispatch(self.world, "consider -d the sky holds")
        self.assertTrue(r.ok, msg=r.message)
        c = ch.load_crates(self.world)[0]
        self.assertEqual(c.body, "the sky holds")
        self.assertEqual(c.title, "")

    def test_bare_consider_is_flat_error_not_list(self) -> None:
        r = dispatch(self.world, "consider")
        text = plain(r.message).lower()
        self.assertIn("consider", text)
        self.assertIn("remember", text)
        self.assertNotIn("[01]", plain(r.message))

    def test_errors_are_vox_slots_not_raw_machine(self) -> None:
        # flags noise → flags-error slot
        r = dispatch(self.world, "consider --not-a-real-flag x")
        text = plain(r.message)
        self.assertIn("ERR", text.upper())
        self.assertIn("flag", text.lower())
        self.assertNotIn("Could not parse flags", text)

        # colorbank bad code
        r2 = dispatch(self.world, "godmode reset colorbank C99")
        t2 = plain(r2.message).lower()
        self.assertIn("c1", t2)
        self.assertIn("err", plain(r2.message).lower())

        # pack missing file
        r3 = dispatch(
            self.world,
            f"import vox {self.path.parent / 'no-such-vox-pack.json'}",
        )
        t3 = plain(r3.message).lower()
        self.assertIn("no pack", t3)
        self.assertIn("err", plain(r3.message).lower())

    def test_list_and_research(self) -> None:
        dispatch(self.world, "consider I am somewhere.")
        dispatch(self.world, "consider I am sometime. -e 0")
        listed = plain(dispatch(self.world, "remember considerations").message)
        self.assertIn("[01]", listed)
        self.assertIn("[02]", listed)
        self.assertIn("ʞ:", listed)
        self.assertNotIn("considered:", listed)
        self.assertNotIn("crate-", listed.lower())  # no instruments on list
        self.assertIn("remember consideration", listed.lower())

        detail = plain(dispatch(self.world, "remember consideration 01").message)
        self.assertIn("I am somewhere.", detail)
        self.assertIn("CRATE", detail)
        self.assertIn("TPS", detail)
        self.assertNotIn("ECHO: Consideration", detail)
        # research consideration still aliases to remember open
        alias = plain(dispatch(self.world, "research consideration 01").message)
        self.assertIn("I am somewhere.", alias)

        # soft spaces on crate id → full report (not rabbit)
        crates = ch.considerations(self.world)
        uid = crates[0].crate_uid  # e.g. C1C-FE3-860
        spaced = uid.replace("-", " ")
        report = plain(dispatch(self.world, f"research crate {spaced}").message)
        self.assertIn("CRATE REPORT", report.upper())
        self.assertIn("I am somewhere.", report)
        self.assertIn(uid, report)
        self.assertIn("CYC", report.upper())
        self.assertIn("mentalor", report.lower())
        # missing id still rabbit/not found
        missing = plain(dispatch(self.world, "research crate ZZZ-ZZZ-999").message)
        self.assertIn("not", missing.lower())

    def test_crate_snapshots_context_fields(self) -> None:
        r = dispatch(self.world, "consider snapshot me please")
        self.assertTrue(r.ok, msg=r.message)
        c = ch.load_crates(self.world)[0]
        self.assertEqual(c.body, "snapshot me please")
        self.assertTrue(c.tps_uid)
        self.assertTrue(c.event_unix)
        self.assertTrue(c.ingest_unix)
        self.assertTrue(c.room)
        self.assertTrue(c.cyc)
        self.assertEqual(c.seed, "mentalor")
        # poster is *who* (ʞ at zero), room is *where* — not the same slot
        self.assertEqual(c.poster, "ʞ")
        self.assertNotEqual(c.poster, c.room)

        kw = ch.crate_face_kwargs(c)
        for key in (
            "crate_uid",
            "tps_uid",
            "event_u",
            "ingest_u",
            "body",
            "poster",
            "room",
            "cyc",
            "seed",
            "seq_label",
        ):
            self.assertIn(key, kw)
            self.assertTrue(str(kw[key]).strip())

    def test_studio_opener_not_stored_as_body(self) -> None:
        from miwbs.multiline_open import (
            commit_multiline_session,
            parse_multiline_opener,
        )

        ml = parse_multiline_opener("consider <<studio")
        self.assertIsNotNone(ml)
        assert ml is not None
        self.assertEqual(ml.kind, "consider")
        self.assertTrue(ml.studio)
        # Must not land as a crate via one-line dispatch
        r = dispatch(self.world, "consider <<studio")
        self.assertIn("studio", plain(r.message).lower())
        self.assertEqual(len(ch.load_crates(self.world)), 0)
        # Commit path stores real body
        result = commit_multiline_session(
            self.world, ml, "Kras wanted the studio."
        )
        self.assertTrue(result.ok)
        self.assertIn("Kras wanted the studio.", plain(result.message))
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].body, "Kras wanted the studio.")

    def test_godmode_face_edit_overrides_hint(self) -> None:
        from miwbs.multiline_open import (
            commit_multiline_session,
            parse_multiline_opener,
            seed_initial_body,
        )

        from miwbs import zero_face as face

        listed = plain(dispatch(self.world, "@god voxlist").message)
        self.assertIn("VOX LIST", listed.upper())
        self.assertIn("not skills", listed.lower())
        self.assertIn("consider-hint", listed)
        self.assertIn("live-echo", listed)
        self.assertIn("A01", listed)
        self.assertIn("L02", listed)
        self.assertIn("success-chrome", listed)
        self.assertIn("CODE", listed)
        # every DEFAULTS slot has a code
        self.assertEqual(set(face.SLOT_CODE), set(face.DEFAULTS))

        # edit by code
        from miwbs.multiline_open import (
            commit_multiline_session,
            parse_multiline_opener,
        )

        ml = parse_multiline_opener("@god edit A01 <<studio")
        self.assertIsNotNone(ml)
        assert ml is not None
        self.assertEqual(ml.face_slot, "live-echo")
        commit_multiline_session(self.world, ml, "coded · {body}")
        r = dispatch(self.world, "consider code works")
        self.assertIn("coded", plain(r.message))
        self.assertIn("code works", plain(r.message))

        # thin aliases
        for cmd in ("@god list", "godmode list", "@god voxlist"):
            self.assertIn(
                "consider-hint",
                plain(dispatch(self.world, cmd).message),
            )

        ml = parse_multiline_opener("@godmode edit consider-hint <<studio")
        self.assertIsNotNone(ml)
        assert ml is not None
        self.assertEqual(ml.kind, "face_edit")
        self.assertEqual(ml.face_slot, "consider-hint")
        seed = seed_initial_body(self.world, ml)
        self.assertIn("remember consideration", seed.lower())

        cute = "HINT: tap remember consideration 01 you absolute legend"
        result = commit_multiline_session(self.world, ml, cute)
        self.assertTrue(result.ok)
        self.assertIn("consider-hint", plain(result.message))

        dispatch(self.world, "consider one note")
        listed2 = plain(dispatch(self.world, "remember considerations").message)
        self.assertIn("absolute legend", listed2)

        # live-echo template
        ml2 = parse_multiline_opener("godmode edit live-echo <<studio")
        assert ml2 is not None
        commit_multiline_session(self.world, ml2, "heard · {body}")
        r = dispatch(self.world, "consider batshit works")
        self.assertIn("heard · batshit works", plain(r.message))

        # reset
        reset = dispatch(self.world, "godmode reset live-echo")
        self.assertIn("reset", plain(reset.message).lower())
        r2 = dispatch(self.world, "consider back to factory")
        self.assertIn("ECHO: back to factory", plain(r2.message))

    def test_godmode_studio_markup_is_parsed_on_print(self) -> None:
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener
        from miwbs.studio_text import is_studio

        ml = parse_multiline_opener("@godmode edit consider-hint <<studio")
        assert ml is not None
        body = "HINT: **tap** remember consideration 01 {c6}you legend{/}"
        result = commit_multiline_session(self.world, ml, body)
        self.assertTrue(result.ok)

        from miwbs import zero_face as face

        raw = face.raw_text("consider-hint", self.world)
        self.assertTrue(is_studio(raw), msg=raw)

        dispatch(self.world, "consider one note")
        listed = dispatch(self.world, "remember considerations").message
        # Rich markup from studio parser (not raw ** or {c6})
        self.assertIn("bold", listed.lower())
        self.assertNotIn("{c6}", listed)
        self.assertNotIn("**tap**", listed)
        self.assertIn("tap", plain(listed).lower())
        self.assertIn("legend", plain(listed).lower())

        # godmode show includes preview section
        shown = dispatch(self.world, "godmode show consider-hint").message
        self.assertIn("preview", plain(shown).lower())

    def test_colorbank_edit_and_studio_codes(self) -> None:
        from miwbs import colorbank as cb
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener
        from miwbs.studio_text import render_studio_text

        view = plain(dispatch(self.world, "godmode view colorbank").message)
        self.assertIn("C1", view)
        self.assertIn("White", view)
        self.assertIn("C8", view)

        r = dispatch(self.world, "godmode edit colorbank C1 -> aabbcc")
        self.assertTrue(r.ok, msg=r.message)
        self.assertEqual(cb.load_bank(self.world)["C1"].hex, "#aabbcc")

        r2 = dispatch(self.world, "godmode edit colorbank C1 name Soft White")
        self.assertTrue(r2.ok)
        self.assertEqual(cb.load_bank(self.world)["C1"].name, "Soft White")

        # studio paint uses code, not name
        painted = render_studio_text("{c1}hi{/}", world=self.world)
        self.assertIn("#aabbcc", painted)
        self.assertIn("hi", plain(painted))

        ml = parse_multiline_opener("@godmode edit live-echo <<studio")
        assert ml is not None
        commit_multiline_session(self.world, ml, "heard {c1}{body}{/}")
        out = dispatch(self.world, "consider peach").message
        self.assertIn("#aabbcc", out)
        self.assertIn("peach", plain(out))

        dispatch(self.world, "godmode reset colorbank C1")
        self.assertEqual(cb.load_bank(self.world)["C1"].hex, "#f3f3f3")

    def test_guy_placeholder_is_last_command(self) -> None:
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener

        ml = parse_multiline_opener("@godmode edit live-echo <<studio")
        assert ml is not None
        commit_multiline_session(
            self.world, ml, "ran: {guy} · said: {body}"
        )
        r = dispatch(self.world, "consider hello guy")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertIn("consider hello guy", text)
        self.assertIn("hello guy", text)

    def test_studio_field_multiline_body_keeps_hang_indent(self) -> None:
        from miwbs.format import plain
        from miwbs.studio_text import render_studio_text

        src = ":list: line one\nline two\nline three"
        rendered = render_studio_text(src)
        text = plain(rendered)
        lines = text.splitlines()
        self.assertGreaterEqual(len(lines), 3)
        # first line has label + value
        self.assertIn("list", lines[0])
        self.assertIn("line one", lines[0])
        # continuations hang under the value column (not col 0)
        for cont in lines[1:]:
            if not cont.strip():
                continue
            self.assertTrue(
                cont.startswith(" "),
                msg=f"expected hang indent, got {cont!r}",
            )
            self.assertIn("line", cont)

        # blank then new field does not steal into previous value
        src2 = ":list: a\nb\n\n:other: z"
        t2 = plain(render_studio_text(src2))
        self.assertIn("other", t2)
        self.assertIn("z", t2)

        # blank ends hang — free line after double break is NOT indented
        src3 = ":list: hung one\nhung two\n\nfree after blank"
        t3 = plain(render_studio_text(src3))
        lines3 = t3.splitlines()
        free = next(ln for ln in lines3 if "free after blank" in ln)
        self.assertFalse(
            free.startswith(" "),
            msg=f"expected no hang after blank break, got {free!r}",
        )
        hung = next(ln for ln in lines3 if "hung two" in ln)
        self.assertTrue(hung.startswith(" "), msg=f"expected hang, got {hung!r}")

    def test_live_echo_studio_color_plus_body_placeholder(self) -> None:
        """Studio {c1}…{/} must not break {body} formatting."""
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener

        ml = parse_multiline_opener("@godmode edit live-echo <<studio")
        assert ml is not None
        # the pattern that used to throw: unexpected { in field name
        commit_multiline_session(
            self.world, ml, "heard {c1}{body}{/}"
        )
        r = dispatch(self.world, "consider I don't mind braces")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertNotIn("unexpected", text.lower())
        self.assertNotIn("face template error", text.lower())
        self.assertIn("heard", text.lower())
        self.assertIn("don't mind braces", text)
        # color applied
        self.assertIn("#f3f3f3", r.message)
        self.assertNotIn("{c1}", r.message)
        self.assertNotIn("{body}", r.message)

    def test_consider_allows_apostrophes(self) -> None:
        r = dispatch(self.world, "consider I don't know yet.")
        self.assertTrue(r.ok, msg=r.message)
        text = plain(r.message)
        self.assertNotIn("Could not parse", text)
        self.assertIn("don't", text)
        crates = ch.load_crates(self.world)
        self.assertEqual(len(crates), 1)
        self.assertEqual(crates[0].body, "I don't know yet.")

        r2 = dispatch(self.world, "consider Kras's note -e 0")
        self.assertTrue(r2.ok, msg=r2.message)
        c2 = ch.load_crates(self.world)[1]
        self.assertEqual(c2.body, "Kras's note")
        self.assertEqual(c2.event_unix, 0)

        r3 = dispatch(self.world, "consider -d it's fine today")
        self.assertTrue(r3.ok, msg=r3.message)
        self.assertEqual(ch.load_crates(self.world)[2].body, "it's fine today")

    def test_export_import_vox_and_viz(self) -> None:
        from miwbs import colorbank as cb
        from miwbs import pack_io
        from miwbs import zero_face as face
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener

        ml = parse_multiline_opener("@godmode edit consider-hint <<studio")
        assert ml is not None
        commit_multiline_session(self.world, ml, "HINT: pack me")
        dispatch(self.world, "godmode edit colorbank C1 -> deadbe")

        vox_path = self.path.parent / "test.vox.json"
        viz_path = self.path.parent / "test.viz.json"
        r1 = dispatch(self.world, f"export vox {vox_path}")
        self.assertTrue(r1.ok, msg=r1.message)
        self.assertTrue(vox_path.is_file())
        r2 = dispatch(self.world, f"export viz {viz_path}")
        self.assertTrue(r2.ok)
        self.assertTrue(viz_path.is_file())

        # wipe overrides
        face.clear_override(self.world, "consider-hint")
        cb.reset_bank(self.world, None)
        self.assertNotIn("pack me", face.raw_text("consider-hint", self.world))
        self.assertEqual(cb.load_bank(self.world)["C1"].hex, "#f3f3f3")

        ri = dispatch(self.world, f"import vox {vox_path}")
        self.assertTrue(ri.ok, msg=ri.message)
        self.assertIn("pack me", face.raw_text("consider-hint", self.world))

        rv = dispatch(self.world, f"import viz {viz_path}")
        self.assertTrue(rv.ok)
        self.assertEqual(cb.load_bank(self.world)["C1"].hex, "#deadbe")

        # default paths resolve under world dir
        out, n = pack_io.export_vox(self.world, pack_io.default_path(self.world, "vox"))
        self.assertGreaterEqual(n, 1)
        self.assertTrue(out.is_file())

    def test_success_slots_are_vox_editable(self) -> None:
        from miwbs.multiline_open import commit_multiline_session, parse_multiline_opener

        # body message
        ml = parse_multiline_opener("@godmode edit godmode-saved <<studio")
        assert ml is not None
        commit_multiline_session(
            self.world, ml, "tucked [{slot}] into the world bag"
        )
        # chrome
        ml2 = parse_multiline_opener("@godmode edit success <<studio")
        assert ml2 is not None
        commit_multiline_session(
            self.world, ml2, "{c5}YAY{/}  {msg}"
        )

        ml3 = parse_multiline_opener("@godmode edit consider-hint <<studio")
        assert ml3 is not None
        result = commit_multiline_session(self.world, ml3, "hi hint")
        text = plain(result.message)
        self.assertIn("YAY", text)
        self.assertIn("consider-hint", text)
        self.assertIn("world bag", text)
        # studio color applied (not raw {c5})
        self.assertNotIn("{c5}", result.message)
        self.assertIn("#6bcb8a", result.message)  # factory C5 green

        # colorbank success body (uses same success chrome → YAY here)
        r = dispatch(self.world, "godmode edit colorbank C2 -> 112233")
        self.assertIn("YAY", plain(r.message).upper())
        self.assertIn("C2", plain(r.message))
        self.assertIn("#112233", plain(r.message))


if __name__ == "__main__":
    unittest.main()
