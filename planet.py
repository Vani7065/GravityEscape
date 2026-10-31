"""
planet.py - Planets: their gravity data, motion and procedural artwork.

A planet is a point mass (for gravity) and a circle (for collisions).
Planets can be fixed, or move on a circular orbit (e.g. a moon). Because the
position is a function of time, `position_at(t)` lets the trajectory
predictor ask where a moving moon will be in the future.

The planet artwork is generated pixel-by-pixel when a level loads: each pixel
gets a 3D surface normal on a sphere, a colour from a simple "sine noise"
pattern, and Lambert lighting from a distant sun in the upper-left.
"""

import math
import random

import pygame
from pygame.math import Vector2

# Direction *towards* the sun (x right, y down, z towards the viewer)
_LIGHT = (-0.55, -0.45, 0.70)
_l = math.sqrt(sum(c * c for c in _LIGHT))
LIGHT = tuple(c / _l for c in _LIGHT)

ATMOSPHERE_COLORS = {
    "earth": (90, 160, 255),
    "mars": (255, 140, 90),
    "moon": (170, 170, 190),
    "gas": (255, 200, 140),
    "ice": (150, 230, 255),
    "lava": (255, 110, 40),
    "toxic": (160, 255, 120),
}

_render_cache = {}


def _lerp(a, b, t):
    return a + (b - a) * t


def _mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def _random_unit(rng):
    while True:
        v = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
        if 0.1 < n <= 1:
            return (v[0] / n, v[1] / n, v[2] / n)


def render_planet(radius, kind, seed):
    """Draw a lit, textured sphere onto a transparent Surface (cached)."""
    key = (radius, kind, seed)
    if key in _render_cache:
        return _render_cache[key]

    rng = random.Random(seed)
    # A few random sine waves over the sphere make a cheap, seamless noise.
    waves = []
    for i in range(7):
        waves.append((_random_unit(rng), rng.uniform(2.0, 7.0) * (1 + i * 0.35),
                      rng.uniform(0, math.tau), 1.0 / (1 + i * 0.6)))
    amp_total = sum(w[3] for w in waves)
    craters = [(_random_unit(rng), rng.uniform(0.08, 0.28)) for _ in range(16)]

    size = radius * 2 + 2
    centre = size / 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    atmosphere = ATMOSPHERE_COLORS.get(kind, (200, 200, 255))
    lx, ly, lz = LIGHT

    surf.lock()
    for py in range(size):
        y = (py + 0.5 - centre) / radius
        for px in range(size):
            x = (px + 0.5 - centre) / radius
            d2 = x * x + y * y
            if d2 > 1.0:
                continue
            z = math.sqrt(1.0 - d2)

            # noise in [-1, 1]
            n = 0.0
            for (dx, dy, dz), freq, phase, amp in waves:
                n += amp * math.sin(freq * (dx * x + dy * y + dz * z) + phase)
            n /= amp_total

            emissive = None
            if kind == "earth":
                if abs(y) > 0.86 + n * 0.08:
                    col = (235, 240, 250)
                elif n > 0.12:
                    col = _mix((70, 145, 70), (150, 135, 85), (n - 0.12) * 3)
                else:
                    col = _mix((20, 55, 140), (40, 105, 190), (n + 1) / 1.12)
            elif kind == "mars":
                col = _mix((205, 100, 55), (125, 55, 35), (n + 0.2) * 1.4)
            elif kind == "moon":
                col = _mix((175, 175, 180), (120, 120, 128), (n + 1) / 2)
            elif kind == "gas":
                band = math.sin(y * 9.0 + n * 2.2)
                col = _mix((225, 185, 130), (165, 105, 65), (band + 1) / 2)
                # a big storm spot
                sx, sy = x - 0.35, y - 0.25
                if sx * sx / 0.05 + sy * sy / 0.018 < 1:
                    col = _mix(col, (200, 80, 60), 0.75)
            elif kind == "ice":
                col = (190, 225, 245)
                if abs(n) < 0.05:
                    col = (100, 160, 210)
            elif kind == "lava":
                col = _mix((55, 30, 30), (90, 50, 40), (n + 1) / 2)
                if abs(n) < 0.06:
                    emissive = _mix((255, 220, 90), (255, 90, 20), abs(n) / 0.06)
            elif kind == "toxic":
                band = math.sin(y * 6.0 + n * 3.0)
                col = _mix((120, 180, 70), (90, 70, 140), (band + 1) / 2)
            else:
                col = (160, 160, 200)

            # craters for rocky worlds
            if kind in ("moon", "mars"):
                for (cx, cy, cz), cr in craters:
                    dot = cx * x + cy * y + cz * z
                    if dot > math.cos(cr):
                        edge = (dot - math.cos(cr)) / (1 - math.cos(cr))
                        col = _mix(col, (col[0] * 0.65, col[1] * 0.65, col[2] * 0.65),
                                   1 - edge * 0.6)
                        break

            # Lambert lighting + ambient
            diffuse = max(0.0, x * lx + y * ly + z * lz)
            shade = 0.13 + 0.87 * diffuse
            r, g, b = col[0] * shade, col[1] * shade, col[2] * shade
            if emissive is not None:
                r, g, b = emissive
            # atmosphere rim
            rim = (1.0 - z) ** 3 * 0.55 * (0.35 + diffuse)
            r = _lerp(r, atmosphere[0], rim)
            g = _lerp(g, atmosphere[1], rim)
            b = _lerp(b, atmosphere[2], rim)

            # anti-aliased edge
            edge_alpha = max(0.0, min(1.0, (1.0 - math.sqrt(d2)) * radius * 1.3))
            surf.set_at((px, py), (int(min(255, r)), int(min(255, g)),
                                   int(min(255, b)), int(255 * edge_alpha)))
    surf.unlock()

    _render_cache[key] = surf
    return surf


