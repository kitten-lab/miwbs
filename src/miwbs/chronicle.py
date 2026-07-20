"""
HERENOW chronicle — crates + TPS shelves (zero-point history).

Minimal store for considerations first. Not lore rows, not multi-leg HST.
Each consideration is one **crate** on a **TPS** time shelf, with simple meta.
Stable list index: append-only ``seq`` (research consideration 01).

Crate snapshot at store time:
  body, tps, event, ingest, poster, room, cyc, seed (+ ids/seq).
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
    """One historic package (consideration first). Snapshot frozen at store."""

    crate_uid: str
    tps_uid: str
    event_unix: int
    ingest_unix: int
    seq: int = 0  # stable research index (append-only)
    kind: str = "consideration"
    body: str = ""
    title: str = ""
    detail: str = ""
    # Snapshot context (names/addresses as strings at store time)
    poster: str = ""  # who posted (writer face; may be empty at zero)
    room: str = ""  # room / surface name at storage
    cyc: str = ""  # cycle face address e.g. CYC ʞ
    seed: str = ""  # starting seed name (e.g. mentalor)
    writer: str | None = None  # optional id; poster is the face string
    subject_ids: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Crate:
        meta = dict(d.get("meta") or {})
        # legacy: context may have lived only in meta
        poster = str(d.get("poster") if d.get("poster") is not None else meta.get("poster") or "")
        room = str(d.get("room") if d.get("room") is not None else meta.get("room") or "")
        cyc = str(d.get("cyc") if d.get("cyc") is not None else meta.get("cyc") or "")
        seed = str(d.get("seed") if d.get("seed") is not None else meta.get("seed") or "")
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
            poster=poster,
            room=room,
            cyc=cyc,
            seed=seed,
            writer=d.get("writer"),
            subject_ids=[str(x) for x in (d.get("subject_ids") or [])],
            meta=meta,
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


def snapshot_store_context(world: World) -> dict[str, str]:
    """
    Freeze room / cyc / seed / poster for a new crate.

    Two different meanings (do not collapse)::

      room   — *where* (surface / herenow / node title at store)
      poster — *who*   (writer face; not the room name)

    Zero-point has no SELF cast yet. Poster defaults to ʞ (unsigned self mark)
    or meta ``poster_name`` if you set one — never copies room.
    """
    room = "HERENOW"
    cyc = "CYC ʞ"
    seed = (
        (get_meta(world.conn, "seed_name", "") or "").strip()
        or (get_meta(world.conn, "seed_flavor", "") or "").strip()
        or (get_meta(world.conn, "seed_version", "") or "").strip()
        or "mentalor"
    )

    # ── room: place / surface ─────────────────────────────────────────
    hid = herenow_id(world) or world.player_id()
    if hid:
        try:
            inst = world.get_instance(hid)
            if inst is not None:
                # display name of the surface (may be poetic override)
                name = (getattr(inst, "name", None) or "").strip()
                ven = (getattr(inst, "ven_name", None) or "").strip()
                if name:
                    room = name
                elif ven:
                    room = ven
        except Exception:  # noqa: BLE001
            pass

    try:
        from . import cycle as cycle_mod

        if cycle_mod.is_mentalor(world):
            st = cycle_mod.load_state(world)
            cyc = cycle_mod.current_face(st)
            node = cycle_mod.current_node(st)
            # Node title is the cycle-surface room name when set
            if node and (node.title or "").strip():
                room = node.title.strip()
    except Exception:  # noqa: BLE001
        pass

    # ── poster: who (never room) ──────────────────────────────────────
    # Explicit author face meta (godmode/later mint), else kras unsigned.
    poster = (
        (get_meta(world.conn, "poster_name", "") or "").strip()
        or (get_meta(world.conn, "author_name", "") or "").strip()
        or "ʞ"
    )

    return {
        "poster": poster,
        "room": room,
        "cyc": cyc,
        "seed": seed,
    }


def crate_face_kwargs(crate: Crate) -> dict[str, str]:
    """
    All ``{slug}`` injects for face paint / research crate report.

    Prefer these names in godmode templates.
    """
    seq_label = format_seq(crate.seq)
    event_u = format_u(crate.event_unix)
    ingest_u = format_u(crate.ingest_unix)
    body = (crate.body or "").strip() or "—"
    poster = (crate.poster or "").strip() or "—"
    room = (crate.room or "").strip() or "—"
    cyc = (crate.cyc or "").strip() or "—"
    seed = (crate.seed or "").strip() or "—"
    crate_uid = crate.crate_uid or "—"
    tps_uid = crate.tps_uid or "—"
    return {
        # ids
        "crate_uid": crate_uid,
        "crate_id": crate_uid,
        "crate": crate_uid,
        "tps_uid": tps_uid,
        "tps_id": tps_uid,
        "tps": tps_uid,
        # times
        "event_unix": str(crate.event_unix),
        "event_u": event_u,
        "event": event_u,
        "ingest_unix": str(crate.ingest_unix),
        "ingest_u": ingest_u,
        "ingest": ingest_u,
        # content
        "body": body,
        "title": (crate.title or "").strip(),
        "detail": (crate.detail or "").strip(),
        # snapshot context
        "poster": poster,
        "room": room,
        "cyc": cyc,
        "cyc_position": cyc,
        "seed": seed,
        "seed_name": seed,
        # index
        "seq": str(crate.seq),
        "seq_label": seq_label,
        "kind": crate.kind or "consideration",
    }


def append_consideration(
    world: World,
    *,
    body: str,
    title: str = "",
    detail: str = "",
    event_unix: int | None = None,
    writer: str | None = None,
    poster: str | None = None,
) -> Crate:
    """
    Store one consideration crate (append-only stable seq).

    *event_unix* — story/event time (``-e``); defaults to ingest (now).
    *ingest_unix* — always wall-clock now.
    Snapshots room / cyc / seed / poster at store time.
    """
    ingest = _now_unix()
    event = ingest if event_unix is None else int(event_unix)
    crates = load_crates(world)
    seq = _next_seq(world, crates)
    ctx = snapshot_store_context(world)
    if poster is not None:
        ctx["poster"] = (poster or "").strip()
    elif writer:
        ctx["poster"] = str(writer).strip()

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
        poster=ctx["poster"],
        room=ctx["room"],
        cyc=ctx["cyc"],
        seed=ctx["seed"],
        writer=writer,
        subject_ids=[hid] if (hid := herenow_id(world)) else [],
        meta={
            "poster": ctx["poster"],
            "room": ctx["room"],
            "cyc": ctx["cyc"],
            "seed": ctx["seed"],
        },
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


def format_histories_stored(crate: Crate, world=None) -> str:
    """Instrument block after a new consideration — copy in zero_face."""
    from . import zero_face as face

    return face.live_histories_stored(world=world, **crate_face_kwargs(crate))


def format_echo_considered(body: str, world=None) -> str:
    """Live reply mouth — copy in zero_face."""
    from . import zero_face as face

    return face.live_echo(body, world=world)


def format_consideration_list(crates: list[Crate], world=None) -> str:
    """Index face — copy in zero_face."""
    from . import zero_face as face

    rows = [(format_seq(c.seq), (c.body or "—").strip()) for c in crates]
    return face.list_face(rows, world=world)


def format_consideration_detail(crate: Crate, world=None) -> str:
    """research consideration N — copy in zero_face."""
    from . import zero_face as face

    return face.research_consideration_detail(world=world, **crate_face_kwargs(crate))


def format_crate_report(crate: Crate, world=None) -> str:
    """research crate <uid> — full report face."""
    from . import zero_face as face

    return face.research_crate_report(world=world, **crate_face_kwargs(crate))


def format_crate_rabbit(token: str, world=None) -> str:
    """Missing crate — stub / not found face."""
    from . import zero_face as face

    return face.research_crate_rabbit(token, world=world)
