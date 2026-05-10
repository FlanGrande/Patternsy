"""Undo/redo command stack.

Each snapshot stores both the shape list AND the selection state so that
undo/redo restores the exact selection that existed before each action.
"""

from __future__ import annotations

from dataclasses import dataclass

from patternsy.model import ShapeInstance


@dataclass
class Snapshot:
    shapes: list[ShapeInstance]
    selected_ids: frozenset[str]


class History:
    def __init__(self, max_depth: int = 100):
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []
        self._max = max_depth

    def push(
        self,
        shapes: list[ShapeInstance],
        selected_ids: set[str] | frozenset[str],
    ) -> None:
        """Save a snapshot before a mutation."""
        self._undo.append(Snapshot(
            shapes=[s.clone() for s in shapes],
            selected_ids=frozenset(selected_ids),
        ))
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()

    def undo(
        self,
        current_shapes: list[ShapeInstance],
        current_selected: set[str] | frozenset[str],
    ) -> Snapshot | None:
        """Return previous snapshot, or None if nothing to undo."""
        if not self._undo:
            return None
        self._redo.append(Snapshot(
            shapes=[s.clone() for s in current_shapes],
            selected_ids=frozenset(current_selected),
        ))
        return self._undo.pop()

    def redo(
        self,
        current_shapes: list[ShapeInstance],
        current_selected: set[str] | frozenset[str],
    ) -> Snapshot | None:
        """Return next snapshot, or None if nothing to redo."""
        if not self._redo:
            return None
        self._undo.append(Snapshot(
            shapes=[s.clone() for s in current_shapes],
            selected_ids=frozenset(current_selected),
        ))
        return self._redo.pop()

    @property
    def can_undo(self) -> bool:
        return len(self._undo) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def push_snapshot(self, snap: "Snapshot") -> None:
        """Commit a pre-built snapshot directly (used by drag / widget deactivation)."""
        self._undo.append(snap)
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
