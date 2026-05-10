"""Pattern generator plugin system."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patternsy.model import PatternState, ShapeInstance

PATTERN_REGISTRY: dict[str, type["PatternGenerator"]] = {}


def register_pattern(name: str):
    def decorator(cls: type[PatternGenerator]) -> type[PatternGenerator]:
        PATTERN_REGISTRY[name] = cls
        return cls
    return decorator


class PatternGenerator(ABC):

    @staticmethod
    @abstractmethod
    def generate(state: "PatternState") -> list["ShapeInstance"]:
        ...

    @staticmethod
    def _make_shape(
        state: "PatternState",
        x: float,
        y: float,
        index: int,
    ) -> "ShapeInstance":
        """Create a ShapeInstance at (x, y) with stable index and state defaults as base values.

        Jitter (from pattern_params["jitter"]) is applied as a deterministic
        delta_position so it survives regen with the same params/seed.
        """
        from patternsy.model import ShapeInstance

        jitter = max(0, int(state.pattern_params.get("jitter", 0)))
        seed   = int(state.pattern_params.get("seed", 0))

        # Jitter is baked into base_position (not delta_position) so that
        # _generate_silent's delta-merge doesn't overwrite it, and user drag
        # overrides remain independent.
        if jitter > 0:
            # Per-shape deterministic RNG: seed XOR'd with index so each point
            # gets a unique reproducible offset, changing seed shifts all.
            rng = random.Random(seed ^ (index * 0x9E3779B9))
            x += rng.uniform(-jitter, jitter)
            y += rng.uniform(-jitter, jitter)

        return ShapeInstance(
            index=index,
            base_position=(x, y),
            base_size=state.default_shape_size,
            base_rotation=state.default_shape_rotation,
            base_color=state.default_shape_color,
            shape_type=state.default_shape_type,
            custom_image_path=state.default_custom_image_path or None,
        )
