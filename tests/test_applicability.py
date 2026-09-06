import pytest
from core.semantics.models import ColumnSemantics, PhysicalType, SemanticRole, Sensitivity
from core.quality.applicability import RuleApplicability
from core.quality import NotNullRule, UniqueRule

def test_unique_rule_applicability():
    # Customer ID (Identifier)
    sem_id = ColumnSemantics("customer_id", PhysicalType.INTEGER, SemanticRole.IDENTIFIER, Sensitivity.NON_PII)
    res_id = UniqueRule("customer_id").check_applicability(sem_id)
    assert res_id.applicable is True
    assert res_id.confidence >= 0.90
    assert "IDENTIFIER" in res_id.reason
    
    # Revenue (Measure)
    sem_rev = ColumnSemantics("revenue", PhysicalType.DOUBLE, SemanticRole.MEASURE, Sensitivity.NON_PII)
    res_rev = UniqueRule("revenue").check_applicability(sem_rev)
    assert res_rev.applicable is False
    assert res_rev.confidence >= 0.90
    
    # Country (Category)
    sem_cat = ColumnSemantics("country", PhysicalType.STRING, SemanticRole.CATEGORY, Sensitivity.NON_PII)
    res_cat = UniqueRule("country").check_applicability(sem_cat)
    assert res_cat.applicable is False

def test_not_null_rule_applicability():
    # Customer ID (Identifier)
    sem_id = ColumnSemantics("customer_id", PhysicalType.INTEGER, SemanticRole.IDENTIFIER, Sensitivity.NON_PII)
    res_id = NotNullRule("customer_id").check_applicability(sem_id)
    assert res_id.applicable is True
    assert res_id.confidence >= 0.90
    
    # Text comments
    sem_txt = ColumnSemantics("comments", PhysicalType.STRING, SemanticRole.TEXT, Sensitivity.NON_PII)
    res_txt = NotNullRule("comments").check_applicability(sem_txt)
    assert res_txt.applicable is False
    assert res_txt.confidence >= 0.90
