"""
Zero-point face copy — defaults here; world overrides via godmode.

Edit in the product (batshit mode)::

    @godmode edit consider-hint <<studio
    godmode list
    godmode show live-echo
    godmode reset consider-hint

Logic stays in chronicle / commands. Strings live as **slots**.
Defaults are the factory mouth; each world may keep its own overrides
in meta key ``face_overrides`` (JSON).

Template slots use ``{name}`` placeholders (see SLOT_VARS).

Always-available injects (any face slot)::

    {guy}   last typed command line (same as {cmd} / {line})
    {cmd}
    {line}
    {kras}  ʞ
"""

from __future__ import annotations

import json
import re
from typing import Any

from . import format as fmt
from .db import get_meta, set_meta

# Only expand known-style placeholders. Studio colors use the same braces
# ({c1}…{/}) and must NOT go through string.Formatter (nested/unknown fields
# throw "unexpected '{' in field name").
_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][\w]*)(![rsa])?\}")

# ── marks ──────────────────────────────────────────────────────────────
KRAS = "ʞ"

FACE_META_KEY = "face_overrides"

# slot_id -> default text (templates keep {placeholders})
DEFAULTS: dict[str, str] = {
    # list
    "list-empty": (
        "No considerations yet.\n"
        "  consider <text>                 store one\n"
        "  remember considerations         list them"
    ),
    "consider-hint": (
        "HINT: Remember a consideration! A simple how-to!\n"
        "  remember consideration 01"
    ),
    "list-row": "[{seq_label}]  {kras}:  {body}",
    # live after store
    "live-echo": "ECHO: {body}",
    "live-histories": (
        "HISTORIES STORED:\n"
        "CRATE     {crate_uid}\n"
        "TPS       {tps_uid}\n"
        "EVENT     {event_u}\n"
        "INGEST    {ingest_u}\n"
        "ROOM      {room}\n"
        "CYC       {cyc}\n"
        "POSTER    {poster}\n"
        "SEED      {seed}"
    ),
    # research
    "research-body": "{kras}:  {body}",
    "research-instruments": (
        "CRATE   {crate_uid}\n"
        "TPS     {tps_uid}\n"
        "EVENT   {event_u}\n"
        "INGEST  {ingest_u}\n"
        "ROOM    {room}\n"
        "CYC     {cyc}\n"
        "POSTER  {poster}\n"
        "SEED    {seed}"
    ),
    "research-crate-hint": (
        "HINT: Research a REPORT! A simple how-to!\n"
        "  research crate {crate_uid}"
    ),
    # full crate report — edit in godmode; all crate slugs available
    "research-crate-report": (
        "CRATE REPORT  {crate_uid}\n"
        "\n"
        ":body: {body}\n"
        "\n"
        ":tps: {tps_uid}\n"
        ":event: {event_u}\n"
        ":ingest: {ingest_u}\n"
        ":poster: {poster}\n"
        ":room: {room}\n"
        ":cyc: {cyc}\n"
        ":seed: {seed}\n"
        ":seq: {seq_label}"
    ),
    "research-crate-rabbit": (
        "No crate {token}.\n"
        "(white rabbit — id not on this shelf)"
    ),
    # usage / errors
    "usage-consider": (
        "consider stores a consideration — it does not list.\n"
        "  consider <text>\n"
        "  consider -d <text>\n"
        "  consider … -e <unix>\n"
        "  consider <<studio\n"
        "  remember considerations"
    ),
    "usage-remember": (
        "remember considerations\n"
        "remember consideration 01\n"
        "remember 01"
    ),
    "usage-research": (
        "research crate C1C-FE3-860\n"
        "research crate C1C FE3 860\n"
        "(open a consideration: remember consideration 01)"
    ),
    "zero-blocked": (
        "Zero point — consider + remember + research + godmode + packs.\n"
        "{usage_consider}\n"
        "{usage_remember}\n"
        "{usage_research}\n"
        "godmode list\n"
        "godmode edit <slot> <<studio\n"
        "export vox · export viz · import vox · import viz\n"
        "clear\n"
        "quit\n"
        "help"
    ),
    "help-zero": (
        "zero point\n"
        "  consider <text>              store a consideration\n"
        "  consider -d <text>           same body via flag\n"
        "  consider … -e <n>            event unix\n"
        "  consider <<studio            studio body\n"
        "  remember considerations      list [01] [02] …\n"
        "  remember consideration 01    open one\n"
        "  research crate C1C FE3 860   full crate report\n"
        "  @god voxlist                 face/mouth slots + codes (not skills)\n"
        "  @god edit A01 <<studio       craft by code (or full slot name)\n"
        "  @god show A01                current text (+ factory if overridden)\n"
        "  @god reset A01               drop world override\n"
        "  @god view colorbank          viz C1–C8 (name + hex)\n"
        "  @god edit colorbank C1 -> f3f3f3\n"
        "  @god edit colorbank C1 name Soft White\n"
        "  @god reset colorbank         factory viz\n"
        "  export vox [path]            save face overrides (survive reseed)\n"
        "  export vox --full [path]     save all slot text\n"
        "  export viz [path]            save colorbank\n"
        "  import vox [path]            load face overrides\n"
        "  import viz [path]            load colorbank\n"
        "  clear · quit                 (ok, these two still share a breath)"
    ),
    "missing-consideration": "No consideration {seq_label}.",
    "bad-event-unix": (
        "Bad -e event unix {raw!r}\n"
        "  use an integer (e.g. -e -100000000)"
    ),
    "open-studio-hint": "Open studio with:\n  consider <<studio",
    # success chrome + bodies (edit via godmode; compose with success())
    "success": "SUCCESS  {msg}",
    # avoid [name] around injects — Rich treats [foo] as markup tags
    "godmode-saved": "Face slot · {slot} · saved.  (world override)",
    "godmode-reset": "Face slot · {slot} · reset to factory default.",
    "godmode-unknown": "Unknown face slot {slot!r}.\n  godmode list",
    "godmode-usage": (
        "@god voxlist               face/mouth slots + codes (not skills)\n"
        "@god show A01              or @god show live-echo\n"
        "@god edit A01 <<studio     or @god edit live-echo <<studio\n"
        "@god reset A01\n"
        "@god view colorbank        viz C1–C8\n"
        "@god edit colorbank C1 -> f3f3f3\n"
        "@god edit colorbank C1 name Soft White\n"
        "@god reset colorbank\n"
        "  (also: godmode · @godmode · @god list = thin alias of voxlist)"
    ),
    "colorbank-saved": "Colorbank {code}  {name}  {hex}",
    "colorbank-reset": "Colorbank reset to factory (C1–C8).",
    "colorbank-reset-one": "Colorbank {code} reset to factory.",
    "pack-exported": "Exported {kind} → {path}  ({n} items)",
    "pack-imported": "Imported {kind} ← {path}  ({n} items)",
    "pack-usage": (
        "export vox [path]          face overrides → JSON\n"
        "export vox --full [path]   all slots (current text)\n"
        "export viz [path]          colorbank C1–C8\n"
        "import vox [path]          merge face overrides\n"
        "import viz [path]          load colorbank\n"
        "  default paths next to world: face.vox.json · colorbank.viz.json"
    ),
    # ── error chrome + bodies (full control — no raw machine noise) ──
    "error": "ERR  {msg}",
    "flags-error": (
        "Couldn't read those flags.\n"
        "  {detail}\n"
        "  try:  consider I am somewhere\n"
        "  or:   consider I am somewhere -e 0"
    ),
    "colorbank-bad-code": (
        "Color code {raw} isn't on the bank.\n"
        "  use C1–C8   (godmode view colorbank)"
    ),
    "colorbank-edit-error": (
        "Couldn't edit colorbank.\n"
        "  {detail}\n"
        "  try:  godmode edit colorbank C1 -> f3f3f3\n"
        "  or:   godmode edit colorbank C1 name Soft White"
    ),
    "colorbank-usage": (
        "godmode edit colorbank C1 -> f3f3f3\n"
        "godmode edit colorbank C1 name Soft White\n"
        "godmode edit colorbank C3 Orange Crush -> ff8800\n"
        "godmode view colorbank"
    ),
    "godmode-edit-studio": (
        "Open studio for face slot · {slot} ·\n"
        "  @god edit {slot} <<studio\n"
        "  @godmode edit {slot} <<studio\n"
        "\n{vars_doc}"
    ),
    "pack-error": (
        "Pack step failed.\n"
        "  {detail}\n"
        "  try:  export vox\n"
        "  or:   import vox\n"
        "  see:  export / import help via bare export"
    ),
    "pack-not-found": (
        "No pack file at · {path} ·\n"
        "  export first, or pass a path that exists"
    ),
    "empty-buffer": "Empty buffer; cancelled.",
    "editor-cancelled": "Editor cancelled.",
    "unexpected": (
        "Something slipped in the room.\n"
        "  {detail}\n"
        "  (if this keeps happening, the layer owes you a clearer door)"
    ),
}

