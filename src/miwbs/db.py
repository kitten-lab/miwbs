"""SQLite connection and schema bootstrap."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    migrate_schema(conn)
    conn.commit()


def _repair_zero_point_codes(conn: sqlite3.Connection) -> None:
    """
    Mentalor zero-point: untyped SELF code is literally ``0``, ECHO is ``1``.

    Older migrations treated bare integers as missing codes (``parse_ven_code``
    only knows XXX-NNN) and rewrote them to OTH-001 / OTH-002. Restore.
    """
    import re as _re

    for want_name, want_code in (("SELF", "0"), ("ECHO", "1")):
        row = conn.execute(
            """
            SELECT id, code, kind, name, slug FROM vens
            WHERE upper(trim(name)) = ? OR upper(trim(slug)) = ?
            ORDER BY created_at, id LIMIT 1
            """,
            (want_name, want_name),
        ).fetchone()
        if row is None:
            continue
        if (row["kind"] or "").strip():
            continue  # typed primes keep kind codes
        cur = (row["code"] or "").strip()
        if cur == want_code:
            continue
        # Free want_code if another row holds it
        holder = conn.execute(
            "SELECT id FROM vens WHERE code = ? AND id != ?",
            (want_code, row["id"]),
        ).fetchone()
        if holder is not None:
            # Park the holder on next free bare int (or next OTH if typed later)
            taken = {
                (r["code"] or "").strip()
                for r in conn.execute(
                    "SELECT code FROM vens WHERE code IS NOT NULL AND code != ''"
                ).fetchall()
            }
            n = 2
            while str(n) in taken or str(n) == want_code:
                n += 1
            conn.execute(
                "UPDATE vens SET code = ? WHERE id = ?",
                (str(n), holder["id"]),
            )
        conn.execute(
            "UPDATE vens SET code = ? WHERE id = ?",
            (want_code, row["id"]),
        )


def migrate_schema(conn: sqlite3.Connection) -> None:
    """Idempotent additive migrations for older world.db files."""
    cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(vens)").fetchall()
    }
    if cols and "parent_ven_id" not in cols:
        conn.execute(
            "ALTER TABLE vens ADD COLUMN parent_ven_id TEXT "
            "REFERENCES vens(id) ON DELETE SET NULL"
        )
    if cols:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_vens_parent ON vens(parent_ven_id)"
        )
    # Compact VEN codes (RLM-001) — typeable handle alongside long cute slugs
    if cols and "code" not in cols:
        conn.execute("ALTER TABLE vens ADD COLUMN code TEXT")
    if cols or "code" in {
        row[1] for row in conn.execute("PRAGMA table_info(vens)").fetchall()
    }:
        import re as _re

        from .ids import format_ven_code, kind_code_prefix, parse_ven_code

        rows = conn.execute(
            "SELECT id, name, kind, code FROM vens ORDER BY kind, created_at, id"
        ).fetchall()
        # Track max seq per prefix from existing XXX-NNN codes, then fill gaps
        max_by_prefix: dict[str, int] = {}
        max_bare = -1  # untyped bare integer codes 0, 1, 2, …
        for r in rows:
            c = (r["code"] or "").strip()
            existing = parse_ven_code(c)
            if existing:
                pref, _, num = existing.partition("-")
                try:
                    max_by_prefix[pref] = max(max_by_prefix.get(pref, 0), int(num))
                except ValueError:
                    pass
            elif _re.fullmatch(r"\d+", c):
                max_bare = max(max_bare, int(c))
        for r in rows:
            c = (r["code"] or "").strip()
            # Keep compact XXX-NNN *and* bare untyped integers (SELF=0, ECHO=1)
            if parse_ven_code(c) or _re.fullmatch(r"\d+", c):
                continue
            kind = (r["kind"] or "").strip()
            if not kind:
                # Untyped prime without a code yet — bare next int, never OTH-
                max_bare += 1
                code = str(max_bare)
            else:
                pref = kind_code_prefix(kind)
                n = max_by_prefix.get(pref, 0) + 1
                max_by_prefix[pref] = n
                code = format_ven_code(pref, n)
            conn.execute("UPDATE vens SET code = ? WHERE id = ?", (code, r["id"]))
        # Repair: mentalor SELF/ECHO must stay codes 0 and 1 (migration used to
        # rewrite bare 0/1 → OTH-00N because parse_ven_code rejects bare ints).
        _repair_zero_point_codes(conn)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_vens_code ON vens(code)"
        )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ven_parts (
            id              TEXT PRIMARY KEY,
            whole_ven_id    TEXT NOT NULL REFERENCES vens(id) ON DELETE CASCADE,
            part_ven_id     TEXT NOT NULL REFERENCES vens(id) ON DELETE CASCADE,
            role            TEXT NOT NULL DEFAULT 'part',
            ordinal         INTEGER NOT NULL DEFAULT 0,
            notes           TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (whole_ven_id, part_ven_id, role)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ven_parts_whole ON ven_parts(whole_ven_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ven_parts_part ON ven_parts(part_ven_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS text_revisions (
            id              TEXT PRIMARY KEY,
            subject_type    TEXT NOT NULL,
            subject_id      TEXT NOT NULL,
            field           TEXT NOT NULL DEFAULT 'body',
            title           TEXT NOT NULL DEFAULT '',
            body            TEXT NOT NULL DEFAULT '',
            format          TEXT NOT NULL DEFAULT 'plain',
            author          TEXT NOT NULL DEFAULT 'builder',
            note            TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_text_rev_subject "
        "ON text_revisions(subject_type, subject_id, created_at)"
    )

    # Dialogs: cute slug + compact DLG-NNN code alongside opaque dlg_ id
    dlg_info = conn.execute("PRAGMA table_info(dialogs)").fetchall()
    if dlg_info:
        dlg_cols = {row[1] for row in dlg_info}
        if "slug" not in dlg_cols:
            conn.execute("ALTER TABLE dialogs ADD COLUMN slug TEXT")
            dlg_cols.add("slug")
        if "code" not in dlg_cols:
            conn.execute("ALTER TABLE dialogs ADD COLUMN code TEXT")
            dlg_cols.add("code")
        from .ids import cute_name, format_ven_code

        rows = conn.execute(
            "SELECT id, title, slug, code FROM dialogs ORDER BY created_at, id"
        ).fetchall()
        used: set[str] = set()
        max_dlg_n = 0
        for r in rows:
            existing = (r["slug"] or "").strip()
            if existing:
                used.add(existing.casefold())
            code = (r["code"] or "").strip().upper()
            if code.startswith("DLG-"):
                try:
                    max_dlg_n = max(max_dlg_n, int(code.split("-", 1)[1]))
                except ValueError:
                    pass
        for r in rows:
            existing = (r["slug"] or "").strip()
            if not existing:
                base = cute_name(r["title"] or "") or "DIALOG"
                if base in ("UNNAMED", ""):
                    base = "DIALOG"
                candidate = base
                n = 2
                while candidate.casefold() in used:
                    candidate = f"{base}-{n}"
                    n += 1
                used.add(candidate.casefold())
                conn.execute(
                    "UPDATE dialogs SET slug = ? WHERE id = ?",
                    (candidate, r["id"]),
                )
            code = (r["code"] or "").strip()
            if not code:
                max_dlg_n += 1
                conn.execute(
                    "UPDATE dialogs SET code = ? WHERE id = ?",
                    (format_ven_code("DLG", max_dlg_n), r["id"]),
                )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_dialogs_slug ON dialogs(slug)"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_dialogs_code ON dialogs(code)"
        )

    # Story-time nodes + material history (life of item)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS timeline_nodes (
            id                      TEXT PRIMARY KEY,
            timeline_instance_id    TEXT NOT NULL REFERENCES instances(id)
                ON DELETE CASCADE,
            node_index              INTEGER NOT NULL,
            name                    TEXT NOT NULL DEFAULT '',
            description             TEXT NOT NULL DEFAULT '',
            created_at              TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE (timeline_instance_id, node_index)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_timeline_nodes_tl "
        "ON timeline_nodes(timeline_instance_id, node_index)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history_entries (
            id                      TEXT PRIMARY KEY,
            subject_type            TEXT NOT NULL,
            subject_id              TEXT NOT NULL,
            event_code              TEXT NOT NULL DEFAULT '',
            place_instance_id       TEXT REFERENCES instances(id)
                ON DELETE SET NULL,
            place_name              TEXT NOT NULL DEFAULT '',
            realm_instance_id       TEXT REFERENCES instances(id)
                ON DELETE SET NULL,
            realm_name              TEXT NOT NULL DEFAULT '',
            timeline_instance_id    TEXT REFERENCES instances(id)
                ON DELETE SET NULL,
            timeline_name           TEXT NOT NULL DEFAULT '',
            story_when              TEXT NOT NULL DEFAULT '@unknown',
            node_index              INTEGER,
            verb                    TEXT NOT NULL DEFAULT 'record',
            note                    TEXT NOT NULL DEFAULT '',
            created_at              TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    # Older DBs: add event_code and backfill HST-NNN per row
    hist_cols = {
        row[1]
        for row in conn.execute("PRAGMA table_info(history_entries)").fetchall()
    }
    if hist_cols and "event_code" not in hist_cols:
        conn.execute(
            "ALTER TABLE history_entries ADD COLUMN event_code TEXT "
            "NOT NULL DEFAULT ''"
        )
        hist_cols.add("event_code")
    if hist_cols and "event_code" in hist_cols:
        from .ids import format_ven_code

        orphans = conn.execute(
            """
            SELECT id FROM history_entries
            WHERE event_code IS NULL OR TRIM(event_code) = ''
            ORDER BY created_at, id
            """
        ).fetchall()
        if orphans:
            max_n = 0
            for r in conn.execute(
                "SELECT event_code FROM history_entries "
                "WHERE event_code GLOB 'HST-[0-9]*'"
            ).fetchall():
                code = (r["event_code"] or "").strip().upper()
                if code.startswith("HST-"):
                    try:
                        max_n = max(max_n, int(code.split("-", 1)[1]))
                    except ValueError:
                        pass
            for r in orphans:
                max_n += 1
                code = format_ven_code("HST", max_n)
                conn.execute(
                    "UPDATE history_entries SET event_code = ? WHERE id = ?",
                    (code, r["id"]),
                )
    # Place + snapshotted names for where-the-act-happened context
    for col, decl in (
        ("place_instance_id", "TEXT"),
        ("place_name", "TEXT NOT NULL DEFAULT ''"),
        ("realm_name", "TEXT NOT NULL DEFAULT ''"),
        ("timeline_name", "TEXT NOT NULL DEFAULT ''"),
    ):
        if hist_cols and col not in hist_cols:
            conn.execute(
                f"ALTER TABLE history_entries ADD COLUMN {col} {decl}"
            )
            hist_cols.add(col)
    # Best-effort fill of missing name snapshots from current instance titles
    # (instances have name_override; formal name lives on the prime VEN)
    _inst_title = (
        "COALESCE(NULLIF(TRIM(i.name_override), ''), v.name, '')"
    )
    if hist_cols and "place_name" in hist_cols:
        conn.execute(
            f"""
            UPDATE history_entries
            SET place_name = COALESCE(
                (
                    SELECT {_inst_title}
                    FROM instances i
                    JOIN vens v ON v.id = i.ven_id
                    WHERE i.id = history_entries.place_instance_id
                ),
                place_name, ''
            )
            WHERE (place_name IS NULL OR TRIM(place_name) = '')
              AND place_instance_id IS NOT NULL
            """
        )
        conn.execute(
            f"""
            UPDATE history_entries
            SET realm_name = COALESCE(
                (
                    SELECT {_inst_title}
                    FROM instances i
                    JOIN vens v ON v.id = i.ven_id
                    WHERE i.id = history_entries.realm_instance_id
                ),
                realm_name, ''
            )
            WHERE (realm_name IS NULL OR TRIM(realm_name) = '')
              AND realm_instance_id IS NOT NULL
            """
        )
        conn.execute(
            f"""
            UPDATE history_entries
            SET timeline_name = COALESCE(
                (
                    SELECT {_inst_title}
                    FROM instances i
                    JOIN vens v ON v.id = i.ven_id
                    WHERE i.id = history_entries.timeline_instance_id
                ),
                timeline_name, ''
            )
            WHERE (timeline_name IS NULL OR TRIM(timeline_name) = '')
              AND timeline_instance_id IS NOT NULL
            """
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_subject "
        "ON history_entries(subject_type, subject_id, created_at)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_timeline "
        "ON history_entries(timeline_instance_id, node_index)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_event_code "
        "ON history_entries(event_code)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_history_place "
        "ON history_entries(place_instance_id)"
    )


def get_meta(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return row["value"]


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
