from __future__ import annotations

import os

from PIL import Image

from patternsy_v2.shapes.base import Shape, register_shape

# Cache: (path, w, h) → Image
_cache: dict[tuple[str, int, int], Image.Image] = {}


@register_shape("custom")
class CustomShape(Shape):

    @staticmethod
    def vertices(width: float, height: float) -> list[tuple[float, float]]:
        # Textured quad — two triangles
        return [
            (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5),
            (-0.5, -0.5), (0.5, 0.5), (-0.5, 0.5),
        ]

    @staticmethod
    def rasterize(
        width: int,
        height: int,
        color: tuple[int, int, int, int],
        custom_image_path: str | None = None,
    ) -> Image.Image:
        if custom_image_path and os.path.exists(custom_image_path):
            key = (custom_image_path, width, height)
            if key not in _cache:
                img = Image.open(custom_image_path).convert("RGBA")
                img = img.resize((width, height), Image.LANCZOS)
                _cache[key] = img.copy()
            return _cache[key].copy()
        # Fallback: magenta square (indicates missing image)
        img = Image.new("RGBA", (width, height), (255, 0, 255, 255))
        return img

    @staticmethod
    def load_gl_texture(path: str, width: int, height: int) -> Image.Image | None:
        """Load image for OpenGL texture. Returns RGBA PIL image or None."""
        if not path or not os.path.exists(path):
            return None
        key = (path, width, height)
        if key not in _cache:
            img = Image.open(path).convert("RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            _cache[key] = img.copy()
        return _cache[key].copy()
