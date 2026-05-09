"""Application state manager."""

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
        self._drag_origins: dict[str, tuple[float, float]] = {}  # id → base effective pos at drag start
        self._last_pattern_key: object = None

    # ── Pattern generation ──────────────────────────────────────────────

    def _pattern_key(self) -> tuple:
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
        """Regenerate, preserving per-point deltas across the regen via index matching."""
        gen_cls = PATTERN_REGISTRY.get(self.state.pattern_type)
        if gen_cls is None:
            return

        # Build lookup: index → old shape (to carry deltas forward)
        old_by_index: dict[int, ShapeInstance] = {
            s.index: s for s in self.state.shapes
        }

        new_shapes = gen_cls.generate(self.state)

        # Merge: copy deltas + locked + override_color from matching old shape
        for ns in new_shapes:
            old = old_by_index.get(ns.index)
            if old is not None:
                ns.delta_position = old.delta_position
                ns.delta_size = old.delta_size
                ns.delta_rotation = old.delta_rotation
                ns.override_color = old.override_color
                ns.locked = old.locked

        self.state.shapes = new_shapes

        # Keep selection valid (ids changed on regen; clear stale selections)
        new_ids = {s.id for s in new_shapes}
        self.selected_ids &= new_ids

    def generate(self) -> None:
        """Explicit regeneration with history push."""
        self.history.push(self.state.shapes)
        self._generate_silent()
        self._last_pattern_key = self._pattern_key()

    # ── Reset helpers ────────────────────────────────────────────────────

    def reset_all_deltas(self) -> None:
        """Reset every point to pattern defaults (clear all deltas)."""
        self.history.push(self.state.shapes)
        for s in self.state.shapes:
            s.reset_deltas()

    def reset_selected_deltas(self) -> None:
        """Reset only selected points to pattern defaults."""
        if not self.selected_ids:
            return
        self.history.push(self.state.shapes)
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.reset_deltas()

    # ── Selection ────────────────────────────────────────────────────────

    def pick(self, cx: float, cy: float, extend: bool = False) -> ShapeInstance | None:
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
            self.selected_ids ^= {hit.id}
        else:
            self.selected_ids = {hit.id}
        return hit

    def selected_shapes(self) -> list[ShapeInstance]:
        return [s for s in self.state.shapes if s.id in self.selected_ids]

    def select_all(self) -> None:
        self.selected_ids = {s.id for s in self.state.shapes}

    def deselect_all(self) -> None:
        self.selected_ids.clear()

    # ── Dragging — writes to delta_position, not base ───────────────────

    def begin_drag(self, cx: float, cy: float) -> None:
        self._dragging = True
        self._drag_start = (cx, cy)
        # Store the effective position at drag start for each draggable selected shape
        self._drag_origins = {
            s.id: s.position
            for s in self.state.shapes
            if s.id in self.selected_ids and not s.locked
        }
        self.history.push(self.state.shapes)

    def update_drag(self, cx: float, cy: float) -> None:
        if not self._dragging:
            return
        dx = cx - self._drag_start[0]
        dy = cy - self._drag_start[1]
        for shape in self.state.shapes:
            if shape.id in self._drag_origins:
                ox, oy = self._drag_origins[shape.id]
                # Write delta so base_position stays untouched
                shape.set_effective_position(ox + dx, oy + dy)

    def end_drag(self) -> None:
        self._dragging = False
        self._drag_origins.clear()

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ── Undo / Redo ──────────────────────────────────────────────────────

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

    # ── Shape mutations ──────────────────────────────────────────────────

    def delete_selected(self) -> None:
        if not self.selected_ids:
            return
        self.history.push(self.state.shapes)
        self.state.shapes = [s for s in self.state.shapes if s.id not in self.selected_ids]
        self.selected_ids.clear()

    def set_selected_rotation(self, effective_deg: float) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.set_effective_rotation(effective_deg)

    def set_selected_color(self, color: tuple[int, int, int, int]) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.set_effective_color(color)

    def set_selected_size(self, effective_size: tuple[float, float]) -> None:
        for s in self.state.shapes:
            if s.id in self.selected_ids:
                s.set_effective_size(effective_size[0], effective_size[1])
