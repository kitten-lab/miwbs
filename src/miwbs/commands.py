"""Zero-point command surface — consider + research (+ clear / quit / help)."""

from __future__ import annotations

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
        "research",
    }
)


def dispatch(world, line: str) -> CommandResult:
    line = (line or "").strip()
    if not line:
        return CommandResult(True, "")

    parts = line.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd not in _ZERO_CMDS:
        return CommandResult(True, fmt.hint(face.ZERO_BLOCKED))

    try:
        if cmd in ("quit", "exit", "q"):
            return CommandResult(True, fmt.hint("Until the next shelf."), quit=True)
        if cmd in ("clear", "clr"):
            return CommandResult(True, "", clear_log=True)
        if cmd in ("help", "?"):
            return CommandResult(True, fmt.hint(face.HELP_ZERO))
        if cmd in ("consider", "wonder"):
            return CommandResult(True, _consider_herenow(world, arg))
        if cmd == "research":
            return CommandResult(True, _research(world, arg))
    except Exception as e:  # noqa: BLE001
        return CommandResult(False, fmt.err(str(e)))

    return CommandResult(True, "")


def _consider_herenow(world, arg: str) -> str:
    from . import chronicle as ch
    from .argflags import CONSIDER_FLAG_ALIASES, parse_named_flags

    raw = (arg or "").strip()
    if not raw:
        return ch.format_consideration_list(ch.considerations(world))

    low = raw.lower()
    if low.startswith("note ") or low.startswith("note|") or low == "note":
        raw = raw[4:].lstrip(" |") if low.startswith("note") else ""
        if not raw.strip():
            return _consider_herenow(world, "")

    parsed = parse_named_flags(raw, aliases=CONSIDER_FLAG_ALIASES)
    if parsed.error:
        return fmt.hint(parsed.error)

    body_flag = parsed.get("body")
    event_raw = parsed.get("event")
    body = " ".join(parsed.positionals).strip()
    if body_flag and not body:
        body = body_flag
    elif body_flag and body:
        body = body_flag.strip()
    if not body:
        return fmt.hint(face.USAGE_CONSIDER)
    if body.lower().strip() in ("<<", "<<studio", "{", "{studio}"):
        return fmt.hint(face.open_studio_hint())

    event_unix: int | None = None
    if event_raw:
        try:
            event_unix = int(str(event_raw).strip().lstrip("uU"))
        except ValueError:
            return fmt.hint(face.bad_event_unix(event_raw))

    crate = ch.append_consideration(
        world,
        body=body,
        title="",
        detail="",
        event_unix=event_unix,
        writer=None,
    )
    echo = ch.format_echo_considered(body)
    hist = ch.format_histories_stored(crate)
    return f"{echo}\n\n{hist}"


def _research(world, arg: str) -> str:
    from . import chronicle as ch

    raw = (arg or "").strip()
    if not raw:
        return fmt.hint(face.USAGE_RESEARCH)

    parts = raw.split(maxsplit=1)
    kind = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    if kind.isdigit() or re.fullmatch(r"0*\d+", kind):
        rest = kind
        kind = "consideration"

    if kind in ("consideration", "consider", "c", "con"):
        if not rest:
            return fmt.hint("research consideration 01")
        token = rest.strip().lstrip("#").strip("[]")
        if not token.isdigit():
            return fmt.hint(f"Need a list number, got {rest!r}")
        seq = int(token)
        crate = ch.get_consideration_by_seq(world, seq)
        if crate is None:
            return fmt.hint(face.missing_consideration(ch.format_seq(seq)))
        return ch.format_consideration_detail(crate)

    if kind in ("crate", "cr"):
        if not rest:
            return fmt.hint("research crate C1C-FE3-860")
        crate = ch.get_crate_by_uid(world, rest)
        if crate is None:
            return ch.format_crate_rabbit(rest)
        return ch.format_crate_rabbit(crate.crate_uid)

    if kind in ("tps",):
        return fmt.hint(
            "TPS research soon.\n"
            "  For now: research consideration 01"
        )

    return fmt.hint(face.USAGE_RESEARCH)
