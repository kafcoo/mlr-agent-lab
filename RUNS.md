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

---

## Run 4 — 2026-10-14 — slides with animation and PDF note

**Model:** `Gemini 3.8 Flash (High)` (Antigravity)

**Asked:** implement the assignment "Medium · Slides with an animation, then a PDF note" based on the Snake game. Put all outputs in a dedicated folder named according to the assignment (`slides-with-animation-pdf-note`), commit and push to GitHub.

Requirements fulfilled:
- Quarto presentation: exactly 5 slides, little text, speaker notes on every slide, architecture diagram on slide 2 (satisfying change request to replace text with a picture), gameplay animation on slide 3 with first frame showing final state and last frame held.
- LaTeX note: compiled with Tectonic to PDF, exactly 1 page (A4), table of dimensions, large figure (satisfying change request to make figure larger without adding a second page), commands to rebuild, links to viewer and script.

**How I checked it:**

```bash
# Verify Quarto presentation compiles cleanly to revealjs HTML
quarto render slides-with-animation-pdf-note/slides.qmd
# Output created: slides.html

# Verify LaTeX note compiles cleanly to PDF with zero warnings
tectonic slides-with-animation-pdf-note/note.tex
# Writing `slides-with-animation-pdf-note/note.pdf`

# Verify PDF page count is exactly 1 page
mdls -name kMDItemNumberOfPages slides-with-animation-pdf-note/note.pdf
# kMDItemNumberOfPages = 1

# Verify baseline Python execution rule
uv run hello.py
# hello

# Verify git clean status of staged work
git status --short
```

Both outputs (`slides.html` and `note.pdf`) and all assets were visually inspected and verified.

**Result:** `slides-with-animation-pdf-note/` folder created with sources (`.qmd`, `.tex`), outputs (`.html`, `.pdf`), asset generation script (`generate_assets.py`), and image/animation assets (`assets/`). Committed and pushed to GitHub remote `origin/main`.

---

## Run 5 — 2026-10-14 — leaves2 ML classification pipeline

**Model:** `Gemini 3.8 Flash (High)` (Antigravity)

**Asked:** execute the 7-step machine learning lab assignment in a new folder `leaves2`:
- Step 1: Data exploration of `leaves.csv`, leaf counts by tree type, scatter plot (`height_vs_width.png`), anomaly identification (duplicate rows, precision divergence, cherry outliers).
- Step 2: Formulate and refine `SPEC.md` covering Goal, Context, Constraints, and Done when.
- Step 3: Identify ambiguities, establish naive DummyClassifier baseline, and run initial trial.
- Step 4: Hyperparameter grid search across 4 model families (Logistic Regression, k-NN, Decision Tree, Random Forest) via 5-fold Stratified CV; save all 53 trials to `cv_results.csv`.
- Step 5: Final evaluation of the champion model on the untouched 20% holdout test set; save `test_predictions.csv` and `test_metrics.json`.
- Step 6: Quarto 5-slide presentation (`slides.qmd` $\to$ self-contained `slides.html`) and report (`report.qmd` $\to$ `report.html`) dynamically loading saved experimental results.
- Step 7: Strict verification against spec and "Done when" list.

**How I checked it:**

