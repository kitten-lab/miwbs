"""
Zero-point face copy — edit wording HERE.

This is the style sheet for consider / research printouts.
Logic stays in chronicle.py / commands.py; strings live here so
you can craft cute copy without hunting ·-insert habits.

Convention:
  - Story / mouth lines → soft white (caller wraps)
  - Instrument rows → dim labels CRATE / TPS (no middle-dot)
  - Hints → dim, plain language; prefer newlines over · chains
"""

from __future__ import annotations

from . import format as fmt

# ── marks ──────────────────────────────────────────────────────────────
KRAS = "ʞ"  # zero-point self mark (who, before a name)


# ── live consider (just after you store) ───────────────────────────────
def live_echo(body: str) -> str:
    """Mouth line after a new consideration."""
    b = (body or "").strip() or "—"
    return f"ECHO: {fmt.safe(b)}"


def live_histories_stored(
    *,
    crate_uid: str,
    tps_uid: str,
    event_u: str,
    ingest_u: str,
) -> str:
    """Instrument block under the live ECHO line."""
    return "\n".join(
        [
            "HISTORIES STORED:",
            f"CRATE     {fmt.safe(crate_uid)}",
            f"TPS       {fmt.safe(tps_uid)}",
            f"EVENT     {fmt.safe(event_u)}",
            f"INGEST    {fmt.safe(ingest_u)}",
        ]
    )


# ── list (consider with no args) ───────────────────────────────────────
LIST_EMPTY = (
    "No considerations yet.\n"
    "  consider <text>\n"
    "  consider -d <text>\n"
    "  consider … -e <unix>\n"
    "  consider <<studio"
)

LIST_HINT = (
    "HINT: Research a consideration! A simple how-to!\n"
    "  research consideration 01"
)


def list_row(seq_label: str, body: str) -> str:
    """One index line: [01]  ʞ:  body"""
    b = (body or "—").strip()
    return (
        f"[{fmt.SOFT_WHITE}][{fmt.safe(seq_label)}]  "
        f"{KRAS}:  {fmt.safe(b)}[/{fmt.SOFT_WHITE}]"
    )


def list_face(rows: list[tuple[str, str]]) -> str:
    """
    rows = [(seq_label, body), …]
    """
    if not rows:
        return fmt.hint(LIST_EMPTY)
    lines = [list_row(seq, body) for seq, body in rows]
    lines.append("")
    lines.append(fmt.hint(LIST_HINT))
    return "\n".join(lines)


# ── research consideration N ───────────────────────────────────────────
def research_consideration_detail(
    *,
    body: str,
    crate_uid: str,
    tps_uid: str,
) -> str:
    b = (body or "—").strip()
    return "\n".join(
        [
            f"[{fmt.SOFT_WHITE}]{KRAS}:  {fmt.safe(b)}[/{fmt.SOFT_WHITE}]",
            "",
            f"[dim]CRATE   {fmt.safe(crate_uid)}[/dim]",
            f"[dim]TPS     {fmt.safe(tps_uid)}[/dim]",
            "",
            fmt.hint(research_crate_hint(crate_uid)),
        ]
    )


def research_crate_hint(crate_uid: str) -> str:
    return (
        "HINT: Research a REPORT! A simple how-to!\n"
        f"  research crate {crate_uid}"
    )


def research_crate_rabbit(token: str) -> str:
    """Stub until real crate report exists."""
    return "\n".join(
        [
            "Followed the white rabbit!",
            fmt.hint(
                f"(crate {token} — real report data soon!  —management)"
            ),
        ]
    )


# ── usage / errors (no · chains) ───────────────────────────────────────
USAGE_CONSIDER = (
    "consider <text>\n"
    "consider -d <text>\n"
    "consider … -e <unix>\n"
    "consider <<studio"
)

USAGE_RESEARCH = (
    "research consideration 01\n"
    "research crate C1C-FE3-860\n"
    "research crate C1C FE3 860"
)

ZERO_BLOCKED = (
    "Zero point — consider + research.\n"
    f"{USAGE_CONSIDER}\n"
    f"{USAGE_RESEARCH}\n"
    "clear\n"
    "quit\n"
    "help"
)

HELP_ZERO = "\n".join(
    [
        "zero point",
        "  consider <text>              store a consideration",
        "  consider -d <text>           same body via flag",
        "  consider … -e <n>            event unix",
        "  consider <<studio            studio body",
        "  consider                     list [01] [02] …",
        "  research consideration 01    open one",
        "  research crate C1C FE3 860   follow (stub)",
        "  clear · quit                 (ok, these two still share a breath)",
    ]
)


def missing_consideration(seq_label: str) -> str:
    return f"No consideration [{seq_label}]."


def bad_event_unix(raw: str) -> str:
    return (
        f"Bad -e event unix {raw!r}\n"
        "  use an integer (e.g. -e -100000000)"
    )


def open_studio_hint() -> str:
    return "Open studio with:\n  consider <<studio"
