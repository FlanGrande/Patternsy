"""Pattern generator plugin system."""

from __future__ import annotations

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
        """Create a ShapeInstance at (x, y) with stable index and state defaults as base values."""
        from patternsy.model import ShapeInstance
        return ShapeInstance(
            index=index,
            base_position=(x, y),
            base_size=state.default_shape_size,
            base_rotation=state.default_shape_rotation,
            base_color=state.default_shape_color,
            shape_type=state.default_shape_type,
            custom_image_path=state.default_custom_image_path or None,
        )
