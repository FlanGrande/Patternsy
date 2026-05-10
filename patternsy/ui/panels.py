"""ImGui UI panels: properties, pattern settings, canvas settings, toolbar."""

from __future__ import annotations

import os
from imgui_bundle import imgui, portable_file_dialogs as pfd

from patternsy.app import App
from patternsy.shapes.base import SHAPE_REGISTRY
from patternsy.patterns.base import PATTERN_REGISTRY
from patternsy.serialization import save_project, load_project
from patternsy.export import export_pattern

# Track file dialog state
_save_dialog = None
_load_dialog = None
_export_dialog = None
_custom_img_dialog = None


def draw_toolbar(app: App) -> None:
    """Menu items (called inside hello_imgui's menu bar context)."""
    if imgui.begin_menu("File"):
        if imgui.menu_item("Save Project", "Ctrl+S", False, True)[0]:
            _start_save_dialog(app)
        if imgui.menu_item("Load Project", "Ctrl+O", False, True)[0]:
            _start_load_dialog(app)
        imgui.separator()
        if imgui.menu_item("Export Image", "Ctrl+E", False, True)[0]:
            _start_export_dialog(app)
        imgui.separator()
        if imgui.menu_item("Quit", "Ctrl+Q", False, True)[0]:
            import sys
            sys.exit(0)
        imgui.end_menu()

    if imgui.begin_menu("Edit"):
        if imgui.menu_item("Undo", "Ctrl+Z", False, app.history.can_undo)[0]:
            app.undo()
        if imgui.menu_item("Redo", "Ctrl+Y", False, app.history.can_redo)[0]:
            app.redo()
        imgui.separator()
        if imgui.menu_item("Select All", "Ctrl+A", False, True)[0]:
            app.select_all()
        if imgui.menu_item("Deselect All", "Escape", False, True)[0]:
            app.deselect_all()
        if imgui.menu_item("Delete Selected", "Delete", False, len(app.selected_ids) > 0)[0]:
            app.delete_selected()
        imgui.end_menu()

    # Process pending file dialogs
    _process_dialogs(app)


def draw_pattern_panel(app: App) -> None:
    """Pattern generator settings panel."""
    imgui.begin("Pattern Settings")

    # Pattern type
    pattern_names = list(PATTERN_REGISTRY.keys())
    current_idx = pattern_names.index(app.state.pattern_type) if app.state.pattern_type in pattern_names else 0
    changed, new_idx = imgui.combo("Pattern Type", current_idx, pattern_names)
    if changed:
        app.state.pattern_type = pattern_names[new_idx]

    imgui.separator()

    # Pattern params
    p = app.state.pattern_params
    changed, v = imgui.input_int("Columns", int(p.get("columns", 8)))
    if changed:
        p["columns"] = max(1, v)
    changed, v = imgui.input_int("Rows", int(p.get("rows", 8)))
    if changed:
        p["rows"] = max(1, v)

    if app.state.pattern_type == "diagonal_grid":
        changed, v = imgui.input_int("Diagonal Offset X", int(p.get("diagonal_offset_x", 0)))
        if changed:
            p["diagonal_offset_x"] = v

    if app.state.pattern_type in ("random", "diagonal_grid", "grid", "offset_grid"):
        changed, v = imgui.input_int("Seed", int(p.get("seed", 0)))
        if changed:
            p["seed"] = v
        imgui.same_line()
        if imgui.button("New Seed"):
            import random
            p["seed"] = random.randint(0, 2**31 - 1)

    changed, v = imgui.input_int("Jitter", int(p.get("jitter", 0)))
    if changed:
        p["jitter"] = max(0, v)

    imgui.separator()

    # Default shape settings
    imgui.text("Default Shape:")
    shape_names = list(SHAPE_REGISTRY.keys())
    current_shape_idx = shape_names.index(app.state.default_shape_type) if app.state.default_shape_type in shape_names else 0
    changed, new_shape_idx = imgui.combo("Shape Type", current_shape_idx, shape_names)
    if changed:
        app.state.default_shape_type = shape_names[new_shape_idx]

    size = list(app.state.default_shape_size)
    changed, size = imgui.input_float2("Shape Size", size)
    if changed:
        app.state.default_shape_size = (max(1.0, size[0]), max(1.0, size[1]))

    imgui.set_next_item_width(imgui.get_content_region_avail().x - 70)
    changed, v = imgui.slider_float("##defrot_slider", app.state.default_shape_rotation, 0.0, 360.0)
    if changed:
        app.state.default_shape_rotation = v
    imgui.same_line()
    imgui.set_next_item_width(60)
    changed, v = imgui.input_float("##defrot_input", app.state.default_shape_rotation, 0.0, 0.0, "%.1f")
    if changed:
        app.state.default_shape_rotation = v % 360
    imgui.same_line()
    imgui.text("Rotation")

    col = [c / 255 for c in app.state.default_shape_color]
    changed, col = imgui.color_edit4("Shape Color", col)
    if changed:
        app.state.default_shape_color = tuple(int(c * 255) for c in col)  # type: ignore

    if app.state.default_shape_type == "custom":
        path_text = app.state.default_custom_image_path or "(none)"
        imgui.text(f"Image: {os.path.basename(path_text)}")
        if imgui.button("Browse Custom Image..."):
            _start_custom_img_dialog(app)

    imgui.separator()

    # Reset all points to pattern defaults
    n_edited = sum(1 for s in app.state.shapes if s.has_any_delta())
    label = f"Reset All Points ({n_edited} edited)" if n_edited else "Reset All Points"
    if imgui.button(label, imgui.ImVec2(-1, 0)):
        app.reset_all_deltas()

    imgui.spacing()

    # Quick export button — defaults to cwd
    if imgui.button("Export Image...", imgui.ImVec2(-1, 0)):
        _start_export_dialog(app)

    imgui.end()


