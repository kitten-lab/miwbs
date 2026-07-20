"""
Simple vox / viz pack export & import (JSON files).

Survive reseed / move worlds::

    export vox
    export viz
    import vox
    import viz
    export vox path\\my-mouth.vox.json
    import viz path\\soft.viz.json

*vox*  — face slot overrides (godmode mouth), only slots that differ from factory  
         plus optional full snapshot flag later; for now: all **current overrides**
         and, when exporting, also any slot you want — we export **overrides only**
         (what reseed kills). If you need factory-inlined full voice, use
         ``export vox --full`` to dump every slot's current raw text as a pack.

*viz*  — colorbank C1–C8 (name + hex) as currently resolved (factory merged).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from . import colorbank as cb
from . import zero_face as face
from .db import get_meta

PackKind = Literal["vox", "viz"]

VOX_VERSION = 1
VIZ_VERSION = 1

DEFAULT_VOX_NAME = "face.vox.json"
DEFAULT_VIZ_NAME = "colorbank.viz.json"


def world_dir(world: Any) -> Path:
    """Directory of the open world db, or cwd if in-memory / unknown."""
    try:
        row = world.conn.execute("PRAGMA database_list").fetchone()
        # columns: seq, name, file
        if row is not None:
            keys = row.keys() if hasattr(row, "keys") else []
            path = row["file"] if "file" in keys else (row[2] if len(row) > 2 else "")
            if path:
                p = Path(path)
                if p.parent.is_dir():
                    return p.parent
    except Exception:  # noqa: BLE001
        pass
    return Path.cwd()


def default_path(world: Any, kind: PackKind) -> Path:
    name = DEFAULT_VOX_NAME if kind == "vox" else DEFAULT_VIZ_NAME
    return world_dir(world) / name


def resolve_path(world: Any, kind: PackKind, raw: str | None) -> Path:
    s = (raw or "").strip().strip('"').strip("'")
    if not s:
        return default_path(world, kind)
    p = Path(s).expanduser()
    if not p.is_absolute():
        p = world_dir(world) / p
    return p


# ── vox ────────────────────────────────────────────────────────────────

def build_vox_payload(world: Any, *, full: bool = False) -> dict[str, Any]:
    """
    full=False → only world overrides (what reseed wipes).
    full=True  → every slot's current raw text (override or factory).
    """
    if full:
        slots = {s: face.raw_text(s, world) for s in face.known_slots()}
    else:
        slots = dict(face.load_overrides(world))
    return {
        "kind": "vox",
        "version": VOX_VERSION,
        "full": bool(full),
        "slots": slots,
    }


def apply_vox_payload(world: Any, data: dict[str, Any], *, merge: bool = True) -> int:
    """
    Apply pack. *merge*: keep other overrides; False replaces all face overrides.
    Returns number of slots written.
    """
    if not isinstance(data, dict):
        raise ValueError("vox pack must be a JSON object")
    kind = str(data.get("kind") or "vox").lower()
    if kind not in ("vox", "face", "face_overrides"):
        raise ValueError(f"not a vox pack (kind={kind!r})")
    slots = data.get("slots")
    if not isinstance(slots, dict):
        raise ValueError("vox pack missing slots object")
    if not merge:
        # clear all overrides then write
        from .db import set_meta

        set_meta(world.conn, face.FACE_META_KEY, json.dumps({}, ensure_ascii=False))
    n = 0
    for key, val in slots.items():
        sk = face.normalize_slot(str(key))
        if not face.is_slot(sk):
            continue
        if not isinstance(val, str):
            continue
        face.save_override(world, sk, val)
        n += 1
    return n


def export_vox(world: Any, path: Path, *, full: bool = False) -> tuple[Path, int]:
    payload = build_vox_payload(world, full=full)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path, len(payload["slots"])


def import_vox(world: Any, path: Path, *, merge: bool = True) -> tuple[Path, int]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no file {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    n = apply_vox_payload(world, data, merge=merge)
    return path, n


# ── viz ────────────────────────────────────────────────────────────────

def build_viz_payload(world: Any) -> dict[str, Any]:
    bank = cb.load_bank(world)
    return {
        "kind": "viz",
        "version": VIZ_VERSION,
        "slots": {code: bank[code].to_dict() for code in cb.CODES},
    }


def apply_viz_payload(world: Any, data: dict[str, Any]) -> int:
    if not isinstance(data, dict):
        raise ValueError("viz pack must be a JSON object")
    kind = str(data.get("kind") or "viz").lower()
    if kind not in ("viz", "colorbank", "palette"):
        raise ValueError(f"not a viz pack (kind={kind!r})")
    slots = data.get("slots")
    if not isinstance(slots, dict):
        raise ValueError("viz pack missing slots object")
    bank = cb.factory_bank()
    n = 0
    for key, val in slots.items():
        code = cb.normalize_code(str(key))
        if not code or code not in bank:
            continue
        if isinstance(val, dict):
            bank[code] = cb.ColorSlot.from_dict(val, bank[code])
            n += 1
        elif isinstance(val, str):
            hx = cb.normalize_hex(val)
            if hx:
                bank[code] = cb.ColorSlot(code=code, name=bank[code].name, hex=hx)
                n += 1
    cb.save_bank(world, bank)
    return n


def export_viz(world: Any, path: Path) -> tuple[Path, int]:
    payload = build_viz_payload(world)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path, len(payload["slots"])


def import_viz(world: Any, path: Path) -> tuple[Path, int]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"no file {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    n = apply_viz_payload(world, data)
    return path, n
