"""Step 1: Clean the Online Retail dataset."""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR /"data"/ "Online Retail.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE.name}. Put it in the same folder as cleaning.py."
        )

    df = pd.read_excel(INPUT_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    required = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country"
    ]
    missing_columns = [col for col in required if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    original_rows = len(df)
    duplicate_count = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = df["CustomerID"].astype("string").str.replace(r"\.0$", "", regex=True)
    df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
    df["Description"] = df["Description"].astype("string").str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()

    # Revenue for each transaction line.
    df["LineTotal"] = df["Quantity"] * df["UnitPrice"]
    df["IsCancelled"] = df["InvoiceNo"].str.startswith("C", na=False)

    # Keep all cleaned rows in cleaned_transactions.csv.
    cleaned_path = OUTPUT_DIR / "cleaned_transactions.csv"
    df.to_csv(cleaned_path, index=False)

    # Sales dataset excludes cancellations and invalid/non-positive sales lines.
    sales = df[
        df["InvoiceDate"].notna()
        & df["Quantity"].gt(0)
        & df["UnitPrice"].gt(0)
        & ~df["IsCancelled"]
    ].copy()
    sales.to_csv(OUTPUT_DIR / "valid_sales.csv", index=False)

    # Customer analysis needs a known CustomerID.
    customer_sales = sales[
        sales["CustomerID"].notna()
        & (df.loc[sales.index, "CustomerID"] != "")
        & (sales["CustomerID"].str.lower() != "nan")
    ].copy()
    customer_sales.to_csv(OUTPUT_DIR / "customer_sales.csv", index=False)

    summary = pd.DataFrame({
        "Metric": [
            "Original rows", "Exact duplicates removed", "Rows after deduplication",
            "Missing InvoiceDate", "Missing CustomerID",
            "Valid sales rows", "Rows used for customer analysis"
        ],
        "Value": [
            original_rows, duplicate_count, len(df),
            int(df["InvoiceDate"].isna().sum()),
            int(df["CustomerID"].isna().sum() | (df["CustomerID"].str.lower() == "nan").sum()),
            len(sales), len(customer_sales)
        ]
    })
    summary.to_csv(OUTPUT_DIR / "cleaning_summary.csv", index=False)

    print("Data cleaning completed.")
    print(summary.to_string(index=False))
    print(f"\nSaved cleaned data and summaries in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
