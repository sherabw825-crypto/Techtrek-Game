"""The slime: a small hopping enemy that notices you and lunges.

Its sheet is a 9x5 grid of 80x80 cells with five animations, so the state
machine is built around exactly those five:

    row 0  idle    6 frames
    row 1  walk    8 frames
    row 2  attack  9 frames   (the big splash)
    row 3  jump    6 frames
    row 4  hurt    3 frames

There is no death animation in the sheet, so dying replays hurt and then
melts away, which reads better than an abrupt disappearance anyway.
"""
import math
import random

from .settings import SLIME, TILE

# name -> (sheet row, frame count, fps, loops)
ANIM = {
    "idle":   (0, 6,  7, True),
    "walk":   (1, 8, 10, True),
    "attack": (2, 9, 14, False),
    "jump":   (3, 6, 10, False),
    "hurt":   (4, 3, 12, False),
}


def _sign(v):
    return (v > 0) - (v < 0)


class Slime:
    def __init__(self, x, y, fx=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.face = -1
        self.grounded = False

        self.hp = SLIME["hp"]
        self.dead = False
        self.fade = 1.0                  # drops to 0 after death, then removed
        self.remove = False

        self.state = "idle"
        self.state_t = 0.0
        self.anim = "idle"
        self.frame = 0
        self.anim_t = 0.0
        self.anim_done = False

        self.hurt_t = 0.0
        self.attack_cd = random.uniform(0.0, 0.6)
        self.has_hit = False             # one damage event per lunge
        self.think_t = random.uniform(0.0, 1.2)
        self.home_x = float(x)
        self.fx = fx

        self.w = SLIME["hb_w"]
        self.h = SLIME["hb_h"]

    # ------------------------------------------------------------ geometry
    def rect(self):
        return (self.x - self.w / 2.0, self.y - self.h, self.w, self.h)

    # ------------------------------------------------------------ animation
    def set_anim(self, name, restart=False):
        if self.anim == name and not restart:
            return
        self.anim = name
        self.frame = 0
        self.anim_t = 0.0
        self.anim_done = False

    def set_state(self, name):
        if self.state == name:
            return
        self.state = name
        self.state_t = 0.0
        self.set_anim(name if name in ANIM else "idle", restart=True)

    def _advance_anim(self, dt):
        _, n, fps, loop = ANIM[self.anim]
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

    # ------------------------------------------------------------ damage
    def take_hit(self, direction, upward=-70):
        if self.dead:
            return
        self.hp -= 1
        self.hurt_t = SLIME["hurt_time"]
        self.vx = direction * 150.0
        self.vy = upward
        self.face = -direction or self.face
        if self.hp <= 0:
            self.dead = True
            self.set_state("hurt")
        else:
            self.set_state("hurt")

    # ------------------------------------------------------------ the step
    def update(self, dt, tiles, player):
        self.state_t += dt
        self.hurt_t = max(0.0, self.hurt_t - dt)
        self.attack_cd = max(0.0, self.attack_cd - dt)

        if self.dead:
            self._physics(dt, tiles)
            self.fade -= dt * 1.6
            if self.fade <= 0:
                self.remove = True
            self._advance_anim(dt)
            return

        if self.hurt_t > 0:
            self._friction(dt, 300.0)
        else:
            getattr(self, "_st_" + self.state)(dt, tiles, player)

        self._physics(dt, tiles)
        self._advance_anim(dt)

        if self.hurt_t <= 0 and self.state == "hurt":
            self.set_state("idle")

        self._touch(player)

    # ------------------------------------------------------------ helpers
    def _friction(self, dt, rate):
        d = rate * dt
        if abs(self.vx) <= d:
            self.vx = 0.0
        else:
            self.vx -= _sign(self.vx) * d

    def _physics(self, dt, tiles):
        self.vy = min(self.vy + SLIME["gravity"] * dt, SLIME["max_fall"])

        # horizontal, with a wall stop
        self.x += self.vx * dt
        probe = self.x + _sign(self.vx) * (self.w / 2.0 + 1)
        if self.vx and tiles.is_solid(probe, self.y - self.h / 2):
            self.x -= self.vx * dt
            self.vx = 0.0

        # vertical
        self.y += self.vy * dt
        self.grounded = False
        if self.vy > 0 and tiles.is_solid(self.x, self.y):
            self.y = math.floor(self.y / TILE) * TILE - 0.01
            self.vy = 0.0
            self.grounded = True
        elif self.vy < 0 and tiles.is_solid(self.x, self.y - self.h):
            self.y = (math.floor((self.y - self.h) / TILE) + 1) * TILE + self.h
            self.vy = 0.0

        if tiles.is_spike(self.x, self.y - 2) or self.y > tiles.pixel_height + 40:
            self.hp = 0
            self.dead = True
            self.set_state("hurt")

    def _edge_ahead(self, tiles, direction):
        """True if walking further that way would step into thin air."""
        ahead = self.x + direction * (self.w / 2.0 + 4)
        return not tiles.is_solid(ahead, self.y + 3)

    def _blocked(self, tiles, direction):
        ahead = self.x + direction * (self.w / 2.0 + 2)
        return tiles.is_solid(ahead, self.y - self.h / 2)

    def _sees(self, player):
        if player.dead:
            return False
        dx = player.x - self.x
        dy = player.y - self.y
        return abs(dx) < SLIME["sight"] and abs(dy) < 48

    # ------------------------------------------------------------ states
    def _st_idle(self, dt, tiles, player):
        self._friction(dt, 400.0)
        self.set_anim("idle")
        self.think_t -= dt
        if self._sees(player):
            self.face = _sign(player.x - self.x) or self.face
            self.set_state("walk")
            return
        if self.think_t <= 0:
            self.think_t = random.uniform(1.0, 2.4)
            # drift back toward where it started
            self.face = _sign(self.home_x - self.x) or -self.face
            self.set_state("walk")

    def _st_walk(self, dt, tiles, player):
        self.set_anim("walk")
        chasing = self._sees(player)
        if chasing:
            self.face = _sign(player.x - self.x) or self.face
            dist = abs(player.x - self.x)
            if dist < SLIME["attack_range"] and self.attack_cd <= 0 \
                    and abs(player.y - self.y) < 30:
                self.set_state("attack")
                self.has_hit = False
                self.vx = 0.0
                return
        else:
            self.think_t -= dt
            if self.think_t <= 0 or abs(self.x - self.home_x) > 90:
                self.think_t = random.uniform(0.8, 2.0)
                self.set_state("idle")
                return

        # turn round at walls and at the lip of a platform
        if self._blocked(tiles, self.face) or self._edge_ahead(tiles, self.face):
            if chasing and self.grounded and self._blocked(tiles, self.face):
                self.set_state("jump")       # try hopping the obstacle
                return
            self.face = -self.face

        self.vx = self.face * SLIME["walk_speed"]

    def _st_jump(self, dt, tiles, player):
        self.set_anim("jump")
        if self.state_t < 0.12:              # squash before the launch
            self.vx = 0.0
            return
        if self.grounded and self.state_t < 0.2:
            self.vy = -SLIME["hop_speed_y"]
            self.vx = self.face * SLIME["hop_speed_x"]
        if self.grounded and self.state_t > 0.25:
            self.set_state("walk")

    def _st_attack(self, dt, tiles, player):
        self.set_anim("attack")
        if self.state_t < SLIME["attack_windup"]:
            self.vx = 0.0
            return
        # the lunge itself
        if self.state_t < SLIME["attack_windup"] + 0.18:
            self.vx = self.face * 95.0
        else:
            self._friction(dt, 420.0)
        if self.anim_done:
            self.attack_cd = SLIME["attack_cooldown"]
            self.set_state("idle")

    def _st_hurt(self, dt, tiles, player):
        self._friction(dt, 300.0)
        if self.anim_done:
            self.set_state("idle")

    # ------------------------------------------------------------ contact
    def _touch(self, player):
        if self.dead or player.dead or player.iframes > 0:
            return
        if self.hurt_t > 0:
            return
        # the splash frames of the lunge are the dangerous part
        dangerous = self.state == "attack" and \
            self.state_t >= SLIME["attack_windup"] and not self.has_hit
        if not (dangerous or self.state in ("walk", "jump", "idle")):
            return
        if _overlap(player.rect(), self.rect()):
            if self.state == "attack":
                self.has_hit = True
            player.hurt(_sign(player.x - self.x) or 1)


def _overlap(a, b):
    return (a[0] < b[0] + b[2] and a[0] + a[2] > b[0]
            and a[1] < b[1] + b[3] and a[1] + a[3] > b[1])
