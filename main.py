"""
Gravity Escape - a Newtonian spaceflight puzzle game.

Run with:   python main.py

Game loop (every frame):
    read input -> several fixed physics steps -> effects -> render

Each physics step:
    planet positions -> gravitational forces -> acceleration
    -> velocity -> position -> collision detection
"""

import json
import os
import sys

import pygame

from config import (WIDTH, HEIGHT, FPS, TITLE, PHYSICS_DT, MAX_FRAME_TIME, SAVE_FILE)
import collision
import physics
import ui
from effects import Starfield, ParticleSystem, load_image
from level import Level, read_level_info, level_count
from player import Spacecraft

MENU, PLAYING, PAUSED, RESULT = "menu", "playing", "paused", "result"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = ui.Fonts()
        self.starfield = Starfield()
        self.particles = ParticleSystem()
        self.ship_image = load_image("spacecraft.png")

        self.level_infos = [read_level_info(i) for i in range(level_count())]
        self.highscores = self._load_scores()
        self.state = MENU
        self.selected = 0
        self.real_time = 0.0

        self.show_prediction = True
        self.show_vectors = False

        self.level = None
        self.ship = None
        self.sim_time = 0.0        # physics clock (drives moving planets)
        self.time_left = 0.0
        self.accumulator = 0.0
        self.prediction = ([], None)
        self.gravity_now = pygame.math.Vector2()
        self.won = False
        self.fail_reason = ""
        self.result_stats = []
        self.new_best = False

    # ---------------------------------------------------------- persistence
    def _load_scores(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_scores(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.highscores, f, indent=2)
        except OSError:
            pass

    # ---------------------------------------------------------- level flow
    def start_level(self, index):
        self.selected = index
        ui.draw_loading(self.screen, self.fonts, self.level_infos[index]["name"])
        pygame.display.flip()
        self.level = Level.load(index)
        lv = self.level
        self.ship = Spacecraft(lv.start_pos, lv.start_vel, lv.start_angle, lv.fuel, self.ship_image)
        self.sim_time = 0.0
        self.time_left = lv.time_limit
        self.accumulator = 0.0
        self.particles.clear()
        self.won = False
        self.state = PLAYING
        self.clock.tick()  # don't count loading time as a frame

    def finish(self, won, reason=""):
        self.won = won
        self.fail_reason = reason
        self.state = RESULT
        lv, ship = self.level, self.ship
        if won:
            score = int(1000 + ship.fuel * 20 + self.time_left * 10)
            key = str(lv.number)
            self.new_best = score > self.highscores.get(key, 0)
            if self.new_best:
                self.highscores[key] = score
                self._save_scores()
            self.result_stats = [("Fuel left", f"{ship.fuel:.0f}%"),
                                 ("Time left", ui.format_time(self.time_left)),
                                 ("Score", f"{score:,}")]
            self.particles.celebrate(ship.pos)
        else:
            self.new_best = False
            self.result_stats = [("Fuel left", f"{ship.fuel:.0f}%"),
                                 ("Time survived", ui.format_time(self.sim_time)),
                                 ("Level", f"{lv.number} - {lv.name}")]

    # ------------------------------------------------------------- physics
    def physics_step(self, dt):
        """One fixed time step of the simulation."""
        ship, planets = self.ship, self.level.planets

        # 1-2. planet positions & gravitational forces -> acceleration
        gravity = physics.gravity_acceleration(ship.pos, planets, self.sim_time)
        acc = gravity + ship.thrust_acceleration()
        # 3-4. update velocity, then position
        ship.pos, ship.vel = physics.integrate(ship.pos, ship.vel, acc, dt)
        ship.burn_fuel(dt)
        self.sim_time += dt
        self.time_left -= dt
        ship.record_trail(dt)

        # 5. collision detection
        hit = collision.check_planet_collision(ship.pos, ship.radius, planets, self.sim_time)
        if hit:
            ship.alive = False
            self.particles.explosion(ship.pos, ship.vel)
            self.finish(False, f"CRASHED INTO {hit.name.upper()}")
        elif collision.reached_zone(ship.pos, self.level.zone):
            self.finish(True)
        elif collision.out_of_bounds(ship.pos):
            self.finish(False, "LOST IN DEEP SPACE")
        elif self.time_left <= 0:
            self.time_left = 0
            self.finish(False, "OUT OF TIME")

    def update(self, frame_dt):
        self.real_time += frame_dt
        self.particles.update(frame_dt)
        if self.state != PLAYING:
            return

        self.ship.handle_input(pygame.key.get_pressed(), frame_dt)
        if self.ship.thrusting:
            self.particles.exhaust(self.ship)

        self.accumulator += frame_dt
        while self.accumulator >= PHYSICS_DT and self.state == PLAYING:
            self.physics_step(PHYSICS_DT)
            self.accumulator -= PHYSICS_DT

        if self.state == PLAYING:
            self.gravity_now = physics.gravity_acceleration(self.ship.pos, self.level.planets,
                                                            self.sim_time)
            if self.show_prediction:
                self.prediction = physics.predict_trajectory(
                    self.ship.pos, self.ship.vel, self.level.planets, self.sim_time, self.level.zone)

    # -------------------------------------------------------------- input
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True
        key = event.key

        if self.state == MENU:
            if key == pygame.K_ESCAPE:
                return False
            if key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % level_count()
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % level_count()
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = key - pygame.K_1
                if idx < level_count():
                    self.start_level(idx)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_level(self.selected)
            return True

        if key == pygame.K_t:
            self.show_prediction = not self.show_prediction
        elif key == pygame.K_v:
            self.show_vectors = not self.show_vectors
        elif key == pygame.K_r:
            self.start_level(self.level.number - 1)
        elif key == pygame.K_ESCAPE:
            self.state = MENU
        elif self.state == PLAYING and key in (pygame.K_SPACE, pygame.K_p):
            self.state = PAUSED
        elif self.state == PAUSED and key in (pygame.K_SPACE, pygame.K_p):
            self.state = PLAYING
            self.clock.tick()
        elif self.state == RESULT and key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_n):
            nxt = self.level.number
            if self.won and nxt < level_count():
                self.start_level(nxt)
            elif self.won:
                self.state = MENU
        return True

    # -------------------------------------------------------------- drawing
    def draw_world(self):
        lv, ship = self.level, self.ship
        for planet in lv.planets:
            planet.draw(self.screen, self.sim_time, self.fonts.tiny)
        lv.zone.draw(self.screen, self.real_time, self.fonts.tiny)
        ship.draw_trail(self.screen)
        if self.show_prediction and self.state in (PLAYING, PAUSED) and ship.alive:
            ui.draw_prediction(self.screen, *self.prediction)
        self.particles.draw(self.screen)
        ship.draw(self.screen)
        if self.show_vectors and ship.alive:
            ui.draw_vectors(self.screen, self.fonts, ship, self.gravity_now)
        if ship.alive:
            ui.draw_offscreen_marker(self.screen, self.fonts, ship)

        altitude = min((ship.pos - p.position_at(self.sim_time)).length() - p.radius
                       for p in lv.planets)
        ui.draw_hud(self.screen, self.fonts, lv, ship, self.time_left, altitude,
                    self.show_prediction, self.prediction[1])
        ui.draw_hint(self.screen, self.fonts, lv.hint, self.sim_time)
        ui.draw_controls_strip(self.screen, self.fonts)

    def draw(self):
        self.starfield.draw(self.screen, self.real_time)
        if self.state == MENU:
            self.particles.draw(self.screen)
            ui.draw_menu(self.screen, self.fonts, self.level_infos, self.selected,
                         self.highscores, self.real_time)
        else:
            self.draw_world()
            if self.state == PAUSED:
                ui.draw_pause(self.screen, self.fonts)
            elif self.state == RESULT:
                ui.draw_result(self.screen, self.fonts, self.won, self.fail_reason,
                               self.result_stats, self.level.number < level_count(),
                               self.new_best)
        pygame.display.flip()

    # ---------------------------------------------------------------- loop
    def run(self):
        running = True
        while running:
            frame_dt = min(self.clock.tick(FPS) / 1000.0, MAX_FRAME_TIME)
            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False
                    break
            self.update(frame_dt)
            self.draw()
        pygame.quit()


def main():
    # make relative paths work no matter where VS Code launches from
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    Game().run()
    sys.exit(0)


if __name__ == "__main__":
    main()
