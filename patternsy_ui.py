#!/usr/bin/env python3

import os
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
from patternsy import create_pattern

class PatternGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patternsy - Pattern Generator")
        self.root.geometry("1200x800")
        self.root.minsize(900, 700)
        
        # Default values
        self.width = tk.IntVar(value=800)
        self.height = tk.IntVar(value=800)
        self.base_scale = tk.IntVar(value=32)
        self.spacing = tk.IntVar(value=128)
        self.pattern_type = tk.StringVar(value="offset_grid")
        self.shape_type = tk.StringVar(value="circle")
        self.custom_image_path = tk.StringVar(value="")
        self.bg_color = (0, 0, 0, 255)
        self.fg_color = (255, 0, 0, 255)
        self.scale_randomization = tk.DoubleVar(value=0.0)
        self.base_rotation = tk.DoubleVar(value=0.0)
        self.rotation_randomization = tk.DoubleVar(value=0.0)
        self.output_file = tk.StringVar(value="pattern.png")
        
        # Preview settings
        self.preview_img = None
        self.preview_scale = 0.25  # Scale for preview image
        self.preview_thread = None
        self.is_preview_running = False
        
        # Create the UI
        self.create_ui()
        
        # Generate initial preview
        self.schedule_preview_update()
        
    def create_ui(self):
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left panel for controls
        controls_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create right panel for preview and output
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === Controls ===
        # Size controls
        size_frame = ttk.LabelFrame(controls_frame, text="Dimensions", padding="5")
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(size_frame, from_=100, to=8192, textvariable=self.width, width=6,
                   command=self.schedule_preview_update).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(size_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(size_frame, from_=100, to=8192, textvariable=self.height, width=6,
                   command=self.schedule_preview_update).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Shape controls
        shape_frame = ttk.LabelFrame(controls_frame, text="Shape Settings", padding="5")
        shape_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(shape_frame, text="Shape Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        shape_types = ["circle", "square", "triangle", "star", "custom"]
        shape_dropdown = ttk.Combobox(shape_frame, textvariable=self.shape_type, values=shape_types, state="readonly", width=10)
        shape_dropdown.grid(row=0, column=1, sticky=tk.W, pady=2)
        shape_dropdown.bind("<<ComboboxSelected>>", lambda e: self.schedule_preview_update())
        
        ttk.Label(shape_frame, text="Base Scale:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(shape_frame, from_=4, to=1000, textvariable=self.base_scale, width=6,
                   command=self.schedule_preview_update).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(shape_frame, text="Spacing:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(shape_frame, from_=10, to=1000, textvariable=self.spacing, width=6,
                   command=self.schedule_preview_update).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        custom_img_button = ttk.Button(shape_frame, text="Custom Image...", command=self.select_custom_image)
        custom_img_button.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Pattern type controls
        pattern_frame = ttk.LabelFrame(controls_frame, text="Pattern Settings", padding="5")
        pattern_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pattern_frame, text="Pattern Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        pattern_types = ["grid", "offset_grid", "random", "spiral"]
        pattern_dropdown = ttk.Combobox(pattern_frame, textvariable=self.pattern_type, values=pattern_types, state="readonly", width=10)
        pattern_dropdown.grid(row=0, column=1, sticky=tk.W, pady=2)
        pattern_dropdown.bind("<<ComboboxSelected>>", lambda e: self.schedule_preview_update())
        
        # Randomization controls
        random_frame = ttk.LabelFrame(controls_frame, text="Randomization", padding="5")
        random_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(random_frame, text="Scale Random:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Scale(random_frame, from_=0, to=1, variable=self.scale_randomization, orient=tk.HORIZONTAL,
                 command=lambda e: self.schedule_preview_update()).grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(random_frame, text="Base Rotation:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Scale(random_frame, from_=0, to=360, variable=self.base_rotation, orient=tk.HORIZONTAL,
                 command=lambda e: self.schedule_preview_update()).grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(random_frame, text="Rotation Random:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Scale(random_frame, from_=0, to=1, variable=self.rotation_randomization, orient=tk.HORIZONTAL,
                 command=lambda e: self.schedule_preview_update()).grid(row=2, column=1, sticky=tk.EW, pady=2)
        
        # Color controls
        color_frame = ttk.LabelFrame(controls_frame, text="Colors", padding="5")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.bg_color_button = ttk.Button(color_frame, text="Background Color", command=self.select_bg_color)
        self.bg_color_button.grid(row=0, column=0, columnspan=2, sticky=tk.EW, pady=2)
        
        self.fg_color_button = ttk.Button(color_frame, text="Foreground Color", command=self.select_fg_color)
        self.fg_color_button.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=2)
        
        # Update button colors to match current selections
        self.update_color_buttons()
        
        # Output controls
        output_frame = ttk.LabelFrame(controls_frame, text="Output", padding="5")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Filename:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(output_frame, textvariable=self.output_file, width=15).grid(row=0, column=1, sticky=tk.EW, pady=2)
        
        # Generate button
        generate_button = ttk.Button(controls_frame, text="Generate Pattern", command=self.generate_pattern)
        generate_button.pack(fill=tk.X, pady=(10, 0))
        
        # === Preview ===
        self.preview_canvas = tk.Canvas(preview_frame, bg="lightgrey")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
    def update_color_buttons(self):
        """Update color buttons with visual indicators of selected colors"""
        # Create a style for each color button
        bg_color_rgb = f'#{self.bg_color[0]:02x}{self.bg_color[1]:02x}{self.bg_color[2]:02x}'
        fg_color_rgb = f'#{self.fg_color[0]:02x}{self.fg_color[1]:02x}{self.fg_color[2]:02x}'
        
        self.bg_color_button.configure(text=f"Background: {bg_color_rgb}")
        self.fg_color_button.configure(text=f"Foreground: {fg_color_rgb}")
    
    def select_bg_color(self):
        """Open color chooser for background color"""
        color = colorchooser.askcolor(
            title="Select Background Color",
            initialcolor=f'#{self.bg_color[0]:02x}{self.bg_color[1]:02x}{self.bg_color[2]:02x}'
        )
        if color[1]:  # If a color was selected (not canceled)
            r, g, b = [int(x) for x in color[0]]
            self.bg_color = (r, g, b, 255)
            self.update_color_buttons()
            self.schedule_preview_update()
    
    def select_fg_color(self):
        """Open color chooser for foreground color"""
        color = colorchooser.askcolor(
            title="Select Foreground Color",
            initialcolor=f'#{self.fg_color[0]:02x}{self.fg_color[1]:02x}{self.fg_color[2]:02x}'
        )
        if color[1]:  # If a color was selected (not canceled)
            r, g, b = [int(x) for x in color[0]]
            self.fg_color = (r, g, b, 255)
            self.update_color_buttons()
            self.schedule_preview_update()
    
    def select_custom_image(self):
        """Allow user to select a custom image file"""
        file_path = filedialog.askopenfilename(
            title="Select Custom Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.custom_image_path.set(file_path)
            # Automatically switch to custom shape type
            self.shape_type.set("custom")
            self.schedule_preview_update()
    
    def schedule_preview_update(self, *args):
        """Schedule a preview update with debouncing"""
        if self.preview_thread is not None and self.preview_thread.is_alive():
            self.is_preview_running = False
            self.preview_thread.join(timeout=0.1)
        
        self.is_preview_running = True
        self.preview_thread = threading.Thread(target=self.update_preview)
        self.preview_thread.daemon = True
        self.preview_thread.start()
    
    def update_preview(self):
        """Update the preview image in a separate thread"""
        # Small delay for debouncing
        time.sleep(0.2)
        
        if not self.is_preview_running:
            return
        
        try:
            # Create a temporary file for the preview
            temp_output = "preview_temp.png"
            
            # Calculate preview dimensions
            preview_width = max(200, int(self.width.get() * self.preview_scale))
            preview_height = max(200, int(self.height.get() * self.preview_scale))
            
            # Scale down other parameters proportionally for faster preview
            preview_base_scale = max(4, int(self.base_scale.get() * self.preview_scale))
            preview_spacing = max(10, int(self.spacing.get() * self.preview_scale))
            
            # Generate the preview pattern
            create_pattern(
                width=preview_width,
                height=preview_height,
                base_scale=preview_base_scale,
                spacing=preview_spacing,
                pattern_type=self.pattern_type.get(),
                shape_type=self.shape_type.get(),
                custom_image_path=self.custom_image_path.get() if self.shape_type.get() == "custom" else None,
                bg_color=self.bg_color,
                fg_color=self.fg_color,
                scale_randomization=self.scale_randomization.get(),
                base_rotation=self.base_rotation.get(),
                rotation_randomization=self.rotation_randomization.get(),
                output_file=temp_output
            )
            
            # Load the preview image
            img = Image.open(temp_output)
            self.preview_img = ImageTk.PhotoImage(img)
            
            # Update the canvas with the new image
            self.root.after(0, self.display_preview, img.width, img.height)
            
            # Try to remove the temporary file
            try:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except:
                pass
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Preview Error", f"Error generating preview: {str(e)}"))
    
    def display_preview(self, width, height):
        """Display the preview image on the canvas"""
        if not self.preview_img:
            return
            
        # Clear the canvas
        self.preview_canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Calculate the position to center the image
        x = max(0, (canvas_width - width) // 2)
        y = max(0, (canvas_height - height) // 2)
        
        # Draw the image on the canvas
        self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_img)
    
    def generate_pattern(self):
        """Generate the full-resolution pattern and save it"""
        try:
            # Get the output filename
            output_file = self.output_file.get()
            if not output_file:
                output_file = "pattern.png"
            
            # Add extension if not present
            if not output_file.lower().endswith('.png'):
                output_file += '.png'
            
            # Show a progress message
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Generating...")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Center the progress window
            progress_window.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
            progress_window.geometry(f"+{x}+{y}")
            
            ttk.Label(progress_window, text="Generating pattern...", padding="10").pack()
            progress = ttk.Progressbar(progress_window, mode="indeterminate")
            progress.pack(fill=tk.X, padx=20, pady=10)
            progress.start()
            
            # Create a thread to generate the pattern
            def generate_thread():
                try:
                    create_pattern(
                        width=self.width.get(),
                        height=self.height.get(),
                        base_scale=self.base_scale.get(),
                        spacing=self.spacing.get(),
                        pattern_type=self.pattern_type.get(),
                        shape_type=self.shape_type.get(),
                        custom_image_path=self.custom_image_path.get() if self.shape_type.get() == "custom" else None,
                        bg_color=self.bg_color,
                        fg_color=self.fg_color,
                        scale_randomization=self.scale_randomization.get(),
                        base_rotation=self.base_rotation.get(),
                        rotation_randomization=self.rotation_randomization.get(),
                        output_file=output_file
                    )
                    
                    # Close the progress window and show success message
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        messagebox.showinfo("Success", f"Pattern generated and saved as '{output_file}'.")
                    ])
                    
                except Exception as e:
                    # Close the progress window and show error message
                    self.root.after(0, lambda: [
                        progress_window.destroy(),
                        messagebox.showerror("Error", f"Error generating pattern: {str(e)}")
                    ])
            
            # Start the generation thread
            thread = threading.Thread(target=generate_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating pattern: {str(e)}")

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    
    # Set a theme that works well across platforms
    try:
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
    except:
        pass  # If theme setting fails, use default
    
    app = PatternGeneratorApp(root)
    root.mainloop()
