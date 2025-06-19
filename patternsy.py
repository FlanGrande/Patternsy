#!/usr/bin/env python3

import math
import random
import os
from PIL import Image, ImageDraw, ImageOps, ImageFilter

# Global cache for custom images
_custom_image_cache = {}

def get_cached_custom_image(custom_image_path, shape_width, shape_height):
    """Get a cached custom image or load and cache it if not present."""
    if not custom_image_path or not os.path.exists(custom_image_path):
        return None
    
    # Create cache key based on path and dimensions
    cache_key = (custom_image_path, shape_width, shape_height)
    
    # Check if we already have this image cached
    if cache_key in _custom_image_cache:
        return _custom_image_cache[cache_key].copy()
    
    try:
        # Load and resize the custom image
        custom_img = Image.open(custom_image_path).convert("RGBA")
        custom_img = custom_img.resize((shape_width, shape_height), Image.LANCZOS)
        
        # Cache the resized image
        _custom_image_cache[cache_key] = custom_img.copy()
        
        return custom_img
    except Exception as e:
        print(f"Error loading custom image: {e}")
        return None

def create_pattern(
        width=1200,
        height=1200,
        base_scale=32,
        shape_width=None,
        shape_height=None,
        spacing=128,
        spacing_x=None,
        spacing_y=None,
        pattern_type="offset_grid",
        shape_type="circle",
        custom_image_path=None,
        bg_color=(0, 0, 0, 255),
        fg_color=(255, 0, 0, 255),
        scale_randomization=0.0,
        base_rotation=0.0,
        rotation_randomization=0.0,
        output_file="pattern.png",
        antialiasing=True,
        aa_scale=4
):
    """
    Create a seamlessly tiling pattern with various shapes and arrangements.
    
    Parameters:
    - width, height: dimensions of the output image
    - base_scale: base size of the shapes (for backward compatibility)
    - shape_width, shape_height: specific width and height of shapes (overrides base_scale)
    - spacing: distance between shapes (for backward compatibility)
    - spacing_x, spacing_y: horizontal and vertical spacing between shapes (overrides spacing)
    - pattern_type: "grid", "offset_grid", "random", "spiral"
    - shape_type: "circle", "square", "triangle", "star", "custom"
    - custom_image_path: path to custom image (used when shape_type="custom")
    - bg_color: background color as (R,G,B,A) tuple
    - fg_color: foreground color as (R,G,B,A) tuple
    - scale_randomization: random variation in shape size (0.0-1.0)
    - base_rotation: base rotation for all shapes in degrees
    - rotation_randomization: random variation in rotation (0.0-1.0)
    - output_file: filename for the output image
    - antialiasing: whether to apply antialiasing to the whole image
    - aa_scale: antialiasing scale factor (higher = better quality, slower)
    """
    
    if shape_width is None:
        shape_width = base_scale
    if shape_height is None:
        shape_height = base_scale
    
    if spacing_x is None:
        spacing_x = spacing
    if spacing_y is None:
        spacing_y = spacing
    
    # Scale up dimensions for antialiasing
    if antialiasing:
        aa_width = width * aa_scale
        aa_height = height * aa_scale
        aa_shape_width = shape_width * aa_scale
        aa_shape_height = shape_height * aa_scale
        aa_spacing_x = spacing_x * aa_scale
        aa_spacing_y = spacing_y * aa_scale
    else:
        aa_width = width
        aa_height = height
        aa_shape_width = shape_width
        aa_shape_height = shape_height
        aa_spacing_x = spacing_x
        aa_spacing_y = spacing_y
    
    img = Image.new("RGBA", (aa_width, aa_height), bg_color)
    
    coordinates = generate_pattern_coordinates(
        aa_width, aa_height, aa_spacing_x, aa_spacing_y, pattern_type
    )
    
    max_shape_size = max(aa_shape_width, aa_shape_height)
    
    for x, y in coordinates:
        if scale_randomization > 0:
            scale_factor = 1.0 - (scale_randomization * random.uniform(-1, 1))
            current_shape_width = int(aa_shape_width * scale_factor)
            current_shape_height = int(aa_shape_height * scale_factor)
            current_shape_width = max(current_shape_width, 1)
            current_shape_height = max(current_shape_height, 1)
        else:
            current_shape_width = aa_shape_width
            current_shape_height = aa_shape_height
            
        if rotation_randomization > 0:
            rotation_range = 360 * rotation_randomization
            current_rotation = base_rotation + random.uniform(-rotation_range/2, rotation_range/2)
        else:
            current_rotation = base_rotation
        
        shape_img = create_shape(
            shape_type, current_shape_width, current_shape_height, fg_color, current_rotation, 
            custom_image_path
        )
        
        paste_x = int(x - shape_img.width / 2)
        paste_y = int(y - shape_img.height / 2)
        
        draw_shape_with_tiling(img, shape_img, paste_x, paste_y, aa_width, aa_height)
    
    # Apply antialiasing by resizing down
    if antialiasing:
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    img = img.convert("RGB")
    img.save(output_file)
    print(f"Pattern saved as {output_file}")
    return img

