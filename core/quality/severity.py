from dataclasses import dataclass
from core.semantics.models import SemanticRole
from core.findings.models import Severity

# Semantic Weights
SEMANTIC_WEIGHTS = {
    SemanticRole.IDENTIFIER: 1.00,
    SemanticRole.DATETIME: 0.80,
    SemanticRole.MEASURE: 0.70,
    SemanticRole.CATEGORY: 0.50,
    SemanticRole.BOOLEAN: 0.50,
    SemanticRole.TEXT: 0.30,
    SemanticRole.UNKNOWN: 0.10,
}

# Rule Criticality
RULE_CRITICALITY = {
    "UniqueRule": 1.00,
    "NotNullRule": 0.70,
}

@dataclass
class ImpactCalculationResult:
    impact_score: float
    severity: Severity

class ImpactCalculator:
    
    @staticmethod
    def calculate(
        rule_name: str,
        semantic_role: SemanticRole,
        affected_fraction: float,
        confidence: float
    ) -> ImpactCalculationResult:
        
        rule_crit = RULE_CRITICALITY.get(rule_name, 0.5)
        sem_importance = SEMANTIC_WEIGHTS.get(semantic_role, 0.1)
        
        # Use a floor transform so tiny fractions don't make serious problems disappear to 0
        # A floor of 0.65 means a 1.0 critical rule on a 1.0 importance column will score at least 0.637 (HIGH)
        affected_factor = max(0.65, min(1.0, affected_fraction))
        
        conf = max(0.0, min(1.0, confidence))
        
        impact_score = rule_crit * affected_factor * sem_importance * conf
        
        if impact_score >= 0.80:
            severity = Severity.CRITICAL
        elif impact_score >= 0.60:
            severity = Severity.HIGH
        elif impact_score >= 0.40:
            severity = Severity.MEDIUM
        elif impact_score >= 0.20:
            severity = Severity.LOW
        else:
            severity = Severity.INFO
            
        return ImpactCalculationResult(
            impact_score=round(impact_score, 4),
            severity=severity
        )
