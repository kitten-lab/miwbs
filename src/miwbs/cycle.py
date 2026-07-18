"""
Mentalor time spine: Cycle + splice-path nodes.

Not multiverse timeline/realm. Face: CYC ʞ.0 · CYC 0.1.2 · …
ʞ (kras) = Day of Days (Ancient of Days), the cycle before numbered 0.
Item history will hang on this spine later.

Onion skin is deferred. Studio @desc sculpts the current node body.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .db import get_meta, set_meta

if TYPE_CHECKING:
    from .world import World

META_KEY = "mentalor_cycles"
META_MODE = "mentalor_mode"

# Cycle id ʞ or non-negative integer as string
_CYCLE_RE = re.compile(r"^(ʞ|k|K|\d+)$")


def is_mentalor(world: World) -> bool:
    v = get_meta(world.conn, META_MODE, "") or ""
    return v.strip().lower() in ("1", "true", "yes", "mentalor", "on")


def set_mentalor_mode(world: World, on: bool = True) -> None:
    set_meta(world.conn, META_MODE, "1" if on else "0")


def _norm_cycle_id(raw: str) -> str:
    s = (raw or "").strip()
    if s in ("ʞ", "k", "K", "kod", "day-of-days", "ancient"):
        return "ʞ"
    if s.isdigit():
        return str(int(s))
    raise ValueError(f"Unknown cycle {raw!r} — use ʞ or a day number (0, 1, …)")


@dataclass
class CycleNode:
    path: str  # e.g. "0", "1.2", "1.0.1"
    title: str = ""
    body: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "title": self.title, "body": self.body}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CycleNode:
        return cls(
            path=str(d.get("path") or "0"),
            title=str(d.get("title") or ""),
            body=str(d.get("body") or ""),
        )


@dataclass
class Cycle:
    id: str
    label: str = ""
    # Stream order: list of path keys (sibling splice order preserved here)
    order: list[str] = field(default_factory=list)
    nodes: dict[str, CycleNode] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "order": list(self.order),
            "nodes": {k: n.to_dict() for k, n in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Cycle:
        nodes = {
            str(k): CycleNode.from_dict(v) if isinstance(v, dict) else CycleNode(path=str(k))
            for k, v in (d.get("nodes") or {}).items()
        }
        order = [str(x) for x in (d.get("order") or [])]
        if not order and nodes:
            order = sorted(nodes.keys(), key=_path_sort_key)
        return cls(
            id=str(d.get("id") or "0"),
            label=str(d.get("label") or ""),
            order=order,
            nodes=nodes,
        )


def _path_sort_key(path: str) -> tuple:
    parts = []
    for p in (path or "0").split("."):
        try:
            parts.append((0, int(p)))
        except ValueError:
            parts.append((1, p))
    return tuple(parts)


@dataclass
class CycleState:
    current_cycle: str = "ʞ"
    current_path: str = "0"
    cycles: dict[str, Cycle] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_cycle": self.current_cycle,
            "current_path": self.current_path,
            "cycles": {k: c.to_dict() for k, c in self.cycles.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CycleState:
        cycles = {
            str(k): Cycle.from_dict(v) if isinstance(v, dict) else Cycle(id=str(k))
            for k, v in (d.get("cycles") or {}).items()
        }
        return cls(
            current_cycle=str(d.get("current_cycle") or "ʞ"),
            current_path=str(d.get("current_path") or "0"),
            cycles=cycles,
        )


def load_state(world: World) -> CycleState:
    raw = get_meta(world.conn, META_KEY, "") or ""
    if not raw.strip():
        return default_state()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return default_state()
    if not isinstance(data, dict):
        return default_state()
    st = CycleState.from_dict(data)
    if "ʞ" not in st.cycles:
        st.cycles["ʞ"] = _day_of_days_cycle()
    return st


def save_state(world: World, state: CycleState) -> None:
    set_meta(world.conn, META_KEY, json.dumps(state.to_dict(), ensure_ascii=False))


def default_state() -> CycleState:
    c = _day_of_days_cycle()
    return CycleState(current_cycle="ʞ", current_path="0", cycles={"ʞ": c})


def _day_of_days_cycle() -> Cycle:
    n = CycleNode(
        path="0",
        title="the pressure of something",
        body="",
    )
    return Cycle(
        id="ʞ",
        label="Day of Days · Ancient of Days",
        order=["0"],
        nodes={"0": n},
    )


def face_address(cycle_id: str, path: str) -> str:
    """
    Short form with breathing room: ``CYC ʞ.0`` · ``CYC 0.1.2``.

    Kras (ʞ) is the cycle *before* numbered day 0. Space after CYC;
    cycle and node path joined with ``.`` (node path may itself contain dots).
    """
    c = "ʞ" if cycle_id in ("ʞ", "k", "K") else str(cycle_id)
    p = path if path else "0"
    return f"CYC {c}.{p}"


def current_face(state: CycleState) -> str:
    return face_address(state.current_cycle, state.current_path)


def current_node(state: CycleState) -> CycleNode | None:
    cyc = state.cycles.get(state.current_cycle)
    if not cyc:
        return None
    return cyc.nodes.get(state.current_path)


def ensure_current(state: CycleState) -> CycleNode:
    cyc = state.cycles.get(state.current_cycle)
    if cyc is None:
        cyc = Cycle(id=state.current_cycle, label="", order=[], nodes={})
        state.cycles[state.current_cycle] = cyc
    node = cyc.nodes.get(state.current_path)
    if node is None:
        node = CycleNode(path=state.current_path or "0")
        cyc.nodes[node.path] = node
        if node.path not in cyc.order:
            cyc.order.append(node.path)
        state.current_path = node.path
    return node


def _next_sibling_path(parent: str, existing: list[str]) -> str:
    """Next path under parent: parent.1, parent.2, … or '0','1' if parent empty."""
    if parent in ("", None):
        prefix = ""
        children = [p for p in existing if "." not in p]
        nums = []
        for p in children:
            try:
                nums.append(int(p))
            except ValueError:
                pass
        n = (max(nums) + 1) if nums else 0
        return str(n)
    prefix = parent + "."
    nums = []
    for p in existing:
        if p.startswith(prefix) and p.count(".") == parent.count(".") + 1:
            tail = p[len(prefix) :]
            if "." not in tail:
                try:
                    nums.append(int(tail))
                except ValueError:
                    pass
    n = (max(nums) + 1) if nums else 1
    return f"{parent}.{n}"


def add_node_after_current(state: CycleState) -> CycleNode:
    """
    + : append a new sibling after current in stream order.

    Splice pedigree: if current is 1, new may be 2 (top-level) or if we
    always append as next top-level after max root — here we insert *after*
    current in order list with path = next sibling under same parent.
    """
    cyc = state.cycles[state.current_cycle]
    cur = state.current_path
    parent = cur.rsplit(".", 1)[0] if "." in cur else ""
    # siblings share parent; new path under same parent
    new_path = _next_sibling_path(parent, list(cyc.nodes.keys()))
    # if new_path collides (shouldn't), walk
    while new_path in cyc.nodes:
        new_path = _next_sibling_path(parent, list(cyc.nodes.keys()) + [new_path + ".x"])
        # fallback unique
        if new_path in cyc.nodes:
            new_path = f"{cur}.1"
            i = 1
            while new_path in cyc.nodes:
                i += 1
                new_path = f"{cur}.{i}"
            break

    node = CycleNode(path=new_path, title="", body="")
    cyc.nodes[new_path] = node
    if cur in cyc.order:
        idx = cyc.order.index(cur) + 1
        cyc.order.insert(idx, new_path)
    else:
        cyc.order.append(new_path)
    state.current_path = new_path
    return node


def insert_between(state: CycleState, left_path: str, right_path: str) -> CycleNode:
    """
    Splice between two ordered nodes: path left.1 if free under left,
    else left.N next.
    Evidence of insert order lives in the path string.
    """
    cyc = state.cycles[state.current_cycle]
    new_path = _next_sibling_path(left_path, list(cyc.nodes.keys()))
    node = CycleNode(path=new_path, title="", body="")
    cyc.nodes[new_path] = node
    if left_path in cyc.order:
        idx = cyc.order.index(left_path) + 1
        cyc.order.insert(idx, new_path)
    else:
        cyc.order.append(new_path)
    state.current_path = new_path
    return node


def move_rel(state: CycleState, delta: int) -> CycleNode | None:
    cyc = state.cycles.get(state.current_cycle)
    if not cyc or not cyc.order:
        return None
    try:
        i = cyc.order.index(state.current_path)
    except ValueError:
        i = 0
        state.current_path = cyc.order[0]
    j = max(0, min(len(cyc.order) - 1, i + delta))
    state.current_path = cyc.order[j]
    return cyc.nodes.get(state.current_path)


def set_cycle(state: CycleState, cycle_raw: str) -> Cycle:
    cid = _norm_cycle_id(cycle_raw)
    if cid not in state.cycles:
        label = "Day of Days · Ancient of Days" if cid == "ʞ" else f"Day {cid}"
        node = CycleNode(path="0", title="", body="")
        state.cycles[cid] = Cycle(
            id=cid, label=label, order=["0"], nodes={"0": node}
        )
    state.current_cycle = cid
    cyc = state.cycles[cid]
    if not cyc.order:
        n = CycleNode(path="0")
        cyc.nodes["0"] = n
        cyc.order = ["0"]
    if state.current_path not in cyc.nodes:
        state.current_path = cyc.order[0]
    return cyc


def remember_surface_id(world: World) -> str | None:
    """
    Instance that holds the remember title/body for the current beat.

    Prefer player location (place world). Day of Days: no place — use SELF
    (the player instance).
    """
    loc = world.player_location()
    if loc is not None:
        return loc.id
    return world.player_id()


def apply_node_to_surface(world: World, node: CycleNode, face: str) -> None:
    """Push node title/body onto the remember surface (place or SELF)."""
    sid = remember_surface_id(world)
    if not sid:
        return
    title = (node.title or "").strip() or "something not yet named"
    body = node.body if node.body is not None else ""
    world.set_name_override(sid, title)
    world.set_description(sid, body)


# Back-compat alias
apply_node_to_place = apply_node_to_surface


def pull_place_into_node(world: World, node: CycleNode) -> None:
    """After @desc / rename, copy surface text back into current node."""
    sid = remember_surface_id(world)
    if not sid:
        return
    inst = world.get_instance(sid)
    if inst is None:
        return
    node.body = inst.description if inst.description is not None else ""
    ov = world.get_name_override(sid)
    if ov:
        node.title = str(ov)
    elif inst.name:
        node.title = inst.name


def sync_world_to_current(world: World) -> str:
    """Load state, apply current node to surface, return face address."""
    st = load_state(world)
    node = ensure_current(st)
    face = current_face(st)
    apply_node_to_surface(world, node, face)
    save_state(world, st)
    return face


def remember_header_line(world: World, place_name: str) -> str | None:
    """Look lead: OBSERVING: <cyan title>  <dim CYC ʞ.0>"""
    if not is_mentalor(world):
        return None
    from .format import safe

    st = load_state(world)
    face = current_face(st)
    name = (place_name or "").strip() or "something"
    return (
        f"OBSERVING: [cyan]{safe(name)}[/cyan]  [dim]{safe(face)}[/dim]"
    )
