# Gravity Escape

A 2D spaceflight puzzle game in **Python + Pygame**. Your spacecraft is trapped inside a
planetary system — use gravity and controlled thrust to reach the escape zone before your
fuel runs out. You never move the ship directly: you control thrust and direction, and
Newtonian physics decides the trajectory.

## Run it in VS Code

1. Install **Python 3.10+** and the VS Code **Python** extension.
2. Open the `GravityEscape` folder in VS Code (*File → Open Folder*).
3. Open a terminal (*Terminal → New Terminal*) and create a virtual environment:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

4. Install Pygame:

   ```bash
   pip install -r requirements.txt
   ```

   If that fails (very new Python versions sometimes lack a Pygame wheel), run
   `pip install pygame-ce` instead — it is a drop-in replacement, no code changes needed.

5. Run the game: press **F5** (the included `.vscode/launch.json` launches `main.py`),
   or run `python main.py` in the terminal.

No GPU is needed — it runs on any laptop.

## Controls

| Key | Function |
|-----|----------|
| W / ↑ | Thrust |
| A / ← | Rotate left |
| D / → | Rotate right |
| SPACE | Pause / resume |
| R | Restart level |
| T | Toggle trajectory prediction |
| V | Toggle physics vectors (velocity, gravity, thrust) |
| ESC | Back to menu / exit |

## Levels

| Level | Name | Idea |
|-------|------|------|
| 1 | Escape the Planet | One planet. Learn the controls and break out of orbit. |
| 2 | Gravity Assist | Two planets, 40% fuel. Use Ares' gravity to bend your path. |
| 3 | Dangerous System | Four bodies (one is a moving moon). Every planet pulls at once. |

Levels are JSON files in `levels/` — edit them or add new ones (and list the file in
`LEVEL_FILES` in `config.py`). All three levels have been checked to be winnable with a
headless solver.

Score = 1000 + fuel left × 20 + seconds left × 10. Best scores are saved to `highscores.json`.

## Physics

Every physics step (240 per second, fixed time step):

1. **Gravity** from each planet: `F = G·M·m / r²`, directed towards the planet
2. **Acceleration**: `a = F / m`, summed over all planets (plus engine thrust)
3. **Velocity**: `v_new = v_old + a·Δt`
4. **Position**: `x_new = x_old + v_new·Δt`
5. **Collision detection**: circle–circle distance checks

Using the *new* velocity for the position update is semi-implicit (symplectic) Euler —
same cost as plain Euler, but orbits stay stable instead of spiralling outward.

**Trajectory prediction** (the dotted line) runs the same gravity + integration functions
on future time steps with the engine off, for 8 seconds ahead. It turns green when the
coasting path reaches the escape zone and red when it ends in an impact. Moving planets
(Selene in level 3) are predicted correctly because each planet's position is a function
of time.

Distances are in pixels and time in seconds; the HUD converts them to km and km/s for
display (`KM_PER_PIXEL`, `KMS_PER_PIXEL_PER_S` in `config.py`).

## Project structure

```
GravityEscape/
├── main.py              # Game class: state machine, game loop, fixed-step physics
├── config.py            # constants: window, G, thrust, fuel, colours, paths
├── physics.py           # gravity, integration, trajectory prediction
├── player.py            # Spacecraft: controls, thrust, fuel, drawing
├── planet.py            # Planet: mass, orbit motion, procedural lit-sphere artwork
├── level.py             # Level loading from JSON, EscapeZone
├── collision.py         # circle collisions, escape zone, out-of-bounds
├── ui.py                # HUD, menu, pause/result screens, prediction line, vectors
├── effects.py           # starfield, exhaust and explosion particles, asset loading
├── generate_assets.py   # re-renders the PNGs in assets/
├── assets/              # background.png, spacecraft.png, planet previews
└── levels/              # level1.json, level2.json, level3.json
```

`background.png` and `spacecraft.png` are loaded if present — replace them with your own
art to re-skin the game. Planets are drawn procedurally (per-pixel Lambert lighting on a
sphere); the `planet_*.png` files are previews for your report.

## Tuning

All the feel of the game lives in `config.py`: `THRUST_ACCEL`, `ROTATION_SPEED`,
`FUEL_BURN_RATE`, `G`, `PREDICT_STEPS`. Planet masses, fuel and time limits are per level
in the JSON files.
