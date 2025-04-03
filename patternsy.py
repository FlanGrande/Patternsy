#!/usr/bin/env python3

def create_polka_dot_pattern(
		width=1200,
		height=1200,
		dot_size=32,
		spacing=128,
		output_file="polka_pattern.png",
		aa_factor=4  # Anti-aliasing factor
):
	from PIL import Image, ImageDraw
	
	# Create a new image with a black background
	img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
	
	# Calculate the radius of each dot
	radius = dot_size // 2
	
	# Draw dots in a grid pattern with every two rows offset
	for row_index, y in enumerate(range(spacing // 2, height, spacing)):
		# Determine if this row should be offset (every other row)
		row_offset = (spacing // 2) if row_index % 2 == 1 else 0
		
		for x in range(spacing // 2 + row_offset, width, spacing):
			# Create a temporary image at higher resolution for anti-aliasing
			temp_size = dot_size * aa_factor
			temp_radius = temp_size // 2
			
			# Create a temporary image with transparent background
			temp_img = Image.new("RGBA", (temp_size, temp_size), (0, 0, 0, 0))
			temp_draw = ImageDraw.Draw(temp_img)
			
			# Draw the dot on the temporary image
			temp_draw.ellipse(
				[0, 0, temp_size - 1, temp_size - 1],
				fill=(255, 0, 0, 255)  # Red with full opacity
			)
			
			# Resize with anti-aliasing
			temp_img = temp_img.resize((dot_size, dot_size), Image.LANCZOS)
			
			# Calculate paste position
			paste_x = x - radius
			paste_y = y - radius
			
			# Paste the anti-aliased dot onto the main image
			img.paste(temp_img, (paste_x, paste_y), temp_img)
	
	# Convert to RGB and save the resulting image
	img = img.convert("RGB")
	img.save(output_file)

if __name__ == "__main__":
	# Example usage:
	# You can adjust the spacing and dot size here to see different results.
	create_polka_dot_pattern(
		width=4096,
		height=4096,
		dot_size=128,
		spacing=512,
		output_file="my_polka_pattern.png"
	)
	print("Pattern created and saved as 'my_polka_pattern.png'.")
