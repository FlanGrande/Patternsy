from __future__ import annotations

import math

from patternsy_v2.model import PatternState, ShapeInstance
from patternsy_v2.patterns.base import PatternGenerator, register_pattern


@register_pattern("diagonal_grid")
class DiagonalPattern(PatternGenerator):

    @staticmethod
    def generate(state: PatternState) -> list[ShapeInstance]:
        w, h = state.canvas_size
        p = state.pattern_params
        cols = max(1, int(p.get("columns", 8)))
        rows = max(1, int(p.get("rows", 8)))
        diag_off = int(p.get("diagonal_offset_x", 0))
        sx = w / cols
        sy = h / rows
        n_cols = math.ceil(w / sx) + 1

        shapes: list[ShapeInstance] = []
        for r in range(rows):
            if sx > 0:
                row_offset = (r * diag_off) % sx
            else:
                row_offset = 0
            start = sx / 2 + row_offset - sx
            for i in range(n_cols):
                x = start + i * sx
                if 0 <= x < w:
                    y = sy / 2 + r * sy
                    shapes.append(DiagonalPattern._make_shape(state, x, y))
        return shapes
