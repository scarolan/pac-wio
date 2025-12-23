# SPDX-FileCopyrightText: 2025 Sean Carolan (@scarolan)
# SPDX-FileCopyrightText: 2025 Cooper Dalrymple (@relic-se)
#
# SPDX-License-Identifier: MIT

"""
Pac-Man Clone for Seeed Wio Terminal
CircuitPython 10.0.3
"""

# load included modules if we aren't installed on the root path
if len(__file__.split("/")[:-1]) > 1:
    lib_path = "/".join(__file__.split("/")[:-1]) + "/lib"
    try:
        import os
        os.stat(lib_path)
    except:
        pass
    else:
        import sys
        sys.path.append(lib_path)

import board
import displayio
import gc
import time
import random
from digitalio import DigitalInOut, Pull
import terminalio
import pwmio
import os
from micropython import const
try:
    from adafruit_bitmap_font import bitmap_font
    from adafruit_display_text import label
except ImportError:
    pass

WIO = const(0)
FRUIT_JAM = const(1)

DEVICE = WIO
if os.uname().machine.startswith("Adafruit Fruit Jam"):
    try:
        import adafruit_fruitjam
    except ImportError:
        pass
    else:
        DEVICE = FRUIT_JAM

        import supervisor
        import synthio
        import sys

        # using imageload for better performance with more RAM consumption
        try:
            import adafruit_imageload
        except ImportError:
            pass

        try:
            import launcher_config
            config = launcher_config.LauncherConfig()
        except ImportError:
            config = None

# =============================================================================
# CONSTANTS
# =============================================================================

if DEVICE is FRUIT_JAM:
    # get user display width
    if (SCREEN_WIDTH := os.getenv("CIRCUITPY_DISPLAY_WIDTH")) is not None:
        SCREEN_HEIGHT = next((h for w, h in adafruit_fruitjam.peripherals.VALID_DISPLAY_SIZES if SCREEN_WIDTH == w))
    else:
        SCREEN_WIDTH = 720
        SCREEN_HEIGHT = 400
else:
    # Screen dimensions
    SCREEN_WIDTH = 320
    SCREEN_HEIGHT = 240

# determine if we need to display in vertical orientation
DISPLAY_VERTICAL = SCREEN_WIDTH <= 360
DISPLAY_WIDTH = SCREEN_HEIGHT if DISPLAY_VERTICAL else SCREEN_WIDTH
DISPLAY_HEIGHT = SCREEN_WIDTH if DISPLAY_VERTICAL else SCREEN_HEIGHT

# Game area dimensions (from sprite sheet)
GAME_WIDTH = 224
GAME_HEIGHT = 248

# Offset to center game area in screen
OFFSET_X = (DISPLAY_WIDTH - GAME_WIDTH) // 2   # 8 pixels
OFFSET_Y = (DISPLAY_HEIGHT - GAME_HEIGHT) // 2  # 36 pixels

# Tile dimensions
TILE_SIZE = 8

# Maze dimensions in tiles
MAZE_COLS = 28
MAZE_ROWS = 31

# Movement
PACMAN_SPEED = 1.3    # pixels per frame
GHOST_SPEED = 1.22    # pixels per frame (approx 94% of Pac-Man speed)
FRAME_DELAY = 0.005   # Slightly more delay

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

# Ghost Modes
MODE_SCATTER = 0
MODE_CHASE = 1
MODE_FRIGHTENED = 2
MODE_EATEN = 3

# Game States
STATE_PLAY = 0
STATE_DYING = 1
STATE_EATING_GHOST = 2
STATE_GAME_OVER = 3
STATE_LEVEL_COMPLETE = 4
STATE_EATING_FRUIT = 5

# Fruit point values per level
FRUIT_POINTS = [100, 300, 500, 500, 700, 700, 1000, 1000, 2000, 2000, 3000, 3000, 5000]

# Level 1 Mode Timings (seconds)
# Scatter, Chase, Scatter, Chase, Scatter, Chase, Scatter, Chase
MODE_TIMES = [7, 20, 7, 20, 5, 20, 5, 999999]

# Frightened Mode Duration (Frames)
# Level 1: ~6 seconds (at 100fps = 600 frames)
# This will decrease in higher levels
FRIGHTENED_DURATION = 600 

# Sprite Sheet Coordinates (x, y)
SPRITE_LIFE = (128, 16) # 8, 1
SPRITE_FRUIT_CHERRY = (32, 48) # 3, 2
SPRITE_FRUIT_STRAWBERRY = (48, 48)
SPRITE_FRUIT_ORANGE = (64, 48)
SPRITE_FRUIT_APPLE = (80, 48)
SPRITE_FRUIT_MELON = (96, 48)
SPRITE_FRUIT_GALAXIAN = (112, 48)
SPRITE_FRUIT_BELL = (128, 48)
SPRITE_FRUIT_KEY = (144, 48)

FRUIT_LEVELS = [
    SPRITE_FRUIT_CHERRY,     # Level 1
    SPRITE_FRUIT_STRAWBERRY, # Level 2
    SPRITE_FRUIT_ORANGE,     # Level 3
    SPRITE_FRUIT_ORANGE,     # Level 4
    SPRITE_FRUIT_APPLE,      # Level 5
    SPRITE_FRUIT_APPLE,      # Level 6
    SPRITE_FRUIT_MELON,      # Level 7
    SPRITE_FRUIT_MELON,      # Level 8
    SPRITE_FRUIT_GALAXIAN,   # Level 9
    SPRITE_FRUIT_GALAXIAN,   # Level 10
    SPRITE_FRUIT_BELL,       # Level 11
    SPRITE_FRUIT_BELL,       # Level 12
    SPRITE_FRUIT_KEY         # Level 13+
]

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

if DEVICE is WIO:
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

    # Sound toggle button (Button 1 on top of device)
    BUTTON_1 = DigitalInOut(board.BUTTON_1)
    BUTTON_1.switch_to_input(pull=Pull.UP)
    last_button_state = True  # True = not pressed

