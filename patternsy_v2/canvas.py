"""Interactive canvas rendered via ImGui's ImDrawList.

Handles viewport transform (pan/zoom), shape drawing, selection
highlight, ghost tiling preview, and mouse interaction dispatch.
"""

from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image as PILImage
from imgui_bundle import imgui, hello_imgui

from patternsy_v2.model import ShapeInstance
from patternsy_v2.shapes.base import SHAPE_REGISTRY
from patternsy_v2.tiling import ghost_offsets

# ── Color helpers ───────────────────────────────────────────────────────────

def _rgba_to_u32(r: int, g: int, b: int, a: int) -> int:
    return imgui.get_color_u32(imgui.ImVec4(r / 255, g / 255, b / 255, a / 255))

def _rgba_to_u32_alpha(r: int, g: int, b: int, a: int, alpha_mult: float) -> int:
    return imgui.get_color_u32(imgui.ImVec4(r / 255, g / 255, b / 255, (a / 255) * alpha_mult))

# ── GPU texture cache ────────────────────────────────────────────────────────
# Key: image file path. Value: hello_imgui.TextureGpu (must stay alive).
_texture_cache: dict[str, hello_imgui.TextureGpu] = {}

def _get_texture(path: str) -> hello_imgui.TextureGpu | None:
    """Load image from path into a GPU texture (cached by path)."""
    if not path or not os.path.exists(path):
        return None
    if path in _texture_cache:
        return _texture_cache[path]
    try:
        img = PILImage.open(path).convert("RGBA")
        arr = np.asarray(img, dtype=np.uint8)
        tex = hello_imgui.create_texture_gpu_from_rgba_data(arr)
        _texture_cache[path] = tex
        return tex
    except Exception as e:
        print(f"[canvas] texture load failed: {e}")
        return None

def clear_texture_cache() -> None:
    _texture_cache.clear()


