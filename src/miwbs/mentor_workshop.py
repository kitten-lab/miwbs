"""VEN Mentor workshop — merged into MIWBS as hidden production machinery.

Not first-stage verbs. Empty bootstrap: no ambient types.
Doctrine: primes can later *become* types; Day of Days starts with SELF only
in the world DB. This module is the form-house side channel (JSON workshop).

Production layers:
  property  — semantic capability atoms
  type      — shape roots you teach (from primes, later)
  shell     — named form that equips properties
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import (
    KIND_CODE_PREFIX,
    cute_name,
    format_ven_code,
    names_match,
    new_id,
    slugify,
)

PACK_FORMAT = "aidm.ven"
PACK_VERSION = 3

_NAME_RE = re.compile(r"[a-z][a-z0-9_-]*")


def parse_kind_spec(raw: str) -> tuple[str, str | None]:
    """type or type/subtype — freeform (no Earth-kind alias fold)."""
    s = (raw or "").strip()
    if not s:
        return "", None
    for sep in ("/", ":"):
        if sep in s:
            left, _, right = s.partition(sep)
            return left.strip().lower(), (right.strip().lower() or None)
    return s.lower(), None


def kind_code_prefix(kind: str) -> str:
    k = (kind or "").lower().strip()
    if k in KIND_CODE_PREFIX:
        return KIND_CODE_PREFIX[k]
    letters = "".join(c for c in k.upper() if c.isalpha())
    if len(letters) >= 3:
        return letters[:3]
    return (letters + "XXX")[:3]


def aidm_home() -> Path:
    return Path.home() / ".aidm"


def default_workshop_path() -> Path:
    """Prefer ~/.aidm/ven-mentor; keep reading legacy ~/.aidm/ven-minter if present."""
    mentor = aidm_home() / "ven-mentor"
    legacy = aidm_home() / "ven-minter"
    mentor_file = mentor / "workshop.json"
    legacy_file = legacy / "workshop.json"
    if mentor_file.is_file():
        return mentor_file
    if legacy_file.is_file():
        # Stay on legacy path so existing workshops keep working until user migrates.
        return legacy_file
    mentor.mkdir(parents=True, exist_ok=True)
    return mentor_file


def ven_collector_dir() -> Path:
    d = aidm_home() / "ven-collector"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class VenProperty:
    """
    A minted semantic property — capability / sense a VEN may equip.

    Not machine storage (the desc field existing is not “can be described”).
    Codes: PRP-00 …
    """

    name: str
    description: str = ""
    code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "code": self.code,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VenProperty:
        return cls(
            name=str(d.get("name") or "").lower().strip(),
            description=str(d.get("description") or ""),
            code=str(d.get("code") or ""),
        )


@dataclass
class VenType:
    """A mintable root type (shape). Codes: PVT-00 …"""

    name: str
    description: str = ""
    code: str = ""  # PVT-NN
    # Default property names equipped onto shells of this type (by lineage).
    properties: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "properties": list(self.properties),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VenType:
        props = [
            str(x).lower().strip()
            for x in (d.get("properties") or [])
            if str(x).strip()
        ]
        return cls(
            name=str(d.get("name") or "").lower().strip(),
            description=str(d.get("description") or ""),
            code=str(d.get("code") or ""),
            properties=props,
        )


@dataclass
class VenSubtype:
    """Subtype under a type. Codes: PST-0001, …"""

    type_name: str
    name: str
    description: str = ""
    code: str = ""  # PST-NNNN

    def to_dict(self) -> dict[str, Any]:
        return {
            "type_name": self.type_name,
            "name": self.name,
            "description": self.description,
            "code": self.code,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> VenSubtype:
        return cls(
            type_name=str(d.get("type_name") or "").lower().strip(),
            name=str(d.get("name") or "").lower().strip(),
            description=str(d.get("description") or ""),
            code=str(d.get("code") or ""),
        )


@dataclass
class LoreNote:
    title: str = ""
    body: str = ""


@dataclass
class Mint:
    """Prime VEN shell in the workshop — equips properties as it develops."""

    id: str
    name: str
    kind: str
    code: str
    slug: str
    description: str = ""
    subtype: str | None = None
    lore: list[LoreNote] = field(default_factory=list)
    parent_id: str | None = None
    slot: str = "interior"
    # Property names equipped on this shell (type defaults are separate).
    properties: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "subtype": self.subtype,
            "code": self.code,
            "slug": self.slug,
            "description": self.description,
            "lore": [{"title": n.title, "body": n.body} for n in self.lore],
            "parent_id": self.parent_id,
            "slot": self.slot,
            "properties": list(self.properties),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Mint:
        lore = [
            LoreNote(title=str(x.get("title") or ""), body=str(x.get("body") or ""))
            for x in (d.get("lore") or [])
            if isinstance(x, dict)
        ]
        props = [
            str(x).lower().strip()
            for x in (d.get("properties") or [])
            if str(x).strip()
        ]
        return cls(
            id=str(d["id"]),
            name=str(d.get("name") or ""),
            kind=str(d.get("kind") or "thing"),
            subtype=(str(d["subtype"]) if d.get("subtype") else None),
            code=str(d.get("code") or "OTH-000"),
            slug=str(d.get("slug") or "unnamed"),
            description=str(d.get("description") or ""),
            lore=lore,
            parent_id=(str(d["parent_id"]) if d.get("parent_id") else None),
            slot=str(d.get("slot") or "interior"),
            properties=props,
        )


def parse_flags(arg: str) -> tuple[dict[str, str], list[str], str | None]:
    """
    Parse ``-n name -d desc -t type`` free-order flags.

    Values may be multi-word until the next flag.
    Returns (flags, positionals, error).
    """
    raw = (arg or "").strip()
    if not raw:
        return {}, [], None
    # tokenize with simple shlex-like split for quotes
    try:
        import shlex

        tokens = shlex.split(raw, posix=True)
    except ValueError as e:
        return {}, [], f"Could not parse flags: {e}"

    aliases = {
        "n": "name",
        "name": "name",
        "d": "desc",
        "desc": "desc",
        "description": "desc",
        "t": "type",
        "type": "type",
        "kind": "type",
    }
    flags: dict[str, str] = {}
    positionals: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("--") and len(tok) > 2:
            key = tok[2:].lower()
            key = aliases.get(key, key)
            i += 1
            parts: list[str] = []
            while i < len(tokens) and not tokens[i].startswith("-"):
                parts.append(tokens[i])
                i += 1
            flags[key] = " ".join(parts).strip()
            continue
        if tok.startswith("-") and len(tok) == 2 and tok[1].isalpha():
            key = aliases.get(tok[1].lower(), tok[1].lower())
            i += 1
            parts = []
            while i < len(tokens) and not tokens[i].startswith("-"):
                parts.append(tokens[i])
                i += 1
            flags[key] = " ".join(parts).strip()
            continue
        if tok.startswith("-") and "=" in tok:
            # -n=Lab
            left, _, right = tok.partition("=")
            key = left.lstrip("-").lower()
            key = aliases.get(key, key)
            flags[key] = right.strip()
            i += 1
            continue
        positionals.append(tok)
        i += 1
    return flags, positionals, None


class Workshop:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_workshop_path()
        self.properties: dict[str, VenProperty] = {}
        self.types: dict[str, VenType] = {}
        self.subtypes: list[VenSubtype] = []
        self.items: dict[str, Mint] = {}
        self._seq: dict[str, int] = {}  # per kind for prime codes + pvt/pst/prp
        self.load()
        self._ensure_seed_types()
        self._backfill_type_codes()
        self._backfill_property_codes()

    def _next_pvt_n(self) -> int:
        n = int(self._seq.get("pvt", 0)) + 1
        self._seq["pvt"] = n
        return n

    def _next_prp_n(self) -> int:
        n = int(self._seq.get("prp", 0)) + 1
        self._seq["prp"] = n
        return n

    def _format_pvt(self, n: int) -> str:
        """PVT-00 … PVT-99, then PVT-100+ (width expands)."""
        if n < 100:
            return f"PVT-{n:02d}"
        return f"PVT-{n}"

    def _format_prp(self, n: int) -> str:
        if n < 100:
            return f"PRP-{n:02d}"
        return f"PRP-{n}"

    def _alloc_pvt(self) -> str:
        return self._format_pvt(self._next_pvt_n())

    def _alloc_prp(self) -> str:
        return self._format_prp(self._next_prp_n())

    def _alloc_pst(self, parent_type: VenType) -> str:
        """
        Subtype under parent: PVT-00-ST-0, PVT-00-ST-1, … then ST-10+.

        Sequence is per parent type name (not global).
        """
        parent_code = parent_type.code or self._alloc_pvt()
        if not parent_type.code:
            parent_type.code = parent_code
        key = f"pst:{parent_type.name}"
        # start at 0
        if key not in self._seq:
            self._seq[key] = -1
        n = int(self._seq[key]) + 1
        self._seq[key] = n
        return f"{parent_code}-ST-{n}"

    def _backfill_type_codes(self) -> None:
        """Assign PVT / PVT-xx-ST-n codes to legacy workshop rows missing them."""
        dirty = False
        # Migrate old PVT-0001 (4-digit) style if present — only fill missing
        for t in self.types.values():
            if not t.code:
                t.code = self._alloc_pvt()
                dirty = True
        for s in self.subtypes:
            if not s.code:
                parent = self.types.get(s.type_name)
                if parent is None:
                    parent = VenType(
                        name=s.type_name,
                        description="",
                        code=self._alloc_pvt(),
                    )
                    self.types[s.type_name] = parent
                s.code = self._alloc_pst(parent)
                dirty = True
        if dirty:
            self.save()

    def _backfill_property_codes(self) -> None:
        dirty = False
        for p in self.properties.values():
            if not p.code:
                p.code = self._alloc_prp()
                dirty = True
        if dirty:
            self.save()

    def _ensure_seed_types(self) -> None:
        """
        Production bootstrap: conceptualized nothing.

        Do not install person/place/thing/… as ambient cosmology.
        Do not install can-describe / can-contain as ambient properties.
        Types and properties are minted material.

        See docs/production-base.md.
        """
        return

    def load(self) -> None:
        if not self.path.is_file():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.properties = {
            k: VenProperty.from_dict(v)
            for k, v in (data.get("properties") or {}).items()
        }
        self.types = {
            k: VenType.from_dict(v) for k, v in (data.get("types") or {}).items()
        }
        self.subtypes = [
            VenSubtype.from_dict(x)
            for x in (data.get("subtypes") or [])
            if isinstance(x, dict)
        ]
        self.items = {
            k: Mint.from_dict(v) for k, v in (data.get("items") or {}).items()
        }
        self._seq = {str(k): int(v) for k, v in (data.get("seq") or {}).items()}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "properties": {k: p.to_dict() for k, p in self.properties.items()},
            "types": {k: t.to_dict() for k, t in self.types.items()},
            "subtypes": [s.to_dict() for s in self.subtypes],
            "items": {k: m.to_dict() for k, m in self.items.items()},
            "seq": self._seq,
        }
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ── properties (producer layer) ────────────────────────────────────

    def mint_property(self, name: str, description: str = "") -> VenProperty:
        key = (name or "").strip().lower()
        if not key or not _NAME_RE.fullmatch(key):
            raise ValueError(
                "Property name: start with a letter, then letters/digits/_/-"
            )
        if key in self.properties:
            raise ValueError(f"Property {key!r} already exists")
        p = VenProperty(
            name=key,
            description=(description or "").strip(),
            code=self._alloc_prp(),
        )
        self.properties[key] = p
        self.save()
        return p

    def resolve_property(self, query: str) -> VenProperty | None:
        q = (query or "").strip()
        if not q:
            return None
        key = q.lower()
        if key in self.properties:
            return self.properties[key]
        q_up = q.upper().replace(" ", "-")
        hits = [
            p
            for p in self.properties.values()
            if p.code.upper() == q_up
            or p.code.upper().replace("-", "") == q_up.replace("-", "")
            or names_match(q, p.name)
        ]
        if len(hits) == 1:
            return hits[0]
        return None

    def resolve_property_or_raise(self, query: str) -> VenProperty:
        p = self.resolve_property(query)
        if p is None:
            raise ValueError(f"No property matching {query!r}.  Try: properties")
        return p

    def equip_property(self, prop_q: str, target_q: str) -> tuple[VenProperty, str, str]:
        """
        Equip a property onto a type or a prime shell.

        Returns (property, target_kind, target_label) where target_kind is
        'type' or 'ven'.
        """
        prop = self.resolve_property_or_raise(prop_q)
        tkey = (target_q or "").strip().lower()
        if tkey in self.types:
            t = self.types[tkey]
            if prop.name not in t.properties:
                t.properties.append(prop.name)
                self.save()
            return prop, "type", t.name
        m = self.resolve_or_raise(target_q)
        if prop.name not in m.properties:
            m.properties.append(prop.name)
            self.save()
        return prop, "ven", m.name

    def unequip_property(
        self, prop_q: str, target_q: str
    ) -> tuple[VenProperty, str, str]:
        prop = self.resolve_property_or_raise(prop_q)
        tkey = (target_q or "").strip().lower()
        if tkey in self.types:
            t = self.types[tkey]
            if prop.name in t.properties:
                t.properties = [x for x in t.properties if x != prop.name]
                self.save()
            return prop, "type", t.name
        m = self.resolve_or_raise(target_q)
        if prop.name in m.properties:
            m.properties = [x for x in m.properties if x != prop.name]
            self.save()
        return prop, "ven", m.name

    def effective_properties(
        self, m: Mint
    ) -> list[tuple[str, str, VenProperty | None]]:
        """
        Resolved props for a shell: type defaults + shell equips.

        Each row: (name, source 'type'|'shell', property or None if orphan).
        Shell-level wins source label if on both.
        """
        seen: dict[str, str] = {}
        t = self.types.get(m.kind)
        if t:
            for name in t.properties:
                seen[name] = "type"
        for name in m.properties:
            seen[name] = "shell"
        rows: list[tuple[str, str, VenProperty | None]] = []
        for name, src in sorted(seen.items(), key=lambda x: x[0]):
            rows.append((name, src, self.properties.get(name)))
        return rows

    # ── types / subtypes ───────────────────────────────────────────────

    def mint_type(self, name: str, description: str = "") -> VenType:
        key = (name or "").strip().lower()
        if not key or not _NAME_RE.fullmatch(key):
            raise ValueError(
                "Type name: start with a letter, then letters/digits/_/-"
            )
        if key in self.types:
            raise ValueError(f"Type {key!r} already exists")
        t = VenType(
            name=key,
            description=(description or "").strip(),
            code=self._alloc_pvt(),
        )
        self.types[key] = t
        self.save()
        return t

    def mint_subtype(
        self, type_name: str, name: str, description: str = ""
    ) -> VenSubtype:
        tkey = (type_name or "").strip().lower()
        skey = (name or "").strip().lower()
        if tkey not in self.types:
            raise ValueError(
                f"Unknown type {tkey!r}.  mint type -n {tkey} -d …  first"
            )
        if not skey or not _NAME_RE.fullmatch(skey):
            raise ValueError("Subtype name: letter then letters/digits/_/-")
        for s in self.subtypes:
            if s.type_name == tkey and s.name == skey:
                raise ValueError(f"Subtype {tkey}/{skey} already exists")
        parent = self.types[tkey]
        st = VenSubtype(
            type_name=tkey,
            name=skey,
            description=(description or "").strip(),
            code=self._alloc_pst(parent),
        )
        self.subtypes.append(st)
        self.save()
        return st

    def subtypes_for(self, type_name: str) -> list[VenSubtype]:
        t = (type_name or "").lower()
        return [s for s in self.subtypes if s.type_name == t]

    def resolve_type_spec(self, spec: str) -> tuple[str, str | None]:
        """Parse type or type/subtype; must already be minted (no ambient KINDS)."""
        kind, sub = parse_kind_spec(spec)
        if not kind:
            raise ValueError("Type required")
        if kind not in self.types:
            raise ValueError(f"Unknown type '{kind}'")
        if sub:
            if not any(
                s.type_name == kind and s.name == sub for s in self.subtypes
            ):
                raise ValueError(
                    f"Unknown subtype {kind}/{sub}.  "
                    f"mint sub-type -t {kind} -n {sub} -d …"
                )
        return kind, sub

    # ── VEN shells ─────────────────────────────────────────────────────

    def _alloc_code(self, kind: str) -> str:
        prefix = kind_code_prefix(kind)
        n = int(self._seq.get(kind, 0)) + 1
        self._seq[kind] = n
        return format_ven_code(prefix, n)

    def mint_ven(
        self,
        type_spec: str,
        name: str,
        *,
        description: str = "",
    ) -> Mint:
        kind, subtype = self.resolve_type_spec(type_spec)
        name = (name or "").strip()
        if not name:
            raise ValueError("Name required (-n)")
        mid = new_id("mint")
        code = self._alloc_code(kind)
        slug = slugify(name)
        base = slug
        n = 2
        while any(m.slug == slug for m in self.items.values()):
            slug = f"{base}-{n}"
            n += 1
        m = Mint(
            id=mid,
            name=name,
            kind=kind,
            subtype=subtype,
            code=code,
            slug=slug,
            description=description or "",
        )
        self.items[mid] = m
        self.save()
        return m

    def resolve(self, query: str) -> Mint | None:
        q = (query or "").strip()
        if not q:
            return None
        if q in self.items:
            return self.items[q]
        q_up = q.upper().replace(" ", "-")
        hits: list[Mint] = []
        for m in self.items.values():
            if m.code.upper() == q_up or m.code.upper().replace(
                "-", ""
            ) == q_up.replace("-", ""):
                hits.append(m)
                continue
            if (
                names_match(q, m.name)
                or names_match(q, m.slug)
                or names_match(q, cute_name(m.name))
            ):
                hits.append(m)
        if len(hits) == 1:
            return hits[0]
        return None

    def resolve_or_raise(self, query: str) -> Mint:
        m = self.resolve(query)
        if m is None:
            raise ValueError(f"No ven matching {query!r}.  Try: vens")
        return m

    def roots(self) -> list[Mint]:
        return [m for m in self.items.values() if not m.parent_id]

    def contents(self, parent_id: str) -> list[Mint]:
        return [m for m in self.items.values() if m.parent_id == parent_id]

    def put(self, child_q: str, parent_q: str, *, slot: str = "interior") -> tuple[Mint, Mint]:
        child = self.resolve_or_raise(child_q)
        parent = self.resolve_or_raise(parent_q)
        if child.id == parent.id:
            raise ValueError("Cannot put a ven into itself")
        walk: str | None = parent.id
        seen: set[str] = set()
        while walk:
            if walk == child.id:
                raise ValueError("That would create a cycle")
            if walk in seen:
                break
            seen.add(walk)
            walk = self.items[walk].parent_id if walk in self.items else None
        child.parent_id = parent.id
        child.slot = slot or "interior"
        self.save()
        return child, parent

    def take(self, child_q: str) -> Mint:
        child = self.resolve_or_raise(child_q)
        child.parent_id = None
        child.slot = "interior"
        self.save()
        return child

    def set_desc(self, query: str, description: str) -> Mint:
        m = self.resolve_or_raise(query)
        m.description = description
        self.save()
        return m

    def add_lore(self, query: str, *, title: str, body: str) -> Mint:
        m = self.resolve_or_raise(query)
        m.lore.append(LoreNote(title=title or "", body=body or ""))
        self.save()
        return m

    def _node_payload(self, m: Mint) -> dict[str, Any]:
        kids = self.contents(m.id)
        eff = self.effective_properties(m)
        return {
            "prime": {
                "name": m.name,
                "kind": m.kind,
                "subtype": m.subtype,
                "description": m.description,
                "slug": m.slug,
                "code": m.code,
                "properties": [
                    {
                        "name": name,
                        "source": src,
                        "code": (p.code if p else None),
                        "description": (p.description if p else ""),
                    }
                    for name, src, p in eff
                ],
            },
            "lore": [
                {"title": n.title, "body": n.body, "author": "mentor"}
                for n in m.lore
            ],
            "instance": {
                "name_override": None,
                "description_override": None,
                "short_ref_digits": "0001",
                "lore": [],
                "slot": m.slot,
            },
            "contents": [self._node_payload(c) for c in kids],
        }

    def export_tree(
        self,
        query: str,
        *,
        origin: str = "ven-mentor",
        collector: Path | None = None,
    ) -> Path:
        root_m = self.resolve_or_raise(query)
        root = collector or ven_collector_dir()
        seq = 1
        for p in root.glob("*.ven"):
            try:
                n = int(p.name.split("-", 1)[0])
                seq = max(seq, n + 1)
            except ValueError:
                pass
        code = root_m.code or "OTH-000"
        slug = root_m.slug or "unnamed"
        fname = f"{seq:04d}-{code}-{slug}.ven"
        pack = {
            "format": PACK_FORMAT,
            "version": PACK_VERSION,
            "pack_kind": "tree",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "seq": seq,
            "provenance": {
                "origin_world": origin,
                "home_code": code,
                "export_seq": seq,
                "pack_kind": "tree",
                "tool": "ven-mentor",
            },
            "node": self._node_payload(root_m),
        }
        path = root / fname
        path.write_text(
            json.dumps(pack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return path
