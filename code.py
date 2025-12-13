"""
Pac-Man Clone for Seeed Wio Terminal
CircuitPython 10.0.3
"""

import board
import displayio
# import adafruit_imageload
import gc
import time
import random
from digitalio import DigitalInOut, Pull

# =============================================================================
# CONSTANTS
# =============================================================================

# Screen dimensions (vertical orientation)
SCREEN_WIDTH = 240
SCREEN_HEIGHT = 320

# Game area dimensions (from sprite sheet)
GAME_WIDTH = 224
GAME_HEIGHT = 248

# Offset to center game area in screen
OFFSET_X = (SCREEN_WIDTH - GAME_WIDTH) // 2   # 8 pixels
OFFSET_Y = (SCREEN_HEIGHT - GAME_HEIGHT) // 2  # 36 pixels

# Tile dimensions
TILE_SIZE = 8

# Maze dimensions in tiles
MAZE_COLS = 28
MAZE_ROWS = 31

# Movement
PACMAN_SPEED = 1.25  # pixels per frame
GHOST_SPEED = 1.17   # pixels per frame (approx 94% of Pac-Man speed)
FRAME_DELAY = 0.008  # ~100 FPS target

# Directions
DIR_NONE = 0
DIR_UP = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIR_RIGHT = 4

# Maze tile types
EMPTY = 0
WALL = 1
DOT = 2
POWER = 3
GATE = 4

# =============================================================================
# MAZE DATA - Collision map generated from maze_empty.bmp
# 1 = wall, 0 = path/dot
# =============================================================================

MAZE_DATA = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# =============================================================================
# INPUT SETUP
# =============================================================================

UP = DigitalInOut(board.SWITCH_UP)
UP.switch_to_input(pull=Pull.UP)
DOWN = DigitalInOut(board.SWITCH_DOWN)
DOWN.switch_to_input(pull=Pull.UP)
LEFT = DigitalInOut(board.SWITCH_LEFT)
LEFT.switch_to_input(pull=Pull.UP)
RIGHT = DigitalInOut(board.SWITCH_RIGHT)
RIGHT.switch_to_input(pull=Pull.UP)
PRESS = DigitalInOut(board.SWITCH_PRESS)
PRESS.switch_to_input(pull=Pull.UP)

# =============================================================================
# DISPLAY SETUP
# =============================================================================

# Set up display (vertical orientation, flipped 180 from before)
display = board.DISPLAY
display.rotation = 270

# Main display group
main_group = displayio.Group()
display.show(main_group)

# =============================================================================
# LOAD MAZE BACKGROUND
# =============================================================================

# Load the empty maze (no dots) using OnDiskBitmap to save RAM
# We keep the file open for the duration of the program
maze_file = open("/images/maze_empty.bmp", "rb")
maze_bmp = displayio.OnDiskBitmap(maze_file)
maze_palette = maze_bmp.pixel_shader

# Create maze background as TileGrid
maze_bg = displayio.TileGrid(
    maze_bmp,
    pixel_shader=maze_palette,
    x=OFFSET_X,
    y=OFFSET_Y
)
main_group.append(maze_bg)

# =============================================================================
# ITEMS GRID (DOTS & POWER PELLETS)
# =============================================================================

# Create a bitmap for items:
# Tile 0: Empty
# Tile 1: Small Dot
# Tile 2: Power Pellet
items_bitmap = displayio.Bitmap(8, 24, 3) # 8 wide, 24 tall (3 tiles), 3 colors (though we only use 1 index)

# Draw Small Dot (Tile 1, y=8..15)
# 2x2 pixel dot in center
items_bitmap[3, 11] = 1
items_bitmap[4, 11] = 1
items_bitmap[3, 12] = 1
items_bitmap[4, 12] = 1

# Draw Power Pellet (Tile 2, y=16..23)
# 6x6 circle-ish (rounded corners)
for x in range(1, 7):
    for y in range(17, 23):
        # Skip corners to make it round
        if (x == 1 or x == 6) and (y == 17 or y == 22):
            continue
        items_bitmap[x, y] = 2

# Palette for items
items_palette = displayio.Palette(3)
items_palette[0] = 0x000000 # Transparent
items_palette[1] = 0xFFB8AE # Salmon/White (Dot)
items_palette[2] = 0xFFB8AE # Salmon/White (Power Pellet)
items_palette.make_transparent(0)

items_grid = displayio.TileGrid(
    items_bitmap,
    pixel_shader=items_palette,
    width=MAZE_COLS,
    height=MAZE_ROWS,
    tile_width=8,
    tile_height=8,
    x=OFFSET_X,
    y=OFFSET_Y
)

