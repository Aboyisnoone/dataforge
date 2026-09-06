import polars as pl
import os

df = pl.DataFrame({
    "customer_id": [1, 2, 3, 3, 4, 5],
    "revenue": [10.0, None, 30.0, 40.0, None, 60.0],
    "country": ["US", "US", "UK", "UK", "FR", "FR"]
})

os.makedirs("data", exist_ok=True)
df.write_csv("data/sample.csv")
print("Generated data/sample.csv")
