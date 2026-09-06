import pytest
import polars as pl
from core.transformation import TransformationEngine

@pytest.fixture
def base_csv(tmp_path):
    df = pl.DataFrame({
        "id": [1, 2, 2, 3], # Duplicate id: 2
        "status": ["active", None, "active", "inactive"] # Null status
    })
    filepath = tmp_path / "base.csv"
    df.write_csv(filepath)
    return str(filepath)

def test_transformation_engine(base_csv, tmp_path):
    out_dir = tmp_path / "out"
    engine = TransformationEngine(str(out_dir))
    
    # 1. Drop duplicates
    out_file1, t1 = engine.apply_drop_duplicates(base_csv, subset=["id"], input_fingerprint="fp_in")
    
    assert t1.type_name == "drop_duplicates"
    assert t1.affected_columns == ["id"]
    assert "df.unique(" in t1.generated_code
    
    # Verify the actual data changed
    res1_df = pl.read_csv(out_file1)
    assert len(res1_df) == 3 # Dropped 1 duplicate
    
    # 2. Fill nulls on the new file
    out_file2, t2 = engine.apply_fill_nulls(out_file1, column="status", value="unknown", input_fingerprint=t1.output_fingerprint)
    
    assert t2.type_name == "fill_nulls"
    assert t2.affected_columns == ["status"]
    assert t2.input_fingerprint == t1.output_fingerprint # Chain is maintained
    
    # Verify the actual data changed
    res2_df = pl.read_csv(out_file2)
    assert res2_df.filter(pl.col("status").is_null()).height == 0 # No nulls left
    assert res2_df.filter(pl.col("status") == "unknown").height == 1 # 1 unknown
