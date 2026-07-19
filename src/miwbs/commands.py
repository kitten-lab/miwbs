"""Zero-point command surface — consider + research (+ clear / quit / help)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from . import format as fmt


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
        return CommandResult(
            True,
            fmt.hint(
                "Zero point — consider + research.\n"
                "  consider <text>  ·  -d <text>  ·  -e <unix>\n"
                "  consider <<studio  ·  consider  (list)\n"
                "  research consideration 01  ·  research crate C1C FE3 860\n"
                "  clear · quit · help"
            ),
        )

    try:
        if cmd in ("quit", "exit", "q"):
            return CommandResult(True, fmt.hint("Until the next shelf."), quit=True)
        if cmd in ("clear", "clr"):
            return CommandResult(True, "", clear_log=True)
        if cmd in ("help", "?"):
            return CommandResult(True, _help_zero())
        if cmd in ("consider", "wonder"):
            return CommandResult(True, _consider_herenow(world, arg))
        if cmd == "research":
            return CommandResult(True, _research(world, arg))
    except Exception as e:  # noqa: BLE001
        return CommandResult(False, fmt.err(str(e)))

    return CommandResult(True, "")


def _help_zero() -> str:
    return "\n".join(
        [
            fmt.section("zero point"),
            fmt.hint("consider <text>     — store a consideration"),
            fmt.hint("consider -d <text>  — same body via flag"),
            fmt.hint("consider … -e <n>   — event unix"),
            fmt.hint("consider <<studio   — studio body"),
            fmt.hint("consider            — list [01] [02] …"),
            fmt.hint("research consideration 01  — open one"),
            fmt.hint("research crate C1C FE3 860  — follow (stub)"),
            fmt.hint("clear · quit"),
        ]
    )


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
        return fmt.hint(
            "consider <text>  ·  consider -d <text>  ·  -e <unix>\n"
            "  studio: consider <<studio"
        )
    if body.lower().strip() in ("<<", "<<studio", "{", "{studio}"):
        return fmt.hint("Open studio with:  consider <<studio")

    event_unix: int | None = None
    if event_raw:
        try:
            event_unix = int(str(event_raw).strip().lstrip("uU"))
        except ValueError:
            return fmt.hint(
                f"Bad -e event unix {event_raw!r}  ·  "
                f"use an integer (e.g. -e -100000000)"
            )

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
    """
    research consideration 01
    research crate C1C-FE3-860
    research crate C1C FE3 860
    """
    from . import chronicle as ch

    raw = (arg or "").strip()
    if not raw:
        return fmt.hint(
            "research consideration 01\n"
            "research crate C1C-FE3-860  ·  research crate C1C FE3 860"
        )

    parts = raw.split(maxsplit=1)
    kind = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""

    # research 01  → consideration
    if kind.isdigit() or re.fullmatch(r"0*\d+", kind):
        rest = kind
        kind = "consideration"

    if kind in ("consideration", "consider", "c", "con"):
        if not rest:
            return fmt.hint("research consideration 01")
        token = rest.strip().lstrip("#")
        # allow [01] or 01
        token = token.strip("[]")
        if not token.isdigit():
            return fmt.hint(f"Need a list number, got {rest!r}")
        seq = int(token)
        crate = ch.get_consideration_by_seq(world, seq)
        if crate is None:
            return fmt.hint(f"No consideration [{ch.format_seq(seq)}].")
        return ch.format_consideration_detail(crate)

    if kind in ("crate", "cr"):
        if not rest:
            return fmt.hint("research crate C1C-FE3-860")
        crate = ch.get_crate_by_uid(world, rest)
        if crate is None:
            return ch.format_crate_rabbit(rest)
        # Found: still rabbit until full report exists — but acknowledge
        return ch.format_crate_rabbit(crate.crate_uid)

    if kind in ("tps",):
        return fmt.hint(
            "TPS research soon.\n"
            "  For now: research consideration 01  ·  research crate …"
        )

    return fmt.hint(
        "research consideration 01\n"
        "research crate C1C FE3 860"
    )
