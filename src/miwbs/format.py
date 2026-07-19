"""Calm, Grok-Build-adjacent terminal presentation helpers.

Shared chrome for room views and lists: clear hierarchy, dim secondary text,
safe escaping so user/world strings cannot inject Rich markup.
"""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape as rich_escape

from . import PRODUCT_NAME
from .ids import display_name
from .measure import CONTENT_MEASURE, turn_rule_ascii

# Soft accent used sparingly (prompt / section rules), not on every line.
ACCENT = "bright_cyan"
MUTED = "dim"
TITLE = "bold"
OK = "green"
ERR = "red"
LABEL_WIDTH = 10

# Body text ladder — soft default, hard white only for intentional pop
SOFT_WHITE = "#e8e8ec"  # calm prose (log default / SUCCESS body)
HARD_WHITE = "#ffffff"  # rare attention (new name after →, etc.)

# Distinct Rich color per VEN kind (and soft colors for link types).
KIND_COLORS: dict[str, str] = {
    "concept": "bright_white",
    "person": "yellow",
    "place": "bright_white",
    "bin": "bright_cyan",
    "container": "bright_cyan",  # legacy kind color
    "thing": "bright_yellow",
    "folio": "bright_yellow",
    "symbol": "white",
    "sense": "magenta",
    "realm": "cyan",
    "timeline": "bright_green",
    # legacy aliases (same colors as folded roots)
    "object": "bright_yellow",
    "book": "bright_yellow",
    "material": "gold1",
    "feeling": "magenta",
    "goal": "bright_magenta",
    "desire": "magenta",
    "purpose": "bright_magenta",
    "event": "bright_yellow",
    "archetype": "yellow",
    "other": "white",
}

LINK_TYPE_COLORS: dict[str, str] = {
    "spatial": "bright_blue",
    "dimensional": "bright_cyan",  # was magenta; less purple noise near locations
    "temporal": "bright_green",
    "narrative": "cyan",
    "conditional": "yellow",
}

# Turn boundary matches the canonical content measure (ASCII, portable).
TURN_RULE_WIDTH = CONTENT_MEASURE


def turn_separator() -> str:
    """
    Single-line divider between interactive command turns.

    ASCII dashes at :data:`CONTENT_MEASURE` so rules match book/studio artboard
    width and copy-paste cleanly.
    """
    return f"[dim]{turn_rule_ascii(TURN_RULE_WIDTH)}[/dim]"


def safe(text: object) -> str:
    """Escape arbitrary world/user text for Rich markup strings."""
    if text is None:
        return ""
    return rich_escape(str(text))


def plain(text: object) -> str:
    """Strip Rich markup for assertions / plain capture checks."""
    console = Console(force_terminal=False, no_color=True, width=120)
    with console.capture() as cap:
        console.print(str(text), markup=True, highlight=False, end="")
    return cap.get()


def show_name(name: object) -> str:
    """Escaped player-facing entity name (plain readable, not cute storage form)."""
    return safe(display_name(str(name) if name is not None else ""))


def named_ref(name: object, ref: object) -> str:
    """
    Player-facing ``Name #CODE`` with a space before the hash.

    Use in success lines, titles, and lore headings. Prefer this over gluing
    ``Name#CODE``. Command tokens that must parse as ``name#CODE`` stay glued
    at the call site (e.g. book open examples).

    Plain text (not Rich-escaped) — pass through :func:`ok` / :func:`err` or
    escape with :func:`safe` when embedding in markup.
    """
    n = display_name(str(name) if name is not None else "")
    r = str(ref or "").strip().lstrip("#")
    if not r:
        return n
    if not n:
        return f"#{r}"
    return f"{n} #{r}"


def kind_color(kind: str) -> str:
    """Rich color name for a VEN kind (fallback white)."""
    return KIND_COLORS.get((kind or "").lower().strip(), "white")


def kind_label(kind: str) -> str:
    """Dim secondary kind reference (not the colored focus)."""
    k = (kind or "").strip() or "other"
    return f"[dim]{safe(k)}[/dim]"


def kind_markup(kind: str) -> str:
    """Deprecated alias: kind words stay dim; prefer colored_name for entities."""
    return kind_label(kind)


