# So You're God - Now What?
## A QUICK GUIDE TO BUILDING WORLDS WHILE INSIDE THEM

Zero-point **miwbs** cheat sheet. Stripped to what exists *right now*.  
No classic cast. No named vox/viz pack wardrobe yet. Just HERENOW, considerations, godmode mouth + skin, and simple export so reseed doesn’t eat your craft.

This file is a **collab doc** — edit freely; agents should re-read before changing it.

---

## Boot

```text
python -m miwbs
python -m miwbs --world path\to\my.world.db
python -m miwbs -w path\to\my.world.db
```

World is a SQLite file. Face overrides + colorbank stick to **that** world.

Shell commands that always work:

| Command | What |
|---------|------|
| `help` / `?` | zero-point help |
| `clear` / `clr` | clear the log |
| `quit` / `exit` / `q` | leave |

Anything else unknown → blocked with a short “zero point” blurb (rewrite that blurb in godmode: slot `zero-blocked`).

---

## Consider (store only)

`consider` **writes**. It does **not** list. Bare `consider` is a flat usage error.

```text
consider <text>
consider -d <text>
consider … -e <unix>          event time (e.g. -e -100000000 or -e 0)
consider <<studio             open STUDIO Writer for a multi-line body
wonder …                      same as consider
```

After store you get:

1. **Mouth line** — face slot `live-echo` (factory: `ECHO: {body}`)
2. **Instruments** — face slot `live-histories` (CRATE / TPS / EVENT / INGEST / ROOM / CYC / POSTER / SEED)

Each consideration freezes a **crate** snapshot (see slugs below).

Studio tips: **Ctrl+S** save · **Esc** cancel · **F2** / **Alt+P** markup preview.  
Apostrophes in one-liners are fine (`don't`, `Kras's`).

---

## Remember (lookup)

```text
remember considerations       list [01] [02] …
remember consideration 01     open one
remember 01                   same
```

List rows are soft white `ʞ` lines. No instrument noise on the index.  
Footer hint is face slot `consider-hint` (points at remember, not bare consider).

---

## Research (crate report + thin alias)

```text
research crate C1C-FE3-860
research crate C1C FE3 860    soft spaces ok
```

Full report uses face slot **`research-crate-report`** (godmode-editable, all crate slugs).

**Thin alias (muscle memory):**

```text
research consideration 01     → same as remember consideration 01
research considerations       → same as remember considerations
```

Prefer **remember** for people-facing recall; **research** for instruments / crate id follow-through.

Missing crate id → slot `research-crate-rabbit` (not found), not a full report.

---

## Godmode (only door for face + viz)

Prefix optional: `godmode` or `@godmode`.

### Face (vox — world overrides, not named packs yet)

```text
godmode list
godmode show <slot>
godmode edit <slot> <<studio
godmode reset <slot>
```

`godmode list` has a **TYPE** column so chrome vs body is obvious:

| TYPE | Meaning |
|------|---------|
| `success-chrome` | wraps `{msg}` — slot `success` |
| `success-body` | sentence that *is* `{msg}` after ok actions |
| `live` | right after `consider` store |
| `list` | remember index |
| `research` | open / crate report / missing |
| `usage` | how-to blurbs (`usage-consider`, `usage-remember`, …) |
| `error` | bad input lines |
| `chrome` | help / zero-blocked |

`*` = world override · `studio` = stored with `.format: studio`.

#### Handy slots

| Slot | TYPE-ish | Role |
|------|----------|------|
| `live-echo` | live | mouth after store |
| `live-histories` | live | instrument block after store |
| `consider-hint` | list | HINT under `remember considerations` |
| `list-empty` | list | empty index |
| `list-row` | list | one index line |
| `research-body` | research | open-one body line |
| `research-instruments` | research | CRATE/TPS/… under open |
| `research-crate-hint` | research | HINT after open → crate |
| `research-crate-report` | research | full `research crate` report |
| `research-crate-rabbit` | research | crate id not found |
| `success` | success-chrome | `SUCCESS  {msg}` shape |
| `godmode-saved` / `godmode-reset` | success-body | after face edit/reset |
| `colorbank-saved` / `colorbank-reset` / `colorbank-reset-one` | success-body | after viz edits |
| `pack-exported` / `pack-imported` | success-body | after export/import |
| `usage-consider` | usage | bare/wrong consider |
| `usage-remember` | usage | bare/wrong remember |
| `usage-research` | usage | bare/wrong research |
| `bad-event-unix` | error | bad `-e` |
| `missing-consideration` | error | bad remember index |
| `godmode-unknown` | error | bad face slot name |
| `help-zero` / `zero-blocked` | chrome | help + unknown command |

**Success has two layers:** edit `success` for the handle/shape; edit the `*-saved` / `*-reset` body slots for the sentence that fills `{msg}`.

---

## Slugs — `{placeholders}` in face copy

Only expand **known** names. Studio colors (`{c1}…{/}`) are *not* format fields; they pass through to the studio painter.

### Always on (any face slot)

| Slug | Meaning |
|------|---------|
| `{guy}` / `{cmd}` / `{line}` | last typed command line |
| `{kras}` | ʞ |

### Live / list

| Slug | Where |
|------|--------|
| `{body}` | consideration text |
| `{seq_label}` | `01`, `02`, … |

### Crate snapshot (store-time freeze — research report & instruments)

