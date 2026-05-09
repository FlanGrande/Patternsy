"""ImGui UI panels: properties, pattern settings, canvas settings, toolbar."""

from __future__ import annotations

import os
from imgui_bundle import imgui, portable_file_dialogs as pfd

from patternsy_v2.app import App
from patternsy_v2.shapes.base import SHAPE_REGISTRY
from patternsy_v2.patterns.base import PATTERN_REGISTRY
from patternsy_v2.serialization import save_project, load_project
from patternsy_v2.export import export_pattern

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

    # Process dialogs
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

    changed, v = imgui.input_float("Default Rotation", app.state.default_shape_rotation, 1.0, 10.0)
    if changed:
        app.state.default_shape_rotation = v % 360

    # Default color
    col = [c / 255 for c in app.state.default_shape_color]
    changed, col = imgui.color_edit4("Shape Color", col)
    if changed:
        app.state.default_shape_color = tuple(int(c * 255) for c in col)  # type: ignore

    if app.state.default_shape_type == "custom":
        path_text = app.state.default_custom_image_path or "(none)"
        imgui.text(f"Image: {os.path.basename(path_text)}")
        if imgui.button("Browse Custom Image..."):
            _start_custom_img_dialog(app)

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
    imgui.text(f"Shapes: {len(app.state.shapes)}")
    imgui.text(f"Selected: {len(app.selected_ids)}")

    imgui.end()


def draw_properties_panel(app: App) -> None:
    """Selected shape properties."""
    imgui.begin("Properties")

    sel = app.selected_shapes()
    if not sel:
        imgui.text_disabled("No shape selected")
        imgui.end()
        return

    if len(sel) == 1:
        s = sel[0]
        imgui.text(f"ID: {s.id}")
        imgui.text(f"Type: {s.shape_type}")

        pos = list(s.position)
        changed, pos = imgui.input_float2("Position", pos)
        if changed:
            app.history.push(app.state.shapes)
            s.position = tuple(pos)

        size = list(s.size)
        changed, size = imgui.input_float2("Size", size)
        if changed:
            app.history.push(app.state.shapes)
            s.size = (max(1.0, size[0]), max(1.0, size[1]))

        changed, rot = imgui.slider_float("Rotation", s.rotation, 0.0, 360.0)
        if changed:
            app.history.push(app.state.shapes)
            s.rotation = rot

        col = [c / 255 for c in s.color]
        changed, col = imgui.color_edit4("Color", col)
        if changed:
            app.history.push(app.state.shapes)
            s.color = tuple(int(c * 255) for c in col)  # type: ignore

        changed, locked = imgui.checkbox("Locked", s.locked)
        if changed:
            s.locked = locked
    else:
        imgui.text(f"{len(sel)} shapes selected")

        # Bulk rotation
        changed, rot = imgui.slider_float("Rotation (all)", sel[0].rotation, 0.0, 360.0)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_rotation(rot)

        # Bulk color
        col = [c / 255 for c in sel[0].color]
        changed, col = imgui.color_edit4("Color (all)", col)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_color(tuple(int(c * 255) for c in col))  # type: ignore

        # Bulk size
        size = list(sel[0].size)
        changed, size = imgui.input_float2("Size (all)", size)
        if changed:
            app.history.push(app.state.shapes)
            app.set_selected_size((max(1.0, size[0]), max(1.0, size[1])))

    imgui.end()


# ── File dialogs (non-blocking via portable_file_dialogs) ───────────────────

def _start_save_dialog(app: App) -> None:
    global _save_dialog
    _save_dialog = pfd.save_file("Save Project", "", ["JSON files", "*.json"])

def _start_load_dialog(app: App) -> None:
    global _load_dialog
    _load_dialog = pfd.open_file("Load Project", "", ["JSON files", "*.json"])

def _start_export_dialog(app: App) -> None:
    global _export_dialog
    _export_dialog = pfd.save_file("Export Image", "pattern.png", ["PNG files", "*.png"])

def _start_custom_img_dialog(app: App) -> None:
    global _custom_img_dialog
    _custom_img_dialog = pfd.open_file(
        "Select Custom Image", "",
        ["Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"],
    )


def _process_dialogs(app: App) -> None:
    global _save_dialog, _load_dialog, _export_dialog, _custom_img_dialog

    if _save_dialog is not None and _save_dialog.ready():
        path = _save_dialog.result()
        if path:
            p = path if isinstance(path, str) else path
            if not p.lower().endswith(".json"):
                p += ".json"
            save_project(app.state, p)
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
            p = path if isinstance(path, str) else path
            if not p.lower().endswith(".png"):
                p += ".png"
            export_pattern(app.state, p)
        _export_dialog = None

    if _custom_img_dialog is not None and _custom_img_dialog.ready():
        result = _custom_img_dialog.result()
        if result:
            path = result[0] if isinstance(result, list) else result
            app.state.default_custom_image_path = path
        _custom_img_dialog = None
