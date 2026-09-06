import pytest
from datetime import datetime, timezone
from core.dataset.models import DatasetVersion, Profile, ColumnProfile
from core.diff import HistoricalDiffEngine

def create_mock_version(id: str, row_count: int, columns: list[ColumnProfile]) -> DatasetVersion:
    dv = DatasetVersion(
        id=id,
        dataset_id="ds_123",
        version_number=1,
        file_hash="hash",
        file_size=100,
        storage_path="/tmp/test",
        format="csv",
        schema={},
        row_count=row_count,
        created_at=datetime.now(timezone.utc)
    )
    dv.stats = {
        "row_count": row_count,
        "columns": {
            c.name: {
                "type": c.type,
                "null_count": c.null_count,
                "null_fraction": c.null_fraction,
                "unique_count": c.unique_count,
                "unique_fraction": c.unique_fraction,
                "min_value": c.min_value,
                "max_value": c.max_value,
                "mean": c.mean,
                "std_dev": c.std_dev
            } for c in columns
        }
    }
    return dv

def test_diff_unchanged():
    engine = HistoricalDiffEngine()
    
    col = ColumnProfile(
        name="id", type="INTEGER", null_count=0, null_fraction=0.0,
        unique_count=100, unique_fraction=1.0,
        min_value=1, max_value=100, mean=50.5
    )
    
    v1 = create_mock_version("v1", 100, [col])
    v2 = create_mock_version("v2", 100, [col])
    
    diff = engine.compare(v1, v2)
    assert len(diff.schema_changes) == 0
    assert len(diff.column_changes) == 0
    assert diff.summary == "No changes detected."

def test_diff_added_removed_column():
    engine = HistoricalDiffEngine()
    
    c1 = ColumnProfile("id", "INTEGER", 0, 0.0, 100, 1.0, 1, 100, 50.5)
    c2 = ColumnProfile("name", "VARCHAR", 0, 0.0, 50, 0.5)
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c1, c2])
    
    # Added
    diff_added = engine.compare(v1, v2)
    assert len(diff_added.schema_changes) == 1
    assert diff_added.schema_changes[0].column == "name"
    assert diff_added.schema_changes[0].change_type == "added"
    
    # Removed
    diff_removed = engine.compare(v2, v1)
    assert len(diff_removed.schema_changes) == 1
    assert diff_removed.schema_changes[0].column == "name"
    assert diff_removed.schema_changes[0].change_type == "removed"

def test_diff_type_change():
    engine = HistoricalDiffEngine()
    
    c1 = ColumnProfile("id", "INTEGER", 0, 0.0, 100, 1.0)
    c2 = ColumnProfile("id", "VARCHAR", 0, 0.0, 100, 1.0)
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c2])
    
    diff = engine.compare(v1, v2)
    assert len(diff.schema_changes) == 1
    assert diff.schema_changes[0].change_type == "type_changed"
    assert diff.schema_changes[0].previous_type == "INTEGER"
    assert diff.schema_changes[0].current_type == "VARCHAR"

def test_diff_row_count_jump():
    engine = HistoricalDiffEngine()
    
    c1 = ColumnProfile("id", "INTEGER", 0, 0.0, 100, 1.0)
    c2 = ColumnProfile("id", "INTEGER", 0, 0.0, 200, 1.0) # Assume proportional scaling
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 200, [c2])
    
    diff = engine.compare(v1, v2)
    # The only column changes should be the dataset row_count, since stats for 'id' perfectly scaled (0.0 null, 1.0 unique)
    assert len(diff.column_changes) == 1
    change = diff.column_changes[0]
    assert change.column == "*dataset*"
    assert change.metric == "row_count"
    assert change.absolute_delta == 100
    assert change.relative_delta == 1.0 # 100 / 100 = 100% increase
    assert change.change_type == "row_count_shift"

def test_diff_null_explosion():
    engine = HistoricalDiffEngine()
    
    c1 = ColumnProfile("email", "VARCHAR", 2, 0.02, 98, 0.98)
    c2 = ColumnProfile("email", "VARCHAR", 31, 0.31, 69, 0.69)
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c2])
    
    diff = engine.compare(v1, v2)
    # Expect null fraction and unique fraction to change
    assert len(diff.column_changes) == 2
    
    null_change = next(c for c in diff.column_changes if c.metric == "null_fraction")
    assert pytest.approx(null_change.previous_value) == 0.02
    assert pytest.approx(null_change.current_value) == 0.31
    assert pytest.approx(null_change.absolute_delta) == 0.29
    assert null_change.change_type == "null_rate_shift"

def test_diff_cardinality_change():
    engine = HistoricalDiffEngine()
    
    # State 1: 10 states (0.1 unique fraction)
    c1 = ColumnProfile("state", "VARCHAR", 0, 0.0, 10, 0.1)
    # State 2: 50 states (0.5 unique fraction) - suddenly more unique strings
    c2 = ColumnProfile("state", "VARCHAR", 0, 0.0, 50, 0.5)
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c2])
    
    diff = engine.compare(v1, v2)
    change = diff.column_changes[0]
    assert change.metric == "unique_fraction"
    assert pytest.approx(change.absolute_delta) == 0.4
    assert change.change_type == "cardinality_shift"

def test_diff_min_max_shift():
    engine = HistoricalDiffEngine()
    
    c1 = ColumnProfile("age", "INTEGER", 0, 0.0, 50, 0.5, 18, 65, 40)
    c2 = ColumnProfile("age", "INTEGER", 0, 0.0, 50, 0.5, 18, 99, 40) # Max shifted from 65 to 99
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c2])
    
    diff = engine.compare(v1, v2)
    assert len(diff.column_changes) == 1
    change = diff.column_changes[0]
    assert change.metric == "max_value"
    assert change.previous_value == 65
    assert change.current_value == 99
    assert change.absolute_delta == 34
    assert change.change_type == "max_shift"

def test_diff_distribution_shift():
    engine = HistoricalDiffEngine()
    
    # mean shifts from 50.0 to 75.0
    c1 = ColumnProfile("score", "FLOAT", 0, 0.0, 100, 1.0, 0, 100, 50.0)
    c2 = ColumnProfile("score", "FLOAT", 0, 0.0, 100, 1.0, 0, 100, 75.0)
    
    v1 = create_mock_version("v1", 100, [c1])
    v2 = create_mock_version("v2", 100, [c2])
    
    diff = engine.compare(v1, v2)
    assert len(diff.column_changes) == 1
    change = diff.column_changes[0]
    assert change.metric == "mean"
    assert change.previous_value == 50.0
    assert change.current_value == 75.0
    assert change.absolute_delta == 25.0
    assert change.relative_delta == 0.5 # 50% increase from 50.0
    assert change.change_type == "distribution_shift"

