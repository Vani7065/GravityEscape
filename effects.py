"""
effects.py - Visual-only effects: starfield background, engine exhaust and
explosions. Nothing here affects the physics.
"""

import math
import os
import random

import pygame
from pygame.math import Vector2

from config import WIDTH, HEIGHT, BG_COLOR, ASSET_DIR


def load_image(name, alpha=True):
    """Load assets/<name> if it exists, otherwise return None."""
    path = os.path.join(ASSET_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()
    except pygame.error:
        return None


def build_background(seed=7):
    """Deep-space backdrop: nebula clouds, a distant sun and static stars."""
    rng = random.Random(seed)
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill(BG_COLOR)

    # nebula clouds: many faint overlapping circles
    cloud = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for colour, cx, cy in [((70, 40, 120), 950, 520), ((30, 70, 130), 300, 200),
                           ((110, 40, 80), 1100, 150)]:
        for _ in range(60):
            r = rng.randint(60, 220)
            x = cx + rng.gauss(0, 160)
            y = cy + rng.gauss(0, 110)
            pygame.draw.circle(cloud, (*colour, 4), (int(x), int(y)), r)
    surf.blit(cloud, (0, 0))

    # distant sun (light source for the planet shading) in the top-left
    sun = pygame.Surface((420, 420), pygame.SRCALPHA)
    for i in range(30):
        t = i / 30
        pygame.draw.circle(sun, (255, 220, 160, int(2 + 6 * t)), (210, 210), int(210 * (1 - t)))
    pygame.draw.circle(sun, (255, 245, 220), (210, 210), 9)
    surf.blit(sun, (-210 - 25, -210 - 25))  # sun just off-screen, top-left

    for _ in range(420):
        x, y = rng.randrange(WIDTH), rng.randrange(HEIGHT)
        b = rng.randint(50, 170)
        surf.set_at((x, y), (b, b, min(255, b + 30)))
    return surf


class Starfield:
    """Static background plus a handful of twinkling bright stars."""

    def __init__(self, seed=7):
        image = load_image("background.png", alpha=False)
        if image is not None:
            self.background = pygame.transform.smoothscale(image, (WIDTH, HEIGHT))
        else:
            self.background = build_background(seed)
        rng = random.Random(seed + 1)
        self.twinklers = [(rng.randrange(WIDTH), rng.randrange(HEIGHT),
                           rng.uniform(0, math.tau), rng.uniform(1.0, 3.0))
                          for _ in range(70)]

    def draw(self, screen, t):
        screen.blit(self.background, (0, 0))
        for x, y, phase, speed in self.twinklers:
            b = int(150 + 105 * (0.5 + 0.5 * math.sin(t * speed + phase)))
            screen.set_at((x, y), (b, b, 255))
            if b > 235:
                screen.set_at((x + 1, y), (b // 2, b // 2, 160))
                screen.set_at((x - 1, y), (b // 2, b // 2, 160))
                screen.set_at((x, y + 1), (b // 2, b // 2, 160))
                screen.set_at((x, y - 1), (b // 2, b // 2, 160))


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "color", "size")

    def __init__(self, pos, vel, life, color, size):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def clear(self):
        self.particles.clear()

    def exhaust(self, ship):
        """Engine smoke shooting out of the back of the ship."""
        back = ship.pos - ship.heading * 10
        for _ in range(3):
            direction = (-ship.heading).rotate(random.uniform(-14, 14))
            vel = ship.vel + direction * random.uniform(90, 170)
            col = random.choice([(255, 170, 70), (255, 220, 120), (255, 120, 50)])
            self.particles.append(Particle(back, vel, random.uniform(0.25, 0.5), col,
                                           random.uniform(1.5, 3.0)))

    def explosion(self, pos, vel=Vector2()):
        for _ in range(110):
            direction = Vector2(1, 0).rotate(random.uniform(0, 360))
            speed = random.uniform(20, 260)
            col = random.choice([(255, 240, 180), (255, 170, 60), (255, 90, 40), (200, 200, 210)])
            self.particles.append(Particle(pos, vel * 0.3 + direction * speed,
                                           random.uniform(0.5, 1.6), col, random.uniform(1.5, 4.0)))

    def celebrate(self, pos):
        for _ in range(80):
            direction = Vector2(1, 0).rotate(random.uniform(0, 360))
            col = random.choice([(90, 255, 160), (180, 255, 220), (90, 220, 255)])
            self.particles.append(Particle(pos, direction * random.uniform(40, 200),
                                           random.uniform(0.6, 1.4), col, random.uniform(1.5, 3.0)))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life > 0:
                p.pos += p.vel * dt
                p.vel *= 0.985
                alive.append(p)
        self.particles = alive

    def draw(self, screen):
        for p in self.particles:
            t = p.life / p.max_life
            col = (int(p.color[0] * t), int(p.color[1] * t), int(p.color[2] * t))
            pygame.draw.circle(screen, col, (int(p.pos.x), int(p.pos.y)), max(1, int(p.size * t + 0.5)))
