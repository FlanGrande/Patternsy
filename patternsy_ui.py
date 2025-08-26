#!/usr/bin/env python3

import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QSpinBox, QComboBox, QPushButton, QFileDialog, 
                            QSlider, QLineEdit, QGroupBox, QGridLayout, QMessageBox,
                            QScrollArea, QColorDialog, QToolButton)
from PyQt6.QtGui import QPixmap, QImage, QColor, QMouseEvent, QWheelEvent, QKeyEvent, QPainter, QIcon
from PyQt6.QtCore import Qt, QPoint, QSize
from PIL import Image, ImageQt
import time
import re
from patternsy import create_pattern

class ZoomablePreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(600, 600)
        self.setStyleSheet("background-color: lightgrey;")
        
        # Pan and zoom attributes
        self.original_pixmap = None
        self.zoom_factor = 1.0
        self.pan_position = QPoint(0, 0)
        self.last_mouse_position = QPoint(0, 0)
        self.is_panning = False
        
        # Enable mouse tracking for panning
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def set_pixmap(self, pixmap):
        # Only reset position and zoom if this is a new image with different dimensions
        # or if there was no previous image
        if (self.original_pixmap is None or 
            self.original_pixmap.width() != pixmap.width() or 
            self.original_pixmap.height() != pixmap.height()):
            self.pan_position = QPoint(0, 0)
            self.zoom_factor = 1.0
            
        self.original_pixmap = pixmap
        self.update_display()
    
    def update_display(self):
        if self.original_pixmap is None:
            return
        
        # We don't set the pixmap directly anymore - just trigger a repaint
        self.update()
    
    def paintEvent(self, event):
        if not self.original_pixmap:
            return super().paintEvent(event)
        
        painter = QPainter(self)
        
        # Calculate the scaled size
        scaled_width = int(self.original_pixmap.width() * self.zoom_factor)
        scaled_height = int(self.original_pixmap.height() * self.zoom_factor)
        
        # Scale the pixmap
        scaled_pixmap = self.original_pixmap.scaled(scaled_width, scaled_height, 
                                                   Qt.AspectRatioMode.KeepAspectRatio)
        
        # Calculate center position
        x_center = (self.width() - scaled_pixmap.width()) // 2
        y_center = (self.height() - scaled_pixmap.height()) // 2
        
        # Apply panning offset
        x_pos = x_center + self.pan_position.x()
        y_pos = y_center + self.pan_position.y()
        
        # Draw the pixmap at the calculated position
        painter.drawPixmap(x_pos, y_pos, scaled_pixmap)
    
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        zoom_change = 0.1 if delta > 0 else -0.1
        
        # Apply zoom change
        old_zoom = self.zoom_factor
        self.zoom_factor = max(0.1, self.zoom_factor + zoom_change)
        
        # Update display
        self.update_display()
        
        # Prevent event propagation
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.last_mouse_position = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_panning:
            delta = event.position().toPoint() - self.last_mouse_position
            self.pan_position += delta
            self.last_mouse_position = event.position().toPoint()
            self.update_display()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            # Zoom in
            self.zoom_factor = min(5.0, self.zoom_factor + 0.1)
            self.update_display()
        elif event.key() == Qt.Key.Key_Minus:
            # Zoom out
            self.zoom_factor = max(0.1, self.zoom_factor - 0.1)
            self.update_display()
        elif event.key() == Qt.Key.Key_R:
            # Reset zoom and pan
            self.zoom_factor = 1.0
            self.pan_position = QPoint(0, 0)
            self.update_display()
        else:
            super().keyPressEvent(event)

class PatternGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Default values
        self.width = 1024  # Changed from 800 to 1024
        self.height = 1024  # Changed from 800 to 1024
        self.shape_width = 32
        self.shape_height = 32
        self.rows = 8
        self.columns = 8
        self.pattern_type = "offset_grid"
        self.shape_type = "circle"
        self.custom_image_path = ""
        self.bg_color = (0, 0, 0, 255)
        self.fg_color = (255, 136, 0, 255)  # Changed from (255, 0, 0, 255) to #FF8800
        self.scale_randomization = 0.0
        self.base_rotation = 0.0
        self.rotation_randomization = 0.0
        self.output_file = "pattern.png"
        self.column_rotations = []
        self.row_rotations = []
        self.column_rotation_spins = []
        self.row_rotation_spins = []
        
        # Preview settings
        self.preview_img = None
        self.preview_scale = 0.25
        
        # Initialize UI
        self.setWindowTitle("Patternsy - Pattern Generator (PyQt6)")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        self.init_ui()
        self.update_preview()

    def evaluate_expression(self, expression):
        """Safely evaluate a mathematical expression and return the result as an integer."""
        try:
            # Remove whitespace and convert to string
            expr = str(expression).strip()
            
            # If empty, return None
            if not expr:
                return None
            
            # If it's already a number, return it
            if expr.isdigit():
                return int(expr)
            
            # Handle negative numbers - but don't allow them since dimensions must be positive
            if expr.startswith('-'):
                return None
            
            # Allow only safe mathematical operations
            # Remove any characters that aren't digits, operators, parentheses, or decimal points
            if not re.match(r'^[0-9+\-*/().\s]+$', expr):
                return None
            
            # Check for division by zero patterns
            if '/0' in expr.replace(' ', ''):
                return None
            
            # Evaluate the expression safely
            result = eval(expr, {"__builtins__": {}}, {})
            
            # Handle float results
            if isinstance(result, float):
                if not (result.is_finite() and not result.is_nan()):
                    return None
                result = int(round(result))
            else:
                result = int(result)
            
            # Ensure it's within reasonable bounds
            if result > 16384:
                result = 16384
                
            return result
        except Exception as e:
            # If evaluation fails, return None to indicate error
            return None

    def on_width_changed(self):
        """Handle width input field changes."""
        text = self.width_edit.text()
        print(f"Width changed: '{text}'")  # Debug print
        result = self.evaluate_expression(text)
        print(f"Width evaluation result: {result}")  # Debug print
        
        if result is not None:
            self.width = result
            self.width_edit.setText(str(result))
            self.width_edit.setStyleSheet("")  # Reset to normal style
            print(f"Calling schedule_preview_update with width={self.width}")  # Debug print
            self.schedule_preview_update()
        else:
            # Invalid expression - highlight in red
            self.width_edit.setStyleSheet("background-color: #ffcccc;")
            print("Width expression invalid")  # Debug print

    def on_height_changed(self):
        """Handle height input field changes."""
        text = self.height_edit.text()
        print(f"Height changed: '{text}'")  # Debug print
        result = self.evaluate_expression(text)
        print(f"Height evaluation result: {result}")  # Debug print
        
        if result is not None:
            self.height = result
            self.height_edit.setText(str(result))
            self.height_edit.setStyleSheet("")  # Reset to normal style
            print(f"Calling schedule_preview_update with height={self.height}")  # Debug print
            self.schedule_preview_update()
        else:
            # Invalid expression - highlight in red
            self.height_edit.setStyleSheet("background-color: #ffcccc;")
            print("Height expression invalid")  # Debug print

    def on_width_text_changed(self):
        """Handle width text changes for real-time validation."""
        text = self.width_edit.text()
        result = self.evaluate_expression(text)
        
        if result is not None:
            self.width_edit.setStyleSheet("")  # Reset to normal style
        else:
            # Invalid expression - highlight in red
            self.width_edit.setStyleSheet("background-color: #ffcccc;")

    def on_height_text_changed(self):
        """Handle height text changes for real-time validation."""
        text = self.height_edit.text()
        result = self.evaluate_expression(text)
        
        if result is not None:
            self.height_edit.setStyleSheet("")  # Reset to normal style
        else:
            # Invalid expression - highlight in red
            self.height_edit.setStyleSheet("background-color: #ffcccc;")

    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout(main_widget)
        
        # === Left panel for controls ===
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setMinimumWidth(800)
        controls_scroll.setMaximumWidth(1200)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_scroll.setWidget(controls_widget)
        
        # === Size controls ===
        size_group = QGroupBox("Dimensions")
        size_layout = QGridLayout(size_group)
        
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_edit = QLineEdit(str(self.width))
        self.width_edit.setToolTip("Enter width in pixels or mathematical expression (e.g., 6*128)")
        self.width_edit.editingFinished.connect(self.on_width_changed)
        self.width_edit.textChanged.connect(self.on_width_text_changed)
        self.width_edit.returnPressed.connect(self.on_width_changed)
        size_layout.addWidget(self.width_edit, 0, 1)
        
        size_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_edit = QLineEdit(str(self.height))
        self.height_edit.setToolTip("Enter height in pixels or mathematical expression (e.g., 4*256)")
        self.height_edit.editingFinished.connect(self.on_height_changed)
        self.height_edit.textChanged.connect(self.on_height_text_changed)
        self.height_edit.returnPressed.connect(self.on_height_changed)
        size_layout.addWidget(self.height_edit, 1, 1)
        
        controls_layout.addWidget(size_group)
        
        # === Shape controls ===
        shape_group = QGroupBox("Shape Settings")
        shape_layout = QGridLayout(shape_group)
        
        shape_layout.addWidget(QLabel("Shape Type:"), 0, 0)
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["circle", "square", "triangle", "star", "custom"])
        self.shape_combo.setCurrentText(self.shape_type)
        self.shape_combo.currentTextChanged.connect(self.on_shape_changed)
        shape_layout.addWidget(self.shape_combo, 0, 1)
        
        shape_layout.addWidget(QLabel("Shape Width:"), 1, 0)
        self.shape_width_spin = QSpinBox()
        self.shape_width_spin.setRange(1, 500)
        self.shape_width_spin.setValue(self.shape_width)
        self.shape_width_spin.valueChanged.connect(self.schedule_preview_update)
        shape_layout.addWidget(self.shape_width_spin, 1, 1)
        
        shape_layout.addWidget(QLabel("Shape Height:"), 2, 0)
        self.shape_height_spin = QSpinBox()
        self.shape_height_spin.setRange(1, 500)
        self.shape_height_spin.setValue(self.shape_height)
        self.shape_height_spin.valueChanged.connect(self.schedule_preview_update)
        shape_layout.addWidget(self.shape_height_spin, 2, 1)
        
        shape_layout.addWidget(QLabel("Columns:"), 3, 0)
        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 500)
        self.columns_spin.setValue(self.columns)
        self.columns_spin.valueChanged.connect(self.on_columns_changed)
        shape_layout.addWidget(self.columns_spin, 3, 1)
        
        shape_layout.addWidget(QLabel("Rows:"), 4, 0)
        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 500)
        self.rows_spin.setValue(self.rows)
        self.rows_spin.valueChanged.connect(self.on_rows_changed)
        shape_layout.addWidget(self.rows_spin, 4, 1)
        
        self.custom_img_btn = QPushButton("Custom Image...")
        self.custom_img_btn.clicked.connect(self.select_custom_image)
        shape_layout.addWidget(self.custom_img_btn, 5, 0, 1, 2)
        
        controls_layout.addWidget(shape_group)
        
        self.col_rot_group = QGroupBox("Column Rotations")
        self.col_rot_layout = QGridLayout(self.col_rot_group)
        controls_layout.addWidget(self.col_rot_group)
        
        self.row_rot_group = QGroupBox("Row Rotations")
        self.row_rot_layout = QGridLayout(self.row_rot_group)
        controls_layout.addWidget(self.row_rot_group)
        
        # === Pattern type controls ===
        pattern_group = QGroupBox("Pattern Settings")
        pattern_layout = QGridLayout(pattern_group)
        
        pattern_layout.addWidget(QLabel("Pattern Type:"), 0, 0)
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["grid", "offset_grid", "random", "spiral"])
        self.pattern_combo.setCurrentText(self.pattern_type)
        self.pattern_combo.currentTextChanged.connect(self.on_pattern_changed)
        pattern_layout.addWidget(self.pattern_combo, 0, 1)
        
        controls_layout.addWidget(pattern_group)
        
        # === Randomization controls ===
        random_group = QGroupBox("Randomization")
        random_layout = QGridLayout(random_group)
        
        random_layout.addWidget(QLabel("Scale Random:"), 0, 0)
        self.scale_random_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_random_slider.setRange(0, 100)
        self.scale_random_slider.setValue(int(self.scale_randomization * 100))
        self.scale_random_slider.sliderReleased.connect(self.on_scale_random_changed)
        random_layout.addWidget(self.scale_random_slider, 0, 1)
        
        random_layout.addWidget(QLabel("Base Rotation:"), 1, 0)
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(int(self.base_rotation))
        self.rotation_slider.sliderReleased.connect(self.on_rotation_changed)
        random_layout.addWidget(self.rotation_slider, 1, 1)
        
        random_layout.addWidget(QLabel("Rotation Random:"), 2, 0)
        self.rotation_random_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_random_slider.setRange(0, 100)
        self.rotation_random_slider.setValue(int(self.rotation_randomization * 100))
        self.rotation_random_slider.sliderReleased.connect(self.on_rotation_random_changed)
        random_layout.addWidget(self.rotation_random_slider, 2, 1)
        
        controls_layout.addWidget(random_group)
        
        # === Color controls ===
        color_group = QGroupBox("Colors")
        color_layout = QVBoxLayout(color_group)
        
        self.bg_color_btn = QPushButton(f"Background: #{self.bg_color[0]:02x}{self.bg_color[1]:02x}{self.bg_color[2]:02x}")
        self.bg_color_btn.clicked.connect(self.select_bg_color)
        color_layout.addWidget(self.bg_color_btn)
        
        self.fg_color_btn = QPushButton(f"Foreground: #{self.fg_color[0]:02x}{self.fg_color[1]:02x}{self.fg_color[2]:02x}")
        self.fg_color_btn.clicked.connect(self.select_fg_color)
        color_layout.addWidget(self.fg_color_btn)
        
        controls_layout.addWidget(color_group)
        
        # === Output controls ===
        output_group = QGroupBox("Output")
        output_layout = QGridLayout(output_group)
        
        output_layout.addWidget(QLabel("Filename:"), 0, 0)
        self.output_edit = QLineEdit(self.output_file)
        output_layout.addWidget(self.output_edit, 0, 1)
        
        controls_layout.addWidget(output_group)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Pattern")
        self.generate_btn.clicked.connect(self.generate_pattern)
        controls_layout.addWidget(self.generate_btn)
        
        # Add some stretch at the end
        controls_layout.addStretch()
        
        # === Preview area ===
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Add info button for controls help
        preview_header = QHBoxLayout()
        preview_layout.addLayout(preview_header)
        
        preview_header.addStretch()
        
        info_button = QToolButton()
        info_button.setText("i")
        info_button.setToolTip("""
            <b>Zoom In:</b> Mouse wheel up or '+' key<br>
            <b>Zoom Out:</b> Mouse wheel down or '-' key<br>
            <b>Pan:</b> Click and drag with left mouse button<br>
            <b>Reset View:</b> 'R' key
        """)
        info_button.setFixedSize(24, 24)
        info_button.setStyleSheet("""
            QToolButton {
                border: 1px solid gray;
                border-radius: 12px;
                background-color: #ff8800;
                color: #000000;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
        """)
        preview_header.addWidget(info_button)
        
        self.preview_label = ZoomablePreviewLabel()
        preview_layout.addWidget(self.preview_label)
        
        # Add controls scroll and preview to main layout
        main_layout.addWidget(controls_scroll)
        main_layout.addWidget(preview_group, 1)  # Preview takes more space
        
        self.on_columns_changed()
        self.on_rows_changed()
    
    # === Event handlers ===
    def on_shape_changed(self, text):
        self.shape_type = text
        
        # If custom is selected and no image is loaded, prompt to select one
        if text == "custom" and not self.custom_image_path:
            self.select_custom_image()
        else:
            self.schedule_preview_update()
    
    def on_pattern_changed(self, text):
        self.pattern_type = text
        self.schedule_preview_update()
    
    def on_scale_random_changed(self):
        self.scale_randomization = self.scale_random_slider.value() / 100.0
        self.schedule_preview_update()
    
    def on_rotation_changed(self):
        self.base_rotation = self.rotation_slider.value()
        self.schedule_preview_update()
    
    def on_rotation_random_changed(self):
        self.rotation_randomization = self.rotation_random_slider.value() / 100.0
        self.schedule_preview_update()
    
    def select_bg_color(self):
        color = QColor(self.bg_color[0], self.bg_color[1], self.bg_color[2])
        color = QColorDialog.getColor(color, self, "Select Background Color")
        
        if color.isValid():
            self.bg_color = (color.red(), color.green(), color.blue(), 255)
            self.bg_color_btn.setText(f"Background: #{self.bg_color[0]:02x}{self.bg_color[1]:02x}{self.bg_color[2]:02x}")
            self.schedule_preview_update()
    
    def select_fg_color(self):
        color = QColor(self.fg_color[0], self.fg_color[1], self.fg_color[2])
        color = QColorDialog.getColor(color, self, "Select Foreground Color")
        
        if color.isValid():
            self.fg_color = (color.red(), color.green(), color.blue(), 255)
            self.fg_color_btn.setText(f"Foreground: #{self.fg_color[0]:02x}{self.fg_color[1]:02x}{self.fg_color[2]:02x}")
            self.schedule_preview_update()
    
    def select_custom_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Image",
            "",
            "Image files (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;All files (*.*)"
        )
        
        if file_path:
            self.custom_image_path = file_path
            self.shape_combo.setCurrentText("custom")
            self.schedule_preview_update()
    
    def schedule_preview_update(self):
        # Get current values from UI (width and height are now handled by their respective change handlers)
        self.shape_width = self.shape_width_spin.value()
        self.shape_height = self.shape_height_spin.value()
        self.rows = self.rows_spin.value()
        self.columns = self.columns_spin.value()
        if self.column_rotation_spins:
            self.column_rotations = [spin.value() for spin in self.column_rotation_spins]
        if self.row_rotation_spins:
            self.row_rotations = [spin.value() for spin in self.row_rotation_spins]
        self.output_file = self.output_edit.text()
        
        print(f"schedule_preview_update called: width={self.width}, height={self.height}")  # Debug print
        self.update_preview()

    def update_preview(self):
        try:
            # Create a temporary file for the preview
            temp_output = "preview_temp.png"
            
            # Calculate preview dimensions
            preview_width = max(50, int(self.width * self.preview_scale))
            preview_height = max(50, int(self.height * self.preview_scale))
            
            # Scale down other parameters proportionally for faster preview
            preview_shape_width = max(1, int(self.shape_width * self.preview_scale))
            preview_shape_height = max(1, int(self.shape_height * self.preview_scale))
            
            # Calculate spacing based on grid dimensions
            preview_spacing_x = preview_width // max(1, self.columns)
            preview_spacing_y = preview_height // max(1, self.rows)
            
            # Generate the preview pattern
            create_pattern(
                width=preview_width,
                height=preview_height,
                shape_width=preview_shape_width,
                shape_height=preview_shape_height,
                spacing_x=preview_spacing_x,
                spacing_y=preview_spacing_y,
                pattern_type=self.pattern_type,
                shape_type=self.shape_type,
                custom_image_path=self.custom_image_path if self.shape_type == "custom" else None,
                bg_color=self.bg_color,
                fg_color=self.fg_color,
                scale_randomization=self.scale_randomization,
                base_rotation=self.base_rotation,
                rotation_randomization=self.rotation_randomization,
                output_file=temp_output,
                column_rotations=self.column_rotations,
                row_rotations=self.row_rotations,
                columns=self.columns,
                rows=self.rows
            )
            
            # Load the preview image
            img = QPixmap(temp_output)
            self.preview_label.set_pixmap(img)
            
            # Try to remove the temporary file
            try:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Error generating preview: {str(e)}")
    
    def generate_pattern(self):
        try:
            # Get the output filename
            output_file = self.output_edit.text()
            if not output_file:
                output_file = "pattern.png"
            
            # Add extension if not present
            if not output_file.lower().endswith('.png'):
                output_file += '.png'
            
            # Calculate spacing based on grid dimensions
            spacing_x = self.width // max(1, self.columns)
            spacing_y = self.height // max(1, self.rows)
            
            # Show a progress message
            QMessageBox.information(self, "Generating", "Generating pattern. This might take a moment...")
            
            # Generate the pattern
            create_pattern(
                width=self.width,
                height=self.height,
                shape_width=self.shape_width,
                shape_height=self.shape_height,
                spacing_x=spacing_x,
                spacing_y=spacing_y,
                pattern_type=self.pattern_type,
                shape_type=self.shape_type,
                custom_image_path=self.custom_image_path if self.shape_type == "custom" else None,
                bg_color=self.bg_color,
                fg_color=self.fg_color,
                scale_randomization=self.scale_randomization,
                base_rotation=self.base_rotation,
                rotation_randomization=self.rotation_randomization,
                output_file=output_file,
                column_rotations=self.column_rotations,
                row_rotations=self.row_rotations,
                columns=self.columns,
                rows=self.rows
            )
            
            # Show success message
            QMessageBox.information(self, "Success", f"Pattern generated and saved as '{output_file}'.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating pattern: {str(e)}")

    def on_columns_changed(self):
        self.columns = self.columns_spin.value()
        self.rebuild_column_rotation_controls()
        self.schedule_preview_update()

    def on_rows_changed(self):
        self.rows = self.rows_spin.value()
        self.rebuild_row_rotation_controls()
        self.schedule_preview_update()

    def rebuild_column_rotation_controls(self):
        while self.col_rot_layout.count():
            item = self.col_rot_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.column_rotation_spins = []
        values = self.column_rotations if self.column_rotations else [0] * self.columns
        for i in range(self.columns):
            label = QLabel(f"Col {i}:")
            spin = QSpinBox()
            spin.setRange(0, 360)
            spin.setValue(values[i] if i < len(values) else 0)
            spin.valueChanged.connect(self.schedule_preview_update)
            self.col_rot_layout.addWidget(label, i // 4, (i % 4) * 2)
            self.col_rot_layout.addWidget(spin, i // 4, (i % 4) * 2 + 1)
            self.column_rotation_spins.append(spin)
        self.column_rotations = [spin.value() for spin in self.column_rotation_spins]

    def rebuild_row_rotation_controls(self):
        while self.row_rot_layout.count():
            item = self.row_rot_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self.row_rotation_spins = []
        values = self.row_rotations if self.row_rotations else [0] * self.rows
        for i in range(self.rows):
            label = QLabel(f"Row {i}:")
            spin = QSpinBox()
            spin.setRange(0, 360)
            spin.setValue(values[i] if i < len(values) else 0)
            spin.valueChanged.connect(self.schedule_preview_update)
            self.row_rot_layout.addWidget(label, i // 4, (i % 4) * 2)
            self.row_rot_layout.addWidget(spin, i // 4, (i % 4) * 2 + 1)
            self.row_rotation_spins.append(spin)
        self.row_rotations = [spin.value() for spin in self.row_rotation_spins]

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatternGeneratorApp()
    window.show()
    sys.exit(app.exec()) 