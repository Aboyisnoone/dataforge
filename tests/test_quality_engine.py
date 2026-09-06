import pytest
import polars as pl
from core.loader import load_dataset_version
from core.profiler import Profiler
from core.quality.engine import QualityEngine, UniqueRule
from core.findings.models import FindingCategory, Severity

@pytest.fixture
def dataset(tmp_path):
    # Customer_id (Identifier), revenue (Measure), country (Category)
    # All contain exactly one duplicate group
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 3], 
        "revenue": [100.0, 200.0, 300.0, 300.0],
        "country": ["US", "UK", "FR", "FR"]
    })
    filepath = tmp_path / "data.csv"
    df.write_csv(filepath)
    
    version = load_dataset_version("test", str(filepath))
    profiler = Profiler()
    version.stats = profiler.profile(version.storage_path, version.format)
    return version

@pytest.mark.skip(reason="Outdated domain model")
def test_intelligent_quality_engine(dataset):
    engine = QualityEngine()
    
    rules = [
        UniqueRule("customer_id"),
        UniqueRule("revenue"),
        UniqueRule("country")
    ]
    
    findings = engine.evaluate_rules(dataset, rules)
    
    # Prove only customer_id generates a finding, the others are suppressed
    assert len(findings) == 1
    
    finding = findings[0]
    
    # 1. Verification of finding logic
    assert finding.column == "customer_id"
    assert finding.category == FindingCategory.UNIQUENESS
    assert finding.severity in (Severity.HIGH, Severity.CRITICAL)
    
    # 2. Verification of observation attachment
    assert len(finding.observations) == 1
    obs = finding.observations[0]
    assert obs.column == "customer_id"
    assert obs.value == 1 # 1 duplicate
    
    # 3. Verification of impact/confidence metrics
    assert finding.impact_score > 0.0
    assert finding.confidence >= 0.90
    
    # 4. Verification of Evidence generation
    assert len(finding.evidence) >= 2
    types = [ev.type.value for ev in finding.evidence]
    assert "METRIC" in types
    assert "QUERY" in types
    
    # Check details of query evidence
    query_ev = next(ev for ev in finding.evidence if ev.type.value == "QUERY")
    assert "SELECT COUNT(*) as total, COUNT(DISTINCT customer_id) as unique_count" in query_ev.value

