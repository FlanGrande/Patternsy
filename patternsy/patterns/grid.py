from __future__ import annotations

from patternsy.model import PatternState, ShapeInstance
from patternsy.patterns.base import PatternGenerator, register_pattern


@register_pattern("grid")
class GridPattern(PatternGenerator):

    @staticmethod
    def generate(state: PatternState) -> list[ShapeInstance]:
        w, h = state.canvas_size
        p = state.pattern_params
        cols = max(1, int(p.get("columns", 8)))
        rows = max(1, int(p.get("rows", 8)))
        sx = w / cols
        sy = h / rows

        shapes: list[ShapeInstance] = []
        for r in range(rows):
            for c in range(cols):
                x = sx / 2 + c * sx
                y = sy / 2 + r * sy
                index = r * cols + c
                shapes.append(GridPattern._make_shape(state, x, y, index))
        return shapes
