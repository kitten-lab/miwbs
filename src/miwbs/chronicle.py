"""
HERENOW chronicle — crates + TPS shelves (zero-point history).

Minimal store for considerations first. Not lore rows, not multi-leg HST.
Each consideration is one **crate** on a **TPS** time shelf, with simple meta.
Stable list index: append-only ``seq`` (research consideration 01).
"""

from __future__ import annotations

import json
import re
import secrets
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from .db import get_meta, set_meta

if TYPE_CHECKING:
    from .world import World

META_CRATES = "herenow_crates"
META_HERENOW = "herenow_instance_id"
META_SEQ = "herenow_crate_seq"


def _now_unix() -> int:
    return int(time.time())


def new_crate_uid() -> str:
    """Id body like C1C-FE3-860 (letters shouty; prefix CRATE is the label)."""
    a = secrets.token_hex(2).upper()[:3]
    b = secrets.token_hex(2).upper()[:3]
    c = f"{secrets.randbelow(1000):03d}"
    return f"{a}-{b}-{c}"


def tps_uid_for(event_unix: int) -> str:
    """TPS id body (label is TPS on the face)."""
    if event_unix < 0:
        return f"N{abs(event_unix)}"
    return str(event_unix)


def format_u(unix: int) -> str:
    """Compact face: u1784476371 or u-100000000."""
    return f"u{unix}"


def format_seq(n: int) -> str:
    """Stable list address: 01, 02, … 99, 100, …"""
    if n < 1:
        n = 1
    if n < 100:
        return f"{n:02d}"
    return str(n)


def normalize_code_token(raw: str) -> str:
    """Soft codes: spaces/underscores → dashes; letters upper."""
    s = (raw or "").strip()
    if not s:
        return ""
    s = s.replace("_", "-")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    # strip optional prefixes for matching
    low = s.lower()
    for pref in ("crate-", "tps-"):
        if low.startswith(pref):
            s = s[len(pref) :]
            low = s.lower()
    return s.upper()


@dataclass
class Crate:
    """One historic package (consideration first)."""

    crate_uid: str
    tps_uid: str
    event_unix: int
    ingest_unix: int
    seq: int = 0  # stable research index (append-only)
    kind: str = "consideration"
    body: str = ""
    title: str = ""
    detail: str = ""
    writer: str | None = None
    subject_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Crate:
        return cls(
            crate_uid=str(d.get("crate_uid") or ""),
            tps_uid=str(d.get("tps_uid") or ""),
            event_unix=int(d.get("event_unix") or 0),
            ingest_unix=int(d.get("ingest_unix") or 0),
            seq=int(d.get("seq") or 0),
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
    crates = [Crate.from_dict(x) for x in data if isinstance(x, dict)]
    # Backfill stable seq for older crates (append order)
    changed = False
    max_seq = 0
    for i, c in enumerate(crates):
        if c.seq < 1:
            c.seq = i + 1
            changed = True
        max_seq = max(max_seq, c.seq)
    if changed:
        save_crates(world, crates)
        set_meta(world.conn, META_SEQ, str(max_seq))
    return crates


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


def _next_seq(world: World, crates: list[Crate]) -> int:
    raw = (get_meta(world.conn, META_SEQ, "") or "").strip()
    n = 0
    if raw.isdigit():
        n = int(raw)
    for c in crates:
        n = max(n, c.seq)
    return n + 1


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
    Store one consideration crate (append-only stable seq).

    *event_unix* — story/event time (``-e``); defaults to ingest (now).
    *ingest_unix* — always wall-clock now.
    """
    ingest = _now_unix()
    event = ingest if event_unix is None else int(event_unix)
    crates = load_crates(world)
    seq = _next_seq(world, crates)
    crate = Crate(
        crate_uid=new_crate_uid(),
        tps_uid=tps_uid_for(event),
        event_unix=event,
        ingest_unix=ingest,
        seq=seq,
        kind="consideration",
        body=(body or "").strip(),
        title=(title or "").strip(),
        detail=(detail or "").strip(),
        writer=writer,
        subject_ids=[hid] if (hid := herenow_id(world)) else [],
    )
    crates.append(crate)
    save_crates(world, crates)
    set_meta(world.conn, META_SEQ, str(seq))
    return crate


def considerations(world: World) -> list[Crate]:
    """All considerations in stable seq order."""
    crates = [c for c in load_crates(world) if c.kind == "consideration"]
    crates.sort(key=lambda c: c.seq)
    return crates


def get_consideration_by_seq(world: World, seq: int) -> Crate | None:
    for c in considerations(world):
        if c.seq == seq:
            return c
    return None


def get_crate_by_uid(world: World, token: str) -> Crate | None:
    """Match crate id soft: C1C FE3 860 · crate-C1C-FE3-860 · C1C-FE3-860."""
    want = normalize_code_token(token)
    if not want:
        return None
    for c in load_crates(world):
        got = normalize_code_token(c.crate_uid)
        if got == want or c.crate_uid.upper() == want:
            return c
        # full with prefix already stripped in normalize
        if normalize_code_token(c.crate_uid.replace("crate-", "", 1)) == want:
            return c
    return None


def format_histories_stored(crate: Crate) -> str:
    """Instrument block after a new consideration."""
    lines = [
        "HISTORIES STORED:",
        f"CRATE     {crate.crate_uid}",
        f"TPS       {crate.tps_uid}",
        f"EVENT     {format_u(crate.event_unix)}",
        f"INGEST    {format_u(crate.ingest_unix)}",
    ]
    return "\n".join(lines)


def format_echo_considered(body: str) -> str:
    """Live reply mouth: ECHO: <body>."""
    b = (body or "").strip() or "—"
    return f"ECHO: {b}"


def format_consideration_list(crates: list[Crate]) -> str:
    """
    Index face (no ECHO header, no crate/tps on the line)::

        [01]  ʞ:  I am somewhere.
        [02]  ʞ:  I am sometime.
    """
    from . import format as fmt

    if not crates:
        return fmt.hint(
            "No considerations yet.\n"
            "  consider <text>  ·  -d <text>  ·  -e <unix>  ·  <<studio"
        )
    sw = fmt.SOFT_WHITE
    lines: list[str] = []
    for c in crates:
        body = (c.body or "—").strip()
        n = format_seq(c.seq)
        lines.append(
            f"[{sw}][{n}]  ʞ:  {fmt.safe(body)}[/{sw}]"
        )
    lines.append("")
    lines.append(
        fmt.hint("research consideration 01  ·  open a consideration by number")
    )
    return "\n".join(lines)


def format_consideration_detail(crate: Crate) -> str:
    """
    research consideration 01::

        ʞ:  I am somewhere.

        CRATE   C1C-FE3-860
        TPS     1784478058
    """
    from . import format as fmt

    sw = fmt.SOFT_WHITE
    body = (crate.body or "—").strip()
    lines = [
        f"[{sw}]ʞ:  {fmt.safe(body)}[/{sw}]",
        "",
        f"[dim]CRATE   {fmt.safe(crate.crate_uid)}[/dim]",
        f"[dim]TPS     {fmt.safe(crate.tps_uid)}[/dim]",
        "",
        fmt.hint(
            f"research crate {crate.crate_uid}  ·  follow the white rabbit (soon)"
        ),
    ]
    return "\n".join(lines)


def format_crate_rabbit(token: str) -> str:
    """Stub report until real crate report exists."""
    from . import format as fmt

    return "\n".join(
        [
            fmt.hint("Followed the white rabbit!"),
            fmt.hint(
                f"(crate {token} — real report data soon!  —management)"
            ),
        ]
    )
