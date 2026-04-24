#!/usr/bin/env python3

import os
import sys
import re
import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QComboBox, QPushButton, QFileDialog,
    QSlider, QLineEdit, QGroupBox, QGridLayout, QMessageBox,
    QScrollArea, QColorDialog, QToolButton, QSplitter, QFrame,
    QSizePolicy, QStatusBar, QProgressBar, QToolBar,
    QCheckBox
)
from PyQt6.QtGui import (
    QPixmap, QImage, QColor, QMouseEvent, QWheelEvent, QKeyEvent,
    QPainter, QIcon, QKeySequence, QPalette, QFont, QAction, QShortcut
)
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QTimer, QThread, QObject, pyqtSignal, QRunnable,
    QThreadPool, QMutex
)
from PIL import Image, ImageQt
from patternsy import create_pattern


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

class Theme:
    # Palette
    BG_APP        = "#1e1e24"
    BG_PANEL      = "#26262e"
    BG_SECTION    = "#2e2e38"
    BG_INPUT      = "#1a1a22"
    BG_INPUT_FOCUS= "#22222c"
    BG_HOVER      = "#35353f"
    BG_PREVIEW    = "#141418"

    ACCENT        = "#ff8800"
    ACCENT_HOVER  = "#ff9d2e"
    ACCENT_PRESS  = "#cc6d00"
    ACCENT_DIM    = "#7a4200"

    TEXT_PRIMARY  = "#f0f0f5"
    TEXT_SECONDARY= "#9090a0"
    TEXT_DISABLED = "#50505a"
    TEXT_ON_ACCENT= "#0a0a0e"

    BORDER        = "#3a3a48"
    BORDER_FOCUS  = "#ff8800"
    BORDER_ERROR  = "#cc3333"

    SUCCESS       = "#44cc88"
    ERROR         = "#cc3344"
    WARNING       = "#ddaa22"

    # Spacing
    S1 = 4
    S2 = 8
    S3 = 12
    S4 = 16
    S5 = 24

    # Radius
    R1 = 4
    R2 = 6
    R3 = 10

    # Font
    FONT_FAMILY   = "Inter, Segoe UI, Arial, sans-serif"
    FONT_SIZE_SM  = 11
    FONT_SIZE_MD  = 12
    FONT_SIZE_LG  = 13
    FONT_SIZE_H   = 13

    CONTROL_HEIGHT = 28


