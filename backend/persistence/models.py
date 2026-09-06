from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.persistence.database import Base

class DatasetORM(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, index=True, default="ws_local_dev")
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    versions = relationship("DatasetVersionORM", back_populates="dataset", cascade="all, delete-orphan")

class DatasetVersionORM(Base):
    __tablename__ = "dataset_versions"
    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    version_number = Column(Integer, nullable=False)
    file_hash = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)
    format = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    dataset = relationship("DatasetORM", back_populates="versions")
    profile = relationship("ProfileORM", back_populates="dataset_version", uselist=False, cascade="all, delete-orphan")

class ProfileORM(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    row_count = Column(Integer, nullable=False)
    
    dataset_version = relationship("DatasetVersionORM", back_populates="profile")
    column_profiles = relationship("ColumnProfileORM", back_populates="profile", cascade="all, delete-orphan")

class ColumnProfileORM(Base):
    __tablename__ = "column_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    column = Column(String, nullable=False)
    physical_type = Column(String, nullable=False)
    row_count = Column(Integer, nullable=False)
    null_count = Column(Integer, nullable=False)
    null_fraction = Column(Float, nullable=False)
    unique_count = Column(Integer, nullable=False)
    unique_fraction = Column(Float, nullable=False)
    min_value = Column(String, nullable=True)
    max_value = Column(String, nullable=True)
    mean = Column(String, nullable=True)
    
    profile = relationship("ProfileORM", back_populates="column_profiles")

class HypothesisORM(Base):
    __tablename__ = "hypotheses"
    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    finding_id = Column(String, nullable=True)
    attribution_id = Column(String, nullable=True)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PROPOSED")
    created_at = Column(DateTime, nullable=False)
    
    investigation = relationship("InvestigationORM", back_populates="hypotheses")
    experiments = relationship("ExperimentORM", back_populates="hypothesis", cascade="all, delete-orphan")
    validation_result = relationship("ValidationResultORM", back_populates="hypothesis", uselist=False, cascade="all, delete-orphan")

class ValidationResultORM(Base):
    __tablename__ = "validation_results"
    id = Column(String, primary_key=True, index=True)
    hypothesis_id = Column(String, ForeignKey("hypotheses.id"))
    status = Column(String, nullable=False)
    description = Column(String, nullable=False)
    validated_at = Column(DateTime, nullable=False)
    
    hypothesis = relationship("HypothesisORM", back_populates="validation_result")
    evidence = relationship("ValidationEvidenceORM", back_populates="validation_result", cascade="all, delete-orphan")

class ValidationEvidenceORM(Base):
    __tablename__ = "validation_evidence"
    id = Column(String, primary_key=True, index=True)
    validation_result_id = Column(String, ForeignKey("validation_results.id"))
    type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    value_json = Column(JSON, nullable=False)
    description = Column(String, nullable=False)

    validation_result = relationship("ValidationResultORM", back_populates="evidence")

class TimelineEventORM(Base):
    __tablename__ = "timeline_events"
    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    event_type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    description = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    
    investigation = relationship("InvestigationORM", back_populates="timeline_events")

class InvestigationORM(Base):
    __tablename__ = "investigations"
    id = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, index=True, default="ws_local_dev")
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    res_root_cause = Column(String, nullable=True)
    res_resolution_type = Column(String, nullable=True)
    res_resolved_at = Column(DateTime, nullable=True)
    res_validation_result = Column(String, nullable=True)

    findings = relationship("FindingORM", back_populates="investigation", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationORM", back_populates="investigation", cascade="all, delete-orphan")
    hypotheses = relationship("HypothesisORM", back_populates="investigation", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEventORM", back_populates="investigation", cascade="all, delete-orphan")
    experiments = relationship("ExperimentORM", back_populates="investigation", cascade="all, delete-orphan")

class FindingORM(Base):
    __tablename__ = "findings"
    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    impact_score = Column(Float, nullable=False)
    column_name = Column(String, nullable=True)
    rule_name = Column(String, nullable=True)

    investigation = relationship("InvestigationORM", back_populates="findings")
    observations = relationship("ObservationORM", back_populates="finding", cascade="all, delete-orphan")
    evidence = relationship("EvidenceORM", back_populates="finding", cascade="all, delete-orphan")

class ObservationORM(Base):
    __tablename__ = "observations"
    id = Column(String, primary_key=True, index=True)
    finding_id = Column(String, ForeignKey("findings.id"))
    metric = Column(String, nullable=False)
    value_json = Column(JSON, nullable=False)
    column_name = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    description = Column(String, nullable=False)

    finding = relationship("FindingORM", back_populates="observations")

class EvidenceORM(Base):
    __tablename__ = "evidence"
    id = Column(String, primary_key=True, index=True)
    finding_id = Column(String, ForeignKey("findings.id"))
    type = Column(String, nullable=False)
    source = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    value_json = Column(JSON, nullable=False)
    description = Column(String, nullable=False)

    finding = relationship("FindingORM", back_populates="evidence")

class RecommendationORM(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    rationale = Column(String, nullable=False)
    priority = Column(String, nullable=False)

    investigation = relationship("InvestigationORM", back_populates="recommendations")

class ExperimentORM(Base):
    __tablename__ = "experiments"
    id = Column(String, primary_key=True, index=True)
    investigation_id = Column(String, ForeignKey("investigations.id"))
    hypothesis_id = Column(String, ForeignKey("hypotheses.id"))
    sql_query = Column(String, nullable=False)
    requested_by = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    result_json = Column(JSON, nullable=True)

    investigation = relationship("InvestigationORM", back_populates="experiments")
    hypothesis = relationship("HypothesisORM", back_populates="experiments")