def colored_name(name: object, kind: str | None = None) -> str:
    """Player-facing name, colored by VEN kind when kind is given."""
    text = show_name(name)
    if not kind:
        return text
    color = kind_color(kind)
    return f"[{color}]{text}[/{color}]"


def link_type_markup(link_type: str) -> str:
    """Colored link-type word inside parentheses on exit lines."""
    t = (link_type or "").strip() or "spatial"
    color = LINK_TYPE_COLORS.get(t.lower(), MUTED)
    return f"[{color}]{safe(t)}[/{color}]"


def title_line(name: str, kind: str | None = None) -> str:
    """Bold place/entity title; optional kind tints the name."""
    if kind:
        color = kind_color(kind)
        return f"[{TITLE} {color}]{show_name(name)}[/{TITLE} {color}]"
    return f"[{TITLE} {ACCENT}]{show_name(name)}[/{TITLE} {ACCENT}]"


def rule(label: str = "") -> str:
    """Thin section divider; optional label on the left."""
    if label:
        return f"[dim]── {safe(label)} ────────────────────────────[/dim]"
    return "[dim]──────────────────────────────────────[/dim]"


def section(label: str) -> str:
    """Section header: short uppercase-feeling label, restrained."""
    return f"[bold]{safe(label)}[/bold]"


def meta_row(
    label: str,
    value: str,
    secondary: str | None = None,
    *,
    name: bool = False,
    kind: str | None = None,
) -> str:
    """Aligned key/value for whereami-style panels.

    name=True → run display_name on value first.
    kind=... → color the **value** (entity name) by kind; field label stays dim.
    """
    lab = safe(label).ljust(LABEL_WIDTH)
    if kind:
        if name:
            val = colored_name(value, kind)
        else:
            # Already human-readable (e.g. status Situation fields)
            val = f"[{kind_color(kind)}]{safe(value)}[/{kind_color(kind)}]"
    elif name:
        val = show_name(value)
    else:
        val = safe(value)
    line = f"[dim]{lab}[/dim] {val}"
    if secondary:
        line += f"  [dim]{safe(secondary)}[/dim]"
    return line


def bullet(primary: str, secondary: str | None = None, *, kind: str | None = None) -> str:
    """
    List row. ``kind=`` colors the entity name.

    When *secondary* is omitted, a dim kind word is appended (inv-style).
    When *secondary* is set, only that meta is shown (no second kind word) —
    so callers can pass ``kind/subtype · code`` without ``place place``.
    """
    name = colored_name(primary, kind) if kind else show_name(primary)
    if secondary:
        return f"  [dim]·[/dim] {name}  [dim]{safe(secondary)}[/dim]"
    if kind:
        return f"  [dim]·[/dim] {name}  {kind_label(kind)}"
    return f"  [dim]·[/dim] {name}"


def pad_visible(text: str, width: int, *, align: str = "left") -> str:
    """Pad plain text to *width* (for table columns; no Rich markup in *text*)."""
    s = text if text is not None else ""
    if width < 1:
        return s
    if len(s) >= width:
        return s
    pad = width - len(s)
    if align == "right":
        return (" " * pad) + s
    return s + (" " * pad)


def colored_padded_name(name: str, kind: str | None, width: int) -> str:
    """Kind-colored name, space-padded to *width* using the plain display length."""
    shown = show_name(name)
    pad = max(0, width - len(shown))
    if kind:
        return colored_name(shown, kind) + (" " * pad)
    return show_name(shown) + (" " * pad)


def inner_life_row(
    instance_name: str,
    ven_name: str,
    kind: str,
    subtype: str | None = None,
) -> str:
    """
    Person Inner life list line: instance · VEN · type · subtype.

    Field order:
      0. Instance name (this copy; includes name override when set) — colored by kind
      1. Prime VEN name (dim)
      2. VEN kind/type (once)
      3. Subtype when set; otherwise ``-`` (never a second copy of the kind)
    """
    inst = colored_name(instance_name, kind)
    ven = f"[dim]{show_name(ven_name)}[/dim]"
    type_part = kind_label(kind)
    sub = (subtype or "").strip() or "-"
    return f"  [dim]·[/dim] {inst}  {ven}  {type_part}  [dim]{safe(sub)}[/dim]"


