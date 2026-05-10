from __future__ import annotations

from PIL import Image, ImageDraw

from patternsy.shapes.base import Shape, register_shape


@register_shape("square")
class SquareShape(Shape):

    @staticmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        # Two triangles forming a quad (for GL_TRIANGLES)
        return [
            (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5),
            (-0.5, -0.5), (0.5, 0.5), (-0.5, 0.5),
        ]

    @staticmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
    ) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ImageDraw.Draw(img).rectangle([0, 0, width - 1, height - 1], fill=color)
        return img
