# mlr-agent-lab

A lab for experimenting with coding agents: what a given model was actually
asked to do, and how the result was verified.

**Goal:** keep a small, runnable sandbox where agent-driven changes are made
under real rules (uv for Python, checks before "done") and where every run is
logged in `RUNS.md` with the model that performed it and the evidence that it
worked.

> The goal statement above is my reading of the project — correct it if it is
> wrong. See `PLAN.md` for what is next.

## Layout

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Working rules for agents. **Read this first.** |
| `CLAUDE.md` | Imports `AGENTS.md` so Claude Code loads the rules. |
| `README.md` | This file — goal and how to run things. |
| `PLAN.md` | Progress and the next step. |
| `RUNS.md` | Log of runs: model, request, how it was checked. |
| `hello.py` | The current (only) executable. |

## Requirements

- macOS (Apple Silicon)
- `uv` — installed at `/opt/homebrew/bin/uv` (v0.13.0)
- `gh` — GitHub CLI, `/opt/homebrew/bin/gh` (v2.102.0), logged in as `kafcoo`

Both were installed with Homebrew, no admin rights:

```bash
brew install uv gh
```

## How to run things

```bash
uv run hello.py          # run the script
uv run python hello.py   # equivalent, explicit interpreter
uv run python -c "print('hi')"
```

Use `uv`, not bare `python`/`pip`. There is currently no `pyproject.toml`
because there are no dependencies yet — `uv run` works without one. The first
time a third-party package is needed, run `uv add <package>` and commit the
resulting `pyproject.toml` and `uv.lock`.

Ad-hoc tools do not need installing:

```bash
uvx ruff check .         # run a tool without adding it as a dependency
```

## Checks

There is no test suite yet (see `PLAN.md`). The current check is that the
script runs cleanly:

```bash
uv run hello.py          # expect: hello
```

## Git

Public repo: <https://github.com/kafcoo/mlr-agent-lab>

Commits use the GitHub noreply address, set repo-local so the global git
identity is untouched:

```bash
git config user.email    # 158568591+kafcoo@users.noreply.github.com
```