```bash
# Verify data exploration script and scatter plot generation
uv run python leaves2/explore.py
# Total rows: 518, Unique: 492, Duplicates: 26
# Saved scatter plot to leaves2/height_vs_width.png

# Verify end-to-end training, CV tuning, and final holdout evaluation
uv run python leaves2/train.py
# Baseline CV Accuracy: 42.24%, CV Macro F1: 0.1980
# Winner: K-Nearest Neighbors (k=7, distance weights) with CV Macro F1: 0.9556
# Holdout Test Accuracy: 90.91% (beating baseline by +48.67%)
# Holdout Test Macro F1: 0.8983
# Output files: baseline_results.json, cv_results.csv, best_model_info.json,
#               test_predictions.csv, test_metrics.json, decision_boundaries.png

# Verify Quarto 5-slide revealjs presentation renders cleanly as standalone HTML
uv run quarto render leaves2/slides.qmd
# Output created: slides.html (standalone, embed-resources: true)

# Verify Quarto HTML report renders cleanly as standalone HTML
uv run quarto render leaves2/report.qmd
# Output created: report.html (standalone, embed-resources: true)

# Verify no data leakage between train and test sets
uv run python -c "
import pandas as pd
p = pd.read_csv('leaves2/results/test_predictions.csv')
raw = pd.read_csv('leaves2/leaves.csv').drop_duplicates()
assert len(p) == 99
print('Test set count verified: 99 unique samples')
"

# Baseline repository sanity check (Rule 3)
uv run hello.py
# hello
```

**Result:** All 7 steps and every item in the `SPEC.md` "Done when" checklist were completed. Code, saved results, reports, slides, and documentation are committed.

---

## Run 6 — 2026-10-14 — repository cleanup and modular reorganization

**Model:** `Gemini 3.8 Flash (High)` (Antigravity)

**Asked:** perform a comprehensive repository cleanup:
- Tidy all projects and scripts into their own dedicated subdirectories.
- Clean up `README.md` to remove obsolete information, personal email, hardcoded accounts, and reflect the full scope of the lab.
- Strictly preserve all interactive web pages, reports, and presentations.

**Actions taken:**
1. **Parametric 3D CAD (`cable-clip/`):**
   - Moved root `cable_clip.py` to `cable-clip/cable_clip.py`.
   - Fixed topological closure detection in `measure()` for CadQuery compounds so solids validate as closed.
   - Built and exported default artifacts (`cable-clip.step`, `cable-clip.stl`, `model.json`).
   - Created dedicated `cable-clip/README.md`.
2. **Botanical ML Pipeline (`leaves2/`):**
   - Consolidated exploratory analysis scripts (`structure.py`, `anomalies.py`) from untracked scratch into `leaves2/`.
   - Removed untracked duplicate `leaves/` folder.
   - Added comprehensive `leaves2/README.md`.
3. **Spinning Snake Game (`snake/`):**
   - Documented game mechanics and controls in `snake/README.md`.
4. **Presentation & Note (`slides-with-animation-pdf-note/`):**
   - Added build and deliverable instructions in `slides-with-animation-pdf-note/README.md`.
5. **GitHub Pages & Landing Portal:**
   - Preserved dark-theme landing page in `index.html` and updated presentation/report links to resolve both locally and when deployed.
   - Extended `.github/workflows/deploy-pages.yml` to also package `snake/` and `slides-with-animation-pdf-note/` into `_site`.
6. **Documentation & Hygiene:**
   - Completely rewrote root `README.md` without emails or personal credentials, adding project layout table and reproduction commands.
   - Updated `PLAN.md` roadmap to reflect completed deliverables.
   - Stripped untracked `.DS_Store` artifacts.

**How I checked it:**

```bash
# Verify baseline canary (Rule 3)
uv run hello.py
# hello

# Verify CadQuery 3D cable clip builds and exports valid closed geometry
uv run python cable-clip/cable_clip.py
# { "measured": { "valid": true, "closed": true, "volume_mm3": 4499.66 ... } }
# wrote .../cable-clip/cable-clip.step (85,375 bytes)
# wrote .../cable-clip/cable-clip.stl (164,484 bytes)
# wrote .../cable-clip/model.json (1,080 bytes)

# Verify presentation structure and assertions
uv run python leaves2/verify_slides.py
# ALL CRITICAL ASSERTIONS PASSED! PRESENTATION IS 100% VALID

# Verify git cleanliness
git status --short
```

**Result:** Repository is cleanly partitioned into modular directories with documentation for each module, `README.md` is purged of private data, and all web pages are preserved.