def stacked_item(title: str, detail: str, *, kind: str | None = None) -> str:
    """Two-line list entry for long names (avoids broken fixed-width tables)."""
    if kind:
        head = f"  [dim]·[/dim] {colored_name(title, kind)}"
    else:
        head = f"  [dim]·[/dim] {show_name(title)}"
    return f"{head}\n      [dim]{safe(detail)}[/dim]"


def exit_line(label: str, link_type: str, dest: str, dest_kind: str = "place") -> str:
    return (
        f"  [dim]·[/dim] {safe(label)}  "
        f"({link_type_markup(link_type)})  →  {colored_name(dest, dest_kind)}"
    )


def prose(text: str) -> str:
    """
    Render world/user longform text for look / examine / lore.

    Plain bodies are fully escaped. Bodies stored with ``.format: studio``
    (or written via studio opt-in commands) use Studio Text whitelist markup.
    """
    from .studio_text import render_body

    return render_body(text)


def hint(text: str) -> str:
    """Secondary/muted line; always escapes so world/user text cannot inject markup."""
    return f"[dim]{safe(text)}[/dim]"


def ok(msg: str) -> str:
    """Soft success — colored handle, no bold; soft-white body."""
    return (
        f"[green] SUCCESS [/green] "
        f"[{SOFT_WHITE}]{safe(msg)}[/{SOFT_WHITE}]"
    )


def pop_name(text: str) -> str:
    """Hard-white pop for a name/token that should draw the eye."""
    return f"[{HARD_WHITE}]{safe(text)}[/{HARD_WHITE}]"


def success_line(body: str, *, raw: bool = False) -> str:
    """
    Green SUCCESS handle (not bold) + soft-white body::

        SUCCESS  VEN SELF-0001 Renamed · old → new

    Pass ``raw=True`` when *body* is already escaped markup
    (soft spans + optional :func:`pop_name` pops). Avoid nesting
    hard-white inside soft-white — close soft before the pop.
    """
    if raw:
        return f"[bright_green] SUCCESS [/bright_green] {body}"
    return (
        f"[bright_green] SUCCESS [/bright_green] "
        f"[{SOFT_WHITE}]{safe(body)}[/{SOFT_WHITE}]"
    )


def skyline_line(body: str) -> str:
    """
    Yellow SKYLINE handle (not bold) + dim gray records line::

        SKYLINE  RECORDS UPDATED: HST-001 @ CYC ʞ · u1784433943
    """
    return (
        f"[bright_yellow] SKYLINE [/bright_yellow] "
        f"[dim]{safe(body)}[/dim]"
    )


def skyline_soft(body: str) -> str:
    """SKYLINE handle + soft-white body (access headers, primary skyline)."""
    return (
        f"[bright_yellow] SKYLINE [/bright_yellow] "
        f"[{SOFT_WHITE}]{safe(body)}[/{SOFT_WHITE}]"
    )


def skyline_bracket_pop(inner: str) -> str:
    """
    Soft-white brackets, skyline-yellow word inside::

        [rename]   [the kras]

    Brackets match surrounding soft text; only the interior is yellow.
    """
    y = "bright_yellow"
    sw = SOFT_WHITE
    # Escape opening [ so Rich does not treat it as a style tag
    return (
        f"[{sw}]\\[[/{sw}]"
        f"[{y}]{safe(inner)}[/{y}]"
        f"[{sw}]][/{sw}]"
    )


