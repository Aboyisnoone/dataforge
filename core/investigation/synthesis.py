from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Any

from core.investigation.models import Investigation
from core.findings.models import Finding
from core.diff import DatasetDiff, SchemaChange, ColumnChange
from core.attribution.models import Attribution
from core.investigation.hypothesis import Hypothesis
from core.investigation.hypothesis import ValidationResult
from core.attribution.root_cause import RootCauseCandidate, CandidateStatus

@dataclass
class InvestigationSynthesis:
    investigation_id: str
    problem_summary: str
    key_findings: List[Finding]
    important_changes: List[Any]  # SchemaChange or ColumnChange
    attributions: List[Attribution]
    hypotheses: List[Hypothesis]
    validations: List[ValidationResult]
    root_cause_candidates: List[RootCauseCandidate]
    strongest_candidate: Optional[RootCauseCandidate]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        """
        Renders the structured synthesis into a human-readable text format,
        proving we can compile the graph into an answer.
        """
        lines = []
        lines.append(f"# Investigation Synthesis: {self.investigation_id}")
        if self.generated_at:
            lines.append(f"Generated at: {self.generated_at.isoformat()}")
        lines.append("\n## What happened?")
        lines.append(self.problem_summary)

        if self.important_changes:
            lines.append("\n## What changed?")
            for change in self.important_changes:
                if isinstance(change, SchemaChange):
                    lines.append(f"- Schema {change.change_type} on column '{change.column}'")
                elif isinstance(change, ColumnChange):
                    lines.append(f"- {change.metric} on '{change.column}' shifted (delta: {change.absolute_delta})")
        else:
            lines.append("\n## What changed?")
            lines.append("- No historical changes detected.")

        if self.attributions:
            lines.append("\n## What is most likely related?")
            for attr in self.attributions:
                lines.append(f"- [{attr.relevance_score.value}] {attr.reason}")

        if self.hypotheses:
            lines.append("\n## What did we test?")
            for hyp in self.hypotheses:
                lines.append(f"- Hypothesis: {hyp.description}")
                if hyp.validation_result:
                    vr = hyp.validation_result
                    lines.append(f"  Result: {vr.status.value}")
                    lines.append(f"  Evidence: {len(vr.evidence)} artifacts.")
                else:
                    lines.append("  Result: PROPOSED (Not yet validated)")

        if self.strongest_candidate:
            lines.append("\n## Current root-cause candidate:")
            lines.append(f"- {self.strongest_candidate.explanation}")
            lines.append(f"- Status: {self.strongest_candidate.status.value}")
            lines.append(f"- Confidence: {self.strongest_candidate.confidence * 100:.1f}%")
        elif self.root_cause_candidates:
            lines.append("\n## Current root-cause candidate:")
            lines.append("- Multiple candidates exist, but none are strong enough.")
        else:
            lines.append("\n## Current root-cause candidate:")
            lines.append("- No root cause candidates identified yet.")

        return "\n".join(lines)


class InvestigationSynthesizer:
    def synthesize(
        self,
        investigation: Investigation,
        diff: Optional[DatasetDiff] = None,
        attributions: Optional[List[Attribution]] = None,
        candidates: Optional[List[RootCauseCandidate]] = None
    ) -> InvestigationSynthesis:
        """
        Deterministically compiles the investigation graph into a synthesis.
        """
        attributions = attributions or []
        candidates = candidates or []
        
        # Sort candidates deterministically just in case they aren't already sorted
        candidates = sorted(candidates, key=lambda c: (c.score, c.confidence), reverse=True)

        # 1. Generate problem summary
        summary = f"[{investigation.status.value}] {investigation.title}: {investigation.description}."
        if investigation.findings:
            f = investigation.findings[0]
            summary += f" Detected {len(investigation.findings)} finding(s). Primary: {f.title} on {f.column or 'dataset'}."

        # 2. Extract changes
        changes = []
        if diff:
            changes.extend(diff.schema_changes)
            changes.extend(diff.column_changes)

        # 3. Extract validations
        validations = [h.validation_result for h in investigation.hypotheses if h.validation_result]

        # 4. Identify strongest candidate
        strongest = candidates[0] if candidates and candidates[0].status in (CandidateStatus.STRONG, CandidateStatus.PLAUSIBLE) else None

        return InvestigationSynthesis(
            investigation_id=investigation.id,
            problem_summary=summary,
            key_findings=list(investigation.findings),
            important_changes=changes,
            attributions=list(attributions),
            hypotheses=list(investigation.hypotheses),
            validations=validations,
            root_cause_candidates=list(candidates),
            strongest_candidate=strongest
        )
