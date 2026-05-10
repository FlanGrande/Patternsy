"""Undo/redo command stack.

Each snapshot stores shapes, selection, and all PatternState configuration
fields so that every action — including pattern type changes, color changes,
canvas size changes, etc. — is fully reversible.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from patternsy.model import ShapeInstance

if TYPE_CHECKING:
    from patternsy.model import PatternState


@dataclass
class Snapshot:
    # Shape data
    shapes: list[ShapeInstance]
    selected_ids: frozenset[str]
    # PatternState configuration (everything that drives generation + display)
    canvas_size: tuple[int, int] = (1024, 1024)
    bg_color: tuple[int, int, int, int] = (0, 0, 0, 255)
    pattern_type: str = "grid"
    pattern_params: dict = field(default_factory=dict)
    default_shape_type: str = "circle"
    default_shape_size: tuple[float, float] = (32.0, 32.0)
    default_shape_color: tuple[int, int, int, int] = (255, 136, 0, 255)
    default_shape_rotation: float = 0.0
    default_custom_image_path: str = ""
    show_tiling_ghosts: bool = True


def _snap(shapes: list[ShapeInstance], selected_ids: set[str] | frozenset[str], state: "PatternState") -> Snapshot:
    """Build a Snapshot from current app state."""
    return Snapshot(
        shapes=[s.clone() for s in shapes],
        selected_ids=frozenset(selected_ids),
        canvas_size=state.canvas_size,
        bg_color=state.bg_color,
        pattern_type=state.pattern_type,
        pattern_params=copy.deepcopy(state.pattern_params),
        default_shape_type=state.default_shape_type,
        default_shape_size=state.default_shape_size,
        default_shape_color=state.default_shape_color,
        default_shape_rotation=state.default_shape_rotation,
        default_custom_image_path=state.default_custom_image_path,
        show_tiling_ghosts=state.show_tiling_ghosts,
    )


class History:
    def __init__(self, max_depth: int = 100):
        self._undo: list[Snapshot] = []
        self._redo: list[Snapshot] = []
        self._max = max_depth

    def push(
        self,
        shapes: list[ShapeInstance],
        selected_ids: set[str] | frozenset[str],
        state: "PatternState",
    ) -> None:
        """Save a full snapshot before a mutation."""
        self._undo.append(_snap(shapes, selected_ids, state))
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()

    def push_snapshot(self, snap: Snapshot) -> None:
        """Commit a pre-built snapshot directly (used by drag / widget deactivation)."""
        self._undo.append(snap)
        if len(self._undo) > self._max:
            self._undo.pop(0)
        self._redo.clear()

    def undo(
        self,
        shapes: list[ShapeInstance],
        selected_ids: set[str] | frozenset[str],
        state: "PatternState",
    ) -> Snapshot | None:
        if not self._undo:
            return None
        self._redo.append(_snap(shapes, selected_ids, state))
        return self._undo.pop()

    def redo(
        self,
        shapes: list[ShapeInstance],
        selected_ids: set[str] | frozenset[str],
        state: "PatternState",
    ) -> Snapshot | None:
        if not self._redo:
            return None
        self._undo.append(_snap(shapes, selected_ids, state))
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
