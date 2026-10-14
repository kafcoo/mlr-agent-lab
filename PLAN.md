# PLAN.md

Progress and next step. Agents: read this before starting work.

Last updated: 2026-10-14

## Now

**Next step:** decide whether this lab needs a real test suite. If yes, the
first task is `uv add --dev pytest`, a `tests/` directory, and a
`uv run pytest` check wired into `AGENTS.md` §3. If no, delete this section
and keep the "script runs cleanly" check as the bar.

## Done

- [x] Folder created, `hello.py` added and pushed
- [x] Public repo `kafcoo/mlr-agent-lab` created via `gh`
- [x] Working rules written: `AGENTS.md`, imported by `CLAUDE.md`
- [x] `README.md`, `PLAN.md`, `RUNS.md` created
- [x] `uv` and `gh` installed via Homebrew, no admin rights
- [x] Assignment "Medium · Slides with an animation, then a PDF note" completed in `slides-with-animation-pdf-note/` (Quarto presentation + Tectonic 1-page PDF note)

## Open questions

- What is the lab actually *for*? Currently it holds one 15-byte script and a
  process. The `README.md` goal is inferred — confirm or replace it.
- No `.gitignore` yet. A `.DS_Store` is already present and untracked; it will
  be swept up by the next `git add -A` unless ignored.
- No dependency file (`pyproject.toml`) yet, because there are no deps.

## Backlog

- Add `.gitignore` (`.DS_Store`, `__pycache__/`, `*.pyc`, `.venv/`)
- First real experiment: pick a task worth logging in `RUNS.md`
