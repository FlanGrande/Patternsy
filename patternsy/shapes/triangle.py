from __future__ import annotations

from PIL import Image, ImageDraw

from patternsy.shapes.base import Shape, register_shape


@register_shape("triangle")
class TriangleShape(Shape):

    @staticmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        # Equilateral-ish, apex top-center
        return [
            (0.0, -0.5),    # top
            (-0.5, 0.5),    # bottom-left
            (0.5, 0.5),     # bottom-right
        ]

    @staticmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        points = [
            (width // 2, 0),
            (0, height - 1),
            (width - 1, height - 1),
        ]
        ImageDraw.Draw(img).polygon(points, fill=color)
        return img
