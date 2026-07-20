"""Zero-point command surface — consider / remember / research + godmode (+ clear / quit / help)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from . import format as fmt
from . import zero_face as face


@dataclass
class CommandResult:
    ok: bool
    message: str
    quit: bool = False
    open_book_id: str | None = None
    open_wiki: tuple[str, bool] | None = None
    clear_log: bool = False


_ZERO_CMDS = frozenset(
    {
        "quit",
        "exit",
        "q",
        "clear",
        "clr",
        "help",
        "?",
        "consider",
        "wonder",
        "remember",
        "research",
        "godmode",
        "@godmode",
        "@god",
        "export",
        "import",
    }
)


def note_last_command(world, line: str) -> None:
    """Remember the last typed line for face placeholders ``{guy}`` / ``{cmd}``."""
    try:
        world.last_command_line = (line or "").strip()
    except Exception:  # noqa: BLE001
        pass


def last_command(world) -> str:
    return (getattr(world, "last_command_line", None) or "").strip()


def dispatch(world, line: str) -> CommandResult:
    line = (line or "").strip()
    if not line:
        return CommandResult(True, "")

    note_last_command(world, line)

    parts = line.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd not in _ZERO_CMDS:
        return CommandResult(True, face.zero_blocked(world))

    try:
        if cmd in ("quit", "exit", "q"):
            return CommandResult(True, fmt.hint("Until the next shelf."), quit=True)
        if cmd in ("clear", "clr"):
            return CommandResult(True, "", clear_log=True)
        if cmd in ("help", "?"):
            return CommandResult(True, face.help_zero(world))
        if cmd in ("consider", "wonder"):
            return CommandResult(True, _consider_herenow(world, arg))
        if cmd == "remember":
            return CommandResult(True, _remember(world, arg))
        if cmd == "research":
            return CommandResult(True, _research(world, arg))
        if cmd in ("godmode", "@godmode", "@god"):
            return CommandResult(True, _godmode(world, arg))
        if cmd == "export":
            return CommandResult(True, _export_pack(world, arg))
        if cmd == "import":
            return CommandResult(True, _import_pack(world, arg))
    except Exception as e:  # noqa: BLE001
        return CommandResult(
            False, face.error_slot("unexpected", world, detail=str(e))
        )

    return CommandResult(True, "")


def _consider_herenow(world, arg: str) -> str:
    """
    Store only. No list subcommand — bare ``consider`` is a flat usage error.
    Lookup lives on ``remember considerations``.
    """
    from . import chronicle as ch
    from .argflags import CONSIDER_FLAG_ALIASES, parse_named_flags

    raw = (arg or "").strip()
    if not raw:
        return face.usage_consider(world)

    low = raw.lower()
    if low.startswith("note ") or low.startswith("note|") or low == "note":
        raw = raw[4:].lstrip(" |") if low.startswith("note") else ""
        if not raw.strip():
            return face.usage_consider(world)

    parsed = parse_named_flags(raw, aliases=CONSIDER_FLAG_ALIASES)
    if parsed.error:
        return face.error_slot("flags-error", world, detail=parsed.error)

    body_flag = parsed.get("body")
    event_raw = parsed.get("event")
    body = " ".join(parsed.positionals).strip()
    if body_flag and not body:
        body = body_flag
    elif body_flag and body:
        body = body_flag.strip()
    if not body:
        return face.usage_consider(world)
    if body.lower().strip() in ("<<", "<<studio", "{", "{studio}"):
        return face.open_studio_hint(world)

    event_unix: int | None = None
    if event_raw:
        try:
            event_unix = int(str(event_raw).strip().lstrip("uU"))
        except ValueError:
            return face.bad_event_unix(event_raw, world)

    crate = ch.append_consideration(
        world,
        body=body,
        title="",
        detail="",
        event_unix=event_unix,
        writer=None,
    )
    echo = ch.format_echo_considered(body, world)
    hist = ch.format_histories_stored(crate, world)
    return f"{echo}\n\n{hist}"


def _remember(world, arg: str) -> str:
    """
    Lookup / recall.

    remember considerations          → index list
    remember consideration 01        → open one
    remember 01                      → same
    """
    from . import chronicle as ch

    raw = (arg or "").strip()
    if not raw:
        return face.usage_remember(world)

    parts = raw.split(maxsplit=1)
    kind = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    # list
    if kind in ("considerations", "notes", "thoughts"):
        return ch.format_consideration_list(ch.considerations(world), world)

    # open one: consideration 01 · c 01 · bare 01
    if kind.isdigit() or re.fullmatch(r"0*\d+", kind):
        rest = kind
        kind = "consideration"

    if kind in ("consideration", "c", "note", "thought"):
        if not rest:
            # singular without index — point at list + how-to
            return face.usage_remember(world)
        token = rest.split()[0]
        if not re.fullmatch(r"0*\d+", token):
            return face.usage_remember(world)
        seq = int(token)
        crate = ch.get_consideration_by_seq(world, seq)
        if crate is None:
            return face.missing_consideration(ch.format_seq(seq), world)
        return ch.format_consideration_detail(crate, world)

    return face.usage_remember(world)


def _research(world, arg: str) -> str:
    """
    Instrument follow-through (crate report).

    Consideration open lives on ``remember``; ``research consideration``
    still works as a thin alias so old muscle memory doesn't soft-fail hard.
    """
    from . import chronicle as ch

    raw = (arg or "").strip()
    if not raw:
        return face.usage_research(world)

    parts = raw.split(maxsplit=1)
    kind = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if kind.isdigit() or re.fullmatch(r"0*\d+", kind):
        rest = kind
        kind = "consideration"

    if kind in ("consideration", "c", "note", "thought", "considerations"):
        # alias → remember
        if kind == "considerations" and not rest:
            return _remember(world, "considerations")
        return _remember(world, f"consideration {rest}".strip())

    if kind in ("crate", "report"):
        if not rest:
            return face.usage_research(world)
        crate = ch.get_crate_by_uid(world, rest)
        if crate is None:
            return ch.format_crate_rabbit(rest, world)
        return ch.format_crate_report(crate, world)

    return face.usage_research(world)


def _godmode(world, arg: str) -> str:
    """
    godmode list | show | edit | reset  (face slots)
    godmode view colorbank | edit colorbank | reset colorbank  (viz)
    """
    from . import colorbank as cb

    raw = (arg or "").strip()
    if not raw:
        return face.paint_hint("godmode-usage", world)

    parts = raw.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    # ── viz colorbank ────────────────────────────────────────────────
    if sub in ("view", "colorbank", "viz"):
        target = rest.split()[0].lower() if rest else "colorbank"
        if sub == "colorbank" or sub == "viz" or target in (
            "colorbank",
            "colors",
            "palette",
            "viz",
            "bank",
        ):
            return cb.view_face(world)
        if sub == "view" and not rest:
            return cb.view_face(world)
        return face.paint_hint("godmode-usage", world)

    if sub in ("voxlist", "vox", "faces", "list", "ls", "slots"):
        # voxlist = face/mouth slots (not a full skill list)
        return face.godmode_list_face(world)

    if sub in ("show", "get", "cat"):
        if not rest:
            return face.paint_hint("godmode-usage", world)
        token = rest.split()[0].lower()
        if token in ("colorbank", "colors", "palette", "viz", "bank"):
            return cb.view_face(world)
        return face.godmode_show_face(rest.split()[0], world)  # name or CODE

    if sub in ("reset", "clear", "default", "factory"):
        if not rest:
            return face.paint_hint("godmode-usage", world)
        token0 = rest.split()[0].lower()
        if token0 in ("colorbank", "colors", "palette", "viz", "bank"):
            code_rest = rest.split(maxsplit=1)
            code = code_rest[1].strip() if len(code_rest) > 1 else None
            if code:
                c = cb.normalize_code(code)
                if not c:
                    return face.error_slot(
                        "colorbank-bad-code", world, raw=code
                    )
                cb.reset_bank(world, c)
                return face.success_slot("colorbank-reset-one", world, code=c)
            cb.reset_bank(world, None)
            return face.success_slot("colorbank-reset", world)
        tok = rest.split()[0]
        slot = face.resolve_slot(tok)
        if slot is None:
            return face.error_slot("godmode-unknown", world, slot=tok)
        face.clear_override(world, slot)
        return face.success_slot("godmode-reset", world, slot=slot)

    if sub == "edit":
        if not rest:
            return face.paint_hint("godmode-usage", world)
        token0 = rest.split()[0].lower()
        if token0 in ("colorbank", "colors", "palette", "viz", "bank"):
            edit_rest = rest.split(maxsplit=1)
            if len(edit_rest) < 2:
                return face.paint_hint("colorbank-usage", world)
            try:
                code, name, hx = cb.parse_edit_args(edit_rest[1])
                slot = cb.set_slot(world, code, name=name, hex_raw=hx)
            except ValueError as e:
                return face.error_slot(
                    "colorbank-edit-error", world, detail=str(e)
                )
            return face.success_slot(
                "colorbank-saved",
                world,
                code=slot.code,
                name=slot.name,
                hex=slot.hex,
            )
        # face slot edit without <<studio on one line (name or CODE)
        tok = rest.split()[0]
        slot_n = face.resolve_slot(tok)
        if slot_n is None:
            return face.error_slot("godmode-unknown", world, slot=tok)
        code = face.slot_code(slot_n)
        return face.paint_hint(
            "godmode-edit-studio",
            world,
            slot=f"{code} {slot_n}",
            vars_doc=face.slot_vars_doc(slot_n),
        )

    return face.paint_hint("godmode-usage", world)


def _export_pack(world, arg: str) -> str:
    from . import pack_io

    raw = (arg or "").strip()
    if not raw:
        return face.paint_hint("pack-usage", world)
    parts = raw.split()
    kind = parts[0].lower()
    rest = parts[1:]
    full = False
    path_bits: list[str] = []
    for tok in rest:
        if tok in ("--full", "-full", "full"):
            full = True
        else:
            path_bits.append(tok)
    path_raw = " ".join(path_bits).strip() or None

    if kind not in ("vox", "viz", "face", "colorbank"):
        return face.paint_hint("pack-usage", world)
    if kind == "face":
        kind = "vox"
    if kind == "colorbank":
        kind = "viz"

    try:
        path = pack_io.resolve_path(world, kind, path_raw)  # type: ignore[arg-type]
        if kind == "vox":
            out, n = pack_io.export_vox(world, path, full=full)
        else:
            out, n = pack_io.export_viz(world, path)
    except OSError as e:
        return face.error_slot("pack-error", world, detail=str(e))
    return face.success_slot(
        "pack-exported",
        world,
        kind=kind,
        path=str(out),
        n=str(n),
    )


def _import_pack(world, arg: str) -> str:
    from . import pack_io

    raw = (arg or "").strip()
    if not raw:
        return face.paint_hint("pack-usage", world)
    parts = raw.split(maxsplit=1)
    kind = parts[0].lower()
    path_raw = parts[1].strip() if len(parts) > 1 else None
    if kind not in ("vox", "viz", "face", "colorbank"):
        return face.paint_hint("pack-usage", world)
    if kind == "face":
        kind = "vox"
    if kind == "colorbank":
        kind = "viz"

    try:
        path = pack_io.resolve_path(world, kind, path_raw)  # type: ignore[arg-type]
        if kind == "vox":
            out, n = pack_io.import_vox(world, path, merge=True)
        else:
            out, n = pack_io.import_viz(world, path)
    except FileNotFoundError:
        try:
            path = pack_io.resolve_path(world, kind, path_raw)  # type: ignore[arg-type]
            p = str(path)
        except Exception:  # noqa: BLE001
            p = path_raw or ""
        return face.error_slot("pack-not-found", world, path=p)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return face.error_slot("pack-error", world, detail=str(e))
    return face.success_slot(
        "pack-imported",
        world,
        kind=kind,
        path=str(out),
        n=str(n),
    )
