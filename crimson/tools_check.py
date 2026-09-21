#!/usr/bin/env python3
"""Sanity check: confirms every sheet is present and slices as expected.

    python tools_check.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pygame

from core import settings as S
from core.player import ANIM as PA
from core.slime import ANIM as SA

pygame.init()
pygame.display.set_mode((1, 1))

problems = []

for name, spec in PA.items():
    path = S.PLAYER_DIR / (spec[0] + ".png")
    if not path.exists():
        problems.append("missing %s" % path)
        continue
    img = pygame.image.load(str(path))
    w, h = img.get_size()
    if w != S.PLAYER_FRAME:
        problems.append("%s is %dpx wide, expected %d" % (path.name, w, S.PLAYER_FRAME))
    if h // S.PLAYER_FRAME != spec[1]:
        problems.append("%s has %d frames, animation '%s' expects %d"
                        % (path.name, h // S.PLAYER_FRAME, name, spec[1]))

slime = S.ENEMY_DIR / "slime_spritesheet.png"
if not slime.exists():
    problems.append("missing %s" % slime)
else:
    w, h = pygame.image.load(str(slime)).get_size()
    need_cols = max(s[1] for s in SA.values())
    need_rows = max(s[0] for s in SA.values()) + 1
    if w // S.SLIME_CELL < need_cols or h // S.SLIME_CELL < need_rows:
        problems.append("slime sheet is %dx%d, need at least %dx%d cells"
                        % (w, h, need_cols, need_rows))

for extra in (S.ENEMY_DIR / "munch_basic_spritesheet.png",
              S.TILE_DIR / "Tiles.png",
              S.TILE_DIR / "Background.png"):
    if not extra.exists():
        problems.append("missing %s" % extra)

pygame.quit()

if problems:
    print("Problems found:")
    for p in problems:
        print("  -", p)
    raise SystemExit(1)
print("All assets present and correctly sized. %d player animations, %d slime animations."
      % (len(PA), len(SA)))