STYLESHEET = f"""
/* ── App Base ── */
QMainWindow, QWidget {{
    background-color: {Theme.BG_APP};
    color: {Theme.TEXT_PRIMARY};
    font-family: {Theme.FONT_FAMILY};
    font-size: {Theme.FONT_SIZE_MD}px;
}}

/* ── Scroll Area ── */
QScrollArea {{
    background: {Theme.BG_PANEL};
    border: none;
}}
QScrollBar:vertical {{
    background: {Theme.BG_APP};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {Theme.BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Theme.TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {Theme.BG_APP};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {Theme.BORDER};
    border-radius: 4px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {Theme.TEXT_SECONDARY};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Splitter ── */
QSplitter::handle {{
    background: {Theme.BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}

/* ── Group Box ── */
QGroupBox {{
    background: {Theme.BG_SECTION};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R2}px;
    margin-top: 18px;
    padding: {Theme.S3}px {Theme.S3}px {Theme.S3}px {Theme.S3}px;
    font-size: {Theme.FONT_SIZE_H}px;
    font-weight: bold;
    color: {Theme.TEXT_PRIMARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    left: 10px;
    background: {Theme.ACCENT};
    color: {Theme.TEXT_ON_ACCENT};
    border-radius: {Theme.R1}px;
    font-weight: bold;
    font-size: {Theme.FONT_SIZE_SM}px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* ── Labels ── */
QLabel {{
    color: {Theme.TEXT_SECONDARY};
    font-size: {Theme.FONT_SIZE_MD}px;
    background: transparent;
}}
QLabel[class="unit"] {{
    color: {Theme.TEXT_DISABLED};
    font-size: {Theme.FONT_SIZE_SM}px;
}}
QLabel[class="hint"] {{
    color: {Theme.TEXT_DISABLED};
    font-size: {Theme.FONT_SIZE_SM}px;
    font-style: italic;
}}
QLabel[class="error"] {{
    color: {Theme.ERROR};
    font-size: {Theme.FONT_SIZE_SM}px;
}}
QLabel[class="value-display"] {{
    color: {Theme.ACCENT};
    font-size: {Theme.FONT_SIZE_SM}px;
    font-weight: bold;
    min-width: 36px;
    qproperty-alignment: AlignRight;
}}

/* ── Line Edit ── */
QLineEdit {{
    background: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
    padding: 4px 8px;
    color: {Theme.TEXT_PRIMARY};
    font-size: {Theme.FONT_SIZE_MD}px;
    min-height: {Theme.CONTROL_HEIGHT}px;
    max-height: {Theme.CONTROL_HEIGHT}px;
    selection-background-color: {Theme.ACCENT_DIM};
}}
QLineEdit:focus {{
    border-color: {Theme.BORDER_FOCUS};
    background: {Theme.BG_INPUT_FOCUS};
}}
QLineEdit[state="error"] {{
    border-color: {Theme.BORDER_ERROR};
    background: #2a1a1a;
}}
QLineEdit:disabled {{
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BG_SECTION};
}}

/* ── Spin Box ── */
QSpinBox {{
    background: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
    padding: 4px 4px 4px 8px;
    color: {Theme.TEXT_PRIMARY};
    font-size: {Theme.FONT_SIZE_MD}px;
    min-height: {Theme.CONTROL_HEIGHT}px;
    max-height: {Theme.CONTROL_HEIGHT}px;
    selection-background-color: {Theme.ACCENT_DIM};
}}
QSpinBox:focus {{
    border-color: {Theme.BORDER_FOCUS};
    background: {Theme.BG_INPUT_FOCUS};
}}
QSpinBox:disabled {{
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BG_SECTION};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {Theme.BG_HOVER};
    border: none;
    width: 18px;
    border-radius: 2px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {Theme.ACCENT_DIM};
}}
QSpinBox::up-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid {Theme.TEXT_SECONDARY};
}}
QSpinBox::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {Theme.TEXT_SECONDARY};
}}

/* ── Combo Box ── */
QComboBox {{
    background: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
    padding: 4px 8px;
    color: {Theme.TEXT_PRIMARY};
    font-size: {Theme.FONT_SIZE_MD}px;
    min-height: {Theme.CONTROL_HEIGHT}px;
    max-height: {Theme.CONTROL_HEIGHT}px;
}}
QComboBox:focus {{
    border-color: {Theme.BORDER_FOCUS};
}}
QComboBox:hover {{
    background: {Theme.BG_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {Theme.ACCENT};
}}
QComboBox QAbstractItemView {{
    background: {Theme.BG_SECTION};
    border: 1px solid {Theme.BORDER_FOCUS};
    border-radius: {Theme.R1}px;
    color: {Theme.TEXT_PRIMARY};
    selection-background-color: {Theme.ACCENT_DIM};
    outline: none;
    padding: 2px;
}}

/* ── Slider ── */
QSlider::groove:horizontal {{
    background: {Theme.BG_INPUT};
    height: 4px;
    border-radius: 2px;
    border: 1px solid {Theme.BORDER};
}}
QSlider::handle:horizontal {{
    background: {Theme.ACCENT};
    border: none;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -6px 0;
}}
QSlider::handle:horizontal:hover {{
    background: {Theme.ACCENT_HOVER};
}}
QSlider::sub-page:horizontal {{
    background: {Theme.ACCENT_DIM};
    border-radius: 2px;
}}
QSlider:disabled {{
    opacity: 0.4;
}}

/* ── Buttons ── */
QPushButton {{
    background: {Theme.BG_HOVER};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
    padding: 5px 14px;
    color: {Theme.TEXT_PRIMARY};
    font-size: {Theme.FONT_SIZE_MD}px;
    min-height: {Theme.CONTROL_HEIGHT}px;
}}
QPushButton:hover {{
    background: {Theme.BG_SECTION};
    border-color: {Theme.TEXT_SECONDARY};
}}
QPushButton:pressed {{
    background: {Theme.BG_APP};
    border-color: {Theme.ACCENT};
}}
QPushButton:disabled {{
    color: {Theme.TEXT_DISABLED};
    border-color: {Theme.BG_SECTION};
    background: {Theme.BG_PANEL};
}}
QPushButton[class="primary"] {{
    background: {Theme.ACCENT};
    border-color: {Theme.ACCENT};
    color: {Theme.TEXT_ON_ACCENT};
    font-weight: bold;
    font-size: {Theme.FONT_SIZE_LG}px;
    min-height: 36px;
    border-radius: {Theme.R2}px;
}}
QPushButton[class="primary"]:hover {{
    background: {Theme.ACCENT_HOVER};
    border-color: {Theme.ACCENT_HOVER};
}}
QPushButton[class="primary"]:pressed {{
    background: {Theme.ACCENT_PRESS};
    border-color: {Theme.ACCENT_PRESS};
}}
QPushButton[class="primary"]:disabled {{
    background: {Theme.ACCENT_DIM};
    border-color: {Theme.ACCENT_DIM};
    color: #555;
}}
QPushButton[class="secondary"] {{
    background: transparent;
    border: 1px solid {Theme.BORDER};
    color: {Theme.TEXT_SECONDARY};
}}
QPushButton[class="secondary"]:hover {{
    border-color: {Theme.ACCENT};
    color: {Theme.ACCENT};
}}
QPushButton[class="color-swatch"] {{
    text-align: left;
    padding-left: 36px;
    border-radius: {Theme.R1}px;
    min-height: 32px;
}}

/* ── Tool Button ── */
QToolButton {{
    background: transparent;
    border: none;
    color: {Theme.TEXT_SECONDARY};
    border-radius: {Theme.R1}px;
    padding: 4px;
}}
QToolButton:hover {{
    background: {Theme.BG_HOVER};
    color: {Theme.TEXT_PRIMARY};
}}

/* ── Toolbar ── */
QToolBar {{
    background: {Theme.BG_PANEL};
    border-bottom: 1px solid {Theme.BORDER};
    spacing: 4px;
    padding: 4px 8px;
}}
QToolBar QToolButton {{
    min-width: 28px;
    min-height: 28px;
    border-radius: {Theme.R1}px;
    font-size: {Theme.FONT_SIZE_SM}px;
}}

/* ── Status Bar ── */
QStatusBar {{
    background: {Theme.BG_PANEL};
    border-top: 1px solid {Theme.BORDER};
    color: {Theme.TEXT_SECONDARY};
    font-size: {Theme.FONT_SIZE_SM}px;
    padding: 2px 8px;
}}
QStatusBar QLabel {{
    color: {Theme.TEXT_SECONDARY};
    font-size: {Theme.FONT_SIZE_SM}px;
}}

/* ── Progress Bar ── */
QProgressBar {{
    background: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
    height: 4px;
    text-align: center;
    max-height: 4px;
}}
QProgressBar::chunk {{
    background: {Theme.ACCENT};
    border-radius: {Theme.R1}px;
}}

/* ── Frame ── */
QFrame[class="separator"] {{
    background: {Theme.BORDER};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}
QFrame[class="color-preview"] {{
    border: 2px solid {Theme.BORDER};
    border-radius: {Theme.R1}px;
}}

/* ── Checkbox ── */
QCheckBox {{
    color: {Theme.TEXT_SECONDARY};
    spacing: 6px;
    font-size: {Theme.FONT_SIZE_MD}px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {Theme.BORDER};
    border-radius: 3px;
    background: {Theme.BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {Theme.ACCENT};
    border-color: {Theme.ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {Theme.ACCENT};
}}

/* ── Tooltip ── */
QToolTip {{
    background: {Theme.BG_SECTION};
    color: {Theme.TEXT_PRIMARY};
    border: 1px solid {Theme.BORDER_FOCUS};
    border-radius: {Theme.R1}px;
    padding: 4px 8px;
    font-size: {Theme.FONT_SIZE_SM}px;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# STATE MODEL
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PatternSettings:
    # Canvas
    width: int = 1024
    height: int = 1024
    rows: int = 8
    columns: int = 8

    # Shape
    shape_type: str = "circle"
    shape_width: int = 32
    shape_height: int = 32
    custom_image_path: str = ""

    # Pattern
    pattern_type: str = "offset_grid"
    diagonal_offset_x: int = 0

    # Transform
    base_rotation: float = 0.0
    scale_randomization: float = 0.0
    rotation_randomization: float = 0.0
    column_rotations: List[int] = field(default_factory=list)
    row_rotations: List[int] = field(default_factory=list)

    # Color
    bg_color: Tuple[int, int, int, int] = (0, 0, 0, 255)
    fg_color: Tuple[int, int, int, int] = (255, 136, 0, 255)

    # Output
    output_file: str = "pattern.png"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bg_color"] = list(self.bg_color)
        d["fg_color"] = list(self.fg_color)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PatternSettings":
        s = cls()
        s.width  = int(data.get("width",  s.width))
        s.height = int(data.get("height", s.height))
        s.rows    = int(data.get("rows",    s.rows))
        s.columns = int(data.get("columns", s.columns))
        s.shape_type   = str(data.get("shape_type",   s.shape_type))
        s.shape_width  = int(data.get("shape_width",  s.shape_width))
        s.shape_height = int(data.get("shape_height", s.shape_height))
        s.custom_image_path = str(data.get("custom_image_path", s.custom_image_path) or "")
        s.pattern_type       = str(data.get("pattern_type",       s.pattern_type))
        s.diagonal_offset_x  = int(data.get("diagonal_offset_x",  s.diagonal_offset_x))
        s.base_rotation       = float(data.get("base_rotation",       s.base_rotation))
        s.scale_randomization = float(data.get("scale_randomization", s.scale_randomization))
        s.rotation_randomization = float(data.get("rotation_randomization", s.rotation_randomization))
        s.column_rotations = list(data.get("column_rotations", s.column_rotations) or [])
        s.row_rotations    = list(data.get("row_rotations",    s.row_rotations) or [])
        bg = data.get("bg_color")
        if isinstance(bg, (list, tuple)) and len(bg) >= 3:
            s.bg_color = (int(bg[0]), int(bg[1]), int(bg[2]), int(bg[3]) if len(bg) > 3 else 255)
        fg = data.get("fg_color")
        if isinstance(fg, (list, tuple)) and len(fg) >= 3:
            s.fg_color = (int(fg[0]), int(fg[1]), int(fg[2]), int(fg[3]) if len(fg) > 3 else 255)
        s.output_file = str(data.get("output_file", s.output_file))
        return s

    def spacing_x(self) -> int:
        return max(1, self.width // max(1, self.columns))

    def spacing_y(self) -> int:
        return max(1, self.height // max(1, self.rows))


# ─────────────────────────────────────────────────────────────────────────────
# PREVIEW WORKER  (runs off UI thread)
# ─────────────────────────────────────────────────────────────────────────────

class PreviewWorkerSignals(QObject):
    finished = pyqtSignal(object, int)   # (QImage | None, request_id)
    error    = pyqtSignal(str, int)


class PreviewWorker(QRunnable):
    def __init__(self, settings: PatternSettings, preview_scale: float, request_id: int):
        super().__init__()
        self.settings     = settings
        self.preview_scale = preview_scale
        self.request_id   = request_id
        self.signals      = PreviewWorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        try:
            s = self.settings
            pw = max(64, int(s.width  * self.preview_scale))
            ph = max(64, int(s.height * self.preview_scale))
            psw = max(1, int(s.shape_width  * self.preview_scale))
            psh = max(1, int(s.shape_height * self.preview_scale))
            psx = pw // max(1, s.columns)
            psy = ph // max(1, s.rows)

            col_rot = s.column_rotations or [0] * s.columns
            row_rot = s.row_rotations    or [0] * s.rows

            img = create_pattern(
                width=pw,
                height=ph,
                shape_width=psw,
                shape_height=psh,
                spacing_x=psx,
                spacing_y=psy,
                pattern_type=s.pattern_type,
                shape_type=s.shape_type,
                custom_image_path=s.custom_image_path if s.shape_type == "custom" else None,
                bg_color=s.bg_color,
                fg_color=s.fg_color,
                scale_randomization=s.scale_randomization,
                base_rotation=s.base_rotation,
                rotation_randomization=s.rotation_randomization,
                output_file="",
                column_rotations=col_rot,
                row_rotations=row_rot,
                columns=s.columns,
                rows=s.rows,
                diagonal_offset_x=s.diagonal_offset_x,
                antialiasing=False,
                no_save=True,
            )

            # Convert PIL image -> QImage in-memory
            img_rgb = img.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimg = QImage(data, img_rgb.width, img_rgb.height, img_rgb.width * 3, QImage.Format.Format_RGB888).copy()
            self.signals.finished.emit(qimg, self.request_id)
        except Exception as e:
            self.signals.error.emit(str(e), self.request_id)


# ─────────────────────────────────────────────────────────────────────────────
# SLIDER + SPINBOX PAIR WIDGET
# ─────────────────────────────────────────────────────────────────────────────

class SliderSpinRow(QWidget):
    """Paired slider + spinbox that stay in sync, with optional value label."""
    valueChanged = pyqtSignal(float)

    def __init__(self, min_val: float, max_val: float, decimals: int = 0,
                 scale: float = 1.0, unit: str = "", parent=None):
        super().__init__(parent)
        self._scale    = scale      # internal int = external float * scale
        self._decimals = decimals
        self._min      = min_val
        self._max      = max_val
        self._updating = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Theme.S2)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * scale), int(max_val * scale))
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.spin = QSpinBox()
        self.spin.setRange(int(min_val), int(max_val))
        self.spin.setFixedWidth(64)
        if unit:
            self.spin.setSuffix(f" {unit}")

        layout.addWidget(self.slider)
        layout.addWidget(self.spin)

        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)

    def _on_slider(self, v):
        if self._updating: return
        self._updating = True
        external = v / self._scale
        self.spin.setValue(int(round(external)))
        self._updating = False
        self.valueChanged.emit(external)

    def _on_spin(self, v):
        if self._updating: return
        self._updating = True
        self.slider.setValue(int(v * self._scale))
        self._updating = False
        self.valueChanged.emit(float(v))

    def value(self) -> float:
        return self.spin.value() / 1.0

    def setValue(self, v: float):
        self._updating = True
        self.spin.setValue(int(round(v)))
        self.slider.setValue(int(round(v * self._scale)))
        self._updating = False

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.spin.setEnabled(enabled)


# ─────────────────────────────────────────────────────────────────────────────
# COLOR SWATCH BUTTON
# ─────────────────────────────────────────────────────────────────────────────

class ColorSwatchButton(QPushButton):
    """Button with an embedded color preview swatch."""
    def __init__(self, label: str, color: Tuple, parent=None):
        super().__init__(parent)
        self._color = color
        self._label = label
        self.setProperty("class", "color-swatch")
        self.setMinimumHeight(32)
        self._update_text()

    def setColor(self, color: Tuple):
        self._color = color
        self._update_text()
        self.update()

    def color(self) -> Tuple:
        return self._color

    def _update_text(self):
        r, g, b = self._color[0], self._color[1], self._color[2]
        self.setText(f"  {self._label}   #{r:02x}{g:02x}{b:02x}")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r, g, b = self._color[0], self._color[1], self._color[2]
        painter.setBrush(QColor(r, g, b))
        painter.setPen(QColor(Theme.BORDER))
        # Draw swatch on left side
        painter.drawRoundedRect(6, 6, 20, self.height() - 12, 3, 3)


# ─────────────────────────────────────────────────────────────────────────────
# COLLAPSIBLE SECTION
# ─────────────────────────────────────────────────────────────────────────────

class CollapsibleSection(QWidget):
    """A section that can be toggled open/closed."""
    toggled = pyqtSignal(bool)

    def __init__(self, title: str, collapsed: bool = False, parent=None):
        super().__init__(parent)
        self._collapsed = collapsed

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header button
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(not collapsed)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_SECTION};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.R1}px;
                text-align: left;
                padding: 6px 12px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: bold;
                font-size: {Theme.FONT_SIZE_H}px;
            }}
            QPushButton:hover {{
                background: {Theme.BG_HOVER};
                border-color: {Theme.ACCENT};
            }}
            QPushButton:checked {{
                border-color: {Theme.ACCENT};
            }}
        """)
        self._title = title
        self._update_label()
        self.toggle_btn.clicked.connect(self._on_toggle)

        # Content widget
        self.content = QWidget()
        self.content.setStyleSheet(f"""
            QWidget {{
                background: {Theme.BG_SECTION};
                border: 1px solid {Theme.BORDER};
                border-top: none;
                border-radius: 0 0 {Theme.R1}px {Theme.R1}px;
            }}
        """)
        self.content.setVisible(not collapsed)

        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)

    def _update_label(self):
        arrow = "▾" if not self._collapsed else "▸"
        self.toggle_btn.setText(f"  {arrow}  {self._title}")

    def _on_toggle(self, checked: bool):
        self._collapsed = not checked
        self.content.setVisible(checked)
        self._update_label()
        self.toggled.emit(checked)

    def setLayout(self, layout):
        self.content.setLayout(layout)


