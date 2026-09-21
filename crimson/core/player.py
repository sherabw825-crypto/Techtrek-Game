"""The player: movement physics and the animation state machine.

No pygame here. The class talks to the outside world through three small
objects so it can be driven by a real game loop or by a test harness:

    inp    - has .held(name) and .pressed(name)
    world  - has .tiles, .slimes, .kill_slime(...)
    fx     - has .dust(...), .shake(...), .munch(...)

Animation names map one-to-one onto the 25 sprite sheets.
"""
import math

from .settings import T, HB_W, HB_H, SLIDE_H, PLAYER_MAX_HP, TILE

# name -> (sheet file stem, frame count, fps, loops,
#          hit window or None, sword reach, arc)
ANIM = {
    "idle":         ("Idle",                    8,  9,  True,  None,   0,  ""),
    "walk":         ("Walk",                   10, 12,  True,  None,   0,  ""),
    "run":          ("Run",                    10, 15,  True,  None,   0,  ""),
    "run_stop":     ("Run_stop",                6, 16, False,  None,   0,  ""),
    "jump":         ("Jump",                    4, 16, False,  None,   0,  ""),
    "jump_apex":    ("Jump_Apex",               5, 14, False,  None,   0,  ""),
    "fall":         ("Fall",                    5, 12,  True,  None,   0,  ""),
    "land":         ("Land",                    4, 20, False,  None,   0,  ""),
    "land_hard":    ("Land_from_Distance",      8, 18, False,  None,   0,  ""),
    "slide_start":  ("Slide_start",             4, 22, False,  None,   0,  ""),
    "slide":        ("Slide",                   5, 14,  True,  None,   0,  ""),
    "slide_end":    ("Slide_end",               5, 20, False,  None,   0,  ""),
    "wall_start":   ("Wall_hold_start",         3, 20, False,  None,   0,  ""),
    "wall_hold":    ("Wall_hold",               4,  8,  True,  None,   0,  ""),
    "ledge_hold":   ("Ledge_hold",              4,  8,  True,  None,   0,  ""),
    "ledge_climb":  ("_Ledge_hold___climb_up",  5, 14, False,  None,   0,  ""),
    "attack1":      ("Attack_1",                8, 20, False, (2, 4), 30,  ""),
    "attack2":      ("Attack_2",                8, 20, False, (2, 4), 30,  ""),
    "attack3":      ("Wide_Attack_3",          10, 20, False, (3, 6), 52,  ""),
    "attack4":      ("Up_Attack_4",             5, 16, False, (1, 3), 34, "up"),
    "air_attack":   ("Jump_Up_Attack",          6, 18, False, (1, 4), 34, "up"),
    "dive_attack":  ("Fall_Down_Attack",        7, 16,  True, (2, 6), 26, "down"),
    "knockback":    ("Knockback",               5, 14, False,  None,   0,  ""),
    "knock_recover":("Knockback_recover",       7, 15, False,  None,   0,  ""),
    "death":        ("Death",                   9, 11, False,  None,   0,  ""),
}

# States that are allowed to run indefinitely. Anything else that somehow
# overstays gets bounced back to idle by the watchdog in update().
PERSISTENT = {"idle", "walk", "run", "fall", "wall_hold", "ledge_hold",
              "slide", "death"}

# Ledge states place the body themselves: if the landing check fires while
# the climb is still interpolating, it cancels the climb halfway up.
_NO_LAND = {"death", "knockback", "knock_recover", "ledge_hold", "ledge_climb"}


def _sign(v):
    return (v > 0) - (v < 0)


class NullFX:
    """Stand-in used by tests; the real one spawns particles and shakes."""
    def dust(self, x, y, n=1, direction=0, color=None):
        pass

    def shake(self, amount):
        pass

    def munch(self, x, y):
        pass


