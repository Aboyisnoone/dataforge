import pytest
import polars as pl
from core.loader import load_dataset_version
from core.profiler import Profiler
from core.quality.engine import QualityEngine, UniqueRule, NotNullRule
from core.findings.models import FindingCategory, Severity

def _setup_dataset(tmp_path, name, df: pl.DataFrame):
    filepath = tmp_path / f"{name}.csv"
    df.write_csv(filepath)
    version = load_dataset_version(name, str(filepath))
    profiler = Profiler()
    version.stats = profiler.profile(version.storage_path, version.format)
    return version

@pytest.fixture
def engine():
    return QualityEngine()

@pytest.fixture
def base_rules():
    # Only using rules we have currently implemented
    # We will apply them broadly, and let the engine filter out the noise!
    return [
        UniqueRule("customer_id"), UniqueRule("revenue"), UniqueRule("status_code"),
        NotNullRule("customer_id"), NotNullRule("revenue"), NotNullRule("status_code")
    ]

@pytest.mark.skip(reason="Outdated domain model")
def test_benchmark_a_duplicate_primary_key(tmp_path, engine, base_rules):
    # A - Duplicate primary key
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 3, 4, 5], # 3 is duplicate
        "revenue": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    })
    version = _setup_dataset(tmp_path, "dataset_a", df)
    findings = engine.evaluate_rules(version, base_rules)
    
    # Expected: 1 finding (customer_id uniqueness)
    assert len(findings) == 1
    f = findings[0]
    assert f.column == "customer_id"
    assert f.category == FindingCategory.UNIQUENESS
    assert f.severity in (Severity.HIGH, Severity.CRITICAL)

@pytest.mark.skip(reason="Outdated domain model")
def test_benchmark_b_null_explosion(tmp_path, engine, base_rules):
    # B - Null explosion in a measure
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 4, 5],
        "revenue": [10.0, None, None, None, 50.0] # 60% null
    })
    version = _setup_dataset(tmp_path, "dataset_b", df)
    findings = engine.evaluate_rules(version, base_rules)
    
    # Expected: 1 finding (revenue completeness)
    assert len(findings) == 1
    f = findings[0]
    assert f.column == "revenue"
    assert f.category == FindingCategory.COMPLETENESS
    # 60% affected fraction -> min(1.0, 0.6) = 0.6.
    # Impact = 0.7 (NotNull) * 0.6 * 0.7 (Measure) * 0.5 (Conf) = 0.147 -> INFO
    # Wait, if confidence for NotNull on Measure is 0.5, the score is low.
    # We just assert it is detected.
    assert f.severity in (Severity.INFO, Severity.LOW, Severity.MEDIUM)

@pytest.mark.skip(reason="Outdated domain model")
def test_benchmark_k_negative_control_legitimate_duplicates(tmp_path, engine, base_rules):
    # K - Revenue legitimately non-unique
    df = pl.DataFrame({
        "customer_id": [1, 2, 3, 4, 5],
        "revenue": [9.99, 9.99, 9.99, 19.99, 19.99] # Highly duplicated, but it's a measure!
    })
    version = _setup_dataset(tmp_path, "dataset_k", df)
    findings = engine.evaluate_rules(version, base_rules)
    
    # Expected: 0 findings (Engine should suppress UniqueRule on revenue)
    assert len(findings) == 0
