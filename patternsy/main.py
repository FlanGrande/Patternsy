#!/usr/bin/env python3
"""Patternsy — Interactive seamless pattern generator."""

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

import patternsy.shapes   # noqa: F401 — registers all shape types
import patternsy.patterns  # noqa: F401 — registers all pattern types


def _setup_theme() -> None:
    """Apply cutting-mat theme to all ImGui widgets."""
    s = imgui.get_style()
    C = imgui.Col_

    # ── Geometry ──────────────────────────────────────────────────────
    s.window_rounding    = 4.0
    s.frame_rounding     = 3.0
    s.grab_rounding      = 3.0
    s.tab_rounding       = 3.0
    s.scrollbar_rounding = 3.0
    s.popup_rounding     = 4.0
    s.child_rounding     = 4.0
    s.frame_padding      = imgui.ImVec2(6, 4)
    s.item_spacing       = imgui.ImVec2(8, 5)
    s.window_border_size = 1.0
    s.frame_border_size  = 0.0

    def sc(idx: int, r: int, g: int, b: int, a: float = 1.0) -> None:
        s.set_color_(idx, imgui.ImVec4(r/255, g/255, b/255, a))

    # Text
    sc(C.text,          0xEC, 0xE8, 0xD8)
    sc(C.text_disabled, 0x6A, 0x90, 0x84, 0.70)
    # Backgrounds
    sc(C.window_bg,      0x0D, 0x42, 0x36)
    sc(C.child_bg,       0x0D, 0x42, 0x36, 0.0)
    sc(C.popup_bg,       0x09, 0x30, 0x27)
    sc(C.border,         0x1F, 0x7A, 0x62, 0.80)
    sc(C.border_shadow,  0x00, 0x00, 0x00, 0.0)
    # Title bar
    sc(C.title_bg,           0x08, 0x32, 0x28)
    sc(C.title_bg_active,    0x0F, 0x4A, 0x3C)
    sc(C.title_bg_collapsed, 0x08, 0x32, 0x28, 0.75)
    # Menu bar
    sc(C.menu_bar_bg,        0x08, 0x38, 0x2C)
    # Scrollbar
    sc(C.scrollbar_bg,           0x08, 0x32, 0x28)
    sc(C.scrollbar_grab,         0x17, 0x6B, 0x56)
    sc(C.scrollbar_grab_hovered, 0xB8, 0x98, 0x28)
    sc(C.scrollbar_grab_active,  0xD4, 0xB0, 0x30)
    # Frames
    sc(C.frame_bg,         0x0A, 0x3C, 0x30)
    sc(C.frame_bg_hovered, 0x12, 0x55, 0x44)
    sc(C.frame_bg_active,  0x17, 0x6A, 0x55)
    # Slider
    sc(C.slider_grab,        0xC8, 0xA8, 0x32)
    sc(C.slider_grab_active, 0xE0, 0xC0, 0x40)
    # Check
    sc(C.check_mark, 0xD4, 0xB8, 0x3A)
    # Buttons
    sc(C.button,         0x12, 0x55, 0x44)
    sc(C.button_hovered, 0xA8, 0x88, 0x22)
    sc(C.button_active,  0xC8, 0xA8, 0x32)
    # Headers
    sc(C.header,         0x12, 0x55, 0x44)
    sc(C.header_hovered, 0xA8, 0x88, 0x22, 0.80)
    sc(C.header_active,  0xC8, 0xA8, 0x32)
    # Separator
    sc(C.separator,        0x1F, 0x7A, 0x62, 0.60)
    sc(C.separator_hovered,0xC8, 0xA8, 0x32, 0.80)
    sc(C.separator_active, 0xC8, 0xA8, 0x32)
    # Resize grip
    sc(C.resize_grip,        0xC8, 0xA8, 0x32, 0.40)
    sc(C.resize_grip_hovered,0xC8, 0xA8, 0x32, 0.80)
    sc(C.resize_grip_active, 0xE0, 0xC0, 0x40)
    # Tabs
    sc(C.tab,                 0x0A, 0x3C, 0x30)
    sc(C.tab_hovered,         0xA8, 0x88, 0x22)
    sc(C.tab_selected,        0x12, 0x55, 0x44)
    sc(C.tab_selected_overline,0xC8, 0xA8, 0x32)
    sc(C.tab_dimmed,          0x08, 0x32, 0x28)
    sc(C.tab_dimmed_selected, 0x0A, 0x3C, 0x30)
    # Docking
    sc(C.docking_preview,  0xC8, 0xA8, 0x32, 0.50)
    sc(C.docking_empty_bg, 0x08, 0x32, 0x28)
    # Plot
    sc(C.plot_lines,             0xC8, 0xA8, 0x32)
    sc(C.plot_lines_hovered,     0xE0, 0xC0, 0x40)
    sc(C.plot_histogram,         0xC8, 0xA8, 0x32)
    sc(C.plot_histogram_hovered, 0xE0, 0xC0, 0x40)
    # Table
    sc(C.table_header_bg,     0x08, 0x38, 0x2C)
    sc(C.table_border_strong, 0x1F, 0x7A, 0x62)
    sc(C.table_border_light,  0x12, 0x55, 0x44)
    sc(C.table_row_bg,        0x00, 0x00, 0x00, 0.0)
    sc(C.table_row_bg_alt,    0xFF, 0xFF, 0xFF, 0.03)
    # Nav / drag / modal
    sc(C.drag_drop_target,        0xC8, 0xA8, 0x32)
    sc(C.nav_cursor,              0xC8, 0xA8, 0x32)
    sc(C.nav_windowing_highlight, 0xC8, 0xA8, 0x32, 0.70)
    sc(C.nav_windowing_dim_bg,    0x00, 0x00, 0x00, 0.20)
    sc(C.modal_window_dim_bg,     0x00, 0x00, 0x00, 0.35)


