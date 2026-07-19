"""
HERENOW chronicle — crates + TPS shelves (zero-point history).

Minimal store for considerations first. Not lore rows, not multi-leg HST.
Each consideration is one **crate** on a **TPS** time shelf, with simple meta.
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from .db import get_meta, set_meta

if TYPE_CHECKING:
    from .world import World

META_CRATES = "herenow_crates"
META_HERENOW = "herenow_instance_id"


def _now_unix() -> int:
    return int(time.time())


def new_crate_uid() -> str:
    """Face id like crate-1F3-S44-111."""
    a = secrets.token_hex(2).upper()[:3]
    b = secrets.token_hex(2).upper()[:3]
    c = f"{secrets.randbelow(1000):03d}"
    return f"crate-{a}-{b}-{c}"


def tps_uid_for(event_unix: int) -> str:
    # Avoid tps--100 form; keep face readable
    if event_unix < 0:
        return f"tps-n{abs(event_unix)}"
    return f"tps-{event_unix}"


def format_u(unix: int) -> str:
    """Compact face: u1784476371 or u-100000000."""
    return f"u{unix}"


@dataclass
class Crate:
    """One historic package (consideration first)."""

    crate_uid: str
    tps_uid: str
    event_unix: int
    ingest_unix: int
    kind: str = "consideration"  # later: thought, act, …
    body: str = ""
    title: str = ""
    detail: str = ""  # -d
    writer: str | None = None  # NULL at zero — no SELF yet
    subject_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Crate:
        return cls(
            crate_uid=str(d.get("crate_uid") or ""),
            tps_uid=str(d.get("tps_uid") or ""),
            event_unix=int(d.get("event_unix") or 0),
            ingest_unix=int(d.get("ingest_unix") or 0),
            kind=str(d.get("kind") or "consideration"),
            body=str(d.get("body") or ""),
            title=str(d.get("title") or ""),
            detail=str(d.get("detail") or ""),
            writer=d.get("writer"),
            subject_ids=[str(x) for x in (d.get("subject_ids") or [])],
            meta=dict(d.get("meta") or {}),
        )


def load_crates(world: World) -> list[Crate]:
    raw = get_meta(world.conn, META_CRATES, "") or ""
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [Crate.from_dict(x) for x in data if isinstance(x, dict)]


def save_crates(world: World, crates: list[Crate]) -> None:
    set_meta(
        world.conn,
        META_CRATES,
        json.dumps([c.to_dict() for c in crates], ensure_ascii=False),
    )


def herenow_id(world: World) -> str | None:
    return (get_meta(world.conn, META_HERENOW, "") or "").strip() or None


def set_herenow_id(world: World, instance_id: str) -> None:
    set_meta(world.conn, META_HERENOW, instance_id)


def append_consideration(
    world: World,
    *,
    body: str,
    title: str = "",
    detail: str = "",
    event_unix: int | None = None,
    writer: str | None = None,
) -> Crate:
    """
    Store one consideration crate.

    *event_unix* — story/event time (``-u``); defaults to ingest (now).
    *ingest_unix* — always wall-clock now (when you typed it).
    TPS shelf keys the **event** time (time door); crate is the package.
    """
    ingest = _now_unix()
    event = ingest if event_unix is None else int(event_unix)
    crate = Crate(
        crate_uid=new_crate_uid(),
        tps_uid=tps_uid_for(event),
        event_unix=event,
        ingest_unix=ingest,
        kind="consideration",
        body=(body or "").strip(),
        title=(title or "").strip(),
        detail=(detail or "").strip(),
        writer=writer,  # None at zero
        subject_ids=[hid] if (hid := herenow_id(world)) else [],
    )
    crates = load_crates(world)
    crates.append(crate)
    save_crates(world, crates)
    return crate


def format_histories_stored(crate: Crate) -> str:
    """
    Face block after a consideration::

        HISTORIES STORED:
        CRATE cUID:     crate-1F3-S44-111
        TPS tUID:       tps-1784476371
        EVENT_TIME:     u1784476371
        INGEST_TIME:    u1784476371
    """
    lines = [
        "HISTORIES STORED:",
        f"CRATE cUID:     {crate.crate_uid}",
        f"TPS tUID:       {crate.tps_uid}",
        f"EVENT_TIME:     {format_u(crate.event_unix)}",
        f"INGEST_TIME:    {format_u(crate.ingest_unix)}",
    ]
    return "\n".join(lines)


def format_echo_considered(body: str) -> str:
    """ECHO: You considered: …"""
    b = (body or "").strip() or "—"
    return f"ECHO: You considered: {b}"
