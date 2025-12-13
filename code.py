"""
Pac-Man Clone for Seeed Wio Terminal
CircuitPython 10.0.3
"""

import board
import displayio
import adafruit_imageload
import gc
import time
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
MOVE_SPEED = 1  # pixels per frame
FRAME_DELAY = 0.012  # ~80 FPS target (1 px/frame * 80 fps = 80 px/sec, close to arcade 75 px/sec)

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
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1],
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

sprite_sheet, sprite_palette = adafruit_imageload.load(
    "/images/sprites.bmp",
    bitmap=displayio.Bitmap,
    palette=displayio.Palette
)

# Make black transparent for sprites
sprite_palette.make_transparent(0)

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
        # Create sprite using TileGrid (2x2 tiles of 8x8 = 16x16 sprite)
        self.sprite = displayio.TileGrid(
            sprite_sheet,
            pixel_shader=sprite_palette,
            width=2,
            height=2,
            tile_width=8,
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
        
        # Convert pixel position to tile indices
        # Sprite sheet is 224 pixels wide = 28 tiles of 8x8
        tiles_per_row = 28
        base_tile = (fy // 8) * tiles_per_row + (fx // 8)
        
        self.sprite[0, 0] = base_tile
        self.sprite[1, 0] = base_tile + 1
        self.sprite[0, 1] = base_tile + tiles_per_row
        self.sprite[1, 1] = base_tile + tiles_per_row + 1
    
    def update_sprite_pos(self):
        """Update sprite screen position."""
        self.sprite.x = OFFSET_X + self.x
        self.sprite.y = OFFSET_Y + self.y
    
    def can_move(self, direction):
        """Check if movement in direction is possible."""
        next_x = self.x
        next_y = self.y
        
        if direction == DIR_UP:
            next_y -= MOVE_SPEED
        elif direction == DIR_DOWN:
            next_y += MOVE_SPEED
        elif direction == DIR_LEFT:
            next_x -= MOVE_SPEED
        elif direction == DIR_RIGHT:
            next_x += MOVE_SPEED
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
            
        tx = check_x // TILE_SIZE
        ty = check_y // TILE_SIZE
        
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
        target_tx = self.tile_x
        target_ty = self.tile_y
        
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
        return dist_x <= MOVE_SPEED and dist_y <= MOVE_SPEED

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
                    tile_x = center_x // 8
                    tile_y = center_y // 8
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
                tile_x = center_x // 8
                tile_y = center_y // 8
                self.x = tile_x * 8 + 4 - 8
                self.y = tile_y * 8 + 4 - 8
                self.direction = DIR_NONE

        # 4. Move
        if self.direction != DIR_NONE:
            if self.can_move(self.direction):
                if self.direction == DIR_UP:
                    self.y -= MOVE_SPEED
                elif self.direction == DIR_DOWN:
                    self.y += MOVE_SPEED
                elif self.direction == DIR_LEFT:
                    self.x -= MOVE_SPEED
                elif self.direction == DIR_RIGHT:
                    self.x += MOVE_SPEED
                
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
        self.tile_x = (self.x + 8) // TILE_SIZE
        self.tile_y = (self.y + 8) // TILE_SIZE
        self.update_sprite_pos()
        
        # Eat items
        # We use the center point to determine which tile we are on
        # Only eat if we are close to the center to avoid accidental eating
        if self.at_tile_center():
            # Bounds check for tunnel
            if 0 <= self.tile_x < MAZE_COLS and 0 <= self.tile_y < MAZE_ROWS:
                item = items_grid[self.tile_x, self.tile_y]
                if item == 1: # Small Dot
                    items_grid[self.tile_x, self.tile_y] = 0
                    global score
                    score += 10
                    if score % 100 == 0: # Print every 100 points to avoid spam
                        print(f"Score: {score}")
                elif item == 2: # Power Pellet
                    items_grid[self.tile_x, self.tile_y] = 0
                    global score
                    score += 50
                    print(f"Score: {score} - POWER UP!")

# =============================================================================
# CREATE GAME OBJECTS
# =============================================================================

pacman = PacMan()
main_group.append(pacman.sprite)

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

while True:
    start_time = time.monotonic()
    
    read_input()
    pacman.update()
    
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
        debug_timer = 0
        # print(f"Mem: {gc.mem_free()} | Time: {time.monotonic() - start_time:.4f}")
    
    # Frame timing
    elapsed = time.monotonic() - start_time
    if elapsed < FRAME_DELAY:
        time.sleep(FRAME_DELAY - elapsed)
    
    # gc.collect() # Removed from main loop to fix stuttering