# =============================================================================
# SOUND SETUP
# =============================================================================

if DEVICE is FRUIT_JAM:
    peripherals = adafruit_fruitjam.peripherals.Peripherals(
        safe_volume_limit=(config.audio_volume_override_danger if config is not None else 0.75),
    )
    synth = synthio.Synthesizer(
        sample_rate=peripherals.dac.sample_rate,
        channel_count=1,
    )
    peripherals.audio.play(synth)
else:
    # Wio Terminal buzzer is on pin BUZZER (or D0 on some builds)
    try:
        buzzer = pwmio.PWMOut(board.BUZZER, variable_frequency=True)
    except AttributeError:
        # Fallback if BUZZER pin not defined
        try:
            buzzer = pwmio.PWMOut(board.D0, variable_frequency=True)
        except:
            buzzer = None
            print("No buzzer available")

sound_enabled = True

# Pac-Man waka frequencies (alternating)
WAKA_FREQ_1 = 261  # C4
WAKA_FREQ_2 = 392  # G4
waka_toggle = False

def play_sound(freq:int):
    if DEVICE is FRUIT_JAM:
        synth.release_all_then_press(synthio.Note(frequency=freq))
    elif buzzer is not None:
        buzzer.frequency = freq
        buzzer.duty_cycle = 32768  # 50% duty cycle

def stop_sound():
    """Stop any sound."""
    if DEVICE is FRUIT_JAM:
        synth.release_all()
    elif buzzer is not None:
        buzzer.duty_cycle = 0

def play_waka():
    """Play the waka sound effect."""
    global waka_toggle
    if not sound_enabled:
        return
    
    freq = WAKA_FREQ_2 if waka_toggle else WAKA_FREQ_1
    waka_toggle = not waka_toggle
    
    play_sound(freq)

def play_death_sound():
    """Play death sound effect (blocking version - not used during animation)."""
    if not sound_enabled:
        return
    # Descending tone
    for freq in range(400, 100, -30):
        play_sound(freq)
        time.sleep(0.05)
    stop_sound()

def play_death_note(frame_idx):
    """Play a single death note based on animation frame."""
    if not sound_enabled:
        return
    # 11 death frames, descend from 500Hz to 100Hz
    freq = 500 - (frame_idx * 35)
    if freq < 100:
        freq = 100
    play_sound(freq)

def play_eat_ghost_sound():
    """Play ghost eating sound."""
    if not sound_enabled:
        return
    # Quick ascending tone
    for freq in range(200, 800, 100):
        play_sound(freq)
        time.sleep(0.02)
    stop_sound()

def play_startup_jingle():
    """Play the Pac-Man startup jingle."""
    if not sound_enabled:
        return
    
    # Pac-Man Intro Theme
    # Tempo control: lower is faster
    T = 0.11  # Base note duration (16th note)
    H = T * 2 # Half note / ending

    melody = [
        # --- Phrase 1: B Major Arpeggio ---
        (494, T),  # B4
        (988, T),  # B5 (Octave jump!)
        (740, T),  # F#5
        (622, T),  # D#5
        (988, T),  # B5
        (740, T),  # F#5
        (622, H),  # D#5 (End of phrase)

        # --- Phrase 2: C Major Arpeggio ---
        (523, T),  # C5
        (1047, T), # C6 (Octave jump!)
        (784, T),  # G5
        (659, T),  # E5
        (1047, T), # C6
        (784, T),  # G5
        (659, H),  # E5 (End of phrase)

        # --- Phrase 3: Back to B Major ---
        (494, T),  # B4
        (988, T),  # B5
        (740, T),  # F#5
        (622, T),  # D#5
        (988, T),  # B5
        (740, T),  # F#5
        (622, H),  # D#5 

        # --- Phrase 4: Chromatic Rise to Finish ---
        # Rising tension...
        (622, T),  # D#5
        (659, T),  # E5
        (698, T),  # F5
        
        (698, T),  # F5 (Repeat F to bridge the triplet feel)
        (740, T),  # F#5
        (784, T),  # G5
        
        (784, T),  # G5 (Repeat G)
        (831, T),  # G#5
        (880, T),  # A5
        
        (988, H)   # B5 (Final Note - bold finish!)
    ]

    for freq, duration in melody:
        play_sound(freq)
        time.sleep(duration)
        stop_sound()
        time.sleep(0.02)  # Brief gap between notes
    
    stop_sound()

def toggle_sound():
    sound_enabled = not sound_enabled
    print(f"Sound: {'ON' if sound_enabled else 'OFF'}")
    if not sound_enabled:
        stop_sound()

# =============================================================================
# DISPLAY SETUP
# =============================================================================

if DEVICE is FRUIT_JAM:
    # setup display
    adafruit_fruitjam.peripherals.request_display_config(SCREEN_WIDTH, SCREEN_HEIGHT)
    display = supervisor.runtime.display
else:
    # Set up display
    display = board.DISPLAY
display.auto_refresh = False

if DISPLAY_VERTICAL:
    # vertical orientation, flipped 180 from before
    display.rotation = 270

# Main display group
main_group = displayio.Group()
display.root_group = main_group

# =============================================================================
# LOAD MAZE BACKGROUND
# =============================================================================

# Load the empty maze (no dots)
if "adafruit_imageload" in globals():
    maze_bmp, maze_palette = adafruit_imageload.load("images/maze_empty.bmp")
else:
    # using OnDiskBitmap to save RAM
    # We keep the file open for the duration of the program
    maze_file = open("images/maze_empty.bmp", "rb")
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

# Count actual dots for level completion
dot_count = 0
for y in range(MAZE_ROWS):
    for x in range(MAZE_COLS):
        if items_grid[x, y] == 1 or items_grid[x, y] == 2:
            dot_count += 1
TOTAL_DOTS = dot_count
print(f"Total dots in maze: {TOTAL_DOTS}")

