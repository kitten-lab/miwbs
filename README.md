# MIWBS — zero point

**Day of Days** kernel: HERENOW + `consider` → crate / TPS chronicle.

Full studio port lives in **world-studio** (and git branch `archive/full-port-before-strip`).  
We re-attach capabilities only when you mint a word and ask for a string.

## Run

```bash
pip install -e .
python -m miwbs --reseed --textual
# or plain REPL:
python -m miwbs --reseed --repl
```

World file default: `worlds/day-of-days.world.db`  
Worldshots: `core-tests/`

## Open verbs

| Command | Role |
|---------|------|
| `consider <text>` | Store a consideration |
| `consider -d <text>` | Same body via flag |
| `consider … -e <unix>` | Event time |
| `consider <<studio` | Studio body |
| `consider` | List |
| `clear` · `quit` · `help` | Chrome |

## Docs

- [docs/zero-point.md](docs/zero-point.md) — process (kernel → mint → attach)
- [docs/mentalor.md](docs/mentalor.md) — time spine notes

## Layout

```text
src/miwbs/
  chronicle.py   crates + TPS
  commands.py    zero allowlist
  seed.py        HERENOW only
  cycle.py       soft time node
  cli.py         TUI / REPL
  world.py       VEN/instance engine (still large; slim later)
  …
```
