"""A camera that leads the player rather than centring on them.

Looking ahead in the direction of travel gives you more of the level you
are about to run into, and leading the fall keeps the ground visible on
the way down.
"""
import random

from core.settings import VIEW_W, VIEW_H


class Camera:
    def __init__(self, tiles):
        self.tiles = tiles
        self.x = 0.0
        self.y = 0.0
        self.shake = 0.0

    def snap_to(self, player):
        self.x = player.x - VIEW_W / 2
        self.y = player.y - VIEW_H / 2
        self._clamp()

    def update(self, dt, player, shake_amount=0.0):
        self.shake = shake_amount
        target_x = player.x + player.face * 34 + player.vx * 0.22 - VIEW_W / 2
        target_y = (player.y - VIEW_H * 0.58
                    + max(-40.0, min(60.0, player.vy * 0.14)))
        k = 1 - pow(0.0015, dt)          # frame-rate independent smoothing
        self.x += (target_x - self.x) * k
        self.y += (target_y - self.y) * k
        self._clamp()

    def _clamp(self):
        self.x = max(0.0, min(self.tiles.pixel_width - VIEW_W, self.x))
        self.y = max(0.0, min(self.tiles.pixel_height - VIEW_H, self.y))

    def offset(self):
        """Integer draw offset, with shake applied. Keeps pixels aligned."""
        ox, oy = self.x, self.y
        if self.shake > 0.2:
            ox += random.uniform(-self.shake, self.shake)
            oy += random.uniform(-self.shake, self.shake)
        return int(round(ox)), int(round(oy))
