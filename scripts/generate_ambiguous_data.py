import polars as pl
import numpy as np

np.random.seed(42)

n_rows = 10000

# V1
# customer_id: 99.8% unique -> 9980 unique, 20 duplicates
cust_ids_v1 = np.arange(1, 9981).tolist()
# Add 20 duplicates
duplicates = np.random.choice(cust_ids_v1, size=20, replace=True).tolist()
customer_id_v1 = cust_ids_v1 + duplicates
np.random.shuffle(customer_id_v1)

# email: 1% null
email_v1 = [f"user_{c}@example.com" if np.random.rand() > 0.01 else None for c in customer_id_v1]

# revenue: normal dist, mean 100, std 20
revenue_v1 = np.random.normal(100, 20, n_rows)

v1 = pl.DataFrame({
    "customer_id": customer_id_v1,
    "email": email_v1,
    "revenue": revenue_v1
})
v1.write_csv("v1.csv")

# V2
# customer_id: 94% unique -> 9400 unique, 600 duplicates
cust_ids_v2 = np.arange(1, 9401).tolist()
duplicates_v2 = np.random.choice(cust_ids_v2, size=600, replace=True).tolist()
customer_id_v2 = cust_ids_v2 + duplicates_v2
np.random.shuffle(customer_id_v2)

# email: 18% null
email_v2 = [f"user_{c}@example.com" if np.random.rand() > 0.18 else None for c in customer_id_v2]

# revenue: shifted dist, mean 40, std 40
revenue_v2 = np.random.normal(40, 40, n_rows)

v2 = pl.DataFrame({
    "customer_id": customer_id_v2,
    "email": email_v2,
    "revenue": revenue_v2
})
v2.write_csv("v2.csv")

print("Generated ambiguous v1.csv and v2.csv")
