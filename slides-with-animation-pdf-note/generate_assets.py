#!/usr/bin/env python3
"""Generate assets for the Snake game presentation and LaTeX note.

Outputs:
1. assets/architecture.png - Architectural diagram for Slide 2
2. assets/snake_animation.gif - Gameplay animation fulfilling:
   'the animation's first frame shows the final state and the last frame is held'
"""

import os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Colors matching snake/index.html
COLOR_BG = "#0d1117"
COLOR_PANEL = "#161b22"
COLOR_LINE = "#262d38"
COLOR_INK = "#d7dee8"
COLOR_MUTED = "#7d8796"
COLOR_SNAKE = "#3fd68c"
COLOR_SNAKE_DIM = "#1f7a51"
COLOR_SNAKE_HEAD = "#5affac"
COLOR_FOOD = "#ff6b6b"
COLOR_ACCENT = "#ffd166"

# ==============================================================================
# 1. Architecture Diagram
# ==============================================================================
def generate_architecture_diagram():
    w, h = 960, 540
    img = Image.new("RGBA", (w, h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Outer border / card
    draw.rounded_rectangle([20, 20, w - 20, h - 20], radius=16, fill=COLOR_PANEL, outline=COLOR_LINE, width=2)

    # Title
    draw.text((50, 40), "SNAKE GAME: SYSTEM ARCHITECTURE", fill=COLOR_ACCENT)

    # Component boxes
    components = [
        ("Input Subsystem", 50, 100, 240, 380, [
            "Keyboard Event Listener",
            "- KeyDown capture",
            "- WASD / Arrow keys",
            "- Space (Pause) / R (Reset)",
            "",
            "FIFO Turn Queue (max 3)",
            "- Prevents 180 deg reversals",
            "- Eliminates key jamming",
            "- Decoupled from rAF"
        ]),
        ("Core Engine & State", 350, 100, 260, 380, [
            "Tick Engine (110 ms)",
            "- Fixed-step accumulator",
            "- Deterministic RNG seed",
            "",
            "State Representation",
            "- 21 x 21 Discrete Grid",
            "- Snake: [{x, y}, ...]",
            "- Food: Free-cell picker",
            "- Collision detection",
            "- Score & High-score state"
        ]),
        ("Render Pipeline", 670, 100, 240, 380, [
            "HTML5 2D Canvas (500x500)",
            "- window.requestAnimationFrame",
            "- Responsive scaling (vmin)",
            "",
            "Visual Layering",
            "- Grid background & border",
            "- Rounded snake segments",
            "- Pulsing radial food glow",
            "- Backdrop blur overlay",
            "- DOM HUD score sync"
        ]),
    ]

    for title, x, y, bw, bh, bullets in components:
        # Box
        draw.rounded_rectangle([x, y, x + bw, y + bh], radius=10, fill="#1c212b", outline=COLOR_LINE, width=2)
        # Header strip
        draw.rounded_rectangle([x, y, x + bw, y + 42], radius=10, fill="#232936")
        draw.text((x + 16, y + 12), title, fill=COLOR_INK)

        # Content lines
        curr_y = y + 56
        for line in bullets:
            fill_col = COLOR_ACCENT if line.startswith("- KeyDown") or line.startswith("- 21") or line.startswith("- HTML5") else COLOR_INK
            if line.startswith("-"):
                fill_col = COLOR_MUTED
            draw.text((x + 16, curr_y), line, fill=fill_col)
            curr_y += 20

    # Arrows between components
    # 1 -> 2
    draw.line([(290, 270), (350, 270)], fill=COLOR_SNAKE, width=3)
    draw.polygon([(345, 265), (355, 270), (345, 275)], fill=COLOR_SNAKE)
    draw.text((298, 250), "turns", fill=COLOR_SNAKE)

    # 2 -> 3
    draw.line([(610, 270), (670, 270)], fill=COLOR_SNAKE, width=3)
    draw.polygon([(665, 265), (675, 270), (665, 275)], fill=COLOR_SNAKE)
    draw.text((618, 250), "state", fill=COLOR_SNAKE)

    out_path = os.path.join(ASSETS_DIR, "architecture.png")
    img.save(out_path)
    print(f"Saved {out_path}")

# ==============================================================================
# 2. Gameplay Animation (First frame = final state, last frame held)
# ==============================================================================
def generate_gameplay_animation():
    COLS = 21
    ROWS = 21
    CELL_PX = 20
    BOARD_W = COLS * CELL_PX
    BOARD_H = ROWS * CELL_PX
    CANVAS_W = BOARD_W + 40
    CANVAS_H = BOARD_H + 90

    # Define the gameplay sequence:
    # Initial snake at (10, 10), length 4 heading right
    # Food 1 at (14, 10)
    # After eating food 1: length 5, turns UP, Food 2 at (14, 7)
    # After eating food 2: length 6, turns LEFT, Food 3 at (11, 7)
    # After eating food 3: length 7 (final state)
    
    # Path of the head:
    steps = [
        # moving right to eat food 1 at (14, 10)
        {"head": (10, 10), "food": (14, 10), "score": 0, "len": 4},
        {"head": (11, 10), "food": (14, 10), "score": 0, "len": 4},
        {"head": (12, 10), "food": (14, 10), "score": 0, "len": 4},
        {"head": (13, 10), "food": (14, 10), "score": 0, "len": 4},
        {"head": (14, 10), "food": (14, 10), "score": 1, "len": 5}, # Eat food 1!
        # turn UP towards food 2 at (14, 7)
        {"head": (14, 9),  "food": (14, 7),  "score": 1, "len": 5},
        {"head": (14, 8),  "food": (14, 7),  "score": 1, "len": 5},
        {"head": (14, 7),  "food": (14, 7),  "score": 2, "len": 6}, # Eat food 2!
        # turn LEFT towards food 3 at (11, 7)
        {"head": (13, 7),  "food": (11, 7),  "score": 2, "len": 6},
        {"head": (12, 7),  "food": (11, 7),  "score": 2, "len": 6},
        {"head": (11, 7),  "food": (11, 7),  "score": 3, "len": 7}, # Eat food 3 (Final State!)
    ]

    # Pre-calculate full snake bodies for each step
    # Snake history
    history = [(10 - i, 10) for i in range(15)]
    history.reverse() # now history ends at (10, 10)

    frames = []

    def render_frame(snake_cells, food_cell, score, is_final=False):
        img = Image.new("RGB", (CANVAS_W, CANVAS_H), COLOR_BG)
        d = ImageDraw.Draw(img)

        # Header
        d.text((20, 16), "SNAKE", fill=COLOR_INK)
        score_text = f"score {score}   best 3"
        d.text((CANVAS_W - 140, 16), score_text, fill=COLOR_MUTED)

        # Board background
        ox, oy = 20, 50
        d.rounded_rectangle([ox, oy, ox + BOARD_W, oy + BOARD_H], radius=8, fill=COLOR_PANEL, outline=COLOR_LINE, width=1)

        # Draw grid subtle dots
        for gx in range(COLS):
            for gy in range(ROWS):
                px = ox + gx * CELL_PX + CELL_PX // 2
                py = oy + gy * CELL_PX + CELL_PX // 2
                d.point((px, py), fill="#1f2631")

        # Draw food
        fx, fy = food_cell
        f_px = ox + fx * CELL_PX
        f_py = oy + fy * CELL_PX
        # Radial food effect
        d.ellipse([f_px + 2, f_py + 2, f_px + CELL_PX - 2, f_py + CELL_PX - 2], fill=COLOR_FOOD)
        d.ellipse([f_px + 5, f_py + 5, f_px + CELL_PX - 5, f_py + CELL_PX - 5], fill="#ff9999")

        # Draw snake body
        for i, (sx, sy) in enumerate(snake_cells):
            s_px = ox + sx * CELL_PX
            s_py = oy + sy * CELL_PX
            fill_col = COLOR_SNAKE_HEAD if i == 0 else (COLOR_SNAKE if i < 3 else COLOR_SNAKE_DIM)
            d.rounded_rectangle([s_px + 1, s_py + 1, s_px + CELL_PX - 1, s_py + CELL_PX - 1], radius=4, fill=fill_col)
            if i == 0:
                # Eye
                d.ellipse([s_px + 6, s_py + 6, s_px + 9, s_py + 9], fill="#0d1117")

        if is_final:
            # Subtle badge
            d.text((CANVAS_W // 2 - 50, CANVAS_H - 30), "[ TARGET ACHIEVED ]", fill=COLOR_ACCENT)
        else:
            d.text((CANVAS_W // 2 - 35, CANVAS_H - 30), "LIVE GAMEPLAY", fill=COLOR_MUTED)

        return img

    computed_steps = []
    curr_hist = list(history)
    for st in steps:
        curr_hist.append(st["head"])
        body = [curr_hist[-1 - i] for i in range(st["len"])]
        computed_steps.append((body, st["food"], st["score"]))

    # Final state is the last step
    final_body, final_food, final_score = computed_steps[-1]
    final_frame = render_frame(final_body, final_food, final_score, is_final=True)

    # 1. First frame MUST show the final state:
    frames.append(final_frame)
    durations = [1200] # First frame held for 1.2s to clearly show final state

    # 2. Progression frames:
    for body, food, score in computed_steps:
        frame = render_frame(body, food, score, is_final=False)
        frames.append(frame)
        durations.append(250)

    # 3. Last frame is held:
    # Hold the final frame at the end for 2.5 seconds
    frames.append(final_frame)
    durations.append(2500)

    out_gif = os.path.join(ASSETS_DIR, "snake_animation.gif")
    frames[0].save(
        out_gif,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0
    )
    print(f"Saved {out_gif} with {len(frames)} frames. First frame is final state, last frame held.")

if __name__ == "__main__":
    generate_architecture_diagram()
    generate_gameplay_animation()
