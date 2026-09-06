import pytest
from core.semantics.models import SemanticRole
from core.findings.models import Severity
from core.quality.severity import ImpactCalculator

def test_impact_calculator():
    # 1. High-impact identifier violation
    res1 = ImpactCalculator.calculate("UniqueRule", SemanticRole.IDENTIFIER, 1.0, 1.0)
    assert res1.impact_score == 1.0
    assert res1.severity == Severity.CRITICAL
    
    # 2. Same violation on low-importance column (TEXT)
    res2 = ImpactCalculator.calculate("UniqueRule", SemanticRole.TEXT, 1.0, 1.0)
    assert res2.impact_score < res1.impact_score
    
    # 3. Higher affected fraction -> higher impact
    res3 = ImpactCalculator.calculate("NotNullRule", SemanticRole.MEASURE, 0.5, 1.0)
    res4 = ImpactCalculator.calculate("NotNullRule", SemanticRole.MEASURE, 1.0, 1.0)
    assert res4.impact_score > res3.impact_score
    
    # 4. Higher confidence -> higher impact
    res5 = ImpactCalculator.calculate("NotNullRule", SemanticRole.MEASURE, 1.0, 0.5)
    assert res4.impact_score > res5.impact_score
    
    # 5. Tiny fraction on critical identifier should still be meaningful (not INFO/0)
    res_tiny = ImpactCalculator.calculate("UniqueRule", SemanticRole.IDENTIFIER, 0.0001, 1.0)
    assert res_tiny.impact_score > 0.0
    assert res_tiny.severity != Severity.INFO
    assert res_tiny.severity == Severity.HIGH # 1.0 * 0.65 * 1.0 * 1.0 = 0.65