def skyline_history_entry(
    *,
    event_code: str,
    verb: str,
    notation: str,
    timemark: str,
) -> str:
    """
    One history leg in the SKYLINE report::

          > HST-001 HISTORY TYPE: [rename]
            NOTATION: old → new
            TIMEMARK: CYC ʞ · u1784435327

    ``>`` yellow; ``[verb]`` soft brackets + yellow interior;
    NOTATION/TIMEMARK labels soft-white, bodies dim.
    """
    code = (event_code or "—").strip() or "—"
    v = (verb or "record").strip() or "record"
    note = (notation or "").strip() or "—"
    when = (timemark or "").strip() or "—"
    y = "bright_yellow"
    head = (
        f"  [{y}]>[/{y}] "
        f"[{SOFT_WHITE}]{safe(code)} HISTORY TYPE: [/{SOFT_WHITE}]"
        f"{skyline_bracket_pop(v)}"
    )
    # four spaces — under the HST code (after ``> ``)
    note_line = (
        f"    [{SOFT_WHITE}]NOTATION:[/{SOFT_WHITE}] "
        f"[dim]{safe(note)}[/dim]"
    )
    time_line = (
        f"    [{SOFT_WHITE}]TIMEMARK:[/{SOFT_WHITE}] "
        f"[dim]{safe(when)}[/dim]"
    )
    return "\n".join([head, note_line, time_line])


def skyline_history_report(
    access_for: str,
    entry_blocks: list[str],
) -> str:
    """
    Full history readout::

        SKYLINE  ACCESS HISTORY FOR SELF-0001 [title]

          > HST-001 …
        SKYLINE  RECORDS RECEIVED. END OF REPORT.

    *access_for* is pre-built markup (ref + soft/yellow bracket pop),
    not plain text — see callers / :func:`skyline_bracket_pop`.
    """
    head = (
        f"[bright_yellow] SKYLINE [/bright_yellow] "
        f"[{SOFT_WHITE}]ACCESS HISTORY FOR [/{SOFT_WHITE}]"
        f"{access_for}"
    )
    if not entry_blocks:
        return join_blocks(
            head,
            skyline_line("NO RECORDS. END OF REPORT."),
            gap=1,
        )
    # Blank line between each history leg
    body = "\n\n".join(entry_blocks)
    foot = skyline_line("RECORDS RECEIVED. END OF REPORT.")
    # blank line after ACCESS header, blank before footer
    return f"{head}\n\n{body}\n\n{foot}"


def success_with_skyline(
    success_body: str, skyline_body: str, *, raw_success: bool = False
) -> str:
    """Two-line act report: SUCCESS (soft white) then SKYLINE (gray)."""
    return (
        f"{success_line(success_body, raw=raw_success)}\n"
        f"{skyline_line(skyline_body)}"
    )


def skyline_unix(created_at: str | None) -> str:
    """Compact craft time for SKYLINE lines: ``u1784433943`` (no pipe)."""
    d = typed_unix_display(created_at)
    if d.startswith("u|"):
        return "u" + d[2:]
    return d


def err(msg: str) -> str:
    """
    Terminal-prolog-shaped fault line::

        ERR-808  that word has no weight here yet.

    Colored handle, not bold. No compiler voice.
    """
    return (
        f"[white on red] ERR-808 [/white on red] "
        f"[{ERR}]{safe(msg)}[/{ERR}]"
    )


def warn(msg: str) -> str:
    """Prolog-adjacent warning chrome — color only, no bold."""
    return f"[bright_blue] WARNING [/bright_blue] {safe(msg)}"


# Amber/orange for WARN-01 + helper rules (not skyline yellow)
WARN_ORANGE = "#e89a3c"


def warn01_line(body: str) -> str:
    """
    Soft warning handle (not bold)::

        WARN-01  MISSING REQUEST. PRINTING HELPER....
    """
    return (
        f"[{WARN_ORANGE}] WARN-01 [/{WARN_ORANGE}] "
        f"[{SOFT_WHITE}]{safe(body)}[/{SOFT_WHITE}]"
    )


def history_missing_request_help() -> str:
    """
    Bare ``history`` with no subject — WARN-01 + dim helper.

    Open blank lines frame the body (no heavy ``====`` rules).
    """
    # Body one step in from the WARN handle
    g = "   "
    lines = [
        warn01_line("MISSING REQUEST. PRINTING HELPER...."),
        "",
        f"[dim]{g}For researching the history of an item. Not all histories may be[/dim]",
        f"[dim]{g}properly recorded. Records department is improving each day![/dim]",
        "",  # blank line before Suggested Uses
        f"[dim]{g}[bold]Suggested Uses:[/bold] history <thing> or history on <thing>[/dim]",
        f"[dim]{g}Search <thing> by code, name, ven.[/dim]",
        "",
    ]
    return "\n".join(lines)


