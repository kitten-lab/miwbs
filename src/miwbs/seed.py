"""World seeds — zero point (mentalor) only."""

from __future__ import annotations

import sqlite3

from .db import init_schema, set_meta
from .world import World

SEED_FLAVORS = ("mentalor", "miwbs", "day-of-days", "ʞ", "k")


def seed_world(conn: sqlite3.Connection, flavor: str = "mentalor") -> None:
    """Seed a new world. Only Day of Days / mentalor is supported."""
    flavor = (flavor or "mentalor").lower().strip()
    if flavor not in SEED_FLAVORS and flavor not in ("", "default"):
        # Still seed mentalor; unknown flavors do not load classic ports
        pass
    seed_world_mentalor(conn)


def seed_world_mentalor(conn: sqlite3.Connection) -> None:
    """
    Day of Days — strict zero.

    HERENOW only. Writer NULL. Empty workshop. consider → crate + TPS.
    """
    from . import chronicle as chronicle_mod
    from . import cycle as cycle_mod

    init_schema(conn)
    w = World(conn)

    cycle_mod.set_mentalor_mode(w, True)

    hn_ven = w.create_ven(
        "HERENOW",
        "",
        "The first sense of herenow — space before cast, before type.",
    )
    hn_inst = w.instantiate(hn_ven)
    w.set_name_override(hn_inst, "the pressure of something")
    w.set_description(hn_inst, "")
    chronicle_mod.set_herenow_id(w, hn_inst)
    w.set_player(hn_inst)

    set_meta(conn, "world_name", "Day of Days")
    set_meta(conn, "seed_version", "mentalor-ʞ-7")
    st = cycle_mod.default_state()
    cycle_mod.save_state(w, st)
    cycle_mod.apply_node_to_surface(
        w, cycle_mod.ensure_current(st), cycle_mod.current_face(st)
    )
