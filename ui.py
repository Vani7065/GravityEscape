"""
ui.py - Everything drawn on top of the game world: HUD, menus, overlays,
the trajectory prediction line and the physics vector arrows.
"""

import math

import pygame
from pygame.math import Vector2

from config import (WIDTH, HEIGHT, WHITE, GREY, DIM, CYAN, GREEN, YELLOW, ORANGE,
                    RED, PANEL, KM_PER_PIXEL, KMS_PER_PIXEL_PER_S, BG_COLOR)
import collision

MONO = "consolas,dejavusansmono,menlo,couriernew,monospace"
DISPLAY = "verdana,dejavusans,arial,helvetica"


class Fonts:
    def __init__(self):
        self.tiny = pygame.font.SysFont(MONO, 13)
        self.small = pygame.font.SysFont(MONO, 15)
        self.hud = pygame.font.SysFont(MONO, 17, bold=True)
        self.medium = pygame.font.SysFont(DISPLAY, 22, bold=True)
        self.large = pygame.font.SysFont(DISPLAY, 44, bold=True)
        self.title = pygame.font.SysFont(DISPLAY, 76, bold=True)


def text(screen, font, msg, color, pos, anchor="topleft"):
    surf = font.render(msg, True, color)
    rect = surf.get_rect(**{anchor: pos})
    screen.blit(surf, rect)
    return rect


def panel(screen, rect, alpha=190, border=(50, 70, 110)):
    surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surf, (*PANEL, alpha), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*border, 255), surf.get_rect(), 1, border_radius=10)
    screen.blit(surf, rect.topleft)


def _dim_overlay(alpha=160):
    s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    return s


def _blend(color, t):
    """Fade a colour towards the background (t=1 full colour, t=0 background)."""
    return tuple(int(BG_COLOR[i] + (color[i] - BG_COLOR[i]) * t) for i in range(3))


def format_time(seconds):
    seconds = max(0, int(math.ceil(seconds)))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


# --------------------------------------------------------------------- HUD
def fuel_color(pct):
    if pct > 50:
        return GREEN
    if pct > 20:
        return YELLOW
    return RED


