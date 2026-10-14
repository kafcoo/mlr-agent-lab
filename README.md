# mlr-agent-lab

A laboratory for experimenting with AI coding agents: benchmarking prompts, model capabilities, strict verification criteria, and reproducible engineering artifacts under real-world constraints.

🌐 **Live Web Showcase:** [kafcoo.github.io/mlr-agent-lab](https://kafcoo.github.io/mlr-agent-lab/)

---

## Repository Structure

Every project in this repository is organized into its own dedicated, self-contained directory:

| Directory / File | Description | Core Tech |
| :--- | :--- | :--- |
| [`leaves2/`](leaves2/) | **Botanical Classification ML Pipeline:** Exploratory data analysis, 5-fold CV hyperparameter search across 4 model families (k-NN champion with 90.91% test accuracy / 0.8983 Macro F1), interactive decision-boundary canvas report, and 5-slide Quarto presentation. | `scikit-learn`, `pandas`, `quarto` |
| [`snake/`](snake/) | **Spinning Snake Game:** Retro arcade browser game with 90° board rotation mechanics every 4 pellets, non-reversing FIFO turn queue, responsive canvas rendering, and self-tests. | HTML5, Canvas 2D, JS |
| [`slides-with-animation-pdf-note/`](slides-with-animation-pdf-note/) | **Technical Note & Animation Presentation:** 5-slide Quarto Reveal.js presentation with embedded gameplay GIF and a single-page A4 PDF technical specification note. | `quarto`, `tectonic`, LaTeX |
| [`cable-clip/`](cable-clip/) | **Parametric 3D CAD:** Fully parametric M4-mounting cable clip exporting STEP solids, 3D printable STL meshes, and calculated physical metrics (volume, mass). | `cadquery` |
| [`index.html`](index.html) | **Interactive Web Portal:** Central landing page for GitHub Pages featuring live metrics, presentation viewer, and research report links. | HTML5, Modern CSS |
| [`hello.py`](hello.py) | **Sanity Canary:** Minimal environment smoke test required by working rules before completing runs. | Python 3.13 |
| [`AGENTS.md`](AGENTS.md) | **Working Rules:** Strict instructions for agents (read before acting, Python through `uv`, real checks before claiming "done"). | Markdown |
| [`CLAUDE.md`](CLAUDE.md) | Agent config importing `AGENTS.md` for session initialization. | Markdown |
| [`PLAN.md`](PLAN.md) | Roadmap, completed milestones, and immediate next steps. | Markdown |
| [`RUNS.md`](RUNS.md) | Comprehensive audit log of all agent runs, prompts, and empirical verification commands. | Markdown |

---

## Prerequisites & Setup

- **Python:** Managed strictly via [`uv`](https://docs.astral.sh/uv/) (Python 3.13)
- **Dependencies:** Specified in `pyproject.toml` and locked in `uv.lock`

```bash
# Verify uv environment and run the smoke test
uv run hello.py
```

---

## How to Run & Verify Projects

### 1. Botanical Classification (`leaves2/`)
```bash
# Run data exploration
uv run python leaves2/explore.py

# Run cross-validation, hyperparameter tuning, and holdout evaluation
uv run python leaves2/train.py

# Render Quarto presentation and technical report to HTML
uv run quarto render leaves2/slides.qmd
uv run quarto render leaves2/report.qmd
```

### 2. Parametric 3D Cable Clip (`cable-clip/`)
```bash
# Build and export default STEP, STL, and model.json
uv run python cable-clip/cable_clip.py

# Inspect parameter specifications
uv run python cable-clip/cable_clip.py --list
```

### 3. Spinning Snake Game (`snake/`)
```bash
# Launch the game locally in your browser
open snake/index.html
```

### 4. Presentation & PDF Note (`slides-with-animation-pdf-note/`)
```bash
# Rebuild Quarto slides and compile LaTeX note
uv run quarto render slides-with-animation-pdf-note/slides.qmd
tectonic slides-with-animation-pdf-note/note.tex
```

---

## Core Guidelines

All automated agents follow the protocol defined in [`AGENTS.md`](AGENTS.md):
1. **Always use `uv`** — never run raw `pip install` or modify system environments.
2. **Empirical Verification** — commands must be executed and their actual outputs reported before claiming any task is done.
3. **Repository Hygiene** — no personal emails, tokens, or untracked temporary files in commits.