class CanvasRenderer:
    """Draws shapes on an ImGui canvas region with pan/zoom."""

    def __init__(self):
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.zoom: float = 1.0  # Never 0; reset_view sets proper value

    # ── Coordinate transforms ───────────────────────────────────────────

    def canvas_to_screen(self, cx: float, cy: float, origin_x: float, origin_y: float) -> tuple[float, float]:
        return (origin_x + cx * self.zoom + self.offset_x,
                origin_y + cy * self.zoom + self.offset_y)

    def screen_to_canvas(self, sx: float, sy: float, origin_x: float, origin_y: float) -> tuple[float, float]:
        z = self.zoom if self.zoom != 0 else 1.0
        return ((sx - origin_x - self.offset_x) / z,
                (sy - origin_y - self.offset_y) / z)

    # ── Main draw call ──────────────────────────────────────────────────

    def draw(
        self,
        draw_list: imgui.ImDrawList,
        origin: imgui.ImVec2,
        size: imgui.ImVec2,
        shapes: list[ShapeInstance],
        selected_ids: set[str],
        canvas_w: float,
        canvas_h: float,
        show_ghosts: bool,
        bg_color: tuple[int, int, int, int],
    ) -> None:
        ox, oy = origin.x, origin.y

        # Clip to canvas region
        draw_list.push_clip_rect(imgui.ImVec2(ox, oy), imgui.ImVec2(ox + size.x, oy + size.y), True)

        # Draw canvas background
        tl = self.canvas_to_screen(0, 0, ox, oy)
        br = self.canvas_to_screen(canvas_w, canvas_h, ox, oy)
        draw_list.add_rect_filled(
            imgui.ImVec2(tl[0], tl[1]),
            imgui.ImVec2(br[0], br[1]),
            _rgba_to_u32(*bg_color),
        )
        # Canvas border
        draw_list.add_rect(
            imgui.ImVec2(tl[0], tl[1]),
            imgui.ImVec2(br[0], br[1]),
            _rgba_to_u32(128, 128, 128, 255),
        )

        # Draw shapes
        for shape in shapes:
            self._draw_shape(draw_list, ox, oy, shape, shape.id in selected_ids, 1.0)
            if show_ghosts:
                for dx, dy in ghost_offsets(shape, canvas_w, canvas_h):
                    ghost = shape.clone()
                    ghost.position = (shape.position[0] + dx, shape.position[1] + dy)
                    self._draw_shape(draw_list, ox, oy, ghost, False, 0.3)

        # Selection highlight: draw bounding boxes for selected shapes
        for shape in shapes:
            if shape.id in selected_ids:
                self._draw_selection_box(draw_list, ox, oy, shape)

        draw_list.pop_clip_rect()

    # ── Per-shape drawing ───────────────────────────────────────────────

    def _draw_shape(
        self,
        draw_list: imgui.ImDrawList,
        ox: float,
        oy: float,
        shape: ShapeInstance,
        selected: bool,
        alpha: float,
    ) -> None:
        cx, cy = shape.position
        sw, sh = shape.size
        rot_rad = math.radians(shape.rotation)
        cos_r = math.cos(rot_rad)
        sin_r = math.sin(rot_rad)
        color = _rgba_to_u32_alpha(*shape.color, alpha)

        shape_cls = SHAPE_REGISTRY.get(shape.shape_type)
        if shape_cls is None:
            return

        # ── Custom image: render as textured quad ───────────────────────
        if shape.shape_type == "custom" and shape.custom_image_path:
            tex = _get_texture(shape.custom_image_path)
            if tex is not None:
                # 4 corners of the quad in local space (normalized -0.5..+0.5)
                corners_local = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
                pts = [
                    self._transform_vertex(v, cx, cy, sw, sh, cos_r, sin_r, ox, oy)
                    for v in corners_local
                ]
                tint = _rgba_to_u32_alpha(255, 255, 255, 255, alpha)
                tex_ref = imgui.ImTextureRef(tex.texture_id())
                draw_list.add_image_quad(
                    tex_ref,
                    imgui.ImVec2(pts[0][0], pts[0][1]),  # top-left
                    imgui.ImVec2(pts[1][0], pts[1][1]),  # top-right
                    imgui.ImVec2(pts[2][0], pts[2][1]),  # bottom-right
                    imgui.ImVec2(pts[3][0], pts[3][1]),  # bottom-left
                    col=tint,
                )
                return
            # Fallback if texture failed: magenta square
            color = _rgba_to_u32_alpha(255, 0, 255, 255, alpha)

        verts = shape_cls.vertices(sw, sh)

        if shape.shape_type == "circle":
            # Optimized: use ImDrawList circle primitive
            scx, scy = self.canvas_to_screen(cx, cy, ox, oy)
            radius = (sw / 2) * self.zoom
            draw_list.add_circle_filled(
                imgui.ImVec2(scx, scy), radius, color, 64,
            )
        elif shape.shape_type == "star":
            # TRIANGLE_FAN: first vertex is center
            center = verts[0]
            fan_verts = verts[1:]
            scx_c, scy_c = self._transform_vertex(center, cx, cy, sw, sh, cos_r, sin_r, ox, oy)
            for i in range(len(fan_verts) - 1):
                v1 = fan_verts[i]
                v2 = fan_verts[i + 1]
                sv1 = self._transform_vertex(v1, cx, cy, sw, sh, cos_r, sin_r, ox, oy)
                sv2 = self._transform_vertex(v2, cx, cy, sw, sh, cos_r, sin_r, ox, oy)
                draw_list.add_triangle_filled(
                    imgui.ImVec2(scx_c, scy_c),
                    imgui.ImVec2(sv1[0], sv1[1]),
                    imgui.ImVec2(sv2[0], sv2[1]),
                    color,
                )
        elif shape.shape_type == "triangle":
            # 3 vertices → single filled triangle
            pts = [self._transform_vertex(v, cx, cy, sw, sh, cos_r, sin_r, ox, oy) for v in verts]
            draw_list.add_triangle_filled(
                imgui.ImVec2(pts[0][0], pts[0][1]),
                imgui.ImVec2(pts[1][0], pts[1][1]),
                imgui.ImVec2(pts[2][0], pts[2][1]),
                color,
            )
        else:
            # Generic quad (two triangles) — square, custom fallback
            for i in range(0, len(verts) - 2, 3):
                pts = [self._transform_vertex(verts[i + j], cx, cy, sw, sh, cos_r, sin_r, ox, oy) for j in range(3)]
                draw_list.add_triangle_filled(
                    imgui.ImVec2(pts[0][0], pts[0][1]),
                    imgui.ImVec2(pts[1][0], pts[1][1]),
                    imgui.ImVec2(pts[2][0], pts[2][1]),
                    color,
                )

    def _draw_selection_box(
        self,
        draw_list: imgui.ImDrawList,
        ox: float,
        oy: float,
        shape: ShapeInstance,
    ) -> None:
        cx, cy = shape.position
        hw, hh = shape.size[0] / 2, shape.size[1] / 2
        tl = self.canvas_to_screen(cx - hw, cy - hh, ox, oy)
        br = self.canvas_to_screen(cx + hw, cy + hh, ox, oy)
        draw_list.add_rect(
            imgui.ImVec2(tl[0], tl[1]),
            imgui.ImVec2(br[0], br[1]),
            _rgba_to_u32(0, 200, 255, 220),
            0, 0, 2.0,
        )
        # Corner handles
        for hx, hy in [(tl[0], tl[1]), (br[0], tl[1]), (tl[0], br[1]), (br[0], br[1])]:
            draw_list.add_circle_filled(imgui.ImVec2(hx, hy), 4.0, _rgba_to_u32(0, 200, 255, 255))

    # ── Vertex transform ────────────────────────────────────────────────

    def _transform_vertex(
        self,
        v: tuple[float, float],
        cx: float, cy: float,
        sw: float, sh: float,
        cos_r: float, sin_r: float,
        ox: float, oy: float,
    ) -> tuple[float, float]:
        """Local vertex → rotated → canvas → screen."""
        lx = v[0] * sw
        ly = v[1] * sh
        rx = lx * cos_r - ly * sin_r
        ry = lx * sin_r + ly * cos_r
        return self.canvas_to_screen(cx + rx, cy + ry, ox, oy)

    # ── Pan / Zoom ──────────────────────────────────────────────────────

    def handle_pan_zoom(self, origin: imgui.ImVec2, size: imgui.ImVec2) -> None:
        """Call after drawing; reads ImGui IO for pan (middle drag) and zoom (scroll)."""
        io = imgui.get_io()
        mouse = io.mouse_pos

        # Check if mouse is in canvas region
        in_canvas = (origin.x <= mouse.x <= origin.x + size.x and
                     origin.y <= mouse.y <= origin.y + size.y)
        if not in_canvas:
            return

        # Zoom with scroll wheel
        if io.mouse_wheel != 0:
            old_zoom = self.zoom
            self.zoom = max(0.1, min(20.0, self.zoom + io.mouse_wheel * 0.1))
            # Zoom toward mouse position
            factor = self.zoom / old_zoom
            self.offset_x = mouse.x - origin.x - (mouse.x - origin.x - self.offset_x) * factor
            self.offset_y = mouse.y - origin.y - (mouse.y - origin.y - self.offset_y) * factor

        # Pan with middle mouse button
        if imgui.is_mouse_dragging(imgui.MouseButton_.middle, 0):
            delta = io.mouse_delta
            self.offset_x += delta.x
            self.offset_y += delta.y

    def reset_view(self, canvas_w: float, canvas_h: float, viewport_w: float, viewport_h: float) -> None:
        """Fit canvas in viewport."""
        if canvas_w <= 0 or canvas_h <= 0 or viewport_w <= 0 or viewport_h <= 0:
            self.zoom = 1.0
            self.offset_x = 0.0
            self.offset_y = 0.0
            return
        scale_x = viewport_w / canvas_w
        scale_y = viewport_h / canvas_h
        self.zoom = min(scale_x, scale_y) * 0.9
        self.offset_x = (viewport_w - canvas_w * self.zoom) / 2
        self.offset_y = (viewport_h - canvas_h * self.zoom) / 2
