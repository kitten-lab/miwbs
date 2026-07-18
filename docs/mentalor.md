# Mentalor — first stage of MIWBS

*Multidimensional Interactive World Builder Studio*

## Product home

Ment(al)orship is not a peer app. It is the **first stage / layer** of playing MIWBS: empty black box, write thinking, leave residue, expand narrative time as Cycle · node.

Classic `world-studio` remains runnable elsewhere. No automatic world import.

## VEN

**Virtual Entity** and **Variable Energy Node** on the totalizing grid of the fabric of herenow.

## Time spine (one model)

```text
Cycle ʞ  — Day of Days / Ancient of Days (before numbered days)
Cycle 0  — first day-among-days
Cycle N  — bootstraps after prior totalizing runs

Node     — position on a cycle; unit of concept-space writing
Path     — splice chain (1 → between → 1.1 → after → 1.2 → before 1.1 → 1.0.1)
Face     — CYCʞ-0 · CYC0-1.12.3.2
```

Later extensions of the **same** spine (not parallel clocks):

```text
cycle · node
  → cycle · node · realm     (when realm is produced)
  → … · timeline             (when realms split versioning)
```

Item histories will hang on this spine when those senses exist.  
Do **not** grow a permanent separate `@n` cosmology.

## Commands (base kit)

| Command | Role |
|---------|------|
| `remember` / `look` | You remember *title* · CYC… |
| `cycle` / `cycle ʞ` / `cycle 0` | Set / show cycle |
| `node +` or `+` | New node after current |
| `node next` / `node prev` | Move stream |
| `node list` | Paths on this cycle |
| `node insert` | Splice between previous and current |
| `@desc` / `@desc <<studio` | Sculpt current node body (via place surface) |
| `rename` | Remembered title for this node |
| `consider SELF \| …` | Thinker line |
| `consider ECHO \| …` | Self answering self |
| `consider` / `lore` | List considerations |

Onion skin: deferred. Gradient Maker: doctrine only until a play beat demands it.

## SELF and ECHO

- **SELF** — the Thinker  
- **ECHO** — the same Thinker answering; not a second soul  

Stored as lore rows; in mentalor voice they print as **considerations**.

## Seed

`--seed mentalor` (default):

| VEN | Kind | Role |
|-----|------|------|
| **Concept** | concept | The concept of Concept (prime only; not instantiated) |
| **SELF** | concept | The Thinker — player / remember surface |

No person, place, bin, realm, timeline, or other kinds in the DB.  
Mentor workshop starts with **one taught type: `concept`**. Further types are minted as thinking produces them; `create person` etc. **fails until that type is taught**.

Remember surface = SELF instance + Cycle ʞ nodes.

```text
from miwbs import mentor
ws = mentor.workshop_for(world)
ws.mint_type("place", "the sense of location")  # then create place is allowed
```
