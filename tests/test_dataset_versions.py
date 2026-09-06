import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
import polars as pl
from backend.persistence.database import Base, engine, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_dataset_versioning_lifecycle(tmp_path):
    # A. First upload
    df1 = pl.DataFrame({"id": [1, 2], "val": ["a", "b"]})
    f1_path = tmp_path / "data.csv"
    df1.write_csv(f1_path)
    
    with open(f1_path, "rb") as f:
        res1 = client.post("/datasets", files={"file": ("data.csv", f, "text/csv")})
    assert res1.status_code == 200
    d1 = res1.json()
    dataset_id = d1["id"]
    v1_id = d1["latest_version"]["id"]
    assert d1["latest_version"]["version_number"] == 1
    
    # B. Modified dataset
    df2 = pl.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    f2_path = tmp_path / "data.csv" # Same name!
    df2.write_csv(f2_path)
    
    with open(f2_path, "rb") as f:
        res2 = client.post("/datasets", files={"file": ("data.csv", f, "text/csv")})
    assert res2.status_code == 200
    d2 = res2.json()
    # Should use the same dataset_id, but create V2
    assert d2["id"] == dataset_id
    v2_id = d2["latest_version"]["id"]
    assert d2["latest_version"]["version_number"] == 2
    assert v1_id != v2_id
    
    # C. Identical dataset
    with open(f2_path, "rb") as f:
        res3 = client.post("/datasets", files={"file": ("data.csv", f, "text/csv")})
    assert res3.status_code == 200
    d3 = res3.json()
    # Hash match! Should not create V3, should return V2
    assert d3["latest_version"]["id"] == v2_id
    assert d3["latest_version"]["version_number"] == 2
    
    # E & F. History ordering and Immutability
    res_hist = client.get(f"/datasets/{dataset_id}/versions")
    assert res_hist.status_code == 200
    hist = res_hist.json()
    assert len(hist["versions"]) == 2
    assert hist["versions"][0]["version_number"] == 1
    assert hist["versions"][1]["version_number"] == 2
    
    # D. Profile persistence is implicitly tested if we can reload the dataset
    # from the DB and the stats still work via GET /investigations or similar
    # But let's verify row_count on the versions
    assert hist["versions"][0]["row_count"] == 2
    assert hist["versions"][1]["row_count"] == 3