# Populate items_grid based on MAZE_DATA
POWER_PELLETS = [(1, 3), (26, 3), (1, 23), (26, 23)]

# Flood fill to find reachable tiles (avoids placing dots in unreachable islands)
reachable = set()
queue = [(14, 23)] # Start at Pac-Man's position
reachable.add((14, 23))

while queue:
    cx, cy = queue.pop(0)
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = cx + dx, cy + dy
        if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS:
            if MAZE_DATA[ny][nx] != WALL and (nx, ny) not in reachable:
                reachable.add((nx, ny))
                queue.append((nx, ny))

for y in range(MAZE_ROWS):
    for x in range(MAZE_COLS):
        if MAZE_DATA[y][x] == 0 and (x, y) in reachable: # Path and Reachable
            # Check exclusions
            # Ghost house interior (approx rows 13-15, cols 10-17)
            is_ghost_house = (10 <= x <= 17) and (13 <= y <= 15)
            # Ghost house door (row 12, cols 13-14)
            is_ghost_door = (y == 12) and (13 <= x <= 14)
            # Tunnels
            is_tunnel = (y == 14) and (x < 6 or x > 21)
            
            if (x, y) in POWER_PELLETS:
                items_grid[x, y] = 2 # Power Pellet
            elif not is_ghost_house and not is_ghost_door and not is_tunnel:
                items_grid[x, y] = 1 # Small Dot
            else:
                items_grid[x, y] = 0 # Empty
        else:
            items_grid[x, y] = 0 # Empty

main_group.append(items_grid)

# =============================================================================
# POWER PELLET BLINKING (COVERS)
# =============================================================================

# We use 4 small 8x8 black tiles to cover the power pellets when they "blink off".
# This is much faster than updating the global palette which causes full redraws.

cover_bmp = displayio.Bitmap(8, 8, 1)
cover_palette = displayio.Palette(1)
cover_palette[0] = 0x000000 # Black

pellet_covers = []
for tx, ty in POWER_PELLETS:
    tg = displayio.TileGrid(
        cover_bmp,
        pixel_shader=cover_palette,
        x=OFFSET_X + tx * 8,
        y=OFFSET_Y + ty * 8
    )
    tg.hidden = True # Start hidden (pellet visible)
    main_group.append(tg)
    pellet_covers.append(tg)

gc.collect()

# =============================================================================
# LOAD SPRITE SHEET
# =============================================================================

# Use OnDiskBitmap to save RAM and avoid allocation issues
sprite_sheet = displayio.OnDiskBitmap("/images/sprites.bmp")
sprite_palette = sprite_sheet.pixel_shader

print(f"Sprite Sheet Dimensions: {sprite_sheet.width}x{sprite_sheet.height}")

# Make black transparent for sprites
# OnDiskBitmap.pixel_shader is a Palette for indexed BMPs
try:
    sprite_palette.make_transparent(0)
except AttributeError:
    print("Warning: Could not set transparency (not a Palette?)")

gc.collect()

# =============================================================================
# PAC-MAN CLASS
# =============================================================================

