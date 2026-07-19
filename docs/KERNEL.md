# Kernel map (for human + wire-beast eyes)

**Live face:** HERENOW + `consider` → crate / TPS.  
**Port archive:** git `archive/full-port-before-strip` · folder `C:\Builds\miwbs-port-archive` · repo `world-studio`.

## Call path

```text
cli.main
  → ensure_world / seed_world_mentalor
  → run_textual | run_repl
       → parse_multiline_opener?  (consider <<studio)
       → dispatch
            → _consider_herenow
                 → chronicle.append_consideration
```

## Modules (keep)

| File | Role |
|------|------|
| `cli.py` | TUI / REPL entry |
| `commands.py` | Allowlist + consider |
| `chronicle.py` | Crates + TPS store (meta JSON) |
| `seed.py` | HERENOW-only seed |
| `cycle.py` | Soft cycle ʞ node (under the table) |
| `multiline_open.py` | `consider <<studio` |
| `text_editor.py` | Studio buffer |
| `studio_text.py` | Markup whitelist for studio |
| `argflags.py` | `-d` body · `-e` event |
| `format.py` | Soft/hard white, hints, badges |
| `ids.py` | Names, codes, short refs |
| `db.py` / `schema.sql` | SQLite (schema still wide; unused tables ok) |
| `world.py` | VEN/instance engine (**still fat** — attach surface later) |
| `history.py` | Command up/down only |
| `undo.py` | Stub stack World still constructs |
| `measure.py` / `textutil.py` | Editor / text helpers |

## Not here (bring back via attach)

Book, wiki, dialog, mentor, HST history, ven packs, dig/link/portal, classic seeds, full help manuals.

## Tests

`tests/test_consider_chronicle.py` only.
