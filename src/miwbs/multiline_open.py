"""Parse << / <<studio openers — consider + godmode face edit (zero point)."""

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
    @godmode edit consider-hint <<studio
    godmode edit live-echo <<studio
    """
    s = line.strip()
    if not s or "<<" not in s:
        return None
    low = s.lower()
    if low == "consider" or low.startswith("consider ") or low.startswith(
        "wonder "
    ) or low == "wonder":
        return _parse_consider(s)
    if (
        low.startswith("@godmode")
        or low.startswith("godmode")
        or low.startswith("@god")
    ):
        return _parse_godmode(s)
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


def _parse_godmode(s: str) -> MultilineSession | None:
    """
    @godmode edit <slot> <<studio
    @god edit <slot> <<studio
    godmode edit <slot> <<
    """
    low = s.lower().strip()
    # Longest prefix first (@godmode before @god)
    if low.startswith("@godmode"):
        rest = s[len("@godmode") :].strip()
    elif low.startswith("godmode"):
        rest = s[len("godmode") :].strip()
    elif low.startswith("@god"):
        rest = s[len("@god") :].strip()
    else:
        return None

    stripped = _strip_heredoc(rest)
    if stripped is None:
        return None
    head, studio = stripped
    parts = head.split()
    if len(parts) < 2:
        return None
    if parts[0].lower() != "edit":
        return None
    slot_tok = parts[1].strip()
    if not slot_tok:
        return None
    # Resolve name or short code (A01) at parse time when possible
    from . import zero_face as face

    resolved = face.resolve_slot(slot_tok)
    slot = resolved if resolved else slot_tok.lower().replace("_", "-")
    sess = MultilineSession(
        kind="face_edit",
        studio=studio,
        face_slot=slot,
    )
    sess.title = editor_title_for(sess)
    return sess


def seed_initial_body(world, session: MultilineSession) -> str:
    if session.kind == "face_edit" and session.face_slot:
        from . import zero_face as face

        slot = face.resolve_slot(session.face_slot) or face.normalize_slot(
            session.face_slot
        )
        if not face.is_slot(slot):
            return f"# unknown slot: {session.face_slot}\n# @god voxlist\n"
        return face.edit_seed(slot, world)
    return session.initial_body or ""


def seed_page_title(world, session: MultilineSession) -> str | None:
    return None


def commit_multiline_session(
    world,
    session: MultilineSession,
    body: str,
    *,
    page_title: str | None = None,
):
    """Apply editor body — consider crates or godmode face slots."""
    from . import chronicle as ch
    from .argflags import CONSIDER_FLAG_ALIASES, parse_named_flags
    from .commands import CommandResult
    from . import format as fmt
    from . import zero_face as face

    _ = page_title

    if session.kind == "face_edit":
        return _commit_face_edit(world, session, body)

    body = (body or "").strip()
    if not body:
        return CommandResult(
            True, face.error_slot("empty-buffer", world)
        )

    if session.kind != "consider":
        return CommandResult(
            True,
            face.error_slot(
                "unexpected",
                world,
                detail=f"Unknown multiline kind {session.kind!r}",
            ),
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
    echo = ch.format_echo_considered(body, world)
    hist = ch.format_histories_stored(crate, world)
    return CommandResult(True, f"{echo}\n\n{hist}")


def _commit_face_edit(world, session: MultilineSession, body: str):
    from .commands import CommandResult
    from . import format as fmt
    from . import zero_face as face
    from .studio_text import prepare_stored_text

    slot = face.resolve_slot(session.face_slot or "") or face.normalize_slot(
        session.face_slot or ""
    )
    if not face.is_slot(slot):
        return CommandResult(
            True,
            face.error_slot(
                "godmode-unknown", world, slot=session.face_slot or slot
            ),
        )
    if body is None:
        return CommandResult(True, face.error_slot("empty-buffer", world))
    # Preserve intentional whitespace / trailing newlines the user crafted,
    # but strip a single final newline from editor habit.
    text = body
    if text.endswith("\n") and not text.endswith("\n\n"):
        text = text[:-1]
    # <<studio → store with .format: studio so print uses studio whitelist parser
    text = prepare_stored_text(text, studio=bool(session.studio))
    face.save_override(world, slot, text)
    return CommandResult(
        True, face.success_slot("godmode-saved", world, slot=slot)
    )
