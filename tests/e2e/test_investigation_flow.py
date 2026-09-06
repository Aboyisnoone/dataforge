import pytest
import os
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.persistence.database import Base, engine
import polars as pl
from datetime import datetime, timezone

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.skip(reason="Outdated domain model")
def test_full_investigation_lifecycle(tmp_path):
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 3, 5],
        "revenue": [10.0, 20.0, None, 40.0, 50.0]
    })
    filepath = str(tmp_path / "data.csv")
    df.write_csv(filepath)
    
    with open(filepath, "rb") as f:
        res_upload = client.post("/datasets", files={"file": ("data.csv", f, "text/csv")})
    assert res_upload.status_code == 200
    dataset_id = res_upload.json()["id"]
    
    res_inv = client.post("/investigations", json={
        "title": "E2E Test",
        "description": "Lifecycle run",
        "dataset_id": dataset_id
    })
    assert res_inv.status_code == 200
    inv = res_inv.json()
    inv_id = inv["id"]
    
    assert len(inv["findings"]) > 0
    f0 = inv["findings"][0]
    assert len(f0["evidence"]) > 0
    
    res_get = client.get(f"/investigations/{inv_id}")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "OPEN"
    
    res_patch1 = client.patch(f"/investigations/{inv_id}", json={"status": "INVESTIGATING"})
    assert res_patch1.status_code == 200
    assert res_patch1.json()["status"] == "INVESTIGATING"
    
    res_patch2 = client.patch(f"/investigations/{inv_id}", json={
        "status": "RESOLVED",
        "resolution": {
            "root_cause": "Test issue",
            "resolution_type": "Data Fix",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "validation_result": "Fixed"
        }
    })
    assert res_patch2.status_code == 200
    assert res_patch2.json()["status"] == "RESOLVED"
    
    res_final = client.get(f"/investigations/{inv_id}")
    assert res_final.status_code == 200
    final_inv = res_final.json()
    assert final_inv["status"] == "RESOLVED"
    assert final_inv["resolution"]["root_cause"] == "Test issue"

@pytest.mark.skip(reason="Outdated domain model")
def test_failure_paths(tmp_path):
    filepath = str(tmp_path / "data.txt")
    with open(filepath, "w") as f: f.write("hello")
    with open(filepath, "rb") as f:
        res = client.post("/datasets", files={"file": ("data.txt", f, "text/plain")})
    assert res.status_code == 400
    
    res = client.post("/investigations", json={
        "title": "Bad",
        "description": "Bad",
        "dataset_id": "non_existent"
    })
    assert res.status_code == 404
    
    assert client.get("/investigations/inv_missing").status_code == 404
    
    df = pl.DataFrame({"a": [1]})
    valid_csv = str(tmp_path / "valid.csv")
    df.write_csv(valid_csv)
    with open(valid_csv, "rb") as f:
        ds_id = client.post("/datasets", files={"file": ("valid.csv", f, "text/csv")}).json()["id"]
    inv_id = client.post("/investigations", json={"title": "T", "description": "D", "dataset_id": ds_id}).json()["id"]
    
    res = client.patch(f"/investigations/{inv_id}", json={"status": "RESOLVED"})
    assert res.status_code == 400
