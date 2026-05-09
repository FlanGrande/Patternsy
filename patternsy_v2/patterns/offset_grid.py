from __future__ import annotations

import math

from patternsy_v2.model import PatternState, ShapeInstance
from patternsy_v2.patterns.base import PatternGenerator, register_pattern


@register_pattern("offset_grid")
class OffsetGridPattern(PatternGenerator):

    @staticmethod
    def generate(state: PatternState) -> list[ShapeInstance]:
        w, h = state.canvas_size
        p = state.pattern_params
        cols = max(1, int(p.get("columns", 8)))
        rows = max(1, int(p.get("rows", 8)))
        sx = w / cols
        sy = h / rows
        n_cols = math.ceil(w / sx) + 1

        shapes: list[ShapeInstance] = []
        idx = 0
        for r in range(rows):
            if r % 2 == 1:
                offset = sx / 2
                start = sx / 2 + offset - sx
                for i in range(n_cols):
                    x = start + i * sx
                    if 0 <= x < w:
                        y = sy / 2 + r * sy
                        shapes.append(OffsetGridPattern._make_shape(state, x, y, idx))
                        idx += 1
            else:
                for c in range(cols):
                    x = sx / 2 + c * sx
                    y = sy / 2 + r * sy
                    shapes.append(OffsetGridPattern._make_shape(state, x, y, idx))
                    idx += 1
        return shapes
