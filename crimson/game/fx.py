"""Dust, screen shake and the impact burst.

This is the object the pygame-free core talks to when something should be
felt rather than simulated.
"""
import random


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "age", "color")

    def __init__(self, x, y, vx, vy, life, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life, self.age = life, 0.0
        self.color = color


class Burst:
    """One playthrough of the munch sprite sheet at a fixed spot."""
    __slots__ = ("x", "y", "t", "fps", "frames")

    def __init__(self, x, y, frames=5, fps=22.0):
        self.x, self.y = x, y
        self.t = 0.0
        self.fps = fps
        self.frames = frames

    @property
    def index(self):
        return int(self.t * self.fps)

    @property
    def finished(self):
        return self.index >= self.frames


DUST = (118, 104, 92)
BLOOD = (60, 130, 200)      # slimes splash blue, matching the sprite


class FX:
    def __init__(self):
        self.particles = []
        self.bursts = []
        self.shake_amount = 0.0

    # ------------------------------------------------- called by the core
    def dust(self, x, y, n=1, direction=0, color=None):
        for _ in range(n):
            self.particles.append(Particle(
                x, y - 1,
                direction * random.uniform(20, 70) + random.uniform(-20, 20),
                -random.uniform(0, 55),
                random.uniform(0.28, 0.62),
                color or DUST,
            ))

    def shake(self, amount):
        self.shake_amount = max(self.shake_amount, amount)

    def munch(self, x, y):
        self.bursts.append(Burst(x, y))
        self.dust(x, y, 6, 0, BLOOD)

    # ------------------------------------------------------------ update
    def update(self, dt):
        for p in self.particles:
            p.age += dt
            p.vy += 210 * dt
            p.vx *= 0.92
            p.x += p.vx * dt
            p.y += p.vy * dt
        self.particles = [p for p in self.particles if p.age < p.life]

        for b in self.bursts:
            b.t += dt
        self.bursts = [b for b in self.bursts if not b.finished]

        self.shake_amount = max(0.0, self.shake_amount - dt * 22)

    def clear(self):
        self.particles.clear()
        self.bursts.clear()
        self.shake_amount = 0.0