def generate_pattern_coordinates(width, height, spacing_x, spacing_y, pattern_type):
    """Generate coordinates for shapes based on the specified pattern type with seamless tiling support."""
    coordinates = []
    
    if pattern_type == "grid":
        # Simple grid pattern - start from half spacing to center shapes in grid cells
        for y in range(spacing_y // 2, height, spacing_y):
            for x in range(spacing_x // 2, width, spacing_x):
                coordinates.append((x, y))
                
    elif pattern_type == "offset_grid":
        # Grid pattern with every other row offset for seamless tiling
        for row_index, y in enumerate(range(spacing_y // 2, height, spacing_y)):
            if row_index % 2 == 1:
                # Offset row - shift by half spacing
                row_offset = spacing_x // 2
                for x in range(spacing_x // 2 + row_offset, width + spacing_x, spacing_x):
                    coordinates.append((x, y))
            else:
                # Regular row
                for x in range(spacing_x // 2, width, spacing_x):
                    coordinates.append((x, y))
                
    elif pattern_type == "random":
        # Random distribution with tiling considerations
        random.seed(hash((width, height, spacing_x, spacing_y)))
        
        num_shapes = (width // spacing_x) * (height // spacing_y)
        num_shapes = int(num_shapes * 1.2)
        
        min_spacing_x = spacing_x // 3
        min_spacing_y = spacing_y // 3
        
        for _ in range(num_shapes):
            for attempt in range(20):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                
                # Check if this point is far enough from all existing points
                too_close = False
                for ex, ey in coordinates:
                    dx = abs(ex - x)
                    dy = abs(ey - y)
                    
                    if dx < min_spacing_x and dy < min_spacing_y:
                        too_close = True
                        break
                        
                if not too_close:
                    coordinates.append((x, y))
                    break
        
        random.seed()
                    
    elif pattern_type == "spiral":
        # Spiral pattern
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        a = spacing_x / (2 * math.pi)
        b = spacing_y / 20
        
        t = 0
        while True:
            r = a * t
            if r > max_radius:
                break
                
            x = center_x + r * math.cos(t)
            y = center_y + r * math.sin(t)
            
            if 0 <= x < width and 0 <= y < height:
                coordinates.append((int(x), int(y)))
                
            t += b / r if r > 0 else b
    
    return coordinates

def create_shape(shape_type, shape_width, shape_height, color, rotation, custom_image_path):
    """Create a shape image based on the specified shape type."""
    shape_img = Image.new("RGBA", (shape_width, shape_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape_img)
    
    if shape_type == "circle":
        draw.ellipse([0, 0, shape_width - 1, shape_height - 1], fill=color)
        
    elif shape_type == "square":
        draw.rectangle([0, 0, shape_width - 1, shape_height - 1], fill=color)
        
    elif shape_type == "triangle":
        points = [
            (shape_width // 2, 0),       
            (0, shape_height - 1),        
            (shape_width - 1, shape_height - 1)  
        ]
        draw.polygon(points, fill=color)
        
    elif shape_type == "star":
        points = []
        center_x = shape_width // 2
        center_y = shape_height // 2
        outer_radius = min(shape_width, shape_height) // 2
        inner_radius = outer_radius // 2
        
        for i in range(10):
            radius = outer_radius if i % 2 == 0 else inner_radius
            angle = math.pi / 5 * i - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))
            
        draw.polygon(points, fill=color)
        
    elif shape_type == "custom" and custom_image_path and os.path.exists(custom_image_path):
        custom_img = get_cached_custom_image(custom_image_path, shape_width, shape_height)
        if custom_img:
            shape_img = custom_img
        else:
            draw.ellipse([0, 0, shape_width - 1, shape_height - 1], fill=color)
    else:
        draw.ellipse([0, 0, shape_width - 1, shape_height - 1], fill=color)
    
    if rotation != 0:
        shape_img = shape_img.rotate(rotation, resample=Image.NEAREST, expand=False)
    
    return shape_img

def draw_shape_with_tiling(img, shape_img, paste_x, paste_y, width, height):
    """Draw a shape with seamless tiling support - handles wrapping at canvas edges."""
    shape_width = shape_img.width
    shape_height = shape_img.height
    
    # Draw the shape at the original position and handle tiling by drawing
    # wrapped versions only where the original shape extends beyond boundaries
    
    # Always draw the main shape (cropped if necessary)
    draw_cropped_shape(img, shape_img, paste_x, paste_y, width, height)
    
    # Handle horizontal tiling
    if paste_x < 0:
        # Shape extends beyond left edge, draw wrapped version on right
        draw_cropped_shape(img, shape_img, paste_x + width, paste_y, width, height)
    elif paste_x + shape_width > width:
        # Shape extends beyond right edge, draw wrapped version on left
        draw_cropped_shape(img, shape_img, paste_x - width, paste_y, width, height)
    
    # Handle vertical tiling
    if paste_y < 0:
        # Shape extends beyond top edge, draw wrapped version at bottom
        draw_cropped_shape(img, shape_img, paste_x, paste_y + height, width, height)
    elif paste_y + shape_height > height:
        # Shape extends beyond bottom edge, draw wrapped version at top
        draw_cropped_shape(img, shape_img, paste_x, paste_y - height, width, height)
    
    # Handle corner tiling (only if shape extends in both directions)
    if paste_x < 0 and paste_y < 0:
        draw_cropped_shape(img, shape_img, paste_x + width, paste_y + height, width, height)
    elif paste_x < 0 and paste_y + shape_height > height:
        draw_cropped_shape(img, shape_img, paste_x + width, paste_y - height, width, height)
    elif paste_x + shape_width > width and paste_y < 0:
        draw_cropped_shape(img, shape_img, paste_x - width, paste_y + height, width, height)
    elif paste_x + shape_width > width and paste_y + shape_height > height:
        draw_cropped_shape(img, shape_img, paste_x - width, paste_y - height, width, height)

def draw_cropped_shape(img, shape_img, paste_x, paste_y, width, height):
    """Draw a shape, cropping it to fit within the canvas boundaries."""
    shape_width = shape_img.width
    shape_height = shape_img.height
    
    # Calculate the intersection of the shape with the canvas
    left = max(0, paste_x)
    top = max(0, paste_y)
    right = min(width, paste_x + shape_width)
    bottom = min(height, paste_y + shape_height)
    
    # Only draw if there's a visible area
    if right > left and bottom > top:
        # Calculate what part of the shape to use
        shape_left = left - paste_x
        shape_top = top - paste_y
        shape_right = shape_left + (right - left)
        shape_bottom = shape_top + (bottom - top)
        
        # Extract the visible part of the shape
        visible_shape = shape_img.crop((shape_left, shape_top, shape_right, shape_bottom))
        
        # Paste it onto the canvas
        img.paste(visible_shape, (left, top), visible_shape)

if __name__ == "__main__":
    # Example usage:
    create_pattern(
        width=4096,
        height=4096,
        base_scale=128,
        shape_width=128,
        shape_height=128,
        spacing=512,
        spacing_x=512,
        spacing_y=512,
        pattern_type="offset_grid",  # "grid", "offset_grid", "random", "spiral"
        shape_type="circle",         # "circle", "square", "triangle", "star", "custom"
        custom_image_path=None,      # Path to custom image if shape_type="custom"
        bg_color=(0, 0, 0, 255),     # Black background
        fg_color=(255, 0, 0, 255),   # Red foreground
        scale_randomization=0.0,     # No scale randomization
        base_rotation=0.0,           # No base rotation
        rotation_randomization=0.0,  # No rotation randomization
        output_file="my_polka_pattern.png",
        antialiasing=True,
        aa_scale=4
    )
    print("Pattern created and saved as 'my_polka_pattern.png'.")
