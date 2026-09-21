"""The level: a grid of tiles plus the point queries the physics needs.

Deliberately free of pygame so the whole movement system can be simulated
headlessly in tests.
"""
import math

from .settings import TILE

EMPTY = 0
SOLID = 1
SPIKE = 2

MAP_W = 128
MAP_H = 36


class TileMap:
    def __init__(self, width=MAP_W, height=MAP_H):
        self.w = width
        self.h = height
        self.cells = bytearray(width * height)

    # ------------------------------------------------------------ building
    def fill(self, x, y, w, h, value=SOLID):
        for j in range(y, y + h):
            if not (0 <= j < self.h):
                continue
            row = j * self.w
            for i in range(x, x + w):
                if 0 <= i < self.w:
                    self.cells[row + i] = value

    # ------------------------------------------------------------ queries
    def at(self, px, py):
        """Tile value at a world-pixel position."""
        i = int(math.floor(px / TILE))
        j = int(math.floor(py / TILE))
        if i < 0 or i >= self.w or j < 0 or j >= self.h:
            return EMPTY
        return self.cells[j * self.w + i]

    def cell(self, i, j):
        if i < 0 or i >= self.w or j < 0 or j >= self.h:
            return EMPTY
        return self.cells[j * self.w + i]

    def is_solid(self, px, py):
        return self.at(px, py) == SOLID

    def is_spike(self, px, py):
        return self.at(px, py) == SPIKE

    @property
    def pixel_width(self):
        return self.w * TILE

    @property
    def pixel_height(self):
        return self.h * TILE


# ---------------------------------------------------------------- the level
SPAWN = (6 * TILE, 26 * TILE)

# Where the slimes start, in tile coordinates. Kept off the slide runway
# (tiles 46-56) so nothing body-blocks the run-up into the tunnel.
SLIME_SPAWNS = [(30, 26), (75, 26), (90, 26), (98, 26), (122, 26)]


def build_level():
    """Hand-authored layout. Each block is a rectangle in tile space.

    Ground sits at row 26, so its surface is world y = 416.
    """
    m = TileMap()

    # opening ground: room to learn the run and the jump
    m.fill(0, 26, 34, 10)
    m.fill(0, 0, 1, 36)                 # left boundary
    m.fill(18, 23, 5, 1)                # a step, 48px up
    m.fill(26, 20, 5, 1)                # another

    # the pit, with spikes waiting at the bottom
    m.fill(34, 34, 12, 2)
    m.fill(34, 33, 12, 1, SPIKE)

    # main ground, running to the boundary
    m.fill(46, 26, 82, 10)
    m.fill(127, 0, 1, 36)               # right boundary

    # low tunnel: only row 25 is free, 16px, so it has to be slid through
    m.fill(56, 20, 6, 5)

    # step + overhang: jump off the step, catch the ledge
    m.fill(64, 24, 3, 1)
    m.fill(68, 21, 6, 4)

    # ascending platforms, an optional high route
    m.fill(78, 23, 5, 1)
    m.fill(86, 20, 5, 1)
    m.fill(94, 17, 5, 1)

    # the wall-jump shaft. The left wall stops three tiles short of the
    # floor so you can walk in underneath it, and reaches higher than the
    # right wall so the last jump clears the lip.
    m.fill(102, 6, 2, 17)               # left wall, rows 6-22
    m.fill(108, 10, 2, 16)              # right wall, rows 10-25
    m.fill(108, 9, 12, 1)               # its cap, and the exit platform

    # summit
    m.fill(112, 6, 6, 1)
    m.fill(120, 3, 6, 1)

    return m