def draw_canvas_panel(app: App) -> None:
    """Canvas dimensions and background color."""
    imgui.begin("Canvas Settings")

    cs = list(app.state.canvas_size)
    changed, cs = imgui.input_int2("Canvas Size", cs)
    if changed:
        app.state.canvas_size = (max(1, min(16384, cs[0])), max(1, min(16384, cs[1])))

    bg = [c / 255 for c in app.state.bg_color]
    changed, bg = imgui.color_edit4("Background", bg)
    if changed:
        app.state.bg_color = tuple(int(c * 255) for c in bg)  # type: ignore

    changed, v = imgui.checkbox("Show Tiling Ghosts", app.state.show_tiling_ghosts)
    if changed:
        app.state.show_tiling_ghosts = v

    imgui.separator()
    imgui.text(f"Points: {len(app.state.shapes)}")
    imgui.text(f"Selected: {len(app.selected_ids)}")
    edited = sum(1 for s in app.state.shapes if s.has_any_delta())
    if edited:
        imgui.text(f"Edited: {edited}")

    imgui.end()


def draw_properties_panel(app: App) -> None:
    """Selected point properties."""
    imgui.begin("Properties")

    sel = app.selected_shapes()
    if not sel:
        imgui.text_disabled("No point selected")
        imgui.end()
        return

    if len(sel) == 1:
        s = sel[0]
        imgui.text(f"Index: {s.index}")
        imgui.text(f"Type: {s.shape_type}")

        # ── Position ──────────────────────────────────────────────────
        eff_pos = list(s.position)
        changed, eff_pos = imgui.input_float2("Position", eff_pos)
        if changed:
            app.history.push(app.state.shapes)
            s.set_effective_position(eff_pos[0], eff_pos[1])

        dp = s.delta_position
        if dp != (0.0, 0.0):
            imgui.same_line()
            imgui.text_disabled(f"  Δ ({dp[0]:+.1f}, {dp[1]:+.1f})")

        # ── Size ──────────────────────────────────────────────────────
        eff_size = list(s.size)
        changed, eff_size = imgui.input_float2("Size", eff_size)
        if changed:
            app.history.push(app.state.shapes)
            s.set_effective_size(max(1.0, eff_size[0]), max(1.0, eff_size[1]))

        ds = s.delta_size
        if ds != (0.0, 0.0):
            imgui.same_line()
            imgui.text_disabled(f"  Δ ({ds[0]:+.1f}, {ds[1]:+.1f})")

        # ── Rotation ──────────────────────────────────────────────────
        rot_val = s.rotation % 360
        imgui.set_next_item_width(imgui.get_content_region_avail().x - 70)
        changed, rot = imgui.slider_float("##rot_slider", rot_val, 0.0, 360.0)
        if changed:
            app.history.push(app.state.shapes)
            s.set_effective_rotation(rot)
            rot_val = rot
        imgui.same_line()
        imgui.set_next_item_width(60)
        changed, rot = imgui.input_float("##rot_input", rot_val, 0.0, 0.0, "%.1f")
        if changed:
            app.history.push(app.state.shapes)
            s.set_effective_rotation(rot % 360)
        imgui.same_line()
        imgui.text("Rotation")

        if s.delta_rotation != 0.0:
            imgui.text_disabled(f"  Δ {s.delta_rotation:+.1f}°")

        # ── Color ─────────────────────────────────────────────────────
        col = [c / 255 for c in s.color]
        changed, col = imgui.color_edit4("Color", col)
        if changed:
            app.history.push(app.state.shapes)
            s.set_effective_color(tuple(int(c * 255) for c in col))  # type: ignore

        if s.override_color is not None:
            imgui.same_line()
            imgui.text_disabled("  (overridden)")

        imgui.separator()

        # ── Locked ────────────────────────────────────────────────────
        changed, locked = imgui.checkbox("Locked (prevent drag)", s.locked)
        if changed:
            s.locked = locked

        # ── Delta indicator + reset ───────────────────────────────────
        if s.has_any_delta():
            imgui.spacing()
            imgui.text_colored(imgui.ImVec4(1.0, 0.8, 0.2, 1.0), "* Point has manual edits")
            if imgui.button("Reset This Point"):
                app.history.push(app.state.shapes)
                s.reset_deltas()

    else:
        # ── Multi-select ──────────────────────────────────────────────
        imgui.text(f"{len(sel)} points selected")
        n_edited = sum(1 for s in sel if s.has_any_delta())
        if n_edited:
            imgui.text_colored(imgui.ImVec4(1.0, 0.8, 0.2, 1.0), f"* {n_edited} have manual edits")

        imgui.separator()

        # Bulk rotation
        rot_val = sel[0].rotation % 360
        imgui.set_next_item_width(imgui.get_content_region_avail().x - 70)
        changed, rot = imgui.slider_float("##bulkrot_slider", rot_val, 0.0, 360.0)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_rotation(rot)
            rot_val = rot
        imgui.same_line()
        imgui.set_next_item_width(60)
        changed, rot = imgui.input_float("##bulkrot_input", rot_val, 0.0, 0.0, "%.1f")
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_rotation(rot % 360)
        imgui.same_line()
        imgui.text("Rotation (all)")

        # Bulk color
        col = [c / 255 for c in sel[0].color]
        changed, col = imgui.color_edit4("Color (all)", col)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_color(tuple(int(c * 255) for c in col))  # type: ignore

        # Bulk size
        eff_size = list(sel[0].size)
        changed, eff_size = imgui.input_float2("Size (all)", eff_size)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_size((max(1.0, eff_size[0]), max(1.0, eff_size[1])))

        imgui.separator()

        # Bulk locked toggle
        all_locked = all(s.locked for s in sel)
        changed, locked = imgui.checkbox("Locked (all)", all_locked)
        if changed:
            for s in sel:
                s.locked = locked

        imgui.spacing()
        if imgui.button(f"Reset {len(sel)} Points", imgui.ImVec2(-1, 0)):
            app.reset_selected_deltas()

    imgui.end()


