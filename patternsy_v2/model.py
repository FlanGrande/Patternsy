"""Core data model for Patternsy v2."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ShapeInstance:
    """A single shape placed on the canvas. Individually editable."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    position: tuple[float, float] = (0.0, 0.0)   # Center, in canvas pixels
    size: tuple[float, float] = (32.0, 32.0)      # Width, height
    rotation: float = 0.0                          # Degrees
    shape_type: str = "circle"                     # Registry key
    color: tuple[int, int, int, int] = (255, 136, 0, 255)  # RGBA 0-255
    custom_image_path: Optional[str] = None
    locked: bool = False

    def contains(self, px: float, py: float) -> bool:
        """Axis-aligned bounding box hit test (in canvas space)."""
        cx, cy = self.position
        hw, hh = self.size[0] / 2, self.size[1] / 2
        return (cx - hw) <= px <= (cx + hw) and (cy - hh) <= py <= (cy + hh)

    def clone(self) -> "ShapeInstance":
        return ShapeInstance(
            id=self.id,
            position=self.position,
            size=self.size,
            rotation=self.rotation,
            shape_type=self.shape_type,
            color=self.color,
            custom_image_path=self.custom_image_path,
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
