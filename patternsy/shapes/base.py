"""Shape plugin system.

Each shape type registers itself via the @register_shape decorator.
Shapes know how to produce vertices for OpenGL rendering and
how to rasterize themselves to a Pillow image for export.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImage

# Global registry: name → Shape class
SHAPE_REGISTRY: dict[str, type["Shape"]] = {}


def register_shape(name: str):
    """Decorator to register a shape class under *name*."""
    def decorator(cls: type[Shape]) -> type[Shape]:
        SHAPE_REGISTRY[name] = cls
        return cls
    return decorator


class Shape(ABC):
    """Abstract base for a drawable shape type."""

    @staticmethod
    @abstractmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        """Return normalized vertices (centered at origin, unit scale).

        For filled polygons these are ordered for GL_TRIANGLE_FAN or similar.
        For circles, return a polygon approximation.
        Coordinates range roughly -0.5..+0.5 so that multiplying by
        (width, height) gives the final shape.
        """
        ...

    @staticmethod
    @abstractmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
    ) -> "PILImage.Image":
        """Rasterize the shape to an RGBA Pillow image for export."""
        ...


# ── Helpers ──────────────────────────────────────────────────────────────────

def circle_vertices(n: int = 64) -> list[tuple[float, float]]:
    """Generate *n* vertices for a unit circle (radius 0.5)."""
    verts = [(0.0, 0.0)]  # center for TRIANGLE_FAN
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        verts.append((0.5 * math.cos(angle), 0.5 * math.sin(angle)))
    return verts
