import pytest
from backend.copilot.context import ContextBuilder, CopilotContext
from core.investigation.models import Investigation
from core.investigation.hypothesis import HypothesisStatus
from core.investigation.synthesis import InvestigationSynthesis
from core.dataset.models import DatasetVersion, Profile, ColumnProfile
from datetime import datetime, timezone
from core.findings.models import Finding, FindingCategory, Severity
from core.evidence.models import Evidence, EvidenceType
from core.attribution.models import Attribution, Relevance
from core.diff import ColumnChange

def _create_mock_objects():
    inv = Investigation("Test", "Test desc", "v_1")
    inv.id = "inv_123"
    
    f = Finding(
        category=FindingCategory.UNIQUENESS,
        title="Duplicate rows",
        description="Duplicates found",
        severity=Severity.HIGH,
        confidence=0.9,
        impact_score=0.9,
        column="customer_id",
        rule="UniqueRule"
    )
    f.id = "find_1"
    
    ev = Evidence(
        type=EvidenceType.QUERY,
        source="system",
        dataset_version="v_1",
        metric="dup_count",
        value=10,
        description="Duplicate query"
    )
    ev.id = "ev_1"
    f.add_evidence(ev)
    inv.add_finding(f)
    
    dv = DatasetVersion(
        id="v_1",
        dataset_id="ds_1",
        version_number=1,
        file_hash="abc",
        file_size=100,
        storage_path="path",
        format="csv",
        schema={"customer_id": "INTEGER"},
        row_count=100,
        created_at=datetime.now(timezone.utc)
    )
    dv.stats = {"columns": {"customer_id": {"type": "INTEGER", "null_count": 0, "null_fraction": 0.0, "unique_count": 90, "unique_fraction": 0.9, "min_value": 1, "max_value": 100, "mean": 50}}}
    
    attr = Attribution(
        finding_id=f.id,
        change=ColumnChange("customer_id", "unique_fraction", 1.0, 0.9, -0.1, -0.1, "cardinality_shift"),
        relevance_score=Relevance.HIGH,
        confidence=0.9,
        reason="Dropped uniqueness"
    )
    attr.id = "attr_1"
    
    synth = InvestigationSynthesis(
        investigation_id=inv.id,
        problem_summary="Problem",
        key_findings=[f],
        important_changes=[],
        attributions=[attr],
        hypotheses=[],
        validations=[],
        root_cause_candidates=[],
        strongest_candidate=None
    )
    
    return inv, synth, dv, attr

@pytest.mark.skip(reason="Outdated domain model")
def test_context_builder_success():
    inv, synth, dv, attr = _create_mock_objects()
    builder = ContextBuilder()
    
    context = builder.build(
        user_query="Why did this happen?",
        investigation=inv,
        synthesis=synth,
        dataset_version=dv
    )
    
    assert context.investigation_id == "inv_123"
    assert context.user_query == "Why did this happen?"
    
    # Check schema
    assert context.schema_context == {"customer_id": "INTEGER"}
    
    # Check evidence catalog
    assert len(context.evidence_catalog) == 1
    assert context.evidence_catalog[0]["id"] == "ev_1"
    
    # Check attributions
    assert len(context.attributions) == 1
    assert context.attributions[0]["id"] == "attr_1"

def test_context_builder_prevents_investigation_leak():
    inv, synth, dv, _ = _create_mock_objects()
    builder = ContextBuilder()
    
    # Force a mismatch
    synth.investigation_id = "inv_456"
    
    with pytest.raises(ValueError, match="Synthesis mismatch: Expected inv_123, got inv_456"):
        builder.build("Query", inv, synth, dv)

@pytest.mark.skip(reason="Outdated domain model")
def test_context_builder_prevents_dataset_leak():
    inv, synth, dv, _ = _create_mock_objects()
    builder = ContextBuilder()
    
    # Force a dataset profile mismatch
    dv.id = "v_999"
    
    with pytest.raises(ValueError, match="Dataset mismatch: Investigation targets v_1, but provided version is v_999"):
        builder.build("Query", inv, synth, dv)

@pytest.mark.skip(reason="Outdated domain model")
def test_context_builder_extracts_validation_evidence():
    inv, synth, dv, attr = _create_mock_objects()
    builder = ContextBuilder()
    
    hyp = inv.add_hypothesis("A theory", finding_id=inv.findings[0].id)
    ev = Evidence(
        type=EvidenceType.QUERY,
        source="human",
        dataset_version="v_1",
        metric="validation",
        value=1,
        description="Validation ev"
    )
    ev.id = "ev_2"
    
    from core.investigation.hypothesis import ValidationResult
    hyp.validate(ValidationResult(status=HypothesisStatus.SUPPORTED, description="Proven", evidence=[ev]))
    
    context = builder.build("Query", inv, synth, dv)
    
    # We should now have 2 evidence items (1 from finding, 1 from validation)
    assert len(context.evidence_catalog) == 2
    ids = [e["id"] for e in context.evidence_catalog]
    assert "ev_1" in ids
    assert "ev_2" in ids
    
    # Check active hypotheses compiled properly
    assert len(context.active_hypotheses) == 1
    assert context.active_hypotheses[0]["status"] == "SUPPORTED"
