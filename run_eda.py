from src.data import load_data, build_analytics
import pandas as pd

df, quality = load_data("data/Nassau Candy Distributor.csv")
print("\\n=== DATA QUALITY ===")
for k,v in quality.items():
    print(f"{k}: {v}")
print("\\n=== SHIP MODE VOLUME ===")
print(df.groupby("Ship Mode")["Order ID"].nunique().sort_values(ascending=False))
print("\\n=== FACTORY VOLUME ===")
print(df.groupby("Factory")["Order ID"].nunique().sort_values(ascending=False))
print("\\n=== VALIDATED ROUTE ANALYSIS ===")
a = build_analytics(df, delay_threshold=7)
print(a["routes"].head(10).to_string(index=False))
print("\\n=== STATE ANALYSIS ===")
print(a["states"].sort_values("Orders", ascending=False).head(15).to_string(index=False))
df.to_csv("data/processed_nassaulogix.csv", index=False)
print("\\nProcessed file saved to data/processed_nassaulogix.csv")
