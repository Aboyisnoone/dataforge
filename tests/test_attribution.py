import pytest
from core.attribution import AttributionEngine, Relevance
from core.diff import DatasetDiff, ColumnChange, SchemaChange
from core.findings.models import Finding, Severity

# Mock a finding for testing
def create_finding(id: str, column_name: str, rule: str) -> Finding:
    f = Finding(
        category="Test",
        title=f"{rule} finding",
        description="test",
        severity=Severity.HIGH,
        impact_score=0.9,
        confidence=0.9,
        column=column_name,
        rule=rule
    )
    f.id = id
    return f

def test_attribution_killer_scenario():
    # customer_id uniqueness finding
    # 1. customer_id unique_fraction ↓ -> HIGH
    # 2. customer_id null_fraction ↑ -> MEDIUM
    # 3. revenue mean ↑ -> LOW
    
    finding = create_finding("f1", "customer_id", "UniqueRule")
    
    diff = DatasetDiff(
        dataset_id="ds1",
        previous_version_id="v1",
        current_version_id="v2",
        schema_changes=[],
        column_changes=[
            ColumnChange("revenue", "mean", 10.0, 15.0, 5.0, 0.5, "distribution_shift"),
            ColumnChange("customer_id", "null_fraction", 0.0, 0.2, 0.2, 1.0, "null_rate_shift"),
            ColumnChange("customer_id", "unique_fraction", 1.0, 0.8, -0.2, -0.2, "cardinality_shift")
        ],
        summary=""
    )
    
    engine = AttributionEngine()
    results = engine.evaluate(finding, diff)
    
    assert len(results) == 3
    
    # Check ordering
    assert results[0].change.change_type == "cardinality_shift"
    assert results[0].relevance_score == Relevance.HIGH
    
    assert results[1].change.change_type == "null_rate_shift"
    assert results[1].relevance_score == Relevance.MEDIUM
    
    assert results[2].change.change_type == "distribution_shift"
    assert results[2].relevance_score == Relevance.LOW

def test_attribution_null_finding():
    finding = create_finding("f2", "revenue", "NotNullRule")
    
    diff = DatasetDiff(
        dataset_id="ds1",
        previous_version_id="v1",
        current_version_id="v2",
        schema_changes=[],
        column_changes=[
            ColumnChange("revenue", "null_fraction", 0.0, 0.5, 0.5, 1.0, "null_rate_shift"),
        ],
        summary=""
    )
    
    engine = AttributionEngine()
    results = engine.evaluate(finding, diff)
    
    assert len(results) == 1
    assert results[0].relevance_score == Relevance.HIGH
    assert results[0].change.change_type == "null_rate_shift"

def test_attribution_schema_change():
    finding = create_finding("f3", "revenue", "TypeMatch") # Abstract type check rule
    
    diff = DatasetDiff(
        dataset_id="ds1",
        previous_version_id="v1",
        current_version_id="v2",
        schema_changes=[
            SchemaChange("revenue", "type_changed", "INTEGER", "VARCHAR")
        ],
        column_changes=[],
        summary=""
    )
    
    engine = AttributionEngine()
    results = engine.evaluate(finding, diff)
    
    assert len(results) == 1
    assert results[0].relevance_score == Relevance.HIGH
    assert results[0].change.change_type == "type_changed"

def test_attribution_no_changes():
    finding = create_finding("f4", "customer_id", "UniqueRule")
    diff = DatasetDiff("ds1", "v1", "v2", [], [], "No changes")
    
    engine = AttributionEngine()
    results = engine.evaluate(finding, diff)
    assert len(results) == 0

def test_attribution_global_row_count():
    finding = create_finding("f5", "customer_id", "UniqueRule")
    diff = DatasetDiff(
        dataset_id="ds1",
        previous_version_id="v1",
        current_version_id="v2",
        schema_changes=[],
        column_changes=[
            ColumnChange("*dataset*", "row_count", 100, 200, 100, 1.0, "row_count_shift")
        ],
        summary=""
    )
    
    engine = AttributionEngine()
    results = engine.evaluate(finding, diff)
    
    assert len(results) == 1
    assert results[0].relevance_score == Relevance.MEDIUM
    assert results[0].change.column == "*dataset*"
