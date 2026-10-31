"""
generate_assets.py - Render the game's procedural artwork to PNG files.

    python generate_assets.py

Creates assets/background.png and assets/spacecraft.png (the game loads these
if they exist - replace them with your own art to re-skin the game), plus a
planet_<kind>.png preview for every planet type, handy for your report.
"""

import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
from pygame.math import Vector2

from config import ASSET_DIR, WIDTH, HEIGHT, WHITE, CYAN
from effects import build_background
from planet import render_planet, ATMOSPHERE_COLORS
from player import HULL


def main():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN if hasattr(pygame, "HIDDEN") else 0)
    os.makedirs(ASSET_DIR, exist_ok=True)

    pygame.image.save(build_background(), os.path.join(ASSET_DIR, "background.png"))

    ship = pygame.Surface((32, 34), pygame.SRCALPHA)
    centre = Vector2(16, 17)
    pts = [centre + p for p in HULL]
    pygame.draw.polygon(ship, (200, 210, 230), pts)
    pygame.draw.polygon(ship, WHITE, pts, 1)
    pygame.draw.circle(ship, CYAN, centre + Vector2(0, -5), 3)
    pygame.image.save(ship, os.path.join(ASSET_DIR, "spacecraft.png"))

    for kind in ATMOSPHERE_COLORS:
        pygame.image.save(render_planet(90, kind, 42), os.path.join(ASSET_DIR, f"planet_{kind}.png"))

    print(f"Assets written to {ASSET_DIR}")
    pygame.quit()


if __name__ == "__main__":
    main()
