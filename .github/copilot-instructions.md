# Pac-Man Clone for Seeed Wio Terminal

## Project Overview

This project is a pixel-perfect clone of the original Pac-Man arcade game, built to run on the **Seeed Wio Terminal** using **CircuitPython 10.0.3**.

## Hardware Specifications

### Seeed Wio Terminal
- **MCU**: ATSAMD51P19 (ARM Cortex-M4F @ 120MHz, boost to 200MHz)
- **RAM**: 192 KB
- **External Flash**: 4 MB
- **Display**: 2.4" LCD, 320x240 pixels (we use vertical orientation: 240x320)
- **Input**: 5-way joystick switch (UP, DOWN, LEFT, RIGHT, PRESS) + 3 configurable buttons
- **Storage**: microSD card slot (used for sprites and assets)
- **Audio**: Buzzer only (no sound implementation needed)

### Display Orientation
- Physical screen is 320x240 (landscape)
- Game uses **vertical/portrait orientation**: 240 wide x 320 tall
- Original Pac-Man was 224x288 pixels
- Our implementation centers the 224x288 game area within 240x320, leaving a small border for a future bezel

### Input Mapping
```python
import board
from digitalio import DigitalInOut

UP = DigitalInOut(board.SWITCH_UP)      # Joystick up
DOWN = DigitalInOut(board.SWITCH_DOWN)  # Joystick down
LEFT = DigitalInOut(board.SWITCH_LEFT)  # Joystick left
RIGHT = DigitalInOut(board.SWITCH_RIGHT) # Joystick right
PRESS = DigitalInOut(board.SWITCH_PRESS) # Joystick press (center)

# Additional buttons available:
# board.BUTTON_1, board.BUTTON_2, board.BUTTON_3
```

**Note**: Buttons read `False` when pressed, `True` when released.

## CircuitPython Constraints

### Memory Management
- Limited RAM (192 KB) - be aggressive with garbage collection
- Use `gc.collect()` frequently to free memory
- Avoid creating unnecessary objects in game loops
- Prefer pre-allocated buffers over dynamic allocation
- Use `gc.mem_free()` for debugging memory issues

### Display API
- Use `displayio` for all graphics
- `board.DISPLAY` provides access to the built-in LCD
- Use `displayio.TileGrid` for sprite-based graphics
- Use `displayio.Bitmap` and `displayio.Palette` for indexed color images
- `display.rotation` can be set to 0, 90, 180, or 270 for orientation

### File Structure
```
CIRCUITPY/
├── code.py           # Main entry point (runs automatically)
├── boot.py           # Optional boot configuration
├── images/
│   └── pacman.bmp    # Sprite sheet with all Pac-Man sprites
└── lib/
    └── adafruit_imageload/  # Library for loading BMP images
```

### Sprite Sheet Usage
The existing `pacman.bmp` contains the original Pac-Man sprite sheet with 8x8 pixel tiles. Sprites are referenced by tile index in the TileGrid:

```python
sprite_sheet, palette = adafruit_imageload.load(
    "/images/pacman.bmp",
    bitmap=displayio.Bitmap,
    palette=displayio.Palette
)

# Create a 2x2 tile (16x16 pixel) sprite
pacman = displayio.TileGrid(
    sprite_sheet,
    pixel_shader=palette,
    width=2,
    height=2,
    tile_width=8,
    tile_height=8
)
```

## Original Pac-Man Specifications

### Screen Layout (224x288 pixels)
- Maze occupies most of the screen
- Score display at top
- Lives and fruit display at bottom
- 28 tiles wide x 36 tiles tall (8x8 pixel tiles)

### Game Elements
1. **Pac-Man**: 16x16 pixels, animated mouth (3 frames per direction)
2. **Ghosts**: Blinky (red), Pinky (pink), Inky (cyan), Clyde (orange) - 16x16 pixels each
3. **Dots**: Small dots (2x2 pixels) worth 10 points
4. **Power Pellets**: Large dots (8x8 pixels) worth 50 points, 4 total in corners
5. **Fruit**: Appears twice per level in center of maze
6. **Maze**: Blue walls on black background

### Ghost AI Behaviors
- **Blinky (Red)**: Chases Pac-Man directly
- **Pinky (Pink)**: Targets 4 tiles ahead of Pac-Man
- **Inky (Cyan)**: Complex targeting based on Blinky's position
- **Clyde (Orange)**: Chases when far, scatters when close

### Ghost Modes
- **Chase**: Ghosts actively pursue Pac-Man
- **Scatter**: Ghosts retreat to their home corners
- **Frightened**: After power pellet, ghosts turn blue and flee (can be eaten)

### Movement & Timing
- Pac-Man and ghosts move on an 8x8 tile grid
- Movement is pixel-by-pixel but constrained to grid intersections for turning
- Speed varies by level and game state

## Development Workflow

### Testing Changes
1. Edit `code.py` (and any supporting files)
2. Copy files to the CIRCUITPY drive mounted when Wio Terminal is connected via USB
3. The device auto-reloads when files change
4. Use serial console (115200 baud) for print debugging

### Sprint-Based Development
After each sprint/feature implementation:
1. Notify user that changes are ready for testing
2. User copies code to device
3. User provides feedback
4. Iterate based on feedback

## Code Style Guidelines

- Keep code modular with clear separation of concerns
- Use descriptive function and variable names
- Add comments for complex game logic (especially ghost AI)
- Prefer simple, readable code over clever optimizations (unless memory-critical)
- Use constants for magic numbers (tile sizes, speeds, colors, etc.)

## Key Implementation Notes

### Coordinate System
- Origin (0,0) is top-left of screen
- X increases to the right
- Y increases downward
- Game area centered: offset by (8, 16) pixels from screen edges to center 224x288 in 240x320

### Animation
- Use frame-based animation with time delays
- Pac-Man has 3 animation frames per direction (mouth open, half, closed)
- Ghosts have 2 animation frames (alternating feet)
- Frightened ghosts flash blue/white near end of power pellet

### Collision Detection
- Tile-based collision for walls
- Pixel or tile-based for dots/pellets
- Bounding box or center-point for ghost collision

## Resources

- [Wio Terminal CircuitPython Guide](https://wiki.seeedstudio.com/Wio-Terminal-CircuitPython/)
- [CircuitPython Downloads for Wio Terminal](https://circuitpython.org/board/seeeduino_wio_terminal/)
- [CircuitPython DisplayIO Guide](https://learn.adafruit.com/circuitpython-display-support-using-displayio)
- [The Pac-Man Dossier](https://www.gamedeveloper.com/design/the-pac-man-dossier) - Detailed original game mechanics
