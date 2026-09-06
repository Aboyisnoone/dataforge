import time
import os
import polars as pl
import tracemalloc
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.persistence.database import Base, engine

client = TestClient(app)

def run_benchmark(rows: int, filename: str):
    print(f"--- Benchmark: {rows:,} rows ---")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    df = pl.DataFrame({
        "id": range(rows),
        "category": ["A", "B", "C", "D", "E"] * (rows // 5),
        "value": [1.0] * rows
    })
    
    if rows > 100:
        df = df.with_columns(
            pl.when(pl.col("id") > rows - 5)
            .then(0)
            .otherwise(pl.col("id"))
            .alias("id")
        )
        
    df.write_csv(filename)
    file_size = os.path.getsize(filename) / (1024 * 1024)
    print(f"Dataset Size: {file_size:.2f} MB")
    
    tracemalloc.start()
    t0 = time.time()
    with open(filename, "rb") as f:
        res = client.post("/datasets", files={"file": (filename, f, "text/csv")})
    dataset_id = res.json()["id"]
    t1 = time.time()
    print(f"Upload API Time: {t1-t0:.2f}s")
    
    t2 = time.time()
    res = client.post("/investigations", json={
        "title": "Bench",
        "description": "Bench",
        "dataset_id": dataset_id
    })
    t3 = time.time()
    print(f"Investigation API Time (Profile+Rules+Persist): {t3-t2:.2f}s")
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"Peak Memory Usage: {peak / 10**6:.2f} MB\n")
    
    os.remove(filename)

if __name__ == "__main__":
    run_benchmark(10_000, "bench_10k.csv")
    run_benchmark(100_000, "bench_100k.csv")
    run_benchmark(1_000_000, "bench_1m.csv")
