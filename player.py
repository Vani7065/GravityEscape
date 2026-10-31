"""
player.py - The player's spacecraft.

The player never sets the ship's position or velocity directly. They only
control the engine (thrust on/off) and the direction the ship points.
The physics module turns that into motion.
"""

import random
from collections import deque

import pygame
from pygame.math import Vector2

from config import (SHIP_MASS, SHIP_RADIUS, THRUST_ACCEL, ROTATION_SPEED,
                    FUEL_BURN_RATE, WHITE, CYAN)

# Hull outline with the nose pointing up (local coordinates)
HULL = [Vector2(0, -15), Vector2(5, -4), Vector2(10, 10), Vector2(4, 7),
        Vector2(0, 9), Vector2(-4, 7), Vector2(-10, 10), Vector2(-5, -4)]


class Spacecraft:
    def __init__(self, pos, vel, angle, fuel, image=None):
        self.pos = Vector2(pos)
        self.vel = Vector2(vel)
        self.angle = float(angle)       # degrees, 0 = up, 90 = right
        self.fuel = float(fuel)         # percent of a full tank
        self.max_fuel = float(fuel)
        self.mass = SHIP_MASS
        self.radius = SHIP_RADIUS
        self.thrusting = False
        self.alive = True
        self.image = image
        self.trail = deque(maxlen=500)
        self._trail_timer = 0.0

    # ------------------------------------------------------------ controls
    @property
    def heading(self):
        """Unit vector the nose points along."""
        return Vector2(0, -1).rotate(self.angle)

    def handle_input(self, keys, dt):
        """Read the keyboard: rotate and decide whether the engine fires."""
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.angle -= ROTATION_SPEED * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.angle += ROTATION_SPEED * dt
        self.angle %= 360
        wants_thrust = keys[pygame.K_w] or keys[pygame.K_UP]
        self.thrusting = bool(wants_thrust and self.fuel > 0 and self.alive)

    def thrust_acceleration(self):
        """Engine acceleration vector (zero when the engine is off)."""
        if self.thrusting:
            return self.heading * THRUST_ACCEL
        return Vector2()

    def burn_fuel(self, dt):
        if self.thrusting:
            self.fuel = max(0.0, self.fuel - FUEL_BURN_RATE * dt)
            if self.fuel == 0:
                self.thrusting = False

    def record_trail(self, dt):
        self._trail_timer += dt
        if self._trail_timer >= 0.03:
            self._trail_timer = 0.0
            self.trail.append(Vector2(self.pos))

    # ------------------------------------------------------------- drawing
    def draw_trail(self, screen):
        n = len(self.trail)
        if n < 2:
            return
        pts = list(self.trail)
        for i in range(1, n):
            t = i / n
            col = (int(20 + 40 * t), int(40 + 110 * t), int(70 + 150 * t))
            pygame.draw.line(screen, col, pts[i - 1], pts[i], 2 if t > 0.6 else 1)

    def draw(self, screen):
        if not self.alive:
            return
        heading = self.heading
        centre = self.pos

        # engine flame
        if self.thrusting:
            flick = random.uniform(0.75, 1.25)
            base_l = centre + Vector2(-4, 8).rotate(self.angle)
            base_r = centre + Vector2(4, 8).rotate(self.angle)
            tip = centre - heading * (22 * flick)
            inner_tip = centre - heading * (15 * flick)
            pygame.draw.polygon(screen, (255, 120, 40), [base_l, tip, base_r])
            pygame.draw.polygon(screen, (255, 230, 140),
                                [centre + Vector2(-2, 8).rotate(self.angle), inner_tip,
                                 centre + Vector2(2, 8).rotate(self.angle)])

        if self.image is not None:
            img = pygame.transform.rotozoom(self.image, -self.angle, 1.0)
            screen.blit(img, img.get_rect(center=(round(centre.x), round(centre.y))))
        else:
            points = [centre + p.rotate(self.angle) for p in HULL]
            pygame.draw.polygon(screen, (200, 210, 230), points)
            pygame.draw.polygon(screen, WHITE, points, 1)
            # cockpit window
            pygame.draw.circle(screen, CYAN, centre + Vector2(0, -5).rotate(self.angle), 3)
