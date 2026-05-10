#!/usr/bin/env python3
"""Patternsy v2 — Interactive seamless pattern generator.

Main entry point. Sets up the ImGui/GLFW window and runs the main loop.
"""

from __future__ import annotations

import sys

from imgui_bundle import imgui, hello_imgui, immapp

from patternsy.app import App
from patternsy.canvas import CanvasRenderer
from patternsy.ui.panels import (
    draw_toolbar,
    draw_pattern_panel,
    draw_canvas_panel,
    draw_properties_panel,
)

# Force shape/pattern registration by importing the packages
import patternsy.shapes  # noqa: F401
import patternsy.patterns  # noqa: F401


class PatternsyGui:
    def __init__(self):
        self.app = App()
        self.canvas = CanvasRenderer()
        self._first_frame = True
        # Box selection state (screen coords)
        self._box_selecting: bool = False
        self._box_start: tuple[float, float] = (0.0, 0.0)
        self._box_end: tuple[float, float] = (0.0, 0.0)

    def run(self) -> None:
        runner_params = hello_imgui.RunnerParams()
        runner_params.app_window_params.window_title = "Patternsy v2"
        runner_params.app_window_params.window_geometry.size = (1400, 900)
        runner_params.imgui_window_params.show_menu_bar = True
        runner_params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
        )

        # Docking layout
        runner_params.docking_params = self._docking_layout()

        # Callbacks
        runner_params.callbacks.show_gui = self._gui
        runner_params.callbacks.show_menus = lambda: draw_toolbar(self.app)

        immapp.run(runner_params)

    def _docking_layout(self) -> hello_imgui.DockingParams:
        dp = hello_imgui.DockingParams()

        # Splits
        split_main_left = hello_imgui.DockingSplit()
        split_main_left.initial_dock = "MainDockSpace"
        split_main_left.new_dock = "LeftPanel"
        split_main_left.direction = imgui.Dir_.left
        split_main_left.ratio = 0.25

        split_left_bottom = hello_imgui.DockingSplit()
        split_left_bottom.initial_dock = "LeftPanel"
        split_left_bottom.new_dock = "BottomLeftPanel"
        split_left_bottom.direction = imgui.Dir_.down
        split_left_bottom.ratio = 0.5

        dp.docking_splits = [split_main_left, split_left_bottom]

        # Windows
        w_canvas_settings = hello_imgui.DockableWindow()
        w_canvas_settings.label = "Canvas Settings"
        w_canvas_settings.dock_space_name = "LeftPanel"

        w_pattern = hello_imgui.DockableWindow()
        w_pattern.label = "Pattern Settings"
        w_pattern.dock_space_name = "LeftPanel"

        w_properties = hello_imgui.DockableWindow()
        w_properties.label = "Properties"
        w_properties.dock_space_name = "BottomLeftPanel"

        w_viewport = hello_imgui.DockableWindow()
        w_viewport.label = "Viewport"
        w_viewport.dock_space_name = "MainDockSpace"

        dp.dockable_windows = [w_canvas_settings, w_pattern, w_properties, w_viewport]
        return dp

    def _gui(self) -> None:
        # Live update: regenerate if any pattern param changed
        self.app.tick()

        # Draw side panels (handled by docking)
        draw_canvas_panel(self.app)
        draw_pattern_panel(self.app)
        draw_properties_panel(self.app)

        # Viewport
        imgui.begin("Viewport")
        avail = imgui.get_content_region_avail()
        cursor = imgui.get_cursor_screen_pos()

        if self._first_frame:
            cw, ch = self.app.state.canvas_size
            self.canvas.reset_view(cw, ch, avail.x, avail.y)
            self._first_frame = False

        # Reserve space for the canvas
        imgui.invisible_button("canvas_area", avail)
        is_canvas_hovered = imgui.is_item_hovered()
        is_canvas_active = imgui.is_item_active()

        draw_list = imgui.get_window_draw_list()

        # Draw shapes
        self.canvas.draw(
            draw_list,
            cursor,
            avail,
            self.app.state.shapes,
            self.app.selected_ids,
            float(self.app.state.canvas_size[0]),
            float(self.app.state.canvas_size[1]),
            self.app.state.show_tiling_ghosts,
            self.app.state.bg_color,
        )

        # Handle pan/zoom
        if is_canvas_hovered:
            self.canvas.handle_pan_zoom(cursor, avail)

        # Handle mouse interaction for selection/dragging/box-select
        self._handle_mouse(cursor, avail, draw_list, is_canvas_hovered)

        # Handle keyboard shortcuts
        self._handle_keyboard()

        imgui.end()

    def _handle_mouse(
        self,
        origin: imgui.ImVec2,
        size: imgui.ImVec2,
        draw_list: imgui.ImDrawList,
        hovered: bool,
    ) -> None:
        io = imgui.get_io()
        mouse = io.mouse_pos
        ox, oy = origin.x, origin.y
        cx, cy = self.canvas.screen_to_canvas(mouse.x, mouse.y, ox, oy)
        extend = io.key_shift

        # ── Left click ────────────────────────────────────────────────────
        if imgui.is_mouse_clicked(imgui.MouseButton_.left) and hovered:
            hit = self.app.pick(cx, cy, extend)
            if hit and not hit.locked:
                # Clicked a shape → start drag
                self.app.begin_drag(cx, cy)
                self._box_selecting = False
            elif hit is None:
                # Clicked empty space → start box selection
                self._box_selecting = True
                self._box_start = (mouse.x, mouse.y)
                self._box_end = (mouse.x, mouse.y)

        # ── Left drag ─────────────────────────────────────────────────────
        if imgui.is_mouse_dragging(imgui.MouseButton_.left, 4.0):
            if self.app.is_dragging:
                self.app.update_drag(cx, cy)
            elif self._box_selecting:
                self._box_end = (mouse.x, mouse.y)

        # ── Draw box selection rect ───────────────────────────────────────
        if self._box_selecting:
            sx0, sy0 = self._box_start
            sx1, sy1 = self._box_end
            # Clip rect to viewport
            draw_list.push_clip_rect(
                imgui.ImVec2(ox, oy),
                imgui.ImVec2(ox + size.x, oy + size.y),
                True,
            )
            fill_col = imgui.get_color_u32(imgui.ImVec4(0.2, 0.6, 1.0, 0.15))
            border_col = imgui.get_color_u32(imgui.ImVec4(0.3, 0.7, 1.0, 0.9))
            draw_list.add_rect_filled(
                imgui.ImVec2(sx0, sy0), imgui.ImVec2(sx1, sy1), fill_col,
            )
            draw_list.add_rect(
                imgui.ImVec2(sx0, sy0), imgui.ImVec2(sx1, sy1), border_col, 0, 0, 1.5,
            )
            draw_list.pop_clip_rect()

        # ── Left release ──────────────────────────────────────────────────
        if imgui.is_mouse_released(imgui.MouseButton_.left):
            if self.app.is_dragging:
                self.app.end_drag()

            if self._box_selecting:
                self._finish_box_select(ox, oy, extend)
                self._box_selecting = False

    def _finish_box_select(self, ox: float, oy: float, extend: bool) -> None:
        """Convert box (screen coords) to canvas coords and select all shapes inside."""
        sx0, sy0 = self._box_start
        sx1, sy1 = self._box_end

        # Normalise so min/max are correct regardless of drag direction
        cx0, cy0 = self.canvas.screen_to_canvas(min(sx0, sx1), min(sy0, sy1), ox, oy)
        cx1, cy1 = self.canvas.screen_to_canvas(max(sx0, sx1), max(sy0, sy1), ox, oy)

        # Skip tiny accidental clicks (< 4 px drag)
        if abs(sx1 - sx0) < 4 and abs(sy1 - sy0) < 4:
            return

        hit_ids: set[str] = set()
        for shape in self.app.state.shapes:
            spx, spy = shape.position
            shw, shh = shape.size[0] / 2, shape.size[1] / 2
            # AABB overlap test
            if (spx + shw > cx0 and spx - shw < cx1 and
                    spy + shh > cy0 and spy - shh < cy1):
                hit_ids.add(shape.id)

        if extend:
            self.app.selected_ids |= hit_ids
        else:
            self.app.selected_ids = hit_ids

    def _handle_keyboard(self) -> None:
        io = imgui.get_io()

        # Only process if no text input is active
        if io.want_text_input:
            return

        ctrl = io.key_ctrl

        if ctrl and imgui.is_key_pressed(imgui.Key.z):
            self.app.undo()
        elif ctrl and imgui.is_key_pressed(imgui.Key.y):
            self.app.redo()
        elif ctrl and imgui.is_key_pressed(imgui.Key.a):
            self.app.select_all()
        elif imgui.is_key_pressed(imgui.Key.delete):
            self.app.delete_selected()
        elif imgui.is_key_pressed(imgui.Key.escape):
            self.app.deselect_all()
        elif imgui.is_key_pressed(imgui.Key.f):
            # Fit view
            cw, ch = self.app.state.canvas_size
            avail = imgui.get_content_region_avail()
            self.canvas.reset_view(cw, ch, avail.x, avail.y)


def main():
    gui = PatternsyGui()
    gui.run()


if __name__ == "__main__":
    main()
