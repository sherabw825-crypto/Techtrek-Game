"""The game loop, the window, and the glue between core and pygame."""
import sys

import pygame

from core import settings as S
from core.settings import VIEW_W, VIEW_H, SCALE, FIXED_DT, MAX_FRAME_TIME, TILE
from core.tilemap import build_level, SPAWN, SLIME_SPAWNS
from core.player import Player
from core.slime import Slime

from .assets import Assets
from .camera import Camera
from .fx import FX
from .menu import Menu, RESUME, QUIT
from .render import WorldRenderer, draw_hud, draw_debug

# pygame 1.x has no WINDOWFOCUSLOST; resolve it once instead of every frame
FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", -1)

# physical key -> action name the core understands
BINDINGS = {
    pygame.K_a: "left", pygame.K_LEFT: "left",
    pygame.K_d: "right", pygame.K_RIGHT: "right",
    pygame.K_s: "down", pygame.K_DOWN: "down",
    pygame.K_w: "up", pygame.K_UP: "up",
    pygame.K_SPACE: "jump",
    pygame.K_LSHIFT: "walk_mod", pygame.K_RSHIFT: "walk_mod",
    pygame.K_j: "attack", pygame.K_x: "attack",
    pygame.K_k: "hurt_self", pygame.K_l: "kill_self", pygame.K_r: "respawn",
    pygame.K_1: "dbg_boxes", pygame.K_2: "dbg_noclip",
}

# W and Space both jump, but W also climbs a ledge, so both map to "up" too
EXTRA = {pygame.K_w: ("up", "jump"), pygame.K_SPACE: ("jump",)}


class Input:
    """What the core sees: which actions are held and which fired this step."""

    def __init__(self):
        self._held = set()
        self._pressed = set()

    def key_down(self, key):
        for action in self._actions(key):
            if action not in self._held:
                self._pressed.add(action)
            self._held.add(action)

    def key_up(self, key):
        for action in self._actions(key):
            self._held.discard(action)

    @staticmethod
    def _actions(key):
        if key in EXTRA:
            return EXTRA[key]
        action = BINDINGS.get(key)
        return (action,) if action else ()

    def held(self, action):
        return action in self._held

    def pressed(self, action):
        return action in self._pressed

    def end_step(self):
        self._pressed.clear()

    def release_all(self):
        self._held.clear()
        self._pressed.clear()


class World:
    """What the player and slimes are allowed to know about each other."""

    def __init__(self, fx):
        self.tiles = build_level()
        self.slimes = []
        self.fx = fx

    def spawn_slimes(self):
        self.slimes = [Slime(tx * TILE + 8, ty * TILE)
                       for tx, ty in SLIME_SPAWNS]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(S.WINDOW_TITLE)
        self.window = pygame.display.set_mode(
            (VIEW_W * SCALE, VIEW_H * SCALE), pygame.RESIZABLE)
        self.canvas = pygame.Surface((VIEW_W, VIEW_H)).convert()
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 16)
        self.small = pygame.font.Font(None, 13)

        self.assets = Assets()
        if self.assets.missing:
            self._fatal_missing()

        self.fx = FX()
        self.world = World(self.fx)
        self.player = Player(self.world, self.fx)
        self.renderer = WorldRenderer(self.assets, self.world.tiles)
        self.camera = Camera(self.world.tiles)
        self.menu = Menu()
        self.inp = Input()

        self.show_boxes = False
        self.accumulator = 0.0
        self.running = True
        self.reset()

    # ------------------------------------------------------------ helpers
    def _fatal_missing(self):
        print("Missing asset files:", file=sys.stderr)
        for path in self.assets.missing:
            print("  " + path, file=sys.stderr)
        print("\nExpected layout:\n"
              "  assets/player/*.png     25 sheets\n"
              "  assets/enemies/*.png    slime_spritesheet, munch_basic_spritesheet\n"
              "  assets/tiles/*.png      Tiles.png, Background.png", file=sys.stderr)
        pygame.quit()
        raise SystemExit(1)

    def reset(self):
        self.player.respawn(*SPAWN)
        self.world.spawn_slimes()
        self.fx.clear()
        self.camera.snap_to(self.player)

    # ------------------------------------------------------------ events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(
                    (max(VIEW_W, event.w), max(VIEW_H, event.h)),
                    pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if self.menu.open:
                    action = self.menu.handle_key(event.key)
                    if action == QUIT:
                        self.running = False
                    elif action == RESUME:
                        self.inp.release_all()
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.menu.toggle()
                    self.inp.release_all()
                    continue
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    continue
                self.inp.key_down(event.key)

            elif event.type == pygame.KEYUP:
                self.inp.key_up(event.key)

            elif event.type == FOCUS_LOST:
                self.inp.release_all()

    # ------------------------------------------------------------ update
    def step(self, dt):
        if self.inp.pressed("dbg_boxes"):
            self.show_boxes = not self.show_boxes
        if self.inp.pressed("dbg_noclip"):
            self.player.noclip = not self.player.noclip
        if self.inp.pressed("respawn"):
            self.reset()
            return
        if not self.player.dead:
            if self.inp.pressed("kill_self"):
                self.player.die()
            elif self.inp.pressed("hurt_self"):
                self.player.hurt(-self.player.face)

        self.player.update(dt, self.inp)

        for slime in list(self.world.slimes):
            slime.update(dt, self.world.tiles, self.player)
            if slime.remove:
                self.world.slimes.remove(slime)

        self.fx.update(dt)
        self.camera.update(dt, self.player, self.fx.shake_amount)

        if self.player.dead and self.player.respawn_t <= 0:
            self.reset()

    # ------------------------------------------------------------ draw
    def draw(self):
        canvas = self.canvas
        self.renderer.draw_background(canvas, self.camera)
        ox, oy = self.camera.offset()

        self.renderer.draw_tiles(canvas, ox, oy)
        for slime in self.world.slimes:
            self.renderer.draw_slime(canvas, slime, ox, oy)
        self.renderer.draw_player(canvas, self.player, ox, oy)
        self.renderer.draw_fx(canvas, self.fx, ox, oy)

        if self.show_boxes:
            draw_debug(canvas, self.player, self.world.slimes,
                       self.small, ox, oy, self.player.noclip)
        draw_hud(canvas, self.player, self.font)

        if self.menu.open:
            self.menu.draw(canvas, self.font, self.small)

        self._present()

    def _present(self):
        """Scale the low-res canvas up, letterboxed, preserving aspect."""
        win_w, win_h = self.window.get_size()
        scale = min(win_w / VIEW_W, win_h / VIEW_H)
        w, h = int(VIEW_W * scale), int(VIEW_H * scale)
        scaled = pygame.transform.scale(self.canvas, (w, h))
        self.window.fill((0, 0, 0))
        self.window.blit(scaled, ((win_w - w) // 2, (win_h - h) // 2))
        pygame.display.flip()

    # ------------------------------------------------------------ loop
    def run(self):
        while self.running:
            frame_time = min(self.clock.tick(60) / 1000.0, MAX_FRAME_TIME)
            self.handle_events()

            if not self.menu.open:
                self.accumulator += frame_time
                guard = 0
                # fixed timestep: physics is identical on any monitor
                while self.accumulator >= FIXED_DT and guard < 8:
                    self.step(FIXED_DT)
                    self.inp.end_step()
                    self.accumulator -= FIXED_DT
                    guard += 1
            else:
                self.accumulator = 0.0

            self.draw()

        pygame.quit()


def main():
    Game().run()
