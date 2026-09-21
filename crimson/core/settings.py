"""All tuning lives here. No pygame import, so this can be read by tests.

Distances are in world pixels, speeds in px/s, accelerations in px/s^2.
"""
from pathlib import Path

# ---------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PLAYER_DIR = ASSETS / "player"
ENEMY_DIR = ASSETS / "enemies"
TILE_DIR = ASSETS / "tiles"

# ---------------------------------------------------------------- display
VIEW_W, VIEW_H = 480, 270      # internal resolution; everything is drawn here
SCALE = 3                      # window is VIEW * SCALE
WINDOW_TITLE = "Crimson"
FIXED_DT = 1.0 / 120.0         # physics step; independent of frame rate
MAX_FRAME_TIME = 0.25          # never simulate a huge catch-up after a stall

# ---------------------------------------------------------------- sprites
# Player sheets are vertical strips of 160x160 frames.
# Inside a frame the body's centre of mass is x=72 and the soles are y=96.
PLAYER_FRAME = 160
PLAYER_PIVOT = (72, 96)

# Slime sheet is a 9x5 grid of 80x80 cells; body centre x=24, base y=62.
SLIME_CELL = 80
SLIME_PIVOT = (24, 62)

# Munch impact effect: 5 frames of 64x64, drawn centred.
MUNCH_CELL = 64
MUNCH_PIVOT = (32, 32)

TILE = 16

# ---------------------------------------------------------------- physics
DEFAULTS = dict(
    gravity=860.0,        # base downward acceleration
    fall_mult=1.45,       # gravity is heavier on the way down than the way up
    apex_gravity=0.55,    # gravity scale near the top of the arc: hang time
    apex_window=55.0,     # |vy| under this counts as "at the apex"
    apex_boost=1.12,      # horizontal speed bonus during hang time
    jump_vel=305.0,       # upward launch speed
    cut_jump=0.42,        # fraction of vy kept when jump is released early
    max_fall=470.0,       # terminal velocity
    walk_speed=58.0,
    run_speed=142.0,
    ground_accel=760.0,
    ground_decel=980.0,
    air_accel=560.0,
    air_decel=280.0,
    turn_mult=2.0,        # acceleration multiplier when reversing
    coyote=0.10,          # grace period to jump after leaving a ledge
    jump_buffer=0.13,     # early jump presses are remembered this long
    wall_slide=62.0,      # capped fall speed while hugging a wall
    wall_jump_x=178.0,
    wall_jump_y=292.0,
    wall_lock=0.17,       # input ignored briefly after a wall jump
    slide_speed=205.0,
    slide_friction=235.0,
    slide_min=64.0,       # slide ends below this speed
    hard_land_vy=405.0,   # impact speed that triggers the heavy landing
    dive_speed=420.0,
)

# Mutable copy the game actually reads, so it can be retuned at runtime.
T = dict(DEFAULTS)


def reset_tuning():
    T.clear()
    T.update(DEFAULTS)


# ---------------------------------------------------------------- hitboxes
HB_W = 15
HB_H = 30
SLIDE_H = 13

PLAYER_MAX_HP = 5

# ---------------------------------------------------------------- slime
SLIME = dict(
    hp=3,
    walk_speed=26.0,
    hop_speed_x=62.0,
    hop_speed_y=210.0,
    gravity=860.0,
    max_fall=420.0,
    sight=130.0,          # starts following the player inside this range
    attack_range=26.0,    # lunges once the player is this close
    attack_windup=0.30,   # seconds before the lunge actually connects
    attack_cooldown=1.1,
    contact_damage=1,
    hurt_time=0.34,
    hb_w=18,
    hb_h=14,
)
