"""Undo/redo command stack.

Stores snapshots of shape lists. Lightweight for <100 shapes.
"""

from __future__ import annotations

from patternsy_v2.model import ShapeInstance


class History:
    def __init__(self, max_depth: int = 100):
        self._undo: list[list[ShapeInstance]] = []
        self._redo: list[list[ShapeInstance]] = []
        self._max = max_depth

    def push(self, shapes: list[ShapeInstance]) -> None:
        """Save a snapshot before a mutation."""
        self._undo.append([s.clone() for s in shapes])
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()

    def undo(self, current: list[ShapeInstance]) -> list[ShapeInstance] | None:
        """Return previous snapshot, or None if nothing to undo."""
        if not self._undo:
            return None
        self._redo.append([s.clone() for s in current])
        return self._undo.pop()

    def redo(self, current: list[ShapeInstance]) -> list[ShapeInstance] | None:
        """Return next snapshot, or None if nothing to redo."""
        if not self._redo:
            return None
        self._undo.append([s.clone() for s in current])
        return self._redo.pop()

    @property
    def can_undo(self) -> bool:
        return len(self._undo) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
