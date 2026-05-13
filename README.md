# Nutritional Diversity: Ancient vs Modern Foods

Compares the micronutrient density (% RDA per 100g) of hunter-gatherer foods
against their closest modern supermarket equivalents, using the USDA FoodData
Central API.

## Setup

```bash
pip install requests pandas matplotlib numpy
```

## Run

```bash
# First run — fetches from USDA API and caches to data/nutrients_raw.csv
python main.py

# Force re-fetch (e.g. after editing FOOD_PAIRS or KEY_NUTRIENTS)
python main.py --refresh
```

## Project Structure

```
.
├── main.py                  # Entry point
├── src/
│   ├── fetch.py             # USDA API calls + food pair definitions
│   ├── score.py             # % RDA scoring + analysis functions
│   └── visualize.py         # All chart generation
├── data/
│   ├── nutrients_raw.csv    # Cached raw API data (auto-created)
│   └── nutrients_scored.csv # Scored output (auto-created)
└── outputs/
    └── figures/             # All PNG charts (auto-created)
        ├── 01_overall_scores.png
        ├── 02_delta_comparison.png
        ├── 03_radar_<pair>.png
        ├── 04_heatmap.png
        └── 05_era_boxplots.png
```

## Scoring Method

Each food is scored as:

**Micronutrient Density Score = mean( min(nutrient_amount / RDA × 100, 100) )**

...across 21 tracked micronutrients (excluding fat and protein, which are tracked
separately as macro scores). Capping each nutrient at 100% prevents single
outliers (e.g. extremely high vitamin K in nettles) from dominating the score.

## Customisation

- **Add/remove foods**: Edit `FOOD_PAIRS` in `src/fetch.py`
- **Change nutrients**: Edit `KEY_NUTRIENTS` and `RDA` in `src/fetch.py`
- **Different RDA values** (e.g. for children or women): Edit `RDA` in `src/fetch.py`
- **Radar charts for specific pairs**: Pass `radar_pairs=["venison", ...]` in `main.py`