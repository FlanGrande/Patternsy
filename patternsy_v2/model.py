"""Core data model for Patternsy v2."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ShapeInstance:
    """A single shape placed on the canvas. Individually editable.

    Position, size, rotation and color are split into a generator-assigned
    *base* value and a user-applied *delta*.  The canvas and export code
    always read the effective_* properties, which combine both.

    ``index`` is assigned by the pattern generator and stays stable across
    regenerations (same grid cell = same index), allowing deltas to survive
    pattern-settings changes.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    # ── Generator-assigned base values ──────────────────────────────────
    index: int = 0
    base_position: tuple[float, float] = (0.0, 0.0)   # set by generator
    base_size: tuple[float, float] = (32.0, 32.0)      # = default_shape_size at gen time
    base_rotation: float = 0.0                          # = default_shape_rotation at gen time
    base_color: tuple[int, int, int, int] = (255, 136, 0, 255)
    shape_type: str = "circle"
    custom_image_path: Optional[str] = None

    # ── User-applied deltas ─────────────────────────────────────────────
    delta_position: tuple[float, float] = (0.0, 0.0)
    delta_size: tuple[float, float] = (0.0, 0.0)
    delta_rotation: float = 0.0
    override_color: Optional[tuple[int, int, int, int]] = None  # None = use base_color

    # ── Flags ───────────────────────────────────────────────────────────
    locked: bool = False   # prevents drag; deltas always preserved regardless

    # ── Effective (read-only computed) properties ───────────────────────

    @property
    def position(self) -> tuple[float, float]:
        return (self.base_position[0] + self.delta_position[0],
                self.base_position[1] + self.delta_position[1])

    @property
    def size(self) -> tuple[float, float]:
        return (max(1.0, self.base_size[0] + self.delta_size[0]),
                max(1.0, self.base_size[1] + self.delta_size[1]))

    @property
    def rotation(self) -> float:
        return self.base_rotation + self.delta_rotation

    @property
    def color(self) -> tuple[int, int, int, int]:
        return self.override_color if self.override_color is not None else self.base_color

    # ── Delta helpers ───────────────────────────────────────────────────

    def set_effective_position(self, px: float, py: float) -> None:
        self.delta_position = (px - self.base_position[0], py - self.base_position[1])

    def set_effective_size(self, sw: float, sh: float) -> None:
        self.delta_size = (sw - self.base_size[0], sh - self.base_size[1])

    def set_effective_rotation(self, deg: float) -> None:
        self.delta_rotation = deg - self.base_rotation

    def set_effective_color(self, color: tuple[int, int, int, int]) -> None:
        self.override_color = color

    def has_any_delta(self) -> bool:
        return (self.delta_position != (0.0, 0.0) or
                self.delta_size != (0.0, 0.0) or
                self.delta_rotation != 0.0 or
                self.override_color is not None)

    def reset_deltas(self) -> None:
        """Clear all manual overrides — point snaps back to pattern defaults."""
        self.delta_position = (0.0, 0.0)
        self.delta_size = (0.0, 0.0)
        self.delta_rotation = 0.0
        self.override_color = None

    # ── Hit test ────────────────────────────────────────────────────────

    def contains(self, px: float, py: float) -> bool:
        """Axis-aligned bounding box hit test using effective position/size."""
        cx, cy = self.position
        hw, hh = self.size[0] / 2, self.size[1] / 2
        return (cx - hw) <= px <= (cx + hw) and (cy - hh) <= py <= (cy + hh)

    # ── Clone ────────────────────────────────────────────────────────────

    def clone(self) -> "ShapeInstance":
        return ShapeInstance(
            id=self.id,
            index=self.index,
            base_position=self.base_position,
            base_size=self.base_size,
            base_rotation=self.base_rotation,
            base_color=self.base_color,
            shape_type=self.shape_type,
            custom_image_path=self.custom_image_path,
            delta_position=self.delta_position,
            delta_size=self.delta_size,
            delta_rotation=self.delta_rotation,
            override_color=self.override_color,
            locked=self.locked,
        )


@dataclass
class PatternState:
    """Full application state — the single source of truth."""

    canvas_size: tuple[int, int] = (1024, 1024)
    bg_color: tuple[int, int, int, int] = (0, 0, 0, 255)

    # Pattern generator settings
    pattern_type: str = "grid"
    pattern_params: dict = field(default_factory=lambda: {
        "columns": 8,
        "rows": 8,
        "diagonal_offset_x": 0,
        "seed": 0,
        "jitter": 0,
    })

    # Default shape settings (used by pattern generator)
    default_shape_type: str = "circle"
    default_shape_size: tuple[float, float] = (32.0, 32.0)
    default_shape_color: tuple[int, int, int, int] = (255, 136, 0, 255)
    default_shape_rotation: float = 0.0
    default_custom_image_path: str = ""

    # All shapes on the canvas
    shapes: list[ShapeInstance] = field(default_factory=list)

    # Viewport (not serialized)
    viewport_offset: tuple[float, float] = (0.0, 0.0)
    viewport_zoom: float = 1.0

    # Tiling preview toggle
    show_tiling_ghosts: bool = True

    version: str = "2.0.0"

    def snapshot_shapes(self) -> list[ShapeInstance]:
        """Deep copy shapes for undo."""
        return [s.clone() for s in self.shapes]
