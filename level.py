"""
level.py - Level loading and the escape zone.

Levels are plain JSON files in /levels, so new levels can be designed
without touching the code. Each file lists the planets, the ship's starting
state, the fuel and time available, and where the escape zone is.
"""

import json
import math
import os

import pygame
from pygame.math import Vector2

from config import LEVEL_DIR, LEVEL_FILES, GREEN
from planet import Planet


class EscapeZone:
    def __init__(self, pos, radius):
        self.pos = Vector2(pos)
        self.radius = radius
        self._glow = self._make_glow()

    def contains(self, point):
        return (point - self.pos).length_squared() < self.radius * self.radius

    def _make_glow(self):
        size = self.radius * 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for i in range(16):
            t = i / 16
            r = int(self.radius * 2 * (1 - t))
            pygame.draw.circle(surf, (90, 255, 160, int(3 + 9 * t)), (size // 2, size // 2), r)
        return surf

    def draw(self, screen, t, font=None):
        cx, cy = self.pos
        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        screen.blit(self._glow, self._glow.get_rect(center=(round(cx), round(cy))))
        # rotating dashed ring
        r = self.radius
        for i in range(12):
            a0 = t * 0.8 + i * math.tau / 12
            rect = pygame.Rect(0, 0, r * 2, r * 2)
            rect.center = (round(cx), round(cy))
            pygame.draw.arc(screen, GREEN, rect, a0, a0 + 0.32, 2)
        inner = int(r * (0.45 + 0.15 * pulse))
        pygame.draw.circle(screen, (60, 200, 130), (round(cx), round(cy)), inner, 1)
        pygame.draw.circle(screen, (180, 255, 210), (round(cx), round(cy)), 3)
        if font:
            label = font.render("ESCAPE ZONE", True, GREEN)
            screen.blit(label, label.get_rect(midbottom=(cx, cy - r - 6)))


class Level:
    def __init__(self, data, number):
        self.number = number
        self.name = data["name"]
        self.subtitle = data.get("subtitle", "")
        self.hint = data.get("hint", "")
        self.fuel = float(data.get("fuel", 100))
        self.time_limit = float(data.get("time_limit", 60))
        start = data["start"]
        self.start_pos = Vector2(start["pos"])
        self.start_vel = Vector2(start.get("vel", [0, 0]))
        self.start_angle = float(start.get("angle", 0))
        self.planets = [Planet.from_dict(p) for p in data["planets"]]
        z = data["escape_zone"]
        self.zone = EscapeZone(z["pos"], z.get("radius", 50))

    @classmethod
    def load(cls, index):
        with open(level_path(index), "r", encoding="utf-8") as f:
            return cls(json.load(f), index + 1)


def level_path(index):
    return os.path.join(LEVEL_DIR, LEVEL_FILES[index])


def read_level_info(index):
    """Name and subtitle only (fast - used by the menu, no planet rendering)."""
    with open(level_path(index), "r", encoding="utf-8") as f:
        data = json.load(f)
    return {"name": data["name"], "subtitle": data.get("subtitle", ""),
            "planets": len(data["planets"]), "fuel": data.get("fuel", 100),
            "time_limit": data.get("time_limit", 60)}


def level_count():
    return len(LEVEL_FILES)