def echo_line(msg: str) -> str:
    """ECHO mouth (red tag) — soft backflow; color only, no bold."""
    return f"[red] E C H O [/red]  {safe(msg)}"


def typed_unix_display(created_at: str | None) -> str:
    """
    Wall-clock craft time as compact unix display: ``u|1735689600``.

    Accepts SQLite ``datetime('now')`` strings, ISO-ish stamps, or already-unix.
    Falls back to raw string if unparseable.
    """
    raw = (created_at or "").strip()
    if not raw:
        return "u|—"
    if raw.isdigit():
        return f"u|{int(raw)}"
    # already u|…
    if raw.lower().startswith("u|"):
        return raw if raw[2:].strip() else "u|—"
    from datetime import datetime, timezone

    s = raw.replace("T", " ").replace("Z", "").strip()
    # strip fractional seconds
    if "." in s:
        s = s.split(".", 1)[0]
    for fmt_s in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(s, fmt_s).replace(tzinfo=timezone.utc)
            return f"u|{int(dt.timestamp())}"
        except ValueError:
            continue
    return f"u|{safe(raw)}"


def position_memory_success(
    ref: str,
    title: str,
    body: str,
) -> str:
    """
    @desc save report (prolog-shaped)::

      SUCCESS : [#SELF-0001]   Position memory updated. "Title"

      E C H O : <description body>
    """
    ref_raw = (ref or "—").strip().lstrip("#") or "—"
    # Escape [#REF] so Rich does not treat [ as markup
    ref_bracket = safe(f"[#{ref_raw}]")
    # Handles unbold; title pop in hard white, rest soft
    head = (
        f"[green] SUCCESS [/green]:  "
        f"[{SOFT_WHITE}]{ref_bracket}   Position memory updated. \"[/{SOFT_WHITE}]"
        f"{pop_name((title or '').strip() or '—')}"
        f"[{SOFT_WHITE}]\"[/{SOFT_WHITE}]"
    )
    # Reprint body under ECHO (preserve line breaks; escape for Rich)
    raw = body if body is not None else ""
    from .studio_text import is_studio, strip_studio_header

    if is_studio(raw):
        raw = strip_studio_header(raw)
    raw = raw if raw.strip() else "(empty)"
    # Multi-line: tag on first line, body follows indented slightly
    lines = raw.splitlines() or ["(empty)"]
    if len(lines) == 1:
        echo = f"[red] E C H O [/red][red]:[/red]  {safe(lines[0])}"
    else:
        body_block = "\n".join(f"  {safe(ln)}" for ln in lines)
        echo = f"[red] E C H O [/red][red]:[/red]\n{body_block}"
    return join_blocks(head, echo, gap=1)


def join_blocks(*blocks: str | None, gap: int = 1) -> str:
    """Join non-empty blocks with blank-line discipline (no double clutter)."""
    parts = [b.strip("\n") for b in blocks if b and b.strip()]
    sep = "\n" * (gap + 1) if gap else "\n"
    return sep.join(parts)


def cmd_name(text: str) -> str:
    """Highlight a command token (static help text only)."""
    return f"[bold {ACCENT}]{safe(text)}[/bold {ACCENT}]"


def example_line(command: str, note: str = "") -> str:
    """Show a typed example; command is highlighted, optional note is dim."""
    line = f"  [dim]›[/dim] {cmd_name(command)}"
    if note:
        line += f"\n      [dim]{safe(note)}[/dim]"
    return line


def prose_block(*paragraphs: str) -> str:
    """Plain instructional paragraphs (static; still escaped for safety)."""
    return "\n\n".join(safe(p.strip()) for p in paragraphs if p and p.strip())


def render_help(kinds: str) -> str:
    """Comprehensive in-game manual: navigate, build, concepts, examples."""
    return join_blocks(
        title_line(f"{PRODUCT_NAME} · Instruction Manual"),
        prose_block(
            "This is a walkable studio for building a multiverse. "
            "You stand inside places, carry things, and shape the world with the same "
            "prompt you use to explore. Type a command, press Enter, read the reply."
        ),
        _manual_welcome(),
        _manual_concepts(),
        _manual_navigate(),
        _manual_build(kinds),
        _manual_lore(),
        _manual_quick_ref(kinds),
        _manual_tips(),
        gap=1,
    )


