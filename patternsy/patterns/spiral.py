from __future__ import annotations

import math

from patternsy.model import PatternState, ShapeInstance
from patternsy.patterns.base import PatternGenerator, register_pattern


@register_pattern("spiral")
class SpiralPattern(PatternGenerator):

    @staticmethod
    def generate(state: PatternState) -> list[ShapeInstance]:
        w, h = state.canvas_size
        p = state.pattern_params
        cols = max(1, int(p.get("columns", 8)))
        rows = max(1, int(p.get("rows", 8)))
        sx = w / cols
        sy = h / rows

        cx, cy = w / 2, h / 2
        max_r = min(w, h) / 2
        a = sx / (2 * math.pi)
        b = sy / 20

        shapes: list[ShapeInstance] = []
        idx = 0
        t = 0.0
        while True:
            r = a * t
            if r > max_r:
                break
            x = cx + r * math.cos(t)
            y = cy + r * math.sin(t)
            if 0 <= x < w and 0 <= y < h:
                shapes.append(SpiralPattern._make_shape(state, x, y, idx))
                idx += 1
            t += (b / r) if r > 0 else b

        return shapes
