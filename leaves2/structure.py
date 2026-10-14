"""Is leaves.csv 518 independent leaves, or a smaller set copied around?

Two things to separate:
  A. exact repeats      — the same row pasted again
  B. jittered repeats   — the same row re-measured / perturbed (same tree type,
                          same position in the sequence, values nudged)

    uv run --no-project --with pandas python leaves/structure.py
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).parent / "leaves.csv"
df = pd.read_csv(CSV, names=["height", "width", "type"], skiprows=1)
types = df["type"].to_numpy()
n = len(df)

# ---------- A. exact repeats ------------------------------------------------
print("=== A. Exact repeats ===")
dup = df.duplicated().sum()
print(f"  {dup} of {n} rows are an exact copy of a row already seen")
first_repeat = int(df[df.duplicated()].index[0])
print(f"  first exact repeat at file row {first_repeat + 2}: "
      f"{tuple(df.iloc[first_repeat])} — identical to file row "
      f"{df.iloc[:first_repeat].index[(df.iloc[:first_repeat] == df.iloc[first_repeat]).all(axis=1)][0] + 2}")

# ---------- B. repeated sequences ------------------------------------------
print("\n=== B. Is the whole file a cycle? (type-sequence autocorrelation) ===")
for lag in range(1, 40):
    agree = (types[lag:] == types[:-lag]).mean()
    if agree > 0.9:
        print(f"  lag {lag:>2}: type matches at that offset in {agree:.0%} of positions  <-- period")
best = max(range(1, 40), key=lambda L: (types[L:] == types[:-L]).mean())
print(f"  best lag under 40: {best} "
      f"({(types[best:] == types[:-best]).mean():.0%} agreement — 33% would be chance)")

# ---------- C. contiguous exact-run detection ------------------------------
print("\n=== C. Longest run of rows that repeats verbatim elsewhere ===")
runs = []
for L in range(3, 40):  # candidate run lengths
    seen = {}
    for i in range(n - L):
        key = tuple(map(tuple, df.iloc[i:i + L].round(6).to_numpy()))
        if key in seen:
            runs.append((L, seen[key] + 2, i + 2))
        else:
            seen[key] = i
if runs:
    longest = max(runs, key=lambda r: r[0])
    for L, a, b in sorted(set(runs), key=lambda r: -r[0])[:5]:
        print(f"  {L}-row run at file rows {a}–{a + L - 1} reappears verbatim at rows {b}–{b + L - 1}")
else:
    print("  none")

# ---------- D. jittered repeats --------------------------------------------
print("\n=== D. Jittered repeats: same sequence, values nudged ===")


def dp(s):
    s = str(s)
    return len(s.split(".")[1]) if "." in s else 0


raw = CSV.read_text().splitlines()[1:]
prec = [max(dp(a.split(",")[0]), dp(a.split(",")[1])) for a in raw if a.strip()]
hi = [i for i, p in enumerate(prec) if p >= 5]
lo = [i for i, p in enumerate(prec) if p <= 2]
print(f"  rows with >=5 decimal places: n={len(hi)} (file rows {min(hi) + 2}–{max(hi) + 2})")
print(f"  rows with <=2 decimal places: n={len(lo)} (file rows {min(lo) + 2}–{max(lo) + 2})")

# align the high-precision block against the low-precision block that precedes it
lo_start, hi_start = min(lo), min(hi)
span = min(len(lo), len(hi), max(hi) - min(hi) + 1, len(df) - hi_start)
seg_lo = df.iloc[lo_start:lo_start + (hi_start - lo_start)]
seg_hi = df.iloc[hi_start:hi_start + len(seg_lo)]
k = len(seg_lo)
same_type = (seg_lo["type"].to_numpy() == seg_hi["type"].to_numpy()).mean()
dh = (seg_hi["height"].to_numpy() - seg_lo["height"].to_numpy())
dw = (seg_hi["width"].to_numpy() - seg_lo["width"].to_numpy())
print(f"\n  comparing file rows {lo_start + 2}–{lo_start + k} (low precision)")
print(f"       with file rows {hi_start + 2}–{hi_start + k} (high precision):")
print(f"    same tree type in the same position: {same_type:.0%}")
print(f"    Δheight: mean {dh.mean():+.3f}  max |Δ| {abs(dh).max():.2f}")
print(f"    Δwidth : mean {dw.mean():+.3f}  max |Δ| {abs(dw).max():.2f}")
print("  first 5 pairs (height, width, type):")
for i in range(5):
    a, b = seg_lo.iloc[i], seg_hi.iloc[i]
    print(f"    {a['height']:>8.3g}, {a['width']:>8.3g}, {a['type']:<7}"
          f"  ->   {b['height']:>9.5f}, {b['width']:>9.5f}, {b['type']}")

# ---------- D1b. which low-precision rows does each high-precision row copy? --
print("\n  for every high-precision row, the nearest low-precision row (±2 cm):")
lo_df = df.iloc[[i for i in lo]]
block1 = df.iloc[lo_start:lo_start + (hi_start - lo_start)]  # rows 2-101
matches, from_block1, unexplained = 0, 0, []
for i in hi:
    h, w, t = df.iloc[i][["height", "width", "type"]]
    twin = lambda d: len(d[(abs(d["height"] - h) < 0.6) & (abs(d["width"] - w) < 0.6)
                           & (d["type"] == t)]) > 0
    if twin(lo_df):
        matches += 1
        from_block1 += twin(block1)
    else:
        unexplained.append(i)
print(f"    {matches} of {len(hi)} high-precision rows have a low-precision twin "
      f"within 0.6 cm and the same type")
print(f"    of those, {from_block1} match a row in block 1 (file rows 2–101) specifically")
print(f"    unexplained: {len(unexplained)} rows "
      f"(file rows {[i + 2 for i in unexplained][:12]}{'…' if len(unexplained) > 12 else ''})")

# ---------- D2. and the third block? ---------------------------------------
print("\n  third block (file rows 304 onward, all 1 dp) vs block 1:")
seg3 = df.iloc[303:]
seg3 = seg3.reset_index(drop=True)
k = min(len(seg3), 100)
same3 = (seg3["type"].to_numpy()[:k] == df["type"].to_numpy()[:k]).mean()
d3h = seg3["height"].to_numpy()[:k] - df["height"].to_numpy()[:k]
print(f"    same tree type in the same position: {same3:.0%}")
print(f"    Δheight: mean {d3h.mean():+.3f}  max |Δ| {abs(d3h).max():.2f}")
print(f"    rows 304+ n={len(seg3)} vs block-1 n=100 -> "
      f"{'a longer, differently-sampled set, not a copy' if same3 < 0.6 else 'another copy'}")

# ---------- E. how much real information is here? --------------------------
print("\n=== E. Effective sample size ===")
print(f"  rows claimed:                 {n}")
print(f"  unique (height,width,type):   {len(df.drop_duplicates())}")
def distinct(step):
    """Distinct leaves after snapping both dimensions to a `step` cm grid."""
    grid = pd.DataFrame({"h": (df.height / step).round() * step,
                         "w": (df.width / step).round() * step,
                         "type": df.type})
    return len(grid.drop_duplicates())


print(f"  unique rounded to 0.5 cm:     {distinct(0.5)}")
print(f"  unique rounded to 1 cm:       {distinct(1)}")
print(f"  unique rounded to 2 cm:       {distinct(2)}")
print(f"  minus the duplicated block (rows 102–200): {n - 202} rows of genuinely separate origin")
