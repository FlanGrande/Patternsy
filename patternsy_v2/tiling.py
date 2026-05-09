"""Toroidal tiling helpers.

Used both for viewport ghost rendering and for Pillow export.
"""

from __future__ import annotations

from patternsy_v2.model import ShapeInstance


def ghost_offsets(
    shape: ShapeInstance,
    canvas_w: float,
    canvas_h: float,
) -> list[tuple[float, float]]:
    """Return additional (dx, dy) offsets for toroidal wrapping.

    For a shape near an edge, returns the offsets at which ghost copies
    should be drawn to simulate seamless tiling.  Returns an empty list
    if the shape is fully interior.
    """
    cx, cy = shape.position
    hw, hh = shape.size[0] / 2, shape.size[1] / 2
    offsets: list[tuple[float, float]] = []

    wrap_left = cx - hw < 0
    wrap_right = cx + hw > canvas_w
    wrap_top = cy - hh < 0
    wrap_bottom = cy + hh > canvas_h

    # Horizontal wraps
    if wrap_left:
        offsets.append((canvas_w, 0))
    elif wrap_right:
        offsets.append((-canvas_w, 0))

    # Vertical wraps
    if wrap_top:
        offsets.append((0, canvas_h))
    elif wrap_bottom:
        offsets.append((0, -canvas_h))

    # Corner wraps
    if wrap_left and wrap_top:
        offsets.append((canvas_w, canvas_h))
    elif wrap_left and wrap_bottom:
        offsets.append((canvas_w, -canvas_h))
    elif wrap_right and wrap_top:
        offsets.append((-canvas_w, canvas_h))
    elif wrap_right and wrap_bottom:
        offsets.append((-canvas_w, -canvas_h))

    return offsets
