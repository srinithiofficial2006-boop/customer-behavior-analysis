"""Step 3: Create charts from the analysis output files."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
CHART_DIR = OUTPUT_DIR / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

def save_chart(filename):
    plt.tight_layout()
    plt.savefig(CHART_DIR / filename, dpi=160, bbox_inches="tight")
    plt.close()

def main():
    required = ["monthly_revenue.csv", "top_products.csv", "top_countries.csv", "customer_rfm.csv"]
    missing = [f for f in required if not (OUTPUT_DIR / f).exists()]
    if missing:
        raise FileNotFoundError(f"Run cleaning.py and analysis.py first. Missing: {missing}")

    monthly = pd.read_csv(OUTPUT_DIR / "monthly_revenue.csv")
    products = pd.read_csv(OUTPUT_DIR / "top_products.csv")
    countries = pd.read_csv(OUTPUT_DIR / "top_countries.csv")
    rfm = pd.read_csv(OUTPUT_DIR / "customer_rfm.csv")

    plt.figure(figsize=(10, 5))
    plt.plot(monthly["Month"], monthly["Revenue"], marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Revenue (£)")
    plt.xticks(rotation=45, ha="right")
    save_chart("monthly_revenue.png")

    plt.figure(figsize=(10, 6))
    products = products.sort_values("Revenue")
    plt.barh(products["Description"].fillna("Unknown").astype(str), products["Revenue"])
    plt.title("Top 10 Products by Revenue")
    plt.xlabel("Revenue (£)")
    save_chart("top_products.png")

    plt.figure(figsize=(10, 6))
    countries = countries.sort_values("Revenue")
    plt.barh(countries["Country"].astype(str), countries["Revenue"])
    plt.title("Top 10 Countries by Revenue")
    plt.xlabel("Revenue (£)")
    save_chart("top_countries.png")

    plt.figure(figsize=(9, 5))
    plt.hist(rfm["Monetary"].clip(upper=rfm["Monetary"].quantile(0.99)), bins=30)
    plt.title("Customer Spending Distribution (up to 99th percentile)")
    plt.xlabel("Customer Revenue (£)")
    plt.ylabel("Number of Customers")
    save_chart("customer_spending.png")

    print(f"Charts saved to: {CHART_DIR}")

if __name__ == "__main__":
    main()
