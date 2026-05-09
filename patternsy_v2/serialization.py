"""JSON save/load for PatternState."""

from __future__ import annotations

import json
from pathlib import Path

from patternsy_v2.model import PatternState, ShapeInstance


def save_project(state: PatternState, path: str | Path) -> None:
    data = {
        "version": state.version,
        "canvas_size": list(state.canvas_size),
        "bg_color": list(state.bg_color),
        "pattern_type": state.pattern_type,
        "pattern_params": state.pattern_params,
        "default_shape_type": state.default_shape_type,
        "default_shape_size": list(state.default_shape_size),
        "default_shape_color": list(state.default_shape_color),
        "default_shape_rotation": state.default_shape_rotation,
        "default_custom_image_path": state.default_custom_image_path,
        "show_tiling_ghosts": state.show_tiling_ghosts,
        "shapes": [_shape_to_dict(s) for s in state.shapes],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_project(path: str | Path) -> PatternState:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    state = PatternState()
    state.version = data.get("version", "2.0.0")
    cs = data.get("canvas_size", [1024, 1024])
    state.canvas_size = (int(cs[0]), int(cs[1]))
    bg = data.get("bg_color", [0, 0, 0, 255])
    state.bg_color = tuple(int(c) for c in bg)  # type: ignore
    state.pattern_type = data.get("pattern_type", "grid")
    state.pattern_params = data.get("pattern_params", state.pattern_params)
    state.default_shape_type = data.get("default_shape_type", "circle")
    ds = data.get("default_shape_size", [32, 32])
    state.default_shape_size = (float(ds[0]), float(ds[1]))
    dc = data.get("default_shape_color", [255, 136, 0, 255])
    state.default_shape_color = tuple(int(c) for c in dc)  # type: ignore
    state.default_shape_rotation = float(data.get("default_shape_rotation", 0))
    state.default_custom_image_path = data.get("default_custom_image_path", "")
    state.show_tiling_ghosts = data.get("show_tiling_ghosts", True)
    state.shapes = [_dict_to_shape(d) for d in data.get("shapes", [])]
    return state


def _shape_to_dict(s: ShapeInstance) -> dict:
    return {
        "id": s.id,
        "index": s.index,
        "base_position": list(s.base_position),
        "base_size": list(s.base_size),
        "base_rotation": s.base_rotation,
        "base_color": list(s.base_color),
        "shape_type": s.shape_type,
        "custom_image_path": s.custom_image_path or "",
        "delta_position": list(s.delta_position),
        "delta_size": list(s.delta_size),
        "delta_rotation": s.delta_rotation,
        "override_color": list(s.override_color) if s.override_color is not None else None,
        "locked": s.locked,
    }


def _dict_to_shape(d: dict) -> ShapeInstance:
    oc = d.get("override_color")
    return ShapeInstance(
        id=d.get("id", ""),
        index=int(d.get("index", 0)),
        base_position=tuple(d.get("base_position", [0, 0])),  # type: ignore
        base_size=tuple(d.get("base_size", [32, 32])),        # type: ignore
        base_rotation=float(d.get("base_rotation", 0)),
        base_color=tuple(d.get("base_color", [255, 136, 0, 255])),  # type: ignore
        shape_type=d.get("shape_type", "circle"),
        custom_image_path=d.get("custom_image_path") or None,
        delta_position=tuple(d.get("delta_position", [0, 0])),  # type: ignore
        delta_size=tuple(d.get("delta_size", [0, 0])),          # type: ignore
        delta_rotation=float(d.get("delta_rotation", 0)),
        override_color=tuple(oc) if oc is not None else None,  # type: ignore
        locked=bool(d.get("locked", False)),
    )
