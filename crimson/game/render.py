"""Drawing the world.

The terrain sheet is a standard 3x3-plus-edges autotile block. Rather than
hand-placing tile indices in the level data, each tile picks its own
appearance from which of its four neighbours are solid.
"""
import pygame

from core import settings as S
from core.settings import TILE, VIEW_W, VIEW_H
from core.tilemap import SOLID, SPIKE

# Terrain block inside Tiles.png, in tile coordinates.
#   row 0 is the grass that overhangs upward above a top tile
#   row 1 is the grass-topped surface
#   rows 2-3 are the buried fill
#   row 4 is the underside
GRASS_OVERHANG_ROW = 0
TOP_ROW = 1
FILL_ROWS = (2, 3)
BOTTOM_ROW = 4
LEFT_COL, RIGHT_COL = 0, 4
MID_COLS = (1, 2, 3)

SPIKE_DARK = (86, 52, 62)
SPIKE_LIGHT = (196, 96, 112)
VOID = (18, 14, 24)


def _variant(i, j):
    """Stable pseudo-random pick so the same tile always looks the same."""
    return (i * 7 + j * 13) % 3


class WorldRenderer:
    def __init__(self, assets, tiles):
        self.assets = assets
        self.tiles = tiles
        self.cache = {}
        self._bg = None
        if assets.background is not None:
            self._bg = assets.background

    # ------------------------------------------------------------ terrain
    def _piece(self, col, row):
        key = (col, row)
        if key not in self.cache:
            self.cache[key] = self.assets.tile(col, row)
        return self.cache[key]

    def _pick(self, i, j):
        """Choose (col, row) for the solid tile at i, j from its neighbours."""
        m = self.tiles
        up = m.cell(i, j - 1) == SOLID
        down = m.cell(i, j + 1) == SOLID
        left = m.cell(i - 1, j) == SOLID
        right = m.cell(i + 1, j) == SOLID
        v = _variant(i, j)

        if not left and right:
            col = LEFT_COL
        elif left and not right:
            col = RIGHT_COL
        elif not left and not right:
            col = LEFT_COL          # a lone column; the left cap reads best
        else:
            col = MID_COLS[v]

        if not up:
            row = TOP_ROW
        elif not down:
            row = BOTTOM_ROW
        else:
            row = FILL_ROWS[v % 2]
        return col, row, (not up)

    def draw_background(self, surf, cam):
        if self._bg is None:
            surf.fill((24, 20, 34))
            return
        bw = self._bg.get_width()
        # two parallax passes: distant sky, then a nearer, dimmer repeat
        off = int(-cam.x * 0.25) % bw
        for x in (off - bw, off, off + bw):
            surf.blit(self._bg, (x, 0))

    def draw_tiles(self, surf, ox, oy):
        m = self.tiles
        i0 = max(0, ox // TILE - 1)
        i1 = min(m.w, (ox + VIEW_W) // TILE + 2)
        j0 = max(0, oy // TILE - 1)
        j1 = min(m.h, (oy + VIEW_H) // TILE + 2)

        for j in range(j0, j1):
            for i in range(i0, i1):
                value = m.cell(i, j)
                if value == 0:
                    continue
                sx = i * TILE - ox
                sy = j * TILE - oy
                if value == SOLID:
                    col, row, exposed = self._pick(i, j)
                    surf.blit(self._piece(col, row), (sx, sy))
                    if exposed:
                        # grass blades hang above the surface tile
                        surf.blit(self._piece(col, GRASS_OVERHANG_ROW),
                                  (sx, sy - TILE))
                elif value == SPIKE:
                    self._draw_spikes(surf, sx, sy)

    @staticmethod
    def _draw_spikes(surf, sx, sy):
        pygame.draw.rect(surf, VOID, (sx, sy, TILE, TILE))
        for k in range(2):
            bx = sx + k * 8
            pygame.draw.polygon(surf, SPIKE_DARK,
                                [(bx, sy + TILE), (bx + 4, sy + 2),
                                 (bx + 8, sy + TILE)])
            pygame.draw.rect(surf, SPIKE_LIGHT, (bx + 3, sy + 2, 2, 3))

    # ------------------------------------------------------------ actors
    def draw_player(self, surf, player, ox, oy):
        # flicker through invulnerability so being hit is legible
        if player.iframes > 0 and not player.dead:
            if int(player.iframes * 18) % 2 == 0:
                return
        frame = self.assets.player_frame(player.anim, player.frame, player.face)
        px, py = S.PLAYER_PIVOT
        if player.face < 0:
            px = S.PLAYER_FRAME - px
        surf.blit(frame, (int(round(player.x)) - ox - px,
                          int(round(player.y)) - oy - py))

    def draw_slime(self, surf, slime, ox, oy):
        frame = self.assets.slime_frame(slime.anim, slime.frame, slime.face)
        px, py = S.SLIME_PIVOT
        if slime.face < 0:
            px = S.SLIME_CELL - px
        pos = (int(round(slime.x)) - ox - px, int(round(slime.y)) - oy - py)

        if slime.dead and slime.fade < 1.0:
            ghost = frame.copy()
            ghost.set_alpha(max(0, int(255 * slime.fade)))
            surf.blit(ghost, pos)
            return
        if slime.hurt_t > 0 and int(slime.hurt_t * 30) % 2 == 0:
            flash = frame.copy()
            flash.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)
            surf.blit(flash, pos)
            return
        surf.blit(frame, pos)

    def draw_fx(self, surf, fx, ox, oy):
        for p in fx.particles:
            k = 1 - p.age / p.life
            size = max(1, int(k * 3))
            col = tuple(int(c * (0.45 + 0.55 * k)) for c in p.color)
            pygame.draw.rect(surf, col,
                             (int(p.x) - ox, int(p.y) - oy, size, size))
        for b in fx.bursts:
            frames = self.assets.munch
            if not frames:
                continue
            idx = min(b.index, len(frames) - 1)
            px, py = S.MUNCH_PIVOT
            surf.blit(frames[idx], (int(b.x) - ox - px, int(b.y) - oy - py))


# ---------------------------------------------------------------- HUD
HEART_FULL = (224, 36, 59)
HEART_EMPTY = (58, 48, 73)


def draw_hud(surf, player, font):
    for i in range(S.PLAYER_MAX_HP):
        x, y = 8 + i * 9, 8
        col = HEART_FULL if i < player.hp else HEART_EMPTY
        pygame.draw.rect(surf, col, (x, y + 1, 6, 5))
        pygame.draw.rect(surf, col, (x + 1, y, 1, 1))
        pygame.draw.rect(surf, col, (x + 4, y, 1, 1))
        pygame.draw.rect(surf, col, (x + 1, y + 6, 4, 1))
        pygame.draw.rect(surf, col, (x + 2, y + 7, 2, 1))

    if player.dead:
        veil = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        veil.fill((10, 8, 16, 150))
        surf.blit(veil, (0, 0))
        text = font.render("respawning", True, (239, 233, 225))
        surf.blit(text, (VIEW_W // 2 - text.get_width() // 2,
                         VIEW_H // 2 - text.get_height() // 2))


def draw_debug(surf, player, slimes, font, ox, oy, noclip):
    box = player.rect()
    pygame.draw.rect(surf, (111, 199, 214),
                     (int(box[0]) - ox, int(box[1]) - oy,
                      int(box[2]), int(box[3])), 1)
    sword = player.sword_box()
    if sword:
        pygame.draw.rect(surf, (224, 36, 59),
                         (int(sword[0]) - ox, int(sword[1]) - oy,
                          int(sword[2]), int(sword[3])), 1)
    for s in slimes:
        r = s.rect()
        pygame.draw.rect(surf, (140, 220, 140),
                         (int(r[0]) - ox, int(r[1]) - oy,
                          int(r[2]), int(r[3])), 1)
    pygame.draw.rect(surf, (201, 161, 74),
                     (int(player.x) - ox - 1, int(player.y) - oy - 1, 2, 2))

    flags = ("grnd " if player.grounded else "air  ")
    if player.coyote_t > 0:
        flags += "coy "
    if player.buffer_t > 0:
        flags += "buf "
    if player.lock_t > 0:
        flags += "lock "
    if noclip:
        flags += "noclip"
    lines = [
        "state  %s  f%d" % (player.state, player.frame),
        "vel    %5.0f %5.0f" % (player.vx, player.vy),
        "flags  %s" % flags,
        "combo  %d   slimes %d" % (player.combo, len(slimes)),
    ]
    for n, line in enumerate(lines):
        surf.blit(font.render(line, True, (239, 233, 225)),
                  (8, VIEW_H - 46 + n * 10))