def render_glow(radius, color, strength=0.35):
    """Soft halo drawn behind a planet."""
    glow = int(radius * strength) + 6
    size = (radius + glow) * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 14
    for i in range(steps):
        t = i / steps
        r = int(radius + glow * (1 - t))
        alpha = int(4 + 10 * t)
        pygame.draw.circle(surf, (*color, alpha), (size // 2, size // 2), r)
    return surf


class Planet:
    def __init__(self, name, pos, mass, radius, kind="earth", seed=None, orbit=None):
        self.name = name
        self.base_pos = Vector2(pos)
        self.mass = float(mass)
        self.radius = int(radius)
        self.kind = kind
        # deterministic seed from the name (str hash() changes every run)
        self.seed = seed if seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(name))
        # orbit = {"center": [x, y], "radius": r, "period": seconds, "phase": degrees}
        self.orbit = orbit
        self.image = render_planet(self.radius, kind, self.seed)
        self.glow = render_glow(self.radius, ATMOSPHERE_COLORS.get(kind, (200, 200, 255)))

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d.get("pos", [0, 0]), d["mass"], d["radius"],
                   d.get("kind", "earth"), d.get("seed"), d.get("orbit"))

    def position_at(self, t):
        """Planet centre at time t (moving planets follow a circle)."""
        if not self.orbit:
            return self.base_pos
        centre = Vector2(self.orbit["center"])
        r = self.orbit["radius"]
        angle = math.radians(self.orbit.get("phase", 0)) + math.tau * t / self.orbit["period"]
        return centre + Vector2(math.cos(angle), math.sin(angle)) * r

    def draw(self, screen, t, font=None):
        pos = self.position_at(t)
        if self.orbit:
            c = Vector2(self.orbit["center"])
            r = self.orbit["radius"]
            for i in range(0, 360, 6):
                a = math.radians(i)
                pygame.draw.circle(screen, (45, 55, 80),
                                   (int(c.x + math.cos(a) * r), int(c.y + math.sin(a) * r)), 1)
        screen.blit(self.glow, self.glow.get_rect(center=(round(pos.x), round(pos.y))))
        screen.blit(self.image, self.image.get_rect(center=(round(pos.x), round(pos.y))))
        if font:
            label = font.render(self.name.upper(), True, (120, 135, 165))
            screen.blit(label, label.get_rect(midtop=(pos.x, pos.y + self.radius + 8)))