# ── Main application ─────────────────────────────────────────────────────────

class PatternsyGui:
    def __init__(self):
        self.app = App()
        self.canvas = CanvasRenderer()
        self._first_frame = True
        self._theme_applied = False
        # Box selection state (screen coords)
        self._box_selecting: bool = False
        self._box_start: tuple[float, float] = (0.0, 0.0)
        self._box_end: tuple[float, float] = (0.0, 0.0)

    def run(self) -> None:
        self._runner_params = hello_imgui.RunnerParams()
        runner_params = self._runner_params
        runner_params.app_window_params.window_title = "Patternsy"
        runner_params.app_window_params.window_geometry.size = (1400, 900)
        runner_params.imgui_window_params.show_menu_bar = True
        runner_params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
        )
        runner_params.docking_params = self._docking_layout()
        runner_params.callbacks.show_gui   = self._gui
        runner_params.callbacks.show_menus = lambda: draw_toolbar(self.app, runner_params)
        # Clear GPU textures before the GL context is destroyed
        runner_params.callbacks.before_exit = self._on_exit
        immapp.run(runner_params)

    def _on_exit(self) -> None:
        from patternsy.canvas import clear_texture_cache
        clear_texture_cache()

    def _docking_layout(self) -> hello_imgui.DockingParams:
        dp = hello_imgui.DockingParams()

        split_left = hello_imgui.DockingSplit()
        split_left.initial_dock = "MainDockSpace"
        split_left.new_dock = "LeftPanel"
        split_left.direction = imgui.Dir_.left
        split_left.ratio = 0.25

        split_left_bottom = hello_imgui.DockingSplit()
        split_left_bottom.initial_dock = "LeftPanel"
        split_left_bottom.new_dock = "BottomLeftPanel"
        split_left_bottom.direction = imgui.Dir_.down
        split_left_bottom.ratio = 0.5

        dp.docking_splits = [split_left, split_left_bottom]

        w_canvas   = hello_imgui.DockableWindow(); w_canvas.label   = "Canvas Settings"; w_canvas.dock_space_name   = "LeftPanel"
        w_pattern  = hello_imgui.DockableWindow(); w_pattern.label  = "Pattern Settings"; w_pattern.dock_space_name  = "LeftPanel"
        w_props    = hello_imgui.DockableWindow(); w_props.label    = "Properties";       w_props.dock_space_name    = "BottomLeftPanel"
        w_viewport = hello_imgui.DockableWindow(); w_viewport.label = "Viewport";         w_viewport.dock_space_name = "MainDockSpace"

        dp.dockable_windows = [w_canvas, w_pattern, w_props, w_viewport]
        return dp

    def _gui(self) -> None:
        # Apply theme once after GL context is live
        if not self._theme_applied:
            _setup_theme()
            self._theme_applied = True

        self.app.tick()

        draw_canvas_panel(self.app)
        draw_pattern_panel(self.app)
        draw_properties_panel(self.app)

        # ── Viewport ────────────────────────────────────────────────────
        imgui.begin("Viewport")
        avail  = imgui.get_content_region_avail()
        cursor = imgui.get_cursor_screen_pos()

        if self._first_frame:
            cw, ch = self.app.state.canvas_size
            self.canvas.reset_view(cw, ch, avail.x, avail.y)
            self._first_frame = False

        imgui.invisible_button("canvas_area", avail)
        is_hovered = imgui.is_item_hovered()

        draw_list = imgui.get_window_draw_list()

        self.canvas.draw(
            draw_list, cursor, avail,
            self.app.state.shapes,
            self.app.selected_ids,
            float(self.app.state.canvas_size[0]),
            float(self.app.state.canvas_size[1]),
            self.app.state.show_tiling_ghosts,
            self.app.state.bg_color,
        )

        if is_hovered:
            self.canvas.handle_pan_zoom(cursor, avail)

        self._handle_mouse(cursor, avail, draw_list, is_hovered)
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
        mouse  = io.mouse_pos
        ox, oy = origin.x, origin.y
        cx, cy = self.canvas.screen_to_canvas(mouse.x, mouse.y, ox, oy)
        extend = io.key_shift

        # ── Left click ────────────────────────────────────────────────
        if imgui.is_mouse_clicked(imgui.MouseButton_.left) and hovered:
            hit = self.app.pick(cx, cy, extend)
            if hit and not hit.locked:
                self.app.begin_drag(cx, cy)
                self._box_selecting = False
            elif hit is None:
                self._box_selecting = True
                self._box_start = (mouse.x, mouse.y)
                self._box_end   = (mouse.x, mouse.y)

        # ── Left drag ─────────────────────────────────────────────────
        if imgui.is_mouse_dragging(imgui.MouseButton_.left, 4.0):
            if self.app.is_dragging:
                self.app.update_drag(cx, cy)
            elif self._box_selecting:
                self._box_end = (mouse.x, mouse.y)

        # ── Box selection rect (gold) ──────────────────────────────────
        if self._box_selecting:
            sx0, sy0 = self._box_start
            sx1, sy1 = self._box_end
            draw_list.push_clip_rect(
                imgui.ImVec2(ox, oy),
                imgui.ImVec2(ox + size.x, oy + size.y),
                True,
            )
            fill_col   = imgui.get_color_u32(imgui.ImVec4(0.78, 0.66, 0.19, 0.15))
            border_col = imgui.get_color_u32(imgui.ImVec4(0.83, 0.72, 0.22, 0.90))
            draw_list.add_rect_filled(imgui.ImVec2(sx0, sy0), imgui.ImVec2(sx1, sy1), fill_col)
            draw_list.add_rect(imgui.ImVec2(sx0, sy0), imgui.ImVec2(sx1, sy1), border_col, 0, 0, 1.5)
            draw_list.pop_clip_rect()

        # ── Left release ───────────────────────────────────────────────
        if imgui.is_mouse_released(imgui.MouseButton_.left):
            if self.app.is_dragging:
                self.app.end_drag()
            if self._box_selecting:
                self._finish_box_select(ox, oy, extend)
                self._box_selecting = False

    def _finish_box_select(self, ox: float, oy: float, extend: bool) -> None:
        sx0, sy0 = self._box_start
        sx1, sy1 = self._box_end
        cx0, cy0 = self.canvas.screen_to_canvas(min(sx0, sx1), min(sy0, sy1), ox, oy)
        cx1, cy1 = self.canvas.screen_to_canvas(max(sx0, sx1), max(sy0, sy1), ox, oy)

        if abs(sx1 - sx0) < 4 and abs(sy1 - sy0) < 4:
            return

        hit_ids: set[str] = set()
        for shape in self.app.state.shapes:
            spx, spy = shape.position
            shw, shh = shape.size[0] / 2, shape.size[1] / 2
            if spx + shw > cx0 and spx - shw < cx1 and spy + shh > cy0 and spy - shh < cy1:
                hit_ids.add(shape.id)

        new_sel = (self.app.selected_ids | hit_ids) if extend else hit_ids
        if frozenset(new_sel) != frozenset(self.app.selected_ids):
            self.app._push_selection()
            self.app.selected_ids = new_sel

    def _handle_keyboard(self) -> None:
        io = imgui.get_io()
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
            cw, ch = self.app.state.canvas_size
            avail = imgui.get_content_region_avail()
            self.canvas.reset_view(cw, ch, avail.x, avail.y)


def main():
    gui = PatternsyGui()
    gui.run()


if __name__ == "__main__":
    main()