# Message kind for godmode list column (chrome vs body vs …)
# Keep labels short — they are a table column, not essays.
SLOT_KIND: dict[str, str] = {
    "success": "success-chrome",
    "godmode-saved": "success-body",
    "godmode-reset": "success-body",
    "colorbank-saved": "success-body",
    "colorbank-reset": "success-body",
    "colorbank-reset-one": "success-body",
    "pack-exported": "success-body",
    "pack-imported": "success-body",
    "pack-usage": "usage",
    "error": "error-chrome",
    "flags-error": "error",
    "colorbank-bad-code": "error",
    "colorbank-edit-error": "error",
    "colorbank-usage": "usage",
    "godmode-edit-studio": "usage",
    "pack-error": "error",
    "pack-not-found": "error",
    "empty-buffer": "error",
    "editor-cancelled": "error",
    "unexpected": "error",
    "live-echo": "live",
    "live-histories": "live",
    "list-empty": "list",
    "consider-hint": "list",
    "list-row": "list",
    "research-body": "research",
    "research-instruments": "research",
    "research-crate-hint": "research",
    "research-crate-report": "research",
    "research-crate-rabbit": "research",
    "missing-consideration": "research",
    "usage-consider": "usage",
    "usage-remember": "usage",
    "usage-research": "usage",
    "godmode-usage": "usage",
    "open-studio-hint": "usage",
    "bad-event-unix": "error",
    "godmode-unknown": "error",
    "zero-blocked": "chrome",
    "help-zero": "chrome",
}

