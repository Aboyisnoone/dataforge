from dataclasses import dataclass
from core.semantics.models import ColumnSemantics, SemanticRole

@dataclass
class ApplicabilityResult:
    applicable: bool
    confidence: float
    reason: str

class RuleApplicability:
    @staticmethod
    def for_unique_rule(semantics: ColumnSemantics) -> ApplicabilityResult:
        if semantics.semantic_role == SemanticRole.IDENTIFIER:
            return ApplicabilityResult(True, 0.98, "Column is classified as IDENTIFIER")
        elif semantics.semantic_role in (SemanticRole.MEASURE, SemanticRole.CATEGORY):
            return ApplicabilityResult(False, 0.99, f"Column is classified as {semantics.semantic_role.value}")
        else:
            return ApplicabilityResult(False, 0.80, f"Uniqueness generally not expected for {semantics.semantic_role.value}")

    @staticmethod
    def for_not_null_rule(semantics: ColumnSemantics) -> ApplicabilityResult:
        if semantics.semantic_role == SemanticRole.IDENTIFIER:
            return ApplicabilityResult(True, 0.95, "Identifiers usually should not be null")
        elif semantics.semantic_role == SemanticRole.TEXT:
            return ApplicabilityResult(False, 0.90, "Free text columns often contain nulls")
        elif semantics.semantic_role in (SemanticRole.MEASURE, SemanticRole.CATEGORY, SemanticRole.DATETIME):
            return ApplicabilityResult(True, 0.50, f"{semantics.semantic_role.value} applicability depends on domain")
        else:
            return ApplicabilityResult(False, 0.50, "Unknown applicability")