| Slug | Meaning |
|------|---------|
| `{crate_uid}` / `{crate}` / `{crate_id}` | crate id |
| `{tps_uid}` / `{tps_id}` / `{tps}` | TPS shelf id |
| `{event_u}` / `{event}` / `{event_unix}` | event time |
| `{ingest_u}` / `{ingest}` / `{ingest_unix}` | wall-clock ingest |
| `{body}` | text stored |
| `{poster}` | *who* wrote (zero default: `ʞ`, not the room) |
| `{room}` | *where* — surface / node title at store |
| `{cyc}` / `{cyc_position}` | e.g. `CYC ʞ` |
| `{seed}` / `{seed_name}` | starting seed (e.g. `mentalor`) |
| `{seq}` / `{seq_label}` | stable list index |
| `{kind}` | e.g. `consideration` |

**Poster ≠ room.** Room is place; poster is author face. Until SELF exists, poster is unsigned `ʞ` (or world meta `poster_name` / `author_name` if you set one later).

### Success bodies

| Slug | Where |
|------|--------|
| `{msg}` | inside slot `success` only (filled by body slots) |
| `{slot}` | godmode-saved / godmode-reset |
| `{code}` `{name}` `{hex}` | colorbank-saved |
| `{kind}` `{path}` `{n}` | pack-exported / pack-imported |

Example live mouth:

```text
@godmode edit live-echo <<studio
```

```text
ran {guy}
heard {c1}{body}{/}
```

Example crate report craft:

```text
@godmode edit research-crate-report <<studio
```

```text
CRATE {crate_uid}  ·  {cyc}
:poster: {poster}
:room: {room}
:body: {body}
```

Multi-line `{body}` under `:label:` keeps hang-indent with the value column.

`godmode show <slot>` prints placeholders + source (+ studio preview).

---

## Colorbank (viz — fixed 8)

No freeform palette adds. Eight slots. **Studio paints with codes**, not display names.

| Code | Factory name | Factory hex |
|------|--------------|-------------|
| C1 | White | `#f3f3f3` |
| C2 | Gray | `#9a9aa3` |
| C3 | Red | `#e85d5d` |
| C4 | Blue | `#6aa6e8` |
| C5 | Green | `#6bcb8a` |
| C6 | Yellow | `#e8c84a` |
| C7 | Purple | `#b07ce8` |
| C8 | Orange | `#e89a4a` |

```text
godmode view colorbank
godmode edit colorbank C1 -> aabbcc
godmode edit colorbank C1 name Soft White
godmode edit colorbank C3 Orange Crush -> ff8800
godmode reset colorbank
godmode reset colorbank C1
```

Names are **labels**. Markup uses **codes**:

```text
{c1}soft ink{/}
{C6}pop{/}
{c3}warn-ish{/}
```

Also style (not bank slots): `{dim}…{/}` · `{bright}…{/}`.

---

## Export / import (survive reseed)

Not a pack wardrobe — just backup mouth + skin so you can wipe considerations or reseed and reimport craft.

```text
export vox                 →  <world-dir>/face.vox.json
export viz                 →  <world-dir>/colorbank.viz.json
export vox --full          →  every face slot’s current text
export vox path\to\mine.vox.json
import vox
import viz
import vox path\to\mine.vox.json
```

| Kind | Contents |
|------|----------|
| **vox** | face overrides (or `--full` all slots) |
| **viz** | C1–C8 name + hex |

Ritual: `export vox` · `export viz` → reseed → `import vox` · `import viz`.

---

## Studio markup (tiny subset)

Face slots saved with `<<studio` store `.format: studio` and print through the studio parser.

| Write | Effect |
|-------|--------|
| `**bold**` | bold |
| `_italic_` | italic |
| `` `code` `` | bold code-ish |
| `{c1}text{/}` | colorbank C1 |
| `{c1}text{/c1}` | same, closed by name |
| `# heading` | heading |
| `> quote` | dim quote rail |
| `:Label: value` | field row (multi-line values hang under the value column) |

Legacy color *names* (`{yellow}` etc.) still limp for old prose; **new face copy should use C1–C8**.

---

## Mental model

```text
YOU
  consider                 → store (crate + TPS snapshot)
  remember                 → list / open considerations
  research crate …         → crate report (instruments)
  research consideration   → thin alias → remember
  @godmode face slots      → mouth (vox)
  @godmode colorbank       → skin (viz)
  export / import vox|viz  → backup craft across reseed

WORLD FILE
  face_overrides           → slot text
  viz_colorbank            → C1–C8 name + hex
  herenow_crates           → consideration crates
```

Not yet (on purpose):

- named vox / viz packs (`Sexy Wolf`, `SOFT-PASTELS`)
- `@godmode set here vox|viz …`
- godmode password
- classic look / mint / places / books / SELF cast

---

## Suggested play order

1. `consider I am somewhere.`
2. `remember considerations` — list + hint  
3. `remember consideration 01` — open one  
4. `research crate …` — full report (from crate id on the open)  
5. `@godmode view colorbank` — see C1–C8  
6. `@godmode edit colorbank C1 -> e8e8ec`  
7. `@godmode edit live-echo <<studio` → `heard {c1}{body}{/}`  
8. `@godmode edit research-crate-report <<studio` — own the report with slugs  
9. `export vox` · `export viz` before you reseed  

---

## Files (if you fall out of the product)

| Path | Role |
|------|------|
| `src/miwbs/zero_face.py` | factory face slots + paint |
| `src/miwbs/colorbank.py` | factory C1–C8 + world overrides |
| `src/miwbs/pack_io.py` | export / import vox · viz |
| `src/miwbs/commands.py` | allowlist + verbs |
| `src/miwbs/chronicle.py` | crates / TPS / snapshots |
| `docs/zero-point.md` | doctrine (why zero is thin) |

In-product edits beat source hunting. That’s the point of godmode.

---

*Until the next shelf.*
)
