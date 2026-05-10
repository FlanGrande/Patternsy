"""Application state manager."""

from __future__ import annotations

import copy

from patternsy.model import PatternState, ShapeInstance
from patternsy.history import History, Snapshot, _snap
from patternsy.patterns.base import PATTERN_REGISTRY


class App:
    def __init__(self):
        self.state = PatternState()
        self.history = History()
        self.selected_ids: set[str] = set()
        self._dragging: bool = False
        self._drag_start: tuple[float, float] = (0, 0)
        self._drag_origins: dict[str, tuple[float, float]] = {}
        self._pending_drag_snapshot: Snapshot | None = None
        self._last_pattern_key: object = None

    # ── Internal snapshot helpers ────────────────────────────────────────

    def _push(self) -> None:
        """Push the current full state to history before a mutation."""
        self.history.push(self.state.shapes, self.selected_ids, self.state)

    def _push_selection(self) -> None:
        """Push current state to record a selection-only change."""
        self.history.push(self.state.shapes, self.selected_ids, self.state)

    def _restore_snapshot(self, snap: Snapshot) -> None:
        """Apply a snapshot back to app state."""
        self.state.shapes = snap.shapes
        self.selected_ids = set(snap.selected_ids)
        self.state.canvas_size = snap.canvas_size
        self.state.bg_color = snap.bg_color
        self.state.pattern_type = snap.pattern_type
        self.state.pattern_params = copy.deepcopy(snap.pattern_params)
        self.state.default_shape_type = snap.default_shape_type
        self.state.default_shape_size = snap.default_shape_size
        self.state.default_shape_color = snap.default_shape_color
        self.state.default_shape_rotation = snap.default_shape_rotation
        self.state.default_custom_image_path = snap.default_custom_image_path
        self.state.show_tiling_ghosts = snap.show_tiling_ghosts
        # Prevent tick() from immediately re-generating on top of the restored state
        self._last_pattern_key = self._pattern_key()

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
        """Regenerate, preserving per-point deltas via index matching."""
        gen_cls = PATTERN_REGISTRY.get(self.state.pattern_type)
        if gen_cls is None:
            return

        old_by_index: dict[int, ShapeInstance] = {
            s.index: s for s in self.state.shapes
        }

        new_shapes = gen_cls.generate(self.state)

        for ns in new_shapes:
            old = old_by_index.get(ns.index)
            if old is not None:
                ns.delta_position = old.delta_position
                ns.delta_size = old.delta_size
                ns.delta_rotation = old.delta_rotation
                ns.override_color = old.override_color
                ns.locked = old.locked

        self.state.shapes = new_shapes

        new_ids = {s.id for s in new_shapes}
        self.selected_ids &= new_ids

    def generate(self) -> None:
        """Explicit regeneration with history push."""
        self._push()
        self._generate_silent()
        self._last_pattern_key = self._pattern_key()

    # ── Reset helpers ────────────────────────────────────────────────────

    def reset_all_deltas(self) -> None:
        self._push()
        for s in self.state.shapes:
            s.reset_deltas()

    def reset_selected_deltas(self) -> None:
        if not self.selected_ids:
            return
        self._push()
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

        new_sel: set[str]
        if hit is None:
            new_sel = set(self.selected_ids) if extend else set()
        elif extend:
            new_sel = self.selected_ids | {hit.id}
        else:
            new_sel = self.selected_ids if hit.id in self.selected_ids else {hit.id}

        if frozenset(new_sel) != frozenset(self.selected_ids):
            self._push_selection()
            self.selected_ids = new_sel

        return hit

    def selected_shapes(self) -> list[ShapeInstance]:
        return [s for s in self.state.shapes if s.id in self.selected_ids]

    def select_all(self) -> None:
        new_sel = {s.id for s in self.state.shapes}
        if frozenset(new_sel) != frozenset(self.selected_ids):
            self._push_selection()
            self.selected_ids = new_sel

    def deselect_all(self) -> None:
        if self.selected_ids:
            self._push_selection()
            self.selected_ids.clear()

    # ── Dragging ─────────────────────────────────────────────────────────

    def begin_drag(self, cx: float, cy: float) -> None:
        self._dragging = True
        self._drag_start = (cx, cy)
        self._drag_origins = {
            s.id: s.position
            for s in self.state.shapes
            if s.id in self.selected_ids and not s.locked
        }
        self._pending_drag_snapshot = _snap(self.state.shapes, self.selected_ids, self.state)

    def update_drag(self, cx: float, cy: float) -> None:
        if not self._dragging:
            return
        dx = cx - self._drag_start[0]
        dy = cy - self._drag_start[1]
        for shape in self.state.shapes:
            if shape.id in self._drag_origins:
                ox, oy = self._drag_origins[shape.id]
                shape.set_effective_position(ox + dx, oy + dy)

    def end_drag(self) -> None:
        self._dragging = False
        if self._pending_drag_snapshot is not None:
            moved = any(
                s.position != self._drag_origins[s.id]
                for s in self.state.shapes
                if s.id in self._drag_origins
            )
            if moved:
                self.history.push_snapshot(self._pending_drag_snapshot)
        self._pending_drag_snapshot = None
        self._drag_origins.clear()

    @property
    def is_dragging(self) -> bool:
        return self._dragging

    # ── Undo / Redo ──────────────────────────────────────────────────────

    def undo(self) -> None:
        snap = self.history.undo(self.state.shapes, self.selected_ids, self.state)
        if snap is not None:
            self._restore_snapshot(snap)

    def redo(self) -> None:
        snap = self.history.redo(self.state.shapes, self.selected_ids, self.state)
        if snap is not None:
            self._restore_snapshot(snap)

    # ── Shape mutations ──────────────────────────────────────────────────

    def delete_selected(self) -> None:
        if not self.selected_ids:
            return
        self._push()
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