# Stable short codes — call with @god edit A01 <<studio (or full slot name).
# Letter = family; digits = item. Do not renumber casually (export/docs).
SLOT_CODE: dict[str, str] = {
    # A — live (after store)
    "live-echo": "A01",
    "live-histories": "A02",
    # L — list / remember index
    "list-empty": "L01",
    "consider-hint": "L02",
    "list-row": "L03",
    # R — research / crate
    "research-body": "R01",
    "research-instruments": "R02",
    "research-crate-hint": "R03",
    "research-crate-report": "R04",
    "research-crate-rabbit": "R05",
    "missing-consideration": "R06",
    # S — success chrome + bodies
    "success": "S00",
    "godmode-saved": "S01",
    "godmode-reset": "S02",
    "colorbank-saved": "S03",
    "colorbank-reset": "S04",
    "colorbank-reset-one": "S05",
    "pack-exported": "S06",
    "pack-imported": "S07",
    # E — error chrome + bodies
    "error": "E00",
    "flags-error": "E01",
    "bad-event-unix": "E02",
    "colorbank-bad-code": "E03",
    "colorbank-edit-error": "E04",
    "godmode-unknown": "E05",
    "pack-error": "E06",
    "pack-not-found": "E07",
    "empty-buffer": "E08",
    "editor-cancelled": "E09",
    "unexpected": "E10",
    # U — usage / how-to
    "usage-consider": "U01",
    "usage-remember": "U02",
    "usage-research": "U03",
    "godmode-usage": "U04",
    "open-studio-hint": "U05",
    "colorbank-usage": "U06",
    "godmode-edit-studio": "U07",
    "pack-usage": "U08",
    # C — chrome (help / blocked)
    "help-zero": "C01",
    "zero-blocked": "C02",
}

CODE_TO_SLOT: dict[str, str] = {code: slot for slot, code in SLOT_CODE.items()}

# Display order for voxlist sections
VOX_GROUP_ORDER: list[tuple[str, str, str]] = [
    # kind_match or prefix, section title
    ("live", "A", "live — after store"),
    ("list", "L", "list — remember index"),
    ("research", "R", "research — open / crate"),
    ("success-chrome", "S", "success — chrome + bodies"),
    ("success-body", "S", "success — chrome + bodies"),
    ("error-chrome", "E", "error — chrome + bodies"),
    ("error", "E", "error — chrome + bodies"),
    ("usage", "U", "usage — how-to"),
    ("chrome", "C", "chrome — help / blocked"),
]

# human blurbs for godmode list
SLOT_BLURBS: dict[str, str] = {
    "list-empty": "empty consider index",
    "consider-hint": "HINT under the consider list",
    "list-row": "one list line ({seq_label} {body})",
    "live-echo": "mouth line right after store",
    "live-histories": "instrument block after store",
    "research-body": "research consideration body line",
    "research-instruments": "CRATE/TPS under research",
    "research-crate-hint": "HINT after research detail",
    "research-crate-report": "full research crate report (all crate slugs)",
    "research-crate-rabbit": "crate id not found",
    "usage-consider": "consider usage (store only — flat error if empty)",
    "usage-remember": "remember usage (list / open)",
    "usage-research": "research usage (crate report)",
    "zero-blocked": "unknown command reply",
    "help-zero": "help text",
    "missing-consideration": "research missing index",
    "bad-event-unix": "bad -e message",
    "open-studio-hint": "when consider <<studio is one-lined wrong",
    "success": "wraps {msg} — not the sentence itself",
    "godmode-saved": "sentence after face-slot save → {msg}",
    "godmode-reset": "sentence after face-slot reset → {msg}",
    "godmode-unknown": "bad slot name",
    "godmode-usage": "godmode with no args",
    "colorbank-saved": "sentence after colorbank edit → {msg}",
    "colorbank-reset": "sentence after full colorbank reset → {msg}",
    "colorbank-reset-one": "sentence after one-code reset → {msg}",
    "pack-exported": "after export vox|viz → {msg}",
    "pack-imported": "after import vox|viz → {msg}",
    "pack-usage": "export/import usage",
    "error": "ERR line chrome — {msg} is the body",
    "flags-error": "flag parse failure → {detail}",
    "colorbank-bad-code": "bad C1–C8 token → {raw}",
    "colorbank-edit-error": "colorbank edit ValueError → {detail}",
    "colorbank-usage": "edit colorbank without enough args",
    "godmode-edit-studio": "face edit without <<studio",
    "pack-error": "export/import failure → {detail}",
    "pack-not-found": "import missing file → {path}",
    "empty-buffer": "studio save with empty buffer",
    "editor-cancelled": "studio cancelled",
    "unexpected": "uncaught exception → {detail}",
}

