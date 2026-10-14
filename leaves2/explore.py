"""Exploratory data analysis of leaves2/leaves.csv.

Analyzes leaf counts, generates scatter plot (PNG and ASCII),
and inspects anomalies, duplicates, and precision patterns.
"""

from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

HERE = Path(__file__).parent
CSV = HERE / "leaves.csv"

def main():
    df = pd.read_csv(CSV)
    df.columns = ["height", "width", "type"]
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Missing values: {df.isna().sum().to_dict()}")

    # Leaf counts per tree type
    counts = df["type"].value_counts()
    print("\n--- Leaf counts per tree type ---")
    for tree_type, cnt in counts.items():
        pct = cnt / len(df) * 100
        print(f"  {tree_type:<10}: {cnt:>4} leaves ({pct:5.1f}%)")

    # Summary statistics
    print("\n--- Summary statistics by type ---")
    stats = df.groupby("type")[["height", "width"]].describe().round(2)
    print(stats.to_string())

    # Scatter plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    palette = {"maple": "#e6550d", "walnut": "#31a354", "cherry": "#756bb1"}
    markers = {"maple": "o", "walnut": "s", "cherry": "^"}

    for tree_type, group in df.groupby("type"):
        ax.scatter(
            group["height"],
            group["width"],
            label=f"{tree_type} (n={len(group)})",
            color=palette.get(tree_type, "blue"),
            marker=markers.get(tree_type, "o"),
            alpha=0.6,
            edgecolors="none",
            s=30,
        )

    # Reference diagonal (width = height)
    max_val = max(df["height"].max(), df["width"].max()) * 1.05
    ax.plot([0, max_val], [0, max_val], "k--", alpha=0.4, label="width = height (1:1)")

    ax.set_title("Leaf Dimensions: Height vs Width by Tree Type", fontsize=13, fontweight="bold")
    ax.set_xlabel("Height (cm)", fontsize=11)
    ax.set_ylabel("Width (cm)", fontsize=11)
    ax.legend(frameon=True, loc="upper left")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    out_img = HERE / "height_vs_width.png"
    fig.savefig(out_img)
    plt.close(fig)
    print(f"\nSaved scatter plot to {out_img}")

    # ASCII scatter plot
    print("\n--- ASCII Scatter Plot (Terminal Overview) ---")
    print("Labels: m = maple, w = walnut, c = cherry, * = overlap")
    cols, rows = 60, 20
    grid = [[" "] * cols for _ in range(rows)]
    h_min, h_max = df["height"].min(), df["height"].max()
    w_min, w_max = df["width"].min(), df["width"].max()

    type_char = {"maple": "m", "walnut": "w", "cherry": "c"}

    for _, row in df.iterrows():
        c_idx = int((row["height"] - h_min) / (h_max - h_min) * (cols - 1))
        r_idx = int((row["width"] - w_min) / (w_max - w_min) * (rows - 1))
        r_idx = rows - 1 - r_idx  # invert Y for top-down terminal
        current = grid[r_idx][c_idx]
        char = type_char.get(row["type"], "?")
        if current == " ":
            grid[r_idx][c_idx] = char
        elif current != char:
            grid[r_idx][c_idx] = "*"

    for r in range(rows):
        w_val = w_max - r * (w_max - w_min) / (rows - 1)
        line = "".join(grid[r])
        print(f"{w_val:5.1f} |{line}|")
    print("      +" + "-" * cols + "+")
    print(f"       {h_min:<6.1f}" + " " * (cols - 14) + f"{h_max:>6.1f} (Height)")

    # Anomalies / Unusual Findings
    print("\n=== UNUSUAL OBSERVATIONS & DATA QUALITY ISSUES ===")

    # 1. Exact Duplicates
    dup_mask = df.duplicated()
    dup_count = dup_mask.sum()
    unique_count = len(df.drop_duplicates())
    print(f"\n1. Exact Duplicates:")
    print(f"   - Total rows: {len(df)}")
    print(f"   - Unique rows: {unique_count}")
    print(f"   - Duplicate rows: {dup_count} ({(dup_count / len(df) * 100):.1f}%)")

    # Group duplicate counts
    dup_freq = df.groupby(["height", "width", "type"]).size().reset_index(name="count")
    multi = dup_freq[dup_freq["count"] > 1].sort_values("count", ascending=False)
    print(f"   - {len(multi)} distinct patterns appear multiple times (up to {multi['count'].max()} times each).")
    print("   - Top repeated rows:")
    print(multi.head(5).to_string(index=False))

    # 2. Precision divergence
    raw_lines = [ln.strip().split(",") for ln in CSV.read_text().splitlines()[1:] if ln.strip()]
    def get_dp(val):
        return len(val.split(".")[1]) if "." in val else 0
    precisions = [max(get_dp(r[0]), get_dp(r[1])) for r in raw_lines]
    low_prec = [i for i, p in enumerate(precisions) if p <= 2]
    high_prec = [i for i, p in enumerate(precisions) if p >= 5]
    print(f"\n2. Measurement Precision Inconsistency:")
    print(f"   - Low precision rows (1-2 decimal places): {len(low_prec)} rows (e.g. rows {min(low_prec)+2}..{max(low_prec)+2})")
    print(f"   - High precision rows (>=5 decimal places): {len(high_prec)} rows (e.g. rows {min(high_prec)+2}..{max(high_prec)+2})")

    # 3. Dimensional anomalies
    wide = df[df["width"] > df["height"]]
    print(f"\n3. Dimension Anomalies (Width > Height):")
    print(f"   - {len(wide)} leaves are wider than they are tall ({len(wide)/len(df)*100:.1f}%).")
    print(f"   - Breakdown by type: {dict(wide['type'].value_counts())}")

    # 4. Outliers & Clusters
    print(f"\n4. Clustering & Outliers:")
    cherry_wide = df[(df["type"] == "cherry") & (df["width"] > 12)]
    print(f"   - Extremely wide cherry leaves (width > 12 cm): {len(cherry_wide)} row(s)")
    if len(cherry_wide) > 0:
        print(cherry_wide.to_string())

    maple_bimodal = df[df["type"] == "maple"]
    print(f"   - Maple distribution: bimodal split at ~18 cm height:")
    print(f"     * Small maples (<= 18 cm): {len(maple_bimodal[maple_bimodal['height'] <= 18])}")
    print(f"     * Large maples (> 18 cm):  {len(maple_bimodal[maple_bimodal['height'] > 18])}")

if __name__ == "__main__":
    main()