class Player:
    def __init__(self, world, fx=None):
        self.world = world
        self.fx = fx or NullFX()

        self.x, self.y = 0.0, 0.0
        self.vx, self.vy = 0.0, 0.0
        self.face = 1
        self.grounded = False

        self.state = "idle"
        self.anim = "idle"
        self.frame = 0
        self.anim_t = 0.0
        self.anim_done = False
        self.anim_fps = {k: v[2] for k, v in ANIM.items()}  # run/walk retime

        self.state_t = 0.0
        self.coyote_t = 0.0
        self.buffer_t = 0.0
        self.lock_t = 0.0
        self.ledge_cooldown = 0.0

        self.wall_dir = 0
        self.ledge_top = 0.0
        self.ledge_x = 0.0

        self.combo = 0
        self.combo_window = 0.0
        self.attack_queued = False
        self.hit_ids = set()

        self.hp = PLAYER_MAX_HP
        self.iframes = 0.0
        self.dead = False
        self.respawn_t = 0.0

        self.peak_vy = 0.0
        self.dust_t = 0.0
        self.noclip = False

    # ------------------------------------------------------------ geometry
    @property
    def box_w(self):
        return HB_W

    @property
    def box_h(self):
        return SLIDE_H if self.state in ("slide", "slide_start") else HB_H

    @property
    def box_left(self):
        return self.x - self.box_w / 2.0

    @property
    def box_top(self):
        return self.y - self.box_h

    def rect(self):
        """(x, y, w, h) with the feet at self.y and centred on self.x."""
        return (self.box_left, self.box_top, self.box_w, self.box_h)

    # ------------------------------------------------------------ animation
    def set_anim(self, name, restart=False):
        if self.anim == name and not restart:
            return
        self.anim = name
        self.frame = 0
        self.anim_t = 0.0
        self.anim_done = False
        self.hit_ids = set()

    def set_state(self, name, anim=None):
        if self.state == name:
            return
        self.state = name
        self.state_t = 0.0
        self.set_anim(anim or name, restart=True)

    def _advance_anim(self, dt):
        n, _, loop = ANIM[self.anim][1], None, ANIM[self.anim][3]
        fps = self.anim_fps[self.anim]
        self.anim_t += dt
        step = 1.0 / fps
        while self.anim_t >= step:
            self.anim_t -= step
            if self.frame < n - 1:
                self.frame += 1
            elif loop:
                self.frame = 0
            else:
                self.anim_done = True
                break

    # ------------------------------------------------------------ collision
    def _collide_x(self, dx):
        tiles = self.world.tiles
        if self.noclip:
            self.x += dx
            return False
        self.x += dx
        left, top = self.box_left, self.box_top
        w, h = self.box_w, self.box_h
        y0, y1 = top + 1, top + h - 1
        hit = False
        if dx > 0:
            right = left + w
            y = y0
            while True:
                yy = min(y, y1)
                if tiles.is_solid(right, yy):
                    self.x = math.floor(right / TILE) * TILE - w / 2.0 - 0.01
                    hit = True
                    break
                if yy >= y1:
                    break
                y += TILE
        elif dx < 0:
            y = y0
            while True:
                yy = min(y, y1)
                if tiles.is_solid(left, yy):
                    self.x = (math.floor(left / TILE) + 1) * TILE + w / 2.0 + 0.01
                    hit = True
                    break
                if yy >= y1:
                    break
                y += TILE
        if hit:
            self.vx = 0.0
        return hit

    def _collide_y(self, dy):
        tiles = self.world.tiles
        if self.noclip:
            self.y += dy
            self.grounded = False
            return
        self.y += dy
        left, top = self.box_left, self.box_top
        w, h = self.box_w, self.box_h
        x0, x1 = left + 1, left + w - 1
        if dy > 0:
            bottom = top + h
            x = x0
            while True:
                xx = min(x, x1)
                if tiles.is_solid(xx, bottom):
                    self.y = math.floor(bottom / TILE) * TILE - 0.01
                    self.vy = 0.0
                    self.grounded = True
                    break
                if xx >= x1:
                    break
                x += TILE
        elif dy < 0:
            x = x0
            while True:
                xx = min(x, x1)
                if tiles.is_solid(xx, top):
                    self.y = (math.floor(top / TILE) + 1) * TILE + h + 0.01
                    self.vy = 0.0
                    break
                if xx >= x1:
                    break
                x += TILE

    def _ground_check(self):
        if self.noclip:
            return False
        tiles = self.world.tiles
        left, w, b = self.box_left, self.box_w, self.y + 1.5
        return (tiles.is_solid(left + 1, b)
                or tiles.is_solid(left + w - 1, b)
                or tiles.is_solid(left + w / 2.0, b))

    def _headroom(self):
        """Is there room to stand up here?"""
        tiles = self.world.tiles
        left, w, t = self.box_left, self.box_w, self.y - HB_H - 1
        return not (tiles.is_solid(left + 1, t) or tiles.is_solid(left + w - 1, t))

    def _wall_check(self, direction):
        tiles = self.world.tiles
        left, w, top, h = self.box_left, self.box_w, self.box_top, self.box_h
        x = left + w + 2 if direction > 0 else left - 2
        return tiles.is_solid(x, top + 4) and tiles.is_solid(x, top + h - 6)

    # ------------------------------------------------------------ movement
    def _move_input(self, inp):
        if self.lock_t > 0:
            return 0
        return (1 if inp.held("right") else 0) - (1 if inp.held("left") else 0)

    def _apply_horizontal(self, dt, direction, target, accel, decel):
        if direction != 0:
            a = accel
            if direction * self.vx < 0:
                a *= T["turn_mult"]                  # sharper when reversing
            if abs(self.vy) < T["apex_window"] and not self.grounded:
                target *= T["apex_boost"]            # a nudge during hang time
            self.vx += direction * a * dt
            if direction > 0:
                self.vx = min(self.vx, target)
            else:
                self.vx = max(self.vx, -target)
        else:
            d = decel * dt
            if abs(self.vx) <= d:
                self.vx = 0.0
            else:
                self.vx -= _sign(self.vx) * d

    def _gravity(self, dt, scale=1.0):
        g = T["gravity"] * scale
        if self.vy > 0:
            g *= T["fall_mult"]                      # heavier descent
        if abs(self.vy) < T["apex_window"]:
            g *= T["apex_gravity"]                   # hang at the top
        self.vy = min(self.vy + g * dt, T["max_fall"])

    def _jump(self, vy=None, vx=None):
        self.vy = -(T["jump_vel"] if vy is None else vy)
        if vx is not None:
            self.vx = vx
        self.buffer_t = 0.0
        self.coyote_t = 0.0
        self.set_state("jump")
        self.fx.dust(self.x, self.y, 6)

    # ------------------------------------------------------------ ledges
    def _try_ledge(self, inp):
        if self.ledge_cooldown > 0 or self.vy < -30:
            return False
        direction = self.face
        mi = self._move_input(inp)
        if mi != direction and mi != 0:
            return False
        tiles = self.world.tiles
        hx = self.x + direction * (HB_W / 2.0 + 4)
        # Sweep the band the hands could reach and take the first solid.
        # It only counts as a ledge if there is clear air above it, which is
        # what stops this firing all the way down a tall wall.
        probe = self.y - 44
        while probe <= self.y - 10:
            if tiles.is_solid(hx, probe):
                top = math.floor(probe / TILE) * TILE
                if tiles.is_solid(hx, top - 6) or tiles.is_solid(hx, top - 18):
                    return False
                self.ledge_top = top
                self.ledge_x = self.x
                self.peak_vy = 0.0          # do not carry the fall into the climb
                self.y = top + 34
                self.vx = self.vy = 0.0
                self.set_state("ledge_hold")
                return True
            probe += 4
        return False

    # ------------------------------------------------------------ combat
    def sword_box(self):
        sheet = ANIM[self.anim]
        window, reach, arc = sheet[4], sheet[5], sheet[6]
        if window is None or not (window[0] <= self.frame <= window[1]):
            return None
        if arc == "down":
            return (self.x - 12, self.y - 8, 24, 22)
        if arc == "up":
            x = self.x if self.face > 0 else self.x - reach
            return (x, self.y - 44, reach, 34)
        x = self.x if self.face > 0 else self.x - reach
        return (x, self.y - 26, reach, 24)

    def _resolve_hits(self):
        box = self.sword_box()
        if box is None:
            return
        arc = ANIM[self.anim][6]
        for slime in self.world.slimes:
            if slime.dead or id(slime) in self.hit_ids:
                continue
            if _overlap(box, slime.rect()):
                self.hit_ids.add(id(slime))
                upward = -180 if arc == "up" else -70
                slime.take_hit(_sign(slime.x - self.x) or self.face, upward)
                self.fx.munch(slime.x, slime.y - slime.h / 2)
                self.fx.shake(3)
                if arc == "down":                    # a landed dive bounces
                    self.vy = -240.0
                    self.set_state("jump_apex")

    def hurt(self, direction):
        if self.iframes > 0 or self.dead:
            return
        self.hp -= 1
        if self.hp <= 0:
            self.die()
            return
        self.iframes = 1.0
        self.face = -direction
        self.vx = direction * 190.0
        self.vy = -175.0
        self.lock_t = 0.3
        self.set_state("knockback")
        self.fx.shake(5)

    def die(self):
        if self.dead:
            return
        self.dead = True
        self.hp = 0
        self.respawn_t = 1.5
        self.vx = -self.face * 60.0
        self.vy = -150.0
        self.set_state("death")
        self.fx.shake(6)

    def respawn(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.dead = False
        self.hp = PLAYER_MAX_HP
        self.iframes = 1.2
        self.face = 1
        self.combo = 0
        self.peak_vy = 0.0
        self.lock_t = 0.0
        self.state = "idle"
        self.state_t = 0.0
        self.set_anim("idle", restart=True)

    # ------------------------------------------------------------ the step
    def update(self, dt, inp):
        self.state_t += dt
        self.combo_window = max(0.0, self.combo_window - dt)
        self.lock_t = max(0.0, self.lock_t - dt)
        self.iframes = max(0.0, self.iframes - dt)
        self.ledge_cooldown = max(0.0, self.ledge_cooldown - dt)

        if self.noclip:
            self._noclip(dt, inp)
            return

        tiles = self.world.tiles
        if not self.dead:
            if tiles.is_spike(self.x, self.y - 4) or \
               tiles.is_spike(self.x, self.y - HB_H + 2):
                self.die()
                return
            if self.y > tiles.pixel_height + 60:
                self.die()
                return

        grounded_before = self.grounded
        self.grounded = self._ground_check()

        self.coyote_t = T["coyote"] if self.grounded else max(0.0, self.coyote_t - dt)
        if inp.pressed("jump"):
            self.buffer_t = T["jump_buffer"]
        else:
            self.buffer_t = max(0.0, self.buffer_t - dt)

        if not self.grounded:
            self.peak_vy = max(self.peak_vy, self.vy)

        # watchdog: nothing transient may outlast its animation this badly
        if self.state_t > 3.0 and self.state not in PERSISTENT:
            self.set_state("idle" if self.grounded else "fall")

        getattr(self, "_st_" + self.state)(dt, inp)

        # integrate. _collide_y can flip grounded on, which is why the
        # landing check has to come after it rather than before the state.
        # Ledge states place the body themselves and must not be pushed back.
        if self.state not in ("ledge_hold", "ledge_climb"):
            self._collide_x(self.vx * dt)
            self._collide_y(self.vy * dt)
        if self.grounded and self.vy > 0:
            self.vy = 0.0

        if self.grounded and not grounded_before and self.state not in _NO_LAND:
            heavy = self.peak_vy >= T["hard_land_vy"]
            self.fx.dust(self.x, self.y, 14 if heavy else 6)
            if self.state == "dive_attack":
                self.set_state("land_hard")
                self.vx *= 0.2
                self.fx.shake(4)
            elif heavy:
                self.set_state("land_hard")
                self.vx *= 0.35
                self.fx.shake(3)
            elif abs(self.vx) < 30 or self.peak_vy > 190:
                self.set_state("land")
                self.vx *= 0.6
            else:
                # landing at speed keeps the momentum: no recovery pose
                self.set_state("run" if abs(self.vx) > T["walk_speed"] + 12 else "walk")
            self.peak_vy = 0.0

        self._advance_anim(dt)
        self._resolve_hits()
        self._running_dust(dt)

    def _noclip(self, dt, inp):
        sp = 240.0
        self.vx = ((1 if inp.held("right") else 0) - (1 if inp.held("left") else 0)) * sp
        self.vy = ((1 if inp.held("down") else 0) - (1 if inp.held("up") else 0)) * sp
        if self.vx:
            self.face = _sign(self.vx)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.set_state("fall")
        self._advance_anim(dt)

    def _running_dust(self, dt):
        if self.grounded and self.state == "run" and abs(self.vx) > T["run_speed"] * 0.8:
            self.dust_t -= dt
            if self.dust_t <= 0:
                self.dust_t = 0.11
                self.fx.dust(self.x - self.face * 5, self.y, 1, -self.face)

    # ------------------------------------------------------------ helpers
    def _can_act(self):
        return not self.dead and self.lock_t <= 0

    def _start_attack(self, inp):
        if self.grounded:
            self.combo = (self.combo % 4) + 1 if self.combo_window > 0 else 1
            self.combo_window = 0.0
            self.set_state("attack%d" % self.combo)
            self.vx += self.face * (90 if self.combo == 3 else 45)
        elif inp.held("down"):
            self.set_state("dive_attack")
            self.vy = T["dive_speed"]
            self.vx *= 0.3
        else:
            self.set_state("air_attack")
            self.vy = min(self.vy, -40.0)

    def _ground_move(self, dt, inp):
        d = self._move_input(inp)
        if d != 0:
            self.face = d
        top = T["walk_speed"] if inp.held("walk_mod") else T["run_speed"]
        self._apply_horizontal(dt, d, top, T["ground_accel"], T["ground_decel"])

    def _air_control(self, dt, inp, scale=1.0):
        d = self._move_input(inp)
        if d != 0 and self.lock_t <= 0:
            self.face = d
        top = T["walk_speed"] if inp.held("walk_mod") else T["run_speed"]
        self._apply_horizontal(dt, d, top,
                               T["air_accel"] * scale, T["air_decel"] * scale)

    def _friction(self, dt, scale=1.0):
        d = T["ground_decel"] * scale * dt
        if abs(self.vx) <= d:
            self.vx = 0.0
        else:
            self.vx -= _sign(self.vx) * d

    def _ground_transitions(self, inp):
        if not self._can_act():
            return False
        if inp.pressed("attack"):
            self._start_attack(inp)
            return True
        if self.buffer_t > 0 and self.coyote_t > 0 and self._headroom():
            self._jump()
            return True
        if inp.held("down") and abs(self.vx) > T["walk_speed"] \
                and self.state != "slide_start":
            self.set_state("slide_start")
            return True
        if not self.grounded and self.vy >= 0 and \
                self.state not in ("slide", "slide_start"):
            self.set_state("fall")
            return True
        return False

    def _air_transitions(self, inp):
        if self.grounded:
            return False
        if self._can_act() and inp.pressed("attack"):
            self._start_attack(inp)
            return True
        if self._try_ledge(inp):
            return True
        d = self._move_input(inp)
        # catching slightly before the apex, not only once falling, is what
        # keeps a wall climb from losing the height it just gained
        if self.vy > -80 and d != 0 and self._wall_check(d):
            self._enter_wall(d)
            return True
        return False

    def _enter_wall(self, direction):
        self.wall_dir = direction
        self.face = direction
        # carry a little upward momentum into the grab instead of killing it
        self.vy = self.vy * 0.35 if self.vy < 0 else min(self.vy, 45.0)
        self.set_state("wall_start")

    def _wall_physics(self, dt, inp):
        d = self.wall_dir
        self.vy = min(self.vy + T["gravity"] * 0.35 * dt, T["wall_slide"])
        self.vx = d * 8.0                              # stay pressed to it
        if self.state_t % 0.1 < dt:
            self.fx.dust(self.x + d * 7, self.y - 14, 1, -d)

        if self.buffer_t > 0:
            self.lock_t = T["wall_lock"]
            self.face = -d
            self._jump(T["wall_jump_y"], -d * T["wall_jump_x"])
            self.fx.shake(2)
            return
        if self.grounded:
            self.set_state("idle")
            return
        if not self._wall_check(d):
            self.ledge_cooldown = 0.12
            self.set_state("fall")
            return
        if self._move_input(inp) == -d:                # let go by holding away
            self.lock_t = 0.08
            self.ledge_cooldown = 0.12
            self.set_state("fall")
            return
        self._try_ledge(inp)

    def _slide_exits(self, inp):
        if not self.grounded:
            self.set_state("fall")
            return True
        if not self._headroom():
            return True
        if self.buffer_t > 0 and self.coyote_t > 0:
            self._jump()
            return True
        if self._can_act() and inp.pressed("attack"):
            self._start_attack(inp)
            return True
        if not inp.held("down") and self.state_t > 0.14:
            self.set_state("slide_end")
            return True
        return False

    # ------------------------------------------------------------ states
    def _st_idle(self, dt, inp):
        self._ground_move(dt, inp)
        self._gravity(dt)
        if self._ground_transitions(inp):
            return
        if abs(self.vx) > 4:
            self.set_state("run" if abs(self.vx) > T["walk_speed"] + 12 else "walk")
        else:
            self.set_anim("idle")

    def _st_walk(self, dt, inp):
        self._ground_move(dt, inp)
        self._gravity(dt)
        if self._ground_transitions(inp):
            return
        if abs(self.vx) < 3:
            self.set_state("idle")
            return
        if abs(self.vx) > T["walk_speed"] + 12 and not inp.held("walk_mod"):
            self.set_state("run")
            return
        self.set_anim("walk")
        # playback follows real speed, so footfalls match the ground
        self.anim_fps["walk"] = 7 + abs(self.vx) / T["walk_speed"] * 6

    def _st_run(self, dt, inp):
        d = self._move_input(inp)
        self._ground_move(dt, inp)
        self._gravity(dt)
        if self._ground_transitions(inp):
            return
        # reversing at speed plants a foot and skids
        if d != 0 and d * self.vx < -20 and abs(self.vx) > T["run_speed"] * 0.6:
            self.set_state("run_stop")
            return
        if d == 0 and abs(self.vx) > T["run_speed"] * 0.7:
            self.set_state("run_stop")
            return
        if abs(self.vx) < 3:
            self.set_state("idle")
            return
        if abs(self.vx) <= T["walk_speed"] + 10 or inp.held("walk_mod"):
            self.set_state("walk")
            return
        self.set_anim("run")
        self.anim_fps["run"] = 9 + abs(self.vx) / T["run_speed"] * 8

    def _st_run_stop(self, dt, inp):
        self._gravity(dt)
        self._friction(dt, 1.9)
        if self.state_t > 0.06:
            self.fx.dust(self.x - self.face * 4, self.y, 1, -self.face)
        if self._ground_transitions(inp):
            return
        d = self._move_input(inp)
        if self.anim_done or abs(self.vx) < 6:
            if d != 0:
                self.face = d
                self.set_state("walk")
            else:
                self.set_state("idle")

    def _st_jump(self, dt, inp):
        self._air_control(dt, inp)
        # variable height: let go early and the rise is cut short
        if not inp.held("jump") and self.vy < 0:
            self.vy *= T["cut_jump"] ** (dt * 60)
        self._gravity(dt)
        if self._air_transitions(inp):
            return
        if self.vy > -T["apex_window"]:
            self.set_state("jump_apex")

    def _st_jump_apex(self, dt, inp):
        self._air_control(dt, inp)
        if not inp.held("jump") and self.vy < 0:
            self.vy *= T["cut_jump"] ** (dt * 60)
        self._gravity(dt)
        if self._air_transitions(inp):
            return
        if self.vy > T["apex_window"]:
            self.set_state("fall")

    def _st_fall(self, dt, inp):
        self._air_control(dt, inp)
        self._gravity(dt)
        if self.grounded:                    # falling while grounded is never valid
            d = self._move_input(inp)
            if d != 0:
                self.set_state("run" if abs(self.vx) > T["walk_speed"] + 12 else "walk")
            else:
                self.set_state("idle")
            return
        self._air_transitions(inp)

    def _st_land(self, dt, inp):
        self._gravity(dt)
        d = self._move_input(inp)
        self._apply_horizontal(dt, d, T["run_speed"],
                               T["ground_accel"] * 0.7, T["ground_decel"])
        if self._can_act() and inp.pressed("attack"):
            self._start_attack(inp)
            return
        if self.buffer_t > 0 and self.coyote_t > 0:
            self._jump()
            return
        if d != 0 and self.state_t > 0.06:
            self.face = d
            self.set_state("walk")
            return
        if self.anim_done:
            self.set_state("idle")

    def _st_land_hard(self, dt, inp):
        self._gravity(dt)
        self._friction(dt)
        # a heavier landing costs more recovery before you can act
        if self.state_t > 0.22:
            if self.buffer_t > 0 and self.coyote_t > 0:
                self._jump()
                return
            d = self._move_input(inp)
            if d != 0:
                self.face = d
                self.set_state("walk")
                return
        if self.anim_done:
            self.set_state("idle")

    def _st_slide_start(self, dt, inp):
        self._gravity(dt)
        self.vx = self.face * T["slide_speed"]
        if self.anim_done:
            self.set_state("slide")
        self._slide_exits(inp)

    def _st_slide(self, dt, inp):
        self._gravity(dt)
        f = T["slide_friction"] * dt
        if abs(self.vx) <= f:
            self.vx = 0.0
        else:
            self.vx -= _sign(self.vx) * f
        if self.state_t % 0.08 < dt:
            self.fx.dust(self.x - self.face * 6, self.y, 1, -self.face)
        # under a low ceiling you can still shuffle, so a slide never traps you
        if not self._headroom():
            d = self._move_input(inp)
            if d != 0:
                self.face = d
                self.vx += d * 520 * dt
                if abs(self.vx) > 92:
                    self.vx = d * 92
        if abs(self.vx) < T["slide_min"] and self._headroom():
            self.set_state("slide_end")
            return
        self._slide_exits(inp)

    def _st_slide_end(self, dt, inp):
        self._gravity(dt)
        self._friction(dt)
        if not self.grounded:
            self.set_state("fall")
            return
        if self.buffer_t > 0 and self.coyote_t > 0 and self._headroom():
            self._jump()
            return
        if self.anim_done:
            d = self._move_input(inp)
            if d != 0:
                self.face = d
                self.set_state("walk")
            else:
                self.set_state("idle")

    def _st_wall_start(self, dt, inp):
        self._wall_physics(dt, inp)
        if self.state == "wall_start" and self.anim_done:
            self.set_state("wall_hold")

    def _st_wall_hold(self, dt, inp):
        self._wall_physics(dt, inp)

    def _st_ledge_hold(self, dt, inp):
        self.vx = self.vy = 0.0
        self.y = self.ledge_top + 34
        if inp.held("down"):
            self.ledge_cooldown = 0.35
            self.set_state("fall")
            return
        if inp.pressed("jump") or inp.held("up"):
            self.set_state("ledge_climb")
            return
        if self._can_act() and inp.pressed("attack"):
            self.ledge_cooldown = 0.3
            self.set_state("fall")

    def _st_ledge_climb(self, dt, inp):
        self.vx = self.vy = 0.0
        n, fps = ANIM["ledge_climb"][1], self.anim_fps["ledge_climb"]
        k = min(1.0, self.state_t / (n / fps))
        # slide the body up and over across the animation
        self.y = self.ledge_top + 34 - 34 * _ease(k)
        self.x = self.ledge_x + self.face * 18 * _ease(max(0.0, k - 0.45) / 0.55)
        if self.anim_done:
            self.y = self.ledge_top
            self.x = self.ledge_x + self.face * 18
            self.grounded = True
            self.ledge_cooldown = 0.2
            self.set_state("idle")

    def _attack_state(self, dt, inp):
        self._gravity(dt)
        n, fps = ANIM[self.anim][1], self.anim_fps[self.anim]
        duration = n / fps
        self._friction(dt, 1.3)          # the lunge carries, then settles
        if not self.grounded and self.state_t > 0.05:
            self.set_state("fall")
            return
        # buffering the next swing near the end chains the combo
        if inp.pressed("attack") and self.state_t > duration * 0.4:
            self.attack_queued = True
        if self.anim_done:
            self.combo_window = 0.32
            if self.attack_queued:
                self.attack_queued = False
                self._start_attack(inp)
                return
            d = self._move_input(inp)
            if d != 0:
                self.face = d
                self.set_state("walk")
            else:
                self.set_state("idle")

    _st_attack1 = _attack_state
    _st_attack2 = _attack_state
    _st_attack3 = _attack_state
    _st_attack4 = _attack_state

    def _st_air_attack(self, dt, inp):
        self._air_control(dt, inp, 0.6)
        self._gravity(dt, 0.75)
        if self.grounded:
            self.set_state("land")
            return
        if self.anim_done:
            self.set_state("jump_apex" if self.vy < 0 else "fall")

    def _st_dive_attack(self, dt, inp):
        # committed dive: almost no steering, fixed downward speed
        self._air_control(dt, inp, 0.18)
        self.vy = T["dive_speed"]
        if self.grounded:
            self.set_state("land_hard")
            self.vx *= 0.2
            self.fx.shake(4)
            return
        if self._wall_check(self.face) and \
                inp.held("right" if self.face > 0 else "left"):
            self._enter_wall(self.face)

    def _st_knockback(self, dt, inp):
        self._gravity(dt)
        if self.grounded:
            self._friction(dt, 0.8)
        if self.anim_done and self.grounded:
            self.set_state("knock_recover")

    def _st_knock_recover(self, dt, inp):
        self._gravity(dt)
        self._friction(dt)
        if self.state_t > 0.25 and self.buffer_t > 0 and self.coyote_t > 0:
            self._jump()
            return
        if self.anim_done:
            self.set_state("idle")

    def _st_death(self, dt, inp):
        self._gravity(dt)
        if self.grounded:
            self._friction(dt, 0.9)
        self.respawn_t -= dt


def _ease(k):
    return k * k * (3 - 2 * k)


def _overlap(a, b):
    return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0]
            and a[1] < b[1] + b[3] and a[1] + a[3] > b[1])
