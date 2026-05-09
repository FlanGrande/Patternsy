"""Pillow-based image export with seamless tiling support."""

from __future__ import annotations

from PIL import Image, ImageFilter

from patternsy_v2.model import PatternState, ShapeInstance
from patternsy_v2.shapes.base import SHAPE_REGISTRY
from patternsy_v2.tiling import ghost_offsets


def export_pattern(
    state: PatternState,
    output_file: str,
    antialiasing: bool = True,
    aa_scale: int = 4,
) -> Image.Image:
    """Render the pattern to a Pillow image and save it.

    Uses the same toroidal wrapping as the viewport, but renders
    at full (optionally supersampled) resolution via Pillow rasterization.
    """
    w, h = state.canvas_size

    if antialiasing:
        rw, rh = w * aa_scale, h * aa_scale
    else:
        rw, rh = w, h

    scale = aa_scale if antialiasing else 1
    canvas = Image.new("RGBA", (rw, rh), state.bg_color)

    for shape in state.shapes:
        _paste_shape(canvas, shape, rw, rh, scale)

    if antialiasing:
        canvas = canvas.resize((w, h), Image.Resampling.LANCZOS)
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=0.3))

    canvas = canvas.convert("RGB")
    canvas.save(output_file)
    return canvas


def _paste_shape(
    canvas: Image.Image,
    shape: ShapeInstance,
    cw: int,
    ch: int,
    scale: int,
) -> None:
    """Paste a single shape (+ toroidal ghosts) onto the canvas."""
    shape_cls = SHAPE_REGISTRY.get(shape.shape_type)
    if shape_cls is None:
        return

    sw = max(1, int(shape.size[0] * scale))
    sh = max(1, int(shape.size[1] * scale))

    # Rasterize
    if shape.shape_type == "custom" and shape.custom_image_path:
        from patternsy_v2.shapes.custom import CustomShape
        img = CustomShape.rasterize(sw, sh, shape.color, shape.custom_image_path)
    else:
        img = shape_cls.rasterize(sw, sh, shape.color)

    # Rotate — expand=True so corners aren't clipped; BICUBIC for smooth edges.
    # Negate angle: Pillow rotates CCW, but screen-space Y is flipped so the
    # viewport effectively rotates CW for positive angles. Negate to match.
    if shape.rotation != 0:
        img = img.rotate(-shape.rotation, resample=Image.BICUBIC, expand=True)

    # Paste at main position + ghosts
    cx = int(shape.position[0] * scale)
    cy = int(shape.position[1] * scale)
    _do_paste(canvas, img, cx, cy, cw, ch)

    for dx, dy in ghost_offsets(shape, cw / scale, ch / scale):
        _do_paste(canvas, img, cx + int(dx * scale), cy + int(dy * scale), cw, ch)


def _do_paste(
    canvas: Image.Image,
    shape_img: Image.Image,
    cx: int,
    cy: int,
    cw: int,
    ch: int,
) -> None:
    """Paste shape_img centered at (cx, cy), cropped to canvas bounds."""
    px = cx - shape_img.width // 2
    py = cy - shape_img.height // 2

    left = max(0, px)
    top = max(0, py)
    right = min(cw, px + shape_img.width)
    bottom = min(ch, py + shape_img.height)

    if right <= left or bottom <= top:
        return

    crop_l = left - px
    crop_t = top - py
    crop_r = crop_l + (right - left)
    crop_b = crop_t + (bottom - top)

    visible = shape_img.crop((crop_l, crop_t, crop_r, crop_b))
    canvas.paste(visible, (left, top), visible)
