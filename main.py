"""
main.py — Entry point for the nutritional diversity analysis
Run this file to fetch data, score it, and generate all visualizations.

Usage:
    python main.py             # uses cache if available
    python main.py --refresh   # force re-fetch from USDA API
"""

import sys
import pandas as pd
from fetch import fetch_all_foods
from score import score_rda, compute_pair_deltas, era_summary, top_nutrients_by_era
from visualize import run_all


def main():
    force_refresh = "--refresh" in sys.argv

    # ── 1. Fetch (or load from cache) ────────────────────────────────────────
    print("=" * 55)
    print("  Nutritional Diversity: Ancient vs Modern Foods")
    print("=" * 55)
    df = fetch_all_foods(force_refresh=force_refresh)
    print(f"\nLoaded {len(df)} food records ({df['era'].value_counts().to_dict()})")

    # ── 2. Score ──────────────────────────────────────────────────────────────
    scored_df, _ = score_rda(df)

    # ── 3. Print summary tables ───────────────────────────────────────────────
    print("\n── Era Summary ──────────────────────────────────────")
    print(era_summary(df).to_string())

    print("\n── Pair-level Deltas (top 5 ancient wins) ───────────")
    deltas = compute_pair_deltas(df)
    print(deltas.head().to_string(index=False))

    print("\n── Pair-level Deltas (top 5 modern wins) ────────────")
    print(deltas.tail().to_string(index=False))

    print("\n── Top nutrients by era ──────────────────────────────")
    top = top_nutrients_by_era(df, top_n=5)
    for era, nutrients in top.items():
        print(f"\n  {era.upper()}:")
        for name, score in nutrients:
            print(f"    {name:<40} {score:.1f}% RDA avg")

    # ── 4. Save scored data ───────────────────────────────────────────────────
    scored_df.to_csv("data/nutrients_scored.csv", index=False)
    print("\nScored data saved to data/nutrients_scored.csv")

    # ── 5. Generate all charts ────────────────────────────────────────────────
    radar_pairs = ["venison", "wild salmon", "dandelion greens", "wild blueberries"]
    run_all(df, radar_pairs=radar_pairs)


if __name__ == "__main__":
    main()