from __future__ import annotations

from PIL import Image, ImageDraw

from patternsy.shapes.base import Shape, register_shape, circle_vertices


@register_shape("circle")
class CircleShape(Shape):

    @staticmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        return circle_vertices(64)

    @staticmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(img).ellipse([0, 0, width - 1, height - 1], fill=color)
        return img