def reset_dots():
    """Reset all dots and power pellets to their initial state."""
    global dots_eaten
    dots_eaten = 0
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

if "adafruit_imageload" in globals():
    sprite_sheet, sprite_palette = adafruit_imageload.load("images/sprites.bmp")
else:
    # Use OnDiskBitmap to save RAM and avoid allocation issues
    sprite_sheet = displayio.OnDiskBitmap("images/sprites.bmp")
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
    
    # Death Animation Frames (Top Row, Tiles 3-13)
    # x = 3*16 = 48, y = 0
    # 11 frames fitting exactly to the end of the row (Tile 13)
    DEATH_FRAMES = []
    for i in range(11): # 11 frames
        DEATH_FRAMES.append((48 + i * 16, 0))
        
    # Score Sprites (Row 8, Tiles 0-3)
    # 200, 400, 800, 1600
    SCORE_FRAMES = [
        (0, 128),   # 200
        (16, 128),  # 400
        (32, 128),  # 800
        (48, 128)   # 1600
    ]
    
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
        
        # Saved position for score display
        self.saved_x = 0
        self.saved_y = 0
        
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
    
    def set_death_frame(self, frame_idx):
        """Set sprite tiles for death animation."""
        if frame_idx >= len(self.DEATH_FRAMES):
            frame_idx = len(self.DEATH_FRAMES) - 1
            
        fx, fy = self.DEATH_FRAMES[frame_idx]
        
        tiles_per_row = sprite_sheet.width // 16
        base_tile = (fy // 8) * tiles_per_row + (fx // 16)
        
        self.sprite[0, 0] = base_tile
        self.sprite[0, 1] = base_tile + tiles_per_row

    def set_score_frame(self, score_idx):
        """Set sprite tiles for score display."""
        if score_idx >= len(self.SCORE_FRAMES):
            score_idx = len(self.SCORE_FRAMES) - 1
            
        fx, fy = self.SCORE_FRAMES[score_idx]
        
        tiles_per_row = sprite_sheet.width // 16
        base_tile = (fy // 8) * tiles_per_row + (fx // 16)
        
        self.sprite[0, 0] = base_tile
        self.sprite[0, 1] = base_tile + tiles_per_row

    def reset(self):
        """Reset Pac-Man to starting position."""
        self.tile_x = 14
        self.tile_y = 23
        self.x = 106
        self.y = 181
        self.direction = DIR_NONE
        self.next_direction = DIR_NONE
        self.anim_frame = 0
        self.anim_timer = 0
        self.set_frame(DIR_RIGHT, 0)
        self.update_sprite_pos()
    
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
            # Stop the waka sound briefly to create the alternating effect
            stop_sound()
            # Bounds check for tunnel
            tx = int(self.tile_x)
            ty = int(self.tile_y)
            if 0 <= tx < MAZE_COLS and 0 <= ty < MAZE_ROWS:
                item = items_grid[tx, ty]
                if item == 1: # Small Dot
                    items_grid[tx, ty] = 0
                    global score, dots_eaten, bonus_fruit_active, bonus_fruit_timer
                    score += 10
                    dots_eaten += 1
                    play_waka()
                    
                    # Spawn bonus fruit at 70 and 170 dots
                    if dots_eaten == 70 or dots_eaten == 170:
                        bonus_fruit_active = True
                        bonus_fruit_timer = 0
                        bonus_fruit.hidden = False
                        update_bonus_fruit()
                        print(f"BONUS FRUIT APPEARED! (dots: {dots_eaten})")
                    
                    if score % 100 == 0: # Print every 100 points to avoid spam
                        print(f"Score: {score}")
                elif item == 2: # Power Pellet
                    items_grid[tx, ty] = 0
                    global score, dots_eaten
                    score += 50
                    dots_eaten += 1
                    play_waka()
                    print(f"Score: {score} - POWER UP!")
                    
                    # Reset ghost multiplier
                    global ghosts_eaten_count
                    ghosts_eaten_count = 0
                    
                    # Trigger Frightened Mode
                    for g in ghosts:
                        if g.mode != MODE_EATEN:
                            g.mode = MODE_FRIGHTENED
                            g.frightened_timer = 0
                            # Only reverse if outside (inside ghosts just bounce)
                            if not g.in_house:
                                g.reverse_pending = True

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
        self.start_params = (start_tile_x, start_tile_y, x_offset)
        
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
        
        self.mode = MODE_SCATTER
        self.reverse_pending = False
        self.frightened_timer = 0
        
        # Scatter Targets (Fixed Corners)
        # Blinky: Top-Right (25, -3) - Outside maze to force Up/Right bias
        # Pinky: Top-Left (2, -3)
        # Inky: Bottom-Right (27, 31)
        # Clyde: Bottom-Left (0, 31)
        if self.ghost_type == Ghost.TYPE_BLINKY:
            self.scatter_target = (25, -3)
        elif self.ghost_type == Ghost.TYPE_PINKY:
            self.scatter_target = (2, -3)
        elif self.ghost_type == Ghost.TYPE_INKY:
            self.scatter_target = (27, 31)
        elif self.ghost_type == Ghost.TYPE_CLYDE:
            self.scatter_target = (0, 31)
        
        self.set_frame(self.direction, 0)
        self.update_sprite_pos()
        
    def set_frame(self, direction, frame_idx):
        base_y = self.ghost_type
        base_x = 0
        
        # Override for Frightened / Eaten modes
        if self.mode == MODE_FRIGHTENED:
            base_y = 64 # Row 4
            # Flash white if timer is nearing end (last ~2 seconds)
            # Timer counts UP from 0 to FRIGHTENED_DURATION
            if self.frightened_timer > (FRIGHTENED_DURATION - 200) and (self.frightened_timer // 10) % 2 == 0:
                base_x = 160 # White Ghosts (Tiles 10-11)
            else:
                base_x = 128 # Blue Ghosts (Tiles 8-9)
            
            base_x += (frame_idx % 2) * 16
            
        elif self.mode == MODE_EATEN:
            base_y = 80 # Row 5 (Eyes)
            # Eyes Direction: Right, Left, Up, Down
            if direction == DIR_RIGHT:
                base_x = 128
            elif direction == DIR_LEFT:
                base_x = 144
            elif direction == DIR_UP:
                base_x = 160
            elif direction == DIR_DOWN:
                base_x = 176
            else:
                base_x = 128
            
        else:
            # Normal Ghost
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
            
        # SUPER OVERRIDE for Eaten Ghosts near House
        # If we are eyes and near the door/house, ignore walls
        if self.mode == MODE_EATEN:
            # House area: Rows 11-15, Cols 10-17
            if 11 <= ty <= 15 and 10 <= tx <= 17:
                return True
            
        # Ghosts CAN pass through Ghost House Door
        # So we remove that check here
        
        # Prevent re-entry into Ghost House
        # Door is at Row 12 (above wall) -> Row 13 (wall gap)
        # If we are at Row 11 and trying to go DOWN into 12, forbid it
        # unless we are dead (eyes)
        if direction == DIR_DOWN and ty == 12 and (tx == 13 or tx == 14):
             if not self.in_house and self.mode != MODE_EATEN: # If we are outside, don't go back in (unless Eaten)
                 return False
                 
        result = MAZE_DATA[ty][tx] != WALL
        if not result and self.mode == MODE_EATEN:
             print(f"Eyes BLOCKED at {self.tile_x},{self.tile_y} trying {direction} into {tx},{ty}")
             
        return result

    def at_tile_center(self):
        center_x = self.x + 8
        center_y = self.y + 8
        dist_x = abs((center_x - 4) % 8)
        dist_y = abs((center_y - 4) % 8)
        dist_x = min(dist_x, 8 - dist_x)
        dist_y = min(dist_y, 8 - dist_y)
        
        # Threshold depends on speed to ensure we don't skip the window
        # Normal Speed (1.17) -> 0.7
        # Eaten Speed (2.34) -> 1.5
        threshold = 0.7
        if self.mode == MODE_EATEN:
            threshold = 1.5
            
        return dist_x <= threshold and dist_y <= threshold

    def get_chase_target(self):
        px, py = pacman.tile_x, pacman.tile_y
        pd = pacman.direction
        
        if self.ghost_type == Ghost.TYPE_BLINKY:
            return (px, py)
            
        elif self.ghost_type == Ghost.TYPE_PINKY:
            # 4 tiles ahead of Pac-Man
            tx, ty = px, py
            if pd == DIR_UP:
                ty -= 4
                tx -= 4 # Replicate overflow bug (Up+Left)
            elif pd == DIR_DOWN:
                ty += 4
            elif pd == DIR_LEFT:
                tx -= 4
            elif pd == DIR_RIGHT:
                tx += 4
            return (tx, ty)
            
        elif self.ghost_type == Ghost.TYPE_INKY:
            # Vector from Blinky to (Pac-Man + 2) * 2
            # 1. Get position 2 tiles ahead of Pac-Man
            tx, ty = px, py
            if pd == DIR_UP:
                ty -= 2
                tx -= 2 # Bug
            elif pd == DIR_DOWN:
                ty += 2
            elif pd == DIR_LEFT:
                tx -= 2
            elif pd == DIR_RIGHT:
                tx += 2
            
            # 2. Get Blinky's position
            bx, by = 0, 0
            for g in ghosts:
                if g.ghost_type == Ghost.TYPE_BLINKY:
                    bx, by = g.tile_x, g.tile_y
                    break
            
            # 3. Vector
            vx = tx - bx
            vy = ty - by
            
            return (bx + vx * 2, by + vy * 2)
            
        elif self.ghost_type == Ghost.TYPE_CLYDE:
            # If dist > 8, target Pac-Man. Else scatter.
            dist = (self.tile_x - px)**2 + (self.tile_y - py)**2
            if dist > 64: # 8^2
                return (px, py)
            else:
                return self.scatter_target
                
        return (px, py)
    
    def update(self):
        # Handle Ghost House Behavior
        if self.in_house:
            self.house_timer += 1
            should_exit = False
            
            # Exit Conditions
            if self.ghost_type == Ghost.TYPE_BLINKY:
                if self.house_timer > 60: # Wait 1s after revival
                    should_exit = True
            elif self.ghost_type == Ghost.TYPE_PINKY:
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

        # Basic AI: Move forward. At intersection, pick best direction based on target.
        
        # 0. Handle Reverse Pending (Mode Switch)
        if self.reverse_pending:
            self.reverse_pending = False
            rev = DIR_NONE
            if self.direction == DIR_UP:
                rev = DIR_DOWN
            elif self.direction == DIR_DOWN:
                rev = DIR_UP
            elif self.direction == DIR_LEFT:
                rev = DIR_RIGHT
            elif self.direction == DIR_RIGHT:
                rev = DIR_LEFT
            
            if self.can_move(rev):
                self.direction = rev
                # Snap to center to ensure clean turn
                center_x = self.x + 8
                center_y = self.y + 8
                tile_x = int(center_x // 8)
                tile_y = int(center_y // 8)
                self.x = tile_x * 8 + 4 - 8
                self.y = tile_y * 8 + 4 - 8
                return # Skip rest of update for this frame

        # 1. Handle Turns at Intersections
        if self.at_tile_center():
            # Determine Target
            tx, ty = 0, 0
            
            if self.mode == MODE_CHASE:
                tx, ty = self.get_chase_target()
            elif self.mode == MODE_SCATTER:
                tx, ty = self.scatter_target
            elif self.mode == MODE_EATEN:
                # Target Ghost House (Above Door)
                tx, ty = 13, 11
                # If we are at the door entrance (Row 11), target inside (Row 14)
                # We need to force DOWN if we are at (13, 11) or (14, 11)
                if self.tile_y == 11 and (self.tile_x == 13 or self.tile_x == 14):
                    tx, ty = 13, 14
                
                # If we are inside (Row 14), we are done
                if self.tile_y >= 14 and (self.tile_x == 13 or self.tile_x == 14):
                    self.mode = current_mode # Revive!
                    self.in_house = True
                    self.house_timer = 0 # Restart house logic
                    self.direction = DIR_UP # Reset direction
                    
                    # Snap to exact center of pen (Pinky's start: x=104)
                    # This aligns with the exit target X
                    self.x = 104
                    self.y = 14 * 8 - 4 # 108
                    self.tile_x = 13 # Technically between 13 and 14
                    self.tile_y = 14
                    self.update_sprite_pos()
                    return
            elif self.mode == MODE_FRIGHTENED:
                # Random Target (Pseudo-Random Walk)
                # We don't use a target tile, we just pick a random valid direction
                pass
            
            # Find best direction
            best_dist = 999999
            best_dir = self.direction # Default continue
            
            valid_dirs = []
            
            # Check all 4 directions in priority order: UP, LEFT, DOWN, RIGHT
            for d in [DIR_UP, DIR_LEFT, DIR_DOWN, DIR_RIGHT]:
                # Don't reverse (unless forced, handled above)
                if (d == DIR_UP and self.direction == DIR_DOWN) or \
                   (d == DIR_DOWN and self.direction == DIR_UP) or \
                   (d == DIR_LEFT and self.direction == DIR_RIGHT) or \
                   (d == DIR_RIGHT and self.direction == DIR_LEFT):
                    continue
                    
                # Check validity (walls)
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
                            if not self.in_house and self.mode != MODE_EATEN:
                                is_valid = False

                elif ny == 14: # Tunnel
                    is_valid = True
                    
                if is_valid:
                    valid_dirs.append(d)
                    # Calculate distance to target from neighbor tile
                    if self.mode != MODE_FRIGHTENED:
                        dist = (nx - tx)**2 + (ny - ty)**2
                        if dist < best_dist:
                            best_dist = dist
                            best_dir = d
            
            if self.mode == MODE_FRIGHTENED:
                if valid_dirs:
                    self.direction = random.choice(valid_dirs)
            elif self.mode == MODE_EATEN and (self.tile_y == 11 or self.tile_y == 12) and (self.tile_x == 13 or self.tile_x == 14):
                 # Force DOWN if at door entrance OR inside door
                 # print(f"Eyes forcing DOWN at {self.tile_x},{self.tile_y}")
                 self.direction = DIR_DOWN
                 # Force snap to X center to avoid hitting side walls of door
                 target_x = self.tile_x * 8 - 4
                 if abs(self.x - target_x) > 1.0:
                     self.x = target_x
            elif self.mode == MODE_EATEN and self.tile_y == 13 and (self.tile_x == 13 or self.tile_x == 14):
                 # Force DOWN if inside house gap (Row 13) to reach target (Row 14)
                 self.direction = DIR_DOWN
            else:
                self.direction = best_dir
            
            # Snap to center
            center_x = self.x + 8
            center_y = self.y + 8
            tile_x = int(center_x // 8)
            tile_y = int(center_y // 8)
            self.x = tile_x * 8 + 4 - 8
            self.y = tile_y * 8 + 4 - 8

        # 2. Move
        if self.direction != DIR_NONE:
            speed = GHOST_SPEED
            if self.mode == MODE_FRIGHTENED:
                speed = GHOST_SPEED * 0.6 # Slower
            elif self.mode == MODE_EATEN:
                speed = 2.0 # Fixed fast speed (was GHOST_SPEED * 2.0 = 2.34)
                
            if self.can_move(self.direction):
                if self.direction == DIR_UP:
                    self.y -= speed
                elif self.direction == DIR_DOWN:
                    self.y += speed
                elif self.direction == DIR_LEFT:
                    self.x -= speed
                elif self.direction == DIR_RIGHT:
                    self.x += speed
                
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

    def reset(self):
        """Reset ghost to starting position."""
        start_tile_x, start_tile_y, x_offset = self.start_params
        
        self.tile_x = start_tile_x
        self.tile_y = start_tile_y
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
        self.mode = MODE_SCATTER
        self.reverse_pending = False
        
        self.set_frame(self.direction, 0)
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
# SCOREBOARD SETUP
# =============================================================================

score_label = None
one_up_label = None
high_score_label = None
high_score_title_label = None
game_over_label = None

last_score = -1
high_score = 10000
last_high_score = -1

if "label" in globals():
    try:
        FONT = bitmap_font.load_font("fonts/press_start_2p.bdf") if "bitmap_font" in globals() else terminalio.FONT

        # 1UP Label (Top Left)
        one_up_label = label.Label(FONT, text="1UP", color=0xFFFFFF)
        one_up_label.x = 8
        one_up_label.y = 8
        main_group.append(one_up_label)
        
        # Score Label (Below 1UP)
        score_label = label.Label(FONT, text="0" * (2 if "bitmap_font" in globals() else 1), color=0xFFFFFF)
        score_label.x = 8
        score_label.y = 24
        main_group.append(score_label)
        
        # High Score Title (Top Center)
        high_score_title_label = label.Label(FONT, text="HIGH SCORE", color=0xFFFFFF)
        high_score_title_label.anchor_point = (0.5, 0.0)
        high_score_title_label.anchored_position = (DISPLAY_WIDTH // 2, 8)
        main_group.append(high_score_title_label)
        
        # High Score Value (Below Title)
        high_score_label = label.Label(FONT, text=str(high_score), color=0xFFFFFF)
        high_score_label.anchor_point = (0.5, 0.0)
        high_score_label.anchored_position = (DISPLAY_WIDTH // 2, 24)
        main_group.append(high_score_label)
        
        # GAME OVER Label (centered, hidden initially)
        game_over_label = label.Label(FONT, text="GAME  OVER", color=0xFF0000)
        game_over_label.anchor_point = (0.5, 0.5)
        game_over_label.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
        game_over_label.hidden = True
        main_group.append(game_over_label)

    except Exception as e:
        print(f"Scoreboard error: {e}")

# =============================================================================
# LIVES AND FRUIT DISPLAY
# =============================================================================

lives = 3
level = 1

# Helper function to get tile index from pixel coordinates
def get_tile_index(px, py):
    """Convert pixel (x, y) to tile index for 16x8 tile addressing."""
    tiles_per_row = sprite_sheet.width // 16
    base_tile = (py // 8) * tiles_per_row + (px // 16)
    return base_tile

# Create life sprites (bottom left) - up to 5 lives displayed
life_sprites = []
for i in range(5):
    life_tg = displayio.TileGrid(
        sprite_sheet,
        pixel_shader=sprite_palette,
        width=1,
        height=2,
        tile_width=16,
        tile_height=8
    )
    # Position at bottom left, spaced 16 pixels apart
    life_tg.x = OFFSET_X + 24 + (i * 16)
    life_tg.y = OFFSET_Y + GAME_HEIGHT + 4  # Below game area
    
    # Set to life sprite (SPRITE_LIFE = (128, 16))
    base_tile = get_tile_index(SPRITE_LIFE[0], SPRITE_LIFE[1])
    tiles_per_row = sprite_sheet.width // 16
    life_tg[0, 0] = base_tile
    life_tg[0, 1] = base_tile + tiles_per_row
    
    life_tg.hidden = (i >= lives - 1)  # Show lives-1 (current life not shown)
    life_sprites.append(life_tg)
    main_group.append(life_tg)

# Create fruit sprite (bottom right)
fruit_sprite = displayio.TileGrid(
    sprite_sheet,
    pixel_shader=sprite_palette,
    width=1,
    height=2,
    tile_width=16,
    tile_height=8
)
fruit_sprite.x = OFFSET_X + GAME_WIDTH - 32
fruit_sprite.y = OFFSET_Y + GAME_HEIGHT + 4  # Below game area

def update_fruit_sprite():
    """Update fruit sprite based on current level."""
    fruit_idx = min(level - 1, len(FRUIT_LEVELS) - 1)
    fx, fy = FRUIT_LEVELS[fruit_idx]
    base_tile = get_tile_index(fx, fy)
    tiles_per_row = sprite_sheet.width // 16
    fruit_sprite[0, 0] = base_tile
    fruit_sprite[0, 1] = base_tile + tiles_per_row

update_fruit_sprite()
main_group.append(fruit_sprite)

# Bonus fruit that appears in the maze
bonus_fruit = displayio.TileGrid(
    sprite_sheet,
    pixel_shader=sprite_palette,
    width=1,
    height=2,
    tile_width=16,
    tile_height=8
)
# Fruit appears below ghost house (tile 13-14, row 17 in arcade = pixel coords)
bonus_fruit.x = OFFSET_X + 13 * 8  # Center of maze
bonus_fruit.y = OFFSET_Y + 17 * 8 - 4  # Below ghost house, moved up 4 pixels
bonus_fruit.hidden = True
main_group.append(bonus_fruit)

# Bonus fruit score display (reuse same sprite, show score temporarily)
bonus_fruit_active = False
bonus_fruit_timer = 0
dots_eaten = 0
# TOTAL_DOTS is computed at startup after populating items_grid

def update_bonus_fruit():
    """Update bonus fruit sprite based on current level."""
    fruit_idx = min(level - 1, len(FRUIT_LEVELS) - 1)
    fx, fy = FRUIT_LEVELS[fruit_idx]
    base_tile = get_tile_index(fx, fy)
    tiles_per_row = sprite_sheet.width // 16
    bonus_fruit[0, 0] = base_tile
    bonus_fruit[0, 1] = base_tile + tiles_per_row

def update_life_display():
    """Update life sprites visibility based on current lives."""
    for i, sprite in enumerate(life_sprites):
        # Show lives - 1 (don't show current life)
        sprite.hidden = (i >= lives - 1)

print(f"Lives: {lives}, Level: {level}")

# =============================================================================
# INPUT HANDLING
# =============================================================================

def read_input(keys=None):
    """Read joystick and queue direction.
    
    Remapped for 270° screen rotation (USB port on left):
    Physical UP -> Game RIGHT
    Physical DOWN -> Game LEFT
    Physical LEFT -> Game UP
    Physical RIGHT -> Game DOWN
    """
    if (DEVICE is WIO and not UP.value) or (DEVICE is FRUIT_JAM and ("d" in keys or "\x1b[C" in keys)):
        pacman.next_direction = DIR_RIGHT
        # print("UP pressed -> RIGHT")
    elif (DEVICE is WIO and not DOWN.value) or (DEVICE is FRUIT_JAM and ("a" in keys or "\x1b[D" in keys)):
        pacman.next_direction = DIR_LEFT
        # print("DOWN pressed -> LEFT")
    elif (DEVICE is WIO and not LEFT.value) or (DEVICE is FRUIT_JAM and ("w" in keys or "\x1b[A" in keys)):
        pacman.next_direction = DIR_UP
        # print("LEFT pressed -> UP")
    elif (DEVICE is WIO and not RIGHT.value) or (DEVICE is FRUIT_JAM and ("s" in keys or "\x1b[B" in keys)):
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

# Mode Timer
mode_timer = 0
mode_index = 0
current_mode = MODE_SCATTER
last_mode_time = time.monotonic()

game_state = STATE_PLAY
death_timer = 0
death_frame_idx = 0

# Ghost Eating State
eat_timer = 0
ghosts_eaten_count = 0 # Reset when power pellet ends
eaten_ghost_ref = None # Reference to the ghost being eaten

# Level Complete State
level_complete_timer = 0
level_blink_count = 0

# Play startup jingle before game begins
print("GET READY!")
display.refresh()
play_startup_jingle()
time.sleep(0.5)

while True:
    start_time = time.monotonic()

    if DEVICE is FRUIT_JAM:
        # extract keys from input buffer
        keys = []
        if (available := supervisor.runtime.serial_bytes_available) > 0:
            buffer = sys.stdin.read(available)
            while buffer:
                key = buffer[0]
                buffer = buffer[1:]
                if key == "\x1b" and buffer and buffer[0] == "[" and len(buffer) >= 2:
                    key += buffer[:2]
                    buffer = buffer[2:]
                keys.append(key)

    if DEVICE is WIO:
        # Check sound toggle button (Button 1)
        button_state = BUTTON_1.value
        if not button_state and last_button_state:  # Button just pressed
            toggle_sound()
        last_button_state = button_state
    elif DEVICE is FRUIT_JAM and "z" in keys:
        toggle_sound()
    
    if game_state == STATE_PLAY:
        # Update Mode
        if mode_index < len(MODE_TIMES):
            if time.monotonic() - last_mode_time > MODE_TIMES[mode_index]:
                mode_index += 1
                last_mode_time = time.monotonic()
                
                # Toggle Mode
                if current_mode == MODE_SCATTER:
                    current_mode = MODE_CHASE
                    print("Mode: CHASE")
                elif current_mode == MODE_CHASE:
                    current_mode = MODE_SCATTER
                    print("Mode: SCATTER")
                    
                # Apply to ghosts
                for g in ghosts:
                    # Only switch mode if not Eaten or Frightened
                    # Actually, if Frightened, we let the frightened timer expire naturally
                    # But if we switch Scatter/Chase in background, we update the "base" mode?
                    # For simplicity: If Frightened, ignore global mode switch until timer ends
                    if g.mode != MODE_FRIGHTENED and g.mode != MODE_EATEN:
                        g.mode = current_mode
                        # Reverse direction on mode switch (Arcade rule)
                        # Only if not in house
                        if not g.in_house:
                            g.reverse_pending = True

        read_input(keys)
        pacman.update()
        
        # Update ghosts
        for ghost in ghosts:
            # Handle Frightened Timer
            if ghost.mode == MODE_FRIGHTENED:
                ghost.frightened_timer += 1
                if ghost.frightened_timer > FRIGHTENED_DURATION:
                    ghost.mode = current_mode # Revert to global mode
            
            ghost.update()
            
            # Collision Check
            # Simple bounding box or distance check
            # 16x16 sprites, so center distance < 8 is a hit
            dx = abs((pacman.x + 8) - (ghost.x + 8))
            dy = abs((pacman.y + 8) - (ghost.y + 8))
            
            if dx < 6 and dy < 6: # Slightly forgiving hitbox
                if ghost.mode == MODE_FRIGHTENED:
                    # Eat Ghost
                    print(f"ATE GHOST {ghost.ghost_type}!")
                    play_eat_ghost_sound()
                    
                    # Calculate Score (200, 400, 800, 1600)
                    points = 200 * (2 ** ghosts_eaten_count)
                    score += points
                    ghosts_eaten_count += 1
                    
                    # Switch to Eating State
                    game_state = STATE_EATING_GHOST
                    eat_timer = 0
                    eaten_ghost_ref = ghost
                    
                    # Hide Pac-Man and Ghost
                    pacman.sprite.hidden = True
                    ghost.sprite.hidden = True
                    
                    # Show Score Sprite at Ghost Position
                    # We reuse the Pac-Man sprite for the score since it's already in main_group
                    # Save Pac-Man's actual position to restore later
                    pacman.saved_x = pacman.x
                    pacman.saved_y = pacman.y
                    
                    pacman.x = ghost.x
                    pacman.y = ghost.y
                    pacman.update_sprite_pos()
                    pacman.set_score_frame(ghosts_eaten_count - 1)
                    pacman.sprite.hidden = False
                    
                    # Set Ghost to Eaten Mode (will be hidden during freeze)
                    ghost.mode = MODE_EATEN
                    
                elif ghost.mode == MODE_EATEN:
                    pass # Ignore eyes
                else:
                    # Killed by ghost
                    print("PAC-MAN DIED!")
                    stop_sound()
                    game_state = STATE_DYING
                    death_timer = 0
                    death_frame_idx = 0
                    
                    # Hide ghosts
                    for g in ghosts:
                        g.sprite.hidden = True
                    
                    # Pause briefly before animation (no sound yet)
                    time.sleep(1.0)
                    break # Stop checking other ghosts
        
        # Bonus Fruit Logic
        if bonus_fruit_active:
            bonus_fruit_timer += 1
            # Fruit disappears after ~10 seconds (600 frames at 60fps, adjust for actual fps)
            if bonus_fruit_timer > 500:
                bonus_fruit_active = False
                bonus_fruit.hidden = True
                print("Bonus fruit expired")
            else:
                # Check collision with fruit
                fruit_x = 13 * 8  # Center of maze
                fruit_y = 17 * 8
                dx = abs((pacman.x + 8) - (fruit_x + 8))
                dy = abs((pacman.y + 8) - (fruit_y + 8))
                if dx < 8 and dy < 8:
                    # Eat fruit!
                    fruit_idx = min(level - 1, len(FRUIT_POINTS) - 1)
                    points = FRUIT_POINTS[fruit_idx]
                    score += points
                    print(f"ATE FRUIT! +{points} points!")
                    play_eat_ghost_sound()  # Reuse eat sound
                    
                    # Show score at fruit position (use STATE_EATING_FRUIT)
                    bonus_fruit_active = False
                    game_state = STATE_EATING_FRUIT
                    eat_timer = 0
                    
                    # Hide fruit and show score
                    # We'll just hide fruit for now - showing score would need another sprite
                    bonus_fruit.hidden = True
        
        # Check for Level Complete (all dots eaten)
        if dots_eaten >= TOTAL_DOTS:
            print(f"LEVEL {level} COMPLETE!")
            stop_sound()
            game_state = STATE_LEVEL_COMPLETE
            level_complete_timer = 0
            level_blink_count = 0

    elif game_state == STATE_DYING:
        death_timer += 1
        if death_timer >= 8: # Animation speed
            death_timer = 0
            death_frame_idx += 1
            
            if death_frame_idx < len(PacMan.DEATH_FRAMES):
                pacman.set_death_frame(death_frame_idx)
                play_death_note(death_frame_idx)  # Play sound with each frame
            else:
                # Death done
                stop_sound()
                time.sleep(1.0)
                
                # Lose a life
                lives -= 1
                update_life_display()
                print(f"Lives remaining: {lives}")
                
                if lives <= 0:
                    print("GAME OVER!")
                    
                    # Update high score if needed
                    if score > high_score:
                        high_score = score
                        if high_score_label:
                            high_score_label.text = f"{high_score}"
                        print(f"NEW HIGH SCORE: {high_score}")
                    
                    # Show GAME OVER
                    if game_over_label:
                        game_over_label.hidden = False
                    
                    # Hide Pac-Man
                    pacman.sprite.hidden = True
                    
                    game_state = STATE_GAME_OVER
                else:
                    # Reset Game (still have lives)
                    pacman.reset()
                    for g in ghosts:
                        g.reset()
                        g.sprite.hidden = False
                    
                    # Reset Mode
                    mode_index = 0
                    current_mode = MODE_SCATTER
                    last_mode_time = time.monotonic()
                    
                    game_state = STATE_PLAY

    elif game_state == STATE_EATING_GHOST:
        eat_timer += 1
        if eat_timer >= 60: # Freeze for 1 second (approx)
            game_state = STATE_PLAY
            
            # Restore Pac-Man
            pacman.sprite.hidden = False
            pacman.set_frame(pacman.direction, 0)
            # Restore position (he shouldn't have moved, but we moved his sprite for score)
            pacman.x = pacman.saved_x
            pacman.y = pacman.saved_y
            pacman.update_sprite_pos()
            # But Pac-Man continues from where he was? No, the game freezes.
            # So Pac-Man is AT the collision point.
            
            # Restore Ghost Visibility (now Eyes)
            if eaten_ghost_ref:
                eaten_ghost_ref.sprite.hidden = False
                eaten_ghost_ref.set_frame(eaten_ghost_ref.direction, 0) # Update to eyes frame immediately
            
            # Reset Pac-Man sprite to normal (it was showing score)
            pacman.set_frame(pacman.direction, 0)

    elif game_state == STATE_EATING_FRUIT:
        eat_timer += 1
        if eat_timer >= 60:  # Brief pause
            game_state = STATE_PLAY

    elif game_state == STATE_LEVEL_COMPLETE:
        level_complete_timer += 1
        
        # Blink the maze (toggle visibility every 15 frames)
        if level_complete_timer % 15 == 0:
            level_blink_count += 1
            # Toggle maze palette between blue and white
            if level_blink_count % 2 == 0:
                maze_palette[1] = 0x2121DE  # Blue (original)
            else:
                maze_palette[1] = 0xFFFFFF  # White
        
        # After ~3 seconds (180 frames) of blinking, advance level
        if level_complete_timer >= 180:
            # Restore maze color
            maze_palette[1] = 0x2121DE
            
            # Advance level
            level += 1
            dots_eaten = 0
            print(f"Starting Level {level}")
            
            # Update fruit display
            update_fruit_sprite()
            
            # Reset dots
            reset_dots()
            
            # Reset positions
            pacman.reset()
            for g in ghosts:
                g.reset()
                g.sprite.hidden = False
            
            # Hide bonus fruit
            bonus_fruit.hidden = True
            bonus_fruit_active = False
            
            # Reset Mode
            mode_index = 0
            current_mode = MODE_SCATTER
            last_mode_time = time.monotonic()
            
            game_state = STATE_PLAY
            
            # Play startup jingle for new level
            play_startup_jingle()
            time.sleep(0.5)

    elif game_state == STATE_GAME_OVER:
        # Wait for any button press to restart
        if (DEVICE is WIO and (not PRESS.value or not UP.value or not DOWN.value or not LEFT.value or not RIGHT.value)) or (DEVICE is FRUIT_JAM and len(keys) > 0):
            # Hide GAME OVER
            if game_over_label:
                game_over_label.hidden = True
            
            # Reset everything
            lives = 3
            score = 0
            level = 1
            dots_eaten = 0
            update_life_display()
            update_fruit_sprite()
            
            # Reset dots and power pellets
            reset_dots()
            
            # Hide bonus fruit
            bonus_fruit.hidden = True
            bonus_fruit_active = False
            
            # Reset positions
            pacman.reset()
            pacman.sprite.hidden = False
            for g in ghosts:
                g.reset()
                g.sprite.hidden = False
            
            # Reset Mode
            mode_index = 0
            current_mode = MODE_SCATTER
            last_mode_time = time.monotonic()
            
            game_state = STATE_PLAY
            
            # Play startup jingle
            play_startup_jingle()
            time.sleep(0.3)

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
            
        # Blink 1UP Label
        if one_up_label:
            one_up_label.hidden = not blink_state

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
    
    # Update Scoreboard
    if score != last_score:
        if score_label:
            score_label.text = f"{score:02d}" # Arcade style: just the number, often 00 or 0
            # Right align logic if needed, but fixed width font helps
            # If score is 0, arcade shows "00" usually
            if score == 0:
                score_label.text = "00"
            else:
                score_label.text = f"{score}"
                
        # Update High Score
        if score > high_score:
            high_score = score
            if high_score_label:
                high_score_label.text = f"{high_score}"
                
        last_score = score
        
    display.refresh(target_frames_per_second=60)
