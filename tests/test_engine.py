import pytest
import polars as pl
from core.loader import load_dataset_version
from core.profiler import Profiler

@pytest.fixture
def sample_csv(tmp_path):
    df = pl.DataFrame({
        "id": [1, 2, 3, 4, 5, 1], # 1 duplicate for uniqueness testing later
        "name": ["Alice", "Bob", "Charlie", "David", None, "Alice"],
        "age": [25, 30, 35, 40, 22, 25]
    })
    filepath = tmp_path / "sample.csv"
    df.write_csv(filepath)
    return str(filepath)
    
def test_loader(sample_csv):
    version = load_dataset_version("users", sample_csv)
    
    assert version.format == "csv"
    assert "id" in version.schema
    assert version.file_hash is not None

def test_profiler(sample_csv):
    profiler = Profiler()
    stats = profiler.profile(sample_csv, "csv")
    
    assert stats["row_count"] == 6
    assert "id" in stats["columns"]
    
    id_stats = stats["columns"]["id"]
    assert id_stats["dtype"] == "BIGINT"
    assert id_stats["null_count"] == 0
    assert id_stats["min"] == 1
    assert id_stats["max"] == 5
    
    name_stats = stats["columns"]["name"]
    assert name_stats["null_count"] == 1
    assert name_stats["null_fraction"] == 1/6
