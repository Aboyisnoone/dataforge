from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid

from core.findings.models import Finding
from core.attribution.models import Attribution, Relevance
from core.investigation.hypothesis import Hypothesis, HypothesisStatus
from core.investigation.hypothesis import ValidationResult
from core.evidence.models import Evidence

class CandidateStatus(str, Enum):
    STRONG = "STRONG"
    PLAUSIBLE = "PLAUSIBLE"
    UNLIKELY = "UNLIKELY"
    DISQUALIFIED = "DISQUALIFIED"

@dataclass
class RootCauseCandidate:
    finding_id: str
    score: float
    confidence: float
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    explanation: str
    status: CandidateStatus
    hypothesis_id: Optional[str] = None
    attribution_id: Optional[str] = None
    id: str = field(default_factory=lambda: f"rcc_{uuid.uuid4().hex[:8]}")

class RootCauseEngine:
    def rank_candidates(
        self,
        finding: Finding,
        attributions: List[Attribution],
        hypotheses: List[Hypothesis]
    ) -> List[RootCauseCandidate]:
        candidates = []
        
        # We process each hypothesis attached to this finding.
        finding_hypotheses = [h for h in hypotheses if h.finding_id == finding.id]
        
        processed_attribution_ids = set()
        
        for hyp in finding_hypotheses:
            attribution = None
            if hyp.attribution_id:
                attribution = next((a for a in attributions if a.id == hyp.attribution_id), None)
                if attribution:
                    processed_attribution_ids.add(attribution.id)
            
            candidate = self._evaluate_hypothesis(finding, hyp, attribution)
            candidates.append(candidate)
            
        # Add pure attributions that don't have a hypothesis yet
        for attr in attributions:
            if attr.id not in processed_attribution_ids:
                candidate = self._evaluate_attribution(finding, attr)
                candidates.append(candidate)
                
        # Sort deterministically by score (descending), then confidence (descending)
        candidates.sort(key=lambda c: (c.score, c.confidence), reverse=True)
        return candidates

    def _evaluate_hypothesis(self, finding: Finding, hypothesis: Hypothesis, attribution: Optional[Attribution]) -> RootCauseCandidate:
        base_score = 0.0
        base_confidence = 0.5
        
        if attribution:
            base_score = self._score_relevance(attribution.relevance_score)
            base_confidence = attribution.confidence
            
        score = base_score
        confidence = base_confidence
        supporting = []
        contradicting = []
        explanation_parts = []
        
        if attribution:
            explanation_parts.append(f"Based on historical change: {attribution.reason}")
        
        if hypothesis.validation_result:
            vr = hypothesis.validation_result
            if vr.status == HypothesisStatus.SUPPORTED:
                score += 0.4
                confidence = 0.9
                supporting.extend(vr.evidence)
                explanation_parts.append(f"Hypothesis was supported: {vr.description}")
            elif vr.status == HypothesisStatus.REJECTED:
                score -= 0.8
                confidence = 0.9
                contradicting.extend(vr.evidence)
                explanation_parts.append(f"Hypothesis was rejected: {vr.description}")
            elif vr.status == HypothesisStatus.INCONCLUSIVE:
                score -= 0.1
                confidence = 0.5
                explanation_parts.append(f"Validation was inconclusive: {vr.description}")
        else:
            explanation_parts.append("Hypothesis is proposed but not yet validated.")
            
        score = max(0.0, min(1.0, score))
        status = self._determine_status(score, confidence, hypothesis.status)
        
        return RootCauseCandidate(
            finding_id=finding.id,
            hypothesis_id=hypothesis.id,
            attribution_id=attribution.id if attribution else None,
            score=score,
            confidence=confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            explanation=" ".join(explanation_parts),
            status=status
        )

    def _evaluate_attribution(self, finding: Finding, attribution: Attribution) -> RootCauseCandidate:
        score = self._score_relevance(attribution.relevance_score)
        confidence = attribution.confidence
        
        explanation = f"System-proposed candidate based on historical change: {attribution.reason}"
        status = self._determine_status(score, confidence, HypothesisStatus.PROPOSED)
        
        return RootCauseCandidate(
            finding_id=finding.id,
            hypothesis_id=None,
            attribution_id=attribution.id,
            score=score,
            confidence=confidence,
            supporting_evidence=[],
            contradicting_evidence=[],
            explanation=explanation,
            status=status
        )

    def _score_relevance(self, relevance: Relevance) -> float:
        if relevance == Relevance.HIGH: return 0.6
        if relevance == Relevance.MEDIUM: return 0.4
        if relevance == Relevance.LOW: return 0.2
        return 0.0

    def _determine_status(self, score: float, confidence: float, hyp_status: HypothesisStatus) -> CandidateStatus:
        if hyp_status == HypothesisStatus.REJECTED:
            return CandidateStatus.DISQUALIFIED
        if score >= 0.8 and confidence >= 0.8:
            return CandidateStatus.STRONG
        if score >= 0.4:
            return CandidateStatus.PLAUSIBLE
        return CandidateStatus.UNLIKELY
