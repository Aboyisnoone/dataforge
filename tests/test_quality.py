import pytest
import polars as pl
from core.loader import load_dataset_version
from core.quality.engine import QualityEngine, UniqueRule, NotNullRule
from core.dataset import DatasetVersion
from core.profiler import Profiler
from datetime import datetime, timezone

@pytest.fixture
def messy_csv(tmp_path):
    df = pl.DataFrame({
        "customer_id": [1, 1, 2, 3],
        "email": ["a@a.com", None, "b@b.com", None]
    })
    path = tmp_path / "messy.csv"
    df.write_csv(path)
    
    dv = load_dataset_version("customers", str(path))
    profiler = Profiler()
    stats = profiler.profile(dv.storage_path, 'csv')
    dv.stats = stats
    return dv

@pytest.mark.skip(reason="Outdated domain model")
def test_quality_engine(messy_csv):
    engine = QualityEngine()
    rules = [
        UniqueRule("customer_id"),
        NotNullRule("email"),
        NotNullRule("customer_id") # This one should pass
    ]
    
    findings = engine.evaluate_rules(
        messy_csv,
        rules
    )
    
    # We should have exactly 2 findings: one for duplicate customer_id, one for null email
    assert len(findings) == 2
    
    unique_finding = next(f for f in findings if f.rule == "UniqueRule")
    
    notnull_finding = next(f for f in findings if f.rule == "NotNullRule")
