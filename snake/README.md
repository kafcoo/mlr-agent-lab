# Spinning Snake Game

Retro Snake game built in standalone HTML5 Canvas 2D with zero external dependencies.

## Game Mechanics

- **Fixed-tick engine:** 110 ms ticks (9.09 Hz) decoupling simulation from rendering.
- **Dynamic Board Rotation:** Every 4 pellets collected, the arena rotates 90° clockwise or counter-clockwise while preserving snake velocity heading and relative momentum.
- **FIFO Turn Queue:** 3-entry command buffer preventing key jamming and filtering out accidental 180° self-collisions.
- **Deterministic PRNG:** 32-bit xorshift generator for reproducible food spawns and obstacle layouts.
- **Accessibility:** Supports `prefers-reduced-motion` for snapping rotations instead of eased continuous spinning.

## How to Play

Open `index.html` directly in any web browser:

```bash
open snake/index.html
```

### Controls

- **Arrow keys / WASD:** Steer the snake
- **Space:** Pause / Resume
- **R:** Restart game
