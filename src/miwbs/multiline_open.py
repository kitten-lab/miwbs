"""Parse << / <<studio openers — consider only (zero point)."""

from __future__ import annotations

from .text_editor import MultilineSession, editor_title_for

_END_MARKERS = ("<<studio", "<<")


def _strip_heredoc(s: str) -> tuple[str, bool] | None:
    raw = s.strip()
    low = raw.lower()
    for end in _END_MARKERS:
        if low.endswith(end):
            rest = raw[: -len(end)].strip()
            studio = end == "<<studio" or "studio" in low
            return rest, studio
    return None


def is_multiline_opener(line: str) -> bool:
    return parse_multiline_opener(line) is not None


def parse_multiline_opener(line: str) -> MultilineSession | None:
    """
    consider <<studio
    consider -e -100 <<studio
    """
    s = line.strip()
    if not s or "<<" not in s:
        return None
    low = s.lower()
    if low == "consider" or low.startswith("consider ") or low.startswith(
        "wonder "
    ) or low == "wonder":
        return _parse_consider(s)
    return None


def _parse_consider(s: str) -> MultilineSession | None:
    low = s.lower()
    if low.startswith("consider"):
        rest = s[len("consider") :].strip()
    elif low.startswith("wonder"):
        rest = s[len("wonder") :].strip()
    else:
        return None
    stripped = _strip_heredoc(rest if rest else "<<studio")
    if stripped is None:
        low_r = rest.lower().strip()
        if low_r in ("<<", "<<studio", "{", "{studio"):
            studio = "studio" in low_r
            sess = MultilineSession(kind="consider", studio=studio, consider_rest="")
            sess.title = editor_title_for(sess)
            return sess
        return None
    head, studio = stripped
    sess = MultilineSession(
        kind="consider",
        studio=studio,
        consider_rest=head.strip(),
    )
    sess.title = editor_title_for(sess)
    return sess


def seed_initial_body(world, session: MultilineSession) -> str:
    return ""


def seed_page_title(world, session: MultilineSession) -> str | None:
    return None


def commit_multiline_session(
    world,
    session: MultilineSession,
    body: str,
    *,
    page_title: str | None = None,
):
    """Apply editor body — consider crates only."""
    from . import chronicle as ch
    from .argflags import CONSIDER_FLAG_ALIASES, parse_named_flags
    from .commands import CommandResult
    from . import format as fmt

    _ = page_title
    body = (body or "").strip()
    if not body:
        return CommandResult(True, fmt.hint("Empty buffer; cancelled."))

    if session.kind != "consider":
        return CommandResult(
            True, fmt.err(f"Unknown multiline kind {session.kind!r}")
        )

    event_unix: int | None = None
    rest = (session.consider_rest or "").strip()
    if rest:
        parsed = parse_named_flags(rest, aliases=CONSIDER_FLAG_ALIASES)
        if not parsed.error:
            event_raw = parsed.get("event")
            if event_raw:
                try:
                    event_unix = int(str(event_raw).strip().lstrip("uU"))
                except ValueError:
                    pass

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
    return CommandResult(True, f"{echo}\n\n{hist}")