def _manual_welcome() -> str:
    return join_blocks(
        rule("Start here"),
        prose_block(
            "You begin as the Builder in a seed multiverse (Material realm, Prime timeline). "
            "Open your eyes with look. Travel with go. When you are ready to invent, use dig, "
            "link, create, and spawn."
        ),
        example_line("look", "Describe the place you are in"),
        example_line("help", "Show this manual again (also: ?)"),
        gap=0,
    )


def _manual_concepts() -> str:
    return join_blocks(
        rule("Core ideas (plain language)"),
        prose_block(
            "VEN (Virtual Entity) — the prime idea of a thing: a cathedral, a person, "
            "a feeling, a material, a realm, a timeline. Primes are templates and canon.",
            "Instance — one living copy of a VEN, situated in the multiverse "
            "(this hall, now, in Memory-Archive). You walk between place instances.",
            "Containment — anything can hold anything. A room holds people and objects; "
            "a person can hold feelings or motifs. Slots name the relationship "
            "(interior, inventory, feeling, memory, …).",
            "Links (paths) — directed edges from place to place. Types include "
            "spatial, dimensional, temporal, narrative, conditional. "
            "Going “through the mirror” is a normal path, not a special engine mode.",
            "Elevate — promote a lived instance into a new Prime VEN that can spawn "
            "further instances later.",
            "Lore revisions — append-only notes on a place (or VEN), optionally tagged "
            "with a timeline or when-label, so history accumulates instead of overwriting.",
        ),
        gap=0,
    )


def _manual_navigate() -> str:
    return join_blocks(
        rule("How to navigate"),
        prose_block(
            "Navigation is about seeing where you are, what leaves this place, and moving "
            "along a path label. Partial labels work when they uniquely match."
        ),
        section("See the room"),
        example_line("look", "Title, prose, realm/timeline, paths, people, things"),
        example_line("status", "You / place / realm / timeline / inv (sit, whereami)"),
        example_line("paths", "List paths from here (exits / ways / x)"),
        example_line("who", "People present"),
        section("Move"),
        example_line("go south", "Spatial path by label"),
        example_line("go through the mirror", "Dimensional jump (seed world)"),
        example_line("go years later", "Temporal jump (from the Archive)"),
        example_line("g mirror", "Short form: g is go; partial match on “mirror”"),
        section("Carry things"),
        example_line("take silver", "Pick up Silver Thread from the floor (partial name)"),
        example_line("inv", "List inventory (also: inventory, i)"),
        example_line("drop silver", "Put it back in the current place"),
        example_line("examine archivist", "Read a person/thing; see what it contains"),
        prose_block(
            "After go, the studio prints a short travel cue, then a full look of the new place. "
            "Items in your inventory travel with you across spatial, dimensional, and temporal links."
        ),
        gap=0,
    )


def _manual_build(kinds: str) -> str:
    return join_blocks(
        rule("How to build"),
        prose_block(
            "Building never leaves the prompt. Create primes, place instances in the world, "
            "connect paths, write descriptions, and nest contents. You stay in your current "
            "place unless you dig and then link and go."
        ),
        section("Places"),
        example_line("dig Quiet Gallery", "New place VEN + instance (same realm/timeline as here)"),
        example_line(
            "link north -> Quiet Gallery both",
            "Exit from here; both = reverse exit too (default type: spatial)",
        ),
        example_line(
            "link through the tear -> Quiet Gallery dimensional both",
            "Typed link: spatial | dimensional | temporal | narrative | conditional",
        ),
        example_line(
            "@desc Soft light on unfinished canvases. Dust tastes like turpentine.",
            "Replace description (\\n for line breaks; @desc + to append)",
        ),
        example_line("undo", "Reverse the last builder action this session"),
        section("Primes, instances, and nesting"),
        example_line(
            "create material Moon Filament | Thin light that remembers tides.",
            "New prime VEN (kinds listed below)",
        ),
        example_line(
            "create object Secret Document of File | Classified…",
            "Specialization: child of parent prime File",
        ),
        example_line("spawn moon-filament", "Instance into the current place"),
        example_line("spawn moon-filament as A single strand", "Named instance override"),
        example_line("create feeling Distant Thunder | Pressure before rain."),
        example_line("spawn distant-thunder", "Feelings land in the feeling slot here"),
        example_line(
            "put Distant Thunder in The Archivist feeling",
            "Move a thing into a container with an optional slot",
        ),
        example_line(
            "elevate silver as Silver Prime",
            "Instance → new prime under origin; lived copy rebinds",
        ),
        example_line("compose Him + Concept of Him as concept", "Prime-level composition"),
        example_line("vens", "List primes; try: vens place  ·  vens tree"),
        example_line("lineage File", "Specialization path root › …"),
        example_line("kinds", f"VEN kinds: {kinds}"),
        prose_block(
            "Typical loop: dig a room → link it → go there → @desc → create/spawn furnishings "
            "→ lore add for canon over time. Use examine on people and places to check containment. "
            "For conceptual trees: create … of <parent>, elevate, compose, vens tree."
        ),
        gap=0,
    )


