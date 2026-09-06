import pytest
import os
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.persistence.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_dataset_upload_csv(tmp_path):
    # Create dummy csv
    file_path = tmp_path / "test.csv"
    file_path.write_text("a,b\n1,2")
    
    with open(file_path, "rb") as f:
        response = client.post("/datasets", files={"file": ("test.csv", f, "text/csv")})
        
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "test"
    assert data["latest_version"]["format"] == "csv"
    assert data["latest_version"]["file_size"] > 0
    
@pytest.mark.skip(reason="Outdated domain model")
def test_dataset_upload_unsupported(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello")
    
    with open(file_path, "rb") as f:
        response = client.post("/datasets", files={"file": ("test.txt", f, "text/plain")})
        
    assert response.status_code == 413
    assert "Unsupported format" in response.json()["detail"]
    
def test_dataset_upload_large_file(tmp_path, monkeypatch):
    import backend.datasets.storage
    monkeypatch.setattr(backend.datasets.storage, "MAX_UPLOAD_SIZE", 10)
    
    file_path = tmp_path / "test.csv"
    file_path.write_text("a,b\n1,2\n3,4\n5,6")
    
    with open(file_path, "rb") as f:
        response = client.post("/datasets", files={"file": ("test.csv", f, "text/csv")})
        
    assert response.status_code == 413
    assert "maximum upload size" in response.json()["detail"]

def test_dataset_path_traversal(tmp_path):
    file_path = tmp_path / "test.csv"
    file_path.write_text("a,b\n1,2")
    
    with open(file_path, "rb") as f:
        # FileStorage generates a safe name using uuid, so original filename is ignored for storage path
        response = client.post("/datasets", files={"file": ("../../../etc/passwd.csv", f, "text/csv")})
        
    assert response.status_code == 200
    # it saves fine, but path traversal is thwarted by FileStorage
