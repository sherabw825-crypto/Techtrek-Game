"""The Escape menu and the tutorial screen it opens.

Escape opens the menu and pauses the simulation. From the menu you can go
back to the game, read the controls, or quit. Escape inside the tutorial
takes you back to the menu rather than straight out, so you can never get
lost more than one screen deep.
"""
import pygame

from core.settings import VIEW_W, VIEW_H

BONE = (239, 233, 225)
DIM = (150, 142, 165)
CRIMSON = (224, 36, 59)
PANEL = (20, 17, 26)
EDGE = (52, 45, 68)
STEEL = (111, 199, 214)

RESUME, TUTORIAL, QUIT = "resume", "tutorial", "quit"

ITEMS = [
    (RESUME, "Go back"),
    (TUTORIAL, "Tutorial"),
    (QUIT, "Exit game"),
]

# (key, what it does). Shown in two columns on the tutorial screen.
CONTROLS = [
    ("A / D", "Move left and right"),
    ("Arrows", "Also move"),
    ("Shift", "Hold to walk instead of run"),
    ("Space / W", "Jump. Hold longer, jump higher"),
    ("S", "Slide while running"),
    ("J or X", "Attack"),
    ("J, J, J, J", "Four-hit combo, keep the rhythm"),
    ("J in air", "Rising slash"),
    ("S + J in air", "Dive attack, bounces on impact"),
    ("Into a wall", "Cling, Space to wall jump"),
    ("Fall past a ledge", "Grab it, W to climb up"),
    ("K", "Take a hit, see knockback"),
    ("L", "Die, see the death animation"),
    ("R", "Respawn"),
    ("1", "Show hitboxes and state"),
    ("2", "Fly through walls"),
    ("Esc", "This menu"),
]


class Menu:
    """Holds which screen is open and which row is highlighted."""

    def __init__(self):
        self.open = False
        self.screen = "root"        # "root" or "tutorial"
        self.index = 0
        self.tutorial_scroll = 0

    # ------------------------------------------------------------ control
    def toggle(self):
        if self.open:
            self.close()
        else:
            self.open = True
            self.screen = "root"
            self.index = 0

    def close(self):
        self.open = False
        self.screen = "root"
        self.index = 0
        self.tutorial_scroll = 0

    def handle_key(self, key):
        """Returns an action string when one is chosen, else None."""
        if self.screen == "tutorial":
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                       pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.screen = "root"
                self.tutorial_scroll = 0
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.tutorial_scroll = min(self.tutorial_scroll + 1,
                                           max(0, len(CONTROLS) - 12))
            elif key in (pygame.K_UP, pygame.K_w):
                self.tutorial_scroll = max(0, self.tutorial_scroll - 1)
            return None

        if key in (pygame.K_ESCAPE,):
            self.close()
            return RESUME
        if key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(ITEMS)
        elif key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(ITEMS)
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            action = ITEMS[self.index][0]
            if action == TUTORIAL:
                self.screen = "tutorial"
                return None
            if action == RESUME:
                self.close()
            return action
        return None

    # ------------------------------------------------------------ drawing
    def draw(self, surf, font, small):
        veil = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        veil.fill((8, 6, 12, 190))
        surf.blit(veil, (0, 0))
        if self.screen == "tutorial":
            self._draw_tutorial(surf, font, small)
        else:
            self._draw_root(surf, font, small)

    @staticmethod
    def _panel(surf, x, y, w, h):
        pygame.draw.rect(surf, PANEL, (x, y, w, h))
        pygame.draw.rect(surf, EDGE, (x, y, w, h), 1)

    def _draw_root(self, surf, font, small):
        w, h = 176, 116
        x, y = (VIEW_W - w) // 2, (VIEW_H - h) // 2
        self._panel(surf, x, y, w, h)

        title = font.render("Paused", True, BONE)
        surf.blit(title, (x + 14, y + 12))
        pygame.draw.rect(surf, CRIMSON, (x + 14, y + 30, 22, 1))

        for i, (_action, label) in enumerate(ITEMS):
            selected = i == self.index
            ty = y + 44 + i * 18
            if selected:
                pygame.draw.rect(surf, CRIMSON, (x + 14, ty + 4, 3, 7))
            colour = BONE if selected else DIM
            surf.blit(font.render(label, True, colour), (x + 24, ty))

        hint = small.render("Arrows to choose, Enter to pick", True, DIM)
        surf.blit(hint, (x + 14, y + h - 18))

    def _draw_tutorial(self, surf, font, small):
        w, h = 330, 218
        x, y = (VIEW_W - w) // 2, (VIEW_H - h) // 2
        self._panel(surf, x, y, w, h)

        title = font.render("Controls", True, BONE)
        surf.blit(title, (x + 14, y + 10))
        pygame.draw.rect(surf, CRIMSON, (x + 14, y + 28, 22, 1))

        visible = CONTROLS[self.tutorial_scroll:self.tutorial_scroll + 12]
        for i, (key, what) in enumerate(visible):
            ty = y + 38 + i * 13
            surf.blit(small.render(key, True, STEEL), (x + 14, ty))
            surf.blit(small.render(what, True, DIM), (x + 112, ty))

        more = len(CONTROLS) - self.tutorial_scroll - 12
        footer = ("Down for %d more, Esc to go back" % more) if more > 0 \
            else "Esc to go back"
        surf.blit(small.render(footer, True, DIM), (x + 14, y + h - 18))
