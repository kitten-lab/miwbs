"""Zero-point command surface — consider (+ clear / quit / help)."""

from __future__ import annotations

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


# Strict zero allowlist
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
                "Zero point — only consider is open.\n"
                "  consider <text>  ·  -d <text>  ·  -e <unix>\n"
                "  consider <<studio  ·  consider  (list)\n"
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
    except Exception as e:  # noqa: BLE001
        return CommandResult(False, fmt.err(str(e)))

    return CommandResult(True, "")


def _help_zero() -> str:
    return "\n".join(
        [
            fmt.section("zero point"),
            fmt.hint("consider <text>     — store a consideration (crate + TPS)"),
            fmt.hint("consider -d <text>  — same body via flag"),
            fmt.hint("consider … -e <n>   — event unix (story time)"),
            fmt.hint("consider <<studio   — write body in the studio"),
            fmt.hint("consider            — list considerations"),
            fmt.hint("clear · quit"),
        ]
    )


def _consider_herenow(world, arg: str) -> str:
    """
    Single-note consider → crate + TPS.

    Body: positionals and/or -d/--desc/--detail/--data.
    Event: -e / --event only. Writer null.
    """
    from . import chronicle as ch
    from .argflags import CONSIDER_FLAG_ALIASES, parse_named_flags

    raw = (arg or "").strip()
    if not raw:
        crates = [c for c in ch.load_crates(world) if c.kind == "consideration"]
        if not crates:
            return fmt.hint(
                "No considerations yet.\n"
                "  consider <text>  ·  consider -d <text>  ·  -e <unix>\n"
                "  consider <<studio"
            )
        sw = fmt.SOFT_WHITE
        lines: list[str] = []
        for c in crates:
            body = (c.body or "—").strip()
            lines.append(f"[{sw}]ʞ considered:  {fmt.safe(body)}[/{sw}]")
            lines.append(
                f"    [dim]{fmt.safe(c.crate_uid)}  ·  {fmt.safe(c.tps_uid)}[/dim]"
            )
        return "\n".join(lines)

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
            "  e.g. consider I am somewhere  ·  consider I am somewhere -e -100000000\n"
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
