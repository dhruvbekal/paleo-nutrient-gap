import requests
import pandas as pd
API_KEY = 'BqPseerMeaoP9iPBEmQxg44SOFpFWtaG8ee0nibq'
BASE_URL = 'https://api.nal.usda.gov/fdc/v1'
CACHE_PATH = 'data/nutrients_raw.csv'
game_meats = ["venison", "bison", "elk", "boar", "rabbit", "quail"]
wild_fish = ["salmon, wild", "sardines", "mackerel", "roe"]
foraged_plants = ["dandelion greens", "purslane", "nettles", "wild blueberries", "blackberries", "fiddlehead"]
tubers = ["cassava", "yam", "sweet potato"]
# Ancient foods -> modern equivalent
FOOD_PAIRS = {
    "venison":           "beef, ground, 80% lean",
    "bison":             "beef, ground, 90% lean",
    "wild boar":         "pork, ground",
    "rabbit":            "chicken, breast, raw",
    "elk":               "beef, sirloin, raw",
    "quail":             "chicken, whole, raw",
    "wild salmon":       "salmon, atlantic, farmed",
    "sardines, raw":     "tuna, canned in water",
    "mackerel, raw":     "cod, raw",
    "fish roe":          "shrimp, raw",
    "dandelion greens":  "lettuce, iceberg, raw",
    "purslane, raw":     "cucumber, raw",
    "stinging nettles":  "spinach, raw",
    "wild blueberries":  "blueberries, raw",
    "blackberries, raw": "strawberries, raw",
    "fiddlehead ferns":  "broccoli, raw",
    "cassava, raw":      "white potato, raw",
    "yam, raw":          "sweet potato, raw",
}

# Nutrients to track
KEY_NUTRIENTS = [
    "Protein",
    "Total lipid (fat)",
    "Fiber, total dietary",
    "Iron, Fe",
    "Zinc, Zn",
    "Magnesium, Mg",
    "Calcium, Ca",
    "Potassium, K",
    "Phosphorus, P",
    "Vitamin C, total ascorbic acid",
    "Vitamin A, RAE",
    "Vitamin E (alpha-tocopherol)",
    "Vitamin K (phylloquinone)",
    "Thiamin",
    "Riboflavin",
    "Niacin",
    "Vitamin B-6",
    "Folate, total",
    "Vitamin B-12",
    "Selenium, Se",
    "Manganese, Mn",
    "Copper, Cu",
    "Fatty acids, total omega-3",
]

# Recommended Daily Amount
RDA = {
    "Protein":                          50,     # g
    "Total lipid (fat)":                65,     # g
    "Fiber, total dietary":             28,     # g
    "Iron, Fe":                         18,     # mg
    "Zinc, Zn":                         11,     # mg
    "Magnesium, Mg":                    420,    # mg
    "Calcium, Ca":                      1300,   # mg
    "Potassium, K":                     4700,   # mg
    "Phosphorus, P":                    1250,   # mg
    "Vitamin C, total ascorbic acid":   90,     # mg
    "Vitamin A, RAE":                   900,    # mcg
    "Vitamin E (alpha-tocopherol)":     15,     # mg
    "Vitamin K (phylloquinone)":        120,    # mcg
    "Thiamin":                          1.2,    # mg
    "Riboflavin":                       1.3,    # mg
    "Niacin":                           16,     # mg
    "Vitamin B-6":                      1.7,    # mg
    "Folate, total":                    400,    # mcg
    "Vitamin B-12":                     2.4,    # mcg
    "Selenium, Se":                     55,     # mcg
    "Manganese, Mn":                    2.3,    # mg
    "Copper, Cu":                       0.9,    # mg
    "Fatty acids, total omega-3":       1.6,    # g
}



def get_food_id(query):
    """Searching US FDC for a food with fdcId being the best match"""
    url = f"{BASE_URL}/foods/search"
    params = {"query":query, "api_key":API_KEY, "pageSize":5}
    try:
        response = requests.get(url, params = params, timeout = 10)
        response.raise_for_status()
        data = response.json()
        foods = data.get("foods", [])
        if foods:
            print(f"  ✓ Found '{query}' → {foods[0]['description']}) (id {foods[0]['fdcId']})")
            return foods[0]["fdcId"]
        print(f" x No results for '{query}'")
        return None
    except Exception as e:
        print(f" x Error searching '{query}': {e}")
        return None



def get_nutrients_by_id(fdc_id:int) -> dict:
    """Get nutritional content per 100g for a given fdcId"""
    url = f"{BASE_URL}/food/{fdc_id}"
    params = {"api_key":API_KEY}
    try:
        response = requests.get(url, params = params, timeout = 10)
        response.raise_for_status()
        data = response.json()
        nutrients = {}
        for n in data.get("foodNutrients",[]):
            name = n.get("nutrient",{}).get("name")
            amount = n.get("amount")
            if name and amount is not None:
                nutrients[name] = amount
        return nutrients
    except Exception as e:
        print(f" x Error fetching nutrients for id {fdc_id}: {e}")
        return {}
         


import os
import time
def fetch_all_foods(force_refresh: bool = False) -> pd.DataFrame:
    """
    Fetches nutrients for all ancient/modern food pairs
    Results are cached to CACHE_PATH - set force_refresh=True to re-fetch
    Returns a DataFrame with columns: food, era, pair and a column per nutrient
    """
    if not force_refresh and os.path.exists(CACHE_PATH):
        print(f"Loading cached data from {CACHE_PATH}")
        return pd.read_csv(CACHE_PATH)
    
    os.makedirs("data", exist_ok=True)
    rows = []

    for ancient,modern in FOOD_PAIRS.items():
        for era,query in [("ancient",ancient),("modern",modern)]:
            fdc_id = get_food_id(query)
            time.sleep(0.5)
            if fdc_id is None:
                continue
            raw_nutrients = get_nutrients_by_id(fdc_id)
            time.sleep(0.5)
            row = {
                "food":query,
                "era":era,
                "pair":ancient
            }
            for nutrient in KEY_NUTRIENTS:
                row[nutrient] = raw_nutrients.get(nutrient, None)
            rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(CACHE_PATH,index=False)
    print(f"\nSaved {len(df)} rows to {CACHE_PATH}")
    return df