# known placeholder names (docs + safe format)
SLOT_VARS: dict[str, tuple[str, ...]] = {
    "list-row": ("seq_label", "body", "kras"),
    "live-echo": ("body",),
    "live-histories": (
        "crate_uid",
        "tps_uid",
        "event_u",
        "ingest_u",
        "room",
        "cyc",
        "poster",
        "seed",
    ),
    "research-body": ("body", "kras"),
    "research-instruments": (
        "crate_uid",
        "tps_uid",
        "event_u",
        "ingest_u",
        "room",
        "cyc",
        "poster",
        "seed",
    ),
    "research-crate-hint": ("crate_uid",),
    "research-crate-report": (
        "crate_uid",
        "tps_uid",
        "tps_id",
        "event_u",
        "event",
        "ingest_u",
        "ingest",
        "body",
        "poster",
        "room",
        "cyc",
        "seed",
        "seq_label",
        "seq",
    ),
    "research-crate-rabbit": ("token",),
    "zero-blocked": ("usage_consider", "usage_remember", "usage_research"),
    "missing-consideration": ("seq_label",),
    "bad-event-unix": ("raw",),
    "success": ("msg",),
    "godmode-saved": ("slot",),
    "godmode-reset": ("slot",),
    "godmode-unknown": ("slot",),
    "colorbank-saved": ("code", "name", "hex"),
    "colorbank-reset-one": ("code",),
    "pack-exported": ("kind", "path", "n"),
    "pack-imported": ("kind", "path", "n"),
    "error": ("msg",),
    "flags-error": ("detail",),
    "colorbank-bad-code": ("raw",),
    "colorbank-edit-error": ("detail",),
    "godmode-edit-studio": ("slot", "vars_doc"),
    "pack-error": ("detail",),
    "pack-not-found": ("path",),
    "unexpected": ("detail",),
}