def _manual_lore() -> str:
    return join_blocks(
        rule("Lore and history"),
        prose_block(
            "Lore is a revision log, not a single blurb. Add entries as the place changes "
            "across your story’s timeline."
        ),
        example_line("lore", "Show revisions for the current place"),
        example_line(
            "lore add Founding | The nave was raised for market travelers.",
            "Title | body  (title optional: lore add just the body works)",
        ),
        example_line("lore search mirror", "Search titles and bodies"),
        gap=0,
    )


def _manual_quick_ref(kinds: str) -> str:
    return join_blocks(
        rule("Quick command reference"),
        _help_section(
            "Movement & senses",
            [
                ("look / l", "Describe here"),
                ("status", "You / place / layers / inv"),
                ("paths / exits / x", "List paths from here"),
                ("go / g <path>", "Travel (partial labels ok)"),
                ("inv / i", "Inventory"),
                ("take / drop", "Pick up or drop by name"),
                ("examine / exam / inspect / in", "Detail a thing here or carried"),
                ("who", "People here"),
            ],
        ),
        _help_section(
            "Lore",
            [
                ("lore", "Revisions for this place"),
                ("lore add …", "title | body  (or body alone)"),
                ("lore search …", "Search lore text"),
            ],
        ),
        _help_section(
            "Builder",
            [
                ("dig <name>", "New place VEN + instance"),
                ("link …", "<exit> -> <place> [type] [both]"),
                ("@desc …", "Show / set / + append / clear place text"),
                ("create …", "<kind> <name> [of parent] [| desc]"),
                ("spawn …", "<ven> [as name] into current place"),
                ("put …", "<thing> in <container> [slot]"),
                ("elevate …", "<thing> [as name] → rebind prime"),
                ("compose …", "whole + part [as role]"),
                ("lineage …", "root › … specialization path"),
                ("undo / u", "Undo last builder action"),
                ("vens [kind|tree]", "List primes or lineage tree"),
                ("kinds", "List VEN kinds"),
            ],
        ),
        _help_section(
            "System",
            [
                ("help / ?", "This manual"),
                ("quit / exit / q", "Leave the studio"),
            ],
        ),
        hint(f"VEN kinds: {kinds}"),
        gap=0,
    )


def _manual_tips() -> str:
    return join_blocks(
        rule("Tips"),
        prose_block(
            "Names can be partial when unique (take silver, go mirror, examine archiv).",
            "Exit labels need not be compass directions — “through grief” is valid if you link it.",
            "The same place VEN can have many instances (Prime vs Shattered halls in the seed).",
            "Ids in status and examine are for precision; day-to-day, use readable names.",
            "Type help anytime. Domain commands never require a separate editor.",
        ),
        gap=0,
    )


def _help_section(title: str, rows: list[tuple[str, str]]) -> str:
    lines = [f"[bold]{safe(title)}[/bold]"]
    for cmd, desc in rows:
        lines.append(
            f"  [bold {ACCENT}]{safe(cmd):18}[/bold {ACCENT}]  [dim]{safe(desc)}[/dim]"
        )
    return "\n".join(lines)