# ── File dialogs ──────────────────────────────────────────────────────────────

def _start_save_dialog(app: App) -> None:
    global _save_dialog
    _save_dialog = pfd.save_file("Save Project", os.getcwd(), ["JSON files", "*.json"])

def _start_load_dialog(app: App) -> None:
    global _load_dialog
    _load_dialog = pfd.open_file("Load Project", os.getcwd(), ["JSON files", "*.json"])

def _start_export_dialog(app: App) -> None:
    global _export_dialog
    default_path = os.path.join(os.getcwd(), "pattern.png")
    _export_dialog = pfd.save_file("Export Image", default_path, ["PNG files", "*.png"])

def _start_custom_img_dialog(app: App) -> None:
    global _custom_img_dialog
    _custom_img_dialog = pfd.open_file(
        "Select Custom Image", os.getcwd(),
        ["Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"],
    )


def _process_dialogs(app: App) -> None:
    global _save_dialog, _load_dialog, _export_dialog, _custom_img_dialog

    if _save_dialog is not None and _save_dialog.ready():
        path = _save_dialog.result()
        if path:
            if not path.lower().endswith(".json"):
                path += ".json"
            save_project(app.state, path)
        _save_dialog = None

    if _load_dialog is not None and _load_dialog.ready():
        result = _load_dialog.result()
        if result:
            path = result[0] if isinstance(result, list) else result
            app.state = load_project(path)
            app.selected_ids.clear()
            app.history.clear()
        _load_dialog = None

    if _export_dialog is not None and _export_dialog.ready():
        path = _export_dialog.result()
        if path:
            if not path.lower().endswith(".png"):
                path += ".png"
            export_pattern(app.state, path)
        _export_dialog = None

    if _custom_img_dialog is not None and _custom_img_dialog.ready():
        result = _custom_img_dialog.result()
        if result:
            path = result[0] if isinstance(result, list) else result
            app.state.default_custom_image_path = path
        _custom_img_dialog = None
