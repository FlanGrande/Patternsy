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

You can create standalone executables for Patternsy using PyInstaller. This allows you to run the application without requiring Python to be installed on the target system.

### Prerequisites

First, install PyInstaller:

```bash
pip install pyinstaller
```

### Creating the Executable

To create an executable for the GUI version:

```bash
pyinstaller --onefile --windowed patternsy_ui.py
```

For the command-line version:

```bash
pyinstaller --onefile patternsy.py
```

### Command Options Explained

- `--onefile`: Creates a single executable file instead of a directory with multiple files
- `--windowed`: (GUI only) Prevents a console window from appearing when running the GUI application

### Output Location

The executable will be created in the `dist/` directory:
- Linux/macOS: `dist/patternsy_ui` or `dist/patternsy`
- Windows: `dist/patternsy_ui.exe` or `dist/patternsy.exe`

### Cross-Platform Notes

- Executables are platform-specific (Windows executables won't run on Linux/macOS and vice versa)
- To create executables for different platforms, you need to run PyInstaller on each target platform
- The executable includes all necessary dependencies, making it portable within the same platform

## License

See the LICENSE file for details.
