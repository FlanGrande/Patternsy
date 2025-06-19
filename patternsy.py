#!/usr/bin/env python3

import math
import random
import os
from PIL import Image, ImageDraw, ImageOps, ImageFilter

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
        output_file="pattern.png"
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
    """
    
    # Use shape_width and shape_height if provided, otherwise fall back to base_scale
    if shape_width is None:
        shape_width = base_scale
    if shape_height is None:
        shape_height = base_scale
    
    # Use spacing_x and spacing_y if provided, otherwise fall back to spacing
    if spacing_x is None:
        spacing_x = spacing
    if spacing_y is None:
        spacing_y = spacing
    
    # Create a new image with the specified background color
    img = Image.new("RGBA", (width, height), bg_color)
    
    # Generate pattern coordinates based on selected pattern type
    coordinates = generate_pattern_coordinates(
        width, height, spacing_x, spacing_y, pattern_type
    )
    
    # Draw shapes at each coordinate with tiling support
    max_shape_size = max(shape_width, shape_height)
    
    for x, y in coordinates:
        # Apply scale randomization if specified
        if scale_randomization > 0:
            scale_factor = 1.0 - (scale_randomization * random.uniform(-1, 1))
            current_shape_width = int(shape_width * scale_factor)
            current_shape_height = int(shape_height * scale_factor)
            # Ensure minimum size
            current_shape_width = max(current_shape_width, 1)
            current_shape_height = max(current_shape_height, 1)
        else:
            current_shape_width = shape_width
            current_shape_height = shape_height
            
        # Apply rotation randomization if specified
        if rotation_randomization > 0:
            rotation_range = 360 * rotation_randomization
            current_rotation = base_rotation + random.uniform(-rotation_range/2, rotation_range/2)
        else:
            current_rotation = base_rotation
        
        # Draw the shape
        shape_img = create_shape(
            shape_type, current_shape_width, current_shape_height, fg_color, current_rotation, 
            custom_image_path
        )
        
        # Calculate paste position (centered on the coordinate)
        paste_x = int(x - shape_img.width / 2)
        paste_y = int(y - shape_img.height / 2)
        
        # Draw the shape with tiling - handle wrapping for seamless tiling
        draw_shape_with_tiling(img, shape_img, paste_x, paste_y, width, height)
    
    # Convert to RGB and save the resulting image
    img = img.convert("RGB")
    img.save(output_file)
    print(f"Pattern saved as {output_file}")
    return img

def generate_pattern_coordinates(width, height, spacing_x, spacing_y, pattern_type):
    """Generate coordinates for shapes based on the specified pattern type with seamless tiling support."""
    coordinates = []
    
    if pattern_type == "grid":
        # Simple grid pattern with seamless tiling
        for y in range(0, height + spacing_y, spacing_y):
            for x in range(0, width + spacing_x, spacing_x):
                coordinates.append((x, y))
                
    elif pattern_type == "offset_grid":
        # Grid pattern with every other row offset for seamless tiling
        for row_index, y in enumerate(range(0, height + spacing_y, spacing_y)):
            if row_index % 2 == 1:
                # Offset row
                row_offset = spacing_x // 2
                for x in range(row_offset, width + spacing_x + row_offset, spacing_x):
                    coordinates.append((x, y))
            else:
                # Regular row
                for x in range(0, width + spacing_x, spacing_x):
                    coordinates.append((x, y))
                
    elif pattern_type == "random":
        # Random distribution with tiling considerations
        # Use fixed seed based on canvas dimensions for consistent tiling
        random.seed(hash((width, height, spacing_x, spacing_y)))
        
        num_shapes = (width // spacing_x) * (height // spacing_y)
        num_shapes = int(num_shapes * 1.2)
        
        min_spacing_x = spacing_x // 3
        min_spacing_y = spacing_y // 3
        
        for _ in range(num_shapes):
            for attempt in range(20):
                x = random.randint(0, width)
                y = random.randint(0, height)
                
                # Check if this point is far enough from all existing points
                # considering tiling wraparound
                too_close = False
                for ex, ey in coordinates:
                    # Calculate distance considering tiling
                    dx = min(abs(ex - x), width - abs(ex - x))
                    dy = min(abs(ey - y), height - abs(ey - y))
                    
                    if dx < min_spacing_x and dy < min_spacing_y:
                        too_close = True
                        break
                        
                if not too_close:
                    coordinates.append((x, y))
                    break
        
        # Reset random seed
        random.seed()
                    
    elif pattern_type == "spiral":
        # Spiral pattern with tiling considerations
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        a = spacing_x / (2 * math.pi)
        b = spacing_y / 20
        
        t = 0
        while True:
            r = a * t
            if r > max_radius * 1.5:  # Extend beyond center for better tiling
                break
                
            x = center_x + r * math.cos(t)
            y = center_y + r * math.sin(t)
            
            # Add coordinates even if they're outside the immediate canvas
            # The tiling function will handle wrapping
            coordinates.append((int(x), int(y)))
                
            t += b / r if r > 0 else b
    
    return coordinates

def create_shape(shape_type, shape_width, shape_height, color, rotation, custom_image_path):
    """Create a shape image based on the specified shape type."""
    # Create a transparent image for the shape
    shape_img = Image.new("RGBA", (shape_width, shape_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shape_img)
    
    if shape_type == "circle":
        aa_scale = 8
        large_size = max(shape_width, shape_height) * aa_scale
        large_img = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
        large_draw = ImageDraw.Draw(large_img)
        
        # Draw a circle on the larger image
        large_draw.ellipse([0, 0, large_size - 1, large_size - 1], fill=color)
        
        # Apply a subtle blur for smoother edges
        large_img = large_img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Resize down with antialiasing
        shape_img = large_img.resize((shape_width, shape_height), Image.Resampling.LANCZOS)
        
    elif shape_type == "square":
        # Draw a square
        draw.rectangle([0, 0, shape_width - 1, shape_height - 1], fill=color)
        
    elif shape_type == "triangle":
        # Draw a triangle (pointing up)
        points = [
            (shape_width // 2, 0),       # Top
            (0, shape_height - 1),        # Bottom left
            (shape_width - 1, shape_height - 1)  # Bottom right
        ]
        draw.polygon(points, fill=color)
        
    elif shape_type == "star":
        # Draw a five-pointed star
        points = []
        center_x = shape_width // 2
        center_y = shape_height // 2
        outer_radius = min(shape_width, shape_height) // 2
        inner_radius = outer_radius // 2
        
        for i in range(10):
            # Alternate between outer and inner radius
            radius = outer_radius if i % 2 == 0 else inner_radius
            angle = math.pi / 5 * i - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            points.append((x, y))
            
        draw.polygon(points, fill=color)
        
    elif shape_type == "custom" and custom_image_path and os.path.exists(custom_image_path):
        # Use a custom image
        try:
            # Load the custom image
            custom_img = Image.open(custom_image_path).convert("RGBA")
            # Resize to match our size
            custom_img = custom_img.resize((shape_width, shape_height), Image.LANCZOS)
            # Replace shape_img with the custom image
            shape_img = custom_img
        except Exception as e:
            print(f"Error loading custom image: {e}")
            # Fallback to a circle if the custom image fails
            draw.ellipse([0, 0, shape_width - 1, shape_height - 1], fill=color)
    else:
        # Default to circle if shape type not recognized or custom image fails
        draw.ellipse([0, 0, shape_width - 1, shape_height - 1], fill=color)
    
    # Apply rotation if needed
    if rotation != 0:
        shape_img = shape_img.rotate(rotation, resample=Image.BICUBIC, expand=False)
    
    return shape_img

def draw_shape_with_tiling(img, shape_img, paste_x, paste_y, width, height):
    """Draw a shape with seamless tiling support - handles wrapping at canvas edges."""
    shape_width = shape_img.width
    shape_height = shape_img.height
    
    # Calculate all positions where this shape needs to be drawn to ensure seamless tiling
    positions = []
    
    # Original position
    positions.append((paste_x, paste_y))
    
    # Handle horizontal wrapping
    if paste_x < 0:
        positions.append((paste_x + width, paste_y))
    elif paste_x + shape_width > width:
        positions.append((paste_x - width, paste_y))
    
    # Handle vertical wrapping
    if paste_y < 0:
        positions.append((paste_x, paste_y + height))
    elif paste_y + shape_height > height:
        positions.append((paste_x, paste_y - height))
    
    # Handle corner wrapping (both horizontal and vertical)
    if paste_x < 0 and paste_y < 0:
        positions.append((paste_x + width, paste_y + height))
    elif paste_x < 0 and paste_y + shape_height > height:
        positions.append((paste_x + width, paste_y - height))
    elif paste_x + shape_width > width and paste_y < 0:
        positions.append((paste_x - width, paste_y + height))
    elif paste_x + shape_width > width and paste_y + shape_height > height:
        positions.append((paste_x - width, paste_y - height))
    
    # Draw the shape at all calculated positions
    for pos_x, pos_y in positions:
        # Only draw if the shape would be visible within the canvas
        if (pos_x + shape_width > 0 and pos_x < width and 
            pos_y + shape_height > 0 and pos_y < height):
            
            # Create a cropped version of the shape if it extends beyond canvas
            if (pos_x < 0 or pos_y < 0 or 
                pos_x + shape_width > width or pos_y + shape_height > height):
                
                # Calculate crop boundaries
                crop_left = max(0, -pos_x)
                crop_top = max(0, -pos_y)
                crop_right = min(shape_width, width - pos_x)
                crop_bottom = min(shape_height, height - pos_y)
                
                if crop_right > crop_left and crop_bottom > crop_top:
                    cropped_shape = shape_img.crop((crop_left, crop_top, crop_right, crop_bottom))
                    final_x = max(0, pos_x)
                    final_y = max(0, pos_y)
                    img.paste(cropped_shape, (final_x, final_y), cropped_shape)
            else:
                # Shape fits entirely within canvas
                img.paste(shape_img, (pos_x, pos_y), shape_img)

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
        output_file="my_polka_pattern.png"
    )
    print("Pattern created and saved as 'my_polka_pattern.png'.")
