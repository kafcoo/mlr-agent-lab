# AGENTS.md — Working Rules

Rules for any agent (Claude Code, `gh`, or other) working in this repo.
`CLAUDE.md` imports this file, so both entry points share these rules.

## 1. Read before you act

At the start of every session, read these in order:

1. `README.md` — what this project is and how to run it
2. `PLAN.md` — where the work stands and what the next step is

Do not start editing until you have read both. `PLAN.md` is the source of
truth for "what to do next". If it is stale, update it rather than guessing.

## 2. Python goes through uv — always

| Do this | Not this |
| --- | --- |
| `uv run hello.py` | `python hello.py` |
| `uv run python -c "..."` | `python3 -c "..."` |
| `uv add requests` | `pip install requests` |
| `uv run pytest` | `pytest` |
| `uv sync` | `pip install -r requirements.txt` |

Hard rules:

- **Never** run a global `pip install` (or `pip install --user`, or `python -m pip install`).
  Not for this project, not "just this once".
- **Never** `sudo` anything to install Python packages. `uv` installs into
  project-local or user-local locations and needs no admin rights.
- Adding a dependency means `uv add <pkg>`, which updates `pyproject.toml`
  and `uv.lock` together. Commit both.
- Ad-hoc tooling also goes through uv: `uvx <tool>` (e.g. `uvx ruff`).

`uv` is installed at `/opt/homebrew/bin/uv`. If it is missing, see README.

## 3. Run checks before you say it is done

Never report work as complete, working, or fixed without having actually run
something that would have caught it being broken.

Minimum bar before saying "done":

```bash
uv run hello.py          # the thing still runs
git status --short       # no stray files about to be committed
```

Anything larger must be run for real and its real output reported:

- **If the change is a bug fix** — reproduce the bug first, then show it is fixed.
- **If tests exist** — run them (`uv run pytest`) and paste the result.
- **If tests do not exist yet** — say so explicitly. Do not imply coverage
  that does not exist.

Report failures plainly, with the output. "Tests fail with X" is a correct
and useful report. "Should work now" is not a report at all.

Do not describe a command as verified unless you ran it and read its output.
Reading the code and concluding it looks right is not a check.

## 4. Repo hygiene

- Commit messages: imperative subject line ("Add hello script"), no trailing period.
- `.DS_Store` and other OS cruft are gitignored — do not commit them.
- This repo is **public**. Do not commit secrets, tokens, `.env` files, or
  personal data.
- Commit with the GitHub noreply identity, not a real email address
  (already configured repo-local — do not change it to a real address).
- Do not `git push --force`, rewrite published history, or change repo
  visibility without asking first.
