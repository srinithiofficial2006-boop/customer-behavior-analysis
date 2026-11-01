"""Optional Step 4: Segment customers using K-Means."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

def main():
    input_file = OUTPUT_DIR / "customer_rfm.csv"
    if not input_file.exists():
        raise FileNotFoundError("Run cleaning.py and analysis.py first.")

    rfm = pd.read_csv(input_file)
    if len(rfm) < 4:
        raise ValueError("At least four customers are required for clustering.")

    k = 4
    features = rfm[["Recency", "Frequency", "Monetary"]].copy()
    for col in features.columns:
        features[col] = np.log1p(features[col].clip(lower=0))
    scaled = StandardScaler().fit_transform(features)

    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    rfm["Segment"] = model.fit_predict(scaled)
    score = silhouette_score(scaled, rfm["Segment"]) if rfm["Segment"].nunique() > 1 else float("nan")

    summary = rfm.groupby("Segment").agg(
        Customers=("CustomerID", "count"),
        AverageRecencyDays=("Recency", "mean"),
        AverageOrders=("Frequency", "mean"),
        AverageSpend=("Monetary", "mean"),
        TotalSpend=("Monetary", "sum"),
    ).round(2).reset_index()
    rfm.to_csv(OUTPUT_DIR / "customer_segments.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "segment_summary.csv", index=False)

    print(f"K-Means completed with K={k}. Silhouette score: {score:.3f}")
    print(summary.to_string(index=False))
    print(f"Saved outputs/customer_segments.csv and outputs/segment_summary.csv")

if __name__ == "__main__":
    main()
