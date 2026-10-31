"""
config.py - Global constants for Gravity Escape.

All physics runs in "game units": distances in pixels, time in seconds.
The HUD converts these into kilometres and km/s with simple display scales
so the numbers feel like real spaceflight.
"""

import os

# ----------------------------------------------------------------- window
WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "Gravity Escape"

# ---------------------------------------------------------------- physics
# Gravitational constant in game units. Planet masses in the level files
# are chosen so that G * M gives pleasant orbital speeds on screen.
G = 1000.0

# Fixed physics time step. The game loop runs several physics steps per
# rendered frame so the simulation is stable and frame-rate independent.
PHYSICS_DT = 1.0 / 240.0
MAX_FRAME_TIME = 0.1          # clamp long frames (e.g. window dragged)

# ------------------------------------------------------------- spacecraft
SHIP_MASS = 1.0               # cancels out in a = F/m, kept for clarity
SHIP_RADIUS = 9               # collision radius (pixels)
THRUST_ACCEL = 140.0          # engine acceleration (pixels / s^2)
ROTATION_SPEED = 210.0        # degrees per second
FUEL_BURN_RATE = 10.0         # % of tank burned per second of thrust

# ------------------------------------------------- trajectory prediction
PREDICT_DT = 1.0 / 60.0       # time step used for the prediction
PREDICT_STEPS = 480           # 480 * 1/60 s = 8 s into the future

# ------------------------------------------------------ world boundaries
OUT_OF_BOUNDS_MARGIN = 420    # how far off-screen before you're "lost"

# ---------------------------------------------------- HUD display scales
KM_PER_PIXEL = 40.0           # altitude display
KMS_PER_PIXEL_PER_S = 0.1     # speed display: 120 px/s -> 12.0 km/s

# ------------------------------------------------------------------ paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
LEVEL_DIR = os.path.join(BASE_DIR, "levels")
SAVE_FILE = os.path.join(BASE_DIR, "highscores.json")
LEVEL_FILES = ["level1.json", "level2.json", "level3.json"]

# ----------------------------------------------------------------- colours
BG_COLOR = (6, 8, 18)
WHITE = (240, 244, 255)
GREY = (140, 150, 170)
DIM = (80, 90, 110)
CYAN = (90, 220, 255)
GREEN = (90, 255, 160)
YELLOW = (255, 210, 90)
ORANGE = (255, 150, 60)
RED = (255, 80, 80)
PANEL = (14, 20, 38)
