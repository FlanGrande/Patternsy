"""Pattern generator plugin system.

Each pattern type registers via @register_pattern.
Generators produce a list of ShapeInstance from PatternState.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patternsy_v2.model import PatternState, ShapeInstance

PATTERN_REGISTRY: dict[str, type["PatternGenerator"]] = {}


def register_pattern(name: str):
    """Decorator to register a pattern generator under *name*."""
    def decorator(cls: type[PatternGenerator]) -> type[PatternGenerator]:
        PATTERN_REGISTRY[name] = cls
        return cls
    return decorator


class PatternGenerator(ABC):
    """Base class for pattern coordinate generators."""

    @staticmethod
    @abstractmethod
    def generate(state: "PatternState") -> list["ShapeInstance"]:
        """Generate shapes from the current state."""
        ...

    @staticmethod
    def _make_shape(
        state: "PatternState",
        x: float,
        y: float,
    ) -> "ShapeInstance":
        """Helper: create a ShapeInstance at (x, y) using state defaults."""
        from patternsy_v2.model import ShapeInstance
        return ShapeInstance(
            position=(x, y),
            size=state.default_shape_size,
            rotation=state.default_shape_rotation,
            shape_type=state.default_shape_type,
            color=state.default_shape_color,
            custom_image_path=state.default_custom_image_path or None,
        )