class _SafeMap(dict):
    """Missing keys stay as {name} so partial templates don't explode."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def known_slots() -> list[str]:
    """Canonical slot ids in voxlist order (by family code)."""
    return sorted(DEFAULTS.keys(), key=lambda s: SLOT_CODE.get(s, "Z99") + s)


def normalize_slot(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def normalize_code(raw: str) -> str | None:
    """L01 / l1 / L001 → L01 if known."""
    s = (raw or "").strip().upper().replace(" ", "")
    if not s:
        return None
    if s in CODE_TO_SLOT:
        return s
    # soft: L1 → L01, E10 stays
    m = re.fullmatch(r"([A-Z])(\d{1,2})", s)
    if m:
        cand = f"{m.group(1)}{int(m.group(2)):02d}"
        if cand in CODE_TO_SLOT:
            return cand
    return None


def resolve_slot(name: str) -> str | None:
    """
    Resolve user token to canonical slot id.

    Accepts full name (``live-echo``) or short code (``A01``, ``a01``, ``A1``).
    """
    raw = (name or "").strip()
    if not raw:
        return None
    code = normalize_code(raw)
    if code:
        return CODE_TO_SLOT[code]
    sk = normalize_slot(raw)
    if sk in DEFAULTS:
        return sk
    return None


def is_slot(name: str) -> bool:
    return resolve_slot(name) is not None


def slot_code(slot: str) -> str:
    return SLOT_CODE.get(normalize_slot(slot), "??")


def load_overrides(world: Any | None) -> dict[str, str]:
    if world is None:
        return {}
    raw = get_meta(world.conn, FACE_META_KEY, "") or ""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in data.items():
        sk = normalize_slot(str(k))
        if sk in DEFAULTS and isinstance(v, str):
            out[sk] = v
    return out


def save_override(world: Any, slot: str, text: str) -> None:
    slot = normalize_slot(slot)
    if slot not in DEFAULTS:
        raise KeyError(slot)
    data = load_overrides(world)
    data[slot] = text
    set_meta(world.conn, FACE_META_KEY, json.dumps(data, ensure_ascii=False, indent=2))


def clear_override(world: Any, slot: str) -> bool:
    """Remove world override. True if something was cleared."""
    slot = normalize_slot(slot)
    data = load_overrides(world)
    if slot not in data:
        return False
    del data[slot]
    set_meta(world.conn, FACE_META_KEY, json.dumps(data, ensure_ascii=False, indent=2))
    return True


def raw_default(slot: str) -> str:
    return DEFAULTS[normalize_slot(slot)]


def raw_text(slot: str, world: Any | None = None) -> str:
    """Unresolved template/source text for a slot (override or default)."""
    slot = normalize_slot(slot)
    if slot not in DEFAULTS:
        raise KeyError(slot)
    ovr = load_overrides(world)
    return ovr.get(slot, DEFAULTS[slot])


def has_override(slot: str, world: Any | None) -> bool:
    return normalize_slot(slot) in load_overrides(world)


def slot_is_studio(slot: str, world: Any | None = None) -> bool:
    from .studio_text import is_studio

    return is_studio(raw_text(slot, world))


def _last_command_line(world: Any | None) -> str:
    if world is None:
        return ""
    return (getattr(world, "last_command_line", None) or "").strip()


def _prep_kwargs(
    sid: str, world: Any | None, kwargs: dict[str, Any], *, studio: bool
) -> dict[str, Any]:
    kw = dict(kwargs)
    if sid == "zero-blocked" and "usage_consider" not in kw:
        # nested usage blurbs as plain source (not painted)
        from .studio_text import strip_studio_header

        kw["usage_consider"] = strip_studio_header(raw_text("usage-consider", world))
        kw["usage_remember"] = strip_studio_header(raw_text("usage-remember", world))
        kw["usage_research"] = strip_studio_header(raw_text("usage-research", world))
    if "kras" not in kw:
        kw["kras"] = KRAS
    # last typed shell line — {guy} / {cmd} / {line}
    last = _last_command_line(world)
    for alias in ("guy", "cmd", "line"):
        if alias not in kw:
            kw[alias] = last
    if studio:
        # inject plain strings; render_studio_text safes + parses
        return {k: ("" if v is None else str(v)) for k, v in kw.items()}
    # plain face: escape injected values so [user] cannot break Rich
    out: dict[str, Any] = {}
    for k, v in kw.items():
        if isinstance(v, str):
            out[k] = fmt.safe(v)
        elif v is None:
            out[k] = ""
        else:
            out[k] = v
    return out


def render(slot_id: str, world: Any | None = None, **kwargs: Any) -> str:
    """
    Resolve placeholders only (source form). Prefer :func:`paint` for display.
    """
    sid = normalize_slot(slot_id)
    if sid not in DEFAULTS:
        raise KeyError(sid)
    from .studio_text import detect_format

    mode, tmpl = detect_format(raw_text(sid, world))
    body = tmpl if mode == "studio" else (tmpl or raw_text(sid, world))
    # for plain mode detect_format returns ("plain", full text)
    if mode == "plain":
        body = raw_text(sid, world)
    kw = _prep_kwargs(sid, world, kwargs, studio=(mode == "studio"))
    return _format_tmpl(body, kw)


def paint(slot_id: str, world: Any | None = None, **kwargs: Any) -> str:
    """
    Display-ready face: studio dialect → whitelist Rich markup, else plain.
    """
    from .studio_text import detect_format, render_studio_text

    sid = normalize_slot(slot_id)
    if sid not in DEFAULTS:
        raise KeyError(sid)
    mode, tmpl = detect_format(raw_text(sid, world))
    if mode == "studio":
        kw = _prep_kwargs(sid, world, kwargs, studio=True)
        filled = _format_tmpl(tmpl, kw)
        return render_studio_text(filled, world=world)
    # plain
    kw = _prep_kwargs(sid, world, kwargs, studio=False)
    return _format_tmpl(raw_text(sid, world), kw)


def paint_hint(slot_id: str, world: Any | None = None, **kwargs: Any) -> str:
    """Hint-style face: dim when plain; studio keeps its own colors."""
    if slot_is_studio(slot_id, world):
        return paint(slot_id, world, **kwargs)
    return f"[dim]{paint(slot_id, world, **kwargs)}[/dim]"


def success(msg: str, world: Any | None = None, *, raw_msg: bool = False) -> str:
    """
    Display-ready SUCCESS line.

    Slot ``success`` is the full line template (``SUCCESS  {msg}`` by default).
    Studio override owns chrome + color codes. Plain factory colors the
    leading SUCCESS word green and the rest soft-white.

    *raw_msg*: when True, *msg* is already escaped/markup-safe (do not re-escape).
    """
    import re

    from .studio_text import detect_format, render_studio_text

    m = "" if msg is None else str(msg)
    raw = raw_text("success", world)
    mode, tmpl = detect_format(raw)

    last = _last_command_line(world)
    base_kw = {
        "msg": m,
        "kras": KRAS,
        "guy": last,
        "cmd": last,
        "line": last,
    }
    if mode == "studio":
        # studio parser safes free text; inject plain msg
        filled = _format_tmpl(tmpl, base_kw)
        return render_studio_text(filled, world=world)

    # plain template
    inject = m if raw_msg else fmt.safe(m)
    last_s = last if raw_msg else fmt.safe(last)
    filled = _format_tmpl(
        raw,
        {
            "msg": inject,
            "kras": KRAS,
            "guy": last_s,
            "cmd": last_s,
            "line": last_s,
        },
    )
    mm = re.match(
        r"^(?P<pre>\s*)(?P<word>SUCCESS)(?P<sp>\s+)(?P<body>.*)$",
        filled,
        re.S | re.I,
    )
    if mm:
        return (
            f"{mm.group('pre')}"
            f"[green] {mm.group('word').upper()} [/green]"
            f"{mm.group('sp')}"
            f"[{fmt.SOFT_WHITE}]{mm.group('body')}[/{fmt.SOFT_WHITE}]"
        )
    return f"[{fmt.SOFT_WHITE}]{filled}[/{fmt.SOFT_WHITE}]"


def success_slot(slot_id: str, world: Any | None = None, **kwargs: Any) -> str:
    """
    Resolve a body slot, then wrap with slot ``success``.

    Edit ``success`` for the SUCCESS chrome; edit body slots
    (``godmode-saved``, ``colorbank-saved``, …) for the message text.

    Full-line studio control: set ``success`` to ``{msg}`` and put the whole
    line (including SUCCESS) in the body slot as studio.
    """
    return _chrome_slot("success", slot_id, world, **kwargs)


def error(msg: str, world: Any | None = None, *, raw_msg: bool = False) -> str:
    """
    Display-ready ERR line (mirror of :func:`success`).

    Slot ``error`` is the chrome template (``ERR  {msg}`` by default).
    Studio override owns the whole line; plain factory uses a red handle.
    """
    import re

    from .studio_text import detect_format, render_studio_text

    m = "" if msg is None else str(msg)
    raw = raw_text("error", world)
    mode, tmpl = detect_format(raw)
    last = _last_command_line(world)
    base = {
        "msg": m,
        "kras": KRAS,
        "guy": last,
        "cmd": last,
        "line": last,
    }
    if mode == "studio":
        filled = _format_tmpl(tmpl, base)
        return render_studio_text(filled, world=world)

    inject = m if raw_msg else fmt.safe(m)
    last_s = last if raw_msg else fmt.safe(last)
    filled = _format_tmpl(
        raw,
        {
            "msg": inject,
            "kras": KRAS,
            "guy": last_s,
            "cmd": last_s,
            "line": last_s,
        },
    )
    mm = re.match(
        r"^(?P<pre>\s*)(?P<word>ERR)(?P<sp>\s+)(?P<body>.*)$",
        filled,
        re.S | re.I,
    )
    if mm:
        return (
            f"{mm.group('pre')}"
            f"[white on red] {mm.group('word').upper()} [/white on red]"
            f"{mm.group('sp')}"
            f"[{fmt.ERR}]{mm.group('body')}[/{fmt.ERR}]"
        )
    return f"[{fmt.ERR}]{filled}[/{fmt.ERR}]"


def error_slot(slot_id: str, world: Any | None = None, **kwargs: Any) -> str:
    """
    Resolve an error body slot, then wrap with slot ``error``.

    Soft usage lines (how-to without fault) should use :func:`paint_hint`
    instead. Use this when something actually failed.
    """
    return _chrome_slot("error", slot_id, world, **kwargs)


def _chrome_slot(
    chrome_slot: str, slot_id: str, world: Any | None = None, **kwargs: Any
) -> str:
    """Shared compose for success/error chrome + body slot."""
    from .studio_text import detect_format

    sid = normalize_slot(slot_id)
    body_raw = raw_text(sid, world)
    body_mode, body_tmpl = detect_format(body_raw)
    wrap = success if chrome_slot == "success" else error

    if body_mode == "studio" and not slot_is_studio(chrome_slot, world):
        body = paint(sid, world, **kwargs)
        return wrap(body, world, raw_msg=True)

    body_filled = render(sid, world, **kwargs)
    if slot_is_studio(chrome_slot, world):
        if body_mode == "studio":
            kw = _prep_kwargs(sid, world, kwargs, studio=True)
            body_filled = _format_tmpl(body_tmpl, kw)
        return wrap(body_filled, world, raw_msg=False)

    return wrap(body_filled, world, raw_msg=True)


def _format_tmpl(tmpl: str, kwargs: dict[str, Any]) -> str:
    """
    Expand ``{name}`` / ``{name!r}`` when *name* is in *kwargs*.

    Unknown braces stay literal — so studio ``{c1}…{/}`` / ``{c3}…{/c3}``
    survive until :func:`studio_text.render_studio_text`.
    """
    if not tmpl:
        return ""

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        conv = m.group(2)  # e.g. "!r" or None
        if name not in kwargs:
            return m.group(0)
        val = kwargs[name]
        if conv == "!r":
            val = repr(val)
        elif conv == "!s":
            val = str(val)
        elif conv == "!a":
            val = ascii(val)
        return str(val)

    try:
        return _PLACEHOLDER_RE.sub(repl, tmpl)
    except Exception as e:  # noqa: BLE001
        return f"[dim](face template error: {fmt.safe(e)})[/dim]\n{fmt.safe(tmpl)}"


def slot_vars_doc(slot: str) -> str:
    slot = normalize_slot(slot)
    vs = SLOT_VARS.get(slot)
    always = "{guy}/{cmd}/{line} (last command)  {kras}"
    if not vs:
        return f"(plain text)  always: {always}"
    return (
        "placeholders: "
        + " ".join("{" + v + "}" for v in vs)
        + f"  · always: {always}"
    )


def edit_seed(slot: str, world: Any | None = None) -> str:
    """Body for studio/plain editor (no .format header line)."""
    from .studio_text import strip_studio_header

    return strip_studio_header(raw_text(slot, world))


# ── face API (callers use these; they honor world overrides) ───────────

def live_echo(body: str, world: Any | None = None) -> str:
    b = (body or "").strip() or "—"
    return paint("live-echo", world, body=b)


def live_histories_stored(world: Any | None = None, **kwargs: Any) -> str:
    """Instrument block after store — accepts full crate_face_kwargs."""
    return paint("live-histories", world, **kwargs)


LIST_EMPTY = DEFAULTS["list-empty"]  # static fallback for imports/tests
LIST_HINT = DEFAULTS["consider-hint"]


def list_row(seq_label: str, body: str, world: Any | None = None) -> str:
    b = (body or "—").strip()
    line = paint(
        "list-row",
        world,
        seq_label=seq_label,
        body=b,
    )
    if slot_is_studio("list-row", world):
        return line
    return f"[{fmt.SOFT_WHITE}]{line}[/{fmt.SOFT_WHITE}]"


def list_face(rows: list[tuple[str, str]], world: Any | None = None) -> str:
    if not rows:
        return paint_hint("list-empty", world)
    lines = [list_row(seq, body, world) for seq, body in rows]
    lines.append("")
    lines.append(paint_hint("consider-hint", world))
    return "\n".join(lines)


def research_consideration_detail(world: Any | None = None, **kwargs: Any) -> str:
    """research consideration N — body + instruments + crate hint."""
    kw = dict(kwargs)
    b = (kw.get("body") or "—").strip()
    crate_uid = kw.get("crate_uid") or kw.get("crate") or ""
    body_line = paint("research-body", world, **{**kw, "body": b})
    inst = paint("research-instruments", world, **kw)
    if slot_is_studio("research-instruments", world):
        inst_block = inst
    else:
        inst_block = "\n".join(
            f"[dim]{ln}[/dim]" for ln in inst.splitlines() if ln.strip()
        )
    if slot_is_studio("research-body", world):
        body_block = body_line
    else:
        body_block = f"[{fmt.SOFT_WHITE}]{body_line}[/{fmt.SOFT_WHITE}]"
    hint_kw = {**kw, "crate_uid": crate_uid}
    return "\n".join(
        [
            body_block,
            "",
            inst_block,
            "",
            paint_hint("research-crate-hint", world, **hint_kw),
        ]
    )


def research_crate_hint(crate_uid: str = "", world: Any | None = None, **kwargs: Any) -> str:
    kw = dict(kwargs)
    if crate_uid:
        kw["crate_uid"] = crate_uid
    return paint_hint("research-crate-hint", world, **kw)


def research_crate_report(world: Any | None = None, **kwargs: Any) -> str:
    """Full research crate report — godmode slot ``research-crate-report``."""
    return paint("research-crate-report", world, **kwargs)


def research_crate_rabbit(token: str, world: Any | None = None) -> str:
    if slot_is_studio("research-crate-rabbit", world):
        return paint("research-crate-rabbit", world, token=token)
    text = paint("research-crate-rabbit", world, token=token)
    lines = text.splitlines()
    if not lines:
        return text
    head, *rest = lines
    if rest:
        return "\n".join([head, f"[dim]{chr(10).join(rest)}[/dim]"])
    return head


# Back-compat module-level names used as constants in older code paths
USAGE_CONSIDER = DEFAULTS["usage-consider"]
USAGE_REMEMBER = DEFAULTS["usage-remember"]
USAGE_RESEARCH = DEFAULTS["usage-research"]
ZERO_BLOCKED = DEFAULTS["zero-blocked"].format(
    usage_consider=USAGE_CONSIDER,
    usage_remember=USAGE_REMEMBER,
    usage_research=USAGE_RESEARCH,
)
HELP_ZERO = DEFAULTS["help-zero"]


def missing_consideration(seq_label: str, world: Any | None = None) -> str:
    return paint_hint("missing-consideration", world, seq_label=seq_label)


def bad_event_unix(raw: str, world: Any | None = None) -> str:
    return paint_hint("bad-event-unix", world, raw=raw)


def open_studio_hint(world: Any | None = None) -> str:
    return paint_hint("open-studio-hint", world)


def zero_blocked(world: Any | None = None) -> str:
    return paint_hint("zero-blocked", world)


def help_zero(world: Any | None = None) -> str:
    return paint_hint("help-zero", world)


def usage_consider(world: Any | None = None) -> str:
    return paint_hint("usage-consider", world)


def usage_remember(world: Any | None = None) -> str:
    return paint_hint("usage-remember", world)


def usage_research(world: Any | None = None) -> str:
    return paint_hint("usage-research", world)


# ── godmode face listing ───────────────────────────────────────────────

def godmode_list_face(world: Any | None = None) -> str:
    from .studio_text import is_studio

    ovr = load_overrides(world)
    lines = [
        "VOX LIST  — face / mouth slots (not skills)",
        "  @god edit A01 <<studio     or  @god edit live-echo <<studio",
        "  @god show A01              or  @god show live-echo",
        "",
        f"  {'':1} {'CODE':<5} {'SLOT':<22}  {'TYPE':<14}  note",
        f"  {'':1} {'----':<5} {'----':<22}  {'----':<14}  ----",
    ]

    # Section headers by family (A L R S E U C)
    family_title = {
        "A": "A — live (after store)",
        "L": "L — list (remember index)",
        "R": "R — research (open / crate)",
        "S": "S — success (chrome + bodies)",
        "E": "E — error (chrome + bodies)",
        "U": "U — usage (how-to)",
        "C": "C — chrome (help / blocked)",
    }
    last_family = ""
    for slot in known_slots():
        code = SLOT_CODE.get(slot, "??")
        family = code[0] if code else "?"
        if family != last_family:
            if last_family:
                lines.append("")
            lines.append(f"  {family_title.get(family, family)}")
            last_family = family
        mark = "*" if slot in ovr else " "
        kind = SLOT_KIND.get(slot, "other")
        st = " ·studio" if is_studio(raw_text(slot, world)) else ""
        blurb = SLOT_BLURBS.get(slot, "")
        lines.append(
            f"  {mark} {code:<5} {slot:<22}  {kind:<14}  {blurb}{st}"
        )
    lines.append("")
    lines.append("  CODE: short call sign — @god edit A01 <<studio")
    lines.append("  TYPE: success-chrome wraps {msg} · success-body is {msg}")
    lines.append("  * = world override · studio = .format: studio stored")
    lines.append("  @god voxlist")
    return "\n".join(lines)


def godmode_show_face(slot: str, world: Any | None = None) -> str:
    from .studio_text import detect_format, render_studio_text, strip_studio_header

    resolved = resolve_slot(slot)
    if resolved is None:
        return error_slot("godmode-unknown", world, slot=slot)
    slot = resolved
    cur = raw_text(slot, world)
    default = DEFAULTS[slot]
    overridden = has_override(slot, world)
    mode, _ = detect_format(cur)
    code = slot_code(slot)
    header = (
        f"SLOT  {code}  {slot}"
        + ("  (override)" if overridden else "  (factory)")
    )
    if mode == "studio":
        header += "  · studio"
    parts = [
        header,
        slot_vars_doc(slot),
        "",
        "── source ──",
        strip_studio_header(cur) if mode == "studio" else cur,
    ]
    if mode == "studio":
        # preview with placeholders still visible (unfilled)
        parts.extend(
            [
                "",
                "── preview ──",
                render_studio_text(strip_studio_header(cur), world=world),
            ]
        )
    if overridden and cur != default:
        parts.extend(["", "── factory ──", default])
    return "\n".join(parts)
