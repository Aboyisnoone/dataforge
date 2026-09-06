import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.persistence.database import Base, engine
import polars as pl
import os

client = TestClient(app)
# Override default headers for all requests
client.headers = {"X-Workspace-Id": "ws_test"}

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.skip(reason="Outdated domain model")
def test_api_endpoints(tmp_path):
    # Setup test file
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 3, 4],
        "revenue": [10.0, None, 30.0, 40.0, 50.0]
    })
    filepath = str(tmp_path / "test.csv")
    df.write_csv(filepath)
    
    # 1. Upload dataset first
    with open(filepath, "rb") as f:
        res_upload = client.post("/datasets", files={"file": ("test.csv", f, "text/csv")})
    assert res_upload.status_code == 200, res_upload.text
    dataset_data = res_upload.json()
    dataset_id = dataset_data["id"]
    
    # 2. Test POST /investigations using dataset_id
    res_inv = client.post("/investigations", json={
        "title": "API Test Inv",
        "description": "Test description",
        "dataset_id": dataset_id
    })
    assert res_inv.status_code == 200
    inv_data = res_inv.json()
    assert inv_data["status"] == "OPEN"
    assert inv_data["title"] == "API Test Inv"
    assert len(inv_data["findings"]) > 0
    
    # Verify Findings contain observations and evidence
    f = inv_data["findings"][0]
    assert "observations" in f
    assert "evidence" in f
    assert len(f["evidence"]) > 0
    
    # Verify recommendations exist
    assert "recommendations" in inv_data
    
    inv_id = inv_data["id"]
    
    # 3. Test GET /investigations/{id}
    res_get = client.get(f"/investigations/{inv_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == inv_id
    
    # 4. Test PATCH /investigations/{id} (Valid transition)
    res_patch1 = client.patch(f"/investigations/{inv_id}", json={"status": "INVESTIGATING"})
    assert res_patch1.status_code == 200
    assert res_patch1.json()["status"] == "INVESTIGATING"
    
    # 5. Test PATCH /investigations/{id} (Invalid transition to RESOLVED without resolution)
    res_patch2 = client.patch(f"/investigations/{inv_id}", json={"status": "RESOLVED"})
    assert res_patch2.status_code == 400
    assert "Resolution metadata is required" in res_patch2.json()["detail"]
    
    # 6. Test PATCH /investigations/{id} (Valid transition to RESOLVED)
    from datetime import datetime, timezone
    res_patch3 = client.patch(f"/investigations/{inv_id}", json={
        "status": "RESOLVED",
        "resolution": {
            "root_cause": "Bad upstream data",
            "resolution_type": "Data Pipeline Fix",
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "validation_result": "Cleaned"
        }
    })
    assert res_patch3.status_code == 200
    assert res_patch3.json()["status"] == "RESOLVED"
    assert res_patch3.json()["resolution"]["root_cause"] == "Bad upstream data"
    
    # 7. Test GET /investigations (Pagination and Filtering)
    res_list = client.get("/investigations")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    assert list_data["page"] == 1
    assert len(list_data["items"]) >= 1
    
    res_filter = client.get("/investigations?status=RESOLVED")
    assert res_filter.status_code == 200
    assert len(res_filter.json()["items"]) >= 1
    
    res_filter_empty = client.get("/investigations?status=OPEN")
    # depending on other tests, OPEN might be 0 here since we just resolved it
    
    # 8. Test Invalid Request
    res_invalid = client.get("/investigations/invalid_id_123")
    assert res_invalid.status_code == 404
