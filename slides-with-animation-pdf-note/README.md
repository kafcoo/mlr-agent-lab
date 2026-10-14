# Slides with Animation & PDF Note

Interactive Quarto Reveal.js presentation and single-page A4 PDF technical note covering the Snake game architecture and specifications.

## Deliverables

1. **`slides.html` (Quarto Presentation):**
   - 5 linear slides with minimal text and rich visuals.
   - Comprehensive speaker notes on every slide (`s` key in presentation mode).
   - Architectural diagram on Slide 2 (`assets/architecture.png`).
   - Looping gameplay animation on Slide 3 (`assets/snake_animation.gif`) with terminal frame freeze.
2. **`note.pdf` (1-page Technical Note):**
   - Typeset in LaTeX with [Tectonic](https://tectonic-typesetting.github.io/).
   - Strictly fits onto a single A4 page with 1.4 cm margins.
   - Prominent gameplay capture figure, dimensional specifications table, and rebuild instructions.

## Build Instructions

```bash
# Re-generate diagram and animation assets
uv run python generate_assets.py

# Render Quarto slides to HTML
uv run quarto render slides.qmd

# Compile LaTeX technical note to PDF
tectonic note.tex
```
