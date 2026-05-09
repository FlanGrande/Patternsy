from __future__ import annotations

import math

from PIL import Image, ImageDraw

from patternsy_v2.shapes.base import Shape, register_shape


def _star_points(n_points: int = 5) -> list[tuple[float, float]]:
    """Generate normalized 5-pointed star vertices."""
    verts: list[tuple[float, float]] = []
    total = n_points * 2
    for i in range(total):
        r = 0.5 if i % 2 == 0 else 0.25
        angle = math.pi / n_points * i - math.pi / 2
        verts.append((r * math.cos(angle), r * math.sin(angle)))
    return verts


@register_shape("star")
class StarShape(Shape):

    @staticmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        pts = _star_points(5)
        # For GL_TRIANGLE_FAN from center
        return [(0.0, 0.0)] + pts + [pts[0]]

    @staticmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cx, cy = width / 2, height / 2
        outer_r = min(width, height) / 2
        inner_r = outer_r / 2
        points = []
        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            angle = math.pi / 5 * i - math.pi / 2
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        ImageDraw.Draw(img).polygon(points, fill=color)
        return img
