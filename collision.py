"""
collision.py - Collision and boundary checks.

Everything is treated as a circle, so a collision is simply:
    distance(centre_a, centre_b) < radius_a + radius_b
Squared distances are compared to avoid a square root every check.
"""

from config import WIDTH, HEIGHT, OUT_OF_BOUNDS_MARGIN


def circles_overlap(pos_a, radius_a, pos_b, radius_b):
    limit = radius_a + radius_b
    return (pos_a - pos_b).length_squared() < limit * limit


def check_planet_collision(ship_pos, ship_radius, planets, t):
    """Return the planet the ship hit at time t, or None."""
    for planet in planets:
        if circles_overlap(ship_pos, ship_radius, planet.position_at(t), planet.radius):
            return planet
    return None


def reached_zone(ship_pos, zone):
    return zone.contains(ship_pos)


def out_of_bounds(ship_pos, margin=OUT_OF_BOUNDS_MARGIN):
    return (ship_pos.x < -margin or ship_pos.x > WIDTH + margin or
            ship_pos.y < -margin or ship_pos.y > HEIGHT + margin)


def off_screen(ship_pos, pad=0):
    return (ship_pos.x < -pad or ship_pos.x > WIDTH + pad or
            ship_pos.y < -pad or ship_pos.y > HEIGHT + pad)
