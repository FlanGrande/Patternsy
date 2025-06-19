# Patternsy

Patternsy is a pattern generation tool that allows you to create various visual patterns with customizable shapes, arrangements, and colors.

## Features

- Create patterns with different shapes: circles, squares, triangles, stars, or custom images
- Arrange shapes in different patterns: grid, offset grid, random, or spiral
- Adjust size, spacing, rotation, and randomness parameters
- Choose custom colors for background and foreground
- Live preview of your pattern as you adjust settings
- Export patterns as PNG images

## Usage

### Command Line Interface

You can use Patternsy directly from the command line:

```python
python patternsy.py
```

This will generate a pattern with the default settings.

### Graphical User Interface

For more interactive pattern creation, use the GUI:

```python
python patternsy_ui.py
```

The GUI provides:

1. **Settings Panel** (left side):
   - Dimensions: Set the width and height of the output image
   - Shape Settings: Choose shape type, base scale, and spacing
   - Pattern Settings: Select the arrangement pattern
   - Randomization: Control scale and rotation randomness
   - Colors: Set background and foreground colors
   - Output: Specify the output filename

2. **Preview Panel** (right side):
   - Real-time preview of your pattern
   - Preview updates as you adjust settings

3. **Generate Button**:
   - Creates the full-resolution pattern and saves it to disk

## Examples

The repository includes some example patterns:
- `my_polka_pattern.png`: Basic polka dot pattern
- `random_triangles.png`: Randomly distributed triangles
- `spiral_stars.png`: Stars arranged in a spiral pattern

## Requirements

- Python 3.x
- PIL (Python Imaging Library) / Pillow
- Tkinter (for the GUI)

## Creating Executables

You can create standalone executables for Patternsy using Docker and PyInstaller. This approach allows you to create Windows executables from any platform and ensures consistent builds.

### Prerequisites

- Docker installed on your system
- Basic familiarity with Docker commands

### Creating Windows Executables

To create a Windows executable from any platform (Linux, macOS, or Windows), use the provided Dockerfile:

```bash
# Build the Docker image
docker build -f Dockerfile.windows -t patternsy-windows-builder .

# Run the container to create the executable
docker run --rm -v $(pwd)/dist:/app/dist patternsy-windows-builder
```

### What the Docker Build Does

The `Dockerfile.windows` uses a Wine-based Python environment to:
1. Install required Python packages (PyQt6, PyInstaller, Pillow)
2. Copy your application files
3. Use the PyInstaller spec file to build a Windows executable
4. Output the executable to the `dist/` directory

### Output Location

After running the Docker command, you'll find the Windows executable in:
- `dist/patternsy_ui.exe` - The GUI application executable

### Alternative: Native PyInstaller

If you're already on the target platform, you can use PyInstaller directly:

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed patternsy_ui.py
```

### Cross-Platform Notes

- The Docker approach is recommended for creating Windows executables from non-Windows systems
- Docker ensures consistent builds regardless of your host operating system
- The resulting executable includes all necessary dependencies and can run on Windows without Python installed

## License

See the LICENSE file for details.
