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

        p     = state.pattern_params
        jitter = max(0, int(p.get("jitter", 0)))
        seed   = int(p.get("seed", 0))

        # ── Position jitter ───────────────────────────────────────────────
        # Baked into base_position so delta-merge in _generate_silent doesn't
        # clobber it, and user drag overrides remain independent.
        if jitter > 0:
            rng = random.Random(seed ^ (index * 0x9E3779B9))
            x += rng.uniform(-jitter, jitter)
            y += rng.uniform(-jitter, jitter)

        # ── Random rotation ───────────────────────────────────────────────
        # Baked into base_rotation for the same reason.
        base_rot = state.default_shape_rotation
        rot_random = float(p.get("rotation_random", 0.0))
        if rot_random > 0:
            rng_rot = random.Random(int(p.get("rotation_seed", 0)) ^ (index * 0x7F4A7C15))
            base_rot += rng_rot.uniform(-rot_random, rot_random)

        # ── Random scale ──────────────────────────────────────────────────
        # Baked into base_size.
        base_w, base_h = state.default_shape_size
        scale_random = float(p.get("scale_random", 0.0))
        if scale_random > 0:
            rng_scale = random.Random(int(p.get("scale_seed", 0)) ^ (index * 0x5BD1E995))
            factor = 1.0 + rng_scale.uniform(-scale_random, scale_random)
            factor = max(0.05, factor)   # floor at 5% of original size
            base_w *= factor
            base_h *= factor

        return ShapeInstance(
            index=index,
            base_position=(x, y),
            base_size=(base_w, base_h),
            base_rotation=base_rot,
            base_color=state.default_shape_color,
            shape_type=state.default_shape_type,
            custom_image_path=state.default_custom_image_path or None,
        )
