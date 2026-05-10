from __future__ import annotations

import random

from patternsy.model import PatternState, ShapeInstance
from patternsy.patterns.base import PatternGenerator, register_pattern


@register_pattern("random")
class RandomPattern(PatternGenerator):

    @staticmethod
    def generate(state: PatternState) -> list[ShapeInstance]:
        w, h = state.canvas_size
        p = state.pattern_params
        cols = max(1, int(p.get("columns", 8)))
        rows = max(1, int(p.get("rows", 8)))
        seed = int(p.get("seed", 0))
        sx = w / cols
        sy = h / rows

        rng = random.Random(seed if seed else hash((w, h, sx, sy)))
        num_shapes = int(cols * rows * 1.2)
        min_sx = sx / 3
        min_sy = sy / 3

        placed: list[tuple[float, float]] = []
        shapes: list[ShapeInstance] = []
        idx = 0

        for _ in range(num_shapes):
            for _attempt in range(20):
                x = rng.uniform(0, w)
                y = rng.uniform(0, h)
                too_close = False
                for ex, ey in placed:
                    if abs(ex - x) < min_sx and abs(ey - y) < min_sy:
                        too_close = True
                        break
                if not too_close:
                    placed.append((x, y))
                    shapes.append(RandomPattern._make_shape(state, x, y, idx))
                    idx += 1
                    break

        return shapes
