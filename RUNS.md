# RUNS.md

A log of agent runs: which model, what was asked, and how the result was
actually checked. Newest last.

The point of this file is the third column. "How I checked it" must be
something that was really run, with its real output — not the agent asserting
it works.

---

## Run 1 — 2026-10-14 — environment setup

**Model:** `thinker` alias → served by `deepseek-v4.1-flash`
(Claude Code 2.1.299, effort `high`)

Sourced from the session transcript (`requestedModel` vs the model recorded on
each assistant message), not from memory. Note this differs from the
`ANTHROPIC_MODEL` environment variable, which is set to `agentic` — the
in-session `/model thinker` selection is what took effect.

**Asked:** check whether GitHub credentials exist and whether repos can be
created; install `gh` and `uv` without administrator rights into the user
folder; verify both work.

**How I checked it:**

```bash
which gh uv            # /opt/homebrew/bin/gh, /opt/homebrew/bin/uv
gh --version           # 2.102.0
uv --version           # 0.13.0
uv run --python 3.13 python -c "import sys; print(sys.version)"
                       # 3.13.16 arm64 — uv fetched its own interpreter
uv venv --python 3.12  # venv created OK
```

Credential check was read-only against the API:

```bash
printf 'protocol=https\nhost=github.com\n\n' | git credential fill
curl -H "Authorization: Bearer $TOKEN" https://api.github.com/user
                       # 200, login kafcoo, x-oauth-scopes: repo
```

**Result:** both tools installed from Homebrew bottles (no compilation, no
`sudo`). `/opt/homebrew` is owned by the user, so no admin rights were needed.

**Note:** `gh` was not authenticated at install time; the user ran
`gh auth login` separately afterwards.

---

## Run 2 — 2026-10-14 — create the public repo

**Model:** `thinker` alias → `deepseek-v4.1-flash`

**Asked:** create a public repo `mlr-agent-lab` from this folder, showing the
contents before pushing.

**How I checked it:** enumerated the payload locally *before* any network call,
then verified the remote *after* pushing, both against the GitHub API:

```bash
git ls-files -s                     # one blob: hello.py
find . -name '*.env*' -o -name '*.pem' -o -name '*secret*'   # nothing
gh api "repos/kafcoo/mlr-agent-lab/git/trees/main?recursive=1"
                                    # blob 15  hello.py
gh api repos/kafcoo/mlr-agent-lab/contents/hello.py --jq .content | base64 -d
                                    # print("hello")
curl -sS -o /dev/null -w '%{http_code}' \
  https://api.github.com/repos/kafcoo/mlr-agent-lab   # 200 with no auth
```

The anonymous `curl` is the check that matters: it proves the repo is
genuinely public rather than merely reported as such.

**Result:** repo public at <https://github.com/kafcoo/mlr-agent-lab>, exactly
one commit, one file. Commit author is the GitHub noreply address.

---

## Run 3 — 2026-10-14 — write the working rules

**Model:** `thinker` alias → `deepseek-v4.1-flash`

**Asked:** write `AGENTS.md` (read `README.md`/`PLAN.md` first, use uv, run
checks before claiming done), have `CLAUDE.md` load it, and create `README.md`,
`PLAN.md`, `RUNS.md`.

**How I checked it:**

```bash
uv run hello.py          # printed: hello  (README's documented command works)
uv run python hello.py   # printed: hello
uv run python -c "..."   # uv can execute inline code
ls -A                    # AGENTS.md CLAUDE.md PLAN.md README.md RUNS.md
```

The README's documented commands were run before being written down, so the
instructions are known-good rather than assumed.

**Result:** five files created. Verified `uv run` works with no
`pyproject.toml` present, since there are no dependencies yet.

**Caveat:** `CLAUDE.md` uses the `@AGENTS.md` import syntax. Whether Claude
Code picks it up automatically was **not** verified in a fresh session — it
will only be provable on the next session start.
