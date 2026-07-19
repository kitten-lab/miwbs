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
Face     — CYC ʞ · CYC ʞ.1 · CYC 0.ʞ  (kras = nothing first, before 0; origin is just ʞ)
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
| `node +` or `+` | After mark: tail → next sibling (1, 2…); mid-stream → splice under mark (0.1 between kras and 1) |
| `node next` / `node prev` | Move stream |
| `node list` | Paths on this cycle |
| `node insert` | Splice between previous and current |
| `@desc` / `@desc <<studio` | Sculpt current node body (via place surface) |
| `rename` | Room title (`rename here`) or Thinker (`rename me`) — two instances |
| `consider SELF \| …` | Thinker line |
| `consider ECHO \| …` | Self answering self |
| `consider` / `lore` | List considerations |

Onion skin: deferred. Gradient Maker: doctrine only until a play beat demands it.

## SELF and ECHO

- **SELF** — the Thinker  
- **ECHO** — the same Thinker answering; not a second soul  

Stored as lore rows; in mentalor voice they print as **considerations**.

## Seed — zero point

`--seed mentalor` (default):

| VEN | Kind | Code | Role |
|-----|------|------|------|
| **SELF** | *(none)* | **`0`** | The Thinker — untyped zero point |
| **ECHO** | *(none)* | **`1`** | Backflow mouth — dialog partner for `consider` |

No Concept prime. No taught types. No person/place/bin/realm/timeline.

**consider** opens a talk-style SELF ↔ ECHO dialog (`/fin` ends).  
**consider note** still feeds one-shot lore notes.

From here you shape:

```text
from miwbs import mentor
ws = mentor.workshop_for(world)
ws.mint_type("concept", "the sense of Concept")   # type emerges
# then: create concept Concept | the concept of Concept
# later: mint_type("place", …) → create place …
```

Remember surface = first **where** (kind `where`, code WHR-…) + Cycle ʞ nodes.  
SELF (0) stands in it; ECHO (1) shares it. **place** is a *kind of* where (`where/place`), not the root.
