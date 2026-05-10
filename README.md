# Patternsy

Interactive seamless pattern generator. Place shapes on a canvas, adjust them individually or in bulk, and export tileable PNG images.

Built with Dear ImGui (`imgui-bundle`) and Pillow.

## Features

- **5 pattern types:** grid, offset grid, diagonal grid, random, spiral
- **5 shape types:** circle, square, triangle, star, custom image
- **Interactive canvas:** click to select, drag to move, box-select multiple shapes
- **Per-point editing:** each shape has its own position, size, rotation, and color — editable individually or in bulk
- **Delta model:** manual edits survive pattern regeneration (base position updates, your overrides are preserved)
- **Locked points:** lock individual shapes to prevent accidental dragging
- **Tiling preview:** ghost copies at canvas edges show seamless tile behaviour in real time
- **Undo/redo:** full history stack (Ctrl+Z / Ctrl+Y)
- **Export:** full-resolution PNG with 4× supersampled antialiasing
- **Save/load:** project state as JSON (File menu or Ctrl+S / Ctrl+O)

## Requirements

- Python 3.11+
- `imgui-bundle`
- `Pillow`
- `numpy`

```bash
pip install imgui-bundle Pillow numpy
```

## Running

```bash
python3 -m patternsy.main
```

## Controls

| Action | Input |
|---|---|
| Select shape | Left click |
| Add to selection | Shift + left click |
| Box select | Left drag on empty space |
| Move selected | Left drag on shape |
| Pan canvas | Middle mouse drag |
| Zoom | Scroll wheel |
| Fit view | F |
| Select all | Ctrl+A |
| Deselect | Escape |
| Delete selected | Delete |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Save project | Ctrl+S |
| Load project | Ctrl+O |
| Export image | Ctrl+E |

## Pattern Types

| Type | Description |
|---|---|
| **grid** | Regular uniform grid |
| **offset_grid** | Brick/honeycomb — odd rows shift by half spacing |
| **diagonal_grid** | Each row shifts by a configurable pixel offset, creating diagonal lines |
| **random** | Poisson-disk-style rejection sampling with minimum spacing |
| **spiral** | Archimedean spiral from center outward |

## Creating Executables

### Windows (via Docker + Wine)

```bash
# Build the Docker image
docker build -f Dockerfile.windows -t patternsy-windows-builder .

# Run to produce dist/patternsy.exe
docker run --rm -v $(pwd)/dist:/app/dist patternsy-windows-builder
```

### Native (any platform)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name patternsy patternsy/main.py
```

The executable will be in `dist/patternsy` (Linux/macOS) or `dist/patternsy.exe` (Windows).

## License

See the LICENSE file for details.
