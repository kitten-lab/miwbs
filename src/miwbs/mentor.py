"""
VEN Mentor — production machinery inside MIWBS (hidden from first-verbs help).

Day of Days doctrine:
  - World starts with concept primes only (SELF + Concept).
  - Types are taught in this workshop as thinking produces them — not ambient
    person/place/bin KINDS.
  - create_ven in mentalor mode only allows kinds that exist as mentor types.

Usage later (when face verbs arrive)::

    from miwbs import mentor
    ws = mentor.workshop_for(world)
    ws.mint_type("place", "the sense of location")
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from .db import get_meta, set_meta
from .mentor_skyline import skyline_fail, skyline_ok
from .mentor_workshop import Workshop, parse_flags

if TYPE_CHECKING:
    from .world import World

META_WORKSHOP_PATH = "mentor_workshop_path"

__all__ = [
    "Workshop",
    "parse_flags",
    "skyline_ok",
    "skyline_fail",
    "workshop_for",
    "bootstrap_world_workshop",
    "allowed_kinds",
    "assert_kind_allowed",
]


def _workshop_root() -> Path:
    d = Path.home() / ".aidm" / "miwbs" / "workshops"
    d.mkdir(parents=True, exist_ok=True)
    return d


def workshop_path_for(world: World) -> Path:
    """Stable workshop file per world DB (path stored in meta)."""
    existing = get_meta(world.conn, META_WORKSHOP_PATH, "") or ""
    if existing.strip():
        return Path(existing.strip())
    # Fingerprint: world_name + first ven id if any
    wname = get_meta(world.conn, "world_name", "world") or "world"
    row = world.conn.execute(
        "SELECT id FROM vens ORDER BY created_at LIMIT 1"
    ).fetchone()
    seed = f"{wname}:{row['id'] if row else 'empty'}"
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    path = _workshop_root() / f"{h}.workshop.json"
    set_meta(world.conn, META_WORKSHOP_PATH, str(path))
    return path


def workshop_for(world: World) -> Workshop:
    return Workshop(workshop_path_for(world))


def bootstrap_world_workshop(
    world: World,
    initial_types: tuple[str, ...] = ("where",),
) -> Workshop:
    """
    Ensure mentor workshop exists with the given types.

    Day of Days default: **where** only — first floor of being (the room).
    person/thing/etc. are minted later when thinking produces them.
    """
    ws = workshop_for(world)
    # Fresh workshop still empty of types after Workshop.__init__
    for name in initial_types:
        key = name.strip().lower()
        if not key or key in ws.types:
            continue
        desc = {
            "where": (
                "The sense of Where — location, stage, room. "
                "First taught type: you stand in a where; you are not the where."
            ),
            "place": (
                "The sense of Where (place) — location, stage, room. "
                "First taught type: you stand in a where; you are not the where."
            ),
            "concept": (
                "The sense of Concept — root type. Primes of this kind "
                "(SELF, Concept) stand before person/place/thing."
            ),
        }.get(key, f"Type taught at Day of Days: {key}.")
        try:
            ws.mint_type(key, desc)
        except ValueError:
            pass
    return ws


def allowed_kinds(world: World) -> frozenset[str]:
    """
    Typed kinds legal for create in this world.

    Mentalor: only mentor-taught types. Day of Days starts with **where**
    (location / first room). Untyped VENs (kind "") stay separate (SELF=0).
    Classic seeds: full KINDS table.
    """
    from . import cycle as cycle_mod
    from .world import KIND_ALIASES, KINDS

    if not cycle_mod.is_mentalor(world):
        return frozenset(KINDS)
    ws = workshop_for(world)
    keys = set(ws.types.keys())
    # where ↔ place: teach either name, allow both at create
    if "where" in keys or "place" in keys:
        keys.add("where")
        keys.add("place")
    # Also accept alias keys that fold into a taught root
    for alias, root in KIND_ALIASES.items():
        if root in keys:
            keys.add(alias)
    return frozenset(keys)


def assert_kind_allowed(world: World, kind: str) -> None:
    """Raise ValueError if kind is not mentored yet (mentalor) / unknown."""
    k = (kind or "").strip().lower()
    if k in ("", "none", "untyped", "-", "ven", "0", "null"):
        return  # untyped zero-point issuance
    allowed = allowed_kinds(world)
    if k not in allowed:
        from . import cycle as cycle_mod

        if cycle_mod.is_mentalor(world):
            if not allowed:
                raise ValueError(
                    f"type {k!r} is not taught yet. "
                    f"At zero point no types exist — teach type "
                    f"(e.g. concept) as thinking produces it."
                )
            shown = ", ".join(sorted(allowed))
            raise ValueError(
                f"type {k!r} is not taught yet. "
                f"Only mentored types may be formed: {shown}. "
                f"(Teach new types as thinking produces them.)"
            )
        raise ValueError(f"Unknown kind {k!r}; expected one of {tuple(sorted(allowed))}")
