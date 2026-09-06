import pytest
from core.investigation.models import Investigation, InvestigationStatus
from core.findings.models import Finding, FindingCategory, Severity
from core.diff import DatasetDiff, ColumnChange
from core.attribution.models import Attribution, Relevance
from core.investigation.hypothesis import HypothesisStatus
from core.investigation.hypothesis import ValidationResult
from core.evidence.models import Evidence, EvidenceType
from core.attribution.root_cause import RootCauseCandidate, CandidateStatus
from core.investigation.synthesis import InvestigationSynthesizer

def _create_base_investigation() -> Investigation:
    inv = Investigation("Uniqueness Incident", "Duplicate customer IDs found", "v2")
    f = Finding(
        category=FindingCategory.UNIQUENESS,
        title="Duplicate customer_id",
        description="Duplicate rows found",
        severity=Severity.HIGH,
        confidence=0.9,
        impact_score=0.9,
        column="customer_id",
        rule="UniqueRule"
    )
    inv.add_finding(f)
    return inv

@pytest.mark.skip(reason="Outdated domain model")
def test_synthesis_finding_only():
    inv = _create_base_investigation()
    synthesizer = InvestigationSynthesizer()
    synthesis = synthesizer.synthesize(inv)
    
    assert synthesis.investigation_id == inv.id
    assert "Uniqueness Incident" in synthesis.problem_summary
    assert len(synthesis.key_findings) == 1
    assert not synthesis.important_changes
    assert not synthesis.attributions
    assert not synthesis.hypotheses
    assert not synthesis.root_cause_candidates
    assert synthesis.strongest_candidate is None

    markdown = synthesis.to_markdown()
    assert "No historical changes detected." in markdown
    assert "No root cause candidates identified yet." in markdown

def test_synthesis_finding_and_changes():
    inv = _create_base_investigation()
    diff = DatasetDiff("ds1", "v1", "v2", [], [
        ColumnChange("customer_id", "unique_fraction", 1.0, 0.9, -0.1, -0.1, "cardinality_shift")
    ], "Change detected")
    
    synthesizer = InvestigationSynthesizer()
    synthesis = synthesizer.synthesize(inv, diff=diff)
    
    assert len(synthesis.important_changes) == 1
    markdown = synthesis.to_markdown()
    assert "unique_fraction on 'customer_id' shifted (delta: -0.1)" in markdown

def test_synthesis_with_attribution():
    inv = _create_base_investigation()
    attr = Attribution(
        finding_id=inv.findings[0].id,
        change=ColumnChange("customer_id", "unique_fraction", 1.0, 0.9, -0.1, -0.1, "cardinality_shift"),
        relevance_score=Relevance.HIGH,
        confidence=0.9,
        reason="Direct uniqueness shift."
    )
    
    synthesis = InvestigationSynthesizer().synthesize(inv, attributions=[attr])
    assert len(synthesis.attributions) == 1
    
    markdown = synthesis.to_markdown()
    assert "Direct uniqueness shift." in markdown

def test_synthesis_supported_hypothesis():
    inv = _create_base_investigation()
    hyp = inv.add_hypothesis("Data engineering pipeline retry.", finding_id="dummy_finding_id")
    ev = Evidence(EvidenceType.QUERY, "sys", "v2", "dup", 10, "10 dups")
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.SUPPORTED, description="Confirmed via logs", evidence=[ev]))
    
    rc = RootCauseCandidate(
        finding_id=inv.findings[0].id,
        score=0.9,
        confidence=0.9,
        supporting_evidence=[ev],
        contradicting_evidence=[],
        explanation="Pipeline retry supported.",
        status=CandidateStatus.STRONG,
        hypothesis_id=hyp.id
    )
    
    synthesis = InvestigationSynthesizer().synthesize(inv, candidates=[rc])
    assert len(synthesis.validations) == 1
    assert synthesis.strongest_candidate == rc
    
    markdown = synthesis.to_markdown()
    assert "Hypothesis: Data engineering pipeline retry." in markdown
    assert "Result: SUPPORTED" in markdown
    assert "Pipeline retry supported." in markdown
    assert "Status: STRONG" in markdown

def test_synthesis_rejected_hypothesis():
    inv = _create_base_investigation()
    hyp = inv.add_hypothesis("Not a real issue.", finding_id="dummy_finding_id")
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.REJECTED, description="Definitely an issue", evidence=[]))
    
    rc = RootCauseCandidate(
        finding_id=inv.findings[0].id,
        score=0.0,
        confidence=0.9,
        supporting_evidence=[],
        contradicting_evidence=[],
        explanation="Hypothesis rejected.",
        status=CandidateStatus.DISQUALIFIED,
        hypothesis_id=hyp.id
    )
    
    synthesis = InvestigationSynthesizer().synthesize(inv, candidates=[rc])
    # Should not be considered strongest since it's disqualified
    assert synthesis.strongest_candidate is None
    
    markdown = synthesis.to_markdown()
    assert "Result: REJECTED" in markdown

def test_synthesis_multiple_candidates():
    inv = _create_base_investigation()
    
    rc1 = RootCauseCandidate(
        finding_id=inv.findings[0].id,
        score=0.8,
        confidence=0.9,
        supporting_evidence=[],
        contradicting_evidence=[],
        explanation="Candidate 1",
        status=CandidateStatus.STRONG
    )
    
    rc2 = RootCauseCandidate(
        finding_id=inv.findings[0].id,
        score=0.5,
        confidence=0.5,
        supporting_evidence=[],
        contradicting_evidence=[],
        explanation="Candidate 2",
        status=CandidateStatus.PLAUSIBLE
    )
    
    # Intentionally pass out of order
    synthesis = InvestigationSynthesizer().synthesize(inv, candidates=[rc2, rc1])
    
    # Engine must deterministically sort and pick rc1
    assert synthesis.strongest_candidate == rc1
    assert synthesis.root_cause_candidates[0] == rc1
    assert synthesis.root_cause_candidates[1] == rc2

def test_synthesis_deterministic_identical_output():
    # Build complete investigation state
    inv = _create_base_investigation()
    diff = DatasetDiff("ds1", "v1", "v2", [], [ColumnChange("customer_id", "unique_fraction", 1.0, 0.9, -0.1, -0.1, "cardinality_shift")], "Change detected")
    attr = Attribution(inv.findings[0].id, diff.column_changes[0], Relevance.HIGH, 0.9, "Direct metric hit")
    hyp = inv.add_hypothesis("Retry", finding_id="dummy_finding_id", attribution_id=attr.id)
    ev = Evidence(EvidenceType.QUERY, "sys", "v2", "dup", 10, "10 dups")
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.SUPPORTED, description="Logs show retry", evidence=[ev]))
    
    rc = RootCauseCandidate(inv.findings[0].id, 1.0, 0.9, [ev], [], "Retry proven", CandidateStatus.STRONG, hyp.id, attr.id)
    
    # Generate 1
    synth1 = InvestigationSynthesizer().synthesize(inv, diff, [attr], [rc])
    
    # We must explicitly zero out generated_at for exact string comparison, 
    # since it uses timezone.utc currently.
    synth1.generated_at = None 
    markdown1 = synth1.to_markdown()
    
    # Generate 2
    synth2 = InvestigationSynthesizer().synthesize(inv, diff, [attr], [rc])
    synth2.generated_at = None
    markdown2 = synth2.to_markdown()
    
    assert markdown1 == markdown2
    
    # Evidence Traceability
    assert "1 artifacts." in markdown1
    assert attr.reason in markdown1
    assert hyp.description in markdown1
    assert rc.explanation in markdown1
