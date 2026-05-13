import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from score import score_rda, compute_pair_deltas, nutrient_breakdown, KEY_NUTRIENTS
 
FIGURES_DIR = "outputs/figures"
os.makedirs(FIGURES_DIR, exist_ok=True)
 
PALETTE = {
    "ancient": "#C47C2B",   # warm ochre
    "modern":  "#3A7CA5",   # steel blue
    "bg":      "#FAFAF7",
    "grid":    "#E8E8E0",
    "text":    "#1A1A1A",
}
 
 
def _save(fig, name: str):
    path = os.path.join(FIGURES_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=PALETTE["bg"])
    print(f"Saved: {path}")
    plt.close(fig)
 
 
# ── 1. Overall score comparison (bar chart) ──────────────────────────────────
def plot_overall_scores(df: pd.DataFrame):
    scored, _ = score_rda(df)
    deltas = compute_pair_deltas(df).sort_values("ancient_score", ascending=True)
 
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
 
    y = np.arange(len(deltas))
    bar_w = 0.38
 
    ax.barh(y + bar_w/2, deltas["ancient_score"], bar_w,
            color=PALETTE["ancient"], label="Ancient", alpha=0.92)
    ax.barh(y - bar_w/2, deltas["modern_score"],  bar_w,
            color=PALETTE["modern"],  label="Modern",  alpha=0.92)
 
    ax.set_yticks(y)
    ax.set_yticklabels(deltas["pair"], fontsize=9)
    ax.set_xlabel("Micronutrient Density Score (mean % RDA per 100g)", fontsize=10)
    ax.set_title("Ancient vs Modern Food: Micronutrient Density Score",
                 fontsize=13, fontweight="bold", pad=14)
    ax.legend(handles=[
        mpatches.Patch(color=PALETTE["ancient"], label="Ancient"),
        mpatches.Patch(color=PALETTE["modern"],  label="Modern"),
    ])
    ax.grid(axis="x", color=PALETTE["grid"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
 
    _save(fig, "01_overall_scores.png")
 
 
# ── 2. Delta plot (which ancient foods gain most over modern) ─────────────────
def plot_deltas(df: pd.DataFrame):
    deltas = compute_pair_deltas(df).sort_values("delta")
 
    colors = [PALETTE["ancient"] if d > 0 else PALETTE["modern"]
              for d in deltas["delta"]]
 
    fig, ax = plt.subplots(figsize=(9, 6), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
 
    bars = ax.barh(deltas["pair"], deltas["delta"], color=colors, alpha=0.9)
    ax.axvline(0, color=PALETTE["text"], linewidth=0.9, linestyle="--", alpha=0.5)
 
    for bar, val in zip(bars, deltas["delta"]):
        ax.text(val + (0.3 if val >= 0 else -0.3), bar.get_y() + bar.get_height()/2,
                f"{val:+.1f}", va="center", ha="left" if val >= 0 else "right",
                fontsize=8, color=PALETTE["text"])
 
    ax.set_xlabel("Score Difference (Ancient − Modern)", fontsize=10)
    ax.set_title("Micronutrient Density Advantage by Food Pair\n"
                 "Positive = ancient food scores higher",
                 fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x", color=PALETTE["grid"], linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
 
    _save(fig, "02_delta_comparison.png")
 
 
# ── 3. Radar chart for a single food pair ────────────────────────────────────
def plot_radar(df: pd.DataFrame, pair_name: str):
    breakdown = nutrient_breakdown(df, pair_name)
    if breakdown.empty:
        print(f"No data for pair: {pair_name}")
        return
 
    nutrients = breakdown["nutrient"].tolist()
    ancient_vals = breakdown["ancient_pct"].tolist()
    modern_vals  = breakdown["modern_pct"].tolist()
 
    N = len(nutrients)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]   # close the polygon
    ancient_vals += ancient_vals[:1]
    modern_vals  += modern_vals[:1]
 
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"polar": True},
                           facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
 
    ax.plot(angles, ancient_vals, color=PALETTE["ancient"], linewidth=2, label="Ancient")
    ax.fill(angles, ancient_vals, color=PALETTE["ancient"], alpha=0.25)
    ax.plot(angles, modern_vals,  color=PALETTE["modern"],  linewidth=2, label="Modern")
    ax.fill(angles, modern_vals,  color=PALETTE["modern"],  alpha=0.20)
 
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(nutrients, fontsize=8)
    ax.set_yticklabels([])
    ax.set_title(f"Nutrient Profile: {pair_name.title()}\n(% RDA per 100g)",
                 fontsize=11, fontweight="bold", pad=18)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
 
    safe_name = pair_name.replace(" ", "_").replace(",", "")
    _save(fig, f"03_radar_{safe_name}.png")
 
 
# ── 4. Heatmap of % RDA across all foods × nutrients ─────────────────────────
def plot_heatmap(df: pd.DataFrame):
    scored, score_cols = score_rda(df)
 
    pivot_cols = [c for c in score_cols if c in scored.columns]
    pivot = scored.set_index("food")[pivot_cols].copy()
    pivot.columns = [c.replace("_pct_rda", "") for c in pivot.columns]
 
    # Sort rows: ancient first, then modern
    era_order = scored.sort_values("era", ascending=False)["food"].tolist()
    pivot = pivot.loc[[f for f in era_order if f in pivot.index]]
 
    fig, ax = plt.subplots(figsize=(16, 10), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
 
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrBr", vmin=0, vmax=100)
    plt.colorbar(im, ax=ax, label="% RDA per 100g", shrink=0.6)
 
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
 
    # Annotate era boundary
    n_ancient = scored[scored["era"] == "ancient"].shape[0]
    ax.axhline(n_ancient - 0.5, color=PALETTE["text"], linewidth=1.5, linestyle="--")
    ax.text(-0.7, n_ancient / 2 - 0.5, "Ancient", va="center", ha="right",
            fontsize=9, color=PALETTE["ancient"], fontweight="bold", rotation=90)
    ax.text(-0.7, n_ancient + (len(pivot) - n_ancient) / 2, "Modern",
            va="center", ha="right", fontsize=9, color=PALETTE["modern"],
            fontweight="bold", rotation=90)
 
    ax.set_title("Nutrient Density Heatmap — All Foods (% RDA per 100g)",
                 fontsize=13, fontweight="bold", pad=14)
 
    _save(fig, "04_heatmap.png")
 
 
# ── 5. Era-level summary box plots ───────────────────────────────────────────
def plot_era_boxplots(df: pd.DataFrame):
    scored, _ = score_rda(df)
 
    fig, ax = plt.subplots(figsize=(6, 5), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
 
    ancient_scores = scored[scored["era"] == "ancient"]["micro_density_score"].dropna()
    modern_scores  = scored[scored["era"] == "modern"]["micro_density_score"].dropna()
 
    bp = ax.boxplot([ancient_scores, modern_scores],
                    labels=["Ancient foods", "Modern equivalents"],
                    patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2})
 
    bp["boxes"][0].set_facecolor(PALETTE["ancient"])
    bp["boxes"][1].set_facecolor(PALETTE["modern"])
    for patch in bp["boxes"]:
        patch.set_alpha(0.85)
 
    ax.set_ylabel("Micronutrient Density Score", fontsize=10)
    ax.set_title("Score Distribution by Era", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="y", color=PALETTE["grid"], linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
 
    _save(fig, "05_era_boxplots.png")
 
 
def run_all(df: pd.DataFrame, radar_pairs: list[str] = None):
    """Generate all charts. Optionally pass a list of pair names for radar plots."""
    print("\n── Generating charts ──")
    plot_overall_scores(df)
    plot_deltas(df)
    plot_heatmap(df)
    plot_era_boxplots(df)
    if radar_pairs:
        for pair in radar_pairs:
            plot_radar(df, pair)
    print("Done.")