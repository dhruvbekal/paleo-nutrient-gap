import pandas as pd
import numpy as np
from fetch import KEY_NUTRIENTS,RDA



def score_rda(df:pd.DataFrame) -> pd.DataFrame:
    """
    Out of 100g, this calculates how much '%' of the RDA for each nutrient is 
    covered, along with a micronutrient density score (mean '%' RDA across all 
    nutrients). > 100 is capped at 100 to prevent domination of a single nutrient
    """
    df = df.copy()
    score_cols = []
    for nutrient in KEY_NUTRIENTS:
        if nutrient not in df.columns:
            continue
        rda_val = RDA.get(nutrient)
        if rda_val is None or rda_val == 0:
            continue
        col = f"{nutrient}_pct_rda"
        # limit individual nutrient contribution to 100% to prevent skewing
        df[col] = (df[nutrient] / rda_val * 100).clip(upper=100)
        score_cols.append(col)

    # composite score = mean % RDA across all micronutrients (excl. macro fat)
    micro_cols = [
        c for c in score_cols
        if "Total lipid" not in c and "Protein" not in c
    ]
    df["micro_density_score"] = df[micro_cols].mean(axis=1)

    macro_cols = [c for c in score_cols if c not in micro_cols]
    df["macro_density_score"] = df[macro_cols].mean(axis=1)

    return df, score_cols


def compute_pair_deltas(df:pd.DataFrame) -> pd.DataFrame:
    """
    For each food pair (ancient vs modern), compute the absolute and relative 
    difference in micro_density_score. Returns a summary DataFrame with 1 row
    per pair
    """
    scored, _ = score_rda(df)
    ancient = scored[scored["era"] == "ancient"].set_index("pair")
    modern  = scored[scored["era"] == "modern"].set_index("pair")
 
    pairs = ancient.index.intersection(modern.index)
 
    rows = []
    for pair in pairs:
        a_score = ancient.loc[pair, "micro_density_score"]
        m_score = modern.loc[pair, "micro_density_score"]
        delta   = a_score - m_score
        pct_diff = (delta / m_score * 100) if m_score > 0 else np.nan
        rows.append({
            "pair":           pair,
            "ancient_food":   ancient.loc[pair, "food"],
            "modern_food":    modern.loc[pair, "food"],
            "ancient_score":  round(a_score, 2),
            "modern_score":   round(m_score, 2),
            "delta":          round(delta, 2),
            "pct_difference": round(pct_diff, 1),
            "winner":         "ancient" if delta > 0 else "modern",
        })
 
    summary = pd.DataFrame(rows).sort_values("delta", ascending=False)
    return summary
 
 
def nutrient_breakdown(df: pd.DataFrame, pair_name: str) -> pd.DataFrame:
    """
    For a single food pair, return a side-by-side % RDA comparison
    for every tracked nutrient.
    """
    scored, score_cols = score_rda(df)
    pair_df = scored[scored["pair"] == pair_name]
 
    rows = []
    for nutrient in KEY_NUTRIENTS:
        col = f"{nutrient}_pct_rda"
        if col not in scored.columns:
            continue
        ancient_row = pair_df[pair_df["era"] == "ancient"]
        modern_row  = pair_df[pair_df["era"] == "modern"]
        rows.append({
            "nutrient":      nutrient,
            "ancient_pct":   ancient_row[col].values[0] if len(ancient_row) else np.nan,
            "modern_pct":    modern_row[col].values[0]  if len(modern_row)  else np.nan,
        })
 
    return pd.DataFrame(rows).dropna()
 
 
def top_nutrients_by_era(df: pd.DataFrame, top_n: int = 5) -> dict:
    """
    Returns the top N nutrients (by mean % RDA) for ancient and modern foods
    separately.
    """
    scored, score_cols = score_rda(df)
    result = {}
    for era in ["ancient", "modern"]:
        era_df = scored[scored["era"] == era]
        means = {
            col.replace("_pct_rda", ""): era_df[col].mean()
            for col in score_cols
        }
        top = sorted(means.items(), key=lambda x: x[1], reverse=True)[:top_n]
        result[era] = top
    return result
 
 
def era_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    High-level summary: mean micro_density_score by era, and count of pairs
    where ancient outperforms modern.
    """
    scored, _ = score_rda(df)
    summary = scored.groupby("era")["micro_density_score"].agg(
        mean_score="mean",
        median_score="median",
        std_score="std",
        n_foods="count"
    ).round(2)
    return summary
 


