"""Application state manager.

Central coordinator: owns PatternState, History, selection, and
dispatches actions (generate, drag, undo, etc.).
"""

from __future__ import annotations

from patternsy_v2.model import PatternState, ShapeInstance
from patternsy_v2.history import History
from patternsy_v2.patterns.base import PATTERN_REGISTRY


class App:
    def __init__(self):
        self.state = PatternState()
        self.history = History()
        self.selected_ids: set[str] = set()
        self._dragging: bool = False
        self._drag_start: tuple[float, float] = (0, 0)
        self._drag_origins: dict[str, tuple[float, float]] = {}
        self._last_pattern_key: object = None  # tracks last generated config

    # ── Pattern generation ──────────────────────────────────────────────

    def _pattern_key(self) -> tuple:
        """A hashable snapshot of all params that drive generation."""
        s = self.state
        return (
            s.canvas_size,
            s.pattern_type,
            tuple(sorted(s.pattern_params.items())),
            s.default_shape_type,
            s.default_shape_size,
            s.default_shape_color,
            s.default_shape_rotation,
            s.default_custom_image_path,
        )

    def tick(self) -> None:
        """Call once per frame. Auto-regenerates if any pattern param changed."""
        if self._dragging:
            return
        key = self._pattern_key()
        if key != self._last_pattern_key:
            self._last_pattern_key = key
            self._generate_silent()

    def _generate_silent(self) -> None:
        """Regenerate without pushing to history (live update)."""
        gen_cls = PATTERN_REGISTRY.get(self.state.pattern_type)
        if gen_cls is None:
            return
        # Preserve manually-moved shapes by ID if they still have a match
        prev_overrides: dict[str, tuple[float, float]] = {
            s.id: s.position for s in self.state.shapes
        }
        new_shapes = gen_cls.generate(self.state)
        # Re-apply position overrides for shapes that kept the same id
        # (on regen ids are new, so this only helps on canvas_size changes)
        self.state.shapes = new_shapes
        # Keep selection valid
        new_ids = {s.id for s in new_shapes}
        self.selected_ids &= new_ids

    def generate(self) -> None:
        """Explicit regeneration — pushes to history."""
        self.history.push(self.state.shapes)
        self._generate_silent()
        self._last_pattern_key = self._pattern_key()

    # ── Selection ───────────────────────────────────────────────────────

    def pick(self, cx: float, cy: float, extend: bool = False) -> ShapeInstance | None:
        """Hit-test at canvas coords. Returns picked shape or None.

        Searches back-to-front so topmost shape wins.
        """
        hit: ShapeInstance | None = None
        for shape in reversed(self.state.shapes):
            if shape.contains(cx, cy):
                hit = shape
                break

        if hit is None:
            if not extend:
                self.selected_ids.clear()
            return None

        if extend:
            self.selected_ids ^= {hit.id}  # toggle
        else:
            self.selected_ids = {hit.id}
        return hit

    def selected_shapes(self) -> list[ShapeInstance]:
        return [s for s in self.state.shapes if s.id in self.selected_ids]

    def select_all(self) -> None:
        self.selected_ids = {s.id for s in self.state.shapes}

    def deselect_all(self) -> None:
        self.selected_ids.clear()

    # ── Dragging ────────────────────────────────────────────────────────

    def begin_drag(self, cx: float, cy: float) -> None:
        self._dragging = True
        self._drag_start = (cx, cy)
        self._drag_origins = {
            s.id: s.position for s in self.state.shapes if s.id in self.selected_ids and not s.locked
        }
        # Snapshot for undo
        self.history.push(self.state.shapes)

    def update_drag(self, cx: float, cy: float) -> None:
        if not self._dragging:
            return
        dx = cx - self._drag_start[0]
        dy = cy - self._drag_start[1]
        for shape in self.state.shapes:
            if shape.id in self._drag_origins:
                ox, oy = self._drag_origins[shape.id]
                shape.position = (ox + dx, oy + dy)

    def end_drag(self) -> None:
        self._dragging = False
        self._drag_origins.clear()

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ── Undo / Redo ─────────────────────────────────────────────────────

    def undo(self) -> None:
        result = self.history.undo(self.state.shapes)
        if result is not None:
            self.state.shapes = result
            self.selected_ids.clear()

    def redo(self) -> None:
        result = self.history.redo(self.state.shapes)
        if result is not None:
            self.state.shapes = result
            self.selected_ids.clear()

    # ── Shape mutations (with undo snapshot) ────────────────────────────

    def delete_selected(self) -> None:
        if not self.selected_ids:
            return
        self.history.push(self.state.shapes)
        self.state.shapes = [s for s in self.state.shapes if s.id not in self.selected_ids]
        self.selected_ids.clear()

    def set_selected_rotation(self, degrees: float) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.rotation = degrees

    def set_selected_color(self, color: tuple[int, int, int, int]) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.color = color

    def set_selected_size(self, size: tuple[float, float]) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.size = size
