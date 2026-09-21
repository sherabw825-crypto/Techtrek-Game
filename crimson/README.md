# Crimson

A 2D platformer in Python and pygame, built around game-feel physics rather
than plain gravity: asymmetric gravity, apex hang time, coyote time, jump
buffering, wall jumps, ledge grabs and momentum-preserving slides.

## Running it

```bash
pip install pygame
python run.py
```

Check your assets are all present and correctly sized first, if you like:

```bash
python tools_check.py
```

## Controls

| Key | Action |
|---|---|
| `A` `D` or arrows | Move. Walks, then breaks into a run as speed builds |
| `Shift` | Hold to stay at walking pace |
| `Space` or `W` | Jump. Height varies with how long you hold it |
| `S` | Slide while running. Fits under low ceilings |
| `J` or `X` | Attack. Four-hit ground combo if you keep the rhythm |
| `J` in air | Rising slash |
| `S` + `J` in air | Dive attack. Bounces off whatever it lands on |
| Into a wall | Cling, then `Space` to wall jump |
| Falling past a ledge | Grab it, then `W` to climb up |
| `K` | Take a hit, to see knockback and recovery |
| `L` | Die, to see the death animation |
| `R` | Respawn |
| `1` | Show hitboxes, state name and velocity |
| `2` | Fly through walls |
| `Esc` | Pause menu: go back, tutorial, exit |
| `F11` | Fullscreen |

## Project layout

```
crimson/
├── run.py                  entry point
├── tools_check.py          verifies every sheet is present and sized right
├── requirements.txt
├── core/                   NO pygame in here, so it can be tested headlessly
│   ├── settings.py         every tuning number, in one place
│   ├── tilemap.py          the level, and the collision queries
│   ├── player.py           movement physics and the 25-state machine
│   └── slime.py            slime AI and physics
├── game/                   everything that touches pygame
│   ├── assets.py           sheet loading and slicing
│   ├── animation is folded into assets.py and the core state machines
│   ├── camera.py           look-ahead camera
│   ├── fx.py               dust, screen shake, impact bursts
│   ├── render.py           autotiled terrain, sprites, HUD, debug overlay
│   ├── menu.py             Esc menu and tutorial screen
│   └── app.py              window, fixed-timestep loop, input
└── assets/
    ├── player/             25 sheets: Idle.png, Run.png, Attack_1.png, ...
    ├── enemies/            slime_spritesheet.png, munch_basic_spritesheet.png
    └── tiles/              Tiles.png, Background.png
```

### Where the images go

Everything is already in place. If you swap art in later, this is the
contract each folder has to meet:

- **`assets/player/`** — one PNG per animation, named exactly as in
  `core/player.py`. Each is a **vertical strip of 160×160 frames**. Inside a
  frame the body's centre is `x=72` and the soles rest on `y=96`
  (`PLAYER_PIVOT` in `core/settings.py`). Frame counts must match the table
  in `core/player.py`.
- **`assets/enemies/slime_spritesheet.png`** — a **9×5 grid of 80×80 cells**.
  Row 0 idle (6), row 1 walk (8), row 2 attack (9), row 3 jump (6), row 4
  hurt (3). Body centre `x=24`, base `y=62`.
- **`assets/enemies/munch_basic_spritesheet.png`** — 5 frames of 64×64, drawn
  centred on the point of impact.
- **`assets/tiles/Tiles.png`** — 16px tiles. The terrain autotile block sits
  at columns 0–4, rows 0–4: row 0 is the grass overhang, row 1 the grass
  surface, rows 2–3 the buried fill, row 4 the underside.
- **`assets/tiles/Background.png`** — parallax backdrop, scrolls at 0.25×.

## How the physics is put together

The numbers that make a jump feel good all live in `DEFAULTS` in
`core/settings.py`:

- **Asymmetric gravity** (`fall_mult`) — falling is 1.45× heavier than rising,
  which is what makes a jump feel snappy instead of floaty.
- **Apex hang** (`apex_gravity`, `apex_window`) — gravity drops to 55% near
  the top of the arc. This single value contributes more to jump feel than
  anything else. Try setting it to `1.0` and then `0.25`.
- **Variable height** (`cut_jump`) — releasing jump early scales the
  remaining upward velocity down.
- **Coyote time** — you can still jump for 0.1s after walking off an edge.
- **Jump buffering** — a jump pressed up to 0.13s before landing still fires.
- **Turn sharpness** (`turn_mult`) — acceleration doubles when reversing, so
  direction changes are crisp without making top speed twitchy.

Animation is driven by the physics, not the other way round: walk and run
playback rates scale with actual velocity so footfalls match the ground, and
landing picks between `Land` and `Land_from_Distance` based on impact speed.

## Testing without a display

`core/` imports no pygame, so the whole movement system can be driven
headlessly:

```python
from core.tilemap import build_level
from core.player import Player

class Inp:
    def __init__(self): self.h, self.p = set(), set()
    def held(self, k): return k in self.h
    def pressed(self, k): return k in self.p

class World:
    def __init__(self): self.tiles, self.slimes = build_level(), []

w, inp = World(), Inp()
p = Player(w)
p.respawn(96, 416)

inp.h = {"jump"}; inp.p = {"jump"}
top = p.y
for i in range(180):
    p.update(1 / 120, inp)
    inp.p.clear()
    top = min(top, p.y)
print("jump height:", 416 - top)   # 56.8 px
```

## Credits

Slime sprites from the Heroes Fantasy slime pack. Terrain and background from
Legacy Fantasy – High Forest. Player sprites supplied separately. Check each
pack's own licence before shipping anything commercial.
