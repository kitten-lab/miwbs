"""Minimal undo stack stub (zero point does not surface undo yet)."""

from __future__ import annotations

from typing import Any, Callable


class UndoStack:
    def __init__(self) -> None:
        self._items: list[tuple[str, Callable[..., Any]]] = []

    def push(self, label: str, fn: Callable[..., Any]) -> None:
        self._items.append((label, fn))

    def pop(self) -> tuple[str, Callable[..., Any]] | None:
        if not self._items:
            return None
        return self._items.pop()

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)
