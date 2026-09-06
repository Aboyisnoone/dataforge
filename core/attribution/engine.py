from typing import List
from core.findings.models import Finding
from core.diff import DatasetDiff, SchemaChange, ColumnChange
from core.attribution.models import Attribution, Relevance

class AttributionEngine:
    def evaluate(self, finding: Finding, diff: DatasetDiff) -> List[Attribution]:
        attributions = []

        # Evaluate Schema Changes
        for sc in diff.schema_changes:
            relevance, confidence, reason = self._score_schema_change(finding, sc)
            if relevance != Relevance.NONE:
                attributions.append(Attribution(
                    finding_id=finding.id,
                    change=sc,
                    relevance_score=relevance,
                    confidence=confidence,
                    reason=reason
                ))

        # Evaluate Column Changes
        for cc in diff.column_changes:
            relevance, confidence, reason = self._score_column_change(finding, cc)
            if relevance != Relevance.NONE:
                attributions.append(Attribution(
                    finding_id=finding.id,
                    change=cc,
                    relevance_score=relevance,
                    confidence=confidence,
                    reason=reason
                ))

        # Sort by relevance score, then confidence
        attributions.sort(key=lambda a: (a.relevance_score.score, a.confidence), reverse=True)
        return attributions

    def _score_schema_change(self, finding: Finding, change: SchemaChange) -> tuple[Relevance, float, str]:
        finding_col = getattr(finding, "column", None)

        if finding_col and change.column == finding_col:
            if change.change_type == "type_changed":
                # A type change is highly relevant to almost any issue on that column
                return Relevance.HIGH, 0.85, f"Physical type of column '{change.column}' changed."
            elif change.change_type == "removed":
                return Relevance.HIGH, 0.95, f"Column '{change.column}' was removed."
            elif change.change_type == "added":
                return Relevance.MEDIUM, 0.5, f"Column '{change.column}' was recently added."
        
        # Schema change on a different column
        return Relevance.LOW, 0.1, f"Unrelated schema change on '{change.column}'."

    def _score_column_change(self, finding: Finding, change: ColumnChange) -> tuple[Relevance, float, str]:
        finding_col = getattr(finding, "column", None)
        rule_name = getattr(finding, "rule", None)

        if change.column == "*dataset*" and change.metric == "row_count":
            return Relevance.MEDIUM, 0.5, "Dataset-level row count shifted, potentially affecting data distribution."

        if finding_col and change.column == finding_col:
            # Direct hit on the column. Is it a direct hit on the metric?
            if rule_name == "UniqueRule" and change.change_type == "cardinality_shift":
                return Relevance.HIGH, 0.9, "Cardinality shift directly associates with uniqueness violation."
            
            if rule_name == "NotNullRule" and change.change_type == "null_rate_shift":
                return Relevance.HIGH, 0.9, "Null rate shift directly associates with missing value finding."

            # Same column, different metric
            return Relevance.MEDIUM, 0.6, f"Related statistical shift ({change.change_type}) on the affected column."

        # Different column entirely
        return Relevance.LOW, 0.1, f"Unrelated {change.change_type} on '{change.column}'."