class PacMan:
    """Pac-Man player character."""
    
    # Sprite positions in sprites.bmp (16x16 sprites)
    # Based on actual sprite sheet analysis:
    # Row 0: RIGHT animations, then UP animations
    # Row 1: LEFT animations  
    # Row 2: DOWN animations
    # Format: (x, y) pixel position in sprite sheet
    # Order: open mouth, half open, closed (full circle at 32,0)
    FRAMES = {
        DIR_RIGHT: [(0, 0), (16, 0), (32, 0)],      # Right: Row 0
        DIR_LEFT: [(0, 16), (16, 16), (32, 0)],     # Left: Row 1
        DIR_UP: [(0, 32), (16, 32), (32, 0)],       # Up: Row 2
        DIR_DOWN: [(0, 48), (16, 48), (32, 0)],     # Down: Row 3
    }
    
    def __init__(self):
        # Create sprite using TileGrid (1x2 tiles of 16x8 = 16x16 sprite)
        # Optimization: Use 16x8 tiles to handle non-16-divisible bitmap height (248px)
        self.sprite = displayio.TileGrid(
            sprite_sheet,
            pixel_shader=sprite_palette,
            width=1,
            height=2,
            tile_width=16,
            tile_height=8
        )
        
        # Starting position
        # User confirmed (106, 181) looks perfect visually
        # Center is at (114, 189), which is in tile (14, 23)
        self.tile_x = 14
        self.tile_y = 23
        self.x = 106
        self.y = 181
        
        # Movement
        self.direction = DIR_NONE
        self.next_direction = DIR_NONE
        
        # Animation
        self.anim_frame = 0
        self.anim_timer = 0
        
        # Set initial frame and position
        self.set_frame(DIR_RIGHT, 0)
        self.update_sprite_pos()
    
    def set_frame(self, direction, frame_idx):
        """Set sprite tiles based on direction and animation frame."""
        if direction == DIR_NONE:
            direction = DIR_RIGHT
        
        frames = self.FRAMES.get(direction, self.FRAMES[DIR_RIGHT])
        fx, fy = frames[frame_idx % 3]
        
        # Convert pixel position to tile indices (16x8 tiles)
        # Sprite sheet is 224 pixels wide = 14 tiles of 16x8
        tiles_per_row = sprite_sheet.width // 16
        base_tile = (fy // 8) * tiles_per_row + (fx // 16)
        
        self.sprite[0, 0] = base_tile
        self.sprite[0, 1] = base_tile + tiles_per_row
    
    def update_sprite_pos(self):
        """Update sprite screen position."""
        self.sprite.x = int(OFFSET_X + self.x)
        self.sprite.y = int(OFFSET_Y + self.y)
    
    def can_move(self, direction):
        """Check if movement in direction is possible."""
        next_x = self.x
        next_y = self.y
        
        if direction == DIR_UP:
            next_y -= PACMAN_SPEED
        elif direction == DIR_DOWN:
            next_y += PACMAN_SPEED
        elif direction == DIR_LEFT:
            next_x -= PACMAN_SPEED
        elif direction == DIR_RIGHT:
            next_x += PACMAN_SPEED
        else:
            return False
        
        # Calculate center of sprite for next position
        center_x = next_x + 8
        center_y = next_y + 8
        
        # STRICT TUNNEL CHECK
        # If we are in the tunnel (horizontally outside or near edge), disallow vertical movement
        # Tunnel is row 14.
        # Maze width is 224 (28 tiles * 8).
        # Left entrance: x < 8 (Tile 0)
        # Right entrance: x > 216 (Tile 27)
        if center_x < 8 or center_x > 216:
            if direction == DIR_UP or direction == DIR_DOWN:
                return False

        # Tunnel wrap check (allow moving horizontally out of bounds)
        if next_x < -8 or next_x >= GAME_WIDTH - 8:
            return True
            
        # Standard Wall Collision
        # Offset sensor in direction of movement
        SENSOR_OFFSET = 3
        
        if direction == DIR_UP:
            check_x = center_x
            check_y = center_y - SENSOR_OFFSET
        elif direction == DIR_DOWN:
            check_x = center_x
            check_y = center_y + SENSOR_OFFSET
        elif direction == DIR_LEFT:
            check_x = center_x - SENSOR_OFFSET
            check_y = center_y
        elif direction == DIR_RIGHT:
            check_x = center_x + SENSOR_OFFSET
            check_y = center_y
            
        tx = int(check_x // TILE_SIZE)
        ty = int(check_y // TILE_SIZE)
        
        # Bounds check
        if tx < 0 or tx >= MAZE_COLS:
            # We are in the tunnel columns
            if ty == 14:
                return True
            return False
        
        if ty < 0 or ty >= MAZE_ROWS:
            return False
            
        # Ghost House Door Check
        if ty == 12 and (tx == 13 or tx == 14):
            return False
            
        return MAZE_DATA[ty][tx] != WALL

    def can_turn(self, direction):
        """Check if we can turn into the NEXT tile.
        Unlike can_move, this checks the tile grid directly to prevent
        turning into a wall even if we have pixel overlap space.
        """
        target_tx = int(self.tile_x)
        target_ty = int(self.tile_y)
        
        if direction == DIR_UP:
            target_ty -= 1
        elif direction == DIR_DOWN:
            target_ty += 1
        elif direction == DIR_LEFT:
            target_tx -= 1
        elif direction == DIR_RIGHT:
            target_tx += 1
        
        # Bounds/Tunnel check for turning
        if target_tx < 0 or target_tx >= MAZE_COLS:
            return target_ty == 14 # Only allow turning into tunnel row
            
        if target_ty < 0 or target_ty >= MAZE_ROWS:
            return False
            
        # Ghost House Door Check
        if target_ty == 12 and (target_tx == 13 or target_tx == 14):
            return False
            
        return MAZE_DATA[target_ty][target_tx] != WALL
    
    def at_tile_center(self):
        """Check if we are close enough to a tile center to turn."""
        center_x = self.x + 8
        center_y = self.y + 8
        
        # Get distance to nearest tile center (which are at 4, 12, 20...)
        # (val - 4) % 8 should be close to 0
        dist_x = abs((center_x - 4) % 8)
        dist_y = abs((center_y - 4) % 8)
        
        # Handle wrap-around for modulo (e.g. 7 is close to 0 mod 8)
        dist_x = min(dist_x, 8 - dist_x)
        dist_y = min(dist_y, 8 - dist_y)
        
        # Use <= to allow snapping even if we are 1 frame away
        return dist_x <= PACMAN_SPEED and dist_y <= PACMAN_SPEED

    def is_opposite(self, dir1, dir2):
        """Check if two directions are opposite."""
        return ((dir1 == DIR_UP and dir2 == DIR_DOWN) or
                (dir1 == DIR_DOWN and dir2 == DIR_UP) or
                (dir1 == DIR_LEFT and dir2 == DIR_RIGHT) or
                (dir1 == DIR_RIGHT and dir2 == DIR_LEFT))

    def update(self):
        """Update position and animation."""
        # 1. Handle Reversals (Immediate)
        if self.next_direction != DIR_NONE and self.is_opposite(self.direction, self.next_direction):
             if self.can_move(self.next_direction):
                 # print(f"REVERSING to {self.next_direction}")
                 self.direction = self.next_direction
                 self.next_direction = DIR_NONE

        # 2. Handle Starting from Stop
        elif self.direction == DIR_NONE and self.next_direction != DIR_NONE:
             if self.can_move(self.next_direction):
                 # print(f"STARTING to {self.next_direction}")
                 self.direction = self.next_direction
                 self.next_direction = DIR_NONE

                # 3. Handle Turns at Intersections
        elif self.at_tile_center():
            # Snap to grid if we are turning or stopping
            # This prevents drift and ensures clean turns
            
            # Only turn if the new direction is different from current
            # This prevents "snapping loop" when holding the button
            if self.next_direction != DIR_NONE and self.next_direction != self.direction:
                # Try to turn
                # Use can_turn() instead of can_move() to ensure the target tile is actually open
                if self.can_turn(self.next_direction):
                    # print(f"TURNING at ({self.x},{self.y}) to {self.next_direction}")
                    # SNAP to exact center
                    center_x = self.x + 8
                    center_y = self.y + 8
                    tile_x = int(center_x // 8)
                    tile_y = int(center_y // 8)
                    self.x = tile_x * 8 + 4 - 8
                    self.y = tile_y * 8 + 4 - 8
                    
                    self.direction = self.next_direction
                    self.next_direction = DIR_NONE
                else:
                    # Debug why we can't turn
                    # print(f"BLOCKED turning {self.next_direction} at ({self.x},{self.y})")
                    pass
            
            # If we hit a wall, stop and snap
            # Note: We only stop if the CURRENT direction is blocked.
            # Trying to turn into a wall (next_direction) will just fail the turn
            # and we will continue moving in the current direction.
            if self.direction != DIR_NONE and not self.can_move(self.direction):
                # print(f"HIT WALL at ({self.x},{self.y}) dir={self.direction}")
                center_x = self.x + 8
                center_y = self.y + 8
                tile_x = int(center_x // 8)
                tile_y = int(center_y // 8)
                self.x = tile_x * 8 + 4 - 8
                self.y = tile_y * 8 + 4 - 8
                self.direction = DIR_NONE

        # 4. Move
        if self.direction != DIR_NONE:
            if self.can_move(self.direction):
                if self.direction == DIR_UP:
                    self.y -= PACMAN_SPEED
                elif self.direction == DIR_DOWN:
                    self.y += PACMAN_SPEED
                elif self.direction == DIR_LEFT:
                    self.x -= PACMAN_SPEED
                elif self.direction == DIR_RIGHT:
                    self.x += PACMAN_SPEED
                
                # Tunnel wrap
                if self.x < -16:
                    self.x = GAME_WIDTH
                elif self.x >= GAME_WIDTH:
                    self.x = -16
                
                # Animate
                self.anim_timer += 1
                if self.anim_timer >= 3:
                    self.anim_timer = 0
                    self.anim_frame = (self.anim_frame + 1) % 3
                    self.set_frame(self.direction, self.anim_frame)
        
        # Update positions
        self.tile_x = int((self.x + 8) // TILE_SIZE)
        self.tile_y = int((self.y + 8) // TILE_SIZE)
        self.update_sprite_pos()
        
        # Eat items
        # We use the center point to determine which tile we are on
        # Only eat if we are close to the center to avoid accidental eating
        if self.at_tile_center():
            # Bounds check for tunnel
            tx = int(self.tile_x)
            ty = int(self.tile_y)
            if 0 <= tx < MAZE_COLS and 0 <= ty < MAZE_ROWS:
                item = items_grid[tx, ty]
                if item == 1: # Small Dot
                    items_grid[tx, ty] = 0
                    global score
                    score += 10
                    if score % 100 == 0: # Print every 100 points to avoid spam
                        print(f"Score: {score}")
                elif item == 2: # Power Pellet
                    items_grid[tx, ty] = 0
                    global score
                    score += 50
                    print(f"Score: {score} - POWER UP!")

# =============================================================================
# GHOST CLASS
# =============================================================================

class Ghost:
    """Ghost enemy character."""
    
    # Y-offsets in sprite sheet (assuming 1 row per ghost)
    TYPE_BLINKY = 64
    TYPE_PINKY = 80
    TYPE_INKY = 96
    TYPE_CLYDE = 112
    
    def __init__(self, ghost_type, start_tile_x, start_tile_y, x_offset=0):
        self.ghost_type = ghost_type
        
        self.sprite = displayio.TileGrid(
            sprite_sheet,
            pixel_shader=sprite_palette,
            width=1,
            height=2,
            tile_width=16,
            tile_height=8
        )
        
        self.tile_x = start_tile_x
        self.tile_y = start_tile_y
        # Align to pixel grid (Center of 16x16 sprite on 8x8 tile)
        # Tile Center = tile_x * 8 + 4
        # Sprite Center = x + 8
        # x + 8 = tile_x * 8 + 4  =>  x = tile_x * 8 - 4
        self.x = self.tile_x * 8 - 4 + x_offset
        self.y = self.tile_y * 8 - 4
        
        self.direction = DIR_LEFT
        self.next_direction = DIR_NONE
        
        # Ghost House State
        self.in_house = False
        self.house_timer = 0
        if self.ghost_type != Ghost.TYPE_BLINKY:
            self.in_house = True
            # Initial bounce direction
            if self.ghost_type == Ghost.TYPE_PINKY:
                self.direction = DIR_DOWN # Start moving down to bounce
            else:
                self.direction = DIR_UP
        
        self.anim_frame = 0
        self.anim_timer = 0
        
        self.set_frame(self.direction, 0)
        self.update_sprite_pos()
        
    def set_frame(self, direction, frame_idx):
        base_y = self.ghost_type
        
        # Layout assumption: Right, Left, Up, Down (2 frames each)
        if direction == DIR_RIGHT:
            base_x = 0
        elif direction == DIR_LEFT:
            base_x = 32
        elif direction == DIR_UP:
            base_x = 64
        elif direction == DIR_DOWN:
            base_x = 96
        else:
            base_x = 0 # Default
            
        base_x += (frame_idx % 2) * 16
        
        tiles_per_row = sprite_sheet.width // 16
        base_tile = (base_y // 8) * tiles_per_row + (base_x // 16)
        
        self.sprite[0, 0] = base_tile
        self.sprite[0, 1] = base_tile + tiles_per_row

    def update_sprite_pos(self):
        self.sprite.x = int(OFFSET_X + self.x)
        self.sprite.y = int(OFFSET_Y + self.y)

    def can_move(self, direction):
        """Check if movement in direction is possible."""
        next_x = self.x
        next_y = self.y
        
        if direction == DIR_UP:
            next_y -= GHOST_SPEED
        elif direction == DIR_DOWN:
            next_y += GHOST_SPEED
        elif direction == DIR_LEFT:
            next_x -= GHOST_SPEED
        elif direction == DIR_RIGHT:
            next_x += GHOST_SPEED
        else:
            return False
        
        center_x = next_x + 8
        center_y = next_y + 8
        
        # STRICT TUNNEL CHECK
        if center_x < 8 or center_x > 216:
            if direction == DIR_UP or direction == DIR_DOWN:
                return False

        if next_x < -8 or next_x >= GAME_WIDTH - 8:
            return True
            
        SENSOR_OFFSET = 3
        
        if direction == DIR_UP:
            check_x = center_x
            check_y = center_y - SENSOR_OFFSET
        elif direction == DIR_DOWN:
            check_x = center_x
            check_y = center_y + SENSOR_OFFSET
        elif direction == DIR_LEFT:
            check_x = center_x - SENSOR_OFFSET
            check_y = center_y
        elif direction == DIR_RIGHT:
            check_x = center_x + SENSOR_OFFSET
            check_y = center_y
            
        tx = int(check_x // TILE_SIZE)
        ty = int(check_y // TILE_SIZE)
        
        if tx < 0 or tx >= MAZE_COLS:
            if ty == 14:
                return True
            return False
        
        if ty < 0 or ty >= MAZE_ROWS:
            return False
            
        # Ghosts CAN pass through Ghost House Door
        # So we remove that check here
        
        # Prevent re-entry into Ghost House
        # Door is at Row 12 (above wall) -> Row 13 (wall gap)
        # If we are at Row 11 and trying to go DOWN into 12, forbid it
        # unless we are dead (eyes) - TODO
        if direction == DIR_DOWN and ty == 12 and (tx == 13 or tx == 14):
             if not self.in_house: # If we are outside, don't go back in
                 return False
            
        result = MAZE_DATA[ty][tx] != WALL
        if not result and self.ghost_type == 80: # Debug Pinky
             # Only print if we are NOT in a wall (i.e. we are blocked by a wall ahead)
             # This prevents spam when we are just sitting still
             pass
             # print(f"Pinky Blocked: Dir={direction} Pos={self.x:.1f},{self.y:.1f} Check={check_x:.1f},{check_y:.1f} Tile={tx},{ty}")
        return result

    def at_tile_center(self):
        center_x = self.x + 8
        center_y = self.y + 8
        dist_x = abs((center_x - 4) % 8)
        dist_y = abs((center_y - 4) % 8)
        dist_x = min(dist_x, 8 - dist_x)
        dist_y = min(dist_y, 8 - dist_y)
        # Strict check for AI decision making to prevent jitter
        # Must be strictly less than GHOST_SPEED (1.17) to avoid "gravity well" infinite loop
        # Must be >= GHOST_SPEED / 2 (0.585) to ensure we don't skip the window
        # 0.7 is the sweet spot.
        return dist_x <= 0.7 and dist_y <= 0.7

    def update(self):
        # Handle Ghost House Behavior
        if self.in_house:
            self.house_timer += 1
            should_exit = False
            
            # Exit Conditions
            if self.ghost_type == Ghost.TYPE_PINKY:
                should_exit = True # Pinky leaves immediately
            elif self.ghost_type == Ghost.TYPE_INKY and self.house_timer > 300: # ~5s
                should_exit = True
            elif self.ghost_type == Ghost.TYPE_CLYDE and self.house_timer > 600: # ~10s
                should_exit = True
                
            if should_exit:
                # Target: Center X (104), Outside Y (Row 11 Center)
                # Row 11 is the corridor. Center Y = 11*8 - 4 = 84.
                target_x = 13 * 8 # 104 (Between Tile 13 and 14)
                target_y = 11 * 8 - 4 # 84 (Centered in Row 11)
                
                # 1. Align X
                if abs(self.x - target_x) >= GHOST_SPEED:
                    if self.x < target_x:
                        self.x += GHOST_SPEED
                        self.direction = DIR_RIGHT
                    else:
                        self.x -= GHOST_SPEED
                        self.direction = DIR_LEFT
                # 2. Move UP
                else:
                    self.x = target_x # Snap X
                    self.y -= GHOST_SPEED
                    self.direction = DIR_UP
                    
                    # Check if out
                    if self.y <= target_y:
                        self.y = target_y # Snap Y to center of Row 11
                        self.in_house = False
                        self.direction = DIR_LEFT # Default exit direction
                        # print(f"Ghost {self.ghost_type} exited to {self.x}, {self.y}")
            else:
                # Bounce Up/Down
                # Center Y for Row 14 is 108 (14*8 - 4)
                center_y = 14 * 8 - 4
                limit = 3 # Bounce amplitude
                
                if self.direction == DIR_UP:
                    self.y -= GHOST_SPEED / 2 # Move slower in house
                    if self.y < (center_y - limit):
                        self.direction = DIR_DOWN
                else:
                    self.y += GHOST_SPEED / 2
                    if self.y > (center_y + limit):
                        self.direction = DIR_UP
            
            # Update sprite and return (skip normal movement)
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
                self.set_frame(self.direction, self.anim_frame)
            self.update_sprite_pos()
            return

        # Basic AI: Move forward. At intersection, pick random valid direction (not reverse).
        
        # 1. Handle Turns at Intersections
        if self.at_tile_center():
            # print(f"Ghost {self.ghost_type} at intersection {self.tile_x},{self.tile_y}")
            # Get valid directions
            valid_dirs = []
            for d in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
                # Don't reverse
                is_reverse = False
                if d == DIR_UP and self.direction == DIR_DOWN:
                    is_reverse = True
                if d == DIR_DOWN and self.direction == DIR_UP:
                    is_reverse = True
                if d == DIR_LEFT and self.direction == DIR_RIGHT:
                    is_reverse = True
                if d == DIR_RIGHT and self.direction == DIR_LEFT:
                    is_reverse = True
                
                if not is_reverse:
                    # Check grid neighbor directly (Look ahead 1 tile)
                    nx, ny = int(self.tile_x), int(self.tile_y)
                    if d == DIR_UP:
                        ny -= 1
                    elif d == DIR_DOWN:
                        ny += 1
                    elif d == DIR_LEFT:
                        nx -= 1
                    elif d == DIR_RIGHT:
                        nx += 1
                    
                    is_valid = False
                    if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS:
                        if MAZE_DATA[ny][nx] != WALL:
                            is_valid = True
                            
                            # ONE WAY DOOR CHECK FOR AI
                            # Prevent AI from choosing to go back into the house
                            # Block entering Row 12 (Door) from Row 11
                            if d == DIR_DOWN and ny == 12 and (nx == 13 or nx == 14):
                                if not self.in_house:
                                    is_valid = False

                    elif ny == 14: # Tunnel
                        is_valid = True
                        
                    if is_valid:
                        valid_dirs.append(d)
            
            if valid_dirs:
                # If current direction is valid, bias towards it to avoid jittery movement
                # But we want them to turn sometimes.
                # Let's say 20% chance to turn if current is valid.
                if self.direction in valid_dirs and len(valid_dirs) > 1:
                    if random.random() < 0.2:
                        self.direction = random.choice(valid_dirs)
                elif valid_dirs:
                    self.direction = random.choice(valid_dirs)
                
                # Snap to center
                center_x = self.x + 8
                center_y = self.y + 8
                tile_x = int(center_x // 8)
                tile_y = int(center_y // 8)
                self.x = tile_x * 8 + 4 - 8
                self.y = tile_y * 8 + 4 - 8
            else:
                # Dead end or stuck, try to reverse
                reverse_dir = DIR_NONE
                if self.direction == DIR_UP:
                    reverse_dir = DIR_DOWN
                elif self.direction == DIR_DOWN:
                    reverse_dir = DIR_UP
                elif self.direction == DIR_LEFT:
                    reverse_dir = DIR_RIGHT
                elif self.direction == DIR_RIGHT:
                    reverse_dir = DIR_LEFT
                
                if self.can_move(reverse_dir):
                    self.direction = reverse_dir

        # 2. Move
        if self.direction != DIR_NONE:
            if self.can_move(self.direction):
                if self.direction == DIR_UP:
                    self.y -= GHOST_SPEED
                elif self.direction == DIR_DOWN:
                    self.y += GHOST_SPEED
                elif self.direction == DIR_LEFT:
                    self.x -= GHOST_SPEED
                elif self.direction == DIR_RIGHT:
                    self.x += GHOST_SPEED
                
                # Tunnel wrap
                if self.x < -16:
                    self.x = GAME_WIDTH
                elif self.x >= GAME_WIDTH:
                    self.x = -16
                
                # Animate
                self.anim_timer += 1
                if self.anim_timer >= 10: # Slower animation for ghosts
                    self.anim_timer = 0
                    self.anim_frame = (self.anim_frame + 1) % 2
                    self.set_frame(self.direction, self.anim_frame)
            else:
                # STUCK RECOVERY
                # If we can't move in the chosen direction, pick a new one immediately.
                # This handles cases where AI chose a blocked path or alignment issues.
                # print(f"Ghost {self.ghost_type} STUCK at {self.x:.1f},{self.y:.1f} (Tile {self.tile_x},{self.tile_y}) Dir: {self.direction}")
                
                # Try all directions
                possible_turns = []
                possible_reverse = []
                
                reverse_dir = DIR_NONE
                if self.direction == DIR_UP:
                    reverse_dir = DIR_DOWN
                elif self.direction == DIR_DOWN:
                    reverse_dir = DIR_UP
                elif self.direction == DIR_LEFT:
                    reverse_dir = DIR_RIGHT
                elif self.direction == DIR_RIGHT:
                    reverse_dir = DIR_LEFT

                for d in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
                    if self.can_move(d):
                        if d == reverse_dir:
                            possible_reverse.append(d)
                        else:
                            possible_turns.append(d)
                
                # print(f"  Possible Turns: {possible_turns}, Reverse: {possible_reverse}")

                # Prefer turns over reversing to avoid bouncing back and forth
                if possible_turns:
                    self.direction = random.choice(possible_turns)
                    # print(f"  Recovering with TURN to {self.direction}")
                    # SNAP to center to fix alignment if we are turning late
                    center_x = self.x + 8
                    center_y = self.y + 8
                    tile_x = int(center_x // 8)
                    tile_y = int(center_y // 8)
                    self.x = tile_x * 8 + 4 - 8
                    self.y = tile_y * 8 + 4 - 8
                elif possible_reverse:
                    self.direction = possible_reverse[0]
                    # print(f"  Recovering with REVERSE to {self.direction}")
                else:
                    pass
                    # print("  TOTALLY STUCK! No valid moves.")
        
        # Update positions
        self.tile_x = int((self.x + 8) // TILE_SIZE)
        self.tile_y = int((self.y + 8) // TILE_SIZE)
        
        # DEBUG: Check if stuck (position not changing)
        if not hasattr(self, 'last_pos'):
            self.last_pos = (self.x, self.y)
            self.stuck_frames = 0
        
        if abs(self.x - self.last_pos[0]) < 0.1 and abs(self.y - self.last_pos[1]) < 0.1:
            self.stuck_frames += 1
            if self.stuck_frames > 60:
                print(f"Ghost {self.ghost_type} HOVERING at {self.x:.1f},{self.y:.1f} Dir:{self.direction}")
                self.stuck_frames = 0
                # Force a direction change
                self.direction = random.choice([DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT])
        else:
            self.stuck_frames = 0
            self.last_pos = (self.x, self.y)

        self.update_sprite_pos()

# =============================================================================
# CREATE GAME OBJECTS
# =============================================================================

pacman = PacMan()
main_group.append(pacman.sprite)

# Create ghosts
ghosts = []
# Spawn locations (Tile X, Tile Y, X Offset Px)
# Ghost House is roughly X=11-16, Y=13-15
# We spawn them in the center to avoid wall clipping
spawn_points = [
    (13, 11, 0), # Blinky (Outside, above door, Row 11)
    (13, 14, 4), # Pinky (Inside, center, +4px)
    (11, 14, 4), # Inky (Inside, left, +4px)
    (15, 14, 4)  # Clyde (Inside, right, +4px)
]

for i, (gx, gy, x_off) in enumerate(spawn_points):
    ghost_type = Ghost.TYPE_BLINKY
    if i == 1:
        ghost_type = Ghost.TYPE_PINKY
    elif i == 2:
        ghost_type = Ghost.TYPE_INKY
    elif i == 3:
        ghost_type = Ghost.TYPE_CLYDE
        
    ghost = Ghost(ghost_type, gx, gy, x_off)
    ghosts.append(ghost)
    main_group.append(ghost.sprite)

gc.collect()
print(f"Free memory: {gc.mem_free()}")

# =============================================================================
# INPUT HANDLING
# =============================================================================

def read_input():
    """Read joystick and queue direction.
    
    Remapped for 270° screen rotation (USB port on left):
    Physical UP -> Game RIGHT
    Physical DOWN -> Game LEFT
    Physical LEFT -> Game UP
    Physical RIGHT -> Game DOWN
    """
    if not UP.value:
        pacman.next_direction = DIR_RIGHT
        # print("UP pressed -> RIGHT")
    elif not DOWN.value:
        pacman.next_direction = DIR_LEFT
        # print("DOWN pressed -> LEFT")
    elif not LEFT.value:
        pacman.next_direction = DIR_UP
        # print("LEFT pressed -> UP")
    elif not RIGHT.value:
        pacman.next_direction = DIR_DOWN
        # print("RIGHT pressed -> DOWN")

# =============================================================================
# MAIN GAME LOOP
# =============================================================================

score = 0
debug_timer = 0
blink_timer = 0
blink_state = True # True = Visible, False = Hidden
fps_start_time = time.monotonic() # For FPS calculation

while True:
    start_time = time.monotonic()
    
    read_input()
    pacman.update()
    
    # Update ghosts
    for ghost in ghosts:
        ghost.update()
        
    # DEBUG: Heartbeat for ghost positions every 60 frames
    # if debug_timer == 0:
    #    for g in ghosts:
    #        print(f"G{g.ghost_type}: {g.x:.1f},{g.y:.1f} T({g.tile_x},{g.tile_y}) D:{g.direction} InHouse:{g.in_house}")
    
    # Handle Blinking (approx every 15 frames = 250ms)
    blink_timer += 1
    if blink_timer >= 15:
        blink_timer = 0
        blink_state = not blink_state
        
        # Toggle visibility of black covers
        # blink_state True = Pellet Visible = Cover Hidden
        for cover in pellet_covers:
            cover.hidden = blink_state

    # Debug output
    debug_timer += 1
    if debug_timer >= 60: # Every 60 frames
        current_time = time.monotonic()
        elapsed_fps = current_time - fps_start_time
        fps = 60 / elapsed_fps
        
        # Run GC every second to prevent OOM, but not every frame to avoid stutter
        gc.collect()
        
        print(f"FPS: {fps:.1f} | Mem: {gc.mem_free()}")
        
        debug_timer = 0
        fps_start_time = current_time
    
    # Frame timing
    elapsed = time.monotonic() - start_time
    if elapsed < FRAME_DELAY:
        time.sleep(FRAME_DELAY - elapsed)
    
    # gc.collect() # Removed from main loop to fix stuttering
