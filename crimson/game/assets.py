"""Loading and slicing every sprite sheet.

Frames are pre-flipped at load time. Flipping during the draw call would
mean a transform per sprite per frame, which is wasted work when there are
only two possible facings.
"""
import pygame

from core import settings as S
from core.player import ANIM as PLAYER_ANIM
from core.slime import ANIM as SLIME_ANIM


def _strip(path, frame, count):
    """Slice a vertical strip of square frames."""
    sheet = pygame.image.load(str(path)).convert_alpha()
    out = []
    for i in range(count):
        surf = pygame.Surface((frame, frame), pygame.SRCALPHA)
        surf.blit(sheet, (0, 0), (0, i * frame, frame, frame))
        out.append(surf)
    return out


def _grid(path, cell, row, count):
    """Slice `count` cells from one row of a grid sheet."""
    sheet = pygame.image.load(str(path)).convert_alpha()
    out = []
    for i in range(count):
        surf = pygame.Surface((cell, cell), pygame.SRCALPHA)
        surf.blit(sheet, (0, 0), (i * cell, row * cell, cell, cell))
        out.append(surf)
    return out


def _both_facings(frames):
    """(facing_right, facing_left) lists."""
    return frames, [pygame.transform.flip(f, True, False) for f in frames]


class Assets:
    """Everything the renderer needs, loaded once."""

    def __init__(self):
        self.player = {}
        self.slime = {}
        self.munch = []
        self.tiles = None
        self.background = None
        self.missing = []
        self.load()

    # ------------------------------------------------------------ loading
    def load(self):
        # 25 player sheets, one per animation
        for name, spec in PLAYER_ANIM.items():
            stem, count = spec[0], spec[1]
            path = S.PLAYER_DIR / (stem + ".png")
            if not path.exists():
                self.missing.append(str(path))
                continue
            self.player[name] = _both_facings(
                _strip(path, S.PLAYER_FRAME, count))

        # one slime sheet, five rows
        slime_path = S.ENEMY_DIR / "slime_spritesheet.png"
        if slime_path.exists():
            for name, (row, count, _fps, _loop) in SLIME_ANIM.items():
                self.slime[name] = _both_facings(
                    _grid(slime_path, S.SLIME_CELL, row, count))
        else:
            self.missing.append(str(slime_path))

        # the impact burst shown when the sword connects
        munch_path = S.ENEMY_DIR / "munch_basic_spritesheet.png"
        if munch_path.exists():
            self.munch = _grid(munch_path, S.MUNCH_CELL, 0, 5)
        else:
            self.missing.append(str(munch_path))

        tiles_path = S.TILE_DIR / "Tiles.png"
        if tiles_path.exists():
            self.tiles = pygame.image.load(str(tiles_path)).convert_alpha()
        else:
            self.missing.append(str(tiles_path))

        bg_path = S.TILE_DIR / "Background.png"
        if bg_path.exists():
            self.background = pygame.image.load(str(bg_path)).convert_alpha()
        else:
            self.missing.append(str(bg_path))

    # ------------------------------------------------------------ access
    def tile(self, col, row):
        """A 16x16 piece of the terrain sheet."""
        surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
        surf.blit(self.tiles, (0, 0),
                  (col * S.TILE, row * S.TILE, S.TILE, S.TILE))
        return surf

    def player_frame(self, anim, index, facing):
        right, left = self.player[anim]
        frames = right if facing > 0 else left
        return frames[min(index, len(frames) - 1)]

    def slime_frame(self, anim, index, facing):
        right, left = self.slime[anim]
        frames = right if facing > 0 else left
        return frames[min(index, len(frames) - 1)]