def draw_hud(screen, fonts, level, ship, time_left, altitude_px, show_prediction, outcome):
    rect = pygame.Rect(16, 16, 300, 168)
    panel(screen, rect)
    x, y = rect.x + 16, rect.y + 12
    text(screen, fonts.hud, f"LEVEL {level.number}", CYAN, (x, y))
    text(screen, fonts.small, level.name.upper(), GREY, (x + 90, y + 2))
    y += 30

    # fuel bar
    pct = ship.fuel
    text(screen, fonts.hud, "FUEL", WHITE, (x, y))
    bar = pygame.Rect(x + 90, y + 3, 130, 14)
    pygame.draw.rect(screen, (30, 40, 60), bar, border_radius=4)
    fill = bar.copy()
    fill.width = int(bar.width * pct / 100)
    if fill.width > 0:
        pygame.draw.rect(screen, fuel_color(pct), fill, border_radius=4)
    pygame.draw.rect(screen, (70, 90, 130), bar, 1, border_radius=4)
    text(screen, fonts.small, f"{pct:3.0f}%", WHITE, (bar.right + 8, y + 1))
    y += 26

    speed_kms = ship.vel.length() * KMS_PER_PIXEL_PER_S
    text(screen, fonts.hud, "SPEED", WHITE, (x, y))
    text(screen, fonts.hud, f"{speed_kms:5.1f} km/s", CYAN, (x + 90, y))
    y += 26
    alt_km = max(0.0, altitude_px) * KM_PER_PIXEL
    text(screen, fonts.hud, "ALTITUDE", WHITE, (x, y))
    text(screen, fonts.hud, f"{alt_km:,.0f} km", CYAN, (x + 90, y))
    y += 26
    tcol = RED if time_left < 10 else WHITE
    text(screen, fonts.hud, "TIME", WHITE, (x, y))
    text(screen, fonts.hud, format_time(time_left), tcol, (x + 90, y))

    # prediction status (below the panel)
    if show_prediction:
        if outcome == "escape":
            msg, col = "COASTING PATH: REACHES ESCAPE ZONE", GREEN
        elif outcome == "crash":
            msg, col = "COASTING PATH: IMPACT!", RED
        else:
            msg, col = "COASTING PATH: DRIFTING", GREY
        text(screen, fonts.small, msg, col, (rect.x + 4, rect.bottom + 8))

    if ship.fuel <= 0:
        text(screen, fonts.medium, "FUEL EMPTY - ENGINES OFFLINE", RED, (WIDTH // 2, 24), "midtop")


def draw_controls_strip(screen, fonts):
    msg = "W/UP thrust   A/D rotate   SPACE pause   R restart   T trajectory   V vectors   ESC menu"
    text(screen, fonts.tiny, msg, DIM, (WIDTH // 2, HEIGHT - 10), "midbottom")


def draw_hint(screen, fonts, hint, elapsed):
    """Level hint that fades out after a few seconds."""
    if not hint or elapsed > 9:
        return
    alpha = 1.0 if elapsed < 7 else (9 - elapsed) / 2
    col = _blend((210, 225, 255), alpha)
    words = hint.split()
    lines, line = [], ""
    for w in words:
        if fonts.small.size(line + " " + w)[0] > 640:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    lines.append(line)
    y = HEIGHT - 40 - 20 * len(lines)
    for ln in lines:
        text(screen, fonts.small, ln, col, (WIDTH // 2, y), "midtop")
        y += 20


# ------------------------------------------------------ trajectory & vectors
def draw_prediction(screen, points, outcome):
    if not points:
        return
    colour = {"escape": GREEN, "crash": RED}.get(outcome, CYAN)
    n = len(points)
    for i in range(2, n, 4):
        t = 1.0 - 0.75 * (i / n)
        p = points[i]
        pygame.draw.circle(screen, _blend(colour, t), (int(p.x), int(p.y)), 2 if i < n * 0.4 else 1)
    end = points[-1]
    if outcome == "crash":
        for d in (-1, 1):
            pygame.draw.line(screen, RED, (end.x - 7, end.y - 7 * d), (end.x + 7, end.y + 7 * d), 2)
    elif outcome == "escape":
        pygame.draw.circle(screen, GREEN, (int(end.x), int(end.y)), 8, 2)


def _arrow(screen, start, vec, colour, label, font):
    if vec.length() < 2:
        return
    end = start + vec
    pygame.draw.line(screen, colour, start, end, 2)
    head = vec.normalize() * 9
    left = end - head.rotate(25)
    right = end - head.rotate(-25)
    pygame.draw.polygon(screen, colour, [end, left, right])
    text(screen, font, label, colour, (end.x + 6, end.y - 6))


def draw_vectors(screen, fonts, ship, gravity_acc):
    """Velocity (cyan) and gravitational acceleration (orange) arrows."""
    _arrow(screen, ship.pos, ship.vel * 0.45, CYAN, "v", fonts.small)
    _arrow(screen, ship.pos, gravity_acc * 0.35, ORANGE, "a (gravity)", fonts.small)
    if ship.thrusting:
        _arrow(screen, ship.pos, ship.thrust_acceleration() * 0.35, YELLOW, "a (thrust)", fonts.small)


def draw_offscreen_marker(screen, fonts, ship):
    """Arrow on the screen edge pointing at the ship when it flies off-screen."""
    if not collision.off_screen(ship.pos, pad=4):
        return
    cx = min(max(ship.pos.x, 24), WIDTH - 24)
    cy = min(max(ship.pos.y, 24), HEIGHT - 24)
    edge = Vector2(cx, cy)
    direction = ship.pos - edge
    if direction.length() == 0:
        return
    d = direction.normalize()
    tip = edge + d * 10
    pygame.draw.polygon(screen, YELLOW, [tip, edge - d * 8 + d.rotate(90) * 8,
                                         edge - d * 8 - d.rotate(90) * 8])
    dist = direction.length() * KM_PER_PIXEL
    text(screen, fonts.tiny, f"{dist:,.0f} km", YELLOW, (edge - d * 22), "center")


# ---------------------------------------------------------------- screens
def draw_menu(screen, fonts, infos, selected, highscores, t):
    shade = _dim_overlay(90)
    screen.blit(shade, (0, 0))
    bob = math.sin(t * 1.5) * 4
    text(screen, fonts.title, "GRAVITY ESCAPE", WHITE, (WIDTH // 2, 70 + bob), "midtop")
    story = ("Your spacecraft is trapped inside a planetary system. Use gravity and "
             "controlled thrust to reach the escape zone before your fuel runs out.")
    text(screen, fonts.small, story, GREY, (WIDTH // 2, 170), "midtop")

    card_w, card_h, gap = 330, 190, 30
    total = len(infos) * card_w + (len(infos) - 1) * gap
    x0 = (WIDTH - total) // 2
    for i, info in enumerate(infos):
        rect = pygame.Rect(x0 + i * (card_w + gap), 240, card_w, card_h)
        active = i == selected
        panel(screen, rect, alpha=220 if active else 160, border=CYAN if active else (50, 70, 110))
        text(screen, fonts.hud, f"LEVEL {i + 1}", CYAN if active else GREY, (rect.x + 20, rect.y + 18))
        text(screen, fonts.medium, info["name"], WHITE, (rect.x + 20, rect.y + 44))
        # wrap subtitle
        words, line, y = info["subtitle"].split(), "", rect.y + 84
        for w in words:
            if fonts.small.size(line + " " + w)[0] > card_w - 40:
                text(screen, fonts.small, line, GREY, (rect.x + 20, y))
                y += 19
                line = w
            else:
                line = (line + " " + w).strip()
        text(screen, fonts.small, line, GREY, (rect.x + 20, y))
        stats = f"{info['planets']} planet{'s' if info['planets'] > 1 else ''}  |  fuel {info['fuel']:.0f}%  |  {format_time(info['time_limit'])}"
        text(screen, fonts.tiny, stats, DIM, (rect.x + 20, rect.bottom - 44))
        best = highscores.get(str(i + 1))
        best_msg = f"BEST SCORE  {best}" if best else "NOT YET ESCAPED"
        text(screen, fonts.tiny, best_msg, GREEN if best else DIM, (rect.x + 20, rect.bottom - 24))

    rows = [("W / UP", "Thrust"), ("A / LEFT", "Rotate left"), ("D / RIGHT", "Rotate right"),
            ("SPACE", "Pause"), ("R", "Restart"), ("T", "Toggle trajectory"),
            ("V", "Toggle vectors"), ("ESC", "Menu / Exit")]
    cp = pygame.Rect(WIDTH // 2 - 330, 460, 660, 150)
    panel(screen, cp, alpha=150)
    for i, (k, v) in enumerate(rows):
        col, row = divmod(i, 4)
        px = cp.x + 30 + col * 330
        py = cp.y + 18 + row * 30
        text(screen, fonts.hud, k, YELLOW, (px, py))
        text(screen, fonts.hud, v, WHITE, (px + 120, py))

    blink = GREEN if int(t * 2) % 2 == 0 else (60, 160, 110)
    text(screen, fonts.medium, "LEFT / RIGHT or 1-3 to choose   ENTER to launch", blink,
         (WIDTH // 2, HEIGHT - 70), "midtop")


def draw_pause(screen, fonts):
    screen.blit(_dim_overlay(140), (0, 0))
    text(screen, fonts.large, "PAUSED", WHITE, (WIDTH // 2, HEIGHT // 2 - 40), "center")
    text(screen, fonts.small, "SPACE resume   R restart   ESC menu", GREY,
         (WIDTH // 2, HEIGHT // 2 + 14), "center")


def draw_result(screen, fonts, won, reason, stats, has_next, new_best):
    screen.blit(_dim_overlay(150), (0, 0))
    rect = pygame.Rect(0, 0, 560, 300)
    rect.center = (WIDTH // 2, HEIGHT // 2)
    panel(screen, rect, alpha=235, border=GREEN if won else RED)
    title = "ESCAPED!" if won else reason
    text(screen, fonts.large, title, GREEN if won else RED, (rect.centerx, rect.y + 30), "midtop")
    y = rect.y + 104
    for label, value in stats:
        text(screen, fonts.hud, label, GREY, (rect.x + 120, y))
        text(screen, fonts.hud, value, WHITE, (rect.right - 120, y), "topright")
        y += 28
    if new_best:
        text(screen, fonts.small, "NEW BEST SCORE!", YELLOW, (rect.centerx, y + 2), "midtop")
    if won and has_next:
        opts = "ENTER / N next level    R replay    ESC menu"
    elif won:
        opts = "System escaped! ENTER menu    R replay"
    else:
        opts = "R retry    ESC menu"
    text(screen, fonts.small, opts, WHITE, (rect.centerx, rect.bottom - 34), "midtop")


def draw_loading(screen, fonts, name):
    screen.fill(BG_COLOR)
    text(screen, fonts.medium, f"Plotting course: {name}", GREY, (WIDTH // 2, HEIGHT // 2), "center")
