#!/usr/bin/env python3

import math
import random
import os
from PIL import Image, ImageDraw, ImageOps

def create_pattern(
        width=1200,
        height=1200,
        base_scale=32,
        spacing=128,
        pattern_type="offset_grid",
        shape_type="circle",
        custom_image_path=None,
        bg_color=(0, 0, 0, 255),
        fg_color=(255, 0, 0, 255),
        scale_randomization=0.0,
        base_rotation=0.0,
        rotation_randomization=0.0,
        output_file="pattern.png",
        aa_factor=4  # Anti-aliasing factor
):
    """
    Create a pattern with various shapes and arrangements.
    
    Parameters:
    - width, height: dimensions of the output image
    - base_scale: base size of the shapes
    - spacing: distance between shapes
    - pattern_type: "grid", "offset_grid", "random", "spiral"
    - shape_type: "circle", "square", "triangle", "star", "custom"
    - custom_image_path: path to custom image (used when shape_type="custom")
    - bg_color: background color as (R,G,B,A) tuple
    - fg_color: foreground color as (R,G,B,A) tuple
    - scale_randomization: random variation in shape size (0.0-1.0)
    - base_rotation: base rotation for all shapes in degrees
    - rotation_randomization: random variation in rotation (0.0-1.0)
    - output_file: filename for the output image
    - aa_factor: anti-aliasing factor
    """
    
    # Create a new image with the specified background color
    img = Image.new("RGBA", (width, height), bg_color)
    
    # Generate pattern coordinates based on selected pattern type
    coordinates = generate_pattern_coordinates(
        width, height, spacing, pattern_type
    )
    
    # Draw shapes at each coordinate
    for x, y in coordinates:
        # Apply scale randomization if specified
        if scale_randomization > 0:
            scale_factor = 1.0 - (scale_randomization * random.uniform(-1, 1))
            current_scale = int(base_scale * scale_factor)
            # Ensure minimum size
            current_scale = max(current_scale, 4)
        else:
            current_scale = base_scale
            
        # Apply rotation randomization if specified
        if rotation_randomization > 0:
            rotation_range = 360 * rotation_randomization
            current_rotation = base_rotation + random.uniform(-rotation_range/2, rotation_range/2)
        else:
            current_rotation = base_rotation
        
        # Draw the shape
        shape_img = create_shape(
            shape_type, current_scale, fg_color, current_rotation, 
            custom_image_path, aa_factor
        )
        
        # Calculate paste position (centered on the coordinate)
        paste_x = int(x - shape_img.width / 2)
        paste_y = int(y - shape_img.height / 2)
        
        # Paste the shape onto the main image
        img.paste(shape_img, (paste_x, paste_y), shape_img)
    
    # Convert to RGB and save the resulting image
    img = img.convert("RGB")
    img.save(output_file)

def generate_pattern_coordinates(width, height, spacing, pattern_type):
    """Generate coordinates for shapes based on the specified pattern type."""
    coordinates = []
    
    if pattern_type == "grid":
        # Simple grid pattern
        for y in range(spacing // 2, height, spacing):
            for x in range(spacing // 2, width, spacing):
                coordinates.append((x, y))
                
    elif pattern_type == "offset_grid":
        # Grid pattern with every other row offset (original polka dot pattern)
        for row_index, y in enumerate(range(spacing // 2, height, spacing)):
            row_offset = (spacing // 2) if row_index % 2 == 1 else 0
            for x in range(spacing // 2 + row_offset, width, spacing):
                coordinates.append((x, y))
                
    elif pattern_type == "random":
        # Random distribution
        num_shapes = (width // spacing) * (height // spacing)
        # Add 20% more for better coverage
        num_shapes = int(num_shapes * 1.2)
        
        # Ensure minimum spacing between shapes
        min_spacing = spacing // 2
        
        for _ in range(num_shapes):
            # Try up to 10 times to find a non-overlapping position
            for attempt in range(10):
                x = random.randint(min_spacing, width - min_spacing)
                y = random.randint(min_spacing, height - min_spacing)
                
                # Check if this point is far enough from all existing points
                too_close = False
                for ex, ey in coordinates:
                    distance = math.sqrt((ex - x)**2 + (ey - y)**2)
                    if distance < min_spacing:
                        too_close = True
                        break
                        
                if not too_close:
                    coordinates.append((x, y))
                    break
                    
    elif pattern_type == "spiral":
        # Spiral pattern
        center_x, center_y = width // 2, height // 2
        max_radius = min(width, height) // 2
        
        a = spacing / (2 * math.pi)  # Controls spacing between spiral arms
        b = spacing / 10  # Controls how quickly spiral expands
        
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

def create_shape(shape_type, scale, color, rotation, custom_image_path, aa_factor):
    """Create a shape image based on the specified shape type."""
    # Size with anti-aliasing factor applied
    aa_size = scale * aa_factor
    
    # Create a transparent image for the shape
    temp_img = Image.new("RGBA", (aa_size, aa_size), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    if shape_type == "circle":
        # Draw a circle
        temp_draw.ellipse([0, 0, aa_size - 1, aa_size - 1], fill=color)
        
    elif shape_type == "square":
        # Draw a square
        temp_draw.rectangle([0, 0, aa_size - 1, aa_size - 1], fill=color)
        
    elif shape_type == "triangle":
        # Draw a triangle (pointing up)
        points = [
            (aa_size // 2, 0),  # Top
            (0, aa_size - 1),   # Bottom left
            (aa_size - 1, aa_size - 1)  # Bottom right
        ]
        temp_draw.polygon(points, fill=color)
        
    elif shape_type == "star":
        # Draw a five-pointed star
        points = []
        center = aa_size // 2
        outer_radius = aa_size // 2
        inner_radius = outer_radius // 2
        
        for i in range(10):
            # Alternate between outer and inner radius
            radius = outer_radius if i % 2 == 0 else inner_radius
            angle = math.pi / 5 * i - math.pi / 2
            x = center + radius * math.cos(angle)
            y = center + radius * math.sin(angle)
            points.append((x, y))
            
        temp_draw.polygon(points, fill=color)
        
    elif shape_type == "custom" and custom_image_path and os.path.exists(custom_image_path):
        # Use a custom image
        try:
            # Load the custom image
            custom_img = Image.open(custom_image_path).convert("RGBA")
            # Resize to match our anti-aliased size
            custom_img = custom_img.resize((aa_size, aa_size), Image.LANCZOS)
            # Replace temp_img with the custom image
            temp_img = custom_img
        except Exception as e:
            print(f"Error loading custom image: {e}")
            # Fallback to a circle if the custom image fails
            temp_draw.ellipse([0, 0, aa_size - 1, aa_size - 1], fill=color)
    else:
        # Default to circle if shape type not recognized or custom image fails
        temp_draw.ellipse([0, 0, aa_size - 1, aa_size - 1], fill=color)
    
    # Apply rotation if needed
    if rotation != 0:
        temp_img = temp_img.rotate(rotation, resample=Image.BICUBIC, expand=False)
    
    # Resize with anti-aliasing back to original scale
    temp_img = temp_img.resize((scale, scale), Image.LANCZOS)
    
    return temp_img

if __name__ == "__main__":
    # Example usage:
    create_pattern(
        width=4096,
        height=4096,
        base_scale=128,
        spacing=512,
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
