from core.semantics.models import PhysicalType, SemanticRole, Sensitivity
from core.semantics.classifier import SemanticClassifier

def test_semantic_classifier():
    classifier = SemanticClassifier()
    
    # 1. Email
    email_stats = {'dtype': 'VARCHAR', 'unique_count': 100, 'null_fraction': 0.0}
    sem = classifier.classify('email', email_stats, 100)
    assert sem.physical_type == PhysicalType.STRING
    assert sem.semantic_role == SemanticRole.IDENTIFIER
    assert sem.sensitivity == Sensitivity.PII
    
    # 2. Revenue
    rev_stats = {'dtype': 'DOUBLE', 'unique_count': 85, 'null_fraction': 0.0}
    sem = classifier.classify('revenue', rev_stats, 100)
    assert sem.physical_type == PhysicalType.DOUBLE
    assert sem.semantic_role == SemanticRole.MEASURE
    assert sem.sensitivity == Sensitivity.NON_PII
    
    # 3. Customer ID
    id_stats = {'dtype': 'BIGINT', 'unique_count': 100, 'null_fraction': 0.0}
    sem = classifier.classify('customer_id', id_stats, 100)
    assert sem.physical_type == PhysicalType.INTEGER
    assert sem.semantic_role == SemanticRole.IDENTIFIER
    assert sem.sensitivity == Sensitivity.NON_PII
    
    # 4. Country
    country_stats = {'dtype': 'VARCHAR', 'unique_count': 3, 'null_fraction': 0.0}
    sem = classifier.classify('country', country_stats, 1000)
    assert sem.physical_type == PhysicalType.STRING
    assert sem.semantic_role == SemanticRole.CATEGORY
    assert sem.sensitivity == Sensitivity.NON_PII
    
    # 5. Created At
    date_stats = {'dtype': 'TIMESTAMP', 'unique_count': 100, 'null_fraction': 0.0}
    sem = classifier.classify('created_at', date_stats, 100)
    assert sem.physical_type == PhysicalType.DATETIME
    assert sem.semantic_role == SemanticRole.DATETIME
