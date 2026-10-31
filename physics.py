"""
physics.py - Newtonian gravity and numerical integration.

Every physics step does exactly what the design describes:

    Planet positions
          |
    Gravitational force from each planet      F = G * M * m / r^2
          |
    Spacecraft acceleration                   a = F / m   (summed over planets)
          |
    Update velocity                           v_new = v_old + a * dt
          |
    Update position                           x_new = x_old + v_new * dt

Using the *new* velocity to update the position is called semi-implicit
(symplectic) Euler integration. It costs the same as plain Euler but keeps
orbits stable instead of slowly spiralling outward.
"""

from pygame.math import Vector2

from config import G, SHIP_MASS, SHIP_RADIUS, PREDICT_DT, PREDICT_STEPS
import collision


def gravitational_force(ship_pos, ship_mass, planet_pos, planet_mass, min_distance):
    """Force vector on the ship from one planet: F = G * M * m / r^2.

    `min_distance` (the planet's radius) stops the force from blowing up
    to infinity if r ever gets close to zero.
    """
    offset = planet_pos - ship_pos            # vector pointing at the planet
    r = offset.length()
    if r == 0:
        return Vector2()
    r = max(r, min_distance)
    magnitude = G * planet_mass * ship_mass / (r * r)
    return offset / offset.length() * magnitude


def gravity_acceleration(pos, planets, t, ship_mass=SHIP_MASS):
    """Total gravitational acceleration at `pos` at time `t`.

    Each planet contributes its own pull; the vectors simply add up
    (superposition). a = F / m for each one.
    """
    total = Vector2()
    for planet in planets:
        force = gravitational_force(pos, ship_mass, planet.position_at(t),
                                    planet.mass, planet.radius)
        total += force / ship_mass
    return total


def integrate(pos, vel, acc, dt):
    """One semi-implicit Euler step. Returns (new_pos, new_vel)."""
    new_vel = vel + acc * dt                  # v_new = v_old + a * dt
    new_pos = pos + new_vel * dt              # x_new = x_old + v * dt
    return new_pos, new_vel


def predict_trajectory(pos, vel, planets, t0, zone=None,
                       steps=PREDICT_STEPS, dt=PREDICT_DT):
    """Predict where the ship will coast if the engine stays off.

    It repeatedly applies the *same* gravity + integration functions used by
    the real simulation to future time steps.

    Returns (points, outcome) where outcome is None, "crash" or "escape".
    """
    pos = Vector2(pos)
    vel = Vector2(vel)
    points = []
    t = t0
    for _ in range(steps):
        acc = gravity_acceleration(pos, planets, t)
        pos, vel = integrate(pos, vel, acc, dt)
        t += dt
        points.append(pos)
        if collision.check_planet_collision(pos, SHIP_RADIUS, planets, t):
            return points, "crash"
        if zone is not None and zone.contains(pos):
            return points, "escape"
    return points, None


def circular_orbit_speed(planet_mass, radius):
    """Speed needed for a circular orbit: v = sqrt(G*M / r)."""
    return (G * planet_mass / radius) ** 0.5


def escape_speed(planet_mass, radius):
    """Speed needed to escape a planet from distance r: v = sqrt(2*G*M / r)."""
    return (2 * G * planet_mass / radius) ** 0.5
