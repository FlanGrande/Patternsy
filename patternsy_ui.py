#!/usr/bin/env python3

import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QSpinBox, QComboBox, QPushButton, QFileDialog, 
                            QSlider, QLineEdit, QGroupBox, QGridLayout, QMessageBox,
                            QScrollArea, QColorDialog)
from PyQt6.QtGui import QPixmap, QImage, QColor, QMouseEvent, QWheelEvent, QKeyEvent, QPainter
from PyQt6.QtCore import Qt, QPoint
from PIL import Image, ImageQt
import time
from patternsy import create_pattern

class ZoomablePreviewLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 400)
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
        self.base_scale = 32
        self.spacing = 128
        self.pattern_type = "offset_grid"
        self.shape_type = "circle"
        self.custom_image_path = ""
        self.bg_color = (0, 0, 0, 255)
        self.fg_color = (255, 136, 0, 255)  # Changed from (255, 0, 0, 255) to #FF8800
        self.scale_randomization = 0.0
        self.base_rotation = 0.0
        self.rotation_randomization = 0.0
        self.output_file = "pattern.png"
        
        # Preview settings
        self.preview_img = None
        self.preview_scale = 0.25
        
        # Initialize UI
        self.setWindowTitle("Patternsy - Pattern Generator (PyQt6)")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        self.init_ui()
        self.update_preview()
        
    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout(main_widget)
        
        # === Left panel for controls ===
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setMinimumWidth(450)
        controls_scroll.setMaximumWidth(400)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_scroll.setWidget(controls_widget)
        
        # === Size controls ===
        size_group = QGroupBox("Dimensions")
        size_layout = QGridLayout(size_group)
        
        size_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 8192)
        self.width_spin.setValue(self.width)
        self.width_spin.valueChanged.connect(self.schedule_preview_update)
        size_layout.addWidget(self.width_spin, 0, 1)
        
        size_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 8192)
        self.height_spin.setValue(self.height)
        self.height_spin.valueChanged.connect(self.schedule_preview_update)
        size_layout.addWidget(self.height_spin, 1, 1)
        
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
        
        shape_layout.addWidget(QLabel("Base Scale:"), 1, 0)
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(4, 1000)
        self.scale_spin.setValue(self.base_scale)
        self.scale_spin.valueChanged.connect(self.schedule_preview_update)
        shape_layout.addWidget(self.scale_spin, 1, 1)
        
        shape_layout.addWidget(QLabel("Spacing:"), 2, 0)
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(10, 1000)
        self.spacing_spin.setValue(self.spacing)
        self.spacing_spin.valueChanged.connect(self.schedule_preview_update)
        shape_layout.addWidget(self.spacing_spin, 2, 1)
        
        self.custom_img_btn = QPushButton("Custom Image...")
        self.custom_img_btn.clicked.connect(self.select_custom_image)
        shape_layout.addWidget(self.custom_img_btn, 3, 0, 1, 2)
        
        controls_layout.addWidget(shape_group)
        
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
        
        self.preview_label = ZoomablePreviewLabel()
        preview_layout.addWidget(self.preview_label)
        
        # Add controls scroll and preview to main layout
        main_layout.addWidget(controls_scroll)
        main_layout.addWidget(preview_group, 1)  # Preview takes more space
    
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
        # Get current values from UI
        self.width = self.width_spin.value()
        self.height = self.height_spin.value()
        self.base_scale = self.scale_spin.value()
        self.spacing = self.spacing_spin.value()
        self.output_file = self.output_edit.text()
        
        self.update_preview()
    
    def update_preview(self):
        try:
            # Create a temporary file for the preview
            temp_output = "preview_temp.png"
            
            # Calculate preview dimensions
            preview_width = max(200, int(self.width * self.preview_scale))
            preview_height = max(200, int(self.height * self.preview_scale))
            
            # Scale down other parameters proportionally for faster preview
            preview_base_scale = max(4, int(self.base_scale * self.preview_scale))
            preview_spacing = max(10, int(self.spacing * self.preview_scale))
            
            # Generate the preview pattern
            create_pattern(
                width=preview_width,
                height=preview_height,
                base_scale=preview_base_scale,
                spacing=preview_spacing,
                pattern_type=self.pattern_type,
                shape_type=self.shape_type,
                custom_image_path=self.custom_image_path if self.shape_type == "custom" else None,
                bg_color=self.bg_color,
                fg_color=self.fg_color,
                scale_randomization=self.scale_randomization,
                base_rotation=self.base_rotation,
                rotation_randomization=self.rotation_randomization,
                output_file=temp_output
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
            
            # Show a progress message
            QMessageBox.information(self, "Generating", "Generating pattern. This might take a moment...")
            
            # Generate the pattern
            create_pattern(
                width=self.width,
                height=self.height,
                base_scale=self.base_scale,
                spacing=self.spacing,
                pattern_type=self.pattern_type,
                shape_type=self.shape_type,
                custom_image_path=self.custom_image_path if self.shape_type == "custom" else None,
                bg_color=self.bg_color,
                fg_color=self.fg_color,
                scale_randomization=self.scale_randomization,
                base_rotation=self.base_rotation,
                rotation_randomization=self.rotation_randomization,
                output_file=output_file
            )
            
            # Show success message
            QMessageBox.information(self, "Success", f"Pattern generated and saved as '{output_file}'.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating pattern: {str(e)}")

# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PatternGeneratorApp()
    window.show()
    sys.exit(app.exec()) 