"""Which rows in leaves.csv are genuinely odd, not just spread out?

Uses per-type robust z-scores on both dimensions (maple varies far more than
cherry, so one pooled threshold buries it), plus distance to each type's centre.

    uv run --no-project --with pandas python leaves/anomalies.py
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).parent / "leaves.csv"
df = pd.read_csv(CSV, names=["height", "width", "type"], skiprows=1)

# --- per-type robust z on each dimension ------------------------------------
z = pd.DataFrame(index=df.index)
for col in ["height", "width"]:
    z["z_" + col] = 0.0
    for t, g in df.groupby("type"):
        med = g[col].median()
        mad = (g[col] - med).abs().median()
        z.loc[g.index, "z_" + col] = (g[col] - med) / (1.4826 * mad)
z["worst"] = z[["z_height", "z_width"]].abs().max(axis=1)

print("=== Most extreme rows relative to their own tree type (top 15) ===")
out = df.join(z).nlargest(15, "worst")
out.insert(0, "file_row", out.index + 2)
print(out.round(2).to_string(index=False))

print("\n=== Odd on BOTH dimensions for its type (|z| > 2.5 each) ===")
weird = z[(z["z_height"].abs() > 2.5) & (z["z_width"].abs() > 2.5)]
if len(weird):
    show = df.loc[weird.index].join(weird[["z_height", "z_width"]].round(1))
    show.insert(0, "file_row", show.index + 2)
    print(show.to_string(index=False))
else:
    print("  none")

# --- distance to each type's centre (units standardised over the whole file) --
gz = (df[["height", "width"]] - df[["height", "width"]].mean()) / df[["height", "width"]].std()
gcent = gz.groupby(df["type"]).mean()
dist = pd.DataFrame({t: ((gz["height"] - gcent.loc[t, "height"]) ** 2
                         + (gz["width"] - gcent.loc[t, "width"]) ** 2) ** 0.5
                     for t in gcent.index})
own = pd.Series([dist.loc[i, df.loc[i, "type"]] for i in dist.index], index=dist.index)
other = dist.mask(pd.get_dummies(df["type"]).astype(bool)).min(axis=1)
margin = other - own
print(f"\n=== Rows closer to another type's centre than to their own: "
      f"{int((margin < 0).sum())} of {len(df)} ===")
worst = margin.nsmallest(12)
show = df.loc[worst.index].assign(dist_own=own[worst.index].round(2),
                                  dist_other=other[worst.index].round(2))
show.insert(0, "file_row", show.index + 2)
print(show.round(2).to_string(index=False))

# --- the large-maple cluster -------------------------------------------------
small = df[(df["type"] == "maple") & (df["height"] <= 18)]
big = df[(df["type"] == "maple") & (df["height"] > 18)]
print(f"\n=== Maple splits into two size groups ===")
print(f"  <=18 cm tall: n={len(small):>3}  height {small.height.min():.1f}–{small.height.max():.1f}"
      f"  width/height {small.width.mean() / small.height.mean():.2f}")
print(f"   >18 cm tall: n={len(big):>3}  height {big.height.min():.1f}–{big.height.max():.1f}"
      f"  width/height {big.width.mean() / big.height.mean():.2f}")
print(f"  the large group is entirely maple — no walnut or cherry leaf exceeds "
      f"{df[df.type != 'maple'].height.max():.1f} cm")
print("  large-maple file rows:", ", ".join(str(i + 2) for i in big.index))

# --- cherry leaves as wide as a maple ----------------------------------------
q99 = df[df.type == "cherry"].width.quantile(0.99)
c = df[(df["type"] == "cherry") & (df["width"] > 12)]
print(f"\n=== Cherry leaves wider than 12 cm (99th pct of cherry width = {q99:.1f}) ===")
if len(c):
    show = c.copy()
    show.insert(0, "file_row", show.index + 2)
    print(show.round(2).to_string(index=False))
    print("  → these are maple-sized leaves recorded as cherry.")
else:
    print("  none")