# ─────────────────────────────────────────────────────────────────────────────
# ZOOMABLE PREVIEW LABEL
# ─────────────────────────────────────────────────────────────────────────────

class ZoomablePreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"background-color: {Theme.BG_PREVIEW}; border: none;")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.original_pixmap: Optional[QPixmap] = None
        self.zoom_factor   = 1.0
        self.pan_position  = QPoint(0, 0)
        self._last_mouse   = QPoint(0, 0)
        self._panning      = False

        # Checkerboard tile for transparency hint
        self._checker = self._make_checker(16)

    def _make_checker(self, tile: int) -> QPixmap:
        pm = QPixmap(tile * 2, tile * 2)
        pm.fill(QColor("#1a1a22"))
        p = QPainter(pm)
        p.fillRect(0, 0, tile, tile, QColor("#222230"))
        p.fillRect(tile, tile, tile, tile, QColor("#222230"))
        p.end()
        return pm

    def set_pixmap(self, pixmap: QPixmap):
        reset = (self.original_pixmap is None or
                 self.original_pixmap.size() != pixmap.size())
        self.original_pixmap = pixmap
        if reset:
            self.zoom_factor  = 1.0
            self.pan_position = QPoint(0, 0)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Draw checker background
        p.drawTiledPixmap(self.rect(), self._checker)

        if not self.original_pixmap:
            p.setPen(QColor(Theme.TEXT_DISABLED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Generating preview…")
            return

        sw = int(self.original_pixmap.width()  * self.zoom_factor)
        sh = int(self.original_pixmap.height() * self.zoom_factor)
        scaled = self.original_pixmap.scaled(sw, sh,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
        cx = (self.width()  - scaled.width())  // 2 + self.pan_position.x()
        cy = (self.height() - scaled.height()) // 2 + self.pan_position.y()
        p.drawPixmap(cx, cy, scaled)

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = 0.12 if delta > 0 else -0.12
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor + factor))
        self.update()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning    = True
            self._last_mouse = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.position().toPoint() - self._last_mouse
            self.pan_position += delta
            self._last_mouse   = event.position().toPoint()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_factor = min(10.0, self.zoom_factor + 0.15)
            self.update()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_factor = max(0.1, self.zoom_factor - 0.15)
            self.update()
        elif event.key() == Qt.Key.Key_R:
            self.zoom_factor  = 1.0
            self.pan_position = QPoint(0, 0)
            self.update()
        else:
            super().keyPressEvent(event)

    def zoom_in(self):
        self.zoom_factor = min(10.0, self.zoom_factor + 0.2)
        self.update()

    def zoom_out(self):
        self.zoom_factor = max(0.1, self.zoom_factor - 0.2)
        self.update()

    def reset_view(self):
        self.zoom_factor  = 1.0
        self.pan_position = QPoint(0, 0)
        self.update()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────

class PatternGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings       = PatternSettings()
        self._dirty         = False
        self._preview_scale = 0.25
        self._request_id    = 0
        self._request_mutex = QMutex()
        self._pool          = QThreadPool.globalInstance()

        self.setWindowTitle("Patternsy")
        self.setMinimumSize(960, 640)
        self.resize(1400, 860)

        self._init_ui()
        self._apply_model_to_ui()
        self._schedule_preview()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _evaluate_expression(self, expr: str) -> Optional[int]:
        try:
            expr = str(expr).strip()
            if not expr: return None
            if expr.startswith('-'): return None
            if not re.match(r'^[0-9+\-*/().\s]+$', expr): return None
            if '/0' in expr.replace(' ', ''): return None
            result = eval(expr, {"__builtins__": {}}, {})
            if isinstance(result, float):
                if not result.__class__.__name__ == 'float': return None
                result = int(round(result))
            else:
                result = int(result)
            return max(1, min(result, 16384))
        except Exception:
            return None

    def _hex_color(self, rgba: Tuple) -> str:
        return f"#{rgba[0]:02x}{rgba[1]:02x}{rgba[2]:02x}"

    def _make_separator(self) -> QFrame:
        f = QFrame()
        f.setProperty("class", "separator")
        f.setFrameShape(QFrame.Shape.HLine)
        return f

    # ── UI Construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        self._build_toolbar()
        self._build_statusbar()

        # Root splitter
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        root_layout.addWidget(self.splitter)

        # Left: controls pane
        self.splitter.addWidget(self._build_controls_pane())
        # Right: preview pane
        self.splitter.addWidget(self._build_preview_pane())

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([380, 1020])

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.generate_pattern)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_settings)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.load_settings)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.preview_label.reset_view)

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        self.generate_action = QAction("⚙ Generate", self)
        self.generate_action.setToolTip("Generate full-resolution pattern  (Ctrl+G)")
        self.generate_action.triggered.connect(self.generate_pattern)
        tb.addAction(self.generate_action)

        tb.addSeparator()

        save_action = QAction("↑ Save Settings", self)
        save_action.setToolTip("Save settings to JSON  (Ctrl+S)")
        save_action.triggered.connect(self.save_settings)
        tb.addAction(save_action)

        load_action = QAction("↓ Load Settings", self)
        load_action.setToolTip("Load settings from JSON  (Ctrl+O)")
        load_action.triggered.connect(self.load_settings)
        tb.addAction(load_action)

        tb.addSeparator()

        zoom_in_action = QAction("＋ Zoom", self)
        zoom_in_action.triggered.connect(lambda: self.preview_label.zoom_in())
        tb.addAction(zoom_in_action)

        zoom_out_action = QAction("－ Zoom", self)
        zoom_out_action.triggered.connect(lambda: self.preview_label.zoom_out())
        tb.addAction(zoom_out_action)

        reset_view_action = QAction("⌖ Reset View", self)
        reset_view_action.setToolTip("Reset preview zoom & pan  (Ctrl+R)")
        reset_view_action.triggered.connect(lambda: self.preview_label.reset_view())
        tb.addAction(reset_view_action)

        # Dirty indicator (right-aligned via spacer)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)

        self.dirty_label = QLabel()
        self.dirty_label.setStyleSheet(f"color: {Theme.WARNING}; font-size: 11px; padding-right: 8px;")
        tb.addWidget(self.dirty_label)

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.dim_label = QLabel()
        self.dim_label.setStyleSheet(f"color: {Theme.TEXT_DISABLED}; padding-right: 8px;")
        self.status_bar.addPermanentWidget(self.dim_label)

    def _build_controls_pane(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setMinimumWidth(340)
        self._scroll.setMaximumWidth(480)

        container = QWidget()
        container.setStyleSheet(f"background: {Theme.BG_PANEL};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(Theme.S3, Theme.S3, Theme.S3, Theme.S3)
        layout.setSpacing(Theme.S2)

        layout.addWidget(self._build_canvas_section())
        layout.addWidget(self._build_pattern_section())
        layout.addWidget(self._build_shape_section())
        layout.addWidget(self._build_transform_section())
        layout.addWidget(self._build_advanced_section())
        layout.addWidget(self._build_color_section())
        layout.addWidget(self._build_output_section())
        layout.addStretch()

        # ── Action buttons (sticky bottom) ──
        action_bar = QWidget()
        action_bar.setStyleSheet(f"""
            QWidget {{
                background: {Theme.BG_PANEL};
                border-top: 1px solid {Theme.BORDER};
            }}
        """)
        ab_layout = QVBoxLayout(action_bar)
        ab_layout.setContentsMargins(Theme.S3, Theme.S3, Theme.S3, Theme.S3)
        ab_layout.setSpacing(Theme.S2)

        self.generate_btn = QPushButton("⚙  Generate Pattern")
        self.generate_btn.setProperty("class", "primary")
        self.generate_btn.setToolTip("Generate full-resolution pattern  (Ctrl+G)")
        self.generate_btn.clicked.connect(self.generate_pattern)
        ab_layout.addWidget(self.generate_btn)

        file_row = QHBoxLayout()
        file_row.setSpacing(Theme.S2)
        self.save_btn = QPushButton("↑ Save")
        self.save_btn.setProperty("class", "secondary")
        self.save_btn.setToolTip("Save settings to JSON  (Ctrl+S)")
        self.save_btn.clicked.connect(self.save_settings)

        self.load_btn = QPushButton("↓ Load")
        self.load_btn.setProperty("class", "secondary")
        self.load_btn.setToolTip("Load settings from JSON  (Ctrl+O)")
        self.load_btn.clicked.connect(self.load_settings)

        file_row.addWidget(self.save_btn)
        file_row.addWidget(self.load_btn)
        ab_layout.addLayout(file_row)

        # Wrap controls in a vertical layout
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: {Theme.BG_PANEL};")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(0)
        wl.addWidget(container)
        wl.addWidget(action_bar)

        self._scroll.setWidget(wrapper)
        return self._scroll

    # ── Section builders ──────────────────────────────────────────────────────

    def _section(self, title: str) -> Tuple[QGroupBox, QGridLayout]:
        g = QGroupBox(title)
        layout = QGridLayout(g)
        layout.setContentsMargins(Theme.S3, Theme.S3+4, Theme.S3, Theme.S3)
        layout.setSpacing(Theme.S2)
        layout.setColumnMinimumWidth(0, 110)
        layout.setColumnStretch(1, 1)
        return g, layout

    def _label(self, text: str, hint: str = "") -> QLabel:
        lbl = QLabel(text)
        if hint:
            lbl.setToolTip(hint)
        return lbl

    def _build_canvas_section(self) -> QGroupBox:
        g, l = self._section("Canvas")

        l.addWidget(self._label("Width", "Output width in pixels"), 0, 0)
        self.width_edit = QLineEdit()
        self.width_edit.setToolTip("Pixels or math expression (e.g. 8*128)")
        self.width_edit.editingFinished.connect(self._on_dimension_changed)
        self.width_edit.textChanged.connect(lambda: self._validate_dimension(self.width_edit))
        l.addWidget(self.width_edit, 0, 1)
        self.width_err = QLabel("")
        self.width_err.setProperty("class", "error")
        self.width_err.setVisible(False)
        l.addWidget(self.width_err, 1, 1)

        l.addWidget(self._label("Height", "Output height in pixels"), 2, 0)
        self.height_edit = QLineEdit()
        self.height_edit.setToolTip("Pixels or math expression (e.g. 8*128)")
        self.height_edit.editingFinished.connect(self._on_dimension_changed)
        self.height_edit.textChanged.connect(lambda: self._validate_dimension(self.height_edit))
        l.addWidget(self.height_edit, 2, 1)
        self.height_err = QLabel("")
        self.height_err.setProperty("class", "error")
        self.height_err.setVisible(False)
        l.addWidget(self.height_err, 3, 1)

        l.addWidget(self._make_separator(), 4, 0, 1, 2)

        l.addWidget(self._label("Columns"), 5, 0)
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 500)
        self.columns_spin.valueChanged.connect(self._on_columns_changed)
        l.addWidget(self.columns_spin, 5, 1)

        l.addWidget(self._label("Rows"), 6, 0)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 500)
        self.rows_spin.valueChanged.connect(self._on_rows_changed)
        l.addWidget(self.rows_spin, 6, 1)

        return g

    def _build_pattern_section(self) -> QGroupBox:
        g, l = self._section("Pattern")

        l.addWidget(self._label("Type"), 0, 0)
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["grid", "offset_grid", "diagonal_grid", "random", "spiral"])
        self.pattern_combo.currentTextChanged.connect(self._on_pattern_changed)
        l.addWidget(self.pattern_combo, 0, 1)

        # Contextual: diagonal offset (only for diagonal_grid)
        self.diag_label = self._label("Diag. Offset X", "X offset per row — visible only for diagonal_grid")
        self.diag_spin  = QSpinBox()
        self.diag_spin.setRange(-4096, 4096)
        self.diag_spin.setSuffix(" px")
        self.diag_spin.valueChanged.connect(self._mark_dirty_and_preview)
        l.addWidget(self.diag_label, 1, 0)
        l.addWidget(self.diag_spin, 1, 1)

        return g

    def _build_shape_section(self) -> QGroupBox:
        g, l = self._section("Shape")

        l.addWidget(self._label("Type"), 0, 0)
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["circle", "square", "triangle", "star", "custom"])
        self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
        l.addWidget(self.shape_combo, 0, 1)

        l.addWidget(self._label("Width", "Shape width in pixels"), 1, 0)
        self.shape_width_spin = QSpinBox()
        self.shape_width_spin.setRange(1, 1024)
        self.shape_width_spin.setSuffix(" px")
        self.shape_width_spin.valueChanged.connect(self._mark_dirty_and_preview)
        l.addWidget(self.shape_width_spin, 1, 1)

        l.addWidget(self._label("Height", "Shape height in pixels"), 2, 0)
        self.shape_height_spin = QSpinBox()
        self.shape_height_spin.setRange(1, 1024)
        self.shape_height_spin.setSuffix(" px")
        self.shape_height_spin.valueChanged.connect(self._mark_dirty_and_preview)
        l.addWidget(self.shape_height_spin, 2, 1)

        # Contextual: custom image (only for custom shape type)
        self.custom_img_row = QWidget()
        ci_layout = QHBoxLayout(self.custom_img_row)
        ci_layout.setContentsMargins(0, 0, 0, 0)
        ci_layout.setSpacing(Theme.S2)
        self.custom_img_btn = QPushButton("Choose Image…")
        self.custom_img_btn.setProperty("class", "secondary")
        self.custom_img_btn.clicked.connect(self._select_custom_image)
        self.custom_img_label = QLabel("No image")
        self.custom_img_label.setProperty("class", "hint")
        self.custom_img_label.setWordWrap(True)
        ci_layout.addWidget(self.custom_img_btn)
        ci_layout.addWidget(self.custom_img_label, 1)
        l.addWidget(self.custom_img_row, 3, 0, 1, 2)

        return g

    def _build_transform_section(self) -> QGroupBox:
        g, l = self._section("Transform")

        l.addWidget(self._label("Base Rotation", "Starting rotation for all shapes"), 0, 0)
        self.rotation_row = SliderSpinRow(0, 360, unit="°")
        self.rotation_row.valueChanged.connect(lambda v: self._mark_dirty_and_preview())
        l.addWidget(self.rotation_row, 0, 1)

        l.addWidget(self._label("Scale Random", "Random variation in shape size (0–100%)"), 1, 0)
        self.scale_random_row = SliderSpinRow(0, 100, unit="%")
        self.scale_random_row.valueChanged.connect(lambda v: self._mark_dirty_and_preview())
        l.addWidget(self.scale_random_row, 1, 1)

        l.addWidget(self._label("Rot. Random", "Random rotation variation (0–100%)"), 2, 0)
        self.rotation_random_row = SliderSpinRow(0, 100, unit="%")
        self.rotation_random_row.valueChanged.connect(lambda v: self._mark_dirty_and_preview())
        l.addWidget(self.rotation_random_row, 2, 1)

        return g

    def _build_advanced_section(self) -> QWidget:
        """Collapsible per-column and per-row rotation spinboxes."""
        wrapper = QWidget()
        wrapper.setStyleSheet(f"background: transparent;")
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(2)

        # Column rotations collapsible
        self.col_section = CollapsibleSection("Column Rotations", collapsed=True)
        col_inner = QGridLayout()
        col_inner.setContentsMargins(Theme.S3, Theme.S3, Theme.S3, Theme.S3)
        col_inner.setSpacing(Theme.S1)
        self.col_section.setLayout(col_inner)
        self.col_rot_layout = col_inner
        self.column_rotation_spins = []

        # Row rotations collapsible
        self.row_section = CollapsibleSection("Row Rotations", collapsed=True)
        row_inner = QGridLayout()
        row_inner.setContentsMargins(Theme.S3, Theme.S3, Theme.S3, Theme.S3)
        row_inner.setSpacing(Theme.S1)
        self.row_section.setLayout(row_inner)
        self.row_rot_layout = row_inner
        self.row_rotation_spins = []

        wl.addWidget(self.col_section)
        wl.addWidget(self.row_section)
        return wrapper

    def _build_color_section(self) -> QGroupBox:
        g, l = self._section("Colors")

        self.bg_color_btn = ColorSwatchButton("Background", self.settings.bg_color)
        self.bg_color_btn.clicked.connect(self._select_bg_color)
        l.addWidget(self.bg_color_btn, 0, 0, 1, 2)

        self.fg_color_btn = ColorSwatchButton("Foreground", self.settings.fg_color)
        self.fg_color_btn.clicked.connect(self._select_fg_color)
        l.addWidget(self.fg_color_btn, 1, 0, 1, 2)

        return g

    def _build_output_section(self) -> QGroupBox:
        g, l = self._section("Output")

        l.addWidget(self._label("Filename"), 0, 0)
        self.output_edit = QLineEdit()
        self.output_edit.setToolTip("Output PNG filename")
        self.output_edit.textChanged.connect(self._mark_dirty)
        l.addWidget(self.output_edit, 0, 1)

        return g

    def _build_preview_pane(self) -> QWidget:
        pane = QWidget()
        pane.setStyleSheet(f"background: {Theme.BG_PREVIEW};")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Preview header bar
        header = QWidget()
        header.setStyleSheet(f"background: {Theme.BG_PANEL}; border-bottom: 1px solid {Theme.BORDER};")
        header.setFixedHeight(32)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(Theme.S3, 0, Theme.S3, 0)
        hl.setSpacing(Theme.S2)

        preview_title = QLabel("Preview")
        preview_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        hl.addWidget(preview_title)
        hl.addStretch()

        hint = QLabel("Scroll: zoom   Drag: pan   R: reset   Ctrl+R: reset")
        hint.setStyleSheet(f"color: {Theme.TEXT_DISABLED}; font-size: 10px;")
        hl.addWidget(hint)

        layout.addWidget(header)

        self.preview_label = ZoomablePreviewLabel()
        layout.addWidget(self.preview_label, 1)

        return pane

    # ── Model <-> UI sync ─────────────────────────────────────────────────────

    def _apply_model_to_ui(self):
        """Push PatternSettings into all UI widgets (no signals triggered for preview)."""
        s = self.settings

        # Canvas
        self.width_edit.setText(str(s.width))
        self.height_edit.setText(str(s.height))
        self.columns_spin.blockSignals(True)
        self.rows_spin.blockSignals(True)
        self.columns_spin.setValue(s.columns)
        self.rows_spin.setValue(s.rows)
        self.columns_spin.blockSignals(False)
        self.rows_spin.blockSignals(False)

        # Pattern
        self.pattern_combo.blockSignals(True)
        self.pattern_combo.setCurrentText(s.pattern_type)
        self.pattern_combo.blockSignals(False)
        self.diag_spin.blockSignals(True)
        self.diag_spin.setValue(s.diagonal_offset_x)
        self.diag_spin.blockSignals(False)
        self._update_pattern_contextual()

        # Shape
        self.shape_combo.blockSignals(True)
        self.shape_combo.setCurrentText(s.shape_type)
        self.shape_combo.blockSignals(False)
        self.shape_width_spin.blockSignals(True)
        self.shape_height_spin.blockSignals(True)
        self.shape_width_spin.setValue(s.shape_width)
        self.shape_height_spin.setValue(s.shape_height)
        self.shape_width_spin.blockSignals(False)
        self.shape_height_spin.blockSignals(False)
        self._update_shape_contextual()

        # Transform
        self.rotation_row.setValue(s.base_rotation)
        self.scale_random_row.setValue(s.scale_randomization * 100)
        self.rotation_random_row.setValue(s.rotation_randomization * 100)

        # Colors
        self.bg_color_btn.setColor(s.bg_color)
        self.fg_color_btn.setColor(s.fg_color)

        # Output
        self.output_edit.setText(s.output_file)

        # Rotation grids
        self._rebuild_column_rotation_controls()
        self._rebuild_row_rotation_controls()

        # Status
        self._update_dim_label()

    def _read_ui_to_model(self):
        """Pull all UI values into PatternSettings. Returns True if valid."""
        s = self.settings

        w = self._evaluate_expression(self.width_edit.text())
        h = self._evaluate_expression(self.height_edit.text())
        if w is None or h is None:
            return False

        s.width   = w
        s.height  = h
        s.columns = self.columns_spin.value()
        s.rows    = self.rows_spin.value()

        s.pattern_type      = self.pattern_combo.currentText()
        s.diagonal_offset_x = self.diag_spin.value()

        s.shape_type   = self.shape_combo.currentText()
        s.shape_width  = self.shape_width_spin.value()
        s.shape_height = self.shape_height_spin.value()

        s.base_rotation          = self.rotation_row.value()
        s.scale_randomization    = self.scale_random_row.value() / 100.0
        s.rotation_randomization = self.rotation_random_row.value() / 100.0

        if self.column_rotation_spins:
            s.column_rotations = [sp.value() for sp in self.column_rotation_spins]
        if self.row_rotation_spins:
            s.row_rotations = [sp.value() for sp in self.row_rotation_spins]

        s.output_file = self.output_edit.text() or "pattern.png"
        return True

    # ── Contextual visibility ─────────────────────────────────────────────────

    def _update_pattern_contextual(self):
        is_diag = self.pattern_combo.currentText() == "diagonal_grid"
        self.diag_label.setVisible(is_diag)
        self.diag_spin.setVisible(is_diag)

    def _update_shape_contextual(self):
        is_custom = self.shape_combo.currentText() == "custom"
        self.custom_img_row.setVisible(is_custom)
        if is_custom and self.settings.custom_image_path:
            name = os.path.basename(self.settings.custom_image_path)
            self.custom_img_label.setText(name)
        elif not is_custom:
            pass  # keep label as-is; row hidden

    # ── Event handlers ────────────────────────────────────────────────────────

    def _mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.dirty_label.setText("● Unsaved changes")

    def _mark_dirty_and_preview(self):
        self._mark_dirty()
        self._schedule_preview()

    def _on_dimension_changed(self):
        w = self._evaluate_expression(self.width_edit.text())
        h = self._evaluate_expression(self.height_edit.text())
        if w is not None:
            self.settings.width = w
            self.width_edit.setText(str(w))
        if h is not None:
            self.settings.height = h
            self.height_edit.setText(str(h))
        self._update_dim_label()
        self._mark_dirty_and_preview()

    def _validate_dimension(self, edit: QLineEdit):
        text = edit.text()
        valid = self._evaluate_expression(text) is not None
        edit.setProperty("state", "" if valid else "error")
        edit.style().unpolish(edit)
        edit.style().polish(edit)

    def _on_columns_changed(self):
        self.settings.columns = self.columns_spin.value()
        self._rebuild_column_rotation_controls()
        self._update_dim_label()
        self._mark_dirty_and_preview()

    def _on_rows_changed(self):
        self.settings.rows = self.rows_spin.value()
        self._rebuild_row_rotation_controls()
        self._update_dim_label()
        self._mark_dirty_and_preview()

    def _on_pattern_changed(self, text: str):
        self.settings.pattern_type = text
        self._update_pattern_contextual()
        self._mark_dirty_and_preview()

    def _on_shape_changed(self, text: str):
        self.settings.shape_type = text
        self._update_shape_contextual()
        if text == "custom" and not self.settings.custom_image_path:
            self._select_custom_image()
        else:
            self._mark_dirty_and_preview()

    def _select_bg_color(self):
        c = self.settings.bg_color
        color = QColorDialog.getColor(QColor(c[0], c[1], c[2]), self, "Background Color")
        if color.isValid():
            self.settings.bg_color = (color.red(), color.green(), color.blue(), 255)
            self.bg_color_btn.setColor(self.settings.bg_color)
            self._mark_dirty_and_preview()

    def _select_fg_color(self):
        c = self.settings.fg_color
        color = QColorDialog.getColor(QColor(c[0], c[1], c[2]), self, "Foreground Color")
        if color.isValid():
            self.settings.fg_color = (color.red(), color.green(), color.blue(), 255)
            self.fg_color_btn.setColor(self.settings.fg_color)
            self._mark_dirty_and_preview()

    def _select_custom_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Custom Image", "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All files (*.*)"
        )
        if path:
            self.settings.custom_image_path = path
            self.custom_img_label.setText(os.path.basename(path))
            self.shape_combo.setCurrentText("custom")
            self._mark_dirty_and_preview()

    def _update_dim_label(self):
        s = self.settings
        self.dim_label.setText(f"{s.width} × {s.height}  |  {s.columns} col × {s.rows} row")

    # ── Per-column / per-row rotation grids ───────────────────────────────────

    def _rebuild_column_rotation_controls(self):
        while self.col_rot_layout.count():
            item = self.col_rot_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self.column_rotation_spins = []
        vals = self.settings.column_rotations or [0] * self.settings.columns
        for i in range(self.settings.columns):
            lbl = QLabel(f"C{i}:")
            lbl.setStyleSheet(f"color: {Theme.TEXT_DISABLED}; font-size: 10px;")
            spin = QSpinBox()
            spin.setRange(0, 360)
            spin.setSuffix("°")
            spin.setFixedWidth(72)
            spin.setValue(vals[i] if i < len(vals) else 0)
            spin.valueChanged.connect(self._mark_dirty_and_preview)
            row, col = divmod(i, 3)
            self.col_rot_layout.addWidget(lbl,  row, col * 2)
            self.col_rot_layout.addWidget(spin, row, col * 2 + 1)
            self.column_rotation_spins.append(spin)
        self.settings.column_rotations = [sp.value() for sp in self.column_rotation_spins]

    def _rebuild_row_rotation_controls(self):
        while self.row_rot_layout.count():
            item = self.row_rot_layout.takeAt(0)
            w = item.widget()
            if w: w.deleteLater()
        self.row_rotation_spins = []
        vals = self.settings.row_rotations or [0] * self.settings.rows
        for i in range(self.settings.rows):
            lbl = QLabel(f"R{i}:")
            lbl.setStyleSheet(f"color: {Theme.TEXT_DISABLED}; font-size: 10px;")
            spin = QSpinBox()
            spin.setRange(0, 360)
            spin.setSuffix("°")
            spin.setFixedWidth(72)
            spin.setValue(vals[i] if i < len(vals) else 0)
            spin.valueChanged.connect(self._mark_dirty_and_preview)
            row, col = divmod(i, 3)
            self.row_rot_layout.addWidget(lbl,  row, col * 2)
            self.row_rot_layout.addWidget(spin, row, col * 2 + 1)
            self.row_rotation_spins.append(spin)
        self.settings.row_rotations = [sp.value() for sp in self.row_rotation_spins]

    # ── Preview ───────────────────────────────────────────────────────────────

    def _schedule_preview(self):
        """Debounce: restart a 140ms timer on each call, then trigger render."""
        if not hasattr(self, "_preview_timer"):
            self._preview_timer = QTimer(self)
            self._preview_timer.setSingleShot(True)
            self._preview_timer.timeout.connect(self._launch_preview)
        self._preview_timer.start(140)

    def _launch_preview(self):
        if not self._read_ui_to_model():
            return

        self._request_mutex.lock()
        self._request_id += 1
        rid = self._request_id
        self._request_mutex.unlock()

        import copy
        snap = copy.deepcopy(self.settings)

        worker = PreviewWorker(snap, self._preview_scale, rid)
        worker.signals.finished.connect(self._on_preview_done)
        worker.signals.error.connect(self._on_preview_error)
        self._pool.start(worker)
        self.status_label.setText("Updating preview…")
        self.progress_bar.setVisible(True)

    def _on_preview_done(self, qimg: QImage, rid: int):
        self._request_mutex.lock()
        latest = self._request_id
        self._request_mutex.unlock()
        self.progress_bar.setVisible(False)
        if rid != latest:
            return  # stale result — discard
        pixmap = QPixmap.fromImage(qimg)
        self.preview_label.set_pixmap(pixmap)
        self.status_label.setText("Ready")

    def _on_preview_error(self, msg: str, rid: int):
        self._request_mutex.lock()
        latest = self._request_id
        self._request_mutex.unlock()
        self.progress_bar.setVisible(False)
        if rid != latest:
            return
        self.status_label.setText(f"Preview error: {msg}")

    # ── Generate ──────────────────────────────────────────────────────────────

    def generate_pattern(self):
        if not self._read_ui_to_model():
            self.status_label.setText("Fix invalid values before generating.")
            return

        s = self.settings
        output_file = s.output_file or "pattern.png"
        if not output_file.lower().endswith(".png"):
            output_file += ".png"

        self.generate_btn.setEnabled(False)
        self.generate_action.setEnabled(False)
        self.status_label.setText(f"Generating {s.width}×{s.height} pattern…")
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

        try:
            col_rot = s.column_rotations or [0] * s.columns
            row_rot = s.row_rotations    or [0] * s.rows

            create_pattern(
                width=s.width,
                height=s.height,
                shape_width=s.shape_width,
                shape_height=s.shape_height,
                spacing_x=s.spacing_x(),
                spacing_y=s.spacing_y(),
                pattern_type=s.pattern_type,
                shape_type=s.shape_type,
                custom_image_path=s.custom_image_path if s.shape_type == "custom" else None,
                bg_color=s.bg_color,
                fg_color=s.fg_color,
                scale_randomization=s.scale_randomization,
                base_rotation=s.base_rotation,
                rotation_randomization=s.rotation_randomization,
                output_file=output_file,
                column_rotations=col_rot,
                row_rotations=row_rot,
                columns=s.columns,
                rows=s.rows,
                diagonal_offset_x=s.diagonal_offset_x,
            )
            self.status_label.setText(f"Saved → {output_file}")
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", str(e))
            self.status_label.setText("Generation failed.")
        finally:
            self.generate_btn.setEnabled(True)
            self.generate_action.setEnabled(True)
            self.progress_bar.setVisible(False)

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save_settings(self):
        if not self._read_ui_to_model():
            self.status_label.setText("Fix invalid values before saving.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Settings", "", "JSON files (*.json);;All files (*.*)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            self._dirty = False
            self.dirty_label.setText("")
            self.status_label.setText(f"Settings saved → {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def load_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Settings", "", "JSON files (*.json);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.settings = PatternSettings.from_dict(data)
            self._apply_model_to_ui()
            self._dirty = False
            self.dirty_label.setText("")
            self.status_label.setText(f"Settings loaded ← {os.path.basename(path)}")
            self._schedule_preview()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    # ── Close guard ───────────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved settings. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        self._pool.waitForDone(1000)
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # HiDPI (AA_UseHighDpiPixmaps removed in Qt6 — handled automatically)
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    window = PatternGeneratorApp()
    window.show()
    sys.exit(app.exec())
