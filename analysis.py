"""Step 2: Analyze sales and customer behavior."""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

def main():
    sales_file = OUTPUT_DIR / "valid_sales.csv"
    customer_file = OUTPUT_DIR / "customer_sales.csv"
    if not sales_file.exists() or not customer_file.exists():
        raise FileNotFoundError("Run cleaning.py first.")

    sales = pd.read_csv(sales_file, parse_dates=["InvoiceDate"])
    customers = pd.read_csv(customer_file, parse_dates=["InvoiceDate"])

    sales["LineTotal"] = pd.to_numeric(sales["LineTotal"], errors="coerce")
    customers["LineTotal"] = pd.to_numeric(customers["LineTotal"], errors="coerce")

    revenue = sales["LineTotal"].sum()
    orders = sales["InvoiceNo"].nunique()
    customer_count = customers["CustomerID"].nunique()
    product_count = sales["StockCode"].nunique()

    monthly = sales.assign(Month=sales["InvoiceDate"].dt.to_period("M").astype(str)) \
                   .groupby("Month", as_index=False)["LineTotal"].sum()
    monthly.rename(columns={"LineTotal": "Revenue"}, inplace=True)
    monthly.to_csv(OUTPUT_DIR / "monthly_revenue.csv", index=False)

    top_products = sales.groupby("Description", dropna=True)["LineTotal"].sum() \
                        .sort_values(ascending=False).head(10).reset_index()
    top_products.rename(columns={"LineTotal": "Revenue"}, inplace=True)
    top_products.to_csv(OUTPUT_DIR / "top_products.csv", index=False)

    country = sales.groupby("Country")["LineTotal"].sum().sort_values(ascending=False) \
                   .head(10).reset_index()
    country.rename(columns={"LineTotal": "Revenue"}, inplace=True)
    country.to_csv(OUTPUT_DIR / "top_countries.csv", index=False)

    rfm = customers.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (customers["InvoiceDate"].max().normalize() + pd.Timedelta(days=1) - x.max().normalize()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("LineTotal", "sum")
    ).reset_index()
    rfm.to_csv(OUTPUT_DIR / "customer_rfm.csv", index=False)

    repeat_rate = (rfm["Frequency"] >= 2).mean() * 100 if not rfm.empty else 0
    top_product = top_products.iloc[0]["Description"] if not top_products.empty else "N/A"
    top_country = country.iloc[0]["Country"] if not country.empty else "N/A"

    report = f"""CUSTOMER BEHAVIOR ANALYSIS — ANALYSIS SUMMARY

OVERALL METRICS
Total revenue: £{revenue:,.2f}
Distinct orders: {orders:,}
Customers with known IDs: {customer_count:,}
Unique products: {product_count:,}
Repeat customer rate: {repeat_rate:.1f}%

KEY FINDINGS
Top product by revenue: {top_product}
Top country by revenue: {top_country}
Monthly revenue table: outputs/monthly_revenue.csv
Top products table: outputs/top_products.csv
Top countries table: outputs/top_countries.csv
Customer RFM table: outputs/customer_rfm.csv

NOTES
Revenue = Quantity × UnitPrice.
Sales analysis excludes cancelled invoices and rows with invalid dates,
non-positive quantity, or non-positive unit price.
Customer-level analysis excludes transactions with missing customer IDs.
Currency is shown as GBP (£); verify currency with the dataset source before external use.
"""
    (OUTPUT_DIR / "analysis_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"Analysis files saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
