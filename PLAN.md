# PLAN.md

Progress and next steps. Agents: read this before starting work.

Last updated: 2026-10-14

## Now

**Next step:** decide whether this lab needs a unified test harness across subprojects (e.g. `uv add --dev pytest` running smoke tests across all subdirectories). Currently each module has its own verification check (documented in `README.md` and `RUNS.md`).

## Done

- [x] Repository created and baseline `hello.py` smoke test established
- [x] Working rules formulated in `AGENTS.md`, loaded via `CLAUDE.md`
- [x] `uv` package management and dependencies tracked in `pyproject.toml` and `uv.lock`
- [x] Assignment "Medium · Slides with an animation, then a PDF note" completed in `slides-with-animation-pdf-note/`
- [x] Assignment "leaves2" ML pipeline completed in `leaves2/` (data exploration, SPEC.md, baseline, 5-fold CV across 4 model families, holdout test evaluation, Quarto presentation and interactive report)
- [x] Retro arcade Snake game with dynamic rotation mechanics and canvas rendering in `snake/`
- [x] Parametric 3D CadQuery cable clip with STEP/STL export and mass estimation in `cable-clip/`
- [x] Automated GitHub Pages deployment workflow configured in `.github/workflows/deploy-pages.yml`
- [x] Central interactive landing portal created at root `index.html`
- [x] Repository cleanup: modular directory structure, README overhauled with clear instructions and without emails/personal data

## Open questions

- Future automated CI/CD checks: wire `pytest` into GitHub Actions on pull requests / main push.

## Backlog

- Add 3D model web viewer (Three.js / stl-viewer) for `cable-clip/` artifacts in the GitHub Pages portal.
