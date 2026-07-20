"""
Viz colorbank — fixed 8 slots (C1–C8), name + hex, world-local overrides.

Studio markup uses **codes** only: ``{c1}text{/}`` / ``{C3}text{/}``.
Slot **names** are labels for humans (godmode view); they do not paint.

Godmode is the only door::

    @godmode view colorbank
    @godmode edit colorbank C1 -> f3f3f3
    @godmode edit colorbank C1 name Soft White
    @godmode edit colorbank C3 Orange Crush -> ff8800
    @godmode reset colorbank
    @godmode reset colorbank C2
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .db import get_meta, set_meta

META_KEY = "viz_colorbank"

# Studio paint codes (canonical)
CODES: tuple[str, ...] = tuple(f"C{i}" for i in range(1, 9))  # C1..C8

# Factory viz — name is label only; hex is what paints
# Order: White, Gray, Red, Blue, Green, Yellow, Purple, Orange
_FACTORY: tuple[tuple[str, str, str], ...] = (
    ("C1", "White", "#f3f3f3"),
    ("C2", "Gray", "#9a9aa3"),
    ("C3", "Red", "#e85d5d"),
    ("C4", "Blue", "#6aa6e8"),
    ("C5", "Green", "#6bcb8a"),
    ("C6", "Yellow", "#e8c84a"),
    ("C7", "Purple", "#b07ce8"),
    ("C8", "Orange", "#e89a4a"),
)

# Non-palette style tokens (still allowed in studio; not colorbank slots)
_STYLE_TOKENS: dict[str, str] = {
    "dim": "dim",
    "bright": "bold",  # emphasis, not a bank color
}


@dataclass
class ColorSlot:
    code: str  # C1
    name: str  # White
    hex: str  # #f3f3f3

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "name": self.name, "hex": self.hex}

    @staticmethod
    def from_dict(d: dict[str, Any], fallback: "ColorSlot") -> "ColorSlot":
        code = normalize_code(str(d.get("code") or fallback.code)) or fallback.code
        name = str(d.get("name") or fallback.name).strip() or fallback.name
        hx = normalize_hex(str(d.get("hex") or fallback.hex)) or fallback.hex
        return ColorSlot(code=code, name=name, hex=hx)


def factory_bank() -> dict[str, ColorSlot]:
    return {
        code: ColorSlot(code=code, name=name, hex=hx)
        for code, name, hx in _FACTORY
    }


def normalize_code(raw: str) -> str | None:
    """
    Accept C1, c1, 1, 01, C01 → C1 … C8.
    """
    s = (raw or "").strip().upper().replace(" ", "")
    if not s:
        return None
    m = re.fullmatch(r"C0*([1-8])", s)
    if m:
        return f"C{m.group(1)}"
    m2 = re.fullmatch(r"0*([1-8])", s)
    if m2:
        return f"C{m2.group(1)}"
    return None


def normalize_hex(raw: str) -> str | None:
    """
    Accept f3f3f3, #f3f3f3, #abc → #f3f3f3 / #aabbcc.
    """
    s = (raw or "").strip().lower()
    if s.startswith("#"):
        s = s[1:]
    if re.fullmatch(r"[0-9a-f]{3}", s):
        s = "".join(ch * 2 for ch in s)
    if re.fullmatch(r"[0-9a-f]{6}", s):
        return f"#{s}"
    return None


def load_bank(world: Any | None = None) -> dict[str, ColorSlot]:
    bank = factory_bank()
    if world is None:
        return bank
    raw = get_meta(world.conn, META_KEY, "") or ""
    if not raw.strip():
        return bank
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return bank
    if not isinstance(data, dict):
        return bank
    slots = data.get("slots") if "slots" in data else data
    if not isinstance(slots, dict):
        return bank
    for key, val in slots.items():
        code = normalize_code(str(key))
        if not code or code not in bank:
            continue
        if isinstance(val, dict):
            bank[code] = ColorSlot.from_dict(val, bank[code])
        elif isinstance(val, str):
            hx = normalize_hex(val)
            if hx:
                bank[code] = ColorSlot(code=code, name=bank[code].name, hex=hx)
    return bank


def save_bank(world: Any, bank: dict[str, ColorSlot]) -> None:
    payload = {
        "slots": {code: bank[code].to_dict() for code in CODES if code in bank}
    }
    set_meta(world.conn, META_KEY, json.dumps(payload, ensure_ascii=False, indent=2))


def reset_bank(world: Any, code: str | None = None) -> None:
    """Reset one slot or entire bank to factory."""
    if code is None:
        set_meta(world.conn, META_KEY, json.dumps({"slots": {}}, ensure_ascii=False))
        return
    c = normalize_code(code)
    if not c:
        return
    bank = load_bank(world)
    fac = factory_bank()
    bank[c] = fac[c]
    # If everything matches factory, clear meta
    if all(
        bank[k].name == fac[k].name and bank[k].hex == fac[k].hex for k in CODES
    ):
        set_meta(world.conn, META_KEY, json.dumps({"slots": {}}, ensure_ascii=False))
    else:
        save_bank(world, bank)


def set_slot_hex(world: Any, code: str, hex_raw: str) -> ColorSlot:
    c = normalize_code(code)
    if not c:
        raise ValueError(f"bad color code {code!r} (use C1–C8)")
    hx = normalize_hex(hex_raw)
    if not hx:
        raise ValueError(f"bad hex {hex_raw!r} (use f3f3f3 or #f3f3f3)")
    bank = load_bank(world)
    bank[c] = ColorSlot(code=c, name=bank[c].name, hex=hx)
    save_bank(world, bank)
    return bank[c]


def set_slot_name(world: Any, code: str, name: str) -> ColorSlot:
    c = normalize_code(code)
    if not c:
        raise ValueError(f"bad color code {code!r} (use C1–C8)")
    nm = (name or "").strip()
    if not nm:
        raise ValueError("name cannot be empty")
    if len(nm) > 32:
        raise ValueError("name too long (max 32)")
    bank = load_bank(world)
    bank[c] = ColorSlot(code=c, name=nm, hex=bank[c].hex)
    save_bank(world, bank)
    return bank[c]


def set_slot(world: Any, code: str, *, name: str | None = None, hex_raw: str | None = None) -> ColorSlot:
    c = normalize_code(code)
    if not c:
        raise ValueError(f"bad color code {code!r} (use C1–C8)")
    bank = load_bank(world)
    nm = bank[c].name
    hx = bank[c].hex
    if name is not None:
        nm = name.strip()
        if not nm:
            raise ValueError("name cannot be empty")
        if len(nm) > 32:
            raise ValueError("name too long (max 32)")
    if hex_raw is not None:
        got = normalize_hex(hex_raw)
        if not got:
            raise ValueError(f"bad hex {hex_raw!r}")
        hx = got
    bank[c] = ColorSlot(code=c, name=nm, hex=hx)
    save_bank(world, bank)
    return bank[c]


def resolve_token(name: str, world: Any | None = None) -> str | None:
    """
    Map studio color token → Rich color string.

    Bank codes: c1, C1, C01 → slot hex.
    Style tokens: dim, bright.
    Names are NOT paint keys (labels only).
    """
    raw = (name or "").strip()
    if not raw:
        return None
    low = raw.lower()
    if low in _STYLE_TOKENS:
        return _STYLE_TOKENS[low]
    code = normalize_code(raw)
    if code:
        bank = load_bank(world)
        slot = bank.get(code)
        if slot:
            return slot.hex
    return None


def view_face(world: Any | None = None) -> str:
    """Player-facing colorbank table."""
    bank = load_bank(world)
    fac = factory_bank()
    lines = [
        "COLORBANK  (viz)  — studio uses codes: {c1}…{/} … {c8}…{/}",
        "",
        f"  {'CODE':<6} {'NAME':<16} {'HEX':<10}  note",
        f"  {'----':<6} {'----':<16} {'---':<10}",
    ]
    for code in CODES:
        s = bank[code]
        f = fac[code]
        note = ""
        if s.hex != f.hex or s.name != f.name:
            note = "*"
        # show swatch as rich if possible
        lines.append(
            f"  {code:<6} {s.name:<16} {s.hex:<10}  {note}"
            f"  [{s.hex}]████[/{s.hex}]"
        )
    lines.append("")
    lines.append("  * = changed from factory")
    lines.append("  @godmode edit colorbank C1 -> f3f3f3")
    lines.append("  @godmode edit colorbank C1 name Soft White")
    lines.append("  @godmode edit colorbank C3 Orange Crush -> ff8800")
    lines.append("  @godmode reset colorbank")
    return "\n".join(lines)


def parse_edit_args(rest: str) -> tuple[str, str | None, str | None]:
    """
    Parse after ``edit colorbank``:

      C1 -> f3f3f3
      C1 name Soft White
      C1 Soft White -> f3f3f3
      C1 as Soft White

    Returns (code, name|None, hex|None).
    """
    s = (rest or "").strip()
    if not s:
        raise ValueError("edit colorbank needs a code (C1–C8)")

    # C1 -> hex   or  C1 name -> hex
    arrow = re.split(r"\s*->\s*", s, maxsplit=1)
    if len(arrow) == 2:
        left, hx = arrow[0].strip(), arrow[1].strip()
        parts = left.split(None, 1)
        code = parts[0]
        name = None
        if len(parts) > 1:
            tail = parts[1].strip()
            low = tail.lower()
            if low.startswith("name "):
                name = tail[5:].strip()
            elif low.startswith("as "):
                name = tail[3:].strip()
            else:
                name = tail
        return code, name or None, hx

    parts = s.split(None, 2)
    code = parts[0]
    if len(parts) == 1:
        raise ValueError(
            "set hex and/or name:\n"
            "  @godmode edit colorbank C1 -> f3f3f3\n"
            "  @godmode edit colorbank C1 name Soft White"
        )
    if parts[1].lower() in ("name", "as"):
        if len(parts) < 3:
            raise ValueError("name cannot be empty")
        return code, parts[2], None
    # C1 Soft White (name only, no arrow)
    return code, " ".join(parts[1:]), None
